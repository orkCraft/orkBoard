"""Spec 165 Q: Dev and main's goals as cars (docs/specs/165-each-leaders-map-a-board-games-shape.md; decisions §280.2, §280.4, §281.6).

Oldest first in one row (at the wide width), each car its age in words (*3 days*), past the eighth car a mark where the big batch starts, said in words in its label and title, no count; the ticks, **To main** and `Pickable`
stamps as they were. Against the maps' stub host (tests/test_maps_desktop_browser.py), whose `ideas.release_map` goals now carry `at`. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import time

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import card, go, maps, names  # noqa: E402,F401  (fixtures)
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser

DAY = 86400


def goals(days):
    """One goal for each age in `days` (newest first, as release_map gives them)."""
    now = time.time()
    return [{"idea": f"g{n}", "title": f"Goal {n}", "element": "meadow", "commit": f"{n:07d}" + "0" * 33, "ticked": True, "at": int(now - d * DAY - 600)} for n, d in enumerate(days)]


def test_the_goals_are_cars_oldest_first_each_with_its_age(maps):
    pg, host, w = maps
    host.goals = goals([1, 2, 3, 5, 9, 20])                                    # newest first
    go(pg, "release")
    pg.locator(".mp-goal").first.wait_for(timeout=WAIT_MS)
    assert names(pg, ".mp-cars") == ["Goal 5", "Goal 4", "Goal 3", "Goal 2", "Goal 1", "Goal 0"]
    assert [a.strip() for a in pg.locator(".mp-goal .mp-age").all_text_contents()] == ["2 weeks", "9 days", "5 days", "3 days", "2 days", "1 day"]
    assert pg.locator(".mp-batch").count() == 0                                # six cars: the batch is not big
    assert pg.locator(".mp-goal.mp-card[data-id]").count() == 6 and pg.locator(".mp-goal .mp-tick").count() == 6
    if w == "wide":
        ys = {round(b["y"]) for b in (c.bounding_box() for c in pg.locator(".mp-goal").all())}
        assert len(ys) == 1                                                    # one row
    shot(pg, f"release-cars-{w}.png")


def test_past_the_eighth_car_a_mark_says_where_the_big_batch_starts(maps):
    pg, host, w = maps
    host.goals = goals(list(range(1, 12)))
    go(pg, "release")
    pg.locator(".mp-goal").first.wait_for(timeout=WAIT_MS)
    marks = pg.locator(".mp-batch")
    assert marks.count() == 1
    label = marks.get_attribute("aria-label")
    assert label and label == marks.get_attribute("title") and "big batch" in label
    assert not any(ch.isdigit() for ch in label)                               # no count
    before = pg.locator(".mp-cars > *").evaluate_all("els => els.findIndex((e) => e.classList.contains('mp-batch'))")
    assert before == 8                                                         # eight cars, then the mark
    shot(pg, f"release-cars-batch-{w}.png")


def test_a_goal_with_no_age_read_has_no_age_line_and_keeps_its_place_after_the_aged(maps):
    pg, host, w = maps
    host.goals = goals([4, 2])
    host.goals.insert(0, {**host.goals[0], "idea": "none", "title": "Unaged", "at": None})
    go(pg, "release")
    pg.locator(".mp-goal").first.wait_for(timeout=WAIT_MS)
    assert names(pg, ".mp-cars") == ["Goal 0", "Goal 1", "Unaged"]
    assert pg.locator(".mp-goal .mp-age").count() == 2
    assert card(pg, "none").count() == 1
