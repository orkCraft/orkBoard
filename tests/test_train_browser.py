"""Spec 117 part J, Dev and main as a train (docs/specs/117-each-lens-a-games-shape.md §9, decisions §195), in a real browser at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with a mouse), against the maps' stub host
(`MapsHost`, whose `ideas.release_map` here answers `at` and `big_from` as part C does).

The cars: the goals oldest first (by `at`), each the goal's card as built, coupled to the next by a short line (none at the start of a row); its age under its title (*today*, *1 day*, *n days*; none when the time is not known); before the car
where the batch turns big (`big_from`, counted from the oldest) an upright dashed line, *From here the batch is big* (none while fewer wait); a car the kit's heat calls stale lies faint, the reach's edge on it not; **To main** and *Since <version>* as
built; at the narrow width the cars wrap in rows; no sideways scroll. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import time

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import MapsHost, card, go, names, wide  # noqa: E402
from tests.test_table_desktop_browser import shot, title, watch  # noqa: E402

pytestmark = pytest.mark.browser

DAY = 86400
BIG = "From here the batch is big"
SLUGS = [f"g{n}" for n in range(1, 10)]


class TrainHost(MapsHost):
    """The maps' host with nine goals waiting in dev, newest first as the host gives them (`at` in seconds before now), and the gate's `big_from`; `heat`: the heat the stub answers, by goal."""

    def __init__(self, ages=None, big_from=8, heat=None):
        super().__init__()
        now = int(time.time())
        ages = ages if ages is not None else [0, 0, 1, 2, 3, 5, 8, 13, 21]                                    # days old, newest first
        self.big_from = big_from
        self.waiting = {}
        self.goals = [{"idea": SLUGS[n], "title": f"Goal {n + 1}", "element": ("meadow", "ice", "dust", "void", "lava")[n % 5], "commit": f"{n + 1:x}" * 7 + "0" * 33,
                       "at": (now - d * DAY - 60 * (n + 1)) if d is not None else 0, "ticked": n != 1} for n, d in enumerate(ages)]
        self.heats = heat or {}

    def handle(self, name, a):
        if name == "ideas.release_map":
            self.log.append((name, a))
            return {"into": "dev", "main": "main", "same": False, "commits": len(self.goals), "files": 14, "big_from": self.big_from, "goals": self.goals, "since": {"version": "1.3", "out": "2026-10-19T10:00:00"}}
        if name == "ideas.heat":
            self.log.append((name, a))
            return {"map": "release", "parts": self.heats if a["party"] == "release" else {}}
        return super().handle(name, a)


def open_train(gui, width, host):
    """The window at `width` on Release's map: `(page, errors)`."""
    errors: list[str] = []
    server, browser = gui
    pg = narrow.page(browser, width)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    go(pg, "release")
    pg.locator(".mp-goal").first.wait_for(timeout=WAIT_MS)
    return pg, errors


@pytest.fixture(params=narrow.WIDTHS)
def train(gui, request):
    """Release's map at one of the two widths against a TrainHost: `(page, host, width)`; the page's errors are asserted at the end."""
    host = TrainHost()
    pg, errors = open_train(gui, request.param, host)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def order(pg):
    return pg.locator(".tr-car .mp-goal").evaluate_all("els => els.map((e) => e.dataset.id)")


def ages(pg):
    return pg.locator(".tr-car .mp-goal").evaluate_all("els => els.map((e) => e.querySelector('.tr-age')?.textContent ?? null)")


def rows(pg):
    """The distinct tops of the cars: one for each row."""
    return sorted({round(b) for b in pg.locator(".tr-car").evaluate_all("els => els.map((e) => e.getBoundingClientRect().top)")})


def test_the_goals_are_cars_oldest_first_each_with_its_age_under_its_title(train):
    pg, host, w = train
    assert title(pg) == "The whole project · through Release"
    assert order(pg) == SLUGS[::-1], "oldest first: the host gave them newest first"
    assert names(pg, ".tr-train") == [f"Goal {n}" for n in range(9, 0, -1)]
    assert ages(pg) == ["21 days", "13 days", "8 days", "5 days", "3 days", "2 days", "1 day", "today", "today"]
    car = card(pg, "g9")
    head, age, win = (car.locator(s).bounding_box() for s in (".mp-card__head", ".tr-age", ".mp-win"))
    assert head["y"] + head["height"] <= age["y"] + 1 and age["y"] + age["height"] <= win["y"] + 1, "the age lies under the title"
    assert car.locator(".mp-card__l").text_content() == "9" * 7 and car.locator(".mp-tick").get_attribute("aria-label") == "In the merge", "the card as built"
    assert "is-ghost" in card(pg, "g2").get_attribute("class")
    to_main, since = pg.get_by_role("button", name="To main"), pg.locator(".mp-since")
    assert to_main.is_enabled() and "Merges dev into main whole: 9 goals" in pg.locator(".mp-tomain").inner_text() and since.text_content().startswith("Since 1.3")
    assert pg.locator(".mp-tomain").bounding_box()["y"] > pg.locator(".tr-train").bounding_box()["y"]
    shot(pg, f"train-{w}.png")


