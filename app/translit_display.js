/**
 * Renders a transliteration string as a DOM fragment, giving alef (') and
 * ayin (`) distinct colors instead of leaving them as two ASCII marks that
 * look nearly identical at phone size -- the exact confusion behind
 * 'im ("if") vs `im ("with"): same three letters, unrelated meanings,
 * differing only by which one of these two marks starts the word.
 *
 * Display-only: the underlying text (what gets selected/copied) is
 * untouched plain ASCII, per CLAUDE.md's transliteration scheme -- only a
 * <span class> wraps each mark, so copy-paste still yields ' and ` exactly
 * as typed.
 */
const MARK_RE = /(['`])/g;

export function translitFrag(text) {
  const frag = document.createDocumentFragment();
  let last = 0;
  let m;
  MARK_RE.lastIndex = 0;
  while ((m = MARK_RE.exec(text))) {
    if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
    const span = document.createElement('span');
    span.className = m[1] === "'" ? 'translit-alef' : 'translit-ayin';
    span.textContent = m[1];
    frag.appendChild(span);
    last = m.index + 1;
  }
  if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
  return frag;
}
