"""Spec 129 part H2 (docs/specs/129-a-tasks-steps.md, decisions §207.1), in a real browser against a stub host whose tasks carry `steps` as the snapshot serves them (`{items, now, done, total, source, doing}`): the label row of a task's
card (*Doing 2/5*, the pips in orkUI's cell size, the step now in one line in the body face, the time worked in the card's words), the pip now glowing with orkUI's rhythm, an activity with no pips and its line in the muted ink, a task whose steps are
all done (*Checking 4/4*), the lifted card's list with its source said small, the Orkmaster's column card of a goal at work with its tasks' count, the plan's cards, the token under 760 px with its pips alone, and a task with no steps keeping today's label."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, head, node, open_hand, task  # noqa: E402

pytestmark = pytest.mark.browser

DOING = ["write the join", "tests for join", "wire the lobby", "reconnect", "polish"]


def steps(items, now, done, source="file", doing=""):
    """A task's `steps` as the snapshot serves them: `items` a list of `(text, state)`."""
    return {"items": [{"text": t, "state": s} for t, s in items], "now": now, "done": done, "total": len(items), "source": source, "doing": doing}


def five(now=1):
    return steps([(t, "done" if i < now else "now" if i == now else "next") for i, t in enumerate(DOING)], now, now)


def since(secs=72):
    return (datetime.now() - timedelta(seconds=secs)).isoformat(timespec="seconds")


class StepsHost(HandHost):
    """Five goals at work, each the front of its own cascade: `join` (Tech, a steps file: *Doing 2/5 · tests for join*, with a task merged and one waiting behind it), `lobby` (Design, an activity), `check` (Tech, a check with all four steps done),
    `long` (Design, the tool's own list with a long step) and `plain` (Tech, no steps); and a goal in analysis."""

    def __init__(self):
        super().__init__(bare=True)
        long_step = "reconnect every socket after the lobby restarts"
        self.nodes = [
            node("join", "tech", "Let a player rejoin", "table", state="working", stage="implementation", element="ice", tasks=[
                task("a1", "Tests for join", "running", started=since(), steps=five()), task("a2", "Write the join", "merged"), task("a3", "Wire the lobby", "picking")]),
            node("lobby", "design", "Lobby look", "table", state="working", stage="implementation", element="dust", tasks=[
                task("b1", "Draw the lobby", "running", started=since(), steps={"items": [], "now": -1, "done": 0, "total": 0, "source": "activity", "doing": "edits lobby.ts"})]),
            node("check", "tech", "Check the rounds", "table", state="working", stage="implementation", element="lava", tasks=[
                task("c1", "Check the rounds", "testing", band="check", started=since(10), steps=steps([("run the suite", "done"), ("read the diff", "done"), ("try a rejoin", "done"), ("sign off", "done")], -1, 4))]),
            node("long", "design", "Sockets", "table", state="working", stage="implementation", element="meadow", tasks=[
                task("d1", "Sockets", "running", started=since(), steps=steps([("open", "done"), (long_step, "now"), ("close", "next")], 1, 1, source="todo"))]),
            node("plain", "tech", "A plain goal", "table", state="working", stage="implementation", element="void", tasks=[task("e1", "Plain work", "running", started=since())]),
            node("raw", "tech", "Kick a player", "deck", state="raw", element="dust"),
        ]


def open_steps(gui, width="wide"):
    pg, host, log = open_hand(gui, host=StepsHost(), width=width)
    pg.wait_for_selector(".table-card, .table-token", timeout=WAIT_MS)
    return pg, host, log


def card(pg, goal, tid):
    return pg.locator(f'[data-lkey="t:task:{goal}/{tid}"]')


def stage(c):
    """The stage's word and the step of the whole a card says to a screen reader (spec 147 A: the label row is the foot's corners now, the stage lives in the card's words): *doing 2/5*."""
    return re.search(r"\b(Planning|Doing|Checking|To look at|Done)\b( \d+/\d+)?", c.get_attribute("aria-label").split(": ", 1)[1]).group(0).lower()


