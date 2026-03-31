from typing import Dict, List

from pydantic import BaseModel


class DialogueRequest(BaseModel):
    npc_name: str
    user_message: str


class DialogueResponse(BaseModel):
    npc_name: str
    npc_display_name: str
    npc_role: str
    scene_title: str
    scene_theme: str
    reply_text: str
    relationship_score: int
    relationship_stage: str
    task_title: str
    task_status: str
    task_description: str
    task_feedback: str
    memory_highlights: List[str]


class NPCWorldProfileModel(BaseModel):
    id: str
    name: str
    role: str
    personality: str
    speaking_style: str
    avatar_prompt: str
    building_prompt: str


class WorldConfigUpdateRequest(BaseModel):
    scene_title: str
    scene_theme: str
    scene_description: str
    scene_theme_prompt: str
    npcs: Dict[str, NPCWorldProfileModel]


class WorldPresetSummary(BaseModel):
    preset_id: str
    scene_title: str
    scene_theme: str


class WorldConfigResponse(BaseModel):
    preset_id: str
    scene_title: str
    scene_theme: str
    scene_description: str
    scene_theme_prompt: str
    npcs: Dict[str, NPCWorldProfileModel]
    presets: List[WorldPresetSummary]
