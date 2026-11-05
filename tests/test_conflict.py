"""Spec 150 E1 (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md; decisions §254.6): a decision whose call says it goes against a standing decision keeps the conflict as data and is not
confirmable until `ideas.conflict` answers it; the `conflict` row sits under the first lane before the decision; each of the three choices does what E1.3 says. The keeper's call is stubbed as
`tests/test_idea_slices.py` does (its fixtures and its `Model`); no real model.
"""
from __future__ import annotations

import time

import pytest

from orkboard.core.idea_decide import clean_decision
from orkboard.gui.board_host import CommandError
from orkboard.gui.ideas_board import sort_needs
from orkboard.realm import board_map, decision_conflicts, event_log, idea_ripe, idea_words, ideas, lexicon, slices, spec_sections
from tests.test_idea_slices import _idle, _log, _route, design, goal, host, model, release, tech  # noqa: F401  (fixtures)

POINT = "Screens hold six seconds, not ten."
SAID = {"title": "Screens hold ten seconds again", "why": "Slow readers asked.", "points": ["Screens hold 10 seconds.", "Art draws them slower."], "changes": [6],
        "conflicts": [{"number": 6, "point": POINT}]}


def _wait(host, slug, state="decided"):
    for _ in range(1000):
        if ideas.state(host.ideas.state_dir, slug)["state"] == state and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("never " + state)


def _conflicted(host, tech, goal, model, said=None):
    """The goal's decision worded by a call that says a conflict with decision 6 (Tech holds a slice of it); the goal is `decided`."""
    slices.add_cut(host.ideas.state_dir, 6, {tech: {"says": "Your screens hold 6 seconds.", "points": ["6.1"]}})
    _log(host)
    ideas.save_state(host.ideas.state_dir, goal, state="talk", route=[{"party": tech}])
    model.said["decide"] = said or SAID
    host.ideas.keeper.decide(goal)
    _wait(host, goal)
    return goal


def _decision(host, slug):
    return spec_sections.record(host.ideas.state_dir, slug)["decision"]


def _needs(host, slug):
    return [n for n in host.command("ideas.board", {})["needs_you"] if n.get("idea") == slug]


# -- E1.1: the call says it as data -------------------------------------------------------------------------------------------------------

def test_the_call_says_a_conflict_as_data_at_most_two_each_a_known_number_with_a_point_of_one_line():
    long = {"number": 6, "point": "  Six\nseconds " + "x" * 400}
    got = clean_decision({"title": "T", "why": "W", "points": ["a", "b"], "changes": [6], "conflicts": [long, {"number": 6, "point": "again"}, {"number": 99, "point": "unknown"},
                                                                                                         {"number": 5, "point": ""}, {"number": 5, "point": "Five."}, {"number": 3, "point": "x"}, "junk"]}, [3, 5, 6])
    assert [c["number"] for c in got["conflicts"]] == [6, 5] and got["conflicts"][1]["point"] == "Five."          # each once, the unknown and the empty left out
    assert len(got["conflicts"][0]["point"]) <= idea_words.CARD_LINE_CHARS and "\n" not in got["conflicts"][0]["point"]
    assert len(clean_decision({"title": "T", "why": "W", "points": ["a", "b"], "conflicts": [{"number": n, "point": "p"} for n in (3, 5, 6)]}, [3, 5, 6])["conflicts"]) == 2
    assert "conflicts" not in clean_decision({"title": "T", "why": "W", "points": ["a", "b"], "conflicts": "x"}, [6])


def test_the_decisions_call_is_told_to_say_a_conflict_with_what_the_leaders_hold(host, tech, goal):
    slices.add_cut(host.ideas.state_dir, 6, {tech: {"says": "Your screens hold 6 seconds.", "points": ["6.1"]}})
    prompt = host.ideas.keeper.decision_prompt(goal, _route(tech), {})
    assert "`conflicts`" in prompt and '"conflicts": [{"number": 0, "point": "…"}]' in prompt and str(idea_words.CARD_LINE_CHARS) in prompt
    assert "conflicts" not in host.ideas.keeper.decision_prompt("nobody", [], {})                                    # nothing held, nothing to go against


