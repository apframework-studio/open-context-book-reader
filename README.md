# Open Context Book Reader

[简体中文](README.zh-CN.md)

A standalone Agent Skill for source-grounded reading of nonfiction ebooks. It works across nonfiction, with focused checks for AI, science, technology, and philosophy.

The skill offers a preliminary positioning card when only a title or table of contents is available. With readable book text, it builds a map of the central question, the role and relationship of major parts, evidence or derivations, conclusions, and limits. Selected notes retain source locations and distinguish the author's words from the reader's own thoughts. It can add short closed-book recall questions.

Its local extractor accepts PDF, EPUB, TXT, Markdown, and HTML, and writes `source.md` plus `manifest.json`. PDF annotations can be recovered; separate platform exports of highlights or notes can be supplied as companion material. See [SKILL.md](SKILL.md) for agent behavior and [extraction details](references/extraction.md) for format caveats.

## Install for Codex

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/apframework-studio/open-context-book-reader.git ~/.agents/skills/open-context-book-reader
python3 -m pip install -r ~/.agents/skills/open-context-book-reader/requirements.txt
```

Codex discovers the skill from `~/.agents/skills`. Invoke it with `$open-context-book-reader`, or describe a nonfiction book-reading task. Install the Python dependencies in the environment used to run the extractor.

## Use the extractor

```bash
python3 ~/.agents/skills/open-context-book-reader/scripts/extract_book.py /path/to/book.epub --output /path/outside/repo/book-package
```

The output directory must not exist and must be outside this skill repository. The package may contain the book's full text, so keep it in a user-chosen location. TXT and Markdown extraction use the Python standard library; other formats need only their relevant listed packages. Image-only PDFs require a separate OCR source, and figures or complex layouts require review.

The analysis can be used directly in conversation or saved as `analysis.md`. The extraction package keeps a source hash, locations, and coverage information for later review. The user supplies the book and any separate highlight exports; notes with uncertain ownership are labeled accordingly.
