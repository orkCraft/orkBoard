"""Spec 168 H1 and H2 (docs/specs/168-the-window-played-as-a-card-games-table.md; decisions §283.30, §283.31; before them spec 157 D, §267.1), in a real browser against a stub host that answers `ideas.stall`, `ideas.stall_take`
and `ideas.stall_back` in the host's real shapes (`orkboard/gui/ideas_stall.py`): the backpack at the hand's right end opens the inventory as **a row of slots on the table** (the Orkmaster's six, a leader's hero, tool and tier), each its chosen
way as a 144 x 202 card (its label over it, its picture or its kind's sign, its name and what it does, the pips of its ways, a coin where a cheaper way exists); a slot pressed deals its ways to the hand (a card each, its price in its bottom right,
*Yours*, *Yours before*, *Default*, the Orkmaster's pick starred); a way played sends the take and *Undo*, on the table's line, sends the old way; the hand keeps its height and no card is carried; Esc puts the ways back and then shuts the inventory;
a tab pressed picks the chair; Settings' last line opens it; at 1280 x 800 nothing overflows the table; the narrow page keeps the stall (a ware pressed is taken). Screenshots go to the folder `STALL_SHOTS` names when it is set."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests import narrow  # noqa: E402
from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_hand_desktop_browser import HandHost, open_hand  # noqa: E402
from tests.test_hero_table_browser import HeroHost, XP, table  # noqa: E402
from tests.test_night_card_browser import open_settings  # noqa: E402
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


def test_the_backpack_opens_the_slots_and_esc_shuts_it(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pack = pg.locator("[data-backpack]")
        pack.wait_for(timeout=WAIT_MS)
        assert pack.get_attribute("title") == "Inventory: how the project is set" and pack.get_attribute("aria-pressed") == "false"
        head = pg.locator(".hand-end")
        assert head.locator("[data-backpack]").count() == 1 and pg.locator(".table-tabs__end .stall-pack").count() == 0       # the backpack stands at the hand's right end
        assert pack.bounding_box()["x"] > pg.viewport_size["width"] * 0.8 and head.locator(".ork-pack:not(.is-open)").count() == 1
        assert pg.locator(".slots-table").count() == 0 and pg.locator(".table-pane").get_attribute("data-stall") is None
        pack.click()
        pg.locator(".slots-table").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-pane").get_attribute("data-stall") == "open"
        assert pg.locator(".table-pane").evaluate("e => e.classList.contains('ork-leather')") and head.locator(".ork-pack.is-open").count() == 1       # the open pack, the table in its leather
        assert pack.get_attribute("title") == "Close the inventory" and pack.get_attribute("aria-pressed") == "true"
        assert ("ideas.stall", {"chair": ""}) in host.log
        assert pg.locator(".stall, .stall-rug, .stall-merchant, .stall-shelf, .stall-service").count() == 0       # no rug, no shelves, no merchant
        assert pg.locator(".hand .carry, .carry-card, .carry__fan").count() == 0                                   # no card is carried
        assert pg.locator(".table-tab").count() > 0                                                               # the tabs stay
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.slots-table')", timeout=WAIT_MS)
        assert pg.locator("[data-backpack]").get_attribute("aria-pressed") == "false"
        assert not pg.locator(".table-pane").evaluate("e => e.classList.contains('ork-leather')")        # shut, the bronze is back
        pack.click()
        pg.locator(".slots-table").wait_for(timeout=WAIT_MS)
        pack.click()
        pg.wait_for_function("() => !document.querySelector('.slots-table')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_orkmasters_slots_are_a_row_of_six_big_cards_each_its_chosen_way(gui):
    pg, host, log = opened(gui)
    try:
        pg.set_viewport_size({"width": 1366, "height": 768})                                                      # the laptop the decision is fitted to: six cards in one row
        pg.wait_for_timeout(400)
        cards = pg.locator(".slots .slot-card")
        assert cards.evaluate_all("els => els.map((e) => e.dataset.slot)") == ["target", "build_start", "night", "review", "push", "max_parallel"]
        assert [t.lower() for t in pg.locator(".slots .slot-label").all_inner_texts()] == ["how deep", "the build starts", "the night", "lands in dev by itself", "push", "goals at once"]
        for i in range(6):
            box = cards.nth(i).bounding_box()
            assert (round(box["width"]), round(box["height"])) == (144, 202)                                      # a big card
        ys = {round(b["y"]) for b in (cards.nth(i).bounding_box() for i in range(6))}
        assert len(ys) == 1                                                                                       # one row
        deep = slot(pg, "target")
        assert deep.locator(".slot-card__name").inner_text() == "Balance" and "usual tier" in deep.locator(".slot-card__line").inner_text()      # its way and what it does
        assert deep.locator(".slot-pips i").count() == 3 and deep.locator(".slot-pips i.is-on").count() == 1
        assert deep.locator(".slot-pips i").evaluate_all("els => els.map((e) => e.classList.contains('is-on'))") == [False, True, False]
        assert deep.locator(".slot-pic").count() == 1 and deep.locator(".slot-pic .ork-icon").count() == 1 and deep.get_attribute("data-way") == "balance"     # no picture in orkUI yet: the kind's sign
        assert deep.locator(".slot-card__coin").count() == 1 and deep.locator(".slot-card__coin").get_attribute("title") == "A cheaper way exists"      # Thrift is lighter
        assert slot(pg, "push").locator(".slot-card__coin").count() == 0 and slot(pg, "push").locator(".slot-pips i").count() == 3
        assert slot(pg, "build_start").locator(".slot-pips i").count() == 5 and slot(pg, "build_start").locator(".slot-card__name").inner_text() == "In 2 h"
        assert slot(pg, "night").locator(".slot-card__name").inner_text() == "Off" and slot(pg, "night").locator(".slot-pic .ork-sign.moon").count() == 1
        assert slot(pg, "max_parallel").locator(".slot-card__name").inner_text() == "One"
        assert "as set" in deep.inner_text()
        assert pg.locator(".slots .slot-label").first.evaluate("e => e.classList.contains('ork-plaque')")
        assert pg.locator(".hand").bounding_box()["height"] > 100
        shot(pg, "slots-orkmaster")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_leaders_slots_are_its_hero_tool_tier_size_and_how_it_answers_with_its_seats_under_them(gui):
    pg, host, log = opened(gui, "tech")
    try:
        assert ("ideas.stall", {"chair": "tech"}) in host.log
        assert pg.locator(".stall-title").inner_text() == "Inventory"
        assert slot(pg, "hero").evaluate_all("els => els.length") == 1 and pg.locator(".slots .slot-card").evaluate_all("els => els.map((e) => e.dataset.slot)") == ["hero", "tool", "tier", "size", "answers"]
        assert pg.locator(".slots .slot-label").evaluate_all("els => els.map((e) => e.innerText.toLowerCase())") == ["its hero", "its ai tool", "its tier", "its party's size", "how it answers"]
        hero = slot(pg, "hero")
        assert hero.locator(".slot-card__name").inner_text() == "Sh.man" and hero.locator(".slot-pic .ork-race__head").count() == 1 and hero.locator(".slot-pips i").count() == 2     # its head is its picture
        assert slot(pg, "tool").locator(".slot-card__name").inner_text() == "Main tool"
        tier = slot(pg, "tier")
        assert tier.locator(".slot-card__name").inner_text() == "Warrior" and tier.locator(".slot-pips i").count() == 4 and tier.locator(".slot-card__coin").count() == 1
        size, answers = slot(pg, "size"), slot(pg, "answers")
        assert size.locator(".slot-card__name").inner_text() == "Standard" and size.locator(".slot-pips i").count() == 3 and size.locator(".slot-card__coin").count() == 1         # a lighter size exists
        assert answers.locator(".slot-card__name").inner_text() == "Choice" and answers.locator(".slot-pips i").count() == 4 and answers.locator(".slot-card__coin").count() == 0
        seats, row = pg.locator('.stall-seats[data-seats="tech"]'), pg.locator(".slots")
        seats.wait_for(timeout=WAIT_MS)
        assert row.bounding_box()["y"] + row.bounding_box()["height"] <= seats.bounding_box()["y"] + 1               # the seats under the slots
        assert pg.locator(".hand .carry-card").count() == 0
        shot(pg, "slots-tech")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_slot_pressed_deals_its_ways_to_the_hand_and_the_hand_keeps_its_height(gui):
    pg, host, log = opened(gui)
    try:
        before = pg.locator(".hand").bounding_box()
        deal(pg, "target")
        assert pg.locator('[data-slot-deal="target"]').count() == 1 and slot(pg, "target").get_attribute("aria-pressed") == "true"
        ways = pg.locator('[data-slot-ways="target"] .slot-way')
        assert ways.evaluate_all("els => els.map((e) => e.dataset.way)") == ["thrift", "balance", "quality"]
        for i in range(3):
            box = ways.nth(i).bounding_box()
            assert round(box["width"]) == 144 and round(box["height"]) == 202                                        # a way is a big card too
        thrift, balance, quality = way(pg, "target", "thrift"), way(pg, "target", "balance"), way(pg, "target", "quality")
        assert "Thrift" in thrift.inner_text() and "Every step on the cheaper tier" in thrift.inner_text()           # what it does, whole
        assert thrift.locator('[data-price="less"]').inner_text() == "lighter" and quality.locator('[data-price="more"]').inner_text() == "heavier"      # its price in its bottom right
        fb, fc = thrift.locator(".corner--foot").bounding_box(), thrift.bounding_box()
        assert fb["x"] + fb["width"] > fc["x"] + fc["width"] - 20 and fb["y"] + fb["height"] > fc["y"] + fc["height"] - 20
        assert "yours" in balance.inner_text().lower() and balance.get_attribute("data-yours") == "1" and balance.get_attribute("aria-disabled") == "true"     # the way carried
        assert balance.get_attribute("data-default") == "1" and "default" in balance.inner_text().lower()
        assert balance.get_attribute("data-pick") == "1" and balance.locator(".slot-way__star").get_attribute("aria-label") == "The Orkmaster's pick"       # the Orkmaster's pick, starred
        assert thrift.locator(".slot-way__star").count() == 0 and thrift.get_attribute("data-pick") is None
        assert pg.locator('[data-slot-ways="target"] .slot-way .slot-pic').count() == 3
        assert pg.locator('[data-slot-ways="target"] [data-act="put"]').inner_text() == "Put it back"
        after = pg.locator(".hand").bounding_box()
        assert after == before, (before, after)                                                                      # the hand keeps its height
        assert pg.locator(".hand .carry-card").count() == 0
        shot(pg, "slots-ways-dealt")
        pg.locator('[data-slot-ways="target"] [data-act="put"]').click()
        pg.wait_for_function("() => !document.querySelector('[data-slot-ways]')", timeout=WAIT_MS)
        assert slot(pg, "target").get_attribute("aria-pressed") == "false" and pg.locator(".hand").bounding_box() == before
        assert not [e for e in host.log if e[0] in ("ideas.stall_take", "ideas.stall_back")]                         # putting it back sends nothing
        deal(pg, "push")                                                                                             # another slot, then Esc: the ways go back first, the inventory stays
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('[data-slot-ways]')", timeout=WAIT_MS)
        assert pg.locator(".slots-table").count() == 1
        deal(pg, "push")
        slot(pg, "push").click()                                                                                     # the slot pressed again puts them back
        pg.wait_for_function("() => !document.querySelector('[data-slot-ways]')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_way_played_sends_the_take_the_line_says_so_and_undo_sends_the_old_way(gui):
    pg, host, log = opened(gui, "tech")
    try:
        before = pg.locator(".hand").bounding_box()
        deal(pg, "tier")
        way(pg, "tier", "elder").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "tier", "value": "elder"}))
        pg.wait_for_function("() => document.querySelector('.table-title [data-receipt]')?.textContent.includes('Elder')", timeout=WAIT_MS)       # on the table's line
        pg.wait_for_function("() => !document.querySelector('[data-slot-ways]')", timeout=WAIT_MS)                   # the ways go back after one is played
        assert slot(pg, "tier").locator(".slot-card__name").inner_text() == "Elder" and pg.locator(".hand").bounding_box() == before
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


def test_a_slot_s_default_is_a_way_among_the_others(gui):
    host = StallHost()
    host.carry["tech"]["tier"] = "elder"
    pg, host, log = opened(gui, "tech", host=host)
    try:
        deal(pg, "tier")
        default = way(pg, "tier", "")
        assert default.get_attribute("data-default") == "1" and "default" in default.inner_text().lower() and "how deep" in default.inner_text().lower()
        default.click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "tier", "value": ""}))
        pg.wait_for_function("() => document.querySelector('.slots [data-slot=tier]').dataset.way === ''", timeout=WAIT_MS)
        assert slot(pg, "tier").locator(".slot-card__name").inner_text() == "Default"
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_orkmasters_other_slots_deal_their_ways(gui):
    pg, host, log = opened(gui)
    try:
        deal(pg, "build_start")
        assert pg.locator('[data-slot-ways="build_start"] .slot-way').evaluate_all("els => els.map((e) => e.dataset.way)") == ["now", "30m", "2h", "tonight", "hand"]
        assert way(pg, "build_start", "2h").get_attribute("data-yours") == "1"
        way(pg, "build_start", "tonight").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "", "slot": "build_start", "value": "tonight"}))
        pg.wait_for_function("() => document.querySelector('.slots [data-slot=build_start]').dataset.way === 'tonight'", timeout=WAIT_MS)
        deal(pg, "night")
        assert way(pg, "night", "ideas").get_attribute("data-pick") == "1" and way(pg, "night", "ideas").locator('[data-price="more"]').count() == 1
        pg.keyboard.press("Escape")
        deal(pg, "max_parallel")
        assert pg.locator('[data-slot-ways="max_parallel"] .slot-way').evaluate_all("els => els.map((e) => e.dataset.way)") == ["1", "3", "8"]
        shot(pg, "slots-build-start")
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


def test_releases_slot_is_fixed(gui):
    pg, host, log = opened(gui, "release")
    try:
        assert ("ideas.stall", {"chair": "release"}) in host.log
        hero = slot(pg, "hero")
        assert hero.get_attribute("aria-disabled") == "true" and "fixed" in hero.inner_text()
        hero.click(force=True)
        pg.wait_for_timeout(300)
        assert pg.locator("[data-slot-ways]").count() == 0 and hero.get_attribute("aria-pressed") == "false"      # a fixed slot deals nothing
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_settings_ends_with_the_inventory_line_which_opens_the_slots(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand").wait_for(timeout=WAIT_MS)
        open_settings(pg)
        line = pg.locator('[data-settings="inventory"]')
        assert line.inner_text().split("\n")[0].strip().lower() == "how the project is set"
        assert pg.evaluate("() => { const f = [...document.querySelectorAll('.place .shell-form > *')]; return f[f.length - 1].dataset.settings; }") == "inventory"       # the last line
        line.get_by_role("button", name="Inventory").click()
        pg.locator(".slots-table").wait_for(timeout=WAIT_MS)
        assert pg.locator('.place[aria-label="Settings"]').count() == 0
        assert ("ideas.stall", {"chair": ""}) in host.log
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("chair", [None, "tech"])
def test_at_1280_by_800_nothing_overflows_the_table(gui, chair):
    pg, host, log = opened(gui, chair)
    try:
        assert pg.viewport_size == {"width": 1280, "height": 800}
        pg.wait_for_timeout(400)
        got = pg.evaluate("""() => {
          const pane = document.querySelector('.table-pane').getBoundingClientRect(), out = [];
          for (const e of document.querySelectorAll('.slots, .slot, .slot-card, .stall-seats')) {
            const r = e.getBoundingClientRect();
            if (r.right > pane.right + 1 || r.left < pane.left - 1) out.push([e.className, Math.round(r.left), Math.round(r.right), Math.round(pane.right)]);
          }
          const de = document.documentElement, t = document.querySelector('.slots-table');
          return { out, sideways: de.scrollWidth > de.clientWidth, table: [t.scrollWidth, t.clientWidth] };
        }""")
        assert not got["out"], got
        assert not got["sideways"] and got["table"][0] <= got["table"][1], got
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_narrow_page_keeps_the_stall_and_a_ware_pressed_is_taken(gui):
    pg, host, log = open_hand(gui, host=StallHost(), width="narrow")
    try:
        pg.locator(".table-tabs__end .stall-pack").click()
        pg.locator(".stall-rug .stall-ware").first.wait_for(timeout=WAIT_MS)
        assert pg.locator(".slots-table, .slot-card").count() == 0 and pg.locator(".stall-service, .carry-card").count() == 0
        assert plate(pg, "target", "balance").inner_text() == "in your hand"
        pg.locator('.stall-ware[data-ware="quality"] .stall-ware__press').click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "", "slot": "target", "value": "quality"}))
        pg.wait_for_function("() => document.querySelector('.stall-receipt [data-undo]')", timeout=WAIT_MS)
        pg.locator(".stall-receipt [data-undo]").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "", "slot": "target", "value": "balance"}))
        narrow.no_sideways(pg)
    finally:
        pg.close()
    assert not log, "\n".join(log)


class ArchitectHost(HeroHost):
    """A Tech party led by the Architect (whose craft map is the System) with a hero that is not Tech's default: its table is the hero's."""

    def __init__(self):
        super().__init__(table("sh-xp", "lanes", XP, {}), laying=False)
        for p in self.parties:
            if p["slug"] == "tech":
                p["leader"] = {**p["leader"], "slug": "architect"}


def test_a_tech_party_with_a_non_default_hero_shows_its_heros_table_not_the_system(gui):
    pg, host, log = open_hand(gui, host=ArchitectHost())
    try:
        open_tab(pg, "tech")
        pg.locator(".hm").wait_for(timeout=WAIT_MS)
        assert ("ideas.hero_table", {"party": "tech"}) in host.log
        assert [t.lower() for t in pg.locator(".hm-place__nm").all_inner_texts()] == ["red", "green", "refactor", "released small"]
    finally:
        pg.close()
    assert not log, "\n".join(log)


class MakerShelfHost(StallHost):
    """Art's maker data on the existing chair fixture; Tech retains its own shelves."""

    def __init__(self):
        super().__init__()
        self.carry["art"] = copy.deepcopy(self.carry["tech"])
        self.parties.append({**copy.deepcopy(next(p for p in self.parties if p["slug"] == "tech")), "slug": "art", "title": "Art party"})

    def shelves(self, chair):
        shelves = super().shelves(chair)
        if chair == "art":
            shelves.append({"id": "craft_tools", "slot": "craft_tools", "kind": "makers", "label": "Its makers",
                            "sub": "Run in Orkboard on your key", "wares": [
                ware("openai-images", "Picture maker", "OpenAI Images", {"money": "1.25 USD cap"},
                     title="OpenAI Images", makes="pictures", leaves="The picture prompt is sent to OpenAI."),
                ware("elevenlabs-sound", "Sound maker", "ElevenLabs Sound Effects", {"money": "about 1.25 USD cap"},
                     title="ElevenLabs Sound Effects", makes="sound", leaves="The sound prompt is sent to ElevenLabs.")
            ]})
        return shelves


