"""Spec 151 A (decisions §255.3): a goal's phase in its page. `realm/goal_phase.py` on its own, then the host on a real git repository: the keys written with the Board's commit, a phase moved
outside followed (the state moved, a run stopped, the line said, the event logged), a page laid outside, a question laid outside brought to the hand and its answer written under its line.
No model is ever called: the tools are fakes."""
from __future__ import annotations

import re
import json
import subprocess
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import board_ask, event_log, goal_phase, idea_page, idea_questions, ideas, spec_sections

IDEAS = "pages/ideas"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


# -- the table ----------------------------------------------------------------------------------------------------------------

def test_every_fine_state_has_a_phase_and_each_phase_starts_in_itself():
    assert goal_phase.PHASES == ("new", "talk", "spec", "work", "done")
    for state in ideas.STATES:
        assert goal_phase.of(state) in goal_phase.PHASES, state
    assert {s: goal_phase.of(s) for s in ideas.STATES} == goal_phase.STATE_PHASE and set(goal_phase.STATE_PHASE) == set(ideas.STATES)
    for phase in goal_phase.PHASES:
        assert goal_phase.of(goal_phase.first(phase)) == phase
    assert [goal_phase.first(p) for p in goal_phase.PHASES] == ["raw", "routed", "decided", "ready", "done"]
    assert goal_phase.of({"state": "sketch"}) == "spec" and goal_phase.of("nonsense") == "new" and goal_phase.first("nonsense") == "raw"


def test_board_asks_words_are_read_from_the_one_table_and_did_not_change():
    assert board_ask.PHASES == {"routed": "Talk", "talk": "Talk", "decided": "Spec", "sketch": "Spec", "sections": "Spec", "ready": "Work", "planning": "Work", "plan": "Work",
                                "working": "Work", "failed": "Work, failed", "done": "Done"}


def test_the_keys_say_only_what_there_is_to_say():
    st = {**ideas.STATE_DEFAULT, "state": "plan", "route": [{"party": "tech", "leader": "a"}, {"party": "design", "leader": "b"}], "queue": "night"}
    assert goal_phase.keys(st, "abc1234 · 3 files · green", True, "person") == {
        "phase": "work", "route": "tech, design", "queue": "night", "asks": "person", "gate": "abc1234 · 3 files · green", "by": "person", "schema": "3"}
    assert goal_phase.keys({**ideas.STATE_DEFAULT, "queue": "now"}) == {"phase": "new", "schema": "3"}


def test_the_gate_is_the_last_one_that_ran():
    ran = lambda green, **k: {"tests": {"green": green, "ran": True, **k}}
    assert goal_phase.gate_of(None) == "" and goal_phase.gate_of({"tasks": []}) == ""
    assert goal_phase.gate_of({"tasks": [{"tests": {"green": True, "ran": False}}, {"state": "waiting"}]}) == ""               # no gate ran
    plan = {"tasks": [{**ran(False), "commit": "1111111999", "diff": {"files": 2}, "finished": "2026-11-01T10:00:00"},
                      {**ran(True), "commit": "2222222999", "diff": {"files": 1}, "finished": "2026-11-01T11:00:00"}]}
    assert goal_phase.gate_of(plan) == "2222222 · 1 file · green"
    assert goal_phase.gate_of({"tasks": [{**ran(False), "commit": "abc1234", "diff": {"files": 4}}]}) == "abc1234 · 4 files · red"
    slow = {"tasks": [{"tests": {"green": False, "ran": True, "env": "The tests did not finish in 5 minutes: 3 files"}, "commit": "", "diff": {"files": 3}}]}
    assert goal_phase.gate_of(slow) == "— · 3 files · did not finish"


# -- a question in the page ------------------------------------------------------------------------------------------------------