def test_a_conflict_is_kept_on_the_decision_and_it_is_not_confirmable_until_answered(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model)
    d = _decision(host, slug)
    assert d["conflicts"] == [{"number": 6, "point": POINT, "answer": ""}] and d["changes"] == [6]
    assert [c["number"] for c in decision_conflicts.open_of(d)] == [6]
    host.ideas.keeper.sections = lambda s: None
    with pytest.raises(CommandError, match=r"Goes against §6: answer it first"):
        host.command("ideas.confirm", {"idea": slug})
    assert not _decision(host, slug)["confirmed"] and ideas.state(host.ideas.state_dir, slug)["state"] == "decided"
    assert not idea_ripe.running(host.ideas.state_dir, slug)                                                        # and nothing starts by itself while it waits


def test_a_decision_with_no_conflict_is_as_before(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model, {**SAID, "conflicts": []})
    assert _decision(host, slug)["conflicts"] == []
    host.ideas.keeper.sections = lambda s: None
    assert host.command("ideas.confirm", {"idea": slug})["number"] == 7


# -- E1.2: the card ------------------------------------------------------------------------------------------------------------------------

def test_the_conflict_row_is_under_the_first_lane_before_the_decision_with_the_earlier_decisions_words(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model)
    kinds = [n["kind"] for n in _needs(host, slug)]
    assert kinds.index("conflict") < kinds.index("decision")
    (row,) = [n for n in _needs(host, slug) if n["kind"] == "conflict"]
    assert (row["number"], row["point"]) == (6, POINT)
    assert row["title_then"] == "The screens hold six seconds" and row["why_then"] == "People read faster than we thought."
    assert [n for n in _needs(host, slug) if n["kind"] == "decision"][0]["conflicted"] is True
    assert "conflict" in board_map.NEEDS
    rows = [{"kind": "decision", "at": "a", "idea": "x"}, {"kind": "conflict", "at": "a", "idea": "x"}, {"kind": "route", "at": "a", "idea": "y"}]
    assert [n["kind"] for n in sort_needs(rows)] == ["conflict", "decision", "route"]                                 # before the decision it holds back, otherwise by the usual order


def test_the_conflict_row_leaves_with_its_answer_and_the_decision_is_no_longer_conflicted(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model)
    host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "replace"})
    kinds = [n["kind"] for n in _needs(host, slug)]
    assert "conflict" not in kinds and [n for n in _needs(host, slug) if n["kind"] == "decision"][0]["conflicted"] is False


# -- E1.3: the answer ----------------------------------------------------------------------------------------------------------------------

def test_replace_keeps_the_number_in_changes_and_lets_confirm_run(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model, {**SAID, "changes": []})                                            # the call did not name it in changes: replace puts it there
    got = host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "replace"})
    assert got["ok"] is True and got["left"] == 0 and got["reworded"] is False
    d = _decision(host, slug)
    assert d["changes"] == [6] and d["conflicts"][0]["answer"] == "replace" and not model.steps("decide")[1:]      # no second call
    host.ideas.keeper.sections = lambda s: None
    assert host.command("ideas.confirm", {"idea": slug})["number"] == 7
    _idle(host)
    assert "Changes: 6." in host.ideas.keeper._log_text()
    assert [e["choice"] for e in event_log.read(host.repo_root) if e["event"] == event_log.CONFLICT_ANSWERED] == ["replace"]


