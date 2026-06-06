/loop 持续工作，直到所有开发完成、所有深度测试通过。

---

## 零、工作方式

- 使用 `/loop` 命令，让 Agent 在每个迭代中自我驱动，直到开发+测试全部完成
- 每个迭代结束，Agent 应更新 `progress.md` 记录进度
- 遇到不确定的设计决策，Agent 应主动提问而非自行假设
- **测试要求极深**：单元测试 + 集成测试 + 端到端测试（使用真实样例文件）+ 边界情况测试
- 所有测试必须 PASS 才能声称完成

---

## 一、项目概述

**ExamPass Assistant** 是一个期末考试辅助系统，包含两个 Skill：

| Skill | 用途 |
|-------|------|
| `exampass` | 将课程资料（PPT/Word/PDF）按章节转化为知识清单 PDF + 章节测试题 PDF |
| `exampass-final` | 读取整个文件夹下所有内容，生成仿真期末考试试卷 PDF + 答案 PDF |

---

## 二、技术架构（已决策）

| 决策项 | 选型 |
|--------|------|
| PPT 内容提取 | `python-pptx` — 提取文字、表格、图片 blob |
| Word 内容提取 | `python-docx` — 提取文字、表格、图片 blob |
| PDF 内容提取 | `pdfplumber`（文字+表格）+ `pymupdf`/fitz（图片提取） |
| 图片分析 | 提取图片保存为 PNG → 调用 Claude 多模态视觉分析 |
| 内容分析 & 题目生成 | 调用 Claude（Agent 自身），prompt 中传入提取的文本+图片 |
| 输出格式 | **Markdown → PDF**（pandoc + weasyprint 或 wkhtmltopdf） |
| 编程语言 | **Python 3.10+** |
| 用户界面语言 | **中文**（可切换英文） |
| web 信息搜集 | `WebSearch` 工具（找最佳实践、参考考题） |

### 关于图片提取的说明

- `python-pptx`：遍历 slide.shapes，对 `Picture` 类型通过 `shape.image.blob` 获取图片二进制，保存为 PNG
- `python-docx`：遍历 `document.inline_shapes` 或直接解压 docx（本质是 ZIP）读取 `word/media/` 目录
- `pymupdf`：`page.get_images()` 获取 PDF 内嵌图片
- 所有图片保存到临时目录，随后作为多模态输入传给 Claude 分析
- Claude 是多模态模型，可以"看懂"图表、公式截图、示意图

---

## 三、Skill 1：`exampass`（章节知识清单 + 章节测试）

### 3.1 触发方式

用户在任意课程目录下调用 `/exampass`。

### 3.2 工作流程

```
Step 1 — 扫描
  递归遍历当前工作目录，识别所有支持的文件：
    *.pptx, *.ppt  (PowerPoint)
    *.docx, *.doc  (Word)
    *.pdf          (PDF)

Step 2 — 分组
  按文件所在的**直接父目录**分组。一个文件夹 = 一章/一节课。
  例：
    课程/
    ├── 第一章-绪论/
    │   ├── 课件.pptx
    │   ├── 补充阅读.pdf
    │   └── 实验指导.docx
    │   → 这三个文件合并处理，输出到 第一章-绪论/ 下
    ├── 第二章-深度学习基础/
    │   ├── lecture2.pdf
    │   └── assignment.docx
    │   → 这两个文件合并处理，输出到 第二章-深度学习基础/ 下

Step 3 — 内容提取（对每组内每个文件）
  a. 文本提取：用对应 Python 库提取所有文字、表格
  b. 图片提取：提取所有图片到临时目录
  c. 结构化整理：按页码/幻灯片顺序组织内容

Step 4 — 知识清单生成（Claude 分析）
  对每组的内容，调用 Claude 生成知识清单。Prompt 核心要求：
  - 识别并提炼**核心知识点**（定义、定理、公式、关键概念）
  - 提炼**重点解题方法**（步骤、技巧、常见陷阱）
  - 标注**考试高频考点**（基于内容中的强调、重复出现、例题分布）
  - 用 Markdown 组织为清晰的层级结构
  - 公式用 LaTeX 语法（$...$ 或 $$...$$），后续 pandoc 渲染

  Agent 应先用 WebSearch 搜索以下内容来优化 prompt：
  - "how to create effective study guides from lecture slides AI prompt"
  - "best practices for extracting exam key points from course materials"
  - "knowledge distillation from PowerPoint to study notes prompt engineering"

Step 5 — 生成知识清单 PDF
  Markdown → pandoc → PDF（带目录、页码、章节标题格式）
  文件名：`[原文件夹名]-知识清单.pdf`
  输出位置：该章节文件夹下

Step 6 — 生成章节测试题（Claude 分析）
  基于同一组内容，调用 Claude 生成测试题。题型：
  - 选择题（4 选项，考察概念理解）
  - 填空题（关键词/公式挖空）
  - 简答题（考察解题方法应用）
  - 题量：按内容量自动决定，一般 5-15 题

  Agent 应先用 WebSearch 搜索：
  - "how to generate effective practice test questions from study materials AI"
  - "spaced repetition test question design best practices"
  - "Bloom's taxonomy test question generation prompt"

Step 7 — 生成章节测试 PDF + 答案 PDF
  输出两个文件：
  - `[原文件夹名]-章节测试.pdf`（纯题目）
  - `[原文件夹名]-章节测试-答案.pdf`（题目+答案+解析）
  输出位置：该章节文件夹下
```

