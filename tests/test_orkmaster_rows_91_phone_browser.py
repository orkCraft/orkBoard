"""Spec 91 part F on the phone (docs/specs/91-the-owners-list.md §8, decisions §107.6): Chromium at 390 × 844 against the world of the proposal tests (the Passkey, Ideation, Website and Release parties, the Orkmaster's reading of
a mobile project) with `ideas.kind_for` answered by the real words (core/idea_kind.py). The project's sheet has, under the Orkmaster's head, the same two rows as the desktop, one under the other: *Parties* (a strip: a dashed
*New party* and two or three ready parties, each with *Add*) and *New goal* (a line, *for <party>*, *Add goal*; under it the party's kinds, three at most, the guessed one marked, and *More kinds…*); every target 44 px at
least and no sideways scroll. The line is guessed a kind as it is typed and never asks for one first; *Add goal* sends what New goal sends; *More kinds…* opens today's New goal form with the line carried over."""
from __future__ import annotations

import copy

import pytest

from orkboard.core import idea_kind
from orkboard.realm import goal_types
from tests.test_pwa_arena_browser import SCENE, _redrawn, _scene, _shot_to  # noqa: F401  (`_scene`, `_redrawn`: the fixtures of the arena's world)
from tests.test_pwa_goal_types_browser import TYPES
from tests.test_pwa_project_browser import _project, calls
from tests.test_pwa_proposals_browser import ARCH, PM, _seats, proposing
from tests.test_pwa_route_browser import WORLD, norm, world  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _called, _phone

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser


def more_kinds(monkeypatch):
    """The proposal world with Passkey offering five kinds (the row shows three) and the host answering `ideas.kind_for` as it does."""
    proposing(monkeypatch)
    bug = next(t for t in TYPES if t["id"] == "bug")
    passkey = SCENE["map"]["goals"][0]
    assert passkey["slug"] == "passkey"
    passkey["types"] = [*passkey["types"], {**copy.deepcopy(bug), "id": "tidy", "name": "Clean up", "sign": "tidy", "line": "The same behaviour in simpler code", "asks": [], "used": 0},
                        {**copy.deepcopy(bug), "id": "feature", "name": "New feature", "sign": "feature", "line": "Something people can do", "asks": [], "used": 0}]
    real = Stub.commands

    def commands(self):
        got = real(self)

        def kind_for(a):
            a = {k: v for k, v in a.items() if k not in ("link", "device")}
            self.calls.append(("ideas.kind_for", a))
            goal = next((g for g in SCENE["map"]["goals"] if g["slug"] == a.get("party")), None)
            offered = [t["id"] for t in goal.get("types") or []] if goal else [t.id for t in goal_types.CATALOG]
            return {"type": idea_kind.guess(a.get("text"), offered), "types": idea_kind.ranked(a.get("text"), offered)}
        return {**got, "ideas.kind_for": kind_for}
    monkeypatch.setattr(Stub, "commands", commands)


def title(slug):
    """A party's name as `ideas.party_for` gives it in this world: its title."""
    return next(g["title"] for g in SCENE["map"]["goals"] if g["slug"] == slug)


def goal_row(project):
    return project.locator('.orow[data-row="goal"]')


async def _use_party(project, slug):
    await goal_row(project).locator(".orow__for").click()
    await goal_row(project).locator(f'.orow__opt[data-party="{slug}"]').click()


async def _type(project, words):
    await goal_row(project).locator(".orow__text").click()
    await project.page.keyboard.type(words, delay=5)


# -- the rows, one under the other ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_two_rows_are_stacked_under_the_orkmasters_head_every_target_44_px_and_nothing_scrolls_sideways(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        await project.locator(".orow__for", has_text=f"for {title('passkey')}").wait_for(timeout=WAIT_MS)
        parties, goal = project.locator('.orow[data-row="parties"]'), goal_row(project)
        assert (await parties.locator(".orow__lab b").text_content()) == "Parties" and norm(await parties.locator(".orow__lab small").inner_text()) == "who works on this project"
        assert (await goal.locator(".orow__lab b").text_content()) == "New goal" and "say it in a line: the Orkmaster picks its kind" in await goal.locator(".orow__lab").inner_text()
        top, pb, gb = await project.locator(".pj-top").bounding_box(), await parties.bounding_box(), await goal.bounding_box()
        assert top["y"] + top["height"] <= pb["y"] + 1 and pb["y"] + pb["height"] <= gb["y"] + 1 and abs(pb["x"] - gb["x"]) < 2 and abs(pb["width"] - gb["width"]) < 2      # stacked, as wide as one another
        assert "peon-crown" in await project.locator(".pj-top img.ork-race__head").get_attribute("src")
        assert await project.locator(".orow__text").count() == 1 and await project.locator(".orow__add").inner_text() == "Add goal"
        targets = [parties.locator('[data-act="project-new-party"]'), *[c for c in await parties.locator(".ocard__add").all()], goal.locator(".orow__text"), goal.locator(".orow__for"), goal.locator(".orow__add"),
                   *[c for c in await goal.locator(".okind").all()], goal.locator('[data-act="more-kinds"]')]
        for t in targets:
            assert (await t.bounding_box())["height"] >= 44
        assert await page.evaluate(NO_SCROLL) and await project.evaluate("(d) => d.scrollWidth <= d.clientWidth")
        await _shot_to(page, "phone-orkmaster-rows")


