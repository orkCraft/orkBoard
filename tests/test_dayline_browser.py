"""The day over the pane (docs/specs/138-the-day-read-from-the-resets.md part C, decisions §245.6), in a real browser against a stub host: a potion pressed opens a line of time with *Now* across it; ahead the tool's resets
as marks (a 5-hour window repeated every five hours) and the goals that wait for them as cards on the reset they wait for (their rune, short name and the step in words); the person's hours as a band when they are set; behind *Now* what
used the tool today; the old list stays under the line; a card pressed picks its goal and nothing else. The pure helpers (`table/dayline.js`) are called through the page."""
from __future__ import annotations

import datetime as dt

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, node, open_hand, sig  # noqa: E402
from tests.test_hand_mana_browser import pots  # noqa: E402

pytestmark = pytest.mark.browser


def at(hours: float) -> str:
    return (dt.datetime.now() + dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M")


class DayHost(HandHost):
    """Claude's 5-hour window resets in two hours and its week in three days; two goals wait for the first reset (one in Talk, one with its spec to write), one goal waits for Codex's; `hours` are the person's."""

    def __init__(self, hours=None):
        super().__init__(bare=True)
        self.hours = hours or []
        self.limits = [{"provider": "claude", "name": "Claude Code", "left": 0.0, "rows": [{"window": "5h", "left": 0.0, "reset": at(2)}, {"window": "week", "left": 0.6, "reset": at(72)}]},
                       {"provider": "codex", "name": "Codex", "left": 0.5, "rows": [{"window": "week", "left": 0.5, "reset": at(30)}]},
                       {"provider": "agy", "name": "Antigravity", "left": 0.9, "rows": [{"window": "week", "left": 0.9, "reset": at(40)}]}]
        talk = node("talky", "tech", "Talk about the lobby", "table", state="talk", element="ice", held_until=at(2), held_tool="claude")
        spec = node("specky", "tech", "Spec the export", "table", state="raw", element="lava", held_until=at(2), held_tool="claude")
        other = node("codexy", "design", "A codex goal", "table", state="raw", element="meadow", held_until=at(30), held_tool="codex")
        self.nodes = [talk, spec, other]

    def handle(self, name, a):
        if name == "ideas.board":
            return super().handle(name, a) | {"hours": self.hours}
        if name == "ideas.usage":
            self.log.append((name, a))
            return {"provider": a["provider"], "name": "Claude", "left": 0.0, "window": "5h", "reset": at(2), "scope": "project", "scopes": ["project"], "tokens_only": False, "estimated": True, "outside": 10,
                    "rows": [{"party": "tech", "title": "Tech", "share": 60, "tokens": 5, "members": []}, {"party": "design", "title": "Design", "share": 30, "tokens": 3, "members": []}]}
        return super().handle(name, a)


def open_line(gui, host, width="wide", provider="claude"):
    pg, host, log = open_hand(gui, host, width)
    pots(pg)
    pg.locator(f'.hand-mana .hand-pot[data-provider="{provider}"]').click()
    pg.locator('.table-over[data-kind="limits"] .dayline').wait_for(timeout=WAIT_MS)
    return pg, host, log


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_line_has_now_the_resets_ahead_and_the_waiting_goals_on_their_reset(gui, width):
    pg, host, log = open_line(gui, DayHost(), width)
    try:
        line = pg.locator(".dayline")
        assert line.locator(".dayline__nowword").inner_text() == "Now"
        assert pg.locator("[data-title]").inner_text().lower().endswith("claude code: what used it")                             # the view is the same one
        first = line.locator(".dayline__row").first
        assert first.get_attribute("data-provider") == "claude"                                                                      # the pressed tool on top
        resets = first.locator(".dayline__reset")
        stamps = [r.get_attribute("data-reset") for r in resets.all()]
        assert stamps[0] == at(2)[-5:] and len(stamps) >= 3                                                                          # the 5 hours repeated every five hours
        cards = resets.first.locator(".dayline__card")
        assert {c.get_attribute("data-goal"): c.get_attribute("data-step") for c in cards.all()} == {"talky": "Talk", "specky": "spec"}   # on the reset they wait for, the step in words
        assert "Talk about the lobby" in cards.first.inner_text() + cards.last.inner_text()
        rows = [r.get_attribute("data-provider") for r in line.locator(".dayline__row").all()]
        assert rows == ["claude", "codex"]                                                                                           # then the tools that have goals waiting (agy has none)
        assert line.locator(".dayline__hours").count() == 0                                                                          # no hours set, no band
        assert pg.locator(".arena-limits .arena-limit").count() == 1 and pg.locator(".arena-usage").count() == 1                      # the old list stays under the line
        assert line.locator(".dayline__used i").count() == 2                                                                         # behind Now: what used it, by share
        assert line.locator(".dayline__now").bounding_box()["x"] < resets.first.bounding_box()["x"]                                  # Now is before the reset
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_hours_are_a_lighter_band_when_they_are_set(gui):
    hours = [{"days": [0, 1, 2, 3, 4, 5, 6], "from": "09:00", "to": "18:00"}]
    pg, host, log = open_line(gui, DayHost(hours))
    try:
        bands = pg.locator(".dayline__row").first.locator(".dayline__hours")
        assert bands.count() == 2                                                                                                    # today's and tomorrow's
        assert bands.first.bounding_box()["width"] > 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_card_pressed_picks_its_goal_and_decides_nothing(gui):
    pg, host, log = open_line(gui, DayHost())
    try:
        before = len(host.log)
        pg.locator('.dayline__card[data-goal="talky"]').click()
        assert sig(pg, "frame/state.js", "picked") == "talky"
        assert not [c for c in host.log[before:] if c[0] not in ("ideas.map", "ideas.board", "ideas.usage", "ideas.night")]                                              # only reads follow a pick
        pg.locator('.dayline__card[data-goal="talky"]').click()
        assert sig(pg, "frame/state.js", "picked") == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_helpers_lay_the_hours_and_the_resets_on_the_line(gui):
    pg, host, log = open_line(gui, DayHost())
    try:
        got = pg.evaluate("""async () => {
          const m = await import("/static/js/table/dayline.js");
          const now = new Date(2026, 10, 4, 14, 0), day = m.dayOf(now);
          const rows = [{ window: "5h", reset: "2026-11-04T16:00" }, { window: "week", reset: "2026-11-06T09:00" }];
          const resets = m.resetsAhead(rows, day).map((r) => [r.window, new Date(r.at).getHours(), new Date(r.at).getDate()]);
          const bands = m.bandsOf([{ days: [2], from: "22:00", to: "02:00" }], day).map((b) => [new Date(b.from).getDate(), new Date(b.from).getHours(), new Date(b.to).getDate(), new Date(b.to).getHours()]);
          return { now: m.posOf(day.now, day), edge: m.posOf(day.start - 1, day), resets, bands, ticks: m.ticksOf(day).length, step: [m.stepWord({ state: "talk" }), m.stepWord({ state: "raw" }), m.stepWord({ state: "working" })] };
        }""")
        assert got["now"] == pytest.approx(14 / 48) and got["edge"] == 0 and got["ticks"] == 8
        assert got["resets"] == [["5h", 16, 4], ["5h", 21, 4], ["5h", 2, 5], ["5h", 7, 5], ["5h", 12, 5], ["5h", 17, 5], ["5h", 22, 5]]       # every five hours; the week's reset is beyond tomorrow
        assert got["bands"] == [[4, 22, 5, 2]]                                                                                          # Wednesday night over midnight into Thursday
        assert got["step"] == ["Talk", "spec", "work"]
    finally:
        pg.close()
    assert not log, "\n".join(log)
