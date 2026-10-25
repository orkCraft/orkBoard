"""Spec 80 B on the desktop (docs/specs/80-a-party-removed.md §0, §3, §4; decisions §97), in a real browser at 1 440 × 900 against the one window's stub host:
*Remove party* sits at the foot of Edit the party, in the danger colour, never for General; the question has *Move its k goals to General and remove* (the default,
first, focused), *Remove the party and its k goals* (danger) and *Cancel*; an empty party asks *It has no goals* with *Remove* / *Cancel*; the move sends
`ideas.track_drop` with `goals: "move"` and the toast; a refusal is said in the question, which stays; the open party removed falls back to the first; Esc cancels."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui  # noqa: E402,F401  (fixture)
from tests.test_arena_desktop_browser import ArenaHost  # noqa: E402
from tests.test_shell_browser import _calls, _open, _parties  # noqa: E402

pytestmark = pytest.mark.browser

READY = ".arena[data-goal=passkey]"


class RemoveHost(ArenaHost):
    """The passkey party (many goals), Pricing (one goal), Weekly report email (none); `track_drop` removes a party, or refuses with `refuse[slug]`."""

    def __init__(self):
        super().__init__()
        self.refuse: dict[str, str] = {}

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            if m["name"] == "ideas.track_drop":
                self.log.append((m["name"], m["args"]))
                slug, how = m["args"]["slug"], m["args"].get("goals")
                if slug in self.refuse:
                    ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": False, "error": self.refuse[slug]}))
                    return
                title = self.goals.pop(slug)["title"]
                mine = [s for s, i in self.ideas.items() if i["track"] == slug]
                self.nodes = [n for n in self.nodes if n["goal"] != slug]
                for s in mine:
                    if how == "drop":
                        del self.ideas[s]
                    else:
                        self.ideas[s]["track"] = "general"
                got = {"ok": True, "moved": 0 if how == "drop" else len(mine), "dropped": len(mine) if how == "drop" else 0, "title": title}
                ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.bump(got)}))
                return
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
        ws.on_message(on_message)


@pytest.fixture
def removed(gui):
    pg, host, errors = _open(gui, host=RemoveHost(), ready=READY)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def _edit(pg, slug="passkey"):
    """Edit the party of a party: its heading pressed when it is not the open one, then the line's button."""
    if not pg.locator(f'.arena[data-goal="{slug}"]').count():
        _parties(pg).locator(f'.arena-phead[data-goal="{slug}"]').click()
        pg.wait_for_selector(f'.arena[data-goal="{slug}"]', timeout=WAIT_MS)
    pg.get_by_role("button", name="Edit the party").first.click()
    return pg.get_by_role("dialog", name="Edit the party")


def _ask(pg, slug="passkey"):
    dlg = _edit(pg, slug)
    dlg.wait_for(timeout=WAIT_MS)
    dlg.get_by_role("button", name="Remove party").click()
    q = pg.locator('[role=dialog][aria-label^="Remove "]')
    q.wait_for(timeout=WAIT_MS)
    return q


def test_remove_party_is_at_the_foot_of_edit_the_party_in_the_danger_colour(removed):
    pg, _ = removed
    dlg = _edit(pg)
    dlg.wait_for(timeout=WAIT_MS)
    btn = dlg.get_by_role("button", name="Remove party")
    assert btn.count() == 1 and "danger" in btn.get_attribute("class").split()
    assert btn.evaluate("e => e.parentElement.classList.contains('shell-modal__foot')")
    assert btn.bounding_box()["x"] < dlg.get_by_role("button", name="Cancel").bounding_box()["x"]            # at the foot's start, away from Save party


def test_general_has_no_remove_party(removed):
    pg, _ = removed
    assert _parties(pg).locator('.arena-phead[data-goal="general"]').count() == 0                          # General has no heading of its own
    pg.evaluate("""() => import('/static/js/shell/modals.js').then((m) => m.openDialog('goal', {slug: 'general'}))""")
    pg.get_by_role("dialog", name="Edit the party").wait_for(timeout=WAIT_MS)
    assert pg.get_by_role("button", name="Remove party").count() == 0


