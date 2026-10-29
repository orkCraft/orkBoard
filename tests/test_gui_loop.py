"""Spec 102 B, spec 107 N (docs/specs/102-the-other-maps-and-picking-on-them.md §2; docs/specs/107-what-the-owners-day-said.md §14): Game design's loops on the host and its keeper. `ideas.loop` (the loops,
currencies and hooks, what the loop says, whether they are being proposed, the proposal's status), `ideas.loop_set` (the person's loops, their paths checked against dev), `ideas.loop_propose` (one call of Game design's leader on the step `loop`: the cheaper tier, no tools, given the
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
    assert isinstance(h.ideas.keeper, KeeperLoop) and isinstance(h.ideas, GuiLoop)      # wired: the keeper's bases, the host's and its table
    assert set(loop_commands(h.ideas)) <= set(h.commands)
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


def card(name, line="A line", rests_on=(), **more):
    return {"name": name, "line": line, "rests_on": list(rests_on), **more}


def core(*steps, **more):
    return {"loops": [{"span": "core", "name": "The hit", "line": "What the player repeats", "feeds": "", "steps": list(steps)}], **more}


FOUR = [card("Spawn", "Enemies come in waves", ["config/balance.json", "ghost.ts"]), card("Fight", "Hit and dodge", ["levels"]), card("Loot"), card("Upgrade", "Spend the loot")]
ANSWER = core(*FOUR)
GOLD = {"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins from the fights"}
RICH = {"loops": [{"span": "core", "name": "The hit", "line": "x", "feeds": "session", "steps": [card("Aim", feel="challenge", intensity=2), card("Shoot", feel="sensation", intensity=5, gives=["gold"]), card("Reload", feel="submission", intensity=1)]},
                  {"span": "session", "name": "A wave", "line": "y", "feeds": "", "steps": [card("Join", feel="fellowship", intensity=2), card("Hold", feel="challenge", intensity=5, takes=["gold"]), card("Score", feel="fantasy", intensity=3, gives=["gold"])]}],
        "currencies": [GOLD], "hooks": [{"when": "D1", "line": "A daily chest waits"}]}


def names(data, span="core"):
    return [s["name"] for lp in data["loops"] if lp["span"] == span for s in lp["steps"]]


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets, `calls` every call made."""

    def __init__(self, host, answer=None):
        self.host, self.calls, self.answer = host, [], ANSWER if answer is None else answer
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


def _propose(host, party=None, **args):
    got = host.command("ideas.loop_propose", args)
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
    assert "Read no file" in p


def test_the_prompt_is_a_senior_game_designers_brief_for_version_2_of_the_loop(host, game, model):
    _propose(host, game)
    p = model.calls[0]["prompt"]
    assert '{"loops": [{"span": "core"' in p and '"currencies"' in p and '"hooks"' in p and '"cards"' not in p                  # version 2, not 1
    for word in ("core", "session", "meta", "seconds", "minutes", "days and weeks"):                                      # the spans and their time scales
        assert word in p
    assert all(f in p for f in loop.FEELS) and "MDA" in p and "intensity" in p                                            # the eight feelings, and how strongly
    assert "what the player does" in p and "what they feel" in p                                                         # each step says what the player does and feels
    assert "gives" in p and "takes" in p and "piles up" in p and all(k in p for k in loop.KINDS)                           # the currencies, with where they are earned and spent
    assert "D1" in p and "D7" in p and "D30" in p and "comes back" in p                                                    # the hooks
    assert "rests_on" in p and "Never invent a path" in p and "3 to 6" in p and "4 currencies at most" in p


def test_the_step_is_as_project_qs_on_the_cheaper_tier_in_the_specs_stage_of_its_partys_ledger(host, game, model):
    _propose(host, game)
    spent = idea_spend.of_goal(host.ideas.state_dir, game)
    assert spent["usd"] == 0.01 and spent["stages"]["spec"]["usd"] == 0.01
    assert idea_spend.STEP_STAGE["loop"] == "spec" and "loop" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("loop", target) == idea_target.pick("project_q", target)
    assert idea_target.READS["loop"] == 0 and idea_target.CONTEXT["loop"] == idea_target.CONTEXT["project_q"] and idea_target.CAPS["loop"] == idea_target.CAPS["project_q"] <= 0.15


