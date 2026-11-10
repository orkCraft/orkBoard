"""Spec 98 part C, the table (docs/specs/98-the-table-and-the-hand.md §3, §5, §6; mockup docs/mockups/s1/ states 1–4 and 6), re-faced by spec 101 part C (the Board's cards, a goal's cascade, the line in the first lane, the project's tab) and part F (a goal's tasks behind its front card lie as a fan): the window (the
page, spec 98 E), at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch), against a stub host of its own (a project of four parties: Game design, Tech led by the Architect, Art and Release; the Orkmaster reading two goals,
routing one and joining one; tasks at work, failures, a check; three goals in line; Tech's System).

The tabs in order with the project's first (its name), its **…** and its three places over the pane, the empty chair (*New party*), *Stop all* in the die's front face (spec 139 A); the Board's lanes under their tabs, the same widths; a task card's header, window and label row, a goal's strip and
cascade (its front by the rule, the others a fan behind it with a fixed turn by place, opened by a hover, an edge lifting its task, the picked goal's unfolded, a goal in two lanes lit in both); the first lane's cards and the line (the Orkmaster's order, the moon, a drag, *All · search*); a party's header with its
groups, a seat's popover and its **Open**, another party's tab its header alone; Tech's System; a card lifted and lowered (Esc, a press away); a file opened over the pane, its title, **←** back to the card lit; a form in the pane, never a dialog; no
sideways scroll at 390. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set.

Spec 111 B (decisions §187.1–§187.2, §189): one rune a stack (the strip's; none on a task card's header or an edge; a goal the Orkmaster does itself is its card alone with its rune and its whole title), the flame (the rune
glowing in the stage's sign's place on a task at work, none on a task that waits or failed, still under reduced motion, the old motion gone), and the sword and shield on each tab with the marks of the tools its Does and
Checks run on (the open tab's in colour, a Lean party's shield faint with no mark, a dot for a mixed column, the words in the title and the label, none at the narrow width)."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import library  # noqa: E402
from tests import narrow  # noqa: E402
from tests.first_open_kit import desk  # noqa: E402,F401  (fixture)
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser

SHOP = "/work/shop"
HEAD = lambda race, tier, craft="engineering": {"craft": craft, "race": race, "tier": tier}  # noqa: E731
LEADS = {"game": HEAD("knight", "elder", "product"), "tech": HEAD("peon", "elder"), "art": HEAD("elf", "elder", "design"), "release": HEAD("lich", "elder", "product")}
NAMES = {"game": "Game design", "tech": "Tech", "art": "Art", "release": "Release"}
MEMBER = {"grunt": ("Grunts", HEAD("peon", "warrior"), "build"), "tester": ("Tester", HEAD("peon", "laborer"), "build"), "reviewer": ("Reviewer", HEAD("peon", "warrior"), "check"),
          "designer": ("Designer", HEAD("knight", "warrior", "product"), "build"), "artist": ("Artist", HEAD("elf", "warrior", "design"), "build")}
FILE = "server/lobby.ts"
MARKS = {"game": {"does_tool": "claude", "checks_tool": "claude", "does_mixed": False, "checks_mixed": False, "lean": False},                         # a party's sword and shield as `ideas.map` serves them (gui/ideas_map.py `marks_of`)
         "tech": {"does_tool": "claude", "checks_tool": "codex", "does_mixed": False, "checks_mixed": False, "lean": False},
         "art": {"does_tool": "claude", "checks_tool": "", "does_mixed": False, "checks_mixed": False, "lean": True},                                    # Lean: no separate check
         "release": {"does_tool": "codex", "checks_tool": "claude", "does_mixed": True, "checks_mixed": False, "lean": False}}                          # one of its roles runs on another tool
LOBBY = "\n".join(f"line {i}" for i in range(1, 30))


def task(tid, title, state, who="grunt", band="build", **more):
    name, head, _ = MEMBER[who]
    return {"id": tid, "title": title, "short": title, "state": state, "after": [], "tier": "warrior", "head": head, "by": {"slug": who, "name": name}, "band": band, "wave": 1, "row": 1, "tag": "Code",
            "error": "", "note": "", "round": 1, "cost": None, "made": "", **more}


def node(slug, goal, title, state, stage="planning", element="meadow", sign="", tasks=(), **more):
    return {"slug": slug, "goal": goal, "title": title, "short": title, "state": state, "queue": "", "held_until": "", "start_at": "", "priority": "normal", "size": "M", "risk": "low", "tier": 1,
            "depends_on": [], "waits_on": [], "waits": None, "needs_you": "", "progress": {"done": 0, "total": len(tasks)}, "done": 0, "of": len(tasks), "tasks": list(tasks), "estimate": None,
            "plan_estimate": None, "by_itself": False, "folded": False, "updated": "2026-10-28T09:00:00", "stage": stage, "round": 1, "usd": None, "asked": [], "results": [], "checks": [],
            "element": element, "flag": None, "type": {"sign": sign, "name": sign.title()} if sign else None, "route": [], "place": "table", "asks_you": False, "waits_as": "", "seen": "", **more}


def seat(slug, band):
    name, head, _ = MEMBER[slug]
    return {"slug": slug, "name": name, "head": head, "band": band, "state": "work" if slug == "grunt" else "free", "why": ""}


def party(slug, order, seats=()):
    name, head = NAMES.get(slug, slug), LEADS.get(slug, LEADS["art"])
    lead = {"slug": "architect" if slug == "tech" else "taskmaster", "name": "Architect" if slug == "tech" else name, "head": head}
    return {"slug": slug, "title": name, "short": name, "priority": "normal", "state": "ready", "done_when": [], "ideas": 1, "done": 0, "usd": None, "leader": lead, "size": "standard",
            "team": [{"slug": s, "name": MEMBER[s][0], "head": MEMBER[s][1], "checks": MEMBER[s][2] == "check", "every": False} for s, _ in seats], "tool": "", "tools": {}, "craft": "engineering",
            "party": [{**lead, "band": "lead", "state": "free", "why": ""}, *[seat(s, b) for s, b in seats]], "today": {"merged": 0, "usd": 0.0}, "flags": 0, "waits_main": 0, "brief": "", "order": order,
            "next_element": "dust", "free_elements": ["dust", "void", "lava"], **MARKS.get(slug, MARKS["game"])}


def system_doc():
    part = lambda path, uses=(), used_by=(): {"path": path, "name": path.rsplit("/", 1)[-1], "count": 2, "uses": list(uses), "used_by": list(used_by), "gone": False}  # noqa: E731
    parts = {p["path"]: p for p in (part("server/index.ts", ["server/lobby.ts"]), part(FILE, [], ["server/index.ts"]), part("server/rooms.ts"), part("client/net.ts"))}
    cont = lambda path, name, layers: {"path": path, "name": name, "stack": [{"name": "Express", "role": "server"}], "unknown": 0, "ways_in": [], "parts": [p for ly in layers for p in ly["parts"]],
                                       "layers": layers, "gone": []}  # noqa: E731
    return {"commit": "a" * 40, "short": "aaaaaaa", "at": "2026-10-28T08:00:00", "ref": "dev", "since": "", "columns": [{"name": "server", "parts": [], "stack": []}], "changed": {}, "uses_changed": [], "goals": {},
            "overview": {"containers": [cont("server", "server/", [{"role": "doors", "parts": ["server/index.ts"]}, {"role": "data", "parts": [FILE, "server/rooms.ts"]}]),
                                        cont("client", "client/", [{"role": "face", "parts": ["client/net.ts"]}])],
                         "shared": [], "links": [{"from": "client", "to": "server", "http": [{"method": "GET", "path": "/rooms", "called_in": "client/net.ts", "answered_in": FILE}], "socket": []}], "parts": parts}}


class TableHost:
    """The page's host as the table reads it: the snapshot, `ideas.map`, `ideas.board`, `ideas.agents`, `ideas.roles`, `ideas.system`, and the commands a thing over the pane asks."""

    def __init__(self, crowd: int = 0, line: int = 3, rich: bool = True):
        self.log: list[tuple[str, dict]] = []
        self.ws = None
        self.rev = 1
        self.needs: list[dict] = []                                                                                           # the Needs you rows (spec 99), none unless a test adds them
        self.current = SHOP
        order = ["game", "tech", "art", "release"] + [f"extra{i}" for i in range(crowd)]
        seats = {"game": [("designer", "build")], "tech": [("grunt", "build"), ("tester", "build"), ("reviewer", "check")], "art": [("artist", "build")], "release": []}
        self.parties = [party(s, i, seats.get(s, [])) for i, s in enumerate(order)]
        for p in self.parties:
            if p["slug"].startswith("extra"):
                p["title"] = p["short"] = f"Party {p['slug'][5:]}"
        self.nodes = [
            node("results", "tech", "Results screen with the round's best answer", "planning", element="dust", sign="screen"),
            node("timer", "game", "Round timer shows on every phone", "reading", element="meadow", sign="mechanic"),
            node("rules", "game", "Write the timer's rules: seconds in each phase", "working", "implementation", "meadow", "mechanic",
                 [task("r1", "Write the timer's rules: seconds in each phase", "running", "designer")]),
            node("seat", "tech", "Keep the seat when a socket reconnects", "working", "implementation", "ice", "feature",
                 [task("s1", "Keep the seat when a socket reconnects", "running"), task("s2", "Reset the round timer when a player rejoins", "failed", "tester", error="3 checks failed", made="", round=2, cost=1.2)],
                 route=[{"step": "party", "party": "tech", "goal": "seat", "state": "working", "done": 0, "total": 2}, {"step": "moved", "party": "art", "from": "art"}]),
        ]
        if rich:                                                                                                              # what the hand would answer with cards of its own is left out of the window's tests
            self.nodes.insert(1, node("calm", "tech", "Tidy the lobby code", "working", "implementation", "dust", "tidy", [task("k1", "Tidy the lobby code", "running")]))     # nothing wrong: behind the failures in its lane, though first in the Board
            self.nodes += [
                node("recheck", "tech", "Check that a rejoin keeps the round", "working", "checking", "lava", "bug",
                     [task("c1", "Write the rejoin check", "running"), task("c2", "Check the rejoin", "failed", "reviewer", "check", error="1 check failed")]),
                node("bar", "art", "A timer bar that drains", "sections", "implementation", "void", "screen",                    # its sections joined by the Orkmaster while its party works: a strip in both lanes
                     [task("a1", "Draw the bar", "running", "artist", tag="Pixel art"), task("a2", "Check the bar's colours", "testing", "reviewer", "check"),
                      task("a3", "Pick the bar's look", "picking", "artist", tag="Pixel art")]),
            ]
        fixed = [("ln1", "tech", "Chat in the lobby", "dust", "feature", {}),
                 ("ln2", "game", "Round music that fades in", "ice", "sound", {"waits_as": "reset", "held_until": "2026-10-29T06:00:00"}),
                 ("ln3", "art", "A banner for the lobby", "meadow", "picture", {}),
                 ("ln4", "tech", "Rejoin without a lobby", "lava", "bug", {})]
        for i in range(line if rich else 0):
            slug, goal, title, element, sign, more = fixed[i] if i < len(fixed) else (f"ln{i + 1}", ["game", "tech", "art"][i % 3], f"Goal {i + 1} in line", ["dust", "ice", "meadow"][i % 3], "feature", {})
            self.nodes.append(node(slug, goal, title, "ready", element=element, sign=sign, place="deck", **more))

    def push(self):
        """The Board changed: a new revision, and the page reads the map again."""
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))

    def snapshot(self):
        return {"t": "state", "state": {
            "focus": "board", "ideas_rev": self.rev, "look": "office", "project": "shop", "demo": False, "onboarding": False, "words": [], "resources": {}, "orkspaces": [], "buildings": [], "roads": [], "alerts": [],
            "score": {}, "limits": [{"provider": "claude", "name": "Claude", "left": 0.62, "rows": [{"window": "5h", "left": 0.62, "reset": ""}]},
                                    {"provider": "codex", "name": "Codex", "left": 0.18, "rows": [{"window": "daily", "left": 0.18, "reset": ""}]}],
            "mana": {"main": "claude", "now": "claude", "until": None, "moved": None, "paid": None},
            "reserve": {"share": 0.1, "night": False}, "rate": None, "review_count": 0, "needs_you": 0, "sign_in": [], "hud": {"gold": "$2.40", "show_gold": True, "lumber": "120k"},
            "projects": {"current": self.current, "recent": [{"path": "/work/old", "name": "old"}], "open": [{"path": SHOP, "name": "shop", "working": 1, "needs_you": 0, "review": 0},
                                                                                                         {"path": "/work/other", "name": "other", "working": 0, "needs_you": 0, "review": 0}]}}}

    def board(self):
        tracks = [{"slug": p["slug"], "title": p["title"], "about": "", "criteria": [], "deadline": "", "order": p["order"], "count": 1, "priority": "normal", "metrics": [], "links": [], "summary": "",
                   "questions": [], "state": "ready", "state_error": "", "team": [t["slug"] for t in p["team"]], "every": [], "leader": p["leader"], "tool": "", "tools": {}, "craft": "engineering"}
                  for p in self.parties]
        ideas = [{"slug": n["slug"], "title": n["title"], "track": n["goal"], "order": i, "state": n["state"], "size": "M", "asks": 0, "updated": "x", "talk": [], "priority": "normal", "queue": "",
                  "held_until": "", "risk": "low", "risk_triggers": [], "depends_on": [], "waits_on": [], "start_at": "", "in_needs_you": False, "progress": n["progress"], "thesis": ""}
                 for i, n in enumerate(self.nodes)]
        return {"tracks": tracks, "ideas": ideas, "needs_you": copy.deepcopy(self.needs), "target": "balance", "autostart": True, "review": False, "review_notice": False, "rev": self.rev}

    def handle(self, name, a):
        self.log.append((name, a))
        if name == "ideas.map":
            return {"goals": copy.deepcopy(self.parties), "nodes": copy.deepcopy(self.nodes), "edges": [], "rev": self.rev}
        if name == "ideas.board":
            return self.board()
        if name == "ideas.move":                                                                                              # a goal moves before another, else last
            me = next(n for n in self.nodes if n["slug"] == a["slug"])
            self.nodes.remove(me)
            at = next((i for i, n in enumerate(self.nodes) if n["slug"] == a.get("before")), len(self.nodes))
            self.nodes.insert(at, me)
            self.rev += 1
            return {"ok": True}
        if name == "ideas.review_list":
            return {"into": "dev", "push": False, "branches": ["dev", "main"], "results": []}
        if name == "ideas.agents":
            return {"roles": [{"role": s, "name": MEMBER[s][0], "model": "", "max_parallel": 2, "builtin": False, "spend_today": 0, "chips": [], "kinds": ["code"], "usd_task": 0.4, "head": MEMBER[s][1],
                               "harness": {"id": "claude", "name": "Claude"}, "week": None} for s in MEMBER], "done_today": []}
        if name == "ideas.roles":
            return {"roles": [{"slug": s, "name": MEMBER[s][0], "model": "", "max_parallel": 2, "instruction": f"You are the {MEMBER[s][0]}.", "builtin": False, "head": MEMBER[s][1], "spend_today": 0,
                               "record": None} for s in MEMBER], "kinds": [], "models": [{"id": "", "label": "The task's own tier"}], "library": [x | {"installed": False} for x in library.listed()],
                    "suggested": library.SUGGESTED, "seats": library.SEATS, "parties": library.parties(), "presets": library.presets(), "stages": library.stages(), "tier_costs": {}}
        if name == "ideas.gate":
            return {"into": "dev", "main": "main", "same": True, "commits": 0, "files": 0, "ideas": []}
        if name == "ideas.today":
            return {"events": []}
        if name == "ideas.flags":
            return {"goals": [], "flags": []}
        if name == "ideas.system":
            return system_doc()
        if name == "ideas.system_part":
            return {"path": a["path"], "name": a["path"].rsplit("/", 1)[-1], "count": 2, "files": [a["path"], a["path"].replace(".ts", ".test.ts")], "uses": ["server/rooms.ts"], "used_by": ["server/index.ts"],
                    "gone": False, "kind": "", "since": "", "changes": [], "goals": {}}
        if name == "ideas.task":
            return {"id": a["task"], "idea": a["slug"], "idea_title": "Keep the seat", "title": "Keep the seat", "state": "failed" if a["task"] == "s2" else "running", "tier": "warrior", "branch": "ork/s1",
                    "round": 1, "cost": None, "error": "3 checks failed" if a["task"] == "s2" else "", "brief": "Keep a player's seat when the socket reconnects.", "log": "tests: 3 failed\nfix the timer\n",
                    "head": MEMBER["grunt"][1], "note": ""}
        if name == "ideas.diff":
            return {"commits": [{"sha": "abc1234", "subject": "Keep the seat"}], "files": [{"path": FILE, "added": 3, "removed": 1, "patch": "@@ -1 +1 @@\n-a\n+b\n"}], "truncated": False}
        if name == "files.tree":
            return {"entries": [{"name": "server", "path": "server", "dir": True, "secret": False, "ignored": False}, {"name": "README.md", "path": "README.md", "dir": False, "secret": False, "ignored": False}]}
        if name == "files.read":
            return {"path": a["path"], "kind": "text", "text": LOBBY, "html": "", "size": len(LOBBY), "mtime": 1.0}
        if name == "git.status":
            return {"branch": "dev", "work_branch": "dev", "upstream": "", "ahead": 0, "behind": 0, "files": [], "last": None}
        if name == "ideas.usage":
            return {"rows": [], "scopes": ["project"], "window": "5h", "outside": 0, "tokens_only": False}
        if name == "ideas.tools":
            return {"main": "claude", "tools": [{"id": "claude", "name": "Claude Code", "installed": True, "signed_in": True, "ready": True, "tiers": True}]}
        if name == "ideas.parties":
            return {"parties": []}
        if name == "ideas.proposals":
            return {"proposals": []}
        if name == "projects.use":
            self.current = a["path"]
            self.rev += 1
            return {"ok": True}
        return {}

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
            if m["name"] == "projects.use":
                ws.send(json.dumps(self.snapshot()))
        ws.on_message(on_message)


