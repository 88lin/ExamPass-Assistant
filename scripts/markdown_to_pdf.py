"""Convert Markdown to styled HTML. Uses ExamPass templates."""

import os

from template_engine import save_knowledge


def markdown_to_html(markdown_content: str, output_path: str) -> bool:
    """Convert Markdown to a styled, self-contained HTML file with MathJax."""
    try:
        save_knowledge(markdown_content, output_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 100
    except Exception as e:
        print(f"转换失败: {e}")
        return False


def markdown_to_pdf(markdown_content, output_path):
    """Backward-compat. Always outputs .html."""
    if output_path.endswith('.pdf'):
        output_path = output_path[:-4] + '.html'
    return markdown_to_html(markdown_content, output_path)
