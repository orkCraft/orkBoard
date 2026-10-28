"""Spec 102 B (docs/specs/102-the-other-maps-and-picking-on-them.md §2): Game design's loop on the host and its keeper. `ideas.loop` (the cards, whether they are being proposed, the proposal's
status), `ideas.loop_set` (the person's cards, their paths checked against dev), `ideas.loop_propose` (one call of Game design's leader on the step `loop`: the cheaper tier, no tools, given the
start files and the configs' names and first lines chosen by code; four to six cards kept `by: "leader"`; asked once, a failure after one more try asked again at the next press). The model
call is stubbed (`keeper.call`).

These tests compose the mixins onto the keeper and the host the way the lead's wiring does (the `host` fixture): they pass without that wiring in `core/idea_keeper.py` and `gui/ideas.py`.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time

import pytest

from orkboard.core.idea_loop import LoopMixin as KeeperLoop
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_loop import LoopMixin as GuiLoop, loop_commands
from orkboard.realm import goal_team, idea_spend, idea_target, ideas, library, loop, project_facts

COMMANDS = {"ideas.loop", "ideas.loop_set", "ideas.loop_propose"}


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def host(fake_repo) -> Orkboard:
    for name, text in {"config/balance.json": '{"hp": 10}\n', "levels/one.json": "{}\n", "SECRET_NOT_CONFIG.txt": "x"}.items():
        (fake_repo / name).parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / name).write_text(text)
    git(fake_repo, "add", "-A")
    git(fake_repo, "commit", "-q", "-m", "a game")
    git(fake_repo, "branch", "dev")
    h = Orkboard(fake_repo)
    if not isinstance(h.ideas.keeper, KeeperLoop):                            # wired by the lead: the keeper's bases, the host's and its table
        h.ideas.keeper.__class__ = type("KeeperWithLoop", (KeeperLoop, type(h.ideas.keeper)), {})
    if not isinstance(h.ideas, GuiLoop):
        h.ideas.__class__ = type("IdeasWithLoop", (GuiLoop, type(h.ideas)), {})
    h.commands.update(loop_commands(h.ideas))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def game(host):
    return _party(host, "Game design", "game-designer", ["level-designer"], "product")


def card(name, line="A line", rests_on=()):
    return {"name": name, "line": line, "rests_on": list(rests_on)}


FOUR = [card("Spawn", "Enemies come in waves", ["config/balance.json", "ghost.ts"]), card("Fight", "Hit and dodge", ["levels"]), card("Loot"), card("Upgrade", "Spend the loot")]


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=None):
        self.host, self.calls, self.answer = host, [], {"cards": FOUR} if answer is None else answer
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        self.calls.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"],
                           "key": getattr(k._tls, "key", ""), "tool": k.tool_now()})
        answer = self.answer(self.calls[-1]) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy_goal(party):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _propose(host, party=None):
    got = host.command("ideas.loop_propose", {})
    if party:
        _wait(host, party)
    return got


# -- the call: Game design's leader, the cheaper tier, no tools, the files by code ---------------------------------------------------------

def test_the_first_proposal_is_one_call_of_game_designs_leader_on_the_cheaper_tier_with_no_tools_given_the_files_chosen_by_code(host, game, model):
    (host.ideas.keeper.repo_root / "README.md").write_text("# Hordes\n\nA wave game: survive, loot, upgrade.\n", encoding="utf-8")
    (host.ideas.keeper.repo_root / "docs" / "decisions.md").write_text("## 1. SECRET DECISION TEXT\n", encoding="utf-8")
    assert _propose(host, game) == {"ok": True, "asked": True}
    (call,) = model.calls
    assert call["step"] == "loop" and call["tools"] is False and call["key"] == f"goal:{game}"
    assert (call["tier"], call["effort"]) == idea_target.pick("loop", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("loop", "balance")
    p = call["prompt"]
    assert p.startswith("You are Game designer, the leader of this goal's party")                                      # its leader's voice
    assert "config/balance.json" in p and "levels/one.json" in p and '{"hp": 10}' in p                                 # the configs by name, the first lines of the first
    assert "SECRET_NOT_CONFIG" not in p and "SECRET DECISION TEXT" not in p                                           # a file no rule chose; the decisions file never
    assert "Hordes" in p and "docs/notes.md" in p                                                                      # the README and docs/'s top level, by their paths
    assert "Read no file" in p and '"cards"' in p and "4 to 6" in p
    assert p.index("config/balance.json") < p.index("Hordes")                                                          # the configs before the files cut at the context's cap


def test_the_step_is_as_project_qs_on_the_cheaper_tier_in_the_specs_stage_of_its_partys_ledger(host, game, model):
    _propose(host, game)
    spent = idea_spend.of_goal(host.ideas.state_dir, game)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01
    assert idea_spend.STEP_STAGE["loop"] == "spec" and "loop" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("loop", target) == idea_target.pick("project_q", target)
    assert idea_target.READS["loop"] == 0 and idea_target.CONTEXT["loop"] == idea_target.CONTEXT["project_q"] and idea_target.CAPS["loop"] == idea_target.CAPS["project_q"] <= 0.15


def test_the_proposal_is_kept_by_the_leader_with_the_paths_dev_has_and_the_command_reads_it(host, game, model):
    assert host.command("ideas.loop", {}) == {"cards": [], "proposing": False, "status": "", "party": game}
    _propose(host, game)
    got = host.command("ideas.loop", {})
    assert got["status"] == "done" and got["proposing"] is False and got["party"] == game and "error" not in got
    assert [c["name"] for c in got["cards"]] == ["Spawn", "Fight", "Loot", "Upgrade"] and all(c["by"] == "leader" and c["at"] for c in got["cards"])
    assert got["cards"][0]["rests_on"] == ["config/balance.json"]                                                      # `ghost.ts` is no file of dev's
    assert loop.read(host.ideas.state_dir) == got["cards"]
    assert loop.text(host.ideas.state_dir, host.ideas.keeper.repo_root).splitlines()[2] == "1. Spawn: Enemies come in waves"


def test_it_is_asked_once_a_loop_kept_or_proposed_is_never_asked_again(host, game, model):
    assert _propose(host, game)["asked"] is True and _propose(host, game)["asked"] is False and len(model.calls) == 1
    loop.save_proposal(host.ideas.state_dir, "")                                                                       # the proposal forgotten: the cards stand, so nothing is asked
    assert _propose(host, game)["asked"] is False and len(model.calls) == 1


def test_a_loop_the_person_kept_first_is_never_asked_and_never_overwritten_by_a_late_proposal(host, game):
    seen = {}

    def late(call):
        seen["set"] = host.command("ideas.loop_set", {"cards": [card(n, rests_on=["levels"]) for n in "ABCD"]})          # the person keeps theirs while the leader is asked
        return {"cards": FOUR}

    model = Model(host, late)
    _propose(host, game)
    assert [c["name"] for c in loop.read(host.ideas.state_dir)] == list("ABCD") and all(c["by"] == "person" for c in loop.read(host.ideas.state_dir)) and len(model.calls) == 1
    assert _propose(host, game)["asked"] is False and len(model.calls) == 1


def test_a_call_that_does_not_answer_is_tried_once_more_then_recorded_and_asked_again_at_the_next_press(host, game):
    model = Model(host, "not json at all")
    _propose(host, game)
    assert len(model.calls) == 2                                                                                      # one more try
    got = host.command("ideas.loop", {})
    assert got["cards"] == [] and got["status"] == "failed" and "did not answer" in got["error"] and got["proposing"] is False
    for bad in ({"cards": FOUR[:3]}, {"cards": "no"}, {"cards": [*FOUR[:3], {"name": "only"}]}):                       # four to six, strictly
        model.answer = bad
        _propose(host, game)
        assert host.command("ideas.loop", {})["status"] == "failed" and loop.read(host.ideas.state_dir) == []
    model.answer = {"cards": FOUR}
    assert _propose(host, game)["asked"] is True and host.command("ideas.loop", {})["status"] == "done" and len(loop.read(host.ideas.state_dir)) == 4


def test_a_call_lost_with_the_process_is_not_proposing_and_is_asked_again(host, game, model):
    loop.save_proposal(host.ideas.state_dir, "asking")                                                                 # the record of a run that died
    assert host.command("ideas.loop", {})["proposing"] is False and host.command("ideas.loop", {})["status"] == ""
    assert _propose(host, game)["asked"] is True and len(model.calls) == 1


def test_a_proposal_being_asked_is_proposing_and_is_not_asked_a_second_time(host, game):
    seen = {}

    def slow(call):
        seen["loop"] = host.command("ideas.loop", {})
        seen["again"] = host.command("ideas.loop_propose", {})
        return {"cards": FOUR}

    Model(host, slow)
    _propose(host, game)
    assert seen["loop"]["proposing"] is True and seen["loop"]["status"] == "asking" and seen["loop"]["cards"] == []
    assert seen["again"]["asked"] is False


def test_no_game_design_party_or_no_call_to_make_is_asked_false_with_why_never_a_refusal(host, model, monkeypatch):
    assert _propose(host) == {"ok": True, "asked": False, "why": "Game design has no party here: make it first"} and not model.calls
    assert host.command("ideas.loop", {})["party"] == ""
    game = _party(host, "Game design", "game-designer", ["level-designer"], "product")
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    assert _propose(host) == {"ok": True, "asked": False, "why": "Today's spend limit is reached: the keeper waits"}
    assert not model.calls and loop.proposal(host.ideas.state_dir)["status"] == ""                                     # nothing begun: asked at the next press
    assert game


def test_a_party_that_is_not_game_designs_is_not_asked(host, model):
    _party(host, "Product", "product-manager", ["copywriter"], "product")
    _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")
    assert _propose(host)["asked"] is False and not model.calls


# -- the person's cards --------------------------------------------------------------------------------------------------------------

def test_the_person_sets_the_cards_kept_by_the_person_their_paths_checked_against_dev(host, game):
    got = host.command("ideas.loop_set", {"cards": FOUR})
    assert got["ok"] is True and got["dropped"] == [{"name": "Spawn", "path": "ghost.ts"}]
    assert [c["by"] for c in got["cards"]] == ["person"] * 4 and got["cards"][0]["rests_on"] == ["config/balance.json"] and got["cards"][1]["rests_on"] == ["levels"]
    assert host.command("ideas.loop", {})["cards"] == got["cards"]
    again = host.command("ideas.loop_set", {"cards": [*got["cards"][:3], {**got["cards"][3], "line": "Spend it all"}]})
    assert again["cards"][0] == got["cards"][0] and again["cards"][3]["line"] == "Spend it all" and again["dropped"] == []        # an unchanged card is as it was


def test_the_cards_of_the_leader_the_person_did_not_touch_stay_the_leaders(host, game, model):
    _propose(host, game)
    kept = loop.read(host.ideas.state_dir)
    got = host.command("ideas.loop_set", {"cards": [kept[0], {**kept[1], "name": "Duel"}, kept[2], kept[3]]})
    assert [c["by"] for c in got["cards"]] == ["leader", "person", "leader", "leader"] and got["cards"][1]["id"] == "fight"


def test_a_set_that_is_none_is_refused_in_plain_words_and_changes_nothing(host, game):
    host.command("ideas.loop_set", {"cards": FOUR})
    before = loop.read(host.ideas.state_dir)
    for bad, why in (({}, "4 to 6 cards"), ({"cards": FOUR[:3]}, "4 to 6 cards"), ({"cards": "no"}, "4 to 6 cards"), ({"cards": [*FOUR[:3], card("")]}, "name and a line"),
                     ({"cards": [*FOUR[:3], card("loot")]}, "Two cards are named loot"), ({"cards": [*FOUR[:3], {"name": "X", "line": "l", "rests_on": "levels"}]}, "list of files")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.loop_set", bad)
    assert loop.read(host.ideas.state_dir) == before


def test_the_commands_are_in_the_table_by_name(host):
    assert COMMANDS <= set(host.commands) and set(loop_commands(host.ideas)) == COMMANDS
