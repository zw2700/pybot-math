# PyBot does math: browser demo

Served by GitHub Pages at https://zw2700.github.io/pybot-math/. PyBot runs entirely in the
visitor's browser with [Pyodide](https://pyodide.org); these are static files.

Adapted from the original [PyBot demo](https://huggingface.co/spaces/HuggingFaceSwarms/PyBot)
by Hugging Face: same page, worker and glue code, with this repo's bot. The bundle
(`pybot-<commit>-<hash>.zip`) holds `bot/**.py` as source rather than compiled bytecode,
plus `norm.json` and `lines.json` for locating each reply's text.
