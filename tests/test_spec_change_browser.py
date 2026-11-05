"""Spec 144 D (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md; decisions §224.4, §225.2–3) in a real browser against the table's stub host: on the Orkmaster's head with a goal picked whose spec is made, the bubble's field
says before it is sent where the words would go (*It goes to Tech, Art · about 3 calls*, from `ideas.spec_change_preview`, debounced) and **Change the spec** sends `ideas.spec_change`; the goal's card in To review says *Held while its leaders
rewrite*; the one card in the hand (hand/specchangecard.js): the Orkmaster's crowned head as its asker, the person's words, a tab a party with *Now* and *Proposed*, the join's line, the cost, **Accept and start** (or *Accept · starts after
the reset, Mon 09:00* when the limits run low), **Talk more** and **Drop it**; while its leaders rewrite it says so and has **Drop it** only."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_ask_desktop_browser import AskHost, bubble, field, head, opened, settled, start  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

RESULTS_TITLE = "Results screen with the round's best answer"         # the stub host's goal `results`: tech, planning (its spec is being made)
SAID = "Show the winner first, with a banner"


class SpecHost(AskHost):
    """The ask host that also answers the spec change's commands: the preview names Tech and Art, the change makes an `asking` row, the take and the drop remove it."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.reset = ""

    def handle(self, name, a):
        if name == "ideas.spec_change_preview":
            self.log.append((name, a))
            return {"ok": True, "id": "", "via": "spec_change", "parties": [{"party": "tech", "title": "Tech"}, {"party": "art", "title": "Art"}], "estimate": {"calls": 3, "usd_low": 0.1, "usd_high": 0.4}}
        if name == "ideas.spec_change":
            self.log.append((name, a))
            self.needs = [row(status="asking", parties=[])]
            self.push()
            return {"ok": True, "id": "s1", "via": "spec_change", "parties": [], "estimate": {}}
        if name in ("ideas.spec_change_take", "ideas.spec_change_drop", "ideas.spec_change_more"):
            self.log.append((name, a))
            self.needs = [n for n in self.needs if n.get("id") != a["id"]]
            self.push()
            return {"ok": True, "starts": "wait", "text": SAID}
        return super().handle(name, a)


def row(status="ready", **more):
    base = {"kind": "spec_change", "asker": "orkmaster", "idea": "results", "id": "s1", "task": "s1", "goal": "tech", "said": SAID, "status": status, "text": "The banner and the list agree.", "blocks": False,
            "title": RESULTS_TITLE, "priority": "normal", "at": "2026-11-04T09:00:00", "level": "spec", "calls": 3, "usd_low": 0.2, "usd_high": 0.6, "error": "", "low": False, "reset": "",
            "agree": {"ok": True, "line": "The banner and the list agree."},
            "parties": [{"party": "tech", "title": "Tech", "why": "The list shows the winner first.", "before": {"tasks": [{"id": "k2", "title": "Results list", "short": "List", "op": "change"}], "lines": ["changed Results — plain list"]},
                         "after": {"tasks": [{"id": "k2", "title": "Winner first", "short": "Winner", "op": "change"}], "lines": ["changed Results — the winner first"]}},
                        {"party": "art", "title": "Art", "why": "A banner above it.", "before": {"tasks": [], "lines": ["changed Banner — none"]}, "after": {"tasks": [], "lines": ["new Winner banner — drawn above the list"]}}]}
    return {**base, **more}


@pytest.fixture
def asked(gui):
    pg, host, errors = start(gui, "wide", SpecHost())
    yield pg, host
    pg.context.close()
    assert not errors, "\n".join(errors)


def pick(pg, slug):
    pg.evaluate(f"() => import('/static/js/frame/state.js').then((m) => {{ m.picked.value = {slug!r}; }})")


# -- the field on the Orkmaster's head ----------------------------------------------------------------------------------------------------

def test_the_field_says_where_the_words_go_before_they_are_sent_and_change_the_spec_sends_them(asked):
    pg, host = asked
    pick(pg, "results")
    opened(pg)
    change = bubble(pg).get_by_role("button", name="Change the spec")
    assert change.count() == 1 and change.is_disabled() and bubble(pg).locator("[data-spec-goes]").count() == 0, "nothing typed: nothing said"
    field(pg).fill(SAID)
    goes = bubble(pg).locator("[data-spec-goes]")
    goes.wait_for(timeout=WAIT_MS)
    assert goes.inner_text().strip() == "It goes to Tech, Art · about 3 calls" and host.sent("ideas.spec_change") == []
    assert host.sent("ideas.spec_change_preview")[-1] == {"idea": "results", "text": SAID}
    assert change.is_enabled()
    change.click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert host.sent("ideas.spec_change") == [{"idea": "results", "text": SAID}]
    assert host.sent("ideas.ask") == [], "it was a change, not a question"


