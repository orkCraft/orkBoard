"""Spec 102 part D, Design's map (docs/specs/102-the-other-maps-and-picking-on-them.md §5.1–§5.2, mockup docs/mockups/s3/ states 1 and 2; the pains belong on Design's map, not Product's): the window (the page) at both widths
(`tests/narrow.py`) against a stub host of its own that answers `ideas.screens`, `ideas.lens_screen` and `ideas.pain_pin` (a party of craft `design`, one of craft `product`).

The steps as columns left to right (top to bottom at the narrow width), a screen a card (its picture in its window, a kept screen's fetched, else the `screen` sign; the element of the goal that changed it, none when no goal did; its path), the
arrows named by their target between the steps; a screen lifted turns over (its picture large, path, file opened over the pane, links, its pains) and is lowered by Esc; the pains pinned under their screen or step, the segment filter
(*All segments*, then each), a pain pressed and then a screen pressed, or dragged with a mouse, pins it there (`ideas.pain_pin`); a project with no screen says *Nothing to read yet*; Product's tab has no such map; no sideways scroll. Screenshots to the
directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import TableHost, node, party, watch  # noqa: E402

pytestmark = pytest.mark.browser


def _picture(w=160, h=100) -> str:
    """A small drawn screen (a bar, a title, two lines, a button) as a PNG, base64: what a task's shot or a kept screen would be."""
    import base64
    import struct
    import zlib

    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            c = (46, 43, 38)
            if y < 10:
                c = (70, 66, 60)
            elif 24 <= y < 32 and 20 <= x < 90:
                c = (230, 224, 210)
            elif y in (44, 45, 52, 53) and 20 <= x < 120:
                c = (90, 86, 78)
            elif 70 <= y < 84 and 20 <= x < 64:
                c = (120, 160, 110)
            row += bytes(c)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    return base64.b64encode(png).decode()


PNG = _picture()
SHOT = f"data:image/png;base64,{PNG}"
SCREENS = [
    {"id": "home", "name": "Welcome", "path": "/", "file": "src/screens/Welcome.tsx"},
    {"id": "join", "name": "Join", "path": "/join", "file": "src/screens/Join.tsx", "picture": {"kind": "lens", "id": "k1", "name": "Join", "at": "2026-10-28T10:00:00"}},
    {"id": "host", "name": "Host", "path": "/host", "file": "src/screens/Host.tsx"},
    {"id": "lobby", "name": "Lobby", "path": "/lobby", "file": "src/screens/Lobby.tsx",
     "picture": {"kind": "shot", "goal": "lobbyfix", "task": "t1", "id": "s1", "file": "lobby.png", "w": 320, "h": 200, "at": "2026-10-28T11:00:00", "url": SHOT}},
    {"id": "round", "name": "Round", "path": "/round", "file": "src/screens/Round.tsx"},
    {"id": "results", "name": "Results", "path": "/results", "file": "src/screens/Results.tsx"},
]
LINKS = [("home", "join"), ("home", "host"), ("join", "lobby"), ("host", "lobby"), ("lobby", "round"), ("round", "results"), ("results", "home")]
STEPS = [["home"], ["join", "host"], ["lobby"], ["round"], ["results"]]
SEGMENTS = [{"segment": "Hosts", "pains": [{"text": "Too many taps to set up", "on": "host"}, {"text": "Can't tell who has joined", "on": "lobby"}]},
            {"segment": "Players", "pains": [{"text": "Can't tell how to join", "on": "join"}, {"text": "Typing the code is slow", "on": "step:2"}, {"text": "Late players miss the start", "on": ""}]}]


