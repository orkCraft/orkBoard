"""A stub host of the Orkmaster's goals in every state (`ColumnHost`), the snapshot's back of a goal (`back`) and its wait (`ripe`), and `open_column`, which opens the hand on it:
what the tests of the column, the runes, the small cards and the passed questions share."""
from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS  # noqa: E402
from tests.test_hand_desktop_browser import HandHost, head, node, open_hand, task  # noqa: E402


def ripe(left, seconds=240, held=False, by=""):
    return {"left_s": left, "seconds": seconds, "risk": "low", "priority": "high", "held": held, "by": by or ("person" if held else ""), "why": ""}


def back(**more):
    return {"route": [], "cost": None, "offer": [], "short": False, "heard": [], "stances": [], "round": 1, "ripe": None, **more}


class ColumnHost(HandHost):
    """A project of four parties and goals in every state of the column: four in analysis (one being read, one in Talk, two raw), two agreed (their waits running), one held, one put off to the night, one at work with a task running, one done."""

    def __init__(self):
        super().__init__(bare=True)
        timer = node("timer", "tech", "Round timer on phones", "table", state="ready", agreed=True, element="ice", back=back(ripe=ripe(120)))
        scoring = node("scoring", "tech", "Tidy the scoring module", "table", state="ready", agreed=True, element="dust", back=back(ripe=ripe(480)))
        held = node("held", "design", "Lobby in Polish", "table", state="decided", element="void", back=back(ripe=ripe(0, held=True)))
        late = node("late", "tech", "Rename a room after it is made", "table", state="plan", element="lava", start_at="night", waits={"kind": "night", "ref": "", "title": "", "until": ""})
        work = node("music", "design", "Music in the lobby", "table", state="working", element="meadow", stage="implementation", tasks=[task("m1", "Make the loop", "running", head=head("dryad", "design"))])
        self.nodes = [
            node("reading", "tech", "Players see who answered first", "table", state="reading", element="lava"),
            node("talk", "design", "A sound when the round ends", "table", state="talk", element="void", back=back()),
            node("raw1", "tech", "Kick a player from the lobby", "deck", state="raw", element="dust"),
            node("raw2", "design", "Host can skip a round", "deck", state="raw", element="meadow"),
            node("raw3", "tech", "Mute a noisy player", "deck", state="raw", element="ice"),
            timer, scoring, held, late, work,
            node("old", "tech", "An old goal", "history", state="done", seen="2026-10-18T10:00:00"),
        ]

    def handle(self, name, a):
        if name == "ideas.confirm":
            self.log.append((name, a))
            return self.bump({"ok": True})
        return super().handle(name, a)


def open_column(gui, width="wide", host=None):
    pg, host, log = open_hand(gui, host=host or ColumnHost(), width=width)
    pg.wait_for_selector(".hand :is(.hand-plus, [data-blank-deck])", timeout=WAIT_MS)
    return pg, host, log
