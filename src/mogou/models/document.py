from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class DocumentModel:
    """The local state of a single-document Mogou workspace."""

    workspace_path: Path | None = None
    html: str = ""
    name: str = "未命名工作区"
    daily_goal: int = 1000
    daily_progress: dict[str, int] = field(default_factory=dict)
    preferences: dict[str, object] = field(default_factory=lambda: {"font_size": 18})
    is_dirty: bool = False

    CONFIG_DIR = ".mogou"
    CONFIG_NAME = "workspace.json"
    MANUSCRIPT_NAME = "manuscript.html"

    @property
    def display_name(self) -> str:
        return self.name

    def create(self, path: Path, name: str | None = None) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.workspace_path = path
        self.name = name or path.name
        self.html = ""
        self.daily_goal = 1000
        self.daily_progress = {}
        self.preferences = {"font_size": 18}
        self.is_dirty = True
        self.save()

    def load(self, path: Path) -> None:
        config = json.loads((path / self.CONFIG_DIR / self.CONFIG_NAME).read_text(encoding="utf-8"))
        self.workspace_path = path
        self.name = str(config.get("name", path.name))
        self.daily_goal = int(config.get("daily_goal", 1000))
        self.daily_progress = {str(key): int(value) for key, value in config.get("daily_progress", {}).items()}
        self.preferences = dict(config.get("preferences", {"font_size": 18}))
        self.html = (path / self.MANUSCRIPT_NAME).read_text(encoding="utf-8")
        self.is_dirty = False

    def set_html(self, html: str, *, mark_dirty: bool = True) -> None:
        if html != self.html:
            self.html = html
            self.is_dirty = mark_dirty or self.is_dirty

    def add_words(self, delta: int, today: str | None = None) -> None:
        if delta > 0:
            key = today or date.today().isoformat()
            self.daily_progress[key] = self.daily_progress.get(key, 0) + delta
            self.is_dirty = True

    def today_words(self, today: str | None = None) -> int:
        return self.daily_progress.get(today or date.today().isoformat(), 0)

    def set_daily_goal(self, goal: int) -> None:
        self.daily_goal = max(0, goal)
        self.is_dirty = True

    def save(self) -> None:
        if self.workspace_path is None:
            raise ValueError("A workspace is required to save.")
        config_path = self.workspace_path / self.CONFIG_DIR / self.CONFIG_NAME
        manuscript_path = self.workspace_path / self.MANUSCRIPT_NAME
        config_path.parent.mkdir(parents=True, exist_ok=True)
        manuscript_path.write_text(self.html, encoding="utf-8")
        payload = {"name": self.name, "daily_goal": self.daily_goal, "daily_progress": self.daily_progress, "preferences": self.preferences}
        config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.is_dirty = False