### 3.3 注意事项

- 如果某文件夹已存在输出的 PDF，询问用户是否覆盖
- 图片分析结果应融入知识清单（而非仅依赖文字）
- 知识清单风格：**简洁、结构化、适合打印**
- 支持批量处理：一次调用处理当前目录下所有章节

---

## 四、Skill 2：`exampass-final`（仿真期末考试）

### 4.1 触发方式

用户在课程根目录下调用 `/exampass-final`。

### 4.2 交互式配置

调用后，Agent 必须**以对话形式**询问用户以下参数：

1. **考试难度**（选项）：
   - 简单（基础概念为主，60% 送分题）
   - 中等（概念+应用，30% 综合题）
   - 困难（大量综合应用，参考 985 高校标准）
   - 自定义描述

2. **考试时长**（分钟）：
   - 90 分钟 / 120 分钟 / 180 分钟 / 自定义

3. **题型分布偏好**（可选）：
   - 默认：选择题 30% + 填空题 20% + 简答题 30% + 综合题 20%
   - 或用户自定义比例

4. **是否搜索网络参考题**（默认：是）：
   - 搜索 "211/985 [课程名] 期末考试题"
   - 搜索 "[课程名] final exam questions top university"
   - 参考其题型风格、难度分布、出题思路

### 4.3 工作流程

```
Step 1 — 收集全局内容
  递归扫描当前目录下所有 *.pdf 文件（特别是之前生成的知识清单 PDF）
  提取所有文本内容，按章节组织

Step 2 — 网络调研
  使用 WebSearch 搜索类似课程的期末考题（211/985）
  提取：题型分布、难度特征、常见考点覆盖方式
  同时搜索：
  - "university final exam question design principles"
  - "how to create comprehensive final exam blueprint"

Step 3 — 生成试卷
  调用 Claude，传入：
  - 所有章节内容摘要
  - 用户配置（难度、时长、题型分布）
  - 网络调研结果
  要求 Claude 像一位教授一样出题：
  - 覆盖所有章节的知识点
  - 重点章节权重更高
  - 难度与配置一致
  - 题目之间独立（不相互暗示答案）
  - 包含：试卷标题、考试说明、分值标注、题号清晰

Step 4 — 生成试卷 PDF + 答案 PDF
  输出两个文件：
  - `期末考试-[课程名].pdf`（纯试卷）
  - `期末考试-[课程名]-答案.pdf`（详细答案+评分标准+解析）
  输出位置：课程根目录
```

### 4.4 试卷质量标准

- 题量匹配时长（90 分钟约 25-35 题，120 分钟约 35-50 题）
- 分值总和 = 100 分（或用户指定满分）
- 每道题标注分值
- 答案 PDF 中每道题附详细解析，不只是给出答案
- 简答题答案包含评分要点和满分标准

---

## 五、文件结构

Agent 应在 `M:\skills\EPA` 下创建如下结构：

