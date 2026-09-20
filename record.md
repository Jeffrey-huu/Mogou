# Mogou 资料库：Docling 适配记录

> 本文记录当前已验证的本地文档导入能力，供后续资料库、检索与 Agent 功能实现时参考。测试资料、转换产物和模型缓存均为本地私有数据，不纳入版本控制。

## 定位

Docling 是 Mogou 资料库的**导入与结构化解析层**：

```text
本地资料文件
  → Docling DocumentConverter
  → DoclingDocument（保留结构）
  → Chunk / Embedding / 本地索引
  → 资料库检索与写作 Agent 上下文
```

实现资料库时不应将“文件转 Markdown”作为唯一持久化形式。应优先保存原文件元数据、`DoclingDocument` 的结构化 JSON 和解析版本；Markdown 可作为预览与人工阅读导出。后续 Chunker 应直接消费结构化文档，以保留标题层级、表格、阅读顺序和来源定位。

## 已验证的格式

批量测试已本地通过以下 8 类输入：

- DOCX
- Markdown
- MP3
- PDF
- PNG
- PPTX
- TXT
- XLS（旧版 Excel）

批量运行器位于 `test/docling/test_docling_batch.py`。它会递归读取 `test/docling/inputs/`，按原有目录层级把每个成功项导出为 Markdown 至 `test/docling/outputs/`，并生成 JSON 汇总报告。报告仅用于本地排障；资料库实现应将失败状态、错误类别和解析器版本写入数据库。

## Python 与依赖

主项目使用 uv 管理 Python 环境，要求 Python 3.12+。Docling 作为 Git submodule 位于 `submodules/docling`。

基础资料解析需要 Docling 的 `standard` 功能集；音频转写另需 `format-audio`：

```powershell
uv sync --project submodules/docling --locked --extra standard --extra format-audio
uv run --project submodules/docling --extra standard --extra format-audio python test/docling/test_docling_batch.py
```

`format-audio` 会安装 Whisper、CTranslate2、PyAV 等本地 ASR 依赖。首次处理 PDF、图片或音频时，相关模型可能需要下载；模型完整缓存后可离线复用。

## 格式特有的适配

| 格式 | Docling 路径 | 额外要求 | 资料库注意事项 |
| --- | --- | --- | --- |
| PDF / PNG | 文档理解 + OCR / 布局模型 | 本地 Docling/Hugging Face 模型缓存 | 保存页码、标题层级、表格与来源位置，供检索引用。 |
| DOCX / PPTX / TXT / Markdown | 原生文档后端 | `standard` | 保留文件路径、修改时间、章节/幻灯片层级。 |
| XLS | Office 后端 | Windows 上安装 LibreOffice | 将工作表、单元格范围等来源信息写入元数据；旧版格式转换可能更慢。 |
| MP3 | ASR 管线 | `format-audio` 与 Whisper 模型 | 保存时间戳、说话人/片段信息（后续可扩展），不要只保存纯文本。 |

LibreOffice 已安装，用于本地旧版 `.xls` 转换。产品安装包中应将它视为可选的 Office 兼容组件，而不是把它与核心编辑器强绑定。

## 私有数据与缓存策略

测试目录采用两层隔离：

- `test/.gitignore`：任何测试套件的 `output/` 与 `outputs/` 都不进入 Git。
- `test/docling/.gitignore`：除批量测试脚本和规则文件外，Docling 测试目录的所有内容均忽略，包括输入资料、转换结果和模型缓存。

批量脚本将下列环境变量指向 `test/docling/.cache/`，避免使用无权限或不可控的用户级缓存目录：

```text
DOCLING_CACHE_DIR
HF_HOME
XDG_CACHE_HOME
HOME
USERPROFILE
```

正式产品应采用同样的原则，但把位置替换为每个用户的 Mogou 应用数据目录，例如：

```text
Mogou data/
  library/          # 原始资料与结构化解析结果
  models/           # Docling / OCR / ASR / embedding 模型
  cache/            # 可安全重建的转换缓存
  index/            # FTS / vector 索引
```

资料库不得默认上传原文、解析结果、向量或模型缓存。若未来提供云端 LLM，发送检索片段前必须在界面中明确告知用户并取得选择。

## 资料库实现建议

1. 每次导入建立资料记录：文件哈希、原始路径/副本、MIME 类型、导入时间、解析器与模型版本、解析状态。
2. 用文件哈希做增量导入；内容未变化时复用结构化文档与向量，避免重复 OCR/ASR。
3. 解析失败不应阻塞整个批次：记录失败类别，允许重试、替换后端或提示安装可选组件。
4. Chunk 应保存 `document_id`、页码/时间戳、标题路径、原始块定位及内容哈希，方便 Agent 给出可追溯引用。
5. 本地模型下载、缓存路径和磁盘占用应在设置页可见、可清理；清理前需区分可重建缓存与用户资料。
