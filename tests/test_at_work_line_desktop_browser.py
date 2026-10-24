"""Spec 72 B on the desktop (docs/specs/72-at-work-under-a-closed-party.md §1, §2, §4; decisions §87), in a real browser at 1 440 × 900 against the one window's stub
host: under a closed party's heading one quiet line of its goals at work (each its element and short name, the work sign before them, ending *and k more* when they do
not fit); the open party and Operations show none, a party with none at work has none; a press on a goal shows that party with only that goal picked, *and k more*
shows it with no pick; the goals are buttons beside the heading's button, never inside it; the line is in the muted ink. Screenshot to docs/design/img/v1/ when ORKCRAFT_SHOTS is set."""
from __future__ import annotations

import os

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost  # noqa: E402
from tests.test_map_desktop_browser import node  # noqa: E402
from tests.test_shell_browser import SHOTS, _open, _parties, box  # noqa: E402

pytestmark = pytest.mark.browser

OPEN = ".arena-phead[aria-current=true]"
SHOP = "/work/shop"
PRICING = [("billing", "Billing settings page", "Billing", "ice"), ("receipts", "Receipts by email for every order", "Receipts", "lava")]
WEEKLY = [("digest", "Digest layout for the weekly mail", "Digest", "meadow"), ("unsub", "Unsubscribe link on every mail", "Unsubscribe", "dust"),
          ("schedule", "Send schedule per time zone", "Schedule", "void"), ("preview", "Preview before sending", "Preview", "ice"),
          ("bounce", "Bounces and complaints handling", "Bounces", "lava")]


class WorkHost(ArenaHost):
    """The passkey party (open, three goals at work), Pricing with two goals at work, Weekly report email with five, and Operations."""

    def __init__(self, pricing=PRICING, weekly=WEEKLY):
        super().__init__()
        self.ops = True
        for goal, rows in (("pricing", pricing), ("weekly", weekly)):
            for slug, title, short, element in rows:
                self.nodes.append(node(slug, goal, title, "working", 1, stage="implementation", short=short, element=element, flag=None))
                self.ideas[slug] = self.idea(slug, title, "working", 40, track=goal)
            later = f"{goal}-later"                                                                                 # not at work: not in the line
            self.nodes.append(node(later, goal, f"Later of {goal}", "plan", 2, element="dust", flag=None))
            self.ideas[later] = self.idea(later, f"Later of {goal}", "plan", 41, track=goal)

    def snapshot(self):
        snap = super().snapshot()
        snap["state"]["projects"] = {"current": SHOP, "recent": [], "open": [{"path": SHOP, "name": "shop", "working": 0, "needs_you": 0, "review": 0}]}
        return snap


def _party(slug):
    return f'.arena-party:has(.arena-phead[data-goal="{slug}"])'


def _line(pg, slug):
    return _parties(pg).locator(f"{_party(slug)} .arena-atwork")


def _open_on(gui, host):
    pg, _, errors = _open(gui, host=host, ready=".arena[data-goal=passkey]")
    pg.locator(".arena-atwork").first.wait_for(timeout=WAIT_MS)
    pg.evaluate("document.fonts.ready.then(() => 0)")                                                             # the names are measured in the face they are drawn in
    pg.wait_for_function("() => !document.querySelector('.arena-atwork.is-measuring')", timeout=WAIT_MS)
    return pg, errors


@pytest.fixture
def worked(gui):
    pg, errors = _open_on(gui, WorkHost())
    yield pg
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_closed_party_shows_its_goals_at_work_in_one_line_and_the_open_one_none(worked):
    pg = worked
    line = _line(pg, "pricing")
    assert line.count() == 1 and line.get_attribute("role") == "group"
    assert line.get_attribute("aria-label") == "At work: Billing settings page, Receipts by email for every order" and line.get_attribute("title") == line.get_attribute("aria-label")
    assert line.locator(".ork-sign.work").count() == 1 and line.locator(".ork-elem").count() == 2                  # the work sign, an element each (orkUI's, no typed arrow)
    assert [e.get_attribute("class").split()[-1] for e in line.locator(".ork-elem").all()] == ["ice", "lava"]
    goals = line.locator(".arena-atwork__goal")
    assert [g.inner_text().strip() for g in goals.all()] == ["Billing", "Receipts"]                       # short names, in the map's order, joined by ·
    assert [g.get_attribute("title") for g in goals.all()] == ["Billing settings page", "Receipts by email for every order"]
    assert [g.get_attribute("aria-label") for g in goals.all()] == ["Billing settings page", "Receipts by email for every order"]
    assert "·" in line.inner_text() and "↻" not in line.inner_text() and "more" not in line.inner_text()
    assert goals.first.bounding_box()["height"] >= 32 and line.bounding_box()["height"] == 20                       # a 32 px target in a 20 px line
    assert _line(pg, "passkey").count() == 0 and pg.locator(".arena-party.is-open .arena-atwork").count() == 0       # the open party's goals are below its heading
    assert _line(pg, "@operations").count() == 0 and pg.locator(".arena-atwork").count() == 2                      # nor under Operations: pricing and weekly only


