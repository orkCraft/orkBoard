"""Spec 99 E §7.1 (`realm/spec_sections.py`): the spec's format — a common part and a section a party with its `###` parts; a page of before read as one section of its party; a
leader's answer taken strictly; *Will be* and who decided a change on a map. Pure code."""
from __future__ import annotations

from orkboard.realm import idea_page, spec_sections as ss

PARTIES = [{"slug": "tech", "title": "Tech"}, {"slug": "art", "title": "Art"}]
TECH = "### Why\nBecause.\n\n### Done when\n- It works\n- It is fast\n\n### Will be\n- changed orkboard/core — the keeper\n- new orkboard/core/idea_decide.py\n- gone old"


def page(*sections, meta="owner: board"):
    return idea_page.parse(f"---\n{meta}\n---\n# Goal\n" + "".join(f"\n## {n}\n{t}\n" for n, t in sections))


def test_the_parts_of_a_section_are_split_and_joined_in_the_order_they_are_written():
    parts = ss.split("Before.\n\n### Out\n- no\n\n### Why\nBecause.\n### Odd one\nx")
    assert parts == {"": "Before.", "Out": "- no", "Why": "Because.", "Odd one": "x"}
    assert ss.join({"Out": "- no", "Why": "Because.", "Odd one": "x", "Done when": ""}) == "### Why\nBecause.\n\n### Out\n- no\n\n### Odd one\nx"
    assert ss.split(ss.join(ss.split(TECH))) == ss.split(TECH) and ss.split("") == {} and ss.split("plain") == {"": "plain"}


def test_a_party_section_is_one_that_is_no_common_or_old_name_and_holds_a_known_part():
    assert ss.is_party("Tech", TECH) and ss.is_party("Game design", "### Why\nx")
    assert not ss.is_party("Tech", "just words") and not ss.is_party("Tech", "### Odd\nx")
    assert not ss.is_party("Gist", TECH) and not ss.is_party("Done when", TECH) and not ss.is_party("risks", TECH)
    assert ss.section_name("Tech") == "Tech" and ss.section_name("Risks") == "Risks (party)" and ss.section_name("Tech", {"tech"}) == "Tech (party)"
    assert ss.section_name("A ## title\nwith lines") == "A title with lines"


def test_a_page_of_the_new_format_is_a_common_part_and_a_section_a_party():
    p = page(("Asked", "add it"), ("Gist", "Add it"), ("Route", "1. Tech"), ("Depends on", ""), ("Decisions", "- x"), ("Tech", TECH), ("Art", "### Why\nLook."))
    got = ss.read(p, PARTIES, "tech")
    assert got["common"] == {"Asked": "add it", "Gist": "Add it", "Route": "1. Tech", "Depends on": "", "Decisions": "- x"}
    assert [(s.party, s.title, s.older) for s in got["sections"]] == [("tech", "Tech", False), ("art", "Art", False)]
    assert got["sections"][0].parts["Done when"] == "- It works\n- It is fast"
    assert [s.party for s in ss.read(p)["sections"]] == ["", ""]                                              # no parties known: the headings alone


def test_a_page_of_before_reads_as_one_section_of_its_party_and_nothing_is_rewritten():
    p = page(("Gist", "Add dark mode"), ("Why", "People read at night."), ("Done when", "- Setting exists"), ("Out", "- Scheduling"), ("Risks", "Low."), ("Stages", "1. k1"),
             ("Open questions", ""), ("Decisions", ""))
    before = p.text()
    got = ss.read(p, PARTIES, "tech")
    assert got["common"]["Gist"] == "Add dark mode" and len(got["sections"]) == 1
    one = got["sections"][0]
    assert (one.party, one.title, one.older) == ("tech", "Tech", True)
    assert one.parts == {"Why": "People read at night.", "Done when": "- Setting exists", "Out": "- Scheduling", "Risks": "Low."}
    assert p.text() == before and ss.sections_of(p) == []
    assert ss.read(page(("Gist", "x")), PARTIES, "")["sections"] == []                                         # nothing written, no party: no section


def test_the_new_page_answers_for_the_old_sections_by_its_first_section_and_every_sections_done_when():
    p = page(("Gist", "G"), ("Why", ""), ("Tech", TECH), ("Art", "### Why\nLook.\n\n### Done when\n- Pretty\n\n### Out\n- art out"))
    assert ss.folded(p, "Why") == "Because." and ss.folded(p, "Out") == "" and ss.folded(p, "Done when") == "- It works\n- It is fast\nArt: Pretty"
    assert ss.folded(p, "Gist") == "" and ss.folded(page(("Gist", "G")), "Why") == ""
    assert ss.FOLDED == idea_page.FOLDED


