"""Spec 168 H1 and H2 (docs/specs/168-the-window-played-as-a-card-games-table.md; decisions §283.30, §283.31; before them spec 157 D, §267.1), in a real browser against a stub host that answers `ideas.stall`, `ideas.stall_take`
and `ideas.stall_back` in the host's real shapes (`orkboard/gui/ideas_stall.py`): the backpack at the hand's right end opens the inventory as **a row of slots on the table** (the Orkmaster's six, a leader's hero, tool and tier), each its chosen
way as a 144 x 202 card (its label over it, its picture or its kind's sign, its name and what it does, the pips of its ways, a coin where a cheaper way exists); a slot pressed deals its ways to the hand (a card each, its price in its bottom right,
*Yours*, *Yours before*, *Default*, the Orkmaster's pick starred); a way played sends the take and *Undo*, on the table's line, sends the old way; the hand keeps its height and no card is carried; Esc puts the ways back and then shuts the inventory;
a tab pressed picks the chair; Settings' last line opens it; at 1280 x 800 nothing overflows the table; the narrow page keeps the stall (a ware pressed is taken). Screenshots go to the folder `STALL_SHOTS` names when it is set."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_shell_browser import _sent  # noqa: E402
from tests.test_table_desktop_browser import open_tab  # noqa: E402

pytestmark = pytest.mark.browser

SHOTS = Path(os.environ["STALL_SHOTS"]) if os.path.isabs(os.environ.get("STALL_SHOTS", "")) else None     # a folder named in full: `1` is no folder


def shot(pg, name):
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(SHOTS / f"{name}.png"))


def ware(id, word, line, price, **more):
    return {"id": id, "word": word, "line": line, "price": price, "before": False, **more}


def stats(school, flow, size, decides, says_no):
    return {"school": school, "flow": flow, "size": size, "decides": decides, "says_no": says_no}


SH = {"race": "shaman", "tier": "elder"}
# the Orkmaster's chair, as the host lays it: six slots (a slot: slot, label, sub, [(id, word, line)])
KEEPER = [("target", "How deep", "How much the orks spend on a goal", [("thrift", "Thrift", "Every step on the cheaper tier; a spec reads less"), ("balance", "Balance", "Each step on its usual tier"), ("quality", "Quality", "Specs and acceptances on the elder tier")]),
          ("build_start", "The build starts", "When a spec's plan starts by itself", [("now", "At once", "A plan starts as soon as its spec is made"), ("30m", "In 30 min", "A spec waits 30 minutes for your look"), ("2h", "In 2 h", "A spec waits 2 hours for your look"), ("tonight", "Tonight", "A spec waits until tonight's night window"), ("hand", "By hand", "Nothing is built until you press Start")]),
          ("night", "The night", "What runs in the night's window", [("off", "Off", "Nothing runs at night"), ("ideas", "Ideas and specs", "Talk and the specs of the goals in line; nothing is built"), ("builds", "And the builds", "What was agreed by day is built in the night's window"), ("proposals", "And the leaders' proposals", "The leaders you pick may propose a goal each")]),
          ("review", "Lands in dev by itself", "Whether a green result goes into dev with no press", [("on", "On", "A green result goes into dev with no press"), ("off", "Off", "A green result waits in the discard for your press")]),
          ("push", "Push", "What is pushed after a merge", [("no", "No", "Nothing leaves this computer"), ("main", "Main only", "Main is pushed after To main; dev stays here"), ("both", "Dev and main", "Dev and main are pushed after each merge")]),
          ("max_parallel", "Goals at once", "How many goals the orks work on side by side", [("1", "One", "One goal's work at a time"), ("3", "Three", "Up to three goals' work side by side"), ("8", "Eight", "Up to eight goals at once, while the limits hold")])]
ORKMASTER_NOW = {"target": "balance", "build_start": "2h", "night": "off", "review": "on", "push": "no", "max_parallel": "1"}
PRICE = {("target", "thrift"): {"word": "lighter"}, ("target", "quality"): {"word": "heavier"}, ("night", "ideas"): {"word": "heavier"}}
PICKS = {"target": "balance", "build_start": "2h", "night": "ideas", "review": "on", "push": "main", "max_parallel": "1"}
DEFAULTS = {"target": "balance", "build_start": "2h", "night": "off", "review": "on", "push": "no", "max_parallel": "1"}
HEROES = [("sh-c4", "Sh.man", "C4 and hotspots", stats("C4 and hotspots", "containers → parts → hotspots", "standard", 2, 2)),
          ("sh-xp", "Spike Shaman", "Extreme programming", stats("Extreme programming", "test → code → refactor", "standard", 3, 2))]
TIERS = [("", "Default", "Its own calls follow How deep", None), ("laborer", "Laborer", "The lightest model of its tool", {"share": -2}), ("warrior", "Warrior", "The middle model", None), ("elder", "Elder", "The strongest model", {"share": 3})]
SIZES = [("lean", "Lean", "One doer at a time; no checker, the leader accepts each step", {"word": "lighter"}), ("standard", "Standard", "Two at a time; one checker, then the leader accepts", None), ("full", "Full", "Three at a time; every checker that applies, then the leader accepts", {"word": "heavier"})]
ANSWERS = [("pen", "Pen", "It asks, and you answer in your own words each time.", None), ("choice", "Choice", "It offers its ways; you pick one.", None), ("fork", "Fork", "Its ways worked out, with their gains, costs and risks: one more call a question, on the elder tier.", {"money": "+$0.25 to $0.38 a question"}),
         ("silent", "Silent", "It decides and lays a card you can overrule; going into main, money and dropping a goal are still asked.", None)]
TOOLS = [("", "Main tool", "The potions' order: the first AI tool in your hand that has mana", None), ("claude", "Claude", "Every seat works on Claude", {"money": "up to $2 a night"}), ("codex", "Codex", "Signed out", {"locked": "Codex is signed out"})]


class StallHost(HandHost):
    """The inventory of the host in stub form: what is carried per chair and slot, each way's price by what is carried (a way carried is `{mine}`), the slot's pips (`at`), its coin (`cheaper`), the default and the pick."""

    def __init__(self, **more):
        super().__init__(bare=True, **more)
        self.carry = {"": dict(ORKMASTER_NOW), "tech": {"hero": "sh-c4", "tool": "", "tier": "warrior", "size": "standard", "answers": "choice"}}
        self.defaults = {"": dict(DEFAULTS), "tech": {"hero": "sh-c4", "tool": "", "tier": "", "size": "standard", "answers": "choice"}}
        self.before = {}

    def shelves(self, chair):
        now = self.carry.get(chair) or {}

        def priced(slot, id, base):
            return {"mine": True} if now.get(slot) == id else base

        def shelf(slot, label, sub, kind, wares):
            for w in wares:
                w["before"] = self.before.get((chair, slot)) == w["id"] and not w["price"].get("mine")
                if self.defaults.get(chair, {}).get(slot) == w["id"]:
                    w["default"] = True
            at = next((i for i, w in enumerate(wares) if w["price"].get("mine")), -1)
            cheaper = any(w["price"].get("word") == "lighter" or (w["price"].get("share") or 0) < 0 for w in wares)
            return {"id": slot, "label": label, "sub": sub, "kind": kind, "slot": slot, "wares": wares, "at": at, "cheaper": cheaper}
        if chair == "":
            return [shelf(slot, label, sub, "small", [ware(id, word, line, priced(slot, id, PRICE.get((slot, id)) or {"word": "same cost"}), **({"star": True} if PICKS[slot] == id else {})) for id, word, line in wares]) for slot, label, sub, wares in KEEPER]
        if chair == "release":
            lock = {"locked": "Release is in every project: its hero and its gate are fixed"}
            return [shelf("hero", "Its hero", "The school its leader looks by", "heroes",
                          [ware("lich-nk", "Release Night King", "DORA's keys, readiness and semver", lock, head={"race": "lich", "tier": "elder"}, stats=stats("DORA's keys", "dev → the gate → main", "standard", 1, 3))])]
        return [shelf("hero", "Its hero", "The school its leader looks by", "heroes", [ware(id, word, line, priced("hero", id, {"word": "one pass"}), head=SH, stats=st) for id, word, line, st in HEROES]),
                shelf("tool", "Its AI tool", "What runs this party's goals", "small", [ware(id, word, line, priced("tool", id, price or {"word": "same cost"})) for id, word, line, price in TOOLS]),
                shelf("tier", "Its tier", "The model its own calls run on: Talk, its section, its acceptance", "small", [ware(id, word, line, priced("tier", id, price or {"word": "same cost"})) for id, word, line, price in TIERS]),
                shelf("size", "Its party's size", "Its seats' cells and how many work at once", "small", [ware(id, word, line, priced("size", id, price or {"word": "same cost"})) for id, word, line, price in SIZES]),
                shelf("answers", "How it answers", "How it asks what it must ask", "small", [ware(id, word, line, priced("answers", id, price or {"word": "same cost"})) for id, word, line, price in ANSWERS])]

    def stall(self, chair):
        shelves = self.shelves(chair)
        now = self.carry.get(chair) or {}
        hand = []
        for s in shelves:
            if s["kind"] == "makers":
                continue                                    # a maker is no slot: the host's `hand` has none
            w = next((x for x in s["wares"] if x["id"] == now.get(s["slot"], "")), s["wares"][0])
            card = {"slot": s["slot"], "label": s["label"], "word": w["word"], "yours": now.get(s["slot"], ""), "line": w["line"], "fixed": chair == "release"}
            if w.get("head"):
                card["head"] = w["head"]
            hand.append(card)
        say = "Every way has its price in words: lighter or heavier than what you carry, or the same cost. Nothing is guessed." if chair == "" else "Sh.man looks by C4 and hotspots. It lays its craft's map."
        return {"chair": chair, "whose": "The Orkmaster" if chair == "" else "tech party", "say": say, "shelves": shelves, "hand": hand}

    def handle(self, name, a):
        if name == "ideas.stall":
            self.log.append((name, a))
            return self.stall(a["chair"])
        if name == "ideas.stall_take":
            self.log.append((name, a))
            old = self.carry[a["chair"]].get(a["slot"], "")
            self.carry[a["chair"]][a["slot"]] = a["value"]
            self.before[(a["chair"], a["slot"])] = old
            return self.bump({"stall": self.stall(a["chair"]), "undo": {"slot": a["slot"], "value": old}})
        if name == "ideas.stall_back":
            self.log.append((name, a))
            old = self.carry[a["chair"]].get(a["slot"], "")
            self.carry[a["chair"]][a["slot"]] = self.defaults[a["chair"]][a["slot"]]
            return self.bump({"stall": self.stall(a["chair"]), "undo": {"slot": a["slot"], "value": old}})
        return super().handle(name, a)


def opened(gui, chair=None, host=None, width="wide"):
    """The page, the inventory open on a chair: the tab pressed first (a party's), then the backpack."""
    pg, host, log = open_hand(gui, host=host or StallHost(), width=width)
    if chair:
        open_tab(pg, chair)
    pg.locator("[data-backpack]").click()
    pg.locator(".slots-table .slot-card, .stall-rug .stall-ware").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def slot(pg, name):
    return pg.locator(f'.slots .slot-card[data-slot="{name}"]')


def deal(pg, name):
    """A slot pressed: its ways in the hand."""
    slot(pg, name).click()
    pg.locator(f'[data-slot-ways="{name}"] .slot-way').first.wait_for(timeout=WAIT_MS)
    pg.wait_for_timeout(450)            # the hand's rise


def way(pg, name, id):
    return pg.locator(f'[data-slot-ways="{name}"] .slot-way[data-way="{id}"]')


def plate(pg, slot, id):
    return pg.locator(f'.stall-ware[data-slot="{slot}"][data-ware="{id}"] .stall-price')




def test_a_way_played_sends_the_take_the_line_says_so_and_undo_sends_the_old_way(gui):
    pg, host, log = opened(gui, "tech")
    try:
        deal(pg, "tier")
        way(pg, "tier", "elder").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "tier", "value": "elder"}))
        pg.wait_for_function("() => document.querySelector('.table-title [data-receipt]')?.textContent.includes('Elder')", timeout=WAIT_MS)       # on the table's line
        pg.wait_for_function("() => !document.querySelector('[data-slot-ways]')", timeout=WAIT_MS)                   # the ways go back after one is played
        assert slot(pg, "tier").locator(".slot-card__name").inner_text() == "Elder"
        shot(pg, "slots-way-played")
        deal(pg, "tier")
        assert way(pg, "tier", "warrior").get_attribute("data-before") == "1" and "yours before" in way(pg, "tier", "warrior").inner_text().lower()
        assert way(pg, "tier", "elder").get_attribute("data-yours") == "1"
        pg.locator('[data-slot-ways="tier"] [data-act="put"]').click()
        pg.locator(".table-title [data-undo]").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "tier", "value": "warrior"}))
        pg.wait_for_function("() => !document.querySelector('[data-undo]')", timeout=WAIT_MS)
        assert slot(pg, "tier").locator(".slot-card__name").inner_text() == "Warrior"
        deal(pg, "tier")                                                                                             # the way carried and a way not here are not taken
        before_takes = [e for e in host.log if e[0] == "ideas.stall_take"]
        way(pg, "tier", "warrior").click(force=True)
        pg.locator('.slots .slot-card[data-slot="tool"]').click()
        pg.locator('[data-slot-ways="tool"] .slot-way').first.wait_for(timeout=WAIT_MS)
        way(pg, "tool", "codex").click(force=True)
        assert way(pg, "tool", "codex").get_attribute("aria-disabled") == "true" and "signed out" in way(pg, "tool", "codex").get_attribute("title")
        pg.wait_for_timeout(300)
        assert [e for e in host.log if e[0] == "ideas.stall_take"] == before_takes
    finally:
        pg.close()
    assert not log, "\n".join(log)