def shot(pg, name):
    d = os.environ.get("ORKCRAFT_SHOTS_DIR")
    if d:
        Path(d).mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)                                                      # a card has finished turning over
        pg.screenshot(path=str(Path(d) / name))


def watch(pg, errors):
    """The page's errors: a script error, a console error, a failed request."""
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource") and errors.append(f"console: {m.text}"))
    pg.on("response", lambda r: r.status >= 400 and errors.append(f"{r.status}: {r.url}"))


def start(gui, width, errors, **kw):
    """The window at `width` against a TableHost (`kw`: its `crowd`, its `line`): `(page, host)`."""
    server, browser = gui
    host = TableHost(**kw)
    pg = narrow.page(browser, width)
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    if width == "wide":                                                                                                   # a failed task's card lies as a place while its failure is in the hand (spec 128 C.2: tests/test_thrown_browser.py);
        pg.locator(".table-thrown").first.wait_for(timeout=WAIT_MS)                                                       # this file looks at the cards themselves, so they are put back in their lanes
        pg.evaluate("() => import('/static/js/table/flight.js').then((m) => { m.thrown.value = new Map(); })")
        pg.locator('[data-lkey="t:task:seat/s2"]').wait_for(timeout=WAIT_MS)
    return pg, host


@pytest.fixture(params=narrow.WIDTHS)
def table(gui, request):
    """The window at one of the two widths: `(page, host, width)`; the page's errors are asserted at the end."""
    errors: list[str] = []
    pg, host = start(gui, request.param, errors)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def lined(gui, request):
    """The same with four goals in line (two of one party, so one can be moved among them)."""
    errors: list[str] = []
    pg, host = start(gui, request.param, errors, line=4)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.fixture(params=narrow.WIDTHS)
def crowded(gui, request):
    """The same with nine goals in line: past seven the line says *All · search*."""
    errors: list[str] = []
    pg, host = start(gui, request.param, errors, line=9)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def anim(el, pseudo=""):
    """`[name, duration, timing]` of an element's animation (or its pseudo-element's)."""
    return el.evaluate("(e, p) => { const s = getComputedStyle(e, p || null); return [s.animationName, s.animationDuration, s.animationTimingFunction]; }", pseudo)


def tab(pg, slug):
    """A tab: a leader's in the row, the Orkmaster's the column's head at the wide width (spec 128 B.2) and the row's first at the narrow."""
    return pg.locator(f'.table-tab[data-tab="{slug}"], .col-head__tab[data-tab="{slug}"]')


def cell(pg, slug):
    """A tab's cell: the tab's button and, for the open tab, its head and marks beside it (spec 123 F: no button holds a button); the Orkmaster's at the wide width is the column's head."""
    return pg.locator(f'.table-tabcell[data-cell="{slug}"], .col-head') if slug == "orkmaster" else pg.locator(f'.table-tabcell[data-cell="{slug}"]')


def open_tab(pg, slug):
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"], .col-head__tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


def title(pg):
    return " ".join(pg.locator(".table-title__pt").text_content().split())


def open_menu(pg):
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    pg.get_by_role("menu").wait_for(timeout=WAIT_MS)


# -- the tabs ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_tabs_in_order_the_projects_first_then_plus_and_no_stop_all_in_the_row(table):
    pg, host, w = table
    tabs = pg.locator(".table-tab")
    assert [t.get_attribute("data-tab") for t in tabs.all()] == (["game", "tech", "art", "release"] if wide(w) else ["orkmaster", "game", "tech", "art", "release"])         # the project's first at the narrow width, then the Board's order; the leaders' alone at the wide (the Orkmaster's tab is the column's head: spec 128 B.2)
    first = tab(pg, "orkmaster")
    if wide(w):
        assert first.get_attribute("aria-selected") == "true" and first.get_attribute("role") == "tab" and "orkmaster" not in first.text_content().lower() and first.text_content().strip() == "shop"      # the project's name on its first line; the Orkmaster only in its label (spec 161 J, decisions §272.5)
        assert first.get_attribute("aria-label") == "The Orkmaster · shop" and first.evaluate("e => !!e.closest('.frame-column')")
    else:
        assert first.get_attribute("aria-label") == "shop · Does on Claude · Checks on Claude" and first.get_attribute("aria-selected") == "true"                # the first tab is the project's: its name (spec 101 §3.4, decisions §167.6) and the main tool on both (spec 111 §3.4)
        assert "Orkmaster" not in (first.get_attribute("title") or "") and first.locator(".table-tab__sub").count() == 0
        assert first.locator(".table-tab__main").text_content() == "shop"
    assert "peon-crown" in cell(pg, "orkmaster").locator(".ork-race__head").get_attribute("src")                          # its crowned head (the open tab's head is in its cell, beside its button)
    assert "knight-elder" in tab(pg, "game").locator(".ork-race__head").get_attribute("src")                             # a party's tab wears its leader's head
    assert tab(pg, "tech").get_attribute("aria-label") == "Tech · Does on Claude · Checks on Codex"                      # and its name, said also when only the head is drawn, with its sword and shield's words (spec 111 §3.4)
    assert tab(pg, "tech").get_attribute("title") == tab(pg, "tech").get_attribute("aria-label")
    assert pg.get_by_role("button", name="New party").count() == 1 and pg.locator(".table-tabs").get_by_role("button", name="Stop all").count() == 0 and (pg.locator(".release-lane__head") if wide(w) else pg.locator(".hand-die")).get_by_role("button", name="Stop all").count() == 1       # Stop all: in the right column's head at the wide width (spec 168 A4), the die's under 760 px (spec 139 A)
    chair = pg.locator(".table-tabs__end .table-chair")
    assert " ".join(chair.text_content().split()) == ("New party" if wide(w) else "") and "primary" not in chair.get_attribute("class")           # spec 123 §7.5: the empty chair, green is New goal's
    assert pg.get_by_role("button", name="Switch project").count() == 1                                                  # the ▾ after the project's name, its own button
    assert pg.locator(".table-tabs__end .table-chip").count() == 0 and pg.locator(".table-tabs__end button:not(.stall-pack):not(.presence-chain)").count() == 1 and pg.locator(".stall-pack").count() == 1 and pg.locator(".table-logs").count() == 0                  # the tabs' end keeps the empty chair and the door, then the bug under the glass (decisions §190.6): the limits are the hand's potions (spec 104 B)
    if not wide(w):
        assert tab(pg, "tech").locator(".table-tab__txt").is_hidden()                                                    # the tabs a row of heads
        assert all(t.bounding_box()["width"] >= 44 and t.bounding_box()["height"] >= 44 for t in tabs.all())             # a press 44 × 44 on a touch screen
    assert title(pg) == ""  # no goal picked: the title says nothing (§247.5)
    assert tab(pg, "orkmaster").bounding_box()["x"] <= tab(pg, "game").bounding_box()["x"]
    shot(pg, f"table-board-{w}.png")


def test_a_tab_is_the_persons_the_open_one_is_kept_and_nothing_switches_it_under_them(table):
    pg, host, w = table
    open_tab(pg, "tech")
    assert title(pg) == ""  # no goal picked: the title says nothing (§247.5)
    pg.reload()
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    assert tab(pg, "tech").get_attribute("aria-selected") == "true"                                                      # kept for the project on this device
    tab(pg, "tech").focus()
    pg.keyboard.press("ArrowLeft")
    assert tab(pg, "game").get_attribute("aria-selected") == "true"                                                      # the arrows move between tabs
    pg.keyboard.press("Home")
    if wide(w):
        assert tab(pg, "game").get_attribute("aria-selected") == "true"                                                  # the row is the leaders': Home is the first leader
        pg.keyboard.press("ArrowLeft")                                                                                   # and the arrow before it is the Orkmaster's tab, the column's head
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))                                                                            # the Board changes under them
    pg.wait_for_timeout(300)
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"


