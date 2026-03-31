from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents import NPCAgentManager
from config import BASE_DIR, HOST, PORT
from episodic_memory import EpisodicMemoryManager
from memory_manager import ShortTermMemoryManager
from models import (
    DialogueRequest,
    DialogueResponse,
    WorldConfigResponse,
    WorldConfigUpdateRequest,
    WorldPresetSummary,
)
from relationship_manager import RelationshipManager
from task_manager import TaskManager
from world_config import WorldConfigManager

app = FastAPI(title="Helloagents AI Town Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

world_config_manager = WorldConfigManager(data_dir=BASE_DIR / "world_data")
agent_manager = NPCAgentManager(world_config_manager)
memory_manager = ShortTermMemoryManager(max_turns=4)
relationship_manager = RelationshipManager()
task_manager = TaskManager()
episodic_memory_manager = EpisodicMemoryManager(
    data_dir=BASE_DIR / "memory_data",
    max_items_per_npc=50,
)


@app.get("/", summary="Health check")
def health_check():
    return {"status": "ok", "message": "backend is running"}


@app.get("/world-config", response_model=WorldConfigResponse, summary="Get current world config")
def get_world_config():
    config = world_config_manager.get_config()
    return WorldConfigResponse(
        preset_id=config["preset_id"],
        scene_title=config["scene_title"],
        scene_theme=config["scene_theme"],
        scene_description=config["scene_description"],
        scene_theme_prompt=config["scene_theme_prompt"],
        npcs=config["npcs"],
        presets=[WorldPresetSummary(**preset) for preset in world_config_manager.list_presets()],
    )


@app.post("/world-config", response_model=WorldConfigResponse, summary="Save world config")
def save_world_config(request: WorldConfigUpdateRequest):
    config = world_config_manager.update_config(request.model_dump())
    return WorldConfigResponse(
        preset_id=config["preset_id"],
        scene_title=config["scene_title"],
        scene_theme=config["scene_theme"],
        scene_description=config["scene_description"],
        scene_theme_prompt=config["scene_theme_prompt"],
        npcs=config["npcs"],
        presets=[WorldPresetSummary(**preset) for preset in world_config_manager.list_presets()],
    )


@app.post("/world-presets/{preset_id}", response_model=WorldConfigResponse, summary="Apply a world preset")
def apply_world_preset(preset_id: str):
    try:
        config = world_config_manager.apply_preset(preset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return WorldConfigResponse(
        preset_id=config["preset_id"],
        scene_title=config["scene_title"],
        scene_theme=config["scene_theme"],
        scene_description=config["scene_description"],
        scene_theme_prompt=config["scene_theme_prompt"],
        npcs=config["npcs"],
        presets=[WorldPresetSummary(**preset) for preset in world_config_manager.list_presets()],
    )


@app.post("/dialogue", response_model=DialogueResponse, summary="Talk to an NPC")
def dialogue(request: DialogueRequest):
    world_config = world_config_manager.get_config()
    npc = agent_manager.get_npc(request.npc_name)
    recent_history = memory_manager.get_recent_history(npc.npc_id)
    relevant_memories = episodic_memory_manager.search_relevant_memories(
        npc.npc_id,
        request.user_message,
        top_k=3,
    )
    print(
        f"[EpisodicMemory] npc={npc.npc_id} retrieved={len(relevant_memories)} "
        f"total={episodic_memory_manager.get_memory_count(npc.npc_id)}"
    )

    relationship_score, relationship_delta = relationship_manager.update_score(
        npc.npc_id,
        request.user_message,
    )
    relationship_stage = relationship_manager.get_stage(relationship_score)
    relationship_description = relationship_manager.get_stage_description(relationship_score)
    print(
        f"[Relationship] npc={npc.npc_id} score={relationship_score} "
        f"delta={relationship_delta} stage={relationship_stage}"
    )

    task_result = task_manager.process_message(
        npc_id=npc.npc_id,
        relationship_stage=relationship_stage,
        user_message=request.user_message,
        npc_display_name=npc.name,
        npc_role=npc.role,
        scene_title=world_config["scene_title"],
    )
    if task_result is None:
        task_result = task_manager.get_task_view(
            npc_id=npc.npc_id,
            relationship_stage=relationship_stage,
            npc_display_name=npc.name,
            npc_role=npc.role,
            scene_title=world_config["scene_title"],
        )

    task_context = ""
    if task_result is not None:
        task_context = (
            f"Current task title: {task_result.title}. "
            f"Task status: {task_result.status}. "
            f"Task description: {task_result.description}. "
        )
        if task_result.feedback:
            task_context += f"Latest task feedback: {task_result.feedback}. "

    if task_result is not None and task_result.reward_affinity > 0:
        relationship_score = relationship_manager.adjust_score(
            npc.npc_id,
            task_result.reward_affinity,
        )
        relationship_stage = relationship_manager.get_stage(relationship_score)
        relationship_description = relationship_manager.get_stage_description(relationship_score)
        print(
            f"[Task] npc={npc.npc_id} completed={task_result.title} "
            f"reward_affinity={task_result.reward_affinity} score={relationship_score}"
        )

    reply_text = agent_manager.generate_reply(
        npc=npc,
        user_message=request.user_message,
        recent_history=recent_history,
        relevant_memories=relevant_memories,
        relationship_score=relationship_score,
        relationship_stage=relationship_stage,
        relationship_description=relationship_description,
        task_context=task_context,
        requested_npc_id=request.npc_name,
    )

    memory_entry = agent_manager.build_memory_entry(
        npc,
        request.user_message,
        reply_text,
    )
    memory_manager.append_turn(npc.npc_id, request.user_message, memory_entry)

    saved = episodic_memory_manager.save_memory_if_important(
        npc.npc_id,
        request.user_message,
        reply_text,
    )
    if saved:
        print(
            f"[EpisodicMemory] npc={npc.npc_id} saved important memory. "
            f"total={episodic_memory_manager.get_memory_count(npc.npc_id)}"
        )

    if task_result is not None and task_result.completion_memory:
        episodic_memory_manager.save_manual_memory(
            npc.npc_id,
            request.user_message,
            task_result.completion_memory,
        )
        print(
            f"[Task] npc={npc.npc_id} wrote task completion memory. "
            f"total={episodic_memory_manager.get_memory_count(npc.npc_id)}"
        )

    memory_highlights = episodic_memory_manager.get_recent_summaries(npc.npc_id, limit=3)
    task_view = task_manager.get_task_view(
        npc_id=npc.npc_id,
        relationship_stage=relationship_stage,
        npc_display_name=npc.name,
        npc_role=npc.role,
        scene_title=world_config["scene_title"],
    )

    return DialogueResponse(
        npc_name=npc.npc_id,
        npc_display_name=npc.name,
        npc_role=npc.role,
        scene_title=world_config["scene_title"],
        scene_theme=world_config["scene_theme"],
        reply_text=reply_text,
        relationship_score=relationship_score,
        relationship_stage=relationship_stage,
        task_title=task_view.title if task_view is not None else "No active task",
        task_status=task_view.status if task_view is not None else "none",
        task_description=task_view.description if task_view is not None else "",
        task_feedback=task_result.feedback if task_result is not None else "",
        memory_highlights=memory_highlights,
    )
