# Knowledge Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/exampass graph` command that generates an interactive horizontal knowledge tree from course materials.

**Architecture:** Python script builds a prompt, Claude structures extracted content into a tree JSON, template engine embeds the JSON into a self-contained HTML page. The HTML page uses vanilla JS to render the tree with columns-per-level layout, SVG bezier connections, inline edit panels, and localStorage persistence.

**Tech Stack:** Python 3, vanilla HTML/CSS/JS (no frameworks), MathJax (for formula nodes if needed)

---

### Task 1: Create `scripts/knowledge_graph.py`

**Files:**
- Create: `scripts/knowledge_graph.py`
- Create: `tests/test_knowledge_graph.py`

- [ ] **Step 1: Write tests for prompt builder and JSON parser**

```python
"""Tests for knowledge_graph module."""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from knowledge_graph import build_graph_prompt, parse_graph_response, validate_tree_json


def test_build_graph_prompt_contains_text_summary():
    prompt = build_graph_prompt("第一章 深度学习基础\n神经网络概念")
    assert "第一章 深度学习基础" in prompt
    assert "神经网络概念" in prompt
    assert "知识树" in prompt or "tree" in prompt.lower()
    assert "JSON" in prompt


def test_build_graph_prompt_has_schema():
    prompt = build_graph_prompt("test content")
    assert '"id"' in prompt
    assert '"label"' in prompt
    assert '"children"' in prompt
    assert '"summary"' in prompt


def test_build_graph_prompt_empty_content():
    prompt = build_graph_prompt("")
    assert len(prompt) > 0


def test_parse_graph_response_valid_json():
    response = '''```json
{
  "title": "深度学习",
  "nodes": [
    {"id": "n1", "label": "第1章", "summary": "概述", "children": []}
  ]
}
```'''
    result = parse_graph_response(response)
    assert result["title"] == "深度学习"
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["id"] == "n1"


def test_parse_graph_response_no_code_block():
    response = '{"title": "test", "nodes": []}'
    result = parse_graph_response(response)
    assert result["title"] == "test"


def test_validate_tree_json_valid():
    data = {
        "title": "课程",
        "nodes": [
            {"id": "n1", "label": "章", "summary": "s", "children": [
                {"id": "n2", "label": "节", "summary": "s2", "children": []}
            ]}
        ]
    }
    validate_tree_json(data)  # should not raise


def test_validate_tree_json_missing_title():
    import pytest
    with pytest.raises(ValueError, match="title"):
        validate_tree_json({"nodes": []})


def test_validate_tree_json_duplicate_ids():
    import pytest
    data = {
        "title": "t",
        "nodes": [
            {"id": "n1", "label": "a", "summary": "s", "children": []},
            {"id": "n1", "label": "b", "summary": "s", "children": []}
        ]
    }
    with pytest.raises(ValueError, match="duplicate"):
        validate_tree_json(data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_knowledge_graph.py -v`
Expected: All FAIL (module not found)

- [ ] **Step 3: Implement `knowledge_graph.py`**

```python
"""Knowledge graph prompt builder and JSON utilities.

Generates the prompt that asks Claude to structure extracted course
content into a hierarchical knowledge tree, then parses and validates
the response.
"""

import json
import re
import uuid


def build_graph_prompt(text_summary: str) -> str:
    return f"""你是一位资深的大学课程辅导专家。请根据以下课程资料，生成一份**知识树结构**，用作交互式知识图谱。

## 输出要求

输出严格的 JSON 格式，不含其他文字：

```json
{{
  "title": "课程名称",
  "nodes": [
    {{
      "id": "n1",
      "label": "第1章 XXX",
      "summary": "从PPT原文提取的章节概述，1-2句话",
      "children": [
        {{
          "id": "n2",
          "label": "核心概念/知识点",
          "summary": "PPT关于该知识点的关键表述",
          "children": [
            {{"id": "n3", "label": "具体公式/方法", "summary": "关键细节", "children": []}}
          ]
        }}
      ]
    }}
  ]
}}
```

## 构建规则

1. **根节点**：`title` 是课程名称，`nodes` 是顶层章节列表。
2. **Lv1 章节**：每个章节目录对应一个 Lv1 节点。单章课程也正常只有 1 个 Lv1 节点。
3. **Lv2+ 知识点**：逐层细化。中间节点带 `children`，叶子节点 `children: []`。
4. **深度**：3-5 层为宜。每个 Lv1 章节下至少 2 个 Lv2 知识点。
5. **id 唯一**：使用 "n1", "n2" ... 全局递增，不可重复。
6. **summary**：每个节点必须从 PPT 原文提取摘要，1-2 句话。
7. **叶子节点**：深入到具体概念、公式、方法、题型。

## 课程资料

{text_summary}
"""


def parse_graph_response(response: str) -> dict:
    """Extract and parse JSON from Claude's response (may contain markdown fences)."""
    # Try to find JSON in markdown code block
    m = re.search(r'```(?:json)?\s*\n(.*?)\n```', response, re.DOTALL)
    if m:
        json_str = m.group(1)
    else:
        # Try to find raw JSON object
        m = re.search(r'\{[\s\S]*"title"[\s\S]*"nodes"[\s\S]*\}', response)
        if m:
            json_str = m.group(0)
        else:
            json_str = response

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e}. 原始响应前200字符: {response[:200]}")

    validate_tree_json(data)
    return data


def validate_tree_json(data: dict):
    """Validate knowledge tree JSON structure. Raises ValueError on problems."""
    if not isinstance(data, dict):
        raise ValueError("根必须是 JSON 对象")
    if "title" not in data:
        raise ValueError("缺少 'title' 字段")
    if "nodes" not in data:
        raise ValueError("缺少 'nodes' 字段")
    if not isinstance(data["nodes"], list):
        raise ValueError("'nodes' 必须是数组")

    ids = set()

    def walk(nodes):
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError(f"节点必须是对象: {node}")
            if "id" not in node:
                raise ValueError(f"节点缺少 id: {node}")
            if "label" not in node:
                raise ValueError(f"节点 {node.get('id', '?')} 缺少 label")
            if "summary" not in node:
                raise ValueError(f"节点 {node.get('id', '?')} 缺少 summary")
            nid = node["id"]
            if nid in ids:
                raise ValueError(f"重复 id: {nid}")
            ids.add(nid)
            if "children" in node:
                if not isinstance(node["children"], list):
                    raise ValueError(f"节点 {nid} 的 children 必须是数组")
                walk(node["children"])

    walk(data["nodes"])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_knowledge_graph.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/knowledge_graph.py tests/test_knowledge_graph.py
git commit -m "feat: add knowledge_graph prompt builder and JSON parser"
```

