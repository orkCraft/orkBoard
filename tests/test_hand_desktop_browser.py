"""The hand of the new window (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §4–§6, part D; docs/specs/98-the-table-and-the-hand.md §4–§6), in a real browser against a stub host, the
window (the page, spec 98 E), at the two widths of `tests/narrow.py` (1280 × 800 and 390 × 844 with touch): the hand under the lanes (no deck; the + card under the first lane; a stack under the lane of who asks; two goals
under one lane fanned within its width, the back one's edge only and its rise; the discard lies on the table, spec 104 C), a card's face (the header with its element, the window with the action's sign and the asker's head, the label row
with the gem at its right, the foot), the half under the window's edge and its rise on hover, focus and tap, a press lifting it as before (its answers, its cost's words, *Put it back*), the + card and the field it grows into
(a press, a key typed, Enter, Shift+Enter, Esc, the address by the tab and by *@*, a pasted picture, the large card with no goal), the discard (*n ready for main*, *To main*, a result opened and seen), one card size, the gem
only where a card spends, no part with nothing to hold, nothing moving under reduced motion. The table (part C) draws what is opened over the pane; here the faces the hand registered are drawn by the test itself into a box
of its own. Screenshots to $HAND_SHOTS when it is set."""
from __future__ import annotations

import base64
import copy
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import StubHost, _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["HAND_SHOTS"]) if os.environ.get("HAND_SHOTS") else None
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def head(race, craft="engineering", tier="elder"):
    return {"craft": craft, "race": race, "tier": tier}


PARTIES = [("tech", "Tech", "shaman", "engineering"), ("design", "Design", "dryad", "design"), ("product", "Product", "unicorn", "product"), ("release", "Release", "lich", "engineering")]


NEXT_ELEMENT = {"tech": "ice", "design": "dust", "product": "void", "release": "lava"}          # what a new goal of each party would be given (`ideas.map`'s `next_element`, spec 110 §3.1)
FREE_ELEMENTS = {"tech": ["ice", "void", "lava"], "design": ["dust", "lava"], "product": ["void"], "release": []}       # the runes none of its open goals has (`free_elements`, spec 111 §3.2); Release has none free: the face shows all


def party(slug, name, race, craft):
    lead = {"slug": f"{slug}-lead", "name": f"{name} lead", "head": head(race, craft)}
    return {"slug": slug, "title": name, "short": name, "priority": "normal", "state": "ready", "done_when": [], "ideas": 0, "done": 0, "usd": None, "leader": lead,
            "team": [], "party": [], "today": {"merged": 0, "usd": 0.0}, "flags": 0, "waits_main": 0, "brief": "", "craft": craft, "race": race, "ideation": False, "next_element": NEXT_ELEMENT.get(slug, "meadow"), "free_elements": FREE_ELEMENTS.get(slug, [])}


def node(slug, goal, title, place, state="ready", element="meadow", **more):
    return {"slug": slug, "goal": goal, "title": title, "short": title, "state": state, "queue": "", "held_until": "", "element": element, "flag": None, "type": None, "route": [],
            "release": None, "start_at": "", "night_by": "", "place": place, "asks_you": False, "waits_as": "", "seen": "", "priority": "normal", "size": "M", "risk": "low",
            "tier": 1, "depends_on": [], "waits_on": [], "waits_for": [], "waits": None, "needs_you": "", "progress": {"done": 0, "total": 0}, "done": 0, "of": 0, "stage": "planning",
            "round": 1, "usd": None, "plan_estimate": None, "asked": [], "tasks": [], "checks": [], "estimate": None, "by_itself": False, "todo_lines": [], "folded": False,
            "updated": "2026-10-20T10:00:00", "pitch": None, "results": [], **more}


def task(tid, title, state, **more):
    return {"id": tid, "title": title, "short": title, "state": state, "after": [], "tier": "warrior", "head": head("peon", tier="warrior"), "by": {"slug": "grunt", "name": "Grunt"},
            "band": "build", "wave": 1, "row": 1, "tag": "Code", "error": "", "note": "", "round": 1, "cost": None, "started": "", "finished": "", "made": "", "pick": None, "shot": None, **more}


def need(kind, goal, idea, title, text="", **more):
    return {"kind": kind, "goal": goal, "idea": idea, "title": title, "text": text, "at": "2026-10-20T09:00:00", "priority": "normal", "blocks": False, **more}


