"""The hearing's face (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.7, §7 F; decisions §198.6; the mockup docs/mockups/hearing/ 3), in a real browser against a stub host answering the Needs you rows `hearing` and `fork` (with its
`hearing`), `ideas.page` and the command `ideas.throw {idea, moment, dir | text}`: the card in the hand (the question sign, the first leader's head, the heading at its foot, under the first lane); lifted over the pane at the wide and the narrow
widths and in the middle of a phone-sized page, the goal's card (its rune and name, *Done when*, else its gist) and the sides around it (→ right, ← left, ↑ up), each its leaders' heads (the first at 28 px, the others at 16), its line and its outcome; a swipe
past a third of the way throwing the side, one short of it coming back, a fling, down being no side; a press, the keys and the person's own words; the toast *Thrown to <Leader>: <outcome>*, a drop held for six seconds with **Undo** (Undo before it sends
nothing); a refusal keeping the hearing; no sideways scroll; nothing moving under reduced motion. Screenshots to $HEARING_SHOTS when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, need, node, open_hand  # noqa: E402
from tests.test_shell_browser import _calls  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["HEARING_SHOTS"]) if os.environ.get("HEARING_SHOTS") else None
DROP_MS = 6000


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def side(dir_, kind, leaders, names, line, outcome, **more):
    return {"dir": dir_, "kind": kind, "leaders": leaders, "names": names, "also": names[1:], "line": line, "outcome": outcome, **more}


GO = side("right", "go", ["product", "design"], ["Product lead", "Design lead"], "It serves the job the owner named; the most asked thing this week.", "Do it", doubts=[])
DROP = side("left", "drop", ["tech"], ["Tech lead"], "It adds a third caller to server/ws", "Drop it")
SMALLER = side("up", "smaller", ["design"], ["Design lead"], "A crown over a name crowds the small screens; a frame says the same and fits.", "Do the smaller one: a gold frame, no crown", instead="a gold frame, no crown")
LATER = side("left", "later", ["tech"], ["Tech lead"], "First needs the server's clock; the timer goal brings it.", "After Round timer", after="timer", after_title="Round timer")
SIDES = [GO, DROP, SMALLER]
PAGE = [{"name": "Gist", "text": "Players see who answered first."}]
PAGE_DONE = [{"name": "Gist", "text": "Players see who answered first."}, {"name": "Done when", "text": "- The first answer's player wears a mark\n- The mark is gone when the next round starts"}]


def hearing(idea="night", title="Night mode for the lobby", sides=None, heading="Product and Design disagree with Tech", **more):
    return need("hearing", "tech", idea, title, heading, moment="talk", heading=heading, sides=[dict(s) for s in sides or SIDES], left_out=[], own=True, **more)


class HearingHost(HandHost):
    """A project of four parties and a goal `night` of Tech's at Talk whose leaders disagree (Product and Design for it, Tech for dropping it, Design for a smaller one); `second` adds a goal `lobby` with a hearing of its own."""

    def __init__(self, second=False, sides=None, page=None):
        super().__init__(bare=True)
        self.nodes = [n for n in self.nodes if n["place"] != "hand"]
        self.nodes.append(node("night", "tech", "Night mode for the lobby", "table", state="talk", element="ice", asks_you=True, needs_you="hearing"))
        self.needs = [hearing("night", sides=sides)]
        if second:
            self.nodes.append(node("lobby", "tech", "Lobby chat", "table", state="talk", element="dust", asks_you=True, needs_you="hearing"))
            self.needs.append(hearing("lobby", "Lobby chat", sides=sides))
        self.page = PAGE if page is None else page
        self.refuse = False

    def handle(self, name, a):
        if name == "ideas.page":
            self.log.append((name, a))
            return {"slug": a["slug"], "title": a["slug"], "sections": self.page, "state": "talk", "track": "tech"}
        if name == "ideas.throw":
            self.log.append((name, a))
            if self.refuse:
                return {"error": "The keeper is busy with this goal: a moment"}
            self.needs = [n for n in self.needs if not (n["kind"] == "hearing" and n["idea"] == a["idea"])]
            return self.bump({"ok": True, "moment": a["moment"], "kind": "own" if a.get("text") else "go", "dir": a.get("dir", ""), "outcome": "Do it", "to": []})
        return super().handle(name, a)


