"""A goal's rune (docs/specs/50-parties-and-goals.md §2.3; spec 128 G, decisions §206.10): `pick`, `give` and what stores it (realm/idea_element.py), the
`element` (shape) and `hue` (colour) of `ideas.add`'s answer, and the Map giving one, once, to a goal of before. Spec 111 B (decisions §187.3): the shapes no goal
holds (`free` of `open_elements`, the party nodes' `free_elements`) and the shape the person chose, which `ideas.add` takes and `give` stores. Spec 128 G: a rune is a shape
in a colour, unique across the project (its open goals and its done goals whose result is not yet seen). Code, no model."""
from __future__ import annotations

import json

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import idea_element, ideas

SEEN = "2026-11-02T10:00:00+00:00"


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def party(host, title="First party") -> str:
    return ideas.add_track(host.ideas.root(), title)


def raw(host, party_slug: str, text: str, status: str = "raw") -> str:
    """A goal of before: a page and a state with no element."""
    slug = ideas.add_idea(host.ideas.root(), text, party_slug, host.ideas.state_dir)
    ideas.save_state(host.ideas.state_dir, slug, state=status)
    return slug


def state_text(host, slug: str) -> str:
    return (ideas.state_folder(host.ideas.state_dir, slug) / "state.json").read_text()


# -- pick ---------------------------------------------------------------------------------------------------------


# -- give ---------------------------------------------------------------------------------------------------------