def test_an_answers_line_goes_under_its_question_and_reads_back():
    line = idea_questions.answer_line("App Store  first\nplease", "2026-11-06")
    assert line == "  - Answered: App Store first please (the person, 2026-11-06)"
    text = "- Which store first? (**App Store** / Google Play) — iPhone\n- Which week?"
    got = idea_questions.with_answer(text, 0, "Google Play", "2026-11-06")
    assert got.splitlines() == ["- Which store first? (**App Store** / Google Play) — iPhone", "  - Answered: Google Play (the person, 2026-11-06)", "- Which week?"]
    assert idea_questions.answers(got) == ["Google Play", ""] and idea_questions.questions_of(got)[1] == "Which week?"
    assert idea_questions.answers(got.splitlines()) == ["Google Play", ""]                                                 # the lines too
    assert idea_questions.answers("- A (b) is (c)\n  - Answered: yes (it was (really)) (the person, 2026-01-02)") == ["yes (it was (really))"]
    again = idea_questions.with_answer(got, "Which week?", "next", "2026-11-07")
    assert idea_questions.answers(again) == ["Google Play", "next"]
    assert idea_questions.with_answer(again, 0, "App Store", "2026-11-08").count("Answered") == 2                            # an answer there is replaced
    assert idea_questions.questions_of(idea_questions.with_answer("", "A new one?", "yes", "2026-11-06")) == ["A new one?"]
    assert idea_questions.open_of(got) == [(1, "Which week?")]
    with pytest.raises(ValueError):
        idea_questions.with_answer(text, 5, "x", "2026-11-06")


def test_an_answered_question_is_no_longer_open_in_the_page():
    page = ideas.parse("---\nowner: board\n---\n# G\n\n## Open questions\n- One? (a / b)\n  - Answered: a (the person, 2026-11-06)\n- Two?\n")
    assert ideas.items(page.section("Open questions")) == ["Two?"]
    assert ideas.items("- x\n- y") == ["x", "y"] and ideas.items("plain\nlines") == ["plain", "lines"]


def test_a_page_that_asks_the_person_lays_its_unanswered_choices_as_cards():
    page = ideas.parse("---\nowner: board\nasks: person\nby: Claude Code\n---\n# G\n\n## Open questions\n"
                       "- Which store first? (**App Store** / Google Play) — iPhone\n  - Answered: App Store (the person, 2026-11-06)\n"
                       "- Which colour? (red / **blue** / green) — calm\n- Free text, no choices?\n- Which size? (S / M)\n")
    cards = goal_phase.outside_cards(page)
    assert [(c["id"], c["by"], c["q"], c["choices"], c["pick"]) for c in cards] == [
        ("page-1", "Claude Code", "Which colour?", ["red", "blue", "green"], 1), ("page-3", "Claude Code", "Which size?", ["S", "M"], 0)]
    (row,) = goal_phase.outside_rows(page)
    assert row["kind"] == "talk" and row["questions"] == cards and row["text"] == "Which colour?"
    page.set("asks", "")
    assert goal_phase.outside_cards(page) == [] and goal_phase.outside_rows(None) == []


# -- the host, on a real repository -----------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    (fake_repo / ".gitignore").write_text(".orkcraft/\n")
    git(fake_repo, "add", "-A")
    git(fake_repo, "commit", "-qm", "ignore")
    return Orkboard(fake_repo)


def _goal(host, text="a dark mode"):
    root = host.ideas.root()
    slug = ideas.add_idea(root, text, state_dir=host.ideas.state_dir, queue="hold")
    host.ideas.tree_note(slug, "added")
    return root, slug


def _page(root, slug):
    return ideas.idea_page(root, slug)


def test_a_flush_writes_the_keys_and_what_it_wrote(host):
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    ideas.save_state(sd, slug, state="plan", route=[{"party": "tech", "leader": "x"}])
    ideas.save_plan(sd, slug, {"tasks": [{"id": "t1", "state": "merged", "commit": "abcdef0123", "diff": {"files": 2}, "finished": "2026-11-01T10:00:00",
                                         "tests": {"green": True, "ran": True}}]})
    got = host.ideas.tree_flush(force=True)
    page = _page(root, slug)
    assert [(k, page.get(k)) for k in ("phase", "route", "queue", "asks", "gate", "by", "schema")] == [
        ("phase", "work"), ("route", "tech"), ("queue", "hold"), ("asks", "person"), ("gate", "abcdef0 · 2 files · green"), ("by", "person"), ("schema", "3")]    # the plan waits for the person
    assert ideas.state(sd, slug)["phase_written"] == "work"
    assert got["commit"] and "phase: work" in git(host.ideas.state_dir.parent, "show", f"dev:llm-wiki/general/{IDEAS}/{slug}.md")
    assert "owner" in dict(page.meta) and page.section("Gist") == "a dark mode"                # what the page had is kept
    host.ideas.tree_flush(force=True)                                                           # nothing changed: nothing written
    assert git(host.ideas.state_dir.parent, "rev-parse", "dev") == got["commit"]


