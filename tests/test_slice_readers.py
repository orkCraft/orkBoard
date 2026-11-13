"""Spec 131 A.4 (docs/specs/131-a-leaders-slices-and-the-cascade.md; decisions §233.3): the leaders' slices in every leader's call. Each site of the table has the part right after the project's facts and
before the journals and the map (the bubble's and the passed question's prompts put the map first, so the part is before their journals); a member's call has none; the Orkmaster's tab has none; the
context of each step grew by 1,200. The decision's call is `tests/test_idea_slices.py`'s. As `tests/test_journal_readers.py` is written; no model is called.
"""
from __future__ import annotations

import pytest

from orkboard.core import idea_slices
from orkboard.realm import idea_target, slices
from tests.test_idea_slices import HEAD, MAP, _hold, _route, design, goal, host, release, tech  # noqa: F401  (the fixtures)


def _part(prompt, facts=True, map_after=True):
    """The part is in the prompt after the facts and before the journals and the map (`map_after`: False where the prompt puts the map first, as the bubble's and the passed question's)."""
    assert HEAD in prompt and "- Your builds are quick. (§6.2)" in prompt, prompt[:300]
    at = prompt.index(HEAD)
    if facts:
        assert prompt.index("What is known of the project") < at
    for later in ("What you said before and what came of it", "What the project decided and what came of it", *(("Your party's map:",) if map_after else ())):
        if later in prompt:
            assert at < prompt.index(later), later




def test_a_store_that_cannot_be_read_adds_no_part_and_never_stops_a_call(host, tech, goal, monkeypatch):
    _hold(host, tech)
    monkeypatch.setattr(slices, "text", lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    assert idea_slices.parts(host.ideas.state_dir, tech) == []
    assert "Your party's map" in host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), 1, "", False, set())


@pytest.mark.parametrize("rnd", [1, 2])
def test_talks_round_has_the_part_after_the_facts_and_before_the_journals_and_the_map(host, tech, goal, rnd):
    _hold(host, tech)
    _part(host.ideas.keeper.round_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), rnd, "Q? A.", False, set()))






@pytest.mark.parametrize("first", [True, False])
def test_the_sections_have_the_part(host, tech, goal, first):
    _hold(host, tech)
    _part(host.ideas.keeper.section_prompt(goal, {"party": tech, "leader": "architect"}, _route(tech), first))


def test_a_plan_and_a_change_asked_of_a_leader_have_the_part_before_the_map(host, tech, goal):
    _hold(host, tech)
    root = host.ideas.root()
    plan = host.ideas.keeper.plan_prompt(root, goal)
    assert HEAD in plan and "- Your builds are quick. (§6.2)" in plan
    change = host.ideas.keeper.change_prompt(root, goal, tech, "", "make it quicker")
    assert HEAD in change and change.index(HEAD) < change.index("Your map:")












def test_every_prompt_has_the_part_once_and_a_party_with_none_has_prompts_as_before(host, tech, design, goal):
    _hold(host, tech)
    keeper = host.ideas.keeper
    assert keeper.ask_prompt(tech, "q?").count(HEAD) == 1
    other = {"party": design, "leader": "product-designer"}
    for prompt in (keeper.ask_prompt(design, "q?"), keeper.round_prompt(goal, other, _route(design), 1, "", False, set()), keeper.section_prompt(goal, other, [other], True)):
        assert "What you hold of the project's decisions" not in prompt


def test_a_members_call_is_given_none(host, tech, goal):
    """Only the leaders' prompts ask for the slices: no module of a member's call (a task's prompt, the Taskmaster's runner) reads `idea_slices`."""
    from pathlib import Path
    users = sorted(p.name for p in Path(idea_slices.__file__).parent.glob("*.py") if p.name != "idea_slices.py" and "idea_slices" in p.read_text(encoding="utf-8"))
    assert users == ["idea_accept.py", "idea_ask.py", "idea_concerns.py", "idea_decide.py", "idea_diagnose.py", "idea_findings.py", "idea_hypotheses.py", "idea_keeper.py", "idea_lead.py", "idea_leader_change.py", "idea_loop.py", "idea_pass.py",
                     "idea_plan.py", "idea_project_q.py", "idea_sections.py", "idea_talk.py", "idea_tree.py", "idea_verdict.py"]


def test_the_context_of_each_step_that_reads_the_slices_grew_by_twelve_hundred():
    before = {"plan": 10_000, "accept": 10_000, "talk_round": 13_500, "talk_verdict": 9_000, "diagnose": 10_000, "section_first": 17_500, "section": 17_500, "project_q": 12_000, "loop": 12_000,
              "tree": 12_000, "hypotheses": 12_000, "ask": 11_000, "concerns": 15_000}
    for step, was in before.items():
        assert idea_target.CONTEXT[step] == was + 1_200, step
    assert idea_target.CONTEXT["join"] == 8_000 and idea_target.CONTEXT["decide"] == 11_000 + 2_500                       # the rest stay; the decision's call grew by its own part's bound


