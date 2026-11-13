"""The page's own logic that needs no browser (decisions §308): the modules of `gui/static/js/` run by node with the page's import map and a bare
`window`, so a rule such as the leaders' mood or the strip's counts is checked by calling it, not by driving a page. Skipped without node."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "orkboard" / "gui" / "static"
node = shutil.which("node")
pytestmark = pytest.mark.skipif(node is None, reason="node is not installed")

HOOKS = f"""
import {{ pathToFileURL }} from "node:url";
const S = {json.dumps(str(STATIC) + "/")};
const MAP = {{ "preact": "preact.mjs", "preact/hooks": "preact-hooks.mjs", "htm": "htm.mjs", "@preact/signals-core": "signals-core.mjs", "@preact/signals": "preact-signals.mjs" }};
export async function resolve(spec, ctx, next) {{
  if (MAP[spec]) return next(pathToFileURL(S + "vendor/" + MAP[spec]).href, ctx);
  if (spec.startsWith("/static/")) return next(pathToFileURL(S + spec.slice(8)).href, ctx);
  return next(spec, ctx);
}}
"""
REGISTER = 'import { register } from "node:module"; register("./hooks.mjs", import.meta.url);'
WINDOW = """
const store = new Map();
globalThis.location = { search: "", hash: "", protocol: "http:", host: "x", origin: "http://x", href: "http://x/", pathname: "/" };
globalThis.window = globalThis; globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
globalThis.localStorage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, String(v)), removeItem: (k) => store.delete(k) };
globalThis.sessionStorage = globalThis.localStorage;
globalThis.document = { addEventListener() {}, querySelector: () => null, querySelectorAll: () => [], documentElement: { dataset: {}, style: {} }, body: {}, head: { appendChild() {} },
  createElement: () => ({ style: {}, classList: { add() {}, remove() {} }, setAttribute() {}, addEventListener() {} }) };
globalThis.matchMedia = () => ({ matches: false, addEventListener() {} });
globalThis.WebSocket = class { close() {} send() {} };
globalThis.history = { replaceState() {}, pushState() {} };
"""


def run(tmp_path: Path, body: str):
    (tmp_path / "hooks.mjs").write_text(HOOKS)
    (tmp_path / "register.mjs").write_text(REGISTER)
    (tmp_path / "window.mjs").write_text(WINDOW)
    (tmp_path / "case.mjs").write_text('import "./window.mjs";\n' + body + "\nprocess.exit(0);\n")
    done = subprocess.run([node, "--import", "./register.mjs", "case.mjs"], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_a_leaders_mood_is_asleep_before_worried_before_focused(tmp_path):
    got = run(tmp_path, """
const { moodOf } = await import("/static/js/table/moods.js");
const { mapData } = await import("/static/js/shell/store.js");
const dry = { limits: [{ provider: "claude", name: "Claude", left: 0, rows: [{ window: "5h", left: 0, reset: "" }] }], mana: { main: "claude" } };
const fine = { limits: [{ provider: "claude", name: "Claude", left: 0.5, rows: [{ window: "5h", left: 0.5, reset: "" }] }], mana: { main: "claude" } };
const art = { slug: "art" }, worried = { slug: "art", concerns: { alerts: 1, notes: 0, status: "ready" } };
mapData.value = { goals: [], nodes: [] };
const calm = [moodOf(art, fine), moodOf(worried, fine), moodOf(art, {}), moodOf(null, fine), moodOf(null, dry)];
mapData.value = { goals: [], nodes: [{ slug: "x", state: "talk" }] };
console.log(JSON.stringify([...calm, moodOf(null, fine), moodOf(null, dry)]));
""")
    assert got == ["", "worried", "", "", "asleep", "focused", "asleep"]       # the Orkmaster's: asleep when its tool is dry, focused while it talks a goal


def test_the_strips_counts_come_from_the_snapshot_until_the_board_has_read_a_record(tmp_path):
    got = run(tmp_path, """
const { lookOf } = await import("/static/js/table/concerns.js");
const { mapData } = await import("/static/js/shell/store.js");
mapData.value = { goals: [{ slug: "tech", concerns: { alerts: 1, notes: 2, status: "ready" } }, { slug: "art" }], nodes: [] };
console.log(JSON.stringify(["tech", "art", "nobody"].map(lookOf)));
""")
    assert got == [{"status": "ready", "alerts": 1, "notes": 2, "error": "", "since": None},
                   {"status": "", "alerts": 0, "notes": 0, "error": "", "since": None},
                   {"status": "", "alerts": 0, "notes": 0, "error": "", "since": None}]
