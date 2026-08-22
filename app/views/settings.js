/**
 * Settings, progress counts, and the export button.
 *
 * Counts live here rather than on the drill screen on purpose: hard rule 5
 * bans streaks and guilt mechanics, and a progress bar in front of you while
 * you review is exactly that. Here they are something you go and look at.
 */

import { settings, setSetting, exportBlob, exportFilename, resetAll, load } from '../store.js';
import { stats } from '../srs.js';
import * as theme from '../theme.js';
import * as feedback from '../feedback.js';

export function render(root, deck, rerender) {
  root.textContent = '';

  const h = document.createElement('h1');
  h.className = 'title';
  h.textContent = 'Settings';
  root.appendChild(h);

  root.appendChild(statsBlock(deck));

  const s = settings();

  const appearance = group([
    seg('Theme', null, ['system', 'light', 'dark'], ['System', 'Light', 'Dark'], s.theme, (v) => {
      theme.set(v);
      rerender();
    }),
  ]);
  root.appendChild(appearance);

  const feel = group([
    seg('Sound', 'Muted by the ring/silent switch on iPhone.', ['off', 'on'], ['Off', 'On'],
      s.sound ? 'on' : 'off', (v) => {
        setSetting('sound', v === 'on');
        if (v === 'on') feedback.grade('good');
        rerender();
      }),
  ]);
  root.appendChild(feel);

  const pace = group([
    number('New words per day', `${deck.length} total. At ${s.newPerDay || 1}/day that is about ${Math.ceil(deck.length / Math.max(1, s.newPerDay))} days to introduce them all.`,
      s.newPerDay, 0, 40, (v) => { setSetting('newPerDay', v); rerender(); }),
    number('Daily review cap', 'Anything over the cap is quietly held for another day.',
      s.dailyCap, 5, 200, (v) => { setSetting('dailyCap', v); rerender(); }),
  ]);
  root.appendChild(pace);

  const data = document.createElement('div');
  data.className = 'group';
  data.appendChild(button('Export progress', doExport));
  data.appendChild(button('Reset all progress', () => {
    const st = load();
    const n = Object.keys(st.cards).length;
    if (!n) { alert('Nothing to reset yet.'); return; }
    if (!confirm(`Erase scheduling for ${n} cards?\n\nA copy is kept in this browser's storage, but export first if you want a file.`)) return;
    resetAll();
    rerender();
  }, true));
  root.appendChild(data);

  const note = document.createElement('p');
  note.className = 'note';
  note.textContent = 'Progress is stored on this device only — it does not sync between your phone and computer. Export writes a JSON file you can keep as a backup.';
  root.appendChild(note);
}

function statsBlock(deck) {
  const st = stats(deck);
  const wrap = document.createElement('div');
  wrap.className = 'stat-grid';
  const cells = [
    [st.seen, `of ${st.total} started`],
    [st.review, 'in long-term review'],
    [st.dueNow, 'due right now'],
  ];
  for (const [n, label] of cells) {
    const c = document.createElement('div');
    c.className = 'stat';
    const b = document.createElement('b');
    b.textContent = String(n);
    const sp = document.createElement('span');
    sp.textContent = label;
    c.append(b, sp);
    wrap.appendChild(c);
  }
  return wrap;
}

function group(rows) {
  const g = document.createElement('div');
  g.className = 'group';
  for (const r of rows) g.appendChild(r);
  return g;
}

function labelCell(label, sub) {
  const d = document.createElement('div');
  const l = document.createElement('div');
  l.className = 'row-label';
  l.textContent = label;
  d.appendChild(l);
  if (sub) {
    const p = document.createElement('p');
    p.className = 'row-sub';
    p.textContent = sub;
    d.appendChild(p);
  }
  return d;
}

function seg(label, sub, values, labels, current, onPick) {
  const row = document.createElement('div');
  row.className = 'row';
  row.appendChild(labelCell(label, sub));

  const box = document.createElement('div');
  box.className = 'seg';
  values.forEach((v, i) => {
    const b = document.createElement('button');
    b.textContent = labels[i];
    b.setAttribute('aria-pressed', String(v === current));
    b.addEventListener('click', () => onPick(v));
    box.appendChild(b);
  });
  row.appendChild(box);
  return row;
}

function number(label, sub, value, min, max, onChange) {
  const row = document.createElement('div');
  row.className = 'row';
  row.appendChild(labelCell(label, sub));

  const input = document.createElement('input');
  input.className = 'num';
  input.type = 'number';
  input.inputMode = 'numeric';
  input.min = String(min);
  input.max = String(max);
  input.value = String(value);
  input.addEventListener('change', () => {
    const n = Math.round(Number(input.value));
    if (!Number.isFinite(n) || n < min || n > max) {
      input.value = String(value);
      return;
    }
    onChange(n);
  });
  row.appendChild(input);
  return row;
}

function button(text, onClick, danger) {
  const b = document.createElement('button');
  b.className = 'btn' + (danger ? ' danger' : '');
  b.textContent = text;
  b.addEventListener('click', onClick);
  return b;
}

function doExport() {
  const url = URL.createObjectURL(exportBlob());
  const a = document.createElement('a');
  a.href = url;
  a.download = exportFilename();
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
