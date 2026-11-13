"""Goal "The battle and the gate", stages D and F (decisions §303): `ideas.battle` and `ideas.gate_guards` on a fixture Board, read only: no model, no write, nothing in the snapshot.
Stage G (decisions §303.5): `ideas.gate_fix_goal` on a goal done whose way to main went red lays a Fix goal in one press, which its Undo removes.
Stage N3: `ideas.gate_guards` answers the §N read where the gate ran, on what the real way to dev and the real checks on the way to main leave."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from orkboard.core import idea_fix_stage, idea_undo
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, gate_config, goal_branch, harnesses, ideas, main_checks, spec_sections

LOG = "# Decisions\n\n## 1. First\nPlain.\n\n## 2. Second, the old card\nIt stands.\n\n## 3. Third\nAlso stands.\n"
PAGE = "---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: talk\nschema: 3\n---\n# {t}\n\n## Gist\nA goal.\n"
ENTRIES = ("ask", "call", "work_call", "_claude", "_claude_work", "board_ask", "read_now", "draft", "answer", "reword", "ripe_begin", "decide")


def _boom(*a, **k):
    raise AssertionError("a model was reached")


def _w(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture
def host(fake_repo, monkeypatch):
    h = Orkboard(fake_repo)
    root = h.ideas.root()
    ideas.add_track(root, "Tech")
    (root / ideas.IDEAS).mkdir(parents=True, exist_ok=True)
    for slug in ("goal", "skills"):
        (root / ideas.IDEAS / f"{slug}.md").write_text(PAGE.format(t=slug), encoding="utf-8")
        ideas.save_state(h.ideas.state_dir, slug, state="decided")
    way = spec_sections.record(h.ideas.state_dir, "goal")
    way["decision"] = {"number": 9, "title": "New", "text": "x", "conflicts": [{"number": 2, "point": "It goes against the old card", "answer": ""},
                                                                              {"number": 3, "point": "answered", "answer": "keep"}]}
    spec_sections.save_record(h.ideas.state_dir, "goal", way)
    _w(fake_repo, "docs/decisions.md", LOG)
    _w(fake_repo, "llm-wiki/general/pages/ideas/rests.md", "It rests on §2.\n")
    _w(fake_repo, "tests/test_red.py", '"""Guards decisions §2."""\n\ndef test_a():\n    assert 0\n\ndef test_b():\n    assert 0\n')
    _w(fake_repo, "tests/test_bare.py", '"""Nothing named."""\n\ndef test_c():\n    assert 0\n')
    _w(fake_repo, "tests/test_ok.py", '"""Guards decisions §3."""\n\ndef test_d():\n    pass\n')
    for entry in ENTRIES:
        if hasattr(h.ideas.keeper, entry):
            monkeypatch.setattr(h.ideas.keeper, entry, _boom)
    monkeypatch.setattr(harnesses.Harness, "ask", _boom)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _bytes(repo: Path, state: Path):
    return {p.as_posix(): hashlib.sha1(p.read_bytes()).hexdigest() for base in (repo, state) for p in sorted(base.rglob("*")) if p.is_file() and "/.git/" not in p.as_posix()}


def test_a_battle_lays_each_open_conflict_with_what_rests_on_it(host, fake_repo):
    before = _bytes(fake_repo, host.ideas.state_dir)
    got = host.command("ideas.battle", {"idea": "goal"})
    assert [a["number"] for a in got["against"]] == [2] and got["against"][0]["title"] == "Second, the old card"
    assert got["against"][0]["point"] == "It goes against the old card"
    assert got["against"][0]["rests"] == {"goals": ["rests"], "decisions": [], "tests": ["tests/test_red.py"]}
    assert got["cost"]["calls"] == 1 and "usd_high" in got["cost"]
    assert _bytes(fake_repo, host.ideas.state_dir) == before            # nothing written, no model reached (the keeper's entries fail)


def _red_dev(host):
    """A red on the way to dev as stage E wrote it, before the §N were kept with it (stage N3): no `named`."""
    goal_branch.update(host.ideas.state_dir, "goal", branch="goal/goal",
                       failing=["tests/test_red.py::test_a", "tests/test_red.py::test_b", "tests/test_bare.py::test_c"],
                       files=["tests/test_red.py", "tests/test_bare.py", "tests/test_ok.py"])


def _git(repo: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _python(repo: Path) -> None:
    """The repository's own Python, as the gate looks for it (untracked): ours, with pytest."""
    py = repo / ".venv/bin/python"
    py.parent.mkdir(parents=True)
    py.write_text(f'#!/bin/sh\nexec "{Path(sys.prefix) / "bin/python"}" "$@"\n', encoding="utf-8")
    py.chmod(0o755)


