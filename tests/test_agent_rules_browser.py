"""Settings' *Let any AI tool work the Board* (spec 151 C.4), in a real browser on Orkboard's real host: shown under *This project* with its words, *Not now* leaving *Write the rules* alone,
and *Write the rules* writing the Board's rules and saying so. No AI tool is called."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import agent_rules, agent_rules_text as rules_text, first_open, project_kind  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.first_open_kit import desk, git_repo  # noqa: E402,F401  (fixture)
from tests.test_add_tool_browser import fill_hand  # noqa: E402

pytestmark = pytest.mark.browser


def project(d_factory, tmp_path):
    root = git_repo(tmp_path / "shop")
    d = d_factory(root)
    first_open.lay(d.host.ideas.state_dir)
    project_kind.keep(d.host.ideas.state_dir, "code")
    fill_hand(d.host, "claude")
    return root, d


def open_settings(pg):
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    pg.get_by_role("menuitem", name="Settings").click()
    box = pg.locator('[data-settings="agent-rules"]')
    box.wait_for(timeout=WAIT_MS)
    return box


def test_the_line_is_shown_with_its_words_not_now_leaves_the_yes_alone_and_the_yes_writes_the_rules(desk, tmp_path):
    root, d = project(desk, tmp_path)
    pg = d.open()
    box = open_settings(pg)
    text = box.inner_text()
    assert "LET ANY AI TOOL WORK THE BOARD" in text.upper() and "Writes the Board's rules into AGENTS.md and CLAUDE.md, so Claude Code, Codex, Cursor and others" in text
    assert "stop to ask you what is yours to decide." in text
    assert box.locator('[data-rules="write"]').inner_text() == "Write the rules" and box.locator('[data-rules="not-now"]').inner_text() == "Not now"
    box.locator('[data-rules="not-now"]').click()
    box.locator('[data-rules="not-now"]').wait_for(state="detached", timeout=WAIT_MS)
    assert box.locator('[data-rules="write"]').count() == 1 and not (root / "AGENTS.md").exists(), "Not now writes nothing and leaves the yes"
    box.locator('[data-rules="write"]').click()
    box.locator('[data-line="on"]').wait_for(timeout=WAIT_MS)
    assert f"The Board's rules are in this project (schema {rules_text.SCHEMA})" in box.locator('[data-line="on"]').inner_text() and box.locator('[data-rules="write"]').count() == 0
    board = d.host.ideas.state_dir / "board"
    assert agent_rules.has_rules(board) and agent_rules.check(board, d.host.ideas._decision_tree().wiki_rel) == []
    log = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=board, capture_output=True, text=True, check=True).stdout.strip()
    assert log == f"board: the Board's rules (schema {rules_text.SCHEMA})"
    assert not d.errors, d.errors


# -- F's question comes first (spec 151 C.4, F.1) -----------------------------------------------------------------------------------------

ASK = "Your goals, their specs, the leaders' words and the decisions will be public, in the repository's history: a later No does not take them back."


def with_remote(root, url, monkeypatch, code=200):
    from orkboard.realm import board_branch
    subprocess.run(["git", "remote", "add", "origin", url], cwd=root, check=True, capture_output=True)
    monkeypatch.setattr(board_branch, "http_status", lambda u: code)


def test_in_a_public_repository_the_line_shows_the_question_and_its_two_answers_not_write_the_rules(desk, tmp_path, monkeypatch):
    root, d = project(desk, tmp_path)
    with_remote(root, "https://github.com/acme/shop.git", monkeypatch)
    pg = d.open()
    box = open_settings(pg)
    box.locator('[data-in-code="publish"]').wait_for(timeout=WAIT_MS)
    assert box.locator('[data-line="ask"]').inner_text().strip() == ASK
    assert [b.inner_text().strip() for b in box.locator("[data-in-code-answer]").all()] == ["Publish the Board", "Keep the Board off the repository"]
    assert box.locator('[data-rules="write"]').count() == 0 and box.locator('[data-rules="not-now"]').count() == 0
    if os.environ.get("INCODE_SHOTS"):                                                              # a screenshot of the line, when asked for
        Path(os.environ["INCODE_SHOTS"]).mkdir(parents=True, exist_ok=True)
        box.scroll_into_view_if_needed()
        pg.screenshot(path=str(Path(os.environ["INCODE_SHOTS"]) / "wide-switch-line.png"))
    box.locator('[data-in-code-answer="publish"]').click()
    box.locator('[data-rules="write"]').wait_for(timeout=WAIT_MS)
    assert box.locator("[data-in-code-answer]").count() == 0 and box.get_attribute("data-state") == "ready"
    assert "in_code = true" in (root / "orkcraft.toml").read_text(encoding="utf-8") and not (root / "AGENTS.md").exists(), "the yes to F writes no rules"
    assert not d.errors, d.errors


def test_kept_off_the_line_says_the_rules_would_find_no_board_and_offers_nothing(desk, tmp_path, monkeypatch):
    root, d = project(desk, tmp_path)
    with_remote(root, "https://github.com/acme/shop.git", monkeypatch)
    pg = d.open()
    box = open_settings(pg)
    box.locator('[data-in-code-answer="off"]').click()
    box.locator('[data-line="off"]').wait_for(timeout=WAIT_MS)
    assert box.locator('[data-line="off"]').inner_text().strip() == "The Board is kept off this repository: the rules would find no Board"
    assert box.locator("button").count() == 0 and box.get_attribute("data-state") == "off"
    assert "in_code = false" in (root / "orkcraft.toml").read_text(encoding="utf-8") and not (root / "AGENTS.md").exists()
    assert not d.errors, d.errors


def test_a_remote_orkboard_cannot_read_asks_if_it_is_private_first(desk, tmp_path, monkeypatch):
    root, d = project(desk, tmp_path)
    with_remote(root, "git@gitlab.example.com:acme/shop.git", monkeypatch)
    pg = d.open()
    box = open_settings(pg)
    box.locator('[data-in-code="private"]').wait_for(timeout=WAIT_MS)
    assert box.locator('[data-line="ask"]').inner_text().strip() == "Is this repository private?"
    assert [b.inner_text().strip() for b in box.locator("[data-in-code-answer]").all()] == ["Private", "Public"]
    box.locator('[data-in-code-answer="public"]').click()
    box.locator('[data-in-code="publish"]').wait_for(timeout=WAIT_MS)
    assert box.locator('[data-line="ask"]').inner_text().strip() == ASK and not (root / "orkcraft.toml").exists(), "Public is no answer yet"
    assert not d.errors, d.errors
