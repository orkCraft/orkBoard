"""Spec 108 part B, concerns on the maps (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §3, decisions §183.4–§183.5), in a real browser at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844),
against the maps' stub host (`MapsHost`: Game design with its loop, Tech led by the Architect with its System, Art, Release, Marketing) that also answers part A's commands as the contract says —
`ideas.concerns {party}` the record `{at, map_hash, by, status, error, concerns: [{id, on, name, level, what, why, fix, signal}], dismissed}`, `ideas.concerns_again`, `ideas.concern_dismiss` (both the record),
`ideas.concern_goal` (`{ok, idea}`) — and carrying each goal's `concerns: {alerts, notes, status}` in the snapshot.

A card with an alert wears orkUI's alert sign and the leader's small head, a note a dot; the highest level of several, their count only in the label; on a part of the System (inside its scaled box) and on a step of the loop;
what the strip said is exported now (docs/specs/123-the-leaders-at-the-table.md §4): `lookOf(party)` in each state (1 alert, 2 notes; nothing; looking; a failure with its words; the snapshot's counts while no record), `askAgain` in the party's **…** (*Ask again*),
`stepMarked(party, level, aspect)` stepping through the marked cards;
a marked card pressed lifts and its back lists each concern with **Make it a goal** and **Not a problem**, the mark then a link to the goal in its element's colour; the party's tab shows **!** with no count; nothing moves under
reduced motion; every target 44 px at the narrow width; picking wins on a marked card; a host without the commands shows no strip and no error.

Spec 109 part C (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §4): the record also carries `rubric: {framework, short, aspects: [{id, name, ask, state, n, hints}]}` (null or absent: an older host) and each concern its `aspect`;
the row `.cn-aspects` is in the party's header (the rubric's short words, then each aspect an orkUI chip `.cn-aspect` with its state's mark, its words in the label, a button only while a card has an open concern of it; under 760 px only those), a press on one
steps through only its cards, a card's back says *Alert · Coupling*, no row for a record with no rubric, no sideways scroll. Spec 121 part F: the evening line is drawn at the top of the leader's bubble (ask.js; the head that opens it is the tabs', spec 123 F,
so a stand-in carrying `data-ask-head` presses `openAsk`). Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_maps_desktop_browser import MapsHost, Refused  # noqa: E402
from tests.test_table_desktop_browser import node, tab, watch  # noqa: E402

pytestmark = pytest.mark.browser

LOBBY, ROOMS, INDEX = "server/lobby.ts", "server/rooms.ts", "server/index.ts"


def concern(cid, on, level, what, why="", fix="", signal="", aspect=""):
    return {"id": cid, "on": on, "name": on.rsplit("/", 1)[-1], "level": level, "what": what, "why": why or f"Why: {what}", "fix": fix or f"Fix: {what}", "signal": signal, "aspect": aspect}


def aspect(aid, name, ask, state, n=0, hints=()):
    return {"id": aid, "name": name, "ask": ask, "state": state, "n": n, "hints": list(hints)}


# Tech's rubric as spec 109 §2.1 says (the ids are code's, the names and asks the interface's), in the states of TECH below: one alert, two notes, one hint (code noticed it, the leader let it be), one clear
TECH_RUBRIC = {"framework": "C4's containers and parts; ISO/IEC 25010's maintainability, security and reliability; hotspots, where change and size meet; the stable-dependencies principle", "short": "C4 · ISO 25010 · hotspots", "aspects": [
    aspect("modularity", "Modularity", "Are the parts' edges clean: no cycles, no part reaching into many others?", "hint", 0, ["server/index imports 9 parts"]),
    aspect("coupling", "Coupling", "Does a change ripple: a part everyone needs, a shared part changed from many containers?", "alert", 1),
    aspect("hotspots", "Hotspots", "Where is code both big and often changed, where bugs and slow work collect?", "note", 1),
    aspect("testability", "Testability", "Is what changes often covered by tests?", "note", 1),
    aspect("safety", "Security and reliability", "Does a part take people's input, secrets or money without a guard; is one part a single point of failure?", "clear")]}
GAME_RUBRIC = {"framework": "MDA and the eight kinds of fun, core, session and meta loops, an economy of sources and sinks, flow, and why a player comes back", "short": "MDA · loops · economy", "aspects": [
    aspect("loop", "Core loop", "Does every loop reward the player, and does each span feed the next?", "alert", 1), aspect("economy", "Economy", "Does every currency have a source and a sink?", "note", 1),
    aspect("pacing", "Pacing and flow", "Do the intensities rise and rest, with no flat stretch or sudden spike?", "note", 1), aspect("retention", "Retention", "Is there a reason to come back on day 1, day 7 and day 30?", "clear"),
    aspect("grounded", "Grounded", "Does each step rest on the files that make it?", "clear")]}


def record(*concerns, status="ready", error="", by="architect", rubric=TECH_RUBRIC, since=None):
    return {"at": "2026-10-29T08:00:00", "map_hash": "h1", "by": by, "status": status, "error": error, "measure": None, "concerns": list(concerns), "dismissed": [], "rubric": copy.deepcopy(rubric),
            **({"since": since} if since else {})}


TECH = [concern("c1", LOBBY, "alert", "Every room goes through lobby.ts", "Eleven parts use it and it holds the sockets too.", "Split the sockets out of it.", "fan_in", "coupling"),
        concern("c2", LOBBY, "note", "lobby.ts changed six times this month with no test", "", "", "churn", "testability"),
        concern("c3", ROOMS, "note", "rooms.ts grows", "It is four hundred lines.", "Watch it.", "", "hotspots")]
GAME = [concern("g1", "hold-the-tower", "alert", "Nothing in the loop pays for holding the tower", "Gems are only earned.", "Let gems buy a skin.", "finding", "loop"),
        concern("g2", "join-a-match", "note", "Joining takes four steps", "", "", "", "pacing"), concern("g3", "cur:coins", "note", "Coins have no sink", "", "", "", "economy")]


class ConcernHost(MapsHost):
    """The maps' host that also keeps a record for each party and answers part A's commands; `older`: a host that does not know them."""

    def __init__(self):
        super().__init__()
        self.parties[0]["leader"]["name"] = "Game design lead"
        self.records = {"tech": record(*copy.deepcopy(TECH)), "game": record(*copy.deepcopy(GAME), rubric=GAME_RUBRIC)}
        self.older = False                                                                   # a host that knows neither the commands nor the counts
        self.refuse = False                                                                  # a host that refuses the commands but still carries each goal's counts
        self.looks = 0

    def counts(self, slug):
        r = self.records.get(slug)
        if not r:
            return {"alerts": 0, "notes": 0, "status": "ready"}
        return {"alerts": sum(c["level"] == "alert" for c in r["concerns"]), "notes": sum(c["level"] == "note" for c in r["concerns"]), "status": r["status"]}

    def handle(self, name, a):
        if name == "ideas.map" and not self.older:
            got = super().handle(name, a)
            for g in got["goals"]:
                g["concerns"] = self.counts(g["slug"])
            return got
        if name.startswith("ideas.concern"):
            self.log.append((name, a))
            if self.older or self.refuse:
                raise Refused(f"unknown command {name}")
            return self.concerns(name, a)
        return super().handle(name, a)

    def concerns(self, name, a):
        rec = self.records.setdefault(a["party"], record())
        if name == "ideas.concerns":
            if rec["status"] == "looking":                                                     # a look under way ends the second time it is asked about
                self.looks += 1
                if self.looks >= 2:
                    rec["status"] = "ready"
                    self.looks = 0
                    self.rev += 1
            return copy.deepcopy(rec)
        if name == "ideas.concerns_again":
            rec["status"] = "looking"
            self.looks = 0
            return copy.deepcopy(rec)
        c = next(x for x in rec["concerns"] if x["id"] == a["id"])
        if name == "ideas.concern_dismiss":
            rec["concerns"].remove(c)
            rec["dismissed"].append({"on": c["on"], "what": c["what"], "at": "2026-10-29T09:00:00", "map_hash": rec["map_hash"]})
            self.rev += 1
            return copy.deepcopy(rec)
        c["idea"] = "split-sockets"                                                              # ideas.concern_goal: a goal made of it
        self.nodes.append(node("split-sockets", a["party"], c["what"], "ready", element="ice", sign="restructure", place="deck"))
        self.rev += 1
        return {"ok": True, "idea": "split-sockets"}

    def sent(self, name):
        return [a for n, a in self.log if n == name]


def start(gui, width, host=None, **context):
    errors: list[str] = []
    server, browser = gui
    host = host or ConcernHost()
    pg = browser.new_context(**{**(narrow.WIDE if width == "wide" else narrow.FINE), **context}).new_page()
    watch(pg, errors)
    pg.add_init_script("window.__scrolls = []; const into = Element.prototype.scrollIntoView; Element.prototype.scrollIntoView = function (o) { window.__scrolls.push(o && o.behavior); return into.call(this, o); };")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    return pg, host, errors


@pytest.fixture(params=narrow.WIDTHS)
def desk(gui, request):
    """The window at one of the two widths against a ConcernHost: `(page, host, width)`; the page's errors are asserted at the end."""
    pg, host, errors = start(gui, request.param)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def go(pg, slug):
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"], .col-head__tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


