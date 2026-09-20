from pathlib import Path

from mogou.controllers.chat import ChatController
from mogou.controllers.document import DocumentController
from mogou.models.chat import ChatModel
from mogou.models.document import DocumentModel
from mogou.services.chat import EchoChatService


class FakeDocumentView:
    def __init__(self, text: str = "") -> None:
        self.text = text
        self.open_path: Path | None = None
        self.save_path: Path | None = None
        self.discard = True
        self.title: tuple[str, bool] | None = None
        self.errors: list[tuple[str, str]] = []

    def editor_text(self) -> str: return self.text
    def set_editor_text(self, text: str) -> None: self.text = text
    def update_document_title(self, name: str, is_dirty: bool) -> None: self.title = (name, is_dirty)
    def choose_open_path(self) -> Path | None: return self.open_path
    def choose_save_path(self, suggested_name: str) -> Path | None: return self.save_path
    def confirm_discard_changes(self, name: str) -> bool: return self.discard
    def show_error(self, title: str, message: str) -> None: self.errors.append((title, message))


class FakeChatView:
    def __init__(self, text: str) -> None:
        self.text = text
        self.messages: list[tuple[str, str]] = []

    def chat_input_text(self) -> str: return self.text
    def clear_chat_input(self) -> None: self.text = ""
    def append_chat_message(self, role: str, content: str) -> None: self.messages.append((role, content))


def test_document_controller_saves_unnamed_document(tmp_path: Path) -> None:
    view = FakeDocumentView("# 第一章\n正文")
    view.save_path = tmp_path / "novel.md"
    controller = DocumentController(DocumentModel(), view)

    assert controller.save_document()
    assert view.save_path.read_text(encoding="utf-8") == "# 第一章\n正文"
    assert controller.model.path == view.save_path


def test_document_controller_open_replaces_editor_text(tmp_path: Path) -> None:
    path = tmp_path / "opened.md"
    path.write_text("已打开内容", encoding="utf-8")
    view = FakeDocumentView()
    view.open_path = path
    controller = DocumentController(DocumentModel(), view)

    assert controller.open_document()
    assert view.text == "已打开内容"
    assert not controller.model.is_dirty


def test_new_document_respects_discard_decision() -> None:
    view = FakeDocumentView("草稿")
    view.discard = False
    controller = DocumentController(DocumentModel(content="草稿", is_dirty=True), view)
    assert not controller.new_document()
    assert controller.model.content == "草稿"


def test_chat_controller_rejects_blank_message() -> None:
    view = FakeChatView("  ")
    controller = ChatController(ChatModel(), EchoChatService(), view)
    assert not controller.send_message()
    assert view.messages == []


def test_chat_controller_adds_user_and_echo_messages() -> None:
    view = FakeChatView("你好")
    controller = ChatController(ChatModel(), EchoChatService(), view)
    assert controller.send_message()
    assert view.messages == [("user", "你好"), ("assistant", "Echo: 你好")]
