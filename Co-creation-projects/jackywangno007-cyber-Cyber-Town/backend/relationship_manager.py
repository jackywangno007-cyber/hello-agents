from collections import defaultdict
from typing import Dict, Tuple


class RelationshipManager:
    def __init__(self, default_score: int = 50, min_score: int = 0, max_score: int = 100):
        self.default_score = default_score
        self.min_score = min_score
        self.max_score = max_score
        self.relationships: Dict[str, int] = defaultdict(lambda: self.default_score)

        self.positive_keywords = [
            "谢谢",
            "感谢",
            "喜欢",
            "很棒",
            "不错",
            "厉害",
            "帮助",
            "请教",
            "拜托",
            "开心",
            "thank",
            "thanks",
            "great",
            "good",
            "awesome",
            "helpful",
        ]
        self.negative_keywords = [
            "讨厌",
            "糟糕",
            "无聊",
            "差",
            "笨",
            "烦",
            "闭嘴",
            "滚",
            "失望",
            "骗子",
            "hate",
            "bad",
            "stupid",
            "annoying",
            "useless",
            "shut up",
        ]

    def get_score(self, npc_name: str) -> int:
        return self.relationships[npc_name]

    def update_score(self, npc_name: str, user_message: str) -> Tuple[int, int]:
        current_score = self.relationships[npc_name]
        delta = self._calculate_delta(user_message)
        next_score = max(self.min_score, min(self.max_score, current_score + delta))
        self.relationships[npc_name] = next_score
        return next_score, delta

    def adjust_score(self, npc_name: str, delta: int) -> int:
        current_score = self.relationships[npc_name]
        next_score = max(self.min_score, min(self.max_score, current_score + delta))
        self.relationships[npc_name] = next_score
        return next_score

    def get_stage(self, score: int) -> str:
        if score >= 80:
            return "trusted"
        if score >= 60:
            return "warm"
        if score >= 40:
            return "neutral"
        if score >= 20:
            return "guarded"
        return "cold"

    def get_stage_description(self, score: int) -> str:
        stage = self.get_stage(score)
        descriptions = {
            "trusted": "The NPC feels close to the player, speaks openly, and is eager to help.",
            "warm": "The NPC is friendly, patient, and willing to share more.",
            "neutral": "The NPC is polite and balanced, without strong trust or dislike.",
            "guarded": "The NPC is cautious, a bit distant, and does not open up easily.",
            "cold": "The NPC is defensive, terse, and emotionally distant.",
        }
        return descriptions[stage]

    def _calculate_delta(self, user_message: str) -> int:
        lowered = user_message.lower()

        positive_hits = sum(1 for keyword in self.positive_keywords if keyword in lowered)
        negative_hits = sum(1 for keyword in self.negative_keywords if keyword in lowered)

        if positive_hits > negative_hits:
            return min(positive_hits * 6, 12)
        if negative_hits > positive_hits:
            return -min(negative_hits * 8, 16)
        return 0
