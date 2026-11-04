"""Spec 133 C (docs/specs/133-a-hypothesis-its-two-conditions-its-test-its-file.md; decisions §235.6): the project's own hypotheses file, `realm/hypotheses_file.py` (the Markdown, pure) and its bound
reading and writing in `realm/hypotheses.py` (`realm/hypotheses_bind.py`). No model; the Board's tree is the gui test's."""
from __future__ import annotations

import difflib
import json
from pathlib import Path

import pytest

from orkboard.realm import hypotheses as hyp, hypotheses_file as hf

OWN = Path(__file__).resolve().parent.parent / "docs" / "hypotheses.md"          # this repository's own file: H1–H4


def changed(old: str, new: str) -> list[str]:
    return [ln for ln in difflib.unified_diff(old.split("\n"), new.split("\n"), lineterm="", n=0) if ln[:1] in "+-" and ln[:3] not in ("+++", "---")]


# -- where ------------------------------------------------------------------------------------------------------------------------------------

def test_the_file_is_the_chosen_one_else_docs_hypotheses_never_outside_the_root_nor_a_link(tmp_path):
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    assert hf.find(root) is None
    (root / "docs" / "hypotheses.md").write_text("# H\n")
    assert hf.find(root) == "docs/hypotheses.md"
    (root / "ideas.md").write_text("# H\n")
    assert hf.find(root, "ideas.md") == "ideas.md" and hf.find(root, "nope.md") == "docs/hypotheses.md"
    (tmp_path / "outside.md").write_text("# H\n")
    assert hf.find(root, "../outside.md") == "docs/hypotheses.md"
    (root / "link.md").symlink_to(tmp_path / "outside.md")
    assert hf.find(root, "link.md") == "docs/hypotheses.md"
    (root / "docs" / "hypotheses.md").unlink()
    assert hf.find(root, "link.md") is None and hf.find(root, "docs") is None


# -- read: this repository's own file -------------------------------------------------------------------------------------------------------

def test_the_own_file_reads_as_four_hypotheses_with_their_conditions_and_drafts():
    got = hf.parse(OWN.read_text("utf-8"))
    assert got["skipped"] == [] and [i["id"] for i in got["items"]] == ["h1", "h2", "h3", "h4"]
    h1, h2, h3, h4 = got["items"]
    assert [i["state"] for i in got["items"]] == ["open"] * 4                                  # `testing` is the goals' to say, not the file's
    assert h1["text"].startswith("Orkboard is a studio that sees your real product") and h1["signal"].startswith("on the same real tasks, goals made in Orkboard")
    assert [w["name"] for w in h1["refuted"]] == [""] and h1["refuted"][0]["when"].startswith("no difference in first-time acceptance")            # `Refutes:` has no name
    assert h2["signal"].startswith("over the owner's week") and h2["refuted"][0]["when"].startswith("sketches are mostly skipped")
    assert h3["signal"].startswith("the Camp clip's install costs at least 30% less") and [w["name"] for w in h3["refuted"]] == ["the look", "the gap"]
    assert h3["refuted"][1]["when"].startswith("the Camp clip is cheaper, but its people drop")
    assert [w["name"] for w in h4["refuted"]] == ["the hook", "the noise"] and h4["signal"].startswith("over four weeks, the people with the push land at least 20% more goals")
    assert h3["if_holds"].startswith("The clips and landings are made in Camp") and h4["if_holds"].startswith("A decision makes the push a setting")
    assert all(len(i["text"]) <= hyp.TEXT_CHARS and len(i["signal"]) <= hyp.TEXT_CHARS and len(i["if_holds"]) <= hyp.DRAFT_CHARS for i in got["items"])
    assert all(i["evidence"] == [] and i["verdict"] == {} for i in got["items"])


def test_the_own_file_applied_with_what_was_read_is_returned_byte_for_byte():
    text = OWN.read_text("utf-8")
    new, renames = hf.apply(text, hf.parse(text)["items"])
    assert new == text and renames == {}


SMALL = """# Hypotheses

Some words before.

## H1. People want a sketch first

**Status:** open; ready to test. **Raised:** the owner.

### The belief

Prose that is never read.

### What would prove it, what would refute it

- **Holds** when most ask for one
  within a minute
- **Refuted, the hook**: they look and do not pick
- Some other bullet.

### How we test it

An interview.

### If it holds

Sketch first, always.

## Notes

Not a hypothesis.

## H2. A section with no condition

**Status:** open.

Nothing to hold.
"""


