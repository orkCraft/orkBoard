"""Spec 98 part C, the table (docs/specs/98-the-table-and-the-hand.md §3, §5, §6; mockup docs/mockups/s1/ states 1–4 and 6), re-faced by spec 101 part C (the Board's cards, a goal's cascade, the line in the first lane, the project's tab) and part F (a goal's tasks behind its front card lie as a fan): the window (the
page, spec 98 E), at both widths (`tests/narrow.py`: 1280 × 800, and 390 × 844 with touch), against a stub host of its own (a project of four parties: Game design, Tech led by the Architect, Art and Release; the Orkmaster reading two goals,
routing one and joining one; tasks at work, failures, a check; three goals in line; Tech's System).

The tabs in order with the project's first (its name), its **…** and its three places over the pane, **+**, the chips, *Stop all*; the Board's lanes under their tabs, the same widths; a task card's header, window and label row, a goal's strip and
cascade (its front by the rule, the others a fan behind it with a fixed turn by place, opened by a hover, an edge lifting its task, the picked goal's unfolded, a goal in two lanes lit in both); the first lane's cards and the line (the Orkmaster's order, the moon, a drag, *All · search*); a party's header with its
groups, a seat's popover and its **Open**, another party's tab its header alone; Tech's System; a card lifted and lowered (Esc, a press away); a file opened over the pane, its title, **←** back to the card lit; a form in the pane, never a dialog; no
sideways scroll at 390. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.realm import library  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)

pytestmark = pytest.mark.browser

SHOP = "/work/shop"
HEAD = lambda race, tier, craft="engineering": {"craft": craft, "race": race, "tier": tier}  # noqa: E731
LEADS = {"game": HEAD("knight", "elder", "product"), "tech": HEAD("peon", "elder"), "art": HEAD("elf", "elder", "design"), "release": HEAD("lich", "elder", "product")}
NAMES = {"game": "Game design", "tech": "Tech", "art": "Art", "release": "Release"}
MEMBER = {"grunt": ("Grunts", HEAD("peon", "warrior"), "build"), "tester": ("Tester", HEAD("peon", "laborer"), "build"), "reviewer": ("Reviewer", HEAD("peon", "warrior"), "check"),
          "designer": ("Designer", HEAD("knight", "warrior", "product"), "build"), "artist": ("Artist", HEAD("elf", "warrior", "design"), "build")}
FILE = "server/lobby.ts"
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
            "party": [{**lead, "band": "lead", "state": "free", "why": ""}, *[seat(s, b) for s, b in seats]], "today": {"merged": 0, "usd": 0.0}, "flags": 0, "waits_main": 0, "brief": "", "order": order}


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

    def snapshot(self):
        return {"t": "state", "state": {
            "focus": "board", "ideas_rev": self.rev, "look": "office", "project": "shop", "demo": False, "onboarding": False, "words": [], "resources": {}, "orkspaces": [], "buildings": [], "roads": [], "alerts": [],
            "score": {}, "limits": [{"provider": "claude", "name": "Claude", "left": 0.62, "rows": [{"window": "5h", "left": 0.62, "reset": ""}]},
                                    {"provider": "codex", "name": "Codex", "left": 0.18, "rows": [{"window": "daily", "left": 0.18, "reset": ""}]}],
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
        return {"tracks": tracks, "ideas": ideas, "needs_you": [], "target": "balance", "autostart": True, "review": False, "review_notice": False, "rev": self.rev}

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
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
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


def tab(pg, slug):
    return pg.locator(f'.table-tab[data-tab="{slug}"]')


def open_tab(pg, slug):
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


def title(pg):
    return " ".join(pg.locator(".table-title__pt").text_content().split())


def open_menu(pg):
    pg.get_by_role("button", name="The Orkmaster's menu").click()
    pg.get_by_role("menu").wait_for(timeout=WAIT_MS)


# -- the tabs ----------------------------------------------------------------------------------------------------------------------------------------

def test_the_tabs_in_order_the_projects_first_then_plus_the_chips_and_stop_all(table):
    pg, host, w = table
    tabs = pg.locator(".table-tab")
    assert [t.get_attribute("data-tab") for t in tabs.all()] == ["orkmaster", "game", "tech", "art", "release"]         # the project's first, then the Board's order
    first = tab(pg, "orkmaster")
    assert first.get_attribute("aria-label") == "shop" and first.get_attribute("aria-selected") == "true"                # the first tab is the project's: its name (spec 101 §3.4, decisions §167.6)
    assert "Orkmaster" not in (first.get_attribute("title") or "") and first.locator(".table-tab__sub").count() == 0
    assert "peon-crown" in first.locator(".ork-race__head").get_attribute("src")                                         # its crowned head
    assert "knight-elder" in tab(pg, "game").locator(".ork-race__head").get_attribute("src")                             # a party's tab wears its leader's head
    assert tab(pg, "tech").get_attribute("aria-label") == "Tech"                                                         # and its name, said also when only the head is drawn
    assert pg.get_by_role("button", name="New party").count() == 1 and pg.get_by_role("button", name="Stop all").count() == 1
    chips = pg.locator(".table-tabs__end .table-chip")
    if wide(w):
        assert [c.inner_text().strip() for c in chips.all()] == ["Claude 62% left", "Codex 18% left"]                    # the limits as chips
        assert chips.first.locator(".ork-mark").count() == 1
    else:
        assert chips.count() == 0                                                                                        # under 760 px the limits are in the Orkmaster's …
        assert tab(pg, "tech").locator(".table-tab__txt").is_hidden()                                                    # the tabs a row of heads
        assert all(t.bounding_box()["width"] >= 44 and t.bounding_box()["height"] >= 44 for t in tabs.all())             # a press 44 × 44 on a touch screen
    assert title(pg) == "The whole project · through the Orkmaster"                                                      # the Orkmaster is named where it speaks
    assert tab(pg, "orkmaster").bounding_box()["x"] <= tab(pg, "game").bounding_box()["x"]
    shot(pg, f"table-board-{w}.png")


def test_a_tab_is_the_persons_the_open_one_is_kept_and_nothing_switches_it_under_them(table):
    pg, host, w = table
    open_tab(pg, "tech")
    assert title(pg) == "The whole project · through Tech"
    pg.reload()
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    assert tab(pg, "tech").get_attribute("aria-selected") == "true"                                                      # kept for the project on this device
    tab(pg, "tech").focus()
    pg.keyboard.press("ArrowLeft")
    assert tab(pg, "game").get_attribute("aria-selected") == "true"                                                      # the arrows move between tabs
    pg.keyboard.press("Home")
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))                                                                            # the Board changes under them
    pg.wait_for_timeout(300)
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"


def test_the_orkmasters_menu_has_the_projects_settings_and_files_over_the_pane(table):
    pg, host, w = table
    open_menu(pg)
    menu = pg.get_by_role("menu")
    assert [i.inner_text().strip() for i in menu.get_by_role("menuitem").all()] == ["Switch project", "Settings", "Files"]
    if not wide(w):
        assert [c.inner_text().strip() for c in menu.locator(".table-chip").all()] == ["Claude 62% left", "Codex 18% left"]       # the limits' chips in the Orkmaster's …
    menu.get_by_role("menuitem", name="Switch project").click()
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


def test_plus_opens_new_party_in_the_pane_and_a_chip_opens_what_used_the_tool(table):
    pg, host, w = table
    pg.get_by_role("button", name="New party").click()
    pg.locator('.table-over--form[data-kind="party"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Board · New party" and pg.locator(".place").count() == 1
    pg.get_by_role("button", name="Cancel").click()
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)
    if wide(w):
        pg.locator('.table-chip[data-provider="codex"]').click()
        pg.locator('.table-over[data-kind="limits"] .arena-usage').wait_for(timeout=WAIT_MS)
        assert title(pg) == "Board · Codex: what used it"
        assert ("ideas.usage", {"provider": "codex", "scope": "project"}) in host.log
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
    assert lanes.first.get_attribute("data-lane") == "first" and [l.get_attribute("data-party") for l in lanes.all()[1:5]] == ["game", "tech", "art", "release"]
    assert lanes.first.get_attribute("aria-label") == "shop"                                                             # the first lane is the whole project's
    for slug in ("orkmaster", "game", "tech", "art", "release"):
        lane = lanes.first if slug == "orkmaster" else pg.locator(f'.table-lane[data-party="{slug}"]')
        t, l = tab(pg, slug).bounding_box(), lane.bounding_box()
        assert abs(t["x"] - l["x"]) <= 1 and abs(t["width"] - l["width"]) <= 1, slug                                      # a tab is its lane's head: the same x, the same width
    widths = {round(l.bounding_box()["width"]) for l in lanes.all()[:5]}
    assert len(widths) == 1, widths                                                                                       # every lane the same width, the first too
    if wide(w):
        assert abs(widths.pop() - 180) <= 1                                                                              # a card and a quarter (frame.css `--col-w`)
    else:
        assert widths.pop() <= 48                                                                                        # a token wide
    assert pg.locator(".table-board").evaluate("e => e.scrollWidth <= e.clientWidth + 1")                                # no sideways scroll
    assert pg.locator(".table-board").evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length") == 6    # the five lanes and the tabs' end: the frame's `--cols`, no `--tabs`


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
    assert abs(box["width"] - 144) <= 1                                                                                   # 144 wide (frame.css `--card-w`)
    head = failed.locator(".table-card__head")
    assert head.locator(".ork-elem.ice").count() == 1 and failed.locator(".ork-elem").count() == 1                      # the goal's element, bare, at the left
    assert head.evaluate("e => e.firstElementChild.classList.contains('ork-elem')")
    nm = head.locator(".table-card__nm")
    assert nm.inner_text().strip() == "Reset the round timer when a player rejoins"
    assert nm.evaluate("e => getComputedStyle(e).textAlign") in ("left", "start") and nm.evaluate("e => getComputedStyle(e).webkitLineClamp") == "3"        # left-aligned, three lines at most
    pixel = pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ork-font-pixel').split(',')[0].trim().replace(/[\"']/g, '')")
    assert pixel and pixel not in nm.evaluate("e => getComputedStyle(e).fontFamily")                                      # a person's words: the body face, never the pixel one (CLAUDE.md, the owner)
    win = failed.locator(".table-card__win")
    assert abs(win.bounding_box()["height"] - 70) <= 1                                                                   # about 70 px high
    assert win.locator(".ork-sign.feature.big").count() == 1 and win.locator(".ork-sign").count() == 1                  # one sign at the big size: the goal's type (the task has no kind of its own)
    assert win.evaluate("e => e.querySelector('.ork-sign').offsetWidth") == 28 and win.evaluate("e => getComputedStyle(e.querySelector('.ork-sign')).opacity") == "0.6"      # 28 px, toned down
    assert win.evaluate("e => getComputedStyle(e).borderTopWidth") == "1px"                                              # a hairline
    assert failed.locator(".ork-race__head").count() == 0                                                                # no head on a card of the Board: who works is on its back
    row = failed.locator(".table-card__row")
    assert row.locator(".table-stage").inner_text().strip().lower() == "doing" and row.locator(".table-stage .ork-sign.sword").count() == 1      # the stage's small sign and word
    assert abs(row.locator(".table-stage .ork-sign").bounding_box()["width"] - 14) <= 1
    assert row.locator(".ork-gem").inner_text().strip() == "$1" and row.evaluate("e => e.lastElementChild.classList.contains('ork-gem')")                      # a retry spends: the gem at the right
    assert "fails" in failed.get_attribute("class")                                                                      # a failure: orkUI's danger frame
    check = pg.locator('[data-lkey="t:task:recheck/c2"]')                                                                 # a failed check
    assert "fails" in check.get_attribute("class") and check.locator(".table-stage .ork-sign.shield").count() == 1 and check.locator(".ork-gem").count() == 0     # no gem: it is not a retry
    assert check.locator(".table-stage").inner_text().strip().lower() == "checking" and check.locator(".table-card__win .ork-sign.bug").count() == 1
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
    assert edge.locator(".ork-sign.sword").count() == 1 and edge.locator(".ork-elem.void").count() == 1 and edge.locator(".ork-sign").count() == 1             # the stage's small sign and the goal's element
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
        assert title(pg) == "The whole project · through the Orkmaster"
        pg.locator('.table-casc[data-goal="seat"]').locator("xpath=..").locator(".table-gstrip").click()                  # the strip of a goal picks it
        pg.wait_for_function("() => document.querySelector('.table-casc[data-goal=\"seat\"]').dataset.open === 'true'", timeout=WAIT_MS)
        assert title(pg) == "Keep the seat when a socket reconnects · through the Orkmaster"
        pg.locator('.table-casc[data-goal="seat"]').locator("xpath=..").locator(".table-gstrip").click()                  # and again puts it down
        pg.wait_for_function("() => document.querySelector('.table-casc[data-goal=\"seat\"]').dataset.open === 'false'", timeout=WAIT_MS)
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
    pg.wait_for_function("() => document.querySelectorAll('.table .ork-picked').length === 2", timeout=WAIT_MS)
    assert title(pg) == "A timer bar that drains · through the Orkmaster"
    lit = pg.locator(".ork-picked")
    assert [l.get_attribute("data-goal") for l in lit.all()] == ["bar", "bar"]                                            # its strip (or token) in both lanes, lit alike
    assert pg.locator('.table-lane[data-lane="first"] .ork-picked').count() == 1 and pg.locator('.table-lane[data-party="art"] .ork-picked').count() == 1
    if wide(w):
        bar = pg.locator('.table-casc[data-goal="bar"]')
        assert bar.get_attribute("data-open") == "true" and bar.locator(".table-card").count() == 3 and bar.locator(".table-tedge").count() == 0 and pg.locator('.table-casc[data-goal="bar"] .table-fan').count() == 0       # unfolded into whole cards, no fan
        assert keys(pg, '.table-casc[data-goal="bar"]') == ["t:task:bar/a3", "t:task:bar/a1", "t:task:bar/a2"]               # in the same order
        assert bar.locator('[data-lkey="t:task:bar/a1"] .ork-sign.picture').count() == 1                                  # a task of a kind of its own: its kind's sign, not the goal's
        assert pg.locator('.table-casc[data-goal="seat"]').get_attribute("data-open") == "false"                          # the others stay collapsed
        assert pg.locator('.table-casc[data-goal="seat"] .table-tedge').count() == 1
        assert pg.locator('.table-lane[data-lane="first"] .table-gstrip.ork-picked').evaluate("e => e.getAttribute('aria-pressed')") == "true"
    shot(pg, f"table-picked-{w}.png")
    pick(pg, "")
    pg.wait_for_function("() => document.querySelectorAll('.table .ork-picked').length === 0", timeout=WAIT_MS)


def test_the_first_lane_holds_what_is_the_whole_projects_the_goals_read_routed_and_joined_then_the_line(table):
    pg, host, w = table
    first = pg.locator('.table-lane[data-lane="first"]')
    assert keys(pg, '.table-lane[data-lane="first"]') == ["t:orc:timer", "t:orc:results", "t:orc:bar"]                      # what the Orkmaster does itself, in the Board's order
    assert [o.get_attribute("data-stage") for o in first.locator("[data-lkey]").all()] == ["reading", "routing", "joining"]
    if wide(w):
        words = [o.locator(".table-stage").inner_text().strip().lower() for o in first.locator(".table-card--own").all()]
        assert words == ["reading", "routing", "joining"]
        assert first.locator(".table-card--own .ork-race__head").count() == 0                                             # no crown: who works is not on a card of the Board
        goal = first.locator('.table-goal[data-goal="results"]')
        assert goal.locator(".table-gstrip").count() == 1 and goal.locator(".table-card--own").count() == 1               # a card a goal, under its strip
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
        assert line_slugs(pg) == ["ln3", "ln2", "ln1"]                                                                    # the farthest at the top, the next to start whole in front
        front = pg.locator(".table-card--line")
        assert front.get_attribute("data-slug") == "ln1" and abs(front.bounding_box()["width"] - 144) <= 1
        assert front.locator(".ork-elem.dust").count() == 1 and "Chat in the lobby" in front.locator(".table-card__nm").inner_text()      # its element, its name
        assert front.locator(".table-card__win .ork-sign.feature").count() == 1 and front.locator(".table-card__row").inner_text().strip().lower() == "in line"
        edge = pg.locator('.table-ledge[data-slug="ln2"]')
        assert edge.locator(".ork-elem.ice").count() == 1 and edge.evaluate("e => getComputedStyle(e.querySelector('.table-fan__nm')).opacity") == "0"      # the goal's element, its name read only on a hover
        assert pg.locator(".table-casc--line .table-fan").count() == 1 and edge.evaluate("e => getComputedStyle(e).transform") != "none"                                # a fan behind the front one, turned
        moon = edge.locator(".ork-sign.moon")
        assert moon.count() == 1 and moon.get_attribute("title") == "Waits for the reset, from 06:00"                       # the moon, its hour on hover
        assert pg.locator('.table-ledge[data-slug="ln3"] .ork-sign.moon').count() == 0 and front.locator(".ork-sign.moon").count() == 0
        pg.locator(".table-casc--line .table-fan").hover(position={"x": 70, "y": 3})                                          # the fan opens
        pg.wait_for_timeout(400)
        assert "Round music" in edge.inner_text() and edge.evaluate("e => getComputedStyle(e.querySelector('.table-fan__nm')).opacity") == "1"
        shot(pg, f"table-line-fan-{w}.png")
        pg.locator('.table-ledge[data-slug="ln3"]').click(position={"x": 40, "y": 8})                                        # an edge pressed picks its goal
        pg.wait_for_function("() => document.querySelector('.table-ledge[data-slug=\"ln3\"]').classList.contains('ork-picked')", timeout=WAIT_MS)
        assert title(pg) == "A banner for the lobby · through the Orkmaster"
        pg.locator('.table-ledge[data-slug="ln3"]').click(position={"x": 40, "y": 8})
        pg.wait_for_function("() => !document.querySelector('.table-ledge[data-slug=\"ln3\"]').classList.contains('ork-picked')", timeout=WAIT_MS)
        pg.locator(".table-board").evaluate("e => { e.scrollTop = e.scrollHeight; }")
        shot(pg, f"table-line-{w}.png")
    else:
        assert line_slugs(pg) == ["ln1", "ln2", "ln3"]                                                                    # a token a goal (no drag here: the list over the pane has its arrows)
        t2 = pg.locator('.table-line-tokens [data-slug="ln2"]')
        assert t2.locator(".ork-sign.moon").count() == 1 and t2.locator(".ork-sign.sound").count() == 1 and t2.locator(".ork-elem.ice").count() == 1
        t2.click()
        pg.wait_for_function("() => document.querySelector('.table-line-tokens [data-slug=\"ln2\"]').classList.contains('ork-picked')", timeout=WAIT_MS)
        pg.locator(".table-board").evaluate("e => { e.scrollTop = e.scrollHeight; }")
        shot(pg, f"table-line-{w}.png")


def test_a_goal_dragged_among_the_line_moves_with_ideas_move_and_a_drop_among_other_partys_goals_goes_back(lined):
    pg, host, w = lined
    if not wide(w):
        return                                                                                                            # a touch screen scrolls the lane: its moves are the list's arrows
    assert line_slugs(pg) == ["ln4", "ln3", "ln2", "ln1"]
    host.log.clear()

    def drag(slug, onto):
        pg.locator(".table-board").evaluate("e => { e.scrollTop = e.scrollHeight; }")                                    # the line is the first lane's last cascade
        pg.locator(".table-casc--line .table-fan").hover(position={"x": 70, "y": 3})
        pg.wait_for_timeout(400)                                                                                         # the fan is open: an edge is its top 30 px
        a, b = pg.locator(f'[data-line-item][data-slug="{slug}"]').bounding_box(), pg.locator(f'[data-line-item][data-slug="{onto}"]').bounding_box()
        pg.mouse.move(a["x"] + a["width"] / 2, a["y"] + 8)
        pg.mouse.down()
        pg.mouse.move(a["x"] + a["width"] / 2, a["y"] + 20, steps=4)
        pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] - 4, steps=8)
        pg.wait_for_selector(".table-casc--line.is-dragging", timeout=WAIT_MS)                                           # the cascade shows the drag
        pg.mouse.up()
    drag("ln3", "ln1")                                                                                                    # Art's goal among Tech's and Game design's: it goes back
    pg.wait_for_timeout(300)
    assert not [a for n, a in host.log if n == "ideas.move"] and line_slugs(pg) == ["ln4", "ln3", "ln2", "ln1"]
    assert pg.locator(".table-casc--line.is-dragging").count() == 0 and not pg.locator('[data-line-item][data-slug="ln3"]').evaluate("e => e.parentElement.style.transform")
    assert title(pg) == "The whole project · through the Orkmaster"                                                       # the press that ended the drag picked nothing
    drag("ln4", "ln1")                                                                                                    # Tech's other goal before it: the front
    for _ in range(40):
        if any(n == "ideas.move" for n, _ in host.log):
            break
        pg.wait_for_timeout(50)
    assert [a for n, a in host.log if n == "ideas.move"] == [{"slug": "ln4", "before": "ln1"}]
    pg.wait_for_function("() => document.querySelector('.table-card--line').dataset.slug === 'ln4'", timeout=WAIT_MS)
    assert line_slugs(pg) == ["ln3", "ln2", "ln1", "ln4"]                                                                 # the Orkmaster's order is the host's: ln4 first
    assert title(pg) == "The whole project · through the Orkmaster"
    pg.locator('[data-line-item][data-slug="ln1"]').focus()                                                               # no move needs a pointer: Alt and the arrows
    host.log.clear()
    pg.keyboard.press("Alt+ArrowDown")                                                                                    # down is toward the front: earlier in line, before ln4
    for _ in range(40):
        if any(n == "ideas.move" for n, _ in host.log):
            break
        pg.wait_for_timeout(50)
    assert [a for n, a in host.log if n == "ideas.move"] == [{"slug": "ln1", "before": "ln4"}]


def test_past_seven_goals_all_search_opens_the_line_over_the_pane(crowded):
    pg, host, w = crowded
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
    pg.locator('.table-over[data-kind="log"] .shell-log').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Board · Reset the round timer when a player rejoins" and "tests: 3 failed" in pg.locator(".shell-log").inner_text()
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


def test_a_goal_picked_through_the_orkmasters_tab_keeps_every_goal_on_the_board_and_unfolds_its_own(table):
    pg, host, w = table
    cards = pg.locator("[data-lkey]").count()
    pick(pg, "seat")
    pg.wait_for_function("() => document.querySelector('.table-casc[data-goal=\"seat\"], .table-token[data-goal=\"seat\"]') !== null && document.querySelectorAll('.table .ork-picked').length === 1", timeout=WAIT_MS)
    assert title(pg) == "Keep the seat when a socket reconnects · through the Orkmaster"
    assert pg.locator("[data-lkey]").count() >= cards                                                                    # nothing is hidden for it (a picked goal's unfolded cascade only adds cards)
    if wide(w):
        assert keys(pg, '.table-casc[data-goal="seat"]') == ["t:task:seat/s1", "t:task:seat/s2"] and pg.locator('.table-casc[data-goal="seat"] .table-card').count() == 2
    pick(pg, "")
    pg.wait_for_function("() => document.querySelectorAll('.table .ork-picked').length === 0", timeout=WAIT_MS)


def pick(pg, slug):
    pg.evaluate("slug => import('/static/js/frame/state.js').then((m) => { m.picked.value = slug; })", slug)


# -- a party's tab -----------------------------------------------------------------------------------------------------------------------------------

def test_a_partys_header_has_its_squad_in_three_groups_and_a_seat_pressed_opens_its_popover(table):
    pg, host, w = table
    open_tab(pg, "tech")
    head = pg.locator('.table-head[data-party="tech"]')
    assert head.locator(".table-head__name").text_content().strip() == "Tech"
    assert [g.locator(".ork-label").text_content().strip() for g in head.locator(".table-group").all()] == ["Leads", "Does", "Checks"]
    assert [g.locator(".table-seat").count() for g in head.locator(".table-group").all()] == [1, 2, 1]
    seat = head.locator('.table-seat[data-seat="grunt"]')
    assert "peon-warrior" in seat.locator(".ork-race__head").get_attribute("src") and "harness-claude-ink" in seat.locator(".ork-mark").get_attribute("src")     # its tier's gear, its tool's mark in ink
    assert head.locator(".table-size").inner_text().strip() == "Standard"
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
    pg.get_by_role("button", name="Close").click()
    assert pg.locator(".table-seatpop").count() == 0
    seat.click()
    pg.locator(".table-seatpop").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")                                                                                          # Esc closes it
    assert pg.locator(".table-seatpop").count() == 0
    seat.click()
    pg.locator(".table-seatpop").get_by_role("button", name="Open", exact=True).click()
    pg.locator('.table-over[data-kind="role"]').wait_for(timeout=WAIT_MS)                                                  # the role's text, over the pane
    assert title(pg) == "System · Grunts" and "You are the Grunts." in pg.locator(".table-over").inner_text()
    pg.locator(".table-title__back").click()
    pg.locator(".table-head").wait_for(timeout=WAIT_MS)


def test_a_seat_can_be_taken_off_and_its_tool_set_with_undo(table):
    pg, host, w = table
    open_tab(pg, "tech")
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


def test_a_party_menu_has_edit_and_remove_party_over_the_pane(table):
    pg, host, w = table
    open_tab(pg, "art")
    assert pg.locator(".table-sys, .table-board").count() == 0                                                           # another party than Tech: its header alone (no map yet)
    pg.get_by_role("button", name="Art's menu").click()
    pg.get_by_role("menuitem", name="Edit").click()
    pg.locator('.table-over--form[data-kind="party"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Art · Edit Art" and pg.get_by_role("button", name="Save party").count() == 1
    pg.get_by_role("button", name="Remove party").click()                                                                # the Edit form's own button: today's question, in the pane too
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
    assert title(pg) == f"System · {FILE}" and "line 3" in pg.locator(".shell-code").inner_text()                        # a file over the pane, its title says where it came from
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
    assert tab(pg, "tech").locator(".table-tab__txt").is_hidden() and tab(pg, "tech").get_attribute("aria-label") == "Tech"           # more than fit: the heads alone
    assert pg.locator('.table-board[data-tokens="true"]').count() == 1
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


# -- a goal picked, the project, the keys, the motion, the presses ------------------------------------------------------------------------------------

def test_a_goal_picked_puts_a_dot_on_the_tabs_of_its_route_and_opens_on_its_partys_tab(table):
    pg, host, w = table
    assert pg.locator(".table-tab__dot").count() == 0                                                                    # nothing picked: no dot
    pick(pg, "seat")
    pg.locator(".table-tab__dot").first.wait_for(timeout=WAIT_MS)
    assert [t.get_attribute("data-tab") for t in pg.locator(".table-tab:has(.table-tab__dot)").all()] == ["tech", "art"]   # its party's and the party the route passed
    pick(pg, "")
    open_tab(pg, "game")
    pick(pg, "seat")                                                                                                     # picked in the hand, a party's tab open: it opens on its own party's tab
    pg.locator('.table-tab[data-tab="tech"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Keep the seat when a socket reconnects · through Tech"
    pick(pg, "")
    open_tab(pg, "orkmaster")
    pick(pg, "seat")
    assert tab(pg, "orkmaster").get_attribute("aria-selected") == "true"                                                 # the Orkmaster's tab stays: its Board shows the tasks alone


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
    open_menu(pg)
    pg.get_by_role("menuitem", name="Switch project").click()
    pg.locator('.table-projects__one[data-path="/work/other"]').click()
    for _ in range(40):
        if ("projects.use", {"path": "/work/other"}) in host.log:
            break
        pg.wait_for_timeout(50)
    assert ("projects.use", {"path": "/work/other"}) in host.log
    pg.locator(".table-board").wait_for(timeout=WAIT_MS)                                                                 # another project: the map again, nothing open
    assert tab(pg, "orkmaster").get_attribute("aria-label") == "other"


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


def test_every_press_is_44_by_44_on_a_touch_screen_and_nothing_is_said_only_on_hover(table):
    pg, host, w = table
    if wide(w):
        return
    open_tab(pg, "tech")
    pg.locator('.table-seat[data-seat="grunt"]').wait_for(timeout=WAIT_MS)
    for sel in (".table-tab", ".table-plus", ".table-stop", ".table-play", ".table-menu__btn", ".table-seat"):
        for el in pg.locator(sel).all():
            box = el.bounding_box()
            assert box["width"] >= 43.5 and box["height"] >= 43.5, (sel, box)
    for el in pg.locator(".table-tab").all():
        assert el.get_attribute("aria-label") and el.get_attribute("title")                                              # a tab's name is its label too, not only a tooltip
    pg.locator(".table-tab").nth(3).dispatch_event("pointerdown", {"pointerType": "touch"})                              # a long press says the name
    pg.locator(".gui-toast").wait_for(timeout=WAIT_MS)
    assert "Art" in pg.locator(".gui-toast").text_content()
