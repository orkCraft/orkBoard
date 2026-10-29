"""The git of an idea's tasks (realm/idea_git.py): the gate's files, the fast-forward, the secrets."""
from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest

from orkboard.realm import idea_git
from orkboard.realm.idea_git import IdeaGit


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-m", "start")
    return r


def commit_in(path: Path, name: str, text: str) -> None:
    (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-m", f"edit {name}")


def test_the_gate_runs_the_critical_tests_and_those_of_touched_modules(tmp_path):
    (tmp_path / "tests").mkdir()
    for name in ("test_architecture.py", "test_cli.py", "test_updates.py", "test_ideas.py", "test_x.py"):
        (tmp_path / "tests" / name).write_text("")
    files = idea_git.test_files(["orkcraft/realm/ideas.py", "orkcraft/gone.py", "tests/test_x.py", "README.md",
                                 "orkcraft/__init__.py"], tmp_path)
    assert files == [*idea_git.CRITICAL_TESTS, "tests/test_ideas.py", "tests/test_x.py"]


def test_a_task_branch_lands_on_main_checked_out_and_its_files_follow(repo):
    g = IdeaGit(repo)
    path, branch = g.prepare("demo", "k1", "main")
    assert branch == "idea/demo/k1" and git(path, "rev-parse", "--abbrev-ref", "HEAD") == branch
    commit_in(path, "b.txt", "b\n")
    commit, subjects, note = g.land(path, branch, "main", push=True)
    assert commit == git(repo, "rev-parse", "main") and subjects == ["edit b.txt"] and note == ""
    assert (repo / "b.txt").read_text() == "b\n"


def test_main_checked_out_with_the_touched_file_dirty_is_left_as_it_was(repo):
    g = IdeaGit(repo)
    path, branch = g.prepare("demo", "k1", "main")
    commit_in(path, "a.txt", "task\n")
    (repo / "a.txt").write_text("the owner's own edit\n")
    before = git(repo, "rev-parse", "main")
    with pytest.raises(RuntimeError, match="uncommitted changes in a.txt"):
        g.land(path, branch, "main")
    assert git(repo, "rev-parse", "main") == before
    assert (repo / "a.txt").read_text() == "the owner's own edit\n"


def test_an_unrelated_dirty_file_does_not_stop_the_fast_forward(repo):
    g = IdeaGit(repo)
    path, branch = g.prepare("demo", "k1", "main")
    commit_in(path, "b.txt", "b\n")
    (repo / "a.txt").write_text("the owner's own edit\n")
    g.land(path, branch, "main")
    assert (repo / "b.txt").exists() and (repo / "a.txt").read_text() == "the owner's own edit\n"


def test_a_second_prepare_cuts_the_branch_anew(repo):
    g = IdeaGit(repo)
    path, branch = g.prepare("demo", "k1", "main")
    commit_in(path, "b.txt", "old try\n")
    path, _ = g.prepare("demo", "k1", "main")
    assert git(path, "rev-parse", "HEAD") == git(repo, "rev-parse", "main")
    assert not (path / "b.txt").exists()


def test_a_push_failure_is_a_note_not_a_failure(repo, tmp_path):
    git(repo, "remote", "add", "origin", str(tmp_path / "nowhere.git"))
    g = IdeaGit(repo)
    path, branch = g.prepare("demo", "k1", "main")
    commit_in(path, "b.txt", "b\n")
    _commit, _subjects, note = g.land(path, branch, "main", push=True)
    assert note.startswith("push failed")


def test_one_lock_per_repository(repo):
    assert idea_git.lock_of(repo) is idea_git.lock_of(repo / ".") is IdeaGit(repo).lock


def test_secrets_are_read_from_the_state_file(tmp_path):
    (tmp_path / "secrets.json").write_text(json.dumps({"ideas/demo/t1": "v1", "other": {"t2": "v2"}}))
    assert idea_git.read_secret(tmp_path, "demo", "t1") == "v1"
    assert idea_git.read_secret(tmp_path, "other", "t2") == "v2"
    assert idea_git.read_secret(tmp_path, "demo", "nope") is None
    assert idea_git.read_secret(tmp_path / "missing", "demo", "t1") is None


def test_the_env_name_comes_from_the_todos_title():
    assert idea_git.env_name("Add API_KEY for the mailer") == "API_KEY"
    assert idea_git.env_name("The STRIPE token: STRIPE_SECRET") == "STRIPE_SECRET"
    assert idea_git.env_name("GITHUB token") == "GITHUB"
    assert idea_git.env_name("a key") == ""


def test_the_review_branch_is_made_from_the_default_branch_when_missing(repo):
    g = IdeaGit(repo)
    assert g.branches() == ["main"] and g.default_branch() == "main"
    assert g.ensure_branch("dev") is True and g.ensure_branch("dev") is False
    assert git(repo, "rev-parse", "dev") == git(repo, "rev-parse", "main") and g.branches() == ["dev", "main"]
    for bad in ("", "bad name", "a..b", "-x"):
        with pytest.raises(RuntimeError):
            g.ensure_branch(bad)


def test_the_diff_has_commits_files_and_patches_and_cuts_what_is_too_large(repo, monkeypatch):
    g = IdeaGit(repo)
    base = git(repo, "rev-parse", "HEAD")
    path, branch = g.prepare("i", "k1", "main")
    commit_in(path, "a.txt", "a\nb\n")
    commit_in(path, "big.txt", "x" * 100 + "\n")
    got = g.diff(branch, base)
    assert [c["subject"] for c in got["commits"]] == ["edit a.txt", "edit big.txt"] and len(got["commits"][0]["sha"]) == 10
    by = {f["path"]: f for f in got["files"]}
    assert by["a.txt"]["added"] == 1 and by["a.txt"]["removed"] == 0 and "+b" in by["a.txt"]["patch"]
    assert got["truncated"] is False and g.stats(path, base) == {"files": 2, "added": 2, "removed": 0}
    monkeypatch.setattr(idea_git, "PATCH_FILE", 150)
    cut = {f["path"]: f for f in g.diff(branch, base)["files"]}
    assert cut["a.txt"]["patch"] is not None and cut["big.txt"]["patch"] is None
    assert g.diff(branch, base)["truncated"] is True
    monkeypatch.setattr(idea_git, "PATCH_FILE", 10_000)
    monkeypatch.setattr(idea_git, "PATCH_ALL", 250)                 # all of them together
    assert sum(f["patch"] is None for f in g.diff(branch, base)["files"]) == 1


def test_one_file_is_committed_alone_and_a_worktree_is_put_back_as_it_was_cut_spec_51(repo):
    """A picked file is committed by itself (`commit_file`); a task that made variants gets its worktree back (`restore`)."""
    g = IdeaGit(repo)
    path, _branch = g.prepare("demo", "k1", "main")
    start = g.head(path)
    (path / "assets").mkdir()
    (path / "assets" / "logo.png").write_bytes(b"\x89PNG one")
    (path / "stray.txt").write_text("not wanted\n")
    g.commit_file(path, "assets/logo.png", "Draw the logo: B · wolf")
    assert git(path, "log", "-1", "--format=%s") == "Draw the logo: B · wolf"
    assert git(path, "show", "--stat", "--format=", "HEAD").split()[0] == "assets/logo.png" and (path / "stray.txt").exists()
    with pytest.raises(RuntimeError, match="already holds that file"):
        g.commit_file(path, "assets/logo.png", "again")                 # the same bytes: nothing changes
    (repo / ".gitignore").write_text(".orkcraft/\nhidden/\n")
    git(repo, "commit", "-am", "ignore")
    path2, _ = g.prepare("demo", "k2", "main")
    (path2 / "hidden").mkdir()
    (path2 / "hidden" / "logo.png").write_bytes(b"x")
    with pytest.raises(RuntimeError, match="hidden/logo.png is ignored by git"):
        g.commit_file(path2, "hidden/logo.png", "m")
    commit_in(path, "tool.py", "print(1)\n")
    g.restore(path, start)
    assert g.head(path) == start and not (path / "tool.py").exists() and not (path / "stray.txt").exists() and not g.dirty(path)


# -- the main checkout's dependencies, linked into the worktree (spec 86 §2) -------------------------------------------

def installed(repo: Path) -> None:
    """A Node project with a web/ folder, both installed, and a virtual environment: untracked, as they are in life."""
    (repo / "package.json").write_text('{"scripts": {"test": "node --test"}}')
    (repo / "web").mkdir()
    (repo / "web" / "package.json").write_text('{"scripts": {"build": "x"}}')
    (repo / ".gitignore").write_text(".orkcraft/\nnode_modules/\n.venv/\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "node")
    for rel in ("node_modules/dep", "web/node_modules/dep", ".venv/bin"):
        (repo / rel).mkdir(parents=True)
    (repo / "node_modules" / "dep" / "index.js").write_text("module.exports = 1\n")


def test_a_worktree_gets_the_main_checkouts_node_modules_and_venv_as_links(repo):
    installed(repo)
    path, _ = IdeaGit(repo).prepare("demo", "k1", "main")
    for rel in ("node_modules", "web/node_modules", ".venv"):
        assert (path / rel).is_symlink() and (path / rel).resolve() == (repo / rel).resolve(), rel
    assert (path / "node_modules" / "dep" / "index.js").read_text() == "module.exports = 1\n"


def test_the_links_are_never_committed_even_when_the_project_ignores_nothing(repo):
    (repo / "package.json").write_text("{}")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "node")
    (repo / "node_modules" / "dep").mkdir(parents=True)                          # .gitignore does not name it
    (repo / ".venv").mkdir()
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    assert (path / "node_modules").is_symlink() and (path / ".venv").is_symlink()
    assert g.dirty(path) is False                                                # git sees neither link
    commit_in(path, "b.txt", "b\n")
    git(path, "add", "-A")
    assert git(path, "ls-files").split() == [".gitignore", "a.txt", "b.txt", "package.json"]
    assert {"node_modules", ".venv"} <= set((repo / ".git" / "info" / "exclude").read_text().split())


def test_a_worktree_that_has_its_own_or_a_project_without_them_gets_no_link(repo):
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "plain", "main")                                  # nothing installed: nothing linked
    assert not (path / "node_modules").exists() and not (path / ".venv").exists()
    installed(repo)
    (repo / "tracked").mkdir()
    (repo / "tracked" / "package.json").write_text("{}")
    (repo / "tracked" / "node_modules").mkdir()
    (repo / "tracked" / "node_modules" / "x.js").write_text("x\n")
    git(repo, "add", "-f", "tracked/node_modules/x.js", "tracked/package.json")
    git(repo, "commit", "-m", "tracked dependencies")
    path, _ = g.prepare("demo", "k2", "main")
    assert (path / "tracked" / "node_modules").is_dir() and not (path / "tracked" / "node_modules").is_symlink()   # its own
    assert (path / "node_modules").is_symlink()


