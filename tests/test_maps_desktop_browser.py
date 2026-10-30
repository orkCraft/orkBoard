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


def step(sid, name, line, feel, intensity, gives=(), takes=(), rests_on=(), by="leader"):
    return {"id": sid, "name": name, "line": line, "feel": feel, "intensity": intensity, "gives": list(gives), "takes": list(takes), "rests_on": list(rests_on), "by": by, "at": "2026-10-28T08:00:00"}


LOOP = {
    "version": 2, "by": "leader", "at": "2026-10-28T08:30:00",
    "loops": [
        {"id": "core", "span": "core", "name": "Hold the tower", "line": "What a player repeats every round.", "feeds": "session", "steps": [
            step("join-a-match", "Join a match", "Friends meet in a lobby and each picks a hero.", "fellowship", 2, rests_on=["config/balance.ts", "levels/arena-1.json"]),
            step("hold-the-tower", "Hold the tower", "Ninety seconds to keep your tower standing.", "challenge", 5, rests_on=["config/balance.ts"], by="person"),
            step("score-the-round", "Score the round", "The last tower standing earns the most coins.", "fantasy", 3, gives=["coins"])]},
        {"id": "session", "span": "session", "name": "A night of matches", "line": "Rounds played back to back with friends.", "feeds": "meta", "steps": [
            step("spend-the-coins", "Spend the coins", "Coins buy a new hero or a tower skin.", "expression", 2, takes=["coins"], rests_on=["config/shop.ts"]),
            step("pick-a-hero", "Pick a hero", "Each hero holds a tower another way.", "discovery", 3),
            step("rematch", "Rematch", "The losers ask for one more round.", "challenge", 4)]},
        {"id": "meta", "span": "meta", "name": "The season", "line": "What brings a player back across weeks.", "feeds": "", "steps": [
            step("open-a-new-arena", "Open a new arena", "Every fifth win opens the next arena.", "discovery", 3, rests_on=["levels/"]),
            step("climb-the-ladder", "Climb the ladder", "Wins move the player up a ranked ladder.", "challenge", 4, gives=["gems"]),
            step("show-off", "Show off", "A rank badge sits beside the player's name.", "expression", 2)]}],
    "currencies": [{"id": "coins", "name": "Coins", "kind": "soft", "line": "Earned in every round."}, {"id": "gems", "name": "Gems", "kind": "hard", "line": "Earned on the ladder."}],
    "hooks": [{"when": "D1", "line": "A new hero is free on the first night."}, {"when": "D7", "line": "The season's first ladder reset."}],
}
EMPTY = {"version": 2, "loops": [], "currencies": [], "hooks": [], "by": "", "at": ""}
FINDINGS = ["Gems is only earned: it will pile up"]
STEPS = ["Join a match", "Hold the tower", "Score the round", "Spend the coins", "Pick a hero", "Rematch", "Open a new arena", "Climb the ladder", "Show off"]


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
            return {**json.loads(json.dumps(self.loop)), "findings": FINDINGS if self.loop["loops"] else [], "proposing": False, "status": "", "party": "game"}
        if name == "ideas.loop_set":
            self.log.append((name, a))
            self.loop = {**self.loop, "loops": [{**lp, "id": lp["span"], "steps": [{**s, "by": "person", "at": "2026-10-29T08:00:00"} for s in lp["steps"]]} for lp in a["loops"]], "currencies": a["currencies"], "hooks": a["hooks"], "by": "person"}
            self.rev += 1
            return {"ok": True, **self.loop, "findings": FINDINGS, "dropped": []}
        if name == "ideas.loop_propose":
            self.log.append((name, a))
            if self.proposal.get("asked"):
                was = {k: v for k, v in self.loop.items() if k != "was"}
                self.loop = json.loads(json.dumps(LOOP))
                if was["loops"] and was["by"] == "person":
                    self.loop["was"] = was
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
    if slug == "release" and pg.viewport_size["width"] >= 760:        # at the wide width Release is no tab: it waits in the portal ring's lower left corner (docs/specs/111 §4.1)
        pg.locator(".ork-portal-ring__before").click()
        pg.locator('.table[data-tab="release"]').wait_for(timeout=WAIT_MS)
        return
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


