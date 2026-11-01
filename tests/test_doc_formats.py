"""Spec 126 A (docs/specs/126-read-in-and-write-out.md, decisions §204): the common formats of decisions, read and written by code: MADR 4, Nygard's ADRs
(adr-tools) and the Board's own one file."""
from __future__ import annotations

from orkboard.realm import doc_formats as F

MADR = """---
status: "superseded by ADR-0007"
date: 2024-05-02
decision-makers: [Ana, "Tech lead"]
consulted:
  - Design
tags: [storage]
---

# Use Postgres for the scores

## Context and Problem Statement

Scores are lost when the server restarts.

## Considered Options

* Postgres
* SQLite

## Decision Outcome

Chosen option: "Postgres", because we host it already.

### Consequences

* Good, because backups exist.
"""

NYGARD = """# 2. Record architecture decisions

Date: 2023-01-10

## Status

Accepted

## Context

We need to record the decisions.

## Decision

We will use ADRs.

## Consequences

See Nygard's article.
"""

LOG = """# Decisions

## 1. One TV, no accounts (3 October, the person and Orkboard)

Friends play at one TV.

```
## 9. not a heading
```

## 2. Rounds under five minutes (4 October, the leaders, all agreed; Orkboard)

1. Short rounds.
"""


def test_the_front_matter_is_read_flat_with_lists_both_ways():
    meta, rest = F.front_matter(MADR)
    assert meta["status"] == "superseded by ADR-0007" and meta["date"] == "2024-05-02"
    assert meta["decision-makers"] == ["Ana", "Tech lead"] and meta["consulted"] == ["Design"] and meta["tags"] == ["storage"]
    assert rest.lstrip().startswith("# Use Postgres")
    assert F.front_matter("# No meta\n") == ({}, "# No meta\n") and F.front_matter("---\nopen: 1\n")[0] == {}


def test_a_madr_record():
    r = F.parse_record(MADR, "0004-use-postgres.md")
    assert (r["format"], r["number"], r["title"], r["status"], r["date"]) == ("madr", 4, "Use Postgres for the scores", "superseded", "2024-05-02")
    assert r["deciders"] == ["Ana", "Tech lead"] and r["context"] == "Scores are lost when the server restarts."
    assert r["decision"] == 'Chosen option: "Postgres", because we host it already.'                     # its Consequences are their own part
    assert r["consequences"] == "* Good, because backups exist." and r["extra"] == {"consulted": ["Design"], "tags": ["storage"]}


def test_a_nygard_record_and_what_is_not_a_record():
    r = F.parse_record(NYGARD, "0002-record-architecture-decisions.md")
    assert (r["format"], r["number"], r["title"], r["status"], r["date"]) == ("nygard", 2, "Record architecture decisions", "accepted", "2023-01-10")
    assert r["decision"] == "We will use ADRs." and r["consequences"] == "See Nygard's article."
    assert F.parse_record("Just words, no title.\n", "README.md") is None
    assert F.parse_record("# Index\n\n* [one](0001-x.md)\n", "index.md") is None                     # a title but no record's shape


def test_the_boards_own_file_one_record_an_entry():
    got = F.parse_log(LOG, "docs/decisions.md")
    assert [(r["number"], r["title"], r["date"]) for r in got] == [(1, "One TV, no accounts", "3 October, the person and Orkboard"),
                                                                   (2, "Rounds under five minutes", "4 October, the leaders, all agreed; Orkboard")]
    assert "## 9. not a heading" in got[0]["body"] and got[1]["body"] == "1. Short rounds." and all(r["format"] == "log" for r in got)


def test_a_folder_its_format_its_next_number_and_a_new_files_name(tmp_path):
    assert F.folder_format(tmp_path) == "" and F.next_number(tmp_path) == 1
    (tmp_path / "0002-record.md").write_text(NYGARD)
    (tmp_path / "0004-use-postgres.md").write_text(MADR)
    (tmp_path / "0005-other.md").write_text(NYGARD.replace("2. Record", "5. Other"))
    (tmp_path / "README.md").write_text("# ADRs\n")
    assert [r["number"] for r in F.records(tmp_path)] == [2, 4, 5] and F.folder_format(tmp_path) == "nygard" and F.next_number(tmp_path) == 6
    assert F.file_name(12, "No accounts: in the first release!") == "0012-no-accounts-in-the-first-release.md" and F.file_name(1, "!!") == "0001-decision.md"


def test_written_out_and_read_back_the_record_is_the_same():
    rec = {"number": 7, "title": "No accounts", "status": "accepted", "date": "2026-11-01", "deciders": ["the person", "Product: Ada"],
           "context": "Friends at one TV.", "decision": "No accounts in the first release.", "consequences": "Good, because it starts at once.",
           "extra": {"ork-goal": "lobby", "ork-overruled": ["tech"]}}
    back = F.parse_record(F.render_madr(rec), "0007-no-accounts.md")
    assert {k: back[k] for k in ("number", "title", "status", "date", "deciders", "context")} == {k: rec[k] for k in ("number", "title", "status", "date", "deciders", "context")}
    assert back["decision"].startswith("No accounts in the first release.") and back["consequences"] == rec["consequences"] and back["extra"] == rec["extra"]
    ny = F.parse_record(F.render_nygard(rec), "0007-no-accounts.md")
    assert (ny["format"], ny["number"], ny["title"], ny["status"], ny["decision"]) == ("nygard", 7, "No accounts", "accepted", "No accounts in the first release.")
