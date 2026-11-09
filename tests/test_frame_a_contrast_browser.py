"""Spec 168 A7 (decisions §275.1, §283.4, §283.7, §283.9, §285): the frame's new parts keep 4.5:1 and show their focus, in a real browser at 1366 x 768 against a stub host with the lamp's presence.

Contrast: every word of the balloon (its text and its ×), the potion row (the 5 hours' share, *week* and its share, *out*), the unrolled list (the shares, *week*, *back 14:00*, the empty slot), Stop all / Resume, the lamp's chain
(*Here · until 23:00* and *Away · until 19:00*) and the places (*Play*, *Inventory*, *History*) is measured against what it lies on, the lamp lit and out: the element's box is photographed with its words and again with them made invisible (`color: transparent` on
everything); the pixels the glyphs changed (and their neighbours) are what the word lies on, and its own colour (laid over each by its alpha) is compared with each (WCAG 2.x). Focus: tabbing through the right column's head and the hand's places, every control shows a ring
(a box-shadow or an outline that was not there unfocused). A picture to $A7_SHOTS when it is set."""
from __future__ import annotations

import copy
import datetime as dt
import io
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from PIL import Image  # noqa: E402

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost  # noqa: E402
from tests.test_hand_mana_browser import mana_of, tool  # noqa: E402

pytestmark = pytest.mark.browser

VIEW = {"viewport": {"width": 1366, "height": 768}}
HERE = {"here": True, "until": "2026-11-04T23:00", "held": False}
AWAY = {"here": False, "until": "2026-11-05T19:00", "held": False}
MIN = 4.5
SHOTS = Path(os.environ["A7_SHOTS"]) if os.environ.get("A7_SHOTS") else None
LINE = "Claude Code is out until Thu 18:00: the work goes on with Codex."


def week_tool(provider, name, week, five=None, reset=""):
    rows = ([{"window": "5h", "left": five, "reset": reset}] if five is not None else []) + [{"window": "week", "left": week, "reset": ""}]
    return {"provider": provider, "name": name, "left": week if five is None else min(five, week), "rows": rows}


LIMITS = [tool("claude", "Claude Code", 0.62), week_tool("codex", "Codex", 0.5, five=0.0, reset="2026-10-20T14:00:00"), week_tool("agy", "Antigravity", 0.12, five=0.5), tool("cursor", "Cursor", 0.45)]


class FrameHost(HandHost):
    """The hand's host with the lamp (`presence`, turned by `presence.set`), the stop (`stopped`, turned by `halt` and `resume`), the AI tools, a goal at work and the Orkmaster's move to another tool."""

    def __init__(self, presence=HERE):
        super().__init__(extra=True)
        work = next(n for n in self.nodes if n["slug"] == "look")
        work["stage"], work["tasks"][0]["state"] = "implementation", "running"                                  # an ork at work: Stop all is there
        self.presence, self.stopped = copy.deepcopy(presence), False
        self.limits = LIMITS
        self.mana = mana_of("claude", "codex", moved={"from": "claude", "to": "codex", "until": "2026-10-29T18:00", "at": (dt.datetime.now() - dt.timedelta(minutes=5)).isoformat(timespec="seconds"), "line": LINE})

    def snapshot(self):
        doc = super().snapshot()
        doc["state"]["presence"] = copy.deepcopy(self.presence)
        doc["state"]["stopped"] = self.stopped
        doc["state"]["tools"] = {"hand": [{"id": l["provider"], "title": l["name"]} for l in self.limits], "order": [l["provider"] for l in self.limits], "full": False}
        return doc

    def handle(self, name, a):
        if name in ("halt", "resume"):
            self.log.append((name, a))
            self.stopped = name == "halt"
            self.rev += 1
            self.ws.send(json.dumps(self.snapshot()))
            return {"stopped": 1} if self.stopped else {}
        if name == "presence.set":
            self.log.append((name, a))
            self.presence = {"here": a["here"], "until": "2026-11-04T19:00", "held": True}
            self.rev += 1
            self.ws.send(json.dumps(self.snapshot()))
            return self.presence
        return super().handle(name, a)

    def turn(self, **fields):
        for k, v in fields.items():
            setattr(self, k, v)
        self.rev += 1
        self.ws.send(json.dumps(self.snapshot()))