def cn(pg):
    """concerns.js, imported into the page once (`window.__cn`), for the checks that wait on it."""
    pg.evaluate("() => window.__cn || import('/static/js/table/concerns.js').then((m) => { window.__cn = m; })")


def ready(pg, party):
    """The page has read the party's record (`ideas.concerns` answered)."""
    cn(pg)
    pg.wait_for_function("p => !!window.__cn.recordOf(p)", arg=party, timeout=WAIT_MS)


def system(pg):
    go(pg, "tech")
    pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)
    ready(pg, "tech")


def loop(pg):
    go(pg, "game")
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    ready(pg, "game")


def look(pg, party="tech"):
    """`lookOf(party)`: what the strip said, as the table reads it now."""
    return pg.evaluate("p => import('/static/js/table/concerns.js').then((m) => m.lookOf(p))", party)




def step(pg, party="tech", level="", aspect=""):
    """`stepMarked(party, level, aspect)`: what a press on a mark or an aspect does. Whether a card was found."""
    return pg.evaluate("([p, l, a]) => import('/static/js/table/concerns.js').then((m) => m.stepMarked(p, l, a))", [party, level, aspect])


def row(pg):
    return pg.locator(".table-head .cn-aspects")






def chip(pg, aid):
    return pg.locator(f'.cn-aspect[data-aspect="{aid}"]')


