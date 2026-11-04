"""Spec 134 A (docs/specs/134-release-keeps-the-chronicle.md; decisions §238): the chronicle read by code: the versions (tags, the changelog, the weeks), the decisions by their dates, the goals through the
portal, the chapters, a goal as it was, the search. Real git in a temporary repository, no model."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import chronicle, chronicle_decisions, chronicle_find, chronicle_versions, idea_flag, ideas, living_specs, spec_sections
from tests.test_commit_goal import git, repo, state  # noqa: F401  (the fixture)


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    return tmp_path / "pages"


def tag(repo: Path, name: str, day: str, annotated: bool = True) -> None:
    env = {**os.environ, "GIT_COMMITTER_DATE": f"{day}T12:00:00", "GIT_AUTHOR_DATE": f"{day}T12:00:00"}
    args = ["tag", "-a", name, "-m", name] if annotated else ["tag", name]
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env)


def through(pages: Path, repo: Path, title: str, day: str, decision: int = 0, by: str = "gate", slug: str = "") -> str:
    """A goal that went through the portal on `day` (its flag), carrying decision `decision`."""
    slug = ideas.add_idea(pages, title, "general", state(repo))
    ideas._write_json(idea_flag.flag_path(state(repo), slug), {"at": f"{day}T10:00:00", "by": by, "commit": "abc"})
    if decision:
        spec_sections.save_record(state(repo), slug, {"decision": {"title": f"D{decision}", "number": decision}})
    return slug


LOG = """# Decisions

## 1. First (1 October 2026, the owner)

Why: one.

## 2. Second (10 October 2026, the owner)

Changes: 1.

Why: two says purple.

## 3. Third, no date

Changes: 1.2, 2.4; spec 99 §3.

Why: three.

## 4. Fourth (20 October 2026, the owner)

Changes: 4, 9.

