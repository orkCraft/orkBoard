"""Spec 87 B (docs/specs/87-quieter-work-longer-names.md §2, §4.2, §4.3, §6): the desktop's quieter work and longer names, in a real browser at 1 440 × 900 against the arena's stub host.
A field card is 128 × 180 at most (5:7) and its name shows four lines, the whole name its `title`; a spread's cards and the project's level's take the same size; a to-do lies last in the
hand; a goal's plan says *Before <task>: <to-do>* for a to-do not done; each open project in the switcher says one mark (the alert sign, else the busy mark, else nothing) and no number."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost  # noqa: E402
from tests.test_one_hand_desktop_browser import OneHostOne  # noqa: E402
from tests.test_shell_browser import StubHost, _drawer, _open, _stop  # noqa: E402

pytestmark = pytest.mark.browser

LONG = "Spawn the waves of enemies from the wave director and tell the score keeper about each one"      # 90 characters: more than two lines, four lines at most
SHOP, BLOG, GAME = "/work/shop", "/work/blog", "/work/game"


class LongHost(ArenaHost):
    """The arena's stub with a task whose name is long and a card that stacks two of a goal's."""

    def __init__(self):
        super().__init__()
        t = self.node_of("register")["tasks"][1]                       # k2, at work
        t["title"], t["short"] = LONG, ""


def _name(pg, key):
    return pg.locator(f".arena-task[data-key='{key}'] .arena-task__name")


def test_a_card_is_128_by_180_at_most_its_name_shows_four_lines_and_its_whole_name_is_its_title(gui):
    pg, host, errors = _open(gui, host=LongHost(), ready=".arena-phead", viewport={"width": 1500, "height": 900})
    try:
        pg.locator(".arena-task[data-key='register/k2']").wait_for(timeout=WAIT_MS)
        pg.locator(".arena-member[data-agent=backend]").click()                                                  # alone: the card at its full size
        solo = pg.get_by_role("group", name="Only Backend’s tasks")
        one = solo.locator(".arena-task[data-key='register/k2']")
        one.wait_for(timeout=WAIT_MS)
        bb = one.bounding_box()
        assert abs(bb["width"] - 128) < 0.5 and bb["height"] <= 180.5 and abs(bb["height"] / bb["width"] - 7 / 5) < 0.02, bb
        name = one.locator(".arena-task__name")
        line = float(name.evaluate("e => parseFloat(getComputedStyle(e).lineHeight)"))
        shown = name.evaluate("e => ({h: e.getBoundingClientRect().height, clamp: getComputedStyle(e).webkitLineClamp, full: e.scrollHeight})")
        assert shown["clamp"] == "4" and abs(shown["h"] - 4 * line) < 1                                          # four lines, not two
        assert shown["full"] >= shown["h"] - 1
        assert name.get_attribute("title") == LONG                                                              # the whole name on hover
        assert name.inner_text() == LONG
        inside = one.bounding_box()                                                                             # the foot and the count stay inside the card
        foot = one.locator(".arena-task__foot").bounding_box()
        assert foot["y"] + foot["height"] <= inside["y"] + inside["height"] + 0.5
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_short_name_keeps_its_own_lines_and_a_spread_takes_the_same_size(gui):
    pg, host, errors = _open(gui, host=LongHost(), ready=".arena-phead", viewport={"width": 1500, "height": 900})
    try:
        pg.locator(".arena-task[data-key='register/k2']").wait_for(timeout=WAIT_MS)
        stack = pg.locator(".arena-stack[data-agent=backend] .arena-phase[data-row=now] .arena-stk[data-goal=register] .arena-task")
        stack.click()                                                                                           # two of the goal's tasks: a press spreads them
        cards = pg.get_by_role("group", name="tasks of Backend at this phase").locator(".arena-spread__card")
        cards.first.wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => document.getAnimations().every((a) => !a.effect?.target?.classList?.contains('arena-spread__card'))", timeout=WAIT_MS)
        for c in cards.all():
            bb = c.bounding_box()
            assert abs(bb["width"] - 128) < 0.5 and abs(bb["height"] - 180) < 0.5, bb
        assert cards.nth(0).locator(".arena-task__name").get_attribute("title") == LONG
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_to_do_lies_last_in_the_hand_after_the_questions_the_plans_and_the_failures(gui):
    pg, host, errors = _open(gui, host=OneHostOne(), ready=".arena[data-goal=passkey]")
    try:
        cards = pg.locator(".arena-hc")
        cards.first.wait_for(timeout=WAIT_MS)
        kinds = [c.get_attribute("data-kind") for c in cards.all()]
        assert kinds[-1] == "todo" and kinds.count("todo") == 1                                                 # last of all
        assert kinds[:-1] == ["op_failed", "failed", "goal", "op", "plan", "asks", "proposal"]                  # the others as they were: urgency's order
        by_x = sorted(cards.all(), key=lambda c: c.bounding_box()["x"])
        assert by_x[0].get_attribute("data-kind") == "proposal" and by_x[-1].get_attribute("data-kind") == "todo"       # the outermost of the fan, to its right
        assert pg.locator('.arena-hc[data-kind="todo"]').get_attribute("data-party") == "pricing"
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_goals_plan_says_before_a_task_what_is_to_do_and_none_once_it_is_done(gui):
    host = StubHost()
    pg, host, errors = _open(gui, host=host)
    try:
        _stop(pg, "todo").get_by_role("button", name="Open…").click()
        pg.get_by_role("dialog", name="API_KEY").get_by_role("button", name="What waits for it").click()
        plan = _drawer(pg).locator(".board-plan")
        plan.locator("[data-before]").first.wait_for(timeout=WAIT_MS)
        lines = [" ".join(li.inner_text().split()) for li in plan.locator("[data-before]").all()]
        assert lines == ["Before Add the queue: API_KEY", "Before Retry on a lost signal: API_KEY"]               # in the plan's order, a task not merged
        assert plan.locator("[aria-label='To-dos to come']").count() == 1
        assert plan.locator(".board-plan__todo.is-target").count() == 1                                         # the to-do's own block stays where it was
    finally:
        pg.close()
    assert not errors, "\n".join(errors)

    # the same lines from the pure function: a to-do done is not said, nor a task merged; the host's own `todo_lines` is used when the plan carries it
    tasks = [{"id": "k1", "title": "Spawn the boss", "state": "ready"}, {"id": "k2", "title": "Add the queue", "state": "merged"}, {"id": "k3", "title": "Show it", "state": "waiting"}]
    todos = [{"id": "t1", "title": "Record the boss's sounds", "for": ["k1", "k2"], "done": False}, {"id": "t2", "title": "API_KEY", "for": ["k3"], "done": True},
             {"id": "t3", "title": "Pick a font", "for": ["k3", "k1"], "done": False}]
    assert page_lines(gui, {"tasks": tasks, "todos": todos}) == ["Before Spawn the boss: Record the boss's sounds", "Before Spawn the boss: Pick a font", "Before Show it: Pick a font"]
    assert page_lines(gui, {"tasks": [], "todos": [], "todo_lines": ["Before X: Y"]}) == ["Before X: Y"]


def page_lines(gui, plan):
    """`todoLines` of `board/idea.js`, run in the page on a plan."""
    server, browser = gui
    pg = browser.new_page()
    try:
        pg.goto(server.url + "/static/page.css")
        return pg.evaluate("async (plan) => (await import('/static/js/board/idea.js')).todoLines(plan)", plan)
    finally:
        pg.close()


class SwitchHost(ArenaHost):
    """Three open projects: one with something waiting (and a task at work), one at work, one quiet."""

    def snapshot(self):
        snap = super().snapshot()
        snap["state"]["projects"] = {"current": SHOP, "recent": [], "open": [
            {"path": SHOP, "name": "shop", "working": 1, "needs_you": 2, "review": 3},
            {"path": BLOG, "name": "blog", "working": 4, "needs_you": 0, "review": 0},
            {"path": GAME, "name": "game", "working": 0, "needs_you": 0, "review": 0}]}
        return snap


def test_each_open_project_says_one_mark_and_no_number(gui):
    pg, host, errors = _open(gui, host=SwitchHost(), ready=".arena[data-goal=passkey]")
    try:
        pg.locator(".shell-proj__btn").click()
        one = lambda path: pg.locator(f".shell-proj__one[data-path='{path}']")                                   # noqa: E731
        one(SHOP).wait_for(timeout=WAIT_MS)
        assert one(SHOP).locator(".ork-sign.alert").count() == 1 and one(SHOP).locator(".ork-busy").count() == 0      # waits for you, though a task is at work too: the alert sign alone
        assert one(BLOG).locator(".ork-busy").count() == 1 and one(BLOG).locator(".ork-sign").count() == 0
        assert one(GAME).locator(".ork-busy, .ork-sign, [data-mark]").count() == 0                                # nothing
        for path, name in ((SHOP, "shop"), (BLOG, "blog"), (GAME, "game")):
            words = " ".join(one(path).inner_text().split())
            assert words.strip("✓ ").strip() == name, words                                                      # the name and nothing else: no count, no word
        assert one(SHOP).locator("[data-mark=alert]").get_attribute("aria-label") == "waits for you"
        assert one(BLOG).locator("[data-mark=busy]").get_attribute("aria-label") == "at work"
        tone = one(SHOP).locator("[data-mark=alert]").evaluate("e => getComputedStyle(e).color")
        text = one(SHOP).locator(".shell-proj__name").evaluate("e => getComputedStyle(e).color")
        assert tone != text                                                                                      # the alert sign is in the alert colour
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