def card(pg, cid):
    return pg.locator(f'.mp-card[data-id="{cid}"]')


def lifted(pg):
    return pg.locator(".table-back")


def names(pg, sel=".mp-card"):
    return [n.strip() for n in pg.locator(f"{sel} .mp-card__nm").all_text_contents()]


# -- the loops -----------------------------------------------------------------------------------------------------------------------------------------

def steps_of(pg):
    return names(pg, ".mp-st")


def centre(box):
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def test_the_loops_lie_as_rings_one_in_another_the_core_inside_or_as_lists_at_the_narrow_width(maps):
    pg, host, w = maps
    go(pg, "game")
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    assert title(pg) == "The whole project · through Game design" and steps_of(pg) == STEPS
    first, mine = card(pg, "join-a-match"), card(pg, "hold-the-tower")
    assert first.locator(".ork-elem").count() == 0                                                                       # no goal changed it: no element
    assert first.locator(".mp-st__meta > span").first.inner_text() == "fellowship" and first.locator(".mp-pips i.d").count() == 2 and mine.locator(".mp-pips i.d").count() == 5      # its feeling, its intensity drawn
    if wide(w):
        assert pg.locator(".mp-rings").count() == 1 and pg.locator(".mp-ring").count() == 3 and pg.locator(".mp-rings__line ellipse").count() == 3
        tags = [t.replace("\n", " ").lower() for t in pg.locator(".mp-ring__tag").all_inner_texts()]
        assert tags[0] == "core · seconds hold the tower" and "feeds the session loop" in pg.locator(".mp-ring__tag").first.get_attribute("title")
        assert tags[1].startswith("session · minutes a night of matches") and tags[2].startswith("meta · days and weeks the season")       # each ring: its span and its name
        assert pg.locator(".mp-ring__chev").count() == 6 and pg.locator(".mp-ring[data-span=\"core\"] .mp-st").count() == 3
        ring = pg.locator(".mp-rings").bounding_box()
        cx, cy = centre(ring)
        far = {}
        for span, ids in (("core", ["join-a-match", "hold-the-tower", "score-the-round"]), ("session", ["spend-the-coins", "pick-a-hero", "rematch"]), ("meta", ["open-a-new-arena", "climb-the-ladder", "show-off"])):
            boxes = [card(pg, i).bounding_box() for i in ids]
            assert all(b["x"] >= ring["x"] - 1 and b["x"] + b["width"] <= ring["x"] + ring["width"] + 1 for b in boxes)                  # inside the rings' width
            far[span] = sum(((centre(b)[0] - cx) ** 2 + (centre(b)[1] - cy) ** 2) ** 0.5 for b in boxes) / len(boxes)
        assert far["core"] < far["session"] < far["meta"]                                                                   # the core inside, the meta outside
        every = [card(pg, i).bounding_box() for i in ("join-a-match", "hold-the-tower", "score-the-round", "spend-the-coins", "pick-a-hero", "rematch", "open-a-new-arena", "climb-the-ladder", "show-off")]
        for a in range(len(every)):                                                                                          # no step lies on another
            for b in range(a + 1, len(every)):
                p, q = every[a], every[b]
                assert p["x"] + p["width"] <= q["x"] + 1 or q["x"] + q["width"] <= p["x"] + 1 or p["y"] + p["height"] <= q["y"] + 1 or q["y"] + q["height"] <= p["y"] + 1, (a, b)
    else:
        assert pg.locator(".mp-rings").count() == 0 and pg.locator(".mp-ll").count() == 3                                  # the loops as lists
        assert pg.locator('.mp-ll[data-span="core"] .ork-label').inner_text().lower() == "core · seconds"
        assert pg.locator('.mp-ll[data-span="session"] .mp-st').count() == 3 and "Hold the tower" in pg.locator('.mp-ll[data-span="core"]').inner_text()
        assert "Ninety seconds to keep your tower standing." in mine.inner_text()                                           # a step in a list says its line
    shot(pg, f"maps-loop-{w}.png")


