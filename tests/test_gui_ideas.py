"""The board's host commands (spec 29a §6), the phone's allowlist and its compact snapshot, on Orkboard's host
(gui/board_host.py)."""
from __future__ import annotations

import json
import sys
import threading
import time
import types
from pathlib import Path

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import idea_secrets, ideas, jobs, roles

BOARD_COMMANDS = {"ideas.board", "ideas.page", "ideas.add", "ideas.say", "ideas.plan", "ideas.start", "ideas.move",
                  "ideas.edit", "ideas.track_add", "ideas.track_set", "ideas.track_drop", "ideas.todo", "ideas.drop", "ideas.stop",
                  "ideas.review_list", "ideas.diff", "ideas.merge", "ideas.back", "ideas.regate", "ideas.drop_task",
                  "ideas.stop_task", "ideas.agents", "ideas.task", "ideas.into", "ideas.log", "ideas.logs", "ideas.goal_save",
                  "ideas.goal", "ideas.read_now", "ideas.roles", "ideas.role_save", "ideas.role_add", "ideas.role_drop",
                  "ideas.kind_set", "ideas.gate", "ideas.gate_merge", "ideas.to_main_plan", "ideas.to_main", "ideas.today", "ideas.pick",
                  "ideas.revise", "ideas.revise_answer",
                  "ideas.judge", "ideas.pitch_send", "ideas.pitch_again", "ideas.pitch_pass",
                  "ideas.release_out", "ideas.release_candidates", "ideas.shown", "ideas.party_for", "ideas.kind_for", "ideas.proposals",
                  "ideas.tools", "ideas.party_sizes", "ideas.party_presets", "ideas.seen",
                  "ideas.route_set", "ideas.talk", "ideas.route_later", "ideas.route_hold", "ideas.route_start",
                  "ideas.talk_answer", "ideas.cause_answer", "ideas.confirm", "ideas.fork_answer", "ideas.stage", "ideas.stage_set", "ideas.project_ask", "ideas.project_answer", "ideas.project_facts", "ideas.project_fact_set", "ideas.project_kind_set", "ideas.talk_read", "ideas.loop", "ideas.loop_set", "ideas.loop_propose", "ideas.art_map", "ideas.release_map", "ideas.way_map", "ideas.screens", "ideas.pain_pin", "ideas.tree", "ideas.tree_set", "ideas.tree_attach", "ideas.tree_propose", "ideas.paid"}   # spec 105 §3: going on paid, … … the project's questions (spec 99 §8), the project's stage (spec 99 §1.2), the decision and the forks (spec 99 §6, §7), talk's two (spec 99 §5), the route's four (spec 99 §4), spec 91's two, spec 83's one, spec 81's two, spec 75's one, and spec 49's three, spec 51's one, spec 62's two, spec 65's four, spec 68's three, spec 70's one



@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _wait(host, slug):
    for _ in range(300):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _add(host, text, **more):
    """An idea under a goal (spec 35 §3: no idea without one, never General), kept raw (held) unless asked (spec 83: the night is only for Low work, on the person's word)."""
    root = host.ideas.root()
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "First goal")
    return host.command("ideas.add", {"text": text, "track": goal, "hold": True, **more})


def _plan(host, slug, todos=()):
    data = {"idea": slug, "made_at": "2026-10-17T09:00:00", "passed_at": None,
            "estimate": {"tasks": 1, "usd_low": 0.15, "usd_high": 0.45},
            "todos": list(todos),
            "tasks": [{"id": "k1", "title": "Do it", "brief": "b", "tier": "warrior", "after": [], "state": "ready",
                       "branch": "", "commit": "", "session": "", "cost": None, "tokens": None, "started": "",
                       "finished": "", "error": "", "note": ""}]}
    ideas.save_plan(host.ideas.state_dir, slug, data)
    ideas.save_state(host.ideas.state_dir, slug, state="plan")




