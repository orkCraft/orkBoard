"""Spec 127 B (docs/specs/127-the-fields-best-in-our-formats.md): what a decision changes (the Orkmaster's `changes`, cleaned to the headings' numbers; the body's first line
`Changes: 7.` in the one file, `ork-changes` in a MADR folder, the line at the top of a Nygard record's Decision; `decisions_log.headings` and `context` saying *changed by*; the
project's journal's line) and a new project's decisions as the MADR folder `docs/decisions`. The model call is stubbed as the decision's tests stub it."""
from __future__ import annotations

from orkboard.realm import decisions_log as dl, doc_formats, journals, spec_sections
from tests.test_idea_decide import DECISION, MADR_FILE, NYGARD_FILE, _adr_folder, _decided, _state, git, host, model, parties  # noqa: F401  (the fixtures)

LOG = "# Decisions\n\n## 7. Seven (1 May 2026, the person and Orkboard)\n\nWhy: x.\n\n## 8. Eight (2 May 2026, the person and Orkboard)\n\nWhy: y.\n"


def _seed(host, text=LOG):
    """The project keeps `docs/decisions.md` with decisions 7 and 8 (committed to dev, the Board's tree following it)."""
    (host.repo_root / "docs" / "decisions.md").write_text(text, encoding="utf-8")
    git(host.repo_root, "add", "-A")
    git(host.repo_root, "commit", "-qm", "decisions")
    git(host.repo_root, "branch", "-f", "dev", "HEAD")
    host.ideas._board_tree.ensure()


def _confirm(host, slug, **args):
    host.ideas.keeper.sections = lambda s: None
    return host.ideas.keeper.confirm(slug, tree=host.ideas._decision_tree(), **args)


def _journal(host, number):
    return next(e["text"] for e in journals.read(host.ideas.state_dir, journals.PROJECT) if e["kind"] == "decision" and e["ref"] == str(number))


# -- the answer, strictly ------------------------------------------------------------------------------------------------------------------------





def test_a_decision_keeps_the_changes_the_orkmaster_named_and_a_number_it_was_not_given_is_dropped(host, parties, model):
    _seed(host)
    slug = _decided(host, parties, model, answer={**DECISION, "changes": [8, 99, 7]})
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["changes"] == [8, 7]


# -- written -------------------------------------------------------------------------------------------------------------------------------------

def test_in_the_one_file_the_entry_starts_with_the_changes_line_and_the_readers_say_changed_by(host, parties, model):
    _seed(host)
    slug = _decided(host, parties, model, answer={**DECISION, "changes": [7, 8]})
    got = _confirm(host, slug)
    assert got["number"] == 9 and got["path"] == "docs/decisions.md"
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    entry = dl.entry(log, 9)
    assert entry.split("\n")[0].startswith("## 9. Dark mode ships as a setting (") and entry.split("\n")[2:4] == ["Changes: 7, 8.", ""] and "\nWhy: People read at night" in entry
    (rec,) = [r for r in doc_formats.parse_log(log) if r["number"] == 9]
    assert rec["extra"]["changes"] == [7, 8] and rec["status"] == "accepted"                                                     # the reader of spec 127 A reads it
    heads = dl.headings(log)
    assert heads[0] == "7. Seven (1 May 2026, the person and Orkboard) (changed by 9)" and heads[1].endswith("Orkboard) (changed by 9)") and "changed by" not in heads[2]
    assert dl.numbers(log) == [7, 8, 9]
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["changes"] == [7, 8]
    assert _journal(host, 9) == "Decision 9: Dark mode ships as a setting (changes 7, 8)"