def test_the_orkmasters_menu_has_settings_files_and_report_a_problem_and_the_projects_are_the_arrow_after_the_name(table):
    """Spec 107 §8.2: *Switch project* left the Orkmaster's **…** for the **▾** after the project's name."""
    pg, host, w = table
    open_menu(pg)
    menu = pg.get_by_role("menu")
    assert [i.inner_text().strip() for i in menu.get_by_role("menuitem").all()] == ["Settings", "Files", "Report a problem…"]
    if not wide(w):
        assert [c.inner_text().strip() for c in menu.locator(".table-chip").all()] == ["Claude 62% left", "Codex 18% left"]       # the limits' chips in the Orkmaster's …
    pg.keyboard.press("Escape")
    pg.get_by_role("button", name="Switch project").click()
    pg.locator('.table-over[data-kind="projects"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Board · Projects" and pg.locator(".table-projects__one").count() == 3                          # the open projects, the recent ones
    assert pg.locator('[role="dialog"][aria-modal="true"]').count() == 0                                                 # in the pane, never a dialog
    pg.locator(".table-title__back").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    open_menu(pg)
    pg.get_by_role("menuitem", name="Settings").click()
    pg.locator('.table-over--form[data-kind="settings"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Board · Settings" and pg.locator("[aria-modal]").count() == 0               # the form lies in the pane: no dialog, no backdrop
    assert pg.locator(".place").count() == 1 and pg.locator(".shell-backdrop").count() == 0
    shot(pg, f"table-settings-{w}.png")
    pg.get_by_role("button", name="Done").click()                                                                        # the form closes itself: the pane is the Board again
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    open_menu(pg)
    pg.get_by_role("menuitem", name="Files").click()
    pg.locator('.table-over[data-kind="files"] .shell-tree__row').first.wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")                                                                                          # Esc goes back
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)


def test_the_chair_deals_its_crafts_wide_or_opens_the_parties_narrow_and_a_potion_opens_what_used_the_tool(table):
    pg, host, w = table
    pg.get_by_role("button", name="New party").click()
    if wide(w):                                                                                                          # the wide page: the chair deals the crafts to the hand (decisions §272.2)
        pg.locator('[data-chair-deal="question"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.table-over[data-kind="parties"]').count() == 0
        pg.get_by_role("button", name="Put it back").click()
        pg.locator('[data-chair-deal="question"]').wait_for(state="detached", timeout=WAIT_MS)
    else:                                                                                                                # the narrow page keeps the one place of the parties (spec 100 §4)
        pg.locator('.table-over[data-kind="parties"]').wait_for(timeout=WAIT_MS)
        assert title(pg) == "Board · Parties" and pg.locator(".place").count() == 0
        pg.get_by_role("button", name="Back").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    if wide(w):
        narrow.unroll_drum(pg)
        pg.locator('.hand-pot[data-provider="codex"]').click()
        pg.locator('.table-over[data-kind="limits"] .arena-usage').wait_for(timeout=WAIT_MS)
        assert title(pg) == "Board · Codex: what used it"
        assert ("ideas.usage", {"provider": "codex", "scope": "project"}) in host.log
    pg.mouse.move(640, 300)                                                                                                # the row the drum unrolled folds: it lay over the die
    pg.get_by_role("button", name="Stop all").click()
    for _ in range(40):
        if ("halt", {}) in host.log:
            break
        pg.wait_for_timeout(50)
    assert ("halt", {}) in host.log


# -- the Board under the tabs ----------------------------------------------------------------------------------------------------------------------

def keys(pg, scope):
    """The `data-lkey`s inside `scope`, in the order they lie."""
    return [e.get_attribute("data-lkey") for e in pg.locator(f"{scope} [data-lkey]").all()]


def test_the_lanes_stand_under_their_tabs_every_lane_one_width_and_the_first_is_the_projects(table):
    pg, host, w = table
    lanes = pg.locator(".table-lane")
    k = 4 if wide(w) else 5                                                                                              # the lanes: the project's first at the narrow width; at the wide the project's is the Orkmaster's column (spec 128 B.1)
    if wide(w):
        assert pg.locator(".table-lane--first").count() == 0 and [l.get_attribute("data-party") for l in lanes.all()[:4]] == ["game", "tech", "art", "release"]
    else:
        assert lanes.first.get_attribute("data-lane") == "first" and [l.get_attribute("data-party") for l in lanes.all()[1:5]] == ["game", "tech", "art", "release"]
        assert lanes.first.get_attribute("aria-label") == "shop"                                                         # the first lane is the whole project's
    for slug in ("orkmaster", "game", "tech", "art", "release")[1 if wide(w) else 0:]:
        lane = lanes.first if slug == "orkmaster" else pg.locator(f'.table-lane[data-party="{slug}"]')
        t, l = cell(pg, slug).bounding_box(), lane.bounding_box()
        assert abs(t["x"] - l["x"]) <= 1 and abs(t["width"] - l["width"]) <= 1, slug                                      # a tab's cell is its lane's head: the same x, the same width (the open tab's head is in its cell, beside its button)
    widths = {round(l.bounding_box()["width"]) for l in lanes.all()[:k]}
    assert len(widths) == 1, widths                                                                                       # every lane the same width, the first too
    if wide(w):
        assert 144 <= widths.pop() <= 181                                                                                # a card and a quarter at most (frame.css `--col-w`), narrower by what the edge's column takes (spec 150 D.1): a card still fits
    else:
        assert widths.pop() <= 48                                                                                        # a token wide
    assert pg.locator(".table-board").evaluate("e => e.scrollWidth <= e.clientWidth + 1")                                # no sideways scroll
    assert pg.locator(".table-board").evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length") == (5 if wide(w) else 6)    # the lanes and the tabs' end: the frame's `--cols`, no `--tabs`


def test_a_task_card_has_its_header_its_window_with_the_types_sign_and_its_label_row_and_no_head(table):
    pg, host, w = table
    failed = pg.locator('[data-lkey="t:task:seat/s2"]')                                                                   # the front of its goal's cascade
    assert failed.get_attribute("data-state") == "failed"
    if not wide(w):
        tok = failed
        assert "table-token" in tok.get_attribute("class") and tok.get_attribute("aria-label").startswith("Keep the seat when a socket reconnects")
        assert tok.locator(".ork-elem.ice").count() == 1 and tok.locator(".ork-sign.feature").count() == 1 and tok.locator(".ork-sign.sword").count() == 1     # its element, its type, its stage
        assert tok.evaluate("e => e.parentElement.dataset.n") == "1"                                                      # one edge: one more task behind
        assert tok.bounding_box()["width"] <= 46 and pg.locator(".table-card").count() == 0
        return
    box = failed.bounding_box()
    assert abs(box["width"] - 144) <= 1 and abs(box["height"] - 202) <= 2                                                 # 144 wide (frame.css `--card-w`), 5 : 7 (spec 147 A.2)
    head = failed.locator(".table-card__head")
    assert head.locator(".ork-elem").count() == 0 and head.evaluate("e => e.firstElementChild.classList.contains('table-card__nm')")      # no rune in the header: the goal's rune is the top corner's (spec 147 A, decisions §251.2)
    nm = head.locator(".table-card__nm")
    assert nm.inner_text().strip() == "Reset the round timer when a player rejoins"
    assert nm.evaluate("e => getComputedStyle(e).textAlign") in ("left", "start") and nm.evaluate("e => getComputedStyle(e).webkitLineClamp") == "2"        # left-aligned, two lines at most (spec 147 A.2)
    text = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ork-font-text').trim()")
    assert text and nm.evaluate("e => getComputedStyle(e).fontFamily").replace(chr(34), "") == text.replace(chr(34), "")                                           # a person's words: the text face token (orkUI 0.40 draws every face in Rubik, decisions §291, so "not the pixel face" no longer tells)
    win = failed.locator(".table-card__win")
    assert 80 <= win.bounding_box()["height"] <= 92                                                                      # what the corners and the title leave of the card (spec 147 A.2), so a lane's cards line up
    assert win.get_attribute("data-window") == "fail" and win.locator(".ork-sign.alert").count() == 1 and win.locator(".ork-sign").count() == 1      # a failed task: orkUI's alert sign and its reason (spec 142 C, decisions §249.3)
    danger = pg.evaluate("() => { const d = document.createElement('i'); d.style.color = 'var(--ork-danger)'; document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }")
    assert win.locator(".table-win__reason").inner_text().strip() and win.evaluate("e => getComputedStyle(e.querySelector('.ork-sign')).color") == danger      # its reason, the sign in the danger colour
    assert win.evaluate("e => getComputedStyle(e).borderTopWidth") == "1px"                                              # a hairline
    row = failed.locator(".corner--foot")
    assert failed.locator(".corner--top .ork-elem").count() == 1 and failed.get_attribute("data-stage") == "doing"        # the goal's rune and the stage (said in the card's words) (spec 147 A)
    assert row.locator(".ork-race__head").count() == 1 and abs(row.locator(".ork-race__head").bounding_box()["height"] - 16) <= 1      # the seat's head in the foot, 16 px (spec 147 A.2: who works is on the card's face)
    assert abs(failed.locator(".corner--top .ork-sign").bounding_box()["width"] - 14) <= 1
    assert row.locator(".ork-gem").inner_text().strip() == "$1" and row.evaluate("e => e.lastElementChild.querySelector('.ork-gem') !== null")                      # a retry spends: the gem at the right
    assert "fails" in failed.get_attribute("class")                                                                      # a failure: orkUI's danger frame
    check = pg.locator('[data-lkey="t:task:recheck/c2"]')                                                                 # a failed check
    assert "fails" in check.get_attribute("class") and check.get_attribute("data-stage") == "checking" and check.locator(".ork-gem").count() == 0     # no gem: it is not a retry
    assert check.locator(".table-card__win .ork-sign.alert").count() == 1
    shot(pg, f"table-cards-{w}.png")


def test_a_goal_is_a_strip_over_its_cascade_the_front_by_the_rule_and_the_others_a_fan_behind_it(table):
    pg, host, w = table
    if not wide(w):
        assert pg.locator(".table-casc").count() == 0 and pg.locator(".table-gstrip").count() == 0 and pg.locator(".table-stack").count() >= 4      # a goal one token with its stack's edges
        return
    seat = pg.locator('.table-casc[data-goal="seat"]')
    assert keys(pg, '.table-casc[data-goal="seat"]') == ["t:task:seat/s1", "t:task:seat/s2"]                              # the fan first, the front last
    assert pg.locator('[data-lkey="t:task:seat/s1"]').evaluate("e => e.classList.contains('table-tedge')") and pg.locator('[data-lkey="t:task:seat/s2"]').evaluate("e => e.classList.contains('table-card')")
    assert keys(pg, '.table-casc[data-goal="recheck"]') == ["t:task:recheck/c1", "t:task:recheck/c2"]                    # a failed check is the front, before a task being done
    assert keys(pg, '.table-casc[data-goal="bar"]') == ["t:task:bar/a3", "t:task:bar/a1", "t:task:bar/a2"]               # Checking in front, then Doing, then Planning at the top
    bar = pg.locator('.table-casc[data-goal="bar"]')
    assert [e.get_attribute("data-stage") for e in bar.locator("[data-lkey]").all()] == ["planning", "doing", "checking"]
    assert bar.locator(".table-tedge").count() == 2 and bar.locator(".table-card").count() == 1 and bar.get_attribute("data-open") == "false"                  # collapsed: nothing is picked
    edge = pg.locator('[data-lkey="t:task:bar/a1"]')
    assert edge.locator(".ork-sign.sword").count() == 1 and edge.locator(".ork-sign").count() == 1 and edge.locator(".ork-elem.void.is-glowing").count() == 1     # the stage's small sign and, a task at work, the goal's rune glowing before it (spec 111 §3.1)
    assert pg.locator('[data-lkey="t:task:bar/a3"] .ork-elem').count() == 0 and pg.locator('[data-lkey="t:task:bar/a3"] .ork-sign.page').count() == 1                # a task that only asks has the sign and no flame
    assert edge.evaluate("e => getComputedStyle(e.querySelector('.table-fan__nm')).opacity") == "0" and edge.get_attribute("title") == "Draw the bar"       # no name at rest (it is the edge's label for a screen reader)
    assert "asks" in pg.locator('[data-lkey="t:task:bar/a3"]').get_attribute("class")                                    # a pick asked for: orkUI's alert frame
    gs = pg.locator('.table-lane[data-party="tech"] > .table-goal .table-gstrip')
    assert [g.get_attribute("data-goal") for g in gs.all()] == ["seat", "recheck", "calm"]                                # the hand's order: the failures first, a goal with nothing wrong last (though it is first on the Board)
    top = pg.locator('.table-lane[data-party="tech"] .table-goal').first
    assert abs(top.locator(".table-gstrip").bounding_box()["height"] - 22) <= 1 and top.locator(".table-gstrip .ork-elem.ice").count() == 1
    assert "Keep the seat" in top.locator(".table-gstrip").inner_text() and top.locator(".table-gstrip").evaluate("e => e.tagName") == "BUTTON"
    assert seat.locator(".table-tedge").count() == 1 and pg.locator(".table-tstrip").count() == 0                         # no strip of names
    shot(pg, f"table-cascade-{w}.png")
    open_fan(pg, "t:task:bar/a1")
    shot(pg, f"table-fan-open-{w}.png")


FLAME = ".ork-elem.is-glowing"
AT_WORK = ("r1", "k1", "s1", "c1", "a1", "a2")                                                                           # the tasks the stub has running or testing


def test_a_goals_rune_stands_once_on_its_strip_and_a_task_at_work_shows_the_flame_in_the_stages_place(table):
    pg, host, w = table
    if not wide(w):
        glowing = pg.locator('[data-lkey="t:task:rules/r1"]')                                                             # a lane a token wide: the token keeps its rune, glowing while its front task is at work
        assert glowing.locator(".ork-elem.meadow.is-glowing").count() == 1 and glowing.locator(".ork-elem").count() == 1
        assert pg.locator('[data-lkey="t:task:seat/s2"] .ork-elem.ice').count() == 1 and pg.locator('[data-lkey="t:task:seat/s2"] .is-glowing').count() == 0       # its front task failed: the rune is still
        assert anim(glowing.locator(".ork-elem"))[0] == ("none" if "is-still" in glowing.locator(".ork-elem").get_attribute("class") else "ork-glow") and glowing.locator(".table-card__win > *").evaluate_all("els => els.map((e) => getComputedStyle(e).animationName)") == ["none"]
        return
    assert pg.locator(".table-lane[data-party] .table-card__head .ork-elem, .table-lane[data-party] .table-tedge > .ork-elem:not(.is-glowing)").count() == 0       # no rune on a card's header or on an edge that does not work
    for slug in ("rules", "seat", "calm", "recheck", "bar"):
        assert pg.locator(f'.table-lane[data-party] .table-goal[data-goal="{slug}"] .table-gstrip .ork-elem').count() == 1, slug                  # the goal's one rune: its strip's
    r1 = pg.locator('[data-lkey="t:task:rules/r1"]')                                                                      # at work, the front card
    flame = r1.locator(".corner--top .ork-elem.meadow.is-glowing")
    assert flame.count() == 1 and r1.get_attribute("data-stage") == "doing"                                               # the flame is the top corner's rune, glowing (spec 147 A)
    assert flame.evaluate("e => e.offsetWidth") == 14 and flame.get_attribute("aria-hidden") == "true"
    moving = pg.locator(f".table-lane[data-party] {FLAME}").evaluate_all("els => els.filter((e) => getComputedStyle(e).animationName === 'ork-glow').map((e) => [getComputedStyle(e).animationDuration, getComputedStyle(e).animationTimingFunction])")
    assert len(moving) <= 1, moving                                                                                       # one place moves at a time (spec 140 C3): the others' flames stand, lit
    assert all(d == "2.4s" and t.startswith("steps(6") for d, t in moving), moving                                        # orkUI's glow: six steps over 2.4 s
    assert pg.locator('[data-lkey="t:task:bar/a2"] .corner--top .ork-elem.void.is-glowing').count() == 1                 # a task being checked is at work too
    edge = pg.locator('[data-lkey="t:task:seat/s1"]')                                                                     # at work, behind the front one: the rune glowing before the stage's sign
    assert edge.locator(".ork-elem.ice.is-glowing").count() == 1 and edge.locator(".ork-sign.sword").count() == 1 and edge.evaluate("e => e.firstElementChild.classList.contains('ork-elem')")
    for key in ("t:task:seat/s2", "t:task:recheck/c2", "t:task:bar/a3"):                                                  # failed, or asking: no flame (the rune stands, lit)
        assert pg.locator(f'[data-lkey="{key}"] .ork-elem.is-glowing').count() == 0, key
    assert pg.locator(f".table-lane[data-party] {FLAME}").count() == len(AT_WORK)                                          # as many flames as tasks at work
    assert anim(r1.locator(".table-card__win > *").first)[0] == "none" and anim(r1, "::after")[0] == "none"              # the card's own motion of before is gone (the tab's head step stays)
    pg.emulate_media(reduced_motion="reduce")                                                                             # under reduced motion the flame stands, at full strength
    assert anim(flame)[0] == "none" and flame.evaluate("e => getComputedStyle(e).opacity") == "1"
    pg.emulate_media(reduced_motion="no-preference")
    shot(pg, "table-flame-wide.png")
    for n in host.nodes:                                                                                                  # the task stops working: the flame goes, the sign comes back
        for t in n["tasks"]:
            if t["id"] == "r1":
                t["state"] = "failed"
    host.push()
    pg.locator('[data-lkey="t:task:rules/r1"][data-state="failed"]').wait_for(timeout=WAIT_MS)
    assert r1.locator(".ork-elem.is-glowing").count() == 0 and r1.locator(".corner--top .ork-elem").count() == 1


def test_a_goals_tasks_lie_as_a_fan_turned_one_to_three_degrees_by_their_place_and_a_hover_opens_it(table):
    pg, host, w = table
    if not wide(w):
        assert pg.locator(".table-fan").count() == 0                                                                      # a goal one token with its edges
        return
    turn = lambda key: pg.locator(f'[data-lkey="{key}"]').evaluate("e => { const m = new DOMMatrix(getComputedStyle(e).transform); return [Math.atan2(m.b, m.a) * 180 / Math.PI, m.e]; }")  # noqa: E731
    at_rest = {k: turn(k) for k in ("t:task:bar/a1", "t:task:bar/a3", "t:task:recheck/c1", "t:task:seat/s1")}              # bar: a2 in front, a1 behind it, a3 farthest
    for key, (deg, aside) in at_rest.items():
        assert 1 <= abs(deg) <= 3 and 2 <= abs(aside) <= 5, (key, deg, aside)                                             # turned 1° to 3°, moved a few px aside
    assert at_rest["t:task:seat/s1"] == at_rest["t:task:recheck/c1"] == at_rest["t:task:bar/a1"]                          # a fixed turn by the place from the front, never by the goal
    assert at_rest["t:task:bar/a1"][0] * at_rest["t:task:bar/a3"][0] < 0 and at_rest["t:task:bar/a1"][1] * at_rest["t:task:bar/a3"][1] < 0       # by turns left and right
    assert pg.locator('[data-lkey="t:task:seat/s2"]').evaluate("e => getComputedStyle(e).transform") in ("none", "matrix(1, 0, 0, 1, 0, 0)")      # the front card lies straight
    edge = pg.locator('[data-lkey="t:task:bar/a1"]')
    fan = pg.locator('.table-fan:has([data-lkey="t:task:bar/a1"])')
    closed = fan.bounding_box()["height"]
    open_fan(pg, "t:task:bar/a1")                                                                                         # a hover opens the fan a little
    assert fan.bounding_box()["height"] > closed + 10 and fan.bounding_box()["height"] < closed + 60
    assert edge.evaluate("e => getComputedStyle(e.querySelector('.table-fan__nm')).opacity") == "1" and "Draw the bar" in edge.inner_text()      # and the names are read
    assert turn("t:task:bar/a1") == at_rest["t:task:bar/a1"]                                                              # the turn is the same open
    pg.mouse.move(5, 5)
    pg.wait_for_function("(k) => getComputedStyle(document.querySelector(`[data-lkey=\"${k}\"] .table-fan__nm`)).opacity === '0'", arg="t:task:bar/a1", timeout=WAIT_MS)       # the pointer away: closed again
    edge.focus()                                                                                                         # the focus opens it too
    pg.wait_for_function("(k) => getComputedStyle(document.querySelector(`[data-lkey=\"${k}\"] .table-fan__nm`)).opacity === '1'", arg="t:task:bar/a1", timeout=WAIT_MS)
    pg.emulate_media(reduced_motion="reduce")
    assert turn("t:task:bar/a1") == at_rest["t:task:bar/a1"]                                                              # the turns are still under reduced motion
    assert pg.locator('.table-fan__slot').first.evaluate("e => getComputedStyle(e).transitionDuration") == "0s"          # and nothing glides
    pg.emulate_media(reduced_motion="no-preference")


def test_an_edge_lifts_its_task_and_a_goals_strip_picks_the_goal(table):
    pg, host, w = table
    if wide(w):
        edge_click(pg, "t:task:bar/a1")                                                                                   # a card behind the front one, pressed on its edge, lifts its task
        back = pg.locator(".table-back")
        back.wait_for(timeout=WAIT_MS)
        assert back.get_attribute("data-lifted") == "t:task:bar/a1" and "Draw the bar" in back.text_content()
        pg.keyboard.press("Escape")
        pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)
        assert title(pg) == ""  # no goal picked: the title says nothing (§247.5)
        pg.locator('.table-casc[data-goal="seat"]').locator("xpath=..").locator(".table-gstrip").click()                  # the strip of a goal picks it
        pg.wait_for_selector('.table-board--plan[data-plan="seat"]', timeout=WAIT_MS)                                       # the goal picked: the Board is its plan alone (spec 128 F.1; tests/test_plan_arrows_browser.py)
        assert title(pg) == "Keep the seat when a socket reconnects · through the Orkmaster"
        pg.keyboard.press("Escape")                                                                                       # and Esc puts it down (no cross in the title: spec 156 B.3)
        pg.wait_for_selector(".table-board:not(.table-board--plan)", timeout=WAIT_MS)
    else:
        pg.locator('[data-lkey="t:task:bar/a2"]').click()                                                                 # a token lifts its front task: a screen over the pane, its tasks listed
        back = pg.locator(".table-back.is-screen")
        back.wait_for(timeout=WAIT_MS)
        assert [b.get_attribute("data-task") for b in back.locator(".table-back__task").all()] == ["a1", "a3"]            # the goal's other tasks, the next in turn first
        back.locator('.table-back__task[data-task="a1"]').click()
        pg.wait_for_function("() => document.querySelector('.table-back').dataset.lifted === 't:task:bar/a1'", timeout=WAIT_MS)
        pg.get_by_role("button", name="Back").click()
        pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)


