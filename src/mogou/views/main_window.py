from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    editor_changed = Signal()
    chat_send_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(900, 600)
        self.resize(1280, 800)
        self._close_requested: Callable[[], bool] = lambda: True
        self._build_menu()
        self._build_body()

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("文件")
        self.new_action = file_menu.addAction("新建")
        self.open_action = file_menu.addAction("打开…")
        self.save_action = file_menu.addAction("保存")
        self.save_as_action = file_menu.addAction("另存为…")
        file_menu.addSeparator()
        self.exit_action = file_menu.addAction("退出")

        edit_menu = menu.addMenu("编辑")
        self.undo_action = edit_menu.addAction("撤销")
        self.redo_action = edit_menu.addAction("重做")
        edit_menu.addSeparator()
        self.cut_action = edit_menu.addAction("剪切")
        self.copy_action = edit_menu.addAction("复制")
        self.paste_action = edit_menu.addAction("粘贴")
        self.select_all_action = edit_menu.addAction("全选")

        help_menu = menu.addMenu("帮助")
        self.about_action = help_menu.addAction("关于墨构")
        self.about_action.triggered.connect(self._show_about)

    def _build_body(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_navigation())

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("开始写作…")
        self.editor.textChanged.connect(self.editor_changed)
        splitter.addWidget(self.editor)
        splitter.addWidget(self._build_chat())
        splitter.setSizes([190, 770, 320])
        self.setCentralWidget(splitter)

        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_all_action.triggered.connect(self.editor.selectAll)

    def _build_navigation(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        self.navigation = QListWidget()
        self.navigation.addItems(["资料库", "人物", "世界观", "时间线", "设置"])
        self.navigation.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.navigation)
        return panel

    def _build_chat(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        self.chat_history = QPlainTextEdit(readOnly=True)
        self.chat_history.setPlaceholderText("与墨构助手对话…")
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息…")
        self.send_button = QPushButton("发送")
        row = QHBoxLayout()
        row.addWidget(self.chat_input)
        row.addWidget(self.send_button)
        layout.addWidget(self.chat_history)
        layout.addLayout(row)
        self.send_button.clicked.connect(self.chat_send_requested)
        self.chat_input.returnPressed.connect(self.chat_send_requested)
        return panel

    def editor_text(self) -> str:
        return self.editor.toPlainText()

    def set_editor_text(self, text: str) -> None:
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)

    def update_document_title(self, name: str, is_dirty: bool) -> None:
        marker = " *" if is_dirty else ""
        self.setWindowTitle(f"墨构（Mogou）— {name}{marker}")

    def choose_open_path(self) -> Path | None:
        filename, _ = QFileDialog.getOpenFileName(self, "打开 Markdown", "", "Markdown (*.md);;所有文件 (*)")
        return Path(filename) if filename else None

    def choose_save_path(self, suggested_name: str) -> Path | None:
        filename, _ = QFileDialog.getSaveFileName(self, "保存 Markdown", suggested_name, "Markdown (*.md)")
        return Path(filename) if filename else None

    def confirm_discard_changes(self, name: str) -> bool:
        answer = QMessageBox.question(
            self,
            "未保存的更改",
            f"“{name}”有未保存的更改。要放弃它们吗？",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Discard

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def chat_input_text(self) -> str:
        return self.chat_input.text()

    def clear_chat_input(self) -> None:
        self.chat_input.clear()

    def append_chat_message(self, role: str, content: str) -> None:
        prefix = "你" if role == "user" else "Echo"
        self.chat_history.appendPlainText(f"{prefix}：{content}")

    def set_close_requested_handler(self, handler: Callable[[], bool]) -> None:
        self._close_requested = handler

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._close_requested():
            event.accept()
        else:
            event.ignore()

    def _show_about(self) -> None:
        QMessageBox.about(self, "关于墨构", "墨构（Mogou）\n\n一个 local-first 的小说编辑器原型。\n当前 AI 对话为本地 Echo 占位服务。")
