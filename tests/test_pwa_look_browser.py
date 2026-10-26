"""Spec 85 C, the phone (docs/specs/85-the-elf-asks-and-shows.md §1, §3, §4, §5): Chromium at 390 × 844 against the stub of test_pwa_shell_browser.py with the arena's Board. The elf's question is a
stop with the elf's head, *<Name> asks about the look*, its choices answer in one tap and *Pictures you like* opens the form that takes pictures; a token on the field wears the picture of what its task
changed and says *k of n done*; a result shows its picture large, under its stop and on its own screen, or says there is none; the stack of a merged task turns over once to *What it made*. No sideways
scroll; the service worker's version."""
from __future__ import annotations

import base64
import re
from pathlib import Path

import pytest

from tests import pick_files as pf
from tests.test_pwa_arena_browser import ELF, SCENE, SCREENS, _redrawn, _scene, task  # noqa: F401
from tests.test_pwa_shell_browser import NO_SCROLL, WAIT_MS, _called, _phone, _pop  # noqa: F401

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

PNG = "data:image/png;base64," + base64.b64encode(pf.png(64, 40)).decode()
ELF_BY = {**SCREENS, "head": ELF}
MOOD = {"ask": "What mood should the sign-in have?", "choices": ["Calm", "Loud", "Playful"], "pick": 0, "why": "the product is a tool", "look": True, "by": ELF_BY}
REFS = {"ask": "Any pictures to start from?", "choices": ["Pictures you like", "None", "Links"], "pick": 1, "why": "", "look": True, "by": ELF_BY}


def node_of(slug):
    return next(n for n in SCENE["map"]["nodes"] if n["slug"] == slug)


def asking(*questions):
    """The goal `second` asks these (its Needs you row carries them as the host's rows do: with no asker, with `look`)."""
    node_of("second")["asked"] = [dict(q) for q in questions]
    row = next(r for r in SCENE["needs"] if r.get("idea") == "second")
    row["asked"] = [{k: v for k, v in q.items() if k != "by"} for q in questions]
    row["text"], row["questions"] = questions[0]["ask"], [q["ask"] for q in questions]


def counted():
    for n in SCENE["map"]["nodes"]:
        n["done"], n["of"] = n["progress"]["done"], n["progress"]["total"]
        for t in n["tasks"]:
            t.setdefault("shot", None)
            t.setdefault("made", "")


async def ask_of(page):
    return page.locator(".raised[data-kind=asks]")


# -- the elf asks (§1, §5) ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_the_elfs_question_is_a_stop_with_its_head_and_its_name_over_the_look_and_a_choice_answers_in_one_tap(fake_repo, monkeypatch):
    asking(MOOD)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        raised = await _pop(page, "Screens asks about the look")
        assert await raised.locator(".banner").inner_text() == "Screens asks about the look"
        assert "races/elf-warrior" in await raised.locator(".raised__top img.ork-race__head").first.get_attribute("src")      # the elf's small head
        buttons = raised.locator(".raised__quick [data-choice]")
        assert [await b.inner_text() for b in await buttons.all()] == ["● Calm", "Loud", "Playful"]
        await buttons.nth(1).click()
        assert await _called(stub, "ideas.answer", {"slug": "second", "answers": ["Loud"]})


@pytest.mark.asyncio
async def test_a_question_that_is_not_of_the_look_keeps_its_title(fake_repo, monkeypatch):
    asking({**MOOD, "look": False})
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        raised = await _pop(page, "Passkey on a second device")
        assert await raised.locator(".banner").inner_text() == "Passkey on a second device"


@pytest.mark.asyncio
async def test_pictures_you_like_opens_the_form_which_takes_pictures_and_sends_them_with_the_answer(fake_repo, monkeypatch, tmp_path):
    asking(REFS)
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        raised = await _pop(page, "Screens asks about the look")
        await raised.locator('.raised__quick [data-choice="0"]').click()                  # Pictures you like: not answered at once, the form opens
        form = page.get_by_role("dialog", name="Questions")
        await form.wait_for(timeout=WAIT_MS)
        assert await form.get_by_label("Answer 1: Any pictures to start from?").input_value() == "Pictures you like"
        assert [await b.inner_text() for b in await form.locator(".q-choices button").all()] == ["Pictures you like", "None", "Links"]
        assert not [c for c in stub.calls if c[0] == "ideas.answer"]
        (tmp_path / "like.png").write_bytes(pf.png(40, 30))
        await form.locator("input[type=file]").set_input_files(str(tmp_path / "like.png"))
        await form.locator("[data-pictures] img").wait_for(timeout=WAIT_MS)
        add = form.get_by_role("button", name="Add a picture")
        assert (await add.bounding_box())["height"] >= 40
        await form.get_by_role("button", name="Send").click()
        for _ in range(100):
            sent = [a for n, a in stub.calls if n == "ideas.answer"]
            if sent:
                break
            await page.wait_for_timeout(50)
        (sent,) = sent
        assert sent["slug"] == "second" and sent["answers"] == ["Pictures you like"] and len(sent["photos"]) == 1
        assert base64.b64decode(sent["photos"][0]["data"])[:3] == b"\xff\xd8\xff"
        assert await page.evaluate(NO_SCROLL)