def test_no_key_where_there_is_nothing_to_say(host):
    root, slug = _goal(host)
    ideas.save_state(host.ideas.state_dir, slug, state="done", queue="")
    host.ideas.tree_flush(force=True)
    page = _page(root, slug)
    assert page.get("phase") == "done" and not any(k in dict(page.meta) for k in ("route", "queue", "asks", "gate"))


def test_a_state_change_rides_in_the_next_commit(host):
    root, slug = _goal(host)
    host.ideas.tree_flush(force=True)
    assert _page(root, slug).get("phase") == "new"
    tree = host.ideas._board_tree
    assert tree._since is None
    ideas.save_state(host.ideas.state_dir, slug, state="decided")                              # no bus event: the observer alone asks for the write
    assert tree._since is not None
    tree._since -= 11                                                                           # ten seconds on
    got = host.ideas.tree_flush()
    assert got["commit"] and _page(root, slug).get("phase") == "spec"
    assert "phase: spec" in git(host.ideas.state_dir.parent, "show", f"dev:llm-wiki/general/{IDEAS}/{slug}.md")


def test_a_state_that_keeps_its_phase_asks_for_no_write(host):
    root, slug = _goal(host)
    host.ideas.tree_flush(force=True)
    ideas.save_state(host.ideas.state_dir, slug, state="reading")
    assert host.ideas._board_tree._since is None


def _commit_outside(host, slug, edit, who="Claude Code"):
    """What an AI tool does without Orkboard: edits the page on the work branch and commits as itself."""
    repo = Path(host.repo_root)
    work = repo.parent / "tool"
    if not work.exists():
        git(repo, "worktree", "add", "--detach", str(work), "dev")
    git(work, "checkout", "-q", "--detach", "dev")
    path = work / "llm-wiki/general" / IDEAS / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(edit(path.read_text() if path.exists() else ""), encoding="utf-8")
    git(work, "add", "-A")
    git(work, "-c", f"user.name={who}", "-c", "user.email=t@x", "commit", "-qm", "tool: moved a goal")
    git(repo, "update-ref", "refs/heads/dev", git(work, "rev-parse", "HEAD"))
    host.ideas._phase_at = 0.0                      # the clock looks every five seconds: it is time
    return git(work, "rev-parse", "--short", "HEAD")


def test_a_page_moved_outside_moves_the_state_says_it_and_logs_it(host):
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    ideas.save_state(sd, slug, state="talk")
    host.ideas.tree_flush(force=True)
    assert ideas.state(sd, slug)["phase_written"] == "talk"
    toasts = []
    host.ideas.host.toast = lambda msg, **k: toasts.append(msg)
    commit = _commit_outside(host, slug, lambda t: t.replace("phase: talk", "phase: work"))
    host.ideas.tree_flush()
    st = ideas.state(sd, slug)
    assert st["state"] == "ready" and st["phase_written"] == "work"
    (line,) = toasts
    assert line == f"{ideas.idea_page(host.ideas.root(), slug).title} was moved to work in Claude Code"
    (e,) = [r for r in event_log.read(Path(host.repo_root)) if r["event"] == "goal_moved_outside"]
    assert (e["slug"], e["from"], e["to"], e["commit"]) == (slug, "talk", "work", commit)
    host.ideas.tree_flush()
    assert len(toasts) == 1                                                                     # said once
    host.ideas.tree_flush(force=True)
    assert _page(host.ideas.root(), slug).get("phase") == "work" and _page(host.ideas.root(), slug).get("by") == "person"     # who laid it, not who moved it


def test_a_tools_by_is_kept_and_names_it_in_the_line(host):
    root, slug = _goal(host)
    host.ideas.tree_flush(force=True)
    toasts = []
    host.ideas.host.toast = lambda msg, **k: toasts.append(msg)
    _commit_outside(host, slug, lambda t: t.replace("phase: new", "phase: done\nby: Codex"))
    host.ideas.tree_flush()
    assert toasts[0].endswith("was moved to done in Codex") or "in Codex" in toasts[0]
    assert ideas.state(host.ideas.state_dir, slug)["state"] == "done"
    host.ideas.tree_flush(force=True)
    assert _page(host.ideas.root(), slug).get("by") == "Codex"                                  # what the page says is kept


