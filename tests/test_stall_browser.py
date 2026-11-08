"""Spec 157 D (docs/specs/157-the-inventory-a-merchants-stall.md; decisions §267.1), in a real browser against a stub host that answers `ideas.stall`, `ideas.stall_take` and `ideas.stall_back` in the host's real shapes
(`orkboard/gui/ideas_stall.py`): the backpack at the tabs' end opens the stall and Esc closes it; the rug's shelves and the plate under each ware (in your hand, not here with its why, a word, a share with the vial, money);
a ware pressed sends the take and Undo the value it had; a card of the hand dropped on the service, and on the discard, sends `stall_back`; a tab pressed picks the chair; Settings' last line opens it; at 1280 x 800 nothing
overflows the table; and a Tech party whose hero is not its craft's default reaches its hero's table. Screenshots go to the folder `STALL_SHOTS` names when it is set."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

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
# the Orkmaster's chair, as the host lays it: five shelves of small wares (a shelf: slot, label, sub, [(id, word, line)])
KEEPER = [("target", "How deep", "How much the orks spend on a goal", [("thrift", "Thrift", "Cheaper models, fewer checks"), ("balance", "Balance", "The usual mix"), ("quality", "Quality", "Better models, more checks")]),
          ("autostart", "Starts by itself", "A safe plan starts without asking", [("on", "On", "A safe plan starts by itself"), ("off", "Off", "Every plan waits for you")]),
          ("work_at_night", "Works at night", "Plans that would start by themselves wait for the night", [("on", "On", "The orks work in the night's hours"), ("off", "Off", "The orks do not start work at night")]),
          ("push", "Push after merging", "Whether a merge into the work branch is pushed", [("on", "On", "Results are pushed after they merge"), ("off", "Off", "Results stay on this computer")])]
PRICE = {("target", "thrift"): {"word": "lighter"}, ("target", "quality"): {"word": "heavier"}}
HEROES = [("sh-c4", "Sh.man", "C4 and hotspots", stats("C4 and hotspots", "containers → parts → hotspots", "standard", 2, 2)),
          ("sh-xp", "Spike Shaman", "Extreme programming", stats("Extreme programming", "test → code → refactor", "standard", 3, 2))]
TIERS = [("laborer", "Laborer", "The lightest model of its tool", {"share": -2}), ("warrior", "Warrior", "The middle model", None), ("elder", "Elder", "The strongest model", {"share": 3})]
TOOLS = [("", "Main tool", "The potions' order: the first AI tool in your hand that has mana", None), ("claude", "Claude", "Every seat works on Claude", {"money": "up to $2 a night"}), ("codex", "Codex", "Signed out", {"locked": "Codex is signed out"})]


class StallHost(HandHost):
    """The stall of the host in stub form: what is carried per chair and slot, each ware's price by what is carried (a ware carried is `{mine}`)."""

    def __init__(self, **more):
        super().__init__(bare=True, **more)
        self.carry = {"": {"target": "balance", "autostart": "on", "work_at_night": "off", "push": "off"},
                      "tech": {"hero": "sh-c4", "tool": "", "tier": "warrior"}}
        self.defaults = {"": {"target": "balance", "autostart": "on", "work_at_night": "off", "push": "off"}, "tech": {"hero": "sh-c4", "tool": "", "tier": "warrior"}}

    def shelves(self, chair):
        now = self.carry.get(chair) or {}

        def priced(slot, id, base):
            return {"mine": True} if now.get(slot) == id else base
        if chair == "":
            return [{"id": slot, "label": label, "sub": sub, "kind": "small", "slot": slot,
                     "wares": [ware(id, word, line, priced(slot, id, PRICE.get((slot, id)) or {"word": "same cost"})) for id, word, line in wares]} for slot, label, sub, wares in KEEPER]
        if chair == "release":
            lock = {"locked": "Release is in every project: its hero and its gate are fixed"}
            return [{"id": "hero", "label": "Its hero", "sub": "The school its leader looks by", "kind": "heroes", "slot": "hero",
                     "wares": [ware("lich-nk", "Release Night King", "DORA's keys, readiness and semver", lock, head={"race": "lich", "tier": "elder"}, stats=stats("DORA's keys", "dev → the gate → main", "standard", 1, 3))]}]
        return [{"id": "hero", "label": "Its hero", "sub": "The school its leader looks by", "kind": "heroes", "slot": "hero",
                 "wares": [ware(id, word, line, priced("hero", id, {"word": "one pass"}), head=SH, stats=st) for id, word, line, st in HEROES]},
                {"id": "tool", "label": "Its AI tool", "sub": "What runs this party's goals", "kind": "small", "slot": "tool",
                 "wares": [ware(id, word, line, priced("tool", id, price or {"word": "same cost"})) for id, word, line, price in TOOLS]},
                {"id": "tier", "label": "Its seats' tier", "sub": "The model each seat of the party gets", "kind": "small", "slot": "tier",
                 "wares": [ware(id, word, line, priced("tier", id, price or {"word": "same cost"})) for id, word, line, price in TIERS]}]

    def stall(self, chair):
        shelves = self.shelves(chair)
        now = self.carry.get(chair) or {}
        hand = []
        for s in shelves:
            w = next((x for x in s["wares"] if x["id"] == now.get(s["slot"], "")), s["wares"][0])
            card = {"slot": s["slot"], "label": s["label"], "word": w["word"], "yours": now.get(s["slot"], ""), "line": w["line"], "fixed": chair == "release"}
            if w.get("head"):
                card["head"] = w["head"]
            hand.append(card)
        say = "Every ware has its price in words: lighter or heavier than what you carry, one pass, or the same cost. Nothing is guessed." if chair == "" else "Sh.man looks by C4 and hotspots. It lays its craft's map."
        return {"chair": chair, "whose": "The Orkmaster" if chair == "" else "tech party", "say": say, "shelves": shelves, "hand": hand}

    def handle(self, name, a):
        if name == "ideas.stall":
            self.log.append((name, a))
            return self.stall(a["chair"])
        if name == "ideas.stall_take":
            self.log.append((name, a))
            old = self.carry[a["chair"]].get(a["slot"], "")
            self.carry[a["chair"]][a["slot"]] = a["value"]
            return self.bump({"stall": self.stall(a["chair"]), "undo": {"slot": a["slot"], "value": old}})
        if name == "ideas.stall_back":
            self.log.append((name, a))
            old = self.carry[a["chair"]].get(a["slot"], "")
            self.carry[a["chair"]][a["slot"]] = self.defaults[a["chair"]][a["slot"]]
            return self.bump({"stall": self.stall(a["chair"]), "undo": {"slot": a["slot"], "value": old}})
        return super().handle(name, a)