def test_a_goal_picked_unfolds_its_cascade_and_is_lit_in_both_its_lanes_the_others_stay_collapsed(table):
    pg, host, w = table
    assert pg.locator(".ork-picked").count() == 0
    pick(pg, "bar")                                                                                                       # in the first lane it is being joined, in Art's it is at work
    if wide(w):                                                                                                          # the Orkmaster's tab, a goal picked: its plan alone (spec 128 F.1: its tasks in their leaders' lanes, no strip, no fan; tests/test_plan_arrows_browser.py)
        pg.wait_for_selector('.table-board--plan[data-plan="bar"]', timeout=WAIT_MS)
        assert title(pg) == "A timer bar that drains · through the Orkmaster"
        assert pg.locator(".table .ork-picked").count() == 0 and pg.locator(".table-gstrip, .table-fan, .table-casc").count() == 0
        assert sorted(keys(pg, '.table-lane[data-party="art"]')) == ["t:task:bar/a1", "t:task:bar/a2", "t:task:bar/a3"]
        assert pg.locator('[data-lkey="t:task:bar/a1"] .corner--top .ork-sign.picture').count() == 1                     # a task of a kind of its own: its kind's sign in the top corner, not the goal's
        assert pg.locator('[data-lkey^="t:task:seat/"]').count() == 0                                                     # the other goals' tasks are not drawn
        shot(pg, f"table-picked-{w}.png")
        pick(pg, "")
        pg.wait_for_selector(".table-board:not(.table-board--plan)", timeout=WAIT_MS)
        return
    pg.wait_for_function("(n) => document.querySelectorAll('.table .ork-picked').length === n", arg=2, timeout=WAIT_MS)
    assert title(pg) == "A timer bar that drains · through the Orkmaster"
    lit = pg.locator(".table .ork-picked")
    assert [l.get_attribute("data-goal") for l in lit.all()] == ["bar", "bar"]                                          # its token in both lanes, lit alike
    assert pg.locator('.table-lane[data-party="art"] .ork-picked').count() == 1
    assert pg.locator('.table-lane[data-lane="first"] .ork-picked').count() == 1
    shot(pg, f"table-picked-{w}.png")
    pick(pg, "")
    pg.wait_for_function("() => document.querySelectorAll('.table .ork-picked').length === 0", timeout=WAIT_MS)