ONE = SMALL[:SMALL.index("## H2.")]                                                  # SMALL without the section that has no condition (its number would be taken)


def test_a_section_with_no_holds_when_is_skipped_and_what_is_not_ours_is_kept():
    got = hf.parse(SMALL)
    assert [i["id"] for i in got["items"]] == ["h1"] and got["skipped"] == [2]
    one = got["items"][0]
    assert one["signal"] == "most ask for one within a minute" and one["refuted"] == [{"name": "the hook", "when": "they look and do not pick", "change": ""}] and one["if_holds"] == "Sketch first, always."
    new, _ = hf.apply(SMALL, got["items"])
    assert new == SMALL                                              # the Notes and the skipped section stay as written


# -- written: only the lines a change touches -----------------------------------------------------------------------------------------------

def test_a_changed_state_signal_way_draft_and_evidence_each_change_only_their_own_lines():
    item = hf.parse(SMALL)["items"][0]
    status = lambda it: changed(SMALL, hf.apply(SMALL, [it])[0])                                   # noqa: E731
    assert status({**item, "text": "Founders want a sketch first"}) == ["-## H1. People want a sketch first", "+## H1. Founders want a sketch first"]
    got = status({**item, "state": "held", "verdict": {"state": "held", "why": "", "decision": 12, "way": "", "at": "2026-11-04T10:00:00"}})
    assert got[:2] == ["-**Status:** open; ready to test. **Raised:** the owner.", "+**Status:** held; became decision §12. **Raised:** the owner."]
    assert got[2:] == []                                                                                    # the decision's number is in the status; a verdict line comes with a why or a way
    assert status({**item, "signal": "most pick one"}) == ["-- **Holds** when most ask for one", "-  within a minute", "+- **Holds** when most pick one"]
    assert status({**item, "refuted": [{"name": "the hook", "when": "they skip it", "change": ""}, {"name": "the noise", "when": "it is off", "change": ""}]}) == [
        "-- **Refuted, the hook**: they look and do not pick", "+- **Refuted, the hook**: they skip it", "+- **Refuted, the noise**: it is off"]
    assert status({**item, "refuted": []}) == ["-- **Refuted, the hook**: they look and do not pick"]
    assert status({**item, "if_holds": "Sketch first, for every goal."}) == ["-Sketch first, always.", "+Sketch first, for every goal."]
    drafted = hf.apply(SMALL, [{**item, "refuted": [{**item["refuted"][0], "change": "Drop the sketch."}]}])[0]
    assert "### If it is refuted, the hook\n\nDrop the sketch." in drafted and hf.parse(drafted)["items"][0]["refuted"][0]["change"] == "Drop the sketch."
    ev = hf.apply(SMALL, [{**item, "evidence": [{"text": "Four of five asked", "ref": "interview", "at": "2026-11-03T09:00:00"}]}])[0]
    assert "### Evidence\n\n- Four of five asked (interview) — 2026-11-03" in ev and hf.parse(ev)["items"][0]["evidence"] == [{"text": "Four of five asked", "ref": "interview", "at": "2026-11-03"}]


def test_a_verdict_is_written_as_the_status_and_a_verdict_line_and_read_back():
    item = hf.parse(SMALL)["items"][0]
    done = {**item, "state": "refuted", "verdict": {"state": "refuted", "why": "Only opens rose", "decision": 7, "way": "the hook", "at": "2026-11-04T10:00:00"}}
    text, _ = hf.apply(SMALL, [done])
    assert "**Status:** refuted; Only opens rose. **Raised:** the owner." in text and "### Verdict\n\nrefuted: Only opens rose (decision §7, the hook) — 2026-11-04" in text
    back = hf.parse(text)["items"][0]
    assert back["state"] == "refuted" and back["verdict"] == {"state": "refuted", "why": "Only opens rose", "decision": 7, "way": "the hook", "at": "2026-11-04"}
    assert hf.apply(text, [back])[0] == text