DECK = [("kick", "tech", "Kick a player from the room", "dust"), ("skip", "design", "Host can skip a round", "meadow"), ("sound", "tech", "Short sound when a round starts", "void"),
        ("dark", "design", "Dark mode for the lobby", "ice"), ("rename", "tech", "Rename a room after it is made", "lava"), ("code", "tech", "Show the room code big on the host's screen", "dust"),
        ("avatar", "design", "Let players pick an avatar", "meadow"), ("emoji", "design", "Emoji reactions", "ice"), ("mute", "tech", "Mute a noisy player", "lava")]


class HandHost(StubHost):
    """A project of four parties with goals in every place of the hand: nine in line (they lie on the table now, the hand has no deck), a failure and a plan ready of Tech's (two goals under Tech's lane) and two
    questions of Design's (two goals under Design's lane), a question of Product's, two goals done, and two goals ready for main. `both`: a question of Design's about Tech's failing goal (a goal in two lanes)."""

    def __init__(self, empty=False, bare=False, extra=False, both=False):
        super().__init__()
        self.rate = {"tool": "claude", "window": "week", "usd_per_pct": 0.5}
        self.parties = [party(*p) for p in PARTIES]
        self.added, self.seen_log = [], []
        if empty:
            self.nodes, self.needs, self.gate_doc = [], [], {"into": "dev", "main": "main", "same": True, "commits": 0, "files": 0, "ideas": []}
            return
        deck = [node(s, g, t, "deck", state="raw", element=e, waits_as="held") for s, g, t, e in DECK]
        deck[0].update(waits_as="reset", held_until="2026-10-20T21:40:00")
        deck[2].update(waits_as="line")
        timer = node("timer", "tech", "The timer doesn't reset after a reconnect", "hand", state="failed", element="dust", tasks=[task("t1", "Reset the clock", "failed", error="The reset test failed", cost=2.0)])
        export = node("export", "tech", "Export the round scores", "hand", state="plan", element="ice", plan_estimate={"usd_low": 1.0, "usd_high": 2.0},
                      tasks=[task("e1", "Write the export", "waiting"), task("e2", "Check the file", "waiting")])
        todo = {"id": "t9", "title": "EXPORT_KEY", "kind": "secret", "why": "The export needs it", "choices": [], "steps": [], "accept": [], "done": False}
        phones = node("phones", "design", "Round timer shows on every phone", "hand", state="asks", element="meadow",
                      asked=[{"ask": "Where does the timer run?", "choices": ["Server counts, phones show it", "Each phone counts down alone"], "pick": 0, "why": "One clock: every phone agrees.", "by": None, "look": False}])
        words = node("words", "design", "Words on the sign-in screen", "hand", state="asks", element="ice",
                     asked=[{"ask": "Which word for sign in?", "choices": ["Sign in", "Log in"], "pick": None, "why": "", "by": None, "look": False}])
        theme = node("theme", "product", "Pick the theme of the first week", "hand", state="asks", element="lava",
                     asked=[{"ask": "Which theme?", "choices": ["Space", "Farm"], "pick": None, "why": "", "by": None, "look": False}])
        music = node("music", "tech", "Lobby music loop", "discard", state="done", element="void", updated="2026-10-20T12:00:00", tasks=[task("m1", "Make the loop", "merged", made="Add the lobby loop", cost=0.5)])
        codes = node("codes", "design", "Room codes are four letters, no look-alikes", "discard", state="done", element="dust", updated="2026-10-19T12:00:00")
        old = node("old", "tech", "An old goal", "history", state="done", seen="2026-10-18T10:00:00")
        self.nodes = [*deck, timer, export, phones, words, theme, music, codes, old]
        self.needs = [need("failed", "tech", "timer", timer["title"], "It failed", at="2026-10-20T08:00:00"), need("plan", "tech", "export", export["title"], "Plan ready · 2 tasks"),
                      need("todo", "tech", "export", export["title"], "EXPORT_KEY", todo=todo, at="2026-10-20T09:10:00"),
                      need("asks", "design", "phones", phones["title"], "Where does the timer run?", at="2026-10-20T09:30:00", asked=phones["asked"]),
                      need("asks", "design", "words", words["title"], "Which word for sign in?", at="2026-10-20T09:40:00", asked=words["asked"]),
                      need("asks", "product", "theme", theme["title"], "Which theme?", at="2026-10-20T09:50:00", asked=theme["asked"])]
        self.gate_doc = {"into": "dev", "main": "main", "same": False, "commits": 5, "files": 9,
                         "ideas": [{"slug": "music", "title": music["title"], "goal": "tech", "tasks": 1}, {"slug": "codes", "title": codes["title"], "goal": "design", "tasks": 2}]}
        if extra:                                                             # a pick, a tool's sign-in (a stack of no goal) and a card of a kind the hand does not know (spec 100's route)
            look = node("look", "design", "The look of the first screen", "table", state="working", element="ice", asks_you=True, tasks=[task("p1", "Pick the words", "picking")])
            routed = node("fresh", "tech", "A goal just sent", "table", state="routed", element="meadow", asks_you=True)
            self.nodes += [look, routed]
            variants = [{"key": "A", "name": "Calm", "text": "Welcome back.", "why": ""}, {"key": "B", "name": "Loud", "text": "WELCOME BACK!", "why": ""}]
            self.needs += [need("pick", "design", "", look["title"], "Which words?", slug="look", task="p1", round=1, media="text", variants=variants, n=2, ask="Which words?",
                                short="Pick the words", by={"slug": "elf", "name": "Elf", "head": head("elf", "design")}),
                           need("sign_in", "", "", "Claude", "Claude is signed out.", harness="claude", tool="Claude", waiting=2),
                           need("route", "tech", "fresh", routed["title"], "Goes to Tech, by code")]
        if both:                                                              # the failing goal is asked about by Design too: its stacks lie under two lanes
            q = [{"ask": "Does the clock show on phones?", "choices": ["Yes", "No"], "pick": None, "why": "", "by": None, "look": False}]
            self.needs.append(need("asks", "design", "timer", "The timer doesn't reset after a reconnect", "Does the clock show on phones?", at="2026-10-20T09:55:00", asked=q))
        if bare:                                                              # nothing done, nothing ready for main, nothing in line
            self.nodes = [n for n in self.nodes if n["place"] not in ("discard", "deck")]
            self.gate_doc = {"into": "dev", "main": "main", "same": False, "commits": 0, "files": 0, "ideas": []}   # a gate with nothing to merge (the ring asleep); `same` would be no gate at all (spec 113)

    def map_doc(self):
        return {"goals": self.parties, "nodes": copy.deepcopy(self.nodes), "edges": [], "rev": self.rev}

    def handle(self, name, a):
        if name == "ideas.map":
            self.log.append((name, a))
            return self.map_doc()
        if name == "ideas.board":
            self.log.append((name, a))
            tracks = [{"slug": p["slug"], "title": p["title"], "priority": "normal", "order": i, "recipe": "", "count": 0} for i, p in enumerate(self.parties)]
            return {"tracks": tracks, "ideas": [], "needs_you": copy.deepcopy(self.needs), "target": "balance", "autostart": True, "night": "01:00-07:00",
                    "review": False, "review_notice": False, "rev": self.rev}
        if name == "ideas.add":
            self.log.append((name, a))
            self.added.append(a)
            return self.bump({"slug": "new-goal", "queue": "now", "element": a.get("element") or NEXT_ELEMENT.get(a.get("party"), "meadow"), "route": [a.get("party") or "tech"]})
        if name == "ideas.move":
            self.log.append((name, a))
            mine = next(n for n in self.nodes if n["slug"] == a["slug"])
            rest = [n for n in self.nodes if n is not mine]
            at = next((i for i, n in enumerate(rest) if n["slug"] == a.get("before")), None)
            if at is None:                                                         # last of its party
                at = max((i for i, n in enumerate(rest) if n["goal"] == mine["goal"]), default=len(rest) - 1) + 1
            self.nodes = [*rest[:at], mine, *rest[at:]]
            return self.bump({"ok": True})
        if name == "ideas.seen":
            self.log.append((name, a))
            self.seen_log.append(a["idea"])
            next(n for n in self.nodes if n["slug"] == a["idea"]).update(place="history", seen="2026-10-20T13:00:00")
            return self.bump({"ok": True, "seen": "2026-10-20T13:00:00"})
        if name == "ideas.answer":
            self.log.append((name, a))
            self.needs = [n for n in self.needs if (n["idea"] or n["goal"]) != a["slug"]]
            return self.bump({"ok": True})
        if name == "ideas.task":
            self.log.append((name, a))
            mine = next(t for n in self.nodes if n["slug"] == a["slug"] for t in n["tasks"] if t["id"] == a["task"])
            return mine | {"idea": a["slug"], "idea_title": a["slug"], "brief": "Brief", "branch": f"idea/{a['slug']}/{a['task']}", "log": "== round 1\nthe reset test failed\n"}
        if name == "ideas.spend":
            self.log.append((name, a))
            return {"usd": 1.2, "stages": {"goal": {"usd": 0.2}, "work": {"usd": 1.0}}}
        return super().handle(name, a)


