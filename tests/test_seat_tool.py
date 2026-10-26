"""Spec 91 D (docs/specs/91-the-owners-list.md §6): an AI tool for each seat. Tools kept and cleaned, `tool_for` falling back seat → party → "", the
runner running a task on its taker's seat's tool (and the sign-in hold waiting for that tool), the keeper running the leader's steps on the leader's
seat's tool, `makes` on Antigravity only, `needs` on the three roles, `ideas.goal_save {tools}` and the rows that carry them. No real tool is run."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas import Ideas
from orkboard.realm import event_log, goal_team, harnesses, ideas, jobs, library


def stub(tier, prompt, effort="", budget=None):
    return json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, ""


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.ideas.keeper.call = stub
    h.root, h.state = h.ideas.root(), h.ideas.state_dir
    yield h


@pytest.fixture
def installed(monkeypatch):
    have = {"claude", "codex", "agy"}
    monkeypatch.setattr(Ideas, "tools_installed", staticmethod(lambda: set(have)))
    return have


def save(h, **more):
    return h.command("ideas.goal_save", {"title": "Engineering", "about": "Code.", "craft": "engineering", "leader": "architect",
                                         "team": ["tester", "reviewer"], **more})["slug"]


def track(h, slug):
    return next(t for t in ideas.tracks(h.root, make=False) if t["slug"] == slug)


def main_tool(monkeypatch, tool):
    from orkboard import settings
    monkeypatch.setattr(settings, "main_tool", lambda machine=None: tool)


def passed_plan(h, slug, tasks):
    ideas.save_plan(h.state, slug, {"idea": slug, "todos": [], "tasks": tasks, "passed_at": "2026-10-25T10:00:00"})
    ideas.save_state(h.state, slug, state="plan")


# -- §6.1, 6.2: kept, cleaned, and the one answer ---------------------------------------------------------------------------------------

def test_a_seats_tools_are_kept_beside_the_tiers_and_cleaned(host):
    h = host
    slug = save(h)
    assert goal_team.tools_of(h.root, slug) == {}
    goal_team.set_tools(h.root, slug, {"tester": "codex", "architect": "agy"})
    assert goal_team.tools_of(h.root, slug) == {"tester": "codex", "architect": "agy"}
    text = (h.root / ideas.TRACKS / f"{slug}.md").read_text(encoding="utf-8")
    assert 'tools: {"tester": "codex", "architect": "agy"}' in text
    assert goal_team.clean_tools('{"tester": "codex", "Bad Slug": "agy", "reviewer": "robot", "x": 3}') == {"tester": "codex"}
    assert goal_team.clean_tools("not json") == {} and goal_team.clean_tools(["a"]) == {} and goal_team.clean_tools(None) == {}
    goal_team.set_tools(h.root, slug, {})                                                                     # {} clears
    assert goal_team.tools_of(h.root, slug) == {} and '"tester": "codex"' not in (h.root / ideas.TRACKS / f"{slug}.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="No AI tool robot"):
        goal_team.set_tools(h.root, slug, {"tester": "robot"})
    with pytest.raises(ValueError, match="No party"):
        goal_team.set_tools(h.root, "nope", {"tester": "codex"})
    assert goal_team.tools_of(h.root, "nope") == {}


def test_tool_for_falls_back_from_the_seat_to_the_party_to_the_main_tool(host, installed):
    h = host
    slug = save(h, tool="codex")
    goal_team.set_tools(h.root, slug, {"tester": "agy"})
    assert goal_team.tool_for(h.root, slug, "tester") == "agy"                                                # the seat's own
    assert goal_team.tool_for(h.root, slug, "reviewer") == "codex"                                            # no seat tool: the party's
    assert goal_team.tool_for(h.root, slug, "nobody") == "codex"
    plain = save(h, title="Plain")
    assert goal_team.tool_for(h.root, plain, "tester") == ""                                                  # neither: the Main tool, for the caller
    goal_team.set_tools(h.root, plain, {"architect": "claude"})
    assert goal_team.tool_for(h.root, plain, "architect") == "claude" and goal_team.tool_for(h.root, plain, "tester") == ""


# -- §6.3: the runner and the keeper ----------------------------------------------------------------------------------------------------

def test_a_task_runs_on_the_tool_of_the_seat_that_takes_it(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    slug = save(h, tool="codex", tools={"tester": "agy"})
    runner = h.ideas.runner(need=True)
    runner._spawn = lambda *a, **k: None
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    by_tester = {"id": "k1", "tier": "warrior", "kind": "tests", "role": "tester", "title": "T", "state": "ready"}
    by_reviewer = {"id": "k2", "tier": "warrior", "kind": "review", "role": "reviewer", "title": "R", "state": "ready"}
    passed_plan(h, idea, [by_tester, by_reviewer])
    assert runner.tool_of(idea) == "codex"                                                                    # with no task: the party's, as before
    assert runner.tool_of(idea, by_tester) == "agy" and runner.tool_of(idea, by_reviewer) == "codex"
    runner._launch(idea, by_tester)
    runner._launch(idea, by_reviewer)
    assert (by_tester["tool"], by_reviewer["tool"]) == ("agy", "codex")
    other = save(h, title="Plain")                                                                            # a party with no tool at all: the Main tool
    goal_team.set_tools(h.root, other, {"tester": "agy"})
    idea2 = ideas.add_idea(h.root, "Another", other, h.state)
    assert runner.tool_of(idea2, by_tester) == "agy" and runner.tool_of(idea2, by_reviewer) == "claude"
    seen = []

    def run_work(harness, prompt, path, cancel, model="", **k):
        seen.append(harness)
        return "done", 0.5, 100, "s-1"
    monkeypatch.setattr(jobs, "run_work", run_work)
    for task in (by_tester, by_reviewer):
        runner._session(idea, task["id"], h.root, None, "sonnet", {}, "Do it", "", {"cost": None, "tokens": None})
    assert seen == ["agy", "codex"]


def test_a_lean_partys_leader_takes_the_tasks_on_its_own_seat_tool(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    slug = save(h, size="lean", team=[], tool="codex", tools={"architect": "agy"})
    runner = h.ideas.runner(need=True)
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    assert runner.tool_of(idea, {"id": "k1", "kind": "code", "role": "architect"}) == "agy"


def test_a_task_waits_for_the_sign_in_of_its_seats_tool(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    slug = save(h, tool="claude", tools={"tester": "codex"})
    runner = h.ideas.runner(need=True)
    launched = []
    runner._launch = lambda s, t: (launched.append((s, t["id"])), t.update(state="running"))
    runner.sign_ins = SimpleNamespace(blocked=lambda t: t == "codex", holds=lambda e: False)
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    passed_plan(h, idea, [{"id": "k1", "tier": "warrior", "kind": "tests", "role": "tester", "title": "T"},
                          {"id": "k2", "tier": "warrior", "kind": "review", "role": "reviewer", "title": "R"}])
    runner._active[:] = []
    runner.start(idea)
    tasks = {t["id"]: t for t in runner.plan(idea)["tasks"]}
    assert tasks["k1"]["state"] == "held" and tasks["k1"]["held_for"] == "sign_in" and tasks["k1"]["harness"] == "codex"
    assert launched == [(idea, "k2")] and runner.held_for("codex") == 1 and runner.held_for("claude") == 0


def test_the_keeper_runs_the_leaders_steps_on_the_leaders_seat_tool(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    keeper = h.ideas.keeper
    seat = save(h, tool="codex", tools={"architect": "agy", "tester": "claude"})                              # the leader's seat has its own
    party = save(h, title="Party tool", tool="codex")                                                         # no seat tool: the party's
    plain = save(h, title="Plain")                                                                            # neither: the Main tool
    seen = []

    def run_read(harness, prompt, cwd, cancel, model="", **k):
        seen.append(harness)
        return "{}", 0.1, 10, ""
    monkeypatch.setattr(jobs, "run_read", run_read)
    for slug in (seat, party, plain):
        keeper._tls.key = keeper._tls.slug = ideas.add_idea(h.root, "A goal", slug, h.state)
        assert keeper.tool_now() == {seat: "agy", party: "codex", plain: "claude"}[slug]
        keeper._claude("warrior", "A prompt")
    keeper._tls.key = keeper._tls.slug = f"goal:{seat}"
    keeper._claude("warrior", "A prompt")
    keeper._tls.key = keeper._tls.slug = ""
    keeper._claude("warrior", "A prompt")
    assert seen == ["agy", "codex", "claude", "agy", "claude"]


# -- §6.4, 6.5: what a tool makes and what a role needs ------------------------------------------------------------------------------------

def test_only_antigravity_makes_pictures_and_the_list_says_so(host, installed):
    assert {h.id: h.makes for h in harnesses.REGISTRY.values()} == {i: ("pictures",) if i == "agy" else () for i in harnesses.REGISTRY}
    rows = {r["id"]: r for r in host.command("ideas.tools")["tools"]}
    assert rows["agy"]["makes"] == ["pictures"] and all(r["makes"] == [] for i, r in rows.items() if i != "agy")
    assert rows["codex"].keys() == {"id", "name", "ready", "signed_in", "installed", "experimental", "tiers", "makes"}
    assert harnesses.for_party(["agy"], [], "agy")["tools"][0]["makes"] == ["pictures"]


def test_three_roles_say_what_they_need_and_the_page_gets_it(host):
    needs = {a.id: a.needs for a in library.LIBRARY if a.needs}
    assert needs == {"artist": ("pictures",), "aso": ("pictures",), "sound-designer": ("sound",)}
    assert all(a.needs == () for a in library.LIBRARY if a.id not in needs)
    listed = {a["id"]: a for a in library.listed()}
    assert listed["artist"]["needs"] == ["pictures"] and listed["sound-designer"]["needs"] == ["sound"] and listed["grunt"]["needs"] == []
    page = {a["id"]: a for a in host.command("ideas.roles")["library"]}
    assert page["aso"]["needs"] == ["pictures"] and page["tester"]["needs"] == []


# -- §6.6, 6.7: goal_save and the rows --------------------------------------------------------------------------------------------------

def test_goal_save_keeps_the_seats_tools_and_every_row_carries_them(host, installed):
    h = host
    slug = save(h, tool="codex", tools={"tester": "agy", "architect": "claude"})
    assert goal_team.tools_of(h.root, slug) == {"tester": "agy", "architect": "claude"}
    assert track(h, slug)["tools"] == {"tester": "agy", "architect": "claude"}
    assert h.command("ideas.goal", {"slug": slug})["tools"] == {"tester": "agy", "architect": "claude"}
    assert next(g for g in h.command("ideas.map", {})["goals"] if g["slug"] == slug)["tools"] == {"tester": "agy", "architect": "claude"}
    assert next(g for g in h.command("ideas.board", {})["tracks"] if g["slug"] == slug)["tools"] == {"tester": "agy", "architect": "claude"}
    assert track(h, save(h, title="Plain"))["tools"] == {}
    h.command("ideas.goal_save", {"slug": slug, "about": "Code, changed."})                                  # saved again with none sent: they stay
    assert goal_team.tools_of(h.root, slug) == {"tester": "agy", "architect": "claude"}
    h.command("ideas.goal_save", {"slug": slug, "tools": {"reviewer": "codex"}})                              # replaced as sent
    assert goal_team.tools_of(h.root, slug) == {"reviewer": "codex"}
    h.command("ideas.goal_save", {"slug": slug, "tools": {}})
    assert goal_team.tools_of(h.root, slug) == {}
    got = [r for r in event_log.read(h.ideas.host.repo_root) if r["event"] == "goal_saved"]
    assert got[0]["tools"] == ["tester:agy", "architect:claude"] and got[-1]["tools"] == []


def test_goal_save_refuses_an_unknown_tool_and_a_seat_that_is_not_in_the_party(host, installed):
    h = host
    with pytest.raises(CommandError, match="No AI tool robot"):
        save(h, tools={"tester": "robot"})
    with pytest.raises(CommandError, match="grunt is not in the party"):
        save(h, tools={"grunt": "codex"})
    with pytest.raises(CommandError, match="tools is not a map"):
        save(h, tools=["tester"])
    assert [t["title"] for t in ideas.tracks(h.root, make=False) if t["title"] != "General"] == []           # nothing was saved
    slug = save(h, tools={"architect": "codex", "reviewer": "agy"})                                          # the leader and a member are seats
    with pytest.raises(CommandError, match="product-manager is not in the party"):
        h.command("ideas.goal_save", {"slug": slug, "tools": {"product-manager": "codex"}})
    with pytest.raises(CommandError, match="architect is not in the party"):                                 # … judged by the team sent with it
        h.command("ideas.goal_save", {"slug": slug, "leader": "product-manager", "team": ["tester"], "tools": {"architect": "codex"}})
    assert goal_team.tools_of(h.root, slug) == {"architect": "codex", "reviewer": "agy"}
    h.command("ideas.goal_save", {"slug": slug, "team": ["tester"]})                                         # a seat that leaves takes its tool with it
    assert goal_team.tools_of(h.root, slug) == {"architect": "codex"}
    taskmaster = h.command("ideas.goal_save", {"title": "Alone", "about": "Alone.", "craft": "engineering", "tools": {"taskmaster": "agy"}})["slug"]
    assert goal_team.tool_for(h.root, taskmaster, "taskmaster") == "agy"                                     # the Taskmaster alone is the leader