def test_the_line_sits_under_the_headings_name_inside_its_box_and_one_line_high(worked):
    pg = worked
    head, line, party = box(pg, '.arena-phead[data-goal="pricing"]'), box(pg, f"{_party('pricing')} .arena-atwork"), box(pg, _party("pricing"))
    name = box(pg, '.arena-phead[data-goal="pricing"] .arena-phead__name')
    assert line["y"] >= head["y"] + head["height"] - 6 and line["y"] + line["height"] <= party["y"] + party["height"]       # inside the heading's box, under the button
    assert abs(line["x"] - name["x"]) <= 1 and line["x"] > head["x"] + 24                                          # indented by the head's width
    assert line["height"] == 20 and party["height"] - head["height"] <= 24                                         # the heading grew by the line
    one = pg.locator(f"{_party('pricing')} .arena-atwork").evaluate(
        "e => [...e.querySelectorAll('.arena-atwork__goal')].every((c) => Math.abs(c.getBoundingClientRect().top - e.querySelector('.arena-atwork__goal').getBoundingClientRect().top) < 2)")
    assert one                                                                                                     # one row


def test_what_does_not_fit_ends_with_and_k_more_without_a_cut_name(worked):
    pg = worked
    line = _line(pg, "weekly")
    more = line.locator(".arena-atwork__more")
    assert more.count() == 1 and line.get_attribute("aria-label").count(",") == 4                                  # all five are in its name
    shown = line.locator(".arena-atwork__goal")
    k = 5 - shown.count()
    assert 1 <= shown.count() < 5 and more.inner_text().strip() == f"and {k} more"
    inner, last = line.bounding_box(), more.bounding_box()
    assert last["x"] + last["width"] <= inner["x"] + inner["width"] + 1                                            # it fits on the line
    for g in shown.all():                                                                                         # no name is cut: its text is whole and drawn whole
        assert g.locator(".arena-atwork__name").evaluate("e => e.scrollWidth <= e.clientWidth + 1")
    assert [g.inner_text().strip() for g in shown.all()] == [w[2] for w in WEEKLY][: shown.count()]