def opened(gui, chair=None, host=None):
    """The page, the stall open on a chair: the tab pressed first (a party's), then the backpack."""
    pg, host, log = open_hand(gui, host=host or StallHost())
    if chair:
        open_tab(pg, chair)
    pg.locator("[data-backpack]").click()
    pg.locator(".stall-rug .stall-ware").first.wait_for(timeout=WAIT_MS)
    return pg, host, log


def plate(pg, slot, id):
    return pg.locator(f'.stall-ware[data-slot="{slot}"][data-ware="{id}"] .stall-price')


def test_the_backpack_opens_the_stall_and_esc_shuts_it(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pack = pg.locator("[data-backpack]")
        pack.wait_for(timeout=WAIT_MS)
        assert pack.get_attribute("title") == "Inventory: how the project is set" and pack.get_attribute("aria-pressed") == "false"
        head = pg.locator('.release-lane__head[data-room-things="discard"]')
        assert head.locator("[data-backpack]").count() == 1 and pg.locator(".table-tabs__end .stall-pack").count() == 0       # the backpack stands at the left of the discard column's head, not at the tabs' end (spec 161 H)
        assert pack.bounding_box()["x"] > pg.viewport_size["width"] * 0.8 and head.locator(".ork-pack:not(.is-open)").count() == 1
        assert pg.locator(".stall").count() == 0 and pg.locator(".table-pane").get_attribute("data-stall") is None
        pack.click()
        pg.locator(".stall").wait_for(timeout=WAIT_MS)
        assert pg.locator(".table-pane").get_attribute("data-stall") == "open"
        assert pg.locator(".table-pane").evaluate("e => e.classList.contains('ork-leather')") and head.locator(".ork-pack.is-open").count() == 1       # the open pack, the table in its leather (stitched, two straps)
        assert pg.locator(".table-pane").evaluate("e => getComputedStyle(e).outlineStyle") == "dashed"
        assert pack.get_attribute("title") == "Close the inventory" and pack.get_attribute("aria-pressed") == "true"
        assert ("ideas.stall", {"chair": ""}) in host.log
        assert pg.locator(".hand .carry").count() == 1 and pg.locator(".hand .hand-stack, .hand .hand-slot").count() == 0       # what you carry, not the stacks
        assert pg.locator(".table-tab").count() > 0                                  # the tabs stay
        pg.keyboard.press("Escape")
        pg.wait_for_function("() => !document.querySelector('.stall')", timeout=WAIT_MS)
        assert pg.locator(".hand .carry").count() == 0 and pg.locator("[data-backpack]").get_attribute("aria-pressed") == "false"
        assert not pg.locator(".table-pane").evaluate("e => e.classList.contains('ork-leather')")        # shut, the bronze is back
        pack.click()
        pg.locator(".stall").wait_for(timeout=WAIT_MS)
        pack.click()
        pg.wait_for_function("() => !document.querySelector('.stall')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_the_orkmasters_rug_lays_every_ware_with_its_plate_and_its_hand_what_it_carries(gui):
    pg, host, log = opened(gui)
    try:
        assert pg.locator(".stall-bubble").inner_text().startswith("Every ware has its price in words")
        assert pg.locator(".stall-merchant__name").inner_text().lower() == "orkmaster"
        box = pg.locator(".stall-merchant .ork-race__head").bounding_box()
        assert (round(box["width"]), round(box["height"])) == (96, 88)                          # the merchant's crowned head at 96 x 88
        assert pg.locator(".stall-shelf").evaluate_all("els => els.map((e) => e.dataset.shelf)") == ["target", "autostart", "work_at_night", "push"]
        assert [t.lower() for t in pg.locator(".stall-shelf__lab b").all_inner_texts()[:2]] == ["how deep", "starts by itself"]
        assert pg.locator(".stall-ware").count() == 3 + 2 + 2 + 2                              # every ware at once
        assert plate(pg, "target", "balance").inner_text() == "in your hand" and plate(pg, "target", "balance").evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed"
        assert plate(pg, "target", "thrift").inner_text() == "lighter" and plate(pg, "target", "quality").inner_text() == "heavier"
        green = plate(pg, "target", "thrift").evaluate("e => getComputedStyle(e).color"), plate(pg, "target", "quality").evaluate("e => getComputedStyle(e).color")
        assert green[0] != green[1]                                                              # lighter is in the success colour, heavier in the ink
        assert plate(pg, "autostart", "off").inner_text() == "same cost"
        cards = pg.locator(".carry-card")
        assert cards.evaluate_all("els => els.map((e) => e.dataset.slot)") == ["target", "autostart", "work_at_night", "push"]
        assert "Balance" in cards.first.inner_text() and "How deep" in cards.first.inner_text() and "The usual mix" in cards.first.inner_text()
        assert "What you carry of the whole project" in pg.locator(".carry__lab").inner_text() or "what you carry of the whole project" in pg.locator(".carry__lab").inner_text()
        shot(pg, "stall-orkmaster")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_leaders_rug_has_its_heroes_on_top_its_small_things_below_and_every_form_of_plate(gui):
    pg, host, log = opened(gui, "tech")
    try:
        assert ("ideas.stall", {"chair": "tech"}) in host.log
        assert pg.locator(".stall-title").inner_text() == "Inventory"
        assert pg.locator(".stall-shelf.is-heroes .stall-hero").count() == 2
        sh = pg.locator('.stall-ware[data-ware="sh-xp"]')
        assert "Spike Shaman" in sh.inner_text() and "Extreme programming" in sh.inner_text() and "test → code → refactor" in sh.inner_text()
        assert sh.locator(".stall-pips").count() == 2 and sh.locator(".stall-pips i.on").count() == 3 + 2       # the stats' bars: decides 3, says no 2
        assert sh.locator(".ork-race__head").count() == 1
        top, low = pg.locator(".stall-shelf.is-heroes").bounding_box(), pg.locator(".stall-low").bounding_box()
        assert top["y"] + top["height"] <= low["y"] + 1                                           # the heroes on the top shelf, the small things below
        assert plate(pg, "hero", "sh-c4").inner_text() == "in your hand" and plate(pg, "hero", "sh-xp").inner_text() == "one pass"
        share = plate(pg, "tier", "elder")
        assert share.inner_text().strip() == "+3%" and share.locator(".ork-potion.size-vial").count() == 1
        less = plate(pg, "tier", "laborer")
        assert less.inner_text().strip() == "−2%" and less.locator(".ork-potion").count() == 1
        assert less.evaluate("e => getComputedStyle(e).color") != share.evaluate("e => getComputedStyle(e).color")      # a saving in the success colour
        money = plate(pg, "tool", "claude")
        assert money.inner_text().strip() == "up to $2 a night" and money.get_attribute("data-price") == "money"
        assert money.evaluate("e => getComputedStyle(e).color") not in (share.evaluate("e => getComputedStyle(e).color"), less.evaluate("e => getComputedStyle(e).color"))      # money in the warning colour
        locked = plate(pg, "tool", "codex")
        assert locked.inner_text().strip() == "not here" and locked.locator(".stall-lock").count() == 1 and locked.get_attribute("title") == "Codex is signed out"
        assert pg.locator('.stall-ware[data-ware="codex"] .stall-ware__press').get_attribute("aria-disabled") == "true"
        cards = pg.locator(".carry-card")
        assert cards.evaluate_all("els => els.map((e) => e.dataset.slot)") == ["hero", "tool", "tier"]
        assert "Sh.man" in cards.first.inner_text() and cards.first.locator(".ork-race__head").count() == 1
        assert "what you carry of tech party" in pg.locator(".carry__lab").inner_text()
        shot(pg, "stall-tech")
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_hovering_a_ware_shows_it_in_its_card_and_the_merchant_worries_at_two_percent_or_more(gui):
    pg, host, log = opened(gui, "tech")
    try:
        face = lambda: pg.locator(".stall-merchant .ork-race__head").get_attribute("data-mood")      # noqa: E731
        pg.locator('.stall-ware[data-ware="elder"] .stall-ware__press').hover()
        pg.wait_for_function("() => document.querySelector('.carry-card[data-slot=tier]').classList.contains('is-ghost')", timeout=WAIT_MS)
        ghost = pg.locator('.carry-card[data-slot="tier"]')
        assert "Elder" in ghost.inner_text() and ghost.evaluate("e => getComputedStyle(e).borderTopStyle") == "dashed"
        assert face() == "worried"
        assert "Elder: The strongest model" in pg.locator(".stall-bubble").inner_text()
        shot(pg, "stall-tech-hover")
        pg.locator('.stall-ware[data-ware="laborer"] .stall-ware__press').hover()
        pg.wait_for_function("() => document.querySelector('.carry-card[data-slot=tier]').innerText.includes('Laborer')", timeout=WAIT_MS)
        assert face() == "focused"
        pg.mouse.move(5, 5)
        pg.wait_for_function("() => !document.querySelector('.carry-card.is-ghost')", timeout=WAIT_MS)
        assert "Warrior" in ghost.inner_text()
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_ware_pressed_sends_the_take_the_receipt_says_so_and_undo_sends_the_old_value(gui):
    pg, host, log = opened(gui, "tech")
    try:
        pg.locator('.stall-ware[data-ware="elder"] .stall-ware__press').click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "tier", "value": "elder"}))
        pg.wait_for_function("() => document.querySelector('[data-receipt]').innerText.includes('Elder')", timeout=WAIT_MS)
        assert plate(pg, "tier", "elder").inner_text() == "in your hand" and plate(pg, "tier", "warrior").inner_text() != "in your hand"
        assert "Elder" in pg.locator('.carry-card[data-slot="tier"]').inner_text()
        pg.locator('.stall-ware[data-ware="warrior"]').wait_for(timeout=WAIT_MS)
        assert pg.locator('.stall-merchant .ork-race__head').get_attribute("data-mood") == "pleased"
        pg.locator("[data-undo]").click()
        assert _sent(pg, host, ("ideas.stall_take", {"chair": "tech", "slot": "tier", "value": "warrior"}))
        pg.wait_for_function("() => !document.querySelector('[data-undo]')", timeout=WAIT_MS)
        assert plate(pg, "tier", "warrior").inner_text() == "in your hand"
        before = [e for e in host.log if e[0] == "ideas.stall_take"]
        pg.locator('.stall-ware[data-ware="warrior"] .stall-ware__press').click(force=True)          # what is carried is not taken again
        pg.locator('.stall-ware[data-ware="codex"] .stall-ware__press').click(force=True)   # a locked ware is not taken
        pg.wait_for_timeout(300)
        assert [e for e in host.log if e[0] == "ideas.stall_take"] == before
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_dropped_on_the_service_goes_back_to_its_default_and_so_does_one_lifted_and_the_service_pressed(gui):
    host = StallHost()
    host.carry["tech"]["tier"] = "elder"
    host.carry["tech"]["hero"] = "sh-xp"
    pg, host, log = opened(gui, "tech", host=host)
    try:
        assert pg.locator(".stall-service").get_attribute("data-service") == "back" and "free" in pg.locator(".stall-service").inner_text()
        pg.locator('.carry-card[data-slot="tier"]').drag_to(pg.locator(".stall-service"))
        assert _sent(pg, host, ("ideas.stall_back", {"chair": "tech", "slot": "tier"}))
        pg.wait_for_function("() => document.querySelector('[data-receipt]').innerText.includes('back to its default')", timeout=WAIT_MS)
        assert "Warrior" in pg.locator('.carry-card[data-slot="tier"]').inner_text() and plate(pg, "tier", "warrior").inner_text() == "in your hand"
        pg.locator(".stall-service").click()                                                  # no card lifted: the merchant says what to do, nothing is sent
        assert "Lift a card of your hand first" in pg.locator(".stall-bubble").inner_text()
        assert [e for e in host.log if e[0] == "ideas.stall_back"] == [("ideas.stall_back", {"chair": "tech", "slot": "tier"})]
        pg.locator('.carry-card[data-slot="hero"]').click()                                   # a card pressed is lifted; Esc lowers it first
        assert pg.locator('.carry-card[data-slot="hero"]').get_attribute("aria-pressed") == "true" and "is-can" in pg.locator(".stall-service").get_attribute("class")
        assert pg.locator('.stall-shelf[data-shelf="hero"]').get_attribute("class").count("is-on") == 1
        pg.keyboard.press("Escape")
        assert pg.locator('.carry-card[data-slot="hero"]').get_attribute("aria-pressed") == "false" and pg.locator(".stall").count() == 1
        pg.locator('.carry-card[data-slot="hero"]').click()
        pg.locator(".stall-service").click()
        assert _sent(pg, host, ("ideas.stall_back", {"chair": "tech", "slot": "hero"}))
        pg.wait_for_function("() => document.querySelector('.carry-card[data-slot=hero]').innerText.includes('Sh.man')", timeout=WAIT_MS)
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_a_card_dropped_on_the_discard_goes_back_to_its_default_only_while_the_stall_is_open(gui):
    pg, host, log = open_hand(gui, host=HandWithDiscard())
    try:
        pg.locator(".release-lane").wait_for(timeout=WAIT_MS)
        pg.locator("[data-backpack]").click()
        pg.locator(".carry-card").first.wait_for(timeout=WAIT_MS)
        open_tab(pg, "tech")
        pg.locator('.carry-card[data-slot="tier"]').wait_for(timeout=WAIT_MS)
        pg.evaluate("() => import('/static/js/table/stallstate.js').then(() => 1)")                          # the module is loaded: the lane answers a drop
        pg.locator('.carry-card[data-slot="tier"]').drag_to(pg.locator(".release-lane"))
        assert _sent(pg, host, ("ideas.stall_back", {"chair": "tech", "slot": "tier"}))
        assert pg.locator(".release-lane").count() == 1                                    # nothing else changed on it
        shot(pg, "stall-discard")
    finally:
        pg.close()
    assert not log, "\n".join(log)


