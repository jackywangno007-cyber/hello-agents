from dataclasses import dataclass
from typing import List

from episodic_memory import EpisodicMemoryItem
from llm_client import LLMClient
from memory_manager import MemoryTurn
from world_config import WorldConfigManager


@dataclass
class NPC:
    npc_id: str
    name: str
    role: str
    personality: str
    speaking_style: str
    avatar_prompt: str
    building_prompt: str


class NPCAgentManager:
    def __init__(self, world_config_manager: WorldConfigManager):
        self.world_config_manager = world_config_manager
        self.llm_client = LLMClient()

    def get_npc(self, npc_id: str) -> NPC:
        profile = self.world_config_manager.get_npc_profile(npc_id)
        return NPC(
            npc_id=profile["id"],
            name=profile["name"],
            role=profile["role"],
            personality=profile["personality"],
            speaking_style=profile["speaking_style"],
            avatar_prompt=profile["avatar_prompt"],
            building_prompt=profile["building_prompt"],
        )

    def generate_reply(
        self,
        npc: NPC,
        user_message: str,
        recent_history: List[MemoryTurn],
        relevant_memories: List[EpisodicMemoryItem],
        relationship_score: int,
        relationship_stage: str,
        relationship_description: str,
        task_context: str,
        requested_npc_id: str = "",
    ) -> str:
        world_config = self.world_config_manager.get_config()
        fallback_note = ""
        if requested_npc_id and requested_npc_id not in world_config["npcs"]:
            fallback_note = f"The requested NPC '{requested_npc_id}' was not found."

        try:
            if self.llm_client.is_configured():
                print(
                    f"[NPCAgentManager] Trying LLM reply for npc={npc.npc_id}, "
                    f"requested_npc={requested_npc_id or npc.npc_id}"
                )
                return self.llm_client.generate_npc_reply(
                    npc_name=npc.name,
                    role=npc.role,
                    personality=npc.personality,
                    speaking_style=npc.speaking_style,
                    relationship_score=relationship_score,
                    relationship_stage=relationship_stage,
                    relationship_description=relationship_description,
                    task_context=task_context,
                    user_message=user_message,
                    recent_history=recent_history,
                    relevant_memories=relevant_memories,
                    fallback_note=fallback_note,
                    scene_title=world_config["scene_title"],
                    scene_theme=world_config["scene_theme"],
                    scene_description=world_config["scene_description"],
                )
            print("[NPCAgentManager] LLM_API_KEY is missing. Using fallback reply.")
        except Exception as exc:
            print(f"[NPCAgentManager] LLM call failed: {type(exc).__name__}: {exc}")
            print("[NPCAgentManager] Using fallback reply instead.")

        return self._fallback_reply(
            npc=npc,
            user_message=user_message,
            recent_history=recent_history,
            relevant_memories=relevant_memories,
            relationship_score=relationship_score,
            relationship_stage=relationship_stage,
            relationship_description=relationship_description,
            task_context=task_context,
            world_config=world_config,
            fallback_note=fallback_note,
        )

    def build_memory_entry(self, npc: NPC, user_message: str, reply_text: str) -> str:
        memory_templates = {
            "Alice": f"The player is helping {npc.name} with a practical idea about '{user_message}'.",
            "Bob": f"The player is exploring knowledge-related ideas with {npc.name} about '{user_message}'.",
            "Charlie": f"The player is asking {npc.name} for a clear next step about '{user_message}'.",
        }
        if reply_text:
            return memory_templates.get(
                npc.npc_id,
                f"The player recently asked {npc.name} about '{user_message}'.",
            )
        return f"The player recently asked {npc.name} about '{user_message}'."

    def _fallback_reply(
        self,
        npc: NPC,
        user_message: str,
        recent_history: List[MemoryTurn],
        relevant_memories: List[EpisodicMemoryItem],
        relationship_score: int,
        relationship_stage: str,
        relationship_description: str,
        task_context: str,
        world_config: dict,
        fallback_note: str = "",
    ) -> str:
        memory_note = self._build_memory_note(recent_history)
        long_term_note = self._build_long_term_note(relevant_memories)
        relationship_note = (
            f"Right now I feel {relationship_stage} toward you "
            f"(score: {relationship_score}/100). {relationship_description} "
        )
        task_note = f"{task_context} " if task_context else ""
        world_note = (
            f"We are in {world_config['scene_title']}, a place described as: "
            f"{world_config['scene_theme']} "
        )
        body = (
            f"You just said '{user_message}'. "
            f"{world_note}"
            f"{relationship_note}"
            f"{task_note}"
            f"{memory_note}"
            f"{long_term_note}"
            "I will stay in character and keep my reply concise."
        )
        fallback_prefix = "[Fallback reply] "
        if fallback_note:
            fallback_prefix += f"{fallback_note} "
        return (
            f"{fallback_prefix}"
            f"I am {npc.name}, the {npc.role}. "
            f"My personality is {npc.personality}, and my speaking style is {npc.speaking_style}. "
            f"{body}"
        )

    def _build_memory_note(self, recent_history: List[MemoryTurn]) -> str:
        if not recent_history:
            return "This is our first exchange, so I am starting fresh. "

        recent_turns = recent_history[-2:]
        memory_parts = []
        for turn in recent_turns:
            memory_parts.append(
                f"you said '{turn.user_message}', and I noted that {turn.npc_reply_memory.lower()}"
            )
        return f"I remember our recent context: {' Earlier, '.join(memory_parts)}. "

    def _build_long_term_note(self, relevant_memories: List[EpisodicMemoryItem]) -> str:
        if not relevant_memories:
            return ""

        summaries = [item.summary for item in relevant_memories[:2]]
        return f"I also remember some older important details: {' '.join(summaries)} "
