"""A goal's element (docs/specs/50-parties-and-goals.md §2.3): `pick`, `give` and what stores it (realm/idea_element.py), the
`element` of `ideas.add`'s answer, and the Map giving one, once, to a goal of before. Spec 111 B (decisions §187.3): the elements a party has
no open goal of (`free`, `free_for`, the party nodes' `free_elements`) and the element the person chose, which `ideas.add` takes and `give` stores. Code, no model."""
from __future__ import annotations

import json
import os

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import idea_element, ideas


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

def test_the_five_elements_are_orkuis():
    assert idea_element.ELEMENTS == ("meadow", "ice", "dust", "void", "lava")


def test_pick_is_the_element_used_least_and_ties_go_by_the_order():
    pick = idea_element.pick
    assert pick([]) == "meadow"
    assert pick(["meadow"]) == "ice" and pick(["meadow", "ice"]) == "dust"
    assert pick(["meadow", "ice", "dust", "void"]) == "lava"
    assert pick(["meadow", "ice", "dust", "void", "lava"]) == "meadow"                      # a sixth repeats the least used: a tie, by order
    assert pick(["meadow", "meadow", "ice", "dust", "void", "lava"]) == "ice"
    assert pick(["lava", "lava", "void", "meadow", "meadow", "ice", "dust"]) == "ice"       # ice, dust and void tie at 1 …
    assert pick(["lava", "lava", "meadow", "meadow", "ice", "dust"]) == "void"              # … void alone is at 0
    assert pick(["fire", "water", "meadow"]) == "ice"                                       # a word that is no element counts for none
    used = ["dust", "dust", "ice"]
    assert pick(used) == "meadow" and used == ["dust", "dust", "ice"]                       # pure


# -- give ---------------------------------------------------------------------------------------------------------

