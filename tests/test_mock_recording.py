"""Spec 171 G: js/mock/ is the browser tests' fixtures only, recorded from a real host. It answers the host's own command names and no other:
every name the recording holds (`static/mock/board.json`, tools/record_mock.py) is a command of the host's table (gui/board_host.py, with
gui/ideas.py's and gui/ideas_mats.py's), the recording holds the cards' three reads, js/mock/ holds no part of its own, and mocklink.js names no
command of its own. The contract is tested against itself: a name the host drops fails here, not in a browser test that still passes on the recording."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard

STATIC = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static"
RECORDING = STATIC / "mock" / "board.json"
MOCK = STATIC / "js" / "mock"
CARDS = {"ideas.turns", "ideas.verdicts", "ideas.tables"}


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def recorded() -> list[dict]:
    return json.loads(RECORDING.read_text(encoding="utf-8"))["replies"]


def test_the_recording_answers_only_the_hosts_own_command_names(host):
    names = {r["name"] for r in recorded()}
    assert names and not names - set(host.commands), sorted(names - set(host.commands))


def test_the_recording_holds_the_cards_reads_and_each_was_answered():
    got = {r["name"]: r for r in recorded()}
    assert CARDS <= set(got) and all(got[n]["ok"] for n in CARDS)
    assert set(got["ideas.turns"]["result"]) == {"turns"} and isinstance(got["ideas.verdicts"]["result"], dict)
    assert {"tech", "product"} <= set(got["ideas.tables"]["result"])


def test_js_mock_holds_the_link_and_the_plate_only():
    assert sorted(p.name for p in MOCK.rglob("*") if p.is_file()) == ["mocklink.js", "plate.css", "plate.js"]
    assert not (STATIC / "mock" / "tables.json").exists()


def test_mocklink_names_no_command_of_its_own_and_answers_no_proposed_part():
    code = "\n".join(re.sub(r"^\s*//.*$", "", ln) for ln in (MOCK / "mocklink.js").read_text(encoding="utf-8").splitlines())
    assert not re.search(r"[\"'`](?:ideas|first_open|tools|projects|town)\.\w+[\"'`]", code)
    assert "proposed" not in code and "parts/" not in code
