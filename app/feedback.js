/**
 * Haptics and sound, behind one shim so no view has to know what the platform
 * supports. Every function is a no-op when unsupported or switched off.
 *
 * Haptics:
 *   - navigator.vibrate() is the standard API. Android supports it. iOS Safari
 *     does not, and never has -- that is a deliberate WebKit position.
 *   - iOS 17.4+ renders <input type="checkbox" switch> as a native switch, and
 *     toggling it produces real haptic feedback. Clicking a hidden one is the
 *     only route to haptics in an iOS web app. It is undocumented behaviour and
 *     may disappear in an iOS release; if it does, haptics silently stop and
 *     nothing else breaks. The probe must be laid out (not display:none) or the
 *     haptic does not fire, hence .haptic-probe in app.css.
 *
 * Sound:
 *   - Web Audio, oscillator-generated. No audio files, so nothing to ship and
 *     nothing to fetch.
 *   - On iPhone this is muted by the physical silent switch, and a web page
 *     cannot opt out the way a native app can. That is why sound defaults off:
 *     a feature that is inaudible for most users most of the time should be
 *     opt-in rather than mysteriously broken.
 */

import { settings } from './store.js';

let probe = null;
let audioCtx = null;

function hapticProbe() {
  if (probe) return probe;
  probe = document.createElement('input');
  probe.type = 'checkbox';
  probe.setAttribute('switch', '');
  probe.className = 'haptic-probe';
  probe.setAttribute('aria-hidden', 'true');
  probe.tabIndex = -1;
  document.body.appendChild(probe);
  return probe;
}

/** True only where the iOS switch element actually exists. Safari reports a
 *  non-default `switch` property on the element when it supports it. */
function iosSwitchAvailable() {
  const el = hapticProbe();
  return 'switch' in el;
}

export function vibrate(pattern) {
  if (!settings().haptics) return;
  if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
    try {
      navigator.vibrate(pattern);
      return;
    } catch { /* fall through to the iOS path */ }
  }
  if (iosSwitchAvailable()) {
    // Must happen inside the user gesture that called us, which it does --
    // every caller runs from a click handler.
    try { hapticProbe().click(); } catch { /* nothing else to try */ }
  }
}

function tone(freq, ms, gain = 0.05) {
  if (!settings().sound) return;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    if (!audioCtx) audioCtx = new Ctx();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const amp = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.value = freq;
    // Short ramps: a square-edged gate on a sine clicks audibly.
    const t = audioCtx.currentTime;
    amp.gain.setValueAtTime(0, t);
    amp.gain.linearRampToValueAtTime(gain, t + 0.012);
    amp.gain.exponentialRampToValueAtTime(0.0001, t + ms / 1000);
    osc.connect(amp).connect(audioCtx.destination);
    osc.start(t);
    osc.stop(t + ms / 1000 + 0.02);
  } catch (e) {
    console.warn('sound unavailable', e);
  }
}

/** Card advanced a stage. Lightest possible feedback -- this fires a lot. */
export function tap() {
  vibrate(8);
}

export function right() {
  vibrate(12);
  tone(660, 90);
}

export function wrong() {
  vibrate([14, 40, 14]);
  tone(300, 150);
}

export function finish() {
  vibrate([10, 60, 10, 60, 18]);
  tone(523, 110);
  setTimeout(() => tone(784, 180), 110);
}

/** Reported in Settings so the toggles can say what they will actually do,
 *  rather than offering a switch that does nothing on this device. */
export function capabilities() {
  const nav = typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function';
  return {
    vibrateApi: nav,
    iosSwitch: !nav && iosSwitchAvailable(),
    haptics: nav || iosSwitchAvailable(),
    audio: !!(window.AudioContext || window.webkitAudioContext),
  };
}
