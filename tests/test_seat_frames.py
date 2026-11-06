"""Spec 154 A.3: each seat's agent frame holds its rules' text exactly (the function its call is built from), names the paths of A.2 and holds none of a call's frame."""
from __future__ import annotations

import pytest

from orkboard.core import idea_accept, idea_sections, idea_talk
from orkboard.realm import goal_route, roles, seat_frames

WIKI, DECISIONS = "llm-wiki/general", "docs/decisions.md"
NEVER = ("Read no file", "read no file", "JSON", "json", "(The context follows")
CASES = [("orkmaster", "route", "", lambda: goal_route.rules()),
         ("tech-leader", "talk", "engineering", lambda: idea_talk.rules("engineering")),
         ("design-leader", "talk", "design", lambda: idea_talk.rules("design")),
         ("tech-leader", "section", "engineering", lambda: idea_sections.rules()),
         ("tech-leader", "accept", "engineering", lambda: idea_accept.rules()),
         ("taskmaster", "plan", "", lambda: roles.rules("taskmaster")),
         ("grunt", "task", "", lambda: roles.rules("grunt"))]


@pytest.mark.parametrize("seat,step,craft,rules", CASES)
def test_an_agent_frame_holds_its_seats_rules_exactly_and_none_of_a_calls_frame(seat, step, craft, rules):
    frame = seat_frames.agent(seat, step, craft)
    assert rules().strip() and rules() in frame
    for never in NEVER:
        assert never not in frame, never
    assert f"{WIKI}/pages/ideas/<slug>.md" in frame


def test_the_rules_are_the_text_the_calls_prompt_is_built_from():
    assert goal_route.rules() in goal_route.instruction()
    assert idea_talk.rules("engineering") in idea_talk.instruction("engineering")
    assert idea_talk.rules("engineering", second=True) in idea_talk.instruction("engineering", second=True)
    assert idea_sections.rules() in idea_sections.instruction()
    assert idea_sections.join_rules() in idea_sections.join_instruction()
    assert idea_accept.rules() in idea_accept.instruction()
    assert roles.instruction("grunt") == roles.rules("grunt") and roles.instruction("nobody") == ""


def test_a_frame_names_what_to_read_what_to_write_and_what_to_give_back():
    talk = seat_frames.agent("tech-leader", "talk", "engineering")
    for path in (f"{WIKI}/project.md", f"{WIKI}/journals/<party>.md", f"{WIKI}/pages/tracks/<party>.md", DECISIONS):
        assert path in talk
    assert "## Tech" in talk and "### Talk" in talk and "## Give back" in talk and "asks: person" in talk
    accept = seat_frames.agent("tech-leader", "accept", "engineering")
    assert "### Accepted" in accept and "met:" in accept and "not met:" in accept and "cannot see:" in accept and "the files the step changed" in accept and "you run no command" in accept and "git diff" not in accept and "gate" in accept
    assert "`route`" in seat_frames.agent("orkmaster", "route") and f"{WIKI}/pages/tracks/*.md" in seat_frames.agent("orkmaster", "route")
    assert "Stages" in seat_frames.agent("taskmaster", "plan")
    grunt = seat_frames.agent("grunt", "task")
    assert "your leader" in grunt and "do not ask the person" in grunt


def test_the_paths_follow_the_wiki_and_the_decisions_given():
    frame = seat_frames.agent("tech-leader", "section", "engineering", wiki="wiki/x", decisions="notes/decisions.md")
    assert "wiki/x/pages/ideas/<slug>.md" in frame and "notes/decisions.md" in frame and WIKI not in frame


def test_steps_of_each_seat():
    assert seat_frames.steps("orkmaster") == ("route",)
    assert seat_frames.steps("tech-leader") == seat_frames.steps("design-leader") == ("talk", "section", "accept")
    assert seat_frames.steps("taskmaster") == ("plan",) and seat_frames.steps("grunt") == ("task",)
    assert seat_frames.steps("nobody") == () and seat_frames.steps("-leader") == ()


def test_a_step_a_seat_does_not_have_is_refused():
    with pytest.raises(ValueError):
        seat_frames.agent("grunt", "talk")
    with pytest.raises(ValueError):
        seat_frames.agent("tech-leader", "plan")
    with pytest.raises(ValueError):
        seat_frames.agent("nobody", "route")