def test_a_run_on_a_goal_moved_outside_is_stopped_as_stop_stops_it(host):
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    ideas.save_state(sd, slug, state="working")
    ideas.save_plan(sd, slug, {"tasks": [{"id": "t1", "state": "running", "title": "T"}]})
    host.ideas.tree_flush(force=True)
    stopped = []

    class FakeRunner:
        def running_tasks(self):
            return [(slug, "t1")]

        def stop(self, s, why="stopped by you"):
            stopped.append((s, why))
            ideas.save_state(sd, s, state="failed", error=why)

    host.ideas._runner = FakeRunner()
    _commit_outside(host, slug, lambda t: t.replace("phase: work", "phase: spec"))
    host.ideas.tree_flush()
    assert stopped == [(slug, "moved to spec from outside")]
    st = ideas.state(sd, slug)
    assert st["state"] == "decided" and st["error"] == ""                                       # it starts where the phase starts, not failed
    assert ideas.plan(sd, slug)["stopped"] is True                                              # nothing starts it by itself again


def test_a_page_laid_outside_gets_a_state_and_no_page_of_before_moves(host):
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    host.ideas.tree_flush(force=True)
    old = ideas.add_idea(host.ideas.root(), "an old one", state_dir=sd)
    ideas.save_state(sd, old, state="working")
    page = _page(root, old)
    assert page.get("phase") == ""                                                              # written before this spec: no phase
    _commit_outside(host, "laid-by-a-tool", lambda t: "---\nowner: board\nkind: idea\ntrack: general\norder: 9\nphase: spec\nby: Cursor\n---\n# Laid by a tool\n\n## Gist\nIdeas.\n")
    host.ideas.tree_flush()
    assert ideas.state(sd, "laid-by-a-tool")["state"] == "decided" and ideas.state(sd, "laid-by-a-tool")["phase_written"] == "spec"
    assert ideas.state(sd, old)["state"] == "working"                                           # left alone
    host.ideas.tree_flush(force=True)
    assert _page(host.ideas.root(), old).get("phase") == "work"                                 # …until the next flush gives it its phase
    assert ideas.state(sd, old)["state"] == "working"
    assert not [r for r in event_log.read(Path(host.repo_root)) if r["event"] == "goal_moved_outside" and r["slug"] == old]


def test_a_question_laid_outside_comes_to_the_hand_and_its_answer_goes_under_its_line(host):
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    ideas.save_state(sd, slug, state="decided")
    host.ideas.tree_flush(force=True)
    ideas.set_section(root, slug, "Open questions", "- Which store first? (**App Store** / Google Play) — iPhone\n- Which colour? (red / blue)")
    ideas.set_meta(root, slug, asks="person", by="Claude Code")
    host.ideas.tree_flush(force=True)
    board = host.ideas.board()
    (row,) = [n for n in board["needs_you"] if n["idea"] == slug]
    assert row["kind"] == "talk" and [c["id"] for c in row["questions"]] == ["page-0", "page-1"] and row["questions"][0]["by"] == "Claude Code"
    assert _page(root, slug).get("asks") == "person"                                            # a card waits: it stays
    with pytest.raises(Exception, match="Answer every question"):
        host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": "page-0", "pick": 1}]})
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": "page-0", "pick": 1}, {"id": "page-1", "text": "teal, I think"}]})
    text = _page(root, slug).section("Open questions")
    day = __import__("datetime").date.today().isoformat()
    assert text.splitlines() == ["- Which store first? (**App Store** / Google Play) — iPhone", f"  - Answered: Google Play (the person, {day})",
                                 "- Which colour? (red / blue)", f"  - Answered: teal, I think (the person, {day})"]
    assert idea_questions.answers(text) == ["Google Play", "teal, I think"]
    assert ideas.items(text) == []
    assert not [n for n in host.ideas.board()["needs_you"] if n["idea"] == slug]
    host.ideas.tree_flush(force=True)
    assert "asks" not in dict(_page(root, slug).meta)                                           # none left: cleared
    assert [r for r in event_log.read(Path(host.repo_root)) if r["event"] == "idea_answered"][-1]["answers"] == 2