def start(gui, host=None):
    server, browser = gui
    host = host or FrameHost()
    pg = browser.new_context(**VIEW).new_page()
    log: list[str] = []
    pg.on("pageerror", lambda e: log.append(f"pageerror: {e}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(".hand .hand-end", state="attached", timeout=WAIT_MS)
    pg.locator(".pots__row .pot-s").first.wait_for(timeout=WAIT_MS)
    pg.locator(".table-balloon").wait_for(timeout=WAIT_MS)
    pg.locator(".rh-stop").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(700)
    return pg, host, log


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / name))


# ---- WCAG 2.x --------------------------------------------------------------------------------------------------------------------------------------

def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(rgb) -> float:
    r, g, b = (_lin(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b) -> float:
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


PAINT = """(c) => { const x = document.createElement('canvas').getContext('2d'); x.clearRect(0, 0, 1, 1); x.fillStyle = c; x.fillRect(0, 0, 1, 1); return [...x.getImageData(0, 0, 1, 1).data]; }"""
HIDE = "body *, body *::before, body *::after { color: transparent !important; text-shadow: none !important; -webkit-text-fill-color: transparent !important; caret-color: transparent !important; }"


def measure(pg, selector, word=None):
    """The worst contrast of the element `selector`'s own colour against the pixels it lies on: [(text, colour, worst ratio)]. The pointer and the focus are left as they are (the hide sheet changes only colours)."""
    out = []
    for i in range(pg.locator(selector).count()):
        el = pg.locator(selector).nth(i)
        if not el.is_visible():
            continue
        text = (el.inner_text() or el.get_attribute("aria-label") or "").strip().replace("\n", " ")
        if word is not None and word not in text:
            continue
        fg = pg.evaluate(PAINT, el.evaluate("e => getComputedStyle(e).color"))
        box = el.bounding_box()
        el_op = el.evaluate("e => { let o = 1; for (let n = e; n && n !== document.body; n = n.parentElement) o *= Number(getComputedStyle(n).opacity); return o; }")
        clip = {"x": box["x"], "y": box["y"], "width": max(box["width"], 1), "height": max(box["height"], 1)}
        shown = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        pg.add_style_tag(content=HIDE)
        handle = pg.evaluate_handle("() => document.head.lastElementChild")
        try:
            bare = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB")
        finally:
            handle.evaluate("e => e.remove()")
        w, h = bare.size
        ink = {(x, y) for y in range(h) for x in range(w) if shown.getpixel((x, y)) != bare.getpixel((x, y))}              # where the word's glyphs are: what they lie on is the same place without them
        near = {(x + dx, y + dy) for x, y in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1) if 0 <= x + dx < w and 0 <= y + dy < h}
        worst = 99.0
        for px in {bare.getpixel(c) for c in near}:
            a = fg[3] / 255 * el_op
            over = tuple(round(fg[k] * a + px[k] * (1 - a)) for k in range(3))
            worst = min(worst, ratio(over, px))
        if SHOTS and worst < MIN:
            SHOTS.mkdir(parents=True, exist_ok=True)
            bare.save(SHOTS / f"plate-{abs(hash((selector, text)))}.png")
        out.append((text, tuple(fg), round(worst, 2)))
    return out


def check(pg, rows, found):
    for sel, word in rows:
        got = measure(pg, sel, word)
        assert got, f"nothing visible for {sel} {word or ''}"
        for text, fg, r in got:
            found.append((sel, text, r))
            assert r >= MIN, f"{sel} {text!r} in {fg} keeps {r}:1 (< {MIN})"


PARTS = [
    (".table-balloon__line", None), (".table-balloon__x", None),
    (".pots__row .pot-s__five", None), (".pots__row .pot-s__week", None),
    (".rh-stop", None), (".presence-chain__word", None), (".presence-chain__line", None),
    (".hand-end .hand-die__word", None), (".hand-end .stall-pack__word", None), (".hand-end .hand-book__word", None),
]
LIST = [(".pots__all .hand-pot__share", None), (".pots__all .hand-pot__week", None), (".pots__all .hand-pot__back", "back")]


def unroll(pg):
    b = pg.locator(".pots__row").bounding_box()
    pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(200)


