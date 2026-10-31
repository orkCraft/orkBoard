"""Spec 109 A (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §2.1–§2.2; decisions §184): the rubrics (`realm/lens_rubrics.py`): each craft's framework as a few aspects, each with the question it
asks and the kinds of hints of code that ground it; the prompt's lines; the scorecard's five states. Pure code, no model."""
from __future__ import annotations

import re

from orkboard.realm import idea_objections, lens_rubrics as rubrics, lexicon, map_parts, play_signals

CRAFTS = ("tech", "design", "product", "game-design", "art", "release", "marketing", "run", "liveops")
KINDS = {                        # the hints of code each craft has (spec 109 §3), every one in exactly one aspect of its craft
    "tech": ("cycle", "fan_in", "fan_out", "big", "shared_churn", "untested_churn", "hotspot", "unstable", "error", "failed", "slow"),
    "design": ("loose", "dead_end", "no_picture", "no_states", "a11y", "dead_press", "again"),
    "product": ("unserved", "pains", "pain_loose", "vague_outcome", "no_evidence", "off_tree"),
    "game-design": ("no_source", "pile_up", "no_reward", "unfed", "flat", "spike", "no_hook", "unground"),
    "art": ("mixed_sizes", "naming", "heavy", "unused"),
    "release": ("big_batch", "stale", "no_changelog", "reverts"),
    "marketing": ("no_channel", "aso_title", "aso_short", "no_shots", "no_onboarding", "no_return", "no_share", "no_revenue"),
    "run": (), "liveops": (),
}


def test_every_crafts_rubric_is_well_formed():
    assert set(rubrics.RUBRICS) == set(CRAFTS) and set(map_parts.MAPS) <= set(rubrics.RUBRICS)
    for craft, r in rubrics.RUBRICS.items():
        ids = [a["id"] for a in r["aspects"]]
        assert r["framework"] and r["short"] and 3 <= len(ids) <= 6 and len(set(ids)) == len(ids), craft
        for a in r["aspects"]:
            assert re.fullmatch(r"[a-z][a-z_]*", a["id"]) and a["name"] and a["ask"].endswith("?") and isinstance(a["signals"], tuple), (craft, a["id"])
        kinds = [k for a in r["aspects"] for k in a["signals"]]
        assert len(set(kinds)) == len(kinds), f"{craft}: a kind is in two aspects"
        assert set(kinds) == set(KINDS[craft]), f"{craft}: the kinds the spec names"
    assert rubrics.rubric("tech") is rubrics.RUBRICS["tech"] and rubrics.rubric("") is None and rubrics.rubric("nowhere") is None


def test_the_aspects_are_the_specs_in_its_order():
    ids = {c: [a["id"] for a in rubrics.RUBRICS[c]["aspects"]] for c in CRAFTS}
    assert ids["tech"] == ["modularity", "coupling", "hotspots", "testability", "safety"]
    assert ids["design"] == ["flow", "status", "access", "consistency", "seen"]
    assert ids["product"] == ["outcome", "opportunities", "evidence", "focus"]
    assert ids["game-design"] == ["loop", "economy", "pacing", "retention", "grounded"]
    assert ids["art"] == ["style", "pipeline", "budget", "sound"]
    assert ids["release"] == ["batch", "lead_time", "readiness", "failure"]
    assert ids["marketing"] == ["acquisition", "store", "activation", "retention", "referral", "revenue"]
    assert ids["run"] == ["slo", "signals", "runbooks"] and ids["liveops"] == ["calendar", "kpis", "config"]
    assert [a["name"] for a in rubrics.RUBRICS["tech"]["aspects"]][-1] == "Security and reliability"


def test_a_kind_belongs_to_the_aspect_that_names_it_and_an_unknown_one_to_none():
    assert rubrics.aspect_of("tech", "hotspot") == "hotspots" and rubrics.aspect_of("tech", "unstable") == "modularity" and rubrics.aspect_of("tech", "shared_churn") == "coupling"
    assert rubrics.aspect_of("design", "a11y") == "access" and rubrics.aspect_of("marketing", "no_return") == "retention" and rubrics.aspect_of("game-design", "no_hook") == "retention"
    assert rubrics.aspect_of("tech", "a11y") == "" and rubrics.aspect_of("tech", "") == "" and rubrics.aspect_of("nowhere", "cycle") == "" and rubrics.aspect_of("run", "cycle") == ""
    for craft, kinds in KINDS.items():
        assert all(rubrics.aspect_of(craft, k) for k in kinds), craft


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


def test_a_hint_with_no_aspect_of_its_own_is_placed_by_its_kind_and_the_words_are_three_at_most():
    hints = [{"on": f"p{n}", "kind": "big", "words": f"part {n} is big"} for n in range(5)] + [{"on": "", "kind": "nothing_known", "words": "stray"}]
    card = {a["id"]: a for a in rubrics.scorecard("tech", _rec(hints=hints))}
    assert card["hotspots"]["state"] == "hint" and card["hotspots"]["hints"] == ["part 0 is big", "part 1 is big", "part 2 is big"]
    assert all(a["state"] == "clear" for i, a in card.items() if i != "hotspots"), "a hint of a kind no aspect has belongs to none"


