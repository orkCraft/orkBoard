"""A goal's rune (docs/specs/50-parties-and-goals.md §2.3; spec 128 G, decisions §206.10): `pick`, `give` and what stores it (realm/idea_element.py), the
`element` (shape) and `hue` (colour) of `ideas.add`'s answer, and the Map giving one, once, to a goal of before. Spec 111 B (decisions §187.3): the shapes no goal
holds (`free`, `free_for`, the party nodes' `free_elements`) and the shape the person chose, which `ideas.add` takes and `give` stores. Spec 128 G: a rune is a shape
in a colour, unique across the project (its open goals and its done goals whose result is not yet seen). Code, no model."""
from __future__ import annotations

import json
import os

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

def test_the_five_elements_are_orkuis():
    assert idea_element.ELEMENTS == ("meadow", "ice", "dust", "void", "lava")


def test_pick_is_the_shape_used_least_and_ties_go_by_the_order():
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


def test_pick_hue_and_pick_rune_take_the_shape_used_least_then_the_hue_used_least_among_that_shape():
    runes = [("meadow", "meadow"), ("meadow", "ice"), ("ice", "ice")]
    assert idea_element.pick_rune([]) == ("meadow", "meadow")
    assert idea_element.pick_rune(runes) == ("dust", "meadow")                              # dust, void and lava are at 0: the first; no goal of that shape: the first hue
    assert idea_element.pick_hue(runes, "meadow") == "dust"                                 # meadow and ice are used once among the meadow goals: dust is at 0
    assert idea_element.pick_hue(runes, "ice") == "meadow"                                  # one goal of that shape, in the ice hue
    assert idea_element.pick_rune(runes, want="ice") == ("ice", "meadow")                   # a chosen shape: its hue is picked
    assert idea_element.pick_rune(runes, want="fire") == ("dust", "meadow")                 # a word that is no element is not a choice
    assert runes == [("meadow", "meadow"), ("meadow", "ice"), ("ice", "ice")]                # pure


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


def test_the_least_used_counts_the_projects_goals_open_ones_and_done_ones_not_yet_seen(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host, "First party"), party(host, "Second party")
    open_one, done_one, seen_one = raw(host, p, "Open one", "working"), raw(host, p, "Done one", "done"), raw(host, p, "Seen one", "done")
    ideas.save_state(state, open_one, element="meadow")
    ideas.save_state(state, done_one, element="ice")                                          # done, its result not seen: it counts
    ideas.save_state(state, seen_one, element="dust", seen_at=SEEN)                            # done and seen: it frees its rune
    elsewhere = raw(host, q, "Elsewhere")
    ideas.save_state(state, elsewhere, element="void")                                        # another party's: it counts (a rune is unique across the project)
    new = raw(host, p, "New one")
    assert sorted(idea_element.open_elements(root, state)) == ["ice", "meadow", "void"]
    assert idea_element.give(root, state, new) == "dust"                                      # meadow, ice and void are held; dust (seen) and lava are not: the first
    assert sorted(idea_element.open_elements(root, state, besides=new)) == ["ice", "meadow", "void"]
    assert idea_element.give(root, state, seen_one) == "dust"                                 # a done goal keeps the one it had


def test_a_goal_moved_to_another_party_keeps_its_own(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host, "First party"), party(host, "Second party")
    a, b = raw(host, p, "Cache the table"), raw(host, q, "Other work")
    assert idea_element.give(root, state, a) == "meadow" and idea_element.give(root, state, b) == "ice"
    ideas.move(root, a, q)
    assert idea_element.give(root, state, a) == "meadow" == idea_element.of(state, a)         # not picked again against its new party


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


def test_a_goal_with_an_element_and_no_hue_reads_its_element_as_its_hue(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    old = raw(host, party(host), "A goal of before", "working")
    ideas.save_state(state, old, element="void")                                              # no hue: the state of a goal kept from before
    assert ideas.state(state, old)["hue"] == "" and idea_element.hue_of(state, old) == "void"
    assert idea_element.hue_in({"element": "lava", "hue": ""}) == "lava" and idea_element.hue_in({"element": "lava", "hue": "ice"}) == "ice"
    assert idea_element.hue_in({"element": "", "hue": ""}) == "" and idea_element.hue_in({"element": "fire", "hue": "fire"}) == ""
    assert idea_element.open_runes(root, state) == [("void", "void")]
    node = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}[old]
    assert node["element"] == "void" and node["hue"] == "void"                                # the snapshot says it beside the element
    assert idea_element.give(root, state, old) == "void" and ideas.state(state, old)["hue"] == ""      # nothing is written over a goal that has its element


