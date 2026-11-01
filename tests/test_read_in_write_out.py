"""Spec 126 B with C: what `orkboard export` writes, `orkboard import` reads back the same, into a project that has none of it; and a decision the Board
wrote into the project's ADR folder (spec 126 D) is never read in again as another."""
from __future__ import annotations

from orkboard.realm import doc_formats, journals, read_in, write_out


def test_the_journals_written_out_are_read_back_the_same(tmp_path):
    src, dst = tmp_path / "a", tmp_path / "b"
    for p in (src, dst):
        (p / ".orkcraft").mkdir(parents=True)
    sd = src / ".orkcraft"
    journals.add(sd, journals.PROJECT, "decision", "Decision 3: no accounts", ref="3", at="2026-10-03")
    journals.add(sd, "tech", "overruled", "The person went on with “Lobby” against your no: the cache", idea="lobby", on=["cache", "api"])
    journals.add(sd, "tech", "stance", "On “Timer” you said go: small")
    out = write_out.write(src, sd, dst / "docs" / "orkboard")
    assert out["journals"] >= 2
    read_in.take(dst, dst / ".orkcraft")
    back = {scope: [(e["kind"], e["text"], e["at"][:10], e["idea"], e["on"]) for e in journals.read(dst / ".orkcraft", scope)]
            for scope in (journals.PROJECT, "tech")}
    want = {scope: [(e["kind"], e["text"], e["at"][:10], e["idea"], e["on"]) for e in journals.read(sd, scope)] for scope in (journals.PROJECT, "tech")}
    assert back == want
    assert all("<!--" not in t for _k, t, *_ in back["tech"])
    read_in.take(dst, dst / ".orkcraft")                                                  # read in twice: nothing twice
    assert len(journals.read(dst / ".orkcraft", "tech")) == 2


def test_a_decision_the_board_wrote_into_the_adr_folder_is_not_read_in_again(tmp_path):
    (tmp_path / ".orkcraft").mkdir()
    folder = tmp_path / "docs" / "decisions"
    folder.mkdir(parents=True)
    rec = {"number": 1, "title": "No accounts", "status": "accepted", "date": "2026-11-01", "decision": "None.", "extra": {"ork-goal": "lobby"}}
    (folder / doc_formats.file_name(1, "No accounts")).write_text(doc_formats.render_madr(rec))
    (folder / doc_formats.file_name(2, "Postgres")).write_text(doc_formats.render_madr({**rec, "number": 2, "title": "Postgres", "extra": {}}))
    read_in.take(tmp_path, tmp_path / ".orkcraft")
    assert [e["text"].split(":")[0] for e in journals.read(tmp_path / ".orkcraft", journals.PROJECT)] == ["Decision 2"]


def test_a_decision_the_board_wrote_with_no_goal_is_known_by_its_number(tmp_path):
    sd = tmp_path / ".orkcraft"
    sd.mkdir()
    journals.add(sd, journals.PROJECT, "decision", "Decision 1: Postgres", ref="1")                     # as the Board's writer keeps it (spec 125 B)
    folder = tmp_path / "docs" / "decisions"
    folder.mkdir(parents=True)
    (folder / doc_formats.file_name(1, "Postgres")).write_text(doc_formats.render_madr({"number": 1, "title": "Postgres", "decision": "Use it."}))
    read_in.take(tmp_path, sd)
    assert len(journals.read(sd, journals.PROJECT)) == 1