def test_give_stores_the_element_in_the_goals_state_and_keeps_it(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    a = raw(host, p, "Cache the table")
    assert idea_element.of(state, a) == "" and ideas.state(state, a)["element"] == ""
    assert idea_element.give(root, state, a) == "meadow" == idea_element.of(state, a)
    assert json.loads(state_text(host, a))["element"] == "meadow"
    ideas.save_state(state, a, state="working", error="")                                     # save_state keeps it
    assert ideas.state(state, a)["element"] == "meadow" and ideas.state(state, a)["state"] == "working"
    b = raw(host, p, "Queue the writes")
    assert idea_element.give(root, state, b) == "ice"                                         # the least used among the party's open goals
    assert idea_element.give(root, state, a) == "meadow"                                      # a given element never changes


def test_the_least_used_counts_the_open_goals_of_its_own_party_only(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host, "First party"), party(host, "Second party")
    open_one, done_one = raw(host, p, "Open one", "working"), raw(host, p, "Done one", "done")
    ideas.save_state(state, open_one, element="meadow")
    ideas.save_state(state, done_one, element="ice")                                          # done: it does not count
    elsewhere = raw(host, q, "Elsewhere")
    ideas.save_state(state, elsewhere, element="dust")                                        # another party's: it does not count
    new = raw(host, p, "New one")
    assert idea_element.give(root, state, new) == "ice"                                       # meadow is used once here, ice not (done), dust not (elsewhere)
    assert idea_element.open_elements(root, state, p) == ["meadow", "ice"] and idea_element.open_elements(root, state, p, besides=new) == ["meadow"]
    assert idea_element.give(root, state, done_one) == "ice"                                  # a done goal keeps the one it had


def test_a_goal_moved_to_another_party_keeps_its_own(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host, "First party"), party(host, "Second party")
    a, b = raw(host, p, "Cache the table"), raw(host, q, "Other work")
    assert idea_element.give(root, state, a) == "meadow" and idea_element.give(root, state, b) == "meadow"
    ideas.move(root, a, q)
    assert idea_element.give(root, state, a) == "meadow" == idea_element.of(state, a)         # not picked again against its new party


def test_six_goals_at_work_in_one_party_repeat_the_least_used(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    got = [idea_element.give(root, state, raw(host, p, f"Goal number {n}", "working")) for n in range(7)]
    assert got == ["meadow", "ice", "dust", "void", "lava", "meadow", "ice"]


def test_give_does_not_move_the_goals_modification_time(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    a = raw(host, party(host), "Cache the table")
    path = ideas.state_folder(state, a) / "state.json"
    os.utime(path, (1_700_000_000, 1_700_000_000))
    idea_element.give(root, state, a)
    assert path.stat().st_mtime == 1_700_000_000                                              # an element is no change of the goal


# -- ideas.add ----------------------------------------------------------------------------------------------------

def test_a_new_goal_is_given_its_element_at_once_and_its_answer_says_it(host):
    p = party(host)
    got = [host.command("ideas.add", {"text": f"A goal {n}\nwith a body", "track": p, "hold": True}) for n in range(6)]
    assert [g["element"] for g in got] == ["meadow", "ice", "dust", "void", "lava", "meadow"]
    assert all(set(g) == {"slug", "queue", "element", "type", "joined"} for g in got) and got[0]["queue"] == "hold"      # spec 52: its type, who joined
    state = host.ideas.state_dir
    assert [ideas.state(state, g["slug"])["element"] for g in got] == [g["element"] for g in got]      # in each goal's state, raw as it is
    assert ideas.state(state, got[0]["slug"])["state"] == "raw"
    other = host.command("ideas.add", {"text": "In another party", "track": party(host, "Second party"), "hold": True})
    assert other["element"] == "meadow"                                                       # each party counts its own


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
    assert nodes[slugs[5]]["element"] == "meadow"                                              # the done one: the least used among the open ones
    assert sorted(writes) == sorted((s, ["element"]) for s in slugs)                           # one write each
    assert host.snapshot()["ideas_rev"] == rev                                                 # no change for the faces to look at again
    writes.clear()
    second = host.command("ideas.map", {})
    assert writes == [] and [n["element"] for n in second["nodes"]] == [n["element"] for n in first["nodes"]]
    assert host.snapshot()["ideas_rev"] == rev
    only = host.command("ideas.map", {"goal": p})                                              # one party's Map says the same
    assert {n["slug"]: n["element"] for n in only["nodes"]} == {s: n["element"] for s, n in nodes.items()}


def test_the_map_counts_the_elements_a_party_has_before_it_gives(host):
    p = party(host)
    given, old = raw(host, p, "Given", "working"), raw(host, p, "Of before", "working")
    ideas.save_state(host.ideas.state_dir, given, element="meadow")
    nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
    assert nodes[given]["element"] == "meadow" and nodes[old]["element"] == "ice"


def test_a_goal_not_yet_read_has_one_too(host):
    p = party(host)
    a = host.command("ideas.add", {"text": "Not read yet", "track": p, "hold": True})
    (node,) = host.command("ideas.map", {})["nodes"]
    assert node["state"] == "raw" and node["element"] == a["element"] != ""


# -- next_for -----------------------------------------------------------------------------------------------------

def test_next_for_is_what_give_gives_the_next_goal_of_that_party(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host), party(host, "Second party")
    assert idea_element.next_for(root, state, p) == "meadow"
    for n in range(7):
        want = idea_element.next_for(root, state, p)
        assert idea_element.next_for(root, state, p) == want                                  # it reads and stores nothing
        got = idea_element.give(root, state, raw(host, p, f"Goal number {n}", "working"))
        assert got == want
    done = raw(host, p, "Finished", "done")
    ideas.save_state(state, done, element="lava")
    assert idea_element.next_for(root, state, p) == idea_element.pick(idea_element.open_elements(root, state, p))   # a done goal does not count
    assert idea_element.next_for(root, state, q) == "meadow"                                  # each party counts its own


def test_every_party_of_the_map_carries_the_element_its_next_goal_would_be_given(host):
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
        assert g["next_element"] == idea_element.next_for(root, state, slug), slug
    assert parties[p]["next_element"] == "void" and parties[q]["next_element"] == "ice" and parties[empty]["next_element"] == "meadow"
    one = host.command("ideas.map", {"goal": p})                                              # one party's Map says the same
    assert [g["next_element"] for g in one["goals"]] == ["void"]


# -- the rune chosen (spec 111 B, decisions §187.3) ----------------------------------------------------------------

def test_free_is_what_no_open_goal_has_in_the_order_and_empty_when_none_is_free():
    free = idea_element.free
    assert free([]) == list(idea_element.ELEMENTS)
    assert free(["ice", "void", "ice"]) == ["meadow", "dust", "lava"]
    assert free(["lava", "void", "dust", "ice", "meadow"]) == []                           # none free: the face shows all of them
    assert free(["fire"]) == list(idea_element.ELEMENTS)                                   # a word that is no element holds none
    used = ["ice"]
    assert free(used) == ["meadow", "dust", "void", "lava"] and used == ["ice"]            # pure


def test_free_for_reads_the_partys_open_goals_only(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host), party(host, "Second party")
    assert idea_element.free_for(root, state, p) == list(idea_element.ELEMENTS)
    a, b = raw(host, p, "Open one", "working"), raw(host, p, "Open two", "working")
    ideas.save_state(state, a, element="meadow")
    ideas.save_state(state, b, element="dust")
    done = raw(host, p, "Finished", "done")
    ideas.save_state(state, done, element="lava")
    other = raw(host, q, "Another party's", "working")
    ideas.save_state(state, other, element="ice")
    assert idea_element.free_for(root, state, p) == ["ice", "void", "lava"]                # a done goal and another party's do not count
    assert idea_element.free_for(root, state, q) == ["meadow", "dust", "void", "lava"]
    for e, slug in zip(("ice", "void", "lava"), (raw(host, p, "Three", "working"), raw(host, p, "Four", "working"), raw(host, p, "Five", "working"))):
        ideas.save_state(state, slug, element=e)
    assert idea_element.free_for(root, state, p) == []                                     # all five are used: empty, never "all"


def test_give_takes_the_element_asked_for_stores_it_once_and_ignores_what_is_no_element(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    a = raw(host, p, "Chosen")
    assert idea_element.give(root, state, a, want="void") == "void" and idea_element.of(state, a) == "void"
    assert idea_element.give(root, state, a, want="lava") == "void"                        # one write, ever
    b = raw(host, p, "Not an element")
    assert idea_element.give(root, state, b, want="fire") == "meadow"                      # the rule, as before
    c = raw(host, p, "Default")
    assert idea_element.give(root, state, c) == idea_element.pick(["void", "meadow"])


def test_every_party_of_the_map_carries_its_free_elements(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q, empty = party(host), party(host, "Second party"), party(host, "Third party")
    for n in range(2):
        raw(host, p, f"Open {n}", "working")
    raw(host, p, "Closed", "done")
    raw(host, q, "Only one", "working")
    parties = {g["slug"]: g for g in host.command("ideas.map", {})["goals"]}
    for slug, g in parties.items():
        assert g["free_elements"] == idea_element.free_for(root, state, slug), slug
    assert parties[p]["free_elements"] == ["dust", "void", "lava"] and parties[q]["free_elements"] == ["ice", "dust", "void", "lava"] and parties[empty]["free_elements"] == list(idea_element.ELEMENTS)
    assert parties[p]["next_element"] == parties[p]["free_elements"][0]                    # the default is a free one while one is free
    for n in range(3):
        raw(host, p, f"More {n}", "working")
    assert {g["slug"]: g for g in host.command("ideas.map", {})["goals"]}[p]["free_elements"] == []     # none free: empty


def test_ideas_add_gives_the_goal_the_element_chosen_and_the_rule_without_one(host):
    p = party(host)
    state = host.ideas.state_dir
    chosen = host.command("ideas.add", {"text": "Chosen", "track": p, "element": "lava", "hold": True})
    assert chosen["element"] == "lava" and idea_element.of(state, chosen["slug"]) == "lava"
    (node,) = [n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == chosen["slug"]]
    assert node["element"] == "lava"                                                       # the Map reads it, and gives nothing over it
    ruled = host.command("ideas.add", {"text": "By the rule", "track": p, "hold": True})
    assert ruled["element"] == "meadow"                                                    # the default untouched: the one used least
    again = host.command("ideas.add", {"text": "The same one again", "track": p, "element": "lava", "hold": True})
    assert again["element"] == "lava"                                                      # a rune already used is possible, faint in the field only
    assert host.command("ideas.add", {"text": "Next by the rule", "track": p, "hold": True})["element"] == "ice"


def test_ideas_add_refuses_an_element_that_is_none_of_the_five_and_adds_nothing(host):
    p = party(host)
    before = host.command("ideas.board", {})["ideas"]
    with pytest.raises(Exception, match="five runes"):
        host.command("ideas.add", {"text": "Fire", "track": p, "element": "fire"})
    assert host.command("ideas.board", {})["ideas"] == before
