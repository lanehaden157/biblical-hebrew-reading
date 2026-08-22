/**
 * Haptics and sound, behind one shim so no view has to know what the platform
 * supports. Every function is a no-op when unsupported or switched off.
 *
 * Haptics:
 *   - navigator.vibrate() is the standard API. Android supports it. iOS Safari
 *     does not, and never has -- that is a deliberate WebKit position.
 *   - iOS 17.4+ is reported to render <input type="checkbox" switch> as a
 *     native switch, and toggling it produces real haptic feedback. This is
 *     undocumented behaviour, and confirmed-in-testing (2026-08) to NOT
 *     reliably fire from this app -- it may be iOS-version-dependent, may
 *     require a genuine touch rather than a synthetic .click(), or may simply
 *     not exist the way the trick is usually described. The probe is kept
 *     because it is harmless when it does nothing, but the setting should be
 *     understood as experimental, not guaranteed, on iPhone.
 *   - The probe must be laid out and within the viewport (not display:none,
 *     not pushed off-screen) or WebKit appears to skip it entirely.
 *
 * Sound:
 *   - Web Audio, oscillator-generated. No audio files, so nothing to ship and
 *     nothing to fetch.
 *   - On iPhone this is muted by the physical silent switch, and a web page
 *     cannot opt out the way a native app can. That is why sound defaults off.
 *   - iOS suspends an AudioContext aggressively (after backgrounding, after a
 *     stretch of silence). Every tone() call awaits resume() before scheduling
 *     anything -- scheduling against a still-suspended context's currentTime
 *     is the reason early testing had sound that "worked for some presses but
 *     not others": whichever tap arrived while suspended was silently dropped.
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

/** Best-effort signal only, shown in Settings copy -- not used to gate
 *  whether we attempt the click, since a false negative here would silently
 *  disable haptics on a phone that actually supports the trick. */
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
  // Always attempted, not gated on detection -- see the note above. Must
  // happen inside the user gesture that called us, which it does: every
  // caller runs from a click handler.
  try { hapticProbe().click(); } catch { /* nothing else to try */ }
}

function ensureAudioCtx() {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return null;
  if (!audioCtx) audioCtx = new Ctx();
  return audioCtx;
}

function scheduleTone(ctx, freq, startAt, ms, gain) {
  const osc = ctx.createOscillator();
  const amp = ctx.createGain();
  osc.type = 'sine';
  osc.frequency.value = freq;
  // Short ramps: a square-edged gate on a sine clicks audibly.
  amp.gain.setValueAtTime(0, startAt);
  amp.gain.linearRampToValueAtTime(gain, startAt + 0.012);
  amp.gain.exponentialRampToValueAtTime(0.0001, startAt + ms / 1000);
  osc.connect(amp).connect(ctx.destination);
  osc.start(startAt);
  osc.stop(startAt + ms / 1000 + 0.02);
}

/** Plays a short sequence of [freq, ms] notes back to back. Awaits resume()
 *  before touching currentTime -- see the sound note above for why. */
async function playTones(specs, gain = 0.05) {
  if (!settings().sound) return;
  const ctx = ensureAudioCtx();
  if (!ctx) return;
  try {
    if (ctx.state === 'suspended') await ctx.resume();
    let t = ctx.currentTime + 0.005;
    for (const [freq, ms] of specs) {
      scheduleTone(ctx, freq, t, ms, gain);
      t += ms / 1000 + 0.02;
    }
  } catch (e) {
    console.warn('sound unavailable', e);
  }
}

/** Card advanced a stage. Lightest possible feedback -- this fires a lot,
 *  haptic only, deliberately silent so grading is the only moment with sound. */
export function tap() {
  vibrate(8);
}

/** One distinct tone per grade, so the sound carries information rather than
 *  being one repeated blip: a low buzz for Again, a clean confirm for Good,
 *  a bright rising pair for Easy. */
export function grade(key) {
  if (key === 'again') {
    vibrate([14, 40, 14]);
    playTones([[300, 150]]);
  } else if (key === 'easy') {
    vibrate([10, 30, 14]);
    playTones([[784, 90], [988, 140]]);
  } else {
    vibrate(12);
    playTones([[660, 100]]);
  }
}

export function finish() {
  vibrate([10, 60, 10, 60, 18]);
  playTones([[523, 110], [659, 110], [784, 170]]);
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
