from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4


class MemoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def all(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            data = []
        return data if isinstance(data, list) else []

    def _write(self, items: list[dict]) -> None:
        self.path.write_text(json.dumps(items, indent=2), encoding='utf-8')

    def add(self, text: str) -> dict:
        item = {
            'id': str(uuid4()),
            'text': text.strip(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        items = self.all()
        items.append(item)
        self._write(items)
        return item

    def search(self, query: str, limit: int = 5) -> list[dict]:
        terms = [part.lower() for part in query.split() if part.strip()]
        if not terms:
            return self.all()[-limit:]

        scored = []
        for item in self.all():
            text = str(item.get('text', '')).lower()
            score = sum(1 for term in terms if term in text)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]