def test_keep_drops_the_number_and_words_the_decision_again_within_it(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model)
    model.said["decide"] = {"title": "Screens keep six seconds", "why": "Six holds.", "points": ["Screens hold 6 seconds.", "Art keeps its pace."], "changes": [6],
                            "conflicts": [{"number": 6, "point": POINT}]}                                             # a call that still says it: the person already answered
    got = host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "keep"})
    assert got["ok"] is True and got["reworded"] is True and got["cost"]["calls"] == 1
    assert decision_conflicts.open_of(_decision(host, slug)) == []                                                    # answered at once: the card leaves
    _wait(host, slug)
    _idle(host)
    second = model.steps("decide")[-1]["prompt"]
    assert f"Keep §6: {POINT}" in second and "The decision as it is worded now" in second
    d = _decision(host, slug)
    assert d["title"] == "Screens keep six seconds" and d["changes"] == [] and d["conflicts"][0]["answer"] == "keep" and decision_conflicts.open_of(d) == []
    host.ideas.keeper.sections = lambda s: None
    assert host.command("ideas.confirm", {"idea": slug})["number"] == 7


def test_other_words_the_decision_again_with_the_persons_words(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model)
    model.said["decide"] = {"title": "Screens hold eight seconds", "why": "A middle way.", "points": ["Screens hold 8 seconds.", "Art follows."]}
    got = host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "other", "text": "Make it eight seconds."})
    assert got["reworded"] is True
    _wait(host, slug)
    _idle(host)
    assert "Make it eight seconds." in model.steps("decide")[-1]["prompt"]
    d = _decision(host, slug)
    assert d["title"] == "Screens hold eight seconds" and d["conflicts"] == []                  # the new words go against nothing: no conflict is left


def test_a_conflict_is_refused_in_plain_words_when_it_cannot_be_answered(host, tech, goal, model):
    slug = _conflicted(host, tech, goal, model)
    for args, why in (({"idea": slug, "number": 6, "choice": "maybe"}, "The choice is replace, keep or other"), ({"idea": slug, "number": 6, "choice": "other"}, "Write what you want instead"),
                      ({"idea": slug, "number": 5, "choice": "replace"}, "That conflict is answered, or there is none"), ({"idea": slug, "number": "6", "choice": "replace"}, "number is not a number"),
                      ({"idea": "gone", "number": 6, "choice": "replace"}, "That goal is gone")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.conflict", args)
    host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "replace"})
    with pytest.raises(CommandError, match="That conflict is answered, or there is none"):
        host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "keep"})
    assert _decision(host, slug)["changes"] == [6]


def test_a_reword_the_keeper_refuses_puts_the_conflict_back(host, tech, goal, model, monkeypatch):
    from orkboard.core.idea_keeper import KeeperError
    slug = _conflicted(host, tech, goal, model)

    def refuse(self, *a, **k):
        raise KeeperError("Out of room")
    monkeypatch.setattr(type(host.ideas.keeper), "reword", refuse)
    with pytest.raises(CommandError, match="Out of room"):
        host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "keep"})
    d = _decision(host, slug)
    assert [c["number"] for c in decision_conflicts.open_of(d)] == [6] and d["changes"] == [6]


def test_two_conflicts_are_answered_one_at_a_time_and_confirm_waits_for_the_last(host, tech, goal, model):
    slices.add_cut(host.ideas.state_dir, 5, {tech: {"says": "Screens hold ten.", "points": ["5.1"]}})
    said = {**SAID, "changes": [5, 6], "conflicts": [{"number": 6, "point": POINT}, {"number": 5, "point": "Ten seconds was the rule."}]}
    slug = _conflicted(host, tech, goal, model, said)
    host.ideas.keeper.sections = lambda s: None
    assert [n["number"] for n in _needs(host, slug) if n["kind"] == "conflict"] == [6, 5]
    assert host.command("ideas.conflict", {"idea": slug, "number": 6, "choice": "replace"})["left"] == 1
    with pytest.raises(CommandError, match="Goes against §5"):
        host.command("ideas.confirm", {"idea": slug})
    assert host.command("ideas.conflict", {"idea": slug, "number": 5, "choice": "replace"})["left"] == 0
    assert host.command("ideas.confirm", {"idea": slug})["number"] == 7


def test_the_words_of_a_conflict_are_in_the_glossary():
    assert [lexicon.term(k) for k in ("goes_against", "new_one_replaces", "keep_decision", "conflict_other")] == ["Goes against §<n>", "The new one replaces §<n>", "Keep §<n>", "Other…"]
