// === ExamPass Knowledge Graph Engine ===

const BRANCH_COLORS = [
  '#d4c5b9', '#c5d5cb', '#d5cec0', '#c8d0d8',
  '#d0c8c0', '#ccd4c8'
];

const STORAGE_KEY = 'graph_settings';

// ─── Tree model ───────────────────────────────────────────

function walkTree(nodes, branch, depth, callback) {
  for (const node of nodes) {
    const isLeaf = !node.children || node.children.length === 0;
    callback(node, branch, depth, isLeaf);
    if (node.children && node.children.length > 0) {
      walkTree(node.children, branch, depth + 1, callback);
    }
  }
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
