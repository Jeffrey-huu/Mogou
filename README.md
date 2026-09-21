# 墨构 / Mogou

一个 local-first 的 PySide6 沉浸式小说编辑器。基础客户端不依赖网络、Docling 或本地模型。

## 开发

```powershell
uv sync --extra dev
uv run mogou
uv run pytest
```

以工作区文件夹保存：正文为 `manuscript.html`，本地元数据在 `.mogou/workspace.json`。可导入或导出 UTF-8 Markdown 与 TXT。