---

### Task 2: Create HTML template and CSS

**Files:**
- Create: `templates/graph_template.html`
- Create: `templates/graph.css`

- [ ] **Step 1: Create `templates/graph_template.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>__TITLE__ - 知识图谱</title>
<style>
__CSS__
</style>
</head>
<body>

<header id="graph-header">
  <div class="header-left">
    <span class="header-brand">ExamPass Assistant</span>
    <span class="header-sep">|</span>
    <span class="header-title" id="header-title">__TITLE__ - 知识图谱</span>
  </div>
  <div class="header-right">
    <input type="text" id="search-input" placeholder="搜索知识点..." />
    <button id="reset-btn" title="重置视图">↺</button>
  </div>
</header>

<div id="graph-viewport">
  <div id="graph-canvas"></div>
  <svg id="connections-layer"></svg>
</div>

<div id="zoom-bar">
  <button id="zoom-out">−</button>
  <input type="range" id="zoom-slider" min="50" max="200" value="100" step="10" />
  <button id="zoom-in">+</button>
  <span id="zoom-label">100%</span>
</div>

<div id="tooltip" class="tooltip-hidden"></div>

<div id="toast"></div>

<script>
__TREE_DATA__
</script>
<script>
__JS__
</script>
</body>
</html>
```

- [ ] **Step 2: Create `templates/graph.css`**