def test_a_tab_pressed_while_open_picks_the_chair_and_the_slots_follow(gui):
    pg, host, log = opened(gui)
    try:
        deal(pg, "target")
        open_tab(pg, "tech")
        pg.wait_for_function("() => document.querySelector('.slots-table')?.dataset.stall === 'tech'", timeout=WAIT_MS)
        assert ("ideas.stall", {"chair": "tech"}) in host.log and pg.locator(".slots .slot-card[data-slot=hero]").count() == 1
        assert pg.locator("[data-slot-ways]").count() == 0                                                    # the ways of the other chair are put back
        pg.locator('.col-head__tab[data-tab="orkmaster"], .table-tab[data-tab="orkmaster"]').first.click()
        pg.wait_for_function("() => document.querySelector('.slots-table')?.dataset.stall === 'orkmaster'", timeout=WAIT_MS)
        assert pg.locator(".slots .slot-card[data-slot=hero]").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)
































class PickHost(StallHost):
    """A web app's Design slot (Pixel-Perfect starred), or a game's Art: its one hero, with no choice (spec 164 I)."""
    art = False

    def shelves(self, chair):
        shelves = super().shelves(chair)
        if chair != "tech":
            return shelves
        from orkboard.realm import heroes as cat
        if self.art:
            return [s for s in shelves if s["slot"] != "hero"]
        wares = [ware(h.id, h.name, h.school, {"word": "one pass"}, head=cat.head(h), stats=stats(h.school, h.flow, h.size, h.decides, h.says_no), **({"star": True} if h.id == "dry-heur" else {}))
                 for h in (cat.get(i) for i in ("dry-heur", "dry-sprint", "dry-a11y"))]
        shelves[0]["wares"] = wares
        shelves[0]["at"] = -1
        return shelves

    def stall(self, chair):
        got = super().stall(chair)
        if self.art and chair == "tech":
            from orkboard.realm import heroes as cat
            got["hand"].insert(0, {"slot": "hero", "label": "Its hero", "word": "Sprite Dryad", "yours": "dry-sprite", "line": "", "fixed": False, "head": cat.head(cat.get("dry-sprite"))})
        return got






