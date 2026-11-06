"""Spec 150 G (decisions §254.8; before it spec 130 D, decisions §232.3, §232.8, §232.9), in a real browser on Orkboard's real host, with the system's folder dialog, `tools.detect` and the request faked: **the first open as four cards**. From an empty folder the room is dark,
the Orkmaster in its middle holding four backs; each card flies to its place and the place appears as it lands: the AI tools at the potions (*Use Claude Code*), the project at the ring (a new, empty folder, git, its release branch), the table (its kind, the parties
as empty chairs, a chair pressed seats its leader, Start), the hand (the + card's card open, its corners lit one at a time). The second project holds fewer; reduced motion lays each place at once. Settings has its two groups and the one line; the form of
checkboxes is gone."""
from __future__ import annotations

import os

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
ROOM = '.frame[data-room="1"]'
SHOTS = os.environ.get("ORKBOARD_SHOTS", "")          # a folder: the five moments are saved there at 1280 x 800 (the spec's screenshots)


def shot(pg, name):
    if SHOTS:
        pg.wait_for_timeout(700)
        pg.screenshot(path=os.path.join(SHOTS, f"{name}.png"))


def landed(pg, place):
    pg.locator(f'[data-place="{place}"].is-landed').wait_for(state="attached", timeout=WAIT_MS)


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
    pg.locator(f"{ROOM} .fo-fan").wait_for(timeout=WAIT_MS)
    assert pg.locator(".fo-fan > .ork-card-back").count() == 4, "four backs held"
    assert "I'm the Orkmaster. Four cards, and we start." in pg.locator(".fo-room-bubble").inner_text()
    assert pg.locator('.fo-om img.ork-race__head.big').count() == 1, "the Orkmaster in the room's middle, 48 x 44"
    assert pg.locator(".hand-plus, .table-tabcell, .col-sec, .ork-die, .table-chair, .frame-table, .frame-hand").count() == 0, "the room dark: no table, no hand"
    assert pg.locator(".shell-start, .gui-onb").count() == 0
    assert pg.locator('[data-place].is-landed').count() == 0, "no place before its card lands"
    shot(pg, "0-the-room")

    # 1 · the potions: the AI tools
    add = pg.locator(ADD)
    add.wait_for(timeout=WAIT_MS)
    landed(pg, "potions")
    assert pg.locator('[data-place="ring"].is-landed, [data-place="table"].is-landed').count() == 0
    assert pg.locator(".fo-fan > .ork-card-back").count() == 3
    assert "is-lit" in pg.locator('[data-place="potions"] [data-empty-slot]').get_attribute("class")
    use = pg.locator('[data-test-add="1"]')
    pg.wait_for_function("(s) => document.querySelector(s) && !document.querySelector(s).disabled", arg='[data-test-add="1"]', timeout=WAIT_MS)
    assert use.inner_text().strip().upper() == "USE CLAUDE CODE", "a ready tool is one press"
    shot(pg, "1-to-the-potions")
    use.click()
    pg.locator(f'{ADD} [data-turned="1"]').wait_for(timeout=WAIT_MS)
    assert d.asked == ["claude"] and d.host.machine.main_tool == "claude"
    pg.locator('[data-place="potions"] .hand-pot[data-provider="claude"]').wait_for(timeout=WAIT_MS)
    pg.locator(f'{ADD} [data-done="1"]').click()

    # 2 · the ring: the project, its git, its release branch
    card = pg.locator('[data-setup="project"]')
    card.wait_for(timeout=WAIT_MS)
    landed(pg, "ring")
    assert pg.locator('[data-place="ring"] .ork-portal-ring').count() == 1 and pg.locator('[data-place="table"].is-landed').count() == 0
    assert "Which project shall we work on?" in card.inner_text() and "Which project shall we work on?" in pg.locator(".fo-room-bubble").inner_text()
    home = tmp_path / "games"
    home.mkdir()
    dialog["path"] = str(home)
    card.locator('[data-new="1"]').click()
    name = card.locator('[data-new-folder="1"] input')
    name.wait_for(timeout=WAIT_MS)
    name.fill("skyhop")
    card.locator('[data-new-folder="1"] button[type=submit]').click()
    pg.locator('[data-setup="git"]').wait_for(timeout=WAIT_MS)
    assert (home / "skyhop").is_dir() and "No git in skyhop yet. Start git here?" in pg.locator(".fo-room-bubble").inner_text()
    pg.locator('[data-start-git="1"]').click()
    ring = pg.locator('[data-setup="ring"]')
    ring.wait_for(timeout=WAIT_MS)
    branch = ring.locator("[data-release-branch]")
    branch.wait_for(timeout=WAIT_MS)
    state_dir = d.host.projects.current().ideas.state_dir
    now = branch.get_attribute("data-release-branch")
    assert now and "RELEASE BRANCH" in ring.inner_text().upper() and "GitHub: later" in ring.inner_text()
    branch.click()
    pg.locator(f'.fo-branch__list [data-branch="{now}"]').wait_for(timeout=WAIT_MS)
    shot(pg, "2-to-the-ring")
    pg.locator(f'.fo-branch__list [data-branch="{now}"]').click()
    assert pg.locator(".fo-branch__list").count() == 0
    ring.locator('[data-ring-go="1"]').click()

    # 3 · the table: its kind, the parties as empty chairs, Start
    kind = pg.locator('[data-setup="kind"]')
    kind.wait_for(timeout=WAIT_MS)
    landed(pg, "table")
    assert "What is it for?" in kind.inner_text()
    kind.locator('[data-kinds="1"]').click()
    kind.locator('[data-kind="game"]').click()
    start = pg.locator('[data-setup="parties"] [data-act="start"]')
    start.wait_for(timeout=WAIT_MS)
    chairs = pg.locator('[data-place="table"] .fo-chair')
    chairs.first.wait_for(timeout=WAIT_MS)
    assert chairs.count() == pg.locator('[data-place="table"] .fo-chair .ork-chair.is-empty').count() > 0, "every chair empty"
    assert start.is_disabled(), "Start waits for a leader seated"
    chairs.first.click()
    seated = pg.locator('[data-place="table"] .fo-chair.is-seated')
    seated.wait_for(timeout=WAIT_MS)
    assert seated.locator("img.ork-race__head").count() == 1 and seated.locator(".fo-chair__line").inner_text().strip()
    assert pg.locator(".fo-fan > .ork-card-back").count() == 1, "the hand's card is held still"
    shot(pg, "3-the-table")
    assert first_open.laid(state_dir, d.host.projects.current().root) is False
    start.click()

    # 4 · the hand: the + card's card open, its corners lit one at a time
    pg.locator('.frame[data-laid="1"] .table-tabcell').first.wait_for(timeout=WAIT_MS)
    field = pg.locator(".hand-field")
    field.wait_for(timeout=WAIT_MS)
    lit = field.locator('[data-corner="rune"][data-first-lit]')
    lit.wait_for(timeout=WAIT_MS)
    assert field.locator("[data-first-lit]").count() == 1, "one corner lit at a time"
    shot(pg, "4-the-hand")
    field.locator('[data-corner="rune"]').click()
    pg.locator('.hand-pick--rune [role=radio]').nth(2).click()
    field.locator('[data-corner="type"][data-first-lit]').wait_for(timeout=WAIT_MS)
    assert field.locator("[data-first-lit]").count() == 1
    assert pg.locator(ROOM).count() == 0 and pg.locator(SETUP).count() == 0
    assert first_open.kept(state_dir) is True
    assert not d.errors, d.errors


