"""Spec 37 C: the gate on any repository (realm/gate_config.py, idea_git.gate_run, the runner's `tests`) and `ideas.doc`
reading no secret."""
from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError
from orkboard.realm import gate_config, idea_git
from orkboard.realm.idea_git import IdeaGit

from tests.test_gui_goals import host  # noqa: F401  (the host fixture)
from tests.test_idea_git import commit_in, git, repo  # noqa: F401  (a repository with no tests)
from tests.test_idea_runner import plan_of, reviewing, runner_of, tasks_of, town, wait_idle, wait_task  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent


def toml(root: Path, text: str) -> None:
    (root / "orkcraft.toml").write_text(text, encoding="utf-8")


def gate_in(repo: Path, **more):
    """A task worktree with one commit; `gate_run` on it."""
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    commit_in(path, "b.dat", "b\n")
    return g.gate_run(path, "main", threading.Event(), **more)


# -- the file --------------------------------------------------------------------------------------------------

def critical_tests(root: Path) -> None:
    """The three files a Python project of Orkboard's way has (`gate_config.CRITICAL_TESTS`)."""
    (root / "tests").mkdir(exist_ok=True)
    for rel in gate_config.CRITICAL_TESTS:
        (root / rel).write_text("")


def test_without_a_file_or_a_gate_table_the_gate_is_todays_when_the_project_has_its_critical_tests(tmp_path):
    critical_tests(tmp_path)
    assert gate_config.read(tmp_path) == gate_config.Gate() and not gate_config.read(tmp_path).custom
    toml(tmp_path, "[other]\nx = 1\n")
    assert gate_config.read(tmp_path) == gate_config.Gate()
    assert gate_config.Gate().always == idea_git.CRITICAL_TESTS == gate_config.CRITICAL_TESTS
    assert not gate_config.Gate().none