GUARD = '"""The goal\'s own test."""\n\n\ndef test_guarded():\n    """It holds decisions §2."""\n    assert False\n'      # fails, naming §2 in its own text
AGREES = '"""Guards decisions §3."""\n\n\ndef test_fine():\n    pass\n'                                                       # passes, naming §3


def _committed(repo: Path) -> None:
    """The decisions log and a gate of the project's own pytest (`always` one passing test), committed; the fixture's other test files stay untracked."""
    (repo / "orkcraft.toml").write_text('[gate]\nalways = ["tests/test_base.py"]\n', encoding="utf-8")
    _w(repo, "tests/test_base.py", "def test_base():\n    pass\n")
    _git(repo, "add", "orkcraft.toml", "docs/decisions.md", "tests/test_base.py")
    _git(repo, "commit", "-q", "-m", "the log and the gate")
    _python(repo)


def test_a_red_gate_on_the_way_to_dev_lays_the_decisions_its_tests_name_where_it_ran(host, fake_repo):
    """Stage N3, on what `goal_branch.to_dev` really leaves: the goal's branch adds a failing test naming `decisions §2` and a passing file naming §3, which the
    person's checkout (dev) never holds; the gate's worktree is gone when `ideas.gate_guards` is asked, and it answers them as the branch wrote them."""
    from orkboard.realm.idea_git import IdeaGit
    from tests.test_goal_branch import land_task
    _committed(fake_repo)
    _git(fake_repo, "checkout", "-q", "-B", "dev")                                        # the person's checkout is dev (the host may have made it already)
    g, state = IdeaGit(fake_repo), host.ideas.state_dir
    goal_branch.begin(g, state, "goal", {"tasks": []}, "dev", 1)
    land_task(g, "goal", "k1", "goal/goal", "tests/test_goal_guard.py", GUARD)
    land_task(g, "goal", "k2", "goal/goal", "tests/test_goal_agrees.py", AGREES)
    goal_branch.ready(state, "goal")
    with pytest.raises(goal_branch.GoalRed):
        goal_branch.to_dev(g, state, "goal", "dev")
    assert not (fake_repo / "tests/test_goal_guard.py").exists() and not (fake_repo / "tests/test_goal_agrees.py").exists()
    assert not [ln for ln in _git(fake_repo, "worktree", "list").splitlines() if "goal-dev-" in ln]
    before = _bytes(fake_repo, state)
    got = host.command("ideas.gate_guards", {"idea": "goal"})
    assert got["way"] == "dev"
    assert got["failing"] == [{"number": 2, "title": "Second, the old card", "ids": ["tests/test_goal_guard.py::test_guarded"]}]
    assert got["files"] == []
    assert got["agreeing"] == [{"number": 3, "title": "Third"}]
    assert got["cost"] == {"calls": None, "usd_high": None} == idea_fix_stage.COST       # its stage again has no cap in the runner: the seal says its cost is not known yet
    assert _bytes(fake_repo, state) == before                                             # read only: nothing written


def test_a_red_gate_on_the_way_to_main_lays_the_decisions_its_tests_name_in_its_trial(host, fake_repo):
    """Stage N3, on what the checks on the way to main really leave: they run in a trial worktree of their own (main's head with the goal's picks,
    realm/goal_main.py `trial`), never the person's checkout (main here, which lacks the goal's tests), and the trial is gone after."""
    import time
    from tests.test_goal_main import task
    _committed(fake_repo)
    _git(fake_repo, "branch", "-M", "main")
    _git(fake_repo, "branch", "-f", "dev", "main")                                         # the person's checkout is main; dev is cut from it
    task(host, fake_repo, "goal", "k1", {"tests/test_goal_guard.py": GUARD, "tests/test_goal_agrees.py": AGREES})
    ideas.save_state(host.ideas.state_dir, "goal", state="done")
    host.command("ideas.to_main_checks", {"idea": "goal"})
    for _ in range(3000):
        got = host.ideas._main_checks.get("goal")
        if got and not got["running"]:
            break
        time.sleep(0.02)
    tests = got["checks"][1]
    assert (tests["name"], tests["state"]) == ("Tests", "failed") and [f["id"] for f in tests["failures"]] == ["tests/test_goal_guard.py::test_guarded"]
    assert not (fake_repo / "tests/test_goal_guard.py").exists() and not [ln for ln in _git(fake_repo, "worktree", "list").splitlines() if "gate-main" in ln]
    shown = host.ideas.snapshot()["main_checks"]["goal"]                                   # the snapshot carries the steps, never what their tests name
    assert shown[1]["failures"] == tests["failures"] and "named" in tests and not [s for s in shown if "named" in s]
    got = host.command("ideas.gate_guards", {"idea": "goal"})
    assert got["way"] == "main" and got["cost"] is None
    assert got["failing"] == [{"number": 2, "title": "Second, the old card", "ids": ["tests/test_goal_guard.py::test_guarded"]}]
    assert got["files"] == [] and got["agreeing"] == [{"number": 3, "title": "Third"}]



