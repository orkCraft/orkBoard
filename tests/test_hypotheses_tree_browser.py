"""Spec 146 A (docs/specs/146-a-hypothesis-on-the-page.md; decisions §235.1, §235.2, §237.4), the tree's card of a hypothesis, at both widths, against the stub hosts of `tests/test_hypotheses_desktop_browser.py`:

- adding asks two lines, *We believe* and *Holds when*, and nothing else;
- a closed card says its text, *Holds when*, one line a way (*Refuted when <name>: <when>*) and one line a measure (*<what> · until 1 Dec*): never a value, a bar or a count before the day;
- **More** (on a proposed, open or testing one; a judged one has none) opens the rest in the card's own place: *Holds when*, *If it holds*, one to three ways, up to four measures with a bar for *Holds* and each way and a
  span or a day; **Save** sends `ideas.hypothesis_set` and each changed measure's `ideas.hypothesis_measure_set` (a removed one `_drop`); a refusal is said under the fields; **Cancel** puts it back.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hypotheses_desktop_browser import HypothesesHost, ITEMS, card, item  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402
from tests.test_tree_desktop_browser import PARTY, Refused, col, go, open_tree, sent  # noqa: E402
from tests import narrow  # noqa: E402

pytestmark = pytest.mark.browser

MEASURE = {"id": "m1", "what": "Came back within 7 days", "from": "the store page", "by": PARTY, "span_days": 28, "date": "2026-12-01", "value": None,
           "bars": {"holds": {"op": ">=", "n": 30.0, "unit": "%"}, "refuted": [{"way": "the hook", "op": "<", "n": 10.0, "unit": "%"}]}}
RICH = item("code-big", "A big room code is read aloud and typed right", "nine of ten join on the first try", "open", on="get-everyone-in", if_holds="Every room gets a big code.", started="2026-11-03",
            refuted=[{"name": "the hook", "when": "they skip the code", "change": "Drop the code."}, {"name": "", "when": "nobody reads it aloud", "change": ""}], measures=[MEASURE])


class MoreHost(HypothesesHost):
    """The hypotheses host that also answers the edits and the measures' commands, keeping what it was sent."""

    def __init__(self):
        super().__init__(items=[RICH, *[i for i in ITEMS if i["id"] != "code-big"]])
        self.refuse_measure = ""

    def handle(self, name, a):
        if name == "ideas.hypothesis_set" and a.get("id"):
            self.log.append((name, a))
            if self.refuse_set:
                raise Refused(self.refuse_set)
            mine = next(i for i in self.items if i["id"] == a["id"])
            mine.update({k: a[k] for k in ("signal", "if_holds", "refuted") if k in a})
            self.rev += 1
            return {"ok": True, "item": mine}
        if name in ("ideas.hypothesis_measure_set", "ideas.hypothesis_measure_drop"):
            self.log.append((name, a))
            if self.refuse_measure:
                raise Refused(self.refuse_measure)
            self.rev += 1
            return {"ok": True}
        return super().handle(name, a)


@pytest.fixture(params=narrow.WIDTHS)
def more(gui, request):
    host = MoreHost()
    pg, errors = open_tree(gui, request.param, host)
    go(pg)
    pg.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def plain(gui, request):
    host = HypothesesHost()
    pg, errors = open_tree(gui, request.param, host)
    go(pg)
    pg.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def open_more(pg, hid="code-big"):
    card(pg, hid).get_by_role("button", name="More").click()
    form = card(pg, hid).locator(".hf-form")
    form.wait_for(timeout=WAIT_MS)
    return form


# -- adding stays two lines ----------------------------------------------------------------------------------------------------------------------------

def test_adding_asks_we_believe_and_holds_when_and_nothing_else(plain):
    pg, host, w = plain
    mine = col(pg, "play-again")
    mine.get_by_role("button", name="+ Hypothesis").click()
    form = mine.locator(".hy-form")
    form.wait_for(timeout=WAIT_MS)
    assert [x.lower() for x in form.locator(".ork-label").all_text_contents()] == ["we believe", "holds when"]
    assert form.locator("input, select").count() == 0 and form.locator("textarea").count() == 2
    assert [b.inner_text() for b in form.get_by_role("button").all()] == ["Save", "Cancel"]
    form.locator('textarea[name="text"]').fill("A short round brings them back")
    form.locator('textarea[name="signal"]').fill("most start a second round")
    form.get_by_role("button", name="Save").click()
    mine.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_set") == [{"text": "A short round brings them back", "signal": "most start a second round", "on": "play-again"}]


