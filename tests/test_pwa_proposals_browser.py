"""Spec 75 part C, the phone (docs/specs/75-parties-fitted-to-the-project.md §5, §6 "C"; decisions §90): Chromium at 390 × 844 against the stub host of spec 75 §4.1 — `ideas.proposals`, `ideas.map`'s `project.kind`,
`ideas.goal_save` with `size`, a party's `size`. New party opens on the Orkmaster's proposals for a mobile project (three cards, a three-way switch Lean · Standard · Full as a radiogroup of buttons, the heads, the agents and the
price of the size picked, *Make it* sends the leader, the team and the size, a proposal the project has is muted); an empty project asks *What is this project for?* and *Read it* draws the proposals of the line; *More: the library* is
today's tiles and seats with the size switch; the deal shows the proposals first with Standard's price; *About this party* and *Edit the party* have *Its size*; the drawer's Target is *A party with no size of its own works as*;
a host with no `ideas.proposals` keeps today's phone; 44 px targets, no sideways scroll; the service worker's version."""
from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest

from orkboard.gui import pwa
from orkboard.realm import library
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
        return {**got, "ideas.proposals": proposals_, "ideas.goal_save": goal_save}
    monkeypatch.setattr(Stub, "commands", commands)


async def _new_party(page):
    await _new_goal(page)
    sheet = page.get_by_role("dialog", name="New party")
    await sheet.wait_for(timeout=WAIT_MS)
    await sheet.locator(".prop, .props__ask, .preset-list").first.wait_for(timeout=WAIT_MS)
    return sheet


def card_of(sheet, pid):
    return sheet.locator(f'.prop[data-proposal="{pid}"]')


# -- New party opens on the proposals ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_party_opens_on_three_proposals_with_a_three_way_switch_and_the_size_picked_says_its_heads_agents_and_price(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        top = sheet.locator(".props__top")
        assert norm(await top.inner_text()) == "Orkmaster proposes for this project · a mobile app ios/ · android/"
        assert await top.locator("img.ork-race__head").get_attribute("src") == "races/peon-elder.png"                          # the Orkmaster's head
        assert [await c.get_attribute("data-proposal") for c in await sheet.locator(".prop").all()] == ["mobile-features", "mobile-architecture", "release"]
        assert await sheet.get_by_role("button", name="Save party").is_hidden() and await sheet.locator(".preset-tile").count() == 0       # no library at first
        card = card_of(sheet, "mobile-features")
        text = norm(await card.inner_text())
        assert text.startswith("Mobile app: features Screens and what people do on them ios/ and android/ are here Lean Standard Full")
        group = card.get_by_role("radiogroup", name="Its size: Mobile app: features")
        assert [norm(await b.inner_text()) for b in await group.get_by_role("radio").all()] == ["Lean", "Standard", "Full"]
        assert await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"                           # Standard picked
        assert await group.locator("button.ork-btn").count() == 3                                                                   # orkUI's buttons
        assert await card.locator(".prop__heads img").count() == 4 and "4 agents" in text and "≈$1–4 a goal" in text
        await group.get_by_role("radio", name="Lean").click()
        text = norm(await card.inner_text())
        assert await card.locator(".prop__heads img").count() == 1 and "one agent" in text and "≈$0.40–1.20 a goal" in text
        assert await group.get_by_role("radio", name="Lean").get_attribute("aria-checked") == "true" and await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "false"
        await group.get_by_role("radio", name="Full").click()
        text = norm(await card.inner_text())
        assert await card.locator(".prop__heads img").count() == 6 and "6 agents" in text and "≈$3–9 a goal" in text
        assert await card.locator(".prop__heads img").first.get_attribute("src") == "races/lich-elder.png"                           # the leader's head first
        other = card_of(sheet, "mobile-architecture")
        assert await other.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true" and "≈$2–5 a goal" in norm(await other.inner_text())   # each card keeps its own size
        await group.get_by_role("radio", name="Standard").click()
        await group.get_by_role("radio", name="Standard").focus()
        await page.keyboard.press("ArrowRight")                                                                                     # arrows move the pick
        assert await group.get_by_role("radio", name="Full").get_attribute("aria-checked") == "true"
        have = card_of(sheet, "release")
        assert "You have one" in await have.inner_text() and "is-have" in await have.get_attribute("class")                          # muted
        assert not calls(stub, "ideas.goal_save") and len(calls(stub, "ideas.proposals")) == 1 and calls(stub, "ideas.proposals")[0] == {}
        await _shot_to(page, "phone-proposals")
        assert await page.evaluate(NO_SCROLL) and await sheet.evaluate("(d) => d.scrollWidth <= d.clientWidth")
        assert "null" not in await sheet.inner_text() and "undefined" not in await sheet.inner_text()


