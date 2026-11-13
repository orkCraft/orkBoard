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


# -- spec 90 E1: the overview beside the parts ----------------------------------------------------------------------------------------


def test_a_head_that_changed_a_manifest_is_read_again(repo):
    commit(repo, "client/package.json", json.dumps({"dependencies": {"react": "18"}}))
    commit(repo, "client/src/main.js", "export const x = 1;\n")
    project_map.ensure(state(repo), repo, "dev")
    commit(repo, "client/package.json", json.dumps({"dependencies": {"react": "18", "vite": "5"}}))
    got = project_map.ensure(state(repo), repo, "dev")
    client = next(c for c in got["overview"]["containers"] if c["path"] == "client")
    assert [s["name"] for s in client["stack"]] == ["React", "Vite"]


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
    assert set(got["goals"]) == {"waves"} and set(got["goals"]["waves"]) == {"title", "element", "hue"}
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