def test_in_a_madr_folder_the_changes_are_front_matter_and_in_a_nygard_folder_the_line_tops_the_decision(host, parties, model):
    _adr_folder(host, "docs/decisions", MADR_FILE)
    slug = _decided(host, parties, model, answer={**DECISION, "changes": [1, 2]})
    got = _confirm(host, slug)
    assert got["number"] == 3 and got["path"] == "docs/decisions/0003-dark-mode-ships-as-a-setting.md"
    text = git(host.repo_root, "show", f"dev:{got['path']}")
    assert "\nork-changes: [1, 2]\n" in text and "Changes:" not in text and "decision-makers: [the person]" in text
    rec = doc_formats.parse_record(text, "0003-x.md")
    assert dl.changes_of(rec) == [1, 2] and rec["extra"]["ork-changes"] == ["1", "2"]
    folder = host.repo_root / "docs" / "decisions"
    (folder / "0003-dark-mode-ships-as-a-setting.md").write_text(text, encoding="utf-8")
    assert dl.headings(folder) == ["1. Title 1 (changed by 3)", "2. Title 2 (changed by 3)", "3. Dark mode ships as a setting"]
    assert "1. Title 1 (changed by 3)" in dl.context(host.repo_root) and dl.numbers(folder) == [1, 2, 3]
    assert _journal(host, 3) == "Decision 3: Dark mode ships as a setting (changes 1, 2)"




def test_the_persons_correction_keeps_what_they_write_and_theirs_is_the_line(host, parties, model):
    _seed(host)
    slug = _decided(host, parties, model, answer={**DECISION, "changes": [7]})
    _confirm(host, slug, text="Why: mine.\n\n1. Only dark.")                                                        # no line of their own: the Orkmaster's changes are kept
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    assert dl.entry(log, 9).split("\n", 2)[2].startswith("Changes: 7.\n\nWhy: mine.\n\n1. Only dark.")
    other = _decided(host, parties, model, text="add a light mode option", answer={**DECISION, "title": "Light", "changes": [7]})
    got = _confirm(host, other, text="Changes: 8.\nWhy: mine.")                                                      # their own line wins and is written once
    log = git(host.repo_root, "show", "dev:docs/decisions.md")
    entry = dl.entry(log, got["number"])
    assert entry.count("Changes:") == 1 and "Changes: 8.\n\nWhy: mine." in entry
    assert spec_sections.record(host.ideas.state_dir, other)["decision"]["changes"] == [8]
    assert _journal(host, got["number"]).endswith("(changes 8)")




# -- a new project: MADR ------------------------------------------------------------------------------------------------------------------------

def test_a_project_with_no_log_at_all_gets_the_madr_folder_and_its_first_decision_is_the_first_record(host, parties, model):
    (host.ideas.state_dir / "project.json").unlink()                                                                # nothing chosen
    assert dl.path(host.repo_root) == host.repo_root / "docs" / "decisions" and dl.found(host.repo_root) == []
    slug = _decided(host, parties, model, answer={**DECISION, "changes": [1]})
    assert spec_sections.record(host.ideas.state_dir, slug)["decision"]["changes"] == []                            # nothing to change: no heading was given
    got = _confirm(host, slug)
    assert got["number"] == 1 and got["path"] == "docs/decisions/0001-dark-mode-ships-as-a-setting.md" and got["commit"]
    text = git(host.repo_root, "show", f"dev:{got['path']}")
    rec = doc_formats.parse_record(text, "0001-x.md")
    assert text.startswith("---\nstatus: accepted\n") and rec["format"] == "madr" and rec["number"] == 1 and rec["title"] == DECISION["title"]
    assert not (host.repo_root / "docs" / "decisions").exists() and "docs/decisions.md" not in git(host.repo_root, "ls-tree", "-r", "--name-only", "dev")
    second = host.ideas.keeper.write_decision("Another", "Why: too.", host.ideas._decision_tree(), changes=[1])
    assert second["number"] == 2 and second["path"] == "docs/decisions/0002-another.md"
    assert "ork-changes: [1]" in git(host.repo_root, "show", f"dev:{second['path']}")


def test_a_project_with_any_log_keeps_it(tmp_path):
    for rel in ("docs/decisions.md", "DECISIONS.md", "notes/decisions.md"):
        root = tmp_path / rel.replace("/", "_")
        (root / rel).parent.mkdir(parents=True)
        (root / rel).write_text(LOG, encoding="utf-8")
        assert dl.path(root) == (root / "docs" / "decisions.md") and dl.is_folder(root) is False
    root = tmp_path / "file"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "decisions").write_text("not a folder", encoding="utf-8")                                    # a file of that name is not made a folder of
    assert dl.path(root) == root / "docs" / "decisions.md" and dl.is_folder(root) is False
    assert dl.context(tmp_path / "nothing") == "" and dl.path(tmp_path / "nothing", "notes/log.md") == tmp_path / "nothing" / "notes" / "log.md"