```css
/* === ExamPass Knowledge Graph Styles === */

:root {
  --bg: #faf8f5;
  --ink: #3c3c3c;
  --ink-light: #888;
  --divider: #e0dcd5;
  --branch-0: #d4c5b9;
  --branch-1: #c5d5cb;
  --branch-2: #d5cec0;
  --branch-3: #c8d0d8;
  --branch-4: #d0c8c0;
  --branch-5: #ccd4c8;
  --node-radius: 8px;
  --edit-bg: #fefdfa;
  --highlight: #f0e8c0;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Microsoft YaHei", "Noto Sans SC", "SimSun", sans-serif;
  font-size: 13px; line-height: 1.6; color: var(--ink);
  background: var(--bg); overflow-x: hidden;
}

/* ── Header ── */
#graph-header {
  position: sticky; top: 0; z-index: 100;
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 20px; background: var(--bg);
  border-bottom: 1px solid var(--divider);
}
.header-left { display: flex; align-items: baseline; gap: 10px; }
.header-brand { font-size: 1.1em; font-weight: 700; color: #1a1a2e; letter-spacing: 0.3px; }
.header-sep { color: var(--divider); }
.header-title { font-size: 0.95em; color: var(--ink-light); }
.header-right { display: flex; gap: 8px; align-items: center; }
#search-input {
  width: 200px; padding: 4px 10px; border: 1px solid var(--divider);
  border-radius: 4px; font-size: 0.9em; background: #fff; outline: none;
}
#search-input:focus { border-color: #aaa; }
#reset-btn {
  background: none; border: 1px solid var(--divider); border-radius: 4px;
  padding: 4px 10px; cursor: pointer; font-size: 1.1em; color: var(--ink-light);
}
#reset-btn:hover { background: #f0ede5; }

/* ── Viewport ── */
#graph-viewport {
  position: relative;
  width: 100%; min-height: calc(100vh - 90px);
  overflow: auto;
}
#graph-canvas {
  position: relative;
  padding: 40px 40px 200px 40px;
  transform-origin: top left;
  display: flex; gap: 0;
}
#connections-layer {
  position: absolute; top: 0; left: 0;
  pointer-events: none; z-index: 0;
}

/* ── Level columns ── */
.gl {
  display: flex; flex-direction: column;
  min-width: 220px; max-width: 320px;
  padding: 0 16px; position: relative; z-index: 1;
}
.gl:first-child { padding-left: 0; }

/* ── Nodes ── */
.gn {
  position: relative;
  background: #fff;
  border: 1px solid var(--divider);
  border-left: 3px solid var(--divider);
  border-radius: var(--node-radius);
  padding: 8px 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
  user-select: none;
  z-index: 2;
}
.gn:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-color: #c0b8a8; }
.gn:active { box-shadow: 0 1px 4px rgba(0,0,0,0.06); }

.gn-label { font-weight: 600; color: var(--ink); font-size: 0.95em; display: block; }

.gn-badge {
  position: absolute; top: -4px; right: -4px;
  width: 10px; height: 10px; border-radius: 50%;
  background: #8cb88c; border: 1px solid #fff;
  display: none;
}
.gn.has-notes .gn-badge { display: block; }

.gn.collapsed { opacity: 0.5; }
.gn.collapsed::after {
  content: '+'; position: absolute; right: 8px; top: 50%;
  transform: translateY(-50%); font-size: 1em; color: var(--ink-light);
}

.gn.search-hit { box-shadow: 0 0 0 3px var(--highlight); }
.gn.search-dim { opacity: 0.25; }

/* ── Node branch colors ── */
.gn[data-branch="0"] { border-left-color: var(--branch-0); }
.gn[data-branch="1"] { border-left-color: var(--branch-1); }
.gn[data-branch="2"] { border-left-color: var(--branch-2); }
.gn[data-branch="3"] { border-left-color: var(--branch-3); }
.gn[data-branch="4"] { border-left-color: var(--branch-4); }
.gn[data-branch="5"] { border-left-color: var(--branch-5); }

/* ── Edit panel ── */
.ge {
  background: #fefdfa;
  border: 1px solid var(--divider);
  border-radius: var(--node-radius);
  padding: 12px;
  margin-bottom: 10px;
  min-width: 260px; max-width: 460px;
  z-index: 3;
  animation: ge-in 0.15s ease;
}
@keyframes ge-in { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }

.ge-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px; font-size: 0.85em; color: var(--ink-light);
}
.ge-close {
  background: none; border: none; font-size: 1.2em; cursor: pointer;
  color: var(--ink-light); padding: 0 4px;
}
.ge-close:hover { color: var(--ink); }

.ge-notes {
  min-height: 60px; max-height: 300px; overflow-y: auto;
  padding: 8px; border: 1px dashed var(--divider); border-radius: 4px;
  outline: none; font-size: 0.9em; line-height: 1.7;
  background: #fff;
}
.ge-notes:focus { border-style: solid; border-color: #c0b8a8; }

.ge-images { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px; }
.ge-img-wrap { position: relative; }
.ge-img-wrap img { max-width: 200px; max-height: 150px; border-radius: 4px; border: 1px solid var(--divider); }
.ge-img-del {
  position: absolute; top: 2px; right: 2px;
  width: 18px; height: 18px; border-radius: 50%;
  background: rgba(0,0,0,0.5); color: #fff; border: none;
  font-size: 12px; line-height: 18px; cursor: pointer; text-align: center;
}
.ge-img-del:hover { background: rgba(200,0,0,0.7); }

.ge-hint { font-size: 0.8em; color: #bbb; margin-top: 6px; text-align: center; }

/* ── Connections (SVG paths) ── */
.conn-path { fill: none; stroke-width: 1.5; opacity: 0.5; }
.conn-path[data-branch="0"] { stroke: var(--branch-0); }
.conn-path[data-branch="1"] { stroke: var(--branch-1); }
.conn-path[data-branch="2"] { stroke: var(--branch-2); }
.conn-path[data-branch="3"] { stroke: var(--branch-3); }
.conn-path[data-branch="4"] { stroke: var(--branch-4); }
.conn-path[data-branch="5"] { stroke: var(--branch-5); }

/* ── Tooltip ── */
#tooltip {
  position: fixed; z-index: 200;
  max-width: 300px; padding: 8px 12px;
  background: #3c3c3c; color: #f5f0e8;
  border-radius: 6px; font-size: 0.85em; line-height: 1.5;
  pointer-events: none; opacity: 0; transition: opacity 0.12s;
}
#tooltip.tooltip-show { opacity: 1; }

/* ── Zoom bar ── */
#zoom-bar {
  position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1px solid var(--divider);
  border-radius: 20px; padding: 4px 12px; z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
#zoom-bar button {
  background: none; border: none; font-size: 1.2em; cursor: pointer;
  width: 28px; height: 28px; border-radius: 50%; color: var(--ink-light);
}
#zoom-bar button:hover { background: #f0ede5; color: var(--ink); }
#zoom-slider { width: 100px; accent-color: #aaa; }
#zoom-label { font-size: 0.85em; color: var(--ink-light); min-width: 36px; text-align: center; }

/* ── Toast ── */
#toast {
  position: fixed; bottom: 64px; left: 50%; transform: translateX(-50%);
  padding: 6px 16px; border-radius: 6px; font-size: 0.85em;
  background: #3c3c3c; color: #f5f0e8; opacity: 0; transition: opacity 0.3s;
  pointer-events: none; z-index: 300;
}
#toast.toast-show { opacity: 1; }
```

- [ ] **Step 3: Commit**

```bash
git add templates/graph_template.html templates/graph.css
git commit -m "feat: add knowledge graph HTML template and CSS"
```

---

### Task 3: Create `templates/graph.js` — Core rendering

**Files:**
- Create: `templates/graph.js`

- [ ] **Step 1: Write the JS file — tree data, rendering, connections**