def css(el, prop):
    return el.evaluate("(e, p) => getComputedStyle(e)[p]", prop)


def token(pg, name):
    """A colour token of orkUI's, as the page computes it (what the pips and words are drawn in)."""
    return pg.evaluate("(n) => { const d = document.createElement('span'); d.style.color = `var(${n})`; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; }", name)


def test_the_label_row_says_the_stage_the_step_of_the_whole_the_pips_and_the_step_now_and_the_time_goes_to_the_cards_words(gui):
    pg, host, log = open_steps(gui)
    try:
        c = card(pg, "join", "a1")
        c.wait_for(timeout=WAIT_MS)
        row = c.locator(".corner--foot")
        assert stage(c) == "doing 2/5", "the stage's word and done + 1 of the whole"
        assert c.locator(".table-win__now").inner_text().strip() == "tests for join", "the step now, under the stage"
        assert c.locator(".corner--top .ork-elem.is-glowing").count() == 1, "the flame is still the goal's rune, now in the top corner (spec 147 A)"
        pips = c.locator(".table-pips > i")
        assert pips.count() == 5 and [p.get_attribute("data-state") for p in pips.all()] == ["done", "now", "next", "next", "next"]
        boxes = [p.bounding_box() for p in pips.all()]
        assert all(abs(b["width"] - 6) <= 0.5 and abs(b["height"] - 6) <= 0.5 for b in boxes), boxes
        assert all(abs(boxes[i + 1]["x"] - (boxes[i]["x"] + boxes[i]["width"]) - 2) <= 0.5 for i in range(4)), "2 px apart"
        assert css(pips.nth(0), "backgroundColor") == token(pg, "--ork-ink"), "done: filled in the ink"
        assert css(pips.nth(1), "backgroundColor") == token(pg, "--ork-elem-ice"), "the one now: in the goal's element colour"
        assert css(pips.nth(2), "backgroundColor") == token(pg, "--ork-frame") == css(pips.nth(4), "backgroundColor"), "next: faint"
        said, titled = c.get_attribute("aria-label"), c.get_attribute("title")
        assert "Doing 2/5 · tests for join" in said and "Tests for join" in said
        assert "worked 1 m" in said and "worked 1 m" in titled and "Let a player rejoin" in titled, "the time worked moved to the card's words"
        assert not re.search(r"\d+ [ms]\b", row.inner_text().lower()), "no time on the label"
        pixel = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ork-font-pixel').split(',')[0].trim().replace(/[\"']/g, '')")
        assert pixel and pixel not in css(c.locator(".table-win__now"), "fontFamily"), "a person's words: the body face"
        box, now = c.bounding_box(), c.locator(".table-win__now").bounding_box()
        assert now["x"] >= box["x"] and now["x"] + now["width"] <= box["x"] + box["width"] and row.bounding_box()["x"] + row.bounding_box()["width"] <= box["x"] + box["width"] + 0.5, "inside the card"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_step_now_is_cut_to_two_lines_in_the_window_and_read_whole_by_a_screen_reader(gui):
    pg, host, log = open_steps(gui)
    try:
        c = card(pg, "long", "d1")
        c.wait_for(timeout=WAIT_MS)
        now = c.locator(".table-win__now")
        assert now.inner_text().strip() == "reconnect every socket after the lobby restarts", "the host cut it to 40 characters; the page cuts it to two lines"
        assert css(now, "overflow") == "hidden" and now.evaluate("e => getComputedStyle(e).webkitLineClamp") == "2", "two lines at most"
        assert now.bounding_box()["height"] <= 31, "the step now takes two lines at most"
        win = c.locator(".table-card__win")
        assert 80 <= win.bounding_box()["height"] <= 92 and win.get_attribute("data-window") == "steps", "the window takes what the corners and the title leave of the 5 : 7 card (spec 147 A.2) and holds the steps"
        assert win.locator(".table-win__by .ork-race__head").count() == 1 and win.locator(".table-win__busy.is-glowing").count() == 1, "the worker's head with the busy mark"
        assert "Doing 2/3 · reconnect every socket after the lobby restarts" in c.get_attribute("aria-label"), "a screen reader reads it whole"
        assert abs(card(pg, "plain", "e1").locator(".table-card__win").bounding_box()["height"] - win.bounding_box()["height"]) <= 1, "every lane card has the same window height"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_pip_now_glows_in_orkuis_rhythm_and_stands_still_under_reduced_motion(gui):
    pg, host, log = open_steps(gui)
    try:
        c = card(pg, "join", "a1")
        c.wait_for(timeout=WAIT_MS)
        glow = c.locator(".table-pips > i.is-glowing")
        assert glow.count() == 1 and glow.get_attribute("data-state") == "now", "only the one now glows"
        assert pg.locator("[data-lkey] .table-pips > i.is-glowing").count() == 2, "one a task at work that has a step now (the steps file's, the tool's list): not the check, whose steps are all done"
        name, dur, timing = glow.evaluate("e => { const s = getComputedStyle(e); return [s.animationName, s.animationDuration, s.animationTimingFunction]; }")
        flame = c.locator(".corner--top .ork-elem.is-glowing").evaluate("e => { const s = getComputedStyle(e); return [s.animationName, s.animationDuration, s.animationTimingFunction]; }")
        assert [name, dur, timing] == flame == ["ork-glow", "2.4s", "steps(6)"], "the flame's rhythm, orkUI's keyframes"
        pg.emulate_media(reduced_motion="reduce")
        assert css(glow, "animationName") == "none" and css(glow, "opacity") == "1"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_check_with_every_step_done_says_checking_and_the_whole_and_no_pip_glows(gui):
    pg, host, log = open_steps(gui)
    try:
        c = card(pg, "check", "c1")
        c.wait_for(timeout=WAIT_MS)
        assert stage(c) == "checking 4/4"
        assert [p.get_attribute("data-state") for p in c.locator(".table-pips > i").all()] == ["done"] * 4
        assert c.locator(".table-pips > i.is-glowing").count() == 0 and c.locator(".table-win__now").count() == 0, "nothing is now: no step line"
        assert "Checking 4/4" in c.get_attribute("aria-label")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_an_activity_has_no_pips_and_its_line_in_the_muted_ink(gui):
    pg, host, log = open_steps(gui)
    try:
        c = card(pg, "lobby", "b1")
        c.wait_for(timeout=WAIT_MS)
        assert c.locator(".table-pips").count() == 0
        assert stage(c) == "doing", "no count: there is no whole"
        now = c.locator(".table-win__now")
        assert now.inner_text().strip() == "edits lobby.ts" and css(now, "color") == token(pg, "--ork-ink-muted")
        assert "Doing · edits lobby.ts" in c.get_attribute("aria-label") and "worked" in c.get_attribute("aria-label")
        assert css(c.locator(".table-win__now"), "color") != css(card(pg, "join", "a1").locator(".table-win__now"), "color"), "a step is lit, an activity is not"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_task_without_steps_keeps_todays_label_with_the_time_in_it(gui):
    pg, host, log = open_steps(gui)
    try:
        c = card(pg, "plain", "e1")
        c.wait_for(timeout=WAIT_MS)
        text = c.locator(".corner__much").inner_text().strip()
        assert re.fullmatch(r"worked 1 m \d+ s", text.lower()), text                                                    # the time worked is the foot's figure (spec 147 A)
        assert c.locator(".table-pips").count() == 0 and c.locator(".table-win__now").count() == 0
        assert c.get_attribute("aria-label") == "Plain work, A plain goal: Doing" and c.get_attribute("title") == "A plain goal"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_task_behind_the_front_one_keeps_its_stage_sign_only(gui):
    pg, host, log = open_steps(gui)
    try:
        pg.wait_for_selector(".table-tedge", timeout=WAIT_MS)
        assert pg.locator(".table-tedge .table-pips, .table-tedge .table-win__now").count() == 0, "the strips of a cascade keep their stage sign only"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_lifted_card_lists_the_steps_and_says_where_they_come_from(gui):
    pg, host, log = open_steps(gui)
    try:
        card(pg, "join", "a1").click()
        back = pg.locator(".table-back")
        back.wait_for(timeout=WAIT_MS)
        sec = back.locator(".table-steps")
        sec.wait_for(timeout=WAIT_MS)
        items = sec.locator(".table-steps__item")
        assert [" ".join(t.split()) for t in items.all_inner_texts()] == ["✓ write the join", "tests for join", "wire the lobby", "reconnect", "polish"]
        assert [i.get_attribute("data-state") for i in items.all()] == ["done", "now", "next", "next", "next"]
        assert items.nth(1).get_attribute("aria-current") == "step"
        assert css(items.nth(0), "color") == token(pg, "--ork-ink-muted") and css(items.nth(1), "color") == token(pg, "--ork-ink") and css(items.nth(2), "color") == token(pg, "--ork-ink-faint")
        assert sec.locator(".table-steps__src").inner_text().strip() == "from its steps file"
        assert back.locator(".ork-label", has_text="Steps").count() == 1
        assert css(sec.locator(".table-steps__text").first, "fontFamily") == css(back.locator(".table-back__cap"), "fontFamily"), "the body face"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.table-back')", timeout=WAIT_MS)
        card(pg, "long", "d1").click()
        pg.locator(".table-back .table-steps").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-back .table-steps__src").inner_text().strip() == "from its own list"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.table-back')", timeout=WAIT_MS)
        card(pg, "lobby", "b1").click()
        pg.locator(".table-back .table-steps").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-back .table-steps__item").count() == 0 and pg.locator(".table-back .table-steps__line").inner_text().strip() == "edits lobby.ts"
        assert pg.locator(".table-back .table-steps__src").inner_text().strip() == "what it is doing"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.table-back')", timeout=WAIT_MS)
        card(pg, "plain", "e1").click()
        pg.locator(".table-back").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-back .table-steps").count() == 0, "no steps, no section"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_orkmasters_card_of_a_goal_at_work_says_its_tasks_done_of_all_at_its_foot(gui):
    pg, host, log = open_steps(gui)
    try:
        pg.wait_for_selector('.col-card[data-goal="join"]', timeout=WAIT_MS)
        count = pg.locator('.col-card[data-goal="join"] .col-foot .col-count')
        assert count.inner_text().strip() == "1/3", "a1 at work, a2 merged, a3 waiting"
        assert "1 of 3 tasks finished" in pg.locator('.col-card[data-goal="join"]').get_attribute("aria-label")
        assert pg.locator('.col-card[data-goal="lobby"] .col-count').inner_text().strip() == "0/1"
        assert pg.locator('.col-card[data-goal="raw"] .col-count, .col-card--down .col-count').count() == 0, "a goal not at work has no count"
        foot, c = pg.locator('.col-card[data-goal="join"] .col-foot').bounding_box(), count.bounding_box()
        assert c["x"] >= foot["x"] and c["x"] + c["width"] <= foot["x"] + foot["width"] + 0.5, "inside the foot"
        assert count.inner_text().strip() != "2/5", "the tasks, not the steps"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_plans_cards_wear_the_same_label_row(gui):
    pg, host, log = open_steps(gui)
    try:
        pg.locator('.col-card[data-goal="join"]').click()
        pg.wait_for_selector(".table-board--plan", timeout=WAIT_MS)
        c = pg.locator('.plan-slot[data-plan-task="a1"] .table-card')
        assert stage(c) == "doing 2/5" and c.locator(".table-pips > i").count() == 5
        assert c.locator(".table-win__now").inner_text().strip() == "tests for join"
        assert pg.locator('.plan-slot[data-plan-task="a3"] .table-pips').count() == 0, "a task still waiting has no steps"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_under_760_px_the_token_shows_the_pips_only(gui):
    pg, host, log = open_steps(gui, width="narrow")
    try:
        pg.wait_for_selector('.table-token[data-goal="join"]', timeout=WAIT_MS)
        tok = pg.locator('.table-token[data-goal="join"]')
        pips = tok.locator(".table-pips > i")
        assert pips.count() == 5 and [p.get_attribute("data-state") for p in pips.all()] == ["done", "now", "next", "next", "next"]
        assert tok.locator(".table-win__now").count() == 0 and tok.locator(".table-stage").count() == 0, "no line, no words"
        assert tok.locator(".table-pips > i.is-glowing").count() == 1
        box, last = tok.bounding_box(), pips.nth(4).bounding_box()
        assert last["x"] + last["width"] <= box["x"] + box["width"] + 0.5, "the pips lie inside the token"
        assert "Doing 2/5 · tests for join" in tok.get_attribute("aria-label")
        assert pg.locator('.table-token[data-goal="lobby"] .table-pips, .table-token[data-goal="plain"] .table-pips').count() == 0, "an activity and a task with no steps have none"
        assert pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