def test_without_critical_tests_always_is_empty_and_only_the_files_that_exist_count(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_cli.py").write_text("")
    assert gate_config.read(tmp_path).always == ("tests/test_cli.py",)


def test_this_repository_names_its_three_critical_tests_in_always():
    """Orkboard's own critical tests (CLAUDE.md, Alpha); Orkline's (`idea_git.CRITICAL_TESTS`) stay the default of a
    repository with no file."""
    gate = gate_config.read(ROOT)
    assert gate.always == ("tests/test_architecture.py", "tests/test_board_alone.py", "tests/test_updates.py")
    assert not gate.error and not gate.custom and all((ROOT / t).is_file() for t in gate.always)
    assert (ROOT / "orkcraft.toml").is_file()


def test_the_gate_table_is_read_and_unknown_keys_are_ignored(tmp_path):
    toml(tmp_path, '[gate]\nrun = "npm test -- {files}"\nalways = ["t/a.test.js"]\nmap = ["t/{stem}.test.js"]\n'
                   'timeout_min = 5\nsurprise = true\n')
    gate = gate_config.read(tmp_path)
    assert (gate.run, gate.always, gate.map, gate.timeout_min, gate.error) == (
        "npm test -- {files}", ("t/a.test.js",), ("t/{stem}.test.js",), 5, "")


@pytest.mark.parametrize("text", ["[gate\nrun = ", "[gate]\nrun = 3\n", "[gate]\nalways = \"x\"\n", "[gate]\ntimeout_min = -1\n",
                                  "gate = 4\n"])
def test_a_broken_file_is_said_and_the_gate_is_todays(tmp_path, text):
    toml(tmp_path, text)
    gate = gate_config.read(tmp_path)
    assert gate.error.startswith("orkcraft.toml is not usable") and "ran as with no file" in gate.error
    assert not gate.custom and gate.always == () and gate.none           # an empty folder: no tests, said and not run


def test_a_broken_file_gives_the_project_its_own_gate_with_the_error(tmp_path):
    critical_tests(tmp_path)
    toml(tmp_path, "[gate\n")
    gate = gate_config.read(tmp_path)
    assert gate.error.startswith("orkcraft.toml is not usable") and gate.always == gate_config.CRITICAL_TESTS and not gate.none
    (tmp_path / "go.mod").write_text("module x\n")
    import shutil
    shutil.rmtree(tmp_path / "tests")
    assert gate_config.read(tmp_path).run == "go test ./..." and gate_config.read(tmp_path).error


def test_files_hold_always_and_the_mapped_tests_that_exist_and_the_command_quotes_them(tmp_path):
    for rel in ("t/a.test.js", "t/widget.test.js", "src/my dir/test_m.py", "src/lib/core.py"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("")
    gate = gate_config.Gate(run="npm test -- {files}", always=("t/a.test.js", "t/gone.js"),
                            map=("t/{stem}.test.js", "t/{name}.nope", "{dir}/test_{stem}.py"))
    files = gate_config.gate_files(gate, ["src/widget.js", "src/my dir/m.py", "README.md", "src/__init__.py"], tmp_path)
    assert files == ["t/a.test.js", "t/widget.test.js", "src/my dir/test_m.py"]
    assert gate_config.command(gate, files) == "npm test -- t/a.test.js t/widget.test.js 'src/my dir/test_m.py'"
    assert gate_config.command(gate_config.Gate(run="make check"), []) == "make check"     # no {files}: as is
    assert gate_config.command(gate, []) is None                                            # {files} with none to give


def test_without_a_gate_table_the_files_are_those_of_today(tmp_path):
    (tmp_path / "tests").mkdir()
    for name in ("test_architecture.py", "test_cli.py", "test_updates.py", "test_ideas.py", "test_x.py"):
        (tmp_path / "tests" / name).write_text("")
    touched = ["orkcraft/realm/ideas.py", "orkcraft/gone.py", "tests/test_x.py", "README.md", "orkcraft/__init__.py"]
    assert gate_config.gate_files(gate_config.Gate(), touched, tmp_path) == [
        *idea_git.CRITICAL_TESTS, "tests/test_ideas.py", "tests/test_x.py"]


def test_test_argv_comes_from_gate_config_for_the_jobs():
    from orkboard.realm import jobs
    assert gate_config.test_argv("pytest -q") == ["pytest", "-q"]
    assert gate_config.test_argv("pytest -q && ruff check .") == ["sh", "-c", "pytest -q && ruff check ."]
    assert jobs.test_argv is gate_config.test_argv


# -- the run -----------------------------------------------------------------------------------------------------

def test_nothing_to_run_is_not_a_pass(repo):
    run = gate_in(repo)
    assert run.ran is False and run.ok is True and run.code is None and "no tests ran" in run.out
    assert "no test files to run" not in run.out
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k2", "main")
    commit_in(path, "c.txt", "c\n")
    ok, _out = g.gate(path, "main", threading.Event())
    assert ok is False                                    # the plain gate does not call it a pass either


def test_a_command_that_is_not_pytest_is_decided_by_its_exit_code(repo):
    toml(repo, '[gate]\nrun = "sh -c \'exit 0\'"\n')
    ok = gate_in(repo)
    assert (ok.ran, ok.ok, ok.code, ok.command) == (True, True, 0, "sh -c 'exit 0'")
    toml(repo, "[gate]\nrun = \"sh -c 'echo broke; exit 1'\"\n")
    bad = gate_in(repo)
    assert (bad.ran, bad.ok, bad.code) == (True, False, 1) and "broke" in bad.out


def test_the_command_gets_always_and_the_mapped_tests_quoted(repo):
    (repo / "t").mkdir()
    (repo / "t" / "b.t").write_text("")
    (repo / "t" / "other.t").write_text("")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "tests")
    toml(repo, '[gate]\nrun = "echo files: {files}"\nalways = ["t/other.t"]\nmap = ["t/{stem}.t"]\n')
    run = gate_in(repo)
    assert run.ok and run.command == "echo files: t/other.t t/b.t" and "files: t/other.t t/b.t" in run.out


def test_a_command_with_files_and_nothing_to_give_them_runs_nothing(repo):
    toml(repo, '[gate]\nrun = "echo {files}"\nalways = []\nmap = ["t/{stem}.t"]\n')
    run = gate_in(repo)
    assert run.ran is False and run.ok


def test_a_broken_file_is_said_in_the_output_and_the_gate_ran_as_today(repo):
    toml(repo, "[gate\n")
    run = gate_in(repo)
    assert run.ran is False and "orkcraft.toml is not usable" in run.out        # today's gate: no tests in this repository


def test_the_gate_reads_the_file_from_the_repository_not_from_the_task_worktree(repo):
    toml(repo, '[gate]\nrun = "sh -c \'exit 1\'"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "gate")
    g = IdeaGit(repo)
    path, _ = g.prepare("demo", "k1", "main")
    (path / "orkcraft.toml").write_text('[gate]\nrun = "true"\n')                   # a task cannot loosen its own gate
    git(path, "add", "-A")
    git(path, "commit", "-m", "edit the gate")
    assert g.gate_run(path, "main", threading.Event()).ok is False


# -- the result ---------------------------------------------------------------------------------------------------

def no_tests(town):                                                                   # noqa: F811
    git(town.repo, "rm", "-rq", "tests")
    git(town.repo, "commit", "-qm", "no tests")


def test_a_result_with_no_test_to_run_waits_at_review_even_when_review_is_off(town):
    no_tests(town)
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)                                                       # ideas.review: false
    before = git(town.repo, "rev-parse", "main")
    runner.start("demo")
    task = wait_task(runner, "k1", "review")
    assert task["tests"]["ran"] is False and task["tests"]["green"] is True and task["state"] == "review"
    assert git(town.repo, "rev-parse", "main") == before and not (town.repo / "k1.txt").exists()
    assert "no tests ran" in task["tests"]["tail"]
    assert runner.merge("demo", "k1") and (town.repo / "k1.txt").exists()               # Merge stays the person's press


def test_a_command_that_is_not_pytest_leaves_null_counts_and_lands_when_review_is_off(town):
    toml(town.repo, '[gate]\nrun = "sh -c \'exit 0\'"\n')
    git(town.repo, "add", "-A")
    git(town.repo, "commit", "-qm", "gate")
    plan_of(town, [{"id": "k1"}])
    runner, _ = runner_of(town)
    runner.start("demo")
    assert wait_idle(runner)["state"] == "done"
    tests = tasks_of(town)["k1"]["tests"]
    assert (tests["ran"], tests["passed"], tests["failed"], tests["green"], tests["exit"]) == (True, None, None, True, 0)
    assert tests["command"] == "sh -c 'exit 0'"


def test_pytest_keeps_its_counts_and_records_what_ran(town):
    plan_of(town, [{"id": "k1"}])
    runner, _ = reviewing(town)
    runner.start("demo")
    tests = wait_task(runner, "k1", "review")["tests"]
    assert tests["ran"] is True and tests["passed"] >= 3 and tests["failed"] == 0 and tests["green"] is True
    assert tests["command"].startswith("python -m pytest -q tests/test_architecture.py")


def test_a_task_from_before_reads_as_ran(town):
    plan_of(town, [{"id": "k1"}])
    plan = json.loads((town.state / "ideas" / "demo" / "plan.json").read_text())
    plan["tasks"][0].update(state="review", tests={"passed": 3, "failed": 0, "failing": [], "tail": "", "green": True},
                            diff={"files": 1, "added": 1, "removed": 0})
    (town.state / "ideas" / "demo" / "plan.json").write_text(json.dumps(plan))
    runner, _ = reviewing(town)
    assert runner.plan("demo")["tasks"][0]["tests"].get("ran", True) is True


# -- ideas.doc --------------------------------------------------------------------------------------------------

SECRET_PATHS = (".env", ".orkcraft/secrets.json", ".git/config", "id_ed25519", "keys/id_ed25519", ".env.production")


def test_a_linked_document_never_reads_a_secret_or_git_or_orkcraft(host):                  # noqa: F811
    repo = Path(host.town.repo_root)
    for rel in SECRET_PATHS:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("TOKEN=hunter2\n")
    (repo / ".env.example").write_text("TOKEN=\n")
    (repo / "notes.md").write_text("# Notes\n")
    for rel in SECRET_PATHS:
        with pytest.raises(CommandError, match="may hold secrets: open it in your own editor"):
            host.command("ideas.doc", {"path": rel})
    with pytest.raises(CommandError, match="may hold secrets"):
        host.command("ideas.doc", {"path": "/.git/config#top"})
    assert host.command("ideas.doc", {"path": ".env.example"})["text"] == "TOKEN=\n"
    assert host.command("ideas.doc", {"path": "notes.md"})["text"] == "# Notes\n"


def test_a_link_to_a_secret_is_a_secret(host, tmp_path):                                    # noqa: F811
    repo = Path(host.town.repo_root)
    (repo / ".env").write_text("TOKEN=hunter2\n")
    (repo / "readme-link.md").symlink_to(repo / ".env")
    with pytest.raises(CommandError, match="may hold secrets"):
        host.command("ideas.doc", {"path": "readme-link.md"})


def test_the_phone_reads_documents_through_the_same_command(host):                         # noqa: F811
    assert BoardPhone.allowed(host, "ideas.doc", {"path": "notes.md"})
    assert "ideas.doc" not in BoardPhone.COMMANDS                                       # no phone-only path to the files


# -- the project's own gate (spec 86 §3) ----------------------------------------------------------------------------

def package(folder: Path, test: str | None = None, **scripts: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    table = {"build": "tsc", **scripts, **({"test": test} if test else {})}
    (folder / "package.json").write_text(json.dumps({"name": "x", "scripts": table}))


def test_a_node_project_is_gated_by_npm_test(tmp_path):
    package(tmp_path, "node --test")
    gate = gate_config.read(tmp_path)
    assert (gate.run, gate.always, gate.none, gate.custom) == ("npm test", (), False, True)
    assert gate_config.command(gate, gate_config.gate_files(gate, ["src/a.js"], tmp_path)) == "npm test"


def test_each_folder_with_a_test_script_is_tested_three_at_most_with_prefix(tmp_path):
    package(tmp_path / "server", "jest")
    package(tmp_path / "web", "vitest")
    package(tmp_path / "tools", None)                                                    # no test script: skipped
    package(tmp_path / "a", "x")
    package(tmp_path / "b", "y")
    package(tmp_path / "web" / "node_modules" / "dep", "dep test")                     # never inside node_modules
    run = gate_config.read(tmp_path).run
    assert run == "npm test --prefix a && npm test --prefix b && npm test --prefix server"
    assert gate_config.test_argv(run)[:2] == ["sh", "-c"]                                 # `&&` needs a shell
    package(tmp_path, "mocha")
    assert gate_config.read(tmp_path).run.startswith("npm test && npm test --prefix a")


def test_npms_placeholder_test_script_is_no_test(tmp_path):
    package(tmp_path, 'echo "Error: no test specified" && exit 1')
    assert gate_config.read(tmp_path).none is True
    (tmp_path / "go.mod").write_text("module x\n")
    assert gate_config.read(tmp_path).run == "go test ./..."


@pytest.mark.parametrize("files,run", [(("pyproject.toml",), "python -m pytest -q"), (("tests/x.txt",), "python -m pytest -q"),
                                       (("go.mod",), "go test ./..."), (("Cargo.toml",), "cargo test")])
def test_each_language_has_its_own_test_command(tmp_path, files, run):
    for rel in files:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("")
    gate = gate_config.read(tmp_path)
    assert (gate.run, gate.always, gate.none) == (run, (), False)


def test_node_comes_before_python_and_the_first_that_holds_wins(tmp_path):
    package(tmp_path, "jest")
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "go.mod").write_text("")
    assert gate_config.read(tmp_path).run == "npm test"
    (tmp_path / "package.json").unlink()
    assert gate_config.read(tmp_path).run == "python -m pytest -q"


def test_a_project_with_nothing_to_test_has_the_none_gate(tmp_path):
    (tmp_path / "README.md").write_text("x")
    gate = gate_config.read(tmp_path)
    assert (gate.none, gate.run, gate.always, gate.custom) == (True, "", (), False)
    assert gate_config.gate_files(gate, ["README.md"], tmp_path) == []


def test_a_gate_table_of_the_project_is_never_replaced_by_the_derived_one(tmp_path):
    package(tmp_path, "jest")
    toml(tmp_path, '[gate]\nrun = "make check"\n')
    assert gate_config.read(tmp_path).run == "make check"
    toml(tmp_path, '[gate]\nalways = ["t/a.t"]\n')
    gate = gate_config.read(tmp_path)
    assert (gate.run, gate.always, gate.none) == ("", ("t/a.t",), False)


def test_this_repository_keeps_its_gate_unchanged_with_and_without_its_file(tmp_path):
    """Orkboard's own gate: its three critical tests, run by pytest; the project has the files, so deriving gives the same."""
    assert gate_config.read(ROOT).always == tuple(f"tests/test_{n}.py" for n in ("architecture", "board_alone", "updates"))
    assert gate_config.derive(ROOT).always == tuple(t for t in gate_config.CRITICAL_TESTS if (ROOT / t).is_file())     # no file: the same rule
    assert not gate_config.read(ROOT).custom and not gate_config.read(ROOT).none


def test_a_node_gate_runs_in_the_worktree_and_a_none_gate_runs_nothing(repo):
    (repo / "package.json").write_text(json.dumps({"scripts": {"test": "echo node-tests-ran"}}))
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "node")
    import shutil
    if shutil.which("npm"):
        run = gate_in(repo)
        assert run.ran and run.ok and run.command == "npm test" and "node-tests-ran" in run.out
    (repo / "package.json").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "plain")
    run = gate_in(repo)
    assert run.ran is False and "no tests ran" in run.out