def test_drop_an_idea_and_read_the_board_and_its_page(host):
    rev = host.snapshot()["ideas_rev"]
    slug = _add(host, "Dark mode\nfor the night")["slug"]
    board = host.command("ideas.board")
    json.dumps(board)
    assert [t["slug"] for t in board["tracks"]] == ["first-goal"] and board["tracks"][0]["count"] == 1
    (i,) = board["ideas"]
    assert i["slug"] == slug and i["state"] == "raw" and i["thesis"] == "Dark mode" and i["track"] == "first-goal"
    assert i["progress"] == {"done": 0, "total": 0} and i["updated"]
    assert set(i) == {"slug", "title", "short", "track", "order", "state", "size", "thesis", "asks", "progress", "updated",
                      "priority",                 # spec 34 §4: ideas gain a priority
                      "queue", "held_until", "risk", "risk_triggers", "depends_on", "waits_on", "start_at",
                      "in_needs_you",             # spec 35 §12
                      "night_by",                 # spec 44 §4: who put it off to the night
                      "place", "asks_you", "waits_as", "seen",      # spec 98 §2: where it lies in the window (realm/goal_place.py)
                      "levels"}                   # spec 132 C.3: the levels that hold something open of the goal
    assert i["priority"] == "normal" and board["tracks"][0]["priority"] == "normal" and board["tracks"][0]["state"] == "raw"
    assert board["needs_you"] == [] and board["rev"] > rev      # spec 35 §10: `today` became `needs_you`, the batch went
    page = host.command("ideas.page", {"slug": slug})
    assert [s["name"] for s in page["sections"]] == list(ideas.SECTIONS)
    assert page["sections"][0] == {"name": "Gist", "thesis": "Dark mode", "text": "Dark mode\nfor the night"}
    assert page["talk"][0]["who"] == "you" and page["plan"] is None and page["busy"] is False
    assert (host.ideas.root() / "pages/ideas" / f"{slug}.md").exists()   # spec 35 §13: in the Board's own tree
    with pytest.raises(CommandError, match="gone"):
        host.command("ideas.page", {"slug": "nope"})
    with pytest.raises(CommandError, match="text is missing"):
        _add(host, "  ")




def test_say_and_plan_run_the_keeper_in_the_background(host, monkeypatch):
    calls = []

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):   # spec 35 §0's effort, budget
        calls.append({"harness": harness, "model": model, "resume": resume})
        if "turn it into" in prompt:
            return json.dumps({"tasks": [{"id": "a", "title": "T", "brief": "B", "tier": "laborer"}]}), 0.1, 10, "s"
        return json.dumps({"reply": "ok", "sections": {"Why": "because"}, "questions": []}), 0.1, 10, "sess-9"

    monkeypatch.setattr(jobs, "run_read", run_read)
    host.command("ideas.board_set", {"autostart": False})          # spec 35 §5: off, the plan waits for the person
    slug = _add(host, "x")["slug"]
    assert host.command("ideas.say", {"slug": slug, "text": "why?", "section": "Why"}) == {"ok": True}
    _wait(host, slug)
    assert calls[0]["harness"] == "claude" and calls[0]["resume"] == ""
    assert ideas.state(host.ideas.state_dir, slug)["session"] == ""      # spec 35 §0: no session kept …
    host.command("ideas.say", {"slug": slug, "text": "and?"})
    _wait(host, slug)
    assert calls[1]["resume"] == ""                                     # … and none resumed
    host.command("ideas.plan", {"slug": slug})
    _wait(host, slug)
    page = host.command("ideas.page", {"slug": slug})
    assert page["state"] == "plan" and page["plan"]["tasks"][0]["tier"] == "laborer"
    needs = host.command("ideas.board")["needs_you"]
    assert [{k: n[k] for k in ("idea", "kind", "title", "text")} for n in needs] == [
        {"idea": slug, "kind": "plan", "title": "x", "text": "Plan ready · 1 tasks"}]
    assert host.snapshot()["needs_you"] == 1