def test_a_leaders_tab_and_a_goal_not_picked_have_no_change_the_spec(asked):
    pg, host = asked
    opened(pg)
    assert bubble(pg).get_by_role("button", name="Change the spec").count() == 0, "no goal picked"
    head(pg).click()
    bubble(pg).wait_for(state="detached", timeout=WAIT_MS)
    open_tab(pg, "tech")
    pick(pg, "results")
    opened(pg, "tech")
    assert bubble(pg).get_by_role("button", name="Change the spec").count() == 0, "a leader's tab: its own change, as built"


# -- the card in the hand -----------------------------------------------------------------------------------------------------------------

def lifted_card(pg):
    card = pg.locator('.hand-card[data-kind="spec_change"]')
    card.wait_for(timeout=WAIT_MS)
    card.click(position={"x": 10, "y": 20})
    lifted = pg.locator(".hand-lifted")
    lifted.wait_for(timeout=WAIT_MS)
    return lifted


def test_the_card_has_a_tab_a_party_now_and_proposed_the_joins_line_the_cost_and_three_acts(asked):
    pg, host = asked
    host.needs = [row()]
    host.push()
    card = pg.locator('.hand-card[data-kind="spec_change"]')
    card.wait_for(timeout=WAIT_MS)
    assert card.locator(".ork-gem").get_attribute("data-cost") == "$0.20–0.60" and card.locator(".corner--foot img, .hand-card__asker svg, .hand-card__asker .ork-head").count() >= 1, "its asker: the Orkmaster's head"
    lifted = lifted_card(pg)
    assert f"You said: “{SAID}”" in lifted.inner_text() and "The banner and the list agree." in lifted.inner_text() and lifted.locator(".hand-spend").count() == 1
    tabs = lifted.get_by_role("tab")
    assert [t.inner_text().strip().title() for t in tabs.all()] == ["Tech", "Art"] and tabs.nth(0).get_attribute("aria-selected") == "true"
    now, proposed = lifted.locator('[data-side="now"]'), lifted.locator('[data-side="proposed"]')
    assert "~ Results — plain list" in now.inner_text() and "~ Results — the winner first" in proposed.inner_text() and "Winner" in proposed.inner_text()
    tabs.nth(1).click()
    assert "~ Banner — none" in now.inner_text() and "+ Winner banner — drawn above the list" in proposed.inner_text() and "A banner above it." in lifted.inner_text()
    for name in ("Accept and start", "Talk more", "Drop it"):
        assert lifted.get_by_role("button", name=name).count() == 1, name
    lifted.get_by_role("button", name="Accept and start").click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"spec_change\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.spec_change_take") == [{"idea": "results", "id": "s1", "via": "hand"}]


def test_with_the_limits_low_accept_says_it_starts_after_the_reset(asked):
    pg, host = asked
    host.needs = [row(low=True, reset="2026-11-09T09:00:00")]
    host.push()
    lifted = lifted_card(pg)
    assert lifted.get_by_role("button", name="Accept and start").count() == 0
    accept = lifted.locator('[data-act="accept"]')
    assert accept.inner_text().startswith("Accept · starts after the reset, Mon 09:00"), accept.inner_text()


def test_drop_it_changes_nothing_and_talk_more_opens_the_bubble_again_with_the_words_kept(asked):
    pg, host = asked
    host.needs = [row()]
    host.push()
    lifted_card(pg).get_by_role("button", name="Drop it").click()
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"spec_change\"]')", timeout=WAIT_MS)
    assert host.sent("ideas.spec_change_drop") == [{"idea": "results", "id": "s1", "via": "hand"}] and host.sent("ideas.spec_change_take") == []
    host.needs = [row()]
    host.push()
    lifted_card(pg).get_by_role("button", name="Talk more").click()
    bubble(pg).wait_for(timeout=WAIT_MS)
    settled(pg)
    assert bubble(pg).get_attribute("data-ask") == "orkmaster" and field(pg).input_value() == SAID and len(host.sent("ideas.spec_change_more")) == 1


def test_while_its_leaders_rewrite_the_card_says_so_and_has_drop_it_only_and_the_goals_card_is_held(asked):
    pg, host = asked
    next(n for n in host.nodes if n["slug"] == "results").update(state="plan", agreed=True, changing=True)
    host.needs = [row(status="asking", parties=[])]
    host.push()
    lifted = lifted_card(pg)
    assert "Its leaders are rewriting" in lifted.inner_text() and lifted.get_by_role("tab").count() == 0
    assert [b.inner_text().strip() for b in lifted.locator(".hand-answers button").all()] == ["Drop it"]
    card = pg.locator('.col-card[data-goal="results"]')
    card.wait_for(timeout=WAIT_MS)
    assert "Held while its leaders rewrite" in card.get_attribute("aria-label") and card.get_attribute("data-changing") == "1"      # a back has no words on its face (spec 147 B.3): its label says it, the card marks it
