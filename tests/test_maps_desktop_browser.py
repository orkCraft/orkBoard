"""Spec 102 part E, the other maps (docs/specs/102-the-other-maps-and-picking-on-them.md §2, §3, §5.3–§5.6; decisions §167.1, §171.1; mockup docs/mockups/s3/ states 3–6), at both widths (`tests/narrow.py`: 1280 × 800, and
390 × 844 with touch), against a stub host of its own (the table's `TableHost`, with a party of each craft: Game design, Tech, Art, Release and Marketing, each with its `party_craft`, and the commands the maps read:
`ideas.loop`, `ideas.loop_set`, `ideas.loop_propose`, `ideas.art_map`, `ideas.release_map`, `ideas.way_map`, `ideas.gate_merge`).

The loop: its cards on a ring with a chevron between each (a row wrapped two a line at 390), a card's face (no element where no goal changed it, the loop's sign in its window, *Proposed by <party>* or *Yours*), a card lifted with what
it rests on (a file opens over the pane, ← lights the card), **Edit** keeping through `ideas.loop_set`, **Propose** when none is kept. Art's lanes by kind, a picture as its own window, a sound's play button, *new*, a picture lifted
large with its variants not picked, a clip's video, *and n more*. Dev and main: a card a goal with its tick, **To main** with the gate's words and a refusal in its own, *Since <version>*. The way in: four steps, a step with nothing to
read its line. Every card wrapped in `Pickable` with its map, id, name and group. No sideways scroll. Screenshots to the directory ORKCRAFT_SHOTS_DIR names when it is set."""
from __future__ import annotations

import base64
import io
import json
import wave
from urllib.parse import quote

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import HEAD, TableHost, party, shot, tab, title, watch  # noqa: E402

pytestmark = pytest.mark.browser

CRAFTS = {"game": "game-design", "tech": "tech", "art": "art", "release": "release"}
COMMIT = "c" * 40


