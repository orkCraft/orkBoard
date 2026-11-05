"""Spec 128 part D.3 (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.6), in a real browser against a stub host that keeps the snapshot's `passing` as the keeper does: a question passed on is a small card
over the Orkmaster's column's foot (its goal's rune, the two heads, the question, *passing on · N s*); pressed, **Answer it myself** (`ideas.pass_take`) and **Pass it now** (`ideas.pass_now`), each with the row's id; once its call begins the card flies to
the answering leader's tab, which says *answering…*; the answer given, a copy flies back into the goal's card; the goal's card says *Asked Tech* with the faint `question` sign, not yellow. Screenshots to $PASS_SHOTS when it is set."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_column_browser import ColumnHost, open_column  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["PASS_SHOTS"]) if os.environ.get("PASS_SHOTS") else None
QUESTION = "Does the round timer count on the phones or on the server?"


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def row(left_s=6, answering=False, idea="talk", to="tech", by="design", n="q1"):
    return {"id": f"{idea}~{n}", "idea": idea, "task": "", "by": by, "to": to, "q": QUESTION, "left_s": left_s, "answering": answering}


class PassHost(ColumnHost):
    """The column's host with a question or two passing: `passing` is in the snapshot; `ideas.pass_take` and `ideas.pass_now` are logged and answered as the host's are."""

    def __init__(self):
        super().__init__()
        self.passing = []

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["passing"] = self.passing
        return doc

    def put(self, rows):
        self.passing = rows
        self.ws.send(json.dumps(self.snapshot()))

    def handle(self, name, a):
        if name in ("ideas.pass_take", "ideas.pass_now"):
            self.log.append((name, a))
            return {"ok": True}
        return super().handle(name, a)


def start(gui, rows):
    host = PassHost()
    host.passing = rows
    pg, host, log = open_column(gui, host=host)
    return pg, host, log


def flights(pg):
    return pg.evaluate("() => import('/static/js/table/passing.js').then((m) => ({ ...m.passFlights }))")


def test_a_question_passing_is_a_small_card_over_the_columns_foot_with_its_rune_two_heads_the_question_and_its_seconds(gui):
    pg, host, log = start(gui, [row()])
    try:
        card = pg.locator(".frame-column .col-pass")
        card.wait_for(timeout=WAIT_MS)
        assert card.get_attribute("data-goal") == "talk"
        assert card.locator(".ork-elem").count() == 1 and card.locator(".ork-race__head").count() == 2, "the goal's rune and the two heads: who asked, who it is passed to"
        assert QUESTION in card.inner_text()
        text = card.locator(".col-pass__left").inner_text()
        assert text.startswith("passing on · ") and text.endswith(" s") and 1 <= int(text.split("· ")[1].split(" ")[0]) <= 6, text
        c, col, hand = card.bounding_box(), pg.locator(".frame-column").bounding_box(), pg.locator(".frame-hand").bounding_box()
        assert col["x"] <= c["x"] and c["x"] + c["width"] <= col["x"] + col["width"] and c["y"] + c["height"] <= hand["y"] + 1, "inside the column, over its foot"
        assert pg.locator(".col-pass .ork-btn").count() == 0, "its choices are shown when it is pressed"
        shot(pg, "passing")
        pg.wait_for_timeout(2300)
        assert int(card.locator(".col-pass__left").get_attribute("data-left")) <= 4, "the seconds count down between snapshots"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_pressed_it_offers_answer_it_myself_and_pass_it_now_with_its_id(gui):
    pg, host, log = start(gui, [row()])
    try:
        pg.locator(".col-pass__main").click()
        take, now = pg.locator("[data-pass-take]"), pg.locator("[data-pass-now]")
        assert take.inner_text() == "Answer it myself" and now.inner_text() == "Pass it now"
        shot(pg, "passing-open")
        take.click()
        assert _sent(pg, host, ("ideas.pass_take", {"id": "talk~q1"}))
        now.click()
        assert _sent(pg, host, ("ideas.pass_now", {"id": "talk~q1"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_piles_line_says_asked_tech_in_the_faint_ink_and_the_goals_back_is_not_yellow(gui):
    """Spec 147 B.2: a back of the Orkmaster's hand has no room for words, so the question passed on is the pile's line (as it was for a card under the front one), faint, never yellow."""
    pg, host, log = start(gui, [row(idea="reading", by="design", to="tech")])
    try:
        pg.wait_for_selector(".col-pass", timeout=WAIT_MS)
        asked = pg.locator('[data-under-asked="analysis"]')
        asked.wait_for(timeout=WAIT_MS)
        assert asked.inner_text().strip() == "Asked Tech" and asked.evaluate("e => getComputedStyle(e).color") == pg.evaluate("() => { const s = document.createElement('i'); s.style.color = 'var(--ork-ink-faint)'; document.body.append(s); const v = getComputedStyle(s).color; s.remove(); return v; }"), "faint, not yellow"
        assert "asks" not in (pg.locator('.frame-column .col-card[data-goal="reading"]').get_attribute("class") or "").split(), "not yellow: it waits for no one"
        shot(pg, "asked")
        host.put([row(idea="talk", by="tech", to="design")])
        pg.wait_for_function("() => (document.querySelector('[data-under-asked=analysis]')?.textContent || '') === 'Asked Design'", timeout=WAIT_MS)
        assert pg.locator("[data-asked]").count() == 0, "a back of the hand says nothing itself: it is read in the pile's line"
        pg.locator(".col-pass__main").click()
        pg.locator("[data-pass-take]").wait_for(timeout=WAIT_MS)
        host.put([])
        pg.wait_for_function("() => !document.querySelector('[data-asked]') && !document.querySelector('.col-pass') && !document.querySelector('[data-under-asked]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_once_its_call_begins_the_card_flies_to_the_leaders_tab_which_says_answering_and_the_answer_flies_back(gui):
    pg, host, log = start(gui, [row()])
    try:
        pg.wait_for_selector(".col-pass", timeout=WAIT_MS)
        assert pg.locator("[data-answering]").count() == 0
        host.put([row(left_s=0, answering=True)])
        tab = pg.locator('[data-answering="tech"]')
        tab.wait_for(timeout=WAIT_MS)
        assert tab.inner_text() == "answering…" and tab.evaluate("e => !!e.closest('#tab-tech')"), "on the answering leader's own tab"
        pg.wait_for_function("() => !document.querySelector('.col-pass')", timeout=WAIT_MS)
        assert flights(pg)["out"] == 1, "the card flew to the tab"
        assert pg.locator('[data-under-asked=analysis]').inner_text() == "Asked Tech", "the goal still says Asked Tech while it is answered"
        shot(pg, "answering")
        host.put([])
        pg.wait_for_function("() => !document.querySelector('[data-answering]')", timeout=WAIT_MS)
        assert flights(pg)["back"] == 1, "the answer flew back into the goal's card"
        pg.wait_for_function("() => !document.querySelector('.table-flyer')", timeout=WAIT_MS)
        assert pg.locator('[data-under-asked]').count() == 0 and pg.locator(".table-flyer").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_reduced_motion_the_card_is_simply_gone_and_the_tab_says_answering(gui):
    server, browser = gui
    pg, host, log = start(gui, [row()])
    try:
        pg.emulate_media(reduced_motion="reduce")
        pg.wait_for_selector(".col-pass", timeout=WAIT_MS)
        host.put([row(left_s=0, answering=True)])
        pg.locator('[data-answering="tech"]').wait_for(timeout=WAIT_MS)
        host.put([])
        pg.wait_for_function("() => !document.querySelector('[data-answering]')", timeout=WAIT_MS)
        assert flights(pg) == {"out": 0, "back": 0, "now": 0}
    finally:
        pg.close()
    assert not log, "\n".join(log)
