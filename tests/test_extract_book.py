import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_book.py"


class ExtractBookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def run_extract(self, source, name="result"):
        output = self.work / name
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--output", str(output)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return (output / "source.md").read_text(encoding="utf-8"), json.loads(
            (output / "manifest.json").read_text(encoding="utf-8")
        )

    def test_txt_keeps_source_line_locators_and_hash(self):
        source = self.work / "small.txt"
        source.write_text("序言\n\n第一章\n论点。\n", encoding="utf-8")
        body, manifest = self.run_extract(source)
        self.assertIn("论点。", body)
        self.assertIn("L4", body)
        self.assertEqual(manifest["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(manifest["format"], "txt")
        self.assertEqual(manifest["coverage"]["status"], "extracted")
        self.assertTrue(any(unit["locator"] == "L4" for unit in manifest["units"]))

    def test_markdown_keeps_heading_and_source_line(self):
        source = self.work / "book.md"
        source.write_text("# 起点\n正文。\n", encoding="utf-8")
        body, manifest = self.run_extract(source)
        self.assertIn("# 起点", body)
        self.assertEqual(manifest["format"], "markdown")
        self.assertTrue(any(unit["locator"] == "L2" for unit in manifest["units"]))

    def test_html_skips_duplicate_toc_and_joins_character_markup(self):
        source = self.work / "book.html"
        source.write_text(
            '<html><head><title>测试书</title></head><body>'
            '<div id="toc"><p>重复导航</p></div>'
            '<section id="s1"><h1><b>第</b><b>一</b><b>章</b></h1>'
            '<p>核心主张。</p><img src="chart.png" alt=""></section>'
            '</body></html>',
            encoding="utf-8",
        )
        body, manifest = self.run_extract(source)
        self.assertIn("第一章", body)
        self.assertNotIn("第 一 章", body)
        self.assertNotIn("重复导航", body)
        self.assertIn("核心主张。", body)
        self.assertEqual(manifest["metadata"]["title"], "测试书")
        self.assertTrue(any("图" in warning for warning in manifest["warnings"]))
        self.assertTrue(any("#s1" in unit["locator"] for unit in manifest["units"]))

    def test_html_with_malformed_outer_paragraph_still_has_section_units(self):
        source = self.work / "wrapped.html"
        source.write_text(
            '<html><body><p><div id="toc"><p>导航</p></div>'
            '<div id="chapter"><h1>章名</h1><p>第一段。</p><p>第二段。</p></div>'
            '</p></body></html>',
            encoding="utf-8",
        )
        body, manifest = self.run_extract(source)
        self.assertNotIn("导航", body)
        self.assertGreaterEqual(len(manifest["units"]), 3)
        self.assertEqual(body.count("第一段。"), 1)
        self.assertEqual(body.count("第二段。"), 1)

    def test_rejects_output_inside_skill_repository(self):
        source = self.work / "small.txt"
        source.write_text("正文", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--output", str(ROOT / "generated")],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((ROOT / "generated").exists())

    def test_epub_uses_spine_order_and_skips_navigation(self):
        from ebooklib import epub

        book = epub.EpubBook()
        book.set_identifier("example-id")
        book.set_title("样本书")
        book.set_language("zh")
        book.add_author("某作者")
        first = epub.EpubHtml(title="前章", file_name="first.xhtml", lang="zh")
        first.content = '<html><body><section id="a"><h1>前章</h1><p>先读这章。</p></section></body></html>'
        second = epub.EpubHtml(title="后章", file_name="second.xhtml", lang="zh")
        second.content = '<html><body><section id="b"><h1>后章</h1><p>后读这章。</p></section></body></html>'
        nav = epub.EpubNav()
        book.add_item(first)
        book.add_item(second)
        book.add_item(nav)
        book.add_item(epub.EpubNcx())
        book.toc = (epub.Link("first.xhtml", "前章", "first"),)
        book.spine = ["nav", first, second]
        source = self.work / "sample.epub"
        epub.write_epub(str(source), book)

        body, manifest = self.run_extract(source)
        self.assertLess(body.index("先读这章"), body.index("后读这章"))
        self.assertEqual(body.count("先读这章"), 1)
        self.assertEqual(manifest["metadata"]["title"], "样本书")
        self.assertEqual(manifest["metadata"]["author"], "某作者")
        self.assertTrue(any(unit["locator"] == "first.xhtml#a" for unit in manifest["units"]))

    def test_pdf_keeps_pages_annotations_and_blank_page_warning(self):
        import fitz

        source = self.work / "sample.pdf"
        document = fitz.open()
        first = document.new_page()
        first.insert_text((70, 80), "Evidence on page one")
        first.insert_text((70, 100), "Second evidence line")
        highlight = first.add_highlight_annot(first.search_for("Evidence"))
        highlight.set_info(content="Check this", title="Reader")
        document.new_page()
        document.save(str(source))
        document.close()

        body, manifest = self.run_extract(source)
        self.assertIn("Evidence on page one", body)
        first_unit = manifest["units"][0]
        normalized_lines = body.splitlines()
        self.assertIn("Second evidence line", normalized_lines[first_unit["source_line_end"] - 1])
        self.assertTrue(any(unit["locator"] == "p.1" for unit in manifest["units"]))
        self.assertTrue(any("第 2 页" in warning for warning in manifest["warnings"]))
        self.assertEqual(manifest["coverage"]["status"], "partial")
        self.assertEqual(manifest["annotations"][0]["author"], "Reader")
        self.assertEqual(manifest["annotations"][0]["comment"], "Check this")
        self.assertEqual(manifest["annotations"][0]["locator"], "p.1")
        self.assertTrue(manifest["annotations"][0]["selected_text_approximate"])

    def test_image_only_pdf_fails_without_creating_package(self):
        import fitz

        source = self.work / "scan.pdf"
        document = fitz.open()
        document.new_page()
        document.save(str(source))
        document.close()
        output = self.work / "scan-output"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--output", str(output)],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OCR", result.stderr)
        self.assertFalse(output.exists())

    def test_damaged_epub_reports_input_error(self):
        source = self.work / "damaged.epub"
        source.write_bytes(b"not a zip archive")
        output = self.work / "damaged-output"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--output", str(output)],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EPUB", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