class RoadHost(HandHost):
    """HandHost with the road's two parties as the host's map names them (`party_craft`, spec 111 §4.1): Release (the lich, whose members are two undead) and Live (the imp, a goblin beside it), and the checks on the way into main
    scripted (§4.2): `checks[slug]` is what the snapshot's `main_checks` says, `ideas.to_main_checks` answers it, `step` moves it as the host's `main.check` does. A plan with a `conflict` seals through the check *The merge*."""

    def __init__(self, **more):
        super().__init__(**more)
        self.checks: dict[str, list[dict]] = {}
        self.script: dict[str, tuple[tuple[str, ...], dict]] = {}               # slug → the states the checks come to when they are asked (or asked again)
        self.asked: list[dict] = []
        live = party("live", "Live", "imp", "engineering")
        self.parties.append(live)
        for p in self.parties:
            if p["slug"] in ("release", "live"):
                p["party_craft"] = "release" if p["slug"] == "release" else "run"
        release = next(p for p in self.parties if p["slug"] == "release")
        release["party"] = [{"slug": "release-lead", "name": "Release lead", "head": release["leader"]["head"], "band": "lead", "state": "free", "why": ""},
                            {"slug": "keeper", "name": "Keeper", "head": head("lich", "engineering", "warrior"), "band": "build", "state": "free", "why": ""},
                            {"slug": "warden", "name": "Warden", "head": head("lich", "engineering", "laborer"), "band": "check", "state": "free", "why": ""}]
        live["party"] = [{"slug": "live-lead", "name": "Live lead", "head": live["leader"]["head"], "band": "lead", "state": "free", "why": ""},
                         {"slug": "digger", "name": "Digger", "head": head("goblin", "engineering", "warrior"), "band": "build", "state": "free", "why": ""}]

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["main_checks"] = copy.deepcopy(self.checks)
        return doc

    def step(self, slug, *states, words=None):
        """The host's `main.check`: the goal's checks now stand as `states` (one of waiting, running, passed, failed each) and the snapshot carries them."""
        names = ["The merge", "Tests", "Looks", "Regression", "Extra"]
        self.checks[slug] = [{"name": names[i], "state": st, "words": (words or {}).get(i, "")} for i, st in enumerate(states)]
        return self.bump(None)

    def handle(self, name, a):
        if name == "ideas.to_main_checks":
            self.log.append((name, a))
            self.asked.append(a)
            want = self.script.get(a["idea"])
            if want and (a["idea"] not in self.checks or a.get("again")):
                self.step(a["idea"], *want[0], words=want[1])
            got = copy.deepcopy(self.checks.get(a["idea"], []))
            return {"idea": a["idea"], "checks": got, "running": any(c["state"] in ("waiting", "running") for c in got)}
        return super().handle(name, a)


