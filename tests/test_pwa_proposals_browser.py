"""Spec 75 part C, the phone (docs/specs/75-parties-fitted-to-the-project.md §5, §6 "C"; decisions §90), in the sheet of spec 91 §7: Chromium at 390 × 844 against the stub host of spec 75 §4.1 — `ideas.proposals`,
`ideas.map`'s `project.kind`, `ideas.goal_save` with `size`, a party's `size` — and `ideas.party_presets` for the project's kind. The Orkmaster's reading of the project fits New party's presets (the stages of a mobile app),
Standard is picked of the three-way switch Lean · Standard · Full (a radiogroup of buttons) that changes the seats, the agents and the price at once, *Save party* sends the leader, the team, the size and the stage's recipe;
an empty project is asked no line here (the Orkmaster's row asks it, spec 91 §8); the deal shows the proposals first with Standard's price and a press opens New party on its seats; *About this party* and *Edit the party* have
*Its size*; the drawer's Target is *A party with no size of its own works as*; a host with no `ideas.proposals` keeps today's phone; 44 px targets, no sideways scroll; the service worker's version."""
from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from orkboard.realm import library, party_presets
from tests.test_pwa_arena_browser import SCENE, _about, _redrawn, _scene, _shot_to  # noqa: F401
from tests.test_pwa_project_browser import ORKMASTER, STATE, _project, calls, hosted  # noqa: F401
from tests.test_pwa_route_browser import WORLD, norm, world  # noqa: F401
from tests.test_pwa_shell_browser import FAB, NO_SCROLL, WAIT_MS, Stub, _called, _menu, _new_goal, _phone, _pick_goal  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

PM, ARCH = "product-manager", "architect"
LICH, PEON = {"race": "lich", "tier": "elder"}, {"race": "peon", "tier": "elder"}
GRUNT, TESTER = {"race": "peon", "tier": "warrior"}, {"race": "peon", "tier": "laborer"}
ARTIST = {"race": "elf", "tier": "warrior"}


def a_size(leader, team, heads, target, low, high):
    return {"leader": leader, "team": team, "agents": 1 + len(team), "target": target, "price": {"low": low, "high": high}, "heads": heads}


def a_proposal(pid, name, line, why, leader, heads, prices, have=False, team=("grunt", "tester", "reviewer")):
    """A proposal as spec 75 §4.1 says it: Lean the leader alone, Standard the leader, two builders and a checker, Full every seat."""
    lean, std, full = prices
    return {"id": pid, "name": name, "line": line, "why": why, "have": have,
            "sizes": {"lean": a_size(leader, [], heads[:1], "thrift", *lean),
                      "standard": a_size(leader, list(team[:3]), heads[:4], "balance", *std),
                      "full": a_size(leader, list(team) + ["artist", "ui-kit"], heads[:6], "quality", *full)}}


KIND = {"id": "mobile", "words": "a mobile app", "signs": ["ios/", "android/"]}
MOBILE = [
    a_proposal("mobile-features", "Mobile app: features", "Screens and what people do on them", "ios/ and android/ are here", PM, [LICH, GRUNT, ARTIST, TESTER, GRUNT, TESTER],
               ((0.4, 1.2), (1.4, 4.1), (3.0, 9.0))),
    a_proposal("mobile-architecture", "Mobile app: architecture", "How the app is built, and kept honest", "A mobile app needs its structure kept", ARCH, [PEON, GRUNT, TESTER, PEON, GRUNT, TESTER],
               ((0.5, 1.5), (1.8, 5.0), (4.0, 11.0))),
    a_proposal("release", "Release", "A version out: what is new, the build, the stores' list", "You have one", "release-manager", [PEON, GRUNT, TESTER, PEON],
               ((0.3, 0.9), (1.0, 3.0), (2.0, 6.0)), have=True),
]
EMPTY_KIND = {"id": "empty", "words": "an empty folder", "signs": []}
IDEATION = a_proposal("ideation", "Ideation", "Pitches judged from four sides", "Every project starts with ideas", "ideation-lead", [LICH, ARTIST, GRUNT, TESTER], ((0.2, 0.6), (0.6, 1.8), (1.2, 3.6)))
WIKI = [a_proposal("wiki", "Wiki", "Pages that say how the team works", "a team's wiki", PM, [LICH, GRUNT, ARTIST, TESTER], ((0.3, 0.9), (1.0, 3.0), (2.0, 6.0))), IDEATION]


