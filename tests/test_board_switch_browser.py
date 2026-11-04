"""Settings' *Keep the Board in the repository* (spec 137 E), in a real browser on Orkboard's real host: shown under *This project* with its words,
a public repository refused in words, *Turn it on* writing `[board]`, and *Not now* leaving *Turn it on* alone."""
from __future__ import annotations

import subprocess

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import board_switch  # noqa: E402
from orkboard.realm import board_branch, first_open, project_kind  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.first_open_kit import desk, git_repo  # noqa: E402,F401  (fixture)
from tests.test_add_tool_browser import fill_hand  # noqa: E402

pytestmark = pytest.mark.browser


def project(d_factory, tmp_path):
    root = git_repo(tmp_path / "shop")
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:acme/shop.git"], cwd=root, check=True)
    d = d_factory(root)
    first_open.lay(d.host.ideas.state_dir)
    project_kind.keep(d.host.ideas.state_dir, "code")
    fill_hand(d.host, "claude")
    return root, d


def open_settings(pg):
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    pg.get_by_role("menuitem", name="Settings").click()
    box = pg.locator('[data-settings="board-switch"]')
    box.wait_for(timeout=WAIT_MS)
    return box


def test_a_public_repository_is_refused_in_words_then_a_private_one_is_turned_on(desk, tmp_path, monkeypatch):
    root, d = project(desk, tmp_path)
    status = {"code": 200}
    monkeypatch.setattr(board_switch, "http_status", lambda url: status["code"])
    pg = d.open()
    box = open_settings(pg)
    text = box.inner_text()
    assert "KEEP THE BOARD IN THE REPOSITORY" in text.upper() and "orkboard/board" in text and "The repository must be private." in text
    box.locator('[data-board="on"]').click()
    box.locator('[data-line="said"]').wait_for(timeout=WAIT_MS)
    assert "goes only to a private repository" in box.inner_text() and board_branch.read_config(root) is None
    status["code"] = 404
    box.locator('[data-board="on"]').click()
    box.locator('[data-line="on"]').wait_for(timeout=WAIT_MS)
    assert "orkboard/board" in box.locator('[data-line="on"]').inner_text() and box.locator('[data-board="on"]').count() == 0
    assert board_branch.read_config(root) == board_branch.BoardConfig("origin", "orkboard/board")
    assert not d.errors, d.errors


def test_not_now_leaves_turn_it_on_alone(desk, tmp_path):
    root, d = project(desk, tmp_path)
    pg = d.open()
    box = open_settings(pg)
    box.locator('[data-board="not-now"]').click()
    box.locator('[data-board="not-now"]').wait_for(state="detached", timeout=WAIT_MS)
    assert box.locator('[data-board="on"]').count() == 1 and board_branch.read_config(root) is None
    assert not d.errors, d.errors
