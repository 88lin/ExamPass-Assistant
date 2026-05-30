---
name: exampass
description: 将课程资料（PPT/Word/PDF）按章节生成知识清单 PDF 和章节测试题 PDF，帮助高效期末复习。
---

# ExamPass Assistant

## 触发
用户调用 `/exampass`。

## 执行

使用 `scripts/template_engine.py` 中的 `save_knowledge()` 和 `save_test()` 快速生成。

- 知识清单：`save_knowledge(markdown_string, output_path, title)` — 自动套用暖色纸张模板
- 章节测试：`save_test(questions_list, output_path, title, subtitle)` — 自动套用交互式测试模板

两个模板的样式定义在 `templates/base.css` 和 `templates/test.css`。

## Steps

1. 递归扫描当前工作目录
2. 按文件夹分组（一章一组）
3. 每组：提取文字+表格+图片 → Claude 深度分析 → 生成知识清单 HTML（调用 `save_knowledge`）
4. 每组：基于内容生成交互式章节测试 HTML（调用 `save_test`，选项竖排、点击批改）
5. 所有输出放在对应章节文件夹下
6. 浏览器打开 HTML → Ctrl+P → 另存为 PDF（MathJax 公式完美渲染）
