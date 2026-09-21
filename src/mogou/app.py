import sys

from PySide6.QtWidgets import QApplication

from mogou.controllers.chat import ChatController
from mogou.controllers.document import DocumentController
from mogou.models.chat import ChatModel
from mogou.models.document import DocumentModel
from mogou.services.chat import EchoChatService
from mogou.views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("墨构（Mogou）")
    window = MainWindow()

    document_controller = DocumentController(DocumentModel(), window)
    chat_controller = ChatController(ChatModel(), EchoChatService(), window)
    window.editor_changed.connect(document_controller.on_text_changed)
    window.editor_focus_lost.connect(document_controller.on_editor_focus_lost)
    window.new_workspace_action.triggered.connect(document_controller.new_workspace)
    window.open_workspace_action.triggered.connect(document_controller.open_workspace)
    window.import_action.triggered.connect(document_controller.import_document)
    window.save_action.triggered.connect(document_controller.save_workspace)
    window.export_markdown_action.triggered.connect(document_controller.export_markdown)
    window.export_text_action.triggered.connect(document_controller.export_text)
    window.daily_goal_action.triggered.connect(document_controller.set_daily_goal)
    window.focus_action.triggered.connect(window.toggle_focus_mode)
    window.focus_mode_changed.connect(document_controller.save_workspace)
    window.exit_action.triggered.connect(window.close)
    window.chat_send_requested.connect(chat_controller.send_message)
    window.set_close_requested_handler(document_controller.save_before_close)
    window.show()
    return app.exec()
