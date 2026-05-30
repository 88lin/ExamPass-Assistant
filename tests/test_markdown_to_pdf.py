"""Tests for markdown_to_pdf.py (now outputs .html)."""

import os
import pytest
from markdown_to_pdf import markdown_to_pdf, markdown_to_html


SAMPLE_MARKDOWN = """---
title: "测试文档"
lang: zh-CN
---

# 第一章 测试

## 1.1 基本概念

这是一个测试段落。包含一些**加粗**和*斜体*文字。

测试公式：$E = mc^2$

$$\\sum_{i=1}^{n} x_i = \\bar{x}$$

### 1.1.1 子节

| 名称 | 数值 | 描述 |
|------|------|------|
| Alpha | 1.0 | 学习率 |
| Beta | 0.9 | 动量 |

> **重点**：这是一个重要的知识点。

- 项目1
- 项目2
- 项目3
"""


class TestMarkdownToPDF:
    def test_basic_conversion(self, temp_dir):
        output = os.path.join(temp_dir, "test_output.html")
        result = markdown_to_pdf(SAMPLE_MARKDOWN, output)
        assert result is True
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

    def test_chinese_content(self, temp_dir):
        md = """---
title: "中文测试"
lang: zh-CN
---

# 机器学习基础

机器学习是人工智能的一个重要分支。

## 监督学习

监督学习使用带标签的数据进行训练。
"""
        output = os.path.join(temp_dir, "chinese_test.html")
        result = markdown_to_pdf(md, output)
        assert result is True
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0

    def test_math_formulas(self, temp_dir):
        md = """# 公式测试

行内公式：$f(x) = wx + b$

独立公式：

$$\\frac{\\partial L}{\\partial w} = \\frac{1}{n}\\sum_{i=1}^{n} 2(y_i - \\hat{y}_i)(-x_i)$$

矩阵：

$$\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}$$
"""
        output = os.path.join(temp_dir, "math_test.html")
        result = markdown_to_pdf(md, output)
        assert result is True

    def test_table_rendering(self, temp_dir):
        md = """# 表格测试

| 算法 | 准确率 | 训练时间 |
|------|--------|----------|
| SVM | 95.2% | 120s |
| Random Forest | 94.8% | 85s |
| XGBoost | 96.1% | 200s |
| Neural Network | 95.5% | 600s |
"""
        output = os.path.join(temp_dir, "table_test.html")
        result = markdown_to_pdf(md, output)
        assert result is True

    def test_empty_content(self, temp_dir):
        output = os.path.join(temp_dir, "empty.html")
        result = markdown_to_pdf("# Empty\n", output)
        assert result is True

    def test_invalid_output_path(self, temp_dir):
        output = os.path.join(temp_dir, "nonexistent", "out.html")
        result = markdown_to_pdf("# test", output)
        # Should handle gracefully — pandoc will fail on nonexistent dir
        assert isinstance(result, bool)

    def test_output_overwrites(self, temp_dir):
        output = os.path.join(temp_dir, "overwrite.html")
        markdown_to_pdf("# First\n", output)
        markdown_to_pdf("# Second\n", output)
        assert os.path.exists(output)
