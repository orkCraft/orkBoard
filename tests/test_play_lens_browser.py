"""Spec 115 part E (docs/specs/115-the-live-product-under-each-leaders-eyes.md §6.1–§6.3; mockup docs/mockups/play-lenses/ states 1–3 and 8), Chromium against the table's stub host (tests/test_owners_day_desktop_browser.py `Host`) and a
made-up dev server (a plant app and a canvas) reached through the probe's proxy (gui/play_proxy.py): the real probe (gui/static/play/probe.js) speaks to the real page.

Play stays open when the tab changes (the iframe is the same element, never reloaded; the pane's title follows the tab); the lens strip under Play's bar (*<Leader> on <screen>*, the rubric's short, the aspects in their state for this
screen's parts only; *Not on <map>* on a path with no screen; none on the project's tab); a concern and a hint on their elements on a layer that lets presses through (a press on a tag opens its back: the concern's, the hint's with
**Make it a goal** and **Not a problem**); what has no element stands in the strip; **Hide the marks**; a Play with no probe says *Marks keep the picture and the place only*. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when set.
The harness (`Dev`, `LensHost`, `rig`, `open_play`) is the mark's tests' too (tests/test_play_mark_browser.py)."""
from __future__ import annotations

import copy
import http.server
import json
import os
import threading
from pathlib import Path
from urllib.parse import urlparse

import pytest

pytest.importorskip("playwright.sync_api")

from orkboard.gui import play_proxy  # noqa: E402
from orkboard.realm import lens_rubrics  # noqa: E402
from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_owners_day_desktop_browser import Host  # noqa: E402
from tests.test_table_desktop_browser import open_tab, title  # noqa: E402

pytestmark = pytest.mark.browser

