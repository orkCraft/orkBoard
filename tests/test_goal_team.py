"""A goal's team from the library (decisions §53; realm/library.py, realm/goal_team.py): the library's agents and their
instructions, a team kept on the goal and its agents made roles of the project, each task tagged by its kind of work and
given to the one of the team who does that kind, Grunt for the rest."""
from __future__ import annotations

import json
import sys

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import goal_team, ideas, jobs, library, roles


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _wait(host, slug="", goal=False):
    import time
    k = host.ideas.keeper
    for _ in range(400):
        if not (k.busy_goal(slug) if goal else k.busy(slug)):
            return
        time.sleep(0.01)


def test_a_team_routes_each_kind_to_its_specialist_and_the_rest_to_grunt(tmp_path):
    library.install(tmp_path, ["grunt", "product-designer", "accessibility-reviewer", "analyst"])
    team = ["grunt", "product-designer", "accessibility-reviewer", "analyst"]
    assert roles.role_for(tmp_path, "design", team)["slug"] == "product-designer"    # Grunt first in the team: still the designer's
    assert roles.role_for(tmp_path, "a11y", team)["slug"] == "accessibility-reviewer"
    assert roles.role_for(tmp_path, "metrics", team)["slug"] == "analyst"
    assert roles.role_for(tmp_path, "code", team)["slug"] == "grunt"
    assert roles.role_for(tmp_path, "seo", team)["slug"] == "grunt"                  # no one of the team does it
    assert roles.role_for(tmp_path, "design")["slug"] == "grunt"                     # no team: the project's, as before
    assert set(roles.kinds(tmp_path).values()) == {"grunt"}                          # installing gives the project no type


def test_goal_save_with_a_team_makes_its_agents_keeps_the_team_and_never_overwrites_an_agent(host):
    slug = host.command("ideas.goal_save", {"about": "A landing page that sells.", "craft": "design", "leader": "product-designer",
                                            "team": ["ui-kit", "accessibility-reviewer", "taskmaster"]})["slug"]
    _wait(host, slug, goal=True)
    g = next(t for t in host.command("ideas.board")["tracks"] if t["slug"] == slug)
    assert g["team"] == ["ui-kit", "accessibility-reviewer"] and g["leader"]["slug"] == "product-designer"   # the leader leads, not in the team
    assert g["leader"]["head"]["race"] == "dryad" and g["verdict"] is None          # the leader of a Design party: the elves' higher form (spec 99 §1.4)
    pd = roles.role(host.ideas.state_dir, "product-designer")
    assert pd["name"] == "Product designer" and pd["craft"] == "design" and pd["model"] == "elder" and pd["takes"] == ["design"]
    assert pd["instruction"] == library.get("product-designer").instruction
    host.command("ideas.role_save", {"slug": "product-designer", "name": "Product designer", "model": "", "max_parallel": 1,
                                     "instruction": "Mine now."})
    host.command("ideas.goal_save", {"about": "Another page.", "craft": "design", "leader": "product-designer", "team": ["ui-kit"]})
    assert roles.role(host.ideas.state_dir, "product-designer")["instruction"] == "Mine now."   # the person's edit stays
    assert roles.role(host.ideas.state_dir, "product-designer")["takes"] == ["design"]
    with pytest.raises(CommandError, match="No agent 'wizard'"):
        host.command("ideas.goal_save", {"about": "x", "team": ["wizard"]})
    with pytest.raises(CommandError, match="at most 5 builders"):
        host.command("ideas.goal_save", {"about": "x", "team": ["grunt", "tester", "artist", "seo", "aso", "copywriter"]})
    with pytest.raises(CommandError, match="at most 2 checkers"):
        host.command("ideas.goal_save", {"about": "x", "team": ["reviewer", "editor", "playtester"]})
    with pytest.raises(CommandError, match="does not lead"):
        host.command("ideas.goal_save", {"about": "x", "leader": "grunt", "team": []})
    with pytest.raises(CommandError, match="A leader leads"):
        host.command("ideas.goal_save", {"about": "x", "team": ["architect"]})
    got = host.command("ideas.roles")
    assert len(got["library"]) == len(library.LIBRARY) == 41 and got["suggested"] == 2              # 26, Ideation's six (spec 65), Release's four (spec 68) and the five of Art and sound
    artist = next(a for a in got["library"] if a["id"] == "artist")
    assert {"craft": "design", "race": "elf", "tier": "laborer", "takes": ["art"], "check": None}.items() <= artist.items()
    a11y = next(a for a in got["library"] if a["id"] == "accessibility-reviewer")
    assert a11y["check"]["applies"] == "when the idea changes what people see or use"