```
M:\skills\EPA\
├── SKILL.md                      # Skill 入口文件（exampass）
├── exampass-final.md             # Skill 入口文件（exampass-final）
├── scripts/
│   ├── extract_pptx.py           # PPTX 内容提取
│   ├── extract_docx.py           # DOCX 内容提取
│   ├── extract_pdf.py            # PDF 内容提取
│   ├── extractor.py              # 统一的提取调度器（根据文件类型分发）
│   ├── scanner.py                # 递归扫描 + 按文件夹分组
│   ├── markdown_to_pdf.py        # Markdown → PDF 转换（pandoc）
│   ├── knowledge_analyzer.py     # 调用 Claude 生成知识清单
│   ├── test_generator.py         # 调用 Claude 生成测试题
│   ├── exam_generator.py         # 调用 Claude 生成期末试卷
│   ├── web_research.py           # WebSearch 封装
│   ├── image_extractor.py        # 图片提取通用逻辑
│   └── utils.py                  # 通用工具
├── templates/
│   ├── knowledge_template.md     # 知识清单 Markdown 模板
│   ├── chapter_test_template.md  # 章节测试 Markdown 模板
│   └── exam_template.md          # 期末试卷 Markdown 模板
├── tests/
│   ├── test_samples/             # 测试用样例文件（真实的 .pptx, .docx, .pdf）
│   ├── conftest.py               # pytest fixtures
│   ├── test_extract_pptx.py
│   ├── test_extract_docx.py
│   ├── test_extract_pdf.py
│   ├── test_image_extractor.py
│   ├── test_scanner.py
│   ├── test_markdown_to_pdf.py
│   ├── test_knowledge_analyzer.py
│   ├── test_test_generator.py
│   ├── test_exam_generator.py
│   ├── test_integration.py       # 完整流程集成测试
│   └── test_e2e.py              # 端到端测试（用真实样例跑完整流程）
├── requirements.txt
├── progress.md                   # 开发进度追踪
└── README.md                     # 用户使用说明（中文）
```

---

## 六、Python 依赖

`requirements.txt` 至少包含：

```
python-pptx
python-docx
pdfplumber
pymupdf
pandoc
weasyprint
pytest
pytest-mock
Pillow
markdown
```

---

## 七、开发工作流（Loop 自我驱动）

Agent 应创建 `progress.md` 追踪进度，格式：

```markdown
# ExamPass 开发进度

## 当前阶段：[阶段名]
## 开始时间：[timestamp]

### 已完成
- [x] xxx

### 进行中
- [ ] xxx

### 待完成
- [ ] xxx

### 测试状态
- 单元测试：X/Y PASS
- 集成测试：X/Y PASS
- E2E 测试：X/Y PASS

### 遇到的问题
- [记录阻塞问题]
```

Agent 每轮 loop 应：
1. 读取 `progress.md` 了解当前进度
2. 完成一个有意义的工作单元（一个函数/一个模块/一组测试）
3. 运行相关测试确保不退化
4. 更新 `progress.md`
5. 自我评估是否完成所有任务

---

## 八、深度测试要求（极重要）

### 8.1 单元测试（每个模块必须覆盖）

| 模块 | 测试要点 |
|------|---------|
| `extract_pptx.py` | 文字提取、表格提取、**图片提取**、空幻灯片、多级标题、中文编码 |
| `extract_docx.py` | 文字提取、表格提取、**图片提取**、页眉页脚、列表、中文编码 |
| `extract_pdf.py` | 文字提取、表格提取、**图片提取**、多页、扫描版 PDF（纯图片）、加密 PDF |
| `scanner.py` | 多层嵌套目录、空目录、混合文件类型、纯文件无目录 |
| `markdown_to_pdf.py` | LaTeX 公式渲染、中文渲染、表格渲染、图片嵌入、目录生成 |
| `image_extractor.py` | PNG/JPG/EMF/WMF 格式、损坏图片处理、无图片文件处理 |

### 8.2 集成测试

- 单文件处理全流程（PPTX → 知识清单 PDF → 章节测试 PDF）
- 多文件合并处理全流程（PPTX + PDF + DOCX → 一个知识清单 PDF）
- 多章节批量处理全流程
- 期末试卷生成全流程

### 8.3 端到端测试

- **准备真实样例文件**（Agent 需自己创建包含文字、表格、图片的样例 .pptx, .docx, .pdf）
- 在样例目录下运行完整流程，验证输出的 PDF 文件存在且非空
- 验证 PDF 内容包含预期的关键文字
- 模拟真实使用场景：嵌套目录结构下多章节处理

### 8.4 边界测试

- 空文件/损坏文件处理（不崩溃，给出清晰错误提示）
- 超大文件处理（100+ 页 PDF / 200+ 幻灯片 PPTX）
- 纯图片文件（无文字提取可能）→ 应 fallback 到纯视觉分析
- 加密文件处理 → 提示用户解锁
- 文件名含特殊字符 / 中文 / 空格

