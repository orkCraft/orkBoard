"""Spec 168 G2 (docs/specs/168-the-window-played-as-a-card-games-table.md, decisions §283.16.11): a goal's work before and after, where the code keeps both: Tech's System by commit (the snapshot at or before the goal's first commit's parent, the one at or before
its last), Design's shots (the picture of the goal's task, the one of another goal's before it). Real git projects, tests/test_commit_goal.py's."""
from __future__ import annotations

import json

from orkboard.realm import goal_before_after, ideas, project_map
from tests.test_commit_goal import git, land, repo, state  # noqa: F401  (the fixture)
from tests.test_goal_screens import app


def part(path, count, uses=()):
    return {"path": path, "count": count, "uses": list(uses), "used_by": [], "files": []}


def test_the_system_before_and_after_has_the_parts_the_goal_touched_new_changed_and_gone(repo):
    s = state(repo)
    start = git(repo, "rev-parse", "dev")
    project_map._keep(s, start, "", [part("src", 1), part("old", 1), part(".", 1)], {})
    (repo / "old").mkdir()
    (repo / "old" / "gone.py").write_text("x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "old")
    start = git(repo, "rev-parse", "dev")
    project_map._keep(s, start, "", [part("src", 1), part("old", 1), part(".", 1)], {})
    sha, _ = land(repo, "pay", "k1", {"src/a.py": "a\n", "lib/b.py": "b\n"})
    git(repo, "rm", "-q", "-f", "old/gone.py")
    git(repo, "commit", "-q", "-m", "drop old")
    gone = git(repo, "rev-parse", "dev")
    plan = ideas.plan(s, "pay")
    plan["tasks"].append({"id": "k2", "title": "Task k2", "state": "merged", "commit": gone, "subjects": ["drop old"]})
    (ideas.state_folder(s, "pay") / "plan.json").write_text(json.dumps(plan))
    project_map._keep(s, gone, "", [part("src", 2, ["lib"]), part("lib", 1), part(".", 1)], {})
    got = goal_before_after.system(s, repo, "pay")
    assert got["kind"] == "parts" and got["none"] == "" and got["before"]["commit"] == start and got["after"]["commit"] == gone and got["after"]["short"] == gone[:7]
    rows = {r["path"]: r for r in got["parts"]}
    assert rows["lib"]["change"] == "new" and rows["lib"]["before"] is None and rows["lib"]["after"] == {"count": 1, "uses": []}
    assert rows["src"]["change"] == "changed" and rows["src"]["before"]["count"] == 1 and rows["src"]["after"]["count"] == 2 and rows["src"]["uses_new"] == ["lib"]
    assert rows["old"]["change"] == "gone" and rows["old"]["after"] is None
    assert [r["change"] for r in got["parts"]] == ["new", "gone", "changed"], "new first, then gone, then changed"
    assert sha != gone


def test_with_no_snapshot_from_before_the_goal_nothing_is_compared_and_it_says_so_and_with_none_after_it_says_that(repo):
    s = state(repo)
    sha, _ = land(repo, "pay", "k1", {"src/a.py": "a\n"})
    got = goal_before_after.system(s, repo, "pay")
    assert got["before"] is None and got["after"] is None and "not kept" in got["none"] and got["parts"] == []
    project_map._keep(s, sha, "", [part("src", 1)], {})
    got = goal_before_after.system(s, repo, "pay")
    assert got["before"] is None and got["after"]["commit"] == sha and "from before this goal" in got["none"] and [r["path"] for r in got["parts"]] == ["src"]
    assert goal_before_after.system(s, repo, "nobody") is None


def shot(s, slug, task, at):
    plan = ideas.plan(s, slug)
    t = next(x for x in plan["tasks"] if x["id"] == task)
    t["shot"] = {"id": f"{task}-shot-r1", "file": "shot.png", "w": 800, "h": 600, "at": at}
    (ideas.state_folder(s, slug) / "plan.json").write_text(json.dumps(plan))


def test_the_shots_before_and_after_of_a_screen_the_goal_changed_are_its_tasks_picture_and_the_one_of_another_goal_before_it(repo):
    app(repo)
    s = state(repo)
    land(repo, "first", "k1", {"src/pages/Pay.jsx": "export default () => <b>one</b>;\n"})
    shot(s, "first", "k1", "2026-10-01T10:00:00")
    land(repo, "second", "k1", {"src/pages/Pay.jsx": "export default () => <b>two</b>;\n"})
    shot(s, "second", "k1", "2026-10-02T10:00:00")
    got = goal_before_after.shots(s, repo, "second")
    assert [x["screen"] for x in got] == ["pay"]
    assert got[0]["after"]["goal"] == "second" and got[0]["after"]["id"] == "k1-shot-r1" and got[0]["before"]["goal"] == "first"
    only = goal_before_after.shots(s, repo, "first")
    assert only[0]["after"]["goal"] == "first" and only[0]["before"] is None, "nothing was kept before the first: none is made up"


def test_a_screen_the_goal_changed_with_no_picture_has_none_and_of_reads_the_parties_whose_craft_keeps_both(repo):
    app(repo)
    s = state(repo)
    land(repo, "plain", "k1", {"src/pages/Pay.jsx": "export default () => <b>x</b>;\n"})
    got = goal_before_after.of(s, repo, "plain", "dev", {"design": "design", "tech": "tech", "product": "product"})
    assert got["design"] == {"kind": "screens", "screens": [{"screen": "pay", "name": "Pay", "path": "/pay", "before": None, "after": None}]}
    assert set(got) == {"design", "tech"} and got["tech"]["kind"] == "parts"