```javascript
// === ExamPass Knowledge Graph Engine ===

const BRANCH_COLORS = [
  '#d4c5b9', '#c5d5cb', '#d5cec0', '#c8d0d8',
  '#d0c8c0', '#ccd4c8'
];

const STORAGE_KEY = 'graph_settings';

// ─── Tree model ───────────────────────────────────────────

function walkTree(nodes, branch, depth, callback) {
  let idx = 0;
  function _walk(nodes, branch, depth) {
    for (const node of nodes) {
      const isLeaf = !node.children || node.children.length === 0;
      callback(node, branch, depth, isLeaf);
      if (node.children && node.children.length > 0) {
        _walk(node.children, branch, depth + 1);
      }
    }
  }
  _walk(nodes, branch, depth);
}

function assignBranchColors(nodes) {
  nodes.forEach(function(node, i) {
    walkTree([node], i % BRANCH_COLORS.length, 0, function(n, branch) {
      n._branch = branch;
    });
  });
}

function flattenByLevel(nodes) {
  var levels = [];
  function walk(nodes, depth) {
    if (!levels[depth]) levels[depth] = [];
    for (var i = 0; i < nodes.length; i++) {
      var node = nodes[i];
      node._depth = depth;
      levels[depth].push(node);
      if (node.children && node.children.length > 0) {
        walk(node.children, depth + 1);
      }
    }
  }
  walk(nodes, 0);
  return levels;
}

// ─── localStorage helpers ─────────────────────────────────

function loadNotes(nodeId) {
  try {
    return localStorage.getItem('graph_' + nodeId + '_notes') || '';
  } catch(e) { return ''; }
}

function saveNotes(nodeId, html) {
  try {
    if (html) {
      localStorage.setItem('graph_' + nodeId + '_notes', html);
    } else {
      localStorage.removeItem('graph_' + nodeId + '_notes');
    }
    localStorage.setItem('graph_' + nodeId + '_updated', new Date().toISOString());
  } catch(e) {
    if (e.name === 'QuotaExceededError') {
      showToast('存储空间不足，请清理旧笔记或图片');
    }
  }
}

function loadImages(nodeId) {
  try {
    var raw = localStorage.getItem('graph_' + nodeId + '_images');
    return raw ? JSON.parse(raw) : [];
  } catch(e) { return []; }
}

function saveImages(nodeId, images) {
  try {
    if (images.length > 0) {
      localStorage.setItem('graph_' + nodeId + '_images', JSON.stringify(images));
    } else {
      localStorage.removeItem('graph_' + nodeId + '_images');
    }
  } catch(e) {
    if (e.name === 'QuotaExceededError') {
      showToast('图片过大，存储空间不足。请删除部分旧图片');
    }
  }
}

function loadSettings() {
  try {
    var raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch(e) { return {}; }
}

function saveSettings(settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch(e) {}
}

// ─── Rendering ────────────────────────────────────────────

var treeData = null;
var activeEditNode = null;
var settings = loadSettings();

function render(tree) {
  treeData = tree;
  if (!treeData.nodes || treeData.nodes.length === 0) {
    document.getElementById('graph-canvas').innerHTML =
      '<div style="padding:60px;text-align:center;color:#999;">课程内容为空，无法生成知识图谱</div>';
    return;
  }

  assignBranchColors(treeData.nodes);

  var canvas = document.getElementById('graph-canvas');
  canvas.innerHTML = '';

  var levels = flattenByLevel(treeData.nodes);

  // Apply collapsed state from settings
  var collapsed = settings.collapsed || [];
  applyCollapsed(treeData.nodes, collapsed);

  // Render level columns
  for (var li = 0; li < levels.length; li++) {
    var col = document.createElement('div');
    col.className = 'gl gl-' + li;

    for (var ni = 0; ni < levels[li].length; ni++) {
      var node = levels[li][ni];
      var el = renderNode(node);
      col.appendChild(el);

      // Show edit panel if this node was being edited
      if (activeEditNode && activeEditNode.id === node.id) {
        var editEl = renderEditPanel(node);
        col.appendChild(editEl);
        setTimeout(function(el) { el.querySelector('.ge-notes').focus(); }, 50, editEl);
      }
    }

    canvas.appendChild(col);
  }

  // SVG layer
  drawConnections();

  // Restore zoom
  var zoom = settings.zoom || 1;
  canvas.style.transform = 'scale(' + zoom + ')';
  document.getElementById('zoom-slider').value = Math.round(zoom * 100);
  document.getElementById('zoom-label').textContent = Math.round(zoom * 100) + '%';

  // Restore renames
  applyRenames();

  // Update header
  document.getElementById('header-title').textContent =
    (treeData.title || '课程') + ' - 知识图谱';
}

function renderNode(node) {
  var el = document.createElement('div');
  el.className = 'gn gn-lv' + (node._depth || 0);
  el.dataset.id = node.id;
  el.dataset.branch = node._branch;
  el.dataset.depth = node._depth;

  var isLeaf = !node.children || node.children.length === 0;

  var label = document.createElement('span');
  label.className = 'gn-label';
  label.textContent = node.label;
  el.appendChild(label);

  // Badge for notes
  var badge = document.createElement('span');
  badge.className = 'gn-badge';
  el.appendChild(badge);

  // Check for existing notes/images
  if (loadNotes(node.id) || loadImages(node.id).length > 0) {
    el.classList.add('has-notes');
  }

  // Collapsed state
  if (node._collapsed) {
    el.classList.add('collapsed');
  }

  // Tooltip
  if (node.summary) {
    el.addEventListener('mouseenter', function(e) { showTooltip(e, node.summary); });
    el.addEventListener('mouseleave', hideTooltip);
    el.addEventListener('mousemove', moveTooltip);
  }

  // Click handler
  el.addEventListener('click', function(e) {
    e.stopPropagation();
    if (isLeaf) {
      toggleEditPanel(node, el);
    } else {
      toggleCollapse(node);
    }
  });

  // Double-click rename
  el.addEventListener('dblclick', function(e) {
    e.stopPropagation();
    renameNode(node, label);
  });

  return el;
}

// ─── Edit panel ───────────────────────────────────────────

function renderEditPanel(node) {
  var el = document.createElement('div');
  el.className = 'ge';
  el.dataset.forNode = node.id;

  var header = document.createElement('div');
  header.className = 'ge-header';
  var updated = localStorage.getItem('graph_' + node.id + '_updated');
  header.innerHTML = '<span>笔记' + (updated ? ' · 最后保存 ' + formatTime(updated) : '') + '</span>';

  var closeBtn = document.createElement('button');
  closeBtn.className = 'ge-close';
  closeBtn.textContent = '✕';
  closeBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    closeEditPanel(node);
  });
  header.appendChild(closeBtn);
  el.appendChild(header);

  // Notes area
  var notesDiv = document.createElement('div');
  notesDiv.className = 'ge-notes';
  notesDiv.contentEditable = 'true';
  notesDiv.innerHTML = loadNotes(node.id);
  notesDiv.addEventListener('blur', function() {
    saveNotes(node.id, notesDiv.innerHTML);
    updateNodeBadge(node);
  });
  notesDiv.addEventListener('paste', function(e) { handlePaste(e, node); });
  el.appendChild(notesDiv);

  // Images
  var images = loadImages(node.id);
  var imagesDiv = document.createElement('div');
  imagesDiv.className = 'ge-images';
  for (var i = 0; i < images.length; i++) {
    imagesDiv.appendChild(createImageElement(images[i], i, node));
  }
  el.appendChild(imagesDiv);

  // Hint
  var hint = document.createElement('div');
  hint.className = 'ge-hint';
  hint.textContent = 'Ctrl+V 粘贴图片 · 点击外部自动保存';
  el.appendChild(hint);

  return el;
}

function createImageElement(src, index, node) {
  var wrap = document.createElement('div');
  wrap.className = 'ge-img-wrap';

  var img = document.createElement('img');
  img.src = src;
  img.alt = '粘贴的图片';
  wrap.appendChild(img);

  var del = document.createElement('button');
  del.className = 'ge-img-del';
  del.textContent = '✕';
  del.addEventListener('click', function(e) {
    e.stopPropagation();
    var images = loadImages(node.id);
    images.splice(index, 1);
    saveImages(node.id, images);
    wrap.remove();
  });
  wrap.appendChild(del);

  return wrap;
}

function handlePaste(e, node) {
  var items = e.clipboardData && e.clipboardData.items;
  if (!items) return;

  for (var i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      e.preventDefault();
      var blob = items[i].getAsFile();
      compressImage(blob, function(dataUrl) {
        var images = loadImages(node.id);
        images.push(dataUrl);
        saveImages(node.id, images);
        // Add to DOM
        var imagesDiv = e.target.parentElement.querySelector('.ge-images');
        if (imagesDiv) {
          imagesDiv.appendChild(createImageElement(dataUrl, images.length - 1, node));
        }
      });
      return;
    }
  }
}

function compressImage(blob, callback) {
  var img = new Image();
  var url = URL.createObjectURL(blob);
  img.onload = function() {
    URL.revokeObjectURL(url);
    var canvas = document.createElement('canvas');
    var maxW = 800;
    var w = img.width, h = img.height;
    if (w > maxW) { h = h * (maxW / w); w = maxW; }
    canvas.width = w; canvas.height = h;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, w, h);
    callback(canvas.toDataURL('image/jpeg', 0.7));
  };
  img.src = url;
}

function toggleEditPanel(node, nodeEl) {
  if (activeEditNode && activeEditNode.id === node.id) {
    closeEditPanel(node);
    return;
  }
  if (activeEditNode) {
    closeEditPanel(activeEditNode);
  }
  activeEditNode = node;

  var panel = renderEditPanel(node);
  nodeEl.parentElement.insertBefore(panel, nodeEl.nextSibling);
  setTimeout(function() { panel.querySelector('.ge-notes').focus(); }, 50);

  // Scroll detection — close when panel scrolls out of viewport
  panel._scrollHandler = function() {
    var rect = panel.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) {
      closeEditPanel(node);
    }
  };
  window.addEventListener('scroll', panel._scrollHandler, {passive: true});
}

function closeEditPanel(node) {
  var panel = document.querySelector('.ge[data-for-node="' + node.id + '"]');
  if (panel) {
    // Final save
    var notesDiv = panel.querySelector('.ge-notes');
    if (notesDiv) {
      saveNotes(node.id, notesDiv.innerHTML);
    }
    if (panel._scrollHandler) {
      window.removeEventListener('scroll', panel._scrollHandler);
    }
    panel.remove();
  }
  if (activeEditNode && activeEditNode.id === node.id) {
    activeEditNode = null;
  }
  updateNodeBadge(node);
}

function updateNodeBadge(node) {
  var el = document.querySelector('.gn[data-id="' + node.id + '"]');
  if (!el) return;
  var hasContent = loadNotes(node.id) || loadImages(node.id).length > 0;
  if (hasContent) {
    el.classList.add('has-notes');
  } else {
    el.classList.remove('has-notes');
  }
}

// ─── Collapse / Expand ────────────────────────────────────

function applyCollapsed(nodes, collapsedIds) {
  for (var i = 0; i < nodes.length; i++) {
    var node = nodes[i];
    if (collapsedIds.indexOf(node.id) !== -1) {
      node._collapsed = true;
    }
    if (node.children && node.children.length > 0) {
      applyCollapsed(node.children, collapsedIds);
    }
  }
}

function toggleCollapse(node) {
  node._collapsed = !node._collapsed;
  var collapsed = settings.collapsed || [];
  if (node._collapsed) {
    if (collapsed.indexOf(node.id) === -1) collapsed.push(node.id);
  } else {
    var idx = collapsed.indexOf(node.id);
    if (idx !== -1) collapsed.splice(idx, 1);
  }
  settings.collapsed = collapsed;
  saveSettings(settings);
  render(treeData);
}

// ─── Rename ────────────────────────────────────────────────

function renameNode(node, labelEl) {
  var oldLabel = node.label;
  var input = document.createElement('input');
  input.type = 'text';
  input.value = oldLabel;
  input.style.cssText = 'font-weight:600;font-size:0.95em;width:100%;border:1px solid #ccc;border-radius:4px;padding:2px 6px;';
  input.addEventListener('blur', function() { finishRename(node, input.value.trim() || oldLabel); });
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
    if (e.key === 'Escape') { input.value = oldLabel; input.blur(); }
  });
  labelEl.replaceWith(input);
  input.focus();
  input.select();
}

function finishRename(node, newLabel) {
  node.label = newLabel;
  var renamed = settings.renamed || {};
  renamed[node.id] = newLabel;
  settings.renamed = renamed;
  saveSettings(settings);
  render(treeData);
}

function applyRenames() {
  var renamed = settings.renamed || {};
  var ids = Object.keys(renamed);
  for (var i = 0; i < ids.length; i++) {
    var el = document.querySelector('.gn[data-id="' + ids[i] + '"] .gn-label');
    if (el) el.textContent = renamed[ids[i]];
  }
}

// ─── Connections (SVG) ────────────────────────────────────

function drawConnections() {
  var svg = document.getElementById('connections-layer');
  var canvas = document.getElementById('graph-canvas');
  var canvasRect = canvas.getBoundingClientRect();

  svg.style.width = canvas.scrollWidth + 'px';
  svg.style.height = canvas.scrollHeight + 'px';
  svg.setAttribute('viewBox', '0 0 ' + canvas.scrollWidth + ' ' + canvas.scrollHeight);

  var paths = [];

  function collectEdges(nodes) {
    for (var i = 0; i < nodes.length; i++) {
      var parent = nodes[i];
      if (parent._collapsed) continue;
      var parentEl = document.querySelector('.gn[data-id="' + parent.id + '"]');
      if (!parentEl) continue;
      if (parent.children && parent.children.length > 0) {
        for (var j = 0; j < parent.children.length; j++) {
          var child = parent.children[j];
          var childEl = document.querySelector('.gn[data-id="' + child.id + '"]');
          if (!childEl) continue;
          paths.push({
            parent: parentEl,
            child: childEl,
            branch: parent._branch
          });
          collectEdges(parent.children);
        }
      }
    }
  }
  collectEdges(treeData.nodes);

  var html = '';
  for (var i = 0; i < paths.length; i++) {
    var p = paths[i];
    var pRect = p.parent.getBoundingClientRect();
    var cRect = p.child.getBoundingClientRect();

    var x1 = pRect.right - canvasRect.left;
    var y1 = pRect.top + pRect.height / 2 - canvasRect.top;
    var x2 = cRect.left - canvasRect.left;
    var y2 = cRect.top + cRect.height / 2 - canvasRect.top;

    var cx1 = x1 + (x2 - x1) * 0.4;
    var cy1 = y1;
    var cx2 = x1 + (x2 - x1) * 0.6;
    var cy2 = y2;

    html += '<path class="conn-path" data-branch="' + p.branch +
      '" d="M' + x1 + ',' + y1 + ' C' + cx1 + ',' + cy1 + ' ' + cx2 + ',' + cy2 + ' ' + x2 + ',' + y2 + '" />';
  }

  svg.innerHTML = html;
}

// ─── Tooltip ───────────────────────────────────────────────

function showTooltip(e, text) {
  var tip = document.getElementById('tooltip');
  tip.textContent = text;
  tip.classList.add('tooltip-show');
  moveTooltip(e);
}

function moveTooltip(e) {
  var tip = document.getElementById('tooltip');
  var x = e.clientX + 14;
  var y = e.clientY + 14;
  if (x + 300 > window.innerWidth) x = e.clientX - 310;
  if (y + 80 > window.innerHeight) y = e.clientY - 90;
  tip.style.left = x + 'px';
  tip.style.top = y + 'px';
}

function hideTooltip() {
  document.getElementById('tooltip').classList.remove('tooltip-show');
}

// ─── Toast ─────────────────────────────────────────────────

var toastTimer = null;
function showToast(msg) {
  var toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('toast-show');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(function() { toast.classList.remove('toast-show'); }, 2000);
}

// ─── Format helpers ────────────────────────────────────────

function formatTime(iso) {
  try {
    var d = new Date(iso);
    var pad = function(n) { return n < 10 ? '0' + n : String(n); };
    return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()) +
      ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  } catch(e) { return ''; }
}
```

