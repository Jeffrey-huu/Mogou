from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabBar,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class WritingTextEdit(QTextEdit):
    focus_lost = Signal()

    def focusOutEvent(self, event) -> None:  # type: ignore[override]
        super().focusOutEvent(event)
        self.focus_lost.emit()


class MainWindow(QMainWindow):
    editor_changed = Signal()
    focus_mode_changed = Signal()
    chat_send_requested = Signal()

    COLLAPSED_LEFT_WIDTH = 48
    LEFT_MIN_WIDTH = 220
    EDITOR_MIN_WIDTH = 520
    RIGHT_MIN_WIDTH = 280

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(1036, 640)
        self.resize(1180, 800)
        self._close_requested: Callable[[], bool] = lambda: True
        self._focus_mode = False
        self._style_path = Path(__file__).with_name("editor.qss")
        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_status()
        self.setStyleSheet(self._style_path.read_text(encoding="utf-8"))

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件")
        self.new_workspace_action = file_menu.addAction("新建工作区…")
        self.open_workspace_action = file_menu.addAction("打开工作区…")
        self.import_action = file_menu.addAction("导入 Markdown / TXT…")
        file_menu.addSeparator()
        self.save_action = file_menu.addAction("立即保存")
        self.export_markdown_action = file_menu.addAction("导出 Markdown…")
        self.export_text_action = file_menu.addAction("导出 TXT…")
        file_menu.addSeparator()
        self.exit_action = file_menu.addAction("退出")

        edit_menu = self.menuBar().addMenu("编辑")
        self.undo_action = edit_menu.addAction("撤销")
        self.redo_action = edit_menu.addAction("重做")
        edit_menu.addSeparator()
        self.cut_action = edit_menu.addAction("剪切")
        self.copy_action = edit_menu.addAction("复制")
        self.paste_action = edit_menu.addAction("粘贴")
        self.select_all_action = edit_menu.addAction("全选")
        edit_menu.addSeparator()
        self.find_action = edit_menu.addAction("查找")
        self.replace_action = edit_menu.addAction("替换")

        writing_menu = self.menuBar().addMenu("写作")
        self.daily_goal_action = writing_menu.addAction("设置每日目标…")
        self.focus_action = writing_menu.addAction("进入专注模式")
        self.focus_action.setShortcut(QKeySequence("F11"))
        self.focus_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.addAction(self.focus_action)
        self.focus_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        self.focus_shortcut.activated.connect(self.toggle_focus_mode)

        help_menu = self.menuBar().addMenu("帮助")
        self.about_action = help_menu.addAction("关于墨构")
        self.about_action.triggered.connect(self._show_about)

    def _build_toolbar(self) -> None:
        self.toolbar = QToolBar("写作工具", self)
        self.toolbar.setMovable(False)
        self.toolbar.setObjectName("editorToolbar")
        self.toolbar.addAction(self.undo_action)
        self.toolbar.addAction(self.redo_action)
        self.toolbar.addSeparator()

        self.normal_action = self.toolbar.addAction("正文")
        self.heading_one_action = self.toolbar.addAction("标题 1")
        self.heading_two_action = self.toolbar.addAction("标题 2")
        self.quote_action = self.toolbar.addAction("引用")
        self.toolbar.addSeparator()
        self.bold_action = self.toolbar.addAction("粗体")
        self.italic_action = self.toolbar.addAction("斜体")
        self.strike_action = self.toolbar.addAction("删除线")
        self.toolbar.addSeparator()
        self.align_left_action = self.toolbar.addAction("左对齐")
        self.align_center_action = self.toolbar.addAction("居中")
        self.align_right_action = self.toolbar.addAction("右对齐")
        self.bullet_action = self.toolbar.addAction("无序列表")
        self.number_action = self.toolbar.addAction("有序列表")
        self.rule_action = self.toolbar.addAction("分隔线")
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.find_action)
        self.toolbar.addAction(self.focus_action)

    def _build_body(self) -> None:
        self.body_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_sidebar = self._build_left_sidebar()
        self.editor_panel = self._build_editor_panel()
        self.right_sidebar = self._build_chat_sidebar()
        self.editor_panel.setMinimumWidth(self.EDITOR_MIN_WIDTH)
        self.body_splitter.addWidget(self.left_sidebar)
        self.body_splitter.addWidget(self.editor_panel)
        self.body_splitter.addWidget(self.right_sidebar)
        self.body_splitter.setSizes([230, 770, 330])
        self.body_splitter.setStretchFactor(0, 0)
        self.body_splitter.setStretchFactor(1, 1)
        self.body_splitter.setStretchFactor(2, 0)
        self.body_splitter.setChildrenCollapsible(False)
        self.setCentralWidget(self.body_splitter)

    def _build_left_sidebar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("leftSidebar")
        panel.setMinimumWidth(self.LEFT_MIN_WIDTH)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(44)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 2, 0, 12)
        self.left_brand = QLabel("墨构")
        self.left_brand.setObjectName("brand")
        self.collapse_left_button = QPushButton("‹")
        self.collapse_left_button.setObjectName("collapseButton")
        self.collapse_left_button.setFixedSize(30, 30)
        header_layout.addWidget(self.left_brand)
        header_layout.addStretch(1)
        header_layout.addWidget(self.collapse_left_button)
        layout.addWidget(header)

        self.left_content = QWidget()
        content_layout = QVBoxLayout(self.left_content)
        content_layout.setContentsMargins(6, 0, 6, 0)
        content_layout.setSpacing(8)

        self.left_tabs = QTabBar()
        self.left_tabs.setObjectName("leftTabs")
        self.left_tabs.setExpanding(True)
        self.left_tabs.addTab("资料库")
        self.left_tabs.addTab("设置")
        content_layout.addWidget(self.left_tabs)

        self.left_pages = QStackedWidget()
        self.left_pages.setObjectName("leftPages")
        library_page = QWidget()
        library_layout = QVBoxLayout(library_page)
        library_layout.setContentsMargins(0, 8, 0, 0)
        library_layout.setSpacing(6)
        library_title = QLabel("创作资料")
        library_title.setObjectName("sectionTitle")
        library_layout.addWidget(library_title)
        library_empty = QFrame()
        library_empty.setObjectName("libraryEmpty")
        empty_layout = QVBoxLayout(library_empty)
        empty_layout.setContentsMargins(14, 20, 14, 20)
        empty_icon = QLabel("◇")
        empty_icon.setObjectName("emptyIcon")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_title = QLabel("资料库尚未建立")
        empty_title.setObjectName("emptyTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_description = QLabel("后续将在这里管理人物、设定、素材，\n并为 RAG 检索提供内容来源。")
        empty_description.setObjectName("emptyDescription")
        empty_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_description.setWordWrap(True)
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_description)
        library_layout.addWidget(library_empty)
        library_layout.addStretch(1)

        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(0, 8, 0, 0)
        settings_layout.setSpacing(6)
        settings_title = QLabel("写作设置")
        settings_title.setObjectName("sectionTitle")
        settings_layout.addWidget(settings_title)
        self.goal_button = QPushButton("◎  每日目标")
        self.focus_button = QPushButton("□  专注模式")
        for button in (self.goal_button, self.focus_button):
            button.setMinimumHeight(38)
            settings_layout.addWidget(button)
        settings_layout.addStretch(1)
        settings_hint = QLabel("主题、字体与段落偏好将在这里配置")
        settings_hint.setObjectName("sideHint")
        settings_hint.setWordWrap(True)
        settings_layout.addWidget(settings_hint)

        self.left_pages.addWidget(library_page)
        self.left_pages.addWidget(settings_page)
        self.left_tabs.currentChanged.connect(self.left_pages.setCurrentIndex)
        content_layout.addWidget(self.left_pages, 1)
        layout.addWidget(self.left_content, 1)

        self._left_expanded = True
        self._expanded_left_width = max(self.LEFT_MIN_WIDTH, 230)
        self.collapse_left_button.clicked.connect(self.toggle_left_sidebar)
        self.goal_button.clicked.connect(self.daily_goal_action.trigger)
        self.focus_button.clicked.connect(self.focus_action.trigger)
        return panel

    def _build_chat_sidebar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("rightSidebar")
        panel.setMinimumWidth(self.RIGHT_MIN_WIDTH)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        title = QLabel("对话")
        title.setObjectName("panelTitle")
        note = QLabel("和墨构一起推敲这一段文字")
        note.setObjectName("panelNote")

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("chatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_messages = QWidget()
        self.chat_messages.setObjectName("chatMessages")
        self.chat_messages_layout = QVBoxLayout(self.chat_messages)
        self.chat_messages_layout.setContentsMargins(8, 10, 8, 10)
        self.chat_messages_layout.setSpacing(10)
        self.chat_messages_layout.addStretch(1)
        self.chat_scroll.setWidget(self.chat_messages)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入一句话…")
        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("sendButton")
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(self.chat_input, 1)
        row.addWidget(self.send_button)
        layout.addWidget(title)
        layout.addWidget(note)
        layout.addWidget(self.chat_scroll, 1)
        layout.addLayout(row)
        self.send_button.clicked.connect(self.chat_send_requested)
        self.chat_input.returnPressed.connect(self.chat_send_requested)
        return panel

    def _build_editor_panel(self) -> QWidget:
        central = QWidget()
        central.setObjectName("editorPanel")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.toolbar)

        self.find_bar = QFrame()
        find_layout = QHBoxLayout(self.find_bar)
        find_layout.setContentsMargins(22, 8, 22, 8)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("查找")
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("替换为")
        self.find_next_button = QPushButton("下一个")
        self.replace_button = QPushButton("替换")
        self.replace_all_button = QPushButton("全部替换")
        self.close_find_button = QPushButton("×")
        for widget in (self.find_input, self.replace_input, self.find_next_button, self.replace_button, self.replace_all_button, self.close_find_button):
            find_layout.addWidget(widget)
        self.find_bar.hide()
        layout.addWidget(self.find_bar)

        self.editor = WritingTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText("让第一个句子落下来。")
        self.editor.document().setDocumentMargin(48)
        layout.addWidget(self.editor, 1)
        self.editor.textChanged.connect(self.editor_changed)
        self.editor.focus_lost.connect(lambda: self.editor_focus_lost.emit())
        self._connect_editor_actions()
        self.find_next_button.clicked.connect(self._find_next)
        self.find_input.returnPressed.connect(self._find_next)
        self.replace_button.clicked.connect(self._replace_one)
        self.replace_all_button.clicked.connect(self._replace_all)
        self.close_find_button.clicked.connect(self._hide_find)
        return central

    editor_focus_lost = Signal()

    def _build_status(self) -> None:
        self.save_state_label = QLineEdit("尚未保存")
        self.save_state_label.setReadOnly(True)
        self.save_state_label.setObjectName("saveState")
        self.stats_label = QLineEdit("今日 0 / 1000 字  ·  本次 +0 字  ·  00:00")
        self.stats_label.setReadOnly(True)
        self.stats_label.setObjectName("stats")
        self.statusBar().addPermanentWidget(self.save_state_label)
        self.statusBar().addPermanentWidget(self.stats_label)

    def _connect_editor_actions(self) -> None:
        self.undo_action.triggered.connect(self.editor.undo)
        self.redo_action.triggered.connect(self.editor.redo)
        self.cut_action.triggered.connect(self.editor.cut)
        self.copy_action.triggered.connect(self.editor.copy)
        self.paste_action.triggered.connect(self.editor.paste)
        self.select_all_action.triggered.connect(self.editor.selectAll)
        self.find_action.triggered.connect(lambda: self._show_find(False))
        self.replace_action.triggered.connect(lambda: self._show_find(True))
        self.normal_action.triggered.connect(lambda: self._set_block_style("normal"))
        self.heading_one_action.triggered.connect(lambda: self._set_block_style("h1"))
        self.heading_two_action.triggered.connect(lambda: self._set_block_style("h2"))
        self.quote_action.triggered.connect(lambda: self._set_block_style("quote"))
        self.bold_action.triggered.connect(lambda: self._toggle_char_format("bold"))
        self.italic_action.triggered.connect(lambda: self._toggle_char_format("italic"))
        self.strike_action.triggered.connect(lambda: self._toggle_char_format("strike"))
        self.align_left_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft))
        self.align_center_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignHCenter))
        self.align_right_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight))
        self.bullet_action.triggered.connect(lambda: self._insert_list(QTextListFormat.Style.ListDisc))
        self.number_action.triggered.connect(lambda: self._insert_list(QTextListFormat.Style.ListDecimal))
        self.rule_action.triggered.connect(self._insert_rule)

    def _set_block_style(self, style: str) -> None:
        cursor = self.editor.textCursor()
        block_format = cursor.blockFormat()
        char_format = QTextCharFormat()
        if style == "h1":
            block_format.setHeadingLevel(1)
            char_format.setFontPointSize(24)
            char_format.setFontWeight(700)
            block_format.setTopMargin(20)
            block_format.setBottomMargin(8)
        elif style == "h2":
            block_format.setHeadingLevel(2)
            char_format.setFontPointSize(20)
            char_format.setFontWeight(700)
            block_format.setTopMargin(16)
            block_format.setBottomMargin(6)
        elif style == "quote":
            block_format.setHeadingLevel(0)
            block_format.setLeftMargin(28)
            block_format.setTopMargin(6)
            block_format.setBottomMargin(6)
            char_format.setFontItalic(True)
        else:
            block_format.setHeadingLevel(0)
            block_format.setLeftMargin(0)
            block_format.setTopMargin(0)
            block_format.setBottomMargin(8)
            char_format.setFontPointSize(18)
            char_format.setFontWeight(400)
            char_format.setFontItalic(False)
        cursor.mergeBlockFormat(block_format)
        cursor.mergeCharFormat(char_format)
        self.editor.setTextCursor(cursor)

    def _toggle_char_format(self, kind: str) -> None:
        cursor = self.editor.textCursor()
        current = cursor.charFormat()
        format_ = QTextCharFormat()
        if kind == "bold":
            format_.setFontWeight(400 if current.fontWeight() >= 700 else 700)
        elif kind == "italic":
            format_.setFontItalic(not current.fontItalic())
        else:
            format_.setFontStrikeOut(not current.fontStrikeOut())
        cursor.mergeCharFormat(format_)
        self.editor.mergeCurrentCharFormat(format_)

    def _insert_list(self, style: QTextListFormat.Style) -> None:
        self.editor.textCursor().createList(style)

    def _insert_rule(self) -> None:
        cursor = self.editor.textCursor()
        cursor.insertText("\n────────────────\n")

    def _show_find(self, with_replace: bool) -> None:
        self.find_bar.show()
        self.replace_input.setVisible(with_replace)
        self.replace_button.setVisible(with_replace)
        self.replace_all_button.setVisible(with_replace)
        self.find_input.setFocus()

    def _hide_find(self) -> None:
        self.find_bar.hide()
        self.editor.setFocus()

    def _find_next(self) -> bool:
        found = self.editor.find(self.find_input.text())
        if not found:
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(self.find_input.text())
        return found

    def _replace_one(self) -> None:
        cursor = self.editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == self.find_input.text():
            cursor.insertText(self.replace_input.text())
        self._find_next()

    def _replace_all(self) -> None:
        needle = self.find_input.text()
        if not needle:
            return
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        while self.editor.find(needle):
            self.editor.textCursor().insertText(self.replace_input.text())
        cursor.endEditBlock()

    def editor_html(self) -> str:
        return self.editor.toHtml()

    def set_editor_html(self, html: str) -> None:
        self.editor.blockSignals(True)
        self.editor.setHtml(html)
        self.editor.blockSignals(False)

    def chat_input_text(self) -> str:
        return self.chat_input.text()

    def clear_chat_input(self) -> None:
        self.chat_input.clear()

    def append_chat_message(self, role: str, content: str) -> None:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        bubble = QLabel(content)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(260)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if role == "user":
            bubble.setObjectName("chatBubbleUser")
            row_layout.addStretch(1)
            row_layout.addWidget(bubble)
        else:
            bubble.setObjectName("chatBubbleAssistant")
            row_layout.addWidget(bubble)
            row_layout.addStretch(1)
        self.chat_messages_layout.insertWidget(self.chat_messages_layout.count() - 1, row)
        QTimer.singleShot(0, lambda: self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum()))

    def toggle_left_sidebar(self) -> None:
        sizes = self.body_splitter.sizes()
        self._left_expanded = not self._left_expanded
        self.left_content.setVisible(self._left_expanded)
        self.left_brand.setVisible(self._left_expanded)
        self.collapse_left_button.setText("‹" if self._left_expanded else "☰")
        if self._left_expanded:
            target = max(self.LEFT_MIN_WIDTH, self._expanded_left_width)
            self.left_sidebar.setMinimumWidth(self.LEFT_MIN_WIDTH)
            self.left_sidebar.setMaximumWidth(16_777_215)
            restored_center = max(1, sizes[1] - (target - sizes[0]))
            self.body_splitter.setSizes([target, restored_center, sizes[2]])
        else:
            self._expanded_left_width = max(self.LEFT_MIN_WIDTH, sizes[0])
            released = max(0, sizes[0] - self.COLLAPSED_LEFT_WIDTH)
            self.left_sidebar.setMinimumWidth(self.COLLAPSED_LEFT_WIDTH)
            self.left_sidebar.setMaximumWidth(self.COLLAPSED_LEFT_WIDTH)
            self.body_splitter.setSizes([self.COLLAPSED_LEFT_WIDTH, sizes[1] + released, sizes[2]])

    def update_document_title(self, name: str, is_dirty: bool) -> None:
        marker = " *" if is_dirty else ""
        self.setWindowTitle(f"墨构 — {name}{marker}")

    def update_statistics(self, today: int, goal: int, session_delta: int, seconds: int) -> None:
        sign = "+" if session_delta >= 0 else ""
        self.stats_label.setText(f"今日 {today} / {goal} 字  ·  本次 {sign}{session_delta} 字  ·  {seconds // 60:02d}:{seconds % 60:02d}")

    def update_save_state(self, state: str) -> None:
        self.save_state_label.setText(state)

    def choose_new_workspace_path(self) -> Path | None:
        parent = QFileDialog.getExistingDirectory(self, "选择工作区存放位置")
        if not parent:
            return None
        name, accepted = QInputDialog.getText(self, "新建工作区", "工作区名称：")
        return Path(parent) / name.strip() if accepted and name.strip() else None

    def choose_open_workspace_path(self) -> Path | None:
        path = QFileDialog.getExistingDirectory(self, "打开墨构工作区")
        return Path(path) if path else None

    def choose_import_path(self) -> Path | None:
        filename, _ = QFileDialog.getOpenFileName(self, "导入文稿", "", "Markdown 或文本 (*.md *.txt)")
        return Path(filename) if filename else None

    def choose_export_path(self, suffix: str) -> Path | None:
        label = "Markdown" if suffix == ".md" else "纯文本"
        filename, _ = QFileDialog.getSaveFileName(self, f"导出 {label}", f"未命名{suffix}", f"{label} (*{suffix})")
        return Path(filename) if filename else None

    def ask_daily_goal(self, current: int) -> int | None:
        value, accepted = QInputDialog.getInt(self, "每日字数目标", "目标字数：", current, 0, 10_000_000)
        return value if accepted else None

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def set_close_requested_handler(self, handler: Callable[[], bool]) -> None:
        self._close_requested = handler

    def toggle_focus_mode(self) -> None:
        self._focus_mode = not self._focus_mode
        self.menuBar().setVisible(not self._focus_mode)
        self.toolbar.setVisible(not self._focus_mode)
        self.left_sidebar.setVisible(not self._focus_mode)
        self.right_sidebar.setVisible(not self._focus_mode)
        self.find_bar.setVisible(False)
        self.focus_action.setText("退出专注模式" if self._focus_mode else "进入专注模式")
        if self._focus_mode:
            self.showFullScreen()
        else:
            self.showNormal()
        self.editor.setFocus()
        self.focus_mode_changed.emit()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if self._focus_mode and event.key() == Qt.Key.Key_Escape:
            self.toggle_focus_mode()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._close_requested():
            event.accept()
        else:
            event.ignore()

    def _show_about(self) -> None:
        QMessageBox.about(self, "关于墨构", "墨构（Mogou）\n\n一个 local-first 的沉浸式小说编辑器。")
