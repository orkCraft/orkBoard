"""Spec 168 H4 (decisions §266.5, §283.22, §283.33): a leader's own tier over the matrix, a party's size apart from the Target, and the four ways a leader answers: Pen, Choice, Fork and Silent,
with §266.5's locks that are asked and never decided by a leader. The model call is stubbed as in tests/test_idea_talk.py."""
from __future__ import annotations

import pytest

from orkboard.realm import answer_ways, goal_team, idea_questions, idea_target, ideas, seat_talk_rules
from tests.test_idea_talk import _round_one, _state, _talk, card, host, model, parties  # noqa: F401  (the fixtures)


def _silent(host, parties, who="tech"):
    goal_team.set_answers(host.ideas.root(), parties[who], "silent")


def _decided(host, slug):
    return answer_ways.decided_of(host.ideas.state_dir, slug)


# -- the page: how a leader answers, its tier, its size ------------------------------------------------------------------------------

def test_how_a_leader_answers_and_its_tier_are_kept_on_its_page_and_an_old_page_reads_as_it_did(host, parties):
    root, tech = host.ideas.root(), parties["tech"]
    assert goal_team.answers_of(root, tech) == "choice" and goal_team.lead_tier_of(root, tech) == ""              # a page that says nothing: a Choice, *Default*
    for way in answer_ways.WAYS:
        goal_team.set_answers(root, tech, way)
        assert goal_team.answers_of(root, tech) == way
    goal_team.set_answers(root, tech, "choice")
    assert ideas.track_page(root, tech).get("answer_way") == ""                                                     # the Choice is no word on the page: an old reader meets nothing
    for tier in ("laborer", "warrior", "elder", ""):
        goal_team.set_lead_tier(root, tech, tier)
        assert goal_team.lead_tier_of(root, tech) == tier
    with pytest.raises(ValueError):
        goal_team.set_answers(root, tech, "shout")
    with pytest.raises(ValueError):
        goal_team.set_lead_tier(root, tech, "king")
    goal_team.set_size(root, tech, "lean")                                                                          # a size is kept as it was: seats' cells, how many at once
    assert goal_team.size_of(root, tech) == "lean" and goal_team.way("lean")["at_once"] == 1 and goal_team.way("full")["at_once"] == 3


# -- the tier over the matrix, through the keeper ------------------------------------------------------------------------------------

def test_a_leaders_own_tier_is_the_tier_of_its_own_calls_and_default_follows_how_deep(host, parties, model):
    k, root, tech = host.ideas.keeper, host.ideas.root(), parties["tech"]
    for target in idea_target.TARGETS:
        host.command("ideas.board_set", {"target": target})
        k._tls.party = tech
        try:
            goal_team.set_lead_tier(root, tech, "")
            assert k.pick("talk_round") == idea_target.pick("talk_round", target)                                    # *Default* follows *How deep*
            goal_team.set_lead_tier(root, tech, "laborer")
            assert k.pick("talk_round") == ("laborer", "") and k.pick("section") == ("laborer", "")
            assert k.pick("accept_step") == ("laborer", "")
            goal_team.set_lead_tier(root, tech, "elder")
            assert k.pick("talk_round")[0] == "elder" and k.pick("section_first")[0] == "elder"
            assert k.pick("route") == idea_target.pick("route", target) and k.pick("decide") == idea_target.pick("decide", target)         # not its own calls: the matrix
        finally:
            k._tls.party = ""




# -- each way's prompt line ---------------------------------------------------------------------------------------------------------



def test_a_leaders_prompt_says_its_way_and_a_choices_is_as_it_was(host, parties, model):
    k, root = host.ideas.keeper, host.ideas.root()
    base_tech, base_design = k.for_rule(parties["tech"]), k.for_rule(parties["design"])
    assert base_tech.endswith('Say "person" when unsure.') and not any(w in base_tech for w in seat_talk_rules.WAY_RULES.values())      # a Choice: today's text
    for way in ("pen", "fork", "silent"):
        goal_team.set_answers(root, parties["tech"], way)
        assert k.for_rule(parties["tech"]) == base_tech + seat_talk_rules.way_rule(way) and k.for_rule(parties["design"]) == base_design
    goal_team.set_answers(root, parties["tech"], "choice")
    assert k.for_rule(parties["tech"]) == base_tech




# -- the locks ----------------------------------------------------------------------------------------------------------------------





# -- Silent -------------------------------------------------------------------------------------------------------------------------