def test_the_links_go_with_the_worktree_and_leave_the_main_checkout_whole(repo):
    installed(repo)
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    g.remove(path)
    assert not path.exists()
    assert (repo / "node_modules" / "dep" / "index.js").is_file() and (repo / ".venv" / "bin").is_dir()
    again, _ = g.prepare("demo", "k1", "main")                                     # a second try links again, once
    assert (again / "node_modules").is_symlink()
    assert (repo / ".git" / "info" / "exclude").read_text().split().count("node_modules") == 1


# -- spec 107 §1.2: documents only, a run that could not run -----------------------------------------------------------

def toml(root: Path, text: str) -> None:
    (root / "orkcraft.toml").write_text(text, encoding="utf-8")


def gate_on(repo: Path):
    """A task worktree with one commit; `gate_run` on it."""
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    commit_in(path, "b.dat", "b\n")
    return g.gate_run(path, "main", threading.Event())


def test_a_task_that_changed_only_documents_runs_no_derived_gate(repo):
    (repo / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "py")
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    commit_in(path, "docs.md", "# notes\n")
    run = g.gate_run(path, "main", threading.Event())
    assert (run.ok, run.ran, run.docs, run.command, run.env) == (True, False, True, "", "")
    assert run.out == "no tests ran: the task changed only documents"
    commit_in(path, "code.py", "x = 1\n")                                             # a file that is not a document: the gate runs
    run = g.gate_run(path, "main", threading.Event(), timeout_s=120)
    assert run.ran is True and run.docs is False and run.command.startswith("python -m pytest")


