"""The + card and the hand's answers through the project's remote (docs/specs/136 C.5–C.6, spec 137 C), in a real browser at 390 × 844 with touch against a stand-in GitHub
(tests/test_phone_remote_browser.py): with the computer gone and the repository set, Send writes `inbox/<device>/<id>.json` on orkboard/inbox (the branch made on the first goal) and says it;
an answer to a card of the hand goes as `<id>.answer.json`; with no network the goal waits in the app's storage (*Waits for the network*) and is written when the network is back; with no
repository set the phone says once *Set your repository in Settings…*. Screenshots to $REMOTE_SHOTS when it is set."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import gui  # noqa: E402,F401  (fixture)
from tests.test_phone_remote_browser import TOKEN, app, listener, narrow_sideways, shot  # noqa: E402,F401  (fixtures)

pytestmark = pytest.mark.browser

SENT = "Sent through your repository: your computer or a cloud session will take it"


def seated(app, set_repo=True):
    """The page up with the computer answering, then the computer goes: the page stays as it was, offline."""
    app.keep_pairing()
    if set_repo:
        app.pg.evaluate("(d) => localStorage.setItem('orkcraft.remote', JSON.stringify(d))", {"repo": "me/shop", "token": TOKEN, "phone": "phone-test"})
    pg = app.open()
    app.ready()
    app.host.dead = True
    app.host.ws.close(code=1001, reason="gone")
    pg.wait_for_function("() => import('./page/js/link.js').then((l) => !l.online.value && l.unreached.value)")
    return pg


def toasts(pg):
    return pg.evaluate("() => import('./page/js/link.js').then((l) => l.toasts.value.map((t) => t.message))")


def send_goal(pg, words):
    pg.locator("button.up-round").click()                                    # the round button's fan: New goal and Play
    pg.get_by_role("button", name="New goal", exact=True).click()
    field = pg.get_by_role("textbox", name="Write a goal")
    field.fill(words)
    field.press("Enter")                                                     # Enter sends (shift+Enter is a new line)


def wait_for(pg, test, tries=150):
    for _ in range(tries):
        if test():
            return True
        pg.wait_for_timeout(100)
    return False


def test_the_plus_card_writes_the_goal_into_the_inbox_when_the_computer_is_away(app):
    pg = seated(app)
    send_goal(pg, "Daily quests: a streak for each day")
    assert wait_for(pg, lambda: any(p.endswith(".json") for p in app.github.files))
    path = next(p for p in app.github.files if p.endswith(".json"))
    goal = json.loads(app.github.files[path])
    assert path == f"inbox/dev-1/{goal['id']}.json" and goal["device"] == "dev-1", "the pairing's id is the device"
    assert goal["v"] == 1 and goal["text"] == "Daily quests: a streak for each day" and goal["marks"] == [] and goal["photos"] == []
    assert app.github.branch is True
    assert SENT in toasts(pg)
    assert not [a for n, a in app.host.log if n == "ideas.add"], "nothing went to the computer"
    assert pg.get_by_role("textbox", name="Write a goal").count() == 0, "the field turned back"
    narrow_sideways(pg)
    shot(pg, "plus-sent")


def test_with_no_network_the_goal_waits_in_the_storage_and_goes_when_the_network_is_back(app):
    pg = seated(app)
    app.github.down = True
    pg.evaluate("() => { window.__online = Object.getOwnPropertyDescriptor(Navigator.prototype, 'onLine'); Object.defineProperty(Navigator.prototype, 'onLine', { configurable: true, get: () => false }); }")
    send_goal(pg, "Written on the train")
    assert wait_for(pg, lambda: "Waits for the network" in toasts(pg))
    kept = json.loads(pg.evaluate("() => localStorage.getItem('orkcraft.remote.outbox')"))
    assert [(x["kind"], x["text"]) for x in kept] == [("goal", "Written on the train")] and not app.github.files
    app.github.down = False
    pg.evaluate("() => { Object.defineProperty(Navigator.prototype, 'onLine', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); }")
    assert wait_for(pg, lambda: any(p.endswith(".json") for p in app.github.files)), "sent when the network came back"
    assert wait_for(pg, lambda: json.loads(pg.evaluate("() => localStorage.getItem('orkcraft.remote.outbox')")) == [])


