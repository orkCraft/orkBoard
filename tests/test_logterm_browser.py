"""A task's log in a terminal's face (docs/specs/168 I1, decisions §283.16.9), in a real browser against the table's stub host: a running task opened over the pane shows its log in xterm's element (read only), its tail growing
while the task runs (`ideas.task_log` every 1.5 s), its steps over it, a masked value as the host sent it, a round's prompt not drawn, the header with the seat's head, its tier, its tool and the edit mark that opens its
leader's inventory; a task run in the person's own AI tool says so instead. A picture of it at 1366 x 768 when ORKCRAFT_SHOTS_DIR is set."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_table_desktop_browser import MEMBER, TableHost, narrow, shot, watch  # noqa: E402

pytestmark = pytest.mark.browser

STEPS = {"source": "file", "now": 1, "done": 1, "total": 3, "doing": "", "items": [{"text": "write the test for join", "state": "done"}, {"text": "make the seat survive a reconnect", "state": "now"},
                                                                                       {"text": "run the whole suite", "state": "next"}]}
HEAD = "== round 1 · 2026-11-10T09:00:00 · sonnet\nallowed: git, npm\n" + "\n".join(f"prompt line {i}: what the session was told" for i in range(30)) + "\n"
BASE = HEAD + "== the session answered\nI keep the seat in a Map, called with ••••.\n== the gate, try 1\nGET https://api.x.io/v1?key=••••\n"


class LogHost(TableHost):
    """Its running task `s1` has a log that grows by a line at every read of its tail, steps, a party and a tool; `own` makes it a task run in the person's own tool."""

    def __init__(self):
        super().__init__()
        self.ticks, self.own = 0, False

    def text(self):
        return "" if self.own else BASE + "".join(f"tests/test_seat.py::test_case_{i} PASSED\n" for i in range(self.ticks))

    def handle(self, name, a):
        got = super().handle(name, a)
        if name == "ideas.task" and a["task"] == "s1":
            return got | {"state": "running", "log": self.text(), "steps": STEPS, "party": "tech", "tool": "claude", "own_tool": self.own, "head": MEMBER["grunt"][1]}
        if name == "ideas.task_log":
            self.ticks += 1
            return {"state": "running", "log": self.text(), "steps": STEPS, "own_tool": self.own}
        return got


def open_log(gui, host, size=(1366, 768)):
    server, browser = gui
    errors: list[str] = []
    ctx = browser.new_context(viewport={"width": size[0], "height": size[1]})
    pg = ctx.new_page()
    watch(pg, errors)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.locator(".table-tab, .col-head__tab").first.wait_for(timeout=WAIT_MS)
    pg.locator(".cards-lane").first.wait_for(timeout=WAIT_MS)
    pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.openOver('log', { slug: 'seat', task: 's1' }, null, 'Keep the seat when a socket reconnects'))")
    pg.locator('.table-over[data-kind="log"]').wait_for(timeout=WAIT_MS)
    return pg, ctx, errors


def rows(pg):
    return pg.locator(".shell-logterm .xterm-rows").text_content() or ""


def test_a_running_tasks_log_is_in_a_terminal_its_tail_grows_and_its_steps_and_header_stand_over_it(gui):
    host = LogHost()
    pg, ctx, errors = open_log(gui, host)
    try:
        pg.locator(".shell-logterm .xterm-rows").wait_for(timeout=WAIT_MS)
        assert pg.locator(".shell-logterm .xterm").count() == 1 and pg.locator(".shell-logview").count() == 0                       # xterm's element, not the sections
        pg.wait_for_function("() => document.querySelector('.shell-logterm .xterm-rows')?.textContent.includes('the gate, try 1')", timeout=WAIT_MS)
        text = rows(pg)
        assert "key=••••" in text and "called with ••••" in text                                                                      # a masked value, as the host sent it
        assert "prompt line 3" not in text and "31 lines of what the session was told" in text                                        # a round's prompt is not drawn
        assert pg.locator(".shell-logterm .xterm-helper-textarea").evaluate("e => e.readOnly || e.disabled || e.hasAttribute('readonly')")      # read only: nothing typed reaches it
        pg.wait_for_function("() => document.querySelector('.shell-logterm .xterm-rows').textContent.includes('test_case_2 PASSED')", timeout=15000)       # its tail grows while the task runs
        assert host.ticks >= 3 and any(n == "ideas.task_log" for n, _ in host.log)
        steps = pg.locator(".shell-task__steps .table-steps")                                                                         # its steps (§207) over it
        assert steps.locator(".table-steps__item").count() == 3 and steps.locator(".is-now").inner_text().strip() == "make the seat survive a reconnect"
        box = pg.locator(".shell-task").bounding_box()
        assert steps.bounding_box()["y"] < pg.locator(".shell-logterm__screen").bounding_box()["y"] and box["width"] > 0
        head = pg.locator(".shell-seat")                                                                                              # the header: the seat's head, its tier, its tool, the edit mark
        assert head.locator(".ork-race").count() == 1 and head.locator("[data-tool='claude']").count() == 1 and "Claude" in head.inner_text()
        assert head.get_by_role("button", name="Edit its leader's inventory").count() == 1
        shot(pg, "i1-running-task-log.png")
        head.get_by_role("button", name="Edit its leader's inventory").click()                                                        # the edit mark opens the leader's inventory
        pg.wait_for_function("() => import('/static/js/frame/state.js').then((m) => !!m.inventory.value && m.over.value === null)", timeout=WAIT_MS)
        assert pg.evaluate("() => import('/static/js/frame/state.js').then((m) => m.inventory.value)")
    finally:
        ctx.close()
    assert not errors, "\n".join(errors)


def test_a_task_run_in_the_persons_own_ai_tool_says_so_instead_of_a_log(gui):
    host = LogHost()
    host.own = True
    pg, ctx, errors = open_log(gui, host)
    try:
        pg.locator("[data-own-tool]").wait_for(timeout=WAIT_MS)
        assert "run in your own AI tool" in pg.locator("[data-own-tool]").inner_text() and pg.locator(".shell-logterm .xterm").count() == 0
        assert pg.locator(".shell-seat").count() == 1                                                                                 # its header stays
    finally:
        ctx.close()
    assert not errors, "\n".join(errors)
