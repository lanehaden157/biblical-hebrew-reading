/**
 * Sound feedback, behind one shim so no view has to know whether Web Audio
 * is available. Every function is a no-op when unsupported or switched off.
 *
 * Haptics were tried and dropped (2026-08): navigator.vibrate() does not
 * exist on iOS Safari, and the undocumented <input type="checkbox" switch>
 * trick was implemented, hardened, and confirmed on real iPhone hardware to
 * not fire. Not worth carrying dead code and a settings toggle that does
 * nothing for a platform iOS Safari doesn't expose a real API for.
 *
 * Sound:
 *   - Web Audio, oscillator-generated. No audio files, so nothing to ship and
 *     nothing to fetch.
 *   - On iPhone this is muted by the physical silent switch, and a web page
 *     cannot opt out the way a native app can.
 *   - iOS suspends an AudioContext aggressively (after backgrounding, after a
 *     stretch of silence). Every tone() call awaits resume() before scheduling
 *     anything -- scheduling against a still-suspended context's currentTime
 *     is the reason early testing had sound that "worked for some presses but
 *     not others": whichever tap arrived while suspended was silently dropped.
 */

import { settings } from './store.js';

let audioCtx = null;

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

function scheduleSweep(ctx, f1, f2, startAt, ms, gain) {
  const osc = ctx.createOscillator();
  const amp = ctx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(f1, startAt);
  // Exponential, not linear -- pitch is perceived logarithmically, so this
  // is the ramp shape that actually sounds like a smooth glide.
  osc.frequency.exponentialRampToValueAtTime(f2, startAt + ms / 1000);
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

/** One glissando from f1 to f2 -- used for motion (switching views), where a
 *  pitch glide reads as "moving" in a way a static tone doesn't. */
async function playSweep(f1, f2, ms, gain = 0.035) {
  if (!settings().sound) return;
  const ctx = ensureAudioCtx();
  if (!ctx) return;
  try {
    if (ctx.state === 'suspended') await ctx.resume();
    scheduleSweep(ctx, f1, f2, ctx.currentTime + 0.005, ms, gain);
  } catch (e) {
    console.warn('sound unavailable', e);
  }
}

/** Card advanced a stage. One tone per stage, pitched to rise across the
 *  reveal (stage 1: transliteration: A4; stage 2: gloss: C#5) so decoding
 *  then meaning read as two steps up, not one repeated blip -- and stay
 *  clear of the grade tones (300/660/784+988/finish) so a review session
 *  never confuses "revealed" with "graded". */
export function tap(stage) {
  if (stage === 1) playTones([[440, 70]], 0.032);
  else if (stage === 2) playTones([[554, 90]], 0.032);
}

/** Tab bar navigation. A short pitch glide rather than a tone -- reads as
 *  motion, matching the tab bar's left-to-right layout: sweeping up for a
 *  tab to the right, down for a tab to the left. dir is +1 or -1. */
export function switchView(dir) {
  if (dir > 0) playSweep(320, 500, 90);
  else playSweep(500, 320, 90);
}

/** Reader tap-to-reveal. Deliberately different for a word already in the
 *  vocab deck (a quiet, low confirm -- "yes, you know this one") vs. one
 *  that isn't (a brighter two-note sparkle -- flags it as worth noticing,
 *  echoing the underline read.js already draws under new-vocabulary words). */
export function readReveal(isKnown) {
  if (isKnown) playTones([[500, 55]], 0.03);
  else playTones([[880, 45], [1175, 65]], 0.035);
}

/** One distinct tone per grade, so the sound carries information rather than
 *  being one repeated blip: a low buzz for Again, a clean confirm for Good,
 *  a bright rising pair for Easy. */
export function grade(key) {
  if (key === 'again') {
    playTones([[300, 150]]);
  } else if (key === 'easy') {
    playTones([[784, 90], [988, 140]]);
  } else {
    playTones([[660, 100]]);
  }
}

export function finish() {
  playTones([[523, 110], [659, 110], [784, 170]]);
}
