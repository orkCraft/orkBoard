"""Spec 116 part E, the hypotheses' faces (docs/specs/116-hypotheses-on-products-tree.md §6; decisions §194), at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch), against stub hosts of their own:

- On Product's tree (a `TreeHost` of tests/test_tree_desktop_browser.py that also answers `ideas.hypotheses`, `ideas.hypothesis_set`, `_keep`, `_drop` and `ideas.hypotheses_propose`): a job's hypotheses as small cards under it,
  before its goals — *We believe* and *We'll know when* muted, the state as an orkUI chip (*Proposed* dashed, *Held* in the success colour, *Refuted* in the danger colour), the head of the leader that proposed it with
  *Proposed by …* —; a proposed one has **Keep** and **Drop**, an open one **Test it** (the + card's field addressed to Product with the type *Try an experiment* and the hypothesis as a mark), **+ Hypothesis**
  opens a small field, **Propose hypotheses** stands while none is kept; each card is `Pickable` (id `hyp:<id>`). No count of them anywhere.
- In the hand (a `HandHost` with the row `hypothesis`): the card *Did it hold?* with the flask sign, lifted its text, its signal, what was found, the tests and the three answers, each sending `ideas.hypothesis_judge`.
Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import re

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, node as hand_node, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402
from tests.test_table_desktop_browser import shot  # noqa: E402
from tests.test_tree_desktop_browser import PARTY, Refused, TreeHost, col, go, open_tree, sent, wide  # noqa: E402

pytestmark = pytest.mark.browser

LEADER = {"slug": "product-manager", "name": "Product lead", "head": {"craft": "product", "race": "knight", "tier": "elder"}}


def item(id, text, signal, state="open", on="", by="person", party="", **more):
    return {"id": id, "text": text, "signal": signal, "axis": "", "on": on, "rests": [], "tests": [], "by": by, "party": party, "state": state, "evidence": [], "verdict": {}, "at": "2026-10-30T09:00:00", **more}


ITEMS = [
    item("sketch-first", "People want a sketch before anything else", "most ask for one within a minute", "proposed", on="get-everyone-in", by="leader", party=PARTY),
    item("code-big", "A big room code is read aloud and typed right", "nine of ten join on the first try", "open", on="get-everyone-in"),
    item("calm-answers", "Twenty seconds is enough to answer calmly", "fewer than one in ten run out of time", "testing", on="answer-calmly",
         tests=[{"slug": "try-20", "title": "Try 20 seconds to answer", "element": "ice", "place": "work"}]),
    item("seat-kept", "A kept seat brings a player back", "seven of ten come back within a minute", "held", on="jump-in"),
    item("late-bar", "Late players want the whole round told", "no one asks where the round is", "refuted", on="jump-in", by="leader", party=PARTY),
    item("loose-one", "Hosts stay for a second round when the first is short", "half of the nights have a second round", "open", on="lobby"),
]


class HypothesesHost(TreeHost):
    """A tree kept, hypotheses in every state (`ITEMS`), Product's leader named."""

    def __init__(self, items=None, kept=True):
        super().__init__(kept=kept)
        next(p for p in self.parties if p["slug"] == PARTY)["leader"] = LEADER
        self.items = copy.deepcopy(ITEMS if items is None else items)
        self.hyp_asked = {"asked": True}
        self.hyp_proposing = False
        self.hyp_error = ""
        self.refuse_set = ""

    def shown(self):
        out = {"items": copy.deepcopy(self.items), "party": PARTY, "proposing": self.hyp_proposing, "status": "asking" if self.hyp_proposing else ""}
        return {**out, "error": self.hyp_error} if self.hyp_error else out

    def handle(self, name, a):
        if name == "ideas.hypotheses":
            self.log.append((name, a))
            return self.shown()
        if name == "ideas.hypothesis_set":
            self.log.append((name, a))
            if self.refuse_set:
                raise Refused(self.refuse_set)
            self.items.append(item(re.sub(r"[^a-z]+", "-", a["text"].lower()).strip("-")[:30], a["text"], a["signal"], "open", on=a.get("on", "")))
            self.rev += 1
            return {"ok": True, "item": self.items[-1]}
        if name in ("ideas.hypothesis_keep", "ideas.hypothesis_drop"):
            self.log.append((name, a))
            mine = next(i for i in self.items if i["id"] == a["id"])
            if name.endswith("keep"):
                mine["state"] = "open"
            else:
                self.items.remove(mine)
            self.rev += 1
            return {"ok": True}
        if name == "ideas.hypotheses_propose":
            self.log.append((name, a))
            if self.hyp_asked.get("asked"):
                self.items = [i for i in ITEMS if i["state"] == "proposed"] + [item("risky", "Hosts will not wait for slow phones", "no one waits past ten seconds", "proposed", by="leader", party=PARTY)]
                self.rev += 1
            return {"ok": True, **self.hyp_asked}
        return super().handle(name, a)


