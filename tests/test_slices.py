"""Spec 131 A.1 (docs/specs/131-a-leaders-slices-and-the-cascade.md; decisions §233): the store of the leaders' slices, `realm/slices.py`: from nothing, a decision cut once with *none* kept as none, a replacement that
keeps the old and says `was` (and the `was` goes at the next), `resting_on` matching a decision with its points both ways, `text` fitting `CALL_CHARS` with the digest first and `(N older not shown)`, the fold's
bound and a file that is broken. No model, no face."""
from __future__ import annotations

import json

import pytest

from orkboard.realm import slices


def _cut(state, n, **answers):
    return slices.add_cut(state, n, {p: (None if a is None else a) for p, a in answers.items()})


def _says(says, *points, replaces=()):
    return {"says": says, "points": list(points), "replaces": list(replaces)}


# -- from nothing ------------------------------------------------------------------------------------------------------------------------





def test_the_first_cut_sets_from_and_keeps_it_beside_the_store_and_it_is_never_moved(tmp_path):
    (tmp_path / "project.json").write_text(json.dumps({"stage": "live"}), encoding="utf-8")
    _cut(tmp_path, 233, tech=_says("Your tests run first.", "233.3"))
    assert slices.from_(tmp_path) == 233 and slices.kept_from(tmp_path) == 233 and slices.exists(tmp_path)
    assert json.loads((tmp_path / "project.json").read_text(encoding="utf-8")) == {"stage": "live", "slices_from": 233}      # the file's other keys stay
    _cut(tmp_path, 234, tech=_says("Your builds are small.", "234.1"))
    _cut(tmp_path, 12, tech=_says("An older one.", "12.1"))                                                                  # a cut of an earlier number does not move it
    assert slices.from_(tmp_path) == 233 and slices.kept_from(tmp_path) == 233


# -- add_cut ------------------------------------------------------------------------------------------------------------------------------

def test_a_party_with_none_is_kept_as_none_and_a_decision_is_cut_once(tmp_path):
    added = _cut(tmp_path, 233, tech=_says("Your tests run first.", "233.3"), art=None, design=_says("", "233.1"))        # no words are none too
    assert [s["party"] for s in added] == ["tech"] and added[0]["id"].startswith("s-") and added[0]["decision"] == 233
    store = slices.read(tmp_path)
    assert store["cut"] == {"233": ["tech"]} and slices.is_cut(tmp_path, 233)                    # art and design are not there: that is the answer
    assert _cut(tmp_path, 233, tech=_says("Cut again.", "233.1")) == []                         # never twice
    assert len(slices.read(tmp_path)["slices"]) == 1
    _cut(tmp_path, 234, tech=None, art=None)                                                    # a decision that touches nobody is cut too
    assert slices.is_cut(tmp_path, 234) and slices.read(tmp_path)["cut"]["234"] == []




# -- a replacement ------------------------------------------------------------------------------------------------------------------------

def test_a_replacement_keeps_the_old_slice_sets_replaced_by_and_says_was(tmp_path):
    (old,) = _cut(tmp_path, 159, art=_says("Your screens hold 10 seconds.", "159.1"))
    (new,) = _cut(tmp_path, 240, art=_says("Your screens hold 6 seconds.", "240.2", replaces=[old["id"]]))
    assert new["was"] == "Your screens hold 10 seconds (§159.1)" and len(new["was"]) <= slices.WAS_CHARS
    assert [s["id"] for s in slices.standing(tmp_path, "art")] == [new["id"]]
    both = {s["id"]: s for s in slices.read(tmp_path)["slices"]}
    assert both[old["id"]]["replaced_by"] == new["id"] and both[old["id"]]["says"] == "Your screens hold 10 seconds." and set(both) == {old["id"], new["id"]}      # kept, never edited




def test_a_replaces_that_is_another_partys_or_already_replaced_or_unknown_is_ignored(tmp_path):
    (t,) = _cut(tmp_path, 1, tech=_says("Tech one.", "1.1"))
    (a,) = _cut(tmp_path, 2, art=_says("Art one.", "2.1"))
    (a2,) = _cut(tmp_path, 3, art=_says("Art two.", "3.1", replaces=[a["id"]]))
    (a3,) = _cut(tmp_path, 4, art=_says("Art three.", "4.1", replaces=[t["id"], a["id"], "s-nothing"]))             # tech's, an already replaced one, and one that is none
    assert a3["was"] == "" and [s["id"] for s in slices.standing(tmp_path, "tech")] == [t["id"]]
    assert [s["id"] for s in slices.standing(tmp_path, "art")] == [a3["id"], a2["id"]]                                  # newest first; a2 still stands
    assert {s["id"]: s["replaced_by"] for s in slices.read(tmp_path)["slices"]}[a["id"]] == a2["id"]