WIDE = {"width": 1280, "height": 800}
PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Sproutly</title>
<style>body{margin:0;background:#f3f6ef;font:14px sans-serif} main,button,canvas,h2{position:absolute;margin:0}
main{left:20px;top:20px;width:360px;height:260px;background:#fff} h2{left:10px;top:8px;font-size:16px}
#watered{left:260px;top:200px;width:82px;height:20px} #snooze{left:150px;top:200px;width:66px;height:20px}
#boom{left:420px;top:20px;width:80px;height:30px} #fail{left:520px;top:20px;width:80px;height:30px} #push{left:420px;top:70px;width:80px;height:30px}
#game{left:420px;top:120px;width:200px;height:120px;background:#235}</style></head><body>
<main data-source="web/src/components/Plants.tsx:3:1">
  <h2 data-source="web/src/ui/Title.tsx:1:1">Needs you</h2>
  <button id="watered" data-source="web/src/ui/Button.tsx:5:1" onclick="fetch('/api/water', {method: 'POST'})">Watered</button>
  <button id="snooze" data-source="web/src/ui/Button.tsx:5:1">Snooze</button>
</main>
<button id="boom" data-source="web/src/ui/Button.tsx:5:1" onclick="console.error('plant.lastWatered is undefined')">Boom</button>
<button id="fail" data-source="web/src/ui/Button.tsx:5:1" onclick="fetch('/api/water', {method: 'POST'})">Fail</button>
<button id="push" data-source="web/src/ui/Button.tsx:5:1" onclick="history.pushState({}, '', '/nowhere')">Go</button>
<canvas id="game" width="200" height="120"></canvas>
<script>window.__ork = {state: function () { return {level: 3, gold: 40}; }};</script></body></html>"""
MAIN, SNOOZE, WATERED = {"x": 20, "y": 20, "w": 360, "h": 260}, {"x": 170, "y": 220, "w": 66, "h": 20}, {"x": 280, "y": 220, "w": 82, "h": 20}
PLACES = {"/today": {"screen": {"id": "today", "name": "Today", "step": 1},
                     "parts": {"screens": [{"id": "today", "name": "Today"}], "system": [{"id": "web/src/components", "name": "web/src/components"}],
                               "game-design": [{"id": "step-wave", "name": "Survive the wave"}]}}}
NOWHERE = {"screen": None, "parts": {}}
STEPS = ["Place a tower", "Survive the wave", "Spend the gold"]


class Dev(http.server.BaseHTTPRequestHandler):
    """The made-up dev server: any path is the plant page, /api/water answers 500."""

    def log_message(self, *_a) -> None:
        pass

    def do_GET(self) -> None:
        status, body, kind = (500, b"boom", "text/plain") if self.path.startswith("/api/water") else (200, PAGE.encode(), "text/html")
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_POST = do_GET


def serve(handler) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def record(party: str, map_id: str, craft: str, concerns: list[dict]) -> dict:
    """A concerns record as `ideas.concerns` gives it, its rubric the real one (`lens_rubrics.scorecard`)."""
    rec = {"party": party, "map": map_id, "leader": "x", "has_map": True, "at": "2026-10-28T08:00:00", "map_hash": "h", "by": "x", "status": "ready", "error": "", "measure": "", "concerns": concerns,
           "dismissed": [], "hints": [], "alerts": sum(c["level"] == "alert" for c in concerns), "notes": sum(c["level"] == "note" for c in concerns)}
    rubric = lens_rubrics.rubric(craft)
    return {**rec, "rubric": {"framework": rubric["framework"], "short": rubric["short"], "aspects": lens_rubrics.scorecard(craft, rec)}}


def concern(cid: str, on: str, level: str, what: str, aspect: str) -> dict:
    return {"id": cid, "on": on, "name": on, "level": level, "what": what, "why": f"Why: {what}", "fix": f"Fix: {what}", "signal": "", "aspect": aspect}


class Refused(Exception):
    """A command the stub host answers with a refusal (the town said no)."""


class LensHost(Host):
    """The table's host with a Play that plays through the proxy (or not), the commands of spec 115 D answered from what a test sets, and the commands it was asked kept in `calls`."""

    def __init__(self, url: str, probe: bool = True, **kw):
        super().__init__(play={"state": "playing", "url": url, "commit": "a" * 40, "short": "aaaaaaa", "dev": "a" * 40, "logo": "", "probe": probe, "play": "p1"}, **kw)
        for p in self.parties:                                       # the parties' crafts and leaders, as the host's map names them
            p["party_craft"] = {"game": "game-design", "tech": "tech", "art": "design", "release": "release"}[p["slug"]]
        by = {p["slug"]: p for p in self.parties}
        by["art"]["title"] = by["art"]["short"] = "Design"
        by["art"]["leader"]["name"] = "Product designer"
        by["game"]["leader"]["name"] = "Game designer"
        self.places, self.hints, self.offer, self.events, self.marks, self.calls, self.refuse = dict(PLACES), [], None, [], [], [], {}
        self.records = {
            "art": record("art", "screens", "design", [concern("c-1", "today", "alert", "The Watered buttons are 20 px tall.", "access"), concern("c-2", "settings", "note", "Settings has no empty state.", "status")]),
            "tech": record("tech", "system", "tech", [concern("c-3", "web/src/components", "alert", "Plants.tsx is 610 lines and changed in 14 goals.", "hotspots")]),
            "game": record("game", "game-design", "game-design", [concern("c-4", "step-wave", "alert", "Wave 3 spikes the intensity.", "pacing")]),
            "release": record("release", "release", "release", [])}
        self.made = {"slug": "watered-fails", "title": "Watered fails", "party": "tech", "party_title": "Tech", "type": "bug", "element": "lava", "joined": False,
                     "kept": {"picture": True, "errors": 1, "requests": 1, "lines": 0, "state": False, "under": 1, "marks": 1}}

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            try:
                reply = {"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}
            except Refused as e:
                reply = {"t": "reply", "id": m["id"], "ok": False, "error": str(e)}
            ws.send(json.dumps(reply))
        ws.on_message(on_message)

    def handle(self, name, a):
        if name in self.refuse:
            raise Refused(self.refuse[name])
        if name == "ideas.play_events":
            self.events += a["events"]
            return {"ok": True, "kept": len(a["events"])}
        if name == "ideas.play_place":
            self.calls.append((name, a))
            return copy.deepcopy(self.places.get(a["path"].split("#")[0].split("?")[0], NOWHERE))
        if name == "ideas.play_hints":
            return {"hints": copy.deepcopy(self.hints)}
        if name == "ideas.concerns":
            return copy.deepcopy(self.records[a["party"]])
        if name == "ideas.play_mark_offer":
            self.calls.append((name, a))
            return {"goal": self.offer} if self.offer else {}
        if name == "ideas.loop":
            steps = [{"id": f"s{i}", "name": s, "line": "", "feel": "challenge", "intensity": 3, "gives": [], "takes": [], "rests_on": [], "by": "", "at": ""} for i, s in enumerate(STEPS)]
            return {"version": 2, "loops": [{"id": "hold", "span": "core", "name": "Hold the lane", "line": "", "feeds": "", "steps": steps}], "currencies": [], "hooks": [], "by": "", "at": "", "findings": [],
                    "proposing": False, "status": "", "party": "game"}
        if name == "ideas.play_mark":
            self.marks.append(a)
            return copy.deepcopy(self.made)
        return super().handle(name, a)


class Rig:
    """One dev server, its proxy (when `probe`), the host that plays it."""

    def __init__(self, server, probe: bool = True) -> None:
        origin = "{0.scheme}://{0.netloc}".format(urlparse(server.url))
        self.dev = serve(Dev)
        self.proxy = play_proxy.PlayProxy(self.dev.server_address[1], "p1", origin).start() if probe else None
        base = self.proxy.url_of("/today") if self.proxy else f"http://127.0.0.1:{self.dev.server_address[1]}/today"
        self.host = LensHost(base, probe)

    def close(self) -> None:
        if self.proxy:
            self.proxy.stop()
        self.dev.shutdown()
        self.dev.server_close()


@pytest.fixture
def rig(gui):
    r = Rig(gui[0])
    yield r
    r.close()


@pytest.fixture
def bare(gui):
    r = Rig(gui[0], probe=False)
    yield r
    r.close()


def shot(pg, name):
    d = os.environ.get("ORKCRAFT_SHOTS_DIR")
    if d:
        Path(d).mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(Path(d) / name))


def open_play(gui, host, tab: str = "", width=WIDE, **ctx):
    """The window at `width` with Play opened by the die (and `tab` opened first); the page's errors are returned beside it (the product's own errors, in its frame, are not the page's)."""
    server, browser = gui
    errors: list[str] = []
    pg = browser.new_context(viewport=width, **ctx).new_page()
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and m.location.get("url", "").startswith(server.url.split("?")[0]) and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-card, .table-token").first.wait_for(timeout=WAIT_MS)
    if tab:
        open_tab(pg, tab)
    pg.locator(".hand-die").click()
    pg.locator('.table-over[data-kind="play"] .play-frame').wait_for(timeout=WAIT_MS)
    pg.frame_locator(".play-frame").locator("#watered").wait_for(timeout=WAIT_MS)                              # the product has loaded
    if tab and tab != "orkmaster":                                                                               # and the strip has settled (the frame moves down as its aspects come)
        pg.wait_for_function("() => document.querySelector('.play-lens[data-state=noprobe]') || document.querySelector('.play-lens .cn-aspect')", timeout=WAIT_MS)
        pg.wait_for_function("() => document.querySelector('.play-lens[data-state=noprobe]') || /on Today/.test(document.querySelector('.play-lens').innerText)", timeout=WAIT_MS)
    return pg, errors


def finish(pg, errors):
    pg.context.close()
    assert not errors, "\n".join(errors)


def strip_text(pg) -> str:
    return " ".join(pg.locator(".play-lens").first.inner_text().split())


def chip_states(pg) -> dict:
    return pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('.play-lens .cn-aspect')].map((e) => [e.dataset.aspect, e.dataset.state]))")


