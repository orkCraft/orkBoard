"""Spec 127 C.1 (docs/specs/127-the-fields-best-in-our-formats.md; decisions §205): the living specs' store, `realm/living_specs.py`: a capability a file in OpenSpec's shape with front matter,
read, listed, rendered, applied with OpenSpec's archive semantics, and given to a leader as text. No model."""
from __future__ import annotations

import subprocess

import pytest

from orkboard.realm import living_specs
from orkboard.realm.idea_git import BoardTree

FILE = """---
capability: Sign-in
parties: [design, tech]
goals: [add-lobby, magic-link]
updated: 2026-11-01
---

# Sign-in

## Purpose

How a player gets into a game.

## Requirements

### Requirement: Magic link

The product SHALL send a link that signs the player in.

#### Scenario: A link is asked for

- **WHEN** a player types their address and presses Send
- **THEN** a link arrives within a minute
"""


def req(name, text="The product SHALL do it.", *scenarios):
    return {"name": name, "text": text, "scenarios": [{"name": f"{name} works", "when": w, "then": t} for w, t in scenarios]}


@pytest.fixture
def board(tmp_path):
    return tmp_path / "wiki"


def put(board, cap, text):
    (board / "specs").mkdir(parents=True, exist_ok=True)
    (board / "specs" / f"{cap}.md").write_text(text, "utf-8")


# -- read and render ----------------------------------------------------------------------------------------------------------------------

def test_a_file_in_the_specs_shape_is_read(board):
    put(board, "sign-in", FILE)
    assert living_specs.read(board, "sign-in") == {
        "capability": "sign-in", "title": "Sign-in", "purpose": "How a player gets into a game.", "parties": ["design", "tech"], "goals": ["add-lobby", "magic-link"], "updated": "2026-11-01",
        "requirements": [{"name": "Magic link", "text": "The product SHALL send a link that signs the player in.",
                          "scenarios": [{"name": "A link is asked for", "when": "a player types their address and presses Send", "then": "a link arrives within a minute"}]}]}


def test_rendering_a_spec_gives_the_shape_and_reads_back_the_same(board):
    put(board, "sign-in", FILE)
    spec = living_specs.read(board, "sign-in")
    assert living_specs.render(spec) == FILE
    put(board, "again", living_specs.render({**spec, "capability": "again"}))
    assert living_specs.read(board, "again") == {**spec, "capability": "again"}




def test_a_file_without_front_matter_is_read_by_its_name_and_openspecs_and_steps_are_joined(board):
    put(board, "auth", "# Auth Specification\n\n## Purpose\nWho may come in.\n\n## Requirements\n### Requirement: Password\nThe system SHALL check it.\n\n"
                      "#### Scenario: Wrong\n- **WHEN** the password is wrong\n- **AND** it is tried twice\n- **THEN** the door stays shut\n- **AND** a note is made\n")
    spec = living_specs.read(board, "auth")
    assert spec["capability"] == "auth" and spec["title"] == "Auth Specification" and spec["purpose"] == "Who may come in." and spec["parties"] == [] and spec["updated"] == ""
    assert spec["requirements"][0]["scenarios"] == [{"name": "Wrong", "when": "the password is wrong and it is tried twice", "then": "the door stays shut and a note is made"}]




# -- list --------------------------------------------------------------------------------------------------------------------------------

def test_list_gives_each_capability_by_its_name_with_its_requirements_names(board):
    put(board, "sign-in", FILE)
    living_specs.apply(board, "billing", {"added": [req("Invoice"), req("Refund")]}, "pay", "product", title="Billing", purpose="How people pay.")
    assert living_specs.list_(board) == [
        {"capability": "billing", "title": "Billing", "purpose": "How people pay.", "parties": ["product"], "requirements": ["Invoice", "Refund"]},
        {"capability": "sign-in", "title": "Sign-in", "purpose": "How a player gets into a game.", "parties": ["design", "tech"], "requirements": ["Magic link"]}]
    assert living_specs.list_(board / "nowhere") == []


# -- apply -------------------------------------------------------------------------------------------------------------------------------



