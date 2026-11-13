"""The hearing's face (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.7, §7 F; decisions §198.6; the mockup docs/mockups/hearing/ 3), in a real browser against a stub host answering the Needs you rows `hearing` and `fork` (with its
`hearing`), `ideas.page` and the command `ideas.throw {idea, moment, dir | text}`: the card in the hand (the question sign, the first leader's head, the heading at its foot, under the first lane); lifted over the pane at the wide and the narrow
widths and in the middle of a phone-sized page, the goal's card (its rune and name, *Done when*, else its gist) and the sides around it (→ right, ← left, ↑ up), each its leaders' heads (the first at 28 px, the others at 16), its line and its outcome; a swipe
past a third of the way throwing the side, one short of it coming back, a fling, down being no side; a press, the keys and the person's own words; the toast *Thrown to <Leader>: <outcome>*, every Talk throw sent at once and its toast saying **Undo** for six seconds (`ideas.unthrow` takes it back, a refusal is said in the host's words; a fork's has no Undo); a refusal keeping the hearing; no sideways scroll; nothing moving under reduced motion. Screenshots to $HEARING_SHOTS when it is set."""
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
        self.went_on = False                                              # the host says an Undo went on already
        self.sent = []                                                    # the needs rows a throw took out, to put back when it is taken back

    def handle(self, name, a):
        if name == "ideas.page":
            self.log.append((name, a))
            return {"slug": a["slug"], "title": a["slug"], "sections": self.page, "state": "talk", "track": "tech"}
        if name == "ideas.throw":
            self.log.append((name, a))
            if self.refuse:
                return {"error": "The keeper is busy with this goal: a moment"}
            self.sent += [n for n in self.needs if n["kind"] == "hearing" and n["idea"] == a["idea"]]
            self.needs = [n for n in self.needs if not (n["kind"] == "hearing" and n["idea"] == a["idea"])]
            return self.bump({"ok": True, "moment": a["moment"], "kind": "own" if a.get("text") else "go", "dir": a.get("dir", ""), "outcome": "Do it", "to": []})
        if name == "ideas.unthrow":
            self.log.append((name, a))
            if self.went_on:
                return {"error": "It went on already"}
            self.needs += [n for n in self.sent if n["idea"] == a["idea"]]
            self.sent = [n for n in self.sent if n["idea"] != a["idea"]]
            return self.bump({"ok": True, "kind": "go", "moment": a["moment"]})
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
    """The hearing, opened: over the pane (a press on the card), or on the phone in the middle once its card of the hand's row is pressed (goal 169 F: with nothing pressed the middle is the feed). Returns the hearing."""
    if width != "phone":
        front(pg, goal).click(position={"x": 10, "y": 24})
    else:
        pg.locator(f'.hand-up .up-card[data-key="goal:{goal}"]').click()
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




def test_a_drop_is_sent_at_once_and_undo_takes_it_back_with_the_hosts_command(gui):
    pg, host, log = open_hearing(gui, "wide")
    try:
        lift(pg)
        pg.locator('.hr-side[data-dir="left"] .hr-side__btn').click()
        thrown(pg, host, dir="left")
        text = toast_text(pg)
        assert text == "Thrown to Tech lead: Drop it", "no six seconds to wait: it is done, and Undo is offered"
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-goal=\"night\"]')", timeout=WAIT_MS)       # the card is out of the hand
        pg.wait_for_function("() => !document.querySelector('.hr[data-kind=hearing]')", timeout=WAIT_MS)
        pg.locator(".gui-toast").get_by_role("button", name="Undo").click()
        assert _calls(pg, host, "ideas.unthrow") == [{"idea": "night", "moment": "talk"}]
        pg.wait_for_function("() => document.querySelector('.hr[data-goal=\"night\"]')", timeout=WAIT_MS)                # the hearing is back over the pane
        assert front(pg).count() == 1, "and its card in the hand"
        pg.wait_for_timeout(DROP_MS + 600)
        assert len([a for n, a in host.log if n == "ideas.throw"]) == 1, "nothing is sent when the toast goes"
        assert pg.locator(".hr[data-kind=hearing]").count() == 1
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
        assert pg.locator(".hr[data-kind=hearing]").count() == 1 and front(pg).count() == 1, "refused: nothing changed"
        assert "keeper is busy" in toast_text(pg)
    finally:
        pg.close()
    assert not [m for m in log if "pageerror" in m], "\n".join(log)












# -- a fork is a hearing too -------------------------------------------------------------------------------------------------------------





