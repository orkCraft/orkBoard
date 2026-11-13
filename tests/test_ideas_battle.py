"""Goal "The battle and the gate", stages D and F (decisions §303): `ideas.battle` and `ideas.gate_guards` on a fixture Board, read only: no model, no write, nothing in the snapshot.
Stage G (decisions §303.5): `ideas.gate_fix_goal` on a goal done whose way to main went red lays a Fix goal in one press, which its Undo removes."""
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
    monkeypatch.setattr(harnesses.Harness, "call", _boom)
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


def test_a_goal_laid_by_the_skills_has_no_battle(host):
    assert host.command("ideas.battle", {"idea": "skills"})["against"] == []
    with pytest.raises(CommandError):
        host.command("ideas.battle", {"idea": "nope"})


def test_the_snapshot_holds_no_rests(host):
    assert "rests" not in json.dumps(host.command("ideas.board", {}), default=str)


def _red_dev(host):
    goal_branch.update(host.ideas.state_dir, "goal", branch="goal/goal",
                       failing=["tests/test_red.py::test_a", "tests/test_red.py::test_b", "tests/test_bare.py::test_c"],
                       files=["tests/test_red.py", "tests/test_bare.py", "tests/test_ok.py"])


def test_a_red_gate_on_the_way_to_dev_lays_the_decisions_its_tests_name(host, fake_repo):
    _red_dev(host)
    before = _bytes(fake_repo, host.ideas.state_dir)
    got = host.command("ideas.gate_guards", {"idea": "goal"})
    assert got["way"] == "dev"
    assert got["failing"] == [{"number": 2, "title": "Second, the old card", "ids": ["tests/test_red.py::test_a", "tests/test_red.py::test_b"]}]
    assert got["files"] == [{"file": "tests/test_bare.py", "ids": ["tests/test_bare.py::test_c"]}]
    assert got["agreeing"] == [{"number": 3, "title": "Third"}]
    assert got["cost"] == {"calls": None, "usd_high": None} == idea_fix_stage.COST       # its stage again has no cap in the runner: the seal says its cost is not known yet
    assert _bytes(fake_repo, host.ideas.state_dir) == before


def test_a_red_gate_on_the_way_to_main_reads_the_tests_step(host):
    host.ideas._main_checks["goal"] = {"running": False, "checks": [
        {"name": "The merge", "state": "passed", "words": ""},
        {"name": "Tests", "state": "failed", "words": "x", "files": ["tests/test_red.py", "tests/test_bare.py", "tests/test_ok.py"],
         "failures": [{"id": "tests/test_red.py::test_a", "classification": "new"}, {"id": "tests/test_bare.py::test_c", "classification": "new"}]}]}
    got = host.command("ideas.gate_guards", {"idea": "goal"})
    assert got["way"] == "main" and got["cost"] is None
    assert [f["number"] for f in got["failing"]] == [2] and got["files"][0]["file"] == "tests/test_bare.py" and [a["number"] for a in got["agreeing"]] == [3]


def test_an_all_green_gate_lays_nothing_failing(host):
    goal_branch.update(host.ideas.state_dir, "goal", branch="goal/goal", failing=[], files=["tests/test_ok.py"])
    got = host.command("ideas.gate_guards", {"idea": "goal"})
    assert got["failing"] == [] and got["files"] == [] and got["agreeing"] == [{"number": 3, "title": "Third"}]



def test_a_green_tests_step_as_the_writer_leaves_it_lays_the_agreeing_pile(host, fake_repo):
    from orkboard.realm.idea_git import IdeaGit
    def git(*a):
        return subprocess.run(["git", *a], cwd=fake_repo, check=True, capture_output=True, text=True).stdout.strip()
    (fake_repo / "orkcraft.toml").write_text('[gate]\nalways = ["tests/test_ok.py"]\n', encoding="utf-8")      # the gate's own pytest (no `run`) on the critical file
    git("add", "-A")
    git("commit", "-q", "-m", "the fixture's files")
    base = git("rev-parse", "HEAD")
    (fake_repo / "tests/test_ok.py").write_text('"""Guards decisions §3."""\n\ndef test_d():\n    pass\n\n# touched\n', encoding="utf-8")
    git("add", "tests/test_ok.py")
    git("commit", "-q", "-m", "touch the test")
    py = fake_repo / ".venv/bin/python"                                  # the repository's own Python, as the gate looks for it (untracked): ours, with pytest
    py.parent.mkdir(parents=True)
    py.write_text(f'#!/bin/sh\nexec "{Path(sys.prefix) / "bin/python"}" "$@"\n', encoding="utf-8")
    py.chmod(0o755)
    ok, _words, record = main_checks._checked(IdeaGit(fake_repo), fake_repo, base, gate_config.Check("Tests", gate=True), threading.Event(), 120, alone=True)
    assert ok, _words
    assert record["files"] == ["tests/test_ok.py"]
    host.ideas._main_checks["goal"] = {"running": False, "checks": [{"name": "The merge", "state": "passed", "words": ""},
                                                                       {"name": "Tests", "state": "passed", "words": "", **record}]}
    got = host.command("ideas.gate_guards", {"idea": "goal"})
    assert got["way"] == "main" and got["failing"] == [] and got["files"] == [] and got["agreeing"] == [{"number": 3, "title": "Third"}]


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


def test_its_undo_is_refused_once_the_fix_goal_changed(host):
    _red_main(host)
    fix = host.command("ideas.gate_fix_goal", {"idea": "goal", "from": "mat"})["fix"]
    ideas.save_state(host.ideas.state_dir, fix, state="talk")
    with pytest.raises(CommandError, match="It changed since: nothing undone"):
        host.command("ideas.undo", {"idea": "goal"})
    assert ideas.idea_page(host.ideas.root(), fix) is not None


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


def test_fix_it_after_dev_is_refused_where_no_test_failed(host, fake_repo):
    ideas.save_state(host.ideas.state_dir, "goal", state="done")
    before = _bytes(fake_repo, host.ideas.state_dir)
    with pytest.raises(CommandError, match="No test failed on its way to main"):
        host.command("ideas.gate_fix_goal", {"idea": "goal", "from": "mat"})
    assert _bytes(fake_repo, host.ideas.state_dir) == before