# -- a closed card ---------------------------------------------------------------------------------------------------------------------------------------

def test_a_closed_card_says_holds_when_a_line_a_way_and_a_line_a_measure_with_its_day(more):
    pg, host, w = more
    c = card(pg, "code-big")
    lines = [" ".join(p.inner_text().split()) for p in c.locator(".hy-line").all()]
    assert lines == ["We believe A big room code is read aloud and typed right", "Holds when nine of ten join on the first try", "Refuted when the hook: they skip the code",
                     "Refuted when nobody reads it aloud", "Came back within 7 days · until 1 Dec"]
    shot(pg, f"hypothesis-closed-{w}.png")


def test_no_number_stands_on_a_card_whose_measures_day_is_ahead(gui):
    host = MoreHost()
    host.items[0]["measures"] = [{**MEASURE, "date": "2999-01-01", "value": {"n": 64.0, "by": "person", "at": "x", "from": ""}}]       # a host that forgot to hide it
    pg, errors = open_tree(gui, "wide", host)
    go(pg)
    c = card(pg, "code-big")
    c.wait_for(timeout=WAIT_MS)
    text = c.inner_text()
    assert "64" not in text and "30" not in text and "%" not in text and "until 1 Jan" in text
    assert c.locator("progress, meter, .ork-bar, [role=progressbar]").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_more_is_on_a_proposed_open_or_testing_one_and_a_judged_one_has_none(more):
    pg, host, w = more
    for hid in ("sketch-first", "code-big", "calm-answers"):
        assert card(pg, hid).get_by_role("button", name="More").count() == 1, hid
    for hid in ("seat-kept", "late-bar"):
        assert card(pg, hid).get_by_role("button", name="More").count() == 0, hid


# -- More ------------------------------------------------------------------------------------------------------------------------------------------------

def test_more_opens_the_conditions_and_the_measures_in_the_cards_own_place(more):
    pg, host, w = more
    before = card(pg, "code-big").bounding_box()
    form = open_more(pg)
    assert pg.locator(".hf-form").count() == 1, "nothing opens beside it"
    labels = [x.lower() for x in form.locator(".ork-label").all_text_contents()]
    for want in ("holds when", "if it holds", "refuted when", "what it would teach", "when", "then", "measures", "what", "from", "whose map"):
        assert want in labels, want
    assert form.locator('textarea[name="signal"]').input_value() == "nine of ten join on the first try" and form.locator('textarea[name="if_holds"]').input_value() == "Every room gets a big code."
    assert form.locator(".hf-way").count() == 2 and form.locator('input[name="way-name-0"]').input_value() == "the hook" and form.locator('textarea[name="way-change-0"]').input_value() == "Drop the code."
    assert form.locator(".hf-measure").count() == 1 and form.locator('input[name="m0-what"]').input_value() == "Came back within 7 days"
    assert form.locator('select[name="m0-by"]').input_value() == PARTY and form.locator('select[name="m0-by"] option').first.inner_text() == "You"
    assert form.locator('select[name="m0-holds-op"]').input_value() == ">=" and form.locator('input[name="m0-holds-n"]').input_value() == "30"
    assert form.locator('select[name="m0-way0-op"]').input_value() == "<" and form.locator('select[name="m0-way1-op"]').input_value() == ""
    assert form.locator('select[name="m0-mode"]').input_value() == "for" and form.locator('select[name="m0-span"]').input_value() == "28"
    ops = form.locator('select[name="m0-holds-op"] option').all_text_contents()
    assert ops == ["no bar", "at least", "more than", "at most", "less than", "exactly"]
    after = card(pg, "code-big").bounding_box()
    assert after["height"] > before["height"], "the card grew"
    shot(pg, f"hypothesis-more-{w}.png")


