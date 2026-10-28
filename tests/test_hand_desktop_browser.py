"""The hand of the new window (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §4–§6, part D; docs/specs/98-the-table-and-the-hand.md §4–§6), in a real browser against a stub host, the
window (the page, spec 98 E), at the two widths of `tests/narrow.py` (1280 × 800 and 390 × 844 with touch): the hand under the lanes (no deck; the + card under the first lane; a stack under the lane of who asks; two goals
under one lane fanned within its width, the back one's edge only and its rise; the discard under the tabs' end), a card's face (the header with its element, the window with the action's sign and the asker's head, the label row
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


def party(slug, name, race, craft):
    lead = {"slug": f"{slug}-lead", "name": f"{name} lead", "head": head(race, craft)}
    return {"slug": slug, "title": name, "short": name, "priority": "normal", "state": "ready", "done_when": [], "ideas": 0, "done": 0, "usd": None, "leader": lead,
            "team": [], "party": [], "today": {"merged": 0, "usd": 0.0}, "flags": 0, "waits_main": 0, "brief": "", "craft": craft, "race": race, "ideation": False}


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
            routed = node("fresh", "tech", "A goal just sent", "hand", state="routed", element="meadow")
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
            self.gate_doc = {"into": "dev", "main": "main", "same": True, "commits": 0, "files": 0, "ideas": []}

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
            return self.bump({"slug": "new-goal", "queue": "now", "element": "meadow", "route": [a.get("party") or "tech"]})
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


def card_boxes(pg, selector=".hand .hand-card"):
    return [b for b in (c.bounding_box() for c in pg.locator(selector).all()) if b]


def press_at(pg, goal, y=24):
    """A press on the left edge of a goal's front card (a card that lies behind another shows its left edge, and rises under the pointer)."""
    pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]').click(position={"x": 10, "y": y})


def lane(pg, i):
    return pg.locator(f'.hand-lane[data-lane="{i}"]')


