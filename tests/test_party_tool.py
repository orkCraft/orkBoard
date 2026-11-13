"""Spec 81 A (docs/specs/81-a-party-its-tool-and-size.md §1, §2, §3, Tests → A): a party's AI tool kept and read, a goal's task and its leader's
step run on it (a stub registry and stub calls) and on the Main tool without one, a tool without tiers, a tool not signed in holds the task,
`ideas.tools`' order and groups, the size's tiers winning over the library's for a party's seats (a role set by hand keeps its own), Lean's
tasks going to the leader, a resize by a recipe with who joins and leaves, a member at work refused, the events. No real tool is run."""
from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas import Ideas
from orkboard.realm import event_log, goal_team, ideas, jobs, party_recipes, party_resize, roles


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
    """Which tools this computer has: claude and codex, unless a test says otherwise."""
    have = {"claude", "codex"}
    monkeypatch.setattr(Ideas, "tools_installed", staticmethod(lambda: set(have)))
    return have


def events(h, name):
    return [r for r in event_log.read(h.ideas.host.repo_root) if r["event"] == name]


def save(h, **more):
    return h.command("ideas.goal_save", {"title": "Engineering", "about": "Code.", "craft": "engineering", "leader": "architect",
                                         "team": ["tester", "reviewer"], **more})["slug"]


def track(h, slug):
    return next(t for t in ideas.tracks(h.root, make=False) if t["slug"] == slug)


def main_tool(monkeypatch, tool):
    from orkboard import settings
    monkeypatch.setattr(settings, "main_tool", lambda machine=None: tool)


# -- §1: a party's tool kept and read ----------------------------------------------------------------------------------------------------

def test_goal_save_keeps_a_partys_tool_on_its_page_and_every_reader_says_it(host, installed):
    h = host
    slug = save(h, tool="codex")
    assert goal_team.tool_of(h.root, slug) == "codex" and "tool: codex" in (h.root / ideas.TRACKS / f"{slug}.md").read_text(encoding="utf-8")
    assert track(h, slug)["tool"] == "codex" and h.command("ideas.goal", {"slug": slug})["tool"] == "codex"
    assert next(g for g in h.command("ideas.map", {})["goals"] if g["slug"] == slug)["tool"] == "codex"
    assert next(g for g in h.command("ideas.board", {})["tracks"] if g["slug"] == slug)["tool"] == "codex"
    older = h.command("ideas.goal_save", {"title": "Old", "about": "Old.", "craft": "engineering"})["slug"]
    assert track(h, older)["tool"] == "" and goal_team.tool_of(h.root, older) == ""                       # none is the Main tool
    h.command("ideas.goal_save", {"slug": slug, "about": "Code, changed."})                                  # saved again with none sent: it keeps its tool
    assert goal_team.tool_of(h.root, slug) == "codex"
    h.command("ideas.goal_save", {"slug": slug, "tool": ""})                                                 # the Main tool again
    assert goal_team.tool_of(h.root, slug) == ""
    assert events(h, "goal_saved")[0]["tool"] == "codex"


# -- §1.2: the runner and the keeper run on it ---------------------------------------------------------------------------------------

def passed_plan(h, slug, tasks):
    ideas.save_plan(h.state, slug, {"idea": slug, "todos": [], "tasks": tasks, "passed_at": "2026-10-25T10:00:00"})
    ideas.save_state(h.state, slug, state="plan")


