"""One word for each concept: an ork's orkish name when it says who, a plain one when it says what a thing does."""
from __future__ import annotations

from orkboard.realm import lexicon


def test_a_concept_has_one_word():
    assert lexicon.term("ork") == "ork" and lexicon.term("ork", many=True) == "orks"
    assert lexicon.term("orc.fields") == "Taskmaster" and lexicon.term("orc.barracks", many=True) == "Grunts"   # the orks by their orkish names
    assert lexicon.term("war_horn") == "Stop all"                                                               # the rest by what it does
    assert lexicon.term("chore", many=True) == "to-dos"


def test_an_old_spelling_reads_in_todays_word():
    say = lexicon.words
    assert say("Orks wait for the Taskmaster") == "Orks wait for the Taskmaster"      # who keeps its word
    assert say("🧭 TRACKS") == "🧭 PARTIES"
    assert say("📯 War Horn") == "📯 Stop all" and say("Halt All") == "Stop all"
    assert say("Pair a War Raven") == "Pair a Phone"


def test_a_word_inside_another_stays():
    say = lexicon.words
    assert say("Orkboard: teamwork, a roadmap, a racetrack") == "Orkboard: teamwork, a roadmap, a racetrack"
    assert say("the goldfish") == "the goldfish"


def test_the_gui_gets_every_spelling():
    table = dict(lexicon.table())
    assert table["War Horn"] == "Stop all" and table["Chores"] == "To-dos"
    assert table["TRACKS"] == "PARTIES"
    assert "orks" not in table and "Taskmaster" not in table and "party" not in table   # nothing to change
    assert table["War Raven"] == "Phone" and table["WAR RAVEN"] == "PHONE"


def test_a_path_is_not_a_concept():
    say = lexicon.words
    assert say("./ideas/ and ideas/screenshots, src/tracks.py") == "./ideas/ and ideas/screenshots, src/tracks.py"
    assert say("the idea.") == "the goal."








def test_what_was_a_goal_is_a_party_and_what_was_an_idea_is_a_goal():
    """Decisions §63.1: the interface says party for the code's track (a goal's page) and goal for the code's idea. A goal is
    today's word, never an old spelling; `idea` keeps its own (the interface says an old *idea* in today's word) and `track` its."""
    say = lexicon.words
    assert lexicon.term("track") == "party" and lexicon.term("track", many=True) == "parties"
    assert lexicon.term("idea") == "goal" and lexicon.term("idea", many=True) == "goals"
    assert lexicon.term("party") == "party" and lexicon.term("party", many=True) == "parties"      # the members, unchanged
    assert say("the goal") == "the goal" and say("Goal") == "Goal"                                  # "Goal" is no longer the Target's old word
    assert say("your tracks") == "your parties" and say("Track") == "Party"
    assert say("New idea") == "New goal" and say("3 ideas") == "3 goals"                            # an old idea in today's word (spec 50 §2.1)
    rows = {key: (word, was) for key, word, was in lexicon.glossary()}
    assert rows["track"] == ("party", "track") and rows["idea"] == ("goal", "idea") and rows["steward_goal"] == ("Target", "")
    assert rows["flag"] == ("flag", "") and rows["pick"] == ("pick", "")                            # spec 51: the stop Pick one
    assert lexicon.term("pick") == "pick" and lexicon.term("pick", many=True) == "picks"
    table = dict(lexicon.table())
    assert table["track"] == "party" and table["Tracks"] == "Parties" and "Goal" not in table and "goal" not in table






