# -- spec 107 §1.2: the derived gate, documents only, a run that could not run -------------------------------------------

def test_the_project_s_own_gate_is_derived_and_one_its_file_wrote_is_not(tmp_path):
    critical_tests(tmp_path)
    assert gate_config.read(tmp_path).derived is True
    toml(tmp_path, '[gate]\nrun = "make check"\n')
    assert gate_config.read(tmp_path).derived is False
    toml(tmp_path, "[other]\nx = 1\n")
    assert gate_config.read(tmp_path).derived is True
    toml(tmp_path, "[gate\nbroken")
    bad = gate_config.read(tmp_path)
    assert bad.derived is True and bad.error                                   # it ran as with no file
    for kind, make in (("node", lambda d: package(d, "jest")), ("python", lambda d: (d / "pyproject.toml").write_text("")),
                       ("none", lambda d: (d / "README.md").write_text("x"))):
        folder = tmp_path / kind
        folder.mkdir()
        make(folder)
        assert gate_config.read(folder).derived is True
    assert gate_config.Gate().derived is False and gate_config.Gate() == gate_config.Gate(derived=True)     # not part of what a gate is equal by


@pytest.mark.parametrize("files,only", [(["docs/a.md"], True), (["a.MD", "b.mdx", "c.markdown", "d.txt", "e.rst", "f.adoc"], True),
                                        (["docs/a.md", "src/a.js"], False), (["README"], False), ([], False), (["a.md.js"], False)])
def test_only_documents_are_documents(files, only):
    assert gate_config.docs_only(files) is only
