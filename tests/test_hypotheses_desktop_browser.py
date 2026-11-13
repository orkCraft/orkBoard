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
from tests.test_hand_desktop_browser import HandHost, node as hand_node, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402
from tests.test_tree_desktop_browser import PARTY, Refused, TreeHost, go, open_tree, sent  # noqa: E402

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











def test_keep_sends_the_command_and_the_card_becomes_an_open_one(hyps):
    pg, host, w = hyps
    card(pg, "sketch-first").get_by_role("button", name="Keep").click()
    pg.wait_for_function("() => document.querySelector('.hy-card[data-hyp=\"sketch-first\"]')?.dataset.state === 'open'", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_keep") == [{"id": "sketch-first"}]
    assert [b.inner_text().strip() for b in card(pg, "sketch-first").locator(".hy-acts .ork-btn").all()] == ["Test it", "More"]


def test_drop_sends_the_command_and_the_card_goes(hyps):
    pg, host, w = hyps
    card(pg, "sketch-first").get_by_role("button", name="Drop").click()
    pg.wait_for_selector('.hy-card[data-hyp="sketch-first"]', state="detached", timeout=WAIT_MS)
    assert sent(host, "ideas.hypothesis_drop") == [{"id": "sketch-first"}] and pg.locator(".hy-card").count() == 5




# -- + Hypothesis ---------------------------------------------------------------------------------------------------------------------------------------







# -- Test it --------------------------------------------------------------------------------------------------------------------------------------------



# -- picking --------------------------------------------------------------------------------------------------------------------------------------------





# -- Propose hypotheses ---------------------------------------------------------------------------------------------------------------------------------









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




@pytest.mark.parametrize("answer, state", [("Held", "held"), ("Refuted", "refuted"), ("Not sure yet", "unsure")])
def test_each_answer_sends_the_verdict_and_the_card_leaves(due, answer, state):
    pg, host, w = due
    card_ = lifted(pg)
    card_.get_by_role("button", name=answer).click()
    if state == "unsure":                                                                                  # spec 146 B: it asks a day first
        card_.locator('input[name="look-on"]').fill("2026-12-24")
        card_.get_by_role("button", name="Keep it open").click()
        assert _calls(pg, host, "ideas.hypothesis_judge") == [{"id": "calm-answers", "state": "unsure", "date": "2026-12-24"}]
    else:
        assert _calls(pg, host, "ideas.hypothesis_judge") == [{"id": "calm-answers", "state": state}], "no why was written: none is sent"
    pg.wait_for_function("() => !document.querySelector('.hand-lifted') && !document.querySelector('.hand-card[data-kind=\"hypothesis\"]')", timeout=WAIT_MS)