def test_the_first_lane_holds_what_is_the_whole_projects_the_goals_read_routed_and_joined_then_the_line(table):
    pg, host, w = table
    if wide(w):
        assert pg.locator(".table-lane--first").count() == 0 and pg.locator(".table-card--own").count() == 0       # the Orkmaster's goals are the column's at the wide width (spec 128 B; tests/test_column_browser.py)
        assert pg.locator('.frame-column .col-card[data-goal="timer"]').count() == 1 and pg.locator('.frame-column .col-card[data-goal="results"]').count() == 1
        return
    first = pg.locator('.table-lane[data-lane="first"]')
    assert keys(pg, '.table-lane[data-lane="first"]') == ["t:orc:timer", "t:orc:results", "t:orc:bar"]                      # what the Orkmaster does itself, in the Board's order
    assert [o.get_attribute("data-stage") for o in first.locator("[data-lkey]").all()] == ["reading", "routing", "joining"]
    if wide(w):
        words = [o.locator(".table-stage").inner_text().strip().lower() for o in first.locator(".table-card--own").all()]
        assert words == ["reading", "routing", "joining"]
        assert first.locator(".table-card--own .ork-race__head").count() == 0                                             # no crown: who works is not on a card of the Board
        goal = first.locator('.table-goal[data-goal="results"]')
        assert goal.locator(".table-gstrip").count() == 0 and goal.locator(".table-card--own").count() == 1               # a card a goal, no strip over it: the card is the goal's (spec 111 §3.1, decisions §187.1)
        own = goal.locator(".table-card--own .table-card__head")
        assert own.locator(".ork-elem.dust").count() == 1 and own.evaluate("e => e.firstElementChild.classList.contains('ork-elem')") and own.locator(".table-card__nm").inner_text().strip() == "Results screen with the round's best answer"     # its rune and its whole title
        assert goal.locator(".table-card__win .ork-sign.screen").count() == 1
        assert first.locator(".table-casc--line").count() == 1 and first.locator(".table-goal").last.bounding_box()["y"] < first.locator(".table-casc--line").bounding_box()["y"]       # the line last
    else:
        assert first.locator(".table-line-tokens").count() == 1 and first.locator(".table-token[data-lkey^='t:orc:']").count() == 3
    pg.locator('[data-lkey="t:orc:results"]').click()                                                                     # lifted: its own back
    pg.locator(".table-back").wait_for(timeout=WAIT_MS)
    assert "routing it" in pg.locator(".table-back").inner_text()
    pg.keyboard.press("Escape") if wide(w) else pg.get_by_role("button", name="Back").click()
    pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)


def open_fan(pg, key):
    """Hover the fan the card `key` lies on and wait for it to be open: the card's visible edge is then its top 30 px."""
    fan = pg.locator(f'.table-fan:has([data-lkey="{key}"])')
    fan.hover(position={"x": 70, "y": 3})
    pg.wait_for_function("(k) => { const f = document.querySelector(`.table-fan:has([data-lkey=\"${k}\"])`); return Math.abs(f.offsetHeight - parseFloat(getComputedStyle(f).getPropertyValue('--span'))) < 1; }", arg=key, timeout=WAIT_MS)
    pg.wait_for_timeout(300)                                                                                              # the slots have glided
    return fan


def edge_click(pg, key):
    """A press on the visible edge of a card behind the front one (the middle of its box lies under the cards in front)."""
    open_fan(pg, key)
    pg.locator(f'[data-lkey="{key}"]').click(position={"x": 40, "y": 8})


def line_slugs(pg):
    return [e.get_attribute("data-slug") for e in pg.locator(".table-lane[data-lane='first'] [data-line-item], .table-lane[data-lane='first'] .table-line-tokens .table-token[data-slug]").all()]


def test_the_line_is_the_first_lanes_last_cascade_in_the_orkmasters_order_with_the_moon_on_a_goal_that_waits(table):
    pg, host, w = table
    if wide(w):
        return                                                                                                            # at the wide width the line is the column's In analysis (spec 128 B.3; tests/test_column_browser.py)
    assert line_slugs(pg) == ["ln1", "ln2", "ln3"]                                                                    # a token a goal (no drag here: the list over the pane has its arrows)
    t2 = pg.locator('.table-line-tokens [data-slug="ln2"]')
    assert t2.locator(".ork-sign.moon").count() == 1 and t2.locator(".ork-sign.sound").count() == 1 and t2.locator(".ork-elem.ice").count() == 1
    t2.click()
    pg.wait_for_function("() => document.querySelector('.table-line-tokens [data-slug=\"ln2\"]').classList.contains('ork-picked')", timeout=WAIT_MS)
    pg.locator(".table-board").evaluate("e => { e.scrollTop = e.scrollHeight; }")
    shot(pg, f"table-line-{w}.png")


def test_a_goal_dragged_among_the_line_moves_with_ideas_move_and_a_drop_among_other_partys_goals_goes_back(lined):
    pg, host, w = lined
    pytest.skip("the line's drag lived in the first lane's cascade; at the wide width the column's In analysis has Next (spec 128 B.3, tests/test_column_browser.py), at the narrow a touch screen scrolls the lane and its moves are the list's arrows")


def test_past_seven_goals_all_search_opens_the_line_over_the_pane(crowded):
    pg, host, w = crowded
    if wide(w):
        return                                                                                                            # the column holds the line at the wide width (spec 128 B.3)
    items = line_slugs(pg)
    assert len(items) == 7 and set(items) == {"ln1", "ln2", "ln3", "ln4", "ln5", "ln6", "ln7"}                            # seven at most
    all_ = pg.locator(".table-lstrip--all, .table-token--all")
    assert all_.count() == 1 and "All · search" in (all_.get_attribute("title") or all_.inner_text())
    all_.click()
    pg.locator('.table-over[data-kind="line"] .table-line').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Board · In line" and pg.locator('[data-kind="line"][data-owner="table"]').count() == 1           # kind `line`, the table's own
    assert pg.locator(".table-line__row").count() == 9                                                                    # every goal in line
    search = pg.get_by_role("searchbox", name="Search the goals in line")
    search.fill("goal 8")
    assert pg.locator(".table-line__row").count() == 1 and "Goal 8 in line" in pg.locator(".table-line__row").inner_text()
    search.fill("")
    assert pg.locator('.table-line__row[data-slug="ln2"]').text_content().lower().count("waits for the reset") == 1 and pg.locator('.table-line__row[data-slug="ln2"] .ork-sign.moon').count() == 1
    host.log.clear()
    pg.get_by_role("button", name="Move later: Chat in the lobby").click()                                                # ln1 and ln4 are Tech's: the next of Tech's after it
    for _ in range(40):
        if any(n == "ideas.move" for n, _ in host.log):
            break
        pg.wait_for_timeout(50)
    assert [a for n, a in host.log if n == "ideas.move"] == [{"slug": "ln1", "before": "ln5"}]
    pg.locator('.table-line__row[data-slug="ln3"]').click()                                                               # a row picks its goal
    pg.wait_for_function("() => document.querySelector('.table-line__row[data-slug=\"ln3\"]').classList.contains('is-on')", timeout=WAIT_MS)
    pg.keyboard.press("Escape") if wide(w) else pg.locator(".table-title__back").click()                                  # back to the Board as it was
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    assert pg.locator(".ork-picked[data-slug='ln3']").count() == 1


def test_a_card_is_lifted_where_it_lies_and_turns_over_esc_or_a_press_away_lowers_it_one_at_a_time(table):
    pg, host, w = table
    seat, other = pg.locator('[data-lkey="t:task:seat/s2"]'), pg.locator('[data-lkey="t:task:rules/r1"]')
    seat.click()
    back = pg.locator(".table-back")
    back.wait_for(timeout=WAIT_MS)
    assert seat.get_attribute("aria-pressed") == "true" and back.get_attribute("data-lifted") == "t:task:seat/s2"
    assert "Reset the round timer when a player rejoins" in back.text_content() and "Brief" in back.text_content()
    pg.wait_for_function("() => document.querySelector('.table-back').innerText.includes('Keep a player')", timeout=WAIT_MS)
    assert ("ideas.task", {"slug": "seat", "task": "s2"}) in host.log                                                    # its brief, read when it is lifted
    assert [b.get_attribute("data-task") for b in back.locator(".table-back__task").all()] == ["s1"]                      # its goal's other tasks, each a press that lifts it
    if wide(w):
        b, c = back.bounding_box(), seat.bounding_box()
        assert abs(b["x"] - c["x"]) <= 8 and abs(b["y"] - c["y"]) <= 8                                                    # lifted where it lies (the card leans toward the pointer a little)
    else:
        assert back.bounding_box()["width"] >= 380 and "is-screen" in back.get_attribute("class")                         # a screen at the narrow width
    shot(pg, f"table-lifted-{w}.png")
    pg.keyboard.press("Escape")
    pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)
    assert seat.get_attribute("aria-pressed") == "false"
    seat.click()
    pg.locator(".table-back").wait_for(timeout=WAIT_MS)
    back.locator('.table-back__task[data-task="s1"]').click()                                                             # another task of the goal
    pg.wait_for_function("() => document.querySelectorAll('.table-back').length === 1 && document.querySelector('.table-back').dataset.lifted === 't:task:seat/s1'", timeout=WAIT_MS)
    if wide(w):
        pg.locator(".table-title").click()                                                                               # a press away
        pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)
        seat.click()
        other.click()                                                                                                    # another card: one at a time
        pg.wait_for_function("() => document.querySelectorAll('.table-back').length === 1 && document.querySelector('.table-back').dataset.lifted === 't:task:rules/r1'", timeout=WAIT_MS)
        pg.keyboard.press("Escape")
    else:
        pg.get_by_role("button", name="Back").click()
    pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)


def test_open_on_a_task_card_opens_its_log_or_its_task_over_the_pane_and_back_lights_the_card(table):
    pg, host, w = table
    failed = pg.locator('[data-lkey="t:task:seat/s2"]')
    failed.click()
    pg.locator(".table-back .table-back__open").click()                                                                  # a failure: its lines
    pg.locator('.table-over[data-kind="log"] .shell-logterm .xterm-rows').wait_for(timeout=WAIT_MS)                    # the log in a terminal's face (spec 168 I1)
    pg.wait_for_function("() => document.querySelector('.shell-logterm .xterm-rows')?.textContent.includes('tests: 3 failed')", timeout=WAIT_MS)
    assert title(pg) == "Board · Reset the round timer when a player rejoins"
    assert pg.locator(".table-board").count() == 0 and pg.locator(".table-back").count() == 0                          # the map is under it, not drawn
    pg.locator(".table-title__back").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    assert "is-lit" in pg.locator('[data-lkey="t:task:seat/s2"]').get_attribute("class")                                 # the card it came from lit
    pg.locator('[data-lkey="t:task:seat/s2"]').click()
    pg.locator('.table-back__task[data-task="s1"]').click()
    pg.locator(".table-back .table-back__open").click()
    pg.locator('.table-over[data-kind="task"] .shell-facts').wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)


def test_a_goal_picked_through_the_orkmasters_tab_is_its_plan_alone_at_the_wide_width_and_keeps_every_goal_on_the_board_at_the_narrow(table):
    pg, host, w = table
    cards = pg.locator("[data-lkey]").count()
    pick(pg, "seat")
    if wide(w):                                                                                                          # the wide width: its plan alone (spec 128 F.1)
        pg.wait_for_selector('.table-board--plan[data-plan="seat"]', timeout=WAIT_MS)
        assert title(pg) == "Keep the seat when a socket reconnects · through the Orkmaster"
        assert sorted(keys(pg, ".table-board--plan")) == ["t:task:seat/s1", "t:task:seat/s2"], "its tasks only: every other goal's are not drawn"
        pick(pg, "")
        pg.wait_for_selector(".table-board:not(.table-board--plan)", timeout=WAIT_MS)
        assert pg.locator("[data-lkey]").count() == cards
        return
    pg.wait_for_function("() => document.querySelector('.table-casc[data-goal=\"seat\"], .table-token[data-goal=\"seat\"]') !== null && document.querySelectorAll('.table .ork-picked').length === 1", timeout=WAIT_MS)
    assert title(pg) == "Keep the seat when a socket reconnects · through the Orkmaster"
    assert pg.locator("[data-lkey]").count() >= cards                                                                    # nothing is hidden for it (a picked goal's unfolded cascade only adds cards)
    pick(pg, "")
    pg.wait_for_function("() => document.querySelectorAll('.table .ork-picked').length === 0", timeout=WAIT_MS)


def pick(pg, slug):
    pg.evaluate("slug => import('/static/js/frame/state.js').then((m) => { m.picked.value = slug; })", slug)


# -- a party's tab -----------------------------------------------------------------------------------------------------------------------------------

def squad(pg, w):
    """Where the squad is (spec 168 E1): the narrow header's, or at the wide width the leader's inventory, opened from the pane title's … menu (*Seats and tools*)."""
    if not wide(w):
        return pg.locator('.table-head[data-party="tech"]')
    if not pg.locator(".stall-seats").count():
        pg.get_by_role("button", name="Tech's menu").click()
        pg.get_by_role("menuitem", name="Seats and tools").click()
        pg.locator(".stall-seats").wait_for(timeout=WAIT_MS)
    return pg.locator('.stall-seats[data-seats="tech"]')