def picture(fill: str, n: int = 16) -> str:
    """A small drawn picture as a data address (a stand-in for a project's file the host would sign)."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{n}" height="{n}"><rect width="{n}" height="{n}" fill="{fill}"/><rect x="4" y="4" width="8" height="8" fill="white"/></svg>'
    return "data:image/svg+xml;utf8," + quote(svg)


def sound() -> str:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 800)
    return "data:audio/wav;base64," + base64.b64encode(buf.getvalue()).decode()


def asset(path, kind, goal="", change="", **more):
    return {"id": path, "kind": kind, "name": path.rsplit("/", 1)[-1], "bytes": 2048, "w": None, "h": None, "seconds": None, "goal": goal, "task": "", "at": "2026-10-28T09:00:00", "change": change,
            "folder": path.rpartition("/")[0] + "/" if "/" in path else "./", "url": more.pop("url", picture("#888")), **more}


LOOP = [
    {"id": "join-a-match", "name": "Join a match", "line": "Friends meet in a lobby and each picks a hero.", "rests_on": ["config/balance.ts", "levels/arena-1.json"], "by": "leader", "at": "2026-10-28T08:00:00"},
    {"id": "hold-the-tower", "name": "Hold the tower", "line": "Ninety seconds to keep your tower standing.", "rests_on": ["config/balance.ts"], "by": "person", "at": "2026-10-28T08:30:00"},
    {"id": "score-the-round", "name": "Score the round", "line": "The last tower standing earns the most coins.", "rests_on": [], "by": "leader", "at": "2026-10-28T08:00:00"},
    {"id": "spend-the-coins", "name": "Spend the coins", "line": "Coins buy a new hero or a tower skin.", "rests_on": ["config/shop.ts"], "by": "leader", "at": "2026-10-28T08:00:00"},
    {"id": "open-a-new-arena", "name": "Open a new arena", "line": "Every fifth win opens the next arena.", "rests_on": ["levels/"], "by": "leader", "at": "2026-10-28T08:00:00"},
]


class Refused(Exception):
    """A command the host refuses in plain words."""


class MapsHost(TableHost):
    def __init__(self):
        super().__init__(rich=False)
        for p in self.parties:
            p["party_craft"] = CRAFTS[p["slug"]]
        market = party("market", len(self.parties))
        market["title"] = market["short"] = "Marketing"
        market["leader"] = {**market["leader"], "head": HEAD("gnome", "elder", "marketing")}
        market["party_craft"] = "marketing"
        self.parties.append(market)
        self.loop = json.loads(json.dumps(LOOP))
        self.proposal = {"asked": True}
        self.refuse = ""
        self.assets = self._assets()
        self.goals = [{"idea": "timer", "title": "Round timer shows on every phone", "element": "meadow", "commit": "a3f9c21" + "0" * 33, "ticked": True},
                      {"idea": "seat", "title": "Reconnect keeps your seat in the lobby", "element": "ice", "commit": "7be40d5" + "0" * 33, "ticked": True},
                      {"idea": "music", "title": "Lobby music loop", "element": "void", "commit": "c81f2ae" + "0" * 33, "ticked": True},
                      {"idea": "reset", "title": "The timer doesn't reset after a reconnect", "element": "lava", "commit": "0d9a6f3" + "0" * 33, "ticked": False}]
        self.way = {"channels": {"holds": [], "none": True, "more": 0},
                    "store": {"holds": [{"path": "fastlane/metadata/en-US/title.txt", "kind": "store"}, {"path": "fastlane/metadata/en-US/short_description.txt", "kind": "store"},
                                        {"path": "site/index.html", "kind": "site"}, {"path": "store/screenshots.md", "kind": "store"}], "none": False, "more": 3},
                    "install": {"holds": [{"path": "Dockerfile", "kind": "install"}, {"path": "fastlane/Fastfile", "kind": "install"}], "none": False, "more": 0},
                    "first_session": {"holds": [{"path": "src/App.tsx", "kind": "entry"}], "none": False, "more": 0}}

    @staticmethod
    def _assets():
        art = [asset("sprites/hero-idle.png", "art", "timer", w=16, h=16, url=picture("#c9a227"),
                     others={"goal": "timer", "pick": "k1-r1", "picked": "a", "variants": [{"key": "b", "name": "No cape", "mime": "image/png", "url": picture("#445")},
                                                                                         {"key": "c", "name": "Round head", "mime": "image/png", "url": picture("#454")}]}),
               asset("sprites/coin.png", "art", "seat", "added", w=16, h=16, url=picture("#d4af37"))]
        art += [asset(f"sprites/tile-{i}.png", "art", w=16, h=16, url=picture("#556")) for i in range(6)]
        return [{"kind": "art", "own": True, "n": 40, "folders": [{"folder": "sprites/", "n": 40}], "assets": art},
                {"kind": "sound", "own": True, "n": 12, "folders": [{"folder": "sounds/", "n": 12}],
                 "assets": [asset("sounds/hit-thud.wav", "sound", "music", seconds=0.4, url=sound()), asset("sounds/win-jingle.wav", "sound", seconds=1.2, url=sound())]},
                {"kind": "music", "own": True, "n": 3, "folders": [{"folder": "music/", "n": 3}], "assets": [asset("music/lobby-loop.ogg", "music", "music", "changed", seconds=72, url=sound())]},
                {"kind": "clip", "own": True, "n": 2, "folders": [{"folder": "clips/", "n": 2}], "assets": [asset("clips/intro.mp4", "clip", seconds=8, url="data:video/mp4;base64,AAAA")]}]

    def handle(self, name, a):
        if name == "ideas.loop":
            self.log.append((name, a))
            return {"cards": json.loads(json.dumps(self.loop)), "proposing": False, "status": "", "party": "game"}
        if name == "ideas.loop_set":
            self.log.append((name, a))
            self.loop = [{**c, "by": "person"} for c in a["cards"]]
            self.rev += 1
            return {"ok": True, "cards": self.loop, "dropped": []}
        if name == "ideas.loop_propose":
            self.log.append((name, a))
            if self.proposal.get("asked"):
                self.loop = json.loads(json.dumps(LOOP))
                self.rev += 1
            return {"ok": True, **self.proposal}
        if name == "ideas.art_map":
            self.log.append((name, a))
            return {"commit": COMMIT, "short": COMMIT[:7], "ref": "dev", "since": a.get("since", ""), "none": not self.assets, "kinds": self.assets, "stacks": [], "removed": [],
                    "goals": {"timer": {"title": "Hero art", "element": "meadow"}, "seat": {"title": "Reconnect keeps your seat in the lobby", "element": "ice"}, "music": {"title": "Lobby music loop", "element": "void"}}}
        if name == "ideas.release_map":
            self.log.append((name, a))
            return {"into": "dev", "main": "main", "same": False, "commits": 6, "files": 14, "goals": self.goals, "since": {"version": "1.3", "out": "2026-10-19T10:00:00"}}
        if name == "ideas.way_map":
            self.log.append((name, a))
            return {"commit": COMMIT, "short": COMMIT[:7], "ref": "dev", "steps": ["channels", "store", "install", "first_session"], **self.way}
        if name == "ideas.gate_merge":
            self.log.append((name, a))
            if self.refuse:
                raise Refused(self.refuse)
            self.goals = []
            self.rev += 1
            return {"ok": True, "commit": "abc1234", "note": ""}
        return super().handle(name, a)

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            try:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
            except Refused as e:
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": str(e)}))
        ws.on_message(on_message)


PROBE = """async () => {
  const m = await import('/static/js/table/maps.js'), { h } = await import('preact');
  m.pickWith(({ children, map, id, name, group }) => h('div', { class: 'probe', 'data-map': map, 'data-id': id, 'data-name': name, 'data-group': group }, children));
}"""


@pytest.fixture(params=narrow.WIDTHS)
def maps(gui, request):
    """The window at one of the two widths against a MapsHost: `(page, host, width)`; the page's errors are asserted at the end."""
    errors: list[str] = []
    server, browser = gui
    host = MapsHost()
    pg = narrow.page(browser, request.param)
    watch(pg, errors)
    pg.add_init_script("window.__played = []; const play = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { window.__played.push(this.src.slice(0, 20)); return Promise.resolve(); };")
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def go(pg, slug):
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


