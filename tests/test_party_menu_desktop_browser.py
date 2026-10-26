"""Spec 90 part D on the desktop (docs/specs/90-what-the-first-look-said.md §5, §7 D; decisions §105.5), in a real browser at 1 440 × 900 against the project test's stub host: a party's row in the
left column has a menu, opened by a right click or by its **…** (hidden at rest, shown on hover and on focus): *About this party*, *Edit the party*, *Remove party…*; *Remove party…* opens spec 80's
question, unchanged; the Orkmaster's level gives each party's column the same **…**; General has no *Remove party…*; Enter or Space opens it from **…**, the arrows move, Esc closes and gives the focus back."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_project_desktop_browser import ProjectHost, _col, _head, _project  # noqa: E402
from tests.test_shell_browser import _open, _parties  # noqa: E402

pytestmark = pytest.mark.browser

WORDS = ["About this party", "Edit the party", "Remove party…"]


@pytest.fixture
def menu(gui):
    pg, host, errors = _open(gui, host=ProjectHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _row(pg, slug):
    return _parties(pg).locator(f'.arena-pmenu[data-party="{slug}"]')


def _items(pg):
    menu = pg.get_by_role("menu")
    menu.wait_for(timeout=WAIT_MS)
    return menu, [b.inner_text().strip() for b in menu.get_by_role("menuitem").all()]


def _question(pg, title):
    q = pg.get_by_role("dialog", name=f"Remove {title}?")
    q.wait_for(timeout=WAIT_MS)
    return q


def test_a_right_click_on_a_partys_row_opens_its_menu_and_remove_party_opens_the_question(menu):
    pg, _ = menu
    _parties(pg).locator('.arena-phead[data-goal="website"]').click(button="right")
    box, items = _items(pg)
    assert items == WORDS
    rect, win = box.bounding_box(), pg.viewport_size
    assert 0 <= rect["x"] and rect["x"] + rect["width"] <= win["width"] and rect["y"] + rect["height"] <= win["height"]
    assert pg.locator(".arena[data-goal=passkey]").count() == 1                                    # a right click shows nothing else: the party shown is the same
    box.get_by_role("menuitem", name="Remove party…").click()
    q = _question(pg, "Website")
    assert pg.get_by_role("menu").count() == 0
    assert [b.inner_text().strip() for b in q.locator("button:not(.shell-modal__x)").all()][-1] == "Cancel"
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('[role=dialog]')", timeout=WAIT_MS)


def test_the_dots_are_hidden_at_rest_shown_on_hover_and_on_focus_and_open_the_same_menu(menu):
    pg, _ = menu
    dots = _row(pg, "website").get_by_role("button", name="More about Website")
    assert dots.evaluate("e => getComputedStyle(e).opacity") == "0"
    _parties(pg).locator('.arena-phead[data-goal="website"]').hover()
    assert dots.evaluate("e => getComputedStyle(e).opacity") == "1"
    pg.mouse.move(700, 500)
    assert dots.evaluate("e => getComputedStyle(e).opacity") == "0"
    dots.focus()
    assert dots.evaluate("e => getComputedStyle(e).opacity") == "1"                               # focus shows it too
    pg.keyboard.press("Enter")
    _, items = _items(pg)
    assert items == WORDS and dots.get_attribute("aria-expanded") == "true"
    pg.keyboard.press("Escape")
    assert pg.get_by_role("menu").count() == 0 and dots.get_attribute("aria-expanded") == "false"


def test_the_keyboard_opens_with_enter_or_space_moves_with_the_arrows_and_closes_with_escape(menu):
    pg, host = menu
    dots = _row(pg, "website").get_by_role("button", name="More about Website")
    for key in ("Enter", "Space"):
        dots.focus()
        pg.keyboard.press(key)
        box, _ = _items(pg)
        names = lambda: box.evaluate("e => document.activeElement.textContent")  # noqa: E731
        assert names() == "About this party"                                                       # the first item takes the focus
        pg.keyboard.press("ArrowDown")
        assert names() == "Edit the party"
        pg.keyboard.press("ArrowDown")
        assert names() == "Remove party…"
        pg.keyboard.press("ArrowDown")
        assert names() == "About this party"                                                       # round
        pg.keyboard.press("ArrowUp")
        assert names() == "Remove party…"
        pg.keyboard.press("Escape")
        assert pg.get_by_role("menu").count() == 0
        assert dots.evaluate("e => e === document.activeElement")                                   # the focus is back on …
    dots.focus()
    pg.keyboard.press("Enter")
    _items(pg)
    pg.keyboard.press("ArrowDown")
    pg.keyboard.press("ArrowDown")
    pg.keyboard.press("Enter")                                                                      # Remove party… by the keyboard
    _question(pg, "Website")
    assert not [1 for n, _ in host.log if n == "ideas.track_drop"]                                  # asking sends nothing


def test_edit_the_party_and_about_this_party_open_theirs_from_the_menu(menu):
    pg, host = menu
    _row(pg, "website").get_by_role("button", name="More about Website").click()
    pg.get_by_role("menuitem", name="Edit the party").click()
    dlg = pg.get_by_role("dialog", name="Edit the party")
    dlg.wait_for(timeout=WAIT_MS)
    assert dlg.get_by_role("button", name="Remove party").count() == 1                              # the foot keeps its own
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('[role=dialog]')", timeout=WAIT_MS)
    _row(pg, "website").get_by_role("button", name="More about Website").click()
    pg.get_by_role("menuitem", name="About this party").click()
    drawer = pg.get_by_role("complementary", name="The right column")
    drawer.locator(".shell-goal").wait_for(timeout=WAIT_MS)
    assert ("ideas.goal", {"slug": "website"}) in host.log                                          # the party's own screen, not the one shown


def test_a_click_away_closes_the_menu_and_only_one_stands(menu):
    pg, _ = menu
    _parties(pg).locator('.arena-phead[data-goal="website"]').click(button="right")
    _items(pg)
    _parties(pg).locator('.arena-phead[data-goal="passkey"]').click(button="right")          # above the first: its list hangs below the pointer
    assert pg.get_by_role("menu").count() == 1 and pg.get_by_role("menu").get_attribute("aria-label").startswith("Passkey")
    pg.mouse.click(900, 600)
    assert pg.get_by_role("menu").count() == 0


def test_the_orkmasters_columns_have_the_same_dots_and_remove_party_opens_the_question(menu):
    pg, _ = menu
    _project(pg)
    col, head = _col(pg, "website").bounding_box(), _head(pg, "website").bounding_box()
    assert abs(col["x"] - head["x"]) < 2 and abs(col["width"] - head["width"]) < 2                  # the head still lies over its column
    dots = pg.locator('.arena-project__heads').get_by_role("button", name="More about Website")
    assert dots.evaluate("e => getComputedStyle(e).opacity") == "0"
    _head(pg, "website").hover()
    assert dots.evaluate("e => getComputedStyle(e).opacity") == "1"
    dots.click()
    _, items = _items(pg)
    assert items == WORDS
    pg.get_by_role("menuitem", name="Remove party…").click()
    _question(pg, "Website")
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('[role=dialog]')", timeout=WAIT_MS)
    _head(pg, "release").click(button="right")                                                     # a right click on a column's head too
    assert _items(pg)[1] == WORDS
    pg.keyboard.press("Escape")
    assert pg.locator(".arena-project").count() == 1                                                # the level stays


def test_general_has_no_remove_party(menu):
    pg, _ = menu
    assert _parties(pg).locator('.arena-phead[data-goal="general"]').count() == 0                    # General has no row of its own
    got = pg.evaluate("""() => import('/static/js/arena/partymenu.js').then((m) => [m.itemsOf('general').map((i) => i[0]), m.itemsOf('website').map((i) => i[0])])""")
    assert got == [["About this party", "Edit the party"], WORDS]