def frame_box(pg) -> dict:
    return pg.locator(".play-frame").bounding_box()


def rect_of(pg, mark) -> dict:
    """A mark's box in the frame's own pixels."""
    f, b = frame_box(pg), mark.bounding_box()
    return {"x": round(b["x"] - f["x"]), "y": round(b["y"] - f["y"]), "w": round(b["width"]), "h": round(b["height"])}


def wait_place(pg, text: str):
    pg.wait_for_function("(t) => (document.querySelector('.play-lens')?.innerText || '').replace(/\\s+/g, ' ').includes(t)", arg=text, timeout=WAIT_MS)


# -- 1. Play stays open when the tab changes -----------------------------------------------------------------------------------------------------------

def test_play_stays_open_when_the_tab_changes_and_the_frame_is_never_reloaded(gui, rig):
    pg, errors = open_play(gui, rig.host)
    pg.evaluate("() => { const f = document.querySelector('.play-frame'); f.__mine = 1; window.__loads = 0; f.addEventListener('load', () => window.__loads++); }")
    assert pg.locator(".play-lens").count() == 0 and title(pg) == "Board · Play"                      # the project's tab: no strip
    for slug, map_name in (("art", "Screens"), ("tech", "System"), ("game", "Loop"), ("orkmaster", "Board")):
        open_tab(pg, slug)
        assert pg.locator('.table-over[data-kind="play"]').count() == 1 and pg.locator(".play-frame").count() == 1
        pg.wait_for_function("(n) => document.querySelector('.table-title__pt')?.textContent.replace(/\\s+/g, ' ') === n + ' · Play'", arg=map_name, timeout=WAIT_MS)      # the pane's title follows the tab
    assert pg.evaluate("() => [document.querySelector('.play-frame').__mine, window.__loads]") == [1, 0]
    assert pg.locator(".play-lens").count() == 0
    finish(pg, errors)