### 8.5 质量测试

- 生成的知识清单 PDF 必须包含：标题层级、知识点列表、解题方法、考点标注
- 生成的测试题必须：题干完整、选项互斥、答案正确、附解析
- 期末试卷必须：分值总和正确、题型分布符合配置、覆盖所有章节

---

## 九、Skill 入口文件格式

### SKILL.md（exampass 主 skill）

```markdown
---
name: exampass
description: 将课程资料（PPT/Word/PDF）按章节生成知识清单 PDF 和章节测试题 PDF，帮助高效期末复习。
---

# ExamPass Assistant

## 触发
用户调用 `/exampass`。

## 执行
运行 Python 脚本执行完整流程。详见 `scripts/` 目录。

## Steps

1. 递归扫描当前工作目录
2. 按文件夹分组（一章一组）
3. 每组：提取文字+表格+图片 → Claude 分析 → 生成知识清单 PDF
4. 每组：基于内容生成章节测试题 PDF + 答案 PDF
5. 所有输出放在对应章节文件夹下
```

### exampass-final.md（期末试卷子 skill）

```markdown
---
name: exampass-final
description: 读取整个课程目录，搜索网络参考题，生成仿真期末考试试卷 PDF + 答案 PDF。支持配置难度、时长、题型分布。
---

# ExamPass Final Exam

## 触发
用户调用 `/exampass-final`。

## 交互
询问用户：考试难度、时长、题型偏好、是否搜索网络参考题。

## 执行
运行 Python 脚本收集全局内容 → 网络调研 → Claude 出题 → 生成试卷 PDF + 答案 PDF。

## Steps

1. 交互式收集用户配置
2. 递归读取目录下所有知识清单 PDF
3. WebSearch 搜索 211/985 类似课程期末考题
4. Claude 综合出题（像教授一样）
5. 生成试卷 PDF + 答案 PDF（含详细解析+评分标准）
```
```

---

## 十、验收标准（Agent 完成前必须全部达成）

- [ ] 所有单元测试 PASS（覆盖率 ≥ 80%）
- [ ] 所有集成测试 PASS
- [ ] E2E 测试 PASS（用真实样例文件）
- [ ] 知识清单 PDF 内容完整、格式清晰
- [ ] 章节测试 PDF 题目+答案分两个文件
- [ ] 期末试卷 PDF 题量匹配时长、分值正确
- [ ] 图片提取和分析功能正常
- [ ] 中文渲染无乱码
- [ ] 支持嵌套目录批量处理
- [ ] 用户使用说明（README.md）完整

---

## 十一、进度文件初始内容

Agent 开始时应创建以下 `progress.md`：

```markdown
# ExamPass 开发进度

## 当前阶段：环境搭建
## 开始时间：[启动时填写]

### 已完成

### 进行中
- [ ] 创建项目文件结构
- [ ] 安装 Python 依赖

### 待完成
- [ ] 内容提取模块（PPTX、DOCX、PDF）
- [ ] 图片提取模块
- [ ] 扫描与分组模块
- [ ] Markdown → PDF 转换模块
- [ ] 知识清单分析模块
- [ ] 章节测试生成模块
- [ ] 期末试卷生成模块
- [ ] 网络调研模块
- [ ] Skill 入口文件
- [ ] 单元测试
- [ ] 集成测试
- [ ] E2E 测试
- [ ] README 用户文档

### 测试状态
- 单元测试：0/0 PASS
- 集成测试：0/0 PASS
- E2E 测试：0/0 PASS
```
```

---

## 十二、补充说明

1. **所有与 Claude 的交互**（内容分析、出题）通过 Agent 工具或直接在当前会话中完成，不依赖外部 API key。Agent 本身就是 Claude，直接编写分析 prompt 并在代码中通过子 agent 调用。

2. **Pandoc 安装检查**：脚本启动时应检查 pandoc 是否可用，不可用时给出安装指引：
   - Windows: `winget install pandoc` 或下载 pandoc.org
   - Mac: `brew install pandoc`
   - Linux: `apt-get install pandoc`

3. **WeasyPrint 安装**：Windows 下可能需要额外处理，Agent 应测试并写清安装说明。

4. **设计上保持克制**：不要过度抽象，不要为"未来可能需要"设计。代码简洁直接。

5. **遇到不确定的点**：Agent 必须主动提问，不要自行假设实现细节。
