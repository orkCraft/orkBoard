"""Spec 131 B.1, B.3 and B.4 (docs/specs/131-a-leaders-slices-and-the-cascade.md; decisions §233.5–§233.9, §237.6) on the store alone: `clean_proposal`, the store, `rows` (one line when all agree, the forks first when not),
the words. No model, no keeper."""
from __future__ import annotations

import json

from orkboard.realm import cascades, event_log, idea_spend, idea_target, lexicon, slices

STANDING = [{"id": "s-aaaa1111", "party": "tech", "decision": 6, "points": ["6.2", "6.3"], "says": "Your builds are quick.", "was": "", "at": "", "replaced_by": "", "folded": False}]


def _proposal(**over):
    return {"slice": "s-aaaa1111", "says": "Your builds are quick and cached.", "why": "The cache ran into it.", "points": ["6.2"], **over}


# -- clean_proposal -----------------------------------------------------------------------------------------------------------------------

def test_a_proposal_is_a_standing_slice_of_the_answering_party_with_words():
    got = cascades.clean_proposal(_proposal(says="  Your builds   are quick\nand cached. " + "x" * 400, why="y" * 500), "tech", STANDING)
    assert got["slice"] == "s-aaaa1111" and got["points"] == ["6.2"] and "\n" not in got["says"]
    assert len(got["says"]) <= slices.SAYS_CHARS and len(got["why"]) <= cascades.WHY_CHARS


def test_another_partys_slice_a_replaced_slice_and_no_words_drop_the_proposal():
    assert cascades.clean_proposal(_proposal(), "design", STANDING) is None                         # another party's slice
    replaced = [{**STANDING[0], "replaced_by": "s-bbbb2222"}]
    assert cascades.clean_proposal(_proposal(), "tech", replaced) is None                           # a replaced slice
    assert cascades.clean_proposal(_proposal(slice="s-unknown"), "tech", STANDING) is None
    for bad in ({"says": ""}, {"why": " "}, {"says": "Your builds are quick."}):                    # no words, no reason, no change
        assert cascades.clean_proposal(_proposal(**bad), "tech", STANDING) is None
    for raw in (None, "text", [], 5):
        assert cascades.clean_proposal(raw, "tech", STANDING) is None


def test_the_points_default_to_the_slices_own_and_only_its_own_are_kept():
    assert cascades.clean_proposal(_proposal(points=None), "tech", STANDING)["points"] == ["6.2", "6.3"]
    assert cascades.clean_proposal(_proposal(points=["9.9", "6.3", "x"]), "tech", STANDING)["points"] == ["6.3"]
    assert cascades.clean_proposal(_proposal(points=["9.9"]), "tech", STANDING)["points"] == ["6.2", "6.3"]
    assert cascades.clean_proposal(_proposal(points=["6"]), "tech", STANDING)["points"] == ["6"]            # the decision as a whole is the same place


def test_an_answer_is_agrees_or_disagrees_and_a_disagreement_has_its_reason():
    assert cascades.clean_answer({"answer": "agrees", "says": " Art  fits. ", "why": "ok"}, "Art held.") == {"answer": "agrees", "says": "Art fits.", "why": "ok"}
    assert cascades.clean_answer({"answer": "agrees"}, "Art held.")["says"] == "Art held."          # it stands as it is
    assert cascades.clean_answer({"answer": "disagrees", "why": "Cost."}, "x") == {"answer": "disagrees", "says": "", "why": "Cost."}
    for bad in ({"answer": "disagrees"}, {"answer": "maybe"}, {}, None, "agrees"):
        assert cascades.clean_answer(bad, "x") is None


# -- the store ----------------------------------------------------------------------------------------------------------------------------