Why: four.
"""


# -- versions -------------------------------------------------------------------------------------------------------------------------------

def test_tags_that_read_as_a_version_are_the_versions_dated_by_their_tag(repo):
    tag(repo, "v0.2", "2026-10-20")
    tag(repo, "v0.10", "2026-10-25", annotated=False)
    tag(repo, "v0.1", "2026-10-10")
    tag(repo, "nightly", "2026-10-26")
    tag(repo, "release-x", "2026-10-26")
    got = chronicle_versions.read(repo)
    assert got["kind"] == "tag" and [(v["name"], v["id"]) for v in got["versions"]] == [("v0.1", "v:v0.1"), ("v0.2", "v:v0.2"), ("v0.10", "v:v0.10")]
    assert got["versions"][0]["day"] == "2026-10-10" and got["versions"][1]["day"] == "2026-10-20"


def test_with_no_tag_the_changelogs_headings_with_a_version_and_a_day_are_the_versions(repo):
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n## [1.1.0] - 2026-10-20\n- x\n\n## v1.0.0 (17 October 2026)\n\n## 0.9.0\n\n## [0.8.0] - not a day\n")
    got = chronicle_versions.read(repo)
    assert got["kind"] == "changelog" and [(v["name"], v["day"]) for v in got["versions"]] == [("1.0.0", "2026-10-17"), ("1.1.0", "2026-10-20")]
    tag(repo, "v2.0", "2026-10-30")
    assert chronicle_versions.read(repo)["kind"] == "tag"                                      # the tags first


def test_with_neither_the_weeks_and_a_folder_that_is_no_git_has_no_version(tmp_path, repo):
    assert chronicle_versions.read(repo) == {"kind": "week", "versions": []}
    assert chronicle_versions.read(tmp_path / "nowhere") == {"kind": "week", "versions": []}
    assert chronicle_versions.week_of("2026-11-04") == "2026-11-02" and chronicle_versions.week_of("2026-11-02") == "2026-11-02"
    assert chronicle_versions.week_of("nonsense") == ""


# -- decisions ------------------------------------------------------------------------------------------------------------------------------

def test_decisions_by_number_with_their_days_what_they_change_and_what_changed_them():
    rows = chronicle_decisions.read(LOG)
    assert [(r["number"], r["day"]) for r in rows] == [(1, "2026-10-01"), (2, "2026-10-10"), (3, "2026-10-10"), (4, "2026-10-20")]      # no date: the one before's
    assert rows[1]["changes"] == [{"n": 1, "point": 0, "title": "First"}]
    assert rows[2]["changes"] == [{"n": 1, "point": 2, "title": "First"}, {"n": 2, "point": 4, "title": "Second"}]          # `spec 99 §3` is no decision
    assert rows[3]["changes"] == []                                                                                         # its own number and a later one are dropped
    assert rows[0]["changed_by"] == [{"number": 2, "title": "Second", "day": "2026-10-10", "points": []},
                                     {"number": 3, "title": "Third, no date", "day": "2026-10-10", "points": [2]}]
    assert rows[1]["changed_by"][0]["points"] == [4] and "text" not in rows[0]
    assert "says purple" in chronicle_decisions.read(LOG, text=True)[1]["text"]
    assert chronicle_decisions.read("") == []


def test_a_folder_of_records_reads_as_a_log(tmp_path):
    folder = tmp_path / "adr"
    folder.mkdir()
    (folder / "0001-one.md").write_text("---\nstatus: accepted\ndate: 2026-10-01\n---\n# One\n\n## Decision Outcome\n\nA.\n")
    (folder / "0002-two.md").write_text("---\nstatus: accepted\ndate: 2026-10-05\nork-changes: [1]\n---\n# Two\n\n## Decision Outcome\n\nB.\n")
    rows = chronicle_decisions.read(folder)
    assert [(r["number"], r["day"]) for r in rows] == [(1, "2026-10-01"), (2, "2026-10-05")]
    assert rows[1]["changes"] == [{"n": 1, "point": 0, "title": "One"}] and rows[0]["changed_by"][0]["number"] == 2


# -- the goals and the chapters ------------------------------------------------------------------------------------------------------------

def test_the_goals_through_the_portal_and_no_other(repo, pages):
    one = through(pages, repo, "Dark mode", "2026-10-12", 2)
    done = through(pages, repo, "Done without a gate", "2026-10-13", by="done")
    ideas.add_idea(pages, "Only seen", "general", state(repo))
    ideas.save_state(state(repo), ideas.add_idea(pages, "Seen, done", "general", state(repo)), state="done", seen_at="2026-10-14T10:00:00")
    gone = through(pages, repo, "Dropped", "2026-10-14")
    (pages / ideas.IDEAS / f"{gone}.md").unlink()
    rel = through(pages, repo, "Release 1.0", "2026-10-15")
    from orkboard.realm import releases
    ideas._write_json(releases._path(state(repo), rel), {"version": "1.0", "goals": [], "out": "", "at": "2026-10-15T09:00:00"})
    got = chronicle.goals(state(repo), pages)
    assert [(g["idea"], g["day"], g["decision"]) for g in got] == [(one, "2026-10-12", 2), (done, "2026-10-13", 0)]
    assert got[0]["title"] == "Dark mode" and got[0]["commit"] == "abc" and got[0]["at"] == "2026-10-12T10:00:00"


def test_a_chapter_a_version_newest_first_a_days_items_go_with_the_version_of_that_day_and_the_rest_wait_unreleased(repo, pages):
    tag(repo, "v0.1", "2026-10-10")
    tag(repo, "v0.2", "2026-10-20")
    before = through(pages, repo, "Before all", "2026-09-01", 1)
    on_day = through(pages, repo, "On the day", "2026-10-10", 0)
    mid = through(pages, repo, "In the middle", "2026-10-15", 2)
    late = through(pages, repo, "After the last", "2026-10-25", 0)
    got = chronicle.read(state(repo), pages, repo, LOG)
    assert got["kind"] == "tag" and [c["name"] for c in got["chapters"]] == ["v0.2", "v0.1"]
    second, first = got["chapters"]
    assert [g["idea"] for g in first["goals"]] == [on_day, before] and [g["idea"] for g in second["goals"]] == [mid]
    assert [d["number"] for d in first["decisions"]] == [3]                        # 1 is carried by `before`, 2 by `mid`; 3 (10 Oct, no date of its own) is of no goal: v0.1's
    assert [d["number"] for d in second["decisions"]] == [4]                       # 4 (20 Oct) is of no goal: v0.2's
    assert [g["idea"] for g in got["unreleased"]["goals"]] == [late] and got["unreleased"]["decisions"] == []
    assert got["decisions"][1]["goal"] == before and got["decisions"][2]["goal"] == mid and got["decisions"][3]["goal"] == ""
    assert "text" not in got["decisions"][1]


def test_decisions_of_no_goal_are_rows_of_their_own_in_the_chapter_of_their_day(repo, pages):
    tag(repo, "v0.1", "2026-10-10")
    tag(repo, "v0.2", "2026-10-20")
    through(pages, repo, "Carries one", "2026-10-15", 1)
    got = chronicle.read(state(repo), pages, repo, LOG)
    second, first = got["chapters"]
    assert [d["number"] for d in first["decisions"]] == [3, 2] and [d["number"] for d in second["decisions"]] == [4]
    assert first["decisions"][0] == {"number": 3, "title": "Third, no date", "day": "2026-10-10", "changes": got["decisions"][3]["changes"], "changed_by": [], "goal": ""}


def test_with_no_version_the_chapters_are_the_weeks_that_have_something(repo, pages):
    a = through(pages, repo, "A", "2026-11-03")
    b = through(pages, repo, "B", "2026-11-04")
    c = through(pages, repo, "C", "2026-10-13")
    got = chronicle.read(state(repo), pages, repo, "## 7. Seven (5 November 2026, the owner)\n\nWhy.\n")
    assert got["kind"] == "week" and got["unreleased"] is None
    assert [(ch["id"], ch["name"], ch["day"]) for ch in got["chapters"]] == [("w:2026-11-02", "", "2026-11-02"), ("w:2026-10-12", "", "2026-10-12")]
    assert [g["idea"] for g in got["chapters"][0]["goals"]] == [b, a] and [g["idea"] for g in got["chapters"][1]["goals"]] == [c]
    assert [d["number"] for d in got["chapters"][0]["decisions"]] == [7]


def test_earlier_is_the_last_version_or_the_last_week_or_none(repo, pages):
    assert chronicle.earlier(state(repo), pages, repo) is None
    through(pages, repo, "A", "2026-11-04")
    assert chronicle.earlier(state(repo), pages, repo) == {"kind": "week", "name": "", "day": "2026-11-02"}
    tag(repo, "v0.1", "2026-10-10")
    tag(repo, "v0.2", "2026-10-20")
    assert chronicle.earlier(state(repo), pages, repo) == {"kind": "tag", "name": "v0.2", "day": "2026-10-20"}


# -- a goal as it was, a decision -----------------------------------------------------------------------------------------------------------

def test_a_goal_as_it_was_its_spec_its_decision_what_changed_what_it_rests_on_and_its_living_specs(repo, pages):
    slug = through(pages, repo, "Dark mode", "2026-10-12", 3)
    page = ideas.idea_page(pages, slug)
    page.sections = [("Asked", "a dark mode"), ("Gist", "dark"), ("General", "### Why\n\nBecause night.\n\n### Done when\n\n- it is dark\n")]
    ideas._write(pages / ideas.IDEAS / f"{slug}.md", page.text())
    living_specs.apply(pages, "theme", {"added": [{"name": "Dark", "text": "The product SHALL be dark.", "scenarios": []}]}, slug, "general", title="Theme")
    got = chronicle.goal(state(repo), pages, repo, LOG, slug)
    assert got["idea"] == slug and got["title"] == "Dark mode" and got["day"] == "2026-10-12" and got["commit"] == "abc"
    assert got["decision"]["number"] == 3 and "three" in got["decision"]["entry"] and got["decision"]["changes"][0]["n"] == 1
    assert [(c["number"], c["points"]) for c in got["changed_by"]] == []                    # 3's own changes are earlier: nothing later changed 3, 1 or 2
    assert [s["title"] for s in got["spec"]["sections"]] and got["spec"]["gist"].strip() == "dark" and got["spec"]["asked"].strip() == "a dark mode"
    assert got["how_now"] == [{"capability": "theme", "title": "Theme"}]
    early = through(pages, repo, "Early", "2026-10-02", 1)
    got = chronicle.goal(state(repo), pages, repo, LOG, early)
    assert [(c["number"], c["points"]) for c in got["changed_by"]] == [(2, []), (3, [2])]   # later decisions that name decision 1
    assert got["how_now"] == []


def test_a_goal_not_in_the_chronicle_is_refused_and_a_decision_is_read(repo, pages):
    seen = ideas.add_idea(pages, "Only seen", "general", state(repo))
    with pytest.raises(ValueError, match="not in the chronicle"):
        chronicle.goal(state(repo), pages, repo, LOG, seen)
    with pytest.raises(ValueError):
        chronicle.goal(state(repo), pages, repo, LOG, "nope")
    carrier = through(pages, repo, "Carrier", "2026-10-12", 2)
    got = chronicle.decision(state(repo), pages, LOG, 2)
    assert got["number"] == 2 and got["goal"] == carrier and "purple" in got["entry"] and got["changed_by"][0]["number"] == 3
    assert chronicle.decision(state(repo), pages, LOG, 99) is None and chronicle.decision(state(repo), pages, LOG, 3)["goal"] == ""


# -- the search -----------------------------------------------------------------------------------------------------------------------------

def test_the_search_finds_by_every_word_in_goals_sections_and_decisions_by_chapter(repo, pages):
    tag(repo, "v0.1", "2026-10-10")
    tag(repo, "v0.2", "2026-10-20")
    first = through(pages, repo, "Purple buttons", "2026-10-05", 0)
    second = through(pages, repo, "Faster pages", "2026-10-15", 2)
    third = through(pages, repo, "Unrelated", "2026-10-16", 0)
    page = ideas.idea_page(pages, third)
    page.sections = [("General", "### Why\n\nThe violet theme.\n\n### Done when\n\n- done\n")]
    ideas._write(pages / ideas.IDEAS / f"{third}.md", page.text())
    got = chronicle_find.find(state(repo), pages, repo, LOG, "purple")
    assert got["query"] == "purple" and [c["name"] for c in got["chapters"]] == ["v0.2", "v0.1"]
    assert got["chapters"][0]["goals"] == [{"idea": second, "title": "Faster pages", "in": ["decision"]}]                      # decision 2 says purple
    assert [(g["idea"], g["in"][0]) for g in got["chapters"][1]["goals"]] == [(first, "title")] and got["found"] == 2 and got["more"] == 0
    only = chronicle_find.find(state(repo), pages, repo, LOG, "violet THEME")
    assert [c["name"] for c in only["chapters"]] == ["v0.2"] and only["chapters"][0]["goals"][0]["idea"] == third and only["chapters"][0]["goals"][0]["in"] == ["spec"]
    assert chronicle_find.find(state(repo), pages, repo, LOG, "purple violet")["chapters"] == []                              # every word
    no_goal = chronicle_find.find(state(repo), pages, repo, LOG, "four")
    assert [(c["name"], [d["number"] for d in c["decisions"]]) for c in no_goal["chapters"]] == [("v0.2", [4])] and no_goal["chapters"][0]["decisions"][0]["in"] == ["decision"]


def test_an_empty_query_finds_nothing_and_the_finds_are_bounded(repo, pages, monkeypatch):
    for n in range(5):
        through(pages, repo, f"Common title {n}", "2026-11-03")
    assert chronicle_find.find(state(repo), pages, repo, LOG, "  ") == {"query": "", "found": 0, "more": 0, "chapters": [], "unreleased": None}
    monkeypatch.setattr(chronicle_find, "FIND_MAX", 3)
    got = chronicle_find.find(state(repo), pages, repo, LOG, "common")
    assert got["found"] == 3 and got["more"] == 2 and len(got["chapters"][0]["goals"]) == 3
    assert chronicle_find.words("a b c d e f g h") == list("abcdef") and len(chronicle_find.words("x" * 200)) == 1
    assert len(chronicle_find.words("x" * 200)[0]) == chronicle_find.QUERY_MAX


def test_unreleased_finds_are_kept_apart(repo, pages):
    tag(repo, "v0.1", "2026-10-10")
    late = through(pages, repo, "Late purple", "2026-10-25")
    got = chronicle_find.find(state(repo), pages, repo, LOG, "late")
    assert got["chapters"] == [] and [g["idea"] for g in got["unreleased"]["goals"]] == [late]