def test_the_economy_the_feeling_and_what_the_loop_says(maps):
    pg, host, w = maps
    go(pg, "game")
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    says = pg.locator(".mp-says__line")                                                                                      # above: one alert line a finding
    assert says.all_inner_texts() == FINDINGS and says.first.get_attribute("data-tone") == "alert" and says.first.locator(".ork-sign.alert").count() == 1
    coins, gems = pg.locator('.mp-eco__row[data-currency="coins"]'), pg.locator('.mp-eco__row[data-currency="gems"]')      # the economy: what gives it, it, what takes it
    assert pg.locator(".mp-eco__row").count() == 2 and coins.locator(".mp-card__nm").inner_text() == "Coins" and gems.locator(".mp-card__nm").inner_text() == "Gems"
    assert coins.locator(".mp-eco__side.is-in li").all_inner_texts() == ["Score the round"] and coins.locator(".mp-eco__side.is-out li").all_inner_texts() == ["Spend the coins"]
    assert gems.locator(".mp-eco__side.is-in li").all_inner_texts() == ["Climb the ladder"] and gems.locator(".mp-eco__side.is-out .mp-eco__none").inner_text() == "nothing"
    hooks = pg.locator(".mp-hooks__list li")                                                                                 # why a player comes back
    assert hooks.count() == 2 and [h.locator(".mp-hooks__when").inner_text() for h in hooks.all()] == ["D1", "D7"] and "A new hero is free" in hooks.first.inner_text()
    feel = pg.locator(".mp-feel")                                                                                            # the feeling: the session loop's steps, each point its feeling's word
    assert "a night of matches (session)" in feel.locator(".ork-label").inner_text().lower() and pg.locator(".mp-feel__pt").count() == 3
    assert [p.get_attribute("data-feel") for p in pg.locator(".mp-feel__pt").all()] == ["expression", "discovery", "challenge"]
    assert [p.get_attribute("data-intensity") for p in pg.locator(".mp-feel__pt").all()] == ["2", "3", "4"] and [t.text_content() for t in feel.locator(".mp-feel__word").all()] == ["expression", "discovery", "challenge"]
    d = feel.locator(".mp-feel__line").get_attribute("d")
    assert d.startswith("M ") and d.count("H") >= 3 and d.count("V") == 2                                                    # a stepped line: across, then up or down
    ys = [float(p.locator(".mp-feel__dot").get_attribute("y")) for p in pg.locator(".mp-feel__pt").all()]
    assert ys[0] > ys[1] > ys[2]                                                                                             # the more intense, the higher
    if wide(w):
        rings, eco, box = pg.locator(".mp-rings").bounding_box(), pg.locator(".mp-eco").bounding_box(), pg.locator(".mp-feel").bounding_box()
        assert eco["x"] >= rings["x"] + rings["width"] - 1 and box["y"] >= rings["y"] + rings["height"] - 1                  # the economy at the right, the feeling under the rings
    else:
        lists, eco, box = pg.locator(".mp-lists").bounding_box(), pg.locator(".mp-eco").bounding_box(), pg.locator(".mp-feel").bounding_box()
        assert eco["y"] >= lists["y"] + lists["height"] - 1 and box["y"] >= eco["y"] + eco["height"] - 1                      # under the lists: the economy, then the feeling
    feel.locator('.mp-feel__pt[data-feel="discovery"]').click()                                                              # a press on a point lifts its step
    back = lifted(pg)
    back.wait_for(timeout=WAIT_MS)
    assert back.get_attribute("data-lifted") == "t:map:game-design:pick-a-hero"
    shot(pg, f"maps-loop-economy-{w}.png")


def test_the_feeling_is_the_core_loops_when_there_is_no_session_loop(maps):
    pg, host, w = maps
    host.loop["loops"] = [lp for lp in host.loop["loops"] if lp["span"] != "session"]
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    go(pg, "game")
    pg.locator(".mp-feel__pt").first.wait_for(timeout=WAIT_MS)
    assert [p.get_attribute("data-feel") for p in pg.locator(".mp-feel__pt").all()] == ["fellowship", "challenge", "fantasy"] and pg.locator(".mp-ring").count() == (2 if wide(w) else 0) and pg.locator(".mp-ll").count() == (0 if wide(w) else 2)


