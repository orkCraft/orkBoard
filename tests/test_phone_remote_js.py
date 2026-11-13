"""The phone's way through the project's remote (pwa/shell-remote*.js, docs/specs/136 C), run by node with a fake `fetch` and a fake storage: no network, no page. Skipped without node.
The repository and token are checked when they are given (private, and a token that can write), kept only then, and go to GitHub's API alone; the lines of the limits and a refused token."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


PWA = Path(__file__).resolve().parent.parent / "orkboard" / "gui" / "static" / "pwa"
node = shutil.which("node")

PRELUDE = """
const mod = (n) => import(process.argv[1] + n);
const {makeRemote} = await mod("shell-remote.js");
const api = await mod("shell-remote-api.js");
const words = await mod("shell-remote-words.js");
class Store { constructor() { this.m = new Map(); } getItem(k) { return this.m.has(k) ? this.m.get(k) : null; } setItem(k, v) { this.m.set(k, String(v)); } removeItem(k) { this.m.delete(k); } }
const reply = (status, body, headers = {}) => ({ ok: status >= 200 && status < 300, status, headers: { get: (k) => headers[k.toLowerCase()] ?? null }, text: async () => (typeof body === "string" ? body : JSON.stringify(body)) });
/** A GitHub that answers `routes[\"METHOD path\"]` (a function of the request, or a reply) and records every call. */
function github(routes) {
  const calls = [];
  const fetch = async (url, init = {}) => {
    const u = new URL(url), key = `${init.method || "GET"} ${u.pathname}${u.search}`;
    calls.push({ key, url, init, body: init.body ? JSON.parse(init.body) : null });
    if (u.origin !== "https://api.github.com") throw new Error("a call to " + u.origin);
    const r = routes[key] ?? routes[key.split("?")[0]];
    if (!r) return reply(404, { message: "Not Found" });
    return typeof r === "function" ? r(init, calls) : r;
  };
  return { fetch, calls };
}
const out = (v) => console.log(JSON.stringify(v));
"""


def run(body: str) -> dict:
    script = PRELUDE + "\n" + body
    done = subprocess.run([node, "--input-type=module", "-e", script, (PWA.as_uri() + "/")], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout.strip().splitlines()[-1])


REPO = '{ private: true, full_name: "me/game", permissions: { push: true } }'


def test_a_private_repository_and_a_token_that_can_write_are_kept_and_checked_against_the_api():
    got = run(f"""
const s = new Store(), g = github({{"GET /repos/me/game": reply(200, {REPO})}});
const r = makeRemote({{ fetch: g.fetch, storage: s }});
const before = r.ready();
const saved = await r.save({{ repo: "https://github.com/me/game.git", token: "ghp_secret" }});
out({{ before, saved, ready: r.ready(), settings: r.settings(), calls: g.calls.map((c) => c.key), auth: g.calls[0].init.headers.Authorization,
      kept: JSON.parse(s.getItem("orkcraft.remote")) }});
""")
    assert got["before"] is False and got["saved"] == {"ok": True, "line": "Ready: goals go through orkboard/inbox when your computer cannot be reached"}
    assert got["ready"] is True and got["settings"] == {"repo": "me/game", "token": True}, "the token is never handed back"
    assert got["calls"] == ["GET /repos/me/game"] and got["auth"] == "Bearer ghp_secret"
    assert got["kept"]["repo"] == "me/game" and got["kept"]["token"] == "ghp_secret"


def test_a_public_repository_is_refused_in_the_specs_words_and_the_token_is_not_kept():
    got = run("""
const s = new Store(), g = github({"GET /repos/me/game": reply(200, { private: false, full_name: "me/game", permissions: { push: true } })});
const r = makeRemote({ fetch: g.fetch, storage: s });
const saved = await r.save({ repo: "me/game", token: "ghp_x" });
out({ saved, ready: r.ready(), stored: s.getItem("orkcraft.remote") });
""")
    assert got["saved"] == {"ok": False, "line": "This repository is public: goals sent through it would be seen by everyone. Make it private, or use the phone at home."}
    assert got["ready"] is False and "ghp_x" not in (got["stored"] or "")


def test_a_token_that_cannot_write_a_missing_repository_and_a_refused_token_are_said_and_not_kept():
    got = run("""
const run = async (reply_) => { const s = new Store(), g = github({"GET /repos/me/game": reply_}); const r = makeRemote({ fetch: g.fetch, storage: s }); const saved = await r.save({ repo: "me/game", token: "t" }); return [saved.line, r.ready()]; };
out({
  readonly: await run(reply(200, { private: true, full_name: "me/game", permissions: { push: false, pull: true } })),
  missing: await run(reply(404, { message: "Not Found" })),
  refused: await run(reply(401, { message: "Bad credentials" })),
  offline: await (async () => { const r = makeRemote({ fetch: async () => { throw new TypeError("Failed to fetch"); }, storage: new Store() }); return (await r.save({ repo: "me/game", token: "t" })).line; })(),
  noRepo: (await makeRemote({ fetch: async () => reply(200, {}), storage: new Store() }).save({ repo: "nonsense", token: "t" })).line,
  noToken: (await makeRemote({ fetch: async () => reply(200, {}), storage: new Store() }).save({ repo: "me/game", token: "" })).line,
});
""")
    assert got["readonly"] == ["This token cannot write to the repository", False]
    assert got["missing"] == ["This repository was not found, or this token cannot see it", False]
    assert got["refused"] == ["The token was refused: give a new one in Settings", False]
    assert got["offline"] == "Could not reach GitHub: check the network and try again"
    assert got["noRepo"] == "Name the repository as owner/name" and got["noToken"] == "Paste the token"


def test_remove_forgets_the_token_at_once_and_unpairing_forgets_everything():
    got = run(f"""
const s = new Store(), g = github({{"GET /repos/me/game": reply(200, {REPO})}});
const r = makeRemote({{ fetch: g.fetch, storage: s }});
await r.save({{ repo: "me/game", token: "ghp_secret" }});
r.forget();
const afterForget = {{ ready: r.ready(), settings: r.settings(), stored: s.getItem("orkcraft.remote") }};
await r.save({{ repo: "me/game", token: "ghp_secret" }});
r.wipe();
out({{ afterForget, afterWipe: {{ ready: r.ready(), stored: s.getItem("orkcraft.remote"), keys: [...s.m.keys()] }} }});
""")
    assert got["afterForget"]["ready"] is False and got["afterForget"]["settings"] == {"repo": "me/game", "token": False}
    assert "ghp_secret" not in got["afterForget"]["stored"]
    assert got["afterWipe"] == {"ready": False, "stored": None, "keys": []}






