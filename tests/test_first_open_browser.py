"""Spec 130 D (decisions §232.3, §232.8, §232.9), in a real browser on Orkboard's real host, with the system's folder dialog, `tools.detect` and the request faked: **the first open from an empty folder to the laid table**: no project → *Which project shall we work on?* → *A new, empty folder…* → git → the kind's line → an empty hand's tools card →
Test & add → *Go on to the parties* → Start → the table laid and the Orkmaster's line. The second project skips the tools; Settings has its two groups and the one line; the form of checkboxes is gone."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import folder_dialog  # noqa: E402
from orkboard.realm import first_open, project_kind, tool_hand  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.first_open_kit import desk, git_repo  # noqa: E402,F401  (fixture)
from tests.test_add_tool_browser import fill_hand  # noqa: E402

pytestmark = pytest.mark.browser
SETUP = ".fo-card"
ADD = '[data-lift="add-tool"]'


@pytest.fixture
def dialog(monkeypatch):
    """The system's folder dialog: answers with the folder `dialog["path"]` names."""
    picks = {"path": ""}
    monkeypatch.setattr(folder_dialog, "start", lambda begin="": "t1")
    monkeypatch.setattr(folder_dialog, "result", lambda token: {"state": "done", "path": picks["path"], "why": ""} if picks["path"] else {"state": "none", "path": "", "why": ""})
    return picks


def test_from_an_empty_folder_to_the_laid_table(desk, dialog, tmp_path):
    d = desk(None)
    pg = d.open()
    card = pg.locator(SETUP)
    card.wait_for(timeout=WAIT_MS)
    assert card.get_attribute("data-setup") == "project" and "Which project shall we work on?" in card.inner_text()
    assert "Which project shall we work on?" in pg.locator(".fo-bubble").inner_text()
    assert pg.locator('.frame[data-laid="0"]').count() == 1 and pg.locator(".shell-start, .gui-onb").count() == 0, "the start screen is the Orkmaster's first card"
    assert pg.locator(".hand-plus, .table-tabcell, .col-sec, .ork-die, .table-chair").count() == 0
    assert pg.locator("[data-empty-slot]").count() == 1

    home = tmp_path / "games"
    home.mkdir()
    dialog["path"] = str(home)
    card.locator('[data-new="1"]').click()
    name = card.locator('[data-new-folder="1"] input')
    name.wait_for(timeout=WAIT_MS)
    name.fill("skyhop")
    card.locator('[data-new-folder="1"] button[type=submit]').click()

    pg.locator('[data-setup="git"]').wait_for(timeout=WAIT_MS)
    assert (home / "skyhop").is_dir() and "No git in skyhop yet. Start git here?" in pg.locator(".fo-bubble").inner_text()
    pg.locator('[data-start-git="1"]').click()

    kind = pg.locator('[data-setup="kind"]')
    kind.wait_for(timeout=WAIT_MS)
    assert "What is it for?" in kind.inner_text()
    kind.locator('[data-kinds="1"]').click()
    kind.locator('[data-kind="game"]').click()

    add = pg.locator(ADD)
    add.wait_for(timeout=WAIT_MS)
    assert "is-lit" in pg.locator("[data-empty-slot]").get_attribute("class")
    pg.locator('[data-test-add="1"]').wait_for(timeout=WAIT_MS)
    pg.locator('[data-test-add="1"]').click()
    pg.locator(f'{ADD} [data-turned="1"]').wait_for(timeout=WAIT_MS)
    assert d.asked == ["claude"] and d.host.machine.main_tool == "claude"
    pg.locator(f'{ADD} [data-done="1"]').click()

    start = pg.locator('.parties.ork-card [data-act="start"]')
    start.wait_for(timeout=WAIT_MS)
    assert first_open.laid(d.host.projects.current().ideas.state_dir, d.host.projects.current().root) is False
    start.click()

    pg.locator('.frame[data-laid="1"] .table-tabcell').first.wait_for(timeout=WAIT_MS)
    pg.locator(".hand-plus").wait_for(timeout=WAIT_MS)
    assert "The table is laid. What shall we make first? Play the + card." in pg.locator(".fo-bubble").inner_text()
    assert pg.locator(SETUP).count() == 0
    assert first_open.kept(d.host.projects.current().ideas.state_dir) is True
    assert not d.errors, d.errors


