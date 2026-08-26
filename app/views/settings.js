/**
 * Settings, progress counts, and the export button.
 *
 * Counts live here rather than on the drill screen on purpose: hard rule 5
 * bans streaks and guilt mechanics, and a progress bar in front of you while
 * you review is exactly that. Here they are something you go and look at.
 */

import { settings, setSetting, exportBlob, exportFilename, resetAll, load, hasSessionChanges, undoSession } from '../store.js';
import { stats, describeInterval } from '../srs.js';
import * as theme from '../theme.js';
import * as feedback from '../feedback.js';
import * as sync from '../sync.js';

export function render(root, deck, rerender) {
  root.textContent = '';

  const h = document.createElement('h1');
  h.className = 'title';
  h.textContent = 'Settings';
  root.appendChild(h);

  const st = stats(deck);
  root.appendChild(statsBlock(st));

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

  const remaining = Math.max(0, st.total - st.seen);
  const daysLeft = Math.ceil(remaining / Math.max(1, s.newPerDay));
  const paceNote = remaining
    ? `${st.seen} of ${st.total} started. At ${s.newPerDay || 1}/day, about ${daysLeft} more day${daysLeft === 1 ? '' : 's'} to introduce the rest.`
    : `All ${st.total} started.`;

  const pace = group([
    number('New words per day', paceNote,
      s.newPerDay, 0, 40, (v) => { setSetting('newPerDay', v); rerender(); }),
    number('Daily review cap', 'Anything over the cap is quietly held for another day.',
      s.dailyCap, 5, 200, (v) => { setSetting('dailyCap', v); rerender(); }),
  ]);
  root.appendChild(pace);

  root.appendChild(syncBlock(rerender));

  const data = document.createElement('div');
  data.className = 'group';
  data.appendChild(button('Export progress', doExport));
  if (hasSessionChanges()) {
    data.appendChild(button('Undo this session\'s reviews', () => {
      if (!confirm('Undo everything reviewed or introduced since you opened the app just now?\n\nOnly this session is affected -- anything from before stays exactly as it was. A copy of the current state is kept in this browser\'s storage either way.')) return;
      undoSession();
      rerender();
    }, true));
  }
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
  note.textContent = 'Progress is stored on this device by default — set up sync above to share it across devices. Export writes a JSON file you can keep as a backup either way.';
  root.appendChild(note);
}

function statsBlock(st) {
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

let connecting = false;
let connectError = null;

function syncBlock(rerender) {
  const st = sync.status();
  const wrap = document.createElement('div');
  wrap.className = 'group';

  if (!st.connected) {
    const row = document.createElement('div');
    row.className = 'row';
    row.style.flexDirection = 'column';
    row.style.alignItems = 'stretch';
    row.style.gap = '10px';

    row.appendChild(labelCell('Sync across devices',
      'Optional. Stores your progress in a private GitHub Gist so opening the app on another device picks it up. The token stays in this browser and is sent only to GitHub -- keep a copy of it somewhere durable (e.g. a password manager), since a device reset wipes the token along with everything else, and reconnecting needs it.'));

    const link = document.createElement('a');
    link.href = 'https://github.com/settings/tokens/new';
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'row-sub';
    link.style.display = 'block';
    link.textContent = 'Create a classic token, scope checkbox: “gist” only (nothing else) →';
    row.appendChild(link);

    const input = document.createElement('input');
    input.className = 'text-input';
    input.type = 'password';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.placeholder = 'github_pat_...';
    row.appendChild(input);

    if (connectError) {
      const err = document.createElement('p');
      err.className = 'row-sub';
      err.style.color = 'var(--again)';
      err.textContent = connectError;
      row.appendChild(err);
    }

    const btn = button(connecting ? 'Connecting…' : 'Connect', async () => {
      if (connecting) return;
      const token = input.value;
      if (!token.trim()) return;
      connecting = true;
      connectError = null;
      rerender();
      try {
        await sync.connect(token);
      } catch (e) {
        connectError = String(e.message || e);
      } finally {
        connecting = false;
        rerender();
      }
    });
    if (connecting) btn.disabled = true;
    row.appendChild(btn);

    wrap.appendChild(row);
    return wrap;
  }

  const statusRow = document.createElement('div');
  statusRow.className = 'row';
  const label = st.syncing ? 'Syncing…'
    : st.lastError ? `Sync error: ${st.lastError}`
    : st.lastSyncedAt ? `Synced ${describeInterval(st.lastSyncedAt, new Date())} ago`
    : 'Connected';
  statusRow.appendChild(labelCell('Sync across devices', label));
  wrap.appendChild(statusRow);

  wrap.appendChild(button('Sync now', async () => {
    try {
      await sync.syncNow({ force: true });
    } catch (e) {
      connectError = String(e.message || e);
    }
    rerender();
  }));
  wrap.appendChild(button('Disconnect this device', () => {
    if (!confirm('Stop syncing on this device?\n\nYour progress stays exactly as it is here, and the gist on GitHub is untouched -- this only removes the link between them. The token itself isn\'t revoked; do that on GitHub if you want it fully gone.')) return;
    sync.disconnect();
    rerender();
  }, true));

  return wrap;
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