def test_an_item_with_no_section_is_appended_as_the_next_number_and_a_dropped_one_is_removed():
    item = hf.parse(SMALL)["items"][0]
    new = {"id": "founders-pay", "text": "Founders pay", "signal": "ten say so", "state": "open", "refuted": [{"name": "the price", "when": "none would", "change": ""}], "if_holds": "Charge for it.",
           "evidence": [], "verdict": {}}
    text, renames = hf.apply(SMALL, [item, new])
    assert renames == {"founders-pay": "h3"} and "## H3. Founders pay\n\n**Status:** open. **Raised:** " in text and "- **Holds** when ten say so\n- **Refuted, the price**: none would" in text
    got = hf.parse(text)["items"]
    assert [i["id"] for i in got] == ["h1", "h3"] and got[1]["if_holds"] == "Charge for it."
    assert hf.apply(text, [item], drop=("h3",))[0].count("## H3.") == 0 and "## Notes" in hf.apply(text, [item], drop=("h3",))[0]
    fresh, renames = hf.apply("", [new])
    assert fresh.startswith("# Hypotheses") and renames == {"founders-pay": "h1"} and hf.parse(fresh)["items"][0]["signal"] == "ten say so"
    assert hf.apply(SMALL, [item, {**new, "state": "proposed"}])[0] == SMALL                          # a proposed one is never in the file


