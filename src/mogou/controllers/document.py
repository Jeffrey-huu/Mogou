from pathlib import Path
from typing import Protocol

from mogou.models.document import DocumentModel


class DocumentView(Protocol):
    def editor_text(self) -> str: ...
    def set_editor_text(self, text: str) -> None: ...
    def update_document_title(self, name: str, is_dirty: bool) -> None: ...
    def choose_open_path(self) -> Path | None: ...
    def choose_save_path(self, suggested_name: str) -> Path | None: ...
    def confirm_discard_changes(self, name: str) -> bool: ...
    def show_error(self, title: str, message: str) -> None: ...


class DocumentController:
    def __init__(self, model: DocumentModel, view: DocumentView) -> None:
        self.model = model
        self.view = view
        self.refresh_title()

    def refresh_title(self) -> None:
        self.view.update_document_title(self.model.display_name, self.model.is_dirty)

    def on_text_changed(self) -> None:
        self.model.set_content(self.view.editor_text())
        self.refresh_title()

    def may_discard_changes(self) -> bool:
        return not self.model.is_dirty or self.view.confirm_discard_changes(self.model.display_name)

    def new_document(self) -> bool:
        if not self.may_discard_changes():
            return False
        self.model.new()
        self.view.set_editor_text("")
        self.refresh_title()
        return True

    def open_document(self) -> bool:
        if not self.may_discard_changes():
            return False
        path = self.view.choose_open_path()
        if path is None:
            return False
        try:
            self.model.load(path)
        except OSError as error:
            self.view.show_error("无法打开文件", str(error))
            return False
        self.view.set_editor_text(self.model.content)
        self.refresh_title()
        return True

    def save_document(self) -> bool:
        if self.model.path is None:
            return self.save_document_as()
        return self._save_to(self.model.path)

    def save_document_as(self) -> bool:
        path = self.view.choose_save_path(self.model.display_name)
        return False if path is None else self._save_to(path)

    def _save_to(self, path: Path) -> bool:
        self.model.set_content(self.view.editor_text())
        try:
            self.model.save(path)
        except OSError as error:
            self.view.show_error("无法保存文件", str(error))
            return False
        self.refresh_title()
        return True