def test_a_folder_opened_from_the_card_and_a_recent_one(desk, dialog, tmp_path):
    shop = git_repo(tmp_path / "shop")
    d = desk(None)
    pg = d.open()
    pg.locator(SETUP).wait_for(timeout=WAIT_MS)
    dialog["path"] = str(shop)
    pg.locator('[data-open-folder="1"]').click()
    pg.locator('[data-setup="kind"]').wait_for(timeout=WAIT_MS)
    assert "Right?" in pg.locator('[data-setup="kind"]').inner_text()
    assert not d.errors, d.errors


def test_a_dialog_closed_leaves_a_path_to_type_and_a_refusal_is_said_on_the_card(desk, dialog, tmp_path):
    d = desk(None)
    pg = d.open()
    pg.locator(SETUP).wait_for(timeout=WAIT_MS)
    pg.locator('[data-open-folder="1"]').click()
    path = pg.locator('input[aria-label="The folder\'s path"]')
    path.wait_for(timeout=WAIT_MS)
    path.fill(str(tmp_path / "no-such-folder"))
    path.press("Enter")
    pg.locator(f"{SETUP} [role=alert]").wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_ctrl_o_opens_the_same_dialog(desk, dialog, tmp_path):
    shop = git_repo(tmp_path / "shop")
    d = desk(None)
    pg = d.open()
    pg.locator(SETUP).wait_for(timeout=WAIT_MS)
    dialog["path"] = str(shop)
    pg.keyboard.press("Control+o")
    pg.locator('[data-setup="kind"]').wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_the_second_project_skips_the_tools(desk, tmp_path):
    d = desk(git_repo(tmp_path / "second", "project.godot", "[app]\n"))
    fill_hand(d.host, "claude")
    pg = d.open()
    kind = pg.locator('[data-setup="kind"]')
    kind.wait_for(timeout=WAIT_MS)
    kind.locator('[data-yes="1"]').click()
    pg.locator(".parties.ork-card").wait_for(timeout=WAIT_MS)
    assert pg.locator(ADD).count() == 0 and project_kind.kept(d.host.ideas.state_dir) == "game"
    assert not d.errors, d.errors


def test_settings_has_its_two_groups_and_the_one_line_where_the_rest_went(desk, tmp_path):
    d = desk(git_repo(tmp_path / "shop"))
    first_open.lay(d.host.ideas.state_dir)
    project_kind.keep(d.host.ideas.state_dir, "code")
    fill_hand(d.host, "claude")
    pg = d.open()
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    pg.get_by_role("menuitem", name="Settings").click()
    project, computer = pg.locator('[data-group="project"]'), pg.locator('[data-group="computer"]')
    project.wait_for(timeout=WAIT_MS)
    for words in ("Start plans by themselves", "A result that holds lands in dev by itself", "Push after merging"):
        assert words in project.inner_text(), words
    computer.locator('[data-settings="awake"]').wait_for(timeout=WAIT_MS)
    for words in ("Keep the computer awake", "Your phone", "Download today's logs"):
        assert words.upper() in computer.inner_text().upper(), words
    moved = pg.locator('[data-settings="moved"]').inner_text()
    assert "AI tools are in your hand: press a potion, or the empty slot beside them." in moved and "Parties, their size and their AI tool: the empty chair, or a party's Edit." in moved
    assert not d.errors, d.errors


def test_settings_is_reachable_with_no_project_and_the_files_are_not_offered(desk):
    d = desk(None)
    pg = d.open()
    pg.locator(SETUP).wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    assert pg.get_by_role("menuitem", name="Files").count() == 0
    pg.get_by_role("menuitem", name="Settings").click()
    pg.locator('[data-group="computer"]').wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_a_tool_added_keeps_its_place_with_no_form_of_checkboxes(desk, tmp_path):
    d = desk(git_repo(tmp_path / "shop"))
    pg = d.open()
    pg.locator('[data-setup="kind"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(".gui-onb, .gui-onb__table").count() == 0
    assert tool_hand.hand(d.host.machine) == []
    assert not d.errors, d.errors
