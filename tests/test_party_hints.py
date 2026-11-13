"""Spec 43 E (docs/specs/43-party-measured.md §5, Tests → E): `hints` — each of the four, their order, at most two, none for a party that fits —
`Check.fits`, and `ideas.party_price`'s `hints`. Code, no model."""
from __future__ import annotations

import json


from orkboard.realm import party_hints
from tests.test_party_proposals import add, at, check, goal, host  # noqa: F401  (fixtures and helpers)



def quiet(host, goal, n=8, by="reviewer", kind="review", base=0.5):
    """`n` clean checks of the checker, one an idea, the oldest first (a few hours apart)."""
    return [add(host, goal, f"Idea {by} {i}", [check("k1", by, kind, finished=at(base, hours=n - i))]) for i in range(n)]


NO_CODE = "No one in the party writes code: code tasks go to this project's agent for code (the Grunt when none)."
NO_BUILDERS = "No builders: each task goes to this project's agent for its type (the Grunt when none)."


def hints(host, craft, leader, team, every=()):
    party_hints.party_work.forget()                                                                  # a record is kept for 30 s: these tests change the plans
    return party_hints.hints(host.ideas.root(), host.ideas.state_dir, craft, leader, list(team), list(every))


def test_a_check_that_found_nothing_in_its_last_checks_is_said_from_eight_with_none_caught(host, goal):
    quiet(host, goal, 7)
    assert hints(host, "engineering", "architect", ["grunt", "reviewer"]) == []
    add(host, goal, "The eighth", [check("k1", finished=party_hints.party_work.dt.datetime.now().isoformat(timespec="seconds"))])
    assert hints(host, "engineering", "architect", ["grunt", "reviewer"]) == ["Reviewer found nothing in its last 8 checks."]
    quiet(host, goal, 4, by="reviewer")
    assert hints(host, "engineering", "architect", ["grunt", "reviewer"]) == ["Reviewer found nothing in its last 12 checks."]
    add(host, goal, "A catch", [check("k1", findings=[{"where": "x", "what": "y", "fixed": True}])])
    assert hints(host, "engineering", "architect", ["grunt", "reviewer"]) == []                       # it caught one


def test_a_check_that_seldom_applies_to_the_craft_says_when_it_checks(host):
    assert hints(host, "data", "analyst", ["data-engineer", "accessibility-reviewer"]) == [
        "Accessibility reviewer seldom checks a Data party: it checks when the idea changes what people see or use."]
    assert hints(host, "engineering", "architect", ["grunt", "editor"]) == [
        "Editor seldom checks an Engineering party: it checks when the idea adds or changes text people read."]               # an, before a vowel
    assert hints(host, "", "architect", ["grunt", "editor"]) == []                                  # a Mixed goal has no craft to leave out


def test_no_one_who_writes_code_in_an_engineering_or_product_party_and_no_builders_under_a_leader(host):
    assert hints(host, "engineering", "architect", ["tester", "reviewer"]) == [NO_CODE]               # the Tester takes tests, not code
    assert hints(host, "engineering", "architect", ["ui-kit", "reviewer"]) == [NO_CODE]
    assert hints(host, "product", "product-manager", ["copywriter", "reviewer"]) == [NO_CODE]
    assert hints(host, "design", "product-designer", ["ui-kit"]) == []                                 # a design goal needs no code
    assert hints(host, "engineering", "taskmaster", ["ui-kit"]) == [NO_CODE]                          # the Taskmaster alone does not write it
    assert hints(host, "engineering", "taskmaster", []) == [NO_CODE]
    assert hints(host, "design", "product-designer", []) == [NO_BUILDERS]
    assert hints(host, "design", "taskmaster", []) == []                                              # the Taskmaster leads with Grunts by default


def test_ideas_party_price_answers_the_hints_with_the_craft(host):
    got = host.command("ideas.party_price", {"leader": "analyst", "team": ["accessibility-reviewer"], "craft": "data"})
    json.dumps(got)
    assert got["hints"] == ["Accessibility reviewer seldom checks a Data party: it checks when the idea changes what people see or use.", NO_BUILDERS]
    assert host.command("ideas.party_price", {"leader": "analyst", "team": ["accessibility-reviewer"]})["hints"] == [NO_BUILDERS]       # no craft: no craft hint
    assert host.command("ideas.party_price", {"leader": "architect", "team": ["grunt", "tester", "reviewer"], "craft": "engineering"})["hints"] == []
    assert host.command("ideas.party_price", {"craft": "nonsense", "leader": "taskmaster", "team": ["grunt"]})["hints"] == []
