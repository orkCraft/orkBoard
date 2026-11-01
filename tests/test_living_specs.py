"""Spec 127 C.1 (docs/specs/127-the-fields-best-in-our-formats.md; decisions §205): the living specs' store, `realm/living_specs.py`: a capability a file in OpenSpec's shape with front matter,
read, listed, rendered, applied with OpenSpec's archive semantics, and given to a leader as text. No model."""
from __future__ import annotations

import datetime as dt
import subprocess

import pytest

from orkboard.realm import doc_formats, living_specs
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


def test_a_spec_with_no_requirement_and_no_scenario_reads_back_the_same(board):
    spec = {"capability": "empty", "title": "Empty", "purpose": "", "parties": [], "goals": [], "updated": "2026-11-02", "requirements": []}
    put(board, "empty", living_specs.render(spec))
    assert living_specs.read(board, "empty") == spec
    two = {**spec, "capability": "two", "title": "Two", "requirements": [req("A", "The product SHALL a.", ("x", "y"), ("p", "q")), req("B")]}
    put(board, "two", living_specs.render(two))
    assert living_specs.read(board, "two") == two


def test_a_file_without_front_matter_is_read_by_its_name_and_openspecs_and_steps_are_joined(board):
    put(board, "auth", "# Auth Specification\n\n## Purpose\nWho may come in.\n\n## Requirements\n### Requirement: Password\nThe system SHALL check it.\n\n"
                      "#### Scenario: Wrong\n- **WHEN** the password is wrong\n- **AND** it is tried twice\n- **THEN** the door stays shut\n- **AND** a note is made\n")
    spec = living_specs.read(board, "auth")
    assert spec["capability"] == "auth" and spec["title"] == "Auth Specification" and spec["purpose"] == "Who may come in." and spec["parties"] == [] and spec["updated"] == ""
    assert spec["requirements"][0]["scenarios"] == [{"name": "Wrong", "when": "the password is wrong and it is tried twice", "then": "the door stays shut and a note is made"}]


def test_what_is_no_spec_is_not_read_and_a_bad_name_is_none(board):
    put(board, "readme", "# Specs\n\nThis folder holds the specs.\n")
    assert living_specs.read(board, "readme") is None and living_specs.read(board, "missing") is None
    assert living_specs.read(board, "../x") is None and living_specs.read(board, "Sign In") is None and living_specs.read(board, "") is None
    assert living_specs.list_(board) == []


# -- list --------------------------------------------------------------------------------------------------------------------------------

def test_list_gives_each_capability_by_its_name_with_its_requirements_names(board):
    put(board, "sign-in", FILE)
    living_specs.apply(board, "billing", {"added": [req("Invoice"), req("Refund")]}, "pay", "product", title="Billing", purpose="How people pay.")
    assert living_specs.list_(board) == [
        {"capability": "billing", "title": "Billing", "purpose": "How people pay.", "parties": ["product"], "requirements": ["Invoice", "Refund"]},
        {"capability": "sign-in", "title": "Sign-in", "purpose": "How a player gets into a game.", "parties": ["design", "tech"], "requirements": ["Magic link"]}]
    assert living_specs.list_(board / "nowhere") == []


# -- apply -------------------------------------------------------------------------------------------------------------------------------

def test_apply_adds_to_a_new_capability_and_writes_the_file(board):
    got = living_specs.apply(board, "sign-in", {"added": [req("Magic link", "The product SHALL send a link.", ("a player presses Send", "a link arrives"))]}, "magic-link", "tech",
                             title="Sign-in", purpose="How a player gets into a game.")
    assert (board / "specs" / "sign-in.md").is_file() and not list((board / "specs").glob(".*"))
    assert got == living_specs.read(board, "sign-in")
    assert (got["title"], got["purpose"], got["parties"], got["goals"], got["updated"]) == ("Sign-in", "How a player gets into a game.", ["tech"], ["magic-link"], dt.date.today().isoformat())
    assert [r["name"] for r in got["requirements"]] == ["Magic link"]
    meta, _ = doc_formats.front_matter((board / "specs" / "sign-in.md").read_text("utf-8"))
    assert meta["capability"] == "Sign-in" and meta["parties"] == ["tech"]


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


