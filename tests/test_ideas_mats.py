"""Spec 171 C (`gui/ideas_mats.py`: ideas.verdicts, ideas.tables; `realm/code_layers.py`): the verdicts and the leaders' tables, read only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import board_turns, code_layers, ideas, opportunity_tree, page_talk

REPO = Path(__file__).resolve().parents[1]
TALK = "### Talk\n- verdict: doubt — one writer\n- stance: fine\n- for: simple\n- against: a second caller"
PAGE = "---\nowner: board\nkind: idea\ntrack: tech\norder: 1\nphase: talk\nroute: product, tech\nschema: 3\n---\n# Goal\n\n## Gist\nA goal.\n\n## Product\n{p}\n\n## Tech\n{t}\n"


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def lay(host, page: str) -> None:
    root = host.ideas.root()
    ideas.add_track(root, "Product")
    ideas.add_track(root, "Tech")
    folder = root / ideas.IDEAS
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "goal.md").write_text(page, encoding="utf-8")


def test_a_token_for_each_leader_of_the_route_that_has_said_its_talk(host):
    lay(host, PAGE.format(p="No talk yet.", t=TALK))
    got = host.command("ideas.verdicts", {})
    assert list(got) == ["goal"] and [v["leader"] for v in got["goal"]] == ["tech"]
    assert got["goal"][0]["verdict"] == "doubt" and got["goal"][0]["why"] == "one writer"
    assert {"stance", "for", "against", "instead", "assumes"} <= set(got["goal"][0])


def test_a_goal_whose_leaders_have_said_nothing_has_no_tokens(host):
    lay(host, PAGE.format(p="x", t="y"))
    assert host.command("ideas.verdicts", {}) == {}


def test_tables_with_no_tree_lay_the_zones_empty_saying_who_fills_them(host):
    lay(host, PAGE.format(p="x", t="y"))
    got = host.command("ideas.tables", {})
    jt = got["product"]["jtbd"]
    assert jt["job"] is None and jt["jobs"] == [] and jt["personas"] == []
    assert jt["fills"]["jobs"] == "Product lays its jobs" and jt["fills"]["personas"] == "Product asks the person who the people are"
    assert "tech" not in got                                        # the fixture project has no orkboard/ code


def test_tables_with_a_tree_lay_its_jobs(host):
    lay(host, PAGE.format(p="x", t="y"))
    opportunity_tree.keep(host.ideas.state_dir, [{"text": "The person decides"}], [
        {"id": "waits", "when": "I run several tools", "want": "see what waits", "so": "I decide", "segment": "Solo developer"},
        {"id": "stop", "when": "a tool runs away", "want": "stop it", "so": "nothing is lost"},
        {"id": "diff", "when": "before main", "want": "see the diff", "so": "I say yes"}], "person")
    jt = host.command("ideas.tables", {})["product"]["jtbd"]
    assert jt["job"]["want"] == "see what waits" and jt["job"]["persona"] == "Solo developer"
    assert [j["title"] for j in jt["jobs"]] == ["stop it", "see the diff"] and jt["personas"][0]["title"] == "Solo developer"
    assert jt["fills"]["job"] == "" and jt["fills"]["personas"] == ""


def test_on_this_repository_each_token_is_a_talk_architecture_is_its_code_and_nothing_is_an_example():
    h = Orkboard(REPO)
    try:
        verdicts = h.command("ideas.verdicts", {})
        tables = h.command("ideas.tables", {})
    finally:
        sys.modules.pop("orkboard.core.idea_runner", None)
    root = h.ideas.root(make=False)
    found, pages = ideas.ideas_and_pages(root)
    parties = ideas.tracks(root, make=False)
    for i in found:                                                   # each token is a leader's Talk as page_talk reads it, in the route's order
        want = [(s, page_talk.read_talk(pages[i["slug"]], board_turns._title(parties, s))) for s in board_turns.route_of(pages[i["slug"]])]
        want = [{"leader": s, **say} for s, say in want if say is not None]
        assert verdicts.get(i["slug"], []) == want
    assert any(verdicts.values())
    arch = tables["tech"]["architecture"]
    assert arch["title"] == "Architecture" and {c["id"] for layer in arch["layers"] for c in layer["cards"]} >= {"gui/", "core/", "realm/"}
    assert tables["product"]["jtbd"]["fills"]
    assert "· example" not in json.dumps([verdicts, tables])


def test_the_reader_of_the_code_writes_nothing():
    text = Path(code_layers.__file__).read_text(encoding="utf-8")
    assert "write_text" not in text and "subprocess" not in text and "orkboard.gui" not in text
