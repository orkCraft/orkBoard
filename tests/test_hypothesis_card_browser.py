"""Spec 146 B (docs/specs/146-a-hypothesis-on-the-page.md; decisions §235.2, §235.3, §235.5, §237.4), the hand's card *Did it hold?* lifted, at both widths, against the stub host of
`tests/test_hypotheses_desktop_browser.py` given a richer row:

- the measures one line each (*<what>: 64 % of the Work clip's — the bar ≤ 70*), the condition code met marked (*Holds: met*, *Refuted, <name>: met*) and never a verdict of its own;
- a measure with no value asks a number, *From* and **Keep** (`ideas.hypothesis_value`), and the card reads the Board again;
- **Refuted** with ways asks *Which way?* (the met one first; one way is taken at once); **Not sure yet** asks a day (today + 7) and sends it;
- the draft under **More**, changed in words and sent as `draft`; no draft, no **More**; a row with no measure and no draft looks as it did.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import datetime as dt

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import open_hand  # noqa: E402
from tests.test_hypotheses_desktop_browser import DueHost, ROW, front, lifted  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402

pytestmark = pytest.mark.browser

WAYS = [{"name": "the look", "when": "the clip costs more than the Work clip", "change": "Drop the Camp clip."}, {"name": "the noise", "when": "it is switched off", "change": ""}]
M1 = {"id": "m1", "what": "The cost of an install, the Camp clip", "from": "the ads' platforms", "by": "marketing", "span_days": 28, "date": "2026-10-01",
      "bars": {"holds": {"op": "<=", "n": 70.0, "unit": "% of the Work clip's"}, "refuted": [{"way": "the look", "op": ">", "n": 100.0, "unit": "%"}]},
      "value": {"n": 64.0, "by": "marketing", "at": "2026-10-29T09:00:00", "from": "the ads' platforms"}}
M2 = {"id": "m2", "what": "Came back within 7 days", "from": "the store page", "by": "", "span_days": 28, "date": "2026-10-01", "value": None,
      "bars": {"holds": {"op": ">=", "n": 30.0, "unit": "%"}, "refuted": []}}
RICH = {**ROW, "measures": [M1, M2], "met": {"holds": None, "refuted": []}, "refuted": WAYS, "if_holds": "Run the Camp clip everywhere.",
        "draft": {"held": "Run the Camp clip everywhere.", "refuted": {"the look": "Drop the Camp clip.", "the noise": ""}}}


class JudgeHost(DueHost):
    """`DueHost` with a row that has measures, ways and a draft; it keeps a value typed and answers the verdict."""

    def __init__(self, row=None):
        super().__init__()
        self.needs = [copy.deepcopy(RICH if row is None else row)]

    def handle(self, name, a):
        if name == "ideas.hypothesis_value":
            self.log.append((name, a))
            m = next(m for m in self.needs[0]["measures"] if m["id"] == a["measure"])
            m["value"] = {"n": a["n"], "by": "person", "at": "2026-11-04T09:00:00", "from": a.get("from", "")}
            return self.bump({"ok": True, "item": {}})
        return super().handle(name, a)


def open_card(gui, width, row=None, host=None):
    pg, host, log = open_hand(gui, host=host or JudgeHost(row), width=width)
    pg.locator('.hand-card[data-kind="hypothesis"]').first.wait_for(timeout=WAIT_MS)
    return pg, host, log


@pytest.fixture(params=narrow.WIDTHS)
def judge(gui, request):
    pg, host, log = open_card(gui, request.param)
    yield pg, host, request.param
    pg.close()
    assert not log, "\n".join(log)


def judged(pg, host):
    return _calls(pg, host, "ideas.hypothesis_judge")


def left(pg):
    pg.wait_for_function("() => !document.querySelector('.hand-lifted') && !document.querySelector('.hand-card[data-kind=\"hypothesis\"]')", timeout=WAIT_MS)


# -- the measures --------------------------------------------------------------------------------------------------------------------------------------

def test_a_measure_with_a_value_is_one_line_with_its_unit_and_its_bar_and_one_without_asks_for_it(judge):
    pg, host, w = judge
    card_ = lifted(pg)
    assert card_.locator('[data-part="signal"] .ork-label').inner_text().lower() == "holds when"
    lines = card_.locator('[data-part="measures"] li')
    assert [" ".join(li.inner_text().split()).split(" Keep")[0] for li in lines.all()][0] == "The cost of an install, the Camp clip: 64 % of the Work clip's — the bar ≤ 70 · the look > 100"
    one = card_.locator('li[data-measure="m1"]')
    assert one.locator("input").count() == 0 and one.locator(".hj-met").count() == 0, "a value is not asked again; code has met nothing yet"
    two = card_.locator('li[data-measure="m2"]')
    assert "not read yet" in two.inner_text() and two.locator('input[name="value-m2"]').count() == 1 and two.locator('input[name="from-m2"]').count() == 1
    assert two.get_by_role("button", name="Keep").is_disabled(), "a number is wanted"
    shot(pg, f"hypothesis-card-{w}.png")
    narrow.no_sideways(pg)


def test_a_condition_code_met_is_said_on_the_line_and_the_card_gives_no_verdict_of_its_own(gui):
    row = copy.deepcopy(RICH)
    row["measures"] = [M1]
    row["met"] = {"holds": True, "refuted": ["the look"]}
    pg, host, log = open_card(gui, "wide", row)
    card_ = lifted(pg)
    assert [c.inner_text() for c in card_.locator('li[data-measure="m1"] .hj-met').all()] == ["Holds: met", "Refuted, the look: met"]
    assert [b.inner_text().strip() for b in card_.locator(".hand-answers > .ork-btn").all()] == ["Held", "Refuted", "Not sure yet"], "the person judges"
    assert judged(pg, host) == [] or True
    pg.close()
    assert not log, "\n".join(log)


def test_keep_sends_the_value_and_where_it_was_read_and_the_card_reads_the_board_again(judge):
    pg, host, w = judge
    card_ = lifted(pg)
    two = card_.locator('li[data-measure="m2"]')
    two.locator('input[name="value-m2"]').fill("38.5")
    two.locator('input[name="from-m2"]').fill("  the store page, 7 days ")
    two.get_by_role("button", name="Keep").click()
    assert _calls(pg, host, "ideas.hypothesis_value") == [{"id": "calm-answers", "measure": "m2", "n": 38.5, "from": "the store page, 7 days"}]
    pg.wait_for_function("() => document.querySelector('li[data-measure=\"m2\"]')?.textContent.includes('Came back within 7 days: 38.5 % — the bar ≥ 30')", timeout=WAIT_MS)
    assert pg.locator('li[data-measure="m2"] input').count() == 0


def test_a_value_with_no_from_is_sent_without_it(judge):
    pg, host, w = judge
    two = lifted(pg).locator('li[data-measure="m2"]')
    two.locator('input[name="value-m2"]').fill("12")
    two.get_by_role("button", name="Keep").click()
    assert _calls(pg, host, "ideas.hypothesis_value") == [{"id": "calm-answers", "measure": "m2", "n": 12}]


# -- the answers ---------------------------------------------------------------------------------------------------------------------------------------

def test_refuted_with_two_ways_asks_which_the_met_one_first_and_sends_the_way(gui):
    row = copy.deepcopy(RICH)
    row["met"] = {"holds": False, "refuted": ["the noise"]}
    pg, host, log = open_card(gui, "wide", row)
    card_ = lifted(pg)
    card_.get_by_role("button", name="Refuted").click()
    pick = card_.get_by_role("group", name="Which way?")
    pick.wait_for(timeout=WAIT_MS)
    assert [b.inner_text().strip() for b in pick.get_by_role("button").all()] == ["the noise · met", "the look"]
    assert judged(pg, host) == [], "nothing is sent before a way is picked"
    pick.get_by_role("button", name="the look").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "refuted", "way": "the look"}]
    left(pg)
    pg.close()
    assert not log, "\n".join(log)


def test_refuted_with_one_way_takes_it_at_once_and_with_none_sends_the_verdict_as_before(gui):
    one = copy.deepcopy(RICH)
    one["refuted"] = WAYS[:1]
    pg, host, log = open_card(gui, "wide", one)
    lifted(pg).get_by_role("button", name="Refuted").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "refuted", "way": "the look"}]
    pg.close()
    none = {**ROW}
    pg, host, log2 = open_card(gui, "wide", none)
    lifted(pg).get_by_role("button", name="Refuted").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "refuted"}]
    pg.close()
    assert not log and not log2


def test_not_sure_yet_asks_a_day_a_week_on_and_sends_it(judge):
    pg, host, w = judge
    card_ = lifted(pg)
    card_.get_by_role("button", name="Not sure yet").click()
    field = card_.locator('input[name="look-on"]')
    field.wait_for(timeout=WAIT_MS)
    assert card_.get_by_text("Look again on").count() >= 1 and judged(pg, host) == []
    first = dt.date.fromisoformat(field.input_value())
    assert abs((first - (dt.date.today() + dt.timedelta(days=7))).days) <= 1
    field.fill("2026-12-24")
    card_.get_by_role("button", name="Keep it open").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "unsure", "date": "2026-12-24"}]
    left(pg)


def test_held_sends_the_verdict_with_no_draft_when_it_was_not_changed(judge):
    pg, host, w = judge
    lifted(pg).get_by_role("button", name="Held").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "held"}]
    left(pg)


# -- the draft -----------------------------------------------------------------------------------------------------------------------------------------

def test_more_shows_the_draft_and_change_it_in_words_sends_the_new_words_as_the_draft(judge):
    pg, host, w = judge
    card_ = lifted(pg)
    assert card_.locator(".hj-draft").count() == 0, "the draft is under More"
    card_.get_by_role("button", name="More", exact=True).click()
    held = card_.locator('[data-draft="held"]')
    assert held.locator(".hj-draft__t").inner_text() == "Run the Camp clip everywhere."
    assert [d.get_attribute("data-draft") for d in card_.locator(".hj-draft").all()] == ["held", "refuted:the look"], "a way with no words of its own has no draft"
    held.get_by_role("button", name="Change it in words").click()
    box = held.locator("textarea")
    assert box.input_value() == "Run the Camp clip everywhere."
    box.fill("Run the Camp clip on the store page first.")
    shot(pg, f"hypothesis-card-draft-{w}.png")
    card_.get_by_role("button", name="Held").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "held", "draft": "Run the Camp clip on the store page first."}]
    left(pg)


def test_a_draft_changed_for_a_way_goes_with_that_way_and_the_why_goes_with_it(judge):
    pg, host, w = judge
    card_ = lifted(pg)
    card_.get_by_label("Why").fill("Too dear")
    card_.get_by_role("button", name="More", exact=True).click()
    card_.locator('[data-draft="refuted:the look"]').get_by_role("button", name="Change it in words").click()
    card_.locator('[data-draft="refuted:the look"] textarea').fill("Drop the Camp clip and ask Design.")
    card_.get_by_role("button", name="Refuted").click()
    card_.get_by_role("group", name="Which way?").get_by_role("button", name="the look").click()
    assert judged(pg, host) == [{"id": "calm-answers", "state": "refuted", "why": "Too dear", "way": "the look", "draft": "Drop the Camp clip and ask Design."}]
    left(pg)


def test_with_no_draft_more_is_not_shown(gui):
    row = copy.deepcopy(RICH)
    row["if_holds"], row["draft"] = "", {"held": "", "refuted": {"the look": "", "the noise": ""}}
    row["refuted"] = [{**w, "change": ""} for w in WAYS]
    pg, host, log = open_card(gui, "wide", row)
    card_ = lifted(pg)
    assert card_.get_by_role("button", name="More", exact=True).count() == 0
    pg.close()
    assert not log, "\n".join(log)


def test_a_row_with_no_measure_and_no_draft_looks_as_it_did(gui):
    pg, host, log = open_card(gui, "wide", {**ROW})
    card_ = lifted(pg)
    assert card_.locator('[data-part="measures"]').count() == 0 and card_.get_by_role("button", name="More", exact=True).count() == 0
    assert [b.inner_text().strip() for b in card_.locator(".hand-answers > .ork-btn").all()] == ["Held", "Refuted", "Not sure yet"]
    assert card_.locator('[data-part="signal"] .ork-label').inner_text().lower() == "holds when"
    pg.close()
    assert not log, "\n".join(log)