def card(pg, cid):
    return pg.locator(f'.mp-card[data-id="{cid}"]')


def lifted(pg):
    return pg.locator(".table-back")


def names(pg, sel=".mp-card"):
    return [n.strip() for n in pg.locator(f"{sel} .mp-card__nm").all_text_contents()]


# -- the loop ------------------------------------------------------------------------------------------------------------------------------------------

def test_the_loop_is_its_cards_on_a_ring_with_chevrons_or_two_a_line_at_the_narrow_width(maps):
    pg, host, w = maps
    go(pg, "game")
    pg.locator(".mp-card").first.wait_for(timeout=WAIT_MS)
    assert title(pg) == "The whole project · through Game design" and names(pg) == ["Join a match", "Hold the tower", "Score the round", "Spend the coins", "Open a new arena"]
    first, mine = card(pg, "join-a-match"), card(pg, "hold-the-tower")
    assert first.locator(".ork-elem").count() == 0                                                                       # no goal changed it: no element
    assert first.locator(".mp-win .ork-sign.big.mechanic").count() == 1 and first.locator(".mp-card__nm").evaluate("e => getComputedStyle(e).fontFamily").lower().count("pixel") == 0
    assert mine.locator(".mp-card__foot").inner_text() == "Ninety seconds to keep your tower standing."
    if wide(w):
        assert pg.locator(".mp-ring").count() == 1 and pg.locator(".mp-ring__chev").count() == 5 and pg.locator(".mp-ring__line ellipse").count() == 1
        assert first.locator(".mp-card__l").text_content() == "Proposed by Game design" and first.locator(".ork-race__head").count() == 1      # its party, its leader's head at the right
        assert mine.locator(".mp-card__l").text_content() == "Yours" and mine.locator(".ork-race__head").count() == 0
        ring, boxes = pg.locator(".mp-ring").bounding_box(), [card(pg, c["id"]).bounding_box() for c in LOOP]
        assert all(b["x"] >= ring["x"] - 1 and b["x"] + b["width"] <= ring["x"] + ring["width"] + 1 for b in boxes)                  # all inside the ring's width
        assert boxes[0]["y"] < boxes[2]["y"] and abs((boxes[0]["x"] + boxes[0]["width"] / 2) - (ring["x"] + ring["width"] / 2)) < 4     # the first at the top, clockwise
        assert pg.locator(".mp-ring__mid").inner_text().replace("\n", " ").endswith("Five steps, round and round")
    else:
        assert pg.locator(".mp-ring").count() == 0 and first.locator(".mp-card__l").text_content() == "1 of 5"
        a, b = first.bounding_box(), mine.bounding_box()
        assert abs(a["y"] - b["y"]) < 2 and b["x"] > a["x"] + a["width"] - 1                                               # two a line
        assert "Proposed by Game design" in first.inner_text() and "Yours" in mine.inner_text()
    shot(pg, f"maps-loop-{w}.png")


