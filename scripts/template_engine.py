"""Template engine for ExamPass HTML generation.

Architecture:
  templates/page_template.html  -- HTML shell (__TITLE__, __CSS__, __BODY__, __EXTRA_JS__)
  templates/base.css            -- shared styles
  templates/test.css            -- quiz-specific styles
  templates/test_js_template.js -- JS for interactive quiz (__QUESTIONS_PLACEHOLDER__, __LABELS_PLACEHOLDER__)
  templates/test_labels.json    -- Chinese UI labels
"""

import os
import json

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')


def _read(filename):
    path = os.path.join(_TEMPLATES_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


_PAGE_TEMPLATE = _read('page_template.html')

_MATHJAX_CONFIG = '''<script>
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']]
  }
};
</script>'''

_MATHJAX_SCRIPT = (
    '<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"></script>'
)


def _build_page(title, body_html, css_extra='', js_extra=''):
    """Fill the page template. JS goes AFTER body -- critical for DOM access."""
    css = _read('base.css') + '\n' + css_extra
    return (
        _PAGE_TEMPLATE
        .replace('__TITLE__', title)
        .replace('__MATHJAX_CONFIG__', _MATHJAX_CONFIG)
        .replace('__MATHJAX_SCRIPT__', _MATHJAX_SCRIPT)
        .replace('__CSS__', css)
        .replace('__BODY__', body_html)
        .replace('__EXTRA_JS__', js_extra)
    )


# ─── Knowledge page ─────────────────────────────────────────────────

def save_knowledge_html(body_html, output_path, title):
    html = _build_page(title, body_html)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ─── Interactive test page ──────────────────────────────────────────

def save_test(questions, output_path, title, subtitle='', duration_minutes=30):
    """Generate an interactive test page.

    questions: list of {type, points, question, options, answer, explanation, pitfall}
    subtitle: optional custom subtitle (overrides auto-generated duration subtitle)
    duration_minutes: used in auto-generated subtitle if subtitle is empty
    """
    questions_json = json.dumps(questions, ensure_ascii=False)
    labels = json.loads(_read('test_labels.json'))
    labels_json = json.dumps(labels, ensure_ascii=False)

    js_template = _read('test_js_template.js')
    js = js_template.replace('__QUESTIONS_PLACEHOLDER__', questions_json)
    js = js.replace('__LABELS_PLACEHOLDER__', labels_json)
    js = '<script>\n' + js + '\n</script>'

    # Subtitle
    if subtitle:
        sub_html = '<p style="text-align:center;color:var(--ink-light);font-size:0.95em">' + subtitle + '</p>'
    else:
        sub_html = '<p style="text-align:center;color:var(--ink-light);font-size:0.95em">' + labels['duration_prefix'] + str(duration_minutes) + labels['duration_suffix'] + '</p>'

    body = '\n'.join([
        '<h1>' + title + '</h1>',
        '<h2 style="text-align:center">' + labels['page_title'] + '</h2>',
        sub_html,
        '',
        '<div id="score-box"><div class="score-num" id="score-num">0</div><div class="score-label">' + labels['score_label'] + '</div></div>',
        '<div id="questions-container"></div>',
        '<div class="grading-bar no-print"><button onclick="gradeAll()" id="grade-btn">' + labels['grade_button'] + '</button></div>',
    ])

    html = _build_page(title, body, css_extra=_read('test.css'), js_extra=js)
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