def test_the_store_from_nothing_keeps_a_record_and_reads_it_back(tmp_path):
    assert cascades.read(tmp_path) == [] and cascades.get(tmp_path, "c-1") is None and cascades.open_for(tmp_path, "s-aaaa1111") is None
    rec = cascades.add(tmp_path, "tech", cascades.clean_proposal(_proposal(), "tech", STANDING), "section", "a-goal", "Your builds are quick.")
    assert rec["id"].startswith("c-") and rec["status"] == "asking" and rec["from_step"] == "section" and rec["idea"] == "a-goal" and rec["changed"] == ["6.2"]
    assert cascades.get(tmp_path, rec["id"])["says"] == "Your builds are quick and cached."
    assert cascades.open_for(tmp_path, "s-aaaa1111")["id"] == rec["id"]
    cascades.save(tmp_path, {**rec, "status": "ready"})
    assert [r["status"] for r in cascades.read(tmp_path)] == ["ready"] and cascades.open_for(tmp_path, "s-aaaa1111") is not None
    cascades.save(tmp_path, {**rec, "status": "put_back"})
    assert cascades.open_for(tmp_path, "s-aaaa1111") is None                                        # put back: the slice may be proposed on again
    assert cascades.drop(tmp_path, rec["id"]) is True and cascades.drop(tmp_path, rec["id"]) is False and cascades.read(tmp_path) == []


def test_a_broken_file_reads_as_none_and_a_line_that_is_no_record_is_left_out(tmp_path):
    (tmp_path / cascades.FILE).write_text("{not json", encoding="utf-8")
    assert cascades.read(tmp_path) == []
    (tmp_path / cascades.FILE).write_text(json.dumps({"cascades": [{"id": "c-1", "status": "ready"}, {"id": 5}, "x", {"id": "c-2", "status": "weird"}]}), encoding="utf-8")
    assert [r["id"] for r in cascades.read(tmp_path)] == ["c-1"]


def test_the_closed_cascades_are_kept_only_so_many(tmp_path):
    prop = cascades.clean_proposal(_proposal(), "tech", STANDING)
    for _ in range(cascades.KEEP_CLOSED + 5):
        rec = cascades.add(tmp_path, "tech", prop, "ask")
        cascades.save(tmp_path, {**rec, "status": "confirmed"})
    live = cascades.add(tmp_path, "tech", prop, "ask")
    rows = cascades.read(tmp_path)
    assert len(rows) == cascades.KEEP_CLOSED + 1 and rows[-1]["id"] == live["id"]


# -- the rows -----------------------------------------------------------------------------------------------------------------------------

def _ready(tmp_path, steps=(), forks=(), stopped="", **over):
    rec = cascades.add(tmp_path, "tech", cascades.clean_proposal(_proposal(), "tech", STANDING), "section", "", "Your builds are quick.")
    rec = {**rec, "status": "ready", "steps": list(steps), "forks": list(forks), "stopped": stopped, "cost": 0.07,
           "decision": {"title": "Builds are cached", "text": "Why: x\n\n1. One.", "changes": [6]}, **over}
    return cascades.save(tmp_path, rec)


def _step(party, answer="agrees", says="New.", changed=True, forked=False, n=1):
    return {"n": n, "party": party, "slice": f"s-{party}", "answer": answer, "says": says, "why": "", "cost": 0.01, "before": "Old.", "points": ["6.2"], "changed": changed, "forked": forked}


def test_a_cascade_ready_is_one_line_when_all_agree_and_the_chain_is_under_more(tmp_path):
    _ready(tmp_path, steps=[_step("design", says="Art draws it cached."), _step("marketing", changed=False, n=2)])
    (row,) = cascades.rows(tmp_path)
    assert row["kind"] == "cascade" and row["title"] == "Builds are cached" and row["text"] == row["title"] and row["level"] == "decision"
    assert row["line"] == "tech, design and marketing agree"                                      # a leader that agreed and left its slice as it is agrees too
    assert [(c["party"], c["before"], c["after"]) for c in row["chain"]] == [("tech", "Your builds are quick.", "Your builds are quick and cached."), ("design", "Old.", "Art draws it cached.")]
    assert row["forks"] == [] and row["stopped"] == "" and row["cost"] == 0.07 and row["blocks"] is False
    assert row["proposal"] == {"party": "tech", "says": "Your builds are quick and cached.", "why": "The cache ran into it.", "before": "Your builds are quick."}
    assert row["pulls"]["level"] == "decision" and row["sections"] == []


