"""Spec 132 C's face (docs/specs/132-four-levels-the-way-down-and-findings.md C.2; decisions §234.2, §237.7) in a real browser against the table's stub host: every row of a change carries `level` and `pulls`
(realm/way_down.py); the lifted card says the way down in one line, its level's sign first (the sign's title *Changes the spec*, never a word on the card): *About $0.60–1.50 at API prices: 1 section, 2 tasks*, what each is under
**More**; a change that pulls nothing says its own price or that nothing below it is redone; a row with no `level` keeps the plain cost line; the kind rows that make their own lines (a quality card) are not given this one.
Screenshots to $WAY_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import start  # noqa: E402
from tests.test_make_change_browser import ChangeHost, row  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["WAY_SHOTS"]) if os.environ.get("WAY_SHOTS") else None
PULLS = {"level": "spec", "sections": [{"idea": "seat", "party": "tech"}], "tasks": [{"idea": "seat", "id": "s1"}, {"idea": "seat", "id": "s2"}], "checks": 3, "estimate": {"usd_low": 0.6, "usd_high": 1.5}}


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / name))


@pytest.fixture
def asked(gui):
    pg, host, errors = start(gui, "wide", ChangeHost())
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def lift(pg, kind="leader_change"):
    pg.locator(f'.hand-card[data-kind="{kind}"]').first.click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_a_change_says_its_way_down_in_one_line_its_levels_sign_first_and_what_each_is_under_more(asked):
    pg, host = asked
    host.needs = [row(level="spec", pulls=PULLS)]
    host.push()
    pg.locator('.hand-card[data-kind="leader_change"]').wait_for(timeout=WAIT_MS)
    lifted = lift(pg)
    line = lifted.locator(".hand-wayline")
    assert line.count() == 1 and line.get_attribute("data-level") == "spec" and lifted.locator(".hand-spend").count() == 0, "the one line stands where the plain cost line stood"
    words = " ".join(line.locator(".hand-wayline__words").inner_text().split())
    assert words == "About $0.60–1.50 at API prices: 1 section, 2 tasks, 3 checks", words
    sign = line.locator(".hand-wayline__sign .ork-sign")
    assert sign.get_attribute("class").split()[-1] == "page" and sign.get_attribute("title") == "Changes the spec"
    assert "Changes the spec" not in lifted.inner_text(), "the sign's title, not a word on the card"
    assert line.locator(".hand-wayline__list").count() == 0
    line.get_by_role("button", name="More").click()
    items = [" ".join(li.inner_text().split()) for li in line.locator(".hand-wayline__list li").all()]
    assert items == ["Keep the seat when a socket reconnects · Tech", "Keep the seat when a socket reconnects · Keep the seat when a socket reconnects", "Keep the seat when a socket reconnects · Reset the round timer when a player rejoins", "3 checks again"], items
    shot(pg, "way-spec.png")
    line.get_by_role("button", name="Less").click()
    assert line.locator(".hand-wayline__list").count() == 0


def test_a_change_that_pulls_nothing_says_its_own_price_or_that_nothing_below_it_is_redone(asked):
    pg, host = asked
    none = {"level": "spec", "sections": [], "tasks": [], "checks": 0, "estimate": {"usd_low": 0.0, "usd_high": 0.0}}
    host.needs = [row(level="spec", pulls=none)]
    host.push()
    pg.locator('.hand-card[data-kind="leader_change"]').wait_for(timeout=WAIT_MS)
    lifted = lift(pg)
    assert " ".join(lifted.locator(".hand-wayline__words").inner_text().split()) == "About $0.20–0.60 at API prices", "the change's own price"
    assert lifted.locator(".hand-wayline__more").count() == 0, "nothing under More"
    host.needs = [row(level="spec", pulls=none, usd_low=None, usd_high=None)]
    host.push()
    pg.wait_for_function("() => document.querySelector('.hand-wayline__words')?.innerText.includes('Nothing below it is redone')", timeout=WAIT_MS)


def test_each_level_has_its_own_sign_and_a_row_with_no_level_keeps_the_plain_cost_line(asked):
    pg, host = asked
    for level, sign in (("decision", "compass"), ("work", "work")):
        host.needs = [row(level=level, pulls={**PULLS, "level": level})]
        host.push()
        pg.locator('.hand-card[data-kind="leader_change"]').wait_for(timeout=WAIT_MS)
        lifted = lift(pg)
        s = lifted.locator(".hand-wayline__sign .ork-sign")
        assert s.get_attribute("class").split()[-1] == sign and s.get_attribute("title") == f"Changes the {level}"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    host.needs = [row()]
    host.push()
    pg.locator('.hand-card[data-kind="leader_change"]').wait_for(timeout=WAIT_MS)
    lifted = lift(pg)
    assert lifted.locator(".hand-wayline").count() == 0 and lifted.locator(".hand-spend").count() == 1


def test_the_goals_open_levels_are_read_from_its_row_of_the_board(asked):
    pg, host = asked
    got = pg.evaluate("""async () => {
      const { board } = await import('/static/js/board/store.js'), { levelsOf } = await import('/static/js/hand/wayline.js');
      board.value = { ...(board.value || {}), ideas: [{ slug: 'seat', levels: ['quality', 'decision'] }, { slug: 'x' }] };
      return [levelsOf('seat'), levelsOf('x'), levelsOf('none')];
    }""")
    assert got == [["decision", "quality"], [], []], got