def test_start_passes_the_plan_to_the_runner_and_stop_all_reaches_it(host, monkeypatch):
    seen = []

    class FakeRunner:
        def __init__(self, repo_root, state_dir, settings, bus, **kw):
            seen.append(("made", settings.ideas["merge_into"]))
            self.bus = bus

        def start(self, slug):
            seen.append(("start", slug))

        def stop(self, slug):
            seen.append(("stop", slug))

        def tick(self):
            seen.append(("tick",))

        def stop_all(self):
            seen.append(("stop_all",))

    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=FakeRunner))
    slug = _add(host, "x")["slug"]
    _plan(host, slug)
    host.command("ideas.start", {"slug": slug})
    assert seen[:2] == [("made", "dev"), ("start", slug)]
    assert ideas.plan(host.ideas.state_dir, slug)["passed_at"]
    assert host.command("ideas.page", {"slug": slug})["state"] == "working"
    host.ideas.tick(1000.0)
    assert ("tick",) in seen
    host.command("ideas.stop", {"slug": slug})
    host.command("halt")
    assert ("stop", slug) in seen and ("stop_all",) in seen


def test_a_secret_todo_is_stored_and_the_plan_says_stored(host):
    slug = _add(host, "x")["slug"]
    _plan(host, slug, [
        {"id": "t1", "title": "API_KEY", "kind": "secret", "why": "w", "choices": [], "steps": [], "for": ["k1"],
         "done": False, "value": None},
        {"id": "t2", "title": "Which", "kind": "choice", "why": "w", "choices": ["a", "b"], "steps": [], "for": [],
         "done": False, "value": None}])
    assert [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "todo"] == []      # before the work starts a to-do is a line of the plan (spec 87 §4)
    shown = host.command("ideas.page", {"slug": slug})["plan"]
    assert shown["todo_lines"] == ["Before Do it: API_KEY"] and [t["id"] for t in shown["todos"]] == ["t1", "t2"]
    ideas.save_state(host.ideas.state_dir, slug, state="working")                                   # now k1 cannot start without it: the stop is given (spec 35 §10)
    today = [n["todo"] for n in host.command("ideas.board")["needs_you"] if n["kind"] == "todo"]
    assert [t["id"] for t in today] == ["t1"] and "value" not in today[0]
    with pytest.raises(CommandError, match="needs its value"):
        host.command("ideas.todo", {"idea": slug, "id": "t1", "done": True})
    host.command("ideas.todo", {"idea": slug, "id": "t1", "done": True, "value": "sk-secret"})
    plan_text = (host.ideas.state_dir / "ideas" / slug / "plan.json").read_text()
    assert "sk-secret" not in plan_text and json.loads(plan_text)["todos"][0]["value"] == "stored"
    assert idea_secrets.get(host.ideas.state_dir, slug, "t1") == "sk-secret"
    assert json.loads(plan_text)["tasks"][0]["state"] == "ready"
    with pytest.raises(CommandError, match="choices"):
        host.command("ideas.todo", {"idea": slug, "id": "t2", "done": True, "value": "c"})
    host.command("ideas.todo", {"idea": slug, "id": "t2", "done": True, "value": "b"})
    assert [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "todo"] == []
    host.command("ideas.drop", {"slug": slug})
    assert idea_secrets.get(host.ideas.state_dir, slug, "t1") is None










# -- spec 33: Review, Agents, the top bar's limits ---------------------------------------------------------

from orkboard.sources.limits import Limit
import datetime as dt


def _review(host, slug="r", tests=None, state="review", **more):
    """An idea with one task in `state`, as the runner leaves it."""
    ideas.add_idea(host.ideas.root(), "A review idea", "general", host.ideas.state_dir)
    slug = ideas.ideas(host.ideas.root())[-1]["slug"]
    _plan(host, slug)
    ideas.edit_plan(host.ideas.state_dir, slug, lambda p: p["tasks"][0].update(
        state=state, branch=f"idea/{slug}/k1", round=2, finished="2026-10-17T10:00:00", cost=0.42,
        tests=tests or {"passed": 20, "failed": 0, "failing": [], "tail": "20 passed", "green": True},
        diff={"files": 14, "added": 320, "removed": 41}, **more))
    return slug


