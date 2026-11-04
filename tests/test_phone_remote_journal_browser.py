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
    muted = pg.evaluate("() => { const e = document.createElement('i'); e.style.color = 'var(--ork-ink-muted)'; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; }")
    assert head.evaluate("(e) => getComputedStyle(e).color") == muted, "in the muted ink"
    assert pg.evaluate("() => [document.querySelector('#app').hidden, document.querySelector('#phone-status').hidden]") == [True, True], "the page is under it, and says no *As of* of its own"
    parties = pg.locator("#journal [data-party]")
    assert parties.evaluate_all("(els) => els.map((e) => e.querySelector('h2').textContent)") == ["Tech", "Design"]
    goals = pg.locator("#journal [data-party=tech] .remote-goal")
    assert goals.count() == 2 and "Sign-in" in goals.nth(0).inner_text() and "Needs you" in goals.nth(0).inner_text()
    button = goals.nth(0).get_by_role("button")
    assert button.is_disabled() and button.inner_text() == "Needs your computer", "no button that needs the computer is pressable"
    assert goals.nth(1).locator(".remote-goal__error").inner_text() == "tests failed"
    assert pg.locator("#journal [aria-label=Failed] .remote-goal").inner_text().startswith("Cache layer")
    assert [r["headers"]["authorization"] for r in reads(app)] == [f"Bearer {TOKEN}"]
    assert app.foreign() == []
    narrow_sideways(pg)
    shot(pg, "journal")
    assert not app.errors, "\n".join(app.errors)


def test_a_read_with_nothing_new_carries_the_etag_and_a_new_journal_replaces_the_old(app):
    pg = away(app)
    pg.get_by_role("button", name="Try again").click()
    assert until(pg, lambda: len(reads(app)) >= 2)
    first, second = reads(app)[:2]
    assert "if-none-match" not in first["headers"] and second["headers"]["if-none-match"] == app.github.etag, "the second read asks with the ETag: a 304 costs nothing"
    app.github.journal = {**JOURNAL, "written": "2026-11-04T14:17:40", "failed": [], "parties": [
        {"slug": "tech", "title": "Tech", "goals": [{"slug": "sign-in", "title": "Sign-in", "state": "working", "phase": "work", "needs_you": False, "error": ""}]}]}
    app.github.etag = 'W/"2"'
    pg.get_by_role("button", name="Try again").click()
    pg.locator("#journal .remote-asof", has_text="14:17").wait_for()
    assert " ".join(pg.locator("#journal [data-party=tech] .remote-goal").inner_text().split()).startswith("Sign-in working")
    assert pg.locator("#journal [aria-label=Failed]").count() == 0


def test_it_reads_only_while_the_app_is_seen(app):
    pg = away(app)
    pg.evaluate("() => { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' }); }")
    before = len(reads(app))
    pg.get_by_role("button", name="Try again").click()
    pg.wait_for_timeout(1500)
    assert len(reads(app)) == before, "never in the background"
    pg.evaluate("() => { Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' }); document.dispatchEvent(new Event('visibilitychange')); }")
    assert until(pg, lambda: len(reads(app)) > before), "back on the screen it is read at once"


def test_while_the_computer_answers_the_journal_is_not_read_and_not_drawn(app):
    app.keep_pairing()
    app.pg.evaluate("(d) => localStorage.setItem('orkcraft.remote', JSON.stringify(d))", {"repo": "me/shop", "token": TOKEN, "phone": "phone-test"})
    app.github.journal = JOURNAL
    app.open()
    app.ready()
    app.pg.wait_for_timeout(2500)
    assert reads(app) == [], "on the same network the live Board is the truth"
    assert app.pg.locator("#journal .remote-asof").count() == 0 and app.pg.evaluate("() => document.querySelector('#app').hidden") is False


def test_a_limit_stops_the_reads_and_is_said_and_a_refused_token_is_said(app):
    until_s = int(time.time()) + 3600
    app.github.limit = until_s
    pg = away(app, wait=False)
    assert until(pg, lambda: len(reads(app)) == 1)
    pg.wait_for_timeout(1000)
    want = pg.evaluate("(s) => new Date(s * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })", until_s)
    assert pg.evaluate("() => orkboardPhone.remote.state().line") == f"GitHub asks us to wait till {want}"
    pg.evaluate("() => { document.dispatchEvent(new Event('visibilitychange')); }")
    pg.wait_for_timeout(800)
    assert len(reads(app)) == 1, "no more calls while GitHub asks us to wait"
    assert pg.locator("#journal .remote-asof").count() == 0 and pg.evaluate("() => document.querySelector('#app').hidden") is False, "no journal yet: the Board as last seen stays"


def test_a_refused_token_is_said_with_the_journal_that_was_read_before(app):
    pg = away(app)
    app.github.status = 401
    pg.get_by_role("button", name="Try again").click()
    pg.locator("#journal .remote-line.is-bad", has_text="The token was refused: give a new one in Settings").wait_for()
    assert pg.locator("#journal .remote-asof").inner_text().lower() == "as of 14:02", "what it knew stays, with its time"


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


def test_the_board_as_last_seen_can_be_asked_for(app):
    pg = away(app)
    pg.get_by_role("button", name="Show the Board as last seen").click()
    pg.locator("#journal").wait_for(state="hidden")
    assert pg.evaluate("() => document.querySelector('#app').hidden") is False