def test_a_gate_the_project_wrote_runs_as_written_for_documents_too(repo):
    toml(repo, '[gate]\nrun = "echo ran-as-written"\n')
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    commit_in(path, "docs.md", "# notes\n")
    run = g.gate_run(path, "main", threading.Event())
    assert run.ran and run.ok and run.docs is False and "ran-as-written" in run.out and run.env == "" and run.seconds >= 0


def test_a_run_that_found_a_command_missing_says_so_and_a_red_one_does_not(repo):
    toml(repo, '[gate]\nrun = "sh -c \'nonexistent-tool-xyz\'"\n')
    run = gate_on(repo)
    assert run.ok is False and run.ran is True and run.code == 127 and run.docs is False
    assert run.env == "The tests could not run: `nonexistent-tool-xyz` is not installed." and run.seconds >= 0
    toml(repo, '[gate]\nrun = "sh -c \'echo 1 failed; exit 1\'"\n')
    red = gate_on(repo)
    assert red.ok is False and red.code == 1 and red.env == ""


def test_a_command_that_cannot_start_could_not_run(repo):
    toml(repo, '[gate]\nrun = "nonexistent-tool-xyz --go"\n')
    run = gate_on(repo)
    assert run.ok is False and run.code == 127 and "`nonexistent-tool-xyz`" in run.env
