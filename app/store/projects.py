"""On-disk JSON project files + recent-projects index."""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.config import AppConfig, get_config
from app.models import Project


class ProjectStore:
    def __init__(self, cfg: AppConfig | None = None):
        self.cfg = cfg or get_config()

    @property
    def root(self) -> Path:
        return self.cfg.projects_path

    @property
    def recent_path(self) -> Path:
        return self.root / "_recent.json"

    def list_projects(self) -> list[Path]:
        return sorted(
            (p for p in self.root.glob("*.json") if not p.name.startswith("_")),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def save(self, project: Project) -> Path:
        project.updated_at = time.time()
        if not project.created_at:
            project.created_at = project.updated_at
        path = self.root / f"{project.id}.json"
        path.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")
        self._touch_recent(project, path)
        return path

    def load(self, path: str | Path) -> Project:
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        proj = Project.from_dict(data)
        self._touch_recent(proj, p)
        return proj

    def delete(self, project_id: str) -> bool:
        path = self.root / f"{project_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def recent(self, limit: int = 10) -> list[dict]:
        if not self.recent_path.exists():
            return []
        try:
            data = json.loads(self.recent_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data[:limit]

    def _touch_recent(self, project: Project, path: Path) -> None:
        entries = self.recent(limit=50)
        entries = [e for e in entries if e.get("id") != project.id]
        entries.insert(0, {
            "id": project.id,
            "name": project.name,
            "path": str(path),
            "updated_at": project.updated_at,
        })
        self.recent_path.write_text(json.dumps(entries[:50], indent=2), encoding="utf-8")