# -- 2. the strip -----------------------------------------------------------------------------------------------------------------------------------

def test_the_strip_names_the_leader_the_screen_and_the_aspects_for_this_screens_parts_only(gui, rig):
    rig.host.hints = [{"kind": "dead_press", "on": {"selector": "button#snooze", "rect": SNOOZE}, "words": "A press did nothing", "at": 1}]
    pg, errors = open_play(gui, rig.host, "art")
    wait_place(pg, "The Product designer on Today · Step 1")
    assert strip_text(pg).startswith("The Product designer on Today · Step 1") and "Nielsen · WCAG 2.2" in strip_text(pg)
    assert pg.locator(".play-lens .ork-race__head").count() == 1 and pg.locator(".play-lens").get_attribute("data-party") == "art"
    pg.wait_for_function("() => document.querySelector('.cn-aspect[data-aspect=flow]')?.dataset.state === 'hint'", timeout=WAIT_MS)
    # access: this screen's alert; status: a note on the *settings* screen, not this one; flow: a hint of code here; the others looked at and clear
    assert chip_states(pg) == {"flow": "hint", "status": "clear", "access": "alert", "consistency": "clear", "seen": "clear"}
    assert [c.get_attribute("aria-label") for c in pg.locator(".play-lens .cn-aspect").all()][2] == "Accessibility: 1 concern"
    assert pg.locator(".play-lens .cn-aspect").first.inner_text().strip() == "The way through"
    shot(pg, "e115-strip-design.png")
    open_tab(pg, "tech")
    wait_place(pg, "The Architect on Today")
    assert "web/src/components" in strip_text(pg) and "C4 · ISO 25010 · hotspots" in strip_text(pg)
    assert chip_states(pg)["hotspots"] == "alert" and chip_states(pg)["safety"] == "clear" and "access" not in chip_states(pg)
    finish(pg, errors)


def test_a_path_with_no_screen_says_it_is_not_on_the_map_and_a_press_of_the_page_moves_the_place(gui, rig):
    pg, errors = open_play(gui, rig.host, "art")
    wait_place(pg, "on Today")
    pg.frame_locator(".play-frame").locator("#push").click()                                                       # the page pushes /nowhere: the probe says `place`, the host answers no screen
    wait_place(pg, "on /nowhere")
    assert "Not on Screens" in strip_text(pg) and pg.locator(".play-lens .cn-aspect").count() == 0 and pg.locator(".play-lens").get_attribute("data-state") == "off"
    asked = [a for n, a in rig.host.calls if n == "ideas.play_place" and a["path"] == "/nowhere"]
    assert asked and "web/src/components/Plants.tsx" in asked[-1]["files"]                                         # the files the probe named for the elements it found go with the place
    shot(pg, "e115-strip-not-on.png")
    open_tab(pg, "tech")
    wait_place(pg, "The Architect on /nowhere")
    assert "Not on System" in strip_text(pg)
    finish(pg, errors)


