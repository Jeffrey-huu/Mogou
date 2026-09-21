from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QTimer

from mogou.models.document import DocumentModel
from mogou.services.export import html_to_markdown, html_to_text, markdown_to_html, text_to_html


def writing_units(html: str) -> int:
    """Count visible non-whitespace characters, suitable for Chinese and spaced prose."""
    return len("".join(html_to_text(html).split()))


class DocumentView(Protocol):
    def editor_html(self) -> str: ...
    def set_editor_html(self, html: str) -> None: ...
    def update_document_title(self, name: str, is_dirty: bool) -> None: ...
    def update_statistics(self, today: int, goal: int, session_delta: int, seconds: int) -> None: ...
    def update_save_state(self, state: str) -> None: ...
    def choose_new_workspace_path(self) -> Path | None: ...
    def choose_open_workspace_path(self) -> Path | None: ...
    def choose_import_path(self) -> Path | None: ...
    def choose_export_path(self, suffix: str) -> Path | None: ...
    def ask_daily_goal(self, current: int) -> int | None: ...
    def show_error(self, title: str, message: str) -> None: ...
    def show_info(self, title: str, message: str) -> None: ...


class DocumentController:
    AUTOSAVE_DELAY_MS = 800

    def __init__(self, model: DocumentModel, view: DocumentView) -> None:
        self.model = model
        self.view = view
        self._previous_units = 0
        self._session_start_units = 0
        self._session_started_at = time.monotonic()
        self._autosave_timer = QTimer()
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.timeout.connect(self.save_workspace)
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self.refresh_statistics)
        self._stats_timer.start(1000)
        self.refresh_title()
        self.refresh_statistics()
        self.view.update_save_state("新建或打开工作区后自动保存")

    def refresh_title(self) -> None:
        self.view.update_document_title(self.model.display_name, self.model.is_dirty)

    def refresh_statistics(self) -> None:
        seconds = int(time.monotonic() - self._session_started_at)
        self.view.update_statistics(self.model.today_words(), self.model.daily_goal, writing_units(self.model.html) - self._session_start_units, seconds)

    def _begin_session(self) -> None:
        self._previous_units = writing_units(self.model.html)
        self._session_start_units = self._previous_units
        self._session_started_at = time.monotonic()
        self.refresh_statistics()

    def on_text_changed(self) -> None:
        html = self.view.editor_html()
        units = writing_units(html)
        self.model.set_html(html)
        self.model.add_words(units - self._previous_units)
        self._previous_units = units
        self.refresh_title()
        self.refresh_statistics()
        if self.model.workspace_path is not None:
            self.view.update_save_state("正在保存…")
            self._autosave_timer.start(self.AUTOSAVE_DELAY_MS)
        else:
            self.view.update_save_state("未保存：请先新建工作区")

    def new_workspace(self) -> bool:
        if not self.save_workspace():
            return False
        path = self.view.choose_new_workspace_path()
        if path is None:
            return False
        try:
            self.model.create(path)
        except OSError as error:
            self.view.show_error("无法创建工作区", str(error))
            return False
        self.view.set_editor_html("")
        self._begin_session()
        self.refresh_title()
        self.view.update_save_state("已保存")
        return True

    def open_workspace(self) -> bool:
        if not self.save_workspace():
            return False
        path = self.view.choose_open_workspace_path()
        if path is None:
            return False
        try:
            self.model.load(path)
        except (OSError, ValueError, TypeError) as error:
            self.view.show_error("无法打开工作区", f"这不是有效的墨构工作区：{error}")
            return False
        self.view.set_editor_html(self.model.html)
        self._begin_session()
        self.refresh_title()
        self.view.update_save_state("已保存")
        return True

    def import_document(self) -> bool:
        path = self.view.choose_import_path()
        if path is None:
            return False
        workspace = self.view.choose_new_workspace_path()
        if workspace is None:
            return False
        try:
            source = path.read_text(encoding="utf-8")
            html = markdown_to_html(source) if path.suffix.lower() == ".md" else text_to_html(source)
            self.model.create(workspace, workspace.name)
            self.model.set_html(html)
            self.model.save()
        except OSError as error:
            self.view.show_error("无法导入文件", str(error))
            return False
        self.view.set_editor_html(self.model.html)
        self._begin_session()
        self.refresh_title()
        self.view.update_save_state("已保存")
        return True

    def save_workspace(self) -> bool:
        self._autosave_timer.stop()
        if self.model.workspace_path is None:
            return True
        self.model.set_html(self.view.editor_html())
        try:
            self.model.save()
        except OSError as error:
            self.view.update_save_state("保存失败")
            self.view.show_error("无法保存工作区", str(error))
            return False
        self.refresh_title()
        self.refresh_statistics()
        self.view.update_save_state("已保存")
        return True

    def export_markdown(self) -> bool:
        return self._export(".md", html_to_markdown, "Markdown 已导出。字体、颜色和对齐等显示样式未包含在导出文件中。")

    def export_text(self) -> bool:
        return self._export(".txt", html_to_text, "纯文本已导出。富文本样式未包含在导出文件中。")

    def _export(self, suffix: str, formatter, message: str) -> bool:
        if self.model.workspace_path is None:
            self.view.show_error("尚未创建工作区", "请先新建或打开工作区。")
            return False
        path = self.view.choose_export_path(suffix)
        if path is None:
            return False
        try:
            path.with_suffix(suffix).write_text(formatter(self.view.editor_html()), encoding="utf-8")
        except OSError as error:
            self.view.show_error("无法导出文件", str(error))
            return False
        self.view.show_info("导出完成", message)
        return True

    def set_daily_goal(self) -> None:
        goal = self.view.ask_daily_goal(self.model.daily_goal)
        if goal is not None:
            self.model.set_daily_goal(goal)
            self.refresh_statistics()
            self._autosave_timer.start(self.AUTOSAVE_DELAY_MS)

    def on_editor_focus_lost(self) -> None:
        self.save_workspace()

    def save_before_close(self) -> bool:
        return self.save_workspace()