@pytest.mark.asyncio
async def test_make_it_saves_the_party_with_its_leader_its_team_and_size_and_the_words_are_the_persons_else_the_proposals_line(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        card = card_of(sheet, "mobile-features")
        await card.get_by_role("radio", name="Full").click()
        await card.get_by_role("button", name="Make it: Mobile app: features").click()
        assert await _called(stub, "ideas.goal_save", {"about": "Mobile app: features: Screens and what people do on them", "craft": "product", "leader": PM,
                                                       "team": ["grunt", "tester", "reviewer", "artist", "ui-kit"], "every": [], "priority": "normal", "size": "full", "proposal": "mobile-features"})
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_make_it_sends_the_proposals_own_words_and_opens_the_party(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        assert await sheet.get_by_label("What it is for").count() == 0                          # one question at most: the Orkmaster's, for an empty folder
        await card_of(sheet, "mobile-architecture").get_by_role("radio", name="Lean").click()
        await card_of(sheet, "mobile-architecture").get_by_role("button", name="Make it: Mobile app: architecture").click()
        assert await _called(stub, "ideas.goal_save", {"about": "Mobile app: architecture: How the app is built, and kept honest", "craft": "engineering", "leader": ARCH, "team": [], "every": [], "priority": "normal", "size": "lean", "proposal": "mobile-architecture"})
        await sheet.wait_for(state="hidden", timeout=WAIT_MS)
        screen = page.locator("section.screen:not([hidden])")                                                                        # the party's own screen opens, as after Save party
        await screen.wait_for(timeout=WAIT_MS * 2)


@pytest.mark.asyncio
async def test_a_refusal_of_the_host_is_said_and_the_card_stays_to_be_pressed_again(fake_repo, monkeypatch):
    proposing(monkeypatch, refuse="Reviewer has work open: it cannot leave")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        make = card_of(sheet, "mobile-features").get_by_role("button", name="Make it: Mobile app: features")
        await make.click()
        await page.get_by_text("Reviewer has work open: it cannot leave").wait_for(timeout=WAIT_MS)
        assert await sheet.is_visible() and await make.is_enabled() and await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_every_target_of_the_proposals_is_44_px_and_the_page_does_not_scroll_sideways(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        boxes = await sheet.locator(".size-pick, [data-act='make-it'], [data-act='more-library']").evaluate_all("(els) => els.map((e) => { const r = e.getBoundingClientRect(); return [r.width, r.height, r.left, r.right]; })")
        assert len(boxes) == 3 * 3 + 3 + 1
        assert all(round(w) >= 44 and round(h) >= 44 and left >= 0 and right <= 390 for w, h, left, right in boxes)
        assert await page.evaluate(NO_SCROLL)


# -- an empty folder asks one line ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_an_empty_project_asks_what_it_is_for_and_read_it_draws_the_proposals_of_the_line_with_ideation_beside_it_at_once(fake_repo, monkeypatch):
    def answer(about):
        return {"kind": {"id": "wiki", "words": "a team's wiki", "signs": []}, "ask": False, "read": True, "proposals": copy.deepcopy(WIKI)}
    proposing(monkeypatch, kind=EMPTY_KIND, proposals=[IDEATION], ask=True, answer=answer)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        assert norm(await sheet.locator(".props__top").inner_text()) == "Orkmaster proposes for this project · an empty folder"
        assert [await c.get_attribute("data-proposal") for c in await sheet.locator(".prop").all()] == ["ideation"]               # Ideation at once
        ask = sheet.locator(".props__ask")
        assert "what is this project for?" in (await ask.inner_text()).lower() and "a line is enough: a mobile app for…, our team's wiki, my design files" in await ask.inner_text()
        read = ask.get_by_role("button", name="Read it")
        assert await read.is_disabled() and (await read.bounding_box())["height"] >= 44
        await _shot_to(page, "phone-proposals-empty")
        await ask.get_by_label("What is this project for?").fill("our team's wiki")
        await read.click()
        await sheet.locator('.prop[data-proposal="wiki"]').wait_for(timeout=WAIT_MS)
        assert calls(stub, "ideas.proposals")[-1] == {"about": "our team's wiki"}
        assert [await c.get_attribute("data-proposal") for c in await sheet.locator(".prop").all()] == ["wiki", "ideation"]
        assert norm(await sheet.locator(".props__top").inner_text()) == "Orkmaster proposes for this project · a team's wiki"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_line_no_model_could_read_is_said_and_the_proposals_are_the_codes(fake_repo, monkeypatch):
    def answer(about):
        return {"kind": {"id": "code", "words": "code", "signs": []}, "ask": False, "read": False, "proposals": copy.deepcopy(MOBILE[:1])}
    proposing(monkeypatch, kind=EMPTY_KIND, proposals=[IDEATION], ask=True, answer=answer)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.get_by_label("What is this project for?").fill("a thing")
        await sheet.get_by_role("button", name="Read it").click()
        await sheet.locator('.prop[data-proposal="mobile-features"]').wait_for(timeout=WAIT_MS)
        assert "It could not read your line: these are the proposals for code." in await sheet.locator(".props__note").inner_text()
        assert norm(await sheet.locator(".props__top").inner_text()) == "Orkmaster proposes for this project · code"


# -- More: the library -------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_more_the_library_is_todays_tiles_and_seats_with_the_size_switch_and_the_way_back(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        more = sheet.get_by_role("button", name="More: the library")
        assert (await more.bounding_box())["height"] >= 44
        await more.click()
        await sheet.locator(".preset-tile").first.wait_for(timeout=WAIT_MS)
        assert await sheet.locator(".prop").count() == 0 and await sheet.get_by_role("button", name="Save party").is_visible()
        assert await sheet.locator('.preset-tile[data-preset="release"]').count() == 1 and await sheet.locator(".party-line").count() >= 1       # today's tiles and seats
        group = sheet.get_by_role("radiogroup", name="Its size")
        assert await group.get_by_role("radio", name="Standard").get_attribute("aria-checked") == "true"
        await group.get_by_role("radio", name="Full").click()
        await sheet.get_by_label("What it is for").fill("A party of my own")
        await sheet.locator('.preset-tile[data-preset="release"]').click()
        await sheet.get_by_role("button", name="Save party").click()
        await _called(stub, "ideas.goal_save")
        sent = calls(stub, "ideas.goal_save")[-1]
        assert sent["size"] == "full" and sent["about"] == "A party of my own" and sent["preset"] == "release" and sent["leader"] == "release-manager"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_the_way_back_from_the_library_shows_the_proposals_with_no_second_question(fake_repo, monkeypatch):
    proposing(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _new_party(page)
        await sheet.get_by_role("button", name="More: the library").click()
        await sheet.get_by_label("What it is for").fill("a party of my own")                                                          # the library asks it, as New party did
        await sheet.get_by_role("button", name="Orkmaster proposes").click()                                                          # the way back
        await sheet.locator(".prop").first.wait_for(timeout=WAIT_MS)
        assert await sheet.get_by_label("What it is for").count() == 0 and await sheet.get_by_role("button", name="Save party").is_hidden()


# -- the deal ---------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_deal_shows_the_proposals_first_with_standards_price_and_a_press_opens_new_party_on_it(fake_repo, monkeypatch):
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
        await sheet.locator(".prop").first.wait_for(timeout=WAIT_MS)
        assert "is-picked" in await card_of(sheet, "mobile-architecture").get_attribute("class")
        assert await card_of(sheet, "mobile-architecture").evaluate("(e) => { const r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; }")


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
    assert 'const CACHE = "orkcraft-app-v84";' in sw and '"shell-proposals.js"' in sw[sw.index("const SHELL"):sw.index("];", sw.index("const SHELL"))]
    assert re.search(r'orkcraft-app-v(\d+)', sw).group(1) == "84" and library.get(PM) is not None
