"""Spec 128 part B (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.2–§206.3; mockup docs/mockups/goal-card/), in a real browser against a stub host: the Orkmaster's column pinned at the window's left, its head the Orkmaster's tab
(open at first, underlined, the tabs at the top the leaders' alone), its three piles by the goals' states (In analysis face down with no name, To review face up with its wait, At work · later), what a press does (a face-down card lifts the pile's list with Next and
Remove, a face-up card picks its goal, a card of To review lifts Start now and Later today, a put-off one Start now and Back to review), the foot of each card under the front one, the moves between piles, and the phone (under 760 px: no column, the Orkmaster's tab and lane as they were)."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, head, need, node, open_hand, sig, task  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402

pytestmark = pytest.mark.browser


def ripe(left, seconds=240, held=False, by=""):
    return {"left_s": left, "seconds": seconds, "risk": "low", "priority": "high", "held": held, "by": by or ("person" if held else ""), "why": ""}


def back(**more):
    return {"route": [], "cost": None, "offer": [], "short": False, "heard": [], "stances": [], "round": 1, "ripe": None, **more}


class ColumnHost(HandHost):
    """A project of four parties and goals in every state of the column: four in analysis (one being read, one in Talk, two raw), two agreed (their waits running), one held, one put off to the night, one at work with a task running, one done."""

    def __init__(self):
        super().__init__(bare=True)
        timer = node("timer", "tech", "Round timer on phones", "table", state="ready", agreed=True, element="ice", back=back(ripe=ripe(120)))
        scoring = node("scoring", "tech", "Tidy the scoring module", "table", state="ready", agreed=True, element="dust", back=back(ripe=ripe(480)))
        held = node("held", "design", "Lobby in Polish", "table", state="decided", element="void", back=back(ripe=ripe(0, held=True)))
        late = node("late", "tech", "Rename a room after it is made", "table", state="plan", element="lava", start_at="night", waits={"kind": "night", "ref": "", "title": "", "until": ""})
        work = node("music", "design", "Music in the lobby", "table", state="working", element="meadow", stage="implementation", tasks=[task("m1", "Make the loop", "running", head=head("dryad", "design"))])
        self.nodes = [
            node("reading", "tech", "Players see who answered first", "table", state="reading", element="lava"),
            node("talk", "design", "A sound when the round ends", "table", state="talk", element="void", back=back()),
            node("raw1", "tech", "Kick a player from the lobby", "deck", state="raw", element="dust"),
            node("raw2", "design", "Host can skip a round", "deck", state="raw", element="meadow"),
            node("raw3", "tech", "Mute a noisy player", "deck", state="raw", element="ice"),
            timer, scoring, held, late, work,
            node("old", "tech", "An old goal", "history", state="done", seen="2026-10-18T10:00:00"),
        ]

    def handle(self, name, a):
        if name in ("ideas.confirm", "ideas.ripe_hold", "ideas.ripe_back"):
            self.log.append((name, a))
            return self.bump({"ok": True})
        return super().handle(name, a)


def open_column(gui, width="wide", host=None):
    pg, host, log = open_hand(gui, host=host or ColumnHost(), width=width)
    pg.wait_for_selector(".hand .hand-plus", timeout=WAIT_MS)
    return pg, host, log


def goals(pg, pile):
    return pg.eval_on_selector_all(f'.col-sec[data-pile="{pile}"] .col-card', "els => els.map((e) => e.dataset.goal)")


def test_the_column_lies_left_of_the_table_the_table_height_and_its_head_is_the_orkmasters_tab_open_at_first(gui):
    pg, host, log = open_column(gui)
    try:
        col = pg.locator(".frame-column")
        col.wait_for(timeout=WAIT_MS)
        c, t, h = col.bounding_box(), pg.locator(".frame-table").bounding_box(), pg.locator(".frame-hand").bounding_box()
        assert c["x"] == 0 and c["x"] + c["width"] <= t["x"] + 1 and 170 <= c["width"] <= 190, (c, t)
        assert abs(c["height"] - t["height"]) <= 1 and c["y"] + c["height"] <= h["y"] + 1, "the table's height, the hand under both"
        assert h["x"] == 0 and h["width"] >= c["width"] + t["width"] - 1
        tab = col.get_by_role("tab")
        assert tab.count() == 1 and tab.get_attribute("data-tab") == "orkmaster" and tab.get_attribute("aria-selected") == "true"
        assert "the orkmaster" in tab.text_content().lower()
        assert pg.locator(".table-tabs [role=tab][data-tab=orkmaster]").count() == 0, "the tabs at the top are the leaders' alone"
        assert pg.locator(".table-tabs [role=tab]").count() == 4 or pg.locator(".table-tabs [role=tab]").count() >= 3
        assert pg.locator(".table-lane--first").count() == 0, "its goals are in the column, not the Board's first lane"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-head__tab')).boxShadow") != "none", "underlined while open"
        bg = pg.evaluate("() => [getComputedStyle(document.querySelector('.frame-column')).backgroundColor, getComputedStyle(document.querySelector('.frame-hand .hand')).backgroundColor]")
        assert bg[0] == bg[1], "off the table, on the room's colour as the hand is"
        pg.locator('.table-tab[data-tab="tech"]').click()
        assert pg.locator(".col-head__tab").get_attribute("aria-selected") == "false" and pg.locator(".frame-column .col-card").count() > 0, "the same column on every tab"
        col.get_by_role("tab").click()
        pg.wait_for_function("() => document.querySelector('.col-head__tab').getAttribute('aria-selected') === 'true'", timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "tab") == "orkmaster" and pg.locator(".table-board").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_three_piles_hold_the_goals_by_their_states_and_a_goal_lies_in_one(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        assert [t.strip() for t in pg.eval_on_selector_all(".col-plab__t", "els => els.map((e) => e.textContent)")] == ["In analysis", "To review", "At work · later"]
        assert goals(pg, "analysis") == ["reading", "talk", "raw1", "raw2"], "the one the Orkmaster reads first, then Talk, then the rest in its order; the fifth is an edge"
        assert goals(pg, "review") == ["timer", "scoring"], "agreed, the wait that ends first in front"
        assert goals(pg, "work") == ["music", "held", "late"], "at work, then held, then the night's"
        every = goals(pg, "analysis") + goals(pg, "review") + goals(pg, "work")
        assert len(every) == len(set(every)) and "old" not in every, "a goal in one pile; a goal done is the discard's"
        assert pg.locator(".col-card--down").count() == 4 and pg.locator(".col-card--up").count() == 5
        assert pg.locator(".col-sec .col-plab").all_inner_texts() and "writing: Players see who answered first" in pg.locator('[data-under="analysis"]').inner_text()
        assert "next in 2 min" in pg.locator('[data-under="review"]').inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_of_in_analysis_is_face_down_and_sideways_with_no_name_its_front_ring_runs_and_the_pile_is_tight(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--down", timeout=WAIT_MS)
        down = pg.locator(".col-card--down")
        for i in range(down.count()):
            card = down.nth(i)
            text = card.inner_text().strip()
            assert text == "", f"face down with no name: {text!r}"
            assert card.locator(".ork-sigil .ork-elem").count() == 1, "its rune at the seal's top"
        boxes = [down.nth(i).bounding_box() for i in range(down.count())]
        assert abs(boxes[0]["width"] - 157) <= 1 and abs(boxes[0]["height"] - 112) <= 1, f"sideways, 157 x 112: {boxes[0]}"
        assert [round(b["y"] - boxes[0]["y"]) for b in boxes] == [0, 4, 8, 12], "tight: 4 px edges"
        assert pg.locator(".col-pile.is-down .col-edges").count() == 1, "a fifth is an edge only"
        front = down.first
        assert front.locator(".col-sigil.col-busy").count() == 1 and down.nth(1).locator(".col-busy").count() == 0, "the front card's ring runs"
        assert "Players see who answered first" in front.get_attribute("aria-label")
        assert pg.locator(".col-card--down .table-back-nm").count() == 0
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-sigil.col-busy'), '::after').animationName") == "ork-sigil-sweep"
        pg.emulate_media(reduced_motion="reduce")
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.col-sigil.col-busy'), '::after').animationName") == "none", "still under reduced motion"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_press_on_a_face_down_card_lifts_the_list_in_order_and_cannot_pick_next_moves_a_goal_after_the_front_one(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--down", timeout=WAIT_MS)
        pg.locator(".col-card--down").first.click()
        lift = pg.locator('.col-lift[data-lift="list"]')
        lift.wait_for(timeout=WAIT_MS)
        assert sig(pg, "frame/state.js", "picked") == "", "a face-down card cannot be picked"
        rows = lift.locator(".col-list__row")
        assert rows.count() == 5 and rows.first.inner_text().startswith("Players see who answered first"), "each goal's whole title, in the Orkmaster's order"
        assert rows.first.locator("button").count() == 0, "the one being written has no choices yet"
        assert lift.locator("[data-next]").count() == 1, "Next on a goal with a goal of its party before it that waits its turn"
        lift.locator('[data-next="raw3"]').click()
        assert _sent(pg, host, ("ideas.move", {"slug": "raw3", "before": "raw1"}))
        pg.wait_for_function("() => [...document.querySelectorAll('.col-list__row')].map((e) => e.dataset.goal).join() === 'reading,talk,raw3,raw1,raw2'", timeout=WAIT_MS)
        lift.locator('[data-remove="raw1"]').click()
        ask = lift.get_by_role("alertdialog", name="Drop this goal?")
        ask.wait_for(timeout=WAIT_MS)
        assert ask.get_by_role("button", name="Drop it").count() == 1, "Remove asks first"
        pg.wait_for_function("() => document.activeElement && document.activeElement.textContent.trim() === 'Keep it'", timeout=WAIT_MS)      # the safe answer focused (set once it is drawn)
        pg.keyboard.press("Escape")
        ask.wait_for(state="detached", timeout=WAIT_MS)
        assert lift.count() == 1 and not any(c[0] == "ideas.drop" for c in host.log), "the first Esc keeps the goal"
        lift.locator('[data-remove="raw1"]').click()
        lift.get_by_role("button", name="Drop it").click()
        assert _sent(pg, host, ("ideas.drop", {"slug": "raw1"}))
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.col-lift')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_face_up_card_picks_its_goal_and_a_card_of_to_review_lifts_start_now_and_later_today(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        music = pg.locator('.col-card[data-goal="music"]')
        music.click()
        assert sig(pg, "frame/state.js", "picked") == "music" and music.get_attribute("aria-pressed") == "true"
        assert pg.locator(".col-lift").count() == 0, "a goal at work: picked, no choices"
        assert pg.locator(".col-head__tab").get_attribute("aria-selected") == "true", "the open tab stays the Orkmaster's: the column is on every tab"
        music.click()
        assert sig(pg, "frame/state.js", "picked") == ""
        timer = pg.locator('.col-card[data-goal="timer"]')
        timer.click()
        assert sig(pg, "frame/state.js", "picked") == "timer"
        acts = pg.locator('.col-lift[data-lift="acts"]')
        acts.wait_for(timeout=WAIT_MS)
        assert [t for t in acts.get_by_role("button").all_inner_texts() if t.strip()][:2] == ["Start now", "Later today"] and acts.locator(".table-dropper").count() == 1, "and the goal's menu: it can be dropped"
        acts.get_by_role("button", name="Later today").click()
        assert _sent(pg, host, ("ideas.ripe_hold", {"idea": "timer"}))
        timer.click()
        acts.wait_for(timeout=WAIT_MS)
        acts.get_by_role("button", name="Start now").click()
        assert _sent(pg, host, ("ideas.confirm", {"idea": "timer"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_put_off_card_lifts_start_now_and_back_to_review_and_says_held_or_the_moon(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        held, late = pg.locator('.col-card[data-goal="held"]'), pg.locator('.col-card[data-goal="late"]')
        assert "Held" in held.locator(".col-foot").inner_text() and held.locator(".col-foot .ork-sign.pause, .col-foot [class*=pause]").count() >= 0
        assert "01:00" in late.locator(".col-foot").inner_text() and late.locator(".col-win .ork-sign").count() >= 1
        held.click(position={"x": 20, "y": 150})                                  # its foot shows under the card above it
        acts = pg.locator('.col-lift[data-lift="acts"]')
        acts.wait_for(timeout=WAIT_MS)
        assert [t for t in acts.get_by_role("button").all_inner_texts() if t.strip()][:2] == ["Start now", "Back to review"]
        acts.get_by_role("button", name="Back to review").click()
        assert _sent(pg, host, ("ideas.ripe_back", {"idea": "held"}))
        late.click(position={"x": 20, "y": 150})
        acts.wait_for(timeout=WAIT_MS)
        assert [t for t in acts.get_by_role("button").all_inner_texts() if t.strip()] == ["Start now"], "the night's own: only Start now"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_pile_shows_its_front_card_whole_and_the_foot_of_each_under_it_then_edges_and_a_card_hovered_slides_out(gui):
    host = ColumnHost()
    for i in range(6):
        host.nodes.append(node(f"more{i}", "tech", f"Another goal {i}", "table", state="ready", agreed=True, element="ice", back=back(ripe=ripe(600 + i))))
    pg, host, log = open_column(gui, host=host)
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        cards = pg.locator('.col-sec[data-pile="review"] .col-card')
        assert cards.count() == 4, "the front and three under it, no count"
        boxes = [cards.nth(i).bounding_box() for i in range(4)]
        assert abs(boxes[0]["width"] - 112) <= 1 and abs(boxes[0]["height"] - 157) <= 1, boxes[0]
        assert [round(b["y"] - boxes[0]["y"]) for b in boxes] == [0, 20, 40, 60], "the foot of each, 20 px"
        assert pg.locator('.col-sec[data-pile="review"] .col-edges').count() == 1, "then thin edges"
        assert "2 min" in cards.first.locator(".col-foot").inner_text() and cards.first.locator(".col-wbar").count() == 1, "the first's wait as a bar and its time"
        assert cards.nth(1).locator(".col-wbar").count() == 0 and "~" in cards.nth(1).locator(".col-foot").inner_text(), "the others the time they would start"
        assert pg.locator(".col-sec .col-plab").first.inner_text() and "More" not in pg.locator(".col-scroll").inner_text()
        before = cards.nth(2).bounding_box()
        cards.nth(2).hover(position={"x": 30, "y": 150})
        pg.wait_for_function("([x]) => { const e = document.querySelectorAll('.col-sec[data-pile=review] .col-card')[2]; return e.getBoundingClientRect().x > x + 20; }", arg=[before["x"]], timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_agreed_moves_from_in_analysis_to_to_review_and_its_wait_over_to_at_work(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--down", timeout=WAIT_MS)
        host.nodes[2].update(state="ready", agreed=True, back=back(ripe=ripe(60)))
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.col-sec[data-pile=review] [data-goal=raw1]')", timeout=WAIT_MS)
        assert "raw1" not in goals(pg, "analysis") and pg.locator('.col-card[data-goal="raw1"]').get_attribute("class").count("col-card--up") == 1, "turned up where it lay"
        host.nodes[2].update(state="working", stage="implementation", back=back(ripe=ripe(0, by="leaders")), tasks=[task("r1", "Kick it", "running")])
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.col-sec[data-pile=work] [data-goal=raw1]')", timeout=WAIT_MS)
        assert "raw1" not in goals(pg, "review")
        pg.wait_for_selector('.table-board .table-goal[data-goal="raw1"]', timeout=WAIT_MS)
        host.nodes[2].update(state="done", tasks=[])
        host.bump({})
        pg.wait_for_function("() => !document.querySelector('.col-card[data-goal=raw1]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


class SortHost(ColumnHost):
    """Decisions §224: the idea, Talk, the decision and the spec being written lie face down; a spec made lies face up in To review; held is put off."""

    def __init__(self):
        super().__init__()
        self.nodes = [
            node("decide", "tech", "Round timer on phones", "table", state="decided", element="ice", asks_you=True, needs_you="decision", back=back(ripe=None)),
            node("sect", "design", "A timer bar that drains", "table", state="sections", element="void"),
            node("sketch", "design", "Sketch the bar", "table", state="sketch", element="meadow"),
            node("draft", "tech", "Orkmaster's own draft", "table", state="planning", element="dust"),
            node("made", "tech", "Spec made by its leaders", "table", state="plan", element="lava", agreed=True),
            node("heldd", "tech", "Held decision", "table", state="decided", element="ice", back=back(ripe=ripe(0, held=True))),
        ]


def test_a_decision_and_a_spec_being_written_lie_face_down_and_a_spec_made_in_to_review_face_up(gui):
    pg, host, log = open_column(gui, host=SortHost())
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        assert sorted(goals(pg, "analysis")) == ["decide", "draft", "sect", "sketch"], "decided, sections, sketch and the Orkmaster's own planning: face down"
        assert goals(pg, "review") == ["made"], "a spec made by its leaders (agreed) waits in To review, face up"
        assert goals(pg, "work") == ["heldd"], "a decided goal held stays put off"
        assert pg.locator('.col-card[data-goal="made"]').get_attribute("class").count("col-card--up") == 1
        assert "writing: " in pg.locator('[data-under="analysis"]').inner_text() and pg.locator(".col-card--down").first.locator(".col-sigil.col-busy").count() == 1, "the leaders writing its spec: the ring runs and the title says it"
        pg.locator('.col-sec[data-pile="analysis"] .col-card--down').first.click()
        assert len(pg.locator(".col-list__row").all_inner_texts()) == 4
        pg.keyboard.press("Escape")
        for n in host.nodes[1:4]:
            n.update(state="done", folded=True)
        host.bump({})
        pg.wait_for_function("() => document.querySelectorAll('.col-sec[data-pile=analysis] .col-card').length === 1", timeout=WAIT_MS)
        card = pg.locator('.col-card[data-goal="decide"]')
        assert "its decision waits for your word" in card.get_attribute("aria-label") and "waits for you" in pg.locator('[data-under="analysis"]').inner_text()
        assert card.locator(".col-sigil.col-stopped").count() == 1 and card.locator(".col-busy").count() == 0, "yellow and still: it waits for the person"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_phone_has_no_column_and_keeps_the_orkmasters_tab_and_lane(gui):
    pg, host, log = open_column(gui, width="narrow")
    try:
        pg.wait_for_selector(".table-tabs", timeout=WAIT_MS)
        assert pg.locator(".frame-column").count() == 0 and pg.locator(".col-card").count() == 0
        assert pg.locator('.table-tab[data-tab="orkmaster"]').count() == 1 and pg.locator(".table-lane--first").count() == 1, "the narrow table keeps the Orkmaster's tab and its first lane"
    finally:
        pg.close()
    assert not log, "\n".join(log)


DECISION = "Why: One clock.\n\n1. Tech counts."


class AgreedHost(ColumnHost):
    """Decisions §240: three decided goals with a decision row each: `agreed` (all the leaders agreed, its wait runs), `held` (its wait held) and `doubt` (no wait: a leader's no or a doubt)."""

    def __init__(self):
        super().__init__()
        self.nodes = [
            node("agreed", "tech", "Round timer on phones", "table", state="decided", element="ice", back=back(ripe=ripe(600))),
            node("held", "design", "Lobby in Polish", "table", state="decided", element="void", back=back(ripe=ripe(0, held=True))),
            node("doubt", "tech", "Tidy the scoring module", "table", state="decided", element="dust", back=back(ripe=None)),
        ]
        self.needs = [need("decision", g, i, t, DECISION, number=n, confirmed=False, error="")
                      for g, i, t, n in (("tech", "agreed", "Round timer on phones", 201), ("design", "held", "Lobby in Polish", 202), ("tech", "doubt", "Tidy the scoring module", 203))]

    def handle(self, name, a):
        if name == "ideas.ripe_hold":
            self.log.append((name, a))
            next(n for n in self.nodes if n["slug"] == a["idea"])["back"]["ripe"] = ripe(0, held=True)
            return self.bump({"ok": True})
        return super().handle(name, a)


def decisions_in_hand(pg):
    return sorted(pg.eval_on_selector_all('.hand-places .hand-card[data-kind="decision"]', "els => els.map((e) => e.dataset.key)"))


def test_an_agreed_decision_whose_wait_runs_is_not_in_the_hand_and_the_column_says_when_its_spec_starts(gui):
    pg, host, log = open_column(gui, host=AgreedHost())
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelectorAll('.hand-places .hand-card[data-kind=decision]').length === 2", timeout=WAIT_MS)
        keys = decisions_in_hand(pg)
        assert keys == ["decision/doubt/", "decision/held/"], "the held one and the one with no wait are the person's move; the agreed one's wait runs"
        assert sorted(goals(pg, "analysis")) == ["agreed", "doubt"] and goals(pg, "work") == ["held"]
        under = pg.locator('[data-under="analysis"]').inner_text()
        assert under.startswith("decided: Round timer on phones · starts its spec at ") and len(under.split(" at ")[-1]) == 5, under
        card = pg.locator('.col-card[data-goal="agreed"]')
        assert "its decision is agreed; its spec starts by itself at " in card.get_attribute("aria-label")
        assert card.locator(".col-stopped").count() == 0, "it asks nothing: its ring is not yellow"
        card.click()
        rows = pg.locator(".col-list__row")
        assert rows.count() == 2
        agreed = pg.locator('.col-list__row[data-goal="agreed"]')
        assert agreed.get_by_role("button", name="Change…").count() == 1 and agreed.get_by_role("button", name="Start now").count() == 1 and agreed.get_by_role("button", name="Remove").count() == 1
        other = pg.locator('.col-list__row[data-goal="doubt"]')
        assert other.get_by_role("button", name="Change…").count() == 0 and other.get_by_role("button", name="Start now").count() == 0, "a decision with no wait is in the hand, not agreed"
        assert pg.locator(".hand-lifted").count() == 0 and not picked_goal(pg), "a face-down card is never picked"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def picked_goal(pg):
    return pg.locator(".col-card.ork-picked").count() > 0


def test_start_now_on_an_agreed_decision_confirms_it(gui):
    pg, host, log = open_column(gui, host=AgreedHost())
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        pg.locator('.col-card[data-goal="agreed"]').click()
        pg.locator('.col-list__row[data-goal="agreed"]').get_by_role("button", name="Start now").click()
        assert _sent(pg, host, ("ideas.confirm", {"idea": "agreed"}))
        pg.wait_for_selector(".col-list", state="detached", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_change_on_an_agreed_decision_holds_its_wait_and_brings_its_card_into_the_hand_lifted(gui):
    pg, host, log = open_column(gui, host=AgreedHost())
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        pg.locator('.col-card[data-goal="agreed"]').click()
        pg.locator('.col-list__row[data-goal="agreed"]').get_by_role("button", name="Change…").click()
        assert _sent(pg, host, ("ideas.ripe_hold", {"idea": "agreed"}))
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-lifted .hand-way--decision").count() == 1 and pg.locator(".col-list").count() == 0
        assert pg.locator(".hand-lifted").get_by_role("button", name="Start", exact=True).count() == 1, "held: its one button says Start"
        assert decisions_in_hand(pg) == ["decision/agreed/", "decision/doubt/", "decision/held/"]
        assert "agreed" in goals(pg, "work"), "held, the goal lies put off in At work · later until the person starts it"
    finally:
        pg.close()
    assert not log, "\n".join(log)
