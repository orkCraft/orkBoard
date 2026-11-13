"""What the phone writes to the project's inbox (pwa/shell-remote-send.js, docs/specs/136 C.5–C.6, spec 137 C), run by node with a fake GitHub: a goal as `inbox/<device>/<id>.json` the host
reads back (`realm/remote_inbox.py clean`), its photos first, the branch made on the first goal from an empty tree's commit, a 409 tried again three times, a goal kept for the network and
sent when it comes back; an answer through the same writer, its file read back by `realm/remote_answers.py`. No network."""
from __future__ import annotations


from tests.test_phone_remote_js import REPO, run

SETUP = f"""
const s = new Store(), files = {{}}, state = {{ branch: false, conflicts: 0, network: true, status: 0 }};
let t = Date.UTC(2026, 10, 4, 14, 5);
const put = (init, calls) => {{
  const key = calls[calls.length - 1].key.replace(/^PUT \\/repos\\/me\\/game\\/contents\\//, "").replace(/\\?.*$/, ""), body = JSON.parse(init.body);
  if (!state.branch) return reply(404, {{ message: "Branch orkboard/inbox not found" }});
  if (state.conflicts > 0) {{ state.conflicts -= 1; return reply(409, {{ message: "is at x but expected y" }}); }}
  const path = decodeURIComponent(key);
  if (path in files) return reply(422, {{ message: 'Invalid request.\\n\\n"sha" wasn\\'t supplied.' }});
  files[path] = atob(body.content); return reply(201, {{ content: {{ path }} }});
}};
const calls = [];
const g = {{ calls, fetch: async (url, init = {{}}) => {{
  if (!state.network) throw new TypeError("Failed to fetch");
  const u = new URL(url), key = `${{init.method || "GET"}} ${{u.pathname}}`;
  calls.push({{ key, init, body: init.body ? JSON.parse(init.body) : null }});
  if (u.origin !== "https://api.github.com") throw new Error("a call to " + u.origin);
  if (state.status) return reply(state.status, {{ message: "x" }}, state.status === 403 ? {{ "x-ratelimit-remaining": "0", "x-ratelimit-reset": String(Math.floor(t / 1000) + 600) }} : {{}});
  if (key === "GET /repos/me/game") return reply(200, {REPO});
  if (key === "GET /repos/me/game/git/ref/heads/orkboard/inbox") return state.branch ? reply(200, {{ ref: "x" }}) : reply(404, {{ message: "Not Found" }});
  if (key === "POST /repos/me/game/git/commits") return reply(201, {{ sha: "c".repeat(40) }});
  if (key === "POST /repos/me/game/git/refs") {{ state.branch = true; return reply(201, {{ ref: "x" }}); }}
  if (key.startsWith("PUT /repos/me/game/contents/")) return put(init, calls);
  return reply(404, {{ message: "Not Found" }});
}} }};
const r = makeRemote({{ fetch: g.fetch, storage: s, now: () => t, sleep: async () => {{}}, device: () => ({{ id: "phone1" }}) }});
await r.save({{ repo: "me/game", token: "tok" }});
calls.length = 0;
const JPEG = "data:image/jpeg;base64," + btoa("jpeg-bytes");
"""


def test_a_goal_is_one_file_in_the_inbox_the_host_reads_back_with_its_photos_beside_it():
    got = run(SETUP + """
const sent = await r.sendGoal({ text: "Daily quests: who plays them?", party: "game", element: "ice", type: "feature", marks: ["part-a"], photos: [JPEG, "data:image/png;base64,AAAA", JPEG] });
out({ sent, paths: Object.keys(files), calls: calls.map((c) => c.key), gone: r.keep.outbox().length, waiting: r.view ? null : null,
      goal: JSON.parse(files[Object.keys(files).find((p) => p.endsWith(".json"))]), jpg: Object.entries(files).filter(([p]) => p.endsWith(".jpg")).map(([p, v]) => [p, v]) });
""")
    sent = got["sent"]
    assert sent["ok"] is True and "kept" not in sent and sent["photos"] == 2, "the png is not a JPEG: left out"
    gid = sent["id"]
    assert got["paths"][:2] == [f"inbox/phone1/{gid}.1.jpg", f"inbox/phone1/{gid}.2.jpg"] and got["paths"][-1] == f"inbox/phone1/{gid}.json", "the photos first, the goal last"
    assert got["jpg"][0][1] == "jpeg-bytes"
    goal = got["goal"]
    assert goal["v"] == 1 and goal["id"] == gid and goal["device"] == "phone1" and goal["text"] == "Daily quests: who plays them?"
    assert (goal["element"], goal["party"], goal["type"], goal["marks"]) == ("ice", "game", "feature", ["part-a"])
    assert goal["photos"] == [f"{gid}.1.jpg", f"{gid}.2.jpg"] and goal["at"].startswith("20") and goal["at"][-6] in "+-"
    assert "asks" not in goal
    # the first goal made the branch from an empty tree's commit (no history shared with the code), then added the files
    assert got["calls"][:4] == ["GET /repos/me/game/git/ref/heads/orkboard/inbox", "POST /repos/me/game/git/commits", "POST /repos/me/game/git/refs", "PUT /repos/me/game/contents/" + f"inbox/phone1/{gid}.1.jpg"]
    assert all(c.startswith("PUT") for c in got["calls"][3:]) and got["gone"] == 0


def test_without_a_network_the_goal_waits_in_the_outbox_and_goes_when_the_network_comes_back():
    got = run(SETUP + """
state.network = false;
const kept = await r.sendGoal({ text: "Sent on the train", photos: [JPEG] });
const waits = { outbox: r.keep.outbox().map((x) => [x.kind, x.text, x.photos.length]), none: Object.keys(files).length, view: null };
const early = await r.flush();
state.network = true;
const flushed = await r.flush();
out({ kept, waits, early, flushed, files: Object.keys(files).length, outbox: r.keep.outbox().length, sent: r.keep.sent().map((x) => x.text) });
""")
    assert got["kept"]["ok"] is True and got["kept"]["kept"] is True
    assert got["waits"] == {"outbox": [["goal", "Sent on the train", 1]], "none": 0, "view": None}
    assert got["early"] == {"sent": 0, "left": 1}, "still no network: it stays"
    assert got["flushed"] == {"sent": 1, "left": 0} and got["files"] == 2 and got["outbox"] == 0 and got["sent"] == ["Sent on the train"]


def test_a_limit_keeps_the_goal_a_refused_token_does_not_and_no_repository_is_the_hint_once():
    got = run(SETUP + """
state.status = 403;
const limited = await r.sendGoal({ text: "Waits for the limit" });
state.status = 401;
const refused = await r.sendGoal({ text: "Not kept" });
const left = r.keep.outbox().map((x) => x.text);
const bare = makeRemote({ fetch: g.fetch, storage: new Store() });
out({ limited, refused, left, hint: [bare.hint(), bare.hint()], none: await bare.sendGoal({ text: "x" }), blank: await r.sendGoal({ text: "   " }) });
""")
    assert got["limited"]["ok"] is True and got["limited"]["kept"] is True
    assert got["refused"] == {"ok": False, "error": "The token was refused: give a new one in Settings", "photos": 0}
    assert got["left"] == ["Waits for the limit"]
    assert got["hint"] == ["Set your repository in Settings to send goals while your computer is away", ""], "said once"
    assert got["none"]["ok"] is False and got["blank"]["ok"] is False