def open_hand(gui, host=None, width="wide", errors=True):
    """The page against the stub, at one of the two widths; waits for the hand."""
    server, browser = gui
    host = host or HandHost()
    pg = narrow.page(browser, width)
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and log.append(f"console: {m.text} {m.location.get('url', '')}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand", state="attached", timeout=WAIT_MS)
    return pg, host, log


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


# -- the page's own state, read and set through its modules --------------------------------------------------------------------------------

def sig(pg, module, name):
    return pg.evaluate("([m, n]) => import(m).then((x) => x[n].value)", [f"/static/js/{module}", name])


def call(pg, module, name, *args):
    return pg.evaluate("([m, n, a]) => import(m).then((x) => x[n](...a))", [f"/static/js/{module}", name, list(args)])


PANE_JS = """async () => {
  const [{ over }, { faceOf }, { render, h }, { effect }] = await Promise.all([import('/static/js/frame/state.js'), import('/static/js/frame/kinds.js'), import('preact'), import('@preact/signals')]);
  let box = document.getElementById('test-pane');
  if (!box) { box = document.createElement('div'); box.id = 'test-pane'; box.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:240px;overflow:auto;background:var(--ork-table);padding:16px;z-index:1'; document.body.appendChild(box); }
  effect(() => { const o = over.value; if (!o) { render(null, box); return; } const Face = faceOf(o.kind); render(Face ? h(Face, { props: o.props, close: () => {} }) : null, box); });
}"""


