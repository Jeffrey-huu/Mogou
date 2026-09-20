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
    window.new_action.triggered.connect(document_controller.new_document)
    window.open_action.triggered.connect(document_controller.open_document)
    window.save_action.triggered.connect(document_controller.save_document)
    window.save_as_action.triggered.connect(document_controller.save_document_as)
    window.exit_action.triggered.connect(window.close)
    window.chat_send_requested.connect(chat_controller.send_message)
    window.set_close_requested_handler(document_controller.may_discard_changes)
    window.show()
    return app.exec()
