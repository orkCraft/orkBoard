"""The tool now, and moving on (docs/specs/105 §2): the order, room, spent, the reserve, subscriptions only, paid only while it holds, pinned seats and parties
never moved, the runner's and the keeper's resolutions falling to the tool now, and `TOOL_MOVED` once a change."""
from __future__ import annotations

import datetime as dt
import json
import re
import time
from types import SimpleNamespace

import pytest

from orkboard import settings
from orkboard.core import bus as b, idea_keeper, idea_runner
from orkboard.gui.board_host import Orkboard
from orkboard.realm import tool_now
from orkboard.sources.limits import Limit

AT = float(int(time.time()))                                             # the quota's resets are read against the clock the host keeps
NOON = dt.datetime(2026, 10, 29, 12, 0).timestamp()          # a Thursday noon, for the words
H = 3600.0


def machine_of(*on: str, main: str = "", api: tuple[str, ...] = ()) -> settings.MachineSettings:
    m = settings.MachineSettings()
    for t in on:
        m.tools[t] = settings.ToolChoice(enabled=True, billing="api" if t in api else "subscription")
    m.main_tool = main
    return m


def left(tool: str, share: float, resets_in: float = 6 * H, window: str = "session") -> Limit:
    return Limit(tool, "", window, share, dt.datetime.fromtimestamp(AT + resets_in))


def test_the_main_tool_while_it_has_room():
    m = machine_of("claude", "codex")
    got = tool_now.now(m, [left("claude", 0.6), left("codex", 0.9)], AT)
    assert got == {"main": "claude", "now": "claude", "until": None, "moved_from": None}
    assert tool_now.now(m, [], AT)["now"] == "claude"               # nothing read: no limit holds
    assert tool_now.now(m, [left("claude", 0.06)], AT)["now"] == "claude"         # above NEARLY (5 %) still has room


def test_a_spent_main_tool_moves_on_to_the_next_with_room_until_it_is_back():
    m = machine_of("claude", "codex")
    got = tool_now.now(m, [left("claude", 0.01, 5 * H), left("codex", 0.8)], AT)
    assert got["main"] == "claude" and got["now"] == "codex" and got["moved_from"] == "claude" and got["until"] == AT + 5 * H
    assert tool_now.now(m, [left("claude", 0.05, 5 * H), left("codex", 0.8)], AT)["now"] == "codex"      # nearly spent, as the runner's hold reads it
    # the latest of its windows is when it is back
    two = [left("claude", 0.0, 2 * H), left("claude", 0.02, 30 * H, "weekly"), left("codex", 0.8)]
    assert tool_now.now(m, two, AT)["until"] == AT + 30 * H


def test_a_tool_billed_by_its_api_is_picked_only_while_a_yes_holds():
    m = machine_of("claude", "codex", api=("codex",))
    out = [left("claude", 0.0, 4 * H)]
    assert tool_now.now(m, out, AT)["now"] is None
    assert tool_now.now(m, out, AT, paid_until=AT - 1)["now"] is None            # its reset has come: it ended
    got = tool_now.now(m, out, AT, paid_until=AT + 4 * H)
    assert got["now"] == "codex" and got["moved_from"] == "claude" and got["until"] == AT + 4 * H
    # a subscription with room is always the first
    two = machine_of("claude", "agy", "codex", api=("agy",))
    assert tool_now.now(two, [left("claude", 0.0), left("codex", 0.5)], AT, paid_until=AT + H)["now"] == "codex"


# -- who follows it ----------------------------------------------------------------------------------------------

def _runner(tmp_path, follow, party):
    return idea_runner.IdeaRunner(tmp_path, tmp_path / ".orkcraft", SimpleNamespace(ideas={}), None, events=False,
                                  party_of=lambda slug: party, follow=follow)


def test_the_runner_falls_to_the_tool_now_but_never_moves_a_pinned_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "main_tool", lambda machine=None: "claude")
    task = {"id": "k1", "kind": "code"}
    now = {"tool": "codex"}
    runner = _runner(tmp_path, lambda **_: now["tool"], {})
    assert runner.tool_of("demo", task) == "codex" and runner.pinned_tool("demo", task) == ""
    now["tool"] = None
    assert runner.tool_of("demo", task) == "claude"                                    # every tool out: it holds on the Main tool
    now["tool"] = "codex"
    assert _runner(tmp_path, lambda **_: "codex", {"tool": "agy"}).tool_of("demo", task) == "agy"                      # the party's own
    seat = _runner(tmp_path, lambda **_: "codex", {"tool": "agy", "tools": {"grunt": "claude"}})
    assert seat.tool_of("demo", task) == "claude" and seat.pinned_tool("demo", task) == "claude"                   # the seat's own wins
    assert _runner(tmp_path, None, {}).tool_of("demo", task) == "claude"                                           # no host to say: the Main tool

    def broken(**_):
        raise RuntimeError("no read")
    assert _runner(tmp_path, broken, {}).tool_of("demo", task) == "claude"


