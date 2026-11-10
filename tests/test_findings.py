"""Spec 132 D.1, D.3 (docs/specs/132-four-levels-the-way-down-and-findings.md; decisions §234.3–§234.4, §237.1–§237.2, §237.8): the store of findings and a goal's quality record, the hand's rows (one quality card a goal,
its findings in the order of their level, a finding of no goal its own row), the answers and the words. No model is called."""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

from orkboard.core import idea_keeper
from orkboard.gui.board_host import Orkboard
from orkboard.realm import findings, goal_team, idea_route, ideas, lexicon, library, spec_sections, way_down


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def tech(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, ["grunt", "tester", "architect"])
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    goal_team.set_team(root, slug, ["grunt", "tester"], leader="architect")
    return slug


def _goal(host, party, title="show the winner", state="done"):
    root, st = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, title, party, st)
    ideas.save_state(st, slug, state=state)
    return slug


def _add(host, slug, source="verdict", on="src/results", **kw):
    return findings.add(host.ideas.state_dir, {"source": source, "idea": slug, "party": kw.pop("party", "tech"), "on": on, "found": kw.pop("found", f"Not quite: changed {on}"), **kw})


def _sorted(host, slug, f, level, change=""):
    sd = host.ideas.state_dir
    findings.told(sd, slug, f["id"], {"what": f["found"], "cause": "because"})
    return findings.sorted_(sd, slug, f["id"], level, change)


# -- the store ---------------------------------------------------------------------------------------------------------------------------------

def test_a_thing_is_kept_once_by_its_source_its_part_and_its_goal(host, tech):
    slug = _goal(host, tech)
    first = _add(host, slug)
    again = _add(host, slug, found="another way of saying it")
    assert first["id"] == again["id"] and again["found"] == first["found"]
    assert len(findings.of_goal(host.ideas.state_dir, slug)) == 1
    assert _add(host, slug, on="src/other")["id"] != first["id"]                                   # another part: another finding
    assert _add(host, slug, source="lens")["id"] != first["id"]                                    # another source: another finding
    assert _add(host, "")["id"] != first["id"]                                                     # no goal: another finding
    assert findings.add(host.ideas.state_dir, {"source": "nonsense", "idea": slug, "on": "x", "found": "y"}) is None
    assert findings.add(host.ideas.state_dir, {"source": "verdict", "idea": slug, "on": "x", "found": ""}) is None


def test_a_finding_has_the_shape_of_d1_and_code_words_are_its_what_until_its_leader_tells_it(host, tech):
    f = _add(host, _goal(host, tech))
    assert set(f) == {"id", "at", "source", "idea", "party", "on", "found", "what", "shows", "promised", "cause", "level", "change", "status", "answer", "fix"}
    assert f["what"] == f["found"] and f["status"] == "found" and f["level"] == "" and f["answer"] == "" and f["fix"] is None and f["id"].startswith("f-")


def test_a_goals_record_is_quality_json_in_its_state_folder_and_that_of_no_goal_is_findings_json(host, tech):
    sd = host.ideas.state_dir
    slug = _goal(host, tech)
    _add(host, slug)
    _add(host, "", source="concern", on="c-1")
    mine = json.loads((ideas.state_folder(sd, slug) / "quality.json").read_text(encoding="utf-8"))
    assert set(mine) == {"verdict", "checks", "findings", "hypothesis", "at", "status"} and len(mine["findings"]) == 1 and mine["hypothesis"] is None
    loose = json.loads((sd / "findings.json").read_text(encoding="utf-8"))
    assert set(loose) == {"findings"} and loose["findings"][0]["source"] == "concern"
    assert findings.record(sd, "nothing-here") == {"verdict": [], "checks": [], "findings": [], "hypothesis": None, "at": "", "status": ""}


def test_way_down_reads_the_record_and_a_finding_answered_is_not_open(host, tech):
    sd = host.ideas.state_dir
    slug = _goal(host, tech)
    assert "quality" not in way_down.open_levels(sd, slug)
    f = _add(host, slug)
    assert "quality" in way_down.open_levels(sd, slug)
    findings.answer(sd, f["id"], "later")
    assert "quality" not in way_down.open_levels(sd, slug)
    assert findings.open_of_goal(sd, slug) == [] and len(findings.of_goal(sd, slug)) == 1               # put off: still on the record