# -- G: Fix it after dev, one press with its Undo ---------------------------------------------------------------------------------------------

def _red_main(host):
    """The goal done in dev, its way to main red: two failing tests, one in a file naming §2."""
    ideas.save_state(host.ideas.state_dir, "goal", state="done")
    host.ideas._main_checks["goal"] = {"running": False, "checks": [
        {"name": "The merge", "state": "passed", "words": ""},
        {"name": "Tests", "state": "failed", "words": "2 failed", "files": ["tests/test_red.py", "tests/test_bare.py", "tests/test_ok.py"],
         "failures": [{"id": "tests/test_red.py::test_a", "classification": "new"}, {"id": "tests/test_bare.py::test_c", "classification": "new"}]}]}


def _goal_files(host):
    """The done goal's page and state, byte for byte."""
    return idea_undo.snapshot(host.ideas.root(), host.ideas.state_dir, "goal")


def _pages(host):
    return sorted(p.name for p in (host.ideas.root() / ideas.IDEAS).glob("*.md"))


def test_fix_it_after_dev_lays_a_fix_goal_in_one_press_routed_to_tech(host):
    _red_main(host)
    done, pages = _goal_files(host), _pages(host)
    got = host.command("ideas.gate_fix_goal", {"idea": "goal", "from": "mat"})
    fix = got["fix"]
    page = ideas.idea_page(host.ideas.root(), fix)
    assert page.get("fixes") == "goal" and page.get("track") == "tech"
    assert page.title.startswith("Fix: tests/test_red.py::test_a, tests/test_bare.py::test_c")
    assert "The failing tests: tests/test_red.py::test_a, tests/test_bare.py::test_c\nThe goal whose way to main went red: goal" in page.section("Gist")
    st = ideas.state(host.ideas.state_dir, fix)
    assert st["state"] == "routed" and [r["party"] for r in st["route"]] == ["tech"]           # it waits on Tech's route: nothing drafts it, no model reached
    assert _goal_files(host) == done                                                           # the done goal's page and state byte for byte as before
    assert _pages(host) == sorted([*pages, f"{fix}.md"])
    played = [r for r in event_log.read(host.repo_root) if r["event"] == "move_played"]
    assert [(r["idea"], r["kind"], r["from"]) for r in played] == [("goal", "fix_goal", "mat")]
    kept = idea_undo.read(host.ideas.state_dir, "goal")
    assert kept["kind"] == "fix_goal" and kept["laid"] == fix and kept["before"] == {"page": None, "state": None}


def test_its_undo_removes_the_fix_goal_and_leaves_the_done_goal_as_it_was(host):
    _red_main(host)
    done, pages = _goal_files(host), _pages(host)
    fix = host.command("ideas.gate_fix_goal", {"idea": "goal", "from": "hand"})["fix"]
    assert host.command("ideas.undo", {"idea": "goal"})["kind"] == "fix_goal"
    assert ideas.idea_page(host.ideas.root(), fix) is None and not ideas.state_folder(host.ideas.state_dir, fix).exists()
    assert _pages(host) == pages and _goal_files(host) == done
    with pytest.raises(CommandError, match="Nothing to undo"):
        host.command("ideas.undo", {"idea": "goal"})


def test_fix_it_after_dev_is_refused_in_words_on_a_goal_not_in_dev_and_writes_nothing(host, fake_repo):
    _red_main(host)
    _red_dev(host)                                                                            # unmerged on its own branch: its stage runs again instead (H)
    before = _bytes(fake_repo, host.ideas.state_dir)
    with pytest.raises(CommandError, match="not in dev yet: Fix it runs its stage again"):
        host.command("ideas.gate_fix_goal", {"idea": "goal", "from": "mat"})
    with pytest.raises(CommandError, match="not in dev yet"):
        host.command("ideas.gate_fix_goal", {"idea": "skills", "from": "mat"})               # a goal not done
    assert _bytes(fake_repo, host.ideas.state_dir) == before
    assert not [r for r in event_log.read(host.repo_root) if r["event"] == "move_played"]

