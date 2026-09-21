from pathlib import Path

from mogou.controllers.document import DocumentController, writing_units
from mogou.models.document import DocumentModel
from mogou.services.export import html_to_markdown, html_to_text


class FakeDocumentView:
    def __init__(self, html: str = "") -> None:
        self.html = html
        self.new_path: Path | None = None
        self.open_path: Path | None = None
        self.import_path: Path | None = None
        self.export_path: Path | None = None
        self.goal: int | None = None
        self.title: tuple[str, bool] | None = None
        self.stats: tuple[int, int, int, int] | None = None
        self.save_state = ""
        self.errors: list[tuple[str, str]] = []
        self.infos: list[tuple[str, str]] = []

    def editor_html(self) -> str: return self.html
    def set_editor_html(self, html: str) -> None: self.html = html
    def update_document_title(self, name: str, is_dirty: bool) -> None: self.title = (name, is_dirty)
    def update_statistics(self, today: int, goal: int, session_delta: int, seconds: int) -> None: self.stats = (today, goal, session_delta, seconds)
    def update_save_state(self, state: str) -> None: self.save_state = state
    def choose_new_workspace_path(self) -> Path | None: return self.new_path
    def choose_open_workspace_path(self) -> Path | None: return self.open_path
    def choose_import_path(self) -> Path | None: return self.import_path
    def choose_export_path(self, suffix: str) -> Path | None: return self.export_path
    def ask_daily_goal(self, current: int) -> int | None: return self.goal
    def show_error(self, title: str, message: str) -> None: self.errors.append((title, message))
    def show_info(self, title: str, message: str) -> None: self.infos.append((title, message))


def test_controller_creates_workspace_and_autosaves(tmp_path: Path, qtbot) -> None:
    view = FakeDocumentView()
    view.new_path = tmp_path / "novel"
    controller = DocumentController(DocumentModel(), view)

    assert controller.new_workspace()
    view.html = "<p>第一段</p>"
    controller.on_text_changed()
    qtbot.wait(DocumentController.AUTOSAVE_DELAY_MS + 100)
    assert (view.new_path / "manuscript.html").read_text(encoding="utf-8") == view.html
    assert view.save_state == "已保存"


def test_controller_imports_markdown_and_exports(tmp_path: Path, qapp) -> None:
    source = tmp_path / "source.md"
    source.write_text("# 标题\n\n**重要**", encoding="utf-8")
    view = FakeDocumentView()
    view.import_path = source
    view.new_path = tmp_path / "imported"
    controller = DocumentController(DocumentModel(), view)

    assert controller.import_document()
    assert "标题" in html_to_text(view.html)
    view.export_path = tmp_path / "export.md"
    assert controller.export_markdown()
    assert "标题" in view.export_path.read_text(encoding="utf-8")
    assert view.infos


def test_export_helpers_preserve_semantic_text() -> None:
    html = "<h1>标题</h1><p><b>重要</b>内容</p><ul><li>一项</li></ul>"
    markdown = html_to_markdown(html)
    assert "标题" in markdown and "重要" in markdown and "一项" in markdown
    assert html_to_text(html) == "标题\n重要内容\n一项"
    assert writing_units("<p>你 好\n世界</p>") == 4