def test_each_status_in_turn_and_the_answers(host, tech):
    sd = host.ideas.state_dir
    slug = _goal(host, tech)
    f = _add(host, slug)
    got = findings.told(sd, slug, f["id"], {"what": "The list is plain", "shows": "the screen", "promised": "a winner first", "cause": "nobody sorted it\nat all"})
    assert got["status"] == "told" and got["what"] == "The list is plain" and got["cause"] == "nobody sorted it at all"
    got = findings.sorted_(sd, slug, f["id"], "spec", "say the order in the section")
    assert got["status"] == "sorted" and got["level"] == "spec" and got["change"] == "say the order in the section"
    assert findings.sorted_(sd, slug, f["id"], "nonsense")["level"] == "work"                          # a level that is none of the three is work
    moved = findings.move(sd, f["id"], "decision")
    assert moved["level"] == "decision" and moved["answer"] == "moved" and moved["status"] == "sorted"       # moved by the person: it still waits
    with pytest.raises(ValueError):
        findings.move(sd, f["id"], "up")
    done = findings.answer(sd, f["id"], "fix", {"idea": "fix-the-list"})
    assert done["status"] == "answered" and done["answer"] == "fix" and done["fix"] == {"idea": "fix-the-list"}
    with pytest.raises(ValueError):
        findings.answer(sd, f["id"], "moved")
    assert findings.get(sd, f["id"])["answer"] == "fix" and findings.get(sd, "f-none") is None


# -- the calls' answers --------------------------------------------------------------------------------------------------------------------------

def test_a_leaders_answer_is_read_strictly():
    ids = ["f-1", "f-2"]
    got = findings.clean_told({"findings": [{"id": "f-1", "what": "  a\nb ", "shows": "x" * 900, "promised": 3, "cause": "c"}, {"id": "f-9", "what": "not asked"}, {"id": "f-2"}, "junk"]}, ids)
    assert got["f-1"]["what"] == "a b" and len(got["f-1"]["shows"]) == findings.LINE_CHARS and got["f-1"]["promised"] == "" and "f-9" not in got and "f-2" not in got
    assert findings.clean_told({"nothing": 1}, ids) is None and findings.clean_told(None, ids) is None


def test_the_orkmasters_answer_is_read_strictly():
    got = findings.clean_levels({"levels": [{"id": "f-1", "level": "decision", "change": "word it again"}, {"id": "f-2", "level": "heaven"}, {"id": "f-3", "level": "spec"}]}, ["f-1", "f-2"])
    assert got == {"f-1": {"level": "decision", "change": "word it again"}, "f-2": {"level": "work", "change": ""}}
    assert findings.clean_levels({"levels": "no"}, ["f-1"]) is None


# -- when a goal's findings are in -------------------------------------------------------------------------------------------------------------------

