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
from orkboard.realm import goal_branch, ideas, spec_sections
from tests import mock_kit

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


def test_the_recording_holds_what_the_battle_and_the_gate_ask_when_they_open_as_the_host_answered_them():
    got = {r["name"]: r for r in recorded()}
    assert {"ideas.battle", "ideas.gate_guards"} <= set(got) and all(got[n]["ok"] for n in ("ideas.battle", "ideas.gate_guards"))
    assert got["ideas.battle"]["result"]["against"] == [] and got["ideas.gate_guards"]["result"]["failing"] == []      # this Board keeps no conflict and no red gate


def shape(x):
    """The keys of an answer and of its first entry of every list, never the values."""
    if isinstance(x, dict):
        return {k: shape(v) for k, v in sorted(x.items())}
    if isinstance(x, list):
        return [shape(x[0])] if x and isinstance(x[0], dict) else []      # a list of words says nothing of its entries' keys
    return None


@pytest.fixture
def fixture_board(host, fake_repo):
    """D's and F's fixture Board (tests/test_ideas_battle.py): a goal whose decision keeps a conflict with §2, a red gate on its branch."""
    root = host.ideas.root()
    ideas.add_track(root, "Tech")
    (root / ideas.IDEAS).mkdir(parents=True, exist_ok=True)
    (root / ideas.IDEAS / "goal.md").write_text("---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: talk\nschema: 3\n---\n# goal\n\n## Gist\nA goal.\n", encoding="utf-8")
    ideas.save_state(host.ideas.state_dir, "goal", state="decided")
    way = spec_sections.record(host.ideas.state_dir, "goal")
    way["decision"] = {"number": 9, "title": "New", "text": "x", "conflicts": [{"number": 2, "point": "It goes against the old card", "answer": ""}]}
    spec_sections.save_record(host.ideas.state_dir, "goal", way)
    for rel, text in (("docs/decisions.md", "# Decisions\n\n## 2. Second\nIt stands.\n\n## 3. Third\nStands.\n"), ("llm-wiki/general/pages/ideas/rests.md", "It rests on §2.\n"),
                      ("tests/test_red.py", '"""Guards decisions §2."""\n\ndef test_a():\n    assert 0\n'), ("tests/test_bare.py", '"""Nothing named."""\n\ndef test_c():\n    assert 0\n'),
                      ("tests/test_ok.py", '"""Guards decisions §3."""\n\ndef test_d():\n    pass\n')):
        f = fake_repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    goal_branch.update(host.ideas.state_dir, "goal", branch="goal/goal", failing=["tests/test_red.py::test_a", "tests/test_bare.py::test_c"], files=["tests/test_red.py", "tests/test_bare.py", "tests/test_ok.py"])
    return host


def test_the_battle_and_the_gate_laid_for_the_tests_have_the_keys_the_host_answers_with(fixture_board):
    """`mock_kit.lay_battle` and `lay_gate` lay answers with the shapes of the real commands' (a ?mock=1 test never passes on a contract the host no longer answers); every text an example."""
    data = mock_kit.recording()
    slug = mock_kit.lay_battle(data)
    mock_kit.lay_gate(data)
    real_battle, real_gate = fixture_board.command("ideas.battle", {"idea": "goal"}), fixture_board.command("ideas.gate_guards", {"idea": "goal"})
    laid_battle, laid_gate = mock_kit.reply(data, "ideas.battle")["result"], mock_kit.reply(data, "ideas.gate_guards")["result"]
    assert shape(laid_battle) == shape(real_battle) and laid_battle["idea"] == slug and len(laid_battle["against"]) == 3
    assert shape(laid_gate) == shape(real_gate) and shape(laid_gate["failing"]) == shape(real_gate["failing"])
    green = next(r for r in data["replies"] if r["name"] == "ideas.gate_guards" and r["args"] == {"idea": mock_kit.CHRONICLE})["result"]
    assert green["failing"] == [] and green["way"] == "main" and set(green) == set(real_gate)
    rows = [r for r in mock_kit.reply(data, "ideas.board")["result"]["needs_you"] if r["kind"] == "conflict"]
    from orkboard.realm import board_map
    real_rows = board_map.conflict_rows(spec_sections.record(fixture_board.ideas.state_dir, "goal")["decision"], lambda: (Path(fixture_board.repo_root) / "docs" / "decisions.md").read_text(encoding="utf-8"))
    assert real_rows and {k for k in real_rows[0]} <= set(rows[0]) and len(rows) == 3
    texts = [a["title"] for a in laid_battle["against"]] + [f["title"] for f in laid_gate["failing"]] + [r["point"] for r in rows]
    assert all(t.endswith(mock_kit.EXAMPLE) for t in texts), texts
