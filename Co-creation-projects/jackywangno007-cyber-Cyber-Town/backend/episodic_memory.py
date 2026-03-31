import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Set


@dataclass
class EpisodicMemoryItem:
    summary: str
    source_user_message: str
    keywords: List[str]


class EpisodicMemoryManager:
    def __init__(self, data_dir: Path, max_items_per_npc: int = 50):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_items_per_npc = max_items_per_npc

    def save_memory_if_important(
        self,
        npc_name: str,
        user_message: str,
        npc_reply: str,
    ) -> bool:
        if not self._is_important(user_message):
            return False

        item = EpisodicMemoryItem(
            summary=self._build_summary(user_message, npc_reply),
            source_user_message=user_message,
            keywords=sorted(self._extract_keywords(user_message)),
        )

        memory_items = self._load_npc_memory(npc_name)
        memory_items.append(item)
        memory_items = memory_items[-self.max_items_per_npc :]
        self._save_npc_memory(npc_name, memory_items)
        return True

    def save_manual_memory(self, npc_name: str, source_user_message: str, summary: str) -> None:
        item = EpisodicMemoryItem(
            summary=summary,
            source_user_message=source_user_message,
            keywords=sorted(self._extract_keywords(source_user_message)),
        )
        memory_items = self._load_npc_memory(npc_name)
        memory_items.append(item)
        memory_items = memory_items[-self.max_items_per_npc :]
        self._save_npc_memory(npc_name, memory_items)

    def search_relevant_memories(
        self,
        npc_name: str,
        user_message: str,
        top_k: int = 3,
    ) -> List[EpisodicMemoryItem]:
        query_keywords = self._extract_keywords(user_message)
        if not query_keywords:
            return []

        scored_items = []
        for item in self._load_npc_memory(npc_name):
            overlap = query_keywords.intersection(set(item.keywords))
            if overlap:
                scored_items.append((len(overlap), item))

        scored_items.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]

    def get_recent_summaries(self, npc_name: str, limit: int = 3) -> List[str]:
        memory_items = self._load_npc_memory(npc_name)
        return [item.summary for item in memory_items[-limit:]]

    def get_memory_count(self, npc_name: str) -> int:
        return len(self._load_npc_memory(npc_name))

    def _npc_file(self, npc_name: str) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", npc_name)
        return self.data_dir / f"{safe_name}.json"

    def _load_npc_memory(self, npc_name: str) -> List[EpisodicMemoryItem]:
        file_path = self._npc_file(npc_name)
        if not file_path.exists():
            return []

        raw_items = json.loads(file_path.read_text(encoding="utf-8"))
        return [EpisodicMemoryItem(**item) for item in raw_items]

    def _save_npc_memory(self, npc_name: str, memory_items: List[EpisodicMemoryItem]) -> None:
        file_path = self._npc_file(npc_name)
        file_path.write_text(
            json.dumps([asdict(item) for item in memory_items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _is_important(self, user_message: str) -> bool:
        lowered = user_message.lower()
        important_keywords = [
            "记住",
            "不要忘",
            "我是",
            "我叫",
            "我的名字",
            "我喜欢",
            "我讨厌",
            "我的目标",
            "我计划",
            "remember",
            "my name",
            "i am",
            "i'm",
            "i like",
            "i hate",
            "my goal",
            "my plan",
            "birthday",
            "family",
            "work",
            "study",
        ]
        return len(user_message.strip()) >= 8 or any(keyword in lowered for keyword in important_keywords)

    def _build_summary(self, user_message: str, npc_reply: str) -> str:
        reply_preview = npc_reply.strip().replace("\n", " ")
        if len(reply_preview) > 120:
            reply_preview = reply_preview[:117] + "..."
        return (
            f"The player shared this important detail: '{user_message}'. "
            f"The NPC responded with: '{reply_preview}'."
        )

    def _extract_keywords(self, text: str) -> Set[str]:
        normalized = text.lower()
        latin_tokens = set(re.findall(r"[a-z0-9_]{2,}", normalized))
        cjk_chunks = set(re.findall(r"[\u4e00-\u9fff]{2,}", text))
        return latin_tokens.union(cjk_chunks)
