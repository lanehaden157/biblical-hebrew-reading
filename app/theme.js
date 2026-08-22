/**
 * Light/dark. Three states, not two: 'system' follows the phone, 'light' and
 * 'dark' override it. A two-way toggle has no way to say "go back to following
 * the phone", which matters when the phone switches at sunset.
 *
 * Whatever the mode, exactly one attribute drives the CSS: data-theme is set to
 * the resolved value ('light' or 'dark'), so app.css never has to reason about
 * media queries and the resolved theme is inspectable in the DOM.
 */

import { settings, setSetting } from './store.js';

const mql = window.matchMedia('(prefers-color-scheme: dark)');

export function resolved() {
  const mode = settings().theme;
  if (mode === 'light' || mode === 'dark') return mode;
  return mql.matches ? 'dark' : 'light';
}

export function apply() {
  const theme = resolved();
  document.documentElement.setAttribute('data-theme', theme);
  return theme;
}

export function set(mode) {
  setSetting('theme', mode);
  return apply();
}

export function init() {
  apply();
  // Only meaningful in 'system' mode, but harmless to leave attached: apply()
  // re-reads the setting each time and is a no-op when overridden.
  const onChange = () => { if (settings().theme === 'system') apply(); };
  if (typeof mql.addEventListener === 'function') mql.addEventListener('change', onChange);
  else if (typeof mql.addListener === 'function') mql.addListener(onChange);
}