def test_a_pixel_dot_steps_round_the_core_ring_while_a_task_of_the_party_runs_and_not_under_reduced_motion(maps):
    pg, host, w = maps
    go(pg, "game")
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    if not wide(w):
        assert pg.locator(".mp-orbit").count() == 0                                                                          # lists have no ring to go round
        return
    dot = pg.locator(".mp-orbit")
    dot.wait_for(timeout=WAIT_MS)
    css = dot.evaluate("e => { const s = getComputedStyle(e); return [s.animationName, s.animationTimingFunction, s.offsetPath, s.display]; }")
    assert css[0] == "mp-orbit" and css[1].startswith("steps(28") and css[2].startswith("path(") and css[3] != "none"           # stepped, never gliding
    before = dot.bounding_box()
    pg.wait_for_function("(b) => { const r = document.querySelector('.mp-orbit').getBoundingClientRect(); return Math.abs(r.x - b.x) + Math.abs(r.y - b.y) > 4; }", arg=before, timeout=WAIT_MS)      # it goes round
    ring = pg.locator(".mp-rings").bounding_box()
    r = dot.bounding_box()
    assert ring["x"] <= r["x"] <= ring["x"] + ring["width"] and ring["y"] <= r["y"] <= ring["y"] + ring["height"]
    pg.emulate_media(reduced_motion="reduce")
    assert dot.evaluate("e => getComputedStyle(e).display") == "none"                                                        # off under reduced motion
    pg.emulate_media(reduced_motion="no-preference")
    for n in host.nodes:                                                                                                       # nothing at work: nothing alive moves
        for t in n.get("tasks", []):
            if n["goal"] == "game" and t["state"] == "running":
                t["state"] = "done"
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.wait_for_selector(".mp-orbit", state="detached", timeout=WAIT_MS)


def test_a_step_lifted_shows_its_line_feeling_intensity_and_what_it_gives_or_takes_and_a_file_opens_over_the_pane_then_back_lights_the_card(maps):
    pg, host, w = maps
    go(pg, "game")
    card(pg, "join-a-match").locator(".mp-card__nm").click()
    back = lifted(pg)
    back.wait_for(timeout=WAIT_MS)
    assert back.get_attribute("data-lifted") == "t:map:game-design:join-a-match" and card(pg, "join-a-match").get_attribute("data-lkey") == "t:map:game-design:join-a-match"
    text = back.inner_text()
    assert "Friends meet in a lobby" in text and "Proposed by Game design" in text and "Fellowship" in text and "being with others" in text and "easy" in text      # its line, who keeps it, its feeling, its intensity
    assert "It gives nothing" in text and "It takes nothing" in text and back.locator(".mp-pips i.d").count() == 2
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
    text = lifted(pg).inner_text()
    assert "It rests on no file yet" in text and "Coins" in text and "It gives nothing" not in text                         # what it gives is the currency's name
    pg.keyboard.press("Escape")
    pg.wait_for_selector(".table-back", state="detached", timeout=WAIT_MS)
    card(pg, "hold-the-tower").locator(".mp-card__nm").click()
    assert "Yours" in lifted(pg).inner_text()