def open_hearing(gui, width="wide", host=None, reduced=False, **more):
    server, browser = gui
    pg, host, log = open_hand(gui, host=host or HearingHost(**more), width=width)
    if reduced:
        pg.emulate_media(reduced_motion="reduce")
    pg.locator(".hand-stack, .up-row").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def front(pg, goal="night"):
    return pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]')


def lift(pg, goal="night", width="wide"):
    """The hearing, opened: over the pane (a press on the card), or already in the phone's middle. Returns the hearing."""
    if width != "phone":
        front(pg, goal).click(position={"x": 10, "y": 24})
    hr = pg.locator(f'.hr[data-goal="{goal}"]')
    hr.wait_for(timeout=WAIT_MS)
    return hr


def card(pg):
    return pg.locator(".hr-card")


def centre(loc):
    b = loc.bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


def drag(pg, dx, dy, steps=12, release=True):
    """A pointer down on the card's middle, moved by (dx, dy), released (or not)."""
    x, y = centre(card(pg))
    pg.mouse.move(x, y)
    pg.mouse.down()
    pg.mouse.move(x + dx, y + dy, steps=steps)
    if release:
        pg.mouse.up()


def way(pg, dir_):
    """How far the side lies from the card along its axis."""
    cx, cy = centre(card(pg))
    sx, sy = centre(pg.locator(f'.hr-side[data-dir="{dir_}"] .hr-side__btn'))
    return cy - sy if dir_ == "up" else abs(sx - cx)


def toast_text(pg):
    pg.locator(".gui-toast").first.wait_for(timeout=WAIT_MS)
    return pg.locator(".gui-toast .gui-toast__text").first.text_content().strip()


def thrown(pg, host, **want):
    got = _calls(pg, host, "ideas.throw")
    assert got == [{"idea": "night", "moment": "talk", **want}], got


