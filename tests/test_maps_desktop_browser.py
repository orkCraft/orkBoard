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
from tests.test_table_desktop_browser import HEAD, TableHost, party, tab, watch  # noqa: E402

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
        if name == "ideas.gate":                                                                         # a project with a main branch: its gate is there (nothing waits), so the ring holds Release at the wide width; `same` would be no gate (spec 113 §4)
            return {"into": "dev", "main": "main", "same": False, "commits": 0, "files": 0, "ideas": []}
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
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    yield pg, host, request.param
    narrow.no_sideways(pg)
    pg.context.close()
    assert not errors, "\n".join(errors)


def wide(w):
    return w == "wide"


def go(pg, slug):
    if slug == "release":        # Release has no tab at any width (decisions §283.29: it waits; before it only at the wide width, docs/specs/111 §4.1): its page is kept, and its view is opened as a tab opens it
        pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openTab('release'))")
        pg.locator('.table[data-tab="release"]').wait_for(timeout=WAIT_MS)
        return
    tab(pg, slug).click()
    pg.locator(f'.table-tab[data-tab="{slug}"][aria-selected="true"], .col-head__tab[data-tab="{slug}"][aria-selected="true"]').wait_for(timeout=WAIT_MS)


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






















# -- Art's assets --------------------------------------------------------------------------------------------------------------------------------------







# -- Release: dev and main -----------------------------------------------------------------------------------------------------------------------------





# -- Marketing: the way in -----------------------------------------------------------------------------------------------------------------------------