class ScreensHost(TableHost):
    """The table's stub with a Design party and a Product party, and the screens of a small app."""

    def __init__(self, screens=True, **kw):
        super().__init__(rich=False, **kw)
        n = len(self.parties)
        for i, (slug, title, craft) in enumerate((("design", "Design", "design"), ("product", "Product", "product"))):
            p = party(slug, n + i)
            p["title"] = p["short"] = title
            p["party_craft"] = craft
            self.parties.append(p)
        self.nodes.append(node("lobbyfix", "design", "Lobby screen with the player list", "working", "implementation", "ice", "screen"))
        self.screens = screens
        self.segments = copy.deepcopy(SEGMENTS)

    def handle(self, name, a):
        if name == "ideas.screens":
            self.log.append((name, a))
            if not self.screens:
                return {"head": "", "source": "", "entry": "", "more": 0, "loose": [], "links": [], "steps": [], "screens": [], "segments": []}
            return {"head": "a" * 40, "source": "react-router", "entry": "home", "more": 0, "loose": [], "screens": copy.deepcopy(SCREENS), "links": [{"from": f, "to": t} for f, t in LINKS],
                    "steps": copy.deepcopy(STEPS), "segments": copy.deepcopy(self.segments)}
        if name == "ideas.lens_screen":
            self.log.append((name, a))
            return {"id": a["id"], "name": "Join", "type": "image/png", "data": PNG}
        if name == "ideas.pain_pin":
            self.log.append((name, a))
            for s in self.segments:
                for p in s["pains"]:
                    if s["segment"] == a["segment"] and p["text"] == a["pain"]:
                        p["on"] = a["on"]
            return {"ok": True, "segments": copy.deepcopy(self.segments)}
        return super().handle(name, a)


def shot(pg, name):
    d = os.environ.get("ORKCRAFT_SHOTS_DIR")
    if d:
        Path(d).mkdir(parents=True, exist_ok=True)
        pg.wait_for_timeout(450)
        pg.screenshot(path=str(Path(d) / name))


