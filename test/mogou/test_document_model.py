from pathlib import Path

from mogou.models.document import DocumentModel


def test_workspace_create_save_and_load_preserves_html_and_settings(tmp_path: Path) -> None:
    path = tmp_path / "星海纪元"
    model = DocumentModel()
    model.create(path)
    model.name = "星海纪元"
    model.set_html("<h1>开场</h1><p><b>你好</b>，世界。</p>")
    model.set_daily_goal(2500)
    model.add_words(4, "2026-09-22")
    model.save()

    loaded = DocumentModel()
    loaded.load(path)

    assert (path / ".mogou" / "workspace.json").is_file()
    assert (path / "manuscript.html").is_file()
    assert loaded.html == "<h1>开场</h1><p><b>你好</b>，世界。</p>"
    assert loaded.daily_goal == 2500
    assert loaded.today_words("2026-09-22") == 4
    assert not loaded.is_dirty


def test_word_progress_only_increases_for_new_text() -> None:
    model = DocumentModel()
    model.add_words(10, "2026-09-22")
    model.add_words(-3, "2026-09-22")
    assert model.today_words("2026-09-22") == 10


def test_save_without_workspace_requires_workspace() -> None:
    try:
        DocumentModel().save()
    except ValueError:
        pass
    else:
        raise AssertionError("saving without a workspace should fail")