@pytest.mark.asyncio
async def test_the_parties_row_has_new_party_and_two_or_three_proposals_and_add_takes_one(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        cards = project.locator('.orow[data-row="parties"] article.ocard')
        await cards.first.wait_for(timeout=WAIT_MS)
        assert 2 <= await cards.count() <= 3 and await project.locator('.orow[data-row="parties"] .ocard--new').count() == 1
        assert await project.locator(".ocard--new").evaluate("(e) => getComputedStyle(e).borderTopStyle") == "dashed"
        assert [await c.get_attribute("data-proposal") for c in await cards.all()][:2] == ["mobile-features", "mobile-architecture"]
        assert calls(stub, "ideas.proposals")[-1] == {}
        await cards.nth(0).get_by_role("button", name="Add Mobile app: features").click()
        sheet = page.get_by_role("dialog", name="New party")
        await sheet.locator(".pseat[data-seat]").first.wait_for(timeout=WAIT_MS)
        assert await _seats(sheet, "lead") == [PM] and await sheet.get_by_label("Name", exact=True).get_attribute("placeholder") == "Mobile app: features"       # New party on that proposal's seats
        assert await project.is_hidden()                                                                                        # the sheet gives way to New party


# -- the new goal: the party, the kinds -----------------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_before_a_word_the_orkmaster_picks_the_party_and_shows_three_kinds_and_more_kinds_with_none_marked(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        goal = goal_row(project)
        await goal.locator(".okind").first.wait_for(timeout=WAIT_MS)
        assert norm(await goal.locator(".orow__for").inner_text()) == f"for {title('passkey')}" and norm(await goal.locator(".okinds__label").inner_text()) == f"{title('passkey')}'s kinds:"
        assert [await c.get_attribute("data-type") for c in await goal.locator(".okind").all()] == ["bug", "logo", "tidy"]           # three of four, as the party lists them
        assert [(await c.get_attribute("data-guessed"), await c.get_attribute("aria-pressed")) for c in await goal.locator(".okind").all()] == [("false", "false")] * 3
        assert await goal.get_by_role("button", name="More kinds…").count() == 1 and await goal.locator(".orow__add").is_disabled()
        assert not [c for c in stub.calls if c[0] == "ideas.kind_for"]


@pytest.mark.asyncio
async def test_typing_a_goal_guesses_its_kind_marks_it_and_never_asks_for_one_first(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        goal = goal_row(project)
        await goal.locator(".okind").first.wait_for(timeout=WAIT_MS)
        await _use_party(project, "passkey")
        await _type(project, "Tidy up and refactor the sign-in code")
        guessed = goal.locator('.okind[data-guessed="true"]')
        await guessed.wait_for(timeout=WAIT_MS)
        assert await guessed.get_attribute("data-type") == "tidy" and norm(await guessed.inner_text()) == "Clean up · guessed" and await guessed.get_attribute("aria-pressed") == "true"
        assert await goal.locator(".okind").first.get_attribute("data-type") == "tidy" and await goal.locator(".okind").count() == 3        # the guessed one leads, still three
        assert any(c[0] == "ideas.kind_for" and c[1].get("text", "").startswith("Tidy up") for c in stub.calls)
        assert await goal.locator(".orow__add").is_enabled()
        await _shot_to(page, "phone-orkmaster-guess")


@pytest.mark.asyncio
async def test_the_orkmaster_guesses_the_party_of_the_kind_and_for_a_party_switches_the_kinds(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        goal = goal_row(project)
        await goal.locator(".okind").first.wait_for(timeout=WAIT_MS)
        await _type(project, "A new logo for the shop")
        await goal.locator(".orow__for", has_text=f"for {title('website')}").wait_for(timeout=WAIT_MS)                                                 # Website takes a logo whole
        assert calls(stub, "ideas.party_for")[-1] == {"type": "logo"}
        assert norm(await goal.locator(".okinds__label").inner_text()) == f"{title('website')}'s kinds:" and norm(await goal.locator(".okind").first.inner_text()) == "New logo · guessed"
        await goal.locator(".orow__for").click()
        options = goal.locator(".orow__opt")
        assert [await o.get_attribute("data-party") for o in await options.all()] == ["website", "passkey", "release", "ideation"]
        assert await options.nth(0).get_attribute("aria-selected") == "true" and "takes it whole" in await options.nth(0).inner_text() and "needs Artist" in await options.nth(1).inner_text()
        assert min([(await o.bounding_box())["height"] for o in await options.all()]) >= 44
        await options.nth(1).click()                                                                                                       # Passkey, by the person
        assert norm(await goal.locator(".orow__for").inner_text()) == f"for {title('passkey')}" and await goal.locator(".orow__menu").is_hidden()
        assert norm(await goal.locator(".okinds__label").inner_text()) == f"{title('passkey')}'s kinds:"
        await goal.locator('.okind[data-type="logo"][data-guessed="true"]').wait_for(timeout=WAIT_MS)                                    # its own kinds, the line's kind still guessed there
        await goal.locator(".orow__text").press_sequentially(" in pixel art", delay=5)
        await page.wait_for_timeout(700)
        assert norm(await goal.locator(".orow__for").inner_text()) == f"for {title('passkey')}"                                          # a party the person picked stays
        await _use_party(project, "ideation")
        assert await goal.locator(".okind").count() == 0 and "takes it as a pitch" in await goal.locator(".okinds").inner_text()


@pytest.mark.asyncio
async def test_add_goal_sends_what_new_goal_sends_and_clears_the_line(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        goal = goal_row(project)
        await goal.locator(".okind").first.wait_for(timeout=WAIT_MS)
        await _use_party(project, "passkey")
        await _type(project, "Fix the crash when signing in")
        await goal.locator('.okind[data-type="bug"][data-guessed="true"]').wait_for(timeout=WAIT_MS)
        await goal.locator(".orow__add").click()
        assert await _called(stub, "ideas.add")
        sent = calls(stub, "ideas.add")[-1]
        assert sent["text"] == "Fix the crash when signing in" and sent["track"] == "passkey" and sent["type"] == "bug" and set(sent) == {"text", "track", "priority", "type"}
        await page.wait_for_function("() => document.querySelector('.orow__text').value === ''", timeout=WAIT_MS)
        assert await goal.locator(".okind[aria-pressed=true]").count() == 0 and await goal.locator(".orow__add").is_disabled()
        # a kind the person picks instead of the guessed one; the pick pressed again lets go
        await _type(project, "Tidy up and refactor the sign-in code")
        await goal.locator('.okind[data-type="tidy"][data-guessed="true"]').wait_for(timeout=WAIT_MS)
        await goal.locator('.okind[data-type="bug"]').click()
        assert await goal.locator('.okind[data-type="bug"]').get_attribute("aria-pressed") == "true" and await goal.locator('.okind[data-type="tidy"]').get_attribute("aria-pressed") == "false"
        await goal.locator('.okind[data-type="bug"]').click()
        assert await goal.locator(".okind[aria-pressed=true]").count() == 0
        await goal.locator(".orow__text").press("Enter")
        assert await _called(stub, "ideas.add")
        await page.wait_for_function("() => document.querySelector('.orow__text').value === ''", timeout=WAIT_MS)
        sent = calls(stub, "ideas.add")[-1]
        assert sent["text"] == "Tidy up and refactor the sign-in code" and "type" not in sent


@pytest.mark.asyncio
async def test_more_kinds_opens_todays_new_goal_with_the_line_carried_over_and_the_party_picked(fake_repo, monkeypatch):
    more_kinds(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        project = await _project(page)
        goal = goal_row(project)
        await goal.locator(".okind").first.wait_for(timeout=WAIT_MS)
        await _use_party(project, "website")
        await _type(project, "Offline mode for the shop")
        await goal.get_by_role("button", name="More kinds…").click()
        form = page.get_by_role("dialog", name="New goal")
        await form.wait_for(timeout=WAIT_MS)
        await form.locator(".itsparty__chip").first.wait_for(timeout=WAIT_MS)
        assert await form.get_by_role("textbox", name="The goal").input_value() == "Offline mode for the shop"                            # what was typed is there
        assert await form.locator(".itsparty__chip[aria-checked=true]").get_attribute("data-goal") == "website"                          # the party the person picked
        assert not [c for c in stub.calls if c[0] == "ideas.add"]
