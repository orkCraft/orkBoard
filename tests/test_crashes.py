"""Usage stats and crash reports in Orkboard (docs/specs/41-orkget.md §7): orkGet's copy bound to Orkboard's profile,
one answer per machine (`orkboard usage …` from the terminal), `app_opened` and `app_closed` only, and the page's own
errors reported. Nothing leaves the machine here: what would be sent is caught."""
from __future__ import annotations

import json
import sys

import pytest

from orkboard import settings
from orkboard.core import usage
from orkboard.orkget import crashes as copy_crashes


@pytest.fixture
def sent(monkeypatch):
    """Usage stats and crash reports on, and what they would send kept here instead."""
    monkeypatch.delenv("ORKCRAFT_NO_USAGE", raising=False)
    monkeypatch.delenv("CI", raising=False)
    out: list[tuple[str, dict]] = []
    keep = lambda url, data: out.append((url, json.loads(data)))   # noqa: E731
    monkeypatch.setattr("orkboard.orkget.usage._post", keep)
    monkeypatch.setattr(copy_crashes, "_post", keep)
    return out


def _share(yes: bool) -> None:
    """The machine's one answer, as `orkboard usage on|off` gives it (gui/board_cli.py)."""
    machine = settings.load()
    usage.share(machine, yes)
    settings.save(machine)


def test_nothing_is_sent_before_a_yes(fake_repo, sent):
    from orkboard.gui.board_host import Orkboard
    host = Orkboard(fake_repo)
    assert "usage_ask" not in host.snapshot() and "usage.share" not in host.commands      # the page asks nothing: the terminal answers
    host.opened()
    host.close()
    assert sent == []


def test_a_yes_says_hello_as_orkboard_and_a_close_says_goodbye(fake_repo, sent):
    from orkboard.gui.board_host import Orkboard
    _share(True)
    assert settings.load().usage is True and len(settings.load().install_id) == 32      # one answer for the machine
    host = Orkboard(fake_repo)
    host.opened()
    host.close()
    events = [e for url, body in sent if url.endswith("/v1/events") for e in body["events"]]
    assert [e["event"] for e in events] == ["app_opened", "app_closed"]
    body = next(body for url, body in sent if url.endswith("/v1/events"))
    assert body["product"] == "orkboard" and body["install_id"] == settings.load().install_id
    sessions = [body for url, body in sent if url.endswith("/v1/crash")]
    assert sessions and all(b["product"] == "orkboard" for b in sessions)


def test_a_no_forgets_the_id_and_sends_nothing(fake_repo, sent):
    from orkboard.gui.board_host import Orkboard
    _share(True)
    _share(False)
    host = Orkboard(fake_repo)
    sent.clear()
    host.opened()
    host.close()
    assert sent == [] and settings.load().install_id == "" and settings.load().usage is False


def test_the_host_puts_the_hooks_back_when_it_closes(fake_repo):
    from orkboard.gui.board_host import Orkboard
    before = sys.excepthook
    host = Orkboard(fake_repo)
    assert sys.excepthook is not before
    host.close()
    assert sys.excepthook is before


# -- the terminal -------------------------------------------------------------------------------------------------

def test_orkboard_usage_on_keeps_the_installers_id(capsys):
    from orkboard.gui.board_host import main
    assert main(["usage", "on", "--id", "a" * 32]) == 0
    assert settings.load().usage is True and settings.load().install_id == "a" * 32
    assert "install id: " + "a" * 32 in capsys.readouterr().out
    assert main(["usage", "off"]) == 0 and settings.load().install_id == ""
    assert main(["usage", "on", "--id", "nope"]) == 2