def pane(pg):
    """The faces the hand registered, drawn into a box of the test's own (the table draws them in the pane)."""
    pg.evaluate(PANE_JS)
    return pg.locator("#test-pane")


def press_at(pg, goal, y=24):
    """A press on the left edge of a goal's front card (a card that lies behind another shows its left edge, and rises under the pointer)."""
    pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]').click(position={"x": 10, "y": y})


def lane(pg, i):
    return pg.locator(f'.hand-lane[data-lane="{i}"]')






def _plus(pg):
    """The new goal's card: the deck of blank cards at the wide width, the + card at the narrow one."""
    return pg.locator(".hand :is(.hand-plus, [data-blank-deck])")


def _field(pg):
    f = pg.locator(".hand-field")
    f.wait_for(timeout=WAIT_MS)
    return f, f.get_by_role("textbox", name="Write a goal")


# -- the deck -------------------------------------------------------------------------------------------------------------------------------



# -- the + card and its field -------------------------------------------------------------------------------------------------------------





@pytest.mark.parametrize("width", ["narrow"])      # wide: the card in play and the field as large as the hand (tests/test_new_goal_card_browser.py)
def test_the_plus_card_grows_into_the_field_enter_sends_shift_enter_a_new_line_esc_keeps_the_words(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})                                                                                                  # its left edge: at the phone the potions take room and the cards tighten (hand.css)
        field, area = _field(pg)
        assert area.evaluate("e => e === document.activeElement") and area.get_attribute("placeholder") == "Write a goal…"
        area.type("Show the round number")
        pg.keyboard.press("Shift+Enter")
        pg.keyboard.type("above the timer")
        assert area.input_value() == "Show the round number\nabove the timer" and not host.added
        size = pg.viewport_size
        shot(pg, f"{width}-field")
        pg.keyboard.press("Escape")                                              # Esc closes it, its text kept
        assert pg.locator(".hand-field").count() == 0
        _plus(pg).click(position={"x": 8, "y": 60})
        _, area = _field(pg)
        assert area.input_value() == "Show the round number\nabove the timer"
        pg.mouse.click(size["width"] / 2, 60)                                       # a press away closes it, its text kept
        assert pg.locator(".hand-field").count() == 0
        _plus(pg).click(position={"x": 8, "y": 60})
        _, area = _field(pg)
        assert area.input_value() == "Show the round number\nabove the timer"
        area.press("Enter")                                                        # Enter sends: general on the Orkmaster's tab, no party
        assert _sent(pg, host, ("ideas.add", {"match": True, "now": True, "text": "Show the round number\nabove the timer"}))
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)             # sent: the field closes with its text gone
        _plus(pg).click(position={"x": 8, "y": 60})
        assert _field(pg)[1].input_value() == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)




def _radios(pg):
    """The five runes of the field: they stand in a row once the card's rune is pressed (spec 120 §6.1; wide: dealt to the hand in the field's place, spec 168 D2), so the row is opened when it is not."""
    row = ".hand-field .hand-field__runes, .hand-dealt[data-open=rune]"
    if pg.locator(".hand-field").count() and not pg.locator(row).count():
        pg.locator(".hand-field .hand-field__rune").first.click()
        pg.locator(row).first.wait_for(timeout=WAIT_MS)
    return pg.locator(".hand-field .hand-field__runes [role=radio], .hand-dealt[data-open=rune] [data-rune]")


def _checked(pg):
    return [r.get_attribute("data-rune") for r in _radios(pg).all() if r.get_attribute("aria-checked") == "true"]








def test_a_key_typed_with_nothing_focused_opens_the_field_and_a_key_in_a_button_does_not(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.locator(".hand-stack .hand-card").first.focus()
        pg.keyboard.press("x")
        assert pg.locator(".hand-field").count() == 0                              # the focus has the key
        pg.evaluate("() => document.activeElement.blur()")
        pg.keyboard.press("w")
        field, area = _field(pg)
        assert area.input_value() == "w" and area.evaluate("e => e === document.activeElement")
        pg.keyboard.type("ords")
        assert area.input_value() == "words"
    finally:
        pg.close()
    assert not log, "\n".join(log)




def test_a_picture_pasted_goes_with_the_goal(gui):
    pg, host, log = open_hand(gui)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).click()
        field, area = _field(pg)
        area.fill("Make it look like this")
        pg.evaluate("""async (b64) => {
          const f = new File([Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))], 'p.png', { type: 'image/png' }), dt = new DataTransfer();
          dt.items.add(f);
          document.querySelector('.hand-field textarea').dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
        }""", base64.b64encode(PNG).decode())
        field.locator(".hand-pic img").wait_for(timeout=WAIT_MS)
        shot(pg, "wide-field-picture")
        area.press("Enter")
        sent = _calls(pg, host, "ideas.add")[-1]
        assert sent["text"] == "Make it look like this" and len(sent["photos"]) == 1 and sent["photos"][0].startswith("data:image/jpeg")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the stacks and the lifted card ---------------------------------------------------------------------------------------------------------

