"""Spec 151 F on fixture repositories (real git in tmp_path, the anonymous GitHub check faked, no model, no network): the Board in the code of a private
repository without a question; a public one writes nothing to the work branch until answered (its pages commit on `refs/orkboard/pages`); `in_code = false`
takes the pages out of the work branch once; a task gets its spec in `.orkcraft/spec/` and commits none of it; the yes later puts them in once; found public
since holds the pushes; a goal kept off is in no commit of either branch."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

from orkboard.realm import board_branch, board_in_code, board_tree_off, ideas
from orkboard.realm.board_tree import BoardTree
from orkboard.realm.idea_git import IdeaGit

WIKI = "llm-wiki/general"
DAY = 24 * 3600 + 1
NOW = time.time()                    # the asked-once-a-day cache is read against the clock: every test says its own `now` from here


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def fake(code: int):
    calls = []

    def get(url):
        calls.append(url)
        return code
    get.calls = calls
    return get


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refused(url):
        raise AssertionError(f"the test asked GitHub: {url}")
    monkeypatch.setattr(board_branch, "http_status", refused)


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@x")
    git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".orkcraft/\n")
    (repo / "app.py").write_text("x = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "start")
    git(repo, "remote", "add", "origin", "https://github.com/acme/app.git")
    return repo


def tree_of(repo, goes=None, kept=None) -> BoardTree:
    state = repo / ".orkcraft"
    t = BoardTree(repo, state, WIKI, lambda: "dev", goes=goes or (lambda: board_in_code.goes(repo, state)),
                  kept_off=kept or (lambda: board_in_code.sync_kept_off(repo, state, WIKI)))
    t.ensure()
    return t


def page(t, name, text="# Page\n"):
    path = t.root() / "pages" / "ideas" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def commit_code(repo, name="code.py"):
    """A commit on the work branch from outside the Board, as a task landing would be."""
    wt = repo.parent / f"wt-{name}"
    git(repo, "worktree", "add", "-q", "--detach", str(wt), "dev")
    (wt / name).write_text("y = 2\n")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", f"code {name}")
    sha = git(wt, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/heads/dev", sha)
    git(repo, "worktree", "remove", "--force", str(wt))


def in_branch(repo, ref, rel):
    return subprocess.run(["git", "cat-file", "-e", f"{ref}:{rel}"], cwd=repo, capture_output=True).returncode == 0


def ever_committed(repo, needle):
    """Whether any commit of any ref holds a path with `needle` in it."""
    names = git(repo, "log", "--all", "--format=", "--name-only")
    return needle in names


# -- the word in orkcraft.toml ---------------------------------------------------------------------------------------

def test_in_code_is_written_and_read_and_every_other_line_is_kept(tmp_path):
    (tmp_path / "orkcraft.toml").write_text('[gate]\nalways = ["x"]\n')
    assert board_in_code.read(tmp_path) is None
    board_in_code.write(tmp_path, False)
    assert board_in_code.read(tmp_path) is False and (tmp_path / "orkcraft.toml").read_text().startswith('[gate]\nalways = ["x"]\n')
    board_in_code.write(tmp_path, True)
    text = (tmp_path / "orkcraft.toml").read_text()
    assert board_in_code.read(tmp_path) is True and text.count("in_code") == 1 and text.count("[board]") == 1


def test_in_code_alone_is_no_yes_to_the_boards_branch_and_the_branch_goes_in_beside_it(tmp_path):
    board_in_code.write(tmp_path, True)
    assert board_branch.read_config(tmp_path) is None
    board_branch.turn_on(tmp_path)
    assert board_branch.read_config(tmp_path) == board_branch.BoardConfig("origin", "orkboard/board") and board_in_code.read(tmp_path) is True
    assert (tmp_path / "orkcraft.toml").read_text().count("[board]") == 1


# -- the visibility, once a day --------------------------------------------------------------------------------------

def test_the_visibility_is_asked_once_a_day_and_a_look_that_says_nothing_keeps_the_last_word(repo):
    state = repo / ".orkcraft"
    get = fake(404)
    assert board_in_code.status(repo, state, get, now=NOW)["visibility"] == "private" and board_in_code.status(repo, state, get, now=NOW + 100)["goes"]
    assert len(get.calls) == 1
    got = board_in_code.check(repo, state, fake(200), now=NOW + DAY)
    assert got == {"visibility": "public", "was": "private", "found_public": True}
    assert board_in_code.check(repo, state, fake(0), now=NOW + 2 * DAY)["visibility"] == "public"        # offline: the word before stands


def test_no_remote_goes_and_a_remote_not_on_github_does_not_until_the_person_says(tmp_path, repo):
    state = repo / ".orkcraft"
    git(repo, "remote", "remove", "origin")
    assert board_in_code.status(repo, state) == {"visibility": "none", "in_code": None, "goes": True}
    git(repo, "remote", "add", "origin", "git@example.org:acme/app.git")
    assert board_in_code.status(repo, state) == {"visibility": "unknown", "in_code": None, "goes": False}
    board_in_code.write(repo, True)
    assert board_in_code.status(repo, state)["goes"] is True


# -- a private repository: the Board in the code, nothing asked -----------------------------------------------------------

def test_a_private_repository_writes_to_the_work_branch_and_asks_nothing(repo):
    get = fake(404)
    board_in_code.status(repo, repo / ".orkcraft", get, now=NOW)
    t = tree_of(repo)
    page(t, "a.md")
    t.note("A", "drafted", 0.0)
    got = t.flush(force=True)
    assert got["commit"] and not got["held"]
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md") and not board_tree_off.has_ref(t)
    assert board_in_code.pending_question(repo, "dev", get) is None


# -- a public one: nothing on the work branch until answered ----------------------------------------------------------------

def test_a_public_repository_commits_on_the_local_ref_and_never_moves_the_work_branch(repo):
    board_in_code.status(repo, repo / ".orkcraft", fake(200), now=NOW)
    t = tree_of(repo)
    before = git(repo, "rev-parse", "dev")
    page(t, "a.md")
    t.note("A", "drafted", 0.0)
    got = t.flush(force=True)
    assert got["commit"] and not got["held"]
    assert git(repo, "rev-parse", "dev") == before and not in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md")
    assert in_branch(repo, board_tree_off.REF, f"{WIKI}/pages/ideas/a.md") and git(repo, "rev-parse", board_tree_off.REF) == git(t.path, "rev-parse", "HEAD")
    page(t, "b.md")
    t.note("B", "drafted", 0.0)
    t.flush(force=True)
    assert git(repo, "rev-parse", "dev") == before and in_branch(repo, board_tree_off.REF, f"{WIKI}/pages/ideas/b.md")
    assert board_in_code.pending_question(repo, "dev") == {"public": True, "visibility": "public", "pages_in_history": 0}
    assert "refs/orkboard/pages" not in git(repo, "ls-remote", "--refs", ".", "refs/heads/*")


def test_the_tree_follows_the_work_branch_while_it_is_off(repo):
    board_in_code.status(repo, repo / ".orkcraft", fake(200), now=NOW)
    t = tree_of(repo)
    page(t, "a.md")
    t.flush(force=True)
    commit_code(repo)
    page(t, "b.md")
    t.flush(force=True)
    assert (t.path / "code.py").is_file() and (t.root() / "pages/ideas/a.md").is_file() and (t.root() / "pages/ideas/b.md").is_file()
    assert git(repo, "merge-base", "--is-ancestor", "dev", board_tree_off.REF) == "" and not in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md")
    assert not git(repo, "status", "--porcelain", "--", "code.py")


# -- `false`: the pages leave the work branch, once ---------------------------------------------------------------------------

def _on_then_pages(repo):
    """A repository that had the Board in its code: two pages on the work branch, then the person says no."""
    board_in_code.status(repo, repo / ".orkcraft", fake(404), now=NOW)
    t = tree_of(repo)
    page(t, "a.md")
    page(t, "b.md")
    t.flush(force=True)
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md")
    return t


def test_no_takes_the_pages_out_of_the_work_branch_in_one_commit_and_its_history_keeps_them(repo):
    t = _on_then_pages(repo)
    board_in_code.write(repo, False)
    page(t, "c.md")
    count = int(git(repo, "rev-list", "--count", "dev"))
    t.flush(force=True)
    assert int(git(repo, "rev-list", "--count", "dev")) == count + 1
    assert git(repo, "log", "-1", "--format=%s", "dev") == "board: the Board's pages leave the repository"
    assert not in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md") and ever_committed(repo, "pages/ideas/a.md")
    assert (t.root() / "pages/ideas/a.md").is_file() and in_branch(repo, board_tree_off.REF, f"{WIKI}/pages/ideas/c.md")
    assert in_branch(repo, board_tree_off.REF, "app.py")
    t.flush(force=True)                                       # once: nothing more lands on the branch
    page(t, "d.md")
    t.flush(force=True)
    assert int(git(repo, "rev-list", "--count", "dev")) == count + 1
    assert board_in_code.pending_question(repo, "dev") is None          # the person has answered


def test_the_yes_later_puts_the_pages_into_the_work_branch_in_one_commit_and_drops_the_ref(repo):
    t = _on_then_pages(repo)
    board_in_code.write(repo, False)
    page(t, "c.md")
    t.flush(force=True)
    commit_code(repo)
    page(t, "d.md")
    t.flush(force=True)
    count = int(git(repo, "rev-list", "--count", "dev"))
    board_in_code.write(repo, True)
    got = t.flush(force=True)
    assert not got["held"] and int(git(repo, "rev-list", "--count", "dev")) == count + 1
    assert git(repo, "log", "-1", "--format=%s", "dev") == "board: the Board goes into the code"
    for name in "abcd":
        assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/{name}.md")
    assert in_branch(repo, "dev", "code.py") and not board_tree_off.has_ref(t) and not board_tree_off.is_off(t)
    page(t, "e.md")
    t.flush(force=True)
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/e.md") and int(git(repo, "rev-list", "--count", "dev")) == count + 2


def test_a_lost_tree_starts_again_from_the_local_ref(repo):
    board_in_code.status(repo, repo / ".orkcraft", fake(200), now=NOW)
    t = tree_of(repo)
    page(t, "a.md")
    t.flush(force=True)
    git(repo, "worktree", "remove", "--force", str(t.path))
    (repo / ".orkcraft" / board_tree_off.MARK).unlink()
    again = tree_of(repo)
    assert (again.root() / "pages/ideas/a.md").is_file() and board_tree_off.is_off(again)


# -- a task's spec in its worktree ------------------------------------------------------------------------------------------

def test_a_task_is_given_its_spec_in_its_worktree_and_its_commit_holds_none_of_it(repo):
    board_in_code.status(repo, repo / ".orkcraft", fake(200), now=NOW)
    t = tree_of(repo)
    page(t, "dark-mode.md", '---\ndepends_on: ["base"]\n---\n# Dark mode\n')
    page(t, "base.md", "# Base\n")
    t.flush(force=True)
    g = IdeaGit(repo)
    g.ensure_branch("dev")
    path, _branch = g.prepare("dark-mode", "t1", "dev")
    assert (path / ".orkcraft/spec/dark-mode.md").read_text().endswith("# Dark mode\n") and (path / ".orkcraft/spec/base.md").is_file()
    assert board_in_code.worktree_specs(repo, repo / ".orkcraft", "dark-mode") == (".orkcraft/spec/dark-mode.md", [".orkcraft/spec/base.md"])
    assert git(path, "status", "--porcelain") == ""
    (path / "new.py").write_text("z = 3\n")
    assert g.commit_left(path, "the task")
    assert git(path, "show", "--name-only", "--format=", "HEAD") == "new.py"
    assert not ever_committed(repo, ".orkcraft/spec")


def test_a_private_repository_gives_a_task_no_copy(repo):
    board_in_code.status(repo, repo / ".orkcraft", fake(404), now=NOW)
    t = tree_of(repo)
    page(t, "dark-mode.md")
    t.flush(force=True)
    g = IdeaGit(repo)
    path, _branch = g.prepare("dark-mode", "t1", "dev")
    assert not (path / ".orkcraft/spec").exists() and (path / WIKI / "pages/ideas/dark-mode.md").is_file()


# -- found public since ------------------------------------------------------------------------------------------------------

def test_found_public_since_puts_the_board_off_at_once_holds_the_pushes_and_asks(repo, monkeypatch):
    state = repo / ".orkcraft"
    board_in_code.status(repo, state, fake(404), now=NOW)
    t = tree_of(repo)
    page(t, "a.md")
    t.flush(force=True)
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md")
    assert board_in_code.push_hold(repo) == ""
    got = board_in_code.check(repo, state, fake(200), now=NOW + DAY)
    assert got["found_public"] is True
    assert board_in_code.pending_question(repo, "dev") == {"public": True, "visibility": "public", "pages_in_history": 1}
    t.flush(force=True)                                       # the host's forced write: the Board is off at once
    assert not in_branch(repo, "dev", f"{WIKI}/pages/ideas/a.md") and in_branch(repo, board_tree_off.REF, f"{WIKI}/pages/ideas/a.md")
    words = "This repository is public: the Board waits for your answer before anything is pushed."
    assert board_in_code.push_hold(repo) == words and IdeaGit(repo).push("dev") == words
    assert board_branch.push(repo, board_branch.BoardConfig(), "0" * 40) == {"ok": False, "refused": False, "why": words}
    board_in_code.write(repo, False)                          # the answer: the pushes may go
    assert board_in_code.push_hold(repo) == "" and board_in_code.pending_question(repo, "dev") is None


# -- a goal kept off ----------------------------------------------------------------------------------------------------------

def _goals(repo, t):
    state = repo / ".orkcraft"
    for slug in ("plain", "secretive", "marked", "sec-kind"):
        page(t, f"{slug}.md", f"# {slug}\n")
        ideas.save_state(state, slug, state="raw")
    board_in_code.keep_off(state, "marked", True)
    ideas.save_state(state, "sec-kind", type="tech/security")
    (state / "ideas" / "secretive" / "plan.json").write_text(json.dumps({"todos": [{"id": "k1", "kind": "secret", "title": "KEY"}]}))


def test_a_goal_kept_off_is_read_with_the_others_and_is_in_no_commit_of_either_branch(repo):
    state = repo / ".orkcraft"
    board_in_code.write(repo, True)
    board_in_code.status(repo, state, fake(200), now=NOW)
    t = tree_of(repo)
    _goals(repo, t)
    assert board_in_code.kept_off_slugs(state) == ["marked", "sec-kind", "secretive"]
    assert board_in_code.kept_off(repo, state, "marked") and not board_in_code.kept_off(repo, state, "plain")
    t.note("Goals", "drafted", 0.0)
    got = t.flush(force=True)
    assert got["commit"] and not got["held"]
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/plain.md")                  # the repository is public with the yes: the Board is in the code
    for slug in ("marked", "sec-kind", "secretive"):
        assert (t.root() / "pages/ideas" / f"{slug}.md").is_file()                  # read with the others, from the tree
        assert not ever_committed(repo, f"ideas/{slug}.md")
    commit_code(repo)                                                               # a task landed: the tree follows, the pages stay
    page(t, "plain.md", "# plain, edited\n")
    t.flush(force=True)
    t.follow()
    assert all((t.root() / "pages/ideas" / f"{s}.md").is_file() for s in ("marked", "sec-kind", "secretive"))
    assert not ever_committed(repo, "ideas/marked.md") and not ever_committed(repo, "ideas/secretive.md") and ever_committed(repo, "ideas/plain.md")
    files, _held = board_branch.pack(state, WIKI)
    assert f"board/{WIKI}/pages/ideas/plain.md" in files
    assert not any(f"pages/ideas/{s}.md" in n or n.startswith(f"ideas/{s}/") for n in files for s in ("marked", "sec-kind", "secretive"))


def test_pack_leaves_a_goal_kept_off_at_home_and_a_goal_that_goes_is_sent(repo):
    state = repo / ".orkcraft"
    board_in_code.write(repo, True)
    board_in_code.status(repo, state, fake(200), now=NOW)
    t = tree_of(repo)
    _goals(repo, t)
    (state / "ideas" / "marked" / "talk.jsonl").write_text('{"who":"person","text":"words"}\n')
    (state / "ideas" / "plain" / "talk.jsonl").write_text('{"who":"person","text":"words"}\n')
    files, _held = board_branch.pack(state, WIKI)
    assert f"board/{WIKI}/pages/ideas/plain.md" in files and "ideas/plain/talk.jsonl" in files
    for slug in ("marked", "sec-kind", "secretive"):
        assert f"board/{WIKI}/pages/ideas/{slug}.md" not in files and not any(n.startswith(f"ideas/{slug}/") for n in files)
    board_in_code.keep_off(state, "marked", False)                                  # let it go again
    files, _held = board_branch.pack(state, WIKI)
    assert f"board/{WIKI}/pages/ideas/marked.md" in files


def test_a_goal_that_was_committed_before_it_was_kept_off_leaves_the_work_branch_with_the_next_write(repo):
    state = repo / ".orkcraft"
    board_in_code.write(repo, True)
    board_in_code.status(repo, state, fake(200), now=NOW)
    t = tree_of(repo)
    page(t, "later.md")
    ideas.save_state(state, "later", state="raw")
    t.flush(force=True)
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/later.md")
    board_in_code.keep_off(state, "later", True)
    page(t, "plain.md")
    t.flush(force=True)
    assert not in_branch(repo, "dev", f"{WIKI}/pages/ideas/later.md") and (t.root() / "pages/ideas/later.md").is_file()


def _prompt(repo, slug):
    from types import SimpleNamespace

    from orkboard.core.idea_task import TaskMixin
    runner = SimpleNamespace(repo_root=repo, state_dir=repo / ".orkcraft", settings={}, tool_of=lambda *a: "claude", size_of=None,
                             _role=lambda t: {"name": "Grunt", "instruction": "", "slug": "grunt"}, _env=lambda *a: {}, _reading=lambda *a: "",
                             _without=lambda *a: [], _does_it_itself=lambda *a: False)
    plan = {"tasks": [{"id": "t1", "title": "Build it", "brief": "Make the screen"}]}
    return TaskMixin._prompt(runner, slug, plan, plan["tasks"][0])


def test_the_prompt_names_the_spec_in_the_worktree_when_the_board_is_off_and_the_boards_page_when_it_is_in(repo):
    state = repo / ".orkcraft"
    board_in_code.status(repo, state, fake(200), now=NOW)
    t = tree_of(repo)
    page(t, "dark-mode.md", '---\ndepends_on: ["base"]\n---\n# Dark mode\nSECRET WORDS\n')
    page(t, "base.md")
    t.flush(force=True)
    off = _prompt(repo, "dark-mode")
    assert "Its spec is at `.orkcraft/spec/dark-mode.md` in this worktree" in off and "It depends on `.orkcraft/spec/base.md`." in off and "SECRET WORDS" not in off
    board_in_code.write(repo, True)
    t.flush(force=True)
    board_in_code.keep_off(state, "dark-mode", True)                      # in the code, but this goal is kept off it: its spec still comes as a copy
    assert "Its spec is at `.orkcraft/spec/dark-mode.md`" in _prompt(repo, "dark-mode")
    board_in_code.keep_off(state, "dark-mode", False)
    assert f"Its spec is at `{WIKI}/pages/ideas/dark-mode.md`" in _prompt(repo, "dark-mode")


def test_nothing_is_kept_off_in_a_private_repository(repo):
    state = repo / ".orkcraft"
    board_in_code.status(repo, state, fake(404), now=NOW)
    t = tree_of(repo)
    _goals(repo, t)
    assert board_in_code.kept_off_slugs(state) == [] and not board_in_code.kept_off(repo, state, "marked")
    t.flush(force=True)
    assert in_branch(repo, "dev", f"{WIKI}/pages/ideas/marked.md")