- [ ] **Step 2: Commit**

```bash
git add templates/graph.js
git commit -m "feat: add knowledge graph core JS (render, edit panel, connections)"
```

---

### Task 4: Add search, zoom, and initialization to `templates/graph.js`

**Files:**
- Modify: `templates/graph.js` (append at end)

- [ ] **Step 1: Append search, zoom, and init code**

```javascript
// ─── Search ────────────────────────────────────────────────

var searchTimer = null;
document.addEventListener('DOMContentLoaded', function() {
  var searchInput = document.getElementById('search-input');
  if (!searchInput) return;
  searchInput.addEventListener('input', function() {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 200);
  });
  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') { searchInput.value = ''; doSearch(); }
  });
});

function doSearch() {
  var query = document.getElementById('search-input').value.trim().toLowerCase();
  var allNodes = document.querySelectorAll('.gn');
  var firstHit = null;

  allNodes.forEach(function(el) {
    el.classList.remove('search-hit', 'search-dim');
  });

  if (!query) return;

  allNodes.forEach(function(el) {
    var label = (el.querySelector('.gn-label') || {}).textContent || '';
    if (label.toLowerCase().indexOf(query) !== -1) {
      el.classList.add('search-hit');
      if (!firstHit) firstHit = el;
    } else {
      el.classList.add('search-dim');
    }
  });

  if (firstHit) {
    firstHit.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// ─── Zoom ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  var slider = document.getElementById('zoom-slider');
  var label = document.getElementById('zoom-label');
  var outBtn = document.getElementById('zoom-out');
  var inBtn = document.getElementById('zoom-in');
  var resetBtn = document.getElementById('reset-btn');

  if (!slider) return;

  var zoom = settings.zoom || 1;

  function applyZoom(z) {
    zoom = Math.max(0.5, Math.min(2, z));
    var canvas = document.getElementById('graph-canvas');
    if (canvas) canvas.style.transform = 'scale(' + zoom + ')';
    slider.value = Math.round(zoom * 100);
    label.textContent = Math.round(zoom * 100) + '%';
    settings.zoom = zoom;
    saveSettings(settings);
    // Redraw connections after zoom
    setTimeout(drawConnections, 100);
  }

  slider.addEventListener('input', function() { applyZoom(this.value / 100); });
  outBtn.addEventListener('click', function() { applyZoom(zoom - 0.1); });
  inBtn.addEventListener('click', function() { applyZoom(zoom + 0.1); });

  resetBtn.addEventListener('click', function() {
    settings.collapsed = [];
    settings.renamed = {};
    saveSettings(settings);
    activeEditNode = null;
    document.getElementById('search-input').value = '';
    doSearch();
    applyZoom(1);
    render(treeData);
  });
});

// ─── Init ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  if (typeof TREE_DATA === 'undefined') {
    document.getElementById('graph-canvas').innerHTML =
      '<div style="padding:60px;text-align:center;color:#999;">未找到知识图谱数据</div>';
    return;
  }
  render(TREE_DATA);

  // Handle window resize → redraw connections
  var resizeTimer = null;
  window.addEventListener('resize', function() {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
      if (activeEditNode) closeEditPanel(activeEditNode);
      drawConnections();
    }, 300);
  });

  // Close edit panel on click outside
  document.addEventListener('click', function(e) {
    if (activeEditNode) {
      var clickedOnNode = e.target.closest('.gn[data-id="' + activeEditNode.id + '"]');
      var clickedOnPanel = e.target.closest('.ge[data-for-node="' + activeEditNode.id + '"]');
      if (!clickedOnNode && !clickedOnPanel) {
        closeEditPanel(activeEditNode);
      }
    }
  });
});
```