def test_a_leaders_size_and_how_it_answers_are_taken_each_with_its_price_and_undone(gui):
    """Spec 168 H4: the size's ways (*Lean*, *Standard*, *Full*) and how a leader answers (*Pen*, *Choice*, *Fork*, *Silent*) are slots like the others: pressed, their ways dealt (the Fork's price in money on its card), played, sent."""
    pg, host, log = opened(gui, "tech")
    try:
        deal(pg, "size")
        assert [pg.locator('[data-slot-ways="size"] .slot-way').nth(i).get_attribute("data-way") for i in range(3)] == ["lean", "standard", "full"]
        assert way(pg, "size", "standard").get_attribute("data-yours") == "1" and way(pg, "size", "standard").get_attribute("data-default") == "1"
        assert "lighter" in way(pg, "size", "lean").inner_text() and "heavier" in way(pg, "size", "full").inner_text()
        way(pg, "size", "full").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "size", "value": "full"}))
        assert slot(pg, "size").locator(".slot-card__name").inner_text() == "Full"
        deal(pg, "answers")
        assert [pg.locator('[data-slot-ways="answers"] .slot-way').nth(i).get_attribute("data-way") for i in range(4)] == ["pen", "choice", "fork", "silent"]
        assert "a question" in way(pg, "answers", "fork").inner_text() and "$" in way(pg, "answers", "fork").inner_text()           # the Fork's price, said as money
        way(pg, "answers", "silent").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "answers", "value": "silent"}))
        assert slot(pg, "answers").locator(".slot-card__name").inner_text() == "Silent"
        pg.locator("[data-undo]").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "answers", "value": "choice"}))
        assert slot(pg, "answers").locator(".slot-card__name").inner_text() == "Choice"
        deal(pg, "answers")
        shot(pg, "h4-leader-inventory")
    finally:
        pg.close()
    assert not log, "\n".join(log)
