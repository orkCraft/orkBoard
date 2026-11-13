"""The decisions file read by code (realm/decisions_log.py, spec 97 §5): its path, next number, an entry, the headings."""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import decisions_log as dl

SLICE = """# Decisions §45–§50: Orkboard's ground

Copied on 18 October 2026 from Orkline.

## 45. v1 is three buildings in plain windows; Camp waits, its art goes on (17 October, the owner)

Why: the AgentCraft study shows a game image brings views but not a habit.

1. **v1 is three buildings:** the **Task board**, the **Agent pool** and the **Review gate**.
2. **The phone first: three tabs, Board · Agents · Review.**

## 46. Next one

```
## 99. not a heading
```

### A sub-heading stays in 46

## 154. Product's party is the knights, Release's the undead (28 October, the owner)

Body 154.
"""


def _put(root: Path, rel: str, text: str = "x") -> None:
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, "utf-8")


def test_path_default_chosen_and_never_outside(tmp_path):
    assert dl.path(tmp_path) == tmp_path / "docs/decisions"                       # a project with no log at all: the MADR folder (spec 127 B.4)
    assert dl.path(tmp_path, "  ") == tmp_path / "docs/decisions"
    _put(tmp_path, "docs/decisions.md")
    assert dl.path(tmp_path) == tmp_path / "docs/decisions.md" and dl.path(tmp_path, "  ") == tmp_path / "docs/decisions.md"
    (tmp_path / "docs/decisions.md").unlink()
    assert dl.path(tmp_path, "notes/log.md") == tmp_path / "notes/log.md"
    for bad in ("../x.md", "a/../../x.md", str(tmp_path.parent / "x.md"), "/etc/passwd", "."):
        assert dl.path(tmp_path, bad) == tmp_path / dl.DEFAULT
    inside = tmp_path / "docs" / "d.md"
    assert dl.path(tmp_path, str(inside)) == tmp_path / "docs/d.md"


def test_found_folders_files_depth_and_skips(tmp_path):
    _put(tmp_path, "docs/adr/0001.md")
    _put(tmp_path, "doc/adr/0001.md")
    _put(tmp_path, "DECISIONS.md")
    _put(tmp_path, "docs/decisions.md")
    _put(tmp_path, "a/b/c/decisions.md")           # three folders down: found
    _put(tmp_path, "a/b/c/d/decisions.md")         # four: not
    _put(tmp_path, "node_modules/p/decisions.md")  # skipped
    _put(tmp_path, ".git/decisions.md")
    _put(tmp_path, "docs/Decisions.md")
    assert dl.found(tmp_path) == ["DECISIONS.md", "docs/decisions.md", "doc/adr", "docs/adr", "a/b/c/decisions.md"]


def test_context_text_and_bound(tmp_path):
    assert dl.context(tmp_path) == ""
    _put(tmp_path, "docs/decisions.md", SLICE)
    c = dl.context(tmp_path)
    assert c.startswith("The project's decisions (docs/decisions.md): the last ten:\n45. v1 is three")
    assert "This goal's decision" not in c
    c = dl.context(tmp_path, 154)
    assert c.endswith("This goal's decision:\n## 154. Product's party is the knights, Release's the undead "
                      "(28 October, the owner)\n\nBody 154.")
    assert "This goal's decision" not in dl.context(tmp_path, 3)
    _put(tmp_path, "notes/log.md", "## 1. Mine\n")
    assert dl.context(tmp_path, chosen="notes/log.md") == "The project's decisions (notes/log.md): the last ten:\n1. Mine"
    assert dl.context(tmp_path, chosen="../x").startswith("The project's decisions (docs/decisions.md)")
    big = "".join(f"## {i}. {'t' * 400}\n" for i in range(1, 40)) + "## 40. Last\n" + "y" * 20000 + "\n"
    _put(tmp_path, "docs/decisions.md", big)
    assert len(dl.context(tmp_path, 40)) <= dl.ENTRY_MAX + 2000


# -- a project's own folder of ADR files (spec 126 D) ---------------------------------------------------------------------------------------------

MADR = "---\nstatus: accepted\ndate: 2026-03-02\n---\n\n# {title}\n\n## Context and Problem Statement\n\nWhy {n}.\n\n## Decision Outcome\n\nChosen {n}.\n"


def _adrs(root: Path, rel: str, n: int = 3) -> None:
    for i in range(1, n + 1):
        _put(root, f"{rel}/{i:04d}-title-{i}.md", MADR.format(title=f"Title {i}", n=i))


def test_the_place_is_a_folder_when_chosen_or_when_it_is_the_only_log_and_the_default_file_is_not_there(tmp_path):
    assert dl.is_folder(tmp_path) is True and dl.path(tmp_path) == tmp_path / "docs" / "decisions"                 # nothing kept: the new project's folder, not made yet
    assert dl.is_folder(tmp_path, "docs/decisions") is False                                                      # a choice of that name that is no folder is a file
    _adrs(tmp_path, "docs/decisions")
    assert dl.is_folder(tmp_path) is True and dl.path(tmp_path) == tmp_path / "docs" / "decisions"
    _put(tmp_path, "notes/adr.md", "x")
    assert dl.is_folder(tmp_path, "notes/adr.md") is False and dl.is_folder(tmp_path, "docs/decisions") is True      # the person's choice
    _put(tmp_path, "other/decisions.md")
    assert dl.is_folder(tmp_path) is False                                                                          # two logs: none is the only one
    _put(tmp_path, "docs/decisions.md")
    assert dl.is_folder(tmp_path) is False and dl.path(tmp_path) == tmp_path / "docs" / "decisions.md"             # the file the Board writes is there


def test_the_folders_records_give_the_next_number_the_headings_and_an_entry(tmp_path):
    _adrs(tmp_path, "docs/decisions", 12)
    folder = tmp_path / "docs" / "decisions"
    assert dl.next_number(folder) == 13 and dl.next_number(tmp_path / "none") == 1
    assert dl.headings(folder) == [f"{i}. Title {i}" for i in range(3, 13)] and dl.headings(folder, last=2) == ["11. Title 11", "12. Title 12"]
    assert dl.entry(folder, 12).startswith("## 12. Title 12\n\n## Context and Problem Statement") and "Chosen 12." in dl.entry(folder, 12) and dl.entry(folder, 99) == ""
    got = dl.context(tmp_path, 4)
    assert got.startswith("The project's decisions (docs/decisions): the last ten:\n3. Title 3\n") and "This goal's decision:\n## 4. Title 4" in got
    assert "This goal's decision" not in dl.context(tmp_path) and dl.context(tmp_path, 4, "docs/decisions") == got