def test_art_lays_makers_after_its_ai_tool_and_tier_with_money_and_disclosures(gui):
    pg, host, log = opened(gui, "art", host=MakerShelfHost())
    try:
        assert pg.locator(".slots .slot-card").evaluate_all("els => els.map(e => e.dataset.slot)") == ["hero", "tool", "tier", "size", "answers"]
        assert pg.locator(".stall-shelf").evaluate_all("els => els.map(e => e.dataset.shelf)") == ["craft_tools"]                 # the makers lie under the slots and the seats
        assert pg.locator(".slots").bounding_box()["y"] < pg.locator('[data-shelf="craft_tools"]').bounding_box()["y"]
        makers = pg.locator('[data-shelf="craft_tools"]')
        assert makers.locator(".stall-shelf__lab b").inner_text().lower() == "its makers"
        assert makers.locator(".stall-relic__word").all_inner_texts() == ["Picture maker", "Sound maker"]
        assert makers.locator(".stall-maker__service").all_inner_texts() == ["OpenAI Images", "ElevenLabs Sound Effects"]
        assert makers.locator(".ork-sign.picture, .ork-sign.sound").count() == 2
        assert makers.locator(".stall-price").all_inner_texts() == ["1.25 USD cap", "about 1.25 USD cap"]
        assert makers.locator(".stall-maker__leaves").count() == 2
        assert "What leaves this computer" in makers.inner_text()
        assert makers.locator(".stall-price").first.evaluate("e => getComputedStyle(e).color") == pg.locator('.stall-price.is-money').first.evaluate("e => getComputedStyle(e).color")
        pg.locator('.stall-ware[data-ware="openai-images"] .stall-ware__press').focus()
        assert pg.locator(":focus").get_attribute("aria-label") == "Its makers: Picture maker"
        pg.locator('.stall-ware[data-ware="elevenlabs-sound"] .stall-ware__press').focus()
        assert pg.locator(":focus").get_attribute("aria-label") == "Its makers: Sound maker"
        open_tab(pg, "tech")
        pg.wait_for_function("() => document.querySelector('.slots-table')?.dataset.stall === 'tech'", timeout=WAIT_MS)
        assert pg.locator('[data-shelf="craft_tools"]').count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("why", ["no key on this computer", "its AI tool cannot make it", "no official API"])
