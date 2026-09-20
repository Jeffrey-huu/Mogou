from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentModel:
    """Application state for one UTF-8 Markdown document."""

    path: Path | None = None
    content: str = ""
    is_dirty: bool = False

    @property
    def display_name(self) -> str:
        return self.path.name if self.path else "未命名文档"

    def set_content(self, content: str, *, mark_dirty: bool = True) -> None:
        if content != self.content:
            self.content = content
            if mark_dirty:
                self.is_dirty = True

    def new(self) -> None:
        self.path = None
        self.content = ""
        self.is_dirty = False

    def load(self, path: Path) -> None:
        self.path = path
        self.content = path.read_text(encoding="utf-8")
        self.is_dirty = False

    def save(self, path: Path | None = None) -> None:
        target = path or self.path
        if target is None:
            raise ValueError("A path is required to save an unnamed document.")
        target = target.with_suffix(".md") if not target.suffix else target
        target.write_text(self.content, encoding="utf-8")
        self.path = target
        self.is_dirty = False