def test_the_plan_tags_each_task_and_gives_it_to_the_team_member_who_does_that_kind(host, monkeypatch):
    seen = []

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):
        seen.append(prompt)
        if "turn it into" in prompt:
            return json.dumps({"tasks": [
                {"id": "a", "title": "Screens", "brief": "Draw the flow", "kind": "design", "tier": "warrior"},
                {"id": "b", "title": "Contrast", "brief": "Check it", "kind": "a11y", "tier": "laborer", "after": ["a"]},
                {"id": "c", "title": "Wire it", "brief": "Code it", "kind": "code", "tier": "warrior", "after": ["a"]},
                {"id": "d", "title": "Odd", "brief": "x", "kind": "spells", "tier": "warrior"}]}), 0.1, 10, "s"
        if "saved a goal" in prompt:
            return json.dumps({"summary": "ok", "questions": [], "metrics": []}), 0.1, 10, "s"
        return json.dumps({"gist": "A page.", "why": "", "size": "S", "priority": "normal", "before": "", "questions": []}), 0.1, 10, "s"

    monkeypatch.setattr(jobs, "run_read", run_read)
    host.command("ideas.board_set", {"autostart": False})
    goal = host.command("ideas.goal_save", {"about": "A landing page.", "craft": "design", "leader": "product-designer",
                                            "team": ["grunt", "accessibility-reviewer"]})["slug"]
    _wait(host, goal, goal=True)
    slug = host.command("ideas.add", {"text": "The hero section", "track": goal, "hold": True})["slug"]
    host.command("ideas.read_now", {"slug": slug})
    _wait(host, slug)
    host.command("ideas.plan", {"slug": slug})
    _wait(host, slug)
    prompt = next(p for p in seen if "turn it into" in p)
    assert '"uikit" (components and tokens of the design system)' in prompt
    assert "The goal's team, by the tags each does: Grunt (" in prompt and "Product designer (design)" not in prompt, "the leader takes no tag (spec 152 A.2)"
    assert "Accessibility reviewer (a11y)" in prompt
    tasks = host.command("ideas.page", {"slug": slug})["plan"]["tasks"]
    assert [(t["kind"], t["role"]) for t in tasks] == [("design", "grunt"), ("a11y", "accessibility-reviewer"),
                                                       ("code", "grunt"), ("code", "grunt")]   # the leader never does a task (spec 152 A.2): a tag no seat takes goes to the project's role; an unknown tag is code
    assert [t["head"]["race"] for t in tasks] == ["elf", "elf", "elf", "elf"]      # a task wears its party's race (spec 99 §9.2): Design's elf; no task wears the leader's higher form (spec 152 A.2)
    from orkboard.core.idea_runner import IdeaRunner
    assert IdeaRunner._role(host.ideas.keeper, tasks[0])["slug"] == "grunt"
    assert goal_team.for_idea(host.ideas.root(), slug) == ["grunt", "accessibility-reviewer"]
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "plan"


