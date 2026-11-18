// PyBot in a Web Worker: Pyodide (CPython compiled to WebAssembly) runs the bot's Python, so the page stays responsive.
// Messages in:  {type: "turn", id, text} | {type: "reset"}
// Messages out: {type: "progress", stage, loaded?, total?} | {type: "ready", ...} | {type: "reply", id, ...} | {type: "error", id?, message}
// A module worker: new Worker("worker.js", {type: "module"}).
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
const BUNDLE = "pybot-c1d6e69755ac-bea47ff7.zip";  // bot/**.py source (the upstream demo ships .pyc compiled for this Pyodide's Python, plus norm.json and lines.json; renamed on every rebuild so browsers don't reuse a cached copy
const CACHE = "pybot-bundles-v1";

const post = (msg) => self.postMessage(msg);

// Like transformers.js caches model files: the bundle is downloaded once, then read from Cache Storage.
async function fetchBundle() {
  const url = new URL(BUNDLE, self.location.href).href;
  let cache = null;
  try { cache = await caches.open(CACHE); } catch { /* no Cache Storage (e.g. private window): download every time */ }
  const hit = cache && await cache.match(url).catch(() => null);
  if (hit) {
    post({type: "progress", stage: "cached"});
    return new Uint8Array(await hit.arrayBuffer());
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not download PyBot (HTTP ${res.status}).`);
  const total = Number(res.headers.get("content-length")) || 0;
  const reader = res.body.getReader(), chunks = [];
  let loaded = 0;
  for (;;) {
    const {done, value} = await reader.read();
    if (done) break;
    chunks.push(value); loaded += value.length;
    post({type: "progress", stage: "download", loaded, total});
  }
  const bytes = new Uint8Array(loaded);
  let at = 0;
  for (const c of chunks) { bytes.set(c, at); at += c.length; }
  if (cache) {
    // Keep one bundle: drop older commits' bundles, then store this one.
    for (const req of await cache.keys()) if (req.url !== url) await cache.delete(req);
    await cache.put(url, new Response(bytes, {headers: {"content-type": "application/zip"}})).catch(() => {});
  }
  return bytes;
}

let web = null;
const ready = (async () => {
  post({type: "progress", stage: "runtime"});
  const [py, bundle, glue] = await Promise.all([
    loadPyodide({indexURL: PYODIDE, env: {PYTHONHASHSEED: "0"}}),  // the eval server's hash seed, so replies match
    fetchBundle(),
    fetch("pybot_web.py").then((r) => { if (!r.ok) throw new Error("Could not download pybot_web.py."); return r.text(); }),
  ]);
  post({type: "progress", stage: "import"});
  py.unpackArchive(bundle, "zip", {extractDir: "/pybot"});
  py.FS.writeFile("/pybot_web.py", glue);
  py.runPython("import sys; sys.path.insert(0, '/')");
  web = py.pyimport("pybot_web");
  const info = web.load().toJs({dict_converter: Object.fromEntries});
  web.reset();
  post({type: "ready", ...info, python: py.runPython("import sys; sys.version.split()[0]"), pyodide: py.version});
})().catch((err) => post({type: "error", message: String(err && err.message || err)}));

self.onmessage = async ({data}) => {
  await ready;
  if (!web) return;
  if (data.type === "reset") { web.reset(); return; }
  if (data.type === "turn") {
    try {
      post({type: "reply", id: data.id, ...JSON.parse(web.turn(data.text))});
    } catch (err) {
      post({type: "error", id: data.id, message: String(err && err.message || err)});
    }
  }
};
