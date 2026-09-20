# 墨构 / Mogou

一个 local-first 的 PySide6 小说编辑器原型。基础客户端不依赖网络、Docling 或本地模型。

## 开发

```powershell
uv sync --extra dev
uv run mogou
uv run pytest
```

文档以 UTF-8 Markdown 文件保存；右侧 Echo 对话仅保存在当前运行期。