def test_unavailable_maker_says_why_on_focus_and_hover_without_harness(gui, why):
    class MissingMakerHost(MakerShelfHost):
        def shelves(self, chair):
            shelves = super().shelves(chair)
            for s in shelves:
                if s["slot"] == "craft_tools":
                    s["wares"][0].update(here=False, why=why)
            return shelves

    pg, host, log = opened(gui, "art", host=MissingMakerHost())
    try:
        w = pg.locator('[data-slot="craft_tools"][data-ware="openai-images"]')
        reason = w.locator(".stall-maker__why")
        assert w.locator(".stall-price").inner_text().strip() == "not here"
        press = w.locator(".stall-ware__press")
        press.focus()
        assert reason.is_visible() and why in reason.inner_text()
        assert press.get_attribute("aria-describedby") == reason.get_attribute("id")
        pg.locator(".stall-pack").first.focus()
        w.hover()
        assert reason.is_visible() and why in reason.inner_text()
        # Test the computed reading ink against the rug's token background.
        contrast = reason.evaluate('''e => {
          const s = getComputedStyle(e), root = getComputedStyle(document.documentElement);
          const lum = c => { const rgb = c.match(/[\\d.]+/g).slice(0,3).map(Number).map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return rgb[0]*.2126 + rgb[1]*.7152 + rgb[2]*.0722; };
          const probe = document.createElement('span'); e.append(probe);
          probe.style.color = root.getPropertyValue('--ork-panel');
          const a = lum(s.color), b = lum(getComputedStyle(probe).color); probe.remove();
          return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
        }''')
        assert contrast >= 4.5
        assert "harness" not in pg.locator(".slots-table").inner_text().lower()
        # Scan words a reader receives; orkUI's image src filenames keep their names.
        reader_attributes = pg.locator(".slots-table").evaluate('''e =>
          [e, ...e.querySelectorAll('*')].flatMap(node =>
            ['aria-label', 'title', 'alt'].map(name => node.getAttribute(name) || '')
          ).join(' ')
        ''')
        assert "harness" not in reader_attributes.lower()
        if why == "no key on this computer":
            reason.get_by_role("button", name="Settings · sign-ins").click()
            assert pg.locator('[data-place][aria-label="Settings"]').is_visible()
    finally:
        pg.close()
    assert not log, "\n".join(log)