- [ ] **Step 2: Commit**

```bash
git add templates/graph.js
git commit -m "feat: add knowledge graph search, zoom, and init logic"
```

---

### Task 5: Add `save_graph_html()` to template engine

**Files:**
- Modify: `scripts/template_engine.py`

- [ ] **Step 1: Read current template_engine.py to locate insertion point**

The function should be added after `save_knowledge_html()` (around line 98).

- [ ] **Step 2: Add `save_graph_html()` function**

Add the following after the `save_knowledge_html` function (after line 98) and before the `# ─── Interactive test page` comment:

```python
# ─── Knowledge graph page ─────────────────────────────────────────

def save_graph_html(tree_json: dict, output_path: str, title: str):
    """Generate an interactive knowledge graph page.

    tree_json: {"title": "...", "nodes": [...]}
    """
    import json as _json
    tree_data_js = 'const TREE_DATA = ' + _json.dumps(tree_json, ensure_ascii=False) + ';'

    graph_css = _read('graph.css')
    graph_js = _read('graph.js')
    graph_template = _read('graph_template.html')

    html = graph_template
    html = html.replace('__TITLE__', title)
    html = html.replace('__CSS__', graph_css)
    html = html.replace('__TREE_DATA__', '<script>\n' + tree_data_js + '\n</script>')
    html = html.replace('__JS__', graph_js)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
```