def no_throw(pg, host, ms=400):
    pg.wait_for_timeout(ms)
    assert not [a for n, a in host.log if n == "ideas.throw"], "nothing was thrown"


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_hearing_is_a_card_in_the_hand_with_the_question_sign_the_first_leaders_head_and_its_heading(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        c = front(pg)
        assert c.get_attribute("data-kind") == "hearing" and c.get_attribute("aria-label").startswith("Hearing: ")
        assert c.locator(".hand-card__name").text_content().strip() == "Night mode for the lobby" and c.locator(".hand-card__head .ork-elem.ice").count() == 1
        assert c.locator(".hand-card__window .ork-sign.question").count() == 1 and c.locator(".hand-card__asker .ork-race__head").count() == 1
        assert "unicorn" in c.locator(".hand-card__asker .ork-race__head").get_attribute("src"), "the first leader of the first side that has one: Product's"
        if width == "wide":
            assert c.locator(".hand-card__foot").text_content().strip() == "Product and Design disagree with Tech"
        assert c.locator(".ork-gem").count() == 0, "it spends nothing"
        assert pg.locator(".hand-lane").nth(0).locator('.hand-stack[data-goal="night"]').count() == 1, "the whole goal's: under the first lane"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_lifted_over_the_pane_the_goals_card_stands_in_the_middle_and_the_sides_around_it(gui, width):
    pg, host, log = open_hearing(gui, width, page=PAGE_DONE)
    try:
        hr = lift(pg, width=width)
        assert pg.locator('.table-over[data-kind="choose"]').count() == 1, "it is the pane's, not an aside"
        assert hr.locator(".hr-title").text_content().strip() == "Product and Design disagree with Tech"
        c = card(pg)
        assert c.locator(".hr-card__name").text_content().strip() == "Night mode for the lobby" and c.locator(".ork-elem.ice").count() == 1
        pg.wait_for_function("() => document.querySelectorAll('.hr-card__done li').length === 2", timeout=WAIT_MS)
        assert c.locator(".hr-card__lab").text_content().strip().lower() == "done when"
        assert c.locator(".hr-own").text_content().strip() == "Or say it in your own words"
        sides = {s.get_attribute("data-dir"): s for s in hr.locator(".hr-side").all()}
        assert sorted(sides) == ["left", "right", "up"]
        right = sides["right"]
        assert right.locator(".hr-says").text_content().strip() == GO["line"] and right.locator(".hr-out__words").text_content().strip() == "Do it"
        assert right.locator(".hr-who__names").text_content().strip() == "Product lead and Design lead"
        heads = right.locator(".hr-head .ork-race__head")
        assert heads.count() == 2 and heads.nth(0).bounding_box()["width"] == 28 and heads.nth(1).bounding_box()["width"] == 16, "the first leader's head at 28 px, the others' at 16"
        assert sides["left"].locator(".hr-out__words").text_content().strip() == "Drop it" and sides["left"].locator(".ork-sign.cross").count() == 1
        assert sides["up"].locator(".hr-out__words").text_content().strip() == "Do the smaller one: a gold frame, no crown"
        for dir_, s in sides.items():
            label = s.locator(".hr-side__btn").get_attribute("aria-label")
            assert label.startswith(s.locator(".hr-out__words").text_content().strip()) and "argued by" in label, "a button with its outcome in its aria-label"
        cb, rb, lb, ub = c.bounding_box(), right.bounding_box(), sides["left"].bounding_box(), sides["up"].bounding_box()
        if width == "wide":
            assert rb["x"] > cb["x"] + cb["width"] and lb["x"] + lb["width"] < cb["x"] and ub["y"] + ub["height"] <= cb["y"] + 1, "→ at the right, ← at the left, ↑ above"
        else:
            assert ub["y"] + ub["height"] <= cb["y"] + 1 and lb["y"] >= cb["y"] + cb["height"] - 1 and rb["y"] >= cb["y"] + cb["height"] - 1 and lb["x"] < rb["x"], "the phone-sized layout: ↑ above, ← and → under"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.hr-card')).touchAction") == "none"
        assert pg.evaluate("() => getComputedStyle(document.querySelector('.hr')).touchAction") != "none", "the page scrolls everywhere but on the card"
        assert hr.locator(".hr-hint").text_content().strip() == "Swipe the card to the side you take, or press it"
        shot(pg, f"{width}-hearing")
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_whose_sections_are_not_written_says_its_gist_and_a_goal_alone_says_nobody_argued_for_it(gui):
    pg, host, log = open_hearing(gui, "wide", sides=[side("right", "go", [], [], "", "Go on anyway"), DROP])
    try:
        hr = lift(pg)
        pg.wait_for_function("() => document.querySelector('.hr-card__gist')?.textContent.trim() === 'Players see who answered first.'", timeout=WAIT_MS)
        assert card(pg).locator(".hr-card__done").count() == 0
        go = hr.locator('.hr-side[data-dir="right"]')
        assert go.locator(".hr-head").count() == 0 and go.locator(".hr-who__names").text_content().strip() == "No one"
        assert go.locator(".hr-says").text_content().strip() == "Nobody argued for it: the goal as you wrote it." and go.locator(".hr-out__words").text_content().strip() == "Go on anyway"
        assert hr.locator('.hr-side[data-dir="up"]').count() == 0, "a side that is not there is not drawn"
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_swipe_past_a_third_of_the_way_throws_the_side_and_the_toast_says_where(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        lift(pg, width=width)
        far = way(pg, "right")
        drag(pg, far / 3 + 30, 0)
        thrown(pg, host, dir="right")
        assert toast_text(pg).startswith("Thrown to Product lead: Do it")
        assert pg.locator(".gui-toast").first.get_by_role("button", name="Undo").count() == 0, "the host takes no throw back: only a drop waits"
        pg.wait_for_function("() => !document.querySelector('.hr')", timeout=WAIT_MS)
        assert pg.locator('.hand-stack[data-goal="night"]').count() == 0, "the card left the hand"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_swipe_short_of_a_third_brings_the_card_back_and_it_tilts_and_stamps_the_outcome_while_it_nears(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        lift(pg, width=width)
        short = max(20, min(way(pg, "right") / 3 - 30, 40))
        drag(pg, short, 0, release=False)
        assert pg.locator('.hr-side[data-dir="right"].is-near').count() == 1 and pg.locator(".hr-stamp").text_content().strip() == "Do it", "the side grows and its outcome is stamped on the card"
        transform = pg.evaluate("() => document.querySelector('.hr-card').style.transform")
        assert "rotate(" in transform and "translate(" in transform, "the card follows the pointer and tilts toward the side"
        pg.mouse.up()
        pg.wait_for_function("() => !document.querySelector('.hr-card').style.transform && !document.querySelector('.hr-side.is-near')", timeout=WAIT_MS)
        assert pg.locator(".hr-stamp").text_content().strip() == ""
        no_throw(pg, host)
        assert pg.locator(".hr").count() == 1 and card(pg).evaluate("(el) => getComputedStyle(el).opacity") == "1"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_down_is_no_side_and_a_card_dragged_down_comes_back(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        drag(pg, 0, 300, release=False)
        assert pg.locator(".hr-side.is-near").count() == 0 and pg.locator(".hr-stamp").text_content().strip() == ""
        assert pg.evaluate("() => parseFloat(document.querySelector('.hr-card').style.transform.match(/translate\\([^,]+, ([-\\d.]+)px/)[1])") < 100, "it holds back"
        pg.mouse.up()
        pg.wait_for_function("() => !document.querySelector('.hr-card').style.transform", timeout=WAIT_MS)
        no_throw(pg, host)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_flung_toward_a_side_is_thrown_though_it_went_but_a_little_way(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        drag(pg, 0, -45, steps=2)                                                                       # a flick up: fast, and nowhere near a third of the way
        thrown(pg, host, dir="up")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_drag_starting_on_the_sides_or_the_words_button_is_no_gesture(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        x, y = centre(pg.locator(".hr-own"))
        pg.mouse.move(x, y)
        pg.mouse.down()
        pg.mouse.move(x + 400, y, steps=8)
        pg.mouse.up()
        no_throw(pg, host)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_press_on_a_side_throws_it_at_once(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        lift(pg, width=width)
        pg.locator('.hr-side[data-dir="up"] .hr-side__btn').click()
        thrown(pg, host, dir="up")
        assert toast_text(pg).startswith("Thrown to Design lead: Do the smaller one: a gold frame, no crown")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("key,dir_", [("ArrowRight", "right"), ("ArrowUp", "up")])
def test_the_arrow_keys_throw_a_side(gui, key, dir_):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        assert pg.evaluate("() => document.activeElement?.classList.contains('hr-card')"), "the card has the focus: the keys are its own"
        pg.keyboard.press(key)
        thrown(pg, host, dir=dir_)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_key_for_a_side_that_is_not_there_throws_nothing(gui):
    pg, host, log = open_hearing(gui, "wide", sides=[GO, SMALLER])
    try:
        lift(pg)
        pg.keyboard.press("ArrowLeft")
        no_throw(pg, host)
        pg.keyboard.press("ArrowDown")
        no_throw(pg, host)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_enter_on_the_card_opens_the_field_for_the_persons_own_words_and_sends_them_as_text(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        lift(pg, width=width)
        pg.keyboard.press("Enter")
        field = pg.locator(".hr-field__text")
        field.wait_for(timeout=WAIT_MS)
        assert pg.evaluate("() => document.activeElement?.classList.contains('hr-field__text')"), "the field has the focus"
        pg.keyboard.press("ArrowRight")
        no_throw(pg, host, 200)
        field.fill("Do it, and only for the lobby")
        shot(pg, f"{width}-hearing-own")
        pg.keyboard.press("Enter")
        thrown(pg, host, text="Do it, and only for the lobby")
        assert toast_text(pg).startswith("Said in your own words")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_words_button_opens_the_field_and_esc_closes_it_with_the_card_kept(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        pg.get_by_role("button", name="Or say it in your own words").click()
        pg.locator(".hr-field__text").fill("later")
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hr-field')", timeout=WAIT_MS)
        assert pg.locator(".hr").count() == 1, "Esc closes the field, not the hearing"
        no_throw(pg, host, 100)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_drop_is_sent_only_when_the_toast_goes_and_undo_before_that_sends_nothing(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        pg.locator('.hr-side[data-dir="left"] .hr-side__btn').click()
        text = toast_text(pg)
        assert text.startswith("Thrown to Tech lead: Drop it") and "6 s" in text
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"night\"]')", timeout=WAIT_MS)       # the card is out of the hand meanwhile
        pg.wait_for_function("() => !document.querySelector('.hr')", timeout=WAIT_MS)
        no_throw(pg, host, 1500)
        pg.locator(".gui-toast").get_by_role("button", name="Undo").click()
        pg.wait_for_function("() => document.querySelector('.hr[data-goal=\"night\"]')", timeout=WAIT_MS)                # the hearing is back over the pane
        assert front(pg).count() == 1, "and its card in the hand"
        pg.wait_for_timeout(DROP_MS + 600)
        assert not [a for n, a in host.log if n == "ideas.throw"], "Undo before the toast went: nothing was sent"
        assert pg.locator(".hr").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_a_drop_picks_the_next_goal_and_undo_brings_the_hearing_back_with_nothing_sent(gui):
    pg, host, log = open_hearing(gui, "phone", second=True)
    try:
        lift(pg, width="phone")
        pg.locator('.hr-side[data-dir="left"] .hr-side__btn').click()
        assert "Dropped in 6 s" in toast_text(pg)
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'lobby'", timeout=WAIT_MS)
        pg.locator(".gui-toast").get_by_role("button", name="Undo").click()
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'night' && document.querySelector('.hr[data-goal=\"night\"]')", timeout=WAIT_MS)
        pg.wait_for_timeout(DROP_MS + 600)
        assert not [a for n, a in host.log if n == "ideas.throw"], "Undo before the toast went: nothing was sent"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_drop_not_undone_is_sent_when_its_toast_goes(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        pg.keyboard.press("ArrowLeft")
        toast_text(pg)
        no_throw(pg, host, 2500)
        got = _calls(pg, host, "ideas.throw", ms=DROP_MS + 3000)
        assert got == [{"idea": "night", "moment": "talk", "dir": "left"}], got
        pg.wait_for_function("() => !document.querySelector('.gui-toast')", timeout=WAIT_MS)
        assert pg.locator('.hand-stack[data-goal="night"]').count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_throw_to_the_other_left_side_after_a_goal_is_sent_at_once(gui):
    pg, host, log = open_hearing(gui, "wide", sides=[GO, LATER])
    try:
        lift(pg)
        pg.locator('.hr-side[data-dir="left"] .hr-side__btn').click()
        thrown(pg, host, dir="left")
        assert toast_text(pg).startswith("Thrown to Tech lead: After Round timer")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_refused_throw_keeps_the_hearing_and_the_card_comes_back(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        host.refuse = True
        lift(pg, width=width)
        pg.locator('.hr-side[data-dir="right"] .hr-side__btn').click()
        thrown(pg, host, dir="right")
        pg.wait_for_function("() => document.querySelector('.hr-card') && !document.querySelector('.hr-card').classList.contains('is-away')", timeout=WAIT_MS)
        assert pg.locator(".hr").count() == 1 and front(pg).count() == 1, "refused: nothing changed"
        assert "keeper is busy" in toast_text(pg)
    finally:
        pg.close()
    assert not [m for m in log if "pageerror" in m], "\n".join(log)


def test_on_a_phone_the_hearing_is_the_goals_top_card_in_the_middle_and_thrown_the_next_goal_is_picked(gui):
    pg, host, log = open_hearing(gui, "phone", second=True)
    try:
        hr = lift(pg, width="phone")
        assert pg.locator(".up-look[data-look='goal'] .hr").count() == 1 and pg.locator(".table-over").count() == 0, "in the middle, not over the pane"
        assert pg.locator(".up-look .hand-lifted > .hand-card__head").evaluate("(el) => getComputedStyle(el).display") == "none", "the hearing is the card: the lifted card's own head is not drawn twice"
        says = hr.locator(".hr-says").first
        assert says.evaluate("(el) => getComputedStyle(el).webkitLineClamp") == "3", "a side's line wraps to three lines"
        shot(pg, "phone-hearing")
        narrow.no_sideways(pg)
        pg.locator('.hr-side[data-dir="right"] .hr-side__btn').click()
        thrown(pg, host, dir="right")
        pg.wait_for_function("() => document.querySelector('.up-look')?.dataset.goal === 'lobby' && document.querySelector('.hr[data-goal=\"lobby\"]')", timeout=WAIT_MS)
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_on_a_phone_a_line_cut_at_three_lines_opens_whole_on_more(gui):
    long = side("left", "drop", ["tech"], ["Tech lead"], "It adds a third caller to server/ws and a fourth to the lobby, and every one of them has to be kept in step with the rooms, which nobody has the time to do this month.", "Drop it")
    pg, host, log = open_hearing(gui, "phone", sides=[GO, long, SMALLER])
    try:
        hr = lift(pg, width="phone")
        more = hr.locator('.hr-side[data-dir="left"] .hr-more')
        more.wait_for(timeout=WAIT_MS)
        cut = hr.locator('.hr-side[data-dir="left"] .hr-says').bounding_box()["height"]
        more.click()
        assert hr.locator('.hr-side[data-dir="left"] .hr-says').bounding_box()["height"] > cut and more.text_content().strip() == "Less"
        no_throw(pg, host, 100)
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_touch_swipe_on_the_phone_throws_and_does_not_scroll_the_page(gui):
    pg, host, log = open_hearing(gui, "phone")
    try:
        lift(pg, width="phone")
        cdp = pg.context.new_cdp_session(pg)
        x, y = centre(card(pg))
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
        for i in range(1, 9):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + i * 12, "y": y + 10}]})
            pg.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        thrown(pg, host, dir="right")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_under_reduced_motion_nothing_follows_the_pointer_and_nothing_flies(gui, width):
    pg, host, log = open_hearing(gui, width, reduced=True)
    try:
        lift(pg, width=width)
        drag(pg, 28, 0, release=False)
        assert pg.evaluate("() => document.querySelector('.hr-card').style.transform") == "", "the card follows nothing"
        assert pg.locator(".hr-stamp").text_content().strip() == "Do it", "the side it nears is still said"
        pg.mouse.up()
        pg.locator('.hr-side[data-dir="right"] .hr-side__btn').click()
        assert pg.evaluate("() => document.querySelector('.hr-card')?.style.transform ?? ''") == "", "no flight"
        assert pg.evaluate("() => document.getAnimations().filter((a) => a.effect?.target?.closest?.('.hr')).length") == 0
        thrown(pg, host, dir="right")
        assert pg.locator(".hr-card").evaluate("(el) => getComputedStyle(el).transitionDuration") in ("0s", "0s, 0s")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_no_sideways_scroll_while_the_card_is_dragged_or_thrown(gui, width):
    pg, host, log = open_hearing(gui, width)
    try:
        lift(pg, width=width)
        narrow.no_sideways(pg)
        drag(pg, -200, -60, release=False)
        narrow.no_sideways(pg)
        assert pg.evaluate("() => { const b = document.querySelector('.table-over, .up-look') || document.body; return b.scrollWidth - b.clientWidth }") <= 0
        pg.mouse.up()
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- a fork is a hearing too -------------------------------------------------------------------------------------------------------------

FORK_SIDES = [side("right", "side", ["design"], ["Design lead"], "The game is no fun with six.", "A room holds ten players", party="design"),
              side("left", "side", ["tech"], ["Tech lead"], "One server process cannot carry more.", "The server holds six players in a room", party="tech")]


class ForkHost(HearingHost):
    def __init__(self):
        super().__init__()
        self.nodes = [n for n in self.nodes if n["slug"] != "night"]
        self.nodes.append(node("rooms", "tech", "Rooms hold more players", "hand", state="sections", element="dust", route=["design", "tech"]))
        self.needs = [need("fork", "tech", "rooms", "Rooms hold more players", "How many players a room holds", id="f1", about="How many players a room holds", sides=[
            {"party": "design", "leader": "Design lead", "says": "A room holds ten players", "why": "The game is no fun with six."},
            {"party": "tech", "leader": "Tech lead", "says": "The server holds six players in a room", "why": "One server process cannot carry more."}],
            hearing={"moment": "fork", "id": "f1", "about": "How many players a room holds", "title": "Design lead and Tech lead disagree", "sides": FORK_SIDES, "left_out": [], "own": True})]

    def handle(self, name, a):
        if name == "ideas.throw" and a["moment"] == "fork":
            self.log.append((name, a))
            self.needs = []
            return self.bump({"ok": True})
        return super().handle(name, a)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_fork_lifted_is_a_hearing_with_its_sides_and_a_press_throws_it(gui, width):
    pg, host, log = open_hearing(gui, width, host=ForkHost())
    try:
        c = front(pg, "rooms")
        assert c.get_attribute("data-kind") == "fork" and c.get_attribute("aria-label").startswith("A fork: ")
        c.click(position={"x": 10, "y": 24})
        hr = pg.locator('.hr[data-goal="rooms"]')
        hr.wait_for(timeout=WAIT_MS)
        assert hr.get_attribute("data-moment") == "fork" and hr.locator(".hr-title").text_content().strip() == "Design lead and Tech lead disagree"
        assert hr.locator(".hr-side").count() == 2 and hr.locator('.hr-side[data-dir="right"] .hr-out__words').text_content().strip() == "A room holds ten players"
        pg.locator('.spec-page[data-kind="spec"]').wait_for(timeout=WAIT_MS)
        hr.locator('.hr-side[data-dir="left"] .hr-side__btn').click()
        assert _calls(pg, host, "ideas.throw") == [{"idea": "rooms", "moment": "fork", "dir": "left"}]
        pg.wait_for_function("() => !document.querySelector('.hr')", timeout=WAIT_MS)
        assert toast_text(pg).startswith("Thrown to Tech lead: The server holds six players in a room")
    finally:
        pg.close()
    assert not log, "\n".join(log)