def test_the_proposal_is_kept_by_the_leader_with_the_paths_dev_has_and_the_command_reads_it(host, game, model):
    assert host.command("ideas.loop", {}) == {"version": 2, "loops": [], "currencies": [], "hooks": [], "by": "", "at": "", "findings": [], "proposing": False, "status": "", "party": game}
    _propose(host, game)
    got = host.command("ideas.loop", {})
    assert got["status"] == "done" and got["proposing"] is False and got["party"] == game and "error" not in got and got["version"] == 2
    assert names(got) == ["Spawn", "Fight", "Loot", "Upgrade"] and all(s["by"] == "leader" and s["at"] for s in got["loops"][0]["steps"]) and got["by"] == "leader"
    assert got["loops"][0]["steps"][0]["rests_on"] == ["config/balance.json"]                                          # `ghost.ts` is no file of dev's
    assert {k: got[k] for k in ("version", "loops", "currencies", "hooks", "by", "at")} == loop.read(host.ideas.state_dir)
    assert "1. Spawn: Enemies come in waves" in loop.text(host.ideas.state_dir, host.ideas.keeper.repo_root).splitlines()


def test_the_command_says_what_the_loop_says_by_code(host, game):
    Model(host, RICH)
    _propose(host, game)
    got = host.command("ideas.loop", {})
    assert got["findings"] == [] and names(got, "session") == ["Join", "Hold", "Score"] and got["currencies"][0]["id"] == "gold" and got["hooks"] == [{"when": "D1", "line": "A daily chest waits"}]
    flat = json.loads(json.dumps(RICH))
    flat["loops"][1]["steps"] = [{**s, "intensity": 3} for s in flat["loops"][1]["steps"]]
    flat["loops"][0]["steps"][1].pop("gives")
    sent = host.command("ideas.loop_set", flat)
    assert sent["findings"] == ["The core loop rewards nothing", "The session loop's feeling is flat"] and host.command("ideas.loop", {})["findings"] == sent["findings"]


def test_it_is_asked_once_a_loop_kept_or_proposed_is_never_asked_again_unasked(host, game, model):
    assert _propose(host, game)["asked"] is True and _propose(host, game)["asked"] is False and len(model.calls) == 1
    loop.save_proposal(host.ideas.state_dir, "")                                                                       # the proposal forgotten: the loops stand, so nothing is asked
    assert _propose(host, game)["asked"] is False and len(model.calls) == 1


def test_a_loop_the_person_kept_first_is_never_asked_and_never_overwritten_by_a_late_proposal(host, game):
    seen = {}

    def late(call):
        seen["set"] = host.command("ideas.loop_set", core(*[card(n, rests_on=["levels"]) for n in "ABC"]))              # the person keeps theirs while the leader is asked
        return ANSWER

    model = Model(host, late)
    _propose(host, game)
    kept = loop.read(host.ideas.state_dir)
    assert names(kept) == list("ABC") and all(s["by"] == "person" for s in kept["loops"][0]["steps"]) and len(model.calls) == 1 and "was" not in kept
    assert _propose(host, game)["asked"] is False and len(model.calls) == 1


def test_propose_again_asks_over_a_loop_kept_and_puts_the_persons_version_aside(host, game, model):
    host.command("ideas.loop_set", core(*[card(n, rests_on=["levels"]) for n in "ABCD"]))
    assert _propose(host, game)["asked"] is False and not model.calls                                                  # unasked, a loop kept is not asked over
    assert _propose(host, game, again=True) == {"ok": True, "asked": True}
    got = host.command("ideas.loop", {})
    assert len(model.calls) == 1 and got["status"] == "done" and got["by"] == "leader" and names(got) == ["Spawn", "Fight", "Loot", "Upgrade"]
    assert got["was"]["by"] == "person" and names(got["was"]) == list("ABCD")                                           # the person's version is kept aside
    model.answer = core(*FOUR[:3])
    assert _propose(host, game, again=True)["asked"] is True and names(host.command("ideas.loop", {})) == ["Spawn", "Fight", "Loot"]
    assert names(host.command("ideas.loop", {})["was"]) == list("ABCD")                                                # the leader's own version put aside is not theirs: `was` stays the person's


