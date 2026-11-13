"""Spec 154 B.1 (`realm/page_talk.py`; decisions §258.6): a leader's *Talk* and *Accepted* written into its section of the goal's page and read back; every other part and section kept byte for byte; the
section made when the page has none; the party found by its title or its slug; the limits. Pure code over a `Page`."""
from __future__ import annotations

from orkboard.realm import idea_page, page_talk as pt, spec_sections

TECH = "### Why\nBecause.\n\n### Done when\n- [test] the board shows the best three players\n- a tie is ordered by the earlier score\n- the board loads in under a second\n\n### Will be\n- changed web — the board"
ART = "### Why\nLook.\n\n### Done when\n- It is pretty\n\n### Notes\nfree words — kept"
PAGE = f"---\nowner: board\nschema: 2\n---\n# Goal\n\n## Asked\nadd a board\n\n## Gist\nAdd a board\n\n## Tech\n{TECH}\n\n## Art\n{ART}\n\n## Open questions\n- Which store? [**A**, B]\n"
SAY = {"verdict": "doubt", "why": "the cache adds a second caller to the store", "stance": "Tech can build it in a step if the store keeps one writer", "for": "one screen, no new service",
       "against": "a second writer to the store", "instead": "show the cached board only", "assumes": {"text": "players reload less than once a minute", "signal": "the reload events of a week"}}
LINES = [{"line": "the board shows the best three players", "status": "met", "why": ""},
         {"line": "a tie is ordered by the earlier score", "status": "not met", "why": "the order is by name"},
         {"line": "the board loads in under a second", "status": "cannot see", "why": ""}]


def page() -> idea_page.Page:
    return idea_page.parse(PAGE)


def test_a_say_is_written_in_the_specs_format_and_read_back_the_same():
    p = page()
    assert pt.write_talk(p, "Tech", SAY) == SAY
    assert p.section("Tech").endswith("### Talk\n- verdict: doubt — the cache adds a second caller to the store\n- stance: Tech can build it in a step if the store keeps one writer\n- for: one screen, no new service\n"
                                      "- against: a second writer to the store\n- instead: show the cached board only\n- assumes: players reload less than once a minute — shown by: the reload events of a week")
    assert pt.read_talk(p, "Tech") == SAY
    again = idea_page.parse(p.text())
    assert pt.read_talk(again, "Tech") == SAY and pt.read_talk(again, "Art") is None and pt.read_talk(again, "Product") is None


def test_the_acceptance_is_written_and_read_back_the_same_and_a_why_may_follow_a_dash():
    p = page()
    assert pt.write_accepted(p, "Tech", LINES) == LINES
    assert p.section("Tech").endswith("### Accepted\n- met: the board shows the best three players\n- not met: a tie is ordered by the earlier score — the order is by name\n- cannot see: the board loads in under a second")
    assert pt.read_accepted(idea_page.parse(p.text()), "Tech") == LINES and pt.read_accepted(p, "Art") == []
    # a Done when line that holds a dash itself is still one line
    q = idea_page.parse(PAGE.replace("- It is pretty", "- It is pretty — and quick"))
    pt.write_accepted(q, "Art", [{"line": "[look] It is pretty — and quick", "status": "not met", "why": "slow"}, {"line": "It is pretty — and quick", "status": "met"}])
    assert pt.read_accepted(q, "Art") == [{"line": "It is pretty — and quick", "status": "not met", "why": "slow"}, {"line": "It is pretty — and quick", "status": "met", "why": ""}]


def test_the_section_is_made_when_the_page_has_none_in_the_specs_format_after_the_last_party_section():
    p = page()
    pt.write_talk(p, "Product", {"verdict": "go", "stance": "Fine."})
    assert [n for n, _t in p.sections] == ["Asked", "Gist", "Tech", "Art", "Product", "Open questions"]
    assert p.section("Product") == "### Talk\n- verdict: go\n- stance: Fine."
    pt.write_accepted(p, "Product", [{"line": "x", "status": "met"}])
    assert p.section("Product") == "### Talk\n- verdict: go\n- stance: Fine.\n\n### Accepted\n- met: x"
    assert idea_page.parse(p.text()).sections == p.sections
    bare = idea_page.parse("---\nowner: board\n---\n# G\n\n## Gist\nWords\n")
    pt.write_talk(bare, "Game design", {"verdict": "no", "why": "too big"})
    assert [n for n, _t in bare.sections] == ["Gist", "Game design"] and pt.read_talk(bare, "game-design")["verdict"] == "no"
    assert spec_sections.sections_of(bare) == []                                          # a Talk alone makes no spec section: the page stays one of before
    pt.write_talk(bare, "Risks", {"verdict": "go"})                                       # a party titled as a common section gets the format's name for it
    assert bare.sections[-1][0] == "Risks (party)" and pt.read_talk(bare, "Risks") == pt.read_talk(bare, "Risks (party)") is not None


def test_talk_and_accepted_are_no_spec_part_the_page_still_folds_and_counts_as_before():
    p = page()
    pt.write_talk(p, "Tech", SAY)
    pt.write_accepted(p, "Tech", LINES)
    assert spec_sections.folded(p, "Done when") == spec_sections.folded(page(), "Done when") and p.section("Why") == "Because."
    assert len(spec_sections.items(spec_sections.split(p.section("Tech"))["Done when"])) == 3
    assert [s.party for s in spec_sections.read(p, [{"slug": "tech", "title": "Tech"}])["sections"]] == ["tech", ""]




def test_the_limits_are_the_calls_own_and_a_doubt_with_no_why_reads_as_go():
    p = page()
    got = pt.write_talk(p, "Tech", {"verdict": " DOUBT ", "why": "", "stance": "word " * 100, "for": "a\nb\n\nc", "assumes": {"text": "only text", "signal": ""}})
    assert got["verdict"] == "go" and len(got["stance"]) <= pt.LINE_CHARS and got["for"] == "a b c" and got["assumes"] is None and got["instead"] == ""
    assert "- verdict: go\n" in p.section("Tech") + "\n" and "assumes" not in p.section("Tech") and "\n- instead" not in p.section("Tech")
    hand = idea_page.parse(PAGE.replace("## Art\n", "## Art\n### Talk\n- verdict: no\n- stance: hmm\n\n"))
    assert pt.read_talk(hand, "Art")["verdict"] == "go"                                    # a no with no why, written by hand, reads as go
    assert pt.read_talk(idea_page.parse(PAGE.replace("## Art\n", "## Art\n### Talk\n- verdict: maybe — x\n\n")), "Art") is None
    assert pt.write_talk(p, "Tech", {"verdict": "maybe"}) is None and pt.write_talk(p, "Tech", "go") is None and pt.write_talk(p, "", None) is None
    many = [{"line": f"line {i}", "status": "met"} for i in range(30)] + [{"line": "", "status": "met"}, {"line": "bad", "status": "yes"}]
    assert len(pt.write_accepted(p, "Tech", many)) == pt.MAX_ACCEPTED and pt.write_accepted(p, "Art", [{"line": "x", "status": "perhaps"}, "nope"]) == []
    assert all(len(x["line"]) <= pt.LINE_CHARS for x in pt.read_accepted(p, "Tech")) and "### Accepted" not in p.section("Art")
    long = pt.write_accepted(p, "Art", [{"line": "y " * 300, "status": "met", "why": "z " * 300}])[0]
    assert len(long["line"]) <= pt.LINE_CHARS and len(long["why"]) <= pt.LINE_CHARS