def test_review_list_has_the_spec_shape_and_the_phones_may_call_it(host):
    empty = host.command("ideas.review_list")
    assert {k: empty[k] for k in ("into", "push", "results")} == {"into": "dev", "push": False, "results": []}
    assert "dev" in empty["branches"]                       # the branch it merges into is always offered
    slug = _review(host)
    got = host.command("ideas.review_list")
    json.dumps(got)
    (r,) = got["results"]
    assert set(r) == {"idea", "idea_title", "task", "title", "round", "tests", "diff", "cost", "conflict", "finished",
                      "work", "rework", "estimate", "over", "look", "shot"}       # spec 36 §4; spec 84: why it waits; spec 85: its picture
    assert r["idea"] == slug and r["task"] == "k1" and r["round"] == 2 and r["diff"]["files"] == 14
    assert BoardPhone.allowed(host, "ideas.merge", {"slug": slug, "task": "k1"})






def test_the_limits_are_the_smallest_remaining_of_each_installed_tools_rows(host, monkeypatch):
    soon = dt.datetime(2026, 10, 17, 18, 0)
    rows = [Limit("claude", "", "session", 0.62, soon), Limit("claude", "", "weekly", 0.9, None),
            Limit("agy", "Pro", "daily", 0.4, soon), Limit("agy", "Flash", "daily", 0.7, soon),
            Limit("codex", "", "", None, None, "not installed"), Limit("limits", "—", "—", None, None, "off")]
    monkeypatch.setattr(host, "limits", lambda: rows)
    got = host.snapshot()["limits"]
    assert [x["provider"] for x in got] == ["claude", "agy"]
    claude = got[0]
    assert claude["name"] == "Claude" and claude["left"] == 0.62
    assert claude["rows"][0] == {"window": "5h", "left": 0.62, "reset": "2026-10-17T18:00"}
    assert claude["rows"][1]["window"] == "week" and got[1]["left"] == 0.4
    assert BoardPhone.phone_snapshot(host)["limits"][0]["left"] == 0.62










def test_the_answers_at_review_reach_the_runner_and_its_refusals_are_plain_words(host, monkeypatch):
    seen = []

    class FakeRunner:
        def __init__(self, *a, **k):
            pass

        def merge(self, slug, tid, device=""):
            seen.append(("merge", slug, tid))
            return "abc123"

        def back(self, slug, tid, why, device="", suggested=False):
            seen.append(("back", slug, tid, why) + (("suggested",) if suggested else ()))

        def regate(self, slug, tid, install=False, device=""):
            seen.append(("regate", slug, tid, install, device))

        def drop_task(self, slug, tid, device=""):
            seen.append(("drop", slug, tid))

        def stop_task(self, slug, tid, device=""):
            seen.append(("stop", slug, tid))

        def log(self, slug, tid):
            return "the log"

    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=FakeRunner))
    slug = _review(host)
    a = {"slug": slug, "task": "k1"}
    assert host.command("ideas.merge", a) == {"ok": True, "commit": "abc123"}
    assert host.command("ideas.back", {**a, "why": "rename it"}) == {"ok": True}
    assert host.command("ideas.drop_task", a) == {"ok": True} and host.command("ideas.stop_task", a) == {"ok": True}
    assert seen == [("merge", slug, "k1"), ("back", slug, "k1", "rename it"), ("drop", slug, "k1"),
                    ("stop", slug, "k1")]
    seen.clear()                                                                       # spec 107 §1.3, §1.4
    assert host.command("ideas.back", {**a, "why": "Fix the failing tests", "suggested": True}) == {"ok": True}
    assert host.command("ideas.regate", {**a, "install": True}) == {"ok": True} and host.command("ideas.regate", a) == {"ok": True}
    assert seen == [("back", slug, "k1", "Fix the failing tests", "suggested"), ("regate", slug, "k1", True, "desktop"), ("regate", slug, "k1", False, "desktop")]
    with pytest.raises(CommandError, match="suggested is true or false"):
        host.command("ideas.back", {**a, "why": "x", "suggested": "yes"})
    with pytest.raises(CommandError, match="install is true or false"):
        host.command("ideas.regate", {**a, "install": 1})
    assert host.command("ideas.task", a)["log"] == "the log"
    with pytest.raises(CommandError, match="why is missing"):
        host.command("ideas.back", a)

    class Refusing(FakeRunner):
        def merge(self, slug, tid, device=""):
            raise type("RunnerError", (Exception,), {})("Its tests are red: send it back")

    host.ideas._runner = Refusing()
    with pytest.raises(CommandError, match="tests are red"):
        host.command("ideas.merge", a)




