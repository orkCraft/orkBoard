"""Spec 45 part B on the desktop (docs/specs/45-sign-in.md §5, §8, "Tests → B"): in a real browser against a stub host that serves the
snapshot's `sign_in` and the three commands. A tool `needed` with `auto` is asked to sign in once when the person is at the page
(visible and focused), not while it is hidden or unfocused, on its next focus or press; one tool at a time; the toasts of a sign-in
that is open (in the browser, in a terminal, no terminal), done with what goes on, failed, and a browser that did not open; **Sign
in** on the first screen's Check row, on an error line and on the need; *waits: Claude Code's sign-in* on a row and a stop."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_shell_browser import StubHost, _calls, _sent  # noqa: E402

pytestmark = pytest.mark.browser

LINE = "Claude Code is not signed in, or its sign-in has expired. Sign in opens Claude Code's sign-in. In a terminal: claude, then /login."
# the page's focus is the test's to give or take: `document.hasFocus()` is what the page asks (spec 45 §5)
AT_PAGE = "window.__at = true; document.hasFocus = () => window.__at;"
AWAY = "window.__at = false; document.hasFocus = () => window.__at;"


def entry(harness="claude", tool="Claude Code", state="needed", by="browser", auto=True, **more):
    """One tool of the snapshot's `sign_in` (core/sign_ins.py)."""
    return {"harness": harness, "tool": tool, "mark": "✱", "state": state, "by": by, "auto": auto, "since": 1700000000.0, "where": "task",
            "why": "", "command": "", "waiting": 0, **more}


def _page(gui, host, init=AT_PAGE, **kw):
    """The page opened with the focus given (or taken) by `init`, the Board's first goal shown."""
    server, browser = gui
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    pg.add_init_script(init)
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url)
    pg.wait_for_selector(kw.get("ready", ".table-tab"), timeout=WAIT_MS)
    return pg, errors


def _toast(pg, text):
    t = pg.locator(".gui-toast", has_text=text)
    t.first.wait_for(timeout=WAIT_MS)
    return t.first


def _opened(host):
    return [a for n, a in host.log if n == "tools.sign_in"]


def test_a_tool_that_needs_a_sign_in_is_asked_to_open_it_once_when_the_page_is_visible_and_focused(gui):
    host = StubHost()
    host.sign_in = [entry()]
    pg, errors = _page(gui, host)
    try:
        assert _calls(pg, host, "tools.sign_in") == [{"harness": "claude", "auto": True}]
        toast = _toast(pg, "Sign in to Claude Code")                      # open, in the browser: a toast that stays, with Cancel
        assert "Its sign-in opened in your browser. Sign in there: the work that waits for it goes on by itself." in toast.inner_text()
        assert [b.inner_text() for b in toast.locator(".ork-btn").all()] == ["Cancel"]
        pg.wait_for_timeout(600)
        assert len(_opened(host)) == 1                                    # once
        toast.get_by_role("button", name="Cancel").click()
        assert _sent(pg, host, ("tools.sign_in_cancel", {"harness": "claude"}))
        pg.wait_for_timeout(600)
        assert len(_opened(host)) == 1                                    # a cancelled sign-in is not opened again by itself
    finally:
        pg.close()
    assert not errors, "\n".join(errors)














def test_a_sign_in_done_says_the_tool_is_signed_in_and_how_many_tasks_go_on(gui):
    host = StubHost()
    host.sign_in = [entry(state="open", auto=False, waiting=3)]
    pg, errors = _page(gui, host)
    try:
        _toast(pg, "Sign in to Claude Code")
        host.sign_in = []                                                 # signed in: the tool is no longer in the snapshot
        host.bump({})
        _toast(pg, "Claude Code is signed in. 3 tasks go on.")
        assert pg.locator(".gui-toast", has_text="Its sign-in opened in your browser").count() == 0       # the open one is gone
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_a_sign_in_that_did_not_finish_says_why_and_offers_sign_in_again_and_details(gui):
    host = StubHost()
    host.sign_in = [entry(state="open", auto=False)]
    pg, errors = _page(gui, host)
    try:
        _toast(pg, "Sign in to Claude Code")
        host.sign_in[0].update(state="failed", why="timeout")
        host.bump({})
        toast = _toast(pg, "Claude Code's sign-in did not finish.")
        assert [b.inner_text() for b in toast.locator(".ork-btn").all()] == ["Sign in again", "Details"]
        toast.get_by_role("button", name="Details").click()
        _toast(pg, "it took too long")
        host.sign_in[0].update(state="open")                              # again, and again it did not finish
        host.bump({})
        _toast(pg, "Sign in to Claude Code")
        host.sign_in[0].update(state="failed", why="refused")
        host.bump({})
        _toast(pg, "Claude Code's sign-in did not finish.").get_by_role("button", name="Sign in again").click()
        assert _calls(pg, host, "tools.sign_in") == [{"harness": "claude"}]                  # the person's own: not `auto`
    finally:
        pg.close()
    assert not errors, "\n".join(errors)






# -- Sign in beside every failure that a sign-in helps ---------------------------------------------------------------------------



# -- a goal or a task held by it ----------------------------------------------------------------------------------------------------



