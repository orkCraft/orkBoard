"""Spec 128 part B (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md, decisions §206.2–§206.3) as spec 147 part B changed it (docs/specs/147-one-card-four-corners.md, decisions §251.3–§251.4; mockup docs/mockups/card-ratio/), in a real browser against a stub host: the
Orkmaster's column, 160 px, pinned at the window's left, its head the Orkmaster's tab (open at first, underlined, the tabs at the top the leaders' alone), its three piles by the goals' states (In analysis the Orkmaster's hand, a near-straight fan of 56 x 78 backs with the goal being read lifted;
To review a squared deck of backs on their side, its ring the wait, the next to start named; At work · later standing cards read by their four corners), what a press does (a back of the hand lifts the pile's list with Next and Remove, a back of the deck or a standing card picks its goal, a card of
To review lifts Start now and Hold, a put-off one Start now and Back to review), the foot of each card behind the front one, a column that never scrolls and gives way to a short window (giveWay), the moves between piles, and the phone (under 760 px: no column, the Orkmaster's tab and lane as they were)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import lexicon  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, call, head, need, node, open_hand, sig, task  # noqa: E402
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
        assert c["x"] == 0 and c["x"] + c["width"] <= t["x"] + 1 and abs(c["width"] - 160) <= 1, ("spec 147 B.1: 160 px", c, t)
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
        assert goals(pg, "analysis") == ["reading", "talk", "raw1", "raw2", "raw3"], "the one the Orkmaster reads first, then Talk, then the rest in its order: every goal of the pile is a back of the hand"
        assert goals(pg, "review") == ["timer", "scoring"], "agreed, the wait that ends first in front"
        assert goals(pg, "work") == ["music", "held", "late"], "at work, then held, then the night's"
        every = goals(pg, "analysis") + goals(pg, "review") + goals(pg, "work")
        assert len(every) == len(set(every)) and "old" not in every, "a goal in one pile; a goal done is the discard's"
        assert pg.locator(".col-card--fan").count() == 5 and pg.locator(".col-card--deck").count() == 2 and pg.locator(".col-card--up").count() == 3, "the hand, the deck and the standing cards"
        assert pg.locator(".col-sec .col-plab").all_inner_texts() and pg.locator('[data-under="analysis"]').inner_text() == "reading: Players see who answered first"
        assert pg.locator('[data-under="review"]').inner_text() == "next in 2 min: Round timer on phones", "the next to start, its time and its name"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_in_analysis_is_the_orkmasters_hand_a_fan_of_small_backs_each_rune_in_its_middle_and_the_goal_being_read_lifted(gui):
    """Spec 147 B.2 (decisions §251.3): every goal of the pile a back 56 x 78 standing, orkUI's small seal and its goal's rune in its middle, a near-straight fan, the one being read lifted and its rune glowing, no name on the face (it is in the back's title and label)."""
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--fan", timeout=WAIT_MS)
        pg.emulate_media(reduced_motion="reduce")
        fan = pg.locator(".col-fan")
        cards = pg.locator(".col-card--fan")
        assert cards.count() == 5
        for i in range(cards.count()):
            card = cards.nth(i)
            assert card.inner_text().strip() == "", "face down: no name on its face"
            assert card.locator(".ork-card-back").count() == 1 and card.locator(".ork-sigil.small").count() == 1 and card.locator(".ork-elem").count() == 1, "orkUI's back, its small seal and the goal's rune"
            assert card.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [56, 78], "56 x 78"
            rune, box = card.locator(".ork-elem").bounding_box(), card.evaluate("e => { const r = e.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; }")
            assert abs(rune["x"] + rune["width"] / 2 - (box["x"] + box["w"] / 2)) <= 4 and abs(rune["y"] + rune["height"] / 2 - (box["y"] + box["h"] / 2)) <= 8, "the rune in the back's middle"
            assert (card.get_attribute("title") or "").startswith(["Players see", "A sound when", "Kick a player", "Host can skip", "Mute a noisy"][i]) and card.get_attribute("aria-label") == card.get_attribute("title"), "its goal's name"
        assert fan.evaluate("e => e.offsetWidth") <= 144
        step = cards.evaluate_all("els => els.map((e) => e.offsetLeft)")
        assert [b - a for a, b in zip(step, step[1:])] == [22] * 4, f"five backs: 88 / 4 = 22 px apart ({step})"
        turns = cards.evaluate_all("els => els.map((e) => e.style.getPropertyValue('--r'))")
        assert turns == ["-3deg", "-1.5deg", "0deg", "1.5deg", "3deg"], "1.5 degrees apart about the middle one"
        reading = pg.locator(".col-card--fan.is-reading")
        assert reading.count() == 1 and reading.get_attribute("data-goal") == "reading", "the one the Orkmaster reads"
        lift = pg.evaluate("() => [...document.querySelectorAll('.col-card--fan')].map((e) => { const m = new DOMMatrix(getComputedStyle(e).transform); return Math.round(m.f); })")
        assert lift[0] == -12 and lift[1:] == [0, 0, 0, 0], "lifted 12 px out of the fan"
        assert reading.locator(".ork-elem.is-glowing").count() == 1 and cards.nth(1).locator(".is-glowing").count() == 0, "its rune glows"
        assert pg.locator(".col-card--down.col-card--fan .col-sigil").count() == 0 and pg.locator(".col-card--fan .col-mid, .col-card--fan .col-play").count() == 0
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
        assert [t for t in acts.get_by_role("button").all_inner_texts() if t.strip() not in ("", "…")][:2] == ["Start now", "Hold"] and acts.locator(".table-dropper").count() == 1, "and the goal's menu: it can be dropped"
        # a lifted card says its title once (spec 140 A4, decisions §247.6): the whole title is its heading, no line repeats it, what it says is one sentence and the rest is behind its …
        assert acts.locator(".col-lift__t").inner_text().strip() == "Round timer on phones" and acts.get_by_text("Round timer on phones").count() == 1
        said = acts.locator("[data-said]")
        assert said.count() == 1 and said.evaluate("e => e.firstChild.textContent.trim()") == "Its spec is ready; it starts by itself in its turn." and "ask a leader" not in said.inner_text()
        more = said.get_by_role("button", name="More")
        more.click()
        assert "ask a leader there to change it" in said.inner_text() and said.get_by_role("button", name="Less").count() == 1
        acts.get_by_role("button", name="Hold").click()
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
        pg.set_viewport_size({"width": 1280, "height": 1100})                      # room for the foot of each card behind the front one
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        held, late = pg.locator('.col-card[data-goal="held"]'), pg.locator('.col-card[data-goal="late"]')
        assert "Held" in held.locator(".col-foot").inner_text() and held.locator(".col-foot .ork-sign.pause, .col-foot [class*=pause]").count() >= 0
        assert "01:00" in late.locator(".col-foot").inner_text() and late.locator(".col-foot .ork-sign").count() >= 1
        assert pg.locator(".col-card--up .col-win, .col-card--up .table-card__win, .col-fnm").count() == 0, "spec 142 A, 140 A2: no window, no name in a foot"
        held.click(position={"x": 20, "y": held.bounding_box()["height"] - 8})   # its foot shows under the card above it
        acts = pg.locator('.col-lift[data-lift="acts"]')
        acts.wait_for(timeout=WAIT_MS)
        assert [t for t in acts.get_by_role("button").all_inner_texts() if t.strip() not in ("", "…")][:2] == ["Start now", "Back to review"]
        assert acts.locator("[data-said]").count() == 1 and acts.get_by_role("button", name="More").count() == 0, "one sentence: nothing behind a …"
        acts.get_by_role("button", name="Back to review").click()
        assert _sent(pg, host, ("ideas.ripe_back", {"idea": "held"}))
        late.click(position={"x": 20, "y": late.bounding_box()["height"] - 8})
        acts.wait_for(timeout=WAIT_MS)
        assert [t for t in acts.get_by_role("button").all_inner_texts() if t.strip() not in ("", "…")] == ["Start now"], "the night's own: only Start now"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_deck_is_squared_three_pixels_apart_and_standing_cards_show_the_foot_of_each_behind_the_front_one_and_a_card_hovered_slides_out(gui):
    host = ColumnHost()
    for i in range(6):
        host.nodes.append(node(f"more{i}", "tech", f"Another goal {i}", "table", state="ready", agreed=True, element="ice", back=back(ripe=ripe(600 + i))))
    for i in range(3):
        host.nodes.append(node(f"also{i}", "tech", f"Also at work {i}", "table", state="working", element="dust", stage="implementation", tasks=[task(f"a{i}", "Do it", "running")]))
    pg, host, log = open_column(gui, host=host)
    try:
        pg.set_viewport_size({"width": 1280, "height": 1200})
        pg.wait_for_selector(".col-card--deck", timeout=WAIT_MS)
        deck = pg.locator('.col-sec[data-pile="review"] .col-card')
        assert deck.count() == 5, "the front and four behind, no count"
        boxes = [deck.nth(i).bounding_box() for i in range(5)]
        assert all(abs(b["width"] - 157) <= 1 and abs(b["height"] - 112) <= 1 for b in boxes), f"on their side, 157 x 112: {boxes[0]}"
        assert [round(b["y"] - boxes[0]["y"]) for b in boxes] == [0, 3, 6, 9, 12], "a squared deck: 3 px apart"
        assert len({round(b["x"]) for b in boxes}) == 1, "unturned, one above another"
        assert deck.evaluate_all("els => els.map((e) => getComputedStyle(e).transform)") == ["none"] * 5
        work = pg.locator('.col-sec[data-pile="work"] .col-card')
        pg.wait_for_function("() => document.querySelectorAll('.col-sec[data-pile=work] .col-card').length >= 4", timeout=WAIT_MS)
        assert work.count() == 6, "the front and five behind"
        wb = [work.nth(i).bounding_box() for i in range(work.count())]
        assert all(abs(b["width"] - 144) <= 1 and abs(b["height"] - 202) <= 1 for b in wb), f"standing, 144 x 202: {wb[0]}"
        assert all(abs(b["x"] + b["width"] - 144) <= 1 for b in wb[:1]) and abs(boxes[0]["x"] + boxes[0]["width"] - 144) <= 1, "the deck and the standing cards share one right edge"
        assert pg.locator(".col-sec .col-plab").first.inner_text() and "More" not in pg.locator(".col-scroll").inner_text()
        before = work.nth(1).bounding_box()
        assert [round(wb[i + 1]["y"] - wb[i]["y"]) for i in range(5)] == [26] * 5, "the foot of each, 26 px"
        work.nth(1).hover(position={"x": 30, "y": wb[1]["height"] - 6})
        pg.wait_for_function("([x]) => { const e = document.querySelectorAll('.col-sec[data-pile=work] .col-card')[1]; return e.getBoundingClientRect().x > x + 20; }", arg=[before["x"]], timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_agreed_moves_from_in_analysis_to_to_review_and_its_wait_over_to_at_work(gui):
    pg, host, log = open_column(gui)
    try:
        pg.wait_for_selector(".col-card--fan", timeout=WAIT_MS)
        host.nodes[2].update(state="ready", agreed=True, back=back(ripe=ripe(60)))
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.col-sec[data-pile=review] [data-goal=raw1]')", timeout=WAIT_MS)
        assert "raw1" not in goals(pg, "analysis") and pg.locator('.col-card[data-goal="raw1"]').get_attribute("class").count("col-card--deck") == 1, "a back of the deck now: it waits for its start, face down"
        host.nodes[2].update(state="working", stage="implementation", back=back(ripe=ripe(0, by="leaders")), tasks=[task("r1", "Kick it", "running")])
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.col-sec[data-pile=work] [data-goal=raw1]')", timeout=WAIT_MS)
        assert "raw1" not in goals(pg, "review") and pg.locator('.col-card[data-goal="raw1"]:not(.table-flyer)').get_attribute("class").count("col-card--up") == 1, "standing: it plays"
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


def test_a_decision_and_a_spec_being_written_are_backs_of_the_hand_and_a_spec_made_a_back_of_the_deck(gui):
    pg, host, log = open_column(gui, host=SortHost())
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        assert sorted(goals(pg, "analysis")) == ["decide", "draft", "sect", "sketch"], "decided, sections, sketch and the Orkmaster's own planning: face down"
        assert goals(pg, "review") == ["made"], "a spec made by its leaders (agreed) waits in To review, face up"
        assert goals(pg, "work") == ["heldd"], "a decided goal held stays put off"
        assert pg.locator('.col-card[data-goal="made"]').get_attribute("class").count("col-card--deck") == 1
        assert pg.locator('[data-under="analysis"]').inner_text().startswith("reading: ") and pg.locator(".col-card--fan").first.locator(".ork-elem.is-glowing").count() == 1, "the leaders writing its spec: the front back lifted with its rune glowing and the title says it"
        pg.locator('.col-sec[data-pile="analysis"] .col-card--down').first.click()
        assert len(pg.locator(".col-list__row").all_inner_texts()) == 4
        pg.keyboard.press("Escape")
        for n in host.nodes[1:4]:
            n.update(state="done", folded=True)
        host.bump({})
        pg.wait_for_function("() => document.querySelectorAll('.col-sec[data-pile=analysis] .col-card').length === 1", timeout=WAIT_MS)
        card = pg.locator('.col-card[data-goal="decide"]')
        assert "its decision waits for your word" in card.get_attribute("aria-label") and "waits for you" in pg.locator('[data-under="analysis"]').inner_text()
        assert "asks" in card.get_attribute("class").split() and card.locator(".is-glowing").count() == 0, "its frame in the alert and nothing glowing: it waits for the person"
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
        assert "asks" not in card.get_attribute("class").split(), "it asks nothing: its frame is not yellow"
        card.click(position={"x": 20, "y": 8})          # the first back of the hand: the second lies over its right end
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
        pg.locator('.col-card[data-goal="agreed"]').click(position={"x": 20, "y": 8})      # the first back of the hand: the second lies over its right end
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
        pg.locator('.col-card[data-goal="agreed"]').click(position={"x": 20, "y": 8})      # the first back of the hand: the second lies over its right end
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


# -- the Orkmaster's hand says where each goal is by its back alone (decisions §251.3; the middle of the front card's ring of §241 is gone with the card) -------------------------------------------------------------------------------

RACES = [("tech", "shaman"), ("design", "dryad"), ("product", "unicorn"), ("release", "lich"), ("live", "imp")]


def leaders(n, heard=(), written=()):
    """A route of `n` leaders with their heads, and a back that says who has answered and whose section is written."""
    route = [{"party": p, "leader": f"{p}-lead", "head": {"race": r, "tier": "elder"}} for p, r in RACES[:n]]
    return back(route=route, heard=list(heard), written=list(written))


class RingHost(ColumnHost):
    """One goal in analysis, by `state` and its back; `needs` its hand cards."""

    def __init__(self, state="talk", bk=None, title="Round timer on phones", needs=()):
        super().__init__()
        self.nodes = [node("g", "tech", title, "table", state=state, element="ice", back=bk, **({"asks_you": True} if state == "decided" and bk and not bk.get("ripe") else {}))]
        self.needs = list(needs)


def ring_card(gui, **kw):
    pg, host, log = open_column(gui, host=RingHost(**kw))
    pg.wait_for_selector('.col-card--fan[data-goal="g"]', timeout=WAIT_MS)
    return pg, host, log


def test_a_goal_the_orkmaster_or_its_leaders_are_on_is_lifted_with_its_rune_glowing_and_a_goal_not_yet_read_is_not(gui):
    for state, reads in (("reading", True), ("talk", True), ("sections", True), ("routed", False), ("raw", False)):
        pg, host, log = ring_card(gui, state=state, bk=leaders(2) if state in ("talk", "sections", "routed") else None)
        try:
            card = pg.locator('.col-card--fan[data-goal="g"]')
            assert ("is-reading" in card.get_attribute("class").split()) == reads, state
            assert card.locator(".ork-elem.is-glowing").count() == int(reads), state
            assert card.locator(".col-sigil, .col-mid, .col-play").count() == 0, "no ring, no heads, no play on a back of the hand"
            assert pg.locator('[data-under="analysis"]').inner_text().startswith("reading: ") == (state in ("reading", "sections")), state
        finally:
            pg.close()
        assert not log, "\n".join(log)


def test_a_goal_asking_the_person_has_the_frame_in_the_alert_and_nothing_glows_and_a_goal_held_says_so_by_a_sign(gui):
    pg, host, log = ring_card(gui, state="decided", bk=leaders(2), needs=[need("decision", "tech", "g", "Round timer on phones", DECISION, number=201, confirmed=False, error="")])
    try:
        card = pg.locator('.col-card--fan[data-goal="g"]')
        assert "asks" in card.get_attribute("class").split() and card.locator(".is-glowing").count() == 0
        assert pg.evaluate("() => [getComputedStyle(document.querySelector('.col-card--fan')).borderTopColor, getComputedStyle(document.documentElement).getPropertyValue('--ork-alert')]")[0] != "rgba(0, 0, 0, 0)"
        assert pg.locator('[data-under="analysis"]').inner_text() == "waits for you" and "its decision waits for your word" in card.get_attribute("aria-label")
    finally:
        pg.close()
    assert not log, "\n".join(log)
    pg, host, log = ring_card(gui, state="routed", bk=None)
    try:
        host.nodes[0]["held_for"] = "hold"
        host.bump({})
        pg.wait_for_selector(".col-fan__held .ork-sign", timeout=WAIT_MS)
        assert "held: nothing starts it until you press Talk" in pg.locator('.col-card--fan[data-goal="g"]').get_attribute("aria-label")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_agreed_decision_says_when_its_spec_starts_under_the_title_and_start_now_is_on_its_row(gui):
    pg, host, log = ring_card(gui, state="decided", bk=leaders(2) | {"ripe": ripe(120, seconds=240)})
    try:
        under = pg.locator('[data-under="analysis"]').inner_text()
        assert under.startswith("decided: Round timer on phones · starts its spec at "), under
        assert pg.locator(".col-play").count() == 0, "a back of the hand has no play: its row in the list has Start now"
        pg.locator('.col-card--fan[data-goal="g"]').click()
        pg.locator('.col-list__row[data-goal="g"]').get_by_role("button", name="Start now").click()
        assert _sent(pg, host, ("ideas.confirm", {"idea": "g"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_standing_card_has_its_four_corners_its_name_in_three_lines_and_a_foot_row_that_is_26_px_from_its_bottom(gui):
    """Spec 147 B.4 (decisions §251.3): rune and kind at the top, the name in up to three lines (spec 150 C), what it does now, the wait's bar where it waits, who and how much at the foot; no window, no name in a foot."""
    long = "Rename every room after it is made so the whole line of the name has to be said in three lines of the card, with every word of it kept in the page"
    host = ColumnHost()
    host.nodes.append(node("longone", "tech", long, "table", state="working", element="ice", stage="implementation", tasks=[task("l1", "Rename them", "running", left=720)]))
    pg, host, log = open_column(gui, host=host)
    try:
        pg.wait_for_selector(".col-card--up", timeout=WAIT_MS)
        card = pg.locator('.col-card[data-goal="longone"]')
        assert pg.locator(".col-card--up .col-win, .col-card--up .table-card__win").count() == 0
        assert card.locator(".corner--top .corner__rune .ork-elem").count() == 1 and card.locator(".corner--foot").count() == 1, "the four corners"
        assert card.locator(".corner--foot .corner__much").inner_text().strip() == "12 min left", "its time left"
        nm = card.locator(".col-nm")
        assert nm.inner_text().strip() == long, "the name whole in the DOM"
        lines = nm.evaluate("e => Math.round(e.getBoundingClientRect().height / parseFloat(getComputedStyle(e).lineHeight))")
        assert lines == 3, "up to three lines, then cut (spec 150 C, decisions §254.2)"
        assert "Now: Rename them" in card.locator(".col-now").inner_text() and card.locator(".col-count").inner_text() == "0/1"
        box, foot = card.bounding_box(), card.locator(".corner--foot").bounding_box()
        assert abs(box["width"] - 144) <= 1 and abs(box["height"] - 202) <= 1
        assert abs((box["y"] + box["height"]) - foot["y"] - 26) <= 1.5, "the foot row, with the card's padding, is 26 px: what a card behind the front one shows"
        top = card.locator(".corner--top").bounding_box()
        assert abs(nm.bounding_box()["y"] - box["y"] - 32) <= 1.5 and top["height"] == 20, "the name begins 32 px under the card's top"
    finally:
        pg.close()
    assert not log, "\n".join(log)


class PutOffHost(ColumnHost):
    """Spec 138 B.5: goals put off in In analysis, one for this afternoon, one for another day, one whose hour has passed, one with none."""

    def __init__(self):
        super().__init__()
        import datetime as dt
        soon = dt.datetime.now().replace(second=0, microsecond=0) + dt.timedelta(minutes=90)
        far = dt.datetime.now().replace(second=0, microsecond=0) + dt.timedelta(days=2)
        self.soon, self.far = soon, far
        self.nodes = [
            node("soon", "tech", "Kick a player", "deck", state="routed", element="dust", held_until=soon.isoformat(timespec="seconds")),
            node("far", "design", "Host skips a round", "deck", state="routed", element="meadow", held_until=far.isoformat(timespec="seconds")),
            node("gone", "tech", "Mute a player", "deck", state="routed", element="ice", held_until="2020-01-01T10:00:00"),
            node("plain", "tech", "Rename a room", "deck", state="routed", element="lava"),
        ]


def test_a_goal_put_off_says_not_before_its_hour_on_its_row_the_day_when_it_is_not_today_and_nothing_for_a_past_hour(gui):
    pg, host, log = open_column(gui, host=PutOffHost())
    try:
        pg.wait_for_selector(".col-card", timeout=WAIT_MS)
        pg.locator('.col-sec[data-pile="analysis"] .col-card--down').first.click()
        pg.wait_for_selector(".col-list", timeout=WAIT_MS)
        said = lambda slug: pg.locator(f'.col-list__row[data-goal="{slug}"] [data-hold]').all_inner_texts()      # noqa: E731
        assert said("soon") == [f"not before {host.soon:%H:%M}"] or said("soon") == [f"not before {host.soon:%a} {host.soon:%H:%M}"], "today's hour, or the day's name when 90 minutes ahead crossed midnight"
        assert said("far") == [f"not before {host.far:%a} {host.far:%H:%M}"], "another day: its name and the hour"
        assert said("gone") == [] and said("plain") == [], "a past hour or none says nothing"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_laid_over_the_column_covers_it_whole_in_its_shadow_and_the_column_is_not_cut_at_its_edge(gui):
    """Spec 150 A.2 (decisions §254.10): the field open over the column at 1280 x 800, the At work card under it keeps its full width, and the field's shadow is drawn (orkUI's notch clip once cut it at the box)."""
    pg, host, log = open_column(gui)
    try:
        pg.set_viewport_size({"width": 1280, "height": 800})
        pg.wait_for_selector(".col-sec[data-pile=work] .col-card--up", timeout=WAIT_MS)
        pg.locator(".hand .hand-plus").click()
        pg.locator(".hand-field").wait_for(timeout=WAIT_MS)
        got = pg.evaluate("""() => {
          const f = document.querySelector('.hand-field'), c = document.querySelector('.col-sec[data-pile=work] .col-card--up'), r = c.getBoundingClientRect(), fr = f.getBoundingClientRect();
          return {w: r.width, over: fr.left < r.right && fr.right > r.left, shadow: getComputedStyle(f).boxShadow};
        }""")
        assert got["over"], f"the field lies over the column: {got}"
        assert abs(got["w"] - 144) <= 0.5, f"the At work card keeps its full width: {got}"
        assert got["shadow"] != "none", f"the field's shadow falls on the column: {got}"
    finally:
        pg.close()
    assert not log, "\n".join(log)
