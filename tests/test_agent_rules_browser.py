"""Settings' *Let any AI tool work the Board* (spec 151 C.4), in a real browser on Orkboard's real host: shown under *This project* with its words, *Not now* leaving *Write the rules* alone,
and *Write the rules* writing the Board's rules and saying so. No AI tool is called."""
from __future__ import annotations

import subprocess

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import agent_rules, first_open, project_kind  # noqa: E402
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
    assert "The Board's rules are in this project (schema 1)" in box.locator('[data-line="on"]').inner_text() and box.locator('[data-rules="write"]').count() == 0
    board = d.host.ideas.state_dir / "board"
    assert agent_rules.has_rules(board) and agent_rules.check(board, d.host.ideas._decision_tree().wiki_rel) == []
    log = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=board, capture_output=True, text=True, check=True).stdout.strip()
    assert log == "board: the Board's rules (schema 1)"
    assert not d.errors, d.errors