def proposing(monkeypatch, *, kind=KIND, proposals=MOBILE, ask=False, deal="have", answer=None, fail=False, refuse=""):
    """The route world with spec 70's host and spec 75's: `project.kind`, `ideas.proposals` (with `about`, `answer(about)` says the proposals read from the line) and `ideas.goal_save` keeping `size`."""
    hosted(monkeypatch, deal=deal)
    if kind:                                                  # a host older than spec 75 says no `kind`
        SCENE["map"]["project"]["kind"] = copy.deepcopy(kind)
        SCENE["map"]["project"]["deal"] = [{"id": p["id"], "why": "proposal", "n": 0} for p in proposals] + SCENE["map"]["project"]["deal"]     # the proposals' ids first: not all are presets
    real = Stub.commands

    def commands(self):
        got = real(self)

        def presets_(a):                                      # spec 91 §7: New party's presets for the project's kind
            self.calls.append(("ideas.party_presets", {k: v for k, v in a.items() if k not in ("link", "device")}))
            return {"kind": {"id": kind["id"], "words": kind["words"]}, "presets": party_presets.listed(kind["id"])}

        def proposals_(a):
            self.calls.append(("ideas.proposals", {k: v for k, v in a.items() if k not in ("link", "device")}))
            if fail:
                return {"error": "No command ideas.proposals"}
            if a.get("about") and answer:
                return answer(a["about"])
            return {"kind": copy.deepcopy(kind), "ask": ask, "proposals": copy.deepcopy(proposals)}

        def goal_save(a):
            if refuse:
                self.calls.append(("ideas.goal_save", {k: v for k, v in a.items() if k not in ("link", "device")}))
                return {"error": refuse}
            r = got["ideas.goal_save"](a)
            if a.get("size") and r.get("slug") in self.goals:
                self.goals[r["slug"]]["size"] = a["size"]
            for g in SCENE["map"]["goals"]:
                if g["slug"] == a.get("slug") and a.get("size"):
                    g["size"] = a["size"]
            return r
        return {**got, "ideas.proposals": proposals_, "ideas.goal_save": goal_save, **({"ideas.party_presets": presets_} if kind else {})}
    monkeypatch.setattr(Stub, "commands", commands)


async def _new_party(page):
    """New party, its presets and its seats drawn."""
    await _new_goal(page)
    sheet = page.get_by_role("dialog", name="New party")
    await sheet.wait_for(timeout=WAIT_MS)
    await sheet.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
    await sheet.locator(".pseat[data-seat]").first.wait_for(timeout=WAIT_MS)
    return sheet


async def _seats(sheet, band):
    return [await s.get_attribute("data-seat") for s in await sheet.locator(f'.pband[data-band="{band}"] .pseat[data-seat]').all()]


# -- New party opens on the project's presets --------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_party_opens_on_the_projects_presets_with_a_three_way_switch_and_the_size_picked_says_its_agents_and_seats(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        assert norm(await sheet.locator(".presets__kind").inner_text()) == "For a mobile app: the Orkmaster knows what this project is"      # what the Orkmaster read
        assert [await c.get_attribute("data-preset") for c in await sheet.locator(".preset-group.is-stage .preset-tile").all()] == ["ideation", "mobile-concept", "mobile-build", "release", "mobile-liveops"]
        assert await sheet.locator(".prop, .props__top").count() == 0 and calls(stub, "ideas.proposals") == []                                  # no proposals here: they are the deal's
        group = sheet.get_by_role("radiogroup", name="Size")
        assert [norm(await b.inner_text()) for b in await group.get_by_role("radio").all()] == ["Lean", "Standard", "Full"]
        assert await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"                           # Standard picked
        assert await group.locator("button.ork-btn").count() == 3                                                                   # orkUI's buttons
        assert (await _seats(sheet, "lead"), await _seats(sheet, "build"), await _seats(sheet, "check")) == (["product-manager"], ["grunt"], [])
        assert norm(await sheet.locator(".size-says").inner_text()).startswith("2 agents: the leader Veteran, the rest Seasoned")
        await group.get_by_role("radio", name="Lean").click()
        assert await _seats(sheet, "build") == [] and norm(await sheet.locator(".size-says").inner_text()).startswith("One agent, Seasoned · works as thrift")
        assert await group.get_by_role("radio", name="Lean").get_attribute("aria-checked") == "true" and await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "false"
        await group.get_by_role("radio", name="Full").click()
        assert (await _seats(sheet, "build"), await _seats(sheet, "check")) == (["grunt"], ["reviewer"]) and norm(await sheet.locator(".size-says").inner_text()).startswith("3 agents, Seasoned and up · works as quality")
        await page.wait_for_function("() => document.querySelector('.party-price')?.textContent.includes('$')", timeout=WAIT_MS)
        for _ in range(60):                                                                                                         # asked 300 ms after the pick
            if calls(stub, "ideas.party_price")[-1].get("size") == "full":
                break
            await page.wait_for_timeout(100)
        assert calls(stub, "ideas.party_price")[-1]["size"] == "full"                                                               # the price reads the size's Target
        await group.get_by_role("radio", name="Full").focus()
        await page.keyboard.press("ArrowLeft")                                                                                      # arrows move the pick
        assert await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
        assert not calls(stub, "ideas.goal_save")
        await _shot_to(page, "phone-proposals")
        assert await page.evaluate(NO_SCROLL) and await sheet.evaluate("(d) => d.scrollWidth <= d.clientWidth")
        assert "null" not in await sheet.inner_text() and "undefined" not in await sheet.inner_text()