def test_a_partys_header_is_one_row_of_its_squad_in_two_sides_with_a_role_under_each_head_and_a_seat_pressed_opens_its_popover(table):
    pg, host, w = table
    open_tab(pg, "tech")
    head = squad(pg, w)
    assert head.locator(".table-head__name, h2").count() == 0, "no party name in the row: the tab and the title say it"
    groups = head.locator(".table-group")
    assert [g.get_attribute("aria-label") for g in groups.all()] == ["Does", "Checks"] and "Leads" not in head.inner_text(), "no Leads: the leader sits at the table"
    assert [g.locator(".table-seat").count() for g in groups.all()] == [2, 1]
    sides = [g.locator(".table-side") for g in groups.all()]
    assert sides[0].locator(".ork-sign").count() == 1 and sides[1].locator(".ork-sign").count() == 1
    assert sides[0].get_attribute("title") == "Does on Claude" and sides[1].get_attribute("title") == "Checks on Claude", "the tool in the title, one tool for the whole side"
    assert "harness-claude-ink" in sides[0].locator(".ork-mark").get_attribute("src") and sides[0].locator(".table-side__w").text_content() == "Does"
    seat = head.locator('.table-seat[data-seat="grunt"]')
    assert "peon-warrior" in seat.locator(".ork-race__head").get_attribute("src") and seat.locator(".ork-mark").count() == 0, "its tool's mark is the side's: not on the seat"
    assert seat.locator(".table-seat__role").inner_text() == "Grunts" and seat.get_attribute("aria-label") == "Grunts, runs on Claude", "the role under the head, in the label with its tool"
    assert seat.locator(".ork-busy").count() == 1 and head.locator('.table-seat[data-seat="tester"] .ork-busy').count() == 0, "the busy mark on the one at work"
    role = seat.locator(".table-seat__role")
    assert role.evaluate("e => getComputedStyle(e).fontFamily").startswith("Rubik"), "the one face, Rubik (orkUI 0.40, decisions §291): the pixel face is gone"
    assert role.evaluate("e => getComputedStyle(e).color") != seat.evaluate("e => getComputedStyle(e).color"), "muted"
    assert role.evaluate("e => [getComputedStyle(e).textOverflow, getComputedStyle(e).maxWidth]") == ["ellipsis", "76px"]
    box, rbox = seat.locator(".ork-race__head").bounding_box(), role.bounding_box()
    assert rbox["y"] >= box["y"] + box["height"] - 1, "under the head"
    assert head.locator(".table-size").inner_text().strip() == "Standard"
    assert pg.get_by_role("button", name="Tech's menu").count() == 1
    shot(pg, f"table-tech-{w}.png")
    seat.click()
    pop = pg.locator(".table-seatpop")
    pop.wait_for(timeout=WAIT_MS)
    text = pop.inner_text()
    for word in ("Grunts", "Role", "What it does", "Its AI tool", "Its tier", "What it costs", "From the next task", "Set", "Take off the seat", "Open"):
        assert word in text, word
    assert not wide(w) or pop.bounding_box()["y"] >= head.bounding_box()["y"]
    if not wide(w):
        assert pop.bounding_box()["width"] >= 380                                                                        # a sheet at the narrow width
    said = " ".join(pop.locator(".table-seatpop__nm").text_content().split())
    assert said == "GruntsSeasoned · does" or said.endswith("Seasoned · does"), said                                      # its tier and its role, and no word of a race (spec 100 §0)
    assert not any(word in said.lower() for word in ("ork", "elf", "goblin", "gnome", "knight", "lich", "skeleton"))
    assert "ork" not in (seat.get_attribute("aria-label") or "").lower().replace("work", "")
    pg.get_by_role("button", name="Close", exact=True).click()
    assert pg.locator(".table-seatpop").count() == 0
    seat.click()
    pg.locator(".table-seatpop").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")                                                                                          # Esc closes it
    assert pg.locator(".table-seatpop").count() == 0
    seat.click()
    pg.locator(".table-seatpop").get_by_role("button", name="Open", exact=True).click()
    pg.locator('.table-over[data-kind="role"]').wait_for(timeout=WAIT_MS)                                                  # the role's text, over the pane
    assert title(pg) == ("Inventory · Grunts" if wide(w) else "Tech's table · Grunts") and "You are the Grunts." in pg.locator(".table-over").inner_text()
    pg.locator(".table-title__back").click()
    pg.locator(".table-head, .stall-seats").first.wait_for(timeout=WAIT_MS)


def test_a_side_with_seats_on_several_tools_has_no_tool_of_its_own_and_each_seat_shows_its_mark(table):
    pg, host, w = table
    tech = next(p for p in host.parties if p["slug"] == "tech")
    tech["tools"] = {"tester": "codex"}                                                                                   # one of Does' two seats runs on another tool
    host.push()
    open_tab(pg, "tech")
    does = squad(pg, w).locator('.table-group[data-band="build"]')
    does.locator(".table-seat").first.wait_for(timeout=WAIT_MS)
    pg.wait_for_function("() => document.querySelector('.table-group[data-band=build] .table-seat .ork-mark')", timeout=WAIT_MS)
    assert does.locator(".table-side .ork-mark").count() == 0 and does.locator(".table-side").get_attribute("title") == "Does"
    assert "harness-claude-ink" in does.locator('.table-seat[data-seat="grunt"] .ork-mark').get_attribute("src")
    assert "harness-codex-ink" in does.locator('.table-seat[data-seat="tester"] .ork-mark').get_attribute("src")
    assert does.locator('.table-seat[data-seat="tester"]').get_attribute("aria-label") == "Tester, runs on Codex"


def test_the_header_keeps_at_most_six_seats_and_never_the_leader(table):
    pg, host, w = table
    tech = next(p for p in host.parties if p["slug"] == "tech")
    extra = [{**tech["party"][1], "slug": f"more{i}", "name": f"More {i}", "band": "build" if i % 2 else "check"} for i in range(5)]
    tech["party"] = tech["party"] + extra
    tech["team"] = tech["team"] + [{"slug": e["slug"], "name": e["name"], "head": e["head"], "checks": e["band"] == "check", "every": False} for e in extra]
    host.push()
    open_tab(pg, "tech")
    squad(pg, w)
    pg.wait_for_function("() => document.querySelectorAll('.table-head .table-seat, .stall-seats .table-seat').length > 4", timeout=WAIT_MS)
    seats = squad(pg, w).locator(".table-seat")
    assert seats.count() == 6 and squad(pg, w).locator('.table-seat[data-band="lead"]').count() == 0
    narrow.no_sideways(pg)


def test_at_the_narrow_width_the_sides_words_go_and_their_signs_stay_every_seat_44_px(table):
    pg, host, w = table
    open_tab(pg, "tech")
    head = squad(pg, w)
    head.locator(".table-seat").first.wait_for(timeout=WAIT_MS)
    words = head.locator(".table-side__w")
    assert all(x.is_visible() == wide(w) for x in words.all()), "the words are there at the wide width only"
    assert all(x.locator(".ork-sign").is_visible() for x in head.locator(".table-side").all()) and head.locator(".table-side").first.get_attribute("title") == "Does on Claude"
    if not wide(w):
        assert all(x.bounding_box()["width"] >= 43.5 and x.bounding_box()["height"] >= 43.5 for x in head.locator(".table-seat").all())
    box, row = head.bounding_box(), head.locator(".table-group").first.bounding_box()
    assert box["height"] < 130 and row["y"] >= box["y"]
    shot(pg, f"table-header-{w}.png")


def test_a_seat_can_be_taken_off_and_its_tool_set_with_undo(table):
    pg, host, w = table
    open_tab(pg, "tech")
    squad(pg, w)
    pg.locator('.table-seat[data-seat="tester"]').click()
    pop = pg.locator(".table-seatpop")
    pop.get_by_role("button", name="Take off the seat").click()
    for _ in range(40):
        if any(n == "ideas.goal_save" for n, _ in host.log):
            break
        pg.wait_for_timeout(50)
    saved = [a for n, a in host.log if n == "ideas.goal_save"][-1]
    assert saved["slug"] == "tech" and saved["team"] == ["grunt", "reviewer"]                                              # the party works on without it
    assert pg.locator(".table-seatpop").count() == 0


def test_a_party_menu_has_edit_at_that_party_and_remove_party_over_the_pane(table):
    pg, host, w = table
    open_tab(pg, "art")
    assert pg.locator(".table-sys, .table-board").count() == 0                                                           # another party than Tech: its header alone (no map yet)
    pg.get_by_role("button", name="Art's menu").click()
    assert [i.inner_text().strip() for i in pg.get_by_role("menuitem").all()] == (["Edit", "Seats and tools", "Remove party"] if wide(w) else ["Edit", "Remove party"])
    pg.get_by_role("menuitem", name="Edit").click()
    pg.locator('.table-over[data-kind="parties"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Art's table · Parties" and pg.locator('.table-over[data-kind="parties"]').get_attribute("data-owner") == "table"       # the one place of the parties, not today's form
    assert pg.get_by_role("button", name="Save party").count() == 0 and pg.locator(".place").count() == 0
    pg.get_by_role("button", name="Back").click()
    pg.locator(".table-head").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Art's menu").click()
    pg.get_by_role("menuitem", name="Remove party").click()                                                              # the question of a party removed, in the pane too
    pg.locator(".place__text").wait_for(timeout=WAIT_MS)
    assert "Art has 1 goal" in pg.locator(".place__text").text_content()
    assert pg.locator(".shell-backdrop").count() == 0
    pg.keyboard.press("Escape")
    pg.locator(".table-head").wait_for(timeout=WAIT_MS)


# -- Tech's System -----------------------------------------------------------------------------------------------------------------------------------

def test_techs_tab_is_its_header_and_the_system_and_a_part_pressed_is_lifted_and_opens_a_file(table):
    pg, host, w = table
    open_tab(pg, "tech")
    pg.locator(".table-sys .sys[data-state=shown]").wait_for(timeout=WAIT_MS)
    assert pg.locator(".sys-tabs").count() == 0                                                                          # one map a tab: no Feature modules
    assert [c.get_attribute("data-container") for c in pg.locator(".arch-col").all()] == ["server", "client"]
    part = pg.locator(f'.sys-part[data-part="{FILE}"]')
    part.scroll_into_view_if_needed()
    part.click()
    back = pg.locator(".table-back")
    back.wait_for(timeout=WAIT_MS)
    assert back.get_attribute("data-lifted") == f"t:part:tech:{FILE}"
    back.locator(".sys-side[data-path]").wait_for(timeout=WAIT_MS)
    assert all(word in back.text_content() for word in ("Files", "Uses", "Used by")) or all(word.lower() in back.text_content().lower() for word in ("files", "uses", "used by"))                                         # today's part pane, on the back
    assert pg.locator(".shell-drawer").count() == 0
    shot(pg, f"table-system-lifted-{w}.png")
    back.get_by_role("button", name="Open").click()
    pg.locator('.table-over[data-kind="file"] .shell-code').wait_for(timeout=WAIT_MS)
    assert title(pg) == f"Tech's table · {FILE}" and "line 3" in pg.locator(".shell-code").inner_text()                        # a file over the pane, its title says where it came from
    assert pg.locator(".table-sys").count() == 0 and pg.locator(".table-head").count() == 0                              # the map is under it
    shot(pg, f"table-file-{w}.png")
    pg.locator(".table-title__back").click()
    pg.locator(f'.table-sys .sys-part[data-part="{FILE}"].is-lit').wait_for(timeout=WAIT_MS)                              # the card it came from, lit
    pg.keyboard.press("Escape")
    assert pg.locator(".table-head").count() == 1
    part.click()
    back.wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)


def test_a_link_between_two_containers_is_lifted_with_its_routes_too(table):
    pg, host, w = table
    open_tab(pg, "tech")
    link = pg.locator(".table-sys .arch-link").first
    link.wait_for(timeout=WAIT_MS)
    link.click()
    back = pg.locator(".table-back")
    back.wait_for(timeout=WAIT_MS)
    back.locator(".arch-side").wait_for(timeout=WAIT_MS)
    assert "/rooms" in back.inner_text()
    pg.keyboard.press("Escape")


def test_esc_goes_back_from_a_file_and_the_browsers_back_does_at_the_narrow_width(table):
    pg, host, w = table
    pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openOver('file', {path: 'README.md'}, {title: 'Board', key: ''}, 'README.md'))")
    pg.locator(".table-over .shell-code").wait_for(timeout=WAIT_MS)
    if wide(w):
        pg.keyboard.press("Escape")
    else:
        pg.go_back()                                                                                                     # ← the browser's back
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-over").count() == 0


def test_with_many_parties_the_tabs_keep_their_heads_and_the_board_lays_tokens(gui):
    server, browser = gui
    host = TableHost(crowd=5)
    pg = narrow.page(browser, "wide")
    errors: list[str] = []
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").nth(8).wait_for(timeout=WAIT_MS)
    pg.wait_for_selector('.table[data-compact="true"]', timeout=WAIT_MS)
    assert tab(pg, "tech").locator(".table-tab__txt").is_hidden() and tab(pg, "tech").get_attribute("aria-label") == "Tech · Does on Claude · Checks on Codex"           # more than fit: the heads alone, the words said
    assert pg.locator('.table-board[data-tokens="true"]').count() == 1
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- the sword and shield on a tab (spec 111 §3.4, decisions §189) ----------------------------------------------------------------------------------------------

