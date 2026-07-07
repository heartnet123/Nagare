from __future__ import annotations

from pathlib import Path


class SkillsStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict]:
        skills = []
        for path in sorted(self.root.glob('*.md')):
            content = path.read_text(encoding='utf-8')
            title = path.stem
            for line in content.splitlines():
                if line.startswith('#'):
                    title = line.lstrip('#').strip() or title
                    break
            skills.append({'name': path.stem, 'title': title})
        return skills

    def read(self, name: str) -> str:
        safe_name = Path(name).stem
        path = self.root / f'{safe_name}.md'
        if not path.exists():
            raise FileNotFoundError(f'skill not found: {safe_name}')
        return path.read_text(encoding='utf-8')