class WindowHost(StepsHost):
    """A goal with only a task waiting (an elf's, then a Grunt's), one failed with its reason and one at work with neither steps nor a doing line."""

    def __init__(self):
        super().__init__()
        self.nodes = [
            node("wait", "design", "Draw the loop", "table", state="working", stage="implementation", element="meadow", tasks=[
                task("r1", "Sketch the loop", "running", started=since()), task("w1", "Make the loop", "waiting", head=head("elf", craft="design", tier="laborer")),
                task("w2", "Wire the timer", "ready", head=head("peon", tier="laborer"))]),
            node("fail", "tech", "Tests of the loop", "table", state="working", stage="implementation", element="dust", tasks=[
                task("f1", "Fix the tests", "failed", started=since(), error="Tests: 2 fail in audio.test.ts (the loop's end clicks)\nsecond line of the log")]),
            node("bare", "tech", "A bare goal", "table", state="working", stage="implementation", element="void", tasks=[task("n1", "Bare work", "running", started=since())]),
        ]


def test_a_waiting_task_shows_the_head_of_the_seat_that_takes_it_faint_and_says_who_takes_it_next(gui):
    pg, host, log = open_hand(gui, host=WindowHost(), width="wide")
    try:
        pg.wait_for_selector(".table-card", timeout=WAIT_MS)
        pg.locator('.col-card[data-goal="wait"]').click()                                                              # a task waiting is drawn on its goal's plan, not in a lane
        pg.wait_for_selector(".table-board--plan", timeout=WAIT_MS)
        wait, grunt = (pg.locator(f'.plan-slot[data-plan-task="{i}"] .table-card__win') for i in ("w1", "w2"))
        assert wait.get_attribute("data-window") == "wait" and wait.locator(".table-win__line").inner_text().strip() == "an elf takes it next"
        assert wait.locator(".ork-race__head").count() == 1 and float(css(wait.locator(".table-win__faint"), "opacity")) < 0.5, "the seat's head, faint"
        assert grunt.locator(".table-win__line").inner_text().strip() == "a Grunt takes it next"
        assert [round(w.bounding_box()["height"]) for w in (wait, grunt)] == [round(wait.bounding_box()["height"])] * 2, "the window's height is the same on both, so the cards line up"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_failed_card_says_its_reason_and_one_with_nothing_to_say_keeps_the_type_sign(gui):
    pg, host, log = open_hand(gui, host=WindowHost(), width="wide")
    try:
        pg.wait_for_selector(".table-card", timeout=WAIT_MS)
        pg.locator(".table-thrown").first.wait_for(timeout=WAIT_MS)                                                     # a failure lies in the hand after its beat (spec 128 C.2): the card is put back in its lane
        pg.evaluate("() => import('/static/js/table/flight.js').then((m) => { m.thrown.value = new Map(); })")
        fail = card(pg, "fail", "f1").locator(".table-card__win")
        assert fail.get_attribute("data-window") == "fail" and fail.locator(".ork-sign.alert").count() == 1
        reason = fail.locator(".table-win__reason")
        assert reason.inner_text().strip() == "Tests: 2 fail in audio.test.ts (the loop's end clicks)", "the reason, its first line"
        assert css(reason, "overflow") == "hidden" and reason.evaluate("e => getComputedStyle(e).webkitLineClamp") == "2" and reason.bounding_box()["height"] <= 31
        assert css(fail.locator(".ork-sign"), "color") == token(pg, "--ork-danger")
        bare = card(pg, "bare", "n1").locator(".table-card__win")
        assert bare.get_attribute("data-window") == "sign" and bare.locator(".table-win").count() == 0, "at work with nothing to say: today's sign (the stub's goal has no type, so none is drawn)"
    finally:
        pg.close()
    assert not log, "\n".join(log)