def card(pg, hid):
    return pg.locator(f'.hy-card[data-hyp="{hid}"]')


@pytest.fixture(params=narrow.WIDTHS)
def hyps(gui, request):
    """The window at one of the two widths on Product's tab, a tree kept with hypotheses in every state: `(page, host, width)`."""
    host = HypothesesHost()
    pg, errors = open_tree(gui, request.param, host)
    go(pg)
    pg.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def none(gui, request):
    """The same with a tree and no hypothesis."""
    host = HypothesesHost(items=[])
    pg, errors = open_tree(gui, request.param, host)
    go(pg)
    pg.get_by_role("button", name="Propose hypotheses").wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def css(pg, selector, prop):
    return pg.locator(selector).first.evaluate("(e, p) => getComputedStyle(e)[p]", prop)


def token(pg, name):
    """A colour token as the browser computes it."""
    return pg.evaluate("n => { const s = document.createElement('i'); s.style.color = `var(${n})`; document.body.appendChild(s); const c = getComputedStyle(s).color; s.remove(); return c; }", name)


# -- the cards on the tree -----------------------------------------------------------------------------------------------------------------------------

def test_a_jobs_hypotheses_are_small_cards_under_it_before_its_goals_and_the_unplaced_one_lies_under_the_outcome(hyps):
    pg, host, w = hyps
    first = col(pg, "get-everyone-in")
    assert first.locator(".hy-card").count() == 2 and col(pg, "jump-in").locator(".hy-card").count() == 2 and col(pg, "answer-calmly").locator(".hy-card").count() == 1
    assert col(pg, "play-again").locator(".hy-card").count() == 0
    job, mine, goal = (first.locator(sel).first.bounding_box() for sel in (".tr-job", ".hy-card", ".tr-goal"))
    assert job["y"] + job["height"] <= mine["y"] + 1 and mine["y"] + mine["height"] <= goal["y"] + 1, "under the job, before its goals"
    loose = pg.locator(".tr-hyps--outcome .hy-card")
    assert loose.count() == 1 and loose.get_attribute("data-hyp") == "loose-one"
    banner, row, tier = pg.locator(".tr-banner").bounding_box(), loose.bounding_box(), pg.locator(".tr-col").first.bounding_box()
    assert banner["y"] + banner["height"] <= row["y"] + 1 and row["y"] + row["height"] <= tier["y"] + 1, "a row of its own under the outcome"
    shot(pg, f"hypotheses-{w}.png")


def test_a_card_says_we_believe_and_we_will_know_when_each_keyword_muted_and_the_words_after_it(hyps):
    pg, host, w = hyps
    c = card(pg, "code-big")
    lines = [" ".join(p.inner_text().split()) for p in c.locator(".hy-line").all()]
    assert lines == ["We believe A big room code is read aloud and typed right", "We'll know when nine of ten join on the first try"]
    keys = c.locator(".tr-k")
    assert keys.all_text_contents() == ["We believe", "We'll know when"]
    assert css(pg, ".hy-card .hy-line", "color") != keys.first.evaluate("e => getComputedStyle(e).color"), "the keywords are muted"
    assert "pixel" not in c.locator(".hy-line").first.evaluate("e => getComputedStyle(e).fontFamily").lower(), "a person's words are in the body face"


