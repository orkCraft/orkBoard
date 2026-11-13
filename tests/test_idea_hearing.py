"""Spec 120 D (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §4.1–§4.2, §7) in pure code: the sides of a Talk's disagreement (every mix of verdicts) and of a fork of two, three and
four sides, who stands where, and when a hearing is open. No host, no model."""
from __future__ import annotations


from orkboard.realm import idea_hearing
from orkboard.realm.idea_hearing import of_fork, of_talk

NAMES = {"pm": "Product Manager", "des": "Designer", "arch": "Architect", "rel": "Release Manager"}


def name_of(leader):
    return NAMES.get(leader, leader)


def st(party, leader, verdict="go", why="", instead="", after="", after_title="", **more):
    return {"party": party, "leader": leader, "stance": f"{party} stance", "for": f"{party} for", "against": f"{party} against", "verdict": verdict, "why": why, "instead": instead,
            "after": after, "after_title": after_title, **more}


def talk(*stances):
    return of_talk({"mode": "talk", "stances": list(stances)}, name_of)


def kinds(got):
    return [(s["dir"], s["kind"]) for s in got["sides"]]


def test_go_is_always_right_with_the_words_of_the_first_leader_who_said_go_and_the_others_named_after_it():
    got = talk(st("p", "pm"), st("d", "des"), st("t", "arch", "no", "It adds a third caller"))
    go, drop = got["sides"]
    assert (go["dir"], go["kind"], go["outcome"], go["leaders"], go["names"]) == ("right", "go", "Do it", ["p", "d"], ["Product Manager", "Designer"])
    assert go["line"] == "p for" and go["also"] == ["Designer"] and go["doubts"] == []
    assert (drop["dir"], drop["kind"], drop["outcome"], drop["leaders"], drop["line"], drop["also"]) == ("left", "drop", "Drop it", ["t"], "It adds a third caller", [])
    assert got["moment"] == "talk" and got["own"] is True and got["left_out"] == [] and got["title"] == "Architect says no"


def test_a_no_with_an_instead_is_the_smaller_one_at_the_top_the_first_in_the_routes_order_and_its_leaders_who_said_the_same():
    got = talk(st("p", "pm", "doubt", "Costs too much", instead="Only the setting"), st("d", "des", "no", "Another look", instead="Only a switch"), st("t", "arch", "no", "No", instead="only the setting"))
    assert kinds(got) == [("right", "go"), ("up", "smaller")]
    up = got["sides"][1]
    assert up["outcome"] == "Do the smaller one: Only the setting" and up["instead"] == "Only the setting" and up["leaders"] == ["p", "t"]          # the first instead; one who said it the same way joins it
    assert up["line"] == "Costs too much" and up["also"] == ["Architect"]
    assert got["title"] == "Product Manager, Designer and Architect disagree"


def test_a_no_that_names_a_goal_in_line_is_after_that_goal_at_the_left():
    got = talk(st("p", "pm", "no", "The lobby comes first", after="g-lobby", after_title="Add a lobby"), st("t", "arch"))
    assert kinds(got) == [("right", "go"), ("left", "later")]
    left = got["sides"][1]
    assert left["outcome"] == "After Add a lobby" and left["after"] == "g-lobby" and left["after_title"] == "Add a lobby" and left["leaders"] == ["p"]
    assert talk(st("p", "pm", "no", "w", after="g-lobby"))["sides"][1]["outcome"] == "After g-lobby"                           # its title not known: the goal's own name


def test_left_takes_the_first_of_drop_and_later_and_up_the_next_of_smaller_later_drop():
    drop, later, small = st("a", "pm", "no", "drop it"), st("b", "des", "no", "later", after="g1", after_title="G1"), st("c", "arch", "no", "smaller", instead="Less")
    assert kinds(talk(drop)) == [("right", "go"), ("left", "drop")]
    assert kinds(talk(small)) == [("right", "go"), ("up", "smaller")]                                                          # smaller is never left
    assert kinds(talk(later)) == [("right", "go"), ("left", "later")]
    assert kinds(talk(drop, later)) == [("right", "go"), ("left", "drop"), ("up", "later")]
    assert kinds(talk(drop, small)) == [("right", "go"), ("left", "drop"), ("up", "smaller")]
    assert kinds(talk(later, small)) == [("right", "go"), ("left", "later"), ("up", "smaller")]


def test_a_hearing_is_open_while_a_no_waits_or_the_weigher_said_so():
    pending = {"mode": "talk", "objections": [{"party": "t", "answer": ""}]}
    assert idea_hearing.is_open(pending) is True
    assert idea_hearing.is_open({"mode": "talk", "objections": [{"party": "t", "answer": "go"}]}) is False
    assert idea_hearing.is_open({"mode": "talk", "objections": [], "hearing": True}) is True
    assert idea_hearing.is_open({"mode": "bug", "objections": [{"answer": ""}]}) is False and idea_hearing.is_open({}) is False


# -- a fork -------------------------------------------------------------------------------------------------------------------------------------

def fork(n):
    return {"id": "f1", "about": "How many waves", "status": "open",
            "sides": [{"party": f"p{k}", "leader": "pm" if k % 2 else "arch", "says": f"{k} waves", "why": f"because {k}"} for k in range(1, n + 1)]}


def test_a_fork_of_two_and_three_sides_goes_right_left_up():
    two = of_fork(fork(2))
    assert [(s["dir"], s["kind"], s["party"], s["line"], s["outcome"]) for s in two["sides"]] == [("right", "side", "p1", "because 1", "1 waves"), ("left", "side", "p2", "because 2", "2 waves")]
    assert two["moment"] == "fork" and two["id"] == "f1" and two["about"] == two["title"] == "How many waves" and two["own"] is True and two["left_out"] == []
    three = of_fork(fork(3))
    assert [(s["dir"], s["outcome"]) for s in three["sides"]] == [("right", "1 waves"), ("left", "2 waves"), ("up", "3 waves")]