def stacks_in(pg, i):
    return [s.get_attribute("data-stack") for s in lane(pg, i).locator(".hand-stack").all()]


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_hand_lies_under_the_lanes_one_size_half_under_the_edge_and_nothing_sideways(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        shot(pg, f"{width}-rest")
        size = pg.viewport_size
        assert pg.locator(".hand-deckback, .hand-deck, .hand-end--deck").count() == 0, "no deck: the goals in line lie on the table"
        assert pg.evaluate("() => import('/static/js/frame/kinds.js').then((m) => 'deck' in m.KINDS)") is False
        assert pg.locator(".hand-lane").count() == 5 and pg.locator(".hand-end").count() == 1, "a lane under each tab (the project's first, four parties) and the discard's place"
        sizes = set(map(tuple, pg.evaluate("() => [...document.querySelectorAll('.hand .hand-card, .hand .hand-back:not(.edge), .hand .hand-plus')].map((e) => [e.offsetWidth, e.offsetHeight])")))
        assert len(sizes) == 1, f"one card size, got {sizes}"
        assert sizes == ({(144, 202)} if width == "wide" else {(80, 112)}), sizes
        hand, window = pg.locator(".hand").bounding_box(), pg.locator('.hand-card[data-goal="timer"] .hand-card__window').bounding_box()
        card = pg.locator('.hand-card[data-goal="timer"]').bounding_box()
        assert abs(hand["y"] + hand["height"] - size["height"]) <= 1 and window["y"] + window["height"] <= size["height"] + 1, "the header and the window show"
        assert card["y"] + card["height"] > size["height"] + 25, "the lower half of a card lies under the window's edge"
        assert pg.locator('.hand-card[data-goal="timer"] .hand-card__label').bounding_box()["y"] >= size["height"] - 2, "the label row and the foot lie under it"
        assert hand["height"] <= (150 if width == "wide" else 100), "the hand is short: the table gains what it gave back"
        if width == "wide":
            cols = pg.locator(".hand-row").evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').map(parseFloat)")
            assert len(cols) == 6 and len(set(cols[:5])) == 1 and cols[0] == 180, f"every lane one width, a card and a quarter, then the tabs' end: {cols}"
            boxes = [lane(pg, i).bounding_box() for i in range(5)]
            assert all(abs(boxes[i + 1]["x"] - (boxes[i]["x"] + boxes[i]["width"])) <= 1 for i in range(4)), "the lanes are side by side on the grid"
            done, end = pg.locator(".hand-done").bounding_box(), pg.locator(".hand-end").bounding_box()
            assert end["x"] >= boxes[4]["x"] + boxes[4]["width"] - 1 and abs(done["x"] + done["width"] - size["width"]) <= 24, "the discard under the tabs' end, at its right"
        else:
            slots = sorted(pg.locator(".hand-slot, .hand-end").evaluate_all("els => els.map((e) => [e.classList.contains('is-plus') ? 'plus' : e.classList.contains('hand-end') ? 'end' : 'stack', e.getBoundingClientRect().x])"), key=lambda t: t[1])
            assert slots[0][0] == "plus" and slots[-1][0] == "end", "a free row in the lanes' order: the + card first, the discard last"
            assert all(b["width"] >= 44 and b["height"] >= 44 for b in card_boxes(pg)), "a press is 44 x 44 on touch"
        narrow.no_sideways(pg)
        assert pg.locator(".hand-row").evaluate("e => e.scrollWidth <= e.clientWidth + 1")
        assert pg.evaluate("() => document.documentElement.scrollHeight <= document.documentElement.clientHeight"), "the cards under the edge add no scroll"
    finally:
        pg.close()
    assert not log, "\n".join(log)


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


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_stack_lies_under_the_lane_of_who_asks_and_the_plus_card_under_the_first(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(extra=True), width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert stacks_in(pg, 1) == ["timer@1", "export@1"]                                         # Tech's: its failure in front of its plan and to-do
        assert stacks_in(pg, 2) == ["look@2", "phones@2", "words@2"]                                 # Design's: its pick, then its two questions, the oldest first
        assert stacks_in(pg, 3) == ["theme@3"] and stacks_in(pg, 4) == []                            # Product's; Release asks nothing
        assert sorted(stacks_in(pg, 0)) == ["fresh@0", "sign_in/claude@0"]                           # what is the whole goal's (the route) and a tool's sign-in lie under the first lane
        first = lane(pg, 0).locator(".hand-slot")
        assert first.count() == 3 and "is-plus" in first.last.get_attribute("class"), "the + card with them: the last of the first lane's fan"
        assert lane(pg, 0).locator(".hand-plus").count() == 1 and pg.locator(".hand-plus").count() == 1
        if width == "wide":
            box, plus = lane(pg, 0).bounding_box(), pg.locator(".hand-plus").bounding_box()
            assert box["x"] - 12 <= plus["x"] and plus["x"] + plus["width"] <= box["x"] + box["width"] + 12, "under the first lane"   # turned a little (§167.5): its corners reach past the lane by a few pixels
            assert pg.locator(".hand-plus > .ork-icon").evaluate("e => e.offsetWidth || e.width.baseVal.value") == 14, "its + shows on the edge the stacks leave it"   # its own size (the card is turned)
            pg.locator(".hand-plus").click(position={"x": 5, "y": 20})                              # a press on that edge grows it into the field
            _field(pg)
        shot(pg, f"{width}-first-lane")
        for i, goals in ((1, {"timer", "export"}), (2, {"look", "phones", "words"}), (3, {"theme"})):          # no card of one party's lane lies under another's
            assert {c.get_attribute("data-goal") for c in lane(pg, i).locator(".hand-card").all()} == goals
    finally:
        pg.close()
    assert not log, "\n".join(log)


def _at_rest(pg):
    pg.mouse.move(640, 200)
    pg.wait_for_timeout(500)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_two_goals_under_one_lane_fan_within_its_width_the_back_ones_edge_only_and_its_rise(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        front, back = pg.locator('.hand-slot:has(.hand-card[data-goal="timer"])'), pg.locator('.hand-slot:has(.hand-card[data-goal="export"])')
        word, mark = back.locator(".hand-card__name"), back.locator(".hand-card__head .ork-elem")
        fb, bb = front.bounding_box(), back.bounding_box()
        if width == "wide":
            assert "is-behind" in back.get_attribute("class") and "is-behind" not in front.get_attribute("class")                  # the urgent in front, the other behind
            assert int(front.evaluate("e => getComputedStyle(e).zIndex")) > int(back.evaluate("e => getComputedStyle(e).zIndex"))
            box = lane(pg, 1).bounding_box()
            assert bb["x"] < fb["x"] and fb["x"] - bb["x"] >= 20, "the one behind lies to the left, its edge showing"
            assert bb["x"] >= box["x"] - 1 and fb["x"] + fb["width"] <= box["x"] + box["width"] + 1, "the fan lies within its lane's width"
            assert word.evaluate("e => getComputedStyle(e).visibility") == "hidden" and mark.evaluate("e => getComputedStyle(e).visibility") == "visible", "its element only, no words"
            assert front.locator(".hand-card__name").evaluate("e => getComputedStyle(e).visibility") == "visible"
            m = mark.bounding_box()
            assert bb["x"] <= m["x"] and m["x"] + m["width"] <= fb["x"], "the element shows in the edge"
            shot(pg, "wide-fan-rest")
            pg.mouse.move(bb["x"] + 8, bb["y"] + 24)                                                  # hover on its edge: it rises whole, over the front one
            pg.wait_for_timeout(500)
            up = back.bounding_box()
            assert up["y"] <= bb["y"] - 60 and word.evaluate("e => getComputedStyle(e).visibility") == "visible"
            assert pg.evaluate("([x, y]) => document.elementFromPoint(x, y)?.closest('.hand-slot')?.querySelector('.hand-card')?.dataset.goal", [bb["x"] + 100, up["y"] + 60]) == "export"
            assert up["y"] + up["height"] >= pg.viewport_size["height"] - 4, "whole: its foot reaches the window's edge"
            shot(pg, "wide-fan-risen")
            _at_rest(pg)
            assert back.bounding_box()["y"] == bb["y"] and word.evaluate("e => getComputedStyle(e).visibility") == "hidden"
        for goal in ("export", "timer"):                                          # keyboard focus raises a card whole too, at both widths
            card = pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]')
            slot = pg.locator(f'.hand-slot:has(.hand-card[data-goal="{goal}"])')
            y0 = slot.bounding_box()["y"]
            card.focus()
            pg.wait_for_timeout(500)
            assert slot.bounding_box()["y"] <= y0 - 25, f"{goal} rises on focus"
            pg.evaluate("() => document.activeElement.blur()")
            pg.wait_for_timeout(500)
            assert slot.bounding_box()["y"] == y0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_tap_raises_a_card_whole_at_the_narrow_width(gui):
    pg, host, log = open_hand(gui, width="narrow")
    try:
        done = pg.locator(".hand-done")
        done.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        slot = pg.locator(".hand-discard")
        y0, b = slot.bounding_box()["y"], done.bounding_box()
        pg.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + 30)
        pg.wait_for_timeout(500)
        assert pg.evaluate("() => document.activeElement?.classList.contains('hand-done')") and slot.bounding_box()["y"] <= y0 - 25     # the tap focused it: it rose
        shot(pg, "narrow-tap-risen")
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_cards_face_is_a_header_a_window_a_label_row_and_a_foot(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        timer, phones = pg.locator('.hand-card[data-goal="timer"]'), pg.locator('.hand-card[data-goal="phones"]')
        timer.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        c = timer.bounding_box()
        elem, name = timer.locator(".hand-card__head .ork-elem").bounding_box(), timer.locator(".hand-card__name").bounding_box()
        assert elem["x"] - c["x"] <= 12 and elem["x"] + elem["width"] <= name["x"] + 1, "the element at the left of the header, bare, the name beside it"
        assert timer.locator(".hand-card__name").evaluate("e => getComputedStyle(e).textAlign") in ("start", "left")
        assert timer.locator(".hand-card__name").evaluate("e => getComputedStyle(e).webkitLineClamp") == ("3" if width == "wide" else "2"), "three lines at most"
        window = timer.locator(".hand-card__window")
        w, sign, asker = window.bounding_box(), timer.locator(".hand-card__window .ork-sign.alert").bounding_box(), timer.locator(".hand-card__asker .ork-race__head").bounding_box()
        assert sign["width"] == 28 and sign["height"] == 28 and asker["width"] == 24 and asker["height"] == 22, "the action's sign at the signs' big size, the asker's head small"
        # the head lies OVER the sign, on its lower right corner (a badge), and the two are one figure, centred together in the window (decisions §168.3)
        over_x, over_y = min(sign["x"] + 28, asker["x"] + 24) - max(sign["x"], asker["x"]), min(sign["y"] + 28, asker["y"] + 22) - max(sign["y"], asker["y"])
        assert over_x >= 6 and over_y >= 6, "the head overlaps the sign"
        assert asker["x"] > sign["x"] + 6 and asker["y"] > sign["y"] + 6 and asker["x"] + 24 > sign["x"] + 28 and asker["y"] + 22 >= sign["y"] + 28, "on the sign's lower right corner"
        assert timer.locator(".hand-card__window .hand-card__fig").evaluate("e => [...e.children].map((c) => c.className)") == ["hand-card__act", "hand-card__asker"]
        assert pg.evaluate("([s, a]) => getComputedStyle(document.querySelector(a)).zIndex === 'auto' && !!(document.querySelector(s).compareDocumentPosition(document.querySelector(a)) & 4)", [".hand-card[data-goal=timer] .hand-card__act", ".hand-card[data-goal=timer] .hand-card__asker"]), "the head after the sign: over it"
        fx0, fx1, fy0, fy1 = min(sign["x"], asker["x"]), max(sign["x"] + 28, asker["x"] + 24), min(sign["y"], asker["y"]), max(sign["y"] + 28, asker["y"] + 22)
        assert abs((fx0 + fx1) / 2 - (w["x"] + w["width"] / 2)) <= 2 and abs((fy0 + fy1) / 2 - (w["y"] + w["height"] / 2)) <= 3, "the figure centred in the window"
        assert w["x"] <= fx0 and fx1 <= w["x"] + w["width"] and (width == "narrow" or (w["y"] <= fy0 and fy1 <= w["y"] + w["height"])), "inside the window"
        assert timer.locator(".hand-card__window .ork-sign.alert").evaluate("e => getComputedStyle(e).opacity") != "1" and window.evaluate("e => getComputedStyle(e).borderTopWidth") == "1px"
        gem = timer.locator(".hand-card__label .ork-gem")
        gb = gem.bounding_box()
        assert gem.inner_text() == "4%" and gb["x"] + gb["width"] >= c["x"] + c["width"] - 12, "the gem at the label row's right"
        if width == "wide":
            party = timer.locator(".hand-card__party")
            assert party.text_content() == "Tech" and party.bounding_box()["x"] < gb["x"], "the party's name in the label row"
            foot = timer.locator(".hand-card__foot")
            assert foot.inner_text() == "The reset test failed" and foot.evaluate("e => e.scrollHeight <= 2 * parseFloat(getComputedStyle(e).lineHeight) + 4"), "the line in the foot, two lines at most"
        else:
            assert timer.locator(".hand-card__party").evaluate("e => getComputedStyle(e).display") == "none"       # the small card keeps the gem alone in its label row
        q = phones.locator(".hand-card__window .ork-sign.question")                                               # a question: the question mark, toned down in its goal's element colour
        assert q.count() == 1 and q.evaluate("e => getComputedStyle(e).opacity") == "0.6"
        assert q.evaluate("e => getComputedStyle(e).color") == phones.locator(".hand-card__head .ork-elem").evaluate("e => getComputedStyle(e).backgroundColor")
        assert phones.locator(".ork-gem").count() == 0 and phones.locator(".hand-card__asker .ork-race__head").count() == 1
        assert pg.locator(".hand-card .ork-sign.target").count() == 0
        shot(pg, f"{width}-faces")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_picked_goals_stacks_are_lit_alike(gui):
    pg, host, log = open_hand(gui, host=HandHost(both=True))
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert stacks_in(pg, 1) == ["timer@1", "export@1"] and stacks_in(pg, 2) == ["phones@2", "words@2", "timer@2"]       # a goal under two lanes: a stack in each
        assert pg.locator(".hand-card.ork-picked").count() == 0
        call(pg, "frame/state.js", "pick", "timer")
        pg.wait_for_function("() => document.querySelectorAll('.hand-card.ork-picked').length === 2", timeout=WAIT_MS)
        assert [c.get_attribute("data-goal") for c in pg.locator(".hand-card.ork-picked").all()] == ["timer", "timer"]
        assert pg.locator(".hand-card.ork-picked.is-on").count() == 2 and pg.locator(".hand-card.ork-picked").evaluate_all("els => els.map((e) => e.closest('.hand-lane').dataset.lane)") == ["1", "2"]
        pg.wait_for_timeout(500)
        shot(pg, "wide-picked")
        call(pg, "frame/state.js", "pick", "timer")
        pg.wait_for_function("() => document.querySelectorAll('.hand-card.ork-picked').length === 0", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def _plus(pg):
    return pg.locator(".hand .hand-plus")


def _field(pg):
    f = pg.locator(".hand-field")
    f.wait_for(timeout=WAIT_MS)
    return f, f.get_by_role("textbox", name="Write a goal")


# -- the deck -------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_no_part_with_nothing_to_hold(gui, width):
    pg, host, log = open_hand(gui, host=HandHost(bare=True), width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-plus").count() == 1 and lane(pg, 0).locator(".hand-slot").count() == 1 and lane(pg, 0).locator(".hand-slot").get_attribute("data-at") == "1"   # the + card alone under the first lane, in its middle
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


def test_with_no_goal_at_all_the_plus_card_lies_large_in_the_panes_middle(gui):
    pg, host, log = open_hand(gui, host=HandHost(empty=True))
    try:
        big = pg.locator(".hand-plus.is-large")
        big.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-lane").count() == 0 and pg.locator(".hand-end").count() == 0
        table, card = pg.locator(".frame-table").bounding_box(), big.bounding_box()
        assert abs((card["x"] + card["width"] / 2) - (table["x"] + table["width"] / 2)) <= 4 and abs((card["y"] + card["height"] / 2) - (table["y"] + table["height"] / 2)) <= 4
        assert card["width"] > 120
        shot(pg, "wide-large-plus")
        big.click()
        field, area = _field(pg)
        assert "is-middle" in field.get_attribute("class") and big.count() == 0
        area.fill("My first goal")
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"text": "My first goal"}))
    finally:
        pg.close()
    assert not log, "\n".join(log)


# -- the + card and its field -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_plus_card_grows_into_the_field_enter_sends_shift_enter_a_new_line_esc_keeps_the_words(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        _plus(pg).wait_for(timeout=WAIT_MS)
        _plus(pg).click()
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
        _plus(pg).click()
        _, area = _field(pg)
        assert area.input_value() == "Show the round number\nabove the timer"
        pg.mouse.click(size["width"] / 2, 60)                                       # a press away closes it, its text kept
        assert pg.locator(".hand-field").count() == 0
        _plus(pg).click()
        _, area = _field(pg)
        assert area.input_value() == "Show the round number\nabove the timer"
        area.press("Enter")                                                        # Enter sends: general on the Orkmaster's tab, no party
        assert _sent(pg, host, ("ideas.add", {"text": "Show the round number\nabove the timer"}))
        pg.wait_for_function("() => !document.querySelector('.hand-field')", timeout=WAIT_MS)             # sent: the field closes with its text gone
        _plus(pg).click()
        assert _field(pg)[1].input_value() == ""
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
        assert _sent(pg, host, ("ideas.add", {"text": "Reset the clock after a reconnect", "party": "tech"}))
        _plus(pg).click()
        field, area = _field(pg)
        field.get_by_role("button", name="Take off Tech").click()                  # one press takes it off: general
        assert field.locator(".hand-chip").count() == 0
        area.fill("A general goal")
        area.press("Enter")
        assert _sent(pg, host, ("ideas.add", {"text": "A general goal"}))
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
        assert _sent(pg, host, ("ideas.add", {"text": "pick the first theme", "party": "product"}))
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
def test_the_stacks_are_a_goal_each_the_urgent_first_the_gem_only_where_a_card_spends(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        assert [s.get_attribute("data-stack") for s in pg.locator(".hand-stack").all()] == ["timer@1", "export@1", "phones@2", "words@2", "theme@3"]      # lane by lane, the failure first in Tech's; a to-do last
        assert _stack(pg, "export").get_attribute("data-cards") == "2" and _stack(pg, "export").locator(".ork-card-back.edge").count() == 1      # its cards under it face down
        top = lambda goal: pg.locator(f'.hand-card[data-goal="{goal}"][data-top="1"]')                                                          # noqa: E731
        assert top("timer").locator(".ork-gem").text_content() == "4%" and top("export").locator(".ork-gem").text_content() == "2–4%"             # a failure's Start again, a plan's Start
        for none in ("phones", "words", "theme"):
            assert top(none).locator(".ork-gem").count() == 0                                                                                  # a question costs nothing
        assert "fails" in top("timer").get_attribute("class") and "asks" in top("phones").get_attribute("class")
        assert top("timer").locator(".ork-sign.alert").count() == 1 and top("phones").locator(".hand-card__head .ork-elem.meadow").count() == 1
        assert top("timer").locator(".ork-race__head").count() == 1                                                                            # its leader's head
        assert top("timer").locator(".hand-card__party").text_content() == "Tech" and top("phones").locator(".hand-card__party").text_content() == "Design"      # the party's name, on any tab
        call(pg, "frame/state.js", "openTab", "design")
        pg.wait_for_timeout(300)
        assert top("timer").locator(".hand-card__party").text_content() == "Tech" and len(pg.locator(".hand-stack").all()) == 5                       # the hand is the same on every tab
        assert pg.locator(".hand-card .hand-spend, .hand-card .hand-spend__words").count() == 0                                                # its words only on the lifted card
        assert not [t for t in pg.locator(".hand").inner_text().lower().split() if t in ("idea", "ideas", "track", "orc", "agent")]
    finally:
        pg.close()
    assert not log, "\n".join(log)


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


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_stacks_cards_behind_the_front_one_lie_as_a_fan_turned_by_place_and_a_hover_opens_it(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        _stack(pg, "export").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(700)
        sel = '.hand-stack[data-stack="export@1"] > .ork-card-back.edge'
        assert pg.evaluate(FAN_JS, sel) != [] and len(pg.evaluate(FAN_JS, sel)) == 1
        _deepen(pg, host)
        rest = pg.evaluate(FAN_JS, sel)
        assert len(rest) == 5, "five edges at most"
        by_place = rest[::-1]                                                                            # the DOM lists the deepest first: place 1 (the nearest the front) is the last
        assert [t > 0 for t, _ in by_place] == [True, False, True, False, True] and [a > 0 for _, a in by_place] == [True, False, True, False, True], "by turns right and left"
        scale = 1 if width == "wide" else 0.7
        for turn, aside in by_place:
            assert 2 <= abs(turn) <= 4 and 6 * scale - 0.1 <= abs(aside) <= 10 * scale + 0.1, f"turned 2 to 4 degrees, stepped 6 to 10 px aside ({turn}, {aside})"
        front = pg.locator('.hand-card[data-goal="export"][data-top="1"]')
        assert front.evaluate("e => getComputedStyle(e).transform") == "none", "the front card lies straight"
        assert pg.locator(".hand-stack[data-stack='export@1'] .ork-card-back.edge").evaluate_all("els => els.every((e) => !e.innerText)")
        pg.mouse.move(640, 200)
        pg.wait_for_timeout(400)
        shot(pg, f"{width}-fan-rest")
        # a redraw shakes nothing: the same turns after the Board changes
        host.bump({})
        pg.wait_for_timeout(500)
        assert pg.evaluate(FAN_JS, sel) == rest, "a fixed turn by place, no shake on a redraw"
        slot = pg.locator('.hand-slot:has(.hand-stack[data-stack="export@1"])')
        sb = slot.bounding_box()
        pg.mouse.move(sb["x"] + 12, sb["y"] + 30)                                                          # hover: the fan opens a little wider
        pg.wait_for_timeout(600)
        opened = pg.evaluate(FAN_JS, sel)[::-1]
        for (t0, a0), (t1, a1) in zip(by_place, opened):
            assert abs(a1) > abs(a0) and abs(t1) >= abs(t0) and abs(t1) <= 6 and (a0 > 0) == (a1 > 0), "wider, the same sides"
        assert pg.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"), "no sideways scroll"
        shot(pg, f"{width}-fan-open")
        _at_rest(pg)
        assert pg.evaluate(FAN_JS, sel) == rest, "closed again at rest"
        card = pg.locator('.hand-card[data-goal="export"][data-top="1"]')                                   # keyboard focus opens it too
        card.focus()
        pg.wait_for_timeout(600)
        assert abs(pg.evaluate(FAN_JS, sel)[-1][1]) > abs(rest[-1][1])
        pg.evaluate("() => document.activeElement.blur()")
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
def test_two_goals_in_one_lane_are_two_small_fans_the_urgent_in_front(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(700)
        sel = '.hand-lane[data-lane="1"] .hand-stack > .ork-card-back.edge'
        edge = pg.locator(sel)
        assert edge.count() == 1, "the second goal has a card behind its front, laid turned"
        assert edge.evaluate("e => new DOMMatrix(getComputedStyle(e).transform).b") != 0
        front, back = pg.locator('.hand-slot:has(.hand-card[data-goal="timer"])'), pg.locator('.hand-slot:has(.hand-card[data-goal="export"])')
        if width == "wide":
            assert int(front.evaluate("e => getComputedStyle(e).zIndex")) > int(back.evaluate("e => getComputedStyle(e).zIndex"))
            assert front.bounding_box()["x"] > back.bounding_box()["x"], "the urgent at the right, the other behind it"
        else:
            assert front.bounding_box()["x"] < back.bounding_box()["x"], "a free row: the urgent first"
        assert pg.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth")
        shot(pg, f"{width}-fans-in-a-lane")
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
        assert lifted.locator(".hand-spend__words").inner_text() == "about 2–4% of Claude's week" and lifted.locator(".ork-gem.share").count() == 1       # its cost's words
        assert "is-slot" in pg.locator('.hand-card[data-kind="plan"]').get_attribute("class")                                                           # a slot where it lay
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


def test_a_question_is_answered_from_its_card_and_the_card_goes_with_the_stop(gui):
    pg, host, log = open_hand(gui)
    try:
        _press(pg, "phones")
        lifted = pg.locator(".hand-lifted")
        lifted.wait_for(timeout=WAIT_MS)
        assert lifted.locator(".hand-spend").count() == 0 and "Where does the timer run?" in lifted.inner_text()                   # no gem, no words: it spends nothing
        assert lifted.get_by_role("button", name="Let Design lead decide").count() == 1 and lifted.get_by_role("button", name="Put it back").count() == 1
        shot(pg, "wide-lifted-question")
        lifted.get_by_role("button", name="● Server counts, phones show it").click()
        assert _sent(pg, host, ("ideas.answer", {"slug": "phones", "answers": ["Server counts, phones show it"]}))
        pg.wait_for_function("() => !document.querySelector('.hand-stack[data-stack=\"phones@2\"]:not(.is-gone)')", timeout=WAIT_MS)
        assert pg.locator(".hand-lifted").count() == 0 and sig(pg, "frame/state.js", "lifted") == ""
        assert [s.get_attribute("data-stack") for s in pg.locator(".hand-stack:not(.is-gone)").all()] == ["timer@1", "export@1", "words@2", "theme@3"]
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
        pg.locator(".hand-lifted").get_by_role("button", name="Open…").click()
        over = sig(pg, "frame/state.js", "over")
        assert over["kind"] == "stop" and over["props"]["key"].startswith("failed/timer/") and sig(pg, "frame/state.js", "lifted") == ""
        box = pane(pg)
        box.locator(".hand-stopface").wait_for(timeout=WAIT_MS)
        box.get_by_text("the reset test failed", exact=False).first.wait_for(timeout=WAIT_MS)
        box.locator(".shell-log").wait_for(timeout=WAIT_MS)
        assert "reset the clock" in box.inner_text().lower() and "== round 1" in box.locator(".shell-log").inner_text()          # the task, its error and its log
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

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_discard_shows_the_last_goal_done_and_what_is_ready_for_main_and_opens_over_the_pane(gui, width):
    pg, host, log = open_hand(gui, width=width)
    try:
        done = pg.locator(".hand-done")
        done.wait_for(timeout=WAIT_MS)
        assert "Lobby music loop" in done.inner_text() and done.locator(".ork-sign.check").count() == 1 and done.locator(".ork-elem.void").count() == 1
        assert done.locator(".ork-race__head").count() == 1 and "Done" in done.get_attribute("aria-label") and "2 goals ready for main" in done.get_attribute("aria-label")
        if width == "wide":
            assert "2 goals ready for main" in done.inner_text()
        assert pg.locator(".hand-discard > .ork-card-back.edge").count() == 1                                                    # the other goal's back under it
        done.click()
        over = sig(pg, "frame/state.js", "over")
        assert over["kind"] == "discard" and "is-on" in done.get_attribute("class")
        box = pane(pg)
        box.locator(".hand-discardview").wait_for(timeout=WAIT_MS)
        assert box.get_by_role("region", name="Done, not yet seen").locator(".hand-drow").count() == 2                            # the goal seen is in the history, not here
        ready = box.get_by_role("region", name="Ready for main")
        assert ready.locator(".hand-drow").count() == 2 and ready.get_by_role("button", name="To main").count() == 1
        shot(pg, f"{width}-discard-over-the-pane")
        ready.get_by_role("button", name="To main").click()                                                                        # today's merge into main, by code
        assert _sent(pg, host, ("ideas.gate_merge", {}))
        pg.wait_for_function("() => !document.querySelector('.hand-done')?.getAttribute('aria-label')?.includes('ready for main')", timeout=WAIT_MS)
        done.click()                                                                                                                # pressed again, it closes
        assert sig(pg, "frame/state.js", "over") is None
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_goal_pressed_in_the_discard_opens_its_result_is_seen_and_leaves_the_discard(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-done").click()
        box = pane(pg)
        box.get_by_role("region", name="Done, not yet seen").locator('.hand-drow[data-slug="codes"]').click()
        over = sig(pg, "frame/state.js", "over")
        assert over["kind"] == "result" and over["props"] == {"idea": "codes"}
        assert _sent(pg, host, ("ideas.seen", {"idea": "codes"})) and host.seen_log == ["codes"]
        box.locator(".hand-result").wait_for(timeout=WAIT_MS)
        assert "room codes are four letters" in box.inner_text().lower()
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

def test_a_card_leans_and_rises_under_the_pointer_and_nothing_moves_under_reduced_motion(gui):
    pg, host, log = open_hand(gui)
    try:
        card = pg.locator('.hand-card[data-goal="timer"]')
        card.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        assert card.evaluate("e => getComputedStyle(e).transform") == "none"                    # at rest it is flat
        b = card.bounding_box()
        pg.mouse.move(b["x"] + b["width"] - 6, b["y"] + 10)
        pg.wait_for_timeout(400)
        assert card.evaluate("e => getComputedStyle(e).transform") != "none" and card.evaluate("e => getComputedStyle(e).getPropertyValue('--ork-lean-x')").strip() != ""
        assert pg.locator('.hand-slot:has(.hand-card[data-goal="timer"])').bounding_box()["y"] <= b["y"] - 60          # and rises whole (a spring, hand.css)
    finally:
        pg.close()
    assert not log, "\n".join(log)
    server, browser = gui
    ctx = browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.route_web_socket("**/ws*", HandHost().on_socket)
    pg.goto(server.url)
    try:
        card = pg.locator('.hand-card[data-goal="timer"]')
        card.wait_for(timeout=WAIT_MS)
        b = card.bounding_box()
        pg.mouse.move(b["x"] + b["width"] - 6, b["y"] + 10)
        pg.wait_for_timeout(400)
        assert card.evaluate("e => getComputedStyle(e).transform") == "none"
        assert pg.locator(".hand-card.ork-deal").count() == 0
        slot = pg.locator('.hand-slot:has(.hand-card[data-goal="timer"])')
        assert slot.bounding_box()["y"] <= b["y"] - 60 and slot.evaluate("e => getComputedStyle(e).transitionDuration") == "0s"      # a card rises whole all the same (it must be read), without the spring
    finally:
        ctx.close()


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
        _press(pg, "sign_in/claude")
        pg.locator(".hand-lifted").get_by_role("button", name="Sign in").wait_for(timeout=WAIT_MS)
        pg.keyboard.press("Escape")
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


def test_a_card_that_comes_is_dealt_from_under_the_windows_edge_and_a_card_that_goes_crumbles_where_it_lay(gui):
    pg, host, log = open_hand(gui)
    try:
        pg.locator(".hand-stack").first.wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(900)
        assert pg.locator(".hand-card.ork-deal").count() == 0                                   # the first draw deals nothing
        host.nodes = [{**n, "place": "hand"} if n["slug"] == "mute" else n for n in host.nodes]
        host.needs.append(need("asks", "tech", "mute", "Mute a noisy player", "Who may mute?", asked=[{"ask": "Who may mute?", "choices": ["The host"], "pick": None, "why": "", "by": None, "look": False}]))
        host.bump({})
        card = pg.locator('.hand-card[data-goal="mute"]')
        card.wait_for(timeout=WAIT_MS)
        assert "ork-deal" in card.get_attribute("class") and card.evaluate("e => getComputedStyle(e).getPropertyValue('--ork-deal-y')").strip() != ""      # dealt, from under the window's edge
        pg.wait_for_function("() => !document.querySelector('.hand-card.ork-deal')", timeout=WAIT_MS)
        host.needs = [n for n in host.needs if n["idea"] != "mute"]
        host.bump({})
        pg.locator(".hand-stack.is-gone .ork-crumble > i").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".hand-stack.is-gone .ork-crumble > i").count() == 6                  # six pixel squares fall, they do not fade
        pg.wait_for_function("() => !document.querySelector('.hand-stack.is-gone')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)