# -- 3. the marks on the frame --------------------------------------------------------------------------------------------------------------------

def test_a_concern_and_a_hint_stand_on_their_elements_and_let_presses_through(gui, rig):
    rig.host.hints = [{"kind": "dead_press", "on": {"selector": "button#snooze", "rect": SNOOZE}, "words": "A press did nothing", "at": 1},
                      {"kind": "failed", "on": None, "words": "A request failed: POST /api/water 500", "at": 2}]
    pg, errors = open_play(gui, rig.host, "tech")
    concern_mark = pg.locator('.play-mark[data-kind="concern"]')
    concern_mark.wait_for(timeout=WAIT_MS)
    assert rect_of(pg, concern_mark) == MAIN                                                                       # the part's folder is the file the probe named for <main>: its rect, not a child's
    assert concern_mark.evaluate("e => getComputedStyle(e).outlineColor") == pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-alert)'; document.body.append(e); return getComputedStyle(e).color; }")
    assert concern_mark.locator(".ork-race__head").count() == 1 and concern_mark.locator(".ork-sign.alert").count() == 1             # the leader's small head at its corner
    assert pg.locator(".play-marks").evaluate("e => getComputedStyle(e).pointerEvents") == "none" and pg.locator(".play-tag").first.evaluate("e => getComputedStyle(e).pointerEvents") == "auto"
    f = frame_box(pg)                                                                                              # a press inside the outline reaches the product: the layer is not under it
    assert pg.evaluate("([x, y]) => document.elementFromPoint(x, y).tagName", [f["x"] + 100, f["y"] + 100]) == "IFRAME"
    loose = pg.locator(".play-lens__item")                                                                          # a hint with no element stands in the strip
    assert loose.count() == 1 and loose.first.inner_text().strip() == "A request failed: POST /api/water 500" and pg.locator('.play-mark[data-kind="hint"]').count() == 0
    shot(pg, "e115-marks-tech.png")
    concern_mark.locator(".play-tag").click()                                                                       # a press on the tag: the back, as a lifted card's (ConcernsBack)
    back = pg.locator(".play-back")
    back.wait_for(timeout=WAIT_MS)
    assert "Plants.tsx is 610 lines" in back.inner_text() and back.get_by_role("button", name="Make it a goal").count() == 1 and back.get_by_role("button", name="Not a problem").count() == 1
    assert "hotspots" in back.inner_text().lower()
    shot(pg, "e115-back-concern.png")
    back.get_by_role("button", name="Close").click()
    assert pg.locator(".play-back").count() == 0
    loose.first.click()                                                                                             # the loose hint's back
    assert "A request failed" in pg.locator(".play-back").inner_text() and pg.locator(".play-back").get_by_role("button", name="Make it a goal").count() == 1
    finish(pg, errors)


def test_a_hint_on_an_element_has_a_dotted_outline_and_a_hollow_square_and_not_a_problem_hides_it_for_this_play(gui, rig):
    rig.host.hints = [{"kind": "dead_press", "on": {"selector": "button#snooze", "rect": SNOOZE}, "words": "A press did nothing", "at": 1}]
    pg, errors = open_play(gui, rig.host, "art")
    hint = pg.locator('.play-mark[data-kind="hint"]')
    hint.wait_for(timeout=WAIT_MS)
    assert rect_of(pg, hint) == SNOOZE and hint.evaluate("e => getComputedStyle(e).outlineStyle") == "dotted" and hint.locator(".cn-hint").count() == 1 and hint.locator(".ork-race__head").count() == 0
    assert pg.locator('.play-mark[data-kind="concern"]').count() == 0                                               # the screen's concern has no element: it is in the strip
    assert "The Watered buttons are 20 px tall." in pg.locator(".play-lens__item").first.inner_text()
    shot(pg, "e115-marks-design.png")
    hint.locator(".play-tag").click()
    back = pg.locator(".play-back")
    assert "A press did nothing" in back.inner_text() and back.get_by_role("button", name="Make it a goal").count() == 1
    back.get_by_role("button", name="Not a problem").click()
    pg.wait_for_selector('.play-mark[data-kind="hint"]', state="detached", timeout=WAIT_MS)
    assert pg.locator(".play-back").count() == 0
    open_tab(pg, "tech")                                                                                            # and not under another tab, nor again when the hints are asked again
    open_tab(pg, "art")
    pg.wait_for_timeout(500)
    assert pg.locator('.play-mark[data-kind="hint"]').count() == 0
    finish(pg, errors)