def test_a_talks_card_answered_in_the_hand_is_written_to_the_page_beside_talks_record(host):
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    ideas.save_state(sd, slug, state="talk")
    card = idea_questions.card({"q": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "iPhone"}, id="c1", by="tech", leader="ork")
    idea_questions.save_record(sd, slug, {"mode": "talk", "round": 1, "waiting": [card], "stances": []})
    seen = []
    host.ideas.keeper.talk_answer = lambda s, answers, decide=False: seen.append((s, answers, decide))       # the keeper is a fake: no model
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": "c1", "pick": 1}]})
    assert seen == [(slug, [{"id": "c1", "pick": 1}], False)]
    text = _page(root, slug).section("Open questions")
    assert idea_questions.questions_of(text) == ["Which store first?"] and idea_questions.answers(text) == ["Google Play"]
    assert ideas.items(text) == []                                                              # answered: nothing open in the page


# -- the journals and the brief in the Board's commit (spec 151 B) ----------------------------------------------------------------------------

def test_the_journals_and_the_brief_ride_in_the_boards_commit_and_a_line_added_outside_is_taken_once(host):
    from orkboard.realm import journals
    _goal(host)
    sd, repo = host.ideas.state_dir, host.ideas.state_dir.parent
    journals.add(sd, journals.PROJECT, "decision", "Decision 1: no accounts", ref="1")
    host.ideas.tree_flush(force=True)
    assert not (host.ideas._board_tree.root() / "journals").exists()                       # no rules written: no journal goes to the work branch
    (host.ideas._board_tree.path / "AGENTS.md").write_text("<!-- orkboard:begin schema=1 hash=0 -->\n<!-- orkboard:end -->\n")
    host.ideas.tree_flush(force=True)
    shown = git(repo, "show", "dev:llm-wiki/general/journals/project.md")
    assert "orkboard-journal: _project" in shown and "Decision 1: no accounts" in shown
    assert "# Project brief" in git(repo, "show", "dev:llm-wiki/general/project.md")
    tip = git(repo, "rev-parse", "dev")
    host.ideas.tree_flush(force=True)
    assert git(repo, "rev-parse", "dev") == tip                                                # nothing changed: no new commit
    journals.add(sd, "tech", "stance", "Keep it small")
    host.ideas.tree_flush(force=True)
    assert "Keep it small" in git(repo, "show", "dev:llm-wiki/general/journals/tech.md")
    # a tool adds two lines to the file in the work branch; the host reads them in once
    tree = host.ideas._board_tree
    file = tree.root() / "journals" / "project.md"
    file.write_text(file.read_text() + "- 2026-11-05 · decision · Decision 2: from a tool <!-- id=feedfeed0001 -->\n- 2026-11-05 · bogus · Bad kind <!-- id=feedfeed0002 -->\n")
    git(tree.path, "add", "-A")
    git(tree.path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "a tool's line")
    tree.land()
    host.ideas.phase_sync(tree, True)
    texts = [e["text"] for e in journals.read(sd, journals.PROJECT)]
    assert texts == ["Decision 1: no accounts", "Decision 2: from a tool"] and [x["kind"] for x in host.ideas.journal_left] == ["bogus"]
    host.ideas.phase_sync(tree, True)
    host.ideas.tree_flush(force=True)
    assert [e["text"] for e in journals.read(sd, journals.PROJECT)] == texts                   # never again
    assert "Decision 2: from a tool" in git(repo, "show", "dev:llm-wiki/general/journals/project.md")


def test_the_schema_is_3_and_a_page_of_schema_1_or_2_is_read_as_it_is_and_written_3_when_the_board_writes_it(host):
    """Spec 152 F.5, spec 154 B.3: a v1 page has no marks on its Done when lines and is read the same; a v2 page has no Talk or Accepted and is read the same; the Board writes `schema: 3` when it next writes the page."""
    assert goal_phase.SCHEMA == "3" and goal_phase.keys({**ideas.STATE_DEFAULT})["schema"] == "3"
    root, slug = _goal(host)
    goal_phase.mirror(root, host.ideas.state_dir)
    page = ideas.idea_page(root, slug)
    assert page.get("schema") == "3"
    for older in ("1", "2"):
        page.set("schema", older)
        old = idea_page.parse(page.text())
        assert old.get("schema") == older and goal_phase.phase_of_page(old) == "new" and spec_sections.proof_of("a line of a v1 page") == ""
    goal_phase.mirror(root, host.ideas.state_dir)
    assert ideas.idea_page(root, slug).get("schema") == "3"