def test_a_coupler_joins_each_car_to_the_one_before_it_and_none_starts_a_row(train):
    pg, host, w = train
    cars = pg.locator(".tr-car")
    firsts = pg.locator(".tr-car").evaluate_all("els => els.map((e) => e.hasAttribute('data-first'))")
    tops = pg.locator(".tr-car").evaluate_all("els => els.map((e) => e.getBoundingClientRect().top)")
    assert firsts[0] and all(f == (n == 0 or tops[n] > tops[n - 1] + 1) for n, f in enumerate(firsts))
    assert sum(firsts) == len(rows(pg))
    coupled = [cars.nth(n).evaluate("e => { const s = getComputedStyle(e, '::before'); return s.content !== 'none' && parseFloat(s.width) > 0 }") for n in range(9)]
    assert coupled == [not f for f in firsts], "a line before every car but the first of a row"
    if wide(w):
        assert len(rows(pg)) == 3, "the cars wrap (940 px, four a row)"
    else:
        assert len(rows(pg)) == 5, "two a row"
        boxes = [cars.nth(n).bounding_box() for n in range(9)]
        assert all(b["x"] + b["width"] <= 390 for b in boxes)
    cars.nth(3).scroll_into_view_if_needed()
    shot(pg, f"train-couplers-{w}.png")


def test_the_batch_turns_big_at_the_eighth_car_from_the_oldest(train):
    pg, host, w = train
    mark = pg.locator(".tr-big")
    assert mark.count() == 1 and mark.inner_text() == BIG
    assert order(pg)[7] == "g2" and pg.locator(".tr-car").nth(7).locator(".tr-big").count() == 1, "before the 8th car, counted from the oldest"
    car, line = pg.locator(".tr-car").nth(7).bounding_box(), mark.bounding_box()
    assert line["x"] < car["x"] and line["x"] + line["width"] <= car["x"] + 1, "the line stands before the car"
    assert line["height"] >= car["height"] and line["y"] <= car["y"], "upright, as tall as the car"
    assert mark.evaluate("e => getComputedStyle(e).borderLeftStyle") == "dashed"
    assert mark.locator(".mp-cap").bounding_box()["x"] >= line["x"]
    mark.scroll_into_view_if_needed()
    shot(pg, f"train-big-{w}.png")


@pytest.mark.parametrize("waiting,big", [(7, 8), (3, 8), (9, 0), (9, 9)])
def test_no_mark_while_fewer_wait_than_the_batch_is_big_and_one_at_the_very_last_car(gui, waiting, big):
    host = TrainHost(ages=list(range(waiting)), big_from=big)
    pg, errors = open_train(gui, "wide", host)
    n = pg.locator(".tr-big").count()
    assert n == (1 if 0 < big <= waiting else 0)
    if n:
        assert pg.locator(".tr-car").nth(big - 1).locator(".tr-big").count() == 1
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_an_age_is_none_when_the_time_is_not_known_and_a_time_not_known_keeps_its_place(gui):
    host = TrainHost(ages=[0, None, 4])
    pg, errors = open_train(gui, "wide", host)
    assert order(pg) == ["g2", "g3", "g1"], "a time not known is the oldest, the rest by their time"
    assert ages(pg) == [None, "4 days", "today"]
    assert pg.locator(".tr-age").count() == 2 and pg.locator(".tr-big").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_stale_car_lies_faint_and_the_others_do_not(gui):
    host = TrainHost(heat={"g3": [{"kind": "stale", "aspect": "debt", "words": "Waiting in dev for 8 days"}], "g4": [{"kind": "hotspot", "aspect": "hotspots", "words": "Changed 14 times"}]})
    pg, errors = open_train(gui, "wide", host)
    pg.locator('.mp-goal[data-heat~="stale"]').wait_for(timeout=WAIT_MS)
    stale = card(pg, "g3")
    opacity = lambda sel: stale.locator(sel).evaluate("e => getComputedStyle(e).opacity")     # noqa: E731
    assert opacity(".mp-card__head") == "0.5" and opacity(".tr-age") == "0.5" and opacity(".mp-win") == "0.5"
    other = card(pg, "g4")
    assert other.get_attribute("data-heat") == "hotspot" and other.locator(".mp-card__head").evaluate("e => getComputedStyle(e).opacity") == "1"
    assert card(pg, "g5").locator(".mp-card__head").evaluate("e => getComputedStyle(e).opacity") == "1"
    assert stale.evaluate("e => getComputedStyle(e).opacity") == "1", "the card itself stays whole: the reach's edge on it is seen"
    shot(pg, "train-stale-wide.png")
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_cars_wrap_in_rows_at_the_narrow_width_with_nothing_past_the_edge(gui):
    host = TrainHost()
    pg, errors = open_train(gui, "narrow", host)
    boxes = [pg.locator(".tr-car").nth(n).bounding_box() for n in range(9)]
    assert {round(b["x"]) for b in boxes} == {round(boxes[0]["x"]), round(boxes[1]["x"])} and len(rows(pg)) == 5
    assert all(0 <= b["x"] and b["x"] + b["width"] <= 390 for b in boxes)
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)
