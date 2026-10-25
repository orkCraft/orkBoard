"""Spec 81 A (docs/specs/81-a-party-its-tool-and-size.md §1, §2, §3, Tests → A): a party's AI tool kept and read, a goal's task and its leader's
step run on it (a stub registry and stub calls) and on the Main tool without one, a tool without tiers, a tool not signed in holds the task,
`ideas.tools`' order and groups, the size's tiers winning over the library's for a party's seats (a role set by hand keeps its own), Lean's
tasks going to the leader, a resize by a recipe with who joins and leaves, a member at work refused, the events. No real tool is run."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas import Ideas
from orkboard.realm import event_log, goal_team, harnesses, idea_target, ideas, jobs, library, party_recipes, party_resize, roles


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
                                         "team": ["grunt", "tester", "reviewer"], **more})["slug"]


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


def test_a_tool_that_is_none_or_not_installed_is_refused_and_a_kept_one_is_not(host, installed):
    h = host
    with pytest.raises(CommandError, match="No AI tool robot"):
        save(h, tool="robot")
    with pytest.raises(CommandError, match="Hermes Agent is not installed"):
        save(h, tool="hermes")
    assert [t["title"] for t in ideas.tracks(h.root, make=False) if t["title"] != "General"] == []           # nothing was saved
    slug = save(h, tool="codex")
    installed.discard("codex")                                                                               # uninstalled since
    h.command("ideas.goal_save", {"slug": slug, "about": "More.", "tool": "codex"})                          # the same: not a new pick
    with pytest.raises(CommandError, match="Codex is not installed"):
        h.command("ideas.goal_save", {"slug": save(h), "tool": "codex"})
    with pytest.raises(CommandError, match="tool is not text"):
        h.command("ideas.goal_save", {"slug": slug, "tool": 3})
    with pytest.raises(ValueError, match="No AI tool robot"):
        goal_team.set_tool(h.root, slug, "robot")


def test_a_not_signed_in_tool_is_saved_and_the_list_has_its_groups_in_order(host, installed):
    h = host
    h.ideas.host.__class__.sign_ins = property(lambda self: SimpleNamespace(blocked=lambda t: t in ("claude", "pi")))
    try:
        installed.update({"pi", "cursor"})
        got = h.command("ideas.tools")
        rows = {r["id"]: r for r in got["tools"]}
        assert got["main"] in rows and set(rows) == set(harnesses.REGISTRY)
        assert [r["id"] for r in got["tools"]] == ["codex", "cursor", "claude", "pi", "agy", "hermes"]       # ready, then not signed in, then not installed
        assert [r["ready"] for r in got["tools"]] == [True, True, False, False, False, False]
        assert (rows["claude"]["signed_in"], rows["claude"]["installed"]) == (False, True)
        assert (rows["agy"]["installed"], rows["agy"]["ready"], rows["agy"]["experimental"]) == (False, False, True)
        assert rows["codex"]["tiers"] is True and rows["hermes"]["tiers"] is False and rows["pi"]["tiers"] is False
        assert set(rows["codex"]) == {"id", "name", "ready", "signed_in", "installed", "experimental", "tiers"} and rows["codex"]["name"] == "Codex"
        slug = save(h, tool="pi")                                                                           # not signed in: saved, its sign-in follows
        assert goal_team.tool_of(h.root, slug) == "pi"
    finally:
        del h.ideas.host.__class__.sign_ins


def test_the_list_runs_nothing_and_the_main_tool_is_the_machines(host, installed, monkeypatch):
    main_tool(monkeypatch, "codex")
    monkeypatch.setattr(jobs, "run_work", lambda *a, **k: (_ for _ in ()).throw(AssertionError("a tool was run")))
    monkeypatch.setattr(jobs, "run_read", lambda *a, **k: (_ for _ in ()).throw(AssertionError("a tool was run")))
    assert host.command("ideas.tools")["main"] == "codex"
    assert harnesses.for_party(["claude"], [], "")["main"] == "claude"
    assert [r["id"] for r in harnesses.for_party(["pi", "claude"], ["pi"])["tools"]][:2] == ["claude", "pi"]


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


def test_a_task_launched_names_its_partys_tool_and_a_tool_without_tiers_runs_its_own_model(host, installed, monkeypatch):
    h = host
    installed.add("hermes")
    slug = save(h, tool="hermes")
    runner = h.ideas.runner(need=True)
    runner._spawn = lambda *a, **k: None
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    task = {"id": "k1", "tier": "warrior", "kind": "code", "role": "grunt", "title": "T", "state": "ready"}
    passed_plan(h, idea, [task])
    runner._launch(idea, task)
    assert task["tool"] == "hermes" and task["ran_tier"] in ("laborer", "warrior", "elder")                  # the tier is still recorded for the price
    assert harnesses.get("hermes").models == {} and harnesses.get(task["tool"]).pick(task["model"]) == ""     # … and the run names no model: its CLI's default
    assert harnesses.get("hermes").pick("elder") == "" and harnesses.get("codex").models and not harnesses.get("hermes").models


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
    lines = [json.loads(ln) for f in h.state.rglob("spend*.jsonl") for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert {ln.get("harness") or ln.get("tool") for ln in lines} >= {"codex", "claude"}


# -- §2: a size is a team of tiers ----------------------------------------------------------------------------------------------------

def test_a_sizes_tiers_are_kept_and_win_over_the_library_tier_unless_the_person_set_one(host):
    h = host
    slug = save(h, size="standard")
    assert goal_team.tiers_of(h.root, slug) == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "warrior"}
    assert track(h, slug)["size"] == "standard"
    lib = roles.role(h.state, "tester")                                                                      # installed with its library tier (laborer)
    assert lib["model"] == library.get("tester").tier == "laborer"
    seat = goal_team.seat_role(lib, goal_team.tiers_of(h.root, slug))
    assert seat["model"] == "warrior" and lib["model"] == "laborer"                                          # the file is not changed
    h.command("ideas.role_save", {"slug": "tester", "name": "Tester", "model": "elder", "max_parallel": 2})   # set by hand on Agents
    hand = roles.role(h.state, "tester")
    assert goal_team.seat_role(hand, goal_team.tiers_of(h.root, slug)) is hand                              # keeps its own
    assert goal_team.seat_role(None, {"x": "elder"}) is None and goal_team.seat_role(hand, {}) is hand
    full = save(h, size="full", title="Big")
    assert goal_team.tiers_of(h.root, full) == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder"}
    lean = save(h, size="lean", title="Small")
    assert set(goal_team.tiers_of(h.root, lean).values()) == {"warrior"}
    none = h.command("ideas.goal_save", {"title": "Old", "about": "Old.", "craft": "engineering"})["slug"]
    assert goal_team.tiers_of(h.root, none) == {}


def test_a_task_and_a_leaders_step_pick_the_seats_tier(host):
    h = host
    standard = save(h, size="standard")
    runner = h.ideas.runner(need=True)
    idea = ideas.add_idea(h.root, "A goal", standard, h.state)
    task = {"id": "t1", "tier": "laborer", "kind": "tests", "role": "tester"}
    assert runner.ran_on(task, idea) == idea_target.task_pick("laborer", "balance", "warrior")                # not the library's laborer
    assert runner.ran_on({**task, "role": "grunt"}, idea)[0] == "warrior"
    keeper = h.ideas.keeper
    keeper._tls.key = keeper._tls.slug = idea
    assert keeper.leader()["model"] == "elder" and keeper.pick("draft")[0] == "elder"
    lean = save(h, size="lean", title="Small", team=[])
    keeper._tls.key = keeper._tls.slug = ideas.add_idea(h.root, "Another", lean, h.state)
    assert keeper.leader()["model"] == "warrior" and keeper.pick("draft")[0] == "warrior"                    # one Seasoned, not a Veteran on low effort
    keeper._tls.key = keeper._tls.slug = ""


def test_party_recipes_give_tiers_for_any_leader_and_team():
    assert party_recipes.tiers_for("architect", ["grunt", "tester", "reviewer"], "lean") == {"architect": "warrior", "grunt": "warrior", "tester": "warrior", "reviewer": "warrior"}
    assert party_recipes.tiers_for("architect", ["grunt", "tester", "reviewer"], "standard") == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "warrior"}
    assert party_recipes.tiers_for("architect", ["grunt", "tester", "reviewer"], "full") == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder"}
    assert party_recipes.tiers_for("taskmaster", ["grunt"], "full") == {"grunt": "warrior"}                  # the Taskmaster is no seat
    mobile = party_recipes.get("mobile-features")
    for size in ("standard", "full"):
        got = party_recipes.sized(mobile, size)
        assert got["tiers"] == party_recipes.tiers_for(got["leader"], got["team"], size)
    full = party_recipes.sized(mobile, "full")
    assert "laborer" not in full["tiers"].values() and full["tiers"][full["leader"]] == "elder"              # none below Seasoned
    assert party_recipes.sized(mobile, "standard")["tiers"][mobile["leader"]] == "elder"
    assert party_recipes.sized(mobile, "lean")["tiers"] == {mobile["leader"]: "warrior"}


def test_a_lean_partys_task_with_no_taker_goes_to_its_leader_not_the_grunt(host):
    h = host
    h.ideas.keeper.call = lambda tier, prompt, effort="", budget=None: (json.dumps({"tasks": [
        {"id": "k1", "title": "Write the docs", "short": "Docs", "brief": "Write them.", "kind": "docs", "tier": "laborer", "after": []},
        {"id": "k2", "title": "Add code", "short": "Code", "brief": "Add.", "kind": "code", "tier": "warrior", "after": ["k1"]}], "todos": []}), 0.01, 10, "")
    lean = h.command("ideas.goal_save", {"title": "Features", "about": "Features.", "craft": "product", "leader": "product-manager", "team": [],
                                         "size": "lean"})["slug"]
    big = h.command("ideas.goal_save", {"title": "Wide", "about": "Wide.", "craft": "product", "leader": "product-manager",
                                        "team": ["grunt", "copywriter", "reviewer"], "size": "standard"})["slug"]
    assert goal_team.lean_role(h.root, lean) == "product-manager" and goal_team.lean_role(h.root, big) == ""
    for goal, want in ((lean, {"product-manager"}), (big, {"copywriter", "grunt", "reviewer"})):
        idea = ideas.add_idea(h.root, f"A goal in {goal}", goal, h.state)
        ideas.save_state(h.state, idea, state="ready")
        h.ideas.keeper.plan_one(idea)
        got = {t["role"] for t in ideas.plan(h.state, idea)["tasks"]}
        assert got <= want and got, (goal, got)
        assert (got == {"product-manager"}) is (goal == lean)                                                # (a Lean party's leader does them all)
    runner = h.ideas.runner(need=True)
    idea = ideas.add_idea(h.root, "Run it", lean, h.state)
    task = {"id": "k1", "tier": "warrior", "kind": "code", "role": "product-manager"}
    assert runner._role(task)["slug"] == "product-manager" and runner.ran_on(task, idea)[0] == "warrior"


# -- §3: a change of size ---------------------------------------------------------------------------------------------------------------

def made(h, recipe="mobile-features", size="standard", **more):
    r = party_recipes.get(recipe)
    sized = party_recipes.sized(r, size)
    return h.command("ideas.goal_save", {"title": r["name"], "about": r["line"], "craft": "product", "leader": sized["leader"], "team": sized["team"],
                                         "every": [], "size": size, "proposal": recipe, **more})["slug"]


def test_a_party_of_a_recipe_takes_the_sizes_team_and_tiers_in_one_save_and_says_who_joins_and_leaves(host):
    h = host
    slug = made(h)
    assert goal_team.recipe_of(h.root, slug) == "mobile-features" and track(h, slug)["team"] == ["grunt", "artist", "reviewer"]
    h.command("ideas.goal_save", {"slug": slug, "size": "full", "device": "phone"})
    assert track(h, slug)["team"] == ["grunt", "artist", "aso", "reviewer", "accessibility-reviewer"] and track(h, slug)["size"] == "full"
    assert goal_team.tiers_of(h.root, slug)["accessibility-reviewer"] == "elder" and goal_team.tiers_of(h.root, slug)["product-manager"] == "elder"
    assert roles.role(h.state, "aso") is not None                                                            # those who joined are agents of the project
    h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert track(h, slug)["team"] == [] and goal_team.tiers_of(h.root, slug) == {"product-manager": "warrior"}
    h.command("ideas.goal_save", {"slug": slug, "size": "standard"})                                          # a Lean party grows back: its recipe was kept
    assert track(h, slug)["team"] == ["grunt", "artist", "reviewer"]
    rows = events(h, "party_resized")
    assert [(r["from"], r["to"]) for r in rows] == [("standard", "full"), ("full", "lean"), ("lean", "standard")]
    assert rows[0]["joins"] == ["aso", "accessibility-reviewer"] and rows[0]["leaves"] == [] and rows[0]["device"] == "phone"
    assert rows[1]["joins"] == [] and rows[1]["leaves"] == ["grunt", "artist", "aso", "reviewer", "accessibility-reviewer"]
    assert rows[2]["joins"] == ["grunt", "artist", "reviewer"]


def test_the_checks_a_party_has_for_every_idea_stay_across_a_resize(host):
    h = host
    slug = made(h, "engineering-code", "full", every=["reviewer"])
    assert goal_team.every_of(h.root, slug) == ["reviewer"]
    h.command("ideas.goal_save", {"slug": slug, "size": "standard"})
    assert goal_team.every_of(h.root, slug) == ["reviewer"] and track(h, slug)["team"] == ["grunt", "tester", "reviewer"]
    h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert goal_team.every_of(h.root, slug) == []                                                            # the checker left, so did its every


def test_a_resize_that_lets_a_member_at_work_go_is_refused_and_nothing_changes(host):
    h = host
    slug = made(h, "engineering-code", "full")
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    ideas.save_state(h.state, idea, state="working")
    ideas.save_plan(h.state, idea, {"idea": idea, "todos": [], "tasks": [{"id": "t1", "title": "T", "state": "running", "role": "tester", "kind": "tests"}]})
    with pytest.raises(CommandError, match="Tester has work open: it cannot leave"):
        h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert track(h, slug)["size"] == "full" and track(h, slug)["team"] == ["grunt", "tester", "reviewer"]
    assert goal_team.tiers_of(h.root, slug)["reviewer"] == "elder" and events(h, "party_resized") == []
    h.command("ideas.goal_save", {"slug": slug, "size": "standard"})                                          # standard keeps the tester
    assert track(h, slug)["size"] == "standard"


def test_a_party_made_from_the_library_with_no_recipe_keeps_its_team_and_sets_tiers_and_target_only(host):
    h = host
    slug = h.command("ideas.goal_save", {"title": "Mine", "about": "Mine.", "craft": "engineering", "leader": "architect",
                                         "team": ["artist", "accessibility-reviewer"], "size": "standard"})["slug"]
    assert party_resize.recipe_for("architect", ["artist", "accessibility-reviewer"]) is None and goal_team.recipe_of(h.root, slug) == ""
    before = goal_team.team_of(h.root, slug)
    h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert goal_team.team_of(h.root, slug) == before and goal_team.size_of(h.root, slug) == "lean"
    assert set(goal_team.tiers_of(h.root, slug).values()) == {"warrior"}
    got = h.command("ideas.party_sizes", {"slug": slug})
    assert got["size"] == "lean" and all(v["joins"] == v["leaves"] == [] for v in got["sizes"].values())
    [row] = events(h, "party_resized")
    assert row["joins"] == row["leaves"] == []


def test_party_sizes_says_what_each_size_would_make_of_a_party(host):
    h = host
    slug = made(h)
    got = h.command("ideas.party_sizes", {"slug": slug})
    assert got["size"] == "standard" and list(got["sizes"]) == ["lean", "standard", "full"]
    assert got["sizes"]["standard"]["joins"] == got["sizes"]["standard"]["leaves"] == [] and got["sizes"]["standard"]["recipe"] == "mobile-features"
    assert [a["name"] for a in got["sizes"]["lean"]["leaves"]] == ["Grunt", "Artist", "Reviewer"]
    assert [a["slug"] for a in got["sizes"]["full"]["joins"]] == ["aso", "accessibility-reviewer"]
    assert got["sizes"]["lean"]["tiers"] == {"product-manager": "warrior"}
    assert [r["event"] for r in event_log.read(h.ideas.host.repo_root) if r["event"] == "party_resized"] == []        # a read: nothing is written
    with pytest.raises(CommandError, match="That party is gone"):
        h.command("ideas.party_sizes", {"slug": "nope"})
    assert party_resize.recipe_for("product-manager", ["grunt", "artist"], "")["id"] == "mobile-features"
    assert party_resize.recipe_for("taskmaster", ["grunt"]) is None and party_resize.recipe_for("architect", []) is None
    with pytest.raises(ValueError):
        party_resize.resized(h.root, slug, "huge")


def test_ideation_and_release_are_sized_too(host):
    h = host
    ideation = party_recipes.get("ideation")
    slug = h.command("ideas.goal_save", {"title": "Ideation", "about": "Pitches.", "craft": "product", "leader": "investor",
                                         "team": party_recipes.sized(ideation, "full")["team"], "size": "full", "proposal": "ideation"})["slug"]
    h.command("ideas.goal_save", {"slug": slug, "size": "standard"})
    assert goal_team.team_of(h.root, slug) == ["product-view", "market-view", "skeptic"]
    h.command("ideas.goal_save", {"slug": slug, "size": "lean"})
    assert goal_team.team_of(h.root, slug) == [] and goal_team.leader_of(h.root, slug) == "investor"
    with pytest.raises(CommandError, match="its views and the skeptic stay"):
        h.command("ideas.goal_save", {"slug": slug, "team": ["product-view", "market-view", "tech-view"], "leader": "investor"})
    release = made(h, "release", "lean")
    assert goal_team.team_of(h.root, release) == []
    h.command("ideas.goal_save", {"slug": release, "size": "full"})
    assert len(goal_team.team_of(h.root, release)) == 4