# -- spec 33 §9: every action logged ----------------------------------------------------------------------------


from orkboard.realm import event_log


def _events(host, *names):
    return [r for r in event_log.read(Path(host.town.repo_root)) if not names or r["event"] in names]












# -- spec 36 §4, §7: Review's cost against the plan, `dear`, `ideas.spend`, the roles' week and types ----------------



def test_merge_sends_dear_only_when_it_is_ticked(host, monkeypatch):
    seen = []

    class FakeRunner:
        def __init__(self, *a, **k):
            pass

        def merge(self, slug, tid, device="", **more):
            seen.append(more)
            return "abc"

    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=FakeRunner))
    slug = _review(host)
    host.command("ideas.merge", {"slug": slug, "task": "k1"})
    host.command("ideas.merge", {"slug": slug, "task": "k1", "dear": True})
    assert seen == [{}, {"dear": True}]
    with pytest.raises(CommandError, match="true or false"):
        host.command("ideas.merge", {"slug": slug, "task": "k1", "dear": "yes"})










# -- spec 49 A: the reserve, each role's tool, where a press was -------------------------------------------------------













# -- spec 50 A: a goal's element and flag, and no acceptance by itself -----------------------------------------------------------









# -- spec 52 A: New goal by its type, its asks, who joins; a plan's missing ---------------------------------------------------

from orkboard.realm import goal_team, library     # noqa: E402


def _party(host, team=(), leader="taskmaster", title="Ship"):
    """A party with its leader and team as Edit the party keeps them (no reading: no model)."""
    root, state = host.ideas.root(), host.ideas.state_dir
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal")
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


def _new(host, party, text="A goal", **more):
    """A goal added at the press of Add the goal; its draft is not made (no model)."""
    host.ideas.keeper.draft = lambda *a, **k: None
    return host.command("ideas.add", {"text": text, "track": party, **more})


def _says(host, command, args):
    with pytest.raises(CommandError) as err:
        host.command(command, args)
    return str(err.value)






def test_a_free_seat_joins_the_party_before_the_goal_is_added(host):
    ship = _party(host, [], leader="product-manager")                                      # one builder's seat (spec 87 §5), free
    got = _new(host, ship, "A screen", type="screen", join={"add": "ui-kit"})
    assert got["joined"] == {"add": "ui-kit", "out": ""}
    assert goal_team.team_of(host.ideas.root(), ship) == ["ui-kit"] and roles.role(host.ideas.state_dir, "ui-kit") is not None
    (saved,) = _events(host, "goal_saved")
    assert (saved["goal"], saved["joined"], saved["out"], saved["via"], saved["team"], saved["new"]) == (ship, "ui-kit", "", "type", ["ui-kit"], False)
    (added,) = _events(host, "idea_added")
    assert (added["type"], added["asks"], added["refs"], added["joined"], added["out"]) == ("screen", 0, 0, "ui-kit", "")
    assert _says(host, "ideas.add", {"text": "x", "track": ship, "type": "screen", "join": {"add": "ui-kit"}}) == "Design system designer is not what this goal misses"     # it has joined
    assert _says(host, "ideas.add", {"text": "x", "track": ship, "type": "experiment", "join": {"add": "ui-kit"}}) == "Design system designer is not what this goal misses"
    assert _says(host, "ideas.add", {"text": "x", "track": ship, "type": "pain", "join": {"add": "artist"}}) == "Artist is not what this goal misses"
    assert _says(host, "ideas.add", {"text": "x", "track": ship, "join": {"add": "experimenter"}}) == "Experimenter is not what this goal misses"












