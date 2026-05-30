# ExamPass Assistant

**把课堂讲义变成考试利器。** 一键将 PPT、Word、PDF 课件转化为结构清晰的知识清单和交互式测试题，让复习事半功倍。

> [English](./README_EN.md)

### 适用场景

| 角色 | 用途 |
|------|------|
| 大学生 | 上传课程 PPT/讲义 → 自动生成知识清单 + 章节测试（交互式选择+一键批改+逐题解析），高效通过期末考试 |
| 授课教师 | 将课件转化为结构化知识总结 → 一键生成配套习题 + 答案解析 → 直接用于课堂教学或课后作业布置 |
| 考研/考证 | 将参考书 PDF 转为精简知识清单，配合自测题检验掌握程度 |

### 核心功能

- 支持 PPTX / DOCX / PDF 三种格式，递归扫描目录，按章节自动分组
- 提取文字、表格、图片（Claude 多模态分析），保证内容无遗漏
- 生成**知识清单 HTML**：公式完美（MathJax 渲染）、层次分明、重点标注、目录导航
- 生成**交互式章节测试 HTML**：选项竖排、点击批改、逐题解析+易错提醒、自动计分
- 浏览器打开即可使用，Ctrl+P 打印为 PDF

### 安装

```bash
git clone https://github.com/yourname/exampass.git
cd exampass
pip install -r requirements.txt
```

**必需依赖**：[Pandoc](https://pandoc.org)（Markdown 转 HTML）

Windows: `winget install pandoc`
Mac: `brew install pandoc`
Linux: `sudo apt install pandoc`

### 使用方法

#### 1. 生成章节知识清单 + 测试题

在课程目录下调用 `/exampass`：

```
课程/
├── 第一章-绪论/
│   ├── 课件.pptx
│   └── 补充阅读.pdf
├── 第二章-基础/
│   └── lecture.pdf
└── 第三章-进阶/
    ├── slides.pptx
    └── handout.docx
```

每个章节文件夹下自动生成：
- `第一章-绪论-知识清单.html` — 结构化复习资料
- `第一章-绪论-章节测试.html` — 交互式自测
- `第一章-绪论-章节测试-答案.html` — 详细解析

#### 2. 生成仿真期末考试

在课程根目录下调用 `/exampass-final`，按提示配置难度、时长、题型分布，生成全课程综合试卷。

#### 3. 在代码中调用模板引擎

```python
from scripts.template_engine import save_knowledge, save_test

# 知识清单
save_knowledge(markdown_string, 'output.html', '章节标题')

# 交互式测试
questions = [
    {"type": "choice", "points": 2,
     "question": "语言模型的核心功能是什么？",
     "options": ["翻译", "评估句子概率", "分词", "识别物体"],
     "answer": 1,
     "explanation": "语言模型计算词序列概率...",
     "pitfall": "注意区分语言模型和机器翻译"},
    # ...更多题目
]
save_test(questions, 'test.html', '章节测试', '满分 100 分')
```

### 项目结构

```
EPA/
├── SKILL.md                    # /exampass 入口
├── exampass-final.md           # /exampass-final 入口
├── scripts/                    # 核心代码
│   ├── scanner.py              # 递归扫描与分组
│   ├── extractor.py            # 统一提取调度
│   ├── extract_pptx.py         # PPTX 提取
│   ├── extract_docx.py         # DOCX 提取
│   ├── extract_pdf.py          # PDF 提取
│   ├── image_extractor.py      # 图片提取
│   ├── markdown_to_pdf.py      # Markdown → HTML
│   ├── template_engine.py      # 模板引擎（知识清单+交互测试）
│   ├── knowledge_analyzer.py   # 知识清单分析
│   ├── test_generator.py       # 测试题生成
│   ├── exam_generator.py       # 期末试卷生成
│   ├── web_research.py         # 网络调研
│   └── utils.py                # 通用工具
├── templates/                  # 样式模板
│   ├── base.css                # 共享样式（暖色纸张背景）
│   └── test.css                # 测试页样式
├── tests/                      # 测试（102 个用例）
└── requirements.txt
```

### 许可证

本软件采用 **Creative Commons BY-NC 4.0** 许可证。

- 允许自由使用、修改、再分发
- 必须标注原作者署名
- **禁止商业用途**——不得将本软件或其衍生作品用于任何商业目的

完整条款见 [LICENSE](./LICENSE) 文件。

Copyright (c) 2025 ExamPass Assistant Contributors