def test_a_loop_card_lifted_shows_what_it_rests_on_and_a_file_opens_over_the_pane_then_back_lights_the_card(maps):
    pg, host, w = maps
    go(pg, "game")
    card(pg, "join-a-match").locator(".mp-card__nm").click()
    back = lifted(pg)
    back.wait_for(timeout=WAIT_MS)
    assert back.get_attribute("data-lifted") == "t:map:game-design:join-a-match" and card(pg, "join-a-match").get_attribute("data-lkey") == "t:map:game-design:join-a-match"
    assert "Friends meet in a lobby" in back.inner_text() and "Proposed by Game design" in back.inner_text()
    assert [b.inner_text() for b in back.locator(".mp-file").all()] == ["config/balance.ts", "levels/arena-1.json"]
    shot(pg, f"maps-loop-lifted-{w}.png")
    back.locator(".mp-file").first.click()
    pg.locator('.table-over[data-kind="file"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Loop · config/balance.ts"                                                                       # it says where it came from
    pg.locator(".table-title__back").click()
    pg.locator('.mp-card[data-id="join-a-match"].is-lit').wait_for(timeout=WAIT_MS)                                      # the card it came from, lit
    card(pg, "join-a-match").click()
    pg.locator(".table-back").wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)
    card(pg, "score-the-round").locator(".mp-card__nm").click()
    assert "It rests on no file yet" in lifted(pg).inner_text()                                                         # a card that rests on nothing says so


def test_edit_keeps_the_cards_name_line_and_files_through_loop_set(maps):
    pg, host, w = maps
    go(pg, "game")
    card(pg, "spend-the-coins").locator(".mp-card__nm").click()
    back = lifted(pg)
    back.get_by_role("button", name="Edit").click()
    back.locator('input[name="name"]').fill("Buy a hero")
    back.locator('textarea[name="line"]').fill("Coins buy a hero.")
    back.locator('textarea[name="files"]').fill("config/shop.ts\nlevels/")
    shot(pg, f"maps-loop-edit-{w}.png")
    back.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => [...document.querySelectorAll('.mp-card__nm')].some((e) => e.textContent.trim() === 'Buy a hero')", timeout=WAIT_MS)
    sent = [a for n, a in host.log if n == "ideas.loop_set"]
    assert len(sent) == 1 and [c["name"] for c in sent[0]["cards"]] == ["Join a match", "Hold the tower", "Score the round", "Buy a hero", "Open a new arena"]
    assert sent[0]["cards"][3] == {"id": "spend-the-coins", "name": "Buy a hero", "line": "Coins buy a hero.", "rests_on": ["config/shop.ts", "levels/"]}
    assert card(pg, "spend-the-coins").locator(".mp-card__nm").text_content().strip() == "Buy a hero"


def test_with_no_loop_kept_the_map_says_so_and_propose_asks_once(maps):
    pg, host, w = maps
    host.loop = []
    go(pg, "game")
    pg.locator(".mp-nothing").wait_for(timeout=WAIT_MS)
    assert "Nothing to read yet: the game's configs" in pg.locator(".mp-nothing").inner_text() and pg.locator(".mp-card").count() == 0
    shot(pg, f"maps-loop-none-{w}.png")
    pg.get_by_role("button", name="Propose").click()
    pg.locator(".mp-card").first.wait_for(timeout=WAIT_MS)
    assert [a for n, a in host.log if n == "ideas.loop_propose"] == [{}] and len(names(pg)) == 5
    host.loop = []
    host.proposal = {"asked": False, "why": "Game design has no tool to ask"}
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.locator(".mp-nothing").wait_for(timeout=WAIT_MS)
    pg.get_by_role("button", name="Propose").click()
    pg.get_by_role("alert").wait_for(timeout=WAIT_MS)
    assert pg.get_by_role("alert").inner_text() == "Game design has no tool to ask"