def test_a_name_added_that_is_there_is_modified_in_its_place_and_added_twice_too(board):
    put(board, "sign-in", FILE)
    got = living_specs.apply(board, "sign-in", {"added": [req("Other"), req("Magic Link", "The product SHALL do better."), req("Other", "The product SHALL be other.")]}, "g", "tech")
    assert [r["name"] for r in got["requirements"]] == ["Magic Link", "Other"] and got["requirements"][0]["text"] == "The product SHALL do better."
    assert got["requirements"][1]["text"] == "The product SHALL be other."


def test_apply_removed_runs_before_added_and_a_new_capability_left_empty_is_not_written(board):
    got = living_specs.apply(board, "ghost", {"removed": ["Nothing"]}, "g", "tech", title="Ghost")
    assert got["requirements"] == [] and not (board / "specs" / "ghost.md").exists()
    put(board, "sign-in", FILE)
    got = living_specs.apply(board, "sign-in", {"removed": ["Magic link"], "added": [req("Magic link", "The product SHALL be new.")]}, "g", "tech")
    assert [r["text"] for r in got["requirements"]] == ["The product SHALL be new."]
    living_specs.apply(board, "sign-in", {"removed": ["Magic link"]}, "g", "tech")
    assert living_specs.read(board, "sign-in")["requirements"] == []                         # one kept stays, empty: its history is the file's


def test_apply_refuses_a_capability_that_is_no_slug(board):
    for bad in ("Sign In", "../x", "", "a/b", "x" * 61):
        with pytest.raises(ValueError):
            living_specs.apply(board, bad, {"added": [req("A")]}, "g", "tech")
    assert not (board / "specs").exists()


def test_slug(board):
    assert living_specs.slug("Sign-in & Out!") == "sign-in-out" and living_specs.slug("  ") == "" and len(living_specs.slug("word " * 40)) <= 60
    assert not living_specs.slug("-x-").startswith("-")


# -- text --------------------------------------------------------------------------------------------------------------------------------

def _three(board):
    living_specs.apply(board, "billing", {"added": [req("Invoice", "The product SHALL invoice.", ("a month ends", "an invoice is sent"))]}, "pay", "product", title="Billing", purpose="How people pay.")
    living_specs.apply(board, "sign-in", {"added": [req("Magic link", "The product SHALL send a link.")]}, "magic-link", "tech", title="Sign-in", purpose="How a player gets in.")
    living_specs.apply(board, "lobby", {"added": [req("Rooms", "The product SHALL list rooms.")]}, "add-lobby", "tech", title="Lobby", purpose="Where players meet.")


def test_text_gives_every_capability_one_line_then_the_requirements_of_the_partys_capabilities(board):
    _three(board)
    text = living_specs.text(board, "tech")
    assert text.startswith("- Billing: How people pay.\n- Lobby: Where players meet.\n- Sign-in: How a player gets in.")
    assert "Magic link: The product SHALL send a link." in text and "Rooms: The product SHALL list rooms." in text
    assert "Invoice" not in text                                                       # Billing is Product's: its requirements are not Tech's
    assert "WHEN a month ends THEN an invoice is sent" in living_specs.text(board, "product")
    assert living_specs.text(board, "")[:60].count("\n") == 2 and "Magic link" not in living_specs.text(board, "")      # a call with no party: the lines alone
    assert living_specs.text(board / "none", "tech") == ""


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


def test_the_specs_in_the_wiki_move_with_the_pages_into_the_tree(repo):
    legacy = repo / "llm-wiki" / "general"
    living_specs.apply(legacy, "sign-in", {"added": [req("Magic link")]}, "g", "tech", title="Sign-in", purpose="In.")
    _run(repo, "branch", "dev")
    tree = BoardTree(repo, repo / ".orkcraft", "llm-wiki/general", lambda: "dev")
    tree.ensure()
    got = tree.move(legacy)
    assert got["commit"] and living_specs.read(tree.root(), "sign-in")["title"] == "Sign-in" and not (legacy / "specs" / "sign-in.md").exists()