class CapMakerHost(MakerShelfHost):
    def __init__(self):
        super().__init__()
        self.caps = {}

    def shelves(self, chair):
        shelves = super().shelves(chair)
        for s in shelves:
            if s["slot"] == "craft_tools":
                for w in s["wares"]:
                    cap = self.caps.get(w["id"])
                    w.update(here=True, cap=cap, prices=[{"currency": "USD"}])
                    w["price"] = {"money": f"{'about ' if w['makes'] == 'sound' else ''}{cap['amount']} USD cap"} if cap else {"word": "Set a cap"}
        return shelves

    def handle(self, name, a):
        if name == "ideas.stall_take" and a.get("slot") == "craft_tools":
            self.log.append((name, a))
            self.caps[a["value"]] = a["cap"]
            return self.bump({"stall": self.stall(a["chair"])})
        return super().handle(name, a)


@pytest.mark.parametrize("activation", ["click", "Enter"])
def test_a_paid_maker_waits_for_a_cap_and_keeps_focus_after_redraw(gui, activation):
    pg, host, log = opened(gui, "art", host=CapMakerHost())
    try:
        w = pg.locator('[data-slot="craft_tools"][data-ware="openai-images"]')
        press = w.locator(".stall-ware__press")
        assert w.locator(".stall-price").inner_text() == "Set a cap"
        if activation == "click":
            w.locator(".stall-maker__cap").click()
        else:
            press.focus()
            pg.keyboard.press("Enter")
        field = w.get_by_label("Cap per round (USD)")
        field.wait_for(timeout=WAIT_MS)
        assert field.input_value() == "" and field.evaluate("e => e === document.activeElement")
        assert field.bounding_box()["width"] >= 24 and field.bounding_box()["height"] >= 24
        assert w.locator("label").is_visible()
        for amount in ("", "wrong", "0", "-2"):
            field.fill(amount)
            w.get_by_role("button", name="Save cap").click()
            assert w.get_by_role("alert").inner_text() == "Enter a positive amount in USD."
            assert not any(n == "ideas.stall_take" for n, _ in host.log)
        field.fill("1.25")
        pg.keyboard.press("Enter")
        pg.wait_for_function("() => document.querySelector('[data-ware=\"openai-images\"] .stall-price')?.textContent.includes('1.25 USD cap')", timeout=WAIT_MS)
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "art", "slot": "craft_tools", "value": "openai-images", "cap": {"amount": "1.25", "currency": "USD"}}))
        assert w.locator("form").count() == 0
        assert press.evaluate("e => e === document.activeElement")
        assert press.evaluate("e => e.matches(':focus-visible')")
        pg.keyboard.press("Enter")
        assert field.input_value() == "1.25"
        pg.keyboard.press("Escape")
        assert w.locator("form").count() == 0 and pg.locator(".slots-table").count() == 1
        assert press.evaluate("e => e === document.activeElement")
        pg.keyboard.press("Escape")
        assert pg.locator(".slots-table").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


