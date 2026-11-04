"""The cloud run (realm/cloud_run.py, gui/cloud_run_host.py, `orkboard drive cloud-run`; spec 137 D, decisions §244.6–9): the settings in orkcraft.toml, the
workflow's text (its steps are run here, as a shell, on local clones), the run on two clones of one bare repository with a fake reading, the host's side
(the work never starts, the ceiling), and the command. Nothing is run against GitHub or an AI tool."""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from orkboard.realm import board_branch as bb, board_lease as bl, cloud_run as cr, event_log, ideas
from tests.test_board_branch import WIKI, FakeTree, git, make_clone, make_origin, put, seed_board

T0 = dt.datetime(2026, 11, 4, 12, 0, 0, tzinfo=dt.timezone.utc)
CFG = bb.BoardConfig()


# -- the settings -----------------------------------------------------------------------------------------------------

def test_the_settings_are_written_and_read_and_every_other_line_is_kept(tmp_path):
    toml = tmp_path / "orkcraft.toml"
    toml.write_text('[board]\nremote = "origin"\n\n[cloud_run]\nsecret = "oauth"\nschedule = "2h"\nusd = 1\n\n[journal]\ninbox = "x"\n')
    assert cr.read_config(tmp_path) == cr.CloudConfig("oauth", "2h", 1.0)
    cr.write_config(tmp_path, cr.CloudConfig("api_key", "never", 2.5))
    assert cr.read_config(tmp_path) == cr.CloudConfig("api_key", "never", 2.5)
    text = toml.read_text()
    assert text.count("[cloud_run]") == 1 and '[board]\nremote = "origin"' in text and '[journal]\ninbox = "x"' in text
    toml.write_text("")
    assert cr.read_config(tmp_path) is None
    cr.write_config(tmp_path, cr.CloudConfig())
    assert cr.read_config(tmp_path) == cr.CloudConfig("oauth", "2h", 1.0)


def test_a_value_that_is_not_ours_is_the_default():
    assert cr.clean("token", "hourly", "lots") == cr.CloudConfig()
    assert cr.clean("api_key", "never", 0) == cr.CloudConfig("api_key", "never", 1.0)
    assert cr.clean("api_key", None, True).usd == 1.0 and cr.clean(None, None, 5000).usd == 1.0
    assert cr.read_config(Path("/nonexistent")) is None


# -- the workflow's text ----------------------------------------------------------------------------------------------------

def test_the_workflow_runs_on_dispatch_and_the_schedule_one_at_a_time_for_at_most_thirty_minutes():
    text = cr.workflow_text(cr.CloudConfig())
    assert text.startswith(cr.MARK) and "name: Orkboard cloud run" in text
    assert "  workflow_dispatch:\n" in text and '    - cron: "17 */2 * * *"' in text
    assert "concurrency:\n  group: orkboard\n  cancel-in-progress: false" in text
    assert "timeout-minutes: 30" in text and "permissions:\n  contents: write" in text
    assert "orkboard drive cloud-run\n" in text and "--usd" not in text, "a subscription has no ceiling in dollars"
    never = cr.workflow_text(cr.CloudConfig(schedule="never"))
    assert "workflow_dispatch:" in never and "schedule:" not in never and "cron" not in never


def test_only_the_secret_that_pays_is_given_to_the_run_and_the_ceiling_goes_with_an_api_key():
    oauth, key = cr.workflow_text(cr.CloudConfig("oauth")), cr.workflow_text(cr.CloudConfig("api_key", usd=2))
    assert "secrets.CLAUDE_CODE_OAUTH_TOKEN" in oauth and "ANTHROPIC_API_KEY" not in oauth
    assert "secrets.ANTHROPIC_API_KEY" in key and "CLAUDE_CODE_OAUTH_TOKEN" not in key
    assert "orkboard drive cloud-run --usd 2\n" in key
    assert key.count("secrets.") == 1 and oauth.count("secrets.") == 1


def test_the_first_step_asks_the_lease_before_anything_is_installed_and_the_rest_is_skipped_when_held():
    text = cr.workflow_text(cr.CloudConfig())
    steps = [m.start() for m in re.finditer(r"^      - ", text, flags=re.M)]
    assert len(steps) == 7
    assert text.index("Ask who has the Board") < text.index("pip install") < text.index("npm install -g @anthropic-ai/claude-code") < text.index("orkboard drive cloud-run")
    assert text.index("Ask who has the Board") < text.index("actions/setup-python") and text.index("Ask who has the Board") < text.index("Check the secret that pays")
    assert text.count("if: steps.lease.outputs.held != 'true'") == 5
    assert "id: lease" in text and cr.COMPUTER_HAS in text