# -- resting_on ---------------------------------------------------------------------------------------------------------------------------

def test_resting_on_matches_a_decision_with_its_points_both_ways_and_leaves_out_the_proposers_own(tmp_path):
    _cut(tmp_path, 240, tech=_says("Tech on the point.", "240.2"), art=_says("Art on the whole.", "240"), design=_says("Design on another point.", "240.3"), release=_says("Elsewhere.", "241.2"))
    names = lambda pts, **k: [s["party"] for s in slices.resting_on(tmp_path, pts, **k)]
    assert sorted(names(["240.2"])) == ["art", "tech"]                                         # "240.2" meets the slice on "240.2" and the one on "240" as a whole
    assert sorted(names(["240"])) == ["art", "design", "tech"]                                 # "240" meets every point of 240
    assert names(["240.2"], but="tech") == ["art"] and names(["24"]) == [] and names([]) == []
    assert sorted(names(["241.2", "240.3"])) == ["art", "design", "release"]                   # (art rests on 240 as a whole)






# -- text ---------------------------------------------------------------------------------------------------------------------------------



def test_text_fits_call_chars_the_digest_first_and_says_how_many_older_are_not_shown(tmp_path):
    for n in range(1, 11):
        _cut(tmp_path, n, tech=_says(f"Slice number {n:02d} " + "w" * 150, f"{n}.1"))
    got = slices.text(tmp_path, "tech")
    assert len(got) <= slices.CALL_CHARS and "Slice number 10" in got and "Slice number 01" not in got
    shown = got.count("- Slice number")
    assert got.endswith(f"({10 - shown} older not shown)") and 0 < shown < 10
    assert [s["says"][:15] for s in slices.past_bound(tmp_path, "tech")] == [f"Slice number {n:02d}" for n in range(1, 11 - shown)]       # the oldest first: what the fold reads
    ids = [s["id"] for s in slices.past_bound(tmp_path, "tech")]
    slices.save_digest(tmp_path, "tech", "You keep early slices short (§1.1).", ids)
    after = slices.text(tmp_path, "tech")
    left = slices.past_bound(tmp_path, "tech")
    assert after.splitlines()[1] == "In short: You keep early slices short (§1.1)."              # the digest first
    assert len(after) <= slices.CALL_CHARS and after.splitlines()[-1] == f"({len(left)} older not shown)"   # what the digest took room of is past the bound for the next fold; nothing is left out unseen




# -- the fold ----------------------------------------------------------------------------------------------------------------------------



def test_a_folded_slice_replaced_since_is_said_to_have_gone_until_its_replacement_is_folded(tmp_path):
    (a,) = _cut(tmp_path, 1, tech=_says("Ten seconds.", "1.1"))
    slices.save_digest(tmp_path, "tech", "You hold ten seconds (§1.1).", [a["id"]])
    assert slices.gone(tmp_path, "tech") == []
    (b,) = _cut(tmp_path, 2, tech=_says("Six seconds.", "2.1", replaces=[a["id"]]))
    (g,) = slices.gone(tmp_path, "tech")
    assert g["slice"]["id"] == a["id"] and g["replaced_by"]["id"] == b["id"]
    slices.save_digest(tmp_path, "tech", "You hold six seconds (§2.1).", [b["id"]])
    assert slices.gone(tmp_path, "tech") == []


# -- a file that is broken ----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["", "{not json", "[]", '"text"', '{"slices": "x", "cut": [], "digests": 3, "from": "a"}'])
def test_a_broken_file_reads_empty_and_a_line_that_is_no_slice_is_left_out(tmp_path, raw):
    (tmp_path / "slices.json").write_text(raw, encoding="utf-8")
    assert slices.read(tmp_path) == {"v": 1, "from": None, "cut": {}, "slices": [], "digests": {}}
    assert slices.text(tmp_path, "tech") == "" and slices.standing(tmp_path, "tech") == [] and slices.is_cut(tmp_path, 1) is False
    assert slices.exists(tmp_path)                                                              # only a missing file is cut again from the decisions