def marks_of(pg, slug):
    """What a tab's second line holds, in order: `sword`, a tool, `shield`, a tool (or the faint shield with none), as `[kind, tool]`."""
    return pg.locator(f'.table-tab[data-tab="{slug}"] .table-tab__marks').evaluate("""e => [...e.children].filter((c) => !c.classList.contains('table-tab__gap')).map((c) =>
        c.classList.contains('ork-sign') ? [[...c.classList].find((k) => k === 'sword' || k === 'shield'), ''] : c.classList.contains('table-tab__off') ? ['off', c.firstElementChild.classList.contains('shield') ? 'shield' : '']
        : c.classList.contains('table-tab__more') ? ['more', ''] : ['tool', c.dataset.tool])""")


def test_a_tab_has_a_second_line_the_sword_and_the_tool_its_does_run_on_the_shield_and_the_tool_its_checks_run_on(table):
    pg, host, w = table
    if not wide(w):
        assert tab(pg, "tech").locator(".table-tab__marks").is_hidden() and tab(pg, "tech").locator(".table-tab__txt").is_hidden()      # a row of heads: no second line
        assert "Does on Claude · Checks on Codex" in tab(pg, "tech").get_attribute("title")                              # its words are still said
        return
    assert tab(pg, "game").locator(".table-tab__marks").count() == 0                                                      # Does and Checks on the project's default tool (Claude): no second line (decisions §247.7)
    assert marks_of(pg, "tech") == [["shield", ""], ["tool", "codex"]]                                                    # only the side on another tool is drawn: its Checks run on Codex
    assert pg.locator('.col-head__tab .table-tab__marks').count() == 0                                                    # the Orkmaster's tab is the column's head: no sword and shield (the project's tool is the hand's potions)
    assert marks_of(pg, "art") == [["off", "shield"]]                                                                     # Lean: the shield faint, no mark (its Does is on the default: not drawn)
    assert marks_of(pg, "release") == [["sword", ""], ["tool", "codex"], ["more", ""]]                                    # a dot: one of its roles runs on another tool; its Checks on the default are not drawn
    assert tab(pg, "art").locator(".table-tab__off").evaluate("e => getComputedStyle(e).opacity") == "0.35"
    assert tab(pg, "tech").get_attribute("title") == "Tech · Does on Claude · Checks on Codex"                           # the words say both sides
    assert tab(pg, "game").get_attribute("title").endswith("Does on Claude · Checks on Claude")
    assert tab(pg, "art").get_attribute("aria-label") == "Art · Does on Claude · no separate check"
    assert tab(pg, "release").get_attribute("aria-label") == "Release · Does on Codex and others · Checks on Claude"
    line = tab(pg, "tech").locator(".table-tab__marks")
    assert line.get_attribute("aria-hidden") == "true"                                                                    # the words are the tab's label, the marks are drawn
    assert all(abs(b["width"] - 14) <= 1 and abs(b["height"] - 14) <= 1 for b in (e.bounding_box() for e in line.locator(".ork-sign, img").all()))        # 14 px, as the signs' small size
    head, name, tb = tab(pg, "tech").bounding_box(), tab(pg, "tech").locator(".table-tab__main").bounding_box(), line.bounding_box()
    assert head["height"] >= 60 and tb["y"] >= name["y"] + name["height"] - 1 and tb["y"] + tb["height"] <= head["y"] + head["height"] and abs(tb["x"] - name["x"]) <= 1      # under the name, inside the tab (the row is as high as the open head: spec 123 §7.1)
    ink = lambda slug, i: tab(pg, slug).locator(".table-tab__marks img").nth(i).get_attribute("src")                          # noqa: E731
    gone = lambda slug: tab(pg, slug).locator(".table-tab__marks img").count() == 0                                           # noqa: E731
    assert ink("tech", 0).endswith("/marks/harness-codex-ink.png")                                                          # in ink
    assert tab(pg, "tech").locator(".table-tab__marks img").first.get_attribute("srcset").endswith("harness-codex-ink@2x.png 2x")
    open_tab(pg, "tech")
    assert ink("tech", 0).endswith("/marks/harness-codex.png")                                                              # Tech is open: its mark in colour
    assert gone("orkmaster") and gone("game") and ink("release", 0).endswith("/marks/harness-codex-ink.png")                 # and the others back in ink
    shot(pg, "table-tabs-marks-wide.png")


def test_a_potion_hovered_or_focused_lights_the_tabs_of_the_parties_that_run_on_its_tool_and_says_who_drinks_from_it(table):
    pg, host, w = table
    if not wide(w):
        pytest.skip("the potions lie in the hand at the wide width; the narrow width's tabs are heads only")
    lit = lambda: sorted(pg.locator(".table-tab.is-lit").evaluate_all("els => els.map((e) => e.dataset.tab)"))        # noqa: E731
    assert lit() == [] and pg.locator(".table-tab .is-marked").count() == 0
    claude, codex = pg.locator('.hand-pot[data-provider="claude"]'), pg.locator('.hand-pot[data-provider="codex"]')
    narrow.unroll_drum(pg)
    claude.hover()
    pg.wait_for_function("() => document.querySelectorAll('.table-tab.is-lit').length > 0", timeout=WAIT_MS)
    assert lit() == ["art", "game", "release", "tech"]                                                                    # every party that does or checks on Claude (marks drawn or not), none of Codex's alone
    assert pg.locator('.table-tab[data-tab="game"]').evaluate("e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).backgroundColor]")[0] == "none"      # lit as a tab hovered is, not by a 1 px outline
    pg.mouse.move(5, 300)
    pg.wait_for_function("() => document.querySelectorAll('.table-tab.is-lit').length === 0", timeout=WAIT_MS)
    pg.locator(".pots__row .pot-s").first.focus()                                                                                   # the focus unrolls the row, and lights too
    pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)
    codex.focus()
    pg.wait_for_function("() => document.querySelectorAll('.table-tab.is-lit').length > 0", timeout=WAIT_MS)
    assert lit() == ["release", "tech"]
    pg.evaluate("() => document.activeElement.blur()")
    pg.wait_for_function("() => document.querySelectorAll('.table-tab.is-lit').length === 0", timeout=WAIT_MS)
    assert claude.get_attribute("aria-label").endswith(". 3 parties do on it, 2 parties check on it")                       # the parties that do and check on it: Lean checks on none
    assert codex.get_attribute("aria-label") == "Codex: 18% of the day left. 1 party does on it, 1 party checks on it" and codex.get_attribute("title") == codex.get_attribute("aria-label")
    narrow.unroll_drum(pg)
    claude.hover()
    pg.wait_for_function("() => document.querySelectorAll('.table-tab.is-lit').length > 0", timeout=WAIT_MS)
    shot(pg, "table-potion-marks-wide.png")


# -- a goal picked, the project, the keys, the motion, the presses ------------------------------------------------------------------------------------

def on_route_tabs(pg):
    """The party tabs that are not grey (spec 156 B.5): the ones the picked goal's route passes."""
    return sorted(t.get_attribute("data-tab") for t in pg.locator(".table-tab:not(.is-off)").all() if t.get_attribute("data-tab") not in ("orkmaster", "release", "live"))


def test_a_goal_picked_greys_the_tabs_its_route_does_not_pass_and_opens_the_orkmasters_tab_when_the_open_one_is_grey(table):
    pg, host, w = table
    assert pg.locator(".table-tab.is-off, .table-tab__dot").count() == 0                                                 # nothing picked: no tab is grey
    pick(pg, "seat")
    pg.locator(".table-tab.is-off").first.wait_for(timeout=WAIT_MS)
    assert on_route_tabs(pg) == ["art", "tech"]                                                                          # its party's and the party the route passed
    pick(pg, "")
    open_tab(pg, "game")
    pick(pg, "seat")                                                                                                     # picked in the hand, a grey party's tab open: the Orkmaster's tab opens
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"
    pick(pg, "")
    pick(pg, "seat")
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"                                                 # the Orkmaster's tab stays: its Board shows the tasks alone


# -- a goal on its way: the phase marks in the title, the route's dots on the tabs (spec 100 §5, spec 95 §3.6) -------------------------------------------------

TALK_READ = {"idea": "seat", "mode": "talk", "round": 1, "done": True, "cause": None, "stances": [
    {"party": "game", "leader": "Game lead", "stance": "One clock on every phone", "for": "Nobody argues about the time", "against": "A phone offline shows a stale time",
     "questions": [{"id": "q1", "q": "Where does the timer run?", "choices": ["Server counts", "Each phone counts"], "pick": 0, "why": "One clock.", "project": False, "state": "answered", "answer": "Server counts", "round": 1, "how": "pick"}]},
    {"party": "tech", "leader": "Architect", "stance": "The server owns the clock", "for": "One place to reset", "against": "Every round trip adds delay", "questions": []}]}
SPEC_PAGE = [{"name": "Gist", "text": "Keep the seat."}, {"name": "Route", "text": "Game design, then Tech"},
             {"name": "Game design", "text": "### Done when\n- The timer shows\n\n### Will be\n- new timer-bar"}, {"name": "Tech", "text": "### Done when\n- The seat is kept\n\n### Will be\n- changed server/lobby.ts"}]
ROUTE_ROW = {"kind": "route", "goal": "tech", "idea": "seat", "title": "Keep the seat when a socket reconnects", "text": "Route: Game design, then Tech", "at": "2026-10-28T09:00:00", "priority": "normal", "blocks": False,
             "route": [{"party": "game", "leader": "designer", "head": LEADS["game"]}, {"party": "tech", "leader": "architect", "head": LEADS["tech"]}], "cost": {"calls": 6, "usd_low": 0.2, "usd_high": 0.6},
             "place": 1, "short": False, "reproduces": False, "low": False, "offer": [], "type": "feature"}
TALK_ROW = {"kind": "talk", "goal": "tech", "idea": "seat", "title": "Keep the seat when a socket reconnects", "text": "", "at": "2026-10-28T09:00:00", "priority": "normal", "blocks": False, "questions": [],
            "stances": [{"party": "art", "leader": "Art lead", "stance": "The seat shows its owner", "for": "", "against": ""}, {"party": "tech", "leader": "Architect", "stance": "Keep it on the server", "for": "", "against": ""}]}


class WayHost(TableHost):
    """The table's host with the goal `seat` on its way: its state (`routed`, `talk`, `decided`, `sections`, `plan`, `working`, `done`), the rows that wait (`needs`), the Talk as kept and the goal's Spec."""

    def __init__(self, state="working", needs=(), route=None):
        super().__init__(rich=False, line=0)
        seat = next(n for n in self.nodes if n["slug"] == "seat")
        seat["state"] = state
        if route is not None:
            seat["route"] = route
        self.needs = list(needs)

    def handle(self, name, a):
        if name == "ideas.talk_read":
            self.log.append((name, a))
            return copy.deepcopy(TALK_READ)
        if name == "ideas.page":
            self.log.append((name, a))
            return {"slug": a["slug"], "title": "Keep the seat when a socket reconnects", "sections": SPEC_PAGE, "state": "sections", "track": "tech"}
        return super().handle(name, a)


def way(gui, width, errors, **kw):
    """The window at `width` against a WayHost: `(page, host)`."""
    server, browser = gui
    host = WayHost(**kw)
    pg = narrow.page(browser, width)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token, .hand-card").first.wait_for(timeout=WAIT_MS)
    return pg, host


def marks(pg):
    return [(m.get_attribute("data-phase"), m.evaluate("e => e.tagName") == "BUTTON", m.get_attribute("aria-current") == "step") for m in pg.locator(".table-phase").all()]


@pytest.fixture(params=narrow.WIDTHS)
def onway(gui, request):
    """A goal at *Work*, the window at one of the two widths."""
    errors: list[str] = []
    pg, host = way(gui, request.param, errors)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_goal_picked_has_its_phase_marks_in_the_title_spans_the_current_one_marked_and_nothing_opens_over_the_pane(onway):
    pg, host, w = onway
    assert pg.locator(".table-phases").count() == 0                                                                      # nothing picked: no marks
    pick(pg, "seat")
    pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
    assert [m.text_content().strip() for m in pg.locator(".table-phase").all()] == ["Talk", "Spec", "Work", "Done"]
    assert marks(pg) == [("talk", False, False), ("spec", False, False), ("work", False, True), ("done", False, False)]  # Work is now; spans all (spec 156 C.2), no button
    assert pg.locator("button[data-phase]").count() == 0 and pg.locator(".table-phase.is-past").count() == 2
    assert title(pg) == "Keep the seat when a socket reconnects · through the Orkmaster"                                  # the title still says what and through whom
    shot(pg, f"table-phases-{w}.png")
    pg.locator('.table-phase[data-phase="talk"]').click(force=True)
    assert pg.locator(".table-over").count() == 0 and pg.locator(".table-phases").count() == 1
    pick(pg, "")
    pg.wait_for_function("() => document.querySelectorAll('.table-phases').length === 0", timeout=WAIT_MS)


