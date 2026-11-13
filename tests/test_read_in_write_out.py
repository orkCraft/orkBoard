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


def _view_file(wiki, party, text, at, read="goal-a, §12"):
    (wiki / "journals").mkdir(parents=True, exist_ok=True)
    (wiki / "journals" / f"{party}.md").write_text(
        f"---\norkboard-journal: {party}\nparty: {party}\ndigest: \"{text}\"\ndigest_at: {at}\ndigest_read: {read}\n---\n\n# {party}'s journal\n")


def test_a_newer_view_in_the_tree_is_kept_and_not_written_over(tmp_path):
    sd, wiki = tmp_path / ".orkcraft", tmp_path / "wiki"
    journals.add(sd, "tech", "stance", "On “Timer” you said go: small")
    upto = journals.save_digest(sd, "tech", "Works: old.", "", at="2026-11-01T10:00:00")["upto"]
    _view_file(wiki, "tech", "Works: new; goal-a.", "2026-11-08T09:00:00")
    got = read_in.take_outside(wiki, sd)
    assert got["views"] == 1
    d = journals.digest(sd, "tech")
    assert d["text"] == "Works: new; goal-a." and d["at"] == "2026-11-08T09:00:00" and d["read"] == ["goal-a", "§12"] and d["upto"] == upto
    assert "views" not in read_in.take_outside(wiki, sd)