def test_the_question_has_the_move_first_the_drop_in_danger_and_cancel(removed):
    pg, _ = removed
    q = _ask(pg)
    buttons = q.locator("button:not(.shell-modal__x)")
    names = [b.inner_text().strip() for b in buttons.all()]
    n = names[0].split("Move its ")[1].split(" goals")[0]
    assert names == [f"Move its {n} goals to General and remove", f"Remove the party and its {n} goals", "Cancel"] and int(n) > 1
    assert "primary" in buttons.nth(0).get_attribute("class") and "danger" in buttons.nth(1).get_attribute("class")
    assert buttons.nth(0).evaluate("e => e === document.activeElement")                                    # the default is the move
    assert q.get_by_role("heading").text_content() == "Remove Sign in with a passkey?"
    assert pg.get_by_role("dialog", name="Edit the party").count() == 0


def test_move_sends_track_drop_with_move_and_says_it_in_a_toast_and_the_party_is_gone(removed):
    pg, host = removed
    q = _ask(pg)
    q.get_by_role("button", name="Move its").click()
    assert _calls(pg, host, "ideas.track_drop")[-1] == {"slug": "passkey", "goals": "move"}
    pg.locator(".ok-toast", has_text="Sign in with a passkey removed: ").wait_for(timeout=WAIT_MS)
    assert "goals moved to General" in pg.locator(".ok-toast").first.inner_text()
    pg.wait_for_function("() => !document.querySelector('.arena-phead[data-goal=passkey]')", timeout=WAIT_MS)
    assert pg.get_by_role("dialog").count() == 0
    pg.wait_for_selector(".arena[data-goal=pricing]", timeout=WAIT_MS)                                    # the open party was removed: the first party shows


def test_drop_sends_goals_drop(removed):
    pg, host = removed
    q = _ask(pg, "pricing")
    assert "Move its 1 goal to General and remove" in q.inner_text()
    q.get_by_role("button", name="Remove the party and its 1 goal").click()
    assert _calls(pg, host, "ideas.track_drop")[-1] == {"slug": "pricing", "goals": "drop"}
    pg.locator(".ok-toast", has_text="Pricing page removed: 1 goal removed").wait_for(timeout=WAIT_MS)


def test_an_empty_party_asks_remove_or_cancel(removed):
    pg, host = removed
    q = _ask(pg, "weekly")
    assert "It has no goals" in q.inner_text()
    assert [b.inner_text().strip() for b in q.locator("button:not(.shell-modal__x)").all()] == ["Remove", "Cancel"]
    q.get_by_role("button", name="Remove", exact=True).click()
    assert _calls(pg, host, "ideas.track_drop")[-1] == {"slug": "weekly", "goals": "move"}
    pg.locator(".ok-toast", has_text="Weekly report email removed").wait_for(timeout=WAIT_MS)
    assert "to General" not in pg.locator(".ok-toast").first.inner_text()


@pytest.mark.parametrize("why", ["2 goals at work: stop them first", "That party is gone"])
def test_a_refusal_is_said_in_the_question_which_stays(removed, why):
    pg, host = removed
    host.refuse["passkey"] = why
    q = _ask(pg)
    q.get_by_role("button", name="Move its").click()
    q.get_by_role("alert").wait_for(timeout=WAIT_MS)
    assert q.get_by_role("alert").inner_text() == why and pg.locator(".ok-toast", has_text=why).count() == 0     # not a second voice
    assert pg.get_by_role("dialog").count() == 1 and pg.locator(".arena-phead[data-goal=passkey]").count() == 1    # still the one question, the party still there


def test_escape_cancels_and_sends_nothing(removed):
    pg, host = removed
    _ask(pg)
    pg.keyboard.press("Escape")
    pg.wait_for_function("() => !document.querySelector('[role=dialog]')", timeout=WAIT_MS)
    pg.wait_for_timeout(200)
    assert not [1 for n, _ in host.log if n == "ideas.track_drop"] and pg.locator(".arena-phead[data-goal=passkey]").count() == 1