def test_give_stores_the_element_and_the_hue_in_the_goals_state_and_keeps_them(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    a = raw(host, p, "Cache the table")
    assert idea_element.of(state, a) == "" and ideas.state(state, a)["element"] == "" and idea_element.hue_of(state, a) == ""
    assert idea_element.give(root, state, a) == "meadow" == idea_element.of(state, a)
    saved = json.loads(state_text(host, a))
    assert saved["element"] == "meadow" and saved["hue"] == "meadow"
    ideas.save_state(state, a, state="working", error="")                                     # save_state keeps them
    got = ideas.state(state, a)
    assert got["element"] == "meadow" and got["hue"] == "meadow" and got["state"] == "working"
    b = raw(host, p, "Queue the writes")
    assert idea_element.give(root, state, b) == "ice"                                         # the shape used least among the project's goals
    assert idea_element.give(root, state, a) == "meadow"                                      # a given element never changes


def test_the_first_five_goals_differ_by_shape_the_sixth_repeats_a_shape_in_another_hue_and_25_goals_are_25_runes(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host), party(host, "Second party")
    slugs = [raw(host, p if n % 2 else q, f"Goal number {n}", "working") for n in range(25)]      # in two parties: the project counts
    got = []
    for s in slugs:
        idea_element.give(root, state, s)
        got.append((idea_element.of(state, s), idea_element.hue_of(state, s)))
    assert [e for e, _h in got[:5]] == ["meadow", "ice", "dust", "void", "lava"]                  # the first five differ by shape
    assert got[5] == ("meadow", "ice") and got[6] == ("ice", "ice")                            # the sixth repeats a shape, in another hue
    assert len(set(got)) == 25 and {e for e, _h in got} == {h for _e, h in got} == set(idea_element.ELEMENTS)
    assert all(ideas.state(state, s)["hue"] for s in slugs)
    assert idea_element.give(root, state, raw(host, p, "Goal number 26", "working")) == "meadow"      # a 26th starts the cycle again


def test_a_done_goal_whose_result_is_seen_frees_its_rune(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    slugs = [raw(host, p, f"Goal number {n}", "working") for n in range(5)]
    for s in slugs:
        idea_element.give(root, state, s)
    assert idea_element.free(idea_element.open_elements(root, state)) == [] and idea_element.pick_rune(idea_element.open_runes(root, state))[0] == "meadow"
    ideas.save_state(state, slugs[2], state="done")                                           # done, its result not seen: still held
    assert idea_element.free(idea_element.open_elements(root, state)) == [] and idea_element.of(state, slugs[2]) == "dust"
    ideas.save_state(state, slugs[2], seen_at=SEEN)                                           # seen: the rune is free
    assert idea_element.free(idea_element.open_elements(root, state)) == ["dust"] and idea_element.pick_rune(idea_element.open_runes(root, state))[0] == "dust" and idea_element.pick_rune(idea_element.open_runes(root, state))[1] == "meadow"
    assert idea_element.give(root, state, raw(host, p, "A new one", "working")) == "dust"


# -- ideas.add ----------------------------------------------------------------------------------------------------

def test_a_new_goal_is_given_its_rune_at_once_and_its_answer_says_it(host):
    p = party(host)
    got = [host.command("ideas.add", {"text": f"A goal {n}\nwith a body", "track": p, "hold": True}) for n in range(6)]
    assert [g["element"] for g in got] == ["meadow", "ice", "dust", "void", "lava", "meadow"]
    assert [g["hue"] for g in got] == ["meadow", "meadow", "meadow", "meadow", "meadow", "ice"]       # the sixth: a shape repeated, in another hue
    assert all(set(g) == {"slug", "queue", "element", "hue", "type", "joined"} for g in got) and got[0]["queue"] == "hold"      # spec 52: its type, who joined
    state = host.ideas.state_dir
    assert [ideas.state(state, g["slug"])["element"] for g in got] == [g["element"] for g in got]      # in each goal's state, raw as it is
    assert [ideas.state(state, g["slug"])["hue"] for g in got] == [g["hue"] for g in got]
    assert ideas.state(state, got[0]["slug"])["state"] == "raw"
    other = host.command("ideas.add", {"text": "In another party", "track": party(host, "Second party"), "hold": True})
    assert (other["element"], other["hue"]) == ("ice", "ice")                                 # the project counts: meadow twice, the others once; ice, hue meadow is held, ice is not


# -- ideas.map ----------------------------------------------------------------------------------------------------

def test_the_map_gives_one_to_each_goal_of_before_once_and_ideas_rev_does_not_move(host, monkeypatch):
    p = party(host)
    slugs = [raw(host, p, f"Old goal {n}", "done" if n == 5 else "working") for n in range(6)]
    rev = host.snapshot()["ideas_rev"]
    writes = []
    real = ideas.save_state
    monkeypatch.setattr(ideas, "save_state", lambda s, slug, **c: writes.append((slug, sorted(c))) or real(s, slug, **c))
    first = host.command("ideas.map", {})
    nodes = {n["slug"]: n for n in first["nodes"]}
    assert [nodes[s]["element"] for s in slugs[:5]] == ["meadow", "ice", "dust", "void", "lava"]       # the open ones, in the Map's order
    assert nodes[slugs[5]]["element"] == "meadow" and nodes[slugs[5]]["hue"] == "ice"          # the done one (not seen): a shape repeated, in another hue
    assert sorted(writes) == sorted((s, ["element", "hue"]) for s in slugs)                    # one write each
    assert host.snapshot()["ideas_rev"] == rev                                                 # no change for the faces to look at again
    writes.clear()
    second = host.command("ideas.map", {})
    assert writes == [] and [n["element"] for n in second["nodes"]] == [n["element"] for n in first["nodes"]]
    assert [n["hue"] for n in second["nodes"]] == [n["hue"] for n in first["nodes"]]
    assert host.snapshot()["ideas_rev"] == rev
    only = host.command("ideas.map", {"goal": p})                                              # one party's Map says the same
    assert {n["slug"]: (n["element"], n["hue"]) for n in only["nodes"]} == {s: (n["element"], n["hue"]) for s, n in nodes.items()}


# -- the next goal's rune -----------------------------------------------------------------------------------------------------


def test_every_party_of_the_map_carries_the_rune_the_next_goal_would_be_given(host):
    p, q, empty = party(host), party(host, "Second party"), party(host, "Third party")
    for n in range(3):
        raw(host, p, f"Open {n}", "working")
    raw(host, p, "Closed", "done")
    raw(host, q, "Only one", "working")
    root, state = host.ideas.root(), host.ideas.state_dir
    got = host.command("ideas.map", {})
    parties = {g["slug"]: g for g in got["goals"]}
    assert {p, q, empty} <= set(parties)
    for slug, g in parties.items():
        assert g["next_element"] == idea_element.pick_rune(idea_element.open_runes(root, state))[0], slug
        assert g["next_hue"] == idea_element.pick_rune(idea_element.open_runes(root, state))[1], slug
    assert all((g["next_element"], g["next_hue"], g["free_elements"]) == ("meadow", "ice", []) for g in parties.values())     # five goals of the project (the done one not seen) hold the five shapes: meadow again, in the next hue
    one = host.command("ideas.map", {"goal": p})                                              # one party's Map says the same
    assert [(g["next_element"], g["next_hue"]) for g in one["goals"]] == [("meadow", "ice")]


# -- the rune chosen (spec 111 B, decisions §187.3) ----------------------------------------------------------------


def test_give_takes_the_shape_asked_for_picks_its_hue_stores_it_once_and_ignores_what_is_no_element(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    a = raw(host, p, "Chosen")
    assert idea_element.give(root, state, a, want="void") == "void" and idea_element.of(state, a) == "void" and idea_element.hue_of(state, a) == "meadow"
    assert idea_element.give(root, state, a, want="lava") == "void"                        # one write, ever
    b = raw(host, p, "Chosen again")
    assert idea_element.give(root, state, b, want="void") == "void" and idea_element.hue_of(state, b) == "ice"      # the hue used least among the void goals
    c = raw(host, p, "Not an element")
    assert idea_element.give(root, state, c, want="fire") == "meadow"                      # the rule, as before
    d = raw(host, p, "Default")
    assert idea_element.give(root, state, d) == idea_element.pick(["void", "void", "meadow"])


def test_ideas_add_gives_the_goal_the_shape_chosen_and_the_rule_without_one(host):
    p = party(host)
    state = host.ideas.state_dir
    chosen = host.command("ideas.add", {"text": "Chosen", "track": p, "element": "lava", "hold": True})
    assert chosen["element"] == "lava" and chosen["hue"] == "meadow" and idea_element.of(state, chosen["slug"]) == "lava"
    (node,) = [n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == chosen["slug"]]
    assert node["element"] == "lava" and node["hue"] == "meadow"                           # the Map reads it, and gives nothing over it
    ruled = host.command("ideas.add", {"text": "By the rule", "track": p, "hold": True})
    assert ruled["element"] == "meadow"                                                    # the default untouched: the shape used least
    again = host.command("ideas.add", {"text": "The same one again", "track": p, "element": "lava", "hold": True})
    assert again["element"] == "lava" and again["hue"] == "ice"                            # a shape already used is possible: its hue is another
    assert host.command("ideas.add", {"text": "Next by the rule", "track": p, "hold": True})["element"] == "ice"