@pytest.mark.parametrize("state,now,pages", [("routed", "talk", []), ("talk", "talk", []), ("decided", "spec", []), ("sections", "spec", []), ("plan", "work", []), ("done", "done", [])])
def test_the_current_phase_follows_the_goals_state(gui, state, now, pages):
    errors: list[str] = []
    pg, host = way(gui, "wide", errors, state=state)
    pick(pg, "seat")
    pg.locator(".table-phases").wait_for(timeout=WAIT_MS)
    got = marks(pg)
    assert [p for p, _b, cur in got if cur] == [now] and [p for p, button, _c in got if button] == pages
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_a_goal_not_routed_yet_has_no_marks(gui):
    errors: list[str] = []
    pg, host = way(gui, "wide", errors, state="reading")
    pick(pg, "seat")
    pg.wait_for_timeout(200)
    assert pg.locator(".table-phases").count() == 0
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_the_route_of_a_goal_picked_leaves_the_tab_of_each_party_it_passes_not_grey(gui, width):
    errors: list[str] = []
    for state, needs, route, dots in (("routed", [ROUTE_ROW], [], ["game", "tech"]),                                     # the route row's steps (its own party always)
                                      ("talk", [TALK_ROW], [], ["tech", "art"]),                                         # the stances of the Talk
                                      ("working", [], [{"step": "party", "party": "game", "goal": "seat"}, {"step": "party", "party": "tech", "goal": "seat"}], ["game", "tech"])):   # the route as planned
        pg, host = way(gui, width, errors, state=state, needs=needs, route=route)
        assert pg.locator(".table-tab.is-off").count() == 0
        pick(pg, "seat")
        pg.locator(".table-tab.is-off").first.wait_for(timeout=WAIT_MS)
        assert on_route_tabs(pg) == sorted(dots), state                                                                  # the tabs not grey are the route's
        if state == "routed":
            shot(pg, f"table-route-dots-{width}.png")
        narrow.no_sideways(pg)
        pg.context.close()
    assert not errors, "\n".join(errors)


def test_ctrl_o_opens_a_project_in_the_pane_and_another_project_is_shown_from_its_list(table):
    pg, host, w = table
    pg.keyboard.press("Control+o")
    pg.locator('.table-over[data-kind="projects"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Projects" and pg.locator(".table-projects__one").count() == 3                                  # Ctrl+O opens the projects over the pane
    pg.get_by_role("button", name="Open a project…").click()
    pg.locator('.table-over--form[data-kind="projects"]').wait_for(timeout=WAIT_MS)
    assert pg.locator("#open-folder-form").count() == 1 and title(pg) == "Open a project…"
    assert pg.locator(".shell-backdrop").count() == 0 and pg.locator("[aria-modal]").count() == 0                       # in the pane, not over the page
    pg.get_by_role("button", name="Cancel").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Switch project").click()
    pg.locator('.table-projects__one[data-path="/work/other"]').click()
    for _ in range(40):
        if ("projects.use", {"path": "/work/other"}) in host.log:
            break
        pg.wait_for_timeout(50)
    assert ("projects.use", {"path": "/work/other"}) in host.log
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)                                                                 # another project: the map again, nothing open
    assert tab(pg, "orkmaster").get_attribute("aria-label") == ("The Orkmaster · other" if wide(w) else "other · Does on Claude · Checks on Claude")


def test_nothing_moves_under_reduced_motion_and_a_card_turns_on_orkuis_tokens_otherwise(table):
    pg, host, w = table
    seat = pg.locator('[data-lkey="t:task:seat/s2"]')
    seat.click()
    back = pg.locator(".table-back")
    back.wait_for(timeout=WAIT_MS)
    assert back.evaluate("e => getComputedStyle(e).animationName") == "table-turn"
    assert back.evaluate("e => getComputedStyle(e).animationDuration") == "0.25s"                                       # orkUI's sure token
    pg.keyboard.press("Escape")
    pg.emulate_media(reduced_motion="reduce")
    seat.click()
    pg.locator(".table-back").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-back").evaluate("e => getComputedStyle(e).animationName") == "none"
    assert seat.evaluate("e => getComputedStyle(e).transform") in ("none", "matrix(1, 0, 0, 1, 0, 0)")                   # a card at rest is flat, and lifted too
    if wide(w):
        assert pg.locator('[data-lkey="t:task:seat/s1"]').evaluate("e => getComputedStyle(e).transform") not in ("none", "matrix(1, 0, 0, 1, 0, 0)")      # a card of the fan stays turned (a turn is not a motion)
    pg.emulate_media(reduced_motion="no-preference")


def test_every_press_is_44_by_44_on_a_touch_screen_and_nothing_is_said_only_on_hover(gui):
    # Since spec 103 A / decisions §180 a touch window under 760 px is the phone's hand, never the table; a touch screen that
    # shows the table is a tablet's (800 px wide here), and the rule (`pointer: coarse`, spec 94 §1.3) is the same.
    server, browser = gui
    errors: list[str] = []
    host = TableHost()
    pg = browser.new_context(viewport={"width": 800, "height": 700}, has_touch=True).new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    open_tab(pg, "tech")
    squad(pg, "wide")                                                                                                    # 800 px is the wide width: the seats lie in the leader's inventory (spec 168 E1)
    pg.locator('.table-seat[data-seat="grunt"]').wait_for(timeout=WAIT_MS)
    for sel in (".table-tab", ".table-chair", ".hand-die", ".table-menu__btn", ".table-seat", ".table-switch"):
        for el in pg.locator(sel).all():
            box = el.bounding_box()
            assert box["width"] >= 43.5 and box["height"] >= 43.5, (sel, box)
    for el in pg.locator(".table-tab").all():
        assert el.get_attribute("aria-label") and el.get_attribute("title")                                              # a tab's name is its label too, not only a tooltip
    pg.locator('.table-tab[data-tab="art"]').dispatch_event("pointerdown", {"pointerType": "touch"})                     # a long press says the name
    pg.locator(".gui-toast").wait_for(timeout=WAIT_MS)
    assert "Art" in pg.locator(".gui-toast").text_content()
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- spec 130 C.5–C.6: nothing of the table lies beside a form; the window not yet laid, and the laying (decisions §232.1, §232.2, §247.1) -----------------------------------------

def test_a_form_over_the_pane_keeps_the_discards_column_and_the_hand(gui):
    from tests.test_discard_table_browser import open_maps
    pg, host, log = open_maps(gui, "wide")
    try:
        pg.locator(".release-lane .post-card").first.wait_for(timeout=WAIT_MS)
        pg.get_by_role("button", name="The Orkmaster's menu").click()
        pg.get_by_role("menuitem", name="Settings").click()
        pg.locator('.table-over[data-kind="settings"]').wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-end").count() == 0 and pg.locator(".release-lane").count() == 1 and pg.locator('.table-body[data-end="form"]').count() == 1, "the discard's column stays beside a form (spec 168 A3, decisions §283.5)"
        assert pg.locator(".hand-end > .hand-die").count() == 1 and pg.locator(".release-lane__head .pots").count() == 1, "the die stays in the hand, the potions in the column's head"
        assert pg.locator(".frame-column").count() == 1 and pg.locator(".hand-plus").count() == 1
        pg.keyboard.press("Escape")
        pg.locator(".release-lane .post-card").first.wait_for(timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def unlaid(desk, tmp_path, hand=("claude",), **more):
    from orkboard.realm import project_kind
    from tests.first_open_kit import git_repo
    from tests.test_add_tool_browser import fill_hand
    d = desk(git_repo(tmp_path / "skyhop", "project.godot", "[application]\n"), **more)
    project_kind.keep(d.host.ideas.state_dir, "game")
    fill_hand(d.host, *hand)
    return d


def test_the_window_not_yet_laid_holds_the_orkmaster_alone(desk, tmp_path):
    d = unlaid(desk, tmp_path)
    pg = d.open()
    pg.locator('.frame[data-laid="0"][data-room="1"]').wait_for(timeout=WAIT_MS)                # the first open's room (spec 150 G): the Orkmaster alone, the places its cards have laid
    pg.locator(".fo-bubble").wait_for(timeout=WAIT_MS)
    assert pg.locator(".col-head__tab, .table-tabcell, .frame-table, .frame-hand").count() == 0, "no tabs, no table's pane, no hand"
    assert pg.locator(".table-chair, .table-door, .hand-die, .ork-die, .hand-plus, .col-scroll, .col-sec, .table-end").count() == 0, "no empty chair, door, die, + card or piles"
    assert pg.locator('[data-place="potions"] .hand-pot').count() >= 1 and pg.locator("[data-empty-slot]").count() == 1, "the AI tools at the edge's foot"
    assert not d.errors, d.errors


def test_settings_stays_reachable_before_start_over_the_whole_table(desk, tmp_path):
    d = unlaid(desk, tmp_path)
    pg = d.open()
    pg.locator('[data-setup="parties"]').wait_for(timeout=WAIT_MS)                              # the room's table (spec 150 G)
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    pg.get_by_role("menuitem", name="Settings").click()
    pg.locator('.table-over[data-kind="settings"]').wait_for(timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_start_lays_the_table_in_order_and_says_so_and_the_ring_waits_for_its_first_content(desk, tmp_path):
    d = unlaid(desk, tmp_path)
    pg = d.open()
    pg.locator('[data-place="table"] .fo-chair').first.click()                                    # a chair pressed seats its leader (spec 150 G.2.3)
    pg.locator('[data-act="start"]:not([disabled])').click()
    pg.locator(".frame[data-laying] .table-tabcell").first.wait_for(timeout=WAIT_MS)
    delays = pg.evaluate("""() => { const ms = (s) => parseFloat(getComputedStyle(document.querySelector(s)).animationDelay) * 1000; return { tab: ms('.table-tabcell'), chair: ms('.table-chair'), die: ms('.hand-end > .hand-die'), plus: ms('.hand-slot.is-plus') }; }""")
    assert delays["tab"] < delays["chair"] < delays["die"] < delays["plus"], delays
    pg.locator(".hand-field [data-first-lit]").wait_for(timeout=WAIT_MS)                       # the + card's card is open, its first corner lit (spec 150 G.2.4): no tour
    assert pg.locator(".table-end, .ork-card-place, .release-lane .post-card").count() == 0, "§247.1: no pile and no dashed place before the first content (Release's lane is there, empty)"
    pg.locator('.frame:not([data-laying])').wait_for(timeout=WAIT_MS)
    pg.locator(".fo-bubble").wait_for(state="detached", timeout=WAIT_MS)
    assert not d.errors, d.errors


def test_under_reduced_motion_the_table_is_laid_all_at_once(desk, tmp_path):
    d = unlaid(desk, tmp_path)
    pg = d.pg
    pg.emulate_media(reduced_motion="reduce")
    d.open()
    pg.locator('[data-place="table"] .fo-chair').first.click()
    pg.locator('[data-act="start"]:not([disabled])').click()
    pg.locator(".table-tabcell").first.wait_for(timeout=WAIT_MS)
    pg.locator(".hand-field").wait_for(timeout=WAIT_MS)
    assert pg.locator(".frame[data-laying]").count() == 0
    assert not d.errors, d.errors


def test_a_project_opened_laid_is_laid_at_once_with_no_motion(desk, tmp_path):
    from orkboard.realm import first_open
    d = unlaid(desk, tmp_path)
    first_open.lay(d.host.ideas.state_dir)
    pg = d.open()
    pg.locator('.frame[data-laid="1"]').wait_for(timeout=WAIT_MS)
    pg.locator(".hand-plus").wait_for(timeout=WAIT_MS)
    assert pg.locator(".frame[data-laying]").count() == 0 and pg.locator(".fo-bubble").count() == 0
    assert not d.errors, d.errors


def test_a_task_to_look_at_and_a_merged_one_have_stage_words_of_their_own_never_planning(table):
    """Spec 143 F.1 (decisions §250.7): *To look at* (the word the result card says) and *Done* (the finished card's check), and the rest as they were."""
    pg, host, w = table
    got = pg.evaluate("""async () => { const d = await import('/static/js/table/data.js');
      const of = (state, band = '') => { const k = d.stageOf({ state, band }); return [k, d.STAGES[k].word, d.STAGES[k].sign]; };
      return [of('review'), of('merged'), of('merged', 'check'), of('testing'), of('running'), of('failed'), of('waiting'), of('picking')]; }""")
    assert got == [["review", "To look at", "page"], ["done", "Done", "check"], ["done", "Done", "check"], ["checking", "Checking", "shield"], ["doing", "Doing", "sword"],
                   ["doing", "Doing", "sword"], ["planning", "Planning", "page"], ["planning", "Planning", "page"]]