@pytest.mark.parametrize("cap_open", [False, True])
def test_arts_cap_plate_fits_at_1280_by_800_and_has_a_picture(gui, cap_open):
    host = CapMakerHost()
    host.caps["elevenlabs-sound"] = {"amount": "1.25", "currency": "USD"}
    pg, host, log = opened(gui, "art", host=host)
    try:
        assert pg.viewport_size == {"width": 1280, "height": 800}
        assert pg.locator('[data-shelf="craft_tools"] .stall-shelf__lab b').inner_text() == "ITS MAKERS"
        w = pg.locator('[data-slot="craft_tools"][data-ware="openai-images"]')
        if cap_open:
            w.locator(".stall-maker__cap").click()
            w.get_by_label("Cap per round (USD)").wait_for(timeout=WAIT_MS)
        w.scroll_into_view_if_needed()
        money = pg.locator('[data-slot="craft_tools"][data-ware="elevenlabs-sound"] .stall-price.is-money')
        assert money.inner_text() == "about 1.25 USD cap"
        assert money.evaluate("e => getComputedStyle(e).color") == money.evaluate("""e => {
          const p = document.createElement('span'); p.style.color = 'var(--ork-warning)'; e.append(p);
          const c = getComputedStyle(p).color; p.remove(); return c;
        }""")
        assert pg.evaluate("""() => {
          const pane = document.querySelector('.table-pane').getBoundingClientRect();
          return [...document.querySelectorAll('.slots-table, .stall-ware, .stall-maker__form, .stall-maker__form input')].every(e => {
            const r = e.getBoundingClientRect(); return r.left >= pane.left && r.right <= pane.right;
          }) && document.documentElement.scrollWidth <= document.documentElement.clientWidth;
        }""")
        shot(pg, f"art-makers-cap-{'open' if cap_open else 'closed'}-1280x800")
    finally:
        pg.close()
    assert not log, "\n".join(log)