def test_a_plan_the_person_started_may_spend_the_reserve_one_the_board_started_moves_at_it(tmp_path, monkeypatch):
    """Decisions §177.10: the reserve is the person's, so only the work the Board started by itself counts it as out; the keeper's steps never do."""
    import json
    monkeypatch.setattr(settings, "main_tool", lambda machine=None: "claude")
    asked = []

    def follow(reserve=True):
        asked.append(reserve)
        return "codex" if reserve else "claude"
    runner, task = _runner(tmp_path, follow, {}), {"id": "k1", "kind": "code"}
    for slug, passed in (("by-hand", "person"), ("by-itself", "auto")):
        d = runner._dir(slug)
        d.mkdir(parents=True, exist_ok=True)
        (d / "plan.json").write_text(json.dumps({"idea": slug, "tasks": [task], "passed_by": passed}))
    assert runner.tool_of("by-hand", task) == "claude" and runner.tool_of("by-itself", task) == "codex"
    assert asked == [False, True]
    asked.clear()
    assert idea_keeper.IdeaKeeper(tmp_path, tmp_path / ".orkcraft", lambda: tmp_path / "wiki", lambda: {}, follow=follow).tool_now() == "claude" and asked == [False]


def test_the_runner_starts_a_task_on_the_tool_now_and_holds_a_pinned_one(tmp_path, monkeypatch):
    """Resolved where the task starts: the tool the hold is read on is the one it resolves to; a pinned tool's hold says what it waits for."""
    monkeypatch.setattr(settings, "main_tool", lambda machine=None: "claude")
    launched, spent = [], [left("claude", 0.0, 3 * H)]
    monkeypatch.setattr(idea_runner.IdeaRunner, "_launch", lambda self, slug, t: launched.append((slug, t["id"], self.tool_of(slug, t))))
    monkeypatch.setattr(idea_runner.IdeaRunner, "room", lambda self, *a, **k: True)
    party = {"tools": {"grunt": "claude"}}
    runner = idea_runner.IdeaRunner(tmp_path, tmp_path / ".orkcraft", SimpleNamespace(ideas={}), None, events=False, limits=lambda: spent,
                                    party_of=lambda slug: party if slug == "pinned" else {}, follow=lambda **_: "codex")
    for slug in ("moving", "pinned"):
        d = tmp_path / ".orkcraft" / "ideas" / slug
        d.mkdir(parents=True)
        (d / "plan.json").write_text(json.dumps({"idea": slug, "passed_at": "x", "todos": [], "tasks": [
            {"id": "k1", "title": "t", "brief": "b", "tier": "laborer", "kind": "code", "after": [], "state": "ready", "branch": "", "commit": "",
             "session": "", "cost": None, "tokens": None, "started": "", "finished": "", "error": "", "note": ""}]}))
        (d / "state.json").write_text(json.dumps({"state": "working"}))
        runner._active.append(slug)
    runner.tick()
    assert launched == [("moving", "k1", "codex")]
    held = json.loads((tmp_path / ".orkcraft" / "ideas" / "pinned" / "plan.json").read_text())["tasks"][0]
    assert held["state"] == "held" and held["held_why"].startswith("Waits for Claude Code's limit until ")
    assert "set for it on purpose" in held["held_why"]


# -- said once ---------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.machine = machine_of("claude", "codex")
    h.limits.rows = [left("claude", 0.9, 6 * H), left("codex", 0.9, 6 * H)]
    h.moves = []
    h.project.bus.subscribe(b.TOOL_MOVED, lambda e: h.moves.append(dict(e.data)))
    return h


def _tick(host, at):
    host.ideas.mana_tick(at)


def test_a_move_is_published_once_and_so_is_the_way_back(host):
    ideas = host.ideas
    _tick(host, AT)
    assert host.moves == [] and ideas.mana()["moved"] is None and ideas.mana()["now"] == "claude"
    host.limits.rows = [left("claude", 0.0, 5 * H), left("codex", 0.9)]
    _tick(host, AT)
    _tick(host, AT + 60)                                                               # the next tick says nothing more
    assert host.moves == [{"from": "claude", "to": "codex", "until": pytest.approx(AT + 5 * H)}]
    mana = host.snapshot()["mana"]
    assert mana["main"] == "claude" and mana["now"] == "codex" and mana["until"] == dt.datetime.fromtimestamp(AT + 5 * H).isoformat(timespec="minutes")
    assert mana["moved"]["from"] == "claude" and mana["moved"]["to"] == "codex"
    assert re.fullmatch(r"Claude Code is out until (\w{3} )?\d\d:\d\d: the work goes on with Codex\.", mana["moved"]["line"])
    json.dumps(mana)
    host.limits.rows = [left("claude", 0.8), left("codex", 0.9)]
    _tick(host, AT + 6 * H)
    _tick(host, AT + 6 * H + 60)
    assert host.moves[1:] == [{"from": "codex", "to": "claude", "until": None}] and len(host.moves) == 2
    back = host.snapshot()["mana"]
    assert back["now"] == "claude" and back["until"] is None and back["moved"]["line"] == "Claude Code is back: the work goes on with it."