def test_the_state_is_an_orkui_chip_proposed_dashed_held_in_the_success_colour_refuted_in_the_danger_colour(hyps):
    pg, host, w = hyps
    words = {hid: card(pg, hid).locator(".ork-chip").inner_text().strip() for hid in ("sketch-first", "code-big", "calm-answers", "seat-kept", "late-bar")}
    assert words == {"sketch-first": "Proposed", "code-big": "Open", "calm-answers": "Testing", "seat-kept": "Held", "late-bar": "Refuted"}
    chip = lambda hid: card(pg, hid).locator(".ork-chip")  # noqa: E731
    assert chip("sketch-first").evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed" and chip("code-big").evaluate("e => getComputedStyle(e).borderTopStyle") == "solid"
    assert chip("seat-kept").evaluate("e => getComputedStyle(e).color") == token(pg, "--ork-success")
    assert chip("late-bar").evaluate("e => getComputedStyle(e).color") == token(pg, "--ork-danger")
    assert chip("seat-kept").evaluate("e => getComputedStyle(e).borderTopColor") == token(pg, "--ork-success")
    assert card(pg, "code-big").get_attribute("data-state") == "open" and card(pg, "calm-answers").get_attribute("data-state") == "testing"


def test_a_hypothesis_a_leader_proposed_has_its_leaders_small_head_and_says_who_and_the_persons_own_has_none(hyps):
    pg, host, w = hyps
    c = card(pg, "sketch-first")
    assert c.locator(".hy-by .mp-cap").inner_text() == "Proposed by Product lead"
    head = c.locator(".hy-by .ork-race__head")
    assert head.count() == 1 and "knight" in head.get_attribute("src") and head.get_attribute("width") == "24", "the leader's head, small"
    assert card(pg, "late-bar").locator(".hy-by").count() == 1, "kept or judged, it still says who proposed it"
    assert card(pg, "code-big").locator(".hy-by").count() == 0 and card(pg, "seat-kept").locator(".hy-by").count() == 0


def test_keep_and_drop_are_a_proposed_ones_and_test_it_an_open_ones_and_a_testing_or_judged_one_has_none(hyps):
    pg, host, w = hyps
    labels = lambda hid: [b.inner_text().strip() for b in card(pg, hid).locator(".hy-acts .ork-btn").all()]  # noqa: E731
    assert labels("sketch-first") == ["Keep", "Drop"] and labels("code-big") == ["Test it"] and labels("loose-one") == ["Test it"]
    assert labels("calm-answers") == [] and labels("seat-kept") == [] and labels("late-bar") == []
    box = card(pg, "sketch-first").get_by_role("button", name="Keep the hypothesis: People want a sketch before anything else").bounding_box()
    assert box["height"] >= (44 if not wide(w) else 20), "a press the finger can find"


