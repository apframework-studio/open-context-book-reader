# Open Context Book Reader: first release design

**Date:** 2026-10-22
**Scope:** A standalone Agent Skill for nonfiction electronic books.

## Place in Open Context

Open Context Clipper captures web pages. Open Context Article Reader explains one web article. Open Context Forge Vault Maintainer imports article snapshots and compiles them into a selected knowledge vault. Book Reader owns the distinct book-reading step: obtain usable text from a local ebook or an upstream text export, determine what was actually read, and produce a source-grounded book analysis. It does not silently invoke the article workflow or treat the current article-only vault importer as a book importer.

The first release produces a portable Markdown analysis and a normalized source package for a later vault workflow. A user may request a file in a chosen output directory. A vault write remains a separate integration with an explicit target vault and book-aware import contract.

## Inputs and coverage

- Native inputs: local PDF, EPUB, and TXT. Accept Markdown and HTML that an upstream tool extracted from an ebook. Treat these as book text only when the user identifies them as such or their structure establishes a book-length work.
- Optional companion material: user-supplied highlights, annotations, notes, metadata, or table of contents. Such material may be pasted or in a separate readable file. The skill does not assume that a platform's notes are the reader's own; author or ownership fields control attribution.
- Title, metadata, or table of contents alone support a **preliminary positioning card**, not a full-book map or reading notes.
- A partial book, unreadable pages, missing figures, or incomplete extraction produce an explicitly bounded analysis. No claim about an unread chapter is presented as a finding from the book.

Extraction is a separate deterministic stage. The bundled helper converts supported local files into `source.md` with stable line numbers and a `manifest.json` with source hash, format, metadata, source locators, coverage, and warnings. EPUB keeps reading order and section IDs; PDF keeps page numbers and available PDF annotations; TXT/Markdown/HTML keep line or element/section references where available. The original file is never modified. The helper does not download books, bypass access controls, run OCR, or fetch platform notes. If required text is image-only or extraction is malformed, the skill reports the affected range and asks for an OCR result or a more usable source. Figures that carry essential information require inspection or a stated gap.

The normalized source is a working and handoff artifact, not a claim that its formatting perfectly reproduces the ebook. The analysis retains the original locator (PDF page, EPUB item and anchor, or text line) as well as normalized-source line evidence when possible. It records the edition or file identity when known, because page references differ by edition.

## Reading workflow

1. **Inventory:** identify the book, edition, source format, usable text, table of contents, notes ownership, missing ranges, and the reader's question if supplied.
2. **Position:** classify the book's domain and function, its core problem or learning objective, prerequisite knowledge, intended audience, publication context, and related works. External background is separately sourced. “Why read now” is derived from a stated goal or explicitly left open.
3. **Map:** read sections in bounded units, then explain how they build the whole. The shared map is `problem or goal → organizing framework → role of each major part → support, derivation, examples or procedure → conclusions and limits`. A table of contents is a starting index, not the finished map.
4. **Take notes:** select a few consequential ideas and record the author's statement, its support or mechanism, exact locator, a plain-language explanation, questions or limits, and links to other ideas when useful. Preserve reader-supplied observations as theirs; AI-suggested reflections are labeled as prompts, not written in the reader's voice.
5. **Review:** give a short synthesis and a few closed-book reconstruction questions when the user wants learning support.

Use book-function lenses only where relevant: scientific works inspect method, evidence, and uncertainty; technical books inspect prerequisites, mechanisms, reproducibility, and version-sensitive details; philosophical works inspect definitions, premises, inference, and objections; practical works inspect applicable conditions and reported outcomes; nonfiction biography or intellectual history inspect chronology, sources, and interpretation. Mixed books may use more than one lens.

## Output contract

Default response is scaled to the requested depth. A substantial analysis can be saved as a Markdown file containing:

1. Source identity and coverage: title, author, edition/date if known, format, read range, unread or unreliable ranges, and companion-material provenance.
2. Book positioning: one-sentence placement, central question, function, audience/prerequisites, related works with the relationship stated, and a reader-specific reason only when provided.
3. Reading map: the book's structure and each major part's role, including the key concepts, evidence or derivation, tensions, and conclusion.
4. Selected notes: source-located author point, explanation, support, uncertainty, reader comment if actually supplied, and optional follow-up question.
5. Synthesis and limits: what the source supports, what needs independent checking, and optional retrieval questions.

Every consequential statement distinguishes **book statement**, **inference from the book**, **external finding**, **reader statement**, or **unknown**. External information never silently repairs a gap in the book. Short quotations preserve the source wording and locator; analysis does not copy whole chapters into the result.

For downstream use, `source.md` and `manifest.json` provide a stable, local text-and-evidence interface. `analysis.md` is the human-readable handoff. The first release does not impose a vault directory, frontmatter schema, or personal reading list on other users. Book files and full extracted text stay outside this skill repository.

## Sample observations and acceptance

The two supplied exports have a book-length HTML body, an independent JSON object with metadata/catalog, many images, and unequal note coverage. One JSON has seven note records whose ownership flag does not identify them as the user's notes; the other has none. The skill must preserve that distinction. Catalog entries carry levels and anchors, while the HTML contains section IDs and headings with character-level markup; extraction must not turn those heading characters into space-separated text. One supplied note cannot be matched by a simple prefix search, so note-to-passage matching may be uncertain.

Acceptance scenarios:

- An EPUB with multiple spine items yields reading-order text, metadata, locators, and no duplicate navigation text.
- A text PDF yields page-located text and any recoverable annotations. An image-only page is reported as a gap.
- TXT/Markdown and a pre-extracted HTML book yield usable text with line or section locators.
- A title-only request produces preliminary positioning with source limits. A partial book produces a partial map and identifies unread chapters.
- Companion notes with unknown or external ownership are not recast as the reader's ideas.
- A full-book response explains the relationship among parts and supports key points with locators. Technical, scientific, and philosophical sample requests select different lenses without changing the common output contract.
- Article-only and vault-write requests route to the appropriate separate workflow; no vault is selected or changed by default.
