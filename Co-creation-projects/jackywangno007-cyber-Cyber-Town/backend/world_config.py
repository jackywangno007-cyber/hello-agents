import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List


def _build_presets() -> Dict[str, Dict[str, Any]]:
    return {
        "cyber_town": {
            "preset_id": "cyber_town",
            "scene_title": "Cyber Town",
            "scene_theme": "A clean cyber small town with bright roads, friendly shops, and AI citizens.",
            "scene_description": "A compact prototype town where players can walk around, talk to NPCs, and shape the world.",
            "scene_theme_prompt": "light top-down cozy cyber town, flat cartoon style, clear roads, colorful storefronts, calm sky",
            "npcs": {
                "Alice": {
                    "id": "Alice",
                    "name": "Alice",
                    "role": "Market Vendor",
                    "personality": "warm, upbeat, playful, practical",
                    "speaking_style": "friendly, casual, and energetic",
                    "avatar_prompt": "cheerful market vendor, orange apron, top-down cartoon portrait",
                    "building_prompt": "small bright market stall with orange awning",
                },
                "Bob": {
                    "id": "Bob",
                    "name": "Bob",
                    "role": "Library Keeper",
                    "personality": "calm, thoughtful, bookish, patient",
                    "speaking_style": "clear, polite, and gently academic",
                    "avatar_prompt": "kind librarian, blue coat, top-down cartoon portrait",
                    "building_prompt": "cozy small library with blue roof",
                },
                "Charlie": {
                    "id": "Charlie",
                    "name": "Charlie",
                    "role": "Town Guard",
                    "personality": "serious, reliable, observant, protective",
                    "speaking_style": "brief, firm, and reassuring",
                    "avatar_prompt": "vigilant town guard, green cloak, top-down cartoon portrait",
                    "building_prompt": "compact guard post with green roof",
                },
            },
        },
        "seaside_town": {
            "preset_id": "seaside_town",
            "scene_title": "Seaside Town",
            "scene_theme": "A breezy coastal town with sunlit piers, sea wind, and warm local stories.",
            "scene_description": "A compact seaside district where citizens talk about boats, books, and patrols by the harbor.",
            "scene_theme_prompt": "top-down seaside town, fresh pastel palette, wooden piers, ocean breeze, flat cartoon",
            "npcs": {
                "Alice": {
                    "id": "Alice",
                    "name": "Marina",
                    "role": "Harbor Stall Owner",
                    "personality": "sunny, welcoming, lively, business-minded",
                    "speaking_style": "bubbly, direct, and easygoing",
                    "avatar_prompt": "coastal market owner with coral scarf, top-down cartoon portrait",
                    "building_prompt": "harbor stall with striped canopy and small fish signs",
                },
                "Bob": {
                    "id": "Bob",
                    "name": "Elias",
                    "role": "Tide Archive Keeper",
                    "personality": "gentle, reflective, scholarly, curious",
                    "speaking_style": "soft, thoughtful, and descriptive",
                    "avatar_prompt": "archive keeper with navy vest, top-down cartoon portrait",
                    "building_prompt": "seaside reading room with pale blue roof",
                },
                "Charlie": {
                    "id": "Charlie",
                    "name": "Corin",
                    "role": "Harbor Watch",
                    "personality": "steady, disciplined, cautious, loyal",
                    "speaking_style": "measured, practical, and watchful",
                    "avatar_prompt": "harbor guard with green coat, top-down cartoon portrait",
                    "building_prompt": "small harbor watch post with lantern",
                },
            },
        },
        "magic_campus": {
            "preset_id": "magic_campus",
            "scene_title": "Magic Campus",
            "scene_theme": "A bright magical academy courtyard with curious students and whimsical faculty.",
            "scene_description": "A compact fantasy campus where each NPC reflects a different part of academy life.",
            "scene_theme_prompt": "top-down magic campus, pastel fantasy buildings, soft trees, flat cartoon style",
            "npcs": {
                "Alice": {
                    "id": "Alice",
                    "name": "Alya",
                    "role": "Potion Booth Mentor",
                    "personality": "lively, inventive, encouraging, mischievous",
                    "speaking_style": "playful, clever, and enthusiastic",
                    "avatar_prompt": "young potion mentor with amber cape, top-down cartoon portrait",
                    "building_prompt": "small potion kiosk with glowing bottles",
                },
                "Bob": {
                    "id": "Bob",
                    "name": "Borin",
                    "role": "Arcane Library Curator",
                    "personality": "calm, wise, precise, caring",
                    "speaking_style": "formal, clear, and warm",
                    "avatar_prompt": "arcane librarian with blue robe, top-down cartoon portrait",
                    "building_prompt": "mini magical library with crystal roof",
                },
                "Charlie": {
                    "id": "Charlie",
                    "name": "Cyrus",
                    "role": "Campus Warden",
                    "personality": "strict, protective, honorable, dependable",
                    "speaking_style": "short, steady, and authoritative",
                    "avatar_prompt": "campus warden with green mantle, top-down cartoon portrait",
                    "building_prompt": "small academy gate post with runic banner",
                },
            },
        },
    }


class WorldConfigManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / "current_world.json"
        self.presets = _build_presets()
        self.default_preset_id = "cyber_town"
        self.current_config = self._load_or_create()

    def get_config(self) -> Dict[str, Any]:
        return deepcopy(self.current_config)

    def list_presets(self) -> List[Dict[str, str]]:
        items = []
        for preset_id, preset in self.presets.items():
            items.append(
                {
                    "preset_id": preset_id,
                    "scene_title": preset["scene_title"],
                    "scene_theme": preset["scene_theme"],
                }
            )
        return items

    def apply_preset(self, preset_id: str) -> Dict[str, Any]:
        if preset_id not in self.presets:
            raise KeyError(f"Unknown preset: {preset_id}")

        self.current_config = deepcopy(self.presets[preset_id])
        self._save()
        return self.get_config()

    def update_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updated = self.get_config()
        updated["scene_title"] = str(payload.get("scene_title", updated["scene_title"])).strip() or updated["scene_title"]
        updated["scene_theme"] = str(payload.get("scene_theme", updated["scene_theme"])).strip() or updated["scene_theme"]
        updated["scene_description"] = str(payload.get("scene_description", updated["scene_description"])).strip() or updated["scene_description"]
        updated["scene_theme_prompt"] = str(payload.get("scene_theme_prompt", updated["scene_theme_prompt"])).strip() or updated["scene_theme_prompt"]

        payload_npcs = payload.get("npcs", {})
        if isinstance(payload_npcs, dict):
            for npc_id, npc_payload in payload_npcs.items():
                if npc_id not in updated["npcs"] or not isinstance(npc_payload, dict):
                    continue
                npc_data = updated["npcs"][npc_id]
                for field_name in [
                    "name",
                    "role",
                    "personality",
                    "speaking_style",
                    "avatar_prompt",
                    "building_prompt",
                ]:
                    new_value = str(npc_payload.get(field_name, npc_data[field_name])).strip()
                    if new_value:
                        npc_data[field_name] = new_value

        self.current_config = updated
        self._save()
        return self.get_config()

    def get_npc_profile(self, npc_id: str) -> Dict[str, Any]:
        config = self.current_config["npcs"].get(npc_id)
        if config is None:
            return {
                "id": npc_id,
                "name": npc_id,
                "role": "Guide",
                "personality": "adaptable and welcoming",
                "speaking_style": "neutral and helpful",
                "avatar_prompt": "friendly helper portrait",
                "building_prompt": "small helpful kiosk",
            }
        return deepcopy(config)

    def _load_or_create(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            config = deepcopy(self.presets[self.default_preset_id])
            self.current_config = config
            self._save()
            return config

        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        merged = deepcopy(self.presets[self.default_preset_id])
        merged.update({key: value for key, value in data.items() if key != "npcs"})
        for npc_id, npc_data in merged["npcs"].items():
            saved_npc = data.get("npcs", {}).get(npc_id, {})
            if isinstance(saved_npc, dict):
                npc_data.update(saved_npc)
        return merged

    def _save(self) -> None:
        self.file_path.write_text(
            json.dumps(self.current_config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
