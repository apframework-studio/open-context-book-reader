# Open Context Book Reader Implementation Plan

> **For agentic workers:** Implement the tasks in order. Keep book content out of this repository and verify each deliverable before continuing.

**Goal:** Ship a standalone nonfiction ebook-reading skill with a reliable local extraction helper and a portable, source-grounded analysis contract.

**Architecture:** A Python CLI writes normalized `source.md` plus `manifest.json` from PDF, EPUB, TXT, Markdown, or HTML. The `SKILL.md` reads this package and optional companion notes, then guides positioning, book-level mapping, and evidence-located notes. It emits Markdown for a later book-aware vault importer without mutating a vault itself.

**Tech Stack:** Python 3.10+, standard library, optional PyMuPDF for PDF, EbookLib for EPUB, Beautiful Soup for HTML/EPUB; Markdown instructions.

**Spec:** `docs/superpowers/specs/2026-10-22-book-reader-design.md`

## Global constraints

- Read source files only. Output goes to a caller-chosen directory outside the skill repository.
- Preserve PDF page, EPUB item/anchor, and source text line references in the package.
- Reject unsupported or unusable extraction with an actionable error; report partial extraction and image-heavy gaps.
- Do not treat sidecar notes as the reader's own unless the source says so or the reader confirms it.
- Do not call the article-only vault importer on an ebook package.

## File map

- `scripts/extract_book.py`: local format extraction and package writer.
- `tests/test_extract_book.py`: synthetic format and provenance tests.
- `SKILL.md`: trigger boundary and reading workflow.
- `references/extraction.md`: format-specific checks and annotation handling.
- `references/analysis.md`: book-function lenses and output contract.
- `README.md`, `README.zh-CN.md`: user-facing usage and ecosystem boundary.
- `.gitignore`, `requirements.txt`: generated-file exclusion and optional dependencies.

### Task 1: Extract plain text and HTML

- [x] Write tests that call the CLI on UTF-8 TXT, Markdown, and a synthetic HTML export with a duplicate TOC, character-level heading markup, IDs, and images. Assert normalized reading text, locator markers, warnings, output directory policy, and SHA-256 identity.
- [x] Run `python3 -m unittest tests.test_extract_book -v`; confirm the new tests fail because the helper is absent.
- [x] Implement `extract_text`, `extract_html`, `write_package`, and the CLI dispatch in `scripts/extract_book.py`. Use `BeautifulSoup` only for HTML, and fall back to a clear dependency error if it is unavailable.
- [x] Run the same test command and confirm it passes.

### Task 2: Extract EPUB and PDF

- [x] Extend tests with a synthetic EPUB ZIP containing metadata, nav, two spine documents, headings and an image. Assert spine order, title/author, item locators, and no duplicate nav body. Add a PyMuPDF-generated PDF with two text pages, one highlight, and one blank page; assert page locators, annotation provenance, and the blank-page warning.
- [x] Run `python3 -m unittest tests.test_extract_book -v`; confirm the new cases fail for missing format handlers.
- [x] Implement `extract_epub` using EbookLib spine order and `extract_pdf` using PyMuPDF `page.get_text(sort=True)` and `page.annots()`. Record annotation text as approximate when recovered from its rectangle; retain comments and author fields. Keep original source untouched.
- [x] Run the full extraction test suite and inspect the package from one supplied HTML book in a temporary directory. Confirm no sample book text is written into the repository.

### Task 3: Author the skill

- [x] Write `SKILL.md` with precise triggers, book-vs-article routing, source checks, partial-coverage behavior, book positioning, map synthesis, note provenance, and the optional file handoff. Link the two references only where needed.
- [x] Write `references/extraction.md` and `references/analysis.md`, including source-state labels, format/annotation caveats, and a compact Markdown analysis shape. Use the supplied sample observations without copying book text.
- [x] Add bilingual README files, dependency guidance, and `.gitignore`. Keep the skill root independently installable.
- [x] Run the Skill Creator validator against the repository root and inspect frontmatter/links.

### Task 4: End-to-end verification

- [x] Run `python3 -m unittest discover -s tests -v` and `python3 scripts/extract_book.py --help`.
- [x] Extract both supplied HTML book exports into a temporary directory and inspect title, chapter headings, image warnings, and coverage. Inspect JSON note ownership separately; do not import the books or their notes into the repository.
- [x] Check repository status, whitespace, internal links, and absence of copyrighted sample text or machine-local sample paths in skill files.
- [x] Re-read the spec acceptance scenarios and report what was verified, what remains untested, and the exact output files.