- [ ] **Step 3: Write tests for `save_graph_html`**

Add to `tests/test_knowledge_graph.py`:

```python
def test_save_graph_html_creates_file(tmp_path):
    from template_engine import save_graph_html

    tree = {
        "title": "测试课程",
        "nodes": [
            {"id": "n1", "label": "第1章", "summary": "概述", "children": [
                {"id": "n2", "label": "知识点1", "summary": "细节", "children": []}
            ]}
        ]
    }
    output = tmp_path / "知识图谱.html"
    save_graph_html(tree, str(output), "测试课程")

    assert output.exists()
    content = output.read_text(encoding='utf-8')
    assert "测试课程" in content
    assert "TREE_DATA" in content
    assert "n1" in content
    assert "n2" in content
    assert "graph-canvas" in content


def test_save_graph_html_creates_parent_dir(tmp_path):
    from template_engine import save_graph_html

    tree = {"title": "t", "nodes": []}
    output = tmp_path / "subdir" / "graph.html"
    save_graph_html(tree, str(output), "t")
    assert output.exists()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_knowledge_graph.py -v`
Expected: All PASS (2 new + existing tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/template_engine.py tests/test_knowledge_graph.py
git commit -m "feat: add save_graph_html() to template engine with tests"
```

---

### Task 6: Add `graph` subcommand routing to SKILL.md

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Add `graph` to command routing**

The routing section currently checks for `"update"`. Add `"graph"`:

Edit the «命令路由» section — after the `update` line and before the `其他情况` line — to include:

```markdown
- **`args` 为 `"update"`**：执行下方「技能更新」流程，完成后直接结束，不执行知识清单生成。
- **`args` 为 `"graph"`** 或以 `"graph "` 开头：执行下方「知识图谱生成」流程，完成后直接结束。
```

- [ ] **Step 2: Add knowledge graph generation section**

Insert before `# ExamPass Assistant` heading, after the update PowerShell script block:

```markdown
---

## 知识图谱生成

当用户执行 `/exampass graph [目录]` 时：

### 第一步：提取

```bash
python scripts/run_exampass.py <目标目录>
```
（复用扫描+提取管线，产出 `_extraction_bundle.json`）

### 第二步：深度分析生成知识树 JSON

Claude 读取提取内容，按 `scripts/knowledge_graph.py` 的 prompt 将内容组织为知识树 JSON，保存为 `knowledge_graph.json`。

### 第三步：生成交互式 HTML

```python
import json
from scripts.template_engine import save_graph_html

with open('knowledge_graph.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)

save_graph_html(tree, '知识图谱.html', tree['title'])
```

### 第四步：打开

浏览器打开 HTML。用户可交互编辑、粘贴图片、搜索、缩放。

### 从已有 JSON 重新生成

若用户提供了 `--from-json <路径>` 参数：
1. 直接读取 JSON
2. 跳过提取和分析
3. 调用 `save_graph_html()` 重新生成 HTML

```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: add /exampass graph subcommand routing"
```

---

### Task 7: End-to-end verification

**Files:**
- Verify: All new and modified files work together

- [ ] **Step 1: Run all existing tests to ensure no regressions**

```bash
cd M:\skills\EPA && python -m pytest tests/ -v
```
Expected: All 102+ tests PASS

- [ ] **Step 2: Verify imports work**

```bash
cd M:\skills\EPA && python -c "from scripts.knowledge_graph import build_graph_prompt, parse_graph_response, validate_tree_json; print('OK')"
```

- [ ] **Step 3: Verify template engine integration**

```bash
cd M:\skills\EPA && python -c "from scripts.template_engine import save_graph_html; print('OK')"
```

- [ ] **Step 4: Generate a test graph HTML with sample data**

```bash
cd M:\skills\EPA && python -c "
import json
from scripts.template_engine import save_graph_html

tree = {
    'title': '深度学习',
    'nodes': [
        {'id': 'n1', 'label': '第1章 绪论', 'summary': '课程概述和基础概念', 'children': [
            {'id': 'n2', 'label': '神经元模型', 'summary': 'M-P神经元模型是深度学习的基本计算单元', 'children': [
                {'id': 'n3', 'label': '激活函数', 'summary': '引入非线性，常见的有Sigmoid、Tanh、ReLU', 'children': []},
                {'id': 'n4', 'label': '前向传播', 'summary': '输入数据从输入层经隐藏层到输出层的计算过程', 'children': []}
            ]}
        ]},
        {'id': 'n5', 'label': '第2章 神经网络', 'summary': '多层神经网络的训练和优化', 'children': [
            {'id': 'n6', 'label': '反向传播', 'summary': '利用链式法则计算损失函数对每个参数的梯度', 'children': []},
            {'id': 'n7', 'label': '梯度下降', 'summary': '沿负梯度方向更新参数以最小化损失', 'children': [
                {'id': 'n8', 'label': 'SGD', 'summary': '随机梯度下降，每次用一个小批量估计梯度', 'children': []},
                {'id': 'n9', 'label': 'Adam', 'summary': '自适应矩估计，结合动量和RMSProp', 'children': []}
            ]}
        ]},
        {'id': 'n10', 'label': '第3章 CNN', 'summary': '卷积神经网络在图像处理中的应用', 'children': [
            {'id': 'n11', 'label': '卷积层', 'summary': '通过卷积核提取局部特征', 'children': []},
            {'id': 'n12', 'label': '池化层', 'summary': '下采样降低特征图尺寸，保留主要特征', 'children': []}
        ]}
    ]
}
save_graph_html(tree, 'test_graph.html', '深度学习')
print('Generated test_graph.html')
"
```

- [ ] **Step 5: Verify HTML structure**

```bash
cd M:\skills\EPA && python -c "
content = open('test_graph.html', 'r', encoding='utf-8').read()
assert 'TREE_DATA' in content
assert 'graph-canvas' in content
assert 'connections-layer' in content
assert 'search-input' in content
assert 'zoom-slider' in content
assert 'const TREE_DATA' in content
print('HTML structure OK')
"
```

- [ ] **Step 6: Clean up test file**

```bash
Remove-Item M:\skills\EPA\test_graph.html
```

- [ ] **Step 7: Commit (if any fixes were needed)**

Only if changes were required during verification.

---

### Final Verification Checklist

- [ ] `pytest tests/ -v` — all tests pass
- [ ] `python -c "from scripts.knowledge_graph import *"` — imports work
- [ ] `python -c "from scripts.template_engine import save_graph_html"` — new function available
- [ ] Generated HTML contains all required elements (canvas, connections layer, search, zoom)
- [ ] SKILL.md has `graph` routing
- [ ] No regressions in existing functionality