class _Runner:
    started: list = []

    def __init__(self, *a, **k):
        pass

    def start(self, slug):
        _Runner.started.append(slug)

    def tick(self):
        pass

    def stop_all(self):
        pass


def _missing_plan(host, slug, tasks, missing):
    ideas.save_plan(host.ideas.state_dir, slug, {"idea": slug, "made_at": "2026-10-22T09:00:00", "passed_at": None, "todos": [],
                                                 "estimate": {"tasks": len(tasks)}, "tasks": tasks, "missing": missing})
    ideas.save_state(host.ideas.state_dir, slug, state="plan")


def test_add_and_start_joins_the_party_then_gives_the_tasks_not_started_their_new_member(host, monkeypatch):
    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=_Runner))
    ship = _party(host, ["reviewer"], leader="product-designer")
    slug = _new(host, ship, "A logo")["slug"]
    task = {"title": "t", "brief": "b", "tier": "warrior", "after": []}
    _missing_plan(host, slug, [{**task, "id": "k1", "kind": "art", "role": "grunt", "state": "ready"},
                               {**task, "id": "k2", "kind": "art", "role": "grunt", "state": "review"},
                               {**task, "id": "k3", "kind": "code", "role": "grunt", "state": "waiting"}],
                  [{"kind": "art", "agent": "artist"}])
    (row,) = [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "plan"]
    assert row["missing"] == [{"kind": "art", "words": "pixel art", "agent": "artist", "name": "Artist", "band": "build", "free": True}]
    assert host.command("ideas.page", {"slug": slug})["plan"]["missing"] == row["missing"]                # the drawer's plan says the same
    assert _says(host, "ideas.start", {"slug": slug, "join": {"add": "ui-kit"}}) == "Design system designer is not what this plan misses"
    host.command("ideas.start", {"slug": slug, "join": {"add": "artist"}, "via": "hand"})
    assert goal_team.team_of(host.ideas.root(), ship) == ["reviewer", "artist"]
    plan = ideas.plan(host.ideas.state_dir, slug)
    assert [t["role"] for t in plan["tasks"]] == ["artist", "grunt", "grunt"] and plan["passed_by"] == "person"     # in Review: as it was
    assert (_events(host, "goal_saved")[-1]["via"], _events(host, "goal_saved")[-1]["joined"]) == ("plan", "artist")
    passed = _events(host, "plan_passed")[-1]
    assert (passed["joined"], passed["missing"], passed["via"]) == ("artist", 1, "hand")
























# -- spec 62 A: the spec after the start ---------------------------------------------------------------------

def _started(host, slug, rows=(("k1", "merged", []), ("k2", "ready", ["k1"]), ("k3", "waiting", ["k2"]))):
    """The goal's plan (made by `_plan`) passed and its goal working: `rows` (id, state, after); the runner is made first, so that it does not
    take the goal up, and starts nothing."""
    runner = host.ideas.runner(need=True)
    runner.launched = []
    runner._launch = lambda s, t: runner.launched.append(t["id"])
    tasks = []
    for tid, state, after in rows:
        t = idea_keeper._task(tid, f"Task {tid}", f"Do {tid}", "code", "warrior", list(after))
        t.update(state=state, role="", **({"started": "2026-10-23T10:00:00"} if state not in ("waiting", "ready", "held") else {}))
        tasks.append(t)
    ideas.edit_plan(host.ideas.state_dir, slug, lambda p: p.update(tasks=tasks, passed_at="2026-10-23T09:30:00", passed_by="person"))
    ideas.save_state(host.ideas.state_dir, slug, state="working")
    return runner


def _leader(monkeypatch, answer):
    """The model answers a plan change with `answer`; the prompts it was asked are returned."""
    prompts = []

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):
        prompts.append(prompt)
        return json.dumps(answer), 0.1, 10, "s"
    monkeypatch.setattr(jobs, "run_read", run_read)
    return prompts


CHANGE = {"why": "The export is csv only.", "drop": ["k3"],
          "change": [{"id": "k2", "title": "Write csv", "brief": "Write the rows as csv.", "tier": "laborer"}],
          "add": [{"key": "n1", "title": "Stream rows", "brief": "Stream big files.", "tier": "warrior", "after": ["k1"]}]}


