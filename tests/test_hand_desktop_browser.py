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
import re
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
            return {"tracks": tracks, "ideas": [], "needs_you": copy.deepcopy(self.needs), "target": "balance", "autostart": True, "night": "01:00-07:00", "night_low": None,
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


def test_a_row_lies_under_the_lane_of_who_asks(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        lanes = pg.evaluate("""async () => {
          const { laneOf } = await import('/static/js/hand/data.js'), parties = ['tech', 'design', 'product', 'release'].map((slug) => ({ slug }));
          return [laneOf({ kind: 'failed', g: { slug: 'design' } }, parties), laneOf({ kind: 'asks', row: { goal: 'product' } }, parties), laneOf({ kind: 'goal', row: { goal: 'tech', idea: '' } }, parties),
            laneOf({ kind: 'route', row: { goal: 'tech' } }, parties), laneOf({ kind: 'collide', g: { slug: 'tech' } }, parties), laneOf({ kind: 'sign_in', g: null, row: {} }, parties),
            laneOf({ kind: 'asks', row: { goal: 'gone' } }, parties), laneOf({ kind: 'failed', goal: 'release' }, parties)];
        }""")
        assert lanes == [2, 3, 1, 0, 0, 0, 0, 4]        # a failure its task's party, a party's question and the project's questions their leader's party; the route, a fork, a sign-in and a gone party's the first lane
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tap_on_the_discard_opens_it_over_the_pane_at_the_narrow_width(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        done = pg.locator(".table-end .hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        b = done.bounding_box()
        pg.mouse.click(b["x"] + b["width"] / 2, b["y"] + 30)
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => m.over.value?.kind === 'discard')", timeout=WAIT_MS)
        assert pg.evaluate("() => document.activeElement?.classList.contains('hand-done')")
        shot(pg, "narrow-tap-discard")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def _plus(pg):
    """The new goal's card: the deck of blank cards at the wide width, the + card at the narrow one."""
    return pg.locator(".hand :is(.hand-plus, [data-blank-deck])")


def _field(pg):
    f = pg.locator(".hand-field")
    f.wait_for(timeout=WAIT_MS)
    return f, f.get_by_role("textbox", name="Write a goal")


# -- the deck -------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", ["narrow"])                                                           # at the wide width the discard is Release's lane (test_discard_table_browser.py)
def test_no_part_with_nothing_to_hold(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-plus").count() == 1 and lane(pg, 0).locator(".hand-slot").count() == 1 and lane(pg, 0).locator(".hand-slot").get_attribute("data-at") == "0"   # the + card alone at the first lane's left end
        assert pg.locator(".hand-done").count() == 0                                                                    # nothing done, nothing ready for main: no discard
        shot(pg, f"{width}-bare")
    finally:
        pg.close()
    assert not log, "\n".join(log)
    host = HandHost()                                                            # nothing done, but two goals ready for main: that line alone on a back
    host.nodes = [n for n in host.nodes if n["place"] != "discard"]
    pg, host, log = open_hand(gui, host=host, width=width)
    try:
        back = pg.locator(".hand-done.ork-card-back")
        back.wait_for(timeout=WAIT_MS)
        assert back.locator(".ork-race__head").count() == 1 and back.get_attribute("aria-label") == "Done. 2 goals ready for main"
        if width == "wide":
            assert "2 goals ready for main" in back.inner_text()
        shot(pg, f"{width}-ready-only")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the + card and its field -------------------------------------------------------------------------------------------------------------

def _seal(pg, large=False):
    """The element lying in the + card's seal: its class name ("" when the place is empty)."""
    inner = pg.locator(f".hand .hand-plus{'.is-large' if large else ''} > .ork-sigil > .ork-sigil__seal > .ork-elem")
    return inner.get_attribute("class").replace("ork-elem", "").strip() if inner.count() else ""


def test_the_large_plus_card_keeps_the_full_seal_and_the_first_partys_rune(gui):
    pg, host, log = open_hand(gui, host=HandHost(empty=True))
    try:
        big = pg.locator(".hand-plus.is-large")
        big.wait_for(timeout=WAIT_MS)
        sigil = big.locator("> .ork-sigil")
        assert sigil.count() == 1 and "small" not in sigil.get_attribute("class").split()
        assert round(sigil.bounding_box()["width"]) >= 136 and big.bounding_box()["width"] > 136
        assert _seal(pg, large=True) == "ice", "no goal, no party addressed: the first party's next element (§253.10)"
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
        box, size = field.bounding_box(), pg.viewport_size
        assert box["x"] >= 0 and box["x"] + box["width"] <= size["width"] and box["y"] >= 0, "the field lies inside the window"
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


def _frees(pg):
    """The free runes lying in the + card's seal, in the places of the band: `[place, element]`."""
    return pg.locator(".hand .hand-plus .ork-sigil > .ork-sigil__free:not(.hand-deco)").evaluate_all("els => els.map((e) => [e.classList[1], e.firstElementChild.classList[1]])")     # the three of orkUI's own runes (`.hand-deco`) are the ring's whole, not free runes


def _radios(pg):
    """The five runes of the field: they stand in a row once the card's rune is pressed (spec 120 §6.1; wide: dealt to the hand in the field's place, spec 168 D2), so the row is opened when it is not."""
    row = ".hand-field .hand-field__runes, .hand-dealt[data-open=rune]"
    if pg.locator(".hand-field").count() and not pg.locator(row).count():
        pg.locator(".hand-field .hand-field__rune").first.click()
        pg.locator(row).first.wait_for(timeout=WAIT_MS)
    return pg.locator(".hand-field .hand-field__runes [role=radio], .hand-dealt[data-open=rune] [data-rune]")


def _checked(pg):
    return [r.get_attribute("data-rune") for r in _radios(pg).all() if r.get_attribute("aria-checked") == "true"]


def test_the_narrow_seal_is_small_and_holds_no_free_rune(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")
        pg.wait_for_function("() => document.querySelector('.hand .hand-plus .ork-sigil__seal .ork-elem.ice')", timeout=WAIT_MS)
        assert "small" in pg.locator(".hand .hand-plus .ork-sigil").get_attribute("class").split() and _frees(pg) == []        # `.small` has none (orkUI 0.21.0)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", ["narrow"])      # wide: the runes are dealt to the hand (tests/test_new_goal_card_browser.py)
def test_the_field_holds_a_row_of_five_runes_the_default_checked_the_used_faint_arrows_move_it_and_the_seal_follows(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")                                                                      # free: ice (the default), void, lava; meadow and dust are used
        pg.wait_for_function("() => document.querySelector('.hand .hand-plus .ork-sigil__seal .ork-elem.ice')", timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})
        field, area = _field(pg)
        assert field.locator(".hand-field__runes").count() == 0, "the five stand in a row only once the card's rune is pressed"
        assert field.locator(".hand-field__rune").get_attribute("aria-label") == "Its rune: Rune 2, change it"
        radios = _radios(pg)
        group = field.locator(".hand-field__runes")
        assert group.get_attribute("role") == "radiogroup" and group.get_attribute("aria-label") == "Its rune"
        assert [r.get_attribute("aria-label") for r in radios.all()] == ["Rune 1", "Rune 2", "Rune 3", "Rune 4", "Rune 5"]      # the elements are never named (§63.4)
        assert [r.get_attribute("data-rune") for r in radios.all()] == ["meadow", "ice", "dust", "void", "lava"]
        assert all(r.get_attribute("role") == "radio" and r.locator(".ork-elem.big").count() == 1 for r in radios.all()) and _checked(pg) == ["ice"], "the default checked"
        box = radios.first.bounding_box()
        assert abs(box["width"] - 40) <= 1 and abs(box["height"] - 40) <= 1, box                                          # 40 x 40 (44 under a touch pointer)
        assert radios.first.locator(".ork-elem").evaluate("e => e.offsetWidth") == 28                                      # the rune at 28 px
        faint = lambda e: float(pg.locator(f'.hand-rune[data-rune="{e}"] .ork-elem').evaluate("e => getComputedStyle(e).opacity"))  # noqa: E731
        assert faint("meadow") == faint("dust") < faint("void") < faint("ice") == 1.0, "the used ones faint, the free ones bright, the chosen one full"
        assert [r.get_attribute("tabindex") for r in radios.all()] == ["-1", "0", "-1", "-1", "-1"]                         # one stop in the row
        assert group.evaluate("e => e.scrollWidth <= e.clientWidth + 1")
        shot(pg, f"{width}-field-runes")
        radios.nth(1).focus()
        pg.keyboard.press("ArrowRight")                                                                                    # the arrows move the choice and the focus
        assert _checked(pg) == ["dust"] and radios.nth(2).evaluate("e => e === document.activeElement")
        assert _seal(pg) == "dust", "the seal follows the choice"
        if width == "wide":
            assert [f[1] for f in _frees(pg)] == ["ice", "void", "lava"], "and the default is among the free ones again"
        pg.keyboard.press("ArrowLeft"); pg.keyboard.press("ArrowLeft")
        assert _checked(pg) == ["meadow"]
        pg.keyboard.press("ArrowLeft")
        assert _checked(pg) == ["lava"], "it goes round"
        pg.keyboard.press("ArrowUp")
        assert _checked(pg) == ["void"]
        pg.keyboard.press("Tab")                                                                                           # Tab leaves the row
        assert pg.evaluate("() => !document.activeElement.closest('.hand-field__runes')") and _checked(pg) == ["void"]
        radios.nth(0).click()                                                                                              # a press chooses too
        assert _checked(pg) == ["meadow"] and _seal(pg) == "meadow"
        area.fill("The rune is meadow")
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"match": True, "now": True, "text": "The rune is meadow", "party": "tech", "element": "meadow"}))         # sent: the choice differs from the default
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)
        _plus(pg).click(position={"x": 8, "y": 60})
        _field(pg)
        assert _checked(pg) == ["ice"], "the next goal starts from the default again"
        _field(pg)[1].fill("The default")
        _field(pg)[1].press("Enter")
        assert "element" not in _calls(pg, host, "ideas.add", 2)[-1], "the default is not sent"
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_party_named_in_the_text_changes_the_default_and_the_used_runes_and_all_five_used_are_none_faint(gui):
    pg, host, log = open_hand(gui)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).click()
        field, area = _field(pg)
        area.fill("@Design ")
        _radios(pg)
        pg.wait_for_function("() => document.querySelector('.hand-dealt [data-rune=\"dust\"][aria-checked=\"true\"]')", timeout=WAIT_MS)
        assert [r.get_attribute("data-rune") for r in pg.locator(".hand-dealt .hand-deal.is-faint").all()] == ["meadow", "ice", "void"]       # Design's free runes are dust and lava
        pg.keyboard.press("Escape")                                                                                         # the row put back: the words with it
        area.wait_for(timeout=WAIT_MS)
        area.fill("@Release ")
        _radios(pg)
        pg.wait_for_function("() => document.querySelector('.hand-dealt [data-rune=\"lava\"][aria-checked=\"true\"]')", timeout=WAIT_MS)
        assert pg.locator(".hand-dealt .hand-deal.is-faint").count() == 0, "all five used: nothing tells them apart"
    finally:
        pg.close()
    assert not log, "\n".join(log)


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