def _stack(pg, goal):
    return pg.locator(f'.hand-stack[data-goal="{goal}"], .hand-stack[data-stack^="{goal}@"]')


def _press(pg, goal):
    """A press on a goal's stack: the left edge of its front card (a stack that lies behind another shows only that, and rises under the pointer)."""
    _stack(pg, goal).locator('.hand-card[data-top="1"]').first.click(position={"x": 10, "y": 24})










@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_stack_pressed_picks_its_goal_and_lifts_its_top_card_with_its_answers_and_its_cost(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        _press(pg, "export")                                                                                                                              # a stack pressed picks its goal and lifts its top card
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        assert sig(pg, "frame/state.js", "picked") == "export" and sig(pg, "frame/state.js", "lifted") == "hand:plan/export/"
        assert lifted.get_by_role("button", name="Start the work").count() == 1 and lifted.get_by_role("button", name="Put it back").count() == 1
        assert lifted.locator(".hand-spend__words").inner_text() == "about 2–4% of Claude's week" and lifted.locator(".hand-spend .ork-gem.share").count() == 1 and lifted.locator(".corner--foot .corner__much .ork-gem.share").count() == 1       # its cost's words, and its gem at the foot's right (spec 147 D.1)
        assert "is-slot" in pg.locator('.hand-places .hand-card[data-kind="plan"]').get_attribute("class")                                                           # a slot where it lay
        shot(pg, f"{width}-lifted-plan")
        lifted.get_by_role("button", name="Put it back").click()                                                                                          # put back
        assert pg.locator(".hand-lifted").count() == 0 and sig(pg, "frame/state.js", "lifted") == ""
        _press(pg, "export")
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        pg.keyboard.press("Escape")                                                                                                                       # Esc lowers it
        assert pg.locator(".hand-lifted").count() == 0
        _press(pg, "export")
        pg.locator(".hand-lifted").get_by_role("button", name="Start the work").click()                                                                   # answered from the card
        assert _sent(pg, host, ("ideas.start", {"slug": "export", "via": "hand"}))
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.hand-lifted')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)






# -- the discard ----------------------------------------------------------------------------------------------------------------------------



def test_a_goal_pressed_in_the_discard_opens_its_result_is_seen_and_leaves_the_discard(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        pg.locator(".hand-done").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        pg.locator(".hand-done").click()
        box = pg.locator("#table-pane")
        box.get_by_role("region", name="Done, not yet seen").locator('.hand-drow[data-slug="codes"]').click()
        over = sig(pg, "frame/state.js", "over")
        assert over["kind"] == "result" and over["props"] == {"idea": "codes"}
        assert _sent(pg, host, ("ideas.seen", {"idea": "codes"})) and host.seen_log == ["codes"]
        box.locator(".hand-result").wait_for(timeout=WAIT_MS)
        assert "room codes are four letters" in box.inner_text().lower()
        pg.keyboard.press("Escape")                                                                                                 # at the narrow width the pile is hidden while something is over the pane
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value === null)", timeout=WAIT_MS)
        pg.locator(".hand-done").click()
        assert box.get_by_role("region", name="Done, not yet seen").locator(".hand-drow").count() == 1                              # it left the discard
        box.get_by_role("region", name="Done, not yet seen").locator('.hand-drow[data-slug="music"]').click()
        box.locator('.hand-result[data-idea="music"]').wait_for(timeout=WAIT_MS)
        assert "add the lobby loop" in box.inner_text().lower()
        pg.wait_for_timeout(500)
        assert "Lobby music loop" not in pg.locator(".hand-done").inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- motion ---------------------------------------------------------------------------------------------------------------------------------


# -- the other cards of the hand --------------------------------------------------------------------------------------------------------------





# -- the words of the goal's way and the one place of the parties (spec 100 E) -------------------------------------------------------------------------------------







# -- the goal under the pointer (spec 165 I, decisions §280.1) -------------------------------------------------------------------------------









