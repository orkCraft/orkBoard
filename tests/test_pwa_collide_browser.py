"""Spec 71 part C, the phone (docs/specs/71-orkmaster-keeps-parties-apart.md §6, §7 C, §8; decisions §86): Chromium at 390 × 844 against the stub host of spec §8. The hand's stop `collide`
(the Orkmaster's head from `project.orkmaster`, *Orkmaster asks*, the text and the why, its two goals each a 44 px press that opens it, its answers as buttons that say what happens and send
`ideas.collide_answer {id, answer}`); a goal with `waits_for` in the Goals sheet (orkUI's ← sign as its state sign, *waits for <party> · <goal>* in its words); a host without them keeps today's
phone; no sideways scroll; `sw.js` v83."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

from orkboard.gui import pwa
from tests.test_pwa_arena_browser import SCENE, STAMP, _scene, node  # noqa: F401
from tests.test_pwa_route_browser import WORLD, world  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, Stub, _called, _phone, _pop

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

SHOT = os.environ.get("COLLIDE_SHOT", "")                                  # a path: a screenshot of the hand is kept there (a test of the look, kept by hand)
ORKMASTER = {"id": "orkmaster", "name": "Orkmaster", "race": "peon", "tier": "elder"}
ANSWER: dict = {}                    # what `ideas.collide_answer` answers (or an error)
LABELS = "() => [...document.querySelectorAll('.hand .hc')].map((b) => b.getAttribute('aria-label'))"


def goals_of(by="plan"):
    first = {"idea": "register", "party": "passkey", "party_name": "Passkey", "title": "WebAuthn register", "element": "ice"}
    second = {"idea": "site-login", "party": "website", "party_name": "Website", "title": "Site login", "element": "dust"}
    return [first, second] if by == "plan" else [second, first]


def stop(by="plan", **more):
    """The Orkmaster's stop as `ideas.board` serves it in `needs_you` (spec §8.1), on the goal asked about."""
    plan = by == "plan"
    c = {"id": "register|site-login", "by": by, "why": "Both change how a session token is issued", "first": "register" if plan else "",
         "goals": goals_of(by), "answers": ["first:register", "first:site-login", "one", "leave"] if plan else ["replan", "leave"]}
    text = "Passkey «WebAuthn register» and Website «Site login» change the same thing" if plan else "Website changed «Site login»: «WebAuthn register» in Passkey rests on what it was"
    return {"kind": "collide", "idea": "register", "goal": "passkey", "title": "WebAuthn register", "priority": "normal", "blocks": False, "at": STAMP, "text": text, "collide": c, **more}


def hosted(monkeypatch, by="plan", project=True, stops=True):
    """The route tests' world (Passkey, Website, Release, Ideation) with a goal of Website, the Orkmaster and, with `stops`, the stop; `ideas.collide_answer` answers and takes the stop away."""
    world(monkeypatch)
    SCENE["map"]["nodes"].append(node("site-login", "Site login", "working", "implementation", goal="website", element="dust", route=[]))
    if project:
        SCENE["map"]["project"] = {"orkmaster": copy.deepcopy(ORKMASTER), "deal": [], "collisions": [{"id": "register|site-login", "a": "register", "b": "site-login"}] if stops else []}
    if stops:
        SCENE["needs"].append(stop(by))
        next(n for n in SCENE["map"]["nodes"] if n["slug"] == "register")["needs_you"] = "collide"
    ANSWER.clear()
    real = Stub.commands

    def commands(self):
        got = real(self)

        def answer(a):
            a = {k: v for k, v in a.items() if k not in ("link", "device")}
            self.calls.append(("ideas.collide_answer", dict(a)))
            if ANSWER.get("error"):
                return {"error": ANSWER["error"]}
            SCENE["needs"] = [n for n in SCENE["needs"] if n["kind"] != "collide"]
            next(n for n in SCENE["map"]["nodes"] if n["slug"] == "register")["needs_you"] = ""
            self.bump({})
            return {"ok": True}
        return {**got, "ideas.collide_answer": answer}
    monkeypatch.setattr(Stub, "commands", commands)


async def _flash(page, text):
    await page.locator(".flash", has_text=text).first.wait_for(timeout=WAIT_MS)
    return True


async def _raised(page, by="plan"):
    return await _pop(page, "Orkmaster asks: WebAuthn register")