class HandWithDiscard(StallHost):
    """The project of the hand's tests with goals done (the discard lane holds cards) and the stall's answers."""

    def __init__(self):
        HandHost.__init__(self)                                                              # not bare: goals done and ready for main lie in the discard
        self.carry = copy.deepcopy(StallHost().carry)
        self.defaults = copy.deepcopy(StallHost().defaults)


def test_a_tab_pressed_while_open_picks_the_chair_and_the_hand_follows(gui):
    pg, host, log = opened(gui)
    try:
        open_tab(pg, "tech")
        pg.wait_for_function("() => document.querySelector('.stall')?.dataset.stall === 'tech'", timeout=WAIT_MS)
        assert ("ideas.stall", {"chair": "tech"}) in host.log and pg.locator(".stall-shelf.is-heroes").count() == 1
        assert pg.locator(".carry").get_attribute("data-carry") == "tech"
        pg.locator('.col-head__tab[data-tab="orkmaster"], .table-tab[data-tab="orkmaster"]').first.click()
        pg.wait_for_function("() => document.querySelector('.stall')?.dataset.stall === 'orkmaster'", timeout=WAIT_MS)
        assert pg.locator(".stall-shelf.is-heroes").count() == 0
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_releases_rug_is_all_locked(gui):
    pg, host, log = opened(gui, "release")
    try:
        assert ("ideas.stall", {"chair": "release"}) in host.log
        assert plate(pg, "hero", "lich-nk").inner_text().strip() == "not here"
        assert pg.locator(".carry-card.is-fixed").count() == 1 and pg.locator(".carry-card").first.get_attribute("draggable") is None
        pg.locator(".carry-card").first.click()
        assert pg.locator(".carry-card.is-on").count() == 0                                   # a fixed card is not lifted
    finally:
        pg.close()
    assert not log, "\n".join(log)


