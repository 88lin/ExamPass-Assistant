var Q = __QUESTIONS_PLACEHOLDER__;
var LABELS = __LABELS_PLACEHOLDER__;

function build(){
  var container = document.getElementById('questions-container');
  if (!container) { console.error('ExamPass: questions-container not found'); return; }
  var h = '';
  var sec = '';
  var titles = LABELS.section;

  for (var i = 0; i < Q.length; i++) {
    var q = Q[i];
    var s = q.type;
    if (s !== sec) {
      sec = s;
      if (titles[s]) {
        h += '<h3>' + titles[s] + '</h3>';
      }
    }

    var qid = 'q' + i;
    h += '<div class="q-card" id="card-' + qid + '">';
    h += '<div class="q-num">' + (i+1) + '. (' + q.points + ' ' + LABELS.points_suffix + ')</div>';
    h += '<div class="q-text">' + q.question + '</div>';

    if (q.type === 'choice') {
      var opts = q.options || [];
      for (var j = 0; j < opts.length; j++) {
        h += '<label class="option" id="opt-' + qid + '-' + j + '" onclick="sel(\'' + qid + '\',' + j + ')">';
        h += '<input type="radio" name="' + qid + '" value="' + j + '">' + String.fromCharCode(65+j) + '. ' + opts[j] + '</label>';
      }
    } else if (q.type === 'tf') {
      h += '<label class="option" id="opt-' + qid + '-0" onclick="sel(\'' + qid + '\',0)">';
      h += '<input type="radio" name="' + qid + '" value="0">' + LABELS.true_label + '</label>';
      h += '<label class="option" id="opt-' + qid + '-1" onclick="sel(\'' + qid + '\',1)">';
      h += '<input type="radio" name="' + qid + '" value="1">' + LABELS.false_label + '</label>';
    } else {
      h += '<textarea class="q-textarea" id="text-' + qid + '" placeholder="' + LABELS.placeholder + '" rows="3"></textarea>';
    }

    h += '<div class="result" id="result-' + qid + '">';
    h += '<span class="badge" id="badge-' + qid + '"></span><span id="correct-' + qid + '"></span>';
    h += '<div class="explanation">' + q.explanation + '</div>';
    if (q.pitfall) {
      h += '<div class="pitfall">' + LABELS.pitfall_prefix + q.pitfall + '</div>';
    }
    h += '</div></div>';
  }

  container.innerHTML = h;
}

document.addEventListener('DOMContentLoaded', build);
// Fallback: if DOM already loaded, run immediately
if (document.readyState === 'interactive' || document.readyState === 'complete') {
  build();
}

function sel(qid, idx) {
  var prefix = 'opt-' + qid + '-';
  var all = document.querySelectorAll('[id^="' + prefix + '"]');
  for (var i = 0; i < all.length; i++) {
    all[i].classList.remove('selected');
  }
  var target = document.getElementById('opt-' + qid + '-' + idx);
  if (target) {
    target.classList.add('selected');
  }
  var radio = document.querySelector('input[name="' + qid + '"][value="' + idx + '"]');
  if (radio) {
    radio.checked = true;
  }
}

function gradeAll() {
  var score = 0;
  for (var i = 0; i < Q.length; i++) {
    var q = Q[i];
    var qid = 'q' + i;
    var card = document.getElementById('card-' + qid);
    var result = document.getElementById('result-' + qid);
    var badge = document.getElementById('badge-' + qid);
    var correctEl = document.getElementById('correct-' + qid);
    if (!card || !result) continue;

    result.style.display = 'block';

    if (q.type === 'choice' || q.type === 'tf') {
      var radio = document.querySelector('input[name="' + qid + '"]:checked');
      if (radio && parseInt(radio.value) === q.answer) {
        score += q.points;
        card.classList.add('correct');
        badge.className = 'badge badge-ok';
        badge.textContent = LABELS.correct_label;
        correctEl.innerHTML = '';
        var correctOpt = document.getElementById('opt-' + qid + '-' + q.answer);
        if (correctOpt) correctOpt.classList.add('correct-answer');
      } else {
        card.classList.add('wrong');
        badge.className = 'badge badge-no';
        badge.textContent = LABELS.wrong_label;
        var ansText = q.type === 'choice'
          ? String.fromCharCode(65+q.answer) + '. ' + (q.options ? q.options[q.answer] : '')
          : (q.answer === 0 ? LABELS.true_label : LABELS.false_label);
        correctEl.innerHTML = LABELS.answer_prefix + ansText;
        if (radio) {
          var wrongOpt = document.getElementById('opt-' + qid + '-' + radio.value);
          if (wrongOpt) wrongOpt.classList.add('wrong-answer');
        }
        var correctOpt = document.getElementById('opt-' + qid + '-' + q.answer);
        if (correctOpt) correctOpt.classList.add('correct-answer');
      }
    } else {
      card.classList.add('correct');
      badge.className = 'badge badge-ref';
      badge.textContent = LABELS.reference_label;
    }
  }

  var sb = document.getElementById('score-box');
  if (sb) {
    sb.style.display = 'block';
    document.getElementById('score-num').textContent = score;
    sb.scrollIntoView({behavior:'smooth'});
  }

  var opts = document.querySelectorAll('.option');
  for (var i = 0; i < opts.length; i++) opts[i].style.pointerEvents = 'none';
  var tas = document.querySelectorAll('.q-textarea');
  for (var i = 0; i < tas.length; i++) tas[i].disabled = true;

  var btn = document.getElementById('grade-btn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = LABELS.graded_label;
  }
}
