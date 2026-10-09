// Opt-in sync to a private GitHub gist. With no token set this makes no requests.
// Token and gist id live in their own localStorage key, never in the progress state,
// so exports never contain them. Whole-state sync keyed on savedAt: runs on app open,
// at session end and after Settings changes (about 2 requests each time).
// If both this device and the gist changed since the last sync, Lane picks which to keep.
import { state, replace } from './store.js';

const KEY = 'hebrew.sync';
const API = 'https://api.github.com';
const FILE = 'hebrew-v1-progress.json';
const DESC = 'Hebrew reading app v1: progress and reports (written by the app)';

function meta() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
function setMeta(m) { try { localStorage.setItem(KEY, JSON.stringify(m)); } catch (e) { /* ignore */ } }

export const syncInfo = meta; // {token, gist, syncedAt, at, err}

async function gh(path, opts = {}) {
  const r = await fetch(API + path, { ...opts, signal: AbortSignal.timeout(10e3), headers: {
    Authorization: 'Bearer ' + meta().token, Accept: 'application/vnd.github+json' } });
  if (!r.ok) throw new Error(r.status === 401 ? 'token rejected (expired or revoked?)' : `GitHub error ${r.status}`);
  return r.json();
}

async function remote(id) {
  const f = (await gh('/gists/' + id)).files[FILE];
  if (!f) return null;
  return JSON.parse(f.truncated ? await (await fetch(f.raw_url)).text() : f.content);
}

const payload = s => ({ description: DESC, files: { [FILE]: { content: JSON.stringify(s) } } });

// Returns 'pushed' | 'pulled' | 'same' | 'off' | 'error'.
export async function sync() {
  const m = meta();
  if (!m.token) return 'off';
  let out = 'same';
  try {
    const s = state();
    const r = m.gist ? await remote(m.gist) : null;
    const remoteChanged = r && r.savedAt !== m.syncedAt;
    const localChanged = s.savedAt !== m.syncedAt;
    let pull = remoteChanged && !localChanged;
    if (remoteChanged && localChanged) {
      const when = d => d ? new Date(d).toLocaleString() : 'unknown';
      pull = !confirm(`Progress changed here and in the synced copy since the last sync.\n\nThis device: saved ${when(s.savedAt)}\nSynced copy: saved ${when(r.savedAt)}\n\nOK keeps this device's progress. Cancel takes the synced copy.`);
    }
    if (pull) {
      replace(r);
      out = 'pulled';
    } else if (!r || localChanged) {
      if (m.gist) await gh('/gists/' + m.gist, { method: 'PATCH', body: JSON.stringify(payload(s)) });
      else m.gist = (await gh('/gists', { method: 'POST', body: JSON.stringify({ ...payload(s), public: false }) })).id;
      out = 'pushed';
    }
    m.syncedAt = state().savedAt;
    m.at = new Date().toISOString();
    delete m.err;
  } catch (e) {
    m.err = e.message;
    out = 'error';
  }
  setMeta(m);
  return out;
}

// Store the token, find an existing gist from another device if there is one, then sync.
export async function connect(token) {
  setMeta({ token });
  try {
    const gists = await gh('/gists?per_page=100');
    const g = gists.find(x => x.files[FILE]);
    if (g) setMeta({ token, gist: g.id });
  } catch (e) {
    setMeta({ token, err: e.message });
    return 'error';
  }
  return sync();
}

export function disconnect() { try { localStorage.removeItem(KEY); } catch (e) { /* ignore */ } }