def test_the_field_is_addressed_by_the_open_tab_and_by_an_at_sign_and_a_press_takes_it_off(gui):
    pg, host, log = open_hand(gui)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        call(pg, "frame/state.js", "openTab", "tech")                              # Tech's tab
        _plus(pg).click()
        field, area = _field(pg)
        chip = field.locator(".hand-chip")
        assert chip.inner_text().strip() == "Tech" and chip.get_attribute("data-by") == "tab"
        shot(pg, "wide-field-addressed")
        area.fill("Reset the clock after a reconnect")
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"match": True, "now": True, "text": "Reset the clock after a reconnect", "party": "tech"}))
        _plus(pg).click()
        field, area = _field(pg)
        field.get_by_role("button", name="Take off Tech").click()                  # one press takes it off: general
        assert field.locator(".hand-chip").count() == 0
        area.fill("A general goal")
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"match": True, "now": True, "text": "A general goal"}))
        _plus(pg).click()
        field, area = _field(pg)
        assert field.locator(".hand-chip").count() == 0                            # taken off for that tab: still off on it
        call(pg, "frame/state.js", "openTab", "design")
        assert field.locator(".hand-chip").inner_text().strip() == "Design"       # another tab addresses its own party
        call(pg, "frame/state.js", "openTab", "orkmaster")
        area.fill("@Product pick the first theme")                                # *@Product* in the text addresses it, on the Orkmaster's tab
        chip = field.locator(".hand-chip")
        assert chip.inner_text().strip() == "Product" and chip.get_attribute("data-by") == "text"
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"match": True, "now": True, "text": "pick the first theme", "party": "product"}))
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