def test_a_goals_findings_are_in_after_a_day_or_when_its_checks_and_looks_are(host, tech):
    sd = host.ideas.state_dir
    slug = _goal(host, tech)
    assert findings.ripe(sd, "")                                                                      # a finding of no goal waits for no one
    _add(host, slug)
    assert not findings.ripe(sd, slug)                                                                # its verdict was not read
    findings.save_record(sd, slug, at=dt.datetime.now().isoformat(timespec="seconds"))
    assert not findings.ripe(sd, slug)                                                                # no look of the party's lens since
    findings.save_record(sd, slug, at=(dt.datetime.now() - dt.timedelta(hours=findings.QUIET_H + 1)).isoformat(timespec="seconds"))
    assert findings.ripe(sd, slug)                                                                    # a day has passed
    from orkboard.realm import concerns
    findings.save_record(sd, slug, at=(dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds"))
    concerns.save(sd, tech, status="ready", at=dt.datetime.now().isoformat(timespec="seconds"))
    assert findings.ripe(sd, slug)                                                                    # the lens looked after the verdict
    ideas._write_json(ideas.state_folder(sd, slug) / "plan.json", {"idea": slug, "tasks": [{"id": "k1", "kind": "review", "state": "running"}]})
    from orkboard.realm import idea_checks
    assert "review" in idea_checks.TAGS
    assert not findings.ripe(sd, slug)                                                                # a check task is still at work


def test_pending_names_the_goals_with_a_finding_not_told(host, tech):
    sd = host.ideas.state_dir
    slug = _goal(host, tech)
    f = _add(host, slug)
    _add(host, "", source="concern", on="c-1")
    assert set(findings.pending(sd)) == {slug, ""}
    findings.told(sd, slug, f["id"], {})
    assert findings.pending(sd) == [""]


# -- the hand's rows -----------------------------------------------------------------------------------------------------------------------------

def test_one_quality_card_a_goal_its_findings_in_the_order_of_their_level_and_never_urgent(host, tech):
    sd, root = host.ideas.state_dir, host.ideas.root()
    one, two = _goal(host, tech, "first goal"), _goal(host, tech, "second goal")
    work = _sorted(host, one, _add(host, one, on="a"), "work")
    dec = _sorted(host, one, _add(host, one, on="b"), "decision", "the decision was wrong")
    spec = _sorted(host, one, _add(host, one, on="c"), "spec")
    _add(host, one, on="d")                                                                          # found, not sorted: not on the card yet
    _sorted(host, two, _add(host, two, on="a"), "work")
    rows = [r for r in findings.rows(sd, root) if r["kind"] == "quality"]
    assert sorted(r["idea"] for r in rows) == sorted([one, two])                                       # one card a goal, not a card a finding
    card = next(r for r in rows if r["idea"] == one)
    assert [f["id"] for f in card["findings"]] == [dec["id"], spec["id"], work["id"]]                  # Decision first
    assert [f["level"] for f in card["findings"]] == ["decision", "spec", "work"]
    assert card["blocks"] is False and card["title"] == "first goal" and card["level"] == "decision"
    assert card["findings"][0]["change"] == "the decision was wrong" and card["findings"][0]["cause"] == "because"
    assert all(f["pulls"]["level"] == lv for f, lv in zip(card["findings"], ["decision", "spec", "work"]))
    assert card["pulls"]["estimate"]["usd_high"] == pytest.approx(sum(f["pulls"]["estimate"]["usd_high"] for f in card["findings"]), abs=0.02)


def test_a_finding_an_acceptance_told_is_a_card_in_the_hand_before_the_orkmaster_sorts_it(host, tech):
    sd, root = host.ideas.state_dir, host.ideas.root()
    slug = _goal(host, tech)
    f = _add(host, slug, source="accept", on="tech: look at Done when 1", found="Nobody could look at: The screen shows the winner")
    assert findings.rows(sd, root) == [], "found, not told: nothing yet"
    findings.told(sd, slug, f["id"], {"what": f["found"], "shows": "Done when 1", "promised": "The screen shows the winner"})
    rows = findings.rows(sd, root)
    assert [r["kind"] for r in rows] == ["quality"] and rows[0]["idea"] == slug and rows[0]["blocks"] is False
    assert [(x["id"], x["level"], x["source"], x["party"]) for x in rows[0]["findings"]] == [(f["id"], "work", "accept", "tech")], "no level yet: it reads as work"
    assert rows[0]["findings"][0]["promised"] == "The screen shows the winner"
    findings.sorted_(sd, slug, f["id"], "spec")
    assert findings.rows(sd, root)[0]["findings"][0]["level"] == "spec", "the Orkmaster's level replaces it; the card stays"
    findings.answer(sd, f["id"], "later")
    assert findings.rows(sd, root) == [], "answered: it leaves the hand"
    loose = findings.add(sd, {"source": "concern", "idea": "", "party": "tech", "on": "c-1", "found": "Results is slow"})
    findings.told(sd, "", loose["id"], {"what": "Results is slow"})
    assert [r["kind"] for r in findings.rows(sd, root)] == ["finding"], "a told finding of no goal is a row of its own"


def test_a_finding_of_no_goal_is_a_row_of_its_own_and_a_later_finding_joins_its_goals_card(host, tech):
    sd, root = host.ideas.state_dir, host.ideas.root()
    slug = _goal(host, tech)
    _sorted(host, slug, _add(host, slug, on="a"), "work")
    loose = _sorted(host, "", _add(host, "", source="concern", on="c-1", found="Results is slow"), "work")
    rows = findings.rows(sd, root)
    assert [r["kind"] for r in rows].count("quality") == 1 and [r["kind"] for r in rows].count("finding") == 1
    own = next(r for r in rows if r["kind"] == "finding")
    assert own["id"] == loose["id"] and own["idea"] == "" and own["blocks"] is False and own["level"] == "work" and "findings" not in own
    _sorted(host, slug, _add(host, slug, source="lens", on="c-9"), "work")                              # later: it joins the card
    rows = findings.rows(sd, root)
    assert len([r for r in rows if r["kind"] == "quality"]) == 1 and len(next(r for r in rows if r["kind"] == "quality")["findings"]) == 2


def test_not_now_takes_a_finding_out_of_the_hand_and_the_card_goes_with_its_last(host, tech):
    sd, root = host.ideas.state_dir, host.ideas.root()
    slug = _goal(host, tech)
    a = _sorted(host, slug, _add(host, slug, on="a"), "work")
    b = _sorted(host, slug, _add(host, slug, on="b"), "spec")
    findings.answer(sd, a["id"], "later")
    assert [f["id"] for f in findings.rows(sd, root)[0]["findings"]] == [b["id"]]
    findings.answer(sd, b["id"], "fix", {"idea": "x"})
    assert findings.rows(sd, root) == [] and len(findings.of_goal(sd, slug)) == 2                      # the record keeps both


def test_a_fix_pulls_what_is_below_its_level(host, tech):
    sd, root = host.ideas.state_dir, host.ideas.root()
    slug = _goal(host, tech)
    spec_sections.save_record(sd, slug, {"decision": {"title": "D", "text": "t", "number": 240, "confirmed": True, "changes": []}})
    f = _sorted(host, slug, _add(host, slug), "spec")
    got = findings.pulls_of(sd, root, f)
    assert got["level"] == "spec" and got["sections"] == [{"idea": slug, "party": tech}] and got["estimate"]["usd_high"] > 0           # the section written again
    assert findings.pulls_of(sd, root, f, "work")["level"] == "work" and findings.pulls_of(sd, root, f, "decision")["level"] == "decision"
    assert findings.pulls_of(sd, root, {**f, "idea": "gone", "party": "gone"}, "work")["level"] == "work"        # a read that fails pulls nothing, never an error


# -- the words ---------------------------------------------------------------------------------------------------------------------------------------

def test_the_words_of_spec_132_d6_are_in_the_glossary_and_the_mines_finding_keeps_its_own_key():
    rows = {key: (word, was) for key, word, was in lexicon.glossary()}
    assert rows["level"] == ("level", "") and rows["quality_finding"] == ("finding", "") and rows["finding"] == ("Finding", "") and rows["quality_record"] == ("quality record", "")
    assert lexicon.term("level", many=True) == "levels" and lexicon.term("quality_finding", many=True) == "findings" and lexicon.term("finding") == "Finding"
    said = {"level.decision": "Decision", "level.spec": "Spec", "level.work": "Work", "level.quality": "Quality", "quality_of": "Quality of", "found": "found", "fix_there": "Fix it there",
            "fix_all_there": "Fix all there", "another_level": "Another level…", "not_now": "Not now", "add_to_goal": "Add to the goal", "change_decision": "Change…",
            "or_say_change": "Or say what to change", "cause_in_code": "The cause is in the code", "cause_in_spec": "The cause is in the spec", "cause_in_decision": "The cause is in the decision"}
    for key, word in said.items():
        assert lexicon.term(key) == word, key
    lines = "\n".join(Path(f).read_text(encoding="utf-8") for f in lexicon.SOURCES).splitlines()
    for key in ("level", "finding", "quality_record"):
        assert "#" in next(l for l in lines if l.lstrip().startswith(f'_t("{key}"')), key


# -- spec 133 D: a refuted hypothesis is a finding of no goal, naming the goals that rested on it ----------------------------------------------------

def _refuted_item(**more):
    return {"id": "h4", "text": "A weekly push gets more goals landed, not only more opens", "signal": "people with the push land 20% more goals",
            "refuted": [{"name": "the hook", "when": "opens rise, goals landed do not", "change": ""}], "state": "refuted",
            "evidence": [{"text": "Opens up 30%, landed goals flat", "ref": "", "at": "2026-11-04"}], "verdict": {"state": "refuted", "why": "flat", "decision": 0, "way": "the hook", "at": "2026-11-04T10:00:00"}, **more}


def test_a_refuted_hypothesis_is_one_finding_of_no_goal_naming_the_goals_that_rested_on_it_and_kept_once(host):
    from orkboard.realm import findings_gather
    sd = host.ideas.state_dir
    got = findings_gather.hypothesis(sd, _refuted_item(), "product", [("weekly-digest", "A weekly digest"), ("push-settings", "Push settings")])
    assert got["source"] == "hypothesis" and got["idea"] == "" and got["on"] == "h4" and got["party"] == "product" and got["status"] == "found"
    assert got["found"].startswith("Refuted: A weekly push gets more goals landed") and "(the hook: opens rise, goals landed do not)" in got["found"]
    assert "Believed: people with the push land 20% more goals." in got["found"] and "Found: Opens up 30%, landed goals flat." in got["found"]
    assert "Goals that rested on it: weekly-digest (A weekly digest), push-settings (Push settings)." in got["found"] and len(got["found"]) <= findings.FOUND_CHARS
    assert [f["id"] for f in findings.of_goal(sd, "")] == [got["id"]]
    assert findings_gather.hypothesis(sd, _refuted_item(), "product", [("other", "Other")])["id"] == got["id"] and len(findings.of_goal(sd, "")) == 1          # kept once


def test_the_goals_names_stay_in_the_finding_when_the_words_are_long_and_a_hypothesis_not_refuted_is_none(host):
    from orkboard.realm import findings_gather
    sd = host.ideas.state_dir
    long = "word " * 80
    got = findings_gather.hypothesis(sd, _refuted_item(text=long, signal=long, evidence=[{"text": long, "ref": "", "at": ""}]), "", [("the-goal", "The goal")])
    assert got["party"] == "" and len(got["found"]) <= findings.FOUND_CHARS and "the-goal (The goal)" in got["found"]
    assert findings_gather.hypothesis(sd, {**_refuted_item(id="h5"), "state": "held"}, "product") is None and findings_gather.hypothesis(sd, {"id": "x"}) is None
    assert findings_gather.hypothesis(sd, _refuted_item(id="h6"), "", [], "one in four turned it off")["found"].count("Found: one in four turned it off.") == 1


@pytest.mark.accepts
def test_a_finding_of_the_acceptance_is_a_source_of_its_own_told_at_once_and_a_goals_findings_are_ripe_only_when_its_last_step_is_accepted_spec_152_b3(host, tech):
    state = host.ideas.state_dir
    assert "accept" in findings.SOURCES
    f = findings.add(state, {"source": "accept", "on": "tech: Done when 1", "idea": tech, "party": tech, "found": "Nobody could look at: The screen shows the winner"})
    assert f is not None and f["source"] == "accept" and findings.add(state, {"source": "accept", "on": "tech: Done when 1", "idea": tech, "party": tech, "found": "again"})["id"] == f["id"]
    told = findings.told(state, tech, f["id"], {"what": "Nobody could look at: The screen shows the winner", "shows": "Done when 1", "promised": "The screen shows the winner"})
    assert told["status"] == "told" and findings.pending(state) == [] and findings.waiting(state) == [tech]      # told at once, not sorted yet: the Orkmaster still sorts it
    findings.sorted_(state, tech, f["id"], "work", "fix the screen")
    assert findings.waiting(state) == []
    ideas.save_plan(state, tech, {"idea": tech, "passed_at": "x", "todos": [], "tasks": [{"id": "k1", "state": "merged", "step": 1}]})
    findings.save_record(state, tech, at=dt.datetime.now().isoformat(timespec="seconds"))
    assert idea_route.due(ideas.plan(state, tech)) and findings.ripe(state, tech) is False      # the last step landed, its leader has not accepted it
    findings.save_record(state, tech, at=(dt.datetime.now() - dt.timedelta(hours=findings.QUIET_H + 1)).isoformat(timespec="seconds"))
    assert findings.ripe(state, tech) is False                                                  # not even the quiet day lets it ripen before
    ideas.edit_plan(state, tech, lambda p: p.update(accepts={"1": {"round": 1, "verdict": "gone_on"}}))
    assert findings.ripe(state, tech) is True