def test_the_workflow_says_no_orc_and_no_orchestration_and_names_no_model():
    for config in (cr.CloudConfig("oauth"), cr.CloudConfig("api_key", "never")):
        text = cr.workflow_text(config).lower()
        assert not re.search(r"\borc|orchestrat", text) and "opus" not in text and "sonnet" not in text


def test_a_remote_that_is_not_origin_is_refused_in_words():
    with pytest.raises(cr.CloudRunError, match="named origin"):
        cr.workflow_text(cr.CloudConfig(), bb.BoardConfig(remote="upstream"))
    assert cr.workflow_text(cr.CloudConfig(), bb.BoardConfig(branch="my/board")).count("my/board") >= 3


def step_script(text: str, name: str) -> str:
    """The `run: |` of the step called `name`, as the runner's shell gets it (the block's indentation removed)."""
    at = text.index(f"- name: {name}")
    block = text[text.index("run: |\n", at) + len("run: |\n"):]
    lines = []
    for line in block.splitlines():
        if line.strip() and not line.startswith("          "):
            break
        lines.append(line)
    return textwrap.dedent("\n".join(lines)) + "\n"


def run_step(script: str, cwd: Path, **env) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")}
    return subprocess.run(["bash", "-e", "-c", script], cwd=cwd, env={**base, **env}, capture_output=True, text=True)


@pytest.fixture
def world(tmp_path: Path):
    origin = make_origin(tmp_path)
    a, b = make_clone(origin, tmp_path / "a"), make_clone(origin, tmp_path / "b")
    return origin, a, b


def test_the_lease_step_runs_as_a_shell_and_says_who_holds_the_board(world, tmp_path):
    origin, a, b = world
    script = step_script(cr.workflow_text(cr.CloudConfig()), "Ask who has the Board")
    out = tmp_path / "out"

    def ask() -> tuple[str, str]:
        out.write_text("")
        done = run_step(script, b, GITHUB_OUTPUT=str(out))
        assert done.returncode == 0, done.stderr
        return out.read_text().strip(), done.stdout.strip()

    assert ask() == ("held=false", "The Board's branch is not there yet: this run makes it.")
    seed_board(a / ".orkcraft")
    assert bl.take(a, a / ".orkcraft", CFG, "my-laptop", "computer", dt.datetime.now(dt.timezone.utc), wiki_rel=WIKI)["held"]
    held = ask()
    assert held[0] == "held=true" and held[1] == f"{cr.COMPUTER_HAS}: nothing to do this time."
    assert bl.give_back(a, a / ".orkcraft", CFG, "my-laptop", "computer", dt.datetime.now(dt.timezone.utc), wiki_rel=WIKI)["given"]
    assert ask() == ("held=false", "Nobody holds the Board: this run takes it.")
    assert bl.take(a, a / ".orkcraft", CFG, "a cloud run", "cloud run", dt.datetime.now(dt.timezone.utc), wiki_rel=WIKI)["held"]
    assert ask()[1] == f"{cr.CLOUD_HAS}: nothing to do this time."
    old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)
    assert bl.renew(a, a / ".orkcraft", CFG, "my-laptop", "cloud run", old, wiki_rel=WIKI)["held"] is not None
    assert ask()[0] == "held=false", "a lease that ran out is not held"


def test_a_missing_secret_fails_the_run_in_plain_words_and_a_set_one_goes_on(tmp_path):
    for config, name in ((cr.CloudConfig("oauth"), "CLAUDE_CODE_OAUTH_TOKEN"), (cr.CloudConfig("api_key"), "ANTHROPIC_API_KEY")):
        script = step_script(cr.workflow_text(config), "Check the secret that pays")
        missing = run_step(script, tmp_path)
        assert missing.returncode == 1
        words = missing.stdout
        assert f"::error::The secret {name} is not set for this repository, so the cloud run cannot read your goals." in words
        assert "Settings > Secrets and variables > Actions" in words and name in words
        assert run_step(script, tmp_path, **{name: "x"}).returncode == 0
    assert "claude setup-token" in run_step(step_script(cr.workflow_text(cr.CloudConfig("oauth")), "Check the secret that pays"), tmp_path).stdout


