"""Spec 131 C (docs/specs/131-a-leaders-slices-and-the-cascade.md §C; decisions §233.8–§233.9, §237.5–§237.6) in a real browser against the table's stub host: the cascade's card in the hand (hand/cascadecard.js), the
row `cascade` of realm/cascades.py `rows`. The card lies in its proposer's lane with the page sign, *Proposes*, the new decision's title and the cost of what follows; lifted, with no fork it says one line (*Tech and Art agree*)
and **More** opens the chain (each part before and after); with a fork the fork comes first, Confirm waits for its answer and sends it with `fork_answers`; *Stopped after 3 steps* is said; **Confirm and start** sends
`ideas.cascade_confirm {id}` and **Put it back** `ideas.cascade_back {id}`. The leader's bubble draws a `§N` of its answer and of its sources as a link that opens that decision. The phone's hand (upright) draws the same card.
Screenshots to $CASCADE_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import AskHost, bubble, head, opened, record, start  # noqa: E402
from tests.test_hand_context_narrow_browser import UprightHost, open_up  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["CASCADE_SHOTS"]) if os.environ.get("CASCADE_SHOTS") else None
TITLE = "Screens hold the timer for 6 seconds"
CARD = '.hand-card[data-kind="cascade"]'
GONE = "() => !document.querySelector('.hand-card[data-kind=\"cascade\"]')"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(SHOTS / name))


def cascade(forks=(), stopped="", **more):
    """The row as realm/cascades.py `rows` serves it (a row of no goal's: `party` is the proposer's)."""
    chain = [{"party": "tech", "name": "Tech", "slice": "s-1", "before": "Your screens hold 10 seconds (§159.1).", "after": "Your screens hold 6 seconds (§240.2)."},
             {"party": "art", "name": "Art", "slice": "s-2", "before": "The timer ring has ten ticks.", "after": "The timer ring has six ticks."}]
    base = {"kind": "cascade", "id": "c-1", "party": "tech", "title": TITLE, "text": TITLE, "line": "Tech and Art agree" if not forks else "; ".join(f"{f['name']} disagrees: {f['why']}" for f in forks),
            "proposal": {"party": "tech", "says": "Your screens hold 6 seconds (§240.2).", "why": "the lobby test showed ten seconds is too long", "before": "Your screens hold 10 seconds (§159.1)."},
            "chain": chain, "forks": list(forks), "stopped": stopped, "cost": 0.11, "sections": [{"idea": "results", "party": "tech"}, {"idea": "seat", "party": "tech"}], "level": "decision",
            "usd_low": 0.2, "usd_high": 0.6, "blocks": False, "priority": "normal", "at": "2026-11-04T09:00:00"}
    return {**base, **more}


FORK = {"party": "design", "name": "Design", "slice": "s-3", "now": "Your look keeps the ring full.", "says": "Your look drops the ring.", "why": "a full ring is the look of the product"}


class CascadeHost(AskHost):
    """The ask host that also answers the cascade's commands and the decision a link opens, keeping the Needs you rows the test puts."""

    def handle(self, name, a):
        if name in ("ideas.cascade_confirm", "ideas.cascade_back"):
            self.log.append((name, a))
            self.needs = [n for n in self.needs if n.get("id") != a["id"]]
            self.push()
            return {"ok": True, "number": 241, "title": TITLE, "slices": 2, "sections": [{"idea": "results"}, {"idea": "seat"}], "left": []} if name.endswith("confirm") else {"ok": True}
        if name == "ideas.chronicle_decision":
            self.log.append((name, a))
            return {"number": a["number"], "title": "Screens hold the timer", "day": "2026-11-03", "goal": "", "entry": "Why: a test.\n1. Six seconds.", "changes": [], "changed_by": []}
        return super().handle(name, a)


@pytest.fixture
def table(gui):
    pg, host, errors = start(gui, "wide", CascadeHost())
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def lift(pg):
    pg.locator(CARD).click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_the_card_lies_in_its_proposers_lane_with_proposes_the_title_and_the_cost_of_what_follows(table):
    pg, host = table
    host.needs = [cascade()]
    host.push()
    card = pg.locator(CARD)
    card.wait_for(timeout=WAIT_MS)
    assert card.get_attribute("data-party") == "tech" and card.locator(".ork-gem").get_attribute("data-cost") == "$0.20–0.60"
    assert TITLE in card.text_content() and "Tech and Art agree" in card.locator(".hand-card__foot").text_content()
    assert card.locator(".hand-card__asker .ork-race, .corner--foot img, .hand-card__asker").count() >= 1, "the proposing leader's head"
    assert pg.locator('.hand-lane[data-lane="1"] ' + CARD).count() + pg.locator('.hand-lane[data-lane="2"] ' + CARD).count() >= 1, "under a party's lane, not the first"
    shot(pg, "cascade-card.png")


