"""Spec 43 A on the phone (docs/specs/43-party-measured.md §1.4, §1.5, Tests → A): a check's result, a stop along the bottom (spec 49 §10.6), says what it
found, with *Fix them* and *Leave them*; the idea's Checks say *clean* and *found 2: 1 fixed, 1 left*."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.browser

from tests.test_pwa_goal_team_browser import _pick_goal  # noqa: E402,F401
from tests.test_pwa_shell_browser import _open_idea_of, NO_SCROLL, WAIT_MS, _called, _phone, _pop  # noqa: E402,F401
from tests.test_shell_browser import GREEN, task  # noqa: E402

NO_RUN = {"passed": 0, "failed": 0, "failing": [], "tail": "", "green": True, "ran": False, "command": ""}
FOUND = [{"where": "sync.py:41", "what": "a lost signal is not retried", "fixed": True},
         {"where": "queue.py:9", "what": "the queue is never emptied", "fixed": False},
         {"where": "the Sync screen", "what": "no way to cancel", "fixed": False}]


def with_checks(stub):
    stub.plan["tasks"] += [
        task("k6", "Check: Reviewer", "review", ["k5"], kind="review", tests=NO_RUN, diff={"files": 0, "added": 0, "removed": 0}, check="Reviewer",
             findings=FOUND, note="2 left"),
        task("k7", "Check: Accessibility reviewer", "review", ["k5"], kind="a11y", tests=GREEN, diff={"files": 1, "added": 3, "removed": 0},
             check="Accessibility reviewer", findings=[{"where": "a.css:3", "what": "low contrast", "fixed": True}])]


@pytest.mark.asyncio
async def test_a_check_s_card_says_what_it_found_and_fix_them_and_leave_them_answer(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch, ) as (stub, page):
        with_checks(stub)
        stub.rev += 1
        card = await _pop(page, "To look at: Check: Reviewer")
        assert await card.locator(".found-sum").inner_text() == "Found 3: 1 fixed, 2 left"
        assert [" ".join(t.split()) for t in await card.locator(".found-list li").all_inner_texts()] == [
            "queue.py:9 · the queue is never emptied", "the Sync screen · no way to cancel"]
        assert await card.get_by_role("button", name="Fix them").is_enabled() and await card.get_by_role("button", name="Leave them").is_enabled()
        assert await card.get_by_role("button", name="Drop…").count() == 1
        assert await card.get_by_role("button", name="Merge into dev").count() == 0 and await card.get_by_role("button", name="Send back").count() == 0
        assert await page.evaluate(NO_SCROLL)
        await card.get_by_role("button", name="Put it back").click()
        await card.wait_for(state="hidden", timeout=WAIT_MS)
        other = await _pop(page, "To look at: Check: Accessibility reviewer")                          # nothing left: today's stop
        assert await other.locator(".found").count() == 0 and await other.get_by_role("button", name="Merge into dev").is_enabled()
        await other.get_by_role("button", name="Put it back").click()
        card = await _pop(page, "To look at: Check: Reviewer")
        await card.get_by_role("button", name="Fix them").click()
        assert await _called(stub, "ideas.back", {"slug": "sync", "task": "k6",
                                                  "why": "Fix the findings left:\nqueue.py:9: the queue is never emptied\nthe Sync screen: no way to cancel"})


@pytest.mark.asyncio
async def test_leave_them_is_the_merge_and_the_result_screen_says_what_was_found(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        with_checks(stub)
        stub.rev += 1
        card = await _pop(page, "To look at: Check: Reviewer")
        await card.get_by_role("button", name="Open it on its own screen").click()
        screen = page.locator(".screen")
        await screen.locator(".found-sum").wait_for(timeout=WAIT_MS)
        assert await screen.locator(".found-sum").inner_text() == "Found 3: 1 fixed, 2 left"
        await screen.get_by_role("button", name="Leave them").click()
        assert await _called(stub, "ideas.merge", {"slug": "sync", "task": "k6"})


@pytest.mark.asyncio
async def test_the_idea_s_checks_say_clean_or_found_with_what_was_fixed_and_left(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        stub.checks = [{"by": "reviewer", "name": "Reviewer", "applies": True, "why": "", "state": "passed", "found": 0, "fixed": 0, "left": 0},
                       {"by": "accessibility-reviewer", "name": "Accessibility reviewer", "applies": True, "why": "", "state": "passed", "found": 2, "fixed": 1,
                        "left": 1}]
        await _pick_goal(page, "general")
        await _open_idea_of(page, "Retry on a lost signal", "Sync ideas")
        line = page.locator(".screen").get_by_role("list", name="Checks")
        await line.wait_for(timeout=WAIT_MS)
        assert [" ".join(t.split()) for t in await line.get_by_role("listitem").all_inner_texts()] == [
            "Reviewer clean", "Accessibility reviewer found 2: 1 fixed, 1 left"]


# -- spec 86 C, D and spec 84 §4 on the phone ---------------------------------------------------------------------------------------------

ENV = {"where": "npm test", "what": "the command was refused", "fixed": False, "kind": "env"}
CODE = {"where": "queue.py:9", "what": "the queue is never emptied", "fixed": False, "kind": "code"}
NO_FILES = {"files": 0, "added": 0, "removed": 0}
PLACE = "What is left is about where it ran, not the code"


def with_place(stub):
    stub.plan["tasks"] += [
        task("k8", "Check: Security", "review", ["k5"], kind="security", tests=NO_RUN, diff=NO_FILES, check="Security", findings=[ENV], note="1 left",
             look="findings left"),
        task("k9", "Check: Playtest", "review", ["k5"], kind="playtest", tests=NO_RUN, diff=NO_FILES, check="Playtester", findings=[CODE, ENV],
             note="2 left", look="findings left"),
        task("ka", "Check: Words", "review", ["k5"], kind="edit", tests=NO_RUN, diff=NO_FILES, check="Editor", findings=[CODE], note="1 left", same=True,
             look="findings left"),
        task("kb", "Add the store", "review", ["k5"], tests={**NO_RUN, "none": True}, diff={"files": 2, "added": 9, "removed": 0},
             look="no tests in this project")]


@pytest.mark.asyncio
async def test_findings_of_the_place_alone_offer_merge_and_drop_and_say_what_is_left(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        with_place(stub)
        stub.rev += 1
        card = await _pop(page, "To look at: Check: Security")
        assert PLACE in await card.inner_text()
        assert await card.get_by_role("button", name="Fix them").count() == 0 and await card.get_by_role("button", name="Send back").count() == 0
        assert await card.get_by_role("button", name="Leave them").is_enabled() and await card.get_by_role("button", name="Drop…").count() == 1
        await card.get_by_role("button", name="Leave them").click()
        assert await _called(stub, "ideas.merge", {"slug": "sync", "task": "k8"})


@pytest.mark.asyncio
async def test_fix_them_lists_the_findings_of_the_code_only_and_the_same_again_offers_merge_and_drop(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        with_place(stub)
        stub.rev += 1
        same = await _pop(page, "To look at: Check: Words")
        assert PLACE in await same.inner_text() and await same.get_by_role("button", name="Fix them").count() == 0
        await same.get_by_role("button", name="Put it back").click()
        card = await _pop(page, "To look at: Check: Playtest")
        assert PLACE not in await card.inner_text()
        await card.get_by_role("button", name="Fix them").click()
        assert await _called(stub, "ideas.back", {"slug": "sync", "task": "k9", "why": "Fix the findings left:\nqueue.py:9: the queue is never emptied"})


@pytest.mark.asyncio
async def test_a_result_of_a_project_with_no_tests_says_so_and_why_it_waits(fake_repo, monkeypatch):
    async with _phone(fake_repo, monkeypatch) as (stub, page):
        with_place(stub)
        stub.rev += 1
        card = await _pop(page, "To look at: Add the store")
        text = await card.inner_text()
        assert "no tests in this project" in text and "waits: no tests in this project" in text