WHY_SCENE = "a web app has no scene to shape"


class LockedHeroHost(StallHost):
    def shelves(self, chair):
        shelves = super().shelves(chair)
        if chair == "tech":
            shelves[0]["wares"].append(ware("sh-scene", "Scene Shaman", "Scenes and their beats", {"locked": WHY_SCENE}, head=SH, stats=stats("Scenes", "scene → beat → cut", "standard", 2, 2)))
            shelves[0]["at"] = 0
        return shelves


def test_a_locked_hero_says_its_why_on_its_card_and_takes_nothing(gui):
    pg, host, log = opened(gui, "tech", host=LockedHeroHost())
    try:
        deal(pg, "hero")
        w = way(pg, "hero", "sh-scene")
        assert w.get_attribute("aria-disabled") == "true" and w.get_attribute("title") == WHY_SCENE and WHY_SCENE in w.get_attribute("aria-label")
        assert w.locator('[data-price="locked"]').inner_text() == "not here"
        assert way(pg, "hero", "sh-xp").get_attribute("aria-disabled") is None                  # an offered hero is not locked
        before = [e for e in host.log if e[0] == "ideas.stall_take"]
        w.click(force=True)
        w.focus()
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(300)
        assert [e for e in host.log if e[0] == "ideas.stall_take"] == before
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