def test_a_done_goal_whose_result_is_seen_frees_its_rune(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p = party(host)
    slugs = [raw(host, p, f"Goal number {n}", "working") for n in range(5)]
    for s in slugs:
        idea_element.give(root, state, s)
    assert idea_element.free_for(root, state) == [] and idea_element.next_for(root, state) == "meadow"
    ideas.save_state(state, slugs[2], state="done")                                           # done, its result not seen: still held
    assert idea_element.free_for(root, state) == [] and idea_element.of(state, slugs[2]) == "dust"
    ideas.save_state(state, slugs[2], seen_at=SEEN)                                           # seen: the rune is free
    assert idea_element.free_for(root, state) == ["dust"] and idea_element.next_for(root, state) == "dust" and idea_element.next_hue_for(root, state) == "meadow"
    assert idea_element.give(root, state, raw(host, p, "A new one", "working")) == "dust"


def test_give_does_not_move_the_goals_modification_time(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    a = raw(host, party(host), "Cache the table")
    path = ideas.state_folder(state, a) / "state.json"
    os.utime(path, (1_700_000_000, 1_700_000_000))
    idea_element.give(root, state, a)
    assert path.stat().st_mtime == 1_700_000_000                                              # an element is no change of the goal


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


def test_the_map_counts_the_runes_the_project_has_before_it_gives(host):
    p, q = party(host), party(host, "Second party")
    given, old, elsewhere = raw(host, p, "Given", "working"), raw(host, p, "Of before", "working"), raw(host, q, "Elsewhere", "working")
    ideas.save_state(host.ideas.state_dir, given, element="meadow")
    nodes = {n["slug"]: n for n in host.command("ideas.map", {})["nodes"]}
    assert nodes[given]["element"] == "meadow" and nodes[old]["element"] == "ice" and nodes[elsewhere]["element"] == "dust"
    assert nodes[given]["hue"] == "meadow"                                                     # an element and no hue: its element is its hue
    one = {n["slug"]: n for n in host.command("ideas.map", {"goal": q})["nodes"]}               # one party's Map counts the others' runes too
    assert one[elsewhere]["element"] == "dust"


def test_a_goal_not_yet_read_has_one_too(host):
    p = party(host)
    a = host.command("ideas.add", {"text": "Not read yet", "track": p, "hold": True})
    (node,) = host.command("ideas.map", {})["nodes"]
    assert node["state"] == "raw" and node["element"] == a["element"] != "" and node["hue"] == a["hue"] != ""


# -- next_for -----------------------------------------------------------------------------------------------------

def test_next_for_is_what_give_gives_the_next_goal(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host), party(host, "Second party")
    assert idea_element.next_for(root, state) == "meadow" and idea_element.next_hue_for(root, state) == "meadow"
    for n in range(7):
        want = idea_element.next_rune_for(root, state)
        assert idea_element.next_rune_for(root, state) == want                                # it reads and stores nothing
        slug = raw(host, p if n % 2 else q, f"Goal number {n}", "working")
        got = idea_element.give(root, state, slug)
        assert (got, idea_element.hue_of(state, slug)) == want
    done = raw(host, p, "Finished", "done")
    ideas.save_state(state, done, element="lava", seen_at=SEEN)
    assert idea_element.next_for(root, state) == idea_element.pick(idea_element.open_elements(root, state))   # a done goal seen does not count


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
        assert g["next_element"] == idea_element.next_for(root, state), slug
        assert g["next_hue"] == idea_element.next_hue_for(root, state), slug
    assert all((g["next_element"], g["next_hue"], g["free_elements"]) == ("meadow", "ice", []) for g in parties.values())     # five goals of the project (the done one not seen) hold the five shapes: meadow again, in the next hue
    one = host.command("ideas.map", {"goal": p})                                              # one party's Map says the same
    assert [(g["next_element"], g["next_hue"]) for g in one["goals"]] == [("meadow", "ice")]


# -- the rune chosen (spec 111 B, decisions §187.3) ----------------------------------------------------------------

def test_free_is_what_no_open_goal_has_in_the_order_and_empty_when_none_is_free():
    free = idea_element.free
    assert free([]) == list(idea_element.ELEMENTS)
    assert free(["ice", "void", "ice"]) == ["meadow", "dust", "lava"]
    assert free(["lava", "void", "dust", "ice", "meadow"]) == []                           # none free: the face shows all of them
    assert free(["fire"]) == list(idea_element.ELEMENTS)                                   # a word that is no element holds none
    used = ["ice"]
    assert free(used) == ["meadow", "dust", "void", "lava"] and used == ["ice"]            # pure


def test_free_for_reads_the_projects_goals(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host), party(host, "Second party")
    assert idea_element.free_for(root, state) == list(idea_element.ELEMENTS)
    a, b = raw(host, p, "Open one", "working"), raw(host, p, "Open two", "working")
    ideas.save_state(state, a, element="meadow")
    ideas.save_state(state, b, element="dust")
    done = raw(host, p, "Finished", "done")
    ideas.save_state(state, done, element="lava", seen_at=SEEN)
    other = raw(host, q, "Another party's", "working")
    ideas.save_state(state, other, element="ice")
    assert idea_element.free_for(root, state) == ["void", "lava"]                          # another party's counts; a done goal seen does not
    ideas.save_state(state, done, seen_at="")
    assert idea_element.free_for(root, state) == ["void"]                                  # a done goal not yet seen does
    ideas.save_state(state, raw(host, q, "Five", "working"), element="void")
    assert idea_element.free_for(root, state) == []                                        # all five are used: empty, never "all"


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


def test_every_party_of_the_map_carries_the_projects_free_shapes(host):
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q, empty = party(host), party(host, "Second party"), party(host, "Third party")
    for n in range(2):
        raw(host, p, f"Open {n}", "working")
    raw(host, p, "Closed", "done")
    raw(host, q, "Only one", "working")
    parties = {g["slug"]: g for g in host.command("ideas.map", {})["goals"]}
    for slug, g in parties.items():
        assert g["free_elements"] == idea_element.free_for(root, state), slug
    assert all(g["free_elements"] == ["lava"] for g in parties.values())                   # four goals hold four shapes (the done one is not seen), one for all parties
    assert all(g["next_element"] == g["free_elements"][0] for g in parties.values())       # the default is a free one while one is free
    for n in range(2):
        raw(host, p, f"More {n}", "working")
    assert all(g["free_elements"] == [] for g in host.command("ideas.map", {})["goals"])   # none free: empty


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


def test_ideas_add_refuses_an_element_that_is_none_of_the_five_and_adds_nothing(host):
    p = party(host)
    before = host.command("ideas.board", {})["ideas"]
    with pytest.raises(Exception, match="five runes"):
        host.command("ideas.add", {"text": "Fire", "track": p, "element": "fire"})
    assert host.command("ideas.board", {})["ideas"] == before


@pytest.mark.parametrize("shape", idea_element.ELEMENTS)
@pytest.mark.parametrize("filtered", [False, True])
@pytest.mark.parametrize("legacy_assignment", [False, True])
def test_map_predicts_every_shapes_host_hue_without_extra_writes(host, monkeypatch, filtered, legacy_assignment, shape):
    """Predictions use all holders after the Map's existing one-time legacy assignment."""
    root, state = host.ideas.root(), host.ideas.state_dir
    p, q = party(host), party(host, "Other party")
    # Cross-party, unseen done and dropped goals hold; seen done goals do not.
    rows = [
        (p, "Open", "working", "meadow", "meadow", ""),
        (q, "Unseen", "done", "meadow", "ice", ""),
        (q, "Seen", "done", "meadow", "dust", SEEN),
        (q, "Dropped", "dropped", "ice", "meadow", ""),
        (q, "Old shape", "working", "ice", "", ""),
    ]
    for track, title, status, shape, hue, seen in rows:
        slug = raw(host, track, title, status)
        ideas.save_state(state, slug, element=shape, hue=hue, seen_at=seen)
    old = raw(host, p, "Needs a rune", "working") if legacy_assignment else None
    writes = []
    real_save = ideas.save_state

    def save(where, slug, **changes):
        writes.append((slug, changes))
        return real_save(where, slug, **changes)

    monkeypatch.setattr(ideas, "save_state", save)
    args = {"goal": p} if filtered else {}
    rev = host.snapshot()["ideas_rev"]
    snapshot = host.command("ideas.map", args)
    assert writes == ([(old, {"element": "dust", "hue": "meadow"})] if old else [])
    expected = {"meadow": "dust", "ice": "dust", "dust": "ice" if old else "meadow",
                "void": "meadow", "lava": "meadow"}
    assert snapshot["goals"]
    for g in snapshot["goals"]:
        assert list(g["next_hues"]) == list(idea_element.ELEMENTS)
        assert g["next_hues"] == expected
        assert g["next_hues"][g["next_element"]] == g["next_hue"]
        assert g["free_elements"] == (["void", "lava"] if old else ["dust", "void", "lava"])
    writes.clear()
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in state.rglob("state.json")}
    assert host.command("ideas.map", args)["goals"] == snapshot["goals"]
    assert writes == []
    assert {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in before} == before
    assert host.snapshot()["ideas_rev"] == rev
    # Each parametrized case submits one shape against exactly the state read above.
    allocated = host.command("ideas.add", {"text": "Prediction probe", "track": p, "element": shape, "hold": True})
    assert (allocated["element"], allocated["hue"]) == (shape, expected[shape])
