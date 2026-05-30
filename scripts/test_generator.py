"""Prepare prompts and assemble markdown for chapter test generation."""


def build_test_prompt(text_summary: str, knowledge_markdown: str = "", question_count: int = None) -> str:
    """
    Build the analysis prompt for Claude to generate chapter test questions.
    Returns a structured test with questions and answers.
    """
    count_guide = ""
    if question_count:
        count_guide = f"\n请生成大约 {question_count} 道题目。"

    prompt = f"""你是一位大学课程命题专家。请根据以下课程资料，生成一套**章节测试题**。{count_guide}

## 命题要求

### 题型配比
- **选择题**（约 50%）：4 个选项，考察概念理解和辨析。选项应有迷惑性但保证唯一正确答案。
- **填空题**（约 20%）：挖空关键词、公式或数值。每空分值标清。
- **简答题**（约 30%）：考察解题方法应用和知识串联，要求写出关键步骤。

### 质量要求
- 题目之间**相互独立**，不暗示其他题目的答案
- 覆盖资料中的**核心知识点**，重点内容可多出
- 难度梯度：60% 基础 + 30% 提高 + 10% 综合
- 选择题选项长度相近，干扰项要有真实来源（常见错误理解）
- 每道题标注**分值**

### 输出格式

先输出**纯题目部分**，用 `## 题目` 标记开始。
然后输出**答案与解析部分**，用 `## 答案与解析` 标记开始。

答案部分要求：
- 选择题：给正确答案 + **每个选项为什么对/错**
- 填空题：给正确答案 + **相关知识点的简要说明**
- 简答题：给**完整解题过程** + **评分要点** + **满分标准**

---

## 课程资料内容

{text_summary}
"""

    if knowledge_markdown:
        prompt += f"\n\n---\n\n## 本章知识清单（供参考）\n\n{knowledge_markdown}\n"

    prompt += """

---

请严格按照以上要求输出，先输出"## 题目"，再输出"## 答案与解析"。
"""
    return prompt


def split_test_and_answer(full_output: str) -> tuple:
    """Split combined output into (questions_only, answers_only)."""
    if "## 答案与解析" in full_output:
        parts = full_output.split("## 答案与解析", 1)
        questions = parts[0].strip()
        answers = "## 答案与解析\n" + parts[1].strip()
        return questions, answers
    elif "## 答案" in full_output:
        parts = full_output.split("## 答案", 1)
        questions = parts[0].strip()
        answers = "## 答案\n" + parts[1].strip()
        return questions, answers
    else:
        return full_output, ""


def build_test_markdown(questions: str, title: str) -> str:
    """Wrap questions into a standalone test markdown."""
    return f"""---
title: "{title} - 章节测试"
lang: zh-CN
---

# {title}

## 章节测试

> 说明：请独立完成，闭卷作答。

{questions}
"""


def build_answer_markdown(answers: str, title: str) -> str:
    """Wrap answers into a standalone answer markdown."""
    return f"""---
title: "{title} - 章节测试答案与解析"
lang: zh-CN
---

# {title}

## 章节测试 · 答案与解析

{answers}
"""