def test_the_line_is_the_agreeing_leaders_in_the_words_of_the_lexicon(tmp_path):
    _ready(tmp_path, steps=[_step("design")])
    assert cascades.rows(tmp_path)[0]["line"] == lexicon.term("agree_line").replace("<A> and <B>", "tech and design")

def test_a_cascade_that_asked_no_one_says_who_proposes(tmp_path):
    _ready(tmp_path)
    assert cascades.rows(tmp_path)[0]["line"] == "tech proposes"                                    # no one else was asked


def test_the_forks_come_first_when_a_leader_disagrees(tmp_path):
    fork = {"party": "design", "slice": "s-design", "says": "", "now": "Art holds.", "why": "It breaks the look."}
    _ready(tmp_path, steps=[_step("design", answer="disagrees", forked=True), _step("marketing", n=2)], forks=[fork], stopped="Stopped after 3 steps: Run was not asked")
    (row,) = cascades.rows(tmp_path)
    assert row["line"] == "design disagrees: It breaks the look." and " agree" not in row["line"]
    assert row["forks"] == [{**fork, "name": "design"}] and row["stopped"] == "Stopped after 3 steps: Run was not asked"
    assert [c["party"] for c in row["chain"]] == ["tech", "marketing"]                              # the disagreeing leader's slice does not change


def test_only_the_cascades_ready_are_rows_and_the_names_are_the_partys(tmp_path):
    for status in ("asking", "failed", "confirmed", "put_back"):
        _ready(tmp_path, status=status)
    assert cascades.rows(tmp_path) == []
    _ready(tmp_path)
    assert len(cascades.rows(tmp_path)) == 1


def test_a_row_is_not_lost_to_its_price(tmp_path, monkeypatch):
    from orkboard.realm import way_down
    _ready(tmp_path)
    monkeypatch.setattr(way_down, "pulls", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    (row,) = cascades.rows(tmp_path, tmp_path)
    assert row["pulls"] == way_down.empty("decision") and row["usd_low"] == 0.0


def test_the_stopped_words_say_who_was_not_asked():
    assert cascades.stopped_words("steps", 3, ["Marketing"]) == "Stopped after 3 steps: Marketing was not asked"
    assert cascades.stopped_words("steps", 3, ["Marketing", "Run"]) == "Stopped after 3 steps: Marketing and Run were not asked"
    assert cascades.stopped_words("price", 2, ["Run"]) == "Stopped at its price: Run was not asked"


# -- the words and the tables ---------------------------------------------------------------------------------------------------------------

def test_the_words_of_b_are_kept_in_the_lexicon_and_the_step_has_its_tables():
    rows = {key: (word, was) for key, word, was in lexicon.glossary()}
    assert rows["cascade"] == ("cascade", "") and lexicon.term("cascade", many=True) == "cascades"
    for key, word in (("proposes", "Proposes"), ("agrees", "Agrees"), ("disagrees", "Disagrees"), ("stopped_after_steps", "Stopped after <n> steps"), ("agree_line", "<A> and <B> agree"),
                      ("answer_the_fork_first", "Answer the fork first")):
        assert rows[key] == (word, ""), key
    from pathlib import Path
    lines = "\n".join(Path(f).read_text(encoding="utf-8") for f in lexicon.SOURCES).splitlines()
    for key in ("cascade", "proposes", "agrees", "disagrees", "stopped_after_steps", "agree_line", "answer_the_fork_first"):
        assert "#" in next(line for line in lines if line.lstrip().startswith(f'_t("{key}"')), key
    for target in idea_target.TARGETS:
        assert idea_target.pick("cascade", target) == idea_target.pick("slice_digest", target)
    assert idea_target.READS["cascade"] == 0 and idea_target.CONTEXT["cascade"] == 3_000 and idea_target.CAPS["cascade"] <= 0.10 and idea_spend.STEP_STAGE["cascade"] == "spec"
    assert set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for name in ("SLICE_PROPOSED", "CASCADE_READY", "CASCADE_CONFIRMED", "CASCADE_PUT_BACK"):
        assert getattr(event_log, name) in event_log.EVENTS