def test_the_workflow_is_written_into_the_project_only_and_a_file_of_the_persons_own_stays(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    assert cr.workflow_state(project) == "none"
    path = cr.write_workflow(project, cr.CloudConfig())
    assert path == project / ".github" / "workflows" / "orkboard.yml" and path.read_text() == cr.workflow_text(cr.CloudConfig())
    assert cr.workflow_state(project) == "ours"
    cr.write_workflow(project, cr.CloudConfig("api_key"))                   # ours: rewritten on a new yes
    assert "secrets.ANTHROPIC_API_KEY" in path.read_text()
    path.write_text("name: mine\n")
    assert cr.workflow_state(project) == "other"
    with pytest.raises(cr.CloudRunError, match="file of your own"):
        cr.write_workflow(project, cr.CloudConfig())
    assert path.read_text() == "name: mine\n"
    here = Path(__file__).resolve().parents[1]
    assert not (here / ".github" / "workflows" / "orkboard.yml").exists(), "the workflow is the project's file, never this repository's"


# -- the run, on two clones of one bare repository ------------------------------------------------------------------------

class Reading:
    """What the host gives a run, in a fake: a clock the test moves, goals laid in the state folder, a number of steps at work."""

    def __init__(self, state: Path, work: int = 0, per_step_usd: float = 0.0, read=None) -> None:
        self.state, self.work, self.per, self.log, self.tick, self.usd, self.read = state, work, per_step_usd, [], 0, 0.0, read
        self.fake_tree = FakeTree()
        self.inbox = {"laid": 1, "answered": 1}

    def tree(self):
        return self.fake_tree

    def begin(self) -> None:
        self.log.append("begin")

    def take_inbox(self) -> dict:
        self.log.append("inbox")
        put(self.state, "ideas/from-phone/state.json", json.dumps({"state": "plan"}))
        put(self.state, "ideas/from-phone/plan.json", json.dumps({"tasks": [{"id": "t1", "state": "waiting"}, {"id": "t2", "state": "merged"}]}))
        return self.inbox

    def step(self) -> None:
        self.tick += 1
        self.usd += self.per
        if self.read:
            self.read(self)

    def busy(self) -> bool:
        return self.tick <= self.work

    def spent(self) -> float:
        return self.usd

    def flush(self) -> None:
        self.log.append("flush")

    def end(self) -> None:
        self.log.append("end")


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += s


def go(host_root: Path, reading: Reading, clock: Clock | None = None, **kw) -> cr.Result:
    clock = clock or Clock()
    return cr.run(host_root, host_root / ".orkcraft", CFG, reading, "cloud run on a runner", clock=clock, sleep=clock.sleep,
                  now=lambda: T0 + dt.timedelta(seconds=clock.t), **kw)


def remote_lease(origin: Path) -> dict:
    return json.loads(git(origin, "show", "refs/heads/orkboard/board:lease.json"))


def test_a_computer_that_holds_the_board_ends_the_run_at_once_with_exit_zero(world):
    origin, a, b = world
    seed_board(a / ".orkcraft")
    assert bl.take(a, a / ".orkcraft", CFG, "my-laptop", "computer", T0, wiki_rel=WIKI)["held"]
    reading = Reading(b / ".orkcraft")
    got = go(b, reading)
    assert got.code == 0 and not got.held and got.lines == [f"{cr.COMPUTER_HAS}: nothing to do this time."]
    assert reading.log == [], "nothing was read: not the inbox, not a goal"
    assert remote_lease(origin)["by"] == "my-laptop" and remote_lease(origin)["kind"] == "computer"


def test_a_free_board_is_taken_read_pushed_and_given_back_and_the_computer_then_has_the_goals(world):
    origin, a, b = world
    reading = Reading(b / ".orkcraft", work=3)
    got = go(b, reading, quiet_s=10)
    assert got.code == 0 and got.held and got.stopped == "quiet" and got.given
    assert reading.log == ["begin", "inbox", "end"] and reading.tick > 3
    assert got.lines[0].startswith("This cloud run holds the Board") and "The inbox: 1 goals laid, 1 answers taken in" in got.lines
    assert "Nothing is left to read." in got.lines and "The Board was pushed and given back." in got.lines
    lease = remote_lease(origin)
    assert lease["kind"] == "cloud run" and lease["back"] is True
    # the goal the run read is on the branch, with the words that its work waits
    plan = json.loads(git(origin, "show", "refs/heads/orkboard/board:ideas/from-phone/plan.json"))
    assert [t.get("note") for t in plan["tasks"]] == [cr.PLANNED, None] and got.planned == ["from-phone"]
    assert f"{cr.PLANNED}: 1 goal." in got.lines
    # the computer that wakes takes the Board and sees it
    assert bl.take(a, a / ".orkcraft", CFG, "my-laptop", "computer", T0 + dt.timedelta(hours=1), wiki_rel=WIKI)["held"]
    assert json.loads((a / ".orkcraft" / "ideas/from-phone/plan.json").read_text())["tasks"][0]["note"] == cr.PLANNED
    events = [r["event"] for r in event_log.read(b)]
    assert {"board_taken", "board_given_back", "cloud_run"} <= set(events)
    ended = [r for r in event_log.read(b) if r["event"] == "cloud_run"][-1]
    assert ended["stopped"] == "quiet" and ended["planned"] == 1 and ended["given"] is True and "text" not in ended


def test_the_ceiling_in_dollars_stops_the_reading_and_says_so(world):
    origin, a, b = world
    reading = Reading(b / ".orkcraft", work=1000, per_step_usd=0.4)
    got = go(b, reading, usd=1.0)
    assert got.stopped == "ceiling" and got.given and got.code == 0 and got.spent == pytest.approx(1.2)
    assert "At most $1 a cloud run was reached ($1.20): the next run goes on." in got.lines
    assert remote_lease(origin)["back"] is True


def test_no_ceiling_means_the_time_stops_it_and_the_lease_is_renewed_on_the_way(world):
    origin, a, b = world
    reading = Reading(b / ".orkcraft", work=100000)
    got = go(b, reading, work_s=400, poll_s=10)
    assert got.stopped == "time" and got.given and any("stopped at 24 minutes" in line for line in got.lines)
    assert reading.log.count("flush") >= 2, "the Board was flushed and the lease renewed every 180 s"
    pushed = [r for r in event_log.read(b) if r["event"] == "board_pushed"]
    assert len(pushed) >= 3                                         # the take, a renewal or two, the give back


def test_another_worker_that_takes_the_board_meanwhile_ends_the_run_without_giving_back(world):
    origin, a, b = world
    reading = Reading(b / ".orkcraft", work=100000)

    def other_takes(r: Reading) -> None:
        if r.tick == 5 and not r.log.count("stolen"):
            r.log.append("stolen")
            lease = {"v": 1, "by": "my-laptop", "kind": "computer", "until": (T0 + dt.timedelta(hours=2)).isoformat(), "at": T0.isoformat()}
            tip = bb.fetch(a, CFG)["tip"]
            files = bb.files_at(a, bb.REMOTE_REF)
            files[bb.LEASE] = json.dumps(lease).encode()
            made = bb.commit(a, a / ".orkcraft", CFG, files, "board: taken by my-laptop", tip)
            assert bb.push(a, CFG, made)["ok"]

    reading.read = other_takes
    got = go(b, reading, poll_s=60)                                 # a step is a minute: the renewal comes at the fourth
    assert got.stopped == "lost" and got.code == 1 and not got.given
    assert any("Another worker took the Board during this run" in line for line in got.lines)
    assert remote_lease(origin)["by"] == "my-laptop", "this run never wrote over it"


def test_a_board_that_cannot_be_reached_is_a_failed_run_in_words(tmp_path):
    origin = make_origin(tmp_path)
    b = make_clone(origin, tmp_path / "b")
    git(b, "remote", "set-url", "origin", str(tmp_path / "nowhere.git"))
    got = go(b, Reading(b / ".orkcraft"))
    assert got.code == 1 and got.lines[0].startswith("The Board's branch could not be reached:")


def test_a_reading_that_breaks_still_gives_the_board_back(world):
    origin, a, b = world

    def boom(r: Reading) -> None:
        raise RuntimeError("the tool said no")
    got = go(b, Reading(b / ".orkcraft", read=boom))
    assert got.code == 1 and "The reading stopped: the tool said no" in got.lines and got.given
    assert remote_lease(origin)["back"] is True


def test_mark_planned_writes_the_words_on_the_tasks_that_wait_and_nothing_else(tmp_path):
    state = tmp_path / ".orkcraft"
    put(state, "ideas/a/state.json", json.dumps({"state": "working"}))
    put(state, "ideas/a/plan.json", json.dumps({"tasks": [{"id": "1", "state": "ready"}, {"id": "2", "state": "running"}, {"id": "3", "state": "waiting", "note": "kept"}]}))
    put(state, "ideas/b/state.json", json.dumps({"state": "done"}))
    put(state, "ideas/b/plan.json", json.dumps({"tasks": [{"id": "1", "state": "waiting"}]}))
    put(state, "ideas/c/state.json", json.dumps({"state": "ready"}))
    put(state, "ideas/d/state.json", json.dumps({"state": "plan"}))
    put(state, "ideas/d/plan.json", json.dumps({"tasks": [{"id": "1", "state": "merged"}]}))
    assert cr.mark_planned(state) == ["a"]
    assert [t.get("note") for t in ideas.plan(state, "a")["tasks"]] == [cr.PLANNED, None, "kept"]
    assert "note" not in ideas.plan(state, "b")["tasks"][0] and ideas.plan(state, "c") is None


# -- the host's side -----------------------------------------------------------------------------------------------------------

@pytest.fixture
def clone_host(world, tmp_path, monkeypatch):
    """A real Orkboard host on a clone with `[board]` and an inbox, the AI tools hidden."""
    from orkboard import tools
    from orkboard.gui.board_host import Orkboard
    origin, a, b = world
    (b / "orkcraft.toml").write_text('[board]\nremote = "origin"\nbranch = "orkboard/board"\n[journal]\ninbox = "orkboard/inbox"\n')
    monkeypatch.setattr(tools, "detect", lambda *x, **k: [])
    monkeypatch.setattr(tools, "detect_others", lambda *x, **k: [])
    host = Orkboard(b)
    yield origin, a, b, host
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_work_cannot_start_in_a_cloud_run_and_the_words_say_where_it_does(clone_host):
    from orkboard.gui.cloud_run_host import CloudReading
    from orkboard.gui.ideas_args import IdeasError
    _, _, _, host = clone_host
    reading = CloudReading(host.project.root, 0.0, host)
    reading.begin()
    ideas_ = host.project.ideas
    assert ideas_.runner() is None
    with pytest.raises(IdeasError, match="Planned: the work starts on your computer"):
        ideas_.runner(need=True)
    assert not ideas_.running()


def test_the_ceiling_closes_the_keepers_budget_once_the_run_has_spent_it(clone_host):
    from orkboard.gui.cloud_run_host import CloudReading
    _, _, _, host = clone_host
    reading = CloudReading(host.project.root, 1.0, host)
    spent = {"usd": 0.2}
    reading.spent = lambda: spent["usd"]
    reading.begin()
    keeper = host.project.ideas.keeper
    assert keeper.budget_ok() is True
    spent["usd"] = 1.0
    assert keeper.budget_ok() is False, "the next call does not start"


def test_the_inbox_is_taken_by_the_reading_goals_laid_and_nothing_started(clone_host):
    from orkboard.gui.cloud_run_host import CloudReading
    from tests.test_remote_inbox import drop, goal_file
    origin, a, b, host = clone_host
    phone = make_clone(origin, b.parent / "phone")
    party = ideas.add_track(host.project.ideas.root(), "Chips")
    drop(phone, {"inbox/phone1/01JC0000000000000001.json": json.dumps(goal_file("01JC0000000000000001", "Make the table sort", party=party))})
    reading = CloudReading(host.project.root, 0.0, host)
    reading.begin()
    host.project.ideas.keeper.budget_ok = lambda: False          # the keeper makes no call in this test
    got = reading.take_inbox()
    assert got["read"] == 1 and got["taken"] == 1 and got["laid"] == 1 and not got["why"]
    assert reading.step() is None and reading.busy() is False
    assert any(json.loads(f.read_text()).get("inbox_id") == "01JC0000000000000001" for f in (b / ".orkcraft" / "ideas").glob("*/state.json"))


# -- the command ------------------------------------------------------------------------------------------------------------------

def test_the_command_does_nothing_where_the_board_is_not_kept_in_the_repository(fake_repo):
    from orkboard.gui import drive
    out = io.StringIO()
    from orkboard.gui import cloud_run_host
    assert cloud_run_host.command(fake_repo, 1.0, out) == 0
    assert "Turn on \"Keep the Board in the repository\"" in out.getvalue()
    assert drive.main(["cloud-run", "--folder", str(fake_repo)]) == 0


def test_the_command_runs_end_to_end_on_a_local_bare_repository(clone_host, capsys, monkeypatch):
    from orkboard.gui import cloud_run_host
    origin, a, b, host = clone_host
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    host.project.ideas.keeper.stop_all = lambda: None
    out = io.StringIO()
    code = cloud_run_host.command(b, 5.0, out, host=host, quiet_s=0.0, poll_s=0.0, work_s=60)
    text = out.getvalue()
    assert code == 0, text
    assert cr.USD_WITH_KEY in text and "The Board was pushed and given back." in text and "The inbox: nothing waiting" in text
    assert remote_lease(origin)["back"] is True and remote_lease(origin)["kind"] == "cloud run"
