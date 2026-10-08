// Lesson rendering: body text with {n} placeholders -> corpus tokens (never typed Hebrew).
import { h, word } from './render.js';
import { D } from './data.js';

function inline(text, refs) {
  return text.split(/(\{\d+\}|`[^`]+`)/).map(part => {
    const m = part.match(/^\{(\d+)\}$/);
    if (m) {
      const ref = refs[+m[1]];
      if (!ref) return '';
      const hl = typeof ref.hl === 'number' ? ref.hl : null;
      return h('span', { class: 'lw' }, ref.ids.map(id => {
        const t = D.toks[id];
        return t ? word(t, { hl, tr: 'tap' }) : '';
      }));
    }
    if (part.startsWith('`') && part.length > 1) return h('code', {}, part.slice(1, -1));
    return part;
  });
}

export function lessonView(lesson) {
  const out = h('div', { class: 'lesson' }, h('h2', {}, lesson.title));
  for (const para of lesson.body.split(/\n\s*\n/)) {
    const lines = para.split('\n');
    if (lines.every(l => l.startsWith('- '))) {
      out.append(h('ul', {}, lines.map(l => h('li', {}, inline(l.slice(2), lesson.refs)))));
    } else {
      out.append(h('p', {}, inline(lines.join(' '), lesson.refs)));
    }
  }
  return out;
}