# -- through the record ---------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def proj(tmp_path: Path):
    """`<proj>/docs/hypotheses.md` and the state folder `<proj>/.orkcraft` (no Board tree: the file is read and written in the working copy)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / ".orkcraft").mkdir()
    (tmp_path / "docs" / "hypotheses.md").write_text(ONE, "utf-8")
    return tmp_path


def kept(proj: Path) -> list[dict]:
    return hyp.read(proj / ".orkcraft")["items"]


def test_with_no_file_bound_the_record_is_as_it_was(proj):
    state = proj / ".orkcraft"
    item = hyp.add(state, "Alone", "it shows")
    assert item["id"] == "alone" and (proj / "docs" / "hypotheses.md").read_text("utf-8") == ONE and [i["id"] for i in kept(proj)] == ["alone"]


def test_a_bound_file_is_the_source_overlaid_with_the_goals_the_record_keeps(proj):
    state = proj / ".orkcraft"
    assert hyp.bind(state, "docs/hypotheses.md") == 0
    (got,) = kept(proj)
    assert (got["id"], got["text"], got["state"], got["by"], got["rests"]) == ("h1", "People want a sketch first", "open", "person", [])
    hyp.attach(state, "h1", goal="dark-mode", test="interview")
    assert kept(proj)[0]["rests"] == ["dark-mode"] and kept(proj)[0]["tests"] == ["interview"] and (proj / "docs" / "hypotheses.md").read_text("utf-8") == ONE
    assert json.loads((state / "hypotheses.json").read_text())["file"] == "docs/hypotheses.md"
    prop = hyp.add(state, "A leader's idea", "it shows", by="leader", party="product")                           # proposed: the record's only
    assert [i["id"] for i in kept(proj)] == ["h1", prop["id"]] and (proj / "docs" / "hypotheses.md").read_text("utf-8") == ONE
    kept_up = hyp.keep(state, prop["id"])
    assert kept_up["id"] == "h2" and kept_up["state"] == "open" and "## H2. A leader's idea" in (proj / "docs" / "hypotheses.md").read_text("utf-8")


def test_a_change_made_through_the_record_is_in_the_file_and_read_back(proj):
    state = proj / ".orkcraft"
    hyp.bind(state, "docs/hypotheses.md")
    added = hyp.add(state, "Founders pay", "ten say so", refuted=[{"name": "the price", "when": "none would"}], if_holds="Charge for it.")
    assert added["id"] == "h2"
    hyp.edit(state, "h1", signal="most pick one", if_holds="Sketch first, for all.")
    hyp.evidence(state, "h1", "Four of five asked", "interview")
    got = hyp.judge(state, "h1", "refuted", "Only opens rose", 9, way="the hook")
    assert got["state"] == "refuted"
    text = (proj / "docs" / "hypotheses.md").read_text("utf-8")
    assert "- **Holds** when most pick one" in text and "Sketch first, for all." in text and "- Four of five asked (interview)" in text and "**Status:** refuted; Only opens rose." in text
    back = {i["id"]: i for i in kept(proj)}
    assert back["h1"]["state"] == "refuted" and back["h1"]["verdict"]["way"] == "the hook" and back["h1"]["verdict"]["decision"] == 9 and back["h2"]["refuted"][0]["name"] == "the price"
    assert "Some other bullet." in text and "## Notes" in text                                                   # what is not ours is as it was
    hyp.drop(state, "h2")
    assert "## H2." not in (proj / "docs" / "hypotheses.md").read_text("utf-8") and [i["id"] for i in kept(proj)] == ["h1"]


def test_eight_open_are_the_newest_seven_open_and_the_eldest_waiting_and_judging_one_opens_it(proj):
    text = "# Hypotheses\n\n" + "\n".join(f"## H{n}. Claim {n}\n\n**Status:** open.\n\n### What would prove it, what would refute it\n\n- **Holds** when it shows {n}\n" for n in range(1, 9))
    (proj / "docs" / "hypotheses.md").write_text(text)
    state = proj / ".orkcraft"
    hyp.bind(state, "docs/hypotheses.md")
    states = {i["id"]: i["state"] for i in kept(proj)}
    assert states["h1"] == "waiting" and [s for k, s in states.items() if k != "h1"] == ["open"] * 7
    assert hyp.due(state, {}) == [] and hyp.state_of(kept(proj)[0], {}) == "waiting"
    for call in (lambda: hyp.judge(state, "h1", "held"), lambda: hyp.attach(state, "h1", test="t"), lambda: hyp.keep(state, "h1")):
        with pytest.raises(ValueError, match="waits"):
            call()
    with pytest.raises(ValueError, match="7 hypotheses are open"):
        hyp.add(state, "One more", "x")
    hyp.judge(state, "h8", "held")
    assert {i["id"]: i["state"] for i in kept(proj)}["h1"] == "open"
    assert json.loads((state / "hypotheses.json").read_text())["items"][0]["state"] in ("open", "held", "refuted")        # `waiting` is never kept
    assert (proj / "docs" / "hypotheses.md").read_text("utf-8").count("## H") == 8                                   # never dropped


def test_a_failed_write_changes_neither_the_file_nor_the_record(proj, monkeypatch):
    state = proj / ".orkcraft"
    hyp.bind(state, "docs/hypotheses.md")
    before = (state / "hypotheses.json").read_text()

    def boom(rel, edit, message):
        raise RuntimeError("the Board is held")
    hyp.set_writer(state, boom)
    with pytest.raises(ValueError, match="could not be written: the Board is held"):
        hyp.add(state, "Never kept", "x")
    with pytest.raises(ValueError, match="could not be written"):
        hyp.judge(state, "h1", "held")
    assert (state / "hypotheses.json").read_text() == before and (proj / "docs" / "hypotheses.md").read_text("utf-8") == ONE and [i["id"] for i in kept(proj)] == ["h1"]
    hyp.set_writer(state, None)


def test_the_writer_gets_the_files_path_the_edit_and_a_message_naming_the_hypothesis(proj):
    state = proj / ".orkcraft"
    hyp.bind(state, "docs/hypotheses.md")
    seen = []

    def put(rel, edit, message):
        path = proj / rel
        path.write_text(edit(path.read_text("utf-8")), "utf-8")
        seen.append((rel, message() if callable(message) else message))
    hyp.set_writer(state, put)
    hyp.add(state, "Founders pay", "ten say so")
    hyp.judge(state, "h1", "held", "", 4)
    hyp.set_writer(state, None)
    assert seen == [("docs/hypotheses.md", "board: hypothesis h2 — added"), ("docs/hypotheses.md", "board: hypothesis h1 — judged held")]


def test_the_records_own_items_are_adopted_into_the_file_when_it_is_first_bound(proj):
    state = proj / ".orkcraft"
    mine = hyp.add(state, "Founders pay", "ten say so", refuted=[{"name": "the price", "when": "none would"}])
    hyp.attach(state, mine["id"], goal="pricing-page")
    same = hyp.add(state, "People want a sketch first", "x")                                                   # already a section: its goals come with it
    hyp.attach(state, same["id"], test="interview")
    prop = hyp.add(state, "Not kept yet", "x", by="leader", party="product")
    assert hyp.bind(state, "docs/hypotheses.md") == 1
    got = {i["id"]: i for i in kept(proj)}
    assert got["h2"]["text"] == "Founders pay" and got["h2"]["rests"] == ["pricing-page"] and got["h2"]["refuted"][0]["name"] == "the price"
    assert got["h1"]["tests"] == ["interview"] and got[prop["id"]]["state"] == "proposed" and set(got) == {"h1", "h2", prop["id"]}
    assert hyp.bind(state, "docs/hypotheses.md") == 0 and (proj / "docs" / "hypotheses.md").read_text("utf-8").count("## H") == 3


def test_a_file_that_is_gone_reads_as_no_file_and_the_records_copy_is_read(proj):
    state = proj / ".orkcraft"
    hyp.bind(state, "docs/hypotheses.md")
    hyp.attach(state, "h1", goal="dark-mode")
    (proj / "docs" / "hypotheses.md").unlink()
    assert [i["id"] for i in kept(proj)] == ["h1"] and kept(proj)[0]["rests"] == ["dark-mode"]
