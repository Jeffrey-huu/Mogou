from mogou.views.main_window import MainWindow


def test_main_window_has_three_primary_panes(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.navigation.count() == 5
    assert window.editor is not None
    assert window.chat_history.isReadOnly()


def test_main_window_emits_chat_request(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    with qtbot.waitSignal(window.chat_send_requested):
        window.send_button.click()
