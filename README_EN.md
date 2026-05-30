# ExamPass Assistant

**Turn lecture slides into exam-ready study materials.**

> [中文](./README.md)

---

### What is this

An AI-powered exam prep assistant. Drop in your lecture PPTs, Word handouts, or PDF readings — it generates:

- **Knowledge Guides** — structured review notes with perfect formula rendering, priority labels, and table-of-contents navigation
- **Interactive Quizzes** — answer online, one-click grading, per-question explanations with common mistake warnings

Open in any browser. No PDF engine needed. Formulas rendered by MathJax. Ctrl+P to print.

### Why

The universal pain of finals week: scattered lecture files, no idea what's actually on the exam, no reliable practice questions.

ExamPass reads your course materials with Claude → extracts key points → generates quizzes → grades them. Students use it to study smarter. Instructors use it to create exercises and assignments in seconds.

### Supported Formats

PPTX · DOCX · PDF (with image recognition via multimodal analysis)

### Quick Start

```bash
git clone https://github.com/yourname/exampass.git
cd exampass
pip install -r requirements.txt
```

**Requires [Pandoc](https://pandoc.org)**:
- Windows: `winget install pandoc`
- Mac: `brew install pandoc`
- Linux: `sudo apt install pandoc`

### Usage

**Generate chapter study materials** — run `/exampass` in any course directory. The skill scans subfolders, groups files by chapter, extracts all content, and outputs knowledge guides + interactive quizzes into each folder.

**Generate a final exam** — run `/exampass-final` in the course root. Configure difficulty, duration, and question distribution. The skill reads all chapter content and produces a comprehensive exam with answer key.

**Use in your own code**:

```python
from scripts.template_engine import save_knowledge, save_test

# Knowledge guide from markdown
save_knowledge(markdown_string, 'output.html', 'Chapter Title')

# Interactive quiz from structured data
questions = [
    {"type": "choice", "points": 2,
     "question": "What is the core function of a language model?",
     "options": ["Translation", "Estimating sentence probability",
                 "Tokenization", "Object recognition"],
     "answer": 1,
     "explanation": "A language model computes P(w1,...,wT)...",
     "pitfall": "Don't confuse language models with translation systems."},
]
save_test(questions, 'quiz.html', 'Chapter Quiz', '100 points total')
```

### How It Works

1. **Scan & Group** — recursively finds all PPTX/DOCX/PDF files, groups by parent folder (one chapter per folder)
2. **Extract** — pulls text, tables, and embedded images from each file
3. **Analyze** — Claude reads the content, identifies key concepts, formulas, solution methods, and exam-relevant patterns
4. **Generate** — produces styled HTML with MathJax formulas and interactive quiz logic

### Project Structure

```
EPA/
├── SKILL.md                    # /exampass entry point
├── exampass-final.md           # /exampass-final entry point
├── scripts/                    # Core Python modules
│   ├── scanner.py              # Recursive scanning & grouping
│   ├── extractor.py            # Unified extraction dispatcher
│   ├── extract_pptx.py         # PPTX extraction
│   ├── extract_docx.py         # DOCX extraction
│   ├── extract_pdf.py          # PDF extraction
│   ├── image_extractor.py      # Image extraction for multimodal analysis
│   ├── template_engine.py      # HTML template engine (knowledge + quiz)
│   ├── knowledge_analyzer.py   # Knowledge list prompt builder
│   ├── test_generator.py       # Quiz generation prompt builder
│   ├── exam_generator.py       # Final exam prompt builder
│   ├── web_research.py         # Web search utilities
│   └── utils.py
├── templates/                  # CSS stylesheets
│   ├── base.css                # Shared styles (warm paper background)
│   └── test.css                # Interactive quiz styles
├── tests/                      # 102 test cases
└── requirements.txt
```

### License

[CC BY-NC 4.0](./LICENSE) — free to use, modify, and share for non-commercial purposes. Commercial use requires a separate license.

Copyright (c) 2025 ExamPass Assistant Contributors