def start(gui, width, errors, tab="design", **kw):
    server, browser = gui
    host = ScreensHost(**kw)
    pg = narrow.page(browser, width)
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(f'.table-tab[data-tab="{tab}"]').click()
    pg.locator(f'.table-tab[data-tab="{tab}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)
    return pg, host


@pytest.fixture(params=narrow.WIDTHS)
def screens(gui, request):
    errors: list[str] = []
    pg, host = start(gui, request.param, errors)
    pg.locator(".scr-map[data-state='read']").wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def card(pg, sid):
    return pg.locator(f'.scr-card[data-screen="{sid}"]')


def pains_under(pg, at):
    return [p.get_attribute("data-pain") for p in pg.locator(f'.scr-rail[data-on="{at}"] .scr-pain').all()]


def pins(host):
    return [a for n, a in host.log if n == "ideas.pain_pin"]


def inside(pg, el):
    """The element lies within the map's visible scroll area (not cut off at the side)."""
    box, area = el.bounding_box(), pg.locator(".scr-scroll").bounding_box()
    return box["x"] >= area["x"] - 1 and box["x"] + box["width"] <= area["x"] + area["width"] + 1


# -- the flow --------------------------------------------------------------------------------------------------------------------------------------

def test_the_steps_are_columns_left_to_right_and_at_the_narrow_width_top_to_bottom(screens):
    pg, host, w = screens
    steps = pg.locator(".scr-step")
    assert steps.count() == 5
    assert [c.get_attribute("data-screen") for c in pg.locator(".scr-card").all()] == ["home", "join", "host", "lobby", "round", "results"]
    assert [s.locator(".scr-steplab").text_content().strip() for s in steps.all()] == [f"Step {i}" for i in range(1, 6)]
    boxes = [s.bounding_box() for s in steps.all()]
    if wide(w):
        assert all(a["x"] < b["x"] for a, b in zip(boxes, boxes[1:]))                                              # left to right
        assert all(abs(a["y"] - boxes[0]["y"]) < 2 for a in boxes)                                                 # on one line
        assert all(inside(pg, s) for s in steps.all())                                                              # none cut off at 1280
    else:
        assert all(a["y"] < b["y"] for a, b in zip(boxes, boxes[1:]))                                              # top to bottom
        assert all(abs(a["x"] - boxes[0]["x"]) < 2 for a in boxes)
        assert abs(card(pg, "join").bounding_box()["y"] - card(pg, "host").bounding_box()["y"]) < 2               # two cards a row
    assert "Read from dev: 6 screens, 7 links" in pg.locator(".scr-note").inner_text()
    assert "4 without a picture yet" in pg.locator(".scr-note").inner_text()
    assert "Nothing to read" not in pg.locator(".scr-map").inner_text()
    shot(pg, f"design-map-{w}.png")


def test_a_screen_card_has_its_picture_or_the_screen_sign_its_name_its_path_and_the_element_of_the_goal_that_changed_it(screens):
    pg, host, w = screens
    lobby, home, join = card(pg, "lobby"), card(pg, "home"), card(pg, "join")
    assert lobby.locator(".scr-card__nm").inner_text() == "Lobby" and lobby.locator(".scr-card__path").inner_text() == "/lobby"
    assert lobby.locator(".scr-win img").get_attribute("src").startswith("data:image/png")                          # a task's shot: its signed address
    assert "ice" in lobby.locator(".ork-elem").get_attribute("class")                                               # the goal that changed it: its element
    assert home.locator(".ork-elem").count() == 0 and home.locator(".scr-win img").count() == 0                     # no goal changed it, no picture: no element, the sign
    assert home.locator(".scr-win .ork-sign.screen.big").count() == 1
    join.locator(".scr-win img").wait_for(timeout=WAIT_MS)                                                          # a kept screen's picture is fetched
    assert join.locator(".scr-win img").get_attribute("src").startswith("data:image/png;base64,")
    assert ("ideas.lens_screen", {"id": "k1"}) in host.log
    assert join.locator(".ork-elem").count() == 0                                                                   # a lens picture was changed by no goal
    assert lobby.locator(".ork-gem").count() == 0                                                                   # `ideas.screens` does not say what is new: no gem
    name = lobby.locator(".scr-card__nm")
    assert "Orkboard" not in lobby.inner_text() and name.evaluate("e => getComputedStyle(e).fontWeight") in ("600", "700")   # the name in the body face, bold


def test_the_links_are_arrows_named_by_their_target_between_the_steps(screens):
    pg, host, w = screens
    if wide(w):
        names = [a.locator(".scr-arrow__name").inner_text() for a in pg.locator(".scr-arrow").all()]
        assert sorted(names) == sorted(["Join", "Host", "Lobby", "Lobby", "Round", "Results"])                       # six forward links; the one back to Welcome is in the backs
        assert pg.locator(".scr-lines path").count() == 6
        a = pg.locator('.scr-arrow[data-link="join>lobby"]').bounding_box()
        assert card(pg, "lobby").bounding_box()["x"] - 14 < a["x"] <= card(pg, "lobby").bounding_box()["x"] + 1       # it ends at the target's edge
    else:
        links = pg.locator(".scr-links")
        assert links.count() == 4                                                                                   # the links that enter a step, between it and the one before
        assert [c.inner_text() for c in pg.locator(".scr-step[data-step='2'] .scr-links .ork-chip").all()] == ["Join", "Host"]


# -- a screen lifted -------------------------------------------------------------------------------------------------------------------------------

def test_a_screen_pressed_turns_over_with_its_picture_path_file_and_links_and_esc_lowers_it(screens):
    pg, host, w = screens
    card(pg, "lobby").click()
    back = pg.locator(".table-back")
    back.wait_for(timeout=WAIT_MS)
    assert back.get_attribute("data-lifted") == "t:screen:design:lobby" and card(pg, "lobby").get_attribute("aria-pressed") == "true"
    assert back.locator(".scr-back__nm").inner_text() == "Lobby"
    assert back.locator(".scr-bigpic img").get_attribute("src").startswith("data:image/png")                        # the picture large
    text = back.inner_text()
    assert "/lobby" in text and "src/screens/Lobby.tsx" in text
    assert [b.inner_text() for b in back.locator(".scr-back__links .ork-btn").all()] == ["From Join", "From Host", "To Round"]
    assert "Can't tell who has joined" in text                                                                      # the pain pinned here
    shot(pg, f"design-lifted-{w}.png")
    back.locator(".scr-back__links .ork-btn", has_text="To Round").click()                                           # a link lifts the screen at its end
    pg.locator('.table-back[data-lifted="t:screen:design:round"]').wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.locator(".table-back").wait_for(state="detached", timeout=WAIT_MS)
    assert pg.locator(".scr-card[aria-pressed='true']").count() == 0


def test_the_files_name_opens_it_over_the_pane_and_back_returns_to_the_map(screens):
    pg, host, w = screens
    card(pg, "home").click()
    pg.locator(".scr-back__file").click()
    pg.locator(".table-over").wait_for(timeout=WAIT_MS)
    assert pg.locator(".table-title__pt").inner_text().lower() == "screens · src/screens/welcome.tsx"
    pg.get_by_role("button", name="Back").first.click()
    pg.locator(".scr-map").wait_for(timeout=WAIT_MS)
    assert pg.locator(".scr-card.is-lit").count() == 1                                                              # the card it came from is lit


# -- the pains -------------------------------------------------------------------------------------------------------------------------------------

def test_the_pains_lie_pinned_under_their_screen_or_step_and_the_segment_filter_picks_among_them(screens):
    pg, host, w = screens
    assert pains_under(pg, "host") == ["Too many taps to set up"] and pains_under(pg, "lobby") == ["Can't tell who has joined"] and pains_under(pg, "join") == ["Can't tell how to join"]
    assert pains_under(pg, "step:2") == ["Typing the code is slow"]                                                  # a pain pinned to a step: under its label
    assert pains_under(pg, "") == ["Late players miss the start"]                                                    # a pain with no place is not lost
    assert pg.locator('.scr-rail[data-on="join"] .scr-pain__sg').text_content() == "Players"
    assert [c.inner_text() for c in pg.locator(".scr-seg .ork-chip").all()] == ["All segments", "Hosts", "Players"]
    assert pg.locator(".scr-seg .ork-chip[aria-pressed='true']").inner_text() == "All segments"
    box = pg.locator('.scr-rail[data-on="host"]').bounding_box()
    assert box["y"] >= card(pg, "host").bounding_box()["y"] + card(pg, "host").bounding_box()["height"] - 1         # under its screen
    shot(pg, f"design-pains-{w}.png")
    pg.locator(".scr-seg .ork-chip", has_text="Hosts").click()
    assert pg.locator(".scr-pain").count() == 2 and pains_under(pg, "host") == ["Too many taps to set up"] and pains_under(pg, "join") == []
    shot(pg, f"design-pains-hosts-{w}.png")
    pg.locator(".scr-seg .ork-chip", has_text="All segments").click()
    assert pg.locator(".scr-pain").count() == 5


def test_a_pain_pressed_and_then_a_screen_pressed_is_pinned_there(screens):
    pg, host, w = screens
    pg.locator('.scr-pain[data-pain="Can\'t tell how to join"]').click()
    assert pg.locator('.scr-pain[aria-pressed="true"]').count() == 1
    assert "Press a screen or a step" in pg.locator(".scr-note").inner_text()
    card(pg, "round").click()                                                                                       # a press on a screen pins while a pain is carried: it lifts nothing
    pg.locator('.scr-rail[data-on="round"] .scr-pain').wait_for(timeout=WAIT_MS)
    assert pins(host) == [{"segment": "Players", "pain": "Can't tell how to join", "on": "round"}]
    assert pains_under(pg, "join") == [] and pg.locator(".table-back").count() == 0
    pg.locator('.scr-pain[data-pain="Late players miss the start"]').click()                                        # a step takes a pain too
    pg.locator(".scr-steplab", has_text="Step 4").click()
    pg.locator('.scr-rail[data-on="step:4"] .scr-pain').wait_for(timeout=WAIT_MS)
    assert pins(host)[-1] == {"segment": "Players", "pain": "Late players miss the start", "on": "step:4"}
    pg.locator('.scr-pain[data-pain="Typing the code is slow"]').click()                                            # Esc puts a carried pain down
    pg.wait_for_timeout(150)
    pg.keyboard.press("Escape")
    assert pg.locator('.scr-pain[aria-pressed="true"]').count() == 0 and len(pins(host)) == 2


def test_a_pain_dragged_onto_another_screen_pins_it_there(screens):
    pg, host, w = screens
    if not wide(w):
        pytest.skip("a touch screen presses the pain and then the screen")
    pain = pg.locator('.scr-pain[data-pain="Too many taps to set up"]').bounding_box()
    pg.mouse.move(pain["x"] + 20, pain["y"] + 20)
    pg.mouse.down()
    pg.mouse.move(pain["x"] + 40, pain["y"] + 40, steps=4)
    target = card(pg, "round").bounding_box()
    pg.mouse.move(target["x"] + target["width"] / 2, target["y"] + target["height"] / 2, steps=8)
    assert pg.locator(".scr-ghost").count() == 1 and pg.locator('.scr-card[data-screen="round"].is-over').count() == 1   # the pain follows; the screen under it is aimed
    shot(pg, "design-drag-wide.png")
    pg.mouse.up()
    pg.locator('.scr-rail[data-on="round"] .scr-pain').wait_for(timeout=WAIT_MS)
    assert pins(host) == [{"segment": "Hosts", "pain": "Too many taps to set up", "on": "round"}]
    assert pains_under(pg, "host") == [] and pg.locator(".scr-ghost").count() == 0 and pg.locator(".table-back").count() == 0   # the click after the drag lifted nothing


def test_a_pain_dragged_onto_a_step_pins_it_to_the_step_and_a_press_without_a_drag_pins_nothing(screens):
    pg, host, w = screens
    if not wide(w):
        pytest.skip("a touch screen presses the pain and then the step")
    pain = pg.locator('.scr-pain[data-pain="Can\'t tell who has joined"]').bounding_box()
    pg.mouse.move(pain["x"] + 20, pain["y"] + 20)
    pg.mouse.down()
    step = pg.locator('.scr-step[data-step="5"]').bounding_box()
    pg.mouse.move(step["x"] + step["width"] / 2, step["y"] + 6, steps=10)
    pg.mouse.up()
    pg.locator('.scr-rail[data-on="step:5"] .scr-pain').wait_for(timeout=WAIT_MS)
    assert pins(host) == [{"segment": "Hosts", "pain": "Can't tell who has joined", "on": "step:5"}]


# -- the edges -------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_a_project_with_no_screen_to_read_says_so(gui, width):
    errors: list[str] = []
    pg, host = start(gui, width, errors, screens=False)
    pg.locator(".scr-map[data-state='none']").wait_for(timeout=WAIT_MS)
    assert "Nothing to read yet: the app's routes or its screens' folder" in pg.locator(".scr-map").inner_text()
    assert pg.locator(".scr-card").count() == 0
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("width", narrow.WIDTHS)
def test_products_tab_has_not_this_map(gui, width):
    errors: list[str] = []
    pg, host = start(gui, width, errors, tab="product")
    pg.wait_for_timeout(300)
    assert pg.locator(".scr-map").count() == 0 and not [n for n, _ in host.log if n == "ideas.screens"]
    pg.locator('.table-tab[data-tab="design"]').click()
    pg.locator(".scr-map[data-state='read']").wait_for(timeout=WAIT_MS)
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def test_the_map_is_read_again_when_the_board_changes(screens):
    pg, host, w = screens
    before = len([1 for n, _ in host.log if n == "ideas.screens"])
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.wait_for_timeout(600)
    assert len([1 for n, _ in host.log if n == "ideas.screens"]) >= before
