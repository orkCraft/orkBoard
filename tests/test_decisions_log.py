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
    assert dl.path(tmp_path) == tmp_path / "docs/decisions.md"
    assert dl.path(tmp_path, "  ") == tmp_path / "docs/decisions.md"
    assert dl.path(tmp_path, "notes/log.md") == tmp_path / "notes/log.md"
    for bad in ("../x.md", "a/../../x.md", str(tmp_path.parent / "x.md"), "/etc/passwd", "."):
        assert dl.path(tmp_path, bad) == tmp_path / dl.DEFAULT
    inside = tmp_path / "docs" / "d.md"
    assert dl.path(tmp_path, str(inside)) == tmp_path / "docs/d.md"


def test_path_refuses_a_link_out_of_the_root(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    (tmp_path / "out").mkdir()
    (root / "link").symlink_to(tmp_path / "out")
    assert dl.path(root, "link/x.md") == root / dl.DEFAULT


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


def test_found_is_at_most_five_and_empty_for_none(tmp_path):
    assert dl.found(tmp_path) == []
    for i in range(8):
        _put(tmp_path, f"p{i}/decisions.md")
    got = dl.found(tmp_path)
    assert len(got) == 5 and got[0] == "p0/decisions.md"


def test_next_number():
    assert dl.next_number("") == 1
    assert dl.next_number("# Title\n\ntext\n") == 1
    assert dl.next_number("## 7. One\n") == 8
    assert dl.next_number(SLICE) == 155
    assert dl.next_number("## 3. a\n## Notes\n") == 4
    assert dl.next_number("## 3. a\n```\n## 12. in code\n```\n") == 4
    assert dl.next_number("  ## 12. indented\n") == 1


def test_entry_found_missing_last_and_cut():
    e = dl.entry(SLICE, 45)
    assert e.startswith("## 45. v1 is three buildings") and "Review gate" in e and "## 46" not in e
    e46 = dl.entry(SLICE, 46)
    assert "## 99. not a heading" in e46 and "### A sub-heading" in e46 and "Body 154" not in e46
    assert dl.entry(SLICE, 154).endswith("Body 154.")
    assert dl.entry(SLICE, 4) == "" and dl.entry(SLICE, 15) == "" and dl.entry("", 1) == ""
    long = "## 1. Big\n" + "x" * 9000 + "\n## 2. Next\n"
    cut = dl.entry(long, 1)
    assert cut.endswith("… (cut: read the file for the rest)") and len(cut) < dl.ENTRY_MAX + 60
    assert not dl.entry(long, 2).endswith("rest)")


def test_headings_ten_of_many_and_fewer():
    text = "".join(f"## {i}. Title {i}\n\nbody\n\n" for i in range(1, 31))
    assert dl.headings(text) == [f"{i}. Title {i}" for i in range(21, 31)]
    assert dl.headings(text, 3) == ["28. Title 28", "29. Title 29", "30. Title 30"]
    assert dl.headings("## 1. a\n## Notes\n") == ["1. a"]
    assert dl.headings("") == []
    assert dl.headings(SLICE)[-1].startswith("154. Product's party")
    assert "99." not in "".join(dl.headings(SLICE))
    assert dl.headings("## 5. " + "w" * 500) == ["5. " + "w" * 160]


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


def test_a_large_file_is_read_from_its_end(tmp_path):
    tail = "".join(f"## {i}. Title {i}\n\nbody {i}\n\n" for i in range(2, 14))
    _put(tmp_path, "docs/decisions.md", "## 1. First\n\nfirst body\n\n" + "z" * dl.READ_MAX + "\n" + tail)
    c = dl.context(tmp_path, 13)
    assert "13. Title 13" in c and "4. Title 4" in c and "1. First" not in c
    assert c.endswith("body 13")
    # an entry that is not in the end is found by reading the file whole
    assert dl.context(tmp_path, 1).split("This goal's decision:\n")[1].startswith("## 1. First")
    assert dl.next_number(dl._read(tmp_path / "docs/decisions.md")[0]) == 14
