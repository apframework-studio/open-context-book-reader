#!/usr/bin/env python3
"""Extract local ebook text into a source-located Markdown package."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def clean_text(value):
    return re.sub(r"\s+", " ", value).strip()


def plain_units(source, markdown=False):
    raw = source.read_bytes()
    warnings = []
    for encoding in ("utf-8-sig", "utf-16", "gb18030"):
        try:
            content = raw.decode(encoding)
            if encoding != "utf-8-sig":
                warnings.append(f"使用 {encoding} 解码；请核对文字。")
            break
        except UnicodeError:
            continue
    else:
        raise ValueError("无法解码文本；请提供 UTF-8、UTF-16 或 GB18030 文件。")
    units = []
    for number, line in enumerate(content.splitlines(), 1):
        if line.strip():
            units.append({"locator": f"L{number}", "text": line.rstrip()})
    return units, {"title": source.stem, "author": None}, warnings


def html_units(content, locator_prefix="", skip_navigation=True):
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError("HTML/EPUB 提取需要 beautifulsoup4；请安装 requirements.txt。") from exc
    soup = BeautifulSoup(content, "html.parser")
    title_tag = soup.find("title")
    title = clean_text(title_tag.get_text("", strip=False)) if title_tag else None
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    if skip_navigation:
        for tag in soup.find_all(["nav", "aside"]):
            tag.decompose()
        for tag in soup.find_all(id=re.compile(r"^(toc|table-of-contents)$", re.I)):
            tag.decompose()
    body = soup.body or soup
    selected = {f"h{i}" for i in range(1, 7)} | {"p", "li", "blockquote", "pre", "td"}
    units = []
    for tag in body.find_all(selected):
        if tag.find(selected):
            continue
        value = clean_text(tag.get_text("", strip=False))
        if not value:
            continue
        anchor = next((parent.get("id") for parent in [tag, *tag.parents] if parent.get("id")), None)
        locator = locator_prefix + (f"#{anchor}" if anchor else f"/{tag.name}[{len(units) + 1}]")
        if tag.name.startswith("h") and len(tag.name) == 2:
            value = "#" * int(tag.name[1]) + " " + value
        units.append({"locator": locator, "text": value})
    if not units:
        value = clean_text(body.get_text("", strip=False))
        if value:
            units.append({"locator": locator_prefix or "/body", "text": value})
    images = body.find_all("img")
    warnings = []
    if images:
        missing_alt = sum(not clean_text(image.get("alt", "")) for image in images)
        warnings.append(f"包含 {len(images)} 张图，其中 {missing_alt} 张无替代文字；图中信息未提取。")
    return units, title, warnings


def extract_html(source):
    content = source.read_bytes()
    units, title, warnings = html_units(content)
    return units, {"title": title or source.stem, "author": None}, warnings, []


def extract_epub(source):
    try:
        from ebooklib import ITEM_DOCUMENT, epub
    except ImportError as exc:
        raise RuntimeError("EPUB 提取需要 EbookLib；请安装 requirements.txt。") from exc
    try:
        book = epub.read_epub(str(source))
    except epub.EpubException as exc:
        raise ValueError(f"EPUB 文件无法读取：{exc}") from exc

    def first_metadata(name):
        values = book.get_metadata("DC", name)
        return values[0][0] if values else None

    units = []
    warnings = []
    for item_id, _linear in book.spine:
        item = book.get_item_with_id(item_id)
        if not item or item.get_type() != ITEM_DOCUMENT:
            continue
        if isinstance(item, epub.EpubNav) or "nav" in getattr(item, "properties", []):
            continue
        href = item.get_name()
        section, _title, section_warnings = html_units(item.get_content(), locator_prefix=href)
        if section:
            units.extend(section)
        else:
            warnings.append(f"EPUB 章节 {href} 没有可读文字。")
        warnings.extend(f"{href}: {warning}" for warning in section_warnings)
    return units, {"title": first_metadata("title") or source.stem, "author": first_metadata("creator")}, warnings, []


def extract_pdf(source):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF 提取需要 PyMuPDF；请安装 requirements.txt。") from exc
    units = []
    warnings = []
    annotations = []
    with fitz.open(str(source)) as document:
        metadata = document.metadata or {}
        for page_number, page in enumerate(document, 1):
            page_text = page.get_text(sort=True).strip()
            if page_text:
                units.append({"locator": f"p.{page_number}", "text": page_text})
            else:
                warnings.append(f"第 {page_number} 页没有可提取文字；可能是空白页或扫描图像。")
            if page.get_images():
                warnings.append(f"第 {page_number} 页包含图像；图中信息未提取。")
            for annotation in page.annots() or []:
                info = annotation.info or {}
                selected = clean_text(page.get_textbox(annotation.rect))
                annotations.append({
                    "locator": f"p.{page_number}",
                    "type": annotation.type[1],
                    "author": info.get("title") or None,
                    "comment": info.get("content") or None,
                    "selected_text": selected or None,
                    "selected_text_approximate": bool(selected),
                })
    coverage = "partial" if any("没有可提取文字" in warning for warning in warnings) else "extracted"
    return units, {"title": metadata.get("title") or source.stem, "author": metadata.get("author") or None}, warnings, annotations, coverage


def render_package(units):
    lines = ["# 提取的图书文本", "", "> 原文位置标记供回查；行号以本文件为准。", ""]
    mapped = []
    for unit in units:
        start = len(lines) + 1
        lines.append(f"<!-- 原文位置: {unit['locator']} -->")
        lines.extend(unit["text"].splitlines())
        end = len(lines)
        lines.append("")
        mapped.append({"locator": unit["locator"], "source_line_start": start, "source_line_end": end})
    return "\n".join(lines) + "\n", mapped


def write_package(source, output, units, metadata, warnings, annotations, file_format, coverage_status="extracted"):
    if not units:
        raise ValueError("未提取到可读文本；如为扫描件，请先提供 OCR 结果。")
    body, mapped = render_package(units)
    manifest = {
        "schema_version": 1,
        "source_path": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "format": file_format,
        "metadata": metadata,
        "coverage": {"status": coverage_status, "unit_count": len(units)},
        "warnings": warnings,
        "units": mapped,
        "annotations": annotations,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "source.md").write_text(body, encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="提取本地 PDF、EPUB、TXT、Markdown 或 HTML 图书文本")
    parser.add_argument("source", type=Path, help="本地电子书文件")
    parser.add_argument("--output", required=True, type=Path, help="新建输出目录，须在 skill 仓库之外")
    args = parser.parse_args(argv)
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        parser.error(f"源文件不存在：{source}")
    if output == SKILL_ROOT or SKILL_ROOT in output.parents:
        parser.error("输出目录必须位于 skill 仓库之外，避免提交图书全文。")
    if output.exists():
        parser.error(f"输出目录已存在：{output}")
    file_format = source.suffix.lower().lstrip(".")
    try:
        if file_format in {"txt", "md", "markdown"}:
            units, metadata, warnings = plain_units(source, file_format != "txt")
            annotations = []
            coverage_status = "extracted"
            file_format = "markdown" if file_format != "txt" else "txt"
        elif file_format in {"html", "htm"}:
            units, metadata, warnings, annotations = extract_html(source)
            coverage_status = "extracted"
            file_format = "html"
        elif file_format == "epub":
            units, metadata, warnings, annotations = extract_epub(source)
            coverage_status = "extracted"
        elif file_format == "pdf":
            units, metadata, warnings, annotations, coverage_status = extract_pdf(source)
        else:
            raise ValueError(f"暂不支持 {source.suffix} 格式。")
        write_package(source, output, units, metadata, warnings, annotations, file_format, coverage_status)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.error(str(exc))
    print(output)


if __name__ == "__main__":
    main()
