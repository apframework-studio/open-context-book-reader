# Open Context Book Reader

[English](README.md)

一个可独立使用的非虚构图书阅读 Skill。当前重点是 AI、科学、技术、哲学，同时适用于其他非虚构书。提供读前定位、电子书内容提取、读后阅读地图和可回查的读书笔记。

## 能做什么

- **读前定位卡**：书名、作者、领域、写作背景、核心问题、适合谁读、相关作品及阅读动机。材料只有书名或目录时标为「初步定位」。
- **读后阅读地图**：从问题到框架、各部分作用、支撑材料、结论与边界，解释章节之间的关系。
- **精选笔记**：每条保留原文位置，区分作者观点、理解、同意或质疑、待查证点；附少量闭卷问题。
- **本地提取包**：从 PDF、EPUB、TXT、Markdown、HTML 生成 `source.md` 和 `manifest.json`。PDF 内嵌批注可提取；阅读平台另外导出的划线或笔记可作为伴随材料交给 Skill 核对。

## 使用

将此仓库作为 Skill 使用，入口为 [SKILL.md](SKILL.md)。例如：“用 open-context-book-reader 阅读这本 EPUB，给我读前定位、章节关系和带位置的笔记。” 也可仅给书名或目录请求初步定位。

独立使用提取器：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/extract_book.py /path/to/book.epub --output /path/outside/repo/book-package
```

输出目录必须不存在。提取包会包含原文全文，应保存在使用者选择的仓库外目录，不要提交到本仓库。依赖按输入格式使用：TXT/Markdown 仅需 Python；HTML 需 Beautiful Soup；EPUB 再需 EbookLib；PDF 需 PyMuPDF。扫描件需要另备 OCR 文本，图片和复杂版式需要人工核查。

分析可以直接在对话中使用，也可以保存为 `analysis.md`。提取包保留来源 hash、位置和覆盖信息，便于回查。原始书籍和划线导出由用户提供；对于不能确定是用户所写的批注，分析会标明归属不明。
