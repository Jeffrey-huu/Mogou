from mogou.views.main_window import MainWindow


def test_main_window_has_rich_editor_and_writing_actions(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.editor.acceptRichText()
    assert window.new_workspace_action is not None
    assert window.export_markdown_action is not None
    assert window.find_bar.isHidden()
    assert window.left_sidebar is not None
    assert window.chat_scroll.widgetResizable()
    assert window.toolbar.parent() is window.editor_panel
    assert window.left_tabs.count() == 2
    assert window.left_tabs.tabText(0) == "资料库"
    assert window.left_tabs.tabText(1) == "设置"
    assert window.left_sidebar.minimumWidth() == window.LEFT_MIN_WIDTH
    assert window.editor_panel.minimumWidth() == window.EDITOR_MIN_WIDTH
    assert window.right_sidebar.minimumWidth() == window.RIGHT_MIN_WIDTH
    assert window.right_sidebar.maximumWidth() > 10_000


def test_focus_mode_and_find_bar_can_be_toggled(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.toggle_focus_mode()
    assert window._focus_mode
    window.toggle_focus_mode()
    assert not window._focus_mode
    window._show_find(True)
    assert window.find_bar.isVisible()


def test_left_sidebar_collapses_to_icon_rail(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.wait(20)
    before = window.body_splitter.sizes()
    window.toggle_left_sidebar()
    qtbot.wait(20)
    after = window.body_splitter.sizes()
    assert window.left_sidebar.maximumWidth() == window.COLLAPSED_LEFT_WIDTH
    assert window.left_content.isHidden()
    assert window.collapse_left_button.text() == "☰"
    assert after[1] > before[1]


def test_splitter_cannot_collapse_editor_panel(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.wait(20)
    window.body_splitter.setSizes([900, 0, 300])
    qtbot.wait(20)
    assert window.body_splitter.sizes()[1] >= window.EDITOR_MIN_WIDTH


def test_chat_messages_are_aligned_as_bubbles(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    initial = window.chat_messages_layout.count()
    window.append_chat_message("user", "你好")
    window.append_chat_message("assistant", "你好，有什么想聊？")
    assert window.chat_messages_layout.count() == initial + 2