def test_the_table_and_the_hand_are_the_words_of_spec_98():
    """Spec 98 §2.4: each word of the frame has its key, today's word and no old spelling; each is one line of `TERMS`."""
    keys = {"table": "table", "hand": "hand", "discard": "discard", "lane": "lane", "blank_card": "blank card",
            "lifted_card": "lifted card", "seat": "seat", "squad": "squad", "size": "size",
            "to_main": "To main"}
    rows = {key: (word, was) for key, word, was in lexicon.glossary()}
    for key, word in keys.items():
        assert lexicon.term(key) == word and rows[key] == (word, ""), key
    assert rows["map"] == ("table", "map")                                  # spec 150 C.1: what a tab shows is its table; `map` is the old spelling
    assert (lexicon.term("map"), lexicon.term("map", many=True)) == ("table", "tables")
    assert lexicon.words("Open Tech's map to pick; two maps") == "Open Tech's table to pick; two tables"
    assert lexicon.words("a lens, a view, a pitch_view") == "a lens, a view, a pitch_view"
    assert lexicon.term("lane", many=True) == "lanes"
    from pathlib import Path
    lines = "\n".join(Path(f).read_text(encoding="utf-8") for f in lexicon.SOURCES).splitlines()
    for key in (*keys, "map"):
        line = next(l for l in lines if l.lstrip().startswith(f'_t("{key}"'))
        assert "#" in line, key




def test_the_route_and_the_phases_are_the_words_of_spec_99_c():
    """Spec 99 §10: the words of a goal's way, each with its key, today's word and no old spelling; each is one line of `TERMS` with its meaning."""
    keys = {"route": "route", "route_card": "route card", "step": "step", "phase": "phase", "phase.talk": "Talk", "phase.spec": "Spec",
            "phase.work": "Work", "phase.done": "Done", "section": "section", "project_stage": "stage", "will_be": "Will be", "fork": "fork",
            "out_of_contract": "out of the contract", "release_version": "Release a version", "other_choice": "Other…"}
    rows = {key: (word, was) for key, word, was in lexicon.glossary()}
    for key, word in keys.items():
        assert lexicon.term(key) == word and rows[key] == (word, ""), key
    assert rows["map"] == ("table", "map")                                  # spec 150 C.1: what a tab shows is its table; `map` is the old spelling
    assert (lexicon.term("map"), lexicon.term("map", many=True)) == ("table", "tables")
    assert lexicon.words("Open Tech's map to pick; two maps") == "Open Tech's table to pick; two tables"
    assert lexicon.words("a lens, a view, a pitch_view") == "a lens, a view, a pitch_view"
    assert lexicon.term("route", many=True) == "routes" and lexicon.term("step", many=True) == "steps" and lexicon.term("fork", many=True) == "forks"
    assert lexicon.term("stage") == "stage" and lexicon.term("project_stage") == "stage"          # a party's stage (spec 48) and the project's (spec 99 §1) are two concepts
    from pathlib import Path
    lines = "\n".join(Path(f).read_text(encoding="utf-8") for f in lexicon.SOURCES).splitlines()
    for key in keys:
        assert "#" in next(l for l in lines if l.lstrip().startswith(f'_t("{key}"')), key
    assert lexicon.words("the route, Talk, Spec, Work and Done") == "the route, Talk, Spec, Work and Done"      # nothing changes: these have no old spelling


def test_the_inbox_and_the_taken_are_the_words_of_spec_136():
    """Spec 136 D: each word has its key, today's word and no old spelling; each is one line of `TERMS` with its meaning."""
    keys = {"inbox": "inbox", "taken": "taken", "waiting_to_be_taken": "Waiting to be taken", "as_of": "As of"}
    rows = {key: (word, was) for key, word, was in lexicon.glossary()}
    for key, word in keys.items():
        assert lexicon.term(key) == word and rows[key] == (word, ""), key
    assert rows["map"] == ("table", "map")                                  # spec 150 C.1: what a tab shows is its table; `map` is the old spelling
    assert (lexicon.term("map"), lexicon.term("map", many=True)) == ("table", "tables")
    assert lexicon.words("Open Tech's map to pick; two maps") == "Open Tech's table to pick; two tables"
    assert lexicon.words("a lens, a view, a pitch_view") == "a lens, a view, a pitch_view"
    assert lexicon.term("inbox", many=True) == "inboxes"
    from pathlib import Path
    lines = "\n".join(Path(f).read_text(encoding="utf-8") for f in lexicon.SOURCES).splitlines()
    for key in keys:
        assert "#" in next(l for l in lines if l.lstrip().startswith(f'_t("{key}"')), key