def test_a_task_runs_on_its_partys_tool_and_a_party_with_none_on_the_main_tool(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    codex, plain = save(h, tool="codex"), save(h, title="Plain")
    runner = h.ideas.runner(need=True)
    a, b = ideas.add_idea(h.root, "In codex", codex, h.state), ideas.add_idea(h.root, "In plain", plain, h.state)
    assert runner.tool_of(a) == "codex" and runner.tool_of(b) == "claude" and runner.tool_of("nope") == "claude"
    main_tool(monkeypatch, "agy")
    assert runner.tool_of(a) == "codex" and runner.tool_of(b) == "agy"                                       # the Main tool is read when it runs
    seen = []

    def run_work(harness, prompt, path, cancel, model="", **k):
        seen.append((harness, model))
        return "done", 0.5, 100, "s-1"
    monkeypatch.setattr(jobs, "run_work", run_work)
    task = {"id": "k1", "tier": "warrior", "kind": "code", "role": "grunt", "title": "T"}
    for slug in (a, b):
        passed_plan(h, slug, [dict(task)])
        spent = {"cost": None, "tokens": None}
        runner._session(slug, "k1", h.root, None, "sonnet", {}, "Do it", "", spent)
    assert [s[0] for s in seen] == ["codex", "agy"]
    lines = [json.loads(ln) for f in h.state.rglob("spend*.jsonl") for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert {ln.get("harness") or ln.get("tool") for ln in lines} >= {"codex", "agy"}


def test_a_task_waits_for_the_sign_in_of_its_partys_tool_not_of_another(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    codex, plain = save(h, tool="codex"), save(h, title="Plain")
    runner = h.ideas.runner(need=True)
    launched = []
    runner._launch = lambda slug, t: (launched.append((slug, t["id"])), t.update(state="running"))
    runner.sign_ins = SimpleNamespace(blocked=lambda t: t == "codex", holds=lambda e: False)
    a, b = ideas.add_idea(h.root, "In codex", codex, h.state), ideas.add_idea(h.root, "In plain", plain, h.state)
    for slug in (a, b):
        passed_plan(h, slug, [{"id": "k1", "tier": "warrior", "kind": "code", "role": "grunt", "title": "T"}])
    runner._active[:] = []
    runner.start(a)
    runner.start(b)
    held = next(t for t in runner.plan(a)["tasks"])
    assert held["state"] == "held" and held["held_for"] == "sign_in" and held["harness"] == "codex"
    assert launched == [(b, "k1")] and runner.held_for("codex") == 1 and runner.held_for("claude") == 0


def test_the_keeper_runs_a_goals_steps_on_its_partys_tool_and_a_step_of_no_goal_on_the_main_tool(host, installed, monkeypatch):
    h = host
    main_tool(monkeypatch, "claude")
    codex = save(h, tool="codex")
    keeper = h.ideas.keeper
    idea = ideas.add_idea(h.root, "A goal", codex, h.state)
    seen = []

    def run_read(harness, prompt, cwd, cancel, model="", **k):
        seen.append(harness)
        return "{}", 0.1, 10, ""
    monkeypatch.setattr(jobs, "run_read", run_read)
    for key in (idea, f"goal:{codex}", ""):
        keeper._tls.key = keeper._tls.slug = key
        keeper._claude("warrior", "A prompt")
    assert seen == ["codex", "codex", "claude"]
    keeper._tls.key = keeper._tls.slug = ""
    keeper._spent("draft", ("warrior", "medium"), None, 10, 0.1)
    keeper._tls.key = keeper._tls.slug = idea
    keeper._spent("draft", ("warrior", "medium"), None, 10, 0.1)
    for _ in range(1000):                                                                                    # the party's own reading (started by the save) writes its codex line in the background:
        if not keeper.busy_goal(codex):                                                                       # read the ledger once it has, not after a guessed time
            break
        time.sleep(0.01)
    assert not keeper.busy_goal(codex)
    lines = [json.loads(ln) for f in h.state.rglob("spend*.jsonl") for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert {ln.get("harness") or ln.get("tool") for ln in lines} >= {"codex", "claude"}


# -- §2: a size is a team of tiers ----------------------------------------------------------------------------------------------------


def test_no_partys_task_goes_to_its_leader_a_tag_no_seat_takes_goes_to_the_projects_role_at_every_size(host):
    h = host
    h.ideas.keeper.call = lambda tier, prompt, effort="", budget=None: (json.dumps({"tasks": [
        {"id": "k1", "title": "Write the docs", "short": "Docs", "brief": "Write them.", "kind": "docs", "tier": "laborer", "after": []},
        {"id": "k2", "title": "Add code", "short": "Code", "brief": "Add.", "kind": "code", "tier": "warrior", "after": ["k1"]}], "todos": []}), 0.01, 10, "")
    for size in ("lean", "standard", "full"):
        goal = h.command("ideas.goal_save", {"title": f"Features {size}", "about": "Features.", "craft": "product", "leader": "product-manager",
                                             "team": ["copywriter", "reviewer"], "size": size})["slug"]
        assert goal_team.leader_of(h.root, goal) == "product-manager"
        idea = ideas.add_idea(h.root, f"A goal in {goal}", goal, h.state)
        ideas.save_state(h.state, idea, state="ready")
        h.ideas.keeper.plan_one(idea)
        got = {t["role"] for t in ideas.plan(h.state, idea)["tasks"]}
        assert got and got <= {"copywriter", "grunt", "reviewer"} and "product-manager" not in got, (size, got)       # (spec 152 A.2)
        assert not hasattr(goal_team, "lean_role")


# -- §3: a change of size ---------------------------------------------------------------------------------------------------------------

def made(h, recipe="tech", size="standard", **more):
    r = party_recipes.get(recipe)
    sized = party_recipes.sized(r, size)
    return h.command("ideas.goal_save", {"title": r["name"], "about": r["line"], "craft": "product", "leader": sized["leader"], "team": sized["team"],
                                         "every": [], "size": size, "proposal": recipe, **more})["slug"]


def test_a_size_changes_a_partys_tiers_in_one_save_and_never_its_squad_nor_who_joins_or_leaves(host):
    h = host
    squad = ["grunt", "tester", "reviewer"]
    slug = made(h)
    assert goal_team.recipe_of(h.root, slug) == "tech" and track(h, slug)["team"] == squad
    h.command("ideas.goal_save", {"slug": slug, "size": "full", "device": "phone"})
    assert track(h, slug)["team"] == squad and track(h, slug)["size"] == "full"
    assert goal_team.tiers_of(h.root, slug) == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder"}
    assert roles.role(h.state, "reviewer") is not None
    h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert track(h, slug)["team"] == squad and goal_team.tiers_of(h.root, slug) == {"architect": "elder", **{s: "warrior" for s in squad}}
    h.command("ideas.goal_save", {"slug": slug, "size": "standard"})
    assert track(h, slug)["team"] == squad and goal_team.tiers_of(h.root, slug) == {"architect": "elder", "grunt": "warrior"}
    rows = events(h, "party_resized")
    assert [(r["from"], r["to"]) for r in rows] == [("standard", "full"), ("full", "lean"), ("lean", "standard")]
    assert all(r["joins"] == [] and r["leaves"] == [] for r in rows) and rows[0]["device"] == "phone"


def test_a_party_made_from_the_library_with_no_recipe_keeps_its_team_and_sets_tiers_and_target_only(host):
    h = host
    slug = h.command("ideas.goal_save", {"title": "Mine", "about": "Mine.", "craft": "engineering", "leader": "architect",
                                         "team": ["artist", "accessibility-reviewer"], "size": "standard"})["slug"]
    assert party_resize.recipe_for("architect", ["artist", "accessibility-reviewer"]) is None and goal_team.recipe_of(h.root, slug) == ""
    before = goal_team.team_of(h.root, slug)
    h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert goal_team.team_of(h.root, slug) == before and goal_team.size_of(h.root, slug) == "lean"
    assert goal_team.tiers_of(h.root, slug) == {"architect": "elder", "artist": "warrior", "accessibility-reviewer": "warrior"}
    got = h.command("ideas.party_sizes", {"slug": slug})
    assert got["size"] == "lean" and all(v["joins"] == v["leaves"] == [] for v in got["sizes"].values())
    [row] = events(h, "party_resized")
    assert row["joins"] == row["leaves"] == []