# -- Art's assets --------------------------------------------------------------------------------------------------------------------------------------

def test_the_kinds_are_lanes_a_picture_is_its_own_window_a_sound_has_a_play_button_and_new_is_a_gem(maps):
    pg, host, w = maps
    go(pg, "art")
    pg.locator(".mp-lane").first.wait_for(timeout=WAIT_MS)
    assert [h.text_content().strip() for h in pg.locator(".mp-lane__head .ork-label").all()] == ["Art and icons", "Sound", "Music", "Clips"]       # Art's kinds, in order
    assert pg.locator('.mp-lane[data-kind="art"] .mp-cap').first.inner_text() == "sprites/: 40 pictures" and pg.locator('.mp-lane[data-kind="sound"] .mp-cap').first.inner_text() == "sounds/: 12 sounds"
    hero, coin, thud = card(pg, "sprites/hero-idle.png"), card(pg, "sprites/coin.png"), card(pg, "sounds/hit-thud.wav")
    assert hero.locator(".mp-win img").get_attribute("src").startswith("data:image/svg+xml") and hero.locator(".mp-win img.is-pixel").count() == 1      # the picture is the window
    assert hero.locator(".ork-elem.meadow").count() == 1 and card(pg, "sounds/win-jingle.wav").locator(".ork-elem").count() == 0                  # an element only where a goal made it
    assert hero.locator(".ork-gem").count() == 0 and coin.locator(".ork-gem").inner_text() == "new" and card(pg, "music/lobby-loop.ogg").locator(".ork-gem").inner_text() == "changed"
    assert hero.locator(".mp-card__l").text_content() == "16 × 16" and thud.locator(".mp-card__l").text_content() == "0.4 s" and card(pg, "music/lobby-loop.ogg").locator(".mp-card__l").text_content() == "1:12"
    assert thud.locator(".mp-win .ork-sign.big.tune").count() == 1 and thud.locator(".mp-play").count() == 1 and hero.locator(".mp-play").count() == 0
    thud.locator(".mp-play").click()
    assert pg.evaluate("window.__played.length") == 1 and pg.evaluate("window.__played[0]").startswith("data:audio/wav")     # a press on play plays the sound ...
    assert pg.locator(".table-back").count() == 0                                                                        # ... and does not lift the card
    shown = 6 if wide(w) else 4
    assert pg.locator(".mp-lane[data-kind='art'] .mp-card").count() == shown and pg.get_by_role("button", name=f"and {8 - shown} more").count() == 1      # six shown (four at 390), the rest behind a press
    shot(pg, f"maps-art-{w}.png")