def test_the_new_parts_words_keep_4_5_to_1_with_the_lamp_lit_and_out(gui):
    pg, host, log = start(gui)
    found: list = []
    try:
        for state in ("lit", "out"):
            if state == "out":
                pg.mouse.move(5, 5)
                host.turn(presence=copy.deepcopy(AWAY))
                pg.locator(".presence-chain.is-away").wait_for(timeout=WAIT_MS)
                pg.wait_for_timeout(700)
            pg.mouse.move(5, 5)
            pg.wait_for_timeout(200)
            check(pg, PARTS, found)
            unroll(pg)
            check(pg, LIST, found)
            pg.mouse.move(5, 5)
        host.turn(stopped=True)
        pg.locator(".rh-stop.is-resume").wait_for(timeout=WAIT_MS)
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(300)
        check(pg, [(".rh-stop", "Resume")], found)
        print("\n".join(f"{s:42} {t[:40]!r:44} {r}" for s, t, r in found))
    finally:
        pg.close()
    assert not log, "\n".join(log)


RING = """(e) => { const s = getComputedStyle(e); return { shadow: s.boxShadow, outline: s.outlineStyle === 'none' ? '' : `${s.outlineStyle} ${s.outlineWidth} ${s.outlineColor}`, before: getComputedStyle(e, '::before').boxShadow }; }"""


def focus_ring(el):
    return el.evaluate(RING)


def has_ring(now, rest) -> bool:
    return (now["shadow"] != rest["shadow"] and now["shadow"] != "none") or (now["outline"] != "" and now["outline"] != rest["outline"]) or (now["before"] != rest["before"] and now["before"] != "none")


def test_every_control_of_the_head_and_the_places_shows_a_ring_when_tabbed_to(gui):
    pg, host, log = start(gui)
    try:
        controls = [
            (".pots__row .pot-s", "each potion of the row"),
            (".rh-stop", "Stop all"),
            (".presence-chain", "the lamp's chain"),
            (".hand-end .hand-die__play", "the die"),
            (".hand-end .stall-pack", "the backpack"),
            (".hand-end .hand-book", "the book"),
            (".table-balloon__x", "the balloon's ×"),
        ]
        seen = 0
        for sel, what in controls:
            for i in range(pg.locator(sel).count()):
                el = pg.locator(sel).nth(i)
                rest = focus_ring(el)
                pg.mouse.move(5, 5)
                pg.evaluate("() => document.activeElement && document.activeElement.blur()")
                pg.keyboard.press("Tab")                                                                                      # a key press makes the next focus a keyboard focus (:focus-visible)
                el.focus()
                assert pg.evaluate("(e) => e.matches(':focus-visible')", el.element_handle()), f"{what} {i} is not focus-visible"
                assert has_ring(focus_ring(el), rest), f"{what} {i} shows no ring when focused: {focus_ring(el)} (rest {rest})"
                seen += 1
        # the unrolled list: its potions and the empty slot, reached by the keyboard from the row
        pg.locator(".pots__row .pot-s").first.focus()
        pg.locator(".pots[data-open]").wait_for(timeout=WAIT_MS)
        pg.wait_for_timeout(300)
        for sel, what in ((".pots__all .hand-pot", "a potion of the list"), (".pots__all .hand-pot--empty", "the empty slot")):
            for i in range(pg.locator(sel).count()):
                el = pg.locator(sel).nth(i)
                pg.locator(".pots__row .pot-s").first.focus()                                                                   # the list stays unrolled while the focus is inside it: this one is unfocused, another has the focus
                rest = focus_ring(el)
                pg.keyboard.press("Tab")
                el.focus()
                assert has_ring(focus_ring(el), rest), f"{what} {i} shows no ring when focused: {focus_ring(el)} (rest {rest})"
                seen += 1
        assert seen >= 12, seen
        # Tab walks the head in its order: the row, then Stop all and the chain, with the focus never lost
        pg.evaluate("() => document.activeElement.blur()")
        order = []
        pg.locator(".pots__row .pot-s").first.focus()
        for _ in range(14):
            order.append(pg.evaluate("() => { const e = document.activeElement; return e ? (e.className || e.tagName) : ''; }"))
            pg.keyboard.press("Tab")
        assert any("rh-stop" in c for c in order) and any("presence-chain" in c for c in order), order
    finally:
        pg.close()
    assert not log, "\n".join(log)