def test_save_sends_the_conditions_and_only_the_measures_that_changed(more):
    pg, host, w = more
    form = open_more(pg)
    form.locator('textarea[name="signal"]').fill("nine of ten join first time")
    form.locator('textarea[name="if_holds"]').fill("Big codes everywhere.")
    form.get_by_role("button", name="+ A way").click()
    assert form.locator(".hf-way").count() == 3 and form.get_by_role("button", name="+ A way").count() == 0, "three ways at most"
    form.locator('input[name="way-name-2"]').fill("the noise")
    form.locator('textarea[name="way-when-2"]').fill("it is switched off")
    form.locator('textarea[name="way-change-2"]').fill("Make it quiet.")
    form.get_by_role("button", name="Remove the way 2").click()                                           # the unnamed one goes; the new one becomes the second
    form.locator('select[name="m0-way1-op"]').select_option(">")
    form.locator('input[name="m0-way1-n"]').fill("50")
    form.locator('input[name="m0-way1-unit"]').fill("%")
    form.get_by_role("button", name="+ A measure").click()
    form.locator('input[name="m1-what"]').fill("Goals landed")
    form.locator('select[name="m1-by"]').select_option("")
    form.locator('select[name="m1-holds-op"]').select_option("<=")
    form.locator('input[name="m1-holds-n"]').fill("5")
    form.locator('select[name="m1-mode"]').select_option("until")
    form.locator('input[name="m1-date"]').fill("2026-12-20")
    form.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => !document.querySelector('.hf-form')", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_set") == [{"id": "code-big", "signal": "nine of ten join first time", "if_holds": "Big codes everywhere.", "refuted": [
        {"name": "the hook", "when": "they skip the code", "change": "Drop the code."}, {"name": "the noise", "when": "it is switched off", "change": "Make it quiet."}]}]
    got = sent(host, "ideas.hypothesis_measure_set")
    assert got == [
        {"id": "code-big", "measure": "m1", "what": "Came back within 7 days", "from": "the store page", "by": PARTY, "holds": {"op": ">=", "n": 30.0, "unit": "%"},
         "refuted": [{"way": "the hook", "op": "<", "n": 10.0, "unit": "%"}, {"way": "the noise", "op": ">", "n": 50.0, "unit": "%"}], "span_days": 28},
        {"id": "code-big", "what": "Goals landed", "from": "", "by": "", "holds": {"op": "<=", "n": 5.0, "unit": ""}, "refuted": [], "date": "2026-12-20"}]
    assert sent(host, "ideas.hypothesis_measure_drop") == []


def test_a_measure_left_as_it_was_is_not_sent_and_one_removed_is_dropped(more):
    pg, host, w = more
    form = open_more(pg)
    form.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => !document.querySelector('.hf-form')", timeout=WAIT_MS)
    assert len(sent(host, "ideas.hypothesis_set")) == 1 and sent(host, "ideas.hypothesis_measure_set") == [] and sent(host, "ideas.hypothesis_measure_drop") == []
    form = open_more(pg)
    form.get_by_role("button", name="Remove the measure 1").click()
    assert form.locator(".hf-measure").count() == 0
    form.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => !document.querySelector('.hf-form')", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_measure_drop") == [{"id": "code-big", "measure": "m1"}] and sent(host, "ideas.hypothesis_measure_set") == []


def test_up_to_four_measures_and_the_fifth_is_not_offered(more):
    pg, host, w = more
    form = open_more(pg)
    for _ in range(3):
        form.get_by_role("button", name="+ A measure").click()
    assert form.locator(".hf-measure").count() == 4 and form.get_by_role("button", name="+ A measure").count() == 0


def test_a_refusal_is_said_under_the_fields_in_its_words_and_the_form_stays(more):
    pg, host, w = more
    host.refuse_set = "A way it is refuted says when"
    form = open_more(pg)
    form.locator('textarea[name="way-when-0"]').fill("")
    form.get_by_role("button", name="Save").click()
    alert = form.locator("[role=alert]")
    alert.wait_for(timeout=WAIT_MS)
    assert alert.inner_text() == "A way it is refuted says when" and form.locator('input[name="way-name-0"]').input_value() == "the hook"
    assert sent(host, "ideas.hypothesis_measure_set") == [], "nothing else was sent after the refusal"
    host.refuse_set = ""
    host.refuse_measure = "A measure says what is counted and its bar: a number it holds at or a way it is refuted at"
    form.locator('textarea[name="way-when-0"]').fill("they skip the code")
    form.locator('input[name="m0-what"]').fill("Another thing")
    form.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => document.querySelector('.hf-form [role=alert]')?.textContent.startsWith('A measure says')", timeout=WAIT_MS)


def test_cancel_puts_the_card_back_and_sends_nothing(more):
    pg, host, w = more
    form = open_more(pg)
    form.locator('textarea[name="signal"]').fill("something else")
    form.get_by_role("button", name="Cancel").click()
    assert pg.locator(".hf-form").count() == 0 and sent(host, "ideas.hypothesis_set") == []
    assert " ".join(card(pg, "code-big").locator(".hy-line").nth(1).inner_text().split()) == "Holds when nine of ten join on the first try"
    assert card(pg, "code-big").get_by_role("button", name="More").count() == 1
