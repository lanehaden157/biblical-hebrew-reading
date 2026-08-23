/**
 * Optional cross-device sync via a private GitHub Gist. Opt-in only -- with
 * no token configured this module makes zero network requests, so the "no
 * external requests other than the pinned ts-fsrs CDN" default in CLAUDE.md
 * still holds until the user explicitly turns this on in Settings.
 *
 * Why a Gist and not the app's own repo: this is a static site with no
 * backend, so the only way for the browser to "save to the site" itself is
 * to talk to an API directly. A Gist is a purpose-built place to stash one
 * JSON blob via a token; committing progress into the app's own repo on
 * every review would spam its commit history with scheduling noise that has
 * nothing to do with the app's actual source.
 *
 * The token lives in its own localStorage key (SYNC_KEY), never inside the
 * `hebrew:v1` state object store.js reads/writes -- exportBlob() must never
 * leak a credential into a file the user might back up or share. It is sent
 * only to api.github.com, in the Authorization header, and nowhere else.
 *
 * Security note (surfaced in Settings, not just here): the token sits in
 * this browser's storage so the app can use it on every save. Recommend a
 * CLASSIC token with only the "gist" scope checkbox checked (nothing else),
 * so a leaked token can't do more than read/write gists -- fine-grained
 * tokens would be the more modern choice, but as of this writing their
 * creation UI doesn't reliably expose a Gists permission at all, so classic
 * is the one that actually works today, not a weaker fallback chosen for
 * convenience.
 *
 * Merge strategy: per-card, not whole-blob. Card records are independent
 * (keyed by lemma_id or "parse:<id>") and each carries `reps` (monotonic:
 * only grows via review) and `last_review`, so the more-advanced/more-recent
 * side of each individual card wins, rather than one whole device's session
 * silently clobbering the other's -- reviewing card A on your phone and
 * card B on your laptop before the next sync should keep both, not just
 * whichever device happened to sync last. `introducedOn` is kept as the
 * earlier of the two regardless of which side wins the scheduling fields,
 * since that's a historical fact, not scheduling state.
 *
 * Known limitation, not fixed here: no optimistic-concurrency check (ETag)
 * on the gist write, so two devices syncing in the same few seconds could
 * race and one push could overwrite the other's. Acceptable for a
 * single-person hobby app syncing across a couple of devices; would need
 * real handling before this could serve multiple independent users.
 */
import { load, update, SCHEMA } from './store.js';

const SYNC_KEY = 'hebrew:sync:v1';
const GIST_FILENAME = 'hebrew-reading-progress.json';
const GIST_DESCRIPTION = 'Biblical Hebrew reading app -- progress sync (do not edit manually)';
const API = 'https://api.github.com';
const DEBOUNCE_MS = 3000;

function readSyncState() {
  try {
    const s = localStorage.getItem(SYNC_KEY);
    return s ? JSON.parse(s) : {};
  } catch {
    return {};
  }
}

function writeSyncState(patch) {
  const next = { ...readSyncState(), ...patch };
  localStorage.setItem(SYNC_KEY, JSON.stringify(next));
  return next;
}

export function status() {
  const s = readSyncState();
  return {
    connected: Boolean(s.token && s.gistId),
    lastSyncedAt: s.lastSyncedAt || null,
    lastError: s.lastError || null,
    syncing: Boolean(s.syncing),
  };
}

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

async function apiFetch(path, token, init = {}) {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { ...authHeaders(token), ...(init.headers || {}) },
  });
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.json()).message || ''; } catch { /* ignore */ }
    if (res.status === 401) throw new Error('Token was rejected -- check it was copied correctly and hasn\'t expired.');
    if (res.status === 403) throw new Error(`Forbidden (rate limit, or the token isn't scoped to Gists). ${detail}`);
    if (res.status === 404) throw new Error('Gist not found -- it may have been deleted on GitHub.');
    throw new Error(`GitHub API error ${res.status}: ${detail || res.statusText}`);
  }
  return res.json();
}

/** Find this app's own progress gist among the token's existing gists, if
 *  one was already created (by this device or another). Scans up to 500
 *  gists (5 pages) -- fine for a personal account, not built for more. */
async function findExistingGist(token) {
  for (let page = 1; page <= 5; page++) {
    const gists = await apiFetch(`/gists?per_page=100&page=${page}`, token);
    const match = gists.find((g) => g.description === GIST_DESCRIPTION && g.files && g.files[GIST_FILENAME]);
    if (match) return match.id;
    if (gists.length < 100) break;
  }
  return null;
}

async function createGist(token, state) {
  const gist = await apiFetch('/gists', token, {
    method: 'POST',
    body: JSON.stringify({
      description: GIST_DESCRIPTION,
      public: false,
      files: { [GIST_FILENAME]: { content: JSON.stringify(state, null, 2) } },
    }),
  });
  return gist.id;
}

