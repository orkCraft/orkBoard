"""Spec 149 H (docs/specs/149-what-a-goal-on-local-codex-found.md §H): a goal's result in the page says what it promised (its *Done when* lines) over what it made (each merged task with the files and lines
it changed and its gate), and its spend in what is known: with no price, the tokens and the share of the tool's window, never a dollar. The host is the hand's stub."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand, sig  # noqa: E402


class ResultHost(HandHost):
    """The hand's stub, whose goal *music* (done, one merged task) is read as the host reads a Codex goal: tokens and a share, no dollars."""

    def __init__(self, spend, **more):
        super().__init__(**more)
        self.spend = spend

    def handle(self, name, a):
        if name == "ideas.spend":
            self.log.append((name, a))
            return self.spend
        if name == "ideas.goal_result":
            self.log.append((name, a))
            return {"idea": a["idea"], "state": "done", "parties": [{"party": "tech", "title": "Tech", "parts": [], "done_when": [
                {"text": "The host predicts the hue per shape", "state": ""}, {"text": "The phone says the same", "state": ""}]}],
                    "made": [{"task": "m1", "title": "Make the loop", "files": 3, "added": 40, "removed": 2, "gate": "97 passed"}]}
        return super().handle(name, a)


UNPRICED = {"usd": None, "unpriced": 4, "tokens": 3_100_000, "share": {"tool": "codex", "name": "Codex", "window": "week", "share": 2.0},
            "stages": {"goal": {"usd": None, "tokens": 100, "calls": 1}, "work": {"usd": None, "tokens": 3_099_900, "calls": 3}}}
PRICED = {"usd": 1.2, "unpriced": 0, "tokens": 5000, "share": None, "stages": {"goal": {"usd": 0.2}, "work": {"usd": 1.0}}}


def _open_result(pg, slug="music"):
    box = pg.locator("#table-pane")
    pg.locator(".hand-done").click()
    box.get_by_role("region", name="Done, not yet seen").locator(f'.hand-drow[data-slug="{slug}"]').click()
    box.locator(f'.hand-result[data-idea="{slug}"]').wait_for(timeout=WAIT_MS)
    return box.locator(f'.hand-result[data-idea="{slug}"]')


def test_a_result_sets_what_it_promised_over_what_it_made_and_says_its_spend_in_tokens_and_the_share_with_no_price(gui):
    pg, host, log = open_hand(gui, host=ResultHost(UNPRICED))
    try:
        result = _open_result(pg)
        pg.wait_for_function("() => document.querySelector('.hand-result__promised')", timeout=WAIT_MS)
        assert result.locator("p.cap[title]").inner_text() == "This goal so far: 3.1 million tokens · about 2% of Codex's week"
        assert "$" not in result.inner_text(), "no dollar where there is no price"
        promised = result.locator(".hand-result__promised li").all_inner_texts()
        assert promised == ["The host predicts the hue per shape", "The phone says the same"]
        heads = [h.lower() for h in result.locator("h3").all_text_contents()]
        assert heads.index("done when") < heads.index("what it made"), "the promise is read over what was made"
        made = result.locator(".hand-result__made li").first
        assert "Add the lobby loop" in made.inner_text() and made.locator(".hand-result__gate").inner_text() == "3 files, +40 −2 · 97 passed"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_result_with_a_price_says_the_price_as_before(gui):
    pg, host, log = open_hand(gui, host=ResultHost(PRICED))
    try:
        result = _open_result(pg)
        pg.wait_for_function("() => document.querySelector('.hand-result__promised')", timeout=WAIT_MS)
        assert "This goal so far: " in result.inner_text() and "million tokens" not in result.inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_tokens_and_the_share_are_said_in_few_words(gui):
    pg, host, log = open_hand(gui, host=ResultHost(UNPRICED))
    try:
        words = pg.evaluate("""async () => { const { spendWords, tokenWords, shareWords } = await import('/static/js/shell/preview.js');
          return [tokenWords(3100000), tokenWords(412000), tokenWords(900), tokenWords(1), shareWords({ name: 'Codex', window: 'week', share: 0.4 }),
                  shareWords({ name: 'Codex', window: '5h', share: 12 }), shareWords({ name: 'Codex', window: 'month', share: 3 }), shareWords(null),
                  spendWords({ usd: null, tokens: 0, stages: {} }), spendWords({ usd: null, tokens: 5000, stages: {}, share: null })]; }""")
        assert words == ["3.1 million tokens", "412 thousand tokens", "900 tokens", "1 token", "under 1% of Codex's week", "about 12% of Codex's five-hour window", "", "",
                         "This goal so far: —", "This goal so far: 5 thousand tokens"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_route_with_no_price_says_its_calls_and_has_no_dollar_chip(gui):
    pg, host, log = open_hand(gui, host=ResultHost(UNPRICED))
    try:
        got = pg.evaluate("""async () => { const { costLine } = await import('/static/js/hand/routecard.js');
          return [costLine({ calls: 3, usd_low: null, usd_high: null }), costLine({ calls: 4, usd_low: 0.5, usd_high: 1.5 })]; }""")
        assert got[0]["words"] == "about 3 calls" and not got[0]["spend"], "calls only: no gem, no dollars"
        assert got[1]["words"].startswith("about 4 calls, about ") and got[1]["spend"], "a price is said as before"
    finally:
        pg.close()
    assert not log, "\n".join(log)