def test_a_second_project_holds_fewer_and_its_places_are_there(desk, tmp_path):
    d = desk(git_repo(tmp_path / "second", "project.godot", "[app]\n"))
    fill_hand(d.host, "claude")
    pg = d.open()
    pg.locator(f"{ROOM} .fo-fan").wait_for(timeout=WAIT_MS)
    assert pg.locator(".fo-fan > .ork-card-back").count() == 2, "the table's and the hand's: the tools and the project are set"
    assert pg.locator('[data-place="potions"].is-landed').count() == 1 and pg.locator('[data-place="ring"].is-landed').count() == 1
    assert pg.locator(ADD).count() == 0
    kind = pg.locator('[data-setup="kind"]')
    kind.wait_for(timeout=WAIT_MS)
    landed(pg, "table")
    kind.locator('[data-yes="1"]').click()
    pg.locator('[data-setup="parties"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(ADD).count() == 0 and project_kind.kept(d.host.ideas.state_dir) == "game"
    assert not d.errors, d.errors


def test_reduced_motion_lays_each_place_at_once(desk, tmp_path):
    d = desk(git_repo(tmp_path / "shop"))
    d.pg.emulate_media(reduced_motion="reduce")
    d.pg.add_init_script("window.__flew = 0; new MutationObserver((m) => { if (document.querySelector('.fo-flyer')) window.__flew++; }).observe(document, {subtree: true, childList: true});")
    pg = d.open()
    pg.locator(ADD).wait_for(timeout=WAIT_MS)                   # at once: no beat, no flight
    landed(pg, "potions")
    pg.locator(f'{ADD} [data-close="1"]').click()               # closed with no tool: the project's step
    pg.locator('[data-setup="kind"]').wait_for(timeout=WAIT_MS)
    landed(pg, "table")
    assert pg.locator('[data-place="ring"].is-landed').count() == 1
    assert pg.evaluate("window.__flew") == 0, "nothing flew"
    assert not d.errors, d.errors


def test_a_project_with_parties_of_its_own_is_laid_at_once(desk, tmp_path):
    from orkboard.realm import ideas
    root = git_repo(tmp_path / "made")
    ideas.add_track(root, "Tech")
    d = desk(root)
    fill_hand(d.host, "claude")
    pg = d.open()
    pg.locator('.frame[data-laid="1"] .frame-table').wait_for(timeout=WAIT_MS)
    assert pg.locator(ROOM).count() == 0 and pg.locator(".fo-fan").count() == 0
    assert not d.errors, d.errors


def test_a_folder_opened_from_the_card_and_a_recent_one(desk, dialog, tmp_path):
    shop = git_repo(tmp_path / "shop")
    d = desk(None)
    fill_hand(d.host, "claude")
    pg = d.open()
    pg.locator(SETUP).wait_for(timeout=WAIT_MS)
    dialog["path"] = str(shop)
    pg.locator('[data-open-folder="1"]').click()
    pg.locator('[data-ring-go="1"]').click()
    pg.locator('[data-setup="kind"]').wait_for(timeout=WAIT_MS)
    assert "Right?" in pg.locator('[data-setup="kind"]').inner_text()
    assert not d.errors, d.errors


def test_a_dialog_closed_leaves_a_path_to_type_and_a_refusal_is_said_on_the_card(desk, dialog, tmp_path):
    d = desk(None)
    fill_hand(d.host, "claude")
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
    fill_hand(d.host, "claude")
    pg = d.open()
    pg.locator(SETUP).wait_for(timeout=WAIT_MS)
    dialog["path"] = str(shop)
    pg.keyboard.press("Control+o")
    pg.locator('[data-setup="ring"]').wait_for(timeout=WAIT_MS)
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
    pg.locator(f"{ROOM} .fo-menu").wait_for(timeout=WAIT_MS)                 # the room's corner holds the Orkmaster's menu
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    assert pg.get_by_role("menuitem", name="Files").count() == 0
    pg.get_by_role("menuitem", name="Settings").click()
    pg.locator('[data-group="computer"]').wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_a_tool_added_keeps_its_place_with_no_form_of_checkboxes(desk, tmp_path):
    d = desk(git_repo(tmp_path / "shop"))
    pg = d.open()
    pg.locator(ADD).wait_for(timeout=WAIT_MS)                                  # the tools' card first, at the potions' place
    assert pg.locator(".gui-onb, .gui-onb__table").count() == 0
    assert tool_hand.hand(d.host.machine) == []
    assert not d.errors, d.errors