class LeaderHost(StepsHost):
    """A goal whose plan holds a task merged, one to look at, one waiting for its party's leader (a shaman: Tech's leader does it, as at Lean) and one waiting for a Grunt, and one at work."""

    def __init__(self):
        super().__init__()
        self.nodes = [node("mix", "tech", "Mark words", "table", state="working", stage="implementation", element="ice", tasks=[
            task("m1", "Change the terms", "merged"), task("v1", "Level the marks", "review"), task("r1", "Mark coverage", "running", started=since()),
            task("l1", "Review the marks", "waiting", head={**head("shaman", tier="warrior"), "leader": True}), task("l2", "Count the marks", "ready", head=head("peon", tier="laborer"))])]


def test_a_task_to_look_at_says_to_look_at_a_merged_one_done_and_a_leaders_seat_says_its_leader_takes_it_next(gui):
    """Spec 143 F.1, F.2 (decisions §250.7): never *Planning* for a task merged or to look at, never *a Grunt* for a leader's seat; a member's word stands for a member."""
    pg, host, log = open_hand(gui, host=LeaderHost(), width="wide")
    try:
        pg.wait_for_selector(".table-card", timeout=WAIT_MS)
        pg.locator('.col-card[data-goal="mix"]').click()
        pg.wait_for_selector(".table-board--plan", timeout=WAIT_MS)
        assert tuple(stage(card(pg, "mix", tid)) for tid in ("m1", "v1", "l1")) == ("done", "to look at", "planning")
        assert card(pg, "mix", "m1").get_attribute("data-stage") == "done" and card(pg, "mix", "v1").get_attribute("data-stage") == "review"
        lead, grunt = (pg.locator(f'.plan-slot[data-plan-task="{i}"] .table-card__win .table-win__line') for i in ("l1", "l2"))
        assert lead.inner_text().strip() == "Its leader takes it next", "a leader's seat never says a member's word"
        assert grunt.inner_text().strip() == "a Grunt takes it next", "a member's stands"
        # the pure rule: the stages by state, and the cascade's rank (to look at before Checking, done last)
        got = pg.evaluate("""async () => { const d = await import('/static/js/table/data.js'), s = await import('/static/js/table/steps.js');
          return [['review', ''], ['merged', ''], ['testing', 'check'], ['running', ''], ['waiting', ''], ['failed', '']].map(([state, band]) => d.stageOf({ state, band }))
            .concat(['shaman', 'dryad', 'imp', 'fairy', 'unicorn', 'lich', 'peon', 'elf'].map((race) => s.seatWords({ race, tier: 'warrior' }))); }""")
        assert got == ["review", "done", "checking", "doing", "planning", "doing", *["its leader"] * 6, "a Grunt", "an elf"]
    finally:
        pg.close()
    assert not log, "\n".join(log)
