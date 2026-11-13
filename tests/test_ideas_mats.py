"""Spec 171 C (`gui/ideas_mats.py`: ideas.verdicts, ideas.tables; `realm/code_layers.py`): the verdicts and the leaders' tables, read only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import ideas, opportunity_tree

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


# -- the gate mat's seals: the goal read from `idea`, the `from` as sent (goal 113 B; H7) -----------------------------------------------------

from tests.test_goal_main import goal as gm_goal, repo, task as gm_task  # noqa: E402,F401  (repo: a fixture)


@pytest.fixture
def gate_host(repo):
    h = Orkboard(repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _moves(h):
    from orkboard.realm import event_log
    return [r for r in event_log.read(h.repo_root) if r["event"] == "move_played"]


def test_the_gate_mats_merge_into_main_keeps_its_goal_and_its_from_as_sent_and_none_is_none(gate_host):
    import time
    h = gate_host
    for n, (given, kept) in enumerate({"hand": "hand", "mat": "mat", None: "", "portal": ""}.items()):
        slug = gm_goal(h, f"Lobby {n}")
        gm_task(h, h.repo_root, slug, "k1", {f"lobby{n}.ts": "l\n"})
        h.command("ideas.to_main_checks", {"idea": slug})
        for _ in range(1000):
            got = h.ideas._main_checks.get(slug)
            if got and not got["running"]:
                break
            time.sleep(0.02)
        h.command("ideas.to_main", {"sealed": True, "idea": slug, **({"from": given} if given is not None else {})})
        row = _moves(h)[-1]
        assert len(_moves(h)) == n + 1 and (row["idea"], row["kind"], row["from"]) == (slug, "merge_main", kept), (given, row)