def test_lifted_with_no_fork_it_says_one_line_more_opens_the_chain_and_confirm_sends_the_id(table):
    pg, host = table
    host.needs = [cascade()]
    host.push()
    lifted = lift(pg)
    text = " ".join(lifted.text_content().split())                 # the kind's word is drawn in the label face (capitals): read the text itself
    assert "Proposes" in text and TITLE in text and "the lobby test showed ten seconds is too long" in text and "Tech and Art agree" in text
    assert "Written again:" in text
    assert lifted.locator("[data-fork]").count() == 0 and lifted.locator("[data-part=chain]").count() == 0
    lifted.get_by_role("button", name="More").click()
    chain = lifted.locator("[data-part=chain]")
    assert [li.get_attribute("data-party") for li in chain.locator("li").all()] == ["tech", "art"]
    assert "Your screens hold 10 seconds" in chain.inner_text() and "The timer ring has six ticks." in chain.inner_text()
    assert lifted.get_by_role("button", name="Put it back").count() == 1, "one Put it back: the host's"
    assert lifted.locator(".hand-spend").count() == 1, "the cost, in words"
    shot(pg, "cascade-lifted.png")
    lifted.get_by_role("button", name="Confirm and start").click()
    pg.wait_for_function(GONE, timeout=WAIT_MS)
    assert host.sent("ideas.cascade_confirm") == [{"id": "c-1", "via": "hand"}]


def test_put_it_back_sends_the_id_and_the_card_goes(table):
    pg, host = table
    host.needs = [cascade()]
    host.push()
    lift(pg).get_by_role("button", name="Put it back").click()
    pg.wait_for_function(GONE, timeout=WAIT_MS)
    assert host.sent("ideas.cascade_back") == [{"id": "c-1", "via": "hand"}] and host.sent("ideas.cascade_confirm") == []


def test_a_fork_comes_first_confirm_waits_for_its_answer_and_stopped_is_said(table):
    pg, host = table
    host.needs = [cascade([FORK], stopped="Stopped after 3 steps: Marketing was not asked")]
    host.push()
    lifted = lift(pg)
    fork = lifted.locator('[data-fork="s-3"]')
    assert "Design" in fork.inner_text() and "a full ring is the look of the product" in fork.inner_text() and "Your look keeps the ring full." in fork.inner_text()
    assert lifted.locator("[data-part=line]").count() == 0, "the fork is the line"
    assert "Stopped after 3 steps: Marketing was not asked" in lifted.inner_text()
    confirm = lifted.get_by_role("button", name="Confirm and start")
    assert confirm.is_disabled() and confirm.get_attribute("title") == "Answer the fork first"
    fork.locator('[data-fork-answer="change"]').click()
    assert confirm.is_enabled() and fork.locator('[data-fork-answer="change"]').get_attribute("aria-pressed") == "true"
    fork.get_by_label("Design: your own words").fill("Your look shows the ring half full.")
    assert fork.locator('[data-fork-answer="change"]').get_attribute("aria-pressed") == "false"
    confirm.click()
    pg.wait_for_function(GONE, timeout=WAIT_MS)
    assert host.sent("ideas.cascade_confirm") == [{"id": "c-1", "via": "hand", "fork_answers": {"s-3": "Your look shows the ring half full."}}]


def test_a_decision_number_in_the_bubble_answer_and_its_sources_opens_that_decision(table):
    pg, host = table
    open_tab(pg, "tech")
    host.put(record("answered", "tech", answer="The timer holds 6 seconds (§240.2).", sources=["§240.2", "Round timer shows on every phone"]))
    opened(pg, "tech")
    links = bubble(pg).locator(".table-ask__link")
    assert [b.inner_text() for b in links.all()] == ["§240.2", "§240.2"] and bubble(pg).locator(".table-ask__src", has_text="Round timer").count() == 1
    links.first.click()
    pg.locator('[data-decision="240"]').wait_for(timeout=WAIT_MS)
    assert host.sent("ideas.chronicle_decision") == [{"number": 240}]
    assert "Screens hold the timer" in pg.locator(".table-over__chronicle").inner_text()
    assert bubble(pg).count() == 0, "the bubble gives way to the page"


def test_the_phones_hand_draws_the_same_card_and_answers_it(gui):
    class Phone(UprightHost):
        def handle(self, name, a):
            if name == "ideas.cascade_confirm":
                self.log.append((name, a))
                self.needs = [n for n in self.needs if n.get("id") != a["id"]]
                return self.bump({"ok": True, "number": 241, "title": TITLE, "slices": 2, "sections": [], "left": []})
            return super().handle(name, a)

    host = Phone()
    host.needs = [cascade()]
    pg, host, log = open_up(gui, host=host)
    try:
        pg.locator(".hand-up .up-card", has_text=TITLE).first.click()                       # its entry on the screen, the card inline on it
        lifted = pg.locator('.hand-lifted[data-kind="cascade"]')
        lifted.wait_for(timeout=WAIT_MS)
        assert TITLE in lifted.inner_text() and "Tech and Art agree" in lifted.inner_text()
        lifted.get_by_role("button", name="More").click()
        assert lifted.locator("[data-part=chain] li").count() == 2
        shot(pg, "cascade-phone.png")
        narrow.no_sideways(pg)
        lifted.get_by_role("button", name="Confirm and start").click()
        pg.wait_for_function("() => !document.querySelector('.hand-lifted[data-kind=\"cascade\"]')", timeout=WAIT_MS)
        assert [a for n, a in host.log if n == "ideas.cascade_confirm"] == [{"id": "c-1", "via": "hand"}]
    finally:
        pg.close()
    assert not log, "\n".join(log)
