// Report a problem: records the report, quarantines the item (hidden from all queues).
import { h } from './render.js';
import { state, save } from './store.js';

const REASONS = [
  ['gloss', 'English meaning is wrong'],
  ['hebrew', 'Hebrew, parse or highlight is wrong'],
  ['translit', 'Transliteration is wrong'],
  ['other', 'Something else'],
];

// Resolves true if a report was filed, false if cancelled.
export function reportDialog(item, box) {
  return new Promise(res => {
    let reason = null;
    const note = h('textarea', { rows: 3, placeholder: 'Note (optional)' });
    const send = h('button', { class: 'primary', disabled: true }, 'Report and hide this item');
    const close = v => { overlay.remove(); res(v); };
    const overlay = h('div', { class: 'overlay' }, h('div', { class: 'sheet' },
      h('h3', {}, 'Report a problem'),
      REASONS.map(([k, label]) => h('button', { class: 'row-btn reason', onclick: e => {
        reason = k;
        overlay.querySelectorAll('.reason').forEach(b => b.classList.remove('sel'));
        e.currentTarget.classList.add('sel');
        send.disabled = false;
      } }, label)),
      note,
      h('div', { class: 'bar' }, h('button', { onclick: () => close(false) }, 'Cancel'), send)));
    send.addEventListener('click', () => {
      const s = state();
      const toks = [...box.querySelectorAll('[data-id]')].map(e => e.dataset.id);
      s.reports.push({ t: new Date().toISOString(), id: item.id, kind: item.kind, reason,
        note: note.value.trim(), toks: [...new Set(toks)] });
      if (!s.quarantine.includes(item.id)) s.quarantine.push(item.id);
      save();
      close(true);
    });
    document.body.append(overlay);
  });
}

export function restore(id) {
  const s = state();
  s.quarantine = s.quarantine.filter(x => x !== id);
  save();
}
