"""Template engine for ExamPass HTML generation.

Provides two reusable generators:
  render_knowledge(markdown_content, title) -> HTML string
  render_test(questions_data, title) -> HTML string

Call these directly from the skill to skip manual markdown/HTML assembly.
"""

import os
import json

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')


def _read_css(filename):
    path = os.path.join(_TEMPLATES_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''


# ─── Shared page shell ──────────────────────────────────────────────

def _page_shell(title, body_html, extra_css='', extra_js=''):
    """Wrap content in the standard ExamPass HTML shell."""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"></script>
<style>
{_read_css('base.css')}
{extra_css}
</style>
{extra_js}
</head>
<body>

<header id="exampass-header">
  <div class="header-left"><span class="header-brand">ExamPass Assistant</span></div>
  <div class="header-right"><span class="header-url">exampass.ai</span></div>
</header>
<hr class="header-divider">

{body_html}

</body>
</html>'''


# ─── Knowledge page ────────────────────────────────────────────────

def render_knowledge(markdown_content, title='知识清单'):
    """
    Convert markdown to a styled knowledge page HTML string.
    Uses pandoc internally for markdown→HTML conversion.
    """
    import subprocess
    import tempfile
    import uuid

    md_path = os.path.join(tempfile.gettempdir(), f'_exam_know_{uuid.uuid4().hex[:8]}.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    result = subprocess.run([
        'pandoc', md_path, '-t', 'html5',
        '--from=markdown+tex_math_dollars+tex_math_single_backslash',
        '--metadata', 'lang=zh-CN',
        '--standalone',
    ], capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace')

    try:
        os.remove(md_path)
    except Exception:
        pass

    if result.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {result.stderr[:300]}")

    # Extract body content from pandoc output
    body = result.stdout
    for tag in ['<body>', '<BODY>']:
        if tag in body:
            body = body.split(tag, 1)[1]
    for tag in ['</body>', '</BODY>']:
        if tag in body:
            body = body.split(tag, 1)[0]

    # Remove pandoc's default style block
    import re
    body = re.sub(r'<style>.*?</style>', '', body, flags=re.DOTALL)
    # Remove nav#TOC (we use manual TOC in markdown)
    body = re.sub(r'<nav[^>]*id="TOC"[^>]*>.*?</nav>', '', body, flags=re.DOTALL)

    return _page_shell(title, body)


# ─── Interactive test page ─────────────────────────────────────────

def render_test(questions, title='章节测试', subtitle=''):
    """
    Generate an interactive test page.

    questions: list of dicts with keys:
      - type: "choice" | "tf" | "short" | "essay"
      - points: int
      - question: str (HTML allowed)
      - options: list of str (for choice only)
      - answer: int (0-index for choice/tf, -1 for open-ended)
      - explanation: str (HTML allowed)
      - pitfall: str (optional)
    """
    questions_json = json.dumps(questions, ensure_ascii=False)

    sub = f'<p style="text-align:center;color:var(--ink-light);font-size:0.95em">{subtitle}</p>' if subtitle else ''

    body = f'''
<h1>{title}</h1>
<h2 style="text-align:center">章节测试</h2>
{sub}

<div id="score-box"><div class="score-num" id="score-num">0</div><div class="score-label">总分</div></div>
<div id="questions-container"></div>
<div class="grading-bar no-print"><button onclick="gradeAll()" id="grade-btn">提交批改</button></div>
'''

    js = f'''<script>
const Q = {questions_json};

function build(){{
  let h='',sec='';
  const titles={{
    choice:'一、选择题', tf:'二、判断题', short:'三、简答题',
    essay:'四、问答题', comprehensive:'五、综合题'
  }};
  Q.forEach((q,i)=>{{
    let s=q.type==='choice'?'choice':q.type==='tf'?'tf':i<24?'short':i<27?'essay':'comprehensive';
    if(s!==sec){{sec=s;h+='<h3>'+titles[sec]+'</h3>';}}
    let qid='q'+i;
    h+='<div class="q-card" id="card-'+qid+'">';
    h+='<div class="q-num">'+(i+1)+'. ('+q.points+' 分)</div>';
    h+='<div class="q-text">'+q.question+'</div>';
    if(q.type==='choice'){{
      q.options.forEach((o,j)=>{{
        h+='<label class="option" id="opt-'+qid+'-'+j+'" onclick="sel(\\''+qid+'\\','+j+')">';
        h+='<input type="radio" name="'+qid+'" value="'+j+'">'+String.fromCharCode(65+j)+'. '+o+'</label>';
      }});
    }}else if(q.type==='tf'){{
      h+='<label class="option" id="opt-'+qid+'-0" onclick="sel(\\''+qid+'\\',0)"><input type="radio" name="'+qid+'" value="0">正确</label>';
      h+='<label class="option" id="opt-'+qid+'-1" onclick="sel(\\''+qid+'\\',1)"><input type="radio" name="'+qid+'" value="1">错误</label>';
    }}else{{
      h+='<textarea class="q-textarea" id="text-'+qid+'" placeholder="在此作答..." rows="3"></textarea>';
    }}
    h+='<div class="result" id="result-'+qid+'">';
    h+='<span class="badge" id="badge-'+qid+'"></span><span id="correct-'+qid+'"></span>';
    h+='<div class="explanation">'+q.explanation+'</div>';
    if(q.pitfall) h+='<div class="pitfall">易错提醒：'+q.pitfall+'</div>';
    h+='</div></div>';
  }});
  document.getElementById('questions-container').innerHTML=h;
}}

function sel(qid,idx){{
  document.querySelectorAll('[id^="opt-'+qid+'"]').forEach(e=>e.classList.remove('selected'));
  document.getElementById('opt-'+qid+'-'+idx).classList.add('selected');
  document.querySelector('input[name="'+qid+'"][value="'+idx+'"]').checked=true;
}}

function gradeAll(){{
  let score=0;
  Q.forEach((q,i)=>{{
    let qid='q'+i,card=document.getElementById('card-'+qid),result=document.getElementById('result-'+qid);
    let badge=document.getElementById('badge-'+qid),correctEl=document.getElementById('correct-'+qid);
    result.style.display='block';
    if(q.type==='choice'||q.type==='tf'){{
      let sel=document.querySelector('input[name="'+qid+'"]:checked');
      if(sel&&parseInt(sel.value)===q.answer){{
        score+=q.points;card.classList.add('correct');
        badge.className='badge badge-ok';badge.textContent='正确';correctEl.innerHTML='';
        document.getElementById('opt-'+qid+'-'+q.answer).classList.add('correct-answer');
      }}else{{
        card.classList.add('wrong');
        badge.className='badge badge-no';badge.textContent='错误';
        correctEl.innerHTML=' 正确答案：'+(q.type==='choice'?String.fromCharCode(65+q.answer)+'. '+q.options[q.answer]:(q.answer===0?'正确':'错误'));
        if(sel) document.getElementById('opt-'+qid+'-'+sel.value).classList.add('wrong-answer');
        document.getElementById('opt-'+qid+'-'+q.answer).classList.add('correct-answer');
      }}
    }}else{{
      card.classList.add('correct');badge.className='badge badge-ref';badge.textContent='参考答案';
    }}
  }});
  let sb=document.getElementById('score-box');sb.style.display='block';
  document.getElementById('score-num').textContent=score;
  sb.scrollIntoView({{behavior:'smooth'}});
  document.querySelectorAll('.option').forEach(e=>e.style.pointerEvents='none');
  document.querySelectorAll('.q-textarea').forEach(e=>e.disabled=true);
  document.getElementById('grade-btn').disabled=true;
  document.getElementById('grade-btn').textContent='已批改';
}}
build();
</script>'''

    return _page_shell(title, body, extra_css=_read_css('test.css'), extra_js=js)


# ─── Convenience: save to file ─────────────────────────────────────

def save_knowledge(markdown_content, output_path, title='知识清单'):
    html = render_knowledge(markdown_content, title)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def save_test(questions, output_path, title='章节测试', subtitle=''):
    html = render_test(questions, title, subtitle)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
