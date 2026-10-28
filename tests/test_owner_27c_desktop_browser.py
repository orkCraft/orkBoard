"""The owner's 26 October afternoon, on the desktop (Chromium at 1 440 × 900): a held task says what is happening and has Start now (the plan's row, the task's screen);
what is under a party in the left column is one step in, with a guide, and the party's row stays flush; the Orkmaster's tab is *Board* like a party's, and its board lies in the pane
the right column pushes in (decisions §105.2), as a party's does."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_project_desktop_browser import ProjectHost, _project  # noqa: E402
from tests.test_shell_browser import StubHost, _calls, _open, _open_goal, _parties  # noqa: E402

pytestmark = pytest.mark.browser

WHY = "Waits for Antigravity's limit: 14 % of the week left, kept for you until 12:00"
SYNC = "Sync ideas between the phone and the town"


@pytest.fixture
def held(gui):
    """The stub's Sync goal with its last task held by the reserve, the host's sentence on it."""
    host = StubHost()
    host.plan["tasks"][4].update(state="held", note="reserve · after 12:00", held_why=WHY)
    host.chip_extra = {"k5": {"why": WHY, "note": "reserve · after 12:00"}}
    pg, host, errors = _open(gui, host=host)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_held_task_in_the_plan_says_whose_limit_and_how_much_and_has_start_now(held):
    pg, host = held
    _open_goal(pg, SYNC)
    row = pg.locator(".shell-drawer .board-tasks li[data-state=held]")
    row.wait_for(timeout=WAIT_MS)
    assert WHY in row.inner_text() and "keeps your reserve" not in row.inner_text()
    pg.locator(".shell-drawer .board-tasks").get_by_role("button", name="Start now").click()
    assert _calls(pg, host, "ideas.start_now") == [{"slug": "sync"}]
    assert pg.locator(".shell-drawer .board-tasks").get_by_role("button", name="Start now").count() == 1      # one for the goal, not one for every held task


def test_a_held_task_a_window_holds_has_no_start_now(gui):
    host = StubHost()
    host.plan["tasks"][4].update(state="held", note="after 12:00")
    pg, host, errors = _open(gui, host=host)
    _open_goal(pg, SYNC)
    row = pg.locator(".shell-drawer .board-tasks li[data-state=held]")
    row.wait_for(timeout=WAIT_MS)
    assert "waits for limits · after 12:00" in row.inner_text() and pg.get_by_role("button", name="Start now").count() == 0       # a tool's own window is not the person's to override
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_held_tasks_screen_says_whose_limit_and_has_start_now(held):
    pg, host = held
    pg.evaluate("import('/static/js/shell/store.js').then((m) => m.showTask('sync', 'k5'))")                    # (the Agents' chip that opened it went, spec 98 A)
    state = pg.locator(".shell-drawer .shell-facts dd[data-state=held]")
    state.wait_for(timeout=WAIT_MS)
    assert WHY in state.inner_text()
    pg.locator(".shell-drawer").get_by_role("button", name="Start now").click()
    assert _calls(pg, host, "ideas.start_now") == [{"slug": "sync"}]


def test_a_hold_from_before_the_sentence_says_what_it_can(gui):
    host = StubHost()
    host.plan["tasks"][4].update(state="held", note="week · after 12:00")
    pg, host, errors = _open(gui, host=host)
    _open_goal(pg, SYNC)
    row = pg.locator(".shell-drawer .board-tasks li[data-state=held]")
    row.wait_for(timeout=WAIT_MS)
    assert "Waits for the week's pace until 12:00" in row.inner_text() and row.get_by_role("button", name="Start now").count() == 1
    pg.close()
    assert not errors, "\n".join(errors)


# -- the left column: what is under a party is one step in ---------------------------------------------------------------------------------------------------

def test_what_is_under_a_party_is_one_step_in_with_a_guide_and_the_party_row_is_flush(gui):
    pg, host, errors = _open(gui)
    col = pg.locator(".arena-left").bounding_box()
    head = pg.locator(".arena-phead[aria-current=true]")
    box = head.bounding_box()
    assert box["x"] == col["x"] and box["width"] >= col["width"] - 2                                                  # the party's row stays flush, the column's whole width
    body = pg.locator(".arena-party.is-open .arena-pbody").bounding_box()
    name = head.locator(".arena-phead__who").bounding_box()
    assert body["x"] - box["x"] == 32                                                                                   # a head's width (24) and its gap (8)
    for sel in (".arena-sec", ".arena-goal__main", ".arena-frow"):                                      # its labels, goals, the folds
        got = pg.locator(f".arena-pbody {sel}")
        assert got.count() >= 1, sel
        for i in range(got.count()):
            assert got.nth(i).bounding_box()["x"] >= body["x"] - 0.5, (sel, i)
    first = pg.locator(".arena-pbody .arena-goal__main .ork-elem, .arena-pbody .arena-goal__main svg").first.bounding_box()
    assert abs(first["x"] - name["x"]) <= 2                                                                              # the goal's mark starts where the party's name does
    guide = pg.evaluate("() => { const s = getComputedStyle(document.querySelector('.arena-pbody'), '::before'); const f = getComputedStyle(document.documentElement).getPropertyValue('--ork-frame').trim();"
                        " const probe = document.createElement('i'); probe.style.color = f; document.body.append(probe); const want = getComputedStyle(probe).color; probe.remove();"
                        " return {w: s.borderLeftWidth, color: s.borderLeftColor, want, left: s.left}; }")
    assert guide["w"] == "1px" and guide["color"] == guide["want"] and guide["left"] == "-8px"                          # a thin guide in --ork-frame, under the middle of the head
    assert pg.locator(".arena-pbody").evaluate("e => e.querySelectorAll('.arena-goal, .arena-frow').length") > 0
    pg.locator(".arena-phead[aria-current=true]").focus()                                                                # the keys are as they were: ↓ goes to the next heading (or New party)
    pg.keyboard.press("ArrowDown")
    assert pg.evaluate("document.activeElement.matches('.arena-phead, .arena-pnew') && document.activeElement !== document.querySelector('.arena-phead[aria-current=true]')")
    assert pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    pg.close()
    assert not errors, "\n".join(errors)


# -- the Orkmaster's Board -------------------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def level(gui):
    pg, host, errors = _open(gui, host=ProjectHost(), ready=".arena[data-goal=passkey]")
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def test_the_orkmasters_first_tab_is_board_like_a_partys_and_keeps_its_id(level):
    pg, host = level
    _project(pg)
    tabs = pg.locator(".arena-pjtabs [role=tab]")
    assert [t.text_content().strip() for t in tabs.all()] == ["Board", "Assets and files", "Play"]
    assert tabs.first.get_attribute("data-tab") == "field" and tabs.first.get_attribute("aria-selected") == "true"
    assert "Field" not in pg.locator(".arena-project").inner_text()


def test_the_orkmasters_board_lies_in_the_pane_the_right_column_pushes_and_its_columns_share_what_is_left(level):
    pg, host = level
    _project(pg)
    pane = lambda: pg.locator(".arena-project__body").evaluate("e => ({w: e.clientWidth, scroll: e.scrollWidth})")      # noqa: E731
    cols = lambda: pg.locator(".arena-pcol").evaluate_all("els => els.map(e => Math.round(e.getBoundingClientRect().width))")      # noqa: E731
    before, wide = pane(), cols()
    assert before["scroll"] <= before["w"] and len(wide) == 4
    pg.locator(".arena-pcol [data-slug]").first.click()
    pg.locator(".shell-drawer").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    after, narrow = pane(), cols()
    assert after["w"] < before["w"] - 400                                                                                # the right column pushed the pane
    assert after["scroll"] <= after["w"], (before, after)                                                               # the columns re-laid out into it: no sideways scroll
    assert sum(narrow) <= after["w"] + len(narrow) and all(172 <= w < 260 for w in narrow) and max(narrow) < max(wide)               # they shrank (172 at the least) to share the width
    assert pg.locator(".arena-pcol__head").evaluate_all("els => els.map(e => Math.round(e.getBoundingClientRect().width))") == narrow       # each head still over its column
    pg.locator(".shell-drawer__x").click()                                                                               # the column closed: the pane takes the width again
    pg.wait_for_timeout(300)
    assert cols() == wide
