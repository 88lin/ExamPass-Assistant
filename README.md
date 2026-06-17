# ExamPass Assistant <sup>v2.0</sup>

**Turn lecture slides into exam-ready study materials.**

> [中文](./README_CN.md)

> 🎉 **What's new in v2.0** — Notion-style **original-PPT cross-reference** beside every note, a **combined page** (notes + quiz in one file with top tabs), **self-test answers**, **mock-exam from a real past paper**, smarter pedagogy (Hook → TL;DR → Why → What → How → self-check), a 2× faster streaming pipeline, and a pile of rendering-robustness fixes verified with real-browser screenshots. See the [v2.0 changelog](#v20-changelog).

---

### What is this

An AI-powered exam prep assistant. Drop in lecture PPTs, Word handouts, or PDF readings — it generates:

- **Knowledge Guides** — structured review notes with MathJax formulas, dual-color highlighting (key points in bold black, explanations in lighter gray), priority tags (must-know / key / frequent / info), an auto table of contents, a **Hook → TL;DR → Why → What → How → self-check** narrative arc, and **collapsible self-test answers**
- **Original-PPT Cross-Reference** *(new in v2.0)* — a Notion-style right rail pins the rendered slide pages + their original text next to each note, so you can review the source without missing anything; click a heading's `[页N]` chip and the rail scrolls to that slide; choose density (all pages / key pages / none)
- **Combined Page** *(new in v2.0)* — knowledge list and interactive quiz in **one HTML** with top tabs (📖 Notes | 📝 Quiz)
- **Interactive Chapter Quizzes** — click to answer, one-click grading, per-question correct/incorrect badges, detailed explanations, and common-mistake warnings. 9 question types incl. calc and code — automatically chosen by subject
- **Knowledge Graph** — interactive left-root/right-leaf tree with dependency dashed lines, hub-concept stars, hover tooltips, persistent inline note cards (text + paste images), draggable column split, search, and zoom
- **Mock Final / Mock-from-Past-Paper** — full exam with answer key, blueprint scoring exactly 100 points; `mock --ref <real exam>` analyzes a past paper's style and writes brand-new questions in the same shape

Open in any browser. Ctrl+P to print as PDF. MathJax renders formulas perfectly. Responsive down to mobile.

### Why

The universal pain of finals week: scattered lecture files, no clear sense of exam priorities, no reliable practice questions.

ExamPass reads your course materials with Claude, extracts key concepts with logical narratives, and generates self-grading quizzes. Students use it to study smarter. Instructors use it to create exercises and assignments in seconds.

### Supported Formats

PPTX · DOCX · PDF (with image recognition via multimodal analysis)

### Quick Start

```bash
git clone https://github.com/WUBING2023/ExamPass-Assistant.git
cd ExamPass-Assistant
pip install -r requirements.txt
```

### Commands

| Command | Description |
|---------|-------------|
| `/exampass <dir>` | **Default pipeline** — per chapter: notes (with the **PPT cross-reference rail on by default**) + interactive quiz, in one combined page |
| `/exampass graph <dir>` | **Knowledge graph** — interactive left-right tree with dependency edges, hub stars, inline note cards, draggable split, search & zoom |
| `/exampass final <dir> [--ref <past exam>] [--chapter <ch>]` | **Exam generator** — smart question-type selection (analyzes the course, not a fixed template); `--ref` imitates a real past paper's style; `--chapter` does a single chapter |
| `/exampass update` | Pull latest features, fixes, and dependencies from GitHub |

> v2.0 streamlined the commands: `fast` is gone (the default is already fast), and `mock` folded into `final --ref`. The PPT cross-reference rail, previously an opt-in flag, is now **on by default**.

### Multi-Agent Pipeline (default)

The default `/exampass` command orchestrates 5 specialized sub-agents:

| Phase | Agent | Output |
|-------|-------|--------|
| 0. Extract | `run_exampass.py` | per-chapter `_extraction_bundle.json` + `chapter_manifest.json` |
| 1. Skeleton | `skeleton-agent` | `knowledge_skeleton.json` (chapter → KC DAG) + per-chapter slices |
| 2. Create | `notes-agent` + `item-agent` (parallel per chapter) | `notes/chN.html` + `questions/chN.json` |
| 3. Review/Revise | `reviewer-agent` + `solver-agent` (streaming per chapter) | diagnostics → targeted revision |
| 4. Render | `template_engine` | combined page (notes + quiz) per chapter |

All intermediate artifacts land in `.epa_work/`. The orchestrator (main Claude) only schedules — content is produced by sub-agents following agent cards in `agents/`.

### Use in Your Own Code

```python
from scripts.template_engine import (
    save_knowledge_html, save_test, save_graph_html, save_combined_html,
)
from scripts.slide_renderer import build_chapter_slides
from scripts.knowledge_graph import skeleton_to_graph_tree

# Knowledge guide — pass HTML body directly (engine adds H1 + TOC)
body = '<h2>1. Sequence Modeling</h2>\n<h3>1.1 What is Sequence Data</h3>\n<p>...</p>'
save_knowledge_html(body, 'knowledge.html', 'Chapter 15')

# Original-PPT cross-reference rail (renders PDF pages, embeds them as base64)
slides = build_chapter_slides(pdf_paths, '.epa_work/_slides',
                              density='key', skeleton=skeleton, chapter_label='Ch15')
save_knowledge_html(body, 'knowledge.html', 'Chapter 15', slides=slides, kcs=kcs)

# Interactive quiz — pass question data, get a self-grading page
questions = [
    {"type": "choice", "points": 2,
     "question": "What is the core function of a language model?",
     "options": ["Translation", "Estimating sentence probability",
                 "Tokenization", "Object recognition"],
     "answer": 1,
     "explanation": "A language model computes P(w1,...,wT)...",
     "pitfall": "Don't confuse language models with translation systems."},
]
save_test(questions, 'quiz.html', 'Chapter 15', '100 points', duration_minutes=30)

# Combined page — notes + quiz in one file with top tabs
save_combined_html(body, questions, 'chapter15.html', 'Chapter 15',
                   slides=slides, kcs=kcs, subtitle='28 questions')

# Knowledge graph — convert skeleton to interactive DAG visualization
tree = skeleton_to_graph_tree(skeleton)
save_graph_html(tree, 'graph.html', tree['title'])
```

