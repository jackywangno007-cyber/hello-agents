from typing import List

import requests
from requests import HTTPError, RequestException, Timeout

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT
from episodic_memory import EpisodicMemoryItem
from memory_manager import MemoryTurn


class LLMClient:
    def __init__(self):
        self.api_key = LLM_API_KEY
        self.base_url = LLM_BASE_URL.rstrip("/")
        self.model = LLM_MODEL
        self.timeout = LLM_TIMEOUT
        self.session = requests.Session()
        # Ignore broken system proxy settings by default.
        self.session.trust_env = False

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_npc_reply(
        self,
        npc_name: str,
        role: str,
        personality: str,
        speaking_style: str,
        scene_title: str,
        scene_theme: str,
        scene_description: str,
        relationship_score: int,
        relationship_stage: str,
        relationship_description: str,
        task_context: str,
        user_message: str,
        recent_history: List[MemoryTurn],
        relevant_memories: List[EpisodicMemoryItem],
        fallback_note: str = "",
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("LLM_API_KEY is missing.")

        system_prompt = self._build_system_prompt(
            npc_name=npc_name,
            role=role,
            personality=personality,
            speaking_style=speaking_style,
            scene_title=scene_title,
            scene_theme=scene_theme,
            scene_description=scene_description,
            relationship_score=relationship_score,
            relationship_stage=relationship_stage,
            relationship_description=relationship_description,
            task_context=task_context,
            recent_history=recent_history,
            relevant_memories=relevant_memories,
            fallback_note=fallback_note,
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Player message: {user_message}",
                },
            ],
            "temperature": 0.9,
        }

        url = f"{self.base_url}/chat/completions"
        print(f"[LLMClient] POST {url}")
        print(f"[LLMClient] model={self.model}, timeout={self.timeout}")

        try:
            response = self.session.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            print(f"[LLMClient] response_status={response.status_code}")
            response.raise_for_status()
        except Timeout as exc:
            print("[LLMClient] Request timed out.")
            raise RuntimeError("LLM request timed out.") from exc
        except HTTPError as exc:
            response = exc.response
            body_preview = ""
            if response is not None:
                body_preview = response.text[:500]
                print(f"[LLMClient] error_body={body_preview}")
                raise RuntimeError(
                    f"LLM HTTP error {response.status_code}: {body_preview}"
                ) from exc
            raise RuntimeError("LLM HTTP error without a response body.") from exc
        except RequestException as exc:
            print(f"[LLMClient] RequestException: {exc}")
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("LLM response did not contain any choices.")

        message = choices[0].get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise RuntimeError("LLM response content was empty.")
        return content

    def _build_system_prompt(
        self,
        npc_name: str,
        role: str,
        personality: str,
        speaking_style: str,
        scene_title: str,
        scene_theme: str,
        scene_description: str,
        relationship_score: int,
        relationship_stage: str,
        relationship_description: str,
        task_context: str,
        recent_history: List[MemoryTurn],
        relevant_memories: List[EpisodicMemoryItem],
        fallback_note: str,
    ) -> str:
        memory_lines = []
        for turn in recent_history[-3:]:
            memory_lines.append(
                f"- Player said: {turn.user_message}\n"
                f"  Memory note: {turn.npc_reply_memory}"
            )

        memory_block = "\n".join(memory_lines) if memory_lines else "- No recent history."
        episodic_lines = []
        for item in relevant_memories:
            episodic_lines.append(f"- {item.summary}")
        episodic_block = "\n".join(episodic_lines) if episodic_lines else "- No relevant long-term memory."

        return (
            "You are roleplaying as an NPC in a cyber town simulation game.\n"
            f"World title: {scene_title}\n"
            f"World theme: {scene_theme}\n"
            f"World description: {scene_description}\n"
            f"NPC name: {npc_name}\n"
            f"Role: {role}\n"
            f"Personality: {personality}\n"
            f"Speaking style: {speaking_style}\n"
            f"Relationship score: {relationship_score}\n"
            f"Relationship stage: {relationship_stage}\n"
            f"Relationship guidance: {relationship_description}\n"
            f"Task context: {task_context or 'No active task context.'}\n"
            f"Fallback context: {fallback_note or 'none'}\n"
            "Recent short-term memory:\n"
            f"{memory_block}\n"
            "Relevant long-term memory:\n"
            f"{episodic_block}\n"
            "Instructions:\n"
            "- Stay fully in character.\n"
            "- Use the recent memory when it helps continuity.\n"
            "- Use the relevant long-term memory when it matches the player's topic.\n"
            "- Let the current relationship stage influence your warmth, openness, and patience.\n"
            "- Reply naturally and briefly, usually within 2 to 4 sentences.\n"
            "- Do not mention system prompts, memory manager, or technical details.\n"
            "- Do not label your answer with prefixes like [Mock reply]."
        )