# -- the stop (§6, §8.1) ---------------------------------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_stop_is_a_card_in_the_hand_with_the_orkmasters_head_its_text_its_why_and_its_two_goals(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        card = page.locator('.hc[data-kind="collide"]')
        await card.wait_for(timeout=WAIT_MS)
        assert await card.get_attribute("aria-label") == "Orkmaster asks: WebAuthn register"
        raised = await _raised(page)
        assert (await raised.locator(".raised__kind").inner_text()).strip().lower() == "orkmaster asks"
        head = raised.locator(".art img.ork-race__head")
        assert await head.get_attribute("src") == "races/peon-elder@2x.png" and await head.get_attribute("title") == "Orkmaster"             # project.orkmaster
        assert (await raised.locator(".raised__text").inner_text()).strip() == "Passkey «WebAuthn register» and Website «Site login» change the same thing"
        assert (await raised.locator(".raised__why").inner_text()).strip() == "Both change how a session token is issued"
        goals = raised.locator(".cl-goal")
        assert [" ".join((await g.inner_text()).split()) for g in await goals.all()] == ["Passkey · WebAuthn register", "Website · Site login"]
        for g in await goals.all():
            box = await g.bounding_box()
            assert box["height"] >= 44 and box["x"] >= 0 and box["x"] + box["width"] <= 390                                                   # a 44 px tap, inside the screen
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_the_stop_lies_among_the_stops_that_do_not_hold_work_back_in_the_urgency_after_a_plan(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator('.hc[data-kind="collide"]').wait_for(timeout=WAIT_MS)
        labels = await page.evaluate(LABELS)
        at = {kind: next(i for i, label in enumerate(labels) if label.startswith(kind)) for kind in ("Failed", "Plan ready", "Orkmaster asks", "To look at")}
        assert at["Failed"] < at["Plan ready"] < at["Orkmaster asks"] < at["To look at"]


@pytest.mark.asyncio
async def test_the_answers_are_buttons_that_say_what_happens_and_the_suggested_first_is_the_primary(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        raised = await _raised(page)
        buttons = raised.locator(".raised__quick .ork-btn")
        assert [(await b.inner_text()).strip() for b in await buttons.all()] == ["WebAuthn register first", "Site login first", "One goal", "Leave it"]
        assert [await b.get_attribute("data-answer") for b in await buttons.all()] == ["first:register", "first:site-login", "one", "leave"]
        assert [("primary" in await b.get_attribute("class")) for b in await buttons.all()] == [True, False, False, False]                     # the judge's suggestion
        assert "Site login waits until WebAuthn register is flagged" in await buttons.nth(0).get_attribute("title")
        assert "dropped" in await buttons.nth(2).get_attribute("title") and "not asked again" in await buttons.nth(3).get_attribute("title")
        assert all([(await b.bounding_box())["height"] >= 44 for b in await buttons.all()])


@pytest.mark.asyncio
@pytest.mark.parametrize("answer,said", [("first:register", "WebAuthn register goes first."), ("first:site-login", "Site login goes first."), ("one", "Joined into one goal."), ("leave", "Left as they are.")])
async def test_each_answer_sends_collide_answer_with_the_pair_and_its_word_and_the_stop_goes(fake_repo, monkeypatch, answer, said):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        raised = await _raised(page)
        await raised.locator(f'.raised__quick [data-answer="{answer}"]').click()
        assert await _called(stub, "ideas.collide_answer", {"id": "register|site-login", "answer": answer})
        assert await _flash(page, said)
        await page.locator('.hc[data-kind="collide"]').wait_for(state="detached", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_a_spec_changed_under_another_party_asks_to_re_plan_or_leave_it(fake_repo, monkeypatch):
    hosted(monkeypatch, by="change")
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        raised = await _raised(page)
        assert (await raised.locator(".raised__text").inner_text()).strip() == "Website changed «Site login»: «WebAuthn register» in Passkey rests on what it was"
        assert [" ".join((await g.inner_text()).split()) for g in await raised.locator(".cl-goal").all()] == ["Website · Site login", "Passkey · WebAuthn register"]        # the changed goal first
        buttons = raised.locator(".raised__quick .ork-btn")
        assert [(await b.inner_text()).strip() for b in await buttons.all()] == ["Re-plan it", "Leave it"]
        await buttons.nth(0).click()
        assert await _called(stub, "ideas.collide_answer", {"id": "register|site-login", "answer": "replan"})
        assert await _flash(page, "Re-planning what is left.")


@pytest.mark.asyncio
async def test_a_refused_answer_keeps_the_stop_and_says_why(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        ANSWER.update(error="That is answered already")
        raised = await _raised(page)
        await raised.locator('[data-answer="leave"]').click()
        assert await _flash(page, "That is answered already")
        assert await page.locator("dialog.raised-dlg[open]").count() == 1 and await page.locator('.hc[data-kind="collide"]').count() == 1


@pytest.mark.asyncio
async def test_a_press_on_a_goal_opens_it_with_its_party_shown_first(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        raised = await _raised(page)
        await raised.locator('.cl-goal[data-goal="site-login"]').click()
        await page.locator(".screen").wait_for(state="visible", timeout=WAIT_MS)
        assert await page.locator("dialog.raised-dlg[open]").count() == 0
        assert await _called(stub, "ideas.log", {"event": "opened", "what": "idea", "ref": "site-login", "device": "phone", "via": "hand"})
        assert "Site login" in await page.locator(".screen").inner_text()
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_the_front_card_answers_with_the_suggested_first_and_more(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator('.hc[data-kind="collide"]:not(.is-front)').dispatch_event("click")                                                 # a tap on a fanned card brings it to the front
        front = page.locator('.hc.is-front[data-kind="collide"]')
        await front.wait_for(timeout=WAIT_MS)
        quick = front.locator(".hc__quick .ork-btn")
        assert [(await b.inner_text()).strip() for b in await quick.all()] == ["WebAuthn register first", "More…"]
        await quick.nth(0).click()
        assert await _called(stub, "ideas.collide_answer", {"id": "register|site-login", "answer": "first:register"})


# -- a goal that waits (§4, §6, §8.3) -----------------------------------------------------------------------------------------------------------


WAITS = [{"goal": "auth-api", "party": "backend", "party_name": "Backend", "title": "Auth API", "flag": ""}]


async def _sheet(page):
    await page.locator(".gbar__head").wait_for(timeout=WAIT_MS)
    await page.locator(".gbar__head").click()
    sheet = page.get_by_role("dialog", name="Goals")
    await sheet.wait_for(timeout=WAIT_MS)
    return sheet


@pytest.mark.asyncio
async def test_a_goal_that_waits_for_another_partys_wears_the_before_sign_and_says_it_in_its_label(fake_repo, monkeypatch):
    hosted(monkeypatch, stops=False)
    next(n for n in SCENE["map"]["nodes"] if n["slug"] == "register")["waits_for"] = copy.deepcopy(WAITS)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        row = sheet.locator('.dk[data-idea="register"]')
        assert await row.locator(".dk__mark .ork-sign.before").count() == 1 and await row.locator(".dk__mark .ork-sign.work").count() == 0       # orkUI's ← is its state sign
        label = await row.locator(".dk__main").get_attribute("aria-label")
        assert "waits for Backend · Auth API" in label and label.startswith("WebAuthn register · ")
        main = await row.locator(".dk__main").bounding_box()
        assert round(main["height"]) == 44 and await page.evaluate(NO_SCROLL)                                                                  # still one line of 44 px
        await row.locator(".dk__open").click()
        await page.locator(".screen").wait_for(state="visible", timeout=WAIT_MS)


@pytest.mark.asyncio
async def test_a_wait_whose_flag_is_raised_is_over_and_a_louder_mark_stays(fake_repo, monkeypatch):
    hosted(monkeypatch, stops=False)
    next(n for n in SCENE["map"]["nodes"] if n["slug"] == "register")["waits_for"] = [{**WAITS[0], "flag": "2026-10-24"}]
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        row = sheet.locator('.dk[data-idea="register"]')
        assert await row.locator(".ork-sign.before").count() == 0 and "waits for" not in await row.locator(".dk__main").get_attribute("aria-label")
        assert await row.locator(".dk__mark .ork-sign.work").count() == 1


@pytest.mark.asyncio
async def test_a_host_without_collide_rows_or_waits_keeps_todays_phone(fake_repo, monkeypatch):
    hosted(monkeypatch, project=False, stops=False)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        sheet = await _sheet(page)
        assert await sheet.locator(".ork-sign.before").count() == 0 and "waits for" not in await sheet.inner_text()
        assert await page.locator('.hc[data-kind="collide"]').count() == 0
        assert not [c for c in stub.calls if c[0] == "ideas.collide_answer"]


@pytest.mark.asyncio
async def test_a_stop_of_a_host_with_no_project_still_draws_with_the_default_head(fake_repo, monkeypatch):
    hosted(monkeypatch, project=False)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        raised = await _raised(page)
        assert await raised.locator('.cl-goal').count() == 2 and await raised.locator(".raised__quick .ork-btn").count() == 4


# -- the look ---------------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_hand_with_the_stop_raised_fits_the_screen(fake_repo, monkeypatch):
    hosted(monkeypatch)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        raised = await _raised(page)
        box = await raised.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= 390 and box["y"] >= 0 and box["y"] + box["height"] <= 844 and await page.evaluate(NO_SCROLL)
        if SHOT:
            Path(SHOT).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=SHOT)


def test_the_service_worker_is_one_up():
    sw = (Path(pwa.__file__).parent / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v83";' in sw
