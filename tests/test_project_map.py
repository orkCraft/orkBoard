"""Spec 89 A (docs/specs/89-the-tech-lens-system.md §1–§4): the Architect's *System*. A snapshot of the parts after a landing, from the
task's worktree, never raising into the runner; the first from a worktree of dev's head, removed after; the newest 60 kept; the areas and
the layout kept across snapshots (a new part at its column's end, a gone one in place until *Rearrange*), the caps and the stack; the parts
and uses new, changed and gone since a commit with their goals and *By you*; the commands' answers and their events. Real git
repositories (tests/test_commit_goal.py's), no model."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import code_map, event_log, project_map
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)
from tests.test_idea_runner import plan_of, reviewing, runner_of, tasks_of, town, wait_idle, wait_task  # noqa: F401  (the fixture)

LOOP = "from src.ui import hud\n"
HUD = "VALUE = 1\n"


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "dev")


def worktrees(repo: Path) -> list[str]:
    return [ln for ln in git(repo, "worktree", "list", "--porcelain").splitlines() if ln.startswith("worktree ")]


def remove(path: Path, name: str, message: str) -> str:
    git(path, "rm", "-q", "-r", name)
    git(path, "commit", "-q", "-m", message)
    return git(path, "rev-parse", "HEAD")


# -- §1 the snapshots ------------------------------------------------------------------------------------------------------------------

def test_a_landing_keeps_the_parts_from_the_tasks_worktree_before_it_is_removed(town, monkeypatch):
    read_from = []
    real = code_map.parts

    def spy(tree):
        read_from.append((Path(tree), Path(tree).is_dir(), Path(tree) == town.repo))
        return real(tree)
    monkeypatch.setattr(project_map.code_map, "parts", spy)
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    task = tasks_of(town)["k1"]
    snap = project_map.read(town.state, task["commit"])
    assert snap is not None and snap["commit"] == task["commit"] and snap["at"]
    assert {p["path"] for p in snap["parts"]} == {".", "pkg", "tests"}
    (tree, existed, is_root), = read_from
    assert existed and not is_root and not tree.exists()                      # the task's worktree, removed after
    assert project_map.layout(town.state)["parts"].keys() == {".", "pkg", "tests"}


def test_a_result_merged_at_review_keeps_its_snapshot_too(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    wait_task(runner, "k1", "review")
    sha = runner.merge("demo", "k1")
    assert project_map.read(town.state, sha) is not None and git(town.repo, "rev-parse", "dev") == sha


def test_a_snapshot_that_fails_never_troubles_the_landing_and_says_so(town, monkeypatch):
    def broken(tree):
        raise OSError("disk full")
    monkeypatch.setattr(project_map.code_map, "parts", broken)
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    task = tasks_of(town)["k1"]
    assert task["state"] == "merged" and project_map.read(town.state, task["commit"]) is None
    failed = [e for e in event_log.read(town.repo) if e["event"] == "map_snapshot_failed"]
    assert len(failed) == 1 and failed[0]["why"] == "disk full" and task["commit"].startswith(failed[0]["commit"])


def test_the_first_snapshot_is_read_from_a_worktree_of_devs_head_and_the_worktree_goes(repo):
    commit(repo, "src/game/loop.py", LOOP)
    commit(repo, "src/ui/hud.py", HUD)
    (repo / "src" / "ui" / "draft.py").write_text("from src.game import loop\n")             # the working tree's own: never read
    before = worktrees(repo)
    snap = project_map.ensure(state(repo), repo, "dev")
    assert snap["commit"] == head(repo) and project_map.kept(state(repo)) == [head(repo)]
    parts = {p["path"]: p for p in snap["parts"]}
    assert parts["src/ui"]["files"] == ["hud.py"] and parts["src/game"]["uses"] == ["src/ui"] and parts["src/ui"]["used_by"] == ["src/game"]
    assert worktrees(repo) == before and not (state(repo) / "maps" / "tree").exists()
    assert project_map.ensure(state(repo), repo, "dev") == snap                                 # kept: read again, no worktree


def test_a_head_that_changed_no_source_file_takes_the_parts_kept_without_a_worktree(repo, monkeypatch):
    commit(repo, "src/game/loop.py", LOOP)
    first = project_map.ensure(state(repo), repo, "dev")
    commit(repo, "notes.md", "# Notes\n")

    def no_worktree(*args):
        raise AssertionError("a worktree was made")
    monkeypatch.setattr(project_map, "_git", no_worktree)
    got = project_map.ensure(state(repo), repo, "dev")
    assert got["commit"] == head(repo) != first["commit"] and got["parts"] == first["parts"]
    assert got["overview"] == first["overview"] is not None
    assert project_map.ensure(state(repo), repo, "nope") is None                               # no such branch: no map


# -- spec 90 E1: the overview beside the parts ----------------------------------------------------------------------------------------

def test_a_snapshot_keeps_the_overview_beside_its_parts(repo):
    commit(repo, "server/package.json", json.dumps({"dependencies": {"express": "4"}, "scripts": {"start": "node src/index.js"}}))
    commit(repo, "server/src/index.js", "const app = require('express')();\napp.get('/api/x', f);\napp.listen(3000);\n")
    snap = project_map.ensure(state(repo), repo, "dev")
    kept = json.loads((project_map.folder(state(repo)) / f"{snap['commit']}.json").read_text())
    assert kept["overview"] == snap["overview"] and set(snap["overview"]) == {"containers", "links", "shared"}
    server = next(c for c in snap["overview"]["containers"] if c["path"] == "server")
    assert server["stack"] == [{"name": "Express", "role": "server"}] and server["parts"] == ["server/src"]


def test_an_old_snapshot_reads_as_no_overview_and_gets_it_on_the_next_ensure(repo):
    commit(repo, "client/package.json", json.dumps({"dependencies": {"react": "18"}}))
    commit(repo, "client/src/main.js", "export const x = 1;\n")
    snap = project_map.ensure(state(repo), repo, "dev")
    path = project_map.folder(state(repo)) / f"{snap['commit']}.json"
    old = {k: v for k, v in json.loads(path.read_text()).items() if k != "overview"}           # as spec 89 kept it
    path.write_text(json.dumps(old))
    order = project_map.kept(state(repo))
    assert project_map.read(state(repo), snap["commit"])["overview"] is None
    got = project_map.ensure(state(repo), repo, "dev")
    client, = got["overview"]["containers"]                                                   # no code of the root's own: no Root
    assert client["stack"] == [{"name": "React", "role": "UI"}] and got["parts"] == old["parts"]
    assert project_map.read(state(repo), snap["commit"])["overview"] == got["overview"] and project_map.kept(state(repo)) == order
    assert not (state(repo) / "maps" / "tree").exists()


def test_a_head_that_changed_a_manifest_is_read_again(repo):
    commit(repo, "client/package.json", json.dumps({"dependencies": {"react": "18"}}))
    commit(repo, "client/src/main.js", "export const x = 1;\n")
    project_map.ensure(state(repo), repo, "dev")
    commit(repo, "client/package.json", json.dumps({"dependencies": {"react": "18", "vite": "5"}}))
    got = project_map.ensure(state(repo), repo, "dev")
    client = next(c for c in got["overview"]["containers"] if c["path"] == "client")
    assert [s["name"] for s in client["stack"]] == ["React", "Vite"]


def test_the_newest_sixty_are_kept(tmp_path):
    shas = [f"{n:040x}" for n in range(1, 63)]
    for sha in shas:
        project_map.snapshot(tmp_path, tmp_path, sha)
    kept = project_map.kept(tmp_path)
    assert len(kept) == 60 and kept[0] == shas[-1] and set(kept) == set(shas[2:])
    assert project_map.newest(tmp_path)["commit"] == shas[-1]
    with pytest.raises(ValueError):
        project_map.snapshot(tmp_path, tmp_path, "HEAD")


# -- §2 the layout ------------------------------------------------------------------------------------------------------------------

def cols(lay: dict) -> dict[str, list[str]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for path, v in lay["parts"].items():
        out.setdefault(v["column"], []).append((v["row"], path))
    return {c: [p for _r, p in sorted(out.get(c, []))] for c in lay["columns"]}


def test_the_areas_are_the_first_folders_under_the_common_prefix_and_the_layout_stays(tmp_path):
    lay = project_map.place(tmp_path, [".", "app/src/net", "app/src/ui", "app/src/game", "app/src/game/ai"])
    assert lay["prefix"] == ["app", "src"]
    assert cols(lay) == {".": ["."], "game": ["app/src/game", "app/src/game/ai"], "net": ["app/src/net"], "ui": ["app/src/ui"]}
    lay = project_map.place(tmp_path, [".", "app/src/ui", "app/src/game", "app/src/game/ai", "app/src/ui/menu", "app/src/audio",
                                       "app/src/game/ai/paths"])
    assert cols(lay) == {".": ["."], "game": ["app/src/game", "app/src/game/ai", "app/src/game/ai/paths"],
                         "net": ["app/src/net"], "ui": ["app/src/ui", "app/src/ui/menu"], "audio": ["app/src/audio"]}   # gone net in place
    assert json.loads((tmp_path / "maps" / "system" / "layout.json").read_text())["parts"]["app/src/net"] == {"column": "net", "row": 0}
    again = project_map.rearrange(tmp_path, [".", "app/src/ui", "app/src/game", "app/src/audio"])
    assert cols(again) == {".": ["."], "audio": ["app/src/audio"], "game": ["app/src/game"], "ui": ["app/src/ui"]}


def test_beyond_eight_areas_the_smallest_fold_into_other_and_a_new_area_goes_there(tmp_path):
    paths = [f"{a}/x{n}" for a, k in zip("abcdefghij", (5, 4, 4, 3, 3, 3, 2, 1, 1, 1)) for n in range(k)]
    lay = project_map.place(tmp_path, paths)
    assert lay["columns"] == ["a", "b", "c", "d", "e", "f", "g", project_map.OTHER]
    assert cols(lay)[project_map.OTHER] == ["h/x0", "i/x0", "j/x0"]
    lay = project_map.place(tmp_path, [*paths, "k/x0"])
    assert cols(lay)[project_map.OTHER][-1] == "k/x0" and len(lay["columns"]) == 8
    small = project_map.place(tmp_path / "two", [f"{a}/x" for a in "abcdefgh"])                   # eight areas: no Other yet
    small = project_map.place(tmp_path / "two", [f"{a}/x" for a in "abcdefghi"])                 # a ninth: the smallest becomes Other
    assert len(small["columns"]) == 8 and cols(small)[project_map.OTHER] == ["h/x", "i/x"]


def test_a_column_shows_fourteen_cards_and_stacks_the_least_changed(tmp_path):
    paths = [f"src/a/p{n:02}" for n in range(18)] + ["src/b"]
    lay = project_map.place(tmp_path, paths)
    parts = {p: {"count": 1, "uses": [], "used_by": []} for p in paths}
    recent = {"src/a/p00": "2026-01-01T00:00:00+00:00", **{f"src/a/p{n:02}": f"2026-10-{n + 1:02}T00:00:00+00:00" for n in range(1, 18)}}
    a, b = project_map.table(lay, parts, {"src/a/p00"}, recent)
    assert len(a["parts"]) == project_map.CARDS and [c["row"] for c in a["parts"]] == sorted(c["row"] for c in a["parts"])
    assert [c["path"] for c in a["stack"]] == ["src/a/p01", "src/a/p02", "src/a/p03", "src/a/p04"]        # the oldest changed, by row
    assert a["parts"][0]["path"] == "src/a/p00"                                                       # changed since the look: a card
    assert (a["name"], b["name"], b["stack"]) == ("a", "b", [])
    assert set(a["parts"][0]) == {"path", "name", "count", "uses", "used_by", "row", "gone"} and a["parts"][0]["name"] == "p00"


# -- §3 what changed ----------------------------------------------------------------------------------------------------------------

def test_the_parts_and_uses_new_changed_and_gone_since_a_look_with_their_goals(repo):
    commit(repo, "src/ui/hud.py", HUD)
    commit(repo, "src/old/legacy.py", "X = 0\n")
    look = project_map.ensure(state(repo), repo, "dev")["commit"]
    commit(repo, "README.md", "# A game\n")                                        # after the look, no snapshot of its own
    seen = head(repo)
    land(repo, "waves", "k1", {"src/game/loop.py": LOOP})
    project_map.ensure(state(repo), repo, "dev")
    commit(repo, "src/ui/hud.py", "VALUE = 2\n", "tune the hud")                  # the person's own
    remove(repo, "src/old", "drop the old code")
    project_map.ensure(state(repo), repo, "dev")
    got = project_map.changed(state(repo), repo, seen, "dev")                       # read as the snapshot at or before it: the look's
    assert got["since"] == look and got["commit"] == head(repo)
    marks = {p: (c["kind"], c["goal"], c["task"]) for p, c in got["parts"].items()}
    assert marks == {"src/game": ("new", "waves", "k1"), "src/ui": ("changed", "", ""), "src/old": ("gone", "", "")}
    assert all(c["at"] and len(c["sha"]) == 40 for c in got["parts"].values())
    assert [(u["from"], u["to"], u["kind"], u["goal"]) for u in got["uses"]] == [("src/game", "src/ui", "new", "waves")]
    assert project_map.changed(state(repo), repo, head(repo), "dev")["parts"] == {}               # the look is now: nothing
    assert project_map.changed(state(repo), repo, "", "dev") == project_map.nothing(head(repo))
    assert project_map.changed(state(repo), repo, "2001-01-01T00:00", "dev")["since"] == ""       # before every commit: nothing marked
    assert project_map.changed(state(repo), repo, "f" * 40, "dev")["parts"] == {}


def test_no_snapshot_at_or_before_the_look_marks_nothing(repo):
    first = commit(repo, "src/ui/hud.py", HUD)
    commit(repo, "src/game/loop.py", LOOP)
    project_map.ensure(state(repo), repo, "dev")
    got = project_map.changed(state(repo), repo, first, "dev")
    assert got["since"] == "" and got["parts"] == {} and got["uses"] == []


# -- §4 the commands ----------------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(repo):
    from orkboard.gui.board_host import Orkboard
    h = Orkboard(repo)
    yield h
    h.close()


def test_ideas_system_answers_the_columns_what_changed_and_the_goals(host, repo):
    commit(repo, "src/ui/hud.py", HUD)
    commit(repo, "src/old/legacy.py", "X = 0\n")
    look = host.command("ideas.system", {"party": "tech"})                         # no look yet: the first snapshot, nothing marked
    assert set(look) == {"commit", "short", "at", "ref", "since", "columns", "changed", "uses_changed", "goals", "overview"}
    assert look["changed"] == {} and look["since"] == "" and look["ref"] == "dev" and look["short"] == look["commit"][:7]
    assert [c["name"] for c in look["columns"]] == ["old", "ui"]
    land(repo, "waves", "k1", {"src/game/loop.py": LOOP})
    remove(repo, "src/old", "drop the old code")
    got = host.command("ideas.system", {"party": "tech", "since": look["commit"]})
    assert got["since"] == look["commit"] and got["commit"] == head(repo)
    assert {p: (c["kind"], c["goal"], c["task"]) for p, c in got["changed"].items()} == {
        "src/game": ("new", "waves", "k1"), "src/old": ("gone", "", "")}
    assert set(got["changed"]["src/game"]) == {"kind", "goal", "task", "at"}
    by = {c["name"]: c for c in got["columns"]}
    assert [p["path"] for p in by["old"]["parts"]] == ["src/old"] and by["old"]["parts"][0]["gone"] is True     # crumbles in its place
    ov = got["overview"]                                                            # spec 90 E1: the architecture beside the columns
    assert set(ov) == {"containers", "links", "shared", "parts"} and ov["links"] == [] and ov["shared"] == []
    root, = ov["containers"]                                                        # no manifest: the root's own code
    assert (root["path"], root["name"], root["parts"], root["gone"]) == (".", "Root", ["src/game", "src/ui"], ["src/old"])
    assert root["layers"] == [{"role": "", "parts": ["src/game"]}, {"role": "face", "parts": ["src/ui"]}]
    assert ov["parts"]["src/game"] == {"path": "src/game", "name": "game", "count": 1, "uses": ["src/ui"], "used_by": [], "gone": False}
    assert ov["parts"]["src/old"]["gone"] is True and set(ov["parts"]) >= set(got["changed"])   # the marks by the same paths
    assert by["game"]["parts"][0] == {"path": "src/game", "name": "game", "count": 1, "uses": ["src/ui"], "used_by": [], "row": 0, "gone": False}
    assert got["uses_changed"] == [{"from": "src/game", "to": "src/ui", "kind": "new", "goal": "waves", "task": "k1",
                                    "at": got["changed"]["src/game"]["at"]}]
    assert set(got["goals"]) == {"waves"} and set(got["goals"]["waves"]) == {"title", "element"}
    opened = [e for e in event_log.read(repo) if e["event"] == "map_opened"]
    assert [(e["lens"], e["party"], e["changed"]) for e in opened] == [("system", "tech", 0), ("system", "tech", 2)]
    assert opened[0]["hours"] is None and isinstance(opened[1]["hours"], float) and opened[1]["parts"] == 3

    part = host.command("ideas.system_part", {"path": "src/game", "since": look["commit"], "party": "tech"})
    assert part == {"path": "src/game", "name": "game", "count": 1, "files": ["loop.py"], "uses": ["src/ui"], "used_by": [], "gone": False,
                    "kind": "new", "since": look["commit"], "goals": part["goals"],
                    "changes": [{"goal": "waves", "task": "k1", "at": part["changes"][0]["at"], "made": "edit src/game/loop.py"}]}
    gone = host.command("ideas.system_part", {"path": "src/old", "since": look["commit"]})
    assert gone["gone"] is True and gone["kind"] == "gone" and gone["changes"][0]["goal"] == "" and gone["changes"][0]["made"] == ""
    plain = host.command("ideas.system_part", {"path": "src/ui"})
    assert plain["kind"] == "" and plain["changes"] == [] and plain["used_by"] == ["src/game"]
    pressed = [e for e in event_log.read(repo) if e["event"] == "map_part_pressed"]
    assert [(e["lens"], e["changed"], e["goals"]) for e in pressed] == [("system", "new", 1), ("system", "gone", 1), ("system", "", 0)]
    from orkboard.gui.board_host import CommandError
    with pytest.raises(CommandError, match="That part is not in the project"):
        host.command("ideas.system_part", {"path": "src/nowhere"})

    again = host.command("ideas.system_rearrange", {"since": look["commit"]})
    assert [c["name"] for c in again["columns"]] == ["game", "ui"] and again["changed"] == got["changed"]   # the gone part's place taken away
    assert len([e for e in event_log.read(repo) if e["event"] == "map_opened"]) == 2                          # Rearrange is no opening


def test_ideas_system_with_no_dev_branch_is_an_empty_map(tmp_path):
    from orkboard.gui.board_host import Orkboard
    r = tmp_path / "bare"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    commit(r, "a.py", "A = 1\n")
    h = Orkboard(r)
    h.ideas.save_settings({"merge_into": "nothing-here"})
    try:
        got = h.command("ideas.system", {})
        assert got["commit"] == "" and got["columns"] == [] and got["changed"] == {}
    finally:
        h.close()