def test_the_page_says_what_changed_since_the_plan_whether_it_is_passed_and_the_change_that_waits(host, monkeypatch):
    slug = _add(host, "x")["slug"]
    page = host.command("ideas.page", {"slug": slug})
    assert (page["changed"], page["passed"], page["change"]) == ([], False, None)
    host.command("ideas.edit", {"slug": slug, "section": "Out", "text": "no images"})              # no plan: nothing is kept
    assert host.command("ideas.page", {"slug": slug})["changed"] == []
    _plan(host, slug)
    for section, text in (("Out", "no images"), ("Why", "people ask"), ("Open questions", "- which?"), ("Out", "no images or pdf"), ("Gist", "Export csv")):
        host.command("ideas.edit", {"slug": slug, "section": section, "text": text, "device": "phone"})
    page = host.command("ideas.page", {"slug": slug})
    json.dumps(page)
    assert (page["changed"], page["passed"], page["change"]) == (["Gist", "Out"], False, None)     # the same text, Why and Open questions did not count
    edited = _events(host, "idea_edited")
    assert [(e["section"], e["chars"], e["passed"], e["device"]) for e in edited] == [
        ("Out", 9, False, "desktop"), ("Out", 9, False, "phone"), ("Why", 10, False, "phone"), ("Open questions", 8, False, "phone"),
        ("Out", 16, False, "phone"), ("Gist", 10, False, "phone")] and all(e["idea"] == slug for e in edited)
    _started(host, slug)
    prompts = _leader(monkeypatch, CHANGE)
    assert host.command("ideas.revise", {"slug": slug}) == {"ok": True}
    _wait(host, slug)
    assert "These sections changed since the plan: Gist, Out." in prompts[0]
    page = host.command("ideas.page", {"slug": slug})
    json.dumps(page)
    assert page["passed"] is True and page["state"] == "working" and page["changed"] == ["Gist", "Out"] and page["revising"] is False
    for busy, revising in (("planning", True), ("talking", False)):                                  # the leader re-plans what is left, not a talk
        host.ideas.keeper._busy[slug] = busy
        assert host.command("ideas.page", {"slug": slug})["revising"] is revising
    host.ideas.keeper._busy.pop(slug)
    change = page["change"]
    assert set(change) == {"made_at", "why", "added", "changed", "dropped", "usd_low", "usd_high", "rows"}
    assert (change["why"], change["added"], change["changed"], change["dropped"]) == ("The export is csv only.", 1, 1, 1)
    assert change["rows"] == [{"op": "add", "id": "", "title": "Stream rows"}, {"op": "change", "id": "k2", "title": "Write csv"},
                              {"op": "drop", "id": "k3", "title": "Task k3"}]
    assert isinstance(change["usd_low"], float) and isinstance(change["usd_high"], float)
    (revised,) = _events(host, "plan_revised")
    assert revised["changed"] == ["Gist", "Out"] and (revised["added"], revised["changed_n"], revised["dropped"]) == (1, 1, 1)
    assert revised["step"] == "plan" and revised["usd_low"] == change["usd_low"]
    stop = next(n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "change")
    assert {k: v for k, v in stop.items() if k not in ("level", "pulls")} == {"idea": slug, "goal": "first-goal", "title": "x", "priority": "normal", "blocks": False,
                    "at": change["made_at"], "kind": "change",
                    "text": "The plan changes · +1 · 1 changed · −1", "why": "The export is csv only.", "added": 1, "changed": 1, "dropped": 1,
                    "usd_low": change["usd_low"], "usd_high": change["usd_high"]}
    assert stop["level"] == "work" and stop["pulls"]["level"] == "work"            # spec 132 C.2: a plan change's stop says its level and what it pulls
    assert stop["pulls"]["estimate"]["usd_high"] >= stop["pulls"]["estimate"]["usd_low"]
    assert host.snapshot()["needs_you"] == 1