def test_a_page_of_schema_1_whose_phase_is_unchanged_is_not_written_only_to_move_its_schema(host):
    """Spec 155 G.1 (decisions §260.8): the Board writes a page when a key other than `schema` changes; the page it does write gets today's schema."""
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    assert goal_phase.mirror(root, sd) == [slug]
    page = ideas.idea_page(root, slug)
    page.set("schema", "1")
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    assert goal_phase.mirror(root, sd) == [] and ideas.idea_page(root, slug).get("schema") == "1"
    ideas.save_state(sd, slug, state="talk")
    assert goal_phase.mirror(root, sd) == [slug] and ideas.idea_page(root, slug).get("schema") == "3"


def test_a_done_page_new_to_this_machine_is_seen_in_history_and_makes_no_commit_note(host):
    """Spec 155 G.2: a goal done before this machine read it has `seen_at` at once, so it is not in the discard; another phase is moved as before."""
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    host.ideas.tree_flush(force=True)
    _commit_outside(host, "done-before", lambda t: "---\nowner: board\nkind: idea\ntrack: general\norder: 8\nphase: done\nby: Cursor\n---\n# Done before\n\n## Gist\nOld.\n")
    _commit_outside(host, "spec-before", lambda t: "---\nowner: board\nkind: idea\ntrack: general\norder: 9\nphase: spec\nby: Cursor\n---\n# Spec before\n\n## Gist\nNew.\n")
    tree = host.ideas._board_tree
    notes = []
    real = tree.note
    tree.note = lambda title, what, at: (notes.append((title, what)), real(title, what, at))[1]
    with tree.git.lock:
        tree.follow()
    host.ideas.phase_moved(tree)
    st = ideas.state(sd, "done-before")
    assert st["state"] == "done" and st["phase_written"] == "done" and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", st["seen_at"])
    assert notes == [("Spec before", "moved")]                                                  # the goal done before makes no note for a commit
    assert ideas.state(sd, "spec-before")["seen_at"] == ""


def test_a_question_with_lines_is_an_outside_card_with_them_and_a_talk_card_with_lines_is_written_to_the_page_whole(host):
    """Spec 159 B: the ways' lines travel to the page's outside cards, and a Talk card the page lacks is written with them."""
    root, slug = _goal(host)
    sd = host.ideas.state_dir
    ideas.save_state(sd, slug, state="decided")
    host.ideas.tree_flush(force=True)
    ideas.set_section(root, slug, "Open questions", "- Which store first? (**App Store** / Google Play) — iPhone · App Store: Ships in a week · Google Play: Ships in a month\n- Which colour? (red / blue)")
    ideas.set_meta(root, slug, asks="person", by="Claude Code")
    cards = goal_phase.outside_cards(_page(root, slug))
    assert cards[0]["lines"] == ["Ships in a week", "Ships in a month"] and cards[0]["why"] == "iPhone" and "lines" not in cards[1]
    ideas.set_section(root, slug, "Open questions", "")
    ideas.save_state(sd, slug, state="talk")
    card = idea_questions.card({"q": "Which week?", "choices": ["this", "next"], "pick": 0, "why": "soon", "lines": ["Now", "Later"]}, id="c1", by="tech", leader="ork")
    plain = idea_questions.card({"q": "Which size?", "choices": ["S", "L"], "pick": 0, "why": "small"}, id="c2", by="tech", leader="ork")
    idea_questions.save_record(sd, slug, {"mode": "talk", "round": 1, "waiting": [card, plain], "stances": []})
    host.ideas.keeper.talk_answer = lambda s, answers, decide=False: None
    host.command("ideas.talk_answer", {"idea": slug, "answers": [{"id": "c1", "pick": 1}, {"id": "c2", "pick": 0}]})
    text = _page(root, slug).section("Open questions")
    assert idea_questions.questions_of(text) == ["Which week? (**this** / next) — soon · this: Now · next: Later", "Which size?"]
    assert idea_questions.parse(idea_questions.questions_of(text)[0])["lines"] == ["Now", "Later"]
    assert idea_questions.answers(text) == ["next", "S"]
