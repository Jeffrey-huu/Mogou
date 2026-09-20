from pathlib import Path

import pytest

from mogou.models.document import DocumentModel


def test_save_and_load_utf8_markdown(tmp_path: Path) -> None:
    path = tmp_path / "第一章.md"
    model = DocumentModel(content="# 开场\n你好，世界。", is_dirty=True)

    model.save(path)

    loaded = DocumentModel()
    loaded.load(path)
    assert loaded.content == "# 开场\n你好，世界。"
    assert loaded.path == path
    assert not loaded.is_dirty


def test_change_marks_document_dirty() -> None:
    model = DocumentModel(content="初稿")
    model.set_content("修订稿")
    assert model.is_dirty


def test_unnamed_document_requires_path_to_save() -> None:
    with pytest.raises(ValueError):
        DocumentModel().save()


def test_save_appends_markdown_suffix(tmp_path: Path) -> None:
    model = DocumentModel(content="内容")
    model.save(tmp_path / "小说")
    assert (tmp_path / "小说.md").read_text(encoding="utf-8") == "内容"