def test_edit_keeps_the_steps_name_line_feeling_intensity_and_files_through_loop_set(maps):
    pg, host, w = maps
    go(pg, "game")
    card(pg, "spend-the-coins").locator(".mp-card__nm").click()
    back = lifted(pg)
    back.get_by_role("button", name="Edit").click()
    back.locator('input[name="name"]').fill("Buy a hero")
    back.locator('textarea[name="line"]').fill("Coins buy a hero.")
    back.locator('select[name="feel"]').select_option("fantasy")
    back.locator('select[name="intensity"]').select_option("4")
    back.locator('textarea[name="files"]').fill("config/shop.ts\nlevels/")
    shot(pg, f"maps-loop-edit-{w}.png")
    back.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => [...document.querySelectorAll('.mp-st .mp-card__nm')].some((e) => e.textContent.trim() === 'Buy a hero')", timeout=WAIT_MS)
    (sent,) = [a for n, a in host.log if n == "ideas.loop_set"]
    assert [lp["span"] for lp in sent["loops"]] == ["core", "session", "meta"] and [s["name"] for lp in sent["loops"] for s in lp["steps"]] == [
        "Join a match", "Hold the tower", "Score the round", "Buy a hero", "Pick a hero", "Rematch", "Open a new arena", "Climb the ladder", "Show off"]
    assert sent["loops"][1]["steps"][0] == {"id": "spend-the-coins", "name": "Buy a hero", "line": "Coins buy a hero.", "feel": "fantasy", "intensity": 4, "gives": [], "takes": ["coins"], "rests_on": ["config/shop.ts", "levels/"]}
    assert [c["id"] for c in sent["currencies"]] == ["coins", "gems"] and [h["when"] for h in sent["hooks"]] == ["D1", "D7"]          # the rest is sent as it was
    assert card(pg, "spend-the-coins").locator(".mp-card__nm").text_content().strip() == "Buy a hero" and card(pg, "spend-the-coins").locator(".mp-st__meta > span").first.inner_text() == "fantasy"


def test_a_currency_is_renamed_in_place(maps):
    pg, host, w = maps
    go(pg, "game")
    card(pg, "cur:coins").locator(".mp-card__nm").click()
    back = lifted(pg)
    assert back.get_attribute("data-lifted") == "t:map:game-design:cur:coins" and "Score the round" in back.inner_text() and "Spend the coins" in back.inner_text()
    back.get_by_role("button", name="Edit").click()
    back.locator('input[name="name"]').fill("Gold")
    back.get_by_role("button", name="Save").click()
    pg.wait_for_function("() => document.querySelector('.mp-eco__row[data-currency=\"coins\"] .mp-card__nm')?.textContent.trim() === 'Gold'", timeout=WAIT_MS)
    (sent,) = [a for n, a in host.log if n == "ideas.loop_set"]
    assert sent["currencies"][0] == {"id": "coins", "name": "Gold", "kind": "soft", "line": "Earned in every round."} and sent["loops"][0]["steps"][2]["gives"] == ["coins"]      # its id stays: what gives it still does


def test_propose_again_asks_the_leader_once_more_and_the_persons_version_is_said_to_be_kept_aside(maps):
    pg, host, w = maps
    go(pg, "game")
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    assert pg.get_by_role("button", name="Propose again").count() == 1 and pg.locator(".mp-bar .mp-cap").count() == 0
    host.loop["by"] = "person"
    host.rev += 1
    host.ws.send(json.dumps(host.snapshot()))
    pg.get_by_role("button", name="Propose again").click()
    pg.locator(".mp-bar .mp-cap").wait_for(timeout=WAIT_MS)
    assert [a for n, a in host.log if n == "ideas.loop_propose"] == [{"again": True}] and "kept aside" in pg.locator(".mp-bar .mp-cap").inner_text()
    host.proposal = {"asked": False, "why": "Game design has no tool to ask"}
    pg.get_by_role("button", name="Propose again").click()
    pg.get_by_role("alert").wait_for(timeout=WAIT_MS)
    assert pg.get_by_role("alert").inner_text() == "Game design has no tool to ask"


def test_with_no_loop_kept_the_map_says_so_and_propose_asks_once(maps):
    pg, host, w = maps
    host.loop = json.loads(json.dumps(EMPTY))
    go(pg, "game")
    pg.locator(".mp-nothing").wait_for(timeout=WAIT_MS)
    assert "Nothing to read yet: the game's configs" in pg.locator(".mp-nothing").inner_text() and pg.locator(".mp-card").count() == 0 and pg.get_by_role("button", name="Propose again").count() == 0
    shot(pg, f"maps-loop-none-{w}.png")
    pg.get_by_role("button", name="Propose").click()
    pg.locator(".mp-st").first.wait_for(timeout=WAIT_MS)
    assert [a for n, a in host.log if n == "ideas.loop_propose"] == [{}] and len(steps_of(pg)) == 9
    host.loop = json.loads(json.dumps(EMPTY))
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