def test_settings_ends_with_the_inventory_line_which_opens_the_stall(gui):
    pg, host, log = open_hand(gui, host=StallHost())
    try:
        pg.locator(".hand").wait_for(timeout=WAIT_MS)
        open_settings(pg)
        line = pg.locator('[data-settings="inventory"]')
        assert line.inner_text().split("\n")[0].strip().lower() == "how the project is set"
        assert pg.evaluate("() => { const f = [...document.querySelectorAll('.place .shell-form > *')]; return f[f.length - 1].dataset.settings; }") == "inventory"       # the last line
        line.get_by_role("button", name="Inventory").click()
        pg.locator(".stall").wait_for(timeout=WAIT_MS)
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
          for (const e of document.querySelectorAll('.stall-rug, .stall-bubble, .stall-merchant, .stall-ware, .stall-service')) {
            const r = e.getBoundingClientRect();
            if (r.right > pane.right + 1 || r.left < pane.left - 1) out.push([e.className, Math.round(r.left), Math.round(r.right), Math.round(pane.right)]);
          }
          const de = document.documentElement;
          return { out, sideways: de.scrollWidth > de.clientWidth, stall: [document.querySelector('.stall').scrollWidth, document.querySelector('.stall').clientWidth] };
        }""")
        assert not got["out"], got
        assert not got["sideways"] and got["stall"][0] <= got["stall"][1], got
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
        assert pg.locator(".stall-shelf").evaluate_all("els => els.map(e => e.dataset.shelf)") == ["hero", "tool", "tier", "craft_tools"]
        makers = pg.locator('[data-shelf="craft_tools"]')
        assert makers.locator(".stall-shelf__lab b").inner_text().lower() == "its makers"
        assert makers.locator(".stall-relic__word").all_inner_texts() == ["Picture maker", "Sound maker"]
        assert makers.locator(".stall-maker__service").all_inner_texts() == ["OpenAI Images", "ElevenLabs Sound Effects"]
        assert makers.locator(".ork-sign.picture, .ork-sign.sound").count() == 2
        assert makers.locator(".stall-price").all_inner_texts() == ["1.25 USD cap", "about 1.25 USD cap"]
        assert makers.locator(".stall-maker__leaves").count() == 2
        assert "What leaves this computer" in makers.inner_text()
        assert makers.locator(".stall-price").first.evaluate("e => getComputedStyle(e).color") == pg.locator('.stall-price.is-money').first.evaluate("e => getComputedStyle(e).color")
        tier = pg.locator('.stall-ware[data-slot="tier"]').last.locator("button")
        tier.focus()
        pg.keyboard.press("Tab")
        assert pg.locator(":focus").get_attribute("aria-label") == "Its makers: Picture maker"
        pg.keyboard.press("Tab")
        assert pg.locator(":focus").get_attribute("aria-label") == "Its makers: Sound maker"
        open_tab(pg, "tech")
        pg.wait_for_function("() => document.querySelector('.stall')?.dataset.stall === 'tech'", timeout=WAIT_MS)
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
        assert "harness" not in pg.locator(".stall").inner_text().lower()
        # Scan words a reader receives; orkUI's image src filenames keep their names.
        reader_attributes = pg.locator(".stall").evaluate('''e =>
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
        assert w.locator("form").count() == 0 and pg.locator(".stall").count() == 1
        assert press.evaluate("e => e === document.activeElement")
        pg.keyboard.press("Escape")
        assert pg.locator(".stall").count() == 0
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
          return [...document.querySelectorAll('.stall-rug, .stall-ware, .stall-maker__form, .stall-maker__form input')].every(e => {
            const r = e.getBoundingClientRect(); return r.left >= pane.left && r.right <= pane.right;
          }) && document.documentElement.scrollWidth <= document.documentElement.clientWidth;
        }""")
        shot(pg, f"art-makers-cap-{'open' if cap_open else 'closed'}-1280x800")
    finally:
        pg.close()
    assert not log, "\n".join(log)