@pytest.mark.asyncio
async def test_save_party_saves_the_party_with_its_leader_its_team_and_size_and_the_words_are_the_persons(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.locator('.preset-tile[data-preset="mobile-concept"]').click()
        await sheet.get_by_role("radiogroup", name="Size").get_by_role("radio", name="Full").click()
        await sheet.get_by_label("What it is for").fill("How the app looks before it is built.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["about"] == "How the app looks before it is built." and sent["leader"] == "product-designer" and sent["size"] == "full" and sent["proposal"] == "mobile-concept"
        assert sent["team"][0] == "ui-kit" and "title" not in sent and sent["priority"] == "normal"                               # the person's words, not the stage's name
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_save_party_opens_the_party_and_a_lean_party_is_its_leader_alone(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.get_by_role("radiogroup", name="Size").get_by_role("radio", name="Lean").click()
        await sheet.get_by_label("What it is for").fill("The first build.")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["about"] == "The first build." and sent["size"] == "lean" and sent["team"] == [] and sent["proposal"] == "mobile-build" and "title" not in sent
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)
        screen = page.locator("section.screen:not([hidden])")                                                                        # the party's own screen opens
        await screen.wait_for(timeout=WAIT_MS * 2)


@pytest.mark.asyncio
async def test_a_refusal_of_the_host_is_said_and_the_sheet_stays_to_be_saved_again(fake_repo, monkeypatch):
    proposing(monkeypatch, refuse="Reviewer has work open: it cannot leave")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        save = sheet.get_by_role("button", name="Save party")
        await sheet.get_by_role("radiogroup", name="Size").get_by_role("radio", name="Full").click()
        await save.click()
        await page.get_by_text("Reviewer has work open: it cannot leave").wait_for(timeout=WAIT_MS)
        assert await sheet.is_visible() and await save.is_enabled() and await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_every_target_of_new_party_is_44_px_and_the_page_does_not_scroll_sideways(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        boxes = await sheet.locator(".size-pick, .preset-tile, .pseat__x, .pseat.is-empty, .ork-btn.primary").evaluate_all("(els) => els.map((e) => { const r = e.getBoundingClientRect(); return [r.width, r.height, r.left, r.right]; })")
        assert len(boxes) == 3 + 12 + 2 + 1 + 1                                                                                    # three sizes, the twelve tiles, × of two seats, a free seat, Save party
        assert all(round(w) >= 44 and round(h) >= 44 and left >= 0 and right <= 390 for w, h, left, right in boxes)
        assert await page.evaluate(NO_SCROLL)


# -- an empty folder: the Orkmaster's row asks, not New party ---------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_an_empty_project_has_ideations_stage_and_the_stages_of_code_and_asks_no_line_here(fake_repo, monkeypatch):
    proposing(monkeypatch, kind=EMPTY_KIND, proposals=[IDEATION], ask=True)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        assert norm(await sheet.locator(".presets__kind").inner_text()) == "For an empty folder: the Orkmaster knows what this project is"
        assert [await c.get_attribute("data-preset") for c in await sheet.locator(".preset-group.is-stage .preset-tile").all()] == ["ideation", "code-concept", "code-build", "release", "code-liveops"]
        assert await sheet.get_by_label("What is this project for?").count() == 0 and not [c for c in calls(stub, "ideas.proposals") if c.get("about")]      # no line is asked of the person here
        await _shot_to(page, "phone-proposals-empty")
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_host_that_cannot_say_what_the_project_is_keeps_the_librarys_stages_and_crafts(fake_repo, monkeypatch):
    proposing(monkeypatch, kind=None)                                                                                                 # no `ideas.party_presets` of the kind: the library's presets
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        crafts = sheet.locator(".preset-group.is-craft .preset-tile")
        assert [await t.get_attribute("data-preset") for t in await crafts.all()][:5] == ["engineering", "design", "data", "marketing", "product"]
        assert await sheet.locator(".prop").count() == 0


# -- a preset pressed keeps what the person chose -----------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_stage_pressed_keeps_the_size_picked_and_the_words_typed(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        group = sheet.get_by_role("radiogroup", name="Size")
        await group.get_by_role("radio", name="Full").click()
        await sheet.get_by_label("What it is for").fill("A party of my own")                                                         # typed before the press
        await sheet.locator('.preset-tile[data-preset="release"]').click()
        assert await group.get_by_role("radio", name="Full").get_attribute("aria-checked") == "true" and await sheet.get_by_label("What it is for").input_value() == "A party of my own"
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["size"] == "full" and sent["about"] == "A party of my own" and sent["leader"] == "release-manager"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_preset_pressed_asks_no_second_question(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.get_by_label("What it is for").fill("a party of my own")
        await sheet.locator('.preset-tile[data-preset="mobile-liveops"]').click()
        await sheet.locator('.preset-tile[data-preset="mobile-liveops"][aria-pressed="true"]').wait_for(timeout=WAIT_MS)
        assert await sheet.get_by_label("What it is for").input_value() == "a party of my own" and await sheet.get_by_role("button", name="Save party").is_enabled()
        assert not calls(stub, "ideas.goal_save")


# -- the deal ---------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_deal_shows_the_proposals_first_with_standards_price_and_a_press_opens_new_party_on_its_seats(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        await project.get_by_role("button", name="New party").click()
        deal = project.locator(".pj-deal")
        await deal.locator('.pj-tile[data-proposal]').first.wait_for(timeout=WAIT_MS)
        tiles = await deal.locator(".pj-tile").all()
        ids = [await t.get_attribute("data-proposal") for t in tiles]
        assert ids[:3] == ["mobile-features", "mobile-architecture", "release"] and ids[3] is None                                    # the proposals first, the library's tiles after
        first = norm(await tiles[0].inner_text())
        assert "Mobile app: features" in first and "≈$1–4 a goal" in first and "ios/ and android/ are here" in first
        assert "You have one" in norm(await tiles[2].inner_text()) and "is-have" in await tiles[2].get_attribute("class")
        await _shot_to(page, "phone-proposals-deal")
        await tiles[1].click()
        sheet = page.get_by_role("dialog", name="New party")
        await sheet.locator(".pseat[data-seat]").first.wait_for(timeout=WAIT_MS)
        assert await _seats(sheet, "lead") == [ARCH] and await sheet.get_by_label("Name", exact=True).get_attribute("placeholder") == "Mobile app: architecture"      # New party on that proposal's seats
        assert await page.evaluate(NO_SCROLL)


# -- a party's size ---------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_about_this_party_has_its_size_with_each_sizes_price_a_press_saves_it_and_a_party_with_none_says_what_it_works_as(fake_repo, monkeypatch):
    proposing(monkeypatch)
    SCENE["map"]["goals"][0]["leader"] = {"slug": ARCH, "name": "Architect", "head": {"craft": "engineering", "race": "peon", "tier": "elder"}}
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        about = await _about(page)
        size = about.locator('[data-sec="Its size"]')
        await size.wait_for(timeout=WAIT_MS)
        group = size.get_by_role("radiogroup", name="Its size")
        await group.get_by_role("radio", name="Full").wait_for(timeout=WAIT_MS)
        assert [await b.get_attribute("aria-checked") for b in await group.get_by_role("radio").all()] == ["false"] * 3                 # none picked: a party made before
        assert "A party with no size of its own works as Balance" in await size.inner_text()
        assert await group.get_by_role("radio", name="Lean").inner_text() == "Lean\n≈$0.50–1.50" and "≈$4–11" in await group.get_by_role("radio", name="Full").inner_text()
        await _shot_to(page, "phone-size")
        await group.get_by_role("radio", name="Full").click()
        assert await _called(stub, "ideas.goal_save", {"slug": "passkey", "size": "full"})
        await page.wait_for_function("() => document.querySelector('dialog[aria-label=\"About this party\"] .size-pick[data-size=\"full\"]')?.getAttribute('aria-checked') === 'true'")
        await page.wait_for_function("() => !document.querySelector('dialog[aria-label=\"About this party\"] [data-sec=\"no-size\"]')")
        assert "A party with no size of its own" not in await size.inner_text()
        for b in await group.get_by_role("radio").all():
            assert (await b.bounding_box())["height"] >= 44
        assert await page.evaluate(NO_SCROLL)


async def _edit(page):
    about = await _about(page)
    await about.get_by_role("button", name="Edit the party").click()
    edit = page.get_by_role("dialog", name="Edit the party")
    await edit.wait_for(timeout=WAIT_MS)
    return edit


@pytest.mark.asyncio
async def test_edit_the_party_has_its_size_and_sends_nothing_of_it_when_it_was_not_changed(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        edit = await _edit(page)
        assert await edit.get_by_role("radiogroup", name="Its size").is_visible()
        await edit.get_by_label("What it is for").fill("Passkeys, edited")
        await edit.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        assert "size" not in calls(stub, "ideas.goal_save")[-1]


@pytest.mark.asyncio
async def test_edit_the_party_sends_the_size_it_was_changed_to(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        edit = await _edit(page)
        await edit.get_by_role("radiogroup", name="Its size").get_by_role("radio", name="Lean").click()
        await edit.get_by_label("What it is for").fill("Passkeys, edited again")
        await edit.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["size"] == "lean" and sent["slug"] == "passkey" and sent["about"] == "Passkeys, edited again", sent


# -- the Target ---------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_drawers_target_is_what_a_party_with_no_size_of_its_own_works_as(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        drawer = await _menu(page)
        group = drawer.get_by_role("radiogroup", name="A party with no size of its own works as")
        await group.wait_for(timeout=WAIT_MS)
        assert "a party with no size of its own works as" in (await drawer.locator(".target-picks").inner_text()).lower() and await drawer.get_by_role("radiogroup", name="Target").count() == 0
        assert [await p.inner_text() for p in await group.locator("label.pill").all()] == ["Thrift", "Balance", "Quality"]
        assert await group.get_by_role("radio", name="Balance").is_checked()
        await group.get_by_role("radio", name="Quality").click()
        assert await _called(stub, "ideas.board_set", {"target": "quality"})
        assert await page.evaluate(NO_SCROLL)


# -- an older host --------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_host_with_no_proposals_keeps_todays_phone(fake_repo, monkeypatch):
    proposing(monkeypatch, kind=None)                                                                                                 # its Map's project says no kind
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        assert await sheet.locator(".prop, .props").count() == 0 and await sheet.get_by_role("button", name="Save party").is_visible()
        assert await sheet.locator(".preset-tile").count() > 0 and await sheet.get_by_role("radiogroup", name="Its size").count() == 0
        assert calls(stub, "ideas.proposals") == []
        await sheet.get_by_label("What it is for").fill("Plain")
        await sheet.get_by_role("button", name="Save party").click()
        assert await _called(stub, "ideas.goal_save")
        assert "size" not in calls(stub, "ideas.goal_save")[-1]


@pytest.mark.asyncio
async def test_a_host_with_no_proposals_keeps_todays_target_and_deal(fake_repo, monkeypatch):
    proposing(monkeypatch, kind=None)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        drawer = await _menu(page)
        assert await drawer.get_by_role("radiogroup", name="Target").count() == 1 and "no size of its own" not in await drawer.inner_text()
        await page.keyboard.press("Escape")
        project = await _project(page)
        await project.get_by_role("button", name="New party").click()
        await project.locator(".pj-tile").first.wait_for(timeout=WAIT_MS)
        assert await project.locator(".pj-tile[data-proposal]").count() == 0 and calls(stub, "ideas.proposals") == []


@pytest.mark.asyncio
async def test_a_host_that_cannot_answer_proposals_leaves_new_party_as_it_was_without_a_toast(fake_repo, monkeypatch):
    proposing(monkeypatch, fail=True)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
        assert await sheet.get_by_role("button", name="Save party").is_visible() and await sheet.locator(".prop").count() == 0
        assert await page.locator(".toast, [role=status]:has-text('No command')").count() == 0


def test_the_service_worker_keeps_the_proposals_and_is_one_version_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert int(re.search(r'const CACHE = "orkcraft-app-v(\d+)";', sw).group(1)) >= 86 and '"shell-proposals.js"' in sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
    assert library.get(PM) is not None
