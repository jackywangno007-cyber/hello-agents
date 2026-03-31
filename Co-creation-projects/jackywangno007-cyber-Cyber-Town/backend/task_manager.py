from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TaskDefinition:
    npc_id: str
    unlock_stage: str
    accept_keywords: List[str]
    completion_keywords: List[str]
    reward_affinity: int


@dataclass
class TaskState:
    status: str


@dataclass
class TaskUpdateResult:
    status: str
    title: str
    description: str
    feedback: str
    reward_affinity: int
    completion_memory: str


class TaskManager:
    STAGE_ORDER = {
        "cold": 0,
        "guarded": 1,
        "neutral": 2,
        "warm": 3,
        "trusted": 4,
    }

    def __init__(self):
        self.task_definitions: Dict[str, TaskDefinition] = {
            "Alice": TaskDefinition(
                npc_id="Alice",
                unlock_stage="warm",
                accept_keywords=["我来帮你", "我愿意帮你", "好的我帮你", "accept", "help you"],
                completion_keywords=["卖", "水果", "咖啡", "面包", "小吃", "花店", "杂货", "tea", "snack", "shop"],
                reward_affinity=10,
            ),
            "Bob": TaskDefinition(
                npc_id="Bob",
                unlock_stage="neutral",
                accept_keywords=["我来帮你", "我愿意帮你", "好的我帮你", "accept", "help you"],
                completion_keywords=["历史", "编程", "小说", "哲学", "科学", "艺术", "文学", "history", "coding", "novel"],
                reward_affinity=8,
            ),
            "Charlie": TaskDefinition(
                npc_id="Charlie",
                unlock_stage="neutral",
                accept_keywords=["我来帮你", "我愿意帮你", "好的我帮你", "accept", "help you"],
                completion_keywords=["安全", "小心", "巡逻", "警惕", "留意", "注意", "safe", "watch", "patrol", "careful"],
                reward_affinity=9,
            ),
        }
        self.task_states: Dict[str, TaskState] = {}

    def process_message(
        self,
        npc_id: str,
        relationship_stage: str,
        user_message: str,
        npc_display_name: str,
        npc_role: str,
        scene_title: str,
    ) -> Optional[TaskUpdateResult]:
        task = self.task_definitions.get(npc_id)
        if task is None:
            return None

        state = self.task_states.get(npc_id, TaskState(status="locked"))
        feedback = ""
        reward_affinity = 0
        completion_memory = ""

        if state.status == "locked" and self._is_unlocked(task.unlock_stage, relationship_stage):
            state.status = "available"
            feedback = f"New task unlocked: {self._get_title(npc_id, npc_display_name)}"

        lowered = user_message.lower()

        if state.status == "available" and self._contains_any(lowered, task.accept_keywords):
            state.status = "in_progress"
            feedback = f"Task accepted: {self._get_title(npc_id, npc_display_name)}"
        elif state.status == "in_progress" and self._contains_any(lowered, task.completion_keywords):
            state.status = "completed"
            reward_affinity = task.reward_affinity
            completion_memory = self._get_completion_memory(npc_id, npc_display_name, user_message)
            feedback = (
                f"Task completed: {self._get_title(npc_id, npc_display_name)}. "
                f"Affinity +{reward_affinity}"
            )

        self.task_states[npc_id] = state
        return TaskUpdateResult(
            status=state.status,
            title=self._get_title(npc_id, npc_display_name),
            description=self._get_description(npc_id, npc_display_name, npc_role, scene_title),
            feedback=feedback,
            reward_affinity=reward_affinity,
            completion_memory=completion_memory,
        )

    def get_task_view(
        self,
        npc_id: str,
        relationship_stage: str,
        npc_display_name: str,
        npc_role: str,
        scene_title: str,
    ) -> Optional[TaskUpdateResult]:
        task = self.task_definitions.get(npc_id)
        if task is None:
            return None

        state = self.task_states.get(npc_id, TaskState(status="locked"))
        if state.status == "locked" and self._is_unlocked(task.unlock_stage, relationship_stage):
            state.status = "available"
            self.task_states[npc_id] = state

        return TaskUpdateResult(
            status=state.status,
            title=self._get_title(npc_id, npc_display_name),
            description=self._get_description(npc_id, npc_display_name, npc_role, scene_title),
            feedback="",
            reward_affinity=0,
            completion_memory="",
        )

    def _get_title(self, npc_id: str, npc_display_name: str) -> str:
        titles = {
            "Alice": f"{npc_display_name}'s Signature Product",
            "Bob": f"{npc_display_name}'s Reading Plan",
            "Charlie": f"{npc_display_name}'s Patrol Motto",
        }
        return titles.get(npc_id, f"{npc_display_name}'s Task")

    def _get_description(self, npc_id: str, npc_display_name: str, npc_role: str, scene_title: str) -> str:
        descriptions = {
            "Alice": (
                f"In {scene_title}, help {npc_display_name} the {npc_role} choose what their stall should highlight. "
                "Reach the required relationship stage, say you want to help, then suggest what they should offer."
            ),
            "Bob": (
                f"Help {npc_display_name} the {npc_role} define a reading direction for curious visitors. "
                "Accept the task, then mention a topic or subject the library corner should focus on."
            ),
            "Charlie": (
                f"Help {npc_display_name} the {npc_role} craft a short patrol reminder for local safety. "
                "Accept the task, then offer a safety or patrol-themed phrase."
            ),
        }
        return descriptions.get(npc_id, f"Help {npc_display_name} with their current role in {scene_title}.")

    def _get_completion_memory(self, npc_id: str, npc_display_name: str, message: str) -> str:
        templates = {
            "Alice": f"The player helped {npc_display_name} settle on a signature product idea: '{message}'.",
            "Bob": f"The player helped {npc_display_name} choose a reading theme: '{message}'.",
            "Charlie": f"The player helped {npc_display_name} craft a patrol reminder: '{message}'.",
        }
        return templates.get(npc_id, f"The player helped {npc_display_name} with a task about '{message}'.")

    def _is_unlocked(self, required_stage: str, current_stage: str) -> bool:
        return self.STAGE_ORDER.get(current_stage, 0) >= self.STAGE_ORDER.get(required_stage, 0)

    def _contains_any(self, lowered_message: str, keywords: List[str]) -> bool:
        lowered_keywords = [keyword.lower() for keyword in keywords]
        return any(keyword in lowered_message for keyword in lowered_keywords)
