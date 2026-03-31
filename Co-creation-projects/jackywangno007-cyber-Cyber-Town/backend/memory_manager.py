from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List


@dataclass
class MemoryTurn:
    user_message: str
    npc_reply_memory: str


class ShortTermMemoryManager:
    def __init__(self, max_turns: int = 4):
        self.max_turns = max_turns
        self._memory: Dict[str, Deque[MemoryTurn]] = defaultdict(
            lambda: deque(maxlen=self.max_turns)
        )

    def get_recent_history(self, npc_name: str) -> List[MemoryTurn]:
        return list(self._memory[npc_name])

    def append_turn(self, npc_name: str, user_message: str, npc_reply_memory: str) -> None:
        self._memory[npc_name].append(
            MemoryTurn(user_message=user_message, npc_reply_memory=npc_reply_memory)
        )

    def get_turn_count(self, npc_name: str) -> int:
        return len(self._memory[npc_name])