def test_a_stacks_edges_hint_how_many_five_at_most_and_never_a_number(gui):
    pg, host, log = open_hand(gui)
    try:
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        todo = {"id": "t0", "title": "KEY", "kind": "secret", "why": "", "choices": [], "steps": [], "accept": [], "done": False}
        for i in range(7):
            host.needs.append(need("todo", "tech", "export", "Export the round scores", f"KEY_{i}", todo={**todo, "id": f"t{i}", "title": f"KEY_{i}"}, at=f"2026-10-20T09:{20 + i}:00"))
        host.bump({})
        pg.wait_for_function("() => document.querySelector('.hand-stack[data-stack=\"export@1\"]')?.dataset.cards === '9'", timeout=WAIT_MS)
        assert _stack(pg, "export").locator(".ork-card-back.edge").count() == 5
        assert all(not e.inner_text() for e in _stack(pg, "export").locator(".ork-card-back.edge").all())                                  # a back says nothing: no count
    finally:
        pg.close()
    assert not log, "\n".join(log)


FAN_JS = """(sel) => [...document.querySelectorAll(sel)].map((e) => { const m = new DOMMatrix(getComputedStyle(e).transform); return [Math.round(Math.atan2(m.b, m.a) * 1800 / Math.PI) / 10, Math.round(m.e * 10) / 10]; })"""


