"""Spec 83 B on the desktop (docs/specs/83-one-field-and-the-night-asked.md §1, §3, §4; decisions §100), in a real browser at 1 440 × 900 against the one window's stub host:
New goal by a type is one field, *The goal* (no *Its title*, no *What it is for*), its text sent as it stands; the first Low goal asks *Low work may run at night?* once
(*Yes, at night* / *No, by day*) and sends `ideas.night_allow`; the line under Priority says *runs tonight* or *runs after the other priorities*; closing with words in it sends
`hold`, never `night`; Settings has the switch (unset: off, *not asked yet*); *Tonight* on a pitch asks first and makes it Low, and is not drawn after *No, by day*."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_goal_types_desktop_browser import TypesHost, _form  # noqa: E402
from tests.test_ideation_desktop_browser import PARTY, IdeationHost  # noqa: E402
from tests.test_shell_browser import StubHost, _calls, _new_goal, _open, _sent, _show_goal, adds  # noqa: E402

pytestmark = pytest.mark.browser

QUESTION = "Low work may run at night?"
LINE = "Low goals then run between 01:00 and 07:00, on what is left of the window; you can change it in Settings"


class NotAsked(StubHost):
    """The Board has not been asked about the night (`night_low` null)."""

    def __init__(self):
        super().__init__()
        self.night_low = None


class NotAskedTypes(TypesHost):
    def __init__(self):
        super().__init__()
        self.night_low = None


class NotAskedIdeation(IdeationHost):
    def __init__(self):
        super().__init__()
        self.night_low = None


@pytest.fixture
def asked(gui):
    pg, host, errors = _open(gui, host=NotAsked())
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _ask(pg):
    return pg.get_by_role("dialog", name=QUESTION)


def _low_goal(pg, text, priority="low"):
    dlg = _new_goal(pg)
    dlg.get_by_label("Your goal").fill(text)
    dlg.get_by_label("Priority", exact=True).select_option(priority)
    return dlg


def test_the_first_low_goal_asks_the_question_once_and_the_answer_is_sent(asked):
    pg, host = asked
    dlg = _low_goal(pg, "Dark mode please")
    assert "Low: runs after the other priorities." in dlg.locator('[data-night="priority"]').inner_text()
    dlg.get_by_role("button", name="Add the goal").click()
    q = _ask(pg)
    q.wait_for(timeout=WAIT_MS)
    assert adds(host)[-1] == {"text": "Dark mode please", "track": "ship-sync", "priority": "low"}          # the goal is added either way
    assert q.locator("[data-night=line]").inner_text() == LINE
    buttons = q.locator(".shell-modal__foot button").all_inner_texts()
    assert buttons == ["Yes, at night", "No, by day"] and q.get_by_role("button", name="Yes, at night").evaluate("e => e === document.activeElement")
    q.get_by_role("button", name="Yes, at night").click()
    assert _sent(pg, host, ("ideas.night_allow", {"allow": True}))
    q.wait_for(state="detached", timeout=WAIT_MS)
    dlg = _low_goal(pg, "Another low goal")                                                                  # never asked again
    assert "Low: runs tonight." in dlg.locator('[data-night="priority"]').inner_text()
    dlg.get_by_role("button", name="Add the goal").click()
    dlg.wait_for(state="detached", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert _ask(pg).count() == 0 and len([1 for n, _ in host.log if n == "ideas.night_allow"]) == 1


def test_no_by_day_is_sent_and_kept(asked):
    pg, host = asked
    _low_goal(pg, "Someday").get_by_role("button", name="Add the goal").click()
    _ask(pg).get_by_role("button", name="No, by day").click()
    assert _sent(pg, host, ("ideas.night_allow", {"allow": False}))
    dlg = _low_goal(pg, "Later")
    assert "Low: runs after the other priorities." in dlg.locator('[data-night="priority"]').inner_text()
    dlg.get_by_role("button", name="Add the goal").click()
    dlg.wait_for(state="detached", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert _ask(pg).count() == 0                                                                           # answered: not asked again


def test_a_normal_goal_asks_nothing_and_esc_on_the_question_answers_nothing(asked):
    pg, host = asked
    dlg = _low_goal(pg, "A normal goal", "normal")
    dlg.get_by_role("button", name="Add the goal").click()
    dlg.wait_for(state="detached", timeout=WAIT_MS)
    pg.wait_for_timeout(300)
    assert _ask(pg).count() == 0
    _low_goal(pg, "A low goal").get_by_role("button", name="Add the goal").click()
    _ask(pg).wait_for(timeout=WAIT_MS)
    pg.keyboard.press("Escape")
    _ask(pg).wait_for(state="detached", timeout=WAIT_MS)
    assert not [1 for n, _ in host.log if n == "ideas.night_allow"]
    _low_goal(pg, "A second low goal").get_by_role("button", name="Add the goal").click()
    _ask(pg).wait_for(timeout=WAIT_MS)                                                                     # not answered: asked the next time


def test_closing_new_goal_with_words_sends_hold_never_night(asked):
    pg, host = asked
    dlg = _low_goal(pg, "Put back")
    dlg.get_by_role("button", name="Put it back").click()
    pg.wait_for_function("() => !document.querySelector('.shell-modal')", timeout=WAIT_MS)
    sent = _calls(pg, host, "ideas.add")[-1]
    assert sent["hold"] is True and "night" not in sent and sent["text"] == "Put back"
    assert _ask(pg).count() == 0                                                                           # put back, not added: no question
    assert dlg.get_by_role("button", name="Put it back").count() == 0


def test_put_it_back_says_what_it_does(asked):
    pg, _ = asked
    dlg = _new_goal(pg)
    assert dlg.get_by_role("button", name="Put it back").get_attribute("title") == "Keep it on the party, not started"
    assert "or tonight when its priority is Low" not in (dlg.get_by_role("button", name="Add the goal").get_attribute("title") or "")


def test_settings_has_the_switch_unset_is_off_and_not_asked_yet(asked):
    pg, host = asked
    pg.get_by_role("button", name="Settings").click()
    dlg = pg.get_by_role("dialog", name="Settings")
    box_ = dlg.get_by_role("checkbox", name="Low work may run at night")
    assert not box_.is_checked()
    hint = dlg.locator("[data-settings=night-low-hint]")
    assert hint.inner_text() == "and the leaders re-read goals and propose new ones then · not asked yet"
    dlg.get_by_text("Low work may run at night").click()
    assert _sent(pg, host, ("ideas.night_allow", {"allow": True}))
    dlg.locator("[data-settings=night-low-hint]:not(:has-text('not asked yet'))").wait_for(timeout=WAIT_MS)
    assert box_.is_checked()
    dlg.get_by_text("Low work may run at night").click()
    assert _sent(pg, host, ("ideas.night_allow", {"allow": False}))
    dlg.locator("[data-settings=night-low] input:not(:checked)").wait_for(state="attached", timeout=WAIT_MS)


def test_a_typed_goal_is_one_field_its_text_sent_as_it_stands(gui):
    pg, host, errors = _open(gui, host=NotAskedTypes(), ready=".arena-phead")
    try:
        pg.locator(".arena[data-goal=passkey]").wait_for(timeout=WAIT_MS)
        dialog = _form(pg, "New icon")
        field = dialog.get_by_label("The goal", exact=True)
        assert field.evaluate("e => e.tagName") == "TEXTAREA" and dialog.get_by_label("Its title").count() == 0 and dialog.get_by_label("What it is for").count() == 0
        assert " ".join(dialog.locator(".shell-field > .ok-font-label").first.text_content().split()) == "The goal its first line is its title"
        field.fill("A sync icon\n\nFor the tab bar.")
        dialog.get_by_label("Priority", exact=True).select_option("low")
        assert "Low: runs after the other priorities." in dialog.locator('[data-night="priority"]').inner_text()
        dialog.get_by_role("button", name="Add the goal").click()
        assert _calls(pg, host, "ideas.add")[-1]["text"] == "A sync icon\n\nFor the tab bar."
        _ask(pg).wait_for(timeout=WAIT_MS)                                                                 # a typed Low goal asks too
        _ask(pg).get_by_role("button", name="Yes, at night").click()
        assert _sent(pg, host, ("ideas.night_allow", {"allow": True}))
        dialog = _form(pg, "New icon")                                                                    # the line has the word now
        dialog.get_by_label("Priority", exact=True).select_option("low")
        assert "Low: runs tonight." in dialog.locator('[data-night="priority"]').inner_text()
    finally:
        pg.close()
    assert not errors, "\n".join(errors)


def test_tonight_on_a_pitch_asks_first_makes_it_low_and_is_gone_after_no(gui):
    pg, host, errors = _open(gui, host=NotAskedIdeation(), ready=".arena-phead")
    try:
        _show_goal(pg, PARTY)

        def pitch(text):
            pg.locator(".arena-left__proj").get_by_role("button", name="New goal").click()
            dlg = pg.get_by_role("dialog", name="New goal")
            dlg.wait_for(timeout=WAIT_MS)
            dlg.get_by_label("What is the pitch?").fill(text)
            return dlg
        pitch("Offline notes").get_by_role("button", name="Tonight").click()
        _ask(pg).wait_for(timeout=WAIT_MS)
        assert not [1 for n, _ in host.log if n == "ideas.add" and _.get("night")]                          # asked first: nothing is added yet
        _ask(pg).get_by_role("button", name="Yes, at night").click()
        got = _calls(pg, host, "ideas.add")[-1]
        assert got["night"] is True and got["priority"] == "low" and got["text"] == "Offline notes"
        host.night_low = None
        host.bump({})
        pitch("Share by link").get_by_role("button", name="Tonight").click()
        _ask(pg).get_by_role("button", name="No, by day").click()
        got = _calls(pg, host, "ideas.add", at_least=2)[-1]
        assert got["hold"] is True and "night" not in got and got["text"] == "Share by link"               # kept, not lost
        assert _sent(pg, host, ("ideas.night_allow", {"allow": False}))
        dlg = pitch("A third")
        assert [b.inner_text() for b in dlg.locator(".shell-modal__foot button").all()] == ["Hold", "Judge now"]      # Tonight is not drawn
    finally:
        pg.close()
    assert not errors, "\n".join(errors)