def test_an_asset_lifted_shows_large_with_its_file_and_the_variants_not_picked_and_a_sound_and_a_clip_have_players(maps):
    pg, host, w = maps
    go(pg, "art")
    card(pg, "sprites/hero-idle.png").locator(".mp-card__nm").click()
    back = lifted(pg)
    back.wait_for(timeout=WAIT_MS)
    assert back.locator(".mp-big img").get_attribute("src").startswith("data:image/svg+xml")
    assert back.locator(".mp-file").inner_text() == "sprites/hero-idle.png" and "16 × 16" in back.inner_text() and "In “Hero art”" in back.inner_text()
    assert [c.inner_text() for c in back.locator(".mp-variant .mp-cap").all()] == ["No cape", "Round head"] and "variants not picked" in back.inner_text().lower()
    if wide(w):
        assert back.bounding_box()["width"] >= 400                                                                       # an asset large wants room
    shot(pg, f"maps-art-lifted-{w}.png")
    back.locator(".mp-file").click()
    pg.locator('.table-over[data-kind="file"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "Assets · sprites/hero-idle.png"
    pg.locator(".table-title__back").click()
    pg.locator('.mp-card[data-id="sprites/hero-idle.png"].is-lit').wait_for(timeout=WAIT_MS)
    card(pg, "sounds/win-jingle.wav").locator(".mp-card__nm").click()
    assert lifted(pg).locator("audio[controls]").count() == 1 and lifted(pg).locator(".mp-big .ork-sign.big.tune").count() == 1
    pg.keyboard.press("Escape")
    card(pg, "clips/intro.mp4").locator(".mp-play").click()                                                              # a clip's play lifts it, its video there
    pg.wait_for_function("() => document.querySelector('.table-back video[controls]')", timeout=WAIT_MS)
    assert lifted(pg).get_attribute("data-lifted") == "t:map:art:clips/intro.mp4"
    shot(pg, f"maps-art-clip-{w}.png")


def test_and_n_more_opens_the_rest_of_a_lane_and_what_is_new_is_new_once(maps):
    pg, host, w = maps
    go(pg, "art")
    lane = pg.locator('.mp-lane[data-kind="art"]')
    lane.locator(".mp-card").first.wait_for(timeout=WAIT_MS)
    shown = 6 if wide(w) else 4
    more = lane.get_by_role("button", name=f"and {8 - shown} more")
    assert more.count() == 1 and lane.locator(".mp-card").count() == shown
    more.click()
    assert lane.locator(".mp-card").count() == 8 and lane.locator(".mp-more").count() == 0
    assert [a for n, a in host.log if n == "ideas.art_map"][0] == {}                                                      # a first look has nothing to be new against
    go(pg, "game")
    go(pg, "art")
    pg.wait_for_function("() => document.querySelectorAll('.mp-lane').length === 4", timeout=WAIT_MS)
    reads = [a for n, a in host.log if n == "ideas.art_map"]
    assert reads[-1] == {"since": COMMIT}                                                                                 # leaving the map was a look at it: the next read is against that commit


# -- Release: dev and main -----------------------------------------------------------------------------------------------------------------------------

def test_dev_and_main_is_a_card_a_goal_ticked_to_main_with_the_gates_words_and_since_faint(maps):
    pg, host, w = maps
    go(pg, "release")
    pg.locator(".mp-goal").first.wait_for(timeout=WAIT_MS)
    assert title(pg) == "The whole project · through Release"
    assert names(pg, ".mp-goals") == ["Round timer shows on every phone", "Reconnect keeps your seat in the lobby", "Lobby music loop", "The timer doesn't reset after a reconnect"]
    timer, left = card(pg, "timer"), card(pg, "reset")
    assert timer.locator(".ork-elem.meadow").count() == 1 and timer.locator(".mp-card__l").text_content() == "a3f9c21" and timer.locator(".mp-tick").get_attribute("aria-label") == "In the merge"
    assert "is-ghost" in left.get_attribute("class") and left.locator(".mp-tick").get_attribute("aria-label") == "Not in the merge"
    assert "3 ticked" in pg.locator(".mp-dev__head").inner_text() and "4 goals" in pg.locator(".mp-dev__head").inner_text()
    to_main = pg.get_by_role("button", name="To main")
    assert to_main.count() == 1 and to_main.is_enabled() and "Merges dev into main whole: 4 goals" in pg.locator(".mp-tomain").inner_text()
    assert "6 commits to take, 14 files changed" in pg.locator(".mp-checks").inner_text()                                    # the gate's words
    since = pg.locator(".mp-since")
    assert since.text_content().startswith("Since 1.3") and "Out 19 Oct" in since.text_content()
    assert since.locator(".ork-label").evaluate("e => getComputedStyle(e).color") != pg.locator(".mp-dev__head .ork-label").evaluate("e => getComputedStyle(e).color")      # faint: not the ink of the rest
    foot, box = pg.locator(".mp-tomain").bounding_box(), pg.locator(".mp-since").bounding_box()
    assert box["y"] > foot["y"]                                                                                           # Since lies under To main
    shot(pg, f"maps-release-{w}.png")
    timer.locator(".mp-card__nm").click()
    assert "Pick this goal" in lifted(pg).inner_text() and "not in main yet" in lifted(pg).inner_text()
    shot(pg, f"maps-release-lifted-{w}.png")
    pg.keyboard.press("Escape")
    to_main.click()
    pg.wait_for_function("() => document.querySelectorAll('.mp-goal').length === 0", timeout=WAIT_MS)
    assert [a for n, a in host.log if n == "ideas.gate_merge"] == [{}]                                                    # today's command, nothing else
    assert "belong to no goal" in pg.locator(".mp-dev").inner_text()               # the commits are still there: dev is as the stub left it


def test_a_refused_merge_says_why_in_the_gates_words(maps):
    pg, host, w = maps
    host.refuse = "dev and main conflict in server/lobby.ts: merge main into dev first"
    go(pg, "release")
    pg.get_by_role("button", name="To main").click()
    pg.locator(".mp-checks .mp-bad").wait_for(timeout=WAIT_MS)
    assert "conflict in server/lobby.ts" in pg.locator(".mp-checks .mp-bad").inner_text() and pg.locator(".mp-goal").count() == 4         # main as it was
    shot(pg, f"maps-release-refused-{w}.png")


# -- Marketing: the way in -----------------------------------------------------------------------------------------------------------------------------

def test_the_way_in_is_four_steps_a_step_with_nothing_says_what_would_be_read(maps):
    pg, host, w = maps
    go(pg, "market")
    pg.locator(".mp-step").first.wait_for(timeout=WAIT_MS)
    heads = [h.text_content().strip() for h in pg.locator(".mp-step__head .ork-label").all()]
    assert heads == ["1 · Channels", "2 · The store page or the site", "3 · The install", "4 · The first session"]
    assert "Nothing to read yet: the campaigns' folders" in pg.locator('.mp-step[data-step="channels"]').inner_text()
    assert names(pg, '.mp-step[data-step="store"]') == ["title.txt", "short_description.txt", "index.html", "screenshots.md"] and "and 3 more" in pg.locator('.mp-step[data-step="store"]').inner_text()
    title_card = card(pg, "fastlane/metadata/en-US/title.txt")
    assert title_card.locator(".ork-elem").count() == 0 and title_card.locator(".ork-gem").count() == 0                    # no goal changed it: no element, no gem
    assert title_card.locator(".mp-card__l").text_content() == "fastlane/metadata/en-US/title.txt" and title_card.locator(".mp-win .ork-sign.big.store").count() == 1
    assert card(pg, "site/index.html").locator(".ork-sign.big.landing").count() == 1 and card(pg, "src/App.tsx").locator(".ork-sign.big.screen").count() == 1
    boxes = [pg.locator(f'.mp-step[data-step="{s}"]').bounding_box() for s in ("channels", "store", "install", "first_session")]
    if wide(w):
        assert len({round(b["y"]) for b in boxes}) == 1 and [b["x"] for b in boxes] == sorted(b["x"] for b in boxes) and pg.locator(".mp-step__chev").count() == 3
    else:
        assert [b["y"] for b in boxes] == sorted(b["y"] for b in boxes) and len({round(b["x"]) for b in boxes}) == 1             # one under another
    shot(pg, f"maps-way-{w}.png")
    card(pg, "Dockerfile").locator(".mp-card__nm").click()
    back = lifted(pg)
    assert "A file that puts the project on a machine" in back.inner_text()
    shot(pg, f"maps-way-lifted-{w}.png")
    back.locator(".mp-file").click()
    pg.locator('.table-over[data-kind="file"]').wait_for(timeout=WAIT_MS)
    assert title(pg) == "The way in · Dockerfile"


def test_every_card_is_wrapped_in_pickable_with_its_map_id_name_and_group(maps):
    pg, host, w = maps
    pg.evaluate(PROBE)
    expect = {"game": ("game-design", "join-a-match", "Join a match", "loop"), "art": ("art", "sprites/coin.png", "coin.png", "art"), "release": ("release", "seat", "Reconnect keeps your seat in the lobby", "dev"),
              "market": ("marketing", "Dockerfile", "Dockerfile", "install")}
    for slug, (mp, cid, name, group) in expect.items():
        go(pg, slug)
        pg.locator(f'.probe[data-id="{cid}"]').wait_for(timeout=WAIT_MS)
        probe = pg.locator(f'.probe[data-id="{cid}"]')
        assert (probe.get_attribute("data-map"), probe.get_attribute("data-name"), probe.get_attribute("data-group")) == (mp, name, group)
        assert probe.locator(".mp-card").count() == 1
    assert pg.locator(".probe").count() == pg.locator(".mp-card").count()                                                  # every card of the way in is wrapped
