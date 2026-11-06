"""A potion lights the column's cards that wait for its tool, and one place moves at a time (docs/specs/138-the-day-read-from-the-resets.md A.1-A.4, decisions §245.2;
docs/specs/140-the-window-made-lighter.md C3, decisions §247.8): hovering a potion dims the cards whose goal does not wait for its tool (never hidden), its words say goals wait
for its reset (never how many), a column card hovered hatches its next step's share off its tool's potion, and of two goals at work only the picked one, else the first, glows."""
from __future__ import annotations

import datetime as dt

import pytest

pytest.importorskip("playwright")
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, open_column  # noqa: E402
from tests.test_hand_desktop_browser import head, node, task  # noqa: E402
from tests.test_hand_mana_browser import TWO  # noqa: E402

pytestmark = pytest.mark.browser


class DayHost(ColumnHost):
    """The column's project with a second goal at work, one at work held by Codex's spent window, and a plan's estimate on the first goal of To review."""

    def __init__(self):
        super().__init__()
        self.limits = TWO
        later = (dt.datetime.now() + dt.timedelta(hours=2)).replace(microsecond=0).isoformat()
        first = next(n for n in self.nodes if n["slug"] == "timer")
        first["plan_estimate"] = {"usd_low": 1.0, "usd_high": 2.0}
        second = node("sound", "tech", "Sound for the round", "table", state="working", element="dust", stage="implementation", tasks=[task("s1", "Make the sound", "running", head=head("dryad", "design"))])
        waiting = node("codexwait", "tech", "Tidy the lobby", "table", state="working", element="ice", stage="implementation", held_until=later, held_tool="codex", tasks=[task("c1", "Tidy", "ready")])
        self.nodes = [*self.nodes[:-1], second, waiting, self.nodes[-1]]


def dimmed(pg):
    return sorted(pg.locator(".col-card.is-dim").evaluate_all("els => els.map((e) => e.dataset.goal)"))


def shown(pg):
    return sorted(pg.locator(".col-card").evaluate_all("els => els.map((e) => e.dataset.goal)"))


def potion(pg, provider):
    return pg.locator(f'.hand-mana .hand-pot[data-provider="{provider}"]')