def test_the_team_s_checks_go_in_the_spec_and_the_plan_where_they_apply_and_every_idea_s_always(host, monkeypatch):
    """A team sets how deep an idea is worked (realm/idea_checks.py): each checker's check, where it applies, adds its
    Done when line and its task after the work; where it does not, the spec says why; one set to every idea applies always."""
    seen = []

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):
        seen.append(prompt)
        if "turn it into" in prompt:
            return json.dumps({"tasks": [{"id": "a", "title": "Query", "brief": "Write it", "kind": "query", "tier": "laborer"},
                                         {"id": "b", "title": "Wire it", "brief": "Code it", "kind": "code", "tier": "warrior"}]}), 0.1, 10, "s"
        if "saved a goal" in prompt:
            return json.dumps({"summary": "ok", "questions": [], "metrics": []}), 0.1, 10, "s"
        return json.dumps({"gist": "A weekly report.", "why": "", "size": "S", "priority": "normal", "before": "", "questions": [],
                           "done_when": ["The report shows last week"],
                           "checks": [{"by": "accessibility-reviewer", "applies": False, "why": "It changes no screen"},
                                      {"by": "reviewer", "applies": False, "why": "small"}]}), 0.1, 10, "s"

    monkeypatch.setattr(jobs, "run_read", run_read)
    host.command("ideas.board_set", {"autostart": False})
    goal = host.command("ideas.goal_save", {"about": "Weekly numbers.", "craft": "data", "every": ["reviewer", "seo"],
                                            "team": ["grunt", "reviewer"]})["slug"]
    goal_team.set_team(host.ideas.root(), goal, ["grunt", "accessibility-reviewer", "reviewer", "sql"], ["reviewer"])          # a party made before keeps its team
    library.install(host.ideas.state_dir, ["accessibility-reviewer", "sql"])
    _wait(host, goal, goal=True)
    assert next(t for t in host.command("ideas.board")["tracks"] if t["slug"] == goal)["every"] == ["reviewer"]   # only the team's
    slug = host.command("ideas.add", {"text": "A weekly report", "track": goal, "hold": True})["slug"]
    host.command("ideas.read_now", {"slug": slug})
    _wait(host, slug)
    draft = next(p for p in seen if "write its spec" in p)
    assert "accessibility-reviewer (Accessibility reviewer): applies when the idea changes what people see or use" in draft
    assert "reviewer (Reviewer): applies to every idea" in draft and '"checks": [{"by"' in draft
    page = host.command("ideas.page", {"slug": slug})
    done = next(s["text"] for s in page["sections"] if s["name"] == "Done when")
    assert "The report shows last week" in done and "The change was reviewed and no blocking finding is left" in done   # every idea: always
    assert "accessibility check" not in done
    assert [(c["by"], c["applies"], c["why"]) for c in page["checks"]] == [
        ("accessibility-reviewer", False, "It changes no screen"), ("reviewer", True, "")]
    host.command("ideas.plan", {"slug": slug})
    _wait(host, slug)
    plan_prompt = next(p for p in seen if "turn it into" in p)
    assert 'Reviewer: a task tagged "review", after the work it checks' in plan_prompt and "Accessibility reviewer: a task" not in plan_prompt
    page = host.command("ideas.page", {"slug": slug})
    tasks = page["plan"]["tasks"]
    assert [(t["id"], t["title"], t["kind"], t["role"], t["after"]) for t in tasks] == [
        ("k1", "Query", "query", "sql", []), ("k2", "Wire it", "code", "grunt", []),
        ("k3", "Check: Reviewer", "review", "reviewer", ["k1", "k2"])]                  # the plan left it out: added, after the work
    assert [(c["by"], c["state"]) for c in page["checks"]] == [("accessibility-reviewer", ""), ("reviewer", "waiting")]


def test_a_goal_s_steps_run_as_its_leader_its_voice_and_model_and_the_taskmaster_leads_by_default(host, monkeypatch):
    from orkboard.realm import harnesses
    seen = []

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):
        seen.append({"prompt": prompt, "model": model})
        if "saved a goal" in prompt:
            return json.dumps({"summary": "ok", "questions": [], "metrics": [{"name": "weekly reports", "how": "count"}]}), 0.1, 10, "s"
        return json.dumps({"gist": "A report.", "why": "", "size": "S", "priority": "normal", "before": "", "questions": []}), 0.1, 10, "s"

    monkeypatch.setattr(jobs, "run_read", run_read)
    led = host.command("ideas.goal_save", {"about": "Weekly numbers.", "craft": "data", "leader": "analyst", "team": ["sql"]})["slug"]
    _wait(host, led, goal=True)
    assert seen[-1]["prompt"].startswith("You are Analyst, the leader of this goal's party")
    assert library.get("analyst").instruction in seen[-1]["prompt"]
    assert seen[-1]["model"] == harnesses.get("claude").pick("warrior")                  # the Analyst's tier, not the Taskmaster's
    idea = host.command("ideas.add", {"text": "A weekly report", "track": led, "hold": True})["slug"]
    host.command("ideas.read_now", {"slug": idea})
    _wait(host, idea)
    draft = next(c["prompt"] for c in seen if "write its spec" in c["prompt"])
    assert draft.startswith("You are Analyst")                                         # the idea's draft: its goal's leader's
    plain = host.command("ideas.goal_save", {"about": "Faster tests."})["slug"]          # no leader picked: the Taskmaster's
    _wait(host, plain, goal=True)
    assert seen[-1]["prompt"].startswith("You are the keeper") and seen[-1]["model"] == harnesses.get("claude").pick("elder")
    g = next(t for t in host.command("ideas.board")["tracks"] if t["slug"] == plain)
    assert g["leader"]["slug"] == "taskmaster" and g["leader"]["name"] == "Taskmaster"
    # spec 41 §8: the Taskmaster's own instruction goes before each step it runs (it went nowhere before)
    host.command("ideas.role_save", {"slug": "taskmaster", "name": "Taskmaster", "model": "elder", "max_parallel": 1,
                                     "instruction": "Answer in Russian."})
    again = host.command("ideas.goal_save", {"about": "Fewer flaky tests."})["slug"]
    _wait(host, again, goal=True)
    assert seen[-1]["prompt"].startswith("Answer in Russian.\n\nYou are the keeper")