def test_take_the_new_plan_applies_it_through_the_runner_and_keeps_the_rest(host, monkeypatch):
    slug = _add(host, "x")["slug"]
    _plan(host, slug)
    runner = _started(host, slug)
    runner._active.append(slug)                                            # the runner works on it
    host.command("ideas.edit", {"slug": slug, "section": "Out", "text": "no images"})
    _leader(monkeypatch, CHANGE)
    with pytest.raises(CommandError, match="No plan change waits for this goal"):
        host.command("ideas.revise_answer", {"slug": slug, "take": True})
    host.command("ideas.revise", {"slug": slug})
    _wait(host, slug)
    from orkboard.core.idea_runner import Run
    runner._runs[(slug, "k2")] = Run(threading.current_thread(), threading.Event())
    ideas.edit_plan(host.ideas.state_dir, slug, lambda p: p["tasks"][1].update(state="running", started="2026-10-23T12:00:00"))      # k2 starts meanwhile
    with pytest.raises(CommandError, match="take is true or false"):
        host.command("ideas.revise_answer", {"slug": slug})
    got = host.command("ideas.revise_answer", {"slug": slug, "take": True, "via": "hand", "device": "phone"})
    assert got == {"ok": True, "added": 1, "changed": 0, "dropped": 1, "left": ["Task k2"]}
    plan = ideas.plan(host.ideas.state_dir, slug)
    assert [(t["id"], t["state"]) for t in plan["tasks"]] == [("k1", "merged"), ("k2", "running"), ("k4", "ready")] and plan["passed_at"]
    assert plan["tasks"][2]["title"] == "Stream rows" and plan["tasks"][2]["after"] == ["k1"]
    page = host.command("ideas.page", {"slug": slug})
    assert (page["changed"], page["change"], page["state"]) == ([], None, "working")
    assert ideas.idea_page(host.ideas.root(), slug).section("Stages").startswith("1. k1 Task k1")      # the Stages again
    assert "k4 Stream rows" in ideas.idea_page(host.ideas.root(), slug).section("Stages")
    (answered,) = _events(host, "plan_change_answered")
    assert (answered["idea"], answered["take"], answered["added"], answered["changed_n"], answered["dropped"], answered["left"], answered["via"],
            answered["device"]) == (slug, True, 1, 0, 1, 1, "hand", "phone")
    assert runner.launched == []                                           # `ready` on the runner's tick (_advance); the one slot is k2's
    with pytest.raises(CommandError, match="No plan change waits for this goal"):
        host.command("ideas.revise_answer", {"slug": slug, "take": False})












def test_the_party_changes_before_the_goal_both_under_the_lock_and_never_for_a_goal_kept_on_hold(host, monkeypatch):
    import threading
    seen = []

    def held() -> bool:
        free = []
        t = threading.Thread(target=lambda: free.append(ideas.LOCK.acquire(blocking=False) and (ideas.LOCK.release() or True)))
        t.start()
        t.join()
        return not free[0]

    set_team, add_idea = goal_team.set_team, ideas.add_idea
    monkeypatch.setattr(goal_team, "set_team", lambda *a, **k: (seen.append(("party", held())), set_team(*a, **k))[1])
    monkeypatch.setattr(ideas, "add_idea", lambda *a, **k: (seen.append(("goal", held())), add_idea(*a, **k))[1])
    ship = _party(host, [], leader="product-manager")
    seen.clear()
    _new(host, ship, "A screen", type="screen", join={"add": "ui-kit"})
    assert seen == [("party", True), ("goal", True)]
    seen.clear()
    kept = host.command("ideas.add", {"text": "Kept back", "track": ship, "hold": True, "type": "experiment", "join": {"add": "experimenter"}})
    assert seen == [("goal", True)] and kept["joined"] is None and kept["type"] == "experiment"
    assert goal_team.team_of(host.ideas.root(), ship) == ["ui-kit"]



def test_every_board_command_is_the_hosts_and_a_phones(host):
    assert BOARD_COMMANDS <= set(host.commands)
    assert all(BoardPhone.allowed(host, c, {}) for c in BOARD_COMMANDS)
    assert BOARD_COMMANDS <= set(host.command("mobile.hello")["commands"])