def test_hovering_a_potion_dims_the_cards_not_waiting_for_its_tool_and_never_hides_them(gui):
    pg, host, log = open_column(gui, host=DayHost())
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        every = shown(pg)
        assert dimmed(pg) == [], "no potion hovered: no card dimmed"
        narrow.unroll_drum(pg)
        potion(pg, "claude").hover()
        pg.wait_for_selector(".col-card.is-dim", timeout=WAIT_MS)
        assert shown(pg) == every, "dimmed, never hidden"
        assert [g for g in every if g not in dimmed(pg)] == ["scoring", "timer"], "the cards of To review start on the default tool (Claude): they alone stay lit"
        assert pg.locator('.col-card[data-goal="timer"]').evaluate("e => getComputedStyle(e).opacity") == "1"
        assert float(pg.locator('.col-card[data-goal="music"]').evaluate("e => getComputedStyle(e).opacity")) < 1
        potion(pg, "codex").hover()
        pg.wait_for_function("() => document.querySelectorAll('.col-card:not(.is-dim)').length === 1", timeout=WAIT_MS)
        assert [g for g in every if g not in dimmed(pg)] == ["codexwait"], "the goal at work held by Codex's spent window waits for Codex's reset"
        pg.mouse.move(5, 300)
        pg.wait_for_function("() => document.querySelectorAll('.col-card.is-dim').length === 0", timeout=WAIT_MS)
        pg.locator(".hand-mana__drum").focus()                                                                                 # the focus unrolls the row
        pg.locator(".hand-mana[data-open]").wait_for(timeout=WAIT_MS)
        potion(pg, "claude").focus()
        pg.wait_for_selector(".col-card.is-dim", timeout=WAIT_MS)
        pg.evaluate("() => document.activeElement.blur()")
        pg.wait_for_function("() => document.querySelectorAll('.col-card.is-dim').length === 0", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_potions_words_say_goals_wait_for_its_reset_when_any_does_and_never_how_many(gui):
    pg, host, log = open_column(gui, host=DayHost())
    try:
        pg.wait_for_selector(".hand-mana .hand-pot", state="attached", timeout=WAIT_MS)
        for provider in ("claude", "codex"):
            words = potion(pg, provider).get_attribute("aria-label")
            assert words.endswith("Goals wait for its reset") and not any(c.isdigit() for c in words.split("Goals")[1]), words
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_potion_no_goal_waits_for_says_nothing_of_goals(gui):
    host = ColumnHost()
    host.limits = TWO
    pg, host, log = open_column(gui, host=host)
    try:
        pg.wait_for_selector(".hand-mana .hand-pot", state="attached", timeout=WAIT_MS)
        assert "Goals wait" in potion(pg, "claude").get_attribute("aria-label") and "Goals wait" not in potion(pg, "codex").get_attribute("aria-label")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_column_card_hovered_hatches_its_next_steps_share_off_its_tools_potion(gui):
    pg, host, log = open_column(gui, host=DayHost())
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        claude = potion(pg, "claude")
        assert "--ork-potion-spend" not in claude.locator(".ork-potion").get_attribute("style")
        pg.locator('.col-card[data-goal="timer"]').dispatch_event("pointerenter")
        pg.wait_for_function("() => document.querySelector('.hand-pot[data-provider=claude] .ork-potion').getAttribute('style').includes('--ork-potion-spend')", timeout=WAIT_MS)
        assert "--ork-potion-spend:0.04" in claude.locator(".ork-potion").get_attribute("style").replace(" ", "")
        assert "--ork-potion-spend" not in potion(pg, "codex").locator(".ork-potion").get_attribute("style")
        pg.locator('.col-card[data-goal="timer"]').dispatch_event("pointerleave")
        pg.wait_for_function("() => !document.querySelector('.hand-pot[data-provider=claude] .ork-potion').getAttribute('style').includes('--ork-potion-spend')", timeout=WAIT_MS)
        pg.locator('.col-card[data-goal="scoring"]').dispatch_event("pointerenter")                                       # no cost on the node: nothing hatched
        pg.wait_for_timeout(200)
        assert "--ork-potion-spend" not in claude.locator(".ork-potion").get_attribute("style")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def glowing(pg):
    return sorted(pg.locator(".col-card--up .ork-elem.is-glowing").evaluate_all("els => [...new Set(els.map((e) => e.closest('.col-card').dataset.goal))]"))


class WorkOnlyHost(DayHost):
    """Nothing in In analysis is being worked on: the first goal at work in the column's order is the Orkmaster's At work pile's first."""

    def __init__(self):
        super().__init__()
        self.nodes = [n for n in self.nodes if n["slug"] not in ("reading", "talk")]


def test_with_two_goals_at_work_one_glows_the_one_picked_else_the_first(gui):
    pg, host, log = open_column(gui, host=WorkOnlyHost())
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        assert pg.locator('.col-card--up[data-pile="work"]:not([data-off])').count() >= 3, "goals at work: music, sound and the one held"
        assert glowing(pg) == ["music"], "none picked: the first at work in the column's order, and no other"
        pg.locator('.col-card--up[data-goal="sound"]').dispatch_event("click")                                      # picked: the one that moves
        pg.wait_for_function("() => document.querySelector('.col-card[data-goal=sound]').classList.contains('ork-picked')", timeout=WAIT_MS)
        assert glowing(pg) == ["sound"], glowing(pg)
        pg.locator('.col-card--up[data-goal="sound"]').dispatch_event("click")                                      # picked again: none picked, the first again
        pg.wait_for_function("() => !document.querySelector('.col-card[data-goal=sound]').classList.contains('ork-picked')", timeout=WAIT_MS)
        assert glowing(pg) == ["music"], glowing(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_lifted_backs_rune_glows_only_while_its_goal_is_the_one_that_moves(gui):
    """Spec 147 B.2: the Orkmaster's hand has no ring any more; the goal being read is lifted and its rune glows, and (spec 140 C3) it is still while another goal is picked."""
    pg, host, log = open_column(gui, host=DayHost())
    try:
        pg.wait_for_selector(".col-card--fan", timeout=WAIT_MS)
        down = pg.locator(".col-card--fan").first
        assert "is-reading" in down.get_attribute("class").split() and down.locator(".ork-elem.is-glowing").count() == 1, "the Orkmaster is reading: it is the first goal at work in the column's order"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-card--fan .ork-elem.is-glowing')).animationName") == "ork-glow"
        assert glowing(pg) == [], "the goals at work lie still: the reading goal is the one that moves"
        pg.locator('.col-card--up[data-goal="sound"]').dispatch_event("click")
        pg.wait_for_function("() => document.querySelector('.col-card[data-goal=sound]').classList.contains('ork-picked')", timeout=WAIT_MS)
        assert down.locator(".ork-elem.is-glowing").count() == 0, "its rune rests: another goal is picked"
        assert glowing(pg) == ["sound"]
    finally:
        pg.close()
    assert not log, "\n".join(log)