def test_propose_again_is_asked_while_nothing_is_kept_and_not_a_second_time_while_it_is_asked(host, game):
    seen = {}

    def slow(call):
        seen["again"] = host.command("ideas.loop_propose", {"again": True})
        return ANSWER

    model = Model(host, slow)
    assert _propose(host, game, again=True)["asked"] is True and seen["again"]["asked"] is False and len(model.calls) == 1


def test_a_call_that_does_not_answer_is_tried_once_more_then_recorded_and_asked_again_at_the_next_press(host, game):
    model = Model(host, "not json at all")
    _propose(host, game)
    assert len(model.calls) == 2                                                                                      # one more try
    got = host.command("ideas.loop", {})
    assert got["loops"] == [] and got["status"] == "failed" and "did not answer" in got["error"] and got["proposing"] is False
    for bad in (core(*FOUR[:2]), {"loops": "no"}, core(*FOUR[:3], {"name": "only"}), core(*FOUR[:3], card("Spawn"))):     # three to six steps each, strictly
        model.answer = bad
        _propose(host, game)
        assert host.command("ideas.loop", {})["status"] == "failed" and not loop.kept(loop.read(host.ideas.state_dir))
    model.answer = ANSWER
    assert _propose(host, game)["asked"] is True and host.command("ideas.loop", {})["status"] == "done" and len(names(loop.read(host.ideas.state_dir))) == 4


def test_a_call_lost_with_the_process_is_not_proposing_and_is_asked_again(host, game, model):
    loop.save_proposal(host.ideas.state_dir, "asking")                                                                 # the record of a run that died
    assert host.command("ideas.loop", {})["proposing"] is False and host.command("ideas.loop", {})["status"] == ""
    assert _propose(host, game)["asked"] is True and len(model.calls) == 1


def test_a_proposal_being_asked_is_proposing_and_is_not_asked_a_second_time(host, game):
    seen = {}

    def slow(call):
        seen["loop"] = host.command("ideas.loop", {})
        seen["again"] = host.command("ideas.loop_propose", {})
        return ANSWER

    Model(host, slow)
    _propose(host, game)
    assert seen["loop"]["proposing"] is True and seen["loop"]["status"] == "asking" and seen["loop"]["loops"] == []
    assert seen["again"]["asked"] is False


def test_no_game_design_party_or_no_call_to_make_is_asked_false_with_why_never_a_refusal(host, model, monkeypatch):
    assert _propose(host) == {"ok": True, "asked": False, "why": "Game design has no party here: make it first"} and not model.calls
    assert host.command("ideas.loop", {})["party"] == ""
    game = _party(host, "Game design", "game-designer", ["level-designer"], "product")
    monkeypatch.setattr(host.ideas.keeper, "_may_run", lambda: "Today's spend limit is reached: the keeper waits")
    for args in ({}, {"again": True}):
        assert _propose(host, **args) == {"ok": True, "asked": False, "why": "Today's spend limit is reached: the keeper waits"}
    assert not model.calls and loop.proposal(host.ideas.state_dir)["status"] == ""                                     # nothing begun: asked at the next press
    assert game


def test_a_party_that_is_not_game_designs_is_not_asked(host, model):
    _party(host, "Product", "product-manager", ["copywriter"], "product")
    _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")
    assert _propose(host)["asked"] is False and not model.calls


# -- the person's loops --------------------------------------------------------------------------------------------------------------