### Project Structure

```
EPA/
├── SKILL.md                    # /exampass entry point (command routing)
├── agents/                     # Sub-agent cards (methodology + prompt)
│   ├── skeleton-agent.md       # Knowledge architect — builds chapter→KC DAG
│   ├── notes-agent.md          # Note writer — Hook→TL;DR→…→self-check arc
│   ├── item-agent.md           # Question writer — subject-aware question types
│   ├── reviewer-agent.md       # Content reviewer — correctness & completeness
│   └── solver-agent.md         # Exam solver — two-pass verification
├── scripts/                    # Core Python modules
│   ├── run_exampass.py         # Per-chapter extraction entry
│   ├── scanner.py              # Recursive scanning & grouping
│   ├── extractor.py            # Unified extraction dispatcher
│   ├── extract_pptx.py         # PPTX extraction
│   ├── extract_docx.py         # DOCX extraction
│   ├── extract_pdf.py          # PDF extraction
│   ├── image_extractor.py      # Embedded-image extraction for multimodal analysis
│   ├── ocr_backend.py          # OCR fallback for non-multimodal models
│   ├── template_engine.py      # HTML engine (knowledge, test, graph, combined page)
│   ├── slide_renderer.py       # Renders full PDF pages for the PPT cross-reference rail
│   ├── knowledge_graph.py      # Skeleton-to-graph-tree converter (+ fallback)
│   ├── html_generator.py       # Fast generator
│   ├── generate_cached.py      # Cache-based instant re-runs
│   ├── knowledge_analyzer.py   # Knowledge list prompt builder
│   ├── test_generator.py       # Quiz generation prompt builder
│   ├── exam_generator.py       # Final exam prompt builder
│   ├── web_research.py         # Web research
│   └── utils.py                # Shared utilities
├── templates/                  # CSS, JS & HTML templates
│   ├── base.css                # Shared styles (warm paper, dual-color, code panel)
│   ├── test.css                # Interactive quiz styles
│   ├── graph.css               # Knowledge graph styles (tree layout)
│   ├── graph.js                # Graph renderer (dashed deps, tooltips, note cards)
│   ├── page_template.html      # HTML page shell
│   ├── graph_template.html     # Graph HTML shell
│   ├── test_js_template.js     # Quiz JS template
│   └── test_labels.json        # Chinese UI labels
├── tests/                      # 146 test cases
└── requirements.txt
```

### v2.0 Changelog

**New features**
- **Original-PPT cross-reference rail** — `slide_renderer.py` renders whole PDF pages (`get_pixmap`) and pins them, with their original text (collapsible), beside each note; base64-embedded so the HTML stays a single shareable file. Density is selectable (`full` / `key` / `none`). Headings auto-get `[页N]` chips that scroll the rail to the matching slide.
- **Combined page** — `save_combined_html` puts the knowledge list and the interactive quiz in one file with top tabs (📖 Notes | 📝 Quiz).
- **Self-test answers** — every in-note checkpoint now carries a collapsible reference answer (ask-then-reveal, active recall).
- **`mock` command** — generate a fresh exam that imitates a real past paper (`--ref`) or the course's inferred exam style.
- **Pedagogy upgrade** — notes follow a Hook → TL;DR → Why → What → How → self-check arc for "get it in one read."
- **2× faster pipeline** — streaming per-chapter review/feedback/revise instead of waiting for every chapter; cache-skip of unchanged chapters.
- **Graph** — non-agent fallback (so Codex users get a real graph, not cards), draggable left/right split, mobile layout.
- **Code styling** — modern monospace stack + dark code panel for pseudocode/arrays.

**Robustness fixes (all verified with real-browser Playwright screenshots)**
- A raw `<` in question text (e.g. `low<high`) was parsed as an unclosed tag that swallowed every later question — now stray `<` is escaped while real tags are preserved.
- Notes emitted as full dark-themed HTML documents leaked their `<style>` and broke the page — now stripped to the body fragment.
- Long display formulas no longer overflow the column / the slide rail (auto-fit + scroll).
- Mobile horizontal-overflow, collapsed slide cards, and quiz cards rendering at 0 height (MathJax-in-hidden-panel) all fixed.

### Contributors

- Development & Maintenance: [@WUBING2023](https://github.com/WUBING2023)
- Inspirational Contribution: yaxing@cvc.uab.es
- Testing: [@YeMoonlight](https://github.com/YeMoonlight)
- Testing: [@Yuzhihan-zyr](https://github.com/Yuzhihan-zyr)

### License

[CC BY-NC 4.0](./LICENSE) — free to use, modify, and share for non-commercial purposes. Commercial use requires a separate license.

Copyright (c) 2025 ExamPass Assistant Contributors
