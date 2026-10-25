"""Spec 43 A on the desktop (docs/specs/43-party-measured.md §1.4, §1.5, Tests → A): a check's result in Review says what it found, with *Fix
them* and *Leave them*; the idea's Checks say *clean* and *found 2: 1 fixed, 1 left*."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import gui  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import GREEN, WAIT_MS, _open, _sent, _show_goal, task  # noqa: E402,F401

pytestmark = pytest.mark.browser

NO_RUN = {"passed": 0, "failed": 0, "failing": [], "tail": "", "green": True, "ran": False, "command": ""}
FOUND = [{"where": "sync.py:41", "what": "a lost signal is not retried", "fixed": True},
         {"where": "queue.py:9", "what": "the queue is never emptied", "fixed": False},
         {"where": "the Sync screen", "what": "no way to cancel", "fixed": False}]


def with_checks(host):
    """k6: the Reviewer's check, no file changed, 3 found (1 fixed, 2 left); k7: a check that left nothing."""
    host.plan["tasks"] += [
        task("k6", "Check: Reviewer", "review", ["k5"], kind="review", tests=NO_RUN, diff={"files": 0, "added": 0, "removed": 0}, check="Reviewer",
             findings=FOUND, note="2 left"),
        task("k7", "Check: Accessibility reviewer", "review", ["k5"], kind="a11y", tests=GREEN, diff={"files": 1, "added": 3, "removed": 0},
             check="Accessibility reviewer", findings=[{"where": "a.css:3", "what": "low contrast", "fixed": True}])]
    return host


@pytest.fixture
def review(gui):
    from tests.test_shell_browser import StubHost
    pg, host, errors = _open(gui, host=with_checks(StubHost()))
    _show_goal(pg)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def test_a_check_s_card_says_what_it_found_and_has_fix_them_leave_them_and_drop(review):
    pg, host = review
    card = pg.locator(".arena-result", has_text="Check: Reviewer")
    assert card.locator(".shell-found__sum").inner_text() == "Found 3: 1 fixed, 2 left"
    assert [" ".join(t.split()) for t in card.locator(".shell-found__list li").all_inner_texts()] == [
        "queue.py:9 · the queue is never emptied", "the Sync screen · no way to cancel"]                    # the findings left, not the fixed one
    assert card.get_by_role("button", name="Fix them").is_enabled() and card.get_by_role("button", name="Leave them").is_enabled()
    assert card.get_by_role("button", name="Drop…").count() == 1
    assert card.get_by_role("button", name="Merge into dev").count() == 0 and card.get_by_role("button", name="Send back").count() == 0
    assert "no tests ran" in card.inner_text()
    fix = pg.locator(".arena-result", has_text="Check: Accessibility reviewer")                          # nothing left: today's card
    assert fix.locator(".shell-found").count() == 0 and fix.get_by_role("button", name="Merge into dev").is_enabled()
    assert fix.get_by_role("button", name="Fix them").count() == 0


def test_fix_them_sends_back_with_the_findings_left_as_its_why(review):
    pg, host = review
    pg.locator(".arena-result", has_text="Check: Reviewer").get_by_role("button", name="Fix them").click()
    assert _sent(pg, host, ("ideas.back", {"slug": "sync", "task": "k6",
                                           "why": "Fix the findings left:\nqueue.py:9: the queue is never emptied\nthe Sync screen: no way to cancel"}))


def test_leave_them_is_the_merge(review):
    pg, host = review
    pg.locator(".arena-result", has_text="Check: Reviewer").get_by_role("button", name="Leave them").click()
    assert _sent(pg, host, ("ideas.merge", {"slug": "sync", "task": "k6"}))