def told(pg, host, call, tries: int = 60) -> bool:
    """Whether the host was sent `call` (polled: the answer is the page's, a moment after the press)."""
    for _ in range(tries):
        if call in host.log:
            return True
        pg.wait_for_timeout(100)
    return False


def test_the_concerns_back_makes_a_goal_or_lets_it_be_by_the_concerns_own_commands(gui, rig):
    pg, errors = open_play(gui, rig.host, "tech")
    pg.locator('.play-mark[data-kind="concern"] .play-tag').click()
    pg.get_by_role("button", name="Make it a goal").click()
    assert told(pg, rig.host, ("ideas.concern_goal", {"party": "tech", "id": "c-3"}))                              # the host is told as a map's card tells it (table/concerns.js)
    pg.get_by_role("button", name="Not a problem").click()
    assert told(pg, rig.host, ("ideas.concern_dismiss", {"party": "tech", "id": "c-3"}))
    finish(pg, errors)


def test_hide_the_marks_hides_them_and_shows_them_again_with_no_count_and_no_badge(gui, rig):
    rig.host.hints = [{"kind": "failed", "on": None, "words": "A request failed: POST /api/water 500", "at": 2}]
    pg, errors = open_play(gui, rig.host, "tech")
    pg.locator('.play-mark[data-kind="concern"]').wait_for(timeout=WAIT_MS)
    button = pg.get_by_role("button", name="Hide the marks")
    assert button.get_attribute("aria-pressed") == "false" and button.inner_text().strip() == "Hide the marks"
    button.click()
    assert pg.locator(".play-marks").count() == 0 and pg.get_by_role("button", name="Show the marks").get_attribute("aria-pressed") == "true"
    assert pg.locator(".play-lens__item").count() == 1                                                              # the strip is the lens's, not a mark on the frame
    pg.get_by_role("button", name="Show the marks").click()
    assert pg.locator('.play-mark[data-kind="concern"]').count() == 1
    bar = pg.locator(".play-bar")
    assert not [t for t in bar.locator("*").all_inner_texts() if t.strip().isdigit()] and bar.locator(".ork-count").count() == 0
    finish(pg, errors)


# -- 4. no probe ----------------------------------------------------------------------------------------------------------------------------------

def test_a_play_with_no_probe_says_marks_keep_the_picture_and_the_place_only_on_every_tab(gui, bare):
    pg, errors = open_play(gui, bare.host)
    for slug in ("orkmaster", "art", "tech"):
        open_tab(pg, slug)
        assert strip_text(pg) == "Marks keep the picture and the place only" and pg.locator(".play-lens").get_attribute("data-state") == "noprobe"
    assert pg.locator(".play-marks").count() == 0 and pg.get_by_role("button", name="Mark", exact=True).count() == 1
    assert not any(n == "ideas.play_hints" for n, _ in bare.host.log) and bare.host.events == []                  # nothing is asked of a probe that is not there
    shot(pg, "e115-no-probe.png")
    finish(pg, errors)


# -- the phone-width window keeps the strip inside the pane ---------------------------------------------------------------------------------------------

def test_the_strip_wraps_inside_the_pane_at_the_narrow_width(gui, rig):
    pg, errors = open_play(gui, rig.host, "art", width={"width": 390, "height": 844})
    wait_place(pg, "on Today")
    narrow.no_sideways(pg)
    box, pane = pg.locator(".play-lens").bounding_box(), pg.locator("#table-pane").bounding_box()
    assert box["x"] >= pane["x"] and box["x"] + box["width"] <= pane["x"] + pane["width"] + 1
    finish(pg, errors)