def push(pg, host):
    """The host's record changed: a new Board, the page reads it again."""
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))


def marks(pg):
    return pg.locator(".cn-slot .cn-mark")


def back(pg):
    return pg.locator(".table-back")


def wide(w):
    return w == "wide"


# -- the marks -----------------------------------------------------------------------------------------------------------------------------------------







# -- what the strip said: lookOf, Ask again, stepMarked ------------------------------------------------------------------------------------------------------













# -- the card's back -----------------------------------------------------------------------------------------------------------------------------------







# -- the tab -------------------------------------------------------------------------------------------------------------------------------------------



# -- reduced motion, touch, picking, an older host ----------------------------------------------------------------------------------------------------











# -- the aspects (spec 109 part C) ----------------------------------------------------------------------------------------------------------------------

STATES = {"modularity": "hint", "coupling": "alert", "hotspots": "note", "testability": "note", "safety": "clear"}
WORDS = {"modularity": "Modularity: a hint from code", "coupling": "Coupling: 1 concern", "hotspots": "Hotspots: 1 concern", "testability": "Testability: 1 concern", "safety": "Security and reliability: nothing wrong"}




















# -- spec 121 part F (docs/specs/121-the-day-the-morning-and-the-night.md §6, §7.4), spec 123 §6.3: the evening line, at the top of the leader's bubble ---------------------------------------------

SINCE_LINE = "The results screen now says who was first, a clearer way through; the lobby's back button lost its label."


def since(way, line=SINCE_LINE):
    return {"way": way, "line": line, "at": "2026-11-01T18:00:00", "map_hash": "h2"}


def evening(pg):
    return pg.locator(".table-ask__bubble .cn-since")