def test_a_concern_made_into_a_goal_is_not_open():
    concerns = [{"id": "c-1", "aspect": "access", "level": "alert", "idea": "fix-alt"}, {"id": "c-2", "aspect": "flow", "level": "note"}]
    got = {a["id"]: a for a in rubrics.scorecard("design", _rec(concerns=concerns))}
    assert (got["access"]["state"], got["access"]["n"]) == ("clear", 0) and (got["flow"]["state"], got["flow"]["n"]) == ("note", 1)
    hinted = {a["id"]: a["state"] for a in rubrics.scorecard("design", _rec(concerns=concerns, hints=[{"on": "x", "kind": "a11y", "aspect": "access", "words": "an image with no alt"}]))}
    assert hinted["access"] == "hint", "code noticed it, the goal was made: the hint stays until the next look"
    assert {a["id"]: a["state"] for a in rubrics.scorecard("design", _rec(concerns=[{"id": "c", "aspect": "", "level": "alert"}]))}["flow"] == "clear", "a concern of no aspect marks none"


def test_the_word_is_in_the_glossary():
    assert lexicon.term("aspect") == "aspect" and lexicon.term("aspect", many=True) == "aspects"


def test_the_lens_in_talk_ends_with_the_framework_of_a_craft_that_has_a_rubric():
    for craft in CRAFTS:
        assert idea_objections.lens(craft).endswith(f", as a senior of it would: by {rubrics.RUBRICS[craft]['framework']}"), craft
    assert idea_objections.lens("tech").startswith("the architecture on your map: ") and "C4's containers and parts" in idea_objections.lens("tech") and "hotspots" in idea_objections.lens("tech")
    assert idea_objections.lens("run").startswith("what is live:") and "SLOs and error budgets" in idea_objections.lens("run")
    assert idea_objections.lens("nowhere") == "what your party keeps" and idea_objections.lens("") == "what your party keeps", "a craft with no rubric is as it was"


LOOP_KINDS = {"no_source", "pile_up", "no_reward", "unfed", "flat"}          # loop.findings_kinds'
MARKETING_KINDS = {"no_channel", "aso_title", "aso_short", "no_shots", "no_onboarding", "no_return", "no_share", "no_revenue"}   # map_signals_crafts.marketing's, built from a table


def test_every_kind_the_signals_emit_is_in_one_aspect_and_every_aspects_kind_is_emitted():
    """The hints of code (`realm/map_signals.py`, `realm/map_signals_crafts.py`, the loop's findings) and the rubrics name the same kinds (spec 109 §2.1)."""
    import re
    from pathlib import Path
    root = Path(rubrics.__file__).parent
    text = "".join((root / n).read_text(encoding="utf-8") for n in ("map_signals.py", "map_signals_crafts.py"))
    assert all(f'"{k}"' in text for k in MARKETING_KINDS) and all(f'"{k}"' in (root / "loop.py").read_text(encoding="utf-8") for k in LOOP_KINDS)
    emitted = set(re.findall(r'"kind": "([a-z_0-9]+)"', text)) | MARKETING_KINDS | LOOP_KINDS | set(play_signals.CRAFT)
    named = {k for craft in rubrics.RUBRICS for a in rubrics.RUBRICS[craft]["aspects"] for k in a["signals"]}
    assert emitted == named, (sorted(emitted - named), sorted(named - emitted))


def test_the_live_products_kinds_are_in_the_aspects_the_spec_names():
    """Spec 115 §4: the probe's hints (`realm/play_signals.py`) ground a tech and a design aspect each."""
    assert play_signals.CRAFT == {"error": "tech", "failed": "tech", "slow": "tech", "dead_press": "design", "again": "design"}
    got = {k: (c, rubrics.aspect_of(c, k)) for k, c in play_signals.CRAFT.items()}
    assert got == {"error": ("tech", "safety"), "failed": ("tech", "safety"), "slow": ("tech", "hotspots"), "dead_press": ("design", "flow"), "again": ("design", "status")}
    names = {a["id"]: a["name"] for c in ("tech", "design") for a in rubrics.RUBRICS[c]["aspects"]}
    assert names["safety"] == "Security and reliability" and names["hotspots"] == "Hotspots" and names["flow"] == "The way through" and names["status"] == "State and errors"
    assert rubrics.aspect_of("design", "error") == "" and rubrics.aspect_of("tech", "dead_press") == "", "a kind is of one craft"


def test_a_hint_of_the_live_product_lights_its_aspect_in_the_scorecard():
    failed = {"on": "", "kind": "failed", "words": "A request failed: POST /api/water 500"}
    again = {"on": "", "kind": "again", "words": "Pressed again and again"}
    tech = {a["id"]: a for a in rubrics.scorecard("tech", _rec(hints=[failed]))}
    design = {a["id"]: a for a in rubrics.scorecard("design", _rec(hints=[again]))}
    assert tech["safety"]["state"] == "hint" and tech["safety"]["hints"] == [failed["words"]] and design["status"]["state"] == "hint"
