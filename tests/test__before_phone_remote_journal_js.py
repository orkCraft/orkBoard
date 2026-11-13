"""The phone's journal read (pwa/shell-remote-journal.js, docs/specs/136 C.3–C.4), run by node with a fake `fetch`: `status.json` of orkboard/journal asked with its ETag (a 304 changes nothing),
only while the computer is not reached and the app is seen, stopped by GitHub's limit till it lapses; *As of* from the journal's `written`; the goals this phone sent that the journal has not
named lying face down, one taken with an error saying its words, one laid on the Board no longer waited for."""
from __future__ import annotations

from tests.test_phone_remote_js import REPO, run

JOURNAL = """{ v: 1, written: "2026-11-04T14:02:11", parties: [
  { slug: "tech", title: "Tech", goals: [{ slug: "sign-in", title: "Sign-in", state: "working", phase: "work", needs_you: true, error: "" },
                                       { slug: "cache", title: "Cache", state: "failed", phase: "work", needs_you: false, error: "tests failed" }] } ],
  failed: [{ slug: "cache", title: "Cache", error: "tests failed" }], taken: [] }"""

SETUP = f"""
const s = new Store(), journal = {JOURNAL};
let etag = 'W/"1"', served = journal, status = 200;
const g = github({{
  "GET /repos/me/game": reply(200, {REPO}),
  "GET /repos/me/game/contents/status.json": (init) => status !== 200 ? reply(status, {{ message: "x" }}, status === 403 ? {{ "x-ratelimit-remaining": "0", "x-ratelimit-reset": String(Math.floor(t / 1000) + 600) }} : {{}})
    : init.headers["If-None-Match"] === etag ? reply(304, "", {{ etag }}) : reply(200, served, {{ etag, "content-type": "application/vnd.github.raw+json" }}),
}});
let t = Date.UTC(2026, 10, 4, 14, 5);
const r = makeRemote({{ fetch: g.fetch, storage: s, now: () => t }});
await r.save({{ repo: "me/game", token: "tok" }});
g.calls.length = 0;
"""


def test_the_journal_is_read_with_its_etag_and_a_304_changes_nothing():
    got = run(SETUP + """
const first = await r.poll(), view = r.view();
const second = await r.poll();
out({ first, second, calls: g.calls.map((c) => [c.key, c.init.headers["If-None-Match"] || null, c.init.headers.Accept]), asOf: r.asOf(), written: r.journal().written,
      parties: view.parties.map((p) => [p.title, p.goals.map((x) => [x.title, x.state, x.needs_you])]), failed: view.failed.map((f) => f.title), kept: !!JSON.parse(s.getItem("orkcraft.remote.journal")).etag });
""")
    assert got["first"] == {"read": True, "changed": True} and got["second"] == {"read": True, "changed": False}
    path = "GET /repos/me/game/contents/status.json?ref=orkboard%2Fjournal"
    assert [c[:2] for c in got["calls"]] == [[path, None], [path, 'W/"1"']], "the second read carries the first one's ETag"
    assert got["calls"][0][2] == "application/vnd.github.raw+json"
    assert got["asOf"] == "As of 14:02" and got["written"] == "14:02", "the journal's own time, not the phone's"
    assert got["parties"] == [["Tech", [["Sign-in", "working", True], ["Cache", "failed", False]]]] and got["failed"] == ["Cache"] and got["kept"] is True


def test_a_journal_that_is_not_there_yet_is_nothing_to_show():
    got = run(SETUP + """
status = 404;
const first = await r.poll();
out({ first, view: r.view(), line: r.line() });
""")
    assert got["first"] == {"read": True, "changed": False} and got["view"] is None and got["line"] == ""


def test_the_limit_stops_the_reads_till_it_lapses_and_a_refused_token_is_said():
    got = run(SETUP + """
status = 403;
const hit = await r.poll(), line = r.line(), calls = g.calls.length;
const held = await r.poll();                              // still waiting: no call at all
const callsAfter = g.calls.length;
t += 601_000; status = 200;
const later = await r.poll();
status = 401;
const refused = await r.poll();
out({ hit, line, calls, held, callsAfter, later, refused, refusedLine: r.line() });
""")
    assert got["hit"] == {"read": False, "why": "limit"} and got["line"].startswith("GitHub asks us to wait till ")
    assert got["held"] == {"read": False, "why": "limit"} and got["callsAfter"] == got["calls"], "no call while GitHub asks to wait"
    assert got["later"] == {"read": True, "changed": True}
    assert got["refused"] == {"read": False, "why": "token"} and got["refusedLine"] == "The token was refused: give a new one in Settings"


def test_it_reads_only_while_the_computer_is_not_reached_and_the_app_is_seen():
    got = run(SETUP + """
let reached = true, seen = true;
r.watch({ reached: () => reached, seen: () => seen, every: 15 });
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));
await wait(80); const whileReached = g.calls.length;
reached = false; seen = false;
await wait(80); const whileHidden = g.calls.length;
seen = true;
await wait(80); const whileSeen = g.calls.length;
r.stopWatching();
await wait(60); const after = g.calls.length;
const kicked = await r.kick();
out({ whileReached, whileHidden, whileSeen: whileSeen > 0, after: after - whileSeen <= 1, kicked });
""")
    assert got["whileReached"] == 0, "on the same network the live Board is the truth"
    assert got["whileHidden"] == 0, "never in the background"
    assert got["whileSeen"] is True and got["after"] is True
    assert got["kicked"] == {"read": False, "why": "not now"}


def test_the_goals_this_phone_sent_lie_face_down_till_the_journal_names_them():
    got = run(SETUP + """
s.setItem("orkcraft.remote.sent", JSON.stringify([
  { id: "A1", kind: "goal", text: "Daily quests, please", at: t },
  { id: "B2", kind: "goal", text: "A goal the computer could not lay", at: t },
  { id: "C3", kind: "goal", text: "A goal that is on the Board now", at: t },
  { id: "D4", kind: "answer", text: "", at: t }]));
s.setItem("orkcraft.remote.outbox", JSON.stringify([{ key: "E5", id: "E5", kind: "goal", text: "Waits for a network", at: t }]));
served = { ...journal, taken: [{ id: "B2", by: "home", at: "x", slug: "", error: "Could not read this goal: it is empty" }, { id: "C3", by: "home", at: "x", slug: "daily", error: "" },
                               { id: "D4", by: "home", at: "x", slug: "", error: "That card is gone, or answered already" }] };
const before = r.keep.sent().length;
await r.poll();
const v = r.view();
out({ before, waiting: v.waiting.map((w) => [w.id, w.state, w.text, w.error]), refused: v.refused, sentLeft: r.keep.sent().map((x) => x.id) });
""")
    assert got["waiting"] == [["E5", "network", "Waits for a network", ""], ["A1", "waiting", "Daily quests, please", ""],
                              ["B2", "error", "A goal the computer could not lay", "Could not read this goal: it is empty"]]
    assert got["refused"] == [{"id": "D4", "error": "That card is gone, or answered already"}]
    assert got["sentLeft"] == ["A1", "B2", "D4"], "the goal laid on the Board is no longer waited for"