def test_the_person_sets_the_loops_kept_by_the_person_their_paths_checked_against_dev(host, game):
    got = host.command("ideas.loop_set", ANSWER)
    assert got["ok"] is True and got["dropped"] == [{"name": "Spawn", "path": "ghost.ts"}] and got["findings"] == []
    steps = got["loops"][0]["steps"]
    assert [c["by"] for c in steps] == ["person"] * 4 and steps[0]["rests_on"] == ["config/balance.json"] and steps[1]["rests_on"] == ["levels"]
    assert {k: host.command("ideas.loop", {})[k] for k in ("loops", "currencies", "hooks")} == {"loops": got["loops"], "currencies": got["currencies"], "hooks": got["hooks"]}
    again = host.command("ideas.loop_set", {"loops": [{**got["loops"][0], "steps": [*steps[:3], {**steps[3], "line": "Spend it all"}]}]})
    assert again["loops"][0]["steps"][0] == steps[0] and again["loops"][0]["steps"][3]["line"] == "Spend it all" and again["dropped"] == []        # an unchanged step is as it was


def test_a_step_is_edited_in_its_name_line_feeling_and_intensity_and_a_currency_in_its_name(host, game):
    Model(host, RICH)
    _propose(host, game)
    got = host.command("ideas.loop", {})
    loops = json.loads(json.dumps(got["loops"]))
    loops[0]["steps"][0].update(name="Sight", line="Line up the shot", feel="discovery", intensity=4)
    sent = host.command("ideas.loop_set", {"loops": loops, "currencies": [{**got["currencies"][0], "name": "Coins"}], "hooks": got["hooks"]})
    first = sent["loops"][0]["steps"][0]
    assert (first["id"], first["name"], first["line"], first["feel"], first["intensity"], first["by"]) == ("aim", "Sight", "Line up the shot", "discovery", 4, "person")
    assert sent["currencies"][0] == {**GOLD, "name": "Coins"} and sent["loops"][0]["steps"][1]["gives"] == ["gold"] and sent["loops"][0]["steps"][1]["by"] == "leader"        # the id stays: what it gives stays
    assert sent["findings"] == [] and sent["by"] == "person"


def test_the_loops_of_the_leader_the_person_did_not_touch_stay_the_leaders(host, game, model):
    _propose(host, game)
    kept = loop.read(host.ideas.state_dir)["loops"][0]["steps"]
    got = host.command("ideas.loop_set", {"loops": [{"span": "core", "name": "The hit", "steps": [kept[0], {**kept[1], "name": "Duel"}, kept[2], kept[3]]}]})
    assert [c["by"] for c in got["loops"][0]["steps"]] == ["leader", "person", "leader", "leader"] and got["loops"][0]["steps"][1]["id"] == "fight"


def test_a_set_that_is_none_is_refused_in_plain_words_and_changes_nothing(host, game):
    host.command("ideas.loop_set", ANSWER)
    before = loop.read(host.ideas.state_dir)
    for bad, why in (({}, "one to three loops"), (core(*FOUR[:2]), "3 to 6 steps"), ({"loops": "no"}, "one to three loops"), (core(*FOUR[:3], card("")), "name and a line"),
                     (core(*FOUR[:3], card("loot")), "Two steps of the core loop are named loot"), (core(*FOUR[:3], {"name": "X", "line": "l", "rests_on": "levels"}), "list of files"),
                     (core(*FOUR, currencies=[{"name": "A", "kind": "magic"}]), "A currency is soft"), (core(*FOUR[:3], card("X", feel="joy")), "A feeling is one of")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.loop_set", bad)
    assert loop.read(host.ideas.state_dir) == before


def test_a_version_1_set_is_one_core_loop(host, game):
    got = host.command("ideas.loop_set", {"cards": FOUR})
    assert [lp["span"] for lp in got["loops"]] == ["core"] and names(got) == ["Spawn", "Fight", "Loot", "Upgrade"] and {s["intensity"] for s in got["loops"][0]["steps"]} == {3}


def test_the_commands_are_in_the_table_by_name(host):
    assert COMMANDS <= set(host.commands) and set(loop_commands(host.ideas)) == COMMANDS