# -- a token's picture and count (§3, §4) ----------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_token_wears_the_picture_of_what_its_task_changed_and_every_token_says_how_far_its_goal_is(fake_repo, monkeypatch):
    counted()
    node_of("register")["tasks"][2]["shot"] = {"id": "k3-shot-r1", "file": "shot.png", "w": 1280, "h": 800, "url": PNG}
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        await page.locator(".deck[data-task=k3]").wait_for(timeout=WAIT_MS)
        k3, k5 = page.locator(".deck[data-task=k3]"), page.locator(".deck[data-task=k5]")
        assert await k3.locator(".tcard.has-shot img.tcard__shot").get_attribute("src") == PNG and await k5.locator("img").count() == 0
        whole, face = await k3.locator(".tcard").bounding_box(), await k3.locator("img.tcard__shot").bounding_box()
        assert abs(face["width"] - whole["width"]) <= 2 and abs(face["height"] - whole["height"]) <= 2 and abs(whole["width"] - 74) <= 2         # the token's face, still 74 px wide
        assert abs(whole["height"] / whole["width"] - 7 / 5) < 0.03
        assert await k3.locator(".tcard__name").evaluate("e => getComputedStyle(e).zIndex") == "1" and await k3.locator(".tcard__name").inner_text() == "Register screen"
        assert await k3.locator(".tcard__count").inner_text() == "0 of 6 done" and await k5.locator(".tcard__count").inner_text() == "0 of 6 done"
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_goal_with_no_plan_says_nothing_of_how_far_it_is(fake_repo, monkeypatch):
    counted()
    node_of("register")["of"] = 0
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".deck[data-task=k3]").wait_for(timeout=WAIT_MS)
        assert await page.locator(".deck[data-task=k3] .tcard__count").count() == 0


# -- a result's picture (§3) ---------------------------------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_a_result_shows_its_picture_large_under_its_stop_and_says_when_there_is_none(fake_repo, monkeypatch):
    shot = {"id": "k1-shot-r1", "file": "shot.png", "w": 1280, "h": 800, "url": PNG}
    for r in SCENE["results"]:
        r["shot"] = dict(shot) if r["task"] == "k1" else {"none": "no picture: no preview"}
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        raised = await _pop(page, "To look at: Challenge store")
        img = raised.locator(".result-more .result-shot img")
        assert await img.get_attribute("src") == PNG and await img.get_attribute("alt") == "What “Challenge store” looks like"
        shown, card = await img.bounding_box(), await raised.bounding_box()
        assert shown["width"] >= card["width"] - 40 and abs(shown["width"] / shown["height"] - 1280 / 800) < 0.05          # the card's width, the picture's own shape
        await page.keyboard.press("Escape")
        other = await _pop(page, "To look at: Words on the screens")
        assert await other.locator("[data-noshot]").inner_text() == "no picture: no preview" and await other.locator("img.result-shot, .result-shot img").count() == 0
        assert await page.evaluate(NO_SCROLL)


@pytest.mark.asyncio
async def test_a_result_with_no_word_about_a_picture_is_as_it_was(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".gbar").wait_for(timeout=WAIT_MS)
        raised = await _pop(page, "To look at: Challenge store")
        assert await raised.locator(".result-shot, [data-noshot]").count() == 0


# -- a done stack turns over (§4) --------------------------------------------------------------------------------------------------------

WATCH = """() => { window.__made = []; new MutationObserver((rs) => rs.forEach((r) => r.addedNodes.forEach((n) => {
  const m = n.nodeType === 1 && (n.matches?.('[data-made]') ? n : n.querySelector?.('[data-made]')); if (m) window.__made.push(m.textContent); }))).observe(document.body, { childList: true, subtree: true }); }"""


@pytest.mark.asyncio
async def test_the_stack_of_a_merged_task_turns_over_once_to_what_it_made(fake_repo, monkeypatch):
    counted()
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".deck[data-task=k3]").wait_for(timeout=WAIT_MS)
        await page.wait_for_timeout(700)
        await page.evaluate(WATCH)
        k3 = node_of("register")["tasks"][2]
        k3["state"], k3["made"] = "merged", "Add the register screen"
        node_of("register")["done"] = 1
        await _redrawn(stub, page, 100)
        await page.wait_for_function("() => window.__made.length > 0", timeout=WAIT_MS)
        assert await page.evaluate("window.__made") == ["What it madeAdd the register screen"]
        await page.wait_for_function("() => !document.querySelector('.deck[data-task=k3], [data-ghost]')", timeout=WAIT_MS)
        assert await page.locator("[data-made]").count() == 0


@pytest.mark.asyncio
async def test_a_task_dropped_or_merged_with_nothing_made_does_not_turn(fake_repo, monkeypatch):
    counted()
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        await page.locator(".deck[data-task=k3]").wait_for(timeout=WAIT_MS)
        await page.wait_for_timeout(700)
        await page.evaluate(WATCH)
        node_of("register")["tasks"][2]["state"] = "merged"
        node_of("register")["tasks"][3]["state"] = "dropped"
        await _redrawn(stub, page, 900)
        assert await page.evaluate("window.__made") == []


def test_the_service_worker_is_v95_and_the_look_sheet_has_no_colour_of_its_own():
    sw = (Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "pwa" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "orkcraft-app-v99"' in sw
    css = (Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "pwa" / "app.css").read_text(encoding="utf-8")
    block = css[css.index("What the elf asks and shows (spec 85 C)"):]
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|border-radius", block)