async function pullGist(token, gistId) {
  const gist = await apiFetch(`/gists/${gistId}`, token);
  const file = gist.files[GIST_FILENAME];
  if (!file) return null;
  if (file.truncated) {
    // Progress blobs are small (a few hundred KB even at full review-history
    // scale); truncation would mean something unexpected wrote to this gist.
    // Refuse to merge from a partial read rather than silently dropping cards.
    throw new Error('Remote progress file is unexpectedly large and was truncated by GitHub -- refusing to merge from a partial copy.');
  }
  try {
    return JSON.parse(file.content);
  } catch {
    throw new Error('Remote progress file is not valid JSON.');
  }
}

async function pushGist(token, gistId, state) {
  await apiFetch(`/gists/${gistId}`, token, {
    method: 'PATCH',
    body: JSON.stringify({
      files: { [GIST_FILENAME]: { content: JSON.stringify(state, null, 2) } },
    }),
  });
}

/** The one card in {a, b} that represents more/newer review activity.
 *  `reps` only grows through review, so it's a reliable "more advanced"
 *  signal before falling back to last_review recency. */
function betterCard(a, b) {
  if (!a) return b;
  if (!b) return a;
  const ar = a.reps || 0, br = b.reps || 0;
  if (ar !== br) return ar > br ? a : b;
  const at = a.last_review ? new Date(a.last_review).getTime() : 0;
  const bt = b.last_review ? new Date(b.last_review).getTime() : 0;
  return bt > at ? b : a;
}

function earlierDay(a, b) {
  return [a, b].filter(Boolean).sort()[0];
}

/** Per-card merge -- see module docstring for why this isn't a whole-blob
 *  "newer wins". Settings are deliberately NOT merged: they're a per-device
 *  preference (sound, theme, daily cap), not progress, so the local
 *  device's own settings are always kept as-is. */
export function mergeStates(local, remote) {
  if (!remote || remote.schemaVersion !== SCHEMA.SCHEMA_VERSION) return local;
  const cards = { ...local.cards };
  for (const key of Object.keys(remote.cards || {})) {
    const winner = betterCard(local.cards[key], remote.cards[key]);
    cards[key] = {
      ...winner,
      introducedOn: earlierDay(local.cards[key] && local.cards[key].introducedOn, remote.cards[key] && remote.cards[key].introducedOn) || winner.introducedOn,
    };
  }
  return { ...local, cards };
}

/** First-time setup: validate the token, find-or-create the progress gist,
 *  merge whatever's already there with local state, and push the merged
 *  result back so both sides converge. Throws with a user-facing message
 *  on any failure; nothing is persisted locally until this succeeds. */
export async function connect(token) {
  token = token.trim();
  if (!token) throw new Error('Paste a token first.');

  let gistId = await findExistingGist(token);
  const local = load();
  let merged = local;

  if (gistId) {
    const remote = await pullGist(token, gistId);
    merged = mergeStates(local, remote);
  } else {
    gistId = await createGist(token, local);
  }

  await pushGist(token, gistId, merged);
  update((s) => { Object.assign(s, merged); });
  writeSyncState({ token, gistId, lastSyncedAt: new Date().toISOString(), lastError: null });
}

export function disconnect() {
  // Clears this device's link only -- the gist itself (and its content)
  // stays on GitHub. Revoking or deleting the token is a separate, manual
  // step on GitHub's side; this app has no way to do that for you.
  localStorage.removeItem(SYNC_KEY);
}

/** Pull, merge, and push once. Used both for the "Sync now" button and for
 *  the one automatic pull-on-boot (see main.js) -- opening the app on a
 *  second device should pick up the first device's latest progress without
 *  waiting for that device to make a new change first. */
export async function syncNow() {
  const s = readSyncState();
  if (!s.token || !s.gistId) return;
  writeSyncState({ syncing: true });
  try {
    const remote = await pullGist(s.token, s.gistId);
    const local = load();
    const merged = mergeStates(local, remote);
    await pushGist(s.token, s.gistId, merged);
    update((state) => { Object.assign(state, merged); });
    writeSyncState({ syncing: false, lastSyncedAt: new Date().toISOString(), lastError: null });
  } catch (e) {
    writeSyncState({ syncing: false, lastError: String(e.message || e) });
    throw e;
  }
}

let debounceTimer = null;

/** Called from store.js on every save() (via the hook main.js wires up at
 *  boot) -- debounced so a burst of grades in one review session produces
 *  one push, not one per card. No-ops entirely when sync isn't configured,
 *  so a device that never connects never makes a network request. */
export function scheduleSync() {
  const s = readSyncState();
  if (!s.token || !s.gistId) return;
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debounceTimer = null;
    syncNow().catch((e) => console.warn('background sync failed', e));
  }, DEBOUNCE_MS);
}