def test_a_leaders_answer_is_taken_strictly():
    ok = {"why": " Because  it matters. ", "done_when": ["a", "b", "c", "d", "e", "f", "a"], "checks": ["check"], "will_be": ["changed src/x — why", "new src/y", "gone ../z", "wrong", "changed " + "x" * 300],
          "out": ["o1", "o2", "o3", "o4"], "risks": ["r"], "risk": "HIGH", "assumed": ["a1"], "questions": [{"ask": "never written"}]}
    parts, risk = ss.clean_section(ok, ["q — a (its leader's pick)"])
    assert risk == "high" and parts["Why"] == "Because it matters." and parts["Done when"] == "- a\n- b\n- c\n- d\n- e"                    # five theses at most, a repeat once
    assert parts["Will be"] == "- changed src/x — why\n- new src/y" and parts["Out"] == "- o1\n- o2\n- o3" and "Questions" not in parts
    assert parts["Defaults"] == "- q — a (its leader's pick)\n- Assumed: a1" and parts["Checks"] == "- check" and parts["Risks"] == "- r"
    assert ss.clean_section({"why": "w", "done_when": ["t"], "risk": "enormous"})[1] == "low"
    for bad in (None, "x", {}, {"why": "w"}, {"done_when": ["t"]}, {"why": "w", "done_when": "t"}, {"why": 3, "done_when": ["t"]}):
        assert ss.clean_section(bad) is None


def test_a_will_be_names_the_parts_of_the_map_by_their_ids():
    assert ss.will_be(TECH.split("### Will be\n")[1]) == [{"kind": "changed", "id": "orkboard/core", "note": "the keeper"}, {"kind": "new", "id": "orkboard/core/idea_decide.py", "note": ""},
                                                          {"kind": "gone", "id": "old", "note": ""}]
    assert ss.will_be("nothing changes\n- a prose line\n- changed ../x") == []
    assert ss.same_part("orkboard/core", "orkboard/core/idea_decide.py") and ss.same_part("a/b/", "a/b") and not ss.same_part("orkboard/core", "orkboard/corex")
    assert not ss.same_part("", "a")


def test_who_decided_a_change_the_leader_the_person_by_a_fork_or_a_member_alone():
    p = page(("Gist", "G"), ("Decisions", "- 2026-10-28: Decision 4: x\n- 2026-10-28: Fork — waves: Six [sections: Art, Tech]"), ("Tech", TECH), ("Art", "### Why\nLook.\n\n### Will be\n- changed web"))
    assert ss.decided_by(p, "orkboard/core") == "person"                                                      # Tech's section was written again by a fork the person answered
    assert ss.decided_by(p, "web/ui") == "person" and ss.decided_by(p, "orkboard/gui") == "member"             # … Art's too; nobody promised the gui
    plain = page(("Gist", "G"), ("Tech", TECH))
    assert ss.decided_by(plain, "orkboard/core/x.py") == "leader" and ss.decided_by(plain, "somewhere") == "member"
    assert ss.decided_by(page(("Gist", "G"), ("Why", "old")), "orkboard/core") == ""                           # a page of before has no Will be


def test_the_page_is_arranged_common_part_first_then_a_section_a_party_and_what_else_it_holds_is_kept():
    p = page(("Gist", "words"), ("Why", ""), ("Done when", ""), ("Out", ""), ("Risks", "Risk: Low"), ("Depends on", ""), ("Stages", ""), ("Open questions", ""), ("Decisions", "- d"), ("Notes", "mine"))
    ss.arrange(p, {"Asked": "words", "Gist": "One line", "Route": "1. Tech"}, [("Tech", TECH)])
    assert [n for n, _t in p.sections] == ["Asked", "Gist", "Route", "Depends on", "Decisions", "Tech", "Risks", "Notes"]       # the empty old ones went; a known one with words stays
    assert p.section("Gist") == "One line" and p.section("Decisions") == "- d" and p.section("Notes") == "mine"
    ss.arrange(p, {"Gist": "Again"}, [("Tech", "### Why\nNew.")])
    assert p.section("Tech") == "### Why\nNew." and p.section("Asked") == "words" and [n for n, _t in p.sections].count("Tech") == 1


def test_the_record_is_kept_beside_the_goals_state(tmp_path):
    assert ss.record(tmp_path, "a-goal") == {}
    ss.save_record(tmp_path, "a-goal", {"joined": True})
    assert ss.record(tmp_path, "a-goal") == {"joined": True} and (tmp_path / "ideas" / "a-goal" / "way.json").is_file()
