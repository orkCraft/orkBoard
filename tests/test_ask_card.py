"""Spec 168 D3 (decisions §283.20): the quick question as the card of the kind ?. Its route (the open tab's leader; on the Orkmaster's tab the Orkmaster, or one hop to the leader whose part it
is), its one call on the cheaper tier with no reads, the three ways of the card it comes back as, and the `asked` line in the leader's journal (the project's for the Orkmaster's own answer).
The model call is stubbed as in tests/test_idea_ask.py."""
from __future__ import annotations


from orkboard.realm import board_ask, event_log, idea_target, ideas, journals
from tests.test_idea_ask import ANSWER, Model, _ask, _events, _party, _rec, _wait, host, model, product, tech  # noqa: F401


def test_a_party_tab_goes_to_its_leader_and_the_orkmasters_tab_to_the_orkmaster_or_one_hop(host, product, tech):
    root = host.ideas.root()
    assert board_ask.route(root, tech, "Where is the lobby?") == (tech, False)                              # the open tab's leader, whatever the words say
    assert board_ask.route(root, tech, "What does product think?") == (tech, False)
    assert board_ask.route(root, "", "Where is the lobby?") == ("", False)                                  # names no party: the Orkmaster
    assert board_ask.route(root, "", "Why did Tech choose a file for it?") == (tech, True)                  # names one party: one hop to its leader
    assert board_ask.route(root, "", "Does tech or product own the lobby?") == ("", False)                  # two: the Orkmaster itself
    assert board_ask.route(root, "", "Is technology fine?") == ("", False)                                  # a word that only begins like a party is not a party


def test_a_hop_is_one_call_by_the_named_leader_and_the_record_says_where_it_was_asked(host, product, tech, model):
    _ask(host, "", "Why did Tech choose a file for the lobby?")
    (call,) = model.calls
    assert call["key"] == f"goal:{tech}" and call["as_role"] == "" and call["step"] == "ask" and call["tools"] is False
    rec = _rec(host)
    assert rec["status"] == "answered" and rec["party"] == tech and rec["tab"] == "" and rec["hop"] is True
    (ev,) = _events(host, event_log.BOARD_ASKED)
    assert ev["party"] == tech and ev["tab"] == "orkmaster" and ev["hop"] is True


def test_the_orkmasters_own_answer_and_a_partys_are_one_call_each_on_the_cheaper_tier_and_read_nothing(host, product, tech, model):
    _ask(host, "", "Where is the lobby?")
    _ask(host, tech, "Why is the lobby here?")
    assert len(model.calls) == 2 and all(c["step"] == "ask" and c["tools"] is False for c in model.calls)
    assert idea_target.READS["ask"] == 0
    for target in idea_target.TARGETS:
        assert idea_target.pick("ask", target) == idea_target.pick("rewrite", target)                       # the tier `rewrite` chooses
    assert {(c["tier"], c["effort"]) for c in model.calls} == {idea_target.pick("ask", "balance")} == {("warrior", "low")}
    assert [_rec(host)[k] for k in ("party", "tab", "hop")] == [tech, tech, False]




def test_the_answer_is_kept_in_the_leaders_journal_as_asked_and_the_orkmasters_in_the_projects_not_on_the_board(host, product, tech, model):
    state = host.ideas.state_dir
    _ask(host, tech, "Why is the lobby here?")
    (line,) = [e for e in journals.read(state, tech) if e["kind"] == "asked"]
    assert line["text"].startswith("Asked: Why is the lobby here? — Lobby waits for Reconnect.") and len(line["text"]) <= journals.TEXT_CHARS and line["idea"] == ""
    assert journals.read(state, journals.PROJECT) == [] or all(e["kind"] != "asked" for e in journals.read(state, journals.PROJECT))
    _ask(host, "", "Where is the lobby?")
    (mine,) = [e for e in journals.read(state, journals.PROJECT) if e["kind"] == "asked"]
    assert mine["text"].startswith("Asked: Where is the lobby? — ")
    assert "asked" in journals.LEADER_KINDS and "asked" in journals.PROJECT_KINDS
    assert ideas.ideas(host.ideas.root()) == [] and "Where is the lobby?" not in str(host.command("ideas.board"))        # no goal, nothing on the Board