def test_a_silent_leader_decides_its_question_and_the_veto_card_is_kept_with_its_pick(host, parties, model):
    _silent(host, parties)
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Where do the rooms live?", pick=1, choices=("rooms.ts", "a new file"))], "second_round": False}
    model.said[("talk_round", parties["product"])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Who is it for?")], "second_round": False}
    slug = _talk(host, parties, ["product", "tech"])
    rec = idea_questions.record(host.ideas.state_dir, slug)
    assert [c["q"] for c in rec["waiting"]] == ["Who is it for?"]                                                    # the person's leader asks; the silent one decided
    row = _decided(host, slug)
    assert len(row) == 1 and row[0]["q"] == "Where do the rooms live?" and row[0]["answer"] == "a new file" and row[0]["party"] == parties["tech"] and row[0]["why"] == "because"
    assert any(d["answer"] == "a new file" for d in rec["defaults"])                                                 # as any card left to its leader's pick
    node = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == slug)
    assert [d["id"] for d in node["decided"]] == [row[0]["id"]]                                                      # the hand's veto card reads the Board's row


def test_a_silent_leader_never_decides_a_lock_it_asks_it_and_says_why(host, parties, model):
    _silent(host, parties)
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "second_round": False, "questions": [
        card("Merge it into main now?", choices=("Yes, merge", "Not yet")), card("Take the paid cloud run?", choices=("Yes", "No")), card("Where do the rooms live?")]}
    slug = _talk(host, parties, ["tech"])
    rec = idea_questions.record(host.ideas.state_dir, slug)
    asked = {c["q"]: c.get("lock") for c in rec["waiting"]}
    assert asked == {"Merge it into main now?": "going into main", "Take the paid cloud run?": "money above what was agreed"}
    assert [d["q"] for d in _decided(host, slug)] == ["Where do the rooms live?"]                                   # only the one that is no lock




def test_a_choice_leader_decides_nothing_for_the_person(host, parties, model):
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Where do the rooms live?")], "second_round": False}
    slug = _talk(host, parties, ["tech"])
    assert _decided(host, slug) == [] and [c["q"] for c in idea_questions.record(host.ideas.state_dir, slug)["waiting"]] == ["Where do the rooms live?"]


def test_accepted_leaves_the_decision_as_it_stands_and_the_card_goes(host, parties, model):
    _silent(host, parties)
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Where do the rooms live?")], "second_round": False}
    _round_one(model, parties)
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Where do the rooms live?")], "second_round": False}
    slug = _talk(host, parties, ["product", "tech"])
    qid = _decided(host, slug)[0]["id"]
    host.command("ideas.decided_accept", {"idea": slug, "id": qid})
    assert _decided(host, slug) == [] and any(d["id"] == qid for d in idea_questions.record(host.ideas.state_dir, slug)["defaults"])
    with pytest.raises(Exception, match="not there"):
        host.command("ideas.decided_accept", {"idea": slug, "id": qid})


def test_replay_brings_the_question_back_with_its_ways_and_undoes_the_decision(host, parties, model):
    _silent(host, parties)
    _round_one(model, parties)
    model.said[("talk_round", parties["tech"])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Where do the rooms live?", choices=("rooms.ts", "a new file"))], "second_round": False}
    slug = _talk(host, parties, ["product", "tech"])
    qid = _decided(host, slug)[0]["id"]
    assert _state(host, slug)["state"] == "talk"
    host.command("ideas.decided_replay", {"idea": slug, "id": qid})
    rec = idea_questions.record(host.ideas.state_dir, slug)
    back = next(c for c in rec["waiting"] if c["id"] == qid)
    assert back["choices"] == ["rooms.ts", "a new file"] and back["replayed"] is True and rec["done"] is False
    assert _decided(host, slug) == [] and all(d["id"] != qid for d in rec["defaults"])                               # no longer decided: the person answers it




# -- the Fork -----------------------------------------------------------------------------------------------------------------------

def _fork(host, parties, model, who="tech"):
    goal_team.set_answers(host.ideas.root(), parties[who], "fork")
    model.said[("talk_round", parties[who])] = {"stance": "s", "for": "f", "against": "a", "questions": [card("Where do the rooms live?", choices=("rooms.ts", "a new file"))], "second_round": False}


def test_a_fork_is_one_more_call_a_question_at_the_elder_tier_its_lines_and_its_price_on_the_card(host, parties, model):
    _fork(host, parties, model)
    model.said[("fork", parties["tech"])] = {"ways": [{"gain": "nothing moves", "cost": "grows the file", "risk": "low"}, {"gain": "a clean seam", "cost": "a day", "risk": "a merge"}]}
    slug = _talk(host, parties, ["tech"])
    calls = model.steps("fork")
    assert len(calls) == 1 and calls[0]["tier"] == "elder" and calls[0]["tools"] is False and calls[0]["party"] == parties["tech"]      # one call a question, in its leader's voice
    assert "Where do the rooms live?" in calls[0]["prompt"] and "rooms.ts" in calls[0]["prompt"]
    c = idea_questions.record(host.ideas.state_dir, slug)["waiting"][0]
    assert c["lines"] == ["Gain nothing moves; cost grows the file; risk low", "Gain a clean seam; cost a day; risk a merge"] and all(len(x) <= 80 for x in c["lines"])
    assert c["fork"] == answer_ways.fork_price("balance") and c["fork"]["high"] >= calls[0]["budget"] - 0.01                      # its price, the cap of the call




