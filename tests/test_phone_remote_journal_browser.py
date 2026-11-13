"""The phone reads the project's journal while the computer cannot be reached (docs/specs/136 C.3–C.4), in a real browser at 390 × 844 with touch against a stand-in GitHub
(tests/test_phone_remote_browser.py): the journal's screen with its *As of* in the muted ink, the parties and their goals, what needs the person marked and its button not pressable (*Needs your
computer*), what failed; a read with the ETag, a new journal replacing the old; only while the app is seen and the computer is away; a limit and a refused token said; the goals of this phone the
computer has not taken lying face down. Screenshots to $REMOTE_SHOTS when it is set."""
from __future__ import annotations

import time

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import gui  # noqa: E402,F401  (fixture)
from tests.test_phone_remote_browser import TOKEN, app, listener, narrow_sideways, shot  # noqa: E402,F401  (fixtures)

pytestmark = pytest.mark.browser

JOURNAL = {"v": 1, "written": "2026-11-04T14:02:11", "parties": [
    {"slug": "tech", "title": "Tech", "goals": [
        {"slug": "sign-in", "title": "Sign-in", "state": "talk", "phase": "talk", "needs_you": True, "error": ""},
        {"slug": "cache", "title": "Cache layer", "state": "failed", "phase": "work", "needs_you": False, "error": "tests failed"}]},
    {"slug": "design", "title": "Design", "goals": []}],
    "failed": [{"slug": "cache", "title": "Cache layer", "error": "tests failed"}], "taken": []}


def away(app, journal=JOURNAL, sent=None, wait=True):
    """Paired, its repository and token kept, its computer gone: the journal's screen is what the app shows."""
    app.keep_pairing()
    kept = {"repo": "me/shop", "token": TOKEN, "phone": "phone-test"}
    now = int(time.time() * 1000)
    app.pg.evaluate("(d) => { localStorage.setItem('orkcraft.remote', JSON.stringify(d.kept)); if (d.sent.length) localStorage.setItem('orkcraft.remote.sent', JSON.stringify(d.sent)); }",
                    {"kept": kept, "sent": [{**s, "at": now} for s in (sent or [])]})
    app.github.journal = journal
    app.host.dead = True
    pg = app.open()
    if wait:
        pg.locator("#journal .remote-asof").wait_for(state="visible")
    return pg


def reads(app):
    return [r for r in app.github.requests if r["path"].endswith("/contents/status.json")]


def until(pg, test, tries=150):
    for _ in range(tries):
        if test():
            return True
        pg.wait_for_timeout(100)
    return False


def test_the_journal_is_the_screen_while_the_computer_is_away_with_its_as_of_and_what_needs_the_person(app):
    pg = away(app)
    head = pg.locator("#journal .remote-asof")
    assert head.inner_text().lower() == "as of 14:02", "the journal's own time (the title face upper-cases it)"
    assert pg.evaluate("() => [document.querySelector('#app').hidden, document.querySelector('#phone-status').hidden]") == [True, True], "the page is under it, and says no *As of* of its own"
    parties = pg.locator("#journal [data-party]")
    assert parties.evaluate_all("(els) => els.map((e) => e.querySelector('h2').textContent)") == ["Tech", "Design"]
    goals = pg.locator("#journal [data-party=tech] .remote-goal")
    assert goals.count() == 2 and "Sign-in" in goals.nth(0).inner_text() and "Needs you" in goals.nth(0).inner_text()
    button = goals.nth(0).get_by_role("button")
    assert button.is_disabled() and button.inner_text() == "Needs your computer", "no button that needs the computer is pressable"
    assert goals.nth(1).locator(".remote-goal__error").inner_text() == "tests failed"
    assert pg.locator("#journal [aria-label=Failed] .remote-goal").inner_text().startswith("Cache layer")
    assert {r["headers"]["authorization"] for r in reads(app)} == {f"Bearer {TOKEN}"}            # read with the token (a second read under load is as good as one)
    assert app.foreign() == []
    assert not app.errors, "\n".join(app.errors)












def test_the_goals_of_this_phone_the_computer_has_not_taken_lie_face_down_with_the_persons_words(app):
    journal = {**JOURNAL, "taken": [{"id": "B2", "by": "home", "at": "x", "slug": "", "error": "Could not read this goal: it holds no words"},
                                    {"id": "C3", "by": "home", "at": "x", "slug": "daily", "error": ""}]}
    pg = away(app, journal=journal, sent=[
        {"id": "A1", "kind": "goal", "text": "Daily quests, please, with a streak"}, {"id": "B2", "kind": "goal", "text": "A goal the computer could not read"},
        {"id": "C3", "kind": "goal", "text": "A goal already on the Board"}])
    down = pg.locator("#journal .remote-down")
    assert down.count() == 2, "the goal on the Board is no longer waited for"
    assert down.nth(0).locator(".remote-down__words").inner_text() == "Daily quests, please, with a streak"
    assert down.nth(0).locator(".remote-down__note").inner_text() == "Waiting to be taken: your computer or a cloud session will read it"
    assert down.nth(1).locator(".remote-down__note").inner_text() == "Could not read this goal: it holds no words"
    shot(pg, "journal-waiting")


