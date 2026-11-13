"""Spec 99 E §7.1 (`realm/spec_sections.py`): the spec's format — a common part and a section a party with its `###` parts; a page of before read as one section of its party; a
leader's answer taken strictly; *Will be* and who decided a change on a map. Pure code."""
from __future__ import annotations

from orkboard.realm import idea_page, spec_sections as ss

PARTIES = [{"slug": "tech", "title": "Tech"}, {"slug": "art", "title": "Art"}]
TECH = "### Why\nBecause.\n\n### Done when\n- It works\n- It is fast\n\n### Will be\n- changed orkboard/core — the keeper\n- new orkboard/core/idea_decide.py\n- gone old"


def page(*sections, meta="owner: board"):
    return idea_page.parse(f"---\n{meta}\n---\n# Goal\n" + "".join(f"\n## {n}\n{t}\n" for n, t in sections))






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






def test_clean_section_takes_done_when_as_strings_or_as_lines_with_a_proof_and_writes_the_mark():
    got = ss.clean_section({"why": "w", "done_when": ["plain", {"line": "  When a, then b ", "proof": "TEST"}, {"line": "c", "proof": "weird"}, {"line": "d"}, {"line": "", "proof": "test"},
                                                      {"line": "e", "proof": "person"}, {"proof": "look"}, "[look] f"]})
    assert got[0]["Done when"] == "- plain\n- [test] When a, then b\n- c\n- d\n- [person] e"                                  # a bad proof dropped, the line kept; five at most
    parts = ss.clean_section({"why": "w", "done_when": ["[look] f", {"line": "[test] g", "proof": "look"}, {"line": "plain"}, {"line": "plain", "proof": "test"}]})[0]
    assert parts["Done when"] == "- [look] f\n- [look] g\n- plain\n- [test] plain"
    assert ss.clean_section({"why": "w", "done_when": [{"line": "", "proof": "test"}]}) is None


def test_talk_and_accepted_are_parts_the_section_knows_but_no_spec_part():
    """Spec 154 B.2: never folded, never counted as Done when, never lost by the sections' writer, and no `##` of that name is a party."""
    said = TECH + "\n\n### Talk\n- verdict: go\n\n### Accepted\n- met: It works"
    p = page(("Gist", "G"), ("Tech", said), ("Art", "### Why\nLook.\n\n### Done when\n- Pretty"))
    assert ss.split(said)["Talk"] == "- verdict: go" and ss.split(said)["Accepted"] == "- met: It works"
    assert ss.items(ss.split(said)["Done when"]) == ["It works", "It is fast"] and ss.folded(p, "Done when") == "- It works\n- It is fast\nArt: Pretty"
    assert ss.folded(p, "Talk") == "" and ss.folded(p, "Accepted") == ""
    assert ss.is_party("Tech", said) and not ss.is_party("Tech", "### Talk\n- verdict: go") and not ss.is_party("Talk", TECH) and not ss.is_party("accepted", TECH)
    assert ss.section_name("Talk") == "Talk (party)"
    assert ss.join(ss.split(said)).endswith("### Talk\n- verdict: go\n\n### Accepted\n- met: It works") and ss.join({"Accepted": "- met: x", "Talk": "- verdict: go", "Why": "w"}) == "### Why\nw\n\n### Talk\n- verdict: go\n\n### Accepted\n- met: x"
    # the writer: a section written again with the spec's parts only keeps the leader's Talk and Accepted; a writer that gives its own keeps its own
    ss.arrange(p, {}, [("Tech", "### Why\nNew.\n\n### Done when\n- It works")])
    assert ss.split(p.section("Tech")) == {"Why": "New.", "Done when": "- It works", "Talk": "- verdict: go", "Accepted": "- met: It works"}
    ss.arrange(p, {}, [("Tech", "### Why\nNewer.\n\n### Talk\n- verdict: no — x")])
    assert ss.split(p.section("Tech")) == {"Why": "Newer.", "Talk": "- verdict: no — x", "Accepted": "- met: It works"}
    assert ss.read(p, PARTIES)["sections"][0].parts["Talk"] == "- verdict: no — x"