def test_keep_sends_the_command_and_the_card_becomes_an_open_one(hyps):
    pg, host, w = hyps
    card(pg, "sketch-first").get_by_role("button", name="Keep").click()
    pg.wait_for_function("() => document.querySelector('.hy-card[data-hyp=\"sketch-first\"]')?.dataset.state === 'open'", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_keep") == [{"id": "sketch-first"}]
    assert [b.inner_text().strip() for b in card(pg, "sketch-first").locator(".hy-acts .ork-btn").all()] == ["Test it"]


def test_drop_sends_the_command_and_the_card_goes(hyps):
    pg, host, w = hyps
    card(pg, "sketch-first").get_by_role("button", name="Drop").click()
    pg.wait_for_selector('.hy-card[data-hyp="sketch-first"]', state="detached", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_drop") == [{"id": "sketch-first"}] and pg.locator(".hy-card").count() == 5


def test_no_count_of_hypotheses_is_said_anywhere(hyps):
    pg, host, w = hyps
    assert not re.search(r"\d+\s+(?:open\s+)?hypothes", pg.locator(".mp").inner_text(), re.I)
    assert "hypothes" not in pg.locator(".tr-note").inner_text().lower()


# -- + Hypothesis ---------------------------------------------------------------------------------------------------------------------------------------

def test_plus_hypothesis_at_the_end_of_a_jobs_opens_a_small_field_and_save_keeps_it_on_the_job(hyps):
    pg, host, w = hyps
    mine = col(pg, "play-again")
    assert mine.get_by_role("button", name="+ Hypothesis").count() == 1 and pg.get_by_role("button", name="+ Hypothesis").count() == 5, "one at the end of each job's, one under the outcome"
    mine.get_by_role("button", name="+ Hypothesis").click()
    form = mine.locator(".hy-form")
    form.wait_for(timeout=WAIT_MS)
    assert [x.lower() for x in form.locator(".ork-label").all_text_contents()] == ["we believe", "we'll know when"]
    assert form.get_by_role("button", name="Save").is_disabled(), "both lines are wanted"
    form.locator('textarea[name="text"]').fill("A short round brings them back")
    form.locator('textarea[name="signal"]').fill("most start a second round")
    shot(pg, f"hypotheses-form-{w}.png")
    form.get_by_role("button", name="Save").click()
    mine.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_set") == [{"text": "A short round brings them back", "signal": "most start a second round", "on": "play-again"}]
    assert mine.locator(".hy-form").count() == 0 and mine.locator(".hy-card .hy-line").first.inner_text().endswith("A short round brings them back")


def test_plus_hypothesis_under_the_outcome_keeps_one_on_the_outcome_and_cancel_leaves_things_as_they_were(hyps):
    pg, host, w = hyps
    row = pg.locator(".tr-hyps--outcome")
    row.get_by_role("button", name="+ Hypothesis").click()
    row.get_by_role("button", name="Cancel").click()
    assert row.locator(".hy-form").count() == 0 and sent(host, "ideas.hypothesis_set") == []
    row.get_by_role("button", name="+ Hypothesis").click()
    row.locator('textarea[name="text"]').fill("Hosts like a tidy lobby")
    row.locator('textarea[name="signal"]').fill("fewer ask to leave")
    row.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => document.querySelectorAll('.tr-hyps--outcome .hy-card').length === 2", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_set") == [{"text": "Hosts like a tidy lobby", "signal": "fewer ask to leave", "on": "lobby"}]


def test_a_refusal_is_said_in_its_own_words_and_the_field_stays_with_what_was_written(hyps):
    pg, host, w = hyps
    host.refuse_set = "Seven hypotheses are open: judge one first"
    mine = col(pg, "play-again")
    mine.get_by_role("button", name="+ Hypothesis").click()
    mine.locator('textarea[name="text"]').fill("A short round brings them back")
    mine.locator('textarea[name="signal"]').fill("most start a second round")
    mine.get_by_role("button", name="Save").click()
    alert = mine.locator(".hy-form [role=alert]")
    alert.wait_for(timeout=WAIT_MS)
    assert alert.inner_text() == "Seven hypotheses are open: judge one first" and mine.locator('textarea[name="text"]').input_value() == "A short round brings them back"


# -- Test it --------------------------------------------------------------------------------------------------------------------------------------------

def test_test_it_opens_the_field_addressed_to_product_with_the_type_try_an_experiment_and_the_hypothesis_as_a_mark_and_sends_them(hyps):
    pg, host, w = hyps
    card(pg, "code-big").get_by_role("button", name="Test it").click()
    field = pg.locator(".hand-field")
    field.wait_for(timeout=WAIT_MS)
    assert field.locator(".hand-chip[data-by=tab]").inner_text().strip() == "Product", "addressed to Product"
    kind = field.locator('.hand-chip[data-type="experiment"]')
    assert kind.count() == 1 and kind.inner_text().strip() == "Try an experiment" and kind.locator(".ork-sign.flask").count() == 1
    chip = field.locator(".pick-chip")
    assert chip.count() == 1 and chip.get_attribute("data-mark") == "hyp:code-big" and chip.inner_text().strip() == "A big room code is read aloud and typed right"
    assert "ork-picked" in card(pg, "code-big").get_attribute("class"), "Product's map is in picking: the hypothesis is marked"
    shot(pg, f"hypotheses-test-it-{w}.png")
    pg.locator(".hand-field__text").fill("Show the big code to half of the hosts")
    pg.locator(".hand-field__text").press("Enter")
    pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
    got = sent(host, "ideas.add")
    assert got == [{"text": "Show the big code to half of the hosts", "party": PARTY, "type": "experiment",
                    "marks": [{"map": "product", "id": "hyp:code-big", "name": "A big room code is read aloud and typed right"}]}]


# -- picking --------------------------------------------------------------------------------------------------------------------------------------------

def test_every_hypothesis_is_pickable_in_the_product_map_by_hyp_and_its_id_named_by_its_text(hyps):
    pg, host, w = hyps
    mine = pg.locator('[data-pick-id^="hyp:"]')
    assert mine.count() == 6 and {m.get_attribute("data-pick-map") for m in mine.all()} == {"product"}
    one = pg.locator('[data-pick-id="hyp:code-big"]')
    assert one.get_attribute("data-pick-name") == "A big room code is read aloud and typed right" and one.get_attribute("data-pick-group") == "hypotheses"
    assert pg.locator('[data-pick-map="product"]').count() == 4 + 5 + 6, "the jobs, the goals and the hypotheses"


def test_while_picking_a_press_on_a_hypothesis_takes_it_as_a_mark_and_again_puts_it_down(hyps):
    pg, host, w = hyps
    col(pg, "play-again").get_by_role("button", name="Write a goal for this job").click()
    pg.locator(".hand-field").wait_for(timeout=WAIT_MS)
    card(pg, "seat-kept").locator(".hy-line").first.click()
    pg.wait_for_selector('.hy-card[data-hyp="seat-kept"].ork-picked', timeout=WAIT_MS)
    chips = pg.locator(".hand-field .pick-chip")
    assert chips.count() == 2 and chips.nth(1).get_attribute("data-mark") == "hyp:seat-kept"
    assert pg.locator("[data-picking='1']").count() > 0
    card(pg, "seat-kept").locator(".hy-line").first.click()
    pg.wait_for_selector('.hy-card[data-hyp="seat-kept"].ork-picked', state="detached", timeout=WAIT_MS)
    assert pg.locator(".hand-field .pick-chip").count() == 1
    assert sent(host, "ideas.hypothesis_keep") == [] and sent(host, "ideas.hypothesis_drop") == [], "while picking a press is not an act of the card"


# -- Propose hypotheses ---------------------------------------------------------------------------------------------------------------------------------

def test_with_none_kept_propose_hypotheses_asks_once_and_the_proposed_cards_appear(none):
    pg, host, w = none
    button = pg.get_by_role("button", name="Propose hypotheses")
    assert button.is_enabled() and "proposes the riskiest" in pg.locator(".tr-hyps--outcome .mp-cap").inner_text()
    assert pg.locator(".hy-card").count() == 0 and pg.get_by_role("button", name="+ Hypothesis").count() == 5, "a field of their own at each job's end, and under the outcome"
    shot(pg, f"hypotheses-propose-{w}.png")
    button.click()
    pg.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    assert len(sent(host, "ideas.hypotheses_propose")) == 1 and pg.get_by_role("button", name="Propose hypotheses").count() == 0, "with some kept it is not offered again"
    assert card(pg, "risky").locator(".ork-chip").inner_text().strip() == "Proposed" and card(pg, "risky").get_by_role("button", name="Keep").count() == 1


def test_while_the_leader_proposes_the_button_is_busy_with_orkuis_hourglass_and_the_cards_come_when_kept(gui):
    host = HypothesesHost(items=[])
    host.hyp_proposing = True
    pg, errors = open_tree(gui, "wide", host)
    go(pg)
    button = pg.get_by_role("button", name="Proposing…")
    button.wait_for(timeout=WAIT_MS)
    assert button.is_disabled() and pg.locator(".tr-hyps--outcome .ork-busy").count() == 1
    host.hyp_proposing = False
    host.items = [item("risky", "Hosts will not wait for slow phones", "no one waits past ten seconds", "proposed", by="leader", party=PARTY)]
    host.rev += 1
    host.push()
    pg.locator(".hy-card").first.wait_for(timeout=WAIT_MS)
    assert pg.locator(".ork-busy").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_proposal_that_cannot_be_asked_is_said_with_its_why(none):
    pg, host, w = none
    host.hyp_asked = {"asked": False, "why": "The limits are spent: it can be asked after they reset"}
    pg.get_by_role("button", name="Propose hypotheses").click()
    alert = pg.locator(".tr-hyps--outcome [role=alert]")
    alert.wait_for(timeout=WAIT_MS)
    assert alert.inner_text() == "The limits are spent: it can be asked after they reset" and pg.locator(".hy-card").count() == 0
    assert pg.get_by_role("button", name="Propose hypotheses").is_enabled(), "it can be asked again"


def test_a_failed_proposal_the_host_remembers_is_said_as_the_tree_says_its_own(gui):
    host = HypothesesHost(items=[])
    host.hyp_error = "Product's leader could not be reached"
    pg, errors = open_tree(gui, "wide", host)
    go(pg)
    alert = pg.locator(".tr-hyps--outcome [role=alert]")
    alert.wait_for(timeout=WAIT_MS)
    assert alert.inner_text() == "Product's leader could not be reached"
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- in the hand: Did it hold? --------------------------------------------------------------------------------------------------------------------------

ROW = {"kind": "hypothesis", "id": "calm-answers", "text": "Twenty seconds is enough to answer calmly", "signal": "fewer than one in ten run out of time",
       "evidence": [{"text": "Three of the nine ran out of time", "ref": "try-20", "at": "2026-10-30T10:00:00"}, {"text": "Hosts said it felt rushed", "ref": "", "at": "2026-10-30T11:00:00"}],
       "tests": [{"slug": "try-20", "title": "Try 20 seconds to answer"}], "party": "product", "leader": "product-manager", "blocks": False, "priority": "normal", "at": "2026-10-30T12:00:00"}


class DueHost(HandHost):
    """A project of four parties and nothing waiting but the row `hypothesis` (Product's), a test goal `try-20` done."""

    def __init__(self):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.nodes.append(hand_node("try-20", "product", "Try 20 seconds to answer", "discard", state="done", element="ice", updated="2026-10-30T10:00:00"))
        self.needs = [dict(ROW)]
        self.refuse = False

    def handle(self, name, a):
        if name == "ideas.hypothesis_judge":
            self.log.append((name, a))
            if self.refuse:
                return {"error": "That hypothesis is judged already"}
            self.needs = [n for n in self.needs if n.get("id") != a["id"]]
            return self.bump({"ok": True, "item": {}})
        return super().handle(name, a)


@pytest.fixture(params=narrow.WIDTHS)
def due(gui, request):
    pg, host, log = open_hand(gui, host=DueHost(), width=request.param)
    pg.locator('.hand-card[data-kind="hypothesis"]').first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    pg.close()
    assert not log, "\n".join(log)


def front(pg):
    return pg.locator('.hand-card[data-kind="hypothesis"]').first


def lifted(pg):
    press = front(pg)
    press.click(position={"x": 10, "y": 24})
    pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
    return pg.locator(".hand-lifted")


def test_a_hypothesis_tested_is_a_card_with_the_flask_its_name_the_hypothesis_and_its_proposers_head(due):
    pg, host, w = due
    c = front(pg)
    assert c.locator(".hand-card__name").text_content().strip() == ROW["text"]
    assert c.locator(".hand-card__window .ork-sign.flask").count() == 1
    asker = c.locator(".hand-card__asker .ork-race__head")
    assert asker.count() == 1 and "unicorn" in asker.get_attribute("src"), "Product's leader asks"
    assert c.locator(".ork-gem").count() == 0, "it spends nothing"
    if w == "wide":
        assert c.locator(".hand-card__foot").text_content().strip() == "Did it hold?"
    assert pg.locator('.hand-stack[data-goal^="party:product"], .hand-stack').count() >= 1
    narrow.no_sideways(pg)


def test_lifted_the_card_asks_did_it_hold_and_shows_the_signal_what_was_found_and_the_tests(due):
    pg, host, w = due
    card_ = lifted(pg)
    assert card_.locator(".hand-way > .ork-label").first.inner_text().lower() == "did it hold?"
    assert card_.locator('[data-part="text"]').inner_text() == ROW["text"]
    signal = card_.locator('[data-part="signal"]')
    assert signal.locator(".ork-label").inner_text().lower() == "we'll know when" and signal.locator("p").inner_text() == ROW["signal"]
    found = card_.locator('[data-part="evidence"] li')
    assert [" ".join(li.inner_text().split()) for li in found.all()] == ["Three of the nine ran out of time", "Hosts said it felt rushed"]
    assert found.nth(0).locator(".ork-elem.ice").count() == 1 and found.nth(1).locator(".ork-elem").count() == 0, "a line from a goal wears the goal's element"
    assert [li.inner_text() for li in card_.locator('[data-part="tests"] li').all()] == ["Try 20 seconds to answer"]
    assert [b.inner_text().strip() for b in card_.locator(".hand-answers .ork-btn").all()] == ["Held", "Refuted", "Not sure yet"]
    assert "danger" in card_.get_by_role("button", name="Refuted").get_attribute("class").split()
    assert card_.get_by_label("Why").count() == 1 and card_.locator(".hand-spend").count() == 0, "no cost line"
    shot(pg, f"hypotheses-hand-{w}.png")
    narrow.no_sideways(pg)


@pytest.mark.parametrize("answer, state", [("Held", "held"), ("Refuted", "refuted"), ("Not sure yet", "unsure")])
def test_each_answer_sends_the_verdict_and_the_card_leaves(due, answer, state):
    pg, host, w = due
    card_ = lifted(pg)
    card_.get_by_role("button", name=answer).click()
    assert _calls(pg, host, "ideas.hypothesis_judge") == [{"id": "calm-answers", "state": state}], "no why was written: none is sent"
    pg.wait_for_function("() => !document.querySelector('.hand-lifted') && !document.querySelector('.hand-card[data-kind=\"hypothesis\"]')", timeout=WAIT_MS)


def test_the_why_the_person_wrote_goes_with_the_verdict(due):
    pg, host, w = due
    card_ = lifted(pg)
    card_.get_by_label("Why").fill("  Three in nine is too many  ")
    card_.get_by_role("button", name="Refuted").click()
    assert _calls(pg, host, "ideas.hypothesis_judge") == [{"id": "calm-answers", "state": "refuted", "why": "Three in nine is too many"}]
    pg.wait_for_function("() => !document.querySelector('.hand-card[data-kind=\"hypothesis\"]')", timeout=WAIT_MS)


def test_a_refused_verdict_keeps_the_card_lifted(due):
    pg, host, w = due
    host.refuse = True
    card_ = lifted(pg)
    card_.get_by_role("button", name="Held").click()
    assert _calls(pg, host, "ideas.hypothesis_judge") == [{"id": "calm-answers", "state": "held"}]
    pg.wait_for_timeout(300)
    assert pg.locator(".hand-lifted").count() == 1 and pg.locator('.hand-card[data-kind="hypothesis"]').count() >= 1, "refused: nothing changed"
