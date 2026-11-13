"""Spec 109 A (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §2.1–§2.2; decisions §184): the rubrics (`realm/lens_rubrics.py`): each craft's framework as a few aspects, each with the question it
asks and the kinds of hints of code that ground it; the prompt's lines; the scorecard's five states. Pure code, no model."""
from __future__ import annotations


from orkboard.realm import idea_objections, lens_rubrics as rubrics

CRAFTS = ("tech", "design", "product", "game-design", "art", "release", "marketing", "run", "liveops")
KINDS = {                        # the hints of code each craft has (spec 109 §3), every one in exactly one aspect of its craft
    "tech": ("cycle", "fan_in", "fan_out", "big", "shared_churn", "untested_churn", "hotspot", "unstable", "error", "failed", "slow"),
    "design": ("loose", "dead_end", "no_picture", "no_states", "a11y", "dead_press", "again"),
    "product": ("unserved", "pains", "pain_loose", "vague_outcome", "no_evidence", "off_tree", "untested"),
    "game-design": ("no_source", "pile_up", "no_reward", "unfed", "flat", "spike", "no_hook", "unground"),
    "art": ("mixed_sizes", "naming", "heavy", "unused"),
    "release": ("big_batch", "stale", "no_changelog", "reverts"),
    "marketing": ("no_channel", "aso_title", "aso_short", "no_shots", "no_onboarding", "no_return", "no_share", "no_revenue"),
    "run": (), "liveops": (),
}


def test_the_prompt_lines_say_how_a_senior_reviews_and_one_line_an_aspect():
    lines = rubrics.prompt_lines("design").splitlines()
    assert lines[0] == "How a senior of design reviews this map: Nielsen's ten usability heuristics, WCAG 2.2 AA, and the person's way through the screens."
    assert lines[1] == "- flow: The way through. Can a person reach every screen and finish what they came for?" and len(lines) == 1 + 5 and all(ln.startswith("- ") for ln in lines[1:])
    assert rubrics.prompt_lines("") == "" and rubrics.prompt_lines("nowhere") == ""
    for craft in CRAFTS:
        assert rubrics.prompt_lines(craft).count("\n") == len(rubrics.RUBRICS[craft]["aspects"])


def _rec(at="2026-10-29T10:00:00", concerns=(), hints=()):
    return {"at": at, "concerns": list(concerns), "hints": list(hints)}


def _states(craft, rec):
    return {a["id"]: a["state"] for a in rubrics.scorecard(craft, rec)}


def test_the_scorecard_has_each_aspect_in_the_rubrics_order_in_one_of_five_states():
    card = rubrics.scorecard("tech", _rec(at=""))
    assert [a["id"] for a in card] == [a["id"] for a in rubrics.RUBRICS["tech"]["aspects"]]
    assert set(card[0]) == {"id", "name", "ask", "state", "n", "hints"} and card[0]["name"] == "Modularity" and card[0]["ask"].startswith("Are the parts' edges clean")
    assert {a["state"] for a in card} == {"unlooked"} and {a["n"] for a in card} == {0} and {tuple(a["hints"]) for a in card} == {()}
    assert {a["state"] for a in rubrics.scorecard("tech", _rec())} == {"clear"}
    assert rubrics.scorecard("nowhere", _rec()) == [] and rubrics.scorecard("", {}) == []


def test_alert_beats_note_beats_hint_beats_clear_beats_unlooked():
    concerns = [{"id": "c-1", "aspect": "hotspots", "level": "note"}, {"id": "c-2", "aspect": "hotspots", "level": "alert"}, {"id": "c-3", "aspect": "coupling", "level": "note"}]
    hints = [{"on": "a", "kind": "hotspot", "aspect": "hotspots", "words": "a changed often"}, {"on": "b", "kind": "untested_churn", "aspect": "testability", "words": "b changed with no test"}]
    got = _states("tech", _rec(concerns=concerns, hints=hints))
    assert got == {"modularity": "clear", "coupling": "note", "hotspots": "alert", "testability": "hint", "safety": "clear"}
    assert _states("tech", _rec(at="", concerns=concerns, hints=hints))["modularity"] == "unlooked", "no look yet: nothing to be clear of"
    card = {a["id"]: a for a in rubrics.scorecard("tech", _rec(concerns=concerns, hints=hints))}
    assert card["hotspots"]["n"] == 2 and card["coupling"]["n"] == 1 and card["testability"]["n"] == 0 and card["hotspots"]["hints"] == ["a changed often"]


def test_a_concern_made_into_a_goal_is_not_open():
    concerns = [{"id": "c-1", "aspect": "access", "level": "alert", "idea": "fix-alt"}, {"id": "c-2", "aspect": "flow", "level": "note"}]
    got = {a["id"]: a for a in rubrics.scorecard("design", _rec(concerns=concerns))}
    assert (got["access"]["state"], got["access"]["n"]) == ("clear", 0) and (got["flow"]["state"], got["flow"]["n"]) == ("note", 1)
    hinted = {a["id"]: a["state"] for a in rubrics.scorecard("design", _rec(concerns=concerns, hints=[{"on": "x", "kind": "a11y", "aspect": "access", "words": "an image with no alt"}]))}
    assert hinted["access"] == "hint", "code noticed it, the goal was made: the hint stays until the next look"
    assert {a["id"]: a["state"] for a in rubrics.scorecard("design", _rec(concerns=[{"id": "c", "aspect": "", "level": "alert"}]))}["flow"] == "clear", "a concern of no aspect marks none"


def test_the_lens_in_talk_ends_with_the_framework_of_a_craft_that_has_a_rubric():
    for craft in CRAFTS:
        assert idea_objections.lens(craft).endswith(f", as a senior of it would: by {rubrics.RUBRICS[craft]['framework']}"), craft
    assert idea_objections.lens("tech").startswith("the architecture on your map: ") and "C4's containers and parts" in idea_objections.lens("tech") and "hotspots" in idea_objections.lens("tech")
    assert idea_objections.lens("run").startswith("what is live:") and "Observability first" in idea_objections.lens("run")
    assert idea_objections.lens("product").startswith("the goals in line and the product's aim: is this worth doing before them, now, and the open hypotheses: is this goal built on one no one has tested?")
    assert rubrics.aspect_of("product", "untested") == "evidence" and rubrics.aspect_of("product", "no_evidence") == "evidence", "Evidence holds both"
    assert idea_objections.lens("nowhere") == "what your party keeps" and idea_objections.lens("") == "what your party keeps", "a craft with no rubric is as it was"


LOOP_KINDS = {"no_source", "pile_up", "no_reward", "unfed", "flat"}          # loop.findings_kinds'
MARKETING_KINDS = {"no_channel", "aso_title", "aso_short", "no_shots", "no_onboarding", "no_return", "no_share", "no_revenue"}   # map_signals_crafts.marketing's, built from a table


def test_a_hint_of_the_live_product_lights_its_aspect_in_the_scorecard():
    failed = {"on": "", "kind": "failed", "words": "A request failed: POST /api/water 500"}
    again = {"on": "", "kind": "again", "words": "Pressed again and again"}
    tech = {a["id"]: a for a in rubrics.scorecard("tech", _rec(hints=[failed]))}
    design = {a["id"]: a for a in rubrics.scorecard("design", _rec(hints=[again]))}
    assert tech["safety"]["state"] == "hint" and tech["safety"]["hints"] == [failed["words"]] and design["status"]["state"] == "hint"
