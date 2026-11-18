"""PyBot in the browser: load the bot once, then answer turns and explain each reply.

Ported from the PyBot Space's server (bot_runner.py's LOADER and traced(), app.py's answer_source()):
- Random seeds are fixed the way the eval server fixes them, so replies match the benchmark run as
  closely as a browser allows. The server forks a fresh worker per request; here `reset()` restores the
  just-loaded random state and starts a new memory instead.
- For each reply: the module that won (and the lines of its respond()), the ones that also proposed a reply,
  the bot files and functions the winner called with their line ranges (sys.monitoring, one PY_START event
  per function), and the file and line holding the reply's text.
"""
import json
import os
import random
import re
import sys
import time

ROOT = "/pybot"
SEED = 0
_norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())

_rt = None
_loaded_state = None
_memory = {}
_files = {}       # handler name -> {file: [[first line, last line, function name], ...]} for the last turn
_responds = {}    # handler name -> [file, first line, last line] of its respond()
_sources = None   # file -> its text, letters and digits only (norm.json)
_lines = None     # file -> letters and digits on each line (lines.json)
_MAX_CALLS = 40   # functions listed per file; the first one called is what a click opens


def load():
    """Import the bot (seconds); returns {"load_s", "modules", "handlers"}."""
    global _rt, _loaded_state
    sys.path.insert(0, ROOT)
    # Modules make their own random.Random(), which seeds itself from the OS: derive those seeds
    # from the run's seed and a counter instead, so every load starts in the same state.
    os_seeded, created = random.Random.seed, iter(range(1 << 62))

    def derived_seed(self, a=None, version=2):
        os_seeded(self, f"{SEED}:{next(created)}" if a is None else a, version)

    random.Random.seed = derived_seed
    random.seed = random._inst.seed
    random.seed(SEED)
    started = time.monotonic()
    import bot.runtime as rt

    _rt = rt
    _loaded_state = random.getstate()
    _watch_handlers()
    return {"load_s": round(time.monotonic() - started, 2), "modules": len(rt._MODULES), "handlers": len(rt._HANDLERS),
            "responds_found": len(_responds)}


def _span(code):
    """[file, first line, last line] of a code object in the bot, or None."""
    bot_dir = os.path.join(ROOT, "bot") + os.sep
    if not code.co_filename.startswith(bot_dir):
        return None
    last = max((line for _, _, line in code.co_lines() if line), default=code.co_firstlineno)
    return ["bot/" + code.co_filename[len(bot_dir):], code.co_firstlineno, last]


def _own_respond(name, respond):
    """[file, first, last] of the respond() written in bot/modules/<name>.py. Many handlers are wrapped by decorators
    from other bot files, so look through __wrapped__ and closures (breadth first, a few levels) for it."""
    want = f"bot/modules/{name}.py"
    queue, seen = [respond], set()
    while queue and len(seen) < 50:
        fn = queue.pop(0)
        if id(fn) in seen:
            continue
        seen.add(id(fn))
        code = getattr(fn, "__code__", None)
        span = _span(code) if code else None
        if span and span[0] == want:
            return span
        queue += [x for x in [getattr(fn, "__wrapped__", None)] if callable(x)]
        for cell in getattr(fn, "__closure__", None) or ():
            try:
                if callable(cell.cell_contents):
                    queue.append(cell.cell_contents)
            except ValueError:  # an empty cell
                pass
    return None


def _watch_handlers():
    """Wrap every respond() so a turn records the bot files and functions each handler called."""
    mon, tool = sys.monitoring, 5
    seen = {}  # file -> [[first, last, name], ...] in the order the functions first ran
    mon.use_tool_id(tool, "pybot-trace")

    def start(code, offset):
        span = _span(code)
        if span:
            calls = seen.setdefault(span[0], [])
            # module-level code (a lazy import) marks the file as used but has no function to point at
            if code.co_name != "<module>" and len(calls) < _MAX_CALLS:
                calls.append([span[1], span[2], code.co_qualname])
        return mon.DISABLE

    mon.register_callback(tool, mon.events.PY_START, start)

    def watch(name, respond):
        def run(text, mem):
            seen.clear()
            mon.restart_events()
            mon.set_events(tool, mon.events.PY_START)
            try:
                return respond(text, mem)
            finally:
                mon.set_events(tool, 0)
                _files[name] = {f: list(calls) for f, calls in seen.items()}
        return run

    for name, _, respond in _rt._HANDLERS:
        span = _own_respond(name, respond)
        if span:
            _responds[name] = span
    _rt._HANDLERS = [(name, priority, watch(name, respond)) for name, priority, respond in _rt._HANDLERS]


def reset():
    """A new conversation: empty memory and the just-loaded random state."""
    global _memory
    _memory = {}
    random.setstate(_loaded_state)


def turn(text):
    """One reply as JSON: {"reply", "module", "candidates", "files", "calls", "respond", "source", "source_line", "ms"}.
    files: the bot files the winner called; calls: {file: [[first line, last line, function], ...]};
    respond: [file, first line, last line] of the winner's respond(); source_line: 1-based."""
    text = " ".join(str(text).split())
    _files.clear()
    started = time.monotonic()
    decision = {}
    try:
        decision = _rt.turn(text, _memory)
        reply = " ".join(str(decision["reply"]).split()) or "Hello!"
    except Exception:  # noqa: BLE001 - the fixed __main__'s rule
        reply = "Hello!"
    ms = round((time.monotonic() - started) * 1000)
    module = decision.get("module")
    calls = _files.get(module, {}) if module else {}
    files = sorted(calls)
    source, source_line = answer_source(reply, files)
    return json.dumps({"reply": reply, "module": module,
                       "candidates": [c["module"] for c in decision.get("candidates", [])],
                       "files": files, "calls": calls, "respond": _responds.get(module) if module else None,
                       "source": source, "source_line": source_line, "ms": ms})


def answer_source(reply, used):
    """(file, line) of the one file that holds the reply verbatim (its first 40+ letters/digits), preferring files the
    winner called; (None, None) when the reply is composed, too short, or found in several files."""
    global _sources, _lines
    if _sources is None:  # built by build_bundle.py
        with open(os.path.join(ROOT, "norm.json"), encoding="utf-8") as handle:
            _sources = json.load(handle)
        with open(os.path.join(ROOT, "lines.json"), encoding="utf-8") as handle:
            _lines = json.load(handle)
    text = _norm(reply)
    for n in (60, 40):
        key = text[:n]
        if len(key) < 20:  # too short to point at one place
            continue
        hits = [f for f, body in _sources.items() if key in body]
        hits = hits if len(hits) == 1 else [f for f in hits if f in used]
        if len(hits) == 1:
            return hits[0], _line_of(hits[0], _sources[hits[0]].find(key))
    return None, None


def _line_of(path, offset):
    """The 1-based line holding the offset-th letter/digit of a file."""
    seen = 0
    for number, count in enumerate(_lines.get(path, ()), 1):
        seen += count
        if offset < seen:
            return number
    return None