def _deepen(pg, host, n=6):
    """Cards added to the `export` stack until it holds n + 3 (more than the five edges show)."""
    todo = {"id": "t0", "title": "KEY", "kind": "secret", "why": "", "choices": [], "steps": [], "accept": [], "done": False}
    for i in range(n):
        host.needs.append(need("todo", "tech", "export", "Export the round scores", f"KEY_{i}", todo={**todo, "id": f"t{i}", "title": f"KEY_{i}"}, at=f"2026-10-20T09:{20 + i}:00"))
    host.bump({})
    pg.wait_for_function(f"() => document.querySelector('.hand-stack[data-stack=\"export@1\"]')?.dataset.cards === '{n + 2}'", timeout=WAIT_MS)
    pg.wait_for_timeout(700)


def test_a_fan_stands_still_under_reduced_motion(gui):
    server, browser = gui
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    pg = ctx.new_page()
    host = HandHost()
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    try:
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        _deepen(pg, host)
        sel = '.hand-stack[data-stack="export@1"] > .ork-card-back.edge'
        turns = pg.evaluate(FAN_JS, sel)
        assert len(turns) == 5 and all(t != 0 and a != 0 for t, a in turns), "the turn stands (a turn is not a motion)"
        assert pg.locator(sel).first.evaluate("e => getComputedStyle(e).transitionDuration") == "0s"
    finally:
        ctx.close()


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_stack_pressed_picks_its_goal_and_lifts_its_top_card_with_its_answers_and_its_cost(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        _press(pg, "export")                                                                                                                              # a stack pressed picks its goal and lifts its top card
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        box = lifted.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= pg.viewport_size["width"] + 1 and box["y"] >= 0
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


def test_the_cards_of_the_table_a_lifted_card_is_about_rise(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".frame-table").evaluate("""(t) => t.insertAdjacentHTML('beforeend',
          '<div id="a" data-about="idea:timer task:timer/t1">its task</div><div id="b" data-about="idea:timer task:timer/t2">another</div><div id="c" data-about="idea:export">a plan</div>')""")
        _press(pg, "timer")                                                                # a failure is about its task
        pg.locator(".hand-lifted").wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.getElementById('a').classList.contains('is-about')", timeout=WAIT_MS)
        assert not pg.locator("#b").evaluate("e => e.classList.contains('is-about')") and not pg.locator("#c").evaluate("e => e.classList.contains('is-about')")
        assert sig(pg, "hand/about.js", "aboutNow") == {"task": "timer/t1"}
        pg.wait_for_timeout(300)
        assert pg.locator("#a").evaluate("e => getComputedStyle(e).transform") != "none"
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.getElementById('a').classList.contains('is-about')", timeout=WAIT_MS)
        assert sig(pg, "hand/about.js", "aboutNow") is None
        _press(pg, "export")                                                               # a plan is about its goal's cards
        pg.wait_for_function("() => document.getElementById('c').classList.contains('is-about')", timeout=WAIT_MS)
        assert not pg.locator("#a").evaluate("e => e.classList.contains('is-about')")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_open_on_a_lifted_card_opens_the_stop_over_the_pane_and_it_goes_back_when_answered(gui):
    pg, host, log = open_hand(gui)
    try:
        _press(pg, "timer")
        pg.locator(".hand-ways-row").get_by_role("button", name="Open…").click()
        over = sig(pg, "frame/state.js", "over")
        assert over["kind"] == "stop" and over["props"]["key"].startswith("failed/timer/") and sig(pg, "frame/state.js", "lifted") == ""
        box = pane(pg)
        box.locator(".hand-stopface").wait_for(timeout=WAIT_MS)
        box.get_by_text("the reset test failed", exact=False).first.wait_for(timeout=WAIT_MS)
        box.locator(".shell-logview").wait_for(timeout=WAIT_MS)
        assert "reset the clock" in box.inner_text().lower() and "== round 1" in box.locator(".shell-logview").inner_text()          # the task, its error and its log
        assert box.get_by_role("button", name="Start again").count() == 1 and box.locator(".hand-spend__words").inner_text() == "about 4% of Claude's week"
        shot(pg, "wide-stop-over-the-pane")
        host.needs = [n for n in host.needs if n["idea"] != "timer"]
        host.nodes = [n for n in host.nodes if n["slug"] != "timer"]
        host.bump({})
        pg.wait_for_function("async () => (await import('/static/js/frame/state.js')).over.value === null", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the discard ----------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", ["narrow"])                                                           # at the wide width the discard is Release's lane: no view over the pane (spec 156 D.3)
def test_the_discard_shows_the_last_goal_done_and_what_is_ready_for_main_and_opens_over_the_pane(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(".hand-done")
        done.wait_for(timeout=WAIT_MS)
        assert "Lobby music loop" in done.inner_text() and done.locator(".ork-sign.check").count() == 1 and done.locator(".ork-elem.void").count() == 1
        assert done.locator(".ork-race__head").count() == 1 and "Done" in done.get_attribute("aria-label") and "2 goals ready for main" in done.get_attribute("aria-label")
        if width == "wide":
            assert "2 goals ready for main" in done.inner_text()
        assert pg.locator(".table-discard > .ork-card-back.edge").count() == 1                                                    # the other goal's back under it
        done.click()
        over = sig(pg, "frame/state.js", "over")
        assert over["kind"] == "discard" and "is-on" in done.get_attribute("class")
        box = pg.locator("#table-pane")
        box.locator(".hand-discardview").wait_for(timeout=WAIT_MS)
        assert box.get_by_role("region", name="Done, not yet seen").locator(".hand-drow").count() == 2                            # the goal seen is in the history, not here
        ready = box.get_by_role("region", name="Ready for main")
        assert ready.locator("[data-portal-card]").count() == 2 and ready.get_by_role("button", name="To main").count() == 1
        shot(pg, f"{width}-discard-over-the-pane")
        ready.get_by_role("button", name="To main").click()                                                                        # the portal's way (spec 149 G.1): the first goal ready is chosen, dev whole is not merged
        assert _sent(pg, host, ("ideas.to_main_plan", {"idea": ready.locator("[data-portal-card]").first.get_attribute("data-portal-card")})) and not [n for n, _ in host.log if n == "ideas.gate_merge"]
        done.click()                                                                                                                # pressed again, it closes
        assert sig(pg, "frame/state.js", "over") is None
    finally:
        pg.close()
    assert not log, "\n".join(log)


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

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_pick_a_sign_in_and_a_card_of_an_unknown_kind_are_cards_of_the_hand_too(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(extra=True), width=width)
    try:
        _stack(pg, "look").wait_for(timeout=WAIT_MS)
        assert _stack(pg, "sign_in/claude").count() == 1 and _stack(pg, "fresh").count() == 1                      # a stop of no goal is a stack of its own; the route card lies with its goal
        assert _stack(pg, "sign_in/claude").evaluate("e => e.closest('.hand-lane').dataset.lane") == "0" and _stack(pg, "fresh").evaluate("e => e.closest('.hand-lane').dataset.lane") == "0"   # both under the first lane
        _press(pg, "fresh")                                                                                       # the route card (spec 100 A: tests/test_route_card_desktop_browser.py): a press lifts it
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        assert lifted.get_by_role("button", name="Talk").count() == 1 and lifted.get_by_role("button", name="Put it back").count() == 1
        lifted.get_by_role("button", name="Put it back").click()
        pg.mouse.move(pg.viewport_size["width"] / 2, 20)                                                         # the pointer off the cards: one under it would rise over its neighbour's edge
        pg.wait_for_timeout(400)
        _press(pg, "sign_in/claude")
        pg.locator(".hand-lifted").get_by_role("button", name="Sign in").wait_for(timeout=WAIT_MS)
        pg.keyboard.press("Escape")
        pg.evaluate("() => document.activeElement.blur()")                                                         # the card that had the focus lies risen, whole, over its neighbours
        pg.mouse.move(pg.viewport_size["width"] / 2, 20)
        pg.wait_for_timeout(400)
        _press(pg, "look")                                                                                        # a pick: its variants as small tiles, *Take B* once one is picked
        lifted = pg.locator(".hand-lifted")
        lifted.locator(".pick-tile").first.wait_for(timeout=WAIT_MS)
        assert lifted.locator(".pick-tile").count() == 2 and lifted.get_by_role("button", name="Take A").count() == 0
        shot(pg, f"{width}-lifted-pick")
        lifted.locator('.pick-tile__label[data-variant="A"]').click()
        lifted.get_by_role("button", name="Take A").click()
        assert _sent(pg, host, ("ideas.pick", {"slug": "look", "task": "p1", "key": "A", "via": "hand"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_pick_opened_over_the_pane_is_the_variants_large_and_a_note(gui):
    pg, host, log = open_hand(gui, host=HandHost(extra=True))
    try:
        _press(pg, "look")
        pg.locator(".hand-lifted").get_by_role("button", name="Pick, with a note").click()
        assert sig(pg, "frame/state.js", "over")["kind"] == "stop"
        box = pane(pg)
        box.get_by_role("textbox", name="Note").wait_for(timeout=WAIT_MS)
        assert box.locator(".pick-tile").count() == 2 and box.get_by_role("button", name="None of them: make new ones").count() == 1
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the words of the goal's way and the one place of the parties (spec 100 E) -------------------------------------------------------------------------------------

def test_every_kind_of_a_goals_way_has_its_plain_word_and_no_word_of_a_race(gui):
    pg, host, log = open_hand(gui, host=HandHost(bare=True))
    try:
        words = pg.evaluate("() => import('/static/js/arena/arenawords.js').then((m) => m.KIND_WORD)")
        assert {k: words[k] for k in ("route", "start", "talk", "cause", "decision", "fork", "project_q")} == {
            "route": "Route", "start": "Start", "talk": "Talk", "cause": "The cause", "decision": "Decision", "fork": "A fork", "project_q": "About the project"}
        mine = " ".join(words[k] for k in ("route", "start", "talk", "cause", "decision", "fork", "project_q")).lower()
        assert not re.search(r"\b(ork|orks|elf|elves|goblin|gnome|knight|lich|skeleton|undead)\b", mine)
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_edit_the_party_on_a_plan_that_misses_a_member_opens_the_one_place_of_the_parties_at_its_party(gui, width):
    host = HandHost(bare=True)
    next(n for n in host.needs if n["kind"] == "plan")["missing"] = [{"agent": "artist", "name": "Artist", "free": False}]
    pg, host, log = open_hand(gui, host=host, width=width)
    try:
        _stack(pg, "export").first.wait_for(timeout=WAIT_MS)
        pg.locator('.hand-card[data-kind="plan"]').first.click(position={"x": 10, "y": 24}, force=True)
        pg.locator(".hand-lifted").get_by_role("button", name="Edit the party").click()
        pg.locator('.table-over[data-kind="parties"]').wait_for(timeout=WAIT_MS)
        want = "Tech's table · Parties" if width == "wide" else "Board · Parties"        # wide: the card in play opened its asker's tab (spec 168 D1); the narrow page keeps the tab it had
        assert " ".join(pg.locator(".table-title__pt").text_content().split()) == want and pg.locator(".place").count() == 0
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_start_again_says_the_tasks_work_is_thrown_away_only_where_its_branch_holds_commits(gui):
    """Spec 149 D.4: the failure card's *Start again* says in its title that the task's work is thrown away and made again, when the host says the branch holds commits."""
    words = "The task's work is thrown away and made again"
    pg, host, log = open_hand(gui)
    try:
        _press(pg, "timer")
        btn = pg.locator(".hand-ways-row").get_by_role("button", name=re.compile("^Start again"))
        btn.wait_for(timeout=WAIT_MS)
        assert words not in (btn.get_attribute("title") or ""), "no commits: nothing is thrown away"
        pg.keyboard.press("Escape")
        next(n for n in host.nodes if n["slug"] == "timer")["tasks"][0]["holds_commits"] = True
        host.bump({})
        _press(pg, "timer")
        btn = pg.locator(".hand-ways-row").get_by_role("button", name=re.compile("^Start again"))
        btn.wait_for(timeout=WAIT_MS)
        assert words in btn.get_attribute("title")
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the goal under the pointer (spec 165 I, decisions §280.1) -------------------------------------------------------------------------------

REACH = "hand/reachhover.js"


def _card(pg, goal):
    return pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]')


def test_a_pointer_passing_over_a_card_without_resting_names_nothing(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        box = _card(pg, "timer").bounding_box()
        pg.mouse.move(box["x"] + 10, box["y"] + 24)
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(400)
        assert sig(pg, REACH, "reachGoal") == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_focus_names_the_goal_at_once_and_blur_and_esc_clear_it(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        _card(pg, "timer").focus()
        assert sig(pg, REACH, "reachGoal") == "timer"
        pg.evaluate("() => document.activeElement.blur()")
        assert sig(pg, REACH, "reachGoal") == ""
        _card(pg, "timer").focus()
        assert sig(pg, REACH, "reachGoal") == "timer"
        pg.keyboard.press("Escape")
        assert sig(pg, REACH, "reachGoal") == ""
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_touch_press_on_a_hand_card_names_no_goal_and_lifts_it_as_before(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.evaluate("""() => { const el = document.querySelector('.hand-card[data-goal="timer"][data-top="1"]');
          for (const t of ['pointerover', 'pointerdown']) el.dispatchEvent(new PointerEvent(t, { bubbles: true, pointerType: 'touch' })); }""")
        pg.wait_for_timeout(400)
        assert sig(pg, REACH, "reachGoal") == ""
        assert pg.locator(".hand-card.is-slot").count() == 0
        _press(pg, "timer")                                                                          # the press as today lifts the card
        pg.wait_for_selector(".hand-ways-row", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)
