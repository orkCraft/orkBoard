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


# -- stage E: ideas.reply and ideas.ask_leader (a paid pass, sealed; the model faked as tests/test_idea_ask.py fakes it) ---------------------

def _faked(host, calls):
    def call(tier, prompt, effort="", budget=None):
        calls.append(prompt)
        return json.dumps({"answer": "Fine.", "sources": ["§301"], "goal": ""}), 0.01, 10, ""
    host.ideas.keeper.call = call


def _wait_ask(host):
    import time
    for _ in range(1000):
        if not host.ideas.keeper.busy("ask"):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _record(host):
    from orkboard.realm import board_ask
    return board_ask.record(host.ideas.state_dir)


def test_a_reply_is_refused_unsealed_and_nothing_is_begun(host):
    from orkboard.gui.board_host import CommandError
    lay(host, PAGE.format(p="x", t=TALK))
    calls: list = []
    _faked(host, calls)
    for name, args in (("ideas.reply", {"slug": "goal", "leader": "tech", "text": "Why?"}), ("ideas.ask_leader", {"slug": "goal", "leader": "product", "text": "Why?"})):
        with pytest.raises(CommandError, match="a paid pass cannot be undone"):
            host.command(name, args)
    assert not calls and _record(host) is None


def test_its_cost_is_said_first_and_the_call_begins_with_the_goal_named(host):
    lay(host, PAGE.format(p="x", t=TALK))
    calls: list = []
    _faked(host, calls)
    cost = host.command("ideas.ask_cost", {})
    assert cost["calls"] == 1 and cost["usd_high"] and not calls                       # read before any model runs
    got = host.command("ideas.reply", {"slug": "goal", "leader": "tech", "text": "Why one writer?", "sealed": True})
    assert got["ok"] is True and got["usd_high"] == cost["usd_high"]
    _wait_ask(host)
    rec = _record(host)
    assert rec["status"] == "answered" and rec["party"] == "tech" and "(goal)" in rec["q"] and "Why one writer?" in rec["q"]
    assert "Why one writer?" in calls[0]


def test_a_leader_not_on_the_card_and_a_part_of_a_framework_are_asked_the_same_way(host):
    from orkboard.gui.board_host import CommandError
    lay(host, PAGE.format(p="x", t=TALK))
    calls: list = []
    _faked(host, calls)
    host.command("ideas.ask_leader", {"slug": "goal", "leader": "product", "text": "And you?", "sealed": True})
    _wait_ask(host)
    assert _record(host)["party"] == "product"
    host.command("ideas.ask_leader", {"party": "tech", "framework": "Architecture", "card": "core/", "text": "Why here?", "sealed": True})
    _wait_ask(host)
    q = _record(host)["q"]
    assert _record(host)["party"] == "tech" and "Architecture" in q and "core/" in q and "Why here?" in q
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.ask_leader", {"party": "nobody", "framework": "A", "card": "b", "text": "?", "sealed": True})
    with pytest.raises(CommandError, match="No goal"):
        host.command("ideas.reply", {"slug": "nope", "leader": "tech", "text": "?", "sealed": True})


def test_a_sealed_move_logs_move_played_with_its_kind_and_from_and_keeps_no_undo(host):
    """Goal 171 O2: a sealed move that went logs `move_played` (kind, from); a refused one logs nothing; no Undo is kept."""
    from orkboard.gui.board_host import CommandError
    from orkboard.realm import event_log
    lay(host, PAGE.format(p="x", t=TALK))
    _faked(host, [])

    def played():
        return [r for r in event_log.read(host.repo_root) if r["event"] == "move_played"]
    with pytest.raises(CommandError):
        host.command("ideas.reply", {"slug": "goal", "leader": "tech", "text": "Why?", "from": "hand"})      # unsealed: refused
    with pytest.raises(CommandError, match="no plan yet"):
        host.command("ideas.start", {"slug": "goal", "from": "mat", "sealed": True})                        # the host refuses
    assert played() == []
    for n, origin in enumerate(("hand", "mat")):
        host.command("ideas.reply", {"slug": "goal", "leader": "tech", "text": f"Why {n}?", "from": origin, "sealed": True})
        _wait_ask(host)
        rows = played()
        assert len(rows) == n + 1 and rows[-1]["kind"] == "paid_pass" and rows[-1]["from"] == origin and rows[-1]["idea"] == "goal"
    assert not (host.ideas.state_dir / "goals" / "goal" / "undo.json").exists()


def test_each_sealed_kind_played_from_hand_or_mat_logs_one_move_played_and_a_refused_one_none(host):
    """The wrapper itself, over a stand-in command: every sealed table entry logs its kind and `from` once it went, nothing when it raised."""
    from orkboard.gui import ideas_mats
    from orkboard.gui.board_host import CommandError
    from orkboard.realm import event_log
    table = {**ideas_mats.SEALED_BY, **ideas_mats.SEALED_ON_CARDS}

    def count():
        return len([r for r in event_log.read(host.repo_root) if r["event"] == "move_played"])

    def refuse(a):
        raise CommandError("no")
    for name, kind in table.items():
        for origin in ("hand", "mat"):
            before = count()
            ideas_mats.played(host.ideas, name, lambda a: {"ok": True})({"slug": "goal", "from": origin, "sealed": True})
            rows = [r for r in event_log.read(host.repo_root) if r["event"] == "move_played"]
            assert len(rows) == before + 1 and rows[-1]["kind"] == kind and rows[-1]["from"] == origin, (name, origin)
            with pytest.raises(CommandError):
                ideas_mats.played(host.ideas, name, refuse)({"slug": "goal", "from": origin, "sealed": True})
            assert count() == before + 1
    assert not (host.ideas.state_dir / "goals" / "goal" / "undo.json").exists()