def test_and_1_more_is_said_in_the_singular(gui):
    pg, errors = _open_on(gui, WorkHost(weekly=WEEKLY[:3]))
    try:
        line = _line(pg, "weekly")
        rest = 3 - line.locator(".arena-atwork__goal").count()
        assert rest >= 1 and line.locator(".arena-atwork__more").inner_text().strip() == ("and 1 more" if rest == 1 else f"and {rest} more")
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_name_that_does_not_fit_beside_and_k_more_is_left_to_it_not_cut(gui):
    long = [(f"w{i}", f"Everything about the long name number {i}", f"A very long name for the goal number {i}", "ice") for i in range(3)]
    pg, errors = _open_on(gui, WorkHost(weekly=long))
    try:
        line = _line(pg, "weekly")
        assert line.locator(".arena-atwork__goal").count() == 0 and line.locator(".arena-atwork__more").inner_text().strip() == "and 3 more"
        assert line.get_attribute("aria-label").startswith("At work: Everything about the long name number 0")
        line.locator(".arena-atwork__more").click()
        pg.locator('.arena[data-goal="weekly"]').wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_party_with_no_goal_at_work_has_no_line_and_keeps_its_height(gui):
    pg, errors = _open_on(gui, WorkHost(weekly=[]))
    try:
        assert _line(pg, "weekly").count() == 0 and _line(pg, "pricing").count() == 1
        assert box(pg, _party("weekly"))["height"] - box(pg, '.arena-phead[data-goal="weekly"]')["height"] <= 1       # the heading and its rule: nothing more
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_press_on_a_goal_shows_that_party_with_only_that_goal_picked(worked):
    pg = worked
    _line(pg, "pricing").get_by_role("button", name="Receipts by email for every order").click()
    pg.locator('.arena[data-goal="pricing"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(OPEN).get_attribute("data-goal") == "pricing"
    pg.locator(".arena-goal[data-slug=receipts].is-on").wait_for(timeout=WAIT_MS)
    assert pg.locator(".arena-goal.is-on").count() == 1                                                           # only that goal is in the filter
    assert _line(pg, "pricing").count() == 0 and _line(pg, "passkey").count() == 1                                # the line is under the party just left
    _line(pg, "passkey").locator(".arena-atwork__more").click()                                                   # three long names: only *and 3 more* fits, and it picks nothing
    pg.locator('.arena[data-goal="passkey"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(OPEN).get_attribute("data-goal") == "passkey" and pg.locator(".arena-goal.is-on").count() == 0


def test_a_press_on_and_k_more_shows_that_party_with_no_pick(worked):
    pg = worked
    pg.locator('.arena-phead[data-goal="weekly"]').click()                                                         # a pick left in weekly from before ...
    pg.locator('.arena[data-goal="weekly"]').wait_for(timeout=WAIT_MS)
    pg.locator(".arena-goal[data-slug=digest] .arena-goal__main").click()
    pg.locator(".arena-goal[data-slug=digest].is-on").wait_for(timeout=WAIT_MS)
    pg.locator('.arena-phead[data-goal="pricing"]').click()
    pg.locator('.arena[data-goal="pricing"]').wait_for(timeout=WAIT_MS)
    _line(pg, "weekly").locator(".arena-atwork__more").click()
    pg.locator('.arena[data-goal="weekly"]').wait_for(timeout=WAIT_MS)
    assert pg.locator(OPEN).get_attribute("data-goal") == "weekly"
    assert pg.locator(".arena-goal.is-on").count() == 0 and pg.locator(".arena-goal.is-off").count() == 0         # ... is gone: no pick


def test_the_goals_are_buttons_beside_the_headings_button_never_inside_it(worked):
    pg = worked
    assert pg.locator("button button").count() == 0 and pg.locator(".arena-phead .arena-atwork, .arena-phead .arena-atwork__goal").count() == 0
    line = _line(pg, "pricing")
    assert line.locator("button").count() == 2 and line.evaluate("e => e.previousElementSibling.matches('button.arena-phead')")
    pg.locator('.arena-phead[data-goal="pricing"]').focus()                                                       # the arrows still move between the headings
    pg.keyboard.press("ArrowDown")
    assert pg.evaluate("document.activeElement.dataset.goal") == "weekly"
    pg.keyboard.press("ArrowUp")
    assert pg.evaluate("document.activeElement.dataset.goal") == "pricing"
    pg.keyboard.press("Tab")
    assert pg.evaluate("document.activeElement.dataset.slug") == "billing"                                         # and the line's goals are the next stops


def test_the_line_is_quiet_the_muted_ink_in_the_text_face(worked):
    pg = worked
    line = _line(pg, "pricing")
    resolve = "(v) => { const e = document.createElement('i'); e.style.color = v; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }"
    muted, danger, alert = (pg.evaluate(resolve, f"var(--ork-{k})") for k in ("ink-muted", "danger", "alert"))
    assert line.evaluate("e => getComputedStyle(e).color") == muted
    for sel in (".arena-atwork__goal", ".arena-atwork__sign", ".arena-atwork__dot"):
        assert line.locator(sel).first.evaluate("e => getComputedStyle(e).color") == muted != danger != alert
    assert line.locator(".arena-atwork__goal").first.evaluate("e => getComputedStyle(e).fontFamily") == pg.locator(".arena-phead__name").first.evaluate("e => getComputedStyle(e).fontFamily")
    if os.environ.get("ORKCRAFT_SHOTS"):
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / "desktop-at-work-line-1440x900.png"))