def test_the_idea_s_checks_say_clean_or_found_with_what_was_fixed_and_left(review):
    pg, host = review
    host.checks[0].update(found=0, fixed=0, left=0)
    host.checks[1].update(applies=True, why="", state="passed", task="k7", found=2, fixed=1, left=1)
    host.bump({})
    pg.locator(".arena-task[data-task=k3]").click()                                                    # an idea at work: its spec from its task
    pg.locator(".shell-task").get_by_role("button", name="Sync ideas between the phone and the town").click()
    checks = pg.locator(".shell-preview").get_by_role("list", name="Checks")
    checks.wait_for(timeout=WAIT_MS)
    assert [" ".join(t.split()) for t in checks.get_by_role("listitem").all_inner_texts()] == [
        "Reviewer clean", "Accessibility reviewer found 2: 1 fixed, 1 left"]


# -- spec 86 C, D and spec 84 §4: the place's findings, a project with no tests, the reason a result waits ------------------------------

ENV = {"where": "npm test", "what": "the command was refused", "fixed": False, "kind": "env"}
CODE = {"where": "queue.py:9", "what": "the queue is never emptied", "fixed": False, "kind": "code"}
NO_FILES = {"files": 0, "added": 0, "removed": 0}
PLACE = "What is left is about where it ran, not the code"


def with_place(host):
    host.plan["tasks"] += [
        task("k8", "Check: Security", "review", ["k5"], kind="security", tests=NO_RUN, diff=NO_FILES, check="Security", findings=[ENV], note="1 left",
             look="findings left"),
        task("k9", "Check: Playtest", "review", ["k5"], kind="playtest", tests=NO_RUN, diff=NO_FILES, check="Playtester", findings=[CODE, ENV],
             note="2 left", look="findings left"),
        task("ka", "Check: Words", "review", ["k5"], kind="edit", tests=NO_RUN, diff=NO_FILES, check="Editor", findings=[CODE], note="1 left", same=True,
             look="findings left"),
        task("kb", "Add the store", "review", ["k5"], tests={**NO_RUN, "none": True}, diff={"files": 2, "added": 9, "removed": 0},
             look="no tests in this project")]
    return host


@pytest.fixture
def place(gui):
    from tests.test_shell_browser import StubHost
    pg, host, errors = _open(gui, host=with_place(StubHost()))
    _show_goal(pg)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def test_findings_of_the_place_alone_offer_merge_and_drop_and_say_what_is_left(place):
    pg, host = place
    card = pg.locator(".arena-result", has_text="Check: Security")
    assert PLACE in card.inner_text() and "(where it ran)" in card.inner_text()
    assert card.get_by_role("button", name="Fix them").count() == 0 and card.get_by_role("button", name="Send back").count() == 0
    assert card.get_by_role("button", name="Leave them").is_enabled() and card.get_by_role("button", name="Drop…").count() == 1
    card.get_by_role("button", name="Leave them").click()
    assert _sent(pg, host, ("ideas.merge", {"slug": "sync", "task": "k8"}))


def test_fix_them_lists_the_findings_of_the_code_only(place):
    pg, host = place
    card = pg.locator(".arena-result", has_text="Check: Playtest")
    assert PLACE not in card.inner_text() and card.get_by_role("button", name="Fix them").is_enabled()
    card.get_by_role("button", name="Fix them").click()
    assert _sent(pg, host, ("ideas.back", {"slug": "sync", "task": "k9", "why": "Fix the findings left:\nqueue.py:9: the queue is never emptied"}))


def test_the_same_findings_as_the_round_before_offer_merge_and_drop(place):
    pg, host = place
    card = pg.locator(".arena-result", has_text="Check: Words")
    assert PLACE in card.inner_text() and card.get_by_role("button", name="Fix them").count() == 0 and card.get_by_role("button", name="Send back").count() == 0


def test_a_result_of_a_project_with_no_tests_says_so_and_why_it_waits(place):
    pg, host = place
    card = pg.locator(".arena-result", has_text="Add the store")
    assert "no tests in this project" in card.inner_text() and "Waits: no tests in this project" in card.inner_text()
    assert pg.locator(".arena-result", has_text="Check: Security").locator("[data-look]").inner_text() == "Waits: findings left"