def test_a_party_is_never_accepted_by_itself_but_the_person_can_still_ask_its_leader(host, monkeypatch):
    """Spec 50 §2.2: nothing accepts a party when its goals are all done (no model call); `ideas.goal_accept` stays, for a party
    with metrics written before, and its verdict is kept as history."""
    seen = []

    def run_read(harness, prompt, workdir, cancel, model="", env=None, resume="", timeout_s=0, **kw):
        seen.append(prompt)
        if "accept the goal or" in prompt:
            return json.dumps({"met": False, "verdict": "Reports ship, but nobody reads them yet.",
                               "metrics": [{"name": "weekly reports", "status": "not met", "why": "0 opened"}, {"name": "x", "status": "odd"}],
                               "next": ["Mail the report every Monday"]}), 0.1, 10, "s"
        return json.dumps({"summary": "ok", "questions": []}), 0.1, 10, "s"

    monkeypatch.setattr(jobs, "run_read", run_read)
    goal = host.command("ideas.goal_save", {"about": "Weekly numbers.", "craft": "product", "leader": "product-manager", "team": ["copywriter"],
                                            "metrics": [{"name": "weekly reports", "target": "10 opened"}]})["slug"]
    _wait(host, goal, goal=True)
    a = ideas.add_idea(host.ideas.root(), "A weekly report", goal, host.ideas.state_dir)
    ideas.save_state(host.ideas.state_dir, a, state="working")
    host.ideas._state_event(a)                                                          # seen working …
    ideas.save_state(host.ideas.state_dir, a, state="done")
    host.ideas._state_event(a)                                                          # … then done: the party's last goal
    _wait(host, goal, goal=True)
    assert not any("accept the goal or" in p for p in seen)                             # no model call: nothing accepts a party by itself
    g = next(t for t in host.command("ideas.board")["tracks"] if t["slug"] == goal)
    assert g["verdict"] is None
    assert host.command("ideas.goal_accept", {"slug": goal}) == {"ok": True}           # asked, from the party (a party with metrics of before)
    _wait(host, goal, goal=True)
    prompt = next(p for p in seen if "accept the goal or" in p)
    assert prompt.startswith("You are Product manager") and "weekly reports → 10 opened" in prompt and "A weekly report" in prompt
    g = next(t for t in host.command("ideas.board")["tracks"] if t["slug"] == goal)
    v = g["verdict"]
    assert v["met"] is False and v["by"] == "Product manager" and v["next"] == ["Mail the report every Monday"]
    assert v["metrics"] == [{"name": "weekly reports", "status": "not met", "why": "0 opened"}, {"name": "x", "status": "unknown", "why": ""}]
    from orkboard.realm import event_log
    from pathlib import Path
    assert [e for e in event_log.read(Path(host.repo_root)) if e["event"] == "goal_accepted"][-1]["met"] is False
    assert host.command("ideas.goal_accept", {"slug": goal}) == {"ok": True}           # asked again
    _wait(host, goal, goal=True)
    assert sum(1 for p in seen if "accept the goal or" in p) == 2