def test_apply_added_appends_modified_replaces_whole_by_name_and_removed_drops(board):
    put(board, "sign-in", FILE)
    got = living_specs.apply(board, "sign-in", {"added": [req("Password")], "modified": [req("magic  LINK", "The product SHALL send two links.")], "removed": []}, "two-links", "design")
    assert [r["name"] for r in got["requirements"]] == ["magic LINK", "Password"]                          # in its place, as the delta names it
    assert got["requirements"][0]["text"] == "The product SHALL send two links." and got["requirements"][0]["scenarios"] == []     # whole: its scenario went
    got = living_specs.apply(board, "sign-in", {"removed": ["PASSWORD", "no such one"]}, "no-passwords", "tech")
    assert len(got["requirements"]) == 1 and got["requirements"][0]["text"].endswith("two links.")
    assert got["goals"] == ["add-lobby", "magic-link", "two-links", "no-passwords"] and got["parties"] == ["design", "tech"]       # each joins once
    assert got["title"] == "Sign-in" and got["purpose"] == "How a player gets into a game."                                      # a title and a purpose kept are not changed
    assert living_specs.read(board, "sign-in") == got




def test_apply_removed_runs_before_added_and_a_new_capability_left_empty_is_not_written(board):
    got = living_specs.apply(board, "ghost", {"removed": ["Nothing"]}, "g", "tech", title="Ghost")
    assert got["requirements"] == [] and not (board / "specs" / "ghost.md").exists()
    put(board, "sign-in", FILE)
    got = living_specs.apply(board, "sign-in", {"removed": ["Magic link"], "added": [req("Magic link", "The product SHALL be new.")]}, "g", "tech")
    assert [r["text"] for r in got["requirements"]] == ["The product SHALL be new."]
    living_specs.apply(board, "sign-in", {"removed": ["Magic link"]}, "g", "tech")
    assert living_specs.read(board, "sign-in")["requirements"] == []                         # one kept stays, empty: its history is the file's






# -- text --------------------------------------------------------------------------------------------------------------------------------

def _three(board):
    living_specs.apply(board, "billing", {"added": [req("Invoice", "The product SHALL invoice.", ("a month ends", "an invoice is sent"))]}, "pay", "product", title="Billing", purpose="How people pay.")
    living_specs.apply(board, "sign-in", {"added": [req("Magic link", "The product SHALL send a link.")]}, "magic-link", "tech", title="Sign-in", purpose="How a player gets in.")
    living_specs.apply(board, "lobby", {"added": [req("Rooms", "The product SHALL list rooms.")]}, "add-lobby", "tech", title="Lobby", purpose="Where players meet.")




def test_text_puts_the_latest_updated_first_and_stays_within_its_chars(board):
    _three(board)
    old = living_specs.read(board, "lobby")
    put(board, "lobby", living_specs.render({**old, "updated": "2020-01-01"}))
    text = living_specs.text(board, "tech")
    assert text.index("Magic link") < text.index("Rooms")                              # Sign-in was updated today, Lobby in 2020
    for chars in (2500, 200, 120, 60):
        assert len(living_specs.text(board, "tech", chars)) <= chars
    big = {"added": [req(f"Requirement {i}", "The product SHALL " + "do a thing " * 30, ("when " * 30, "then " * 30)) for i in range(8)]}
    living_specs.apply(board, "huge", big, "g", "tech", title="Huge", purpose="Much.")
    assert len(living_specs.text(board, "tech")) <= 2500 and "Huge: Much." in living_specs.text(board, "tech")


# -- committed with the Board's pages ----------------------------------------------------------------------------------------------------------

def _run(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "t@x")
    _run(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".orkcraft/\n")
    (repo / "app.py").write_text("x = 1\n")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "start")
    return repo


def test_the_specs_are_committed_with_the_boards_pages(repo):
    tree = BoardTree(repo, repo / ".orkcraft", "llm-wiki/general", lambda: "dev")
    tree.ensure()
    living_specs.apply(tree.root(), "sign-in", {"added": [req("Magic link")]}, "g", "tech", title="Sign-in", purpose="In.")
    (tree.path / "stray.txt").write_text("not a page\n")
    tree.note("Tech", "edited", 0.0)
    got = tree.flush(force=True)
    assert got["commit"] and got["pages"] == 1 and got["held"] == ""
    assert _run(repo, "show", "--name-only", "--format=", "dev").splitlines() == ["llm-wiki/general/specs/sign-in.md"]
    assert "Magic link" in _run(repo, "show", "dev:llm-wiki/general/specs/sign-in.md")


