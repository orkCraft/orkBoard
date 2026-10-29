"""Spec 63 part C, the phone (docs/specs/63-party-gathered.md §4, §5 "C"; decisions §76.2): Chromium at 390 × 844 against the stub of tests/test_pwa_shell_browser.py. *Save party* on New party's
sheet: the party's heads (the leader's first, six at most), each from where the sheet shows it at the press (its seat in the bands *Leads*, *Does* and *Checks*, spec 91 §7; one that is not on screen from
*Save party*'s box), travel as copies over the page to the goals bar's deck once the sheet has closed and the deck shows the new party, steps(6) 0.30 s, 35 ms apart, each ending at the deck's centre at
0.4 of its size and gone on landing; then the deck is lit once. Nothing under reduced motion, after a refusal, after 6 s, for New goal taking the new party, or for a team changed from its own screen;
`sw.js` v68."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from orkboard.realm import library, party_presets, roles
from tests.test_pwa_goal_team_browser import _pick_goal
from tests.test_pwa_mixed_parties_browser import _sheet, hosted
from tests.test_pwa_shell_browser import FAB, NO_SCROLL, WAIT_MS, Stub, _called, _open_party, _phone

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

# What the page does is recorded as it happens (a gather lasts half a second): each copy that flies (its box and variables, its computed animation, whether the sheet was still open) and when it is gone,
# and each time a deck is lit.
RECORD = """
(() => {
  window.__gather = [];
  const at = () => Math.round(performance.now());
  const look = () => { if (!window.__screenAt && document.querySelector(".screen:not([hidden])")) window.__screenAt = at(); requestAnimationFrame(look); };     // when a screen first shows over the field
  requestAnimationFrame(look);
  const note = (e) => {
    if (!e.classList || !e.classList.contains("gather-fly") || e.__told) return;
    e.__told = true;
    const cs = getComputedStyle(e), deck = document.querySelector(".partydeck"), d = deck && deck.getBoundingClientRect();
    window.__gather.push({ kind: "fly", at: at(), src: e.getAttribute("src"), left: parseFloat(e.style.left), top: parseFloat(e.style.top), width: parseFloat(e.style.width), height: parseFloat(e.style.height),
      dx: e.style.getPropertyValue("--dx"), dy: e.style.getPropertyValue("--dy"), s: e.style.getPropertyValue("--s"), delay: e.style.getPropertyValue("--delay"),
      name: cs.animationName, duration: cs.animationDuration, timing: cs.animationTimingFunction, waits: cs.animationDelay, position: cs.position, z: cs.zIndex, pointer: cs.pointerEvents,
      parent: e.parentElement.tagName, sheet: Boolean(document.querySelector('dialog[open][aria-label="New party"]')), deck: d && { cx: d.left + d.width / 2, cy: d.top + d.height / 2, goal: deck.dataset.goal } });
  };
  document.addEventListener("DOMContentLoaded", () => new MutationObserver((ms) => {
    for (const m of ms) {
      if (m.type === "attributes") {
        const e = m.target, on = e.classList.contains("is-reward");           // (a class set again in the same turn is one light)
        if (e.classList.contains("partydeck") && on && !e.__lit) {
          const cs = getComputedStyle(e);
          window.__gather.push({ kind: "lit", at: at(), goal: e.dataset.goal, name: cs.animationName, duration: cs.animationDuration, timing: cs.animationTimingFunction });
        }
        e.__lit = on;
      }
      for (const n of m.addedNodes) if (n.nodeType === 1) note(n);
      for (const n of m.removedNodes) if (n.nodeType === 1 && n.classList.contains("gather-fly")) window.__gather.push({ kind: "gone", at: at(), src: n.getAttribute("src") });
    }
  }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] }));
})();
"""
GATHER = "() => window.__gather"
SAVED = "a-tower-game"                                                       # the stub's slug for "A tower game."


def seats_of(preset_id):
    """The seats of a party as New party fills them, the leader's first: a squad of up to five who do and two who check (decisions §151.1, §169.2; one a stage before), six heads at most (spec 63 §4.1).
    A party of the project's kind (`party_presets`: Design, Tech …) or one of the library's mixed (the Game, the Mobile app, the Website)."""
    row = next((p for p in party_presets.listed("code") if p["id"] == preset_id), None)
    p = {"lead": row["leader"], "build": row["build"], "check": row["check"]} if row else next(p for p in library.presets() if p["id"] == preset_id)
    return [p["lead"], *p["build"][:5], *p["check"][:2]][:6]


def members(ids):
    """The heads of these seats as the sheet draws them, the leader first: `races/<race>-<tier>@2x.png`."""
    return [f"races/{roles.RACES[library.get(i).craft]}-{library.get(i).tier}@2x.png" for i in ids]


GAME = seats_of("game")                                                      # the Game's seats: the Game designer, four who do, the Playtester (six heads: more than the sheet shows at once)
DESIGN = seats_of("design")                                                  # Design's: its leader, three who do, one who checks (five heads, all in view with the leader's band at the top)


async def _boxes(locator):
    return await locator.evaluate_all("els => els.map((e) => { const r = e.getBoundingClientRect(); return { left: r.left, top: r.top, width: r.width, height: r.height }; })")


async def _flies(page, n=1):
    await page.wait_for_function("(n) => window.__gather.filter((g) => g.kind === 'fly').length >= n", arg=n, timeout=WAIT_MS)
    return [g for g in await page.evaluate(GATHER) if g["kind"] == "fly"]


def _starts(fly, box):
    """The copy starts where the box was: its left, top and size."""
    return all(abs(fly[k] - box[k]) <= 0.5 for k in ("left", "top", "width", "height"))


async def _seat_heads(sheet, ids):
    """The boxes of the seats' heads, in the order of `ids` (the leader's, the builders', the checkers')."""
    return [(await _boxes(sheet.locator(f'.pseat img[data-agent="{i}"]')))[0] for i in ids]


async def _bring_in(sheet, band, block="center"):
    """The band scrolled to the middle (or the top) of the sheet."""
    await sheet.locator(f'.pband[data-band="{band}"]').evaluate("(e, b) => e.scrollIntoView({ block: b })", block)


async def _ready(page, preset="game", about="A tower game."):
    """New party with a party picked and its words written: the sheet."""
    sheet = await _sheet(page)
    await sheet.locator(f'.preset-tile[data-preset="{preset}"]').click()
    await sheet.get_by_label("What it is for").fill(about)
    return sheet


@pytest.mark.asyncio
async def test_save_party_gathers_the_heads_of_the_party_into_its_deck_and_lights_the_deck_once(fake_repo, monkeypatch):
    hosted(monkeypatch)
    n = len(DESIGN)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        sheet = await _ready(page, "design")
        await _bring_in(sheet, "lead", "start")                                            # the seats are on screen: their heads are where the heads start
        heads = await _seat_heads(sheet, DESIGN)
        assert len(heads) == n == 5
        await page.evaluate("() => { window.__screenAt = 0; }")
        await sheet.get_by_role("button", name="Save party").click()
        flies = await _flies(page, n)
        assert [f["src"] for f in flies] == members(DESIGN)                                # the leader's head first, then the builders', the checker's
        assert all(_starts(f, b) for f, b in zip(flies, heads))                            # each from its head's box in the sheet
        assert [f["delay"] for f in flies] == [f"{35 * i}ms" for i in range(n)] and [f["waits"] for f in flies] == ["0s", "0.035s", "0.07s", "0.105s", "0.14s"]       # 35 ms apart
        assert {f["name"] for f in flies} == {"gather"} and {f["duration"] for f in flies} == {"0.3s"} and {f["timing"] for f in flies} == {"steps(6)"}    # 0.30 s, in steps
        assert all(f["position"] == "fixed" and f["pointer"] == "none" and f["parent"] == "BODY" and int(f["z"]) > 10 for f in flies)                       # over the page (the party's screen too), taking nothing
        assert not any(f["sheet"] for f in flies)                                          # the sheet had closed
        assert {f["s"] for f in flies} == {"0.4"} and {f["deck"]["goal"] for f in flies} == {SAVED}       # to the deck of the party just saved, at 0.4 of their size
        for f in flies:
            assert abs(f["left"] + f["width"] / 2 + float(f["dx"][:-2]) - f["deck"]["cx"]) <= 1.5 and abs(f["top"] + f["height"] / 2 + float(f["dy"][:-2]) - f["deck"]["cy"]) <= 1.5   # ending at the deck's centre
        await page.wait_for_function("() => window.__gather.some((g) => g.kind === 'lit')", timeout=WAIT_MS)
        await page.wait_for_function("() => document.querySelectorAll('.gather-fly').length === 0", timeout=WAIT_MS)       # the copies are gone
        await page.wait_for_timeout(900)
        rec = await page.evaluate(GATHER)
        assert len([g for g in rec if g["kind"] == "gone"]) == n
        lit = [g for g in rec if g["kind"] == "lit"]
        assert [(g["goal"], g["name"], g["duration"], g["timing"]) for g in lit] == [(SAVED, "reward", "0.6s", "steps(4)")]       # the deck lit once, the quiet reward's look
        assert lit[0]["at"] >= flies[-1]["at"] + (n - 1) * 35 + 250                        # when the last has landed
        assert await page.locator(".gather-fly").count() == 0 and await page.locator(".partydeck.is-reward").count() == 0
        await page.locator(".screen").wait_for(timeout=WAIT_MS)                            # the party's own screen opened as it always did,
        assert await page.evaluate("() => window.__screenAt") >= lit[0]["at"] + 500         # once the heads had gathered and the deck's light was seen (it covers the deck)
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_heads_that_are_not_on_screen_start_from_save_party(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        sheet = await _ready(page)
        await sheet.evaluate("e => { e.scrollTop = 0; }")                                 # the seats are under the fold, below the presets
        view = await sheet.bounding_box()
        assert all(b["top"] >= view["y"] + view["height"] for b in await _seat_heads(sheet, GAME))
        save = await sheet.get_by_role("button", name="Save party").bounding_box()
        await sheet.get_by_role("button", name="Save party").click()
        flies = await _flies(page, 6)
        assert [f["src"] for f in flies] == members(GAME)
        for f in flies:                                                                    # all six from the middle of the button, at a head's size
            assert abs(f["left"] + f["width"] / 2 - (save["x"] + save["width"] / 2)) <= 1 and abs(f["top"] + f["height"] / 2 - (save["y"] + save["height"] / 2)) <= 1
            assert (f["width"], f["height"]) == (24, 22)


@pytest.mark.asyncio
async def test_the_seats_on_screen_are_where_the_heads_start_and_the_others_start_from_save_party(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        sheet = await _ready(page, "design")
        await sheet.evaluate("e => { e.scrollTop = 0; }")
        floor = (await sheet.locator(".sheet-foot").bounding_box())["y"]
        builder = (await _seat_heads(sheet, DESIGN[3:4]))[0]                                # the last who does
        await sheet.evaluate("(e, y) => { e.scrollTop = y; }", max(0, builder["top"] + builder["height"] - floor + 1))      # scrolled so that the checker's seat is under the foot, the others above it
        leader, *builders, checker = await _seat_heads(sheet, DESIGN)
        assert leader["top"] + leader["height"] <= floor and all(b["top"] + b["height"] <= floor for b in builders) and checker["top"] + checker["height"] > floor
        save = await sheet.get_by_role("button", name="Save party").bounding_box()
        await sheet.get_by_role("button", name="Save party").click()
        flies = await _flies(page, len(DESIGN))
        assert [f["src"] for f in flies] == members(DESIGN)
        assert all(_starts(f, b) for f, b in zip(flies, [leader, *builders]))              # the leader and the builders from their seats
        assert abs(flies[-1]["left"] + flies[-1]["width"] / 2 - (save["x"] + save["width"] / 2)) <= 1 and abs(flies[-1]["top"] + flies[-1]["height"] / 2 - (save["y"] + save["height"] / 2)) <= 1   # the checker, under the foot, from the button


@pytest.mark.asyncio
async def test_a_craft_s_party_gathers_from_its_seats_the_leader_first(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):                # a host with no library of mixed parties: the crafts' parties
        sheet = await _sheet(page)
        await sheet.locator('.preset-tile[data-preset="design"]').click()
        await sheet.get_by_label("What it is for").fill("A design party.")
        ids = DESIGN                                                                       # the party of the craft: its leader, its squad
        await _bring_in(sheet, "lead", "start")
        heads = await _seat_heads(sheet, ids)
        await sheet.get_by_role("button", name="Save party").click()
        flies = await _flies(page, len(ids))
        assert [f["src"] for f in flies] == members(ids)
        assert all(_starts(f, b) for f, b in zip(flies, heads))


@pytest.mark.asyncio
async def test_a_party_of_your_own_gathers_from_the_seats_it_fills(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        stub.own = [{"id": "p-1a2b3c4d", "name": "Lean web", "craft": "engineering", "leader": "architect", "team": ["grunt", "tester", "reviewer"], "every": ["reviewer"],
                     "own": [], "goals": 3, "projects": 2, "met": 2, "saved": "2026-10-20T10:00:00"}]
        sheet = await _sheet(page)
        chip = sheet.locator("[data-party=p-1a2b3c4d]")
        await chip.wait_for(timeout=WAIT_MS)
        await chip.get_by_role("button", name="Pick your party “Lean web”").click()
        await sheet.get_by_label("What it is for").fill("A lean one.")
        chips = await _boxes(chip.locator(".own-heads img"))
        assert len(chips) == 4 and {(round(b["width"]), round(b["height"])) for b in chips} == {(24, 22)}               # a chip's heads are a head's own size, never between (decisions §161.3)
        await _bring_in(sheet, "lead", "start")
        heads = await _seat_heads(sheet, ["architect", "grunt", "tester", "reviewer"])                                 # the seats it fills are where the heads start
        await sheet.get_by_role("button", name="Save party").click()
        flies = await _flies(page, 4)
        assert all(_starts(f, b) for f, b in zip(flies, heads)) and flies[0]["src"] == "races/peon-elder@2x.png"      # the Architect leads


@pytest.mark.asyncio
async def test_under_reduced_motion_nothing_gathers(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        await page.emulate_media(reduced_motion="reduce")
        sheet = await _ready(page)
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save", {"about": "A tower game.", "craft": "design", "leader": "game-designer", "priority": "normal", "preset": "game",
                                                       "team": GAME[1:], "every": []})
        await page.locator(".screen").wait_for(timeout=WAIT_MS)
        await page.wait_for_timeout(900)
        assert await page.evaluate(GATHER) == [] and await page.locator(".gather-fly").count() == 0


@pytest.mark.asyncio
async def test_a_refused_save_gathers_nothing_and_leaves_the_sheet_as_it_was(fake_repo, monkeypatch):
    hosted(monkeypatch)
    real = Stub.commands

    def commands(self):
        def refuse(a):
            self.calls.append(("ideas.goal_save", {k: v for k, v in a.items() if k not in ("link", "device")}))
            return {"error": "The party was not saved."}
        return {**real(self), "ideas.goal_save": refuse}
    monkeypatch.setattr(Stub, "commands", commands)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        sheet = await _ready(page)
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        await page.wait_for_timeout(900)
        assert await sheet.is_visible() and await sheet.get_by_role("button", name="Save party").is_enabled() and await page.evaluate(GATHER) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("after,plays", [(1.0, True), (6.4, False)])
async def test_the_gather_waits_six_seconds_for_the_deck_to_show_the_party(fake_repo, monkeypatch, after, plays):
    """The host answers the slug but the Board has no such party yet, so the deck shows another one; the person picks the new party `after` seconds later: a gather that waited 6 s is dropped."""
    hosted(monkeypatch)
    real = Stub.commands

    def commands(self):
        got = real(self)

        def board_map(a):                                                                  # the party is saved, the Board's Map does not have it yet
            out = got["ideas.map"](a)
            return {**out, "goals": [g for g in out["goals"] if g["slug"] != "a-late-party" or getattr(self, "late", False)]}
        return {**got, "ideas.map": board_map}
    monkeypatch.setattr(Stub, "commands", commands)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        sheet = await _ready(page, about="A late party.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        await page.locator(".screen").wait_for(timeout=WAIT_MS)
        assert await page.evaluate(GATHER) == [] and await page.locator(".partydeck").get_attribute("data-goal") != "a-late-party"          # the deck shows another party: nothing yet
        await page.wait_for_timeout(int(after * 1000))
        stub.late = True
        stub.bump({})
        await page.locator(".screen-head").get_by_role("button", name="Back").click()
        await _pick_goal(page, "a-late-party")                                              # the first draw that shows it
        await page.wait_for_timeout(1200)
        rec = await page.evaluate(GATHER)
        flies = [g for g in rec if g["kind"] == "fly"]
        if plays:
            assert len(flies) == len(GAME) and [g["goal"] for g in rec if g["kind"] == "lit"] == ["a-late-party"]
        else:
            assert rec == []


@pytest.mark.asyncio
async def test_a_party_made_from_new_goal_gathers_nothing_the_form_is_what_the_person_looks_at(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        await page.locator(FAB).click()                                                    # no party yet: New party opens first, New goal after it
        sheet = page.get_by_role("dialog", name="New party")
        await sheet.wait_for(timeout=WAIT_MS)
        await sheet.locator('.preset-tile[data-preset="game"]').click()
        await sheet.get_by_label("What it is for").fill("A tower game.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save", {"about": "A tower game.", "craft": "design", "leader": "game-designer", "priority": "normal", "preset": "game",
                                                       "team": GAME[1:], "every": []})
        form = page.get_by_role("dialog", name="New goal")
        await form.wait_for(timeout=WAIT_MS)                                               # New goal opens for the party just made
        await page.wait_for_timeout(900)
        assert await page.evaluate(GATHER) == [] and await page.locator(".gather-fly").count() == 0


@pytest.mark.asyncio
async def test_a_team_changed_from_the_partys_own_screen_gathers_nothing(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch, init=RECORD) as (stub, page):
        for a in (library.get("product-designer"), library.get("ui-kit"), library.get("accessibility-reviewer")):
            stub.roles[a.id] = {"slug": a.id, "name": a.name, "model": a.tier, "max_parallel": 2, "instruction": a.instruction, "builtin": False,
                                "craft": a.craft, "head": {"craft": a.craft, "race": "elf", "tier": a.tier}}
        stub.goals["land"] = stub.goal("land", "Landing page", "high", "ready", craft="design", race="elf", about="A landing page.",
                                       team=["ui-kit", "accessibility-reviewer"], every=[], leader=stub.leader("product-designer"))
        stub.bump({})
        await _pick_goal(page, "land")
        await _open_party(page, "Landing page")
        await page.locator(".screen").get_by_role("region", name="The party", exact=True).get_by_role("button", name="Change the party").click()
        sheet = page.get_by_role("dialog", name="The party")
        await sheet.locator('.party [data-change="team"]').click()
        await sheet.get_by_role("button", name="Take in: Analyst").click()
        await sheet.get_by_role("region", name="Builds").get_by_role("button", name="Done").click()
        await sheet.get_by_role("button", name="Save the party").click()
        assert await _called(stub, "ideas.goal_save", {"slug": "land", "team": ["ui-kit", "accessibility-reviewer"], "every": [], "leader": "analyst"})
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)
        await page.wait_for_timeout(900)
        assert await page.evaluate(GATHER) == []


def test_the_service_worker_is_one_version_up():
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")).group(1)) >= 86