def test_a_check_skipped_before_the_plan_is_left_out_and_after_it_its_task_is_taken_out_before_it_runs(host):
    from orkboard.realm import idea_checks
    slug = host.command("ideas.goal_save", {"about": "Sync that holds.", "craft": "engineering", "leader": "architect",
                                            "team": ["grunt", "reviewer"]})["slug"]
    idea = host.command("ideas.add", {"text": "Retry a lost sync", "track": slug, "priority": "low"})["slug"]
    root, state = host.ideas.root(), host.ideas.state_dir
    keeper = host.ideas.keeper
    host.command("ideas.check_skip", {"slug": idea, "by": "reviewer"})                       # before a plan: left out of it
    kept = keeper.idea_checks(root, idea)
    assert kept == [{"by": "reviewer", "applies": True, "why": "", "skipped": True}]
    assert idea_checks.plan_lines(kept, keeper.team_checks(root, idea)) == ""
    tasks = [{"id": "k1", "title": "Retry", "kind": "code", "after": []}]
    assert idea_checks.with_check_tasks(tasks, kept, keeper.team_checks(root, idea), lambda *a: {"id": a[0], "kind": a[3]}) == tasks
    assert "reviewer" not in keeper.draft_prompt(root, idea)                                  # not asked of in the draft either
    host.command("ideas.check_skip", {"slug": idea, "by": "reviewer", "skip": False})         # taken again, before a plan
    assert not keeper.idea_checks(root, idea)[0].get("skipped")

    ideas.save_plan(state, idea, {"idea": idea, "todos": [], "tasks": [                       # a plan with its check task, after the work
        {"id": "k1", "title": "Retry", "kind": "code", "state": "merged", "after": []},
        {"id": "k2", "title": "Check: Reviewer", "kind": "review", "state": "waiting", "after": ["k1"]},
        {"id": "k3", "title": "Notes", "kind": "docs", "state": "waiting", "after": ["k2"]}]})
    host.command("ideas.check_skip", {"slug": idea, "by": "reviewer"})
    plan = ideas.plan(state, idea)
    assert [t["id"] for t in plan["tasks"]] == ["k1", "k3"] and plan["tasks"][1]["after"] == []      # what waited for it does not
    st = idea_checks.status(keeper.idea_checks(root, idea), keeper.team_checks(root, idea), plan["tasks"])
    assert st[0]["skipped"] and st[0]["state"] == "" and st[0]["task"] == ""
    with pytest.raises(CommandError, match="comes back with the goal's next plan"):
        host.command("ideas.check_skip", {"slug": idea, "by": "reviewer", "skip": False})
    with pytest.raises(CommandError, match="no such check"):
        host.command("ideas.check_skip", {"slug": idea, "by": "editor"})
    lines = [json.loads(x) for x in (fake_repo_events(host)).read_text().splitlines()]
    skipped = [x for x in lines if x.get("event") == "check_skipped"]
    assert [(x["by"], x["skipped"], x["task"]) for x in skipped] == [("reviewer", True, ""), ("reviewer", False, ""), ("reviewer", True, "k2")]


def fake_repo_events(host):
    from pathlib import Path
    from orkboard.realm import event_log
    return event_log.path(Path(host.repo_root))


# -- a Board in the code: its leaders are seated, its table is laid (spec 155 F) ----------------------------------------

def _page_party(host, slug, leader, recipe="tech"):
    root = host.ideas.root(False)
    (root / ideas.TRACKS).mkdir(parents=True, exist_ok=True)
    (root / ideas.TRACKS / f"{slug}.md").write_text(f"---\ntitle: {slug.title()}\nleader: {leader}\nrecipe: {recipe}\n---\n", encoding="utf-8")
    return root


def test_a_party_page_names_its_leader_and_the_leader_is_installed_and_wears_the_party_s_race(host):
    from orkboard.realm import first_open
    root = _page_party(host, "tech", "architect")
    state_dir = host.ideas.state_dir
    assert roles.role(state_dir, "architect") is None
    assert first_open.laid(state_dir, root) is True                       # the parties under the Board's root lay the table
    row = next(g for g in host.command("ideas.board", {})["tracks"] if g["slug"] == "tech")
    assert roles.role(state_dir, "architect") is not None
    assert row["leader"]["slug"] == "architect" and row["leader"]["head"]["race"] == "shaman"
    mapped = next(g for g in host.command("ideas.map", {})["goals"] if g["slug"] == "tech")
    assert mapped["leader"]["slug"] == "architect" and mapped["leader"]["head"]["race"] == "shaman"