def test_a_design_slot_stars_one_way_by_a_sign_named_for_the_pick_and_the_slot_never_does_spec_164_i(gui):
    pg, host, log = opened(gui, "tech", host=PickHost())
    try:
        deal(pg, "hero")
        assert pg.locator('[data-slot-ways="hero"] .slot-way').evaluate_all("els => els.map((e) => e.dataset.way)") == ["dry-heur", "dry-sprint", "dry-a11y"]
        star = pg.locator(".slot-way__star")
        assert star.count() == 1 and star.get_attribute("aria-label") == "The Orkmaster's pick" and star.get_attribute("role") == "img"
        assert pg.locator('.slot-way[data-way="dry-heur"] .slot-way__star').count() == 1
        assert pg.locator(".slots .slot-card .slot-way__star, .slots .slot-card .ork-sign.pick").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_games_art_has_sprite_dryad_on_its_slot_drawn_by_its_own_head_with_no_choice_spec_164_i(gui):
    host = PickHost()
    host.art = True
    pg, host, log = opened(gui, "tech", host=host)
    try:
        card = slot(pg, "hero")
        assert card.count() == 1 and card.locator(".slot-card__name").inner_text() == "Sprite Dryad" and "hero-dry-sprite" in (card.inner_html() or "")
        assert "no choice" in card.inner_text() and card.get_attribute("aria-disabled") == "true"
        card.click(force=True)
        pg.wait_for_timeout(300)
        assert pg.locator("[data-slot-ways]").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


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
        pg.set_viewport_size({"width": 1366, "height": 768})                                                          # the laptop the window is fitted to
        deal(pg, "answers")
        shot(pg, "h4-leader-inventory")
    finally:
        pg.close()
    assert not log, "\n".join(log)
