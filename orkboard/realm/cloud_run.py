"""The cloud run: the Board's second worker, a job on GitHub Actions (spec 137 D, decisions §244.6–9).

    config = cloud_run.read_config(root)                       # CloudConfig(secret, schedule, usd) · None: not set up (`[cloud_run]` in orkcraft.toml)
    cloud_run.write_config(root, config)                       # the table, on the person's yes; every other line kept
    text = cloud_run.workflow_text(config, board_config)       # `.github/workflows/orkboard.yml`, as it is written into the project
    cloud_run.write_workflow(root, config, board_config)       # only on the person's yes; a file of the person's own with that name is never overwritten
    got = cloud_run.run(root, state_dir, board_config, reading, me, usd=1.0)      # what `orkboard drive cloud-run` does

**What a cloud run does** (`run`): takes the lease as `kind: "cloud run"` (held by an awake computer: it ends at once, exit 0, *The computer has
the Board*); reads the inbox (the phone's goals and answers); carries each goal as far as **the reading** goes (the Orkmaster's route, Talk's
rounds, the sections, the plan) by the host's own clock until nothing is at work for `QUIET_S`, the time (`WORK_S`) or the ceiling in dollars (`usd`,
only with an API key) is used; **never the work**: a goal whose next step is a task waits, said on its tasks (*Planned: the work starts on your
computer*); pushes the Board; gives the lease back, whatever happened. It renews the lease every `board_lease.RENEW_S` while it reads.

`reading` is what the host gives (gui/cloud_run_host.py): `tree()`, `begin()` (nothing that is work can start), `take_inbox()`, `step()`, `busy()`,
`spent()`, `end()` (what is at work stopped, the pages committed). This module has no face and no model: git, the lease, and the words.

**The workflow** is written into the project only on the person's yes (Settings, `board.cloud_run_write`), as a file of the project, which the person
commits. It runs on `workflow_dispatch` and the chosen `schedule`, one run at a time (`concurrency: orkboard`), the job's timeout 30 minutes; its
first step asks the lease without installing anything (held: the rest is skipped, about a minute of Actions); it passes **only the secret the person
chose** to the run (both in the environment would make Claude Code take the API key first, silently paid by the token), and a missing secret fails
the run in plain words.
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from orkboard.realm import board_branch as bb, board_lease as bl, event_log, ideas

TABLE = "cloud_run"
WORKFLOW = ".github/workflows/orkboard.yml"
MARK = "# Written by Orkboard on your yes (spec 137 D). It is your file: commit it to the default branch. Orkboard rewrites it only when you change a cloud run setting."
SECRETS = {"oauth": "CLAUDE_CODE_OAUTH_TOKEN", "api_key": "ANTHROPIC_API_KEY"}
SECRET_WORDS = {"oauth": "Your Claude subscription", "api_key": "An API key"}
SCHEDULES = {"2h": ("Every 2 hours", "17 */2 * * *"), "never": ("Never", "")}      # a minute that is not :00, where GitHub is busiest
DEFAULT = ("oauth", "2h", 1.0)
INSTALL = "orkboard[gui] @ git+https://github.com/orkCraft/orkBoard"
TIMEOUT_MIN = 30
WORK_S = 24 * 60            # the reading stops at 24 minutes: the rest of the job's 30 is for the push and the lease given back
QUIET_S = 60.0              # nothing at work for this long: the reading is done
POLL_S = 2.0
PLANNED = "Planned: the work starts on your computer"
COMPUTER_HAS = "The computer has the Board"
CLOUD_HAS = "Another cloud run has the Board"
MINUTE = "About a minute of Actions when it finds nothing"
CEILING = "At most ${usd} a cloud run"
NEEDS_ORIGIN = "A cloud run reads the Board's branch from origin: the Board's remote must be named origin"
USD_WITH_KEY = "A ceiling in dollars is for an API key: a subscription has its week's limits instead"


class CloudRunError(Exception):
    """What could not be written or done, in words."""


@dataclass(frozen=True)
class CloudConfig:
    secret: str = DEFAULT[0]          # "oauth" (the subscription) · "api_key"
    schedule: str = DEFAULT[1]        # "2h" · "never"
    usd: float = DEFAULT[2]           # at most this many dollars a run, with an API key

    @property
    def secret_name(self) -> str:
        return SECRETS[self.secret]


def ceiling_words(usd: float) -> str:
    return CEILING.format(usd=f"{usd:g}")


# -- the settings, in orkcraft.toml ------------------------------------------------------------------------------------

def read_config(root: Path) -> CloudConfig | None:
    """`[cloud_run]` of `orkcraft.toml`; None with no file, a bad file or no table. A bad value is read as the default."""
    try:
        table = tomllib.loads((Path(root) / bb.FILE).read_text(encoding="utf-8")).get(TABLE)
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    if not isinstance(table, dict):
        return None
    return clean(table.get("secret"), table.get("schedule"), table.get("usd"))


def clean(secret: Any = None, schedule: Any = None, usd: Any = None) -> CloudConfig:
    """A config from what was given: a value that is not one of ours is the default; the ceiling is a number of dollars from 0.01 to 1000."""
    try:
        amount = float(usd) if usd is not None and not isinstance(usd, bool) else DEFAULT[2]
    except (TypeError, ValueError):
        amount = DEFAULT[2]
    if not (0.01 <= amount <= 1000):
        amount = DEFAULT[2]
    return CloudConfig(secret if secret in SECRETS else DEFAULT[0], schedule if schedule in SCHEDULES else DEFAULT[1], round(amount, 2))


def write_config(root: Path, config: CloudConfig) -> CloudConfig:
    """`[cloud_run]` written into `orkcraft.toml` (the person said yes): the table made or replaced, every other line kept. Raises OSError."""
    path = Path(root) / bb.FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    block = f'[{TABLE}]\nsecret = "{config.secret}"\nschedule = "{config.schedule}"\nusd = {config.usd:g}\n'
    pattern = re.compile(rf"^\[{TABLE}\][^\n]*\n(?:(?!\[)[^\n]*\n?)*", re.M)
    if pattern.search(text):
        text = pattern.sub(lambda m: block + ("\n" if m.group(0).endswith("\n\n") else ""), text, count=1)
    else:
        text += ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + block
    path.write_text(text, encoding="utf-8")
    return read_config(root) or config


# -- the workflow -------------------------------------------------------------------------------------------------------

LEASE_CHECK = '''\
          git fetch --quiet --depth=1 origin "+refs/heads/{branch}:refs/remotes/origin/{branch}" 2>/dev/null || {{
            echo "held=false" >> "$GITHUB_OUTPUT"
            echo "The Board's branch is not there yet: this run makes it."
            exit 0
          }}
          python3 - <<'PY'
          import datetime as dt, json, os, subprocess
          got = subprocess.run(["git", "show", "refs/remotes/origin/{branch}:lease.json"], capture_output=True, text=True)
          held, line = False, "Nobody holds the Board: this run takes it."
          if got.returncode == 0:
              try:
                  lease = json.loads(got.stdout)
                  until = dt.datetime.fromisoformat(str(lease["until"]))
                  if not lease.get("back") and dt.datetime.now(dt.timezone.utc) < until + dt.timedelta(seconds=60):
                      held = True
                      line = ("{computer_has}" if lease.get("kind") != "cloud run" else "{cloud_has}") + ": nothing to do this time."
              except (KeyError, ValueError, TypeError, AttributeError):
                  pass
          print(line)
          with open(os.environ["GITHUB_OUTPUT"], "a") as out:
              out.write("held=" + ("true" if held else "false") + "\\n")
          PY'''

SECRET_CHECK = '''\
          if [ -z "${name}" ]; then
            echo "::error::The secret {name} is not set for this repository, so the cloud run cannot read your goals. {how}"
            exit 1
          fi'''

HOW = {
    "oauth": 'Run "claude setup-token" on your computer, then add what it prints under Settings > Secrets and variables > Actions > New repository secret, named CLAUDE_CODE_OAUTH_TOKEN. Or choose an API key in Orkboard\'s settings.',
    "api_key": 'Add your API key under Settings > Secrets and variables > Actions > New repository secret, named ANTHROPIC_API_KEY. Or choose your subscription in Orkboard\'s settings.',
}


def workflow_text(config: CloudConfig, board: bb.BoardConfig | None = None) -> str:
    """The workflow file for these settings. Raises `CloudRunError` when the Board's remote is not origin (a runner's clone has only that one)."""
    board = board or bb.BoardConfig()
    if board.remote != "origin":
        raise CloudRunError(NEEDS_ORIGIN)
    name = config.secret_name
    cron = SCHEDULES[config.schedule][1]
    usd = f" --usd {config.usd:g}" if config.secret == "api_key" else ""
    lease = LEASE_CHECK.format(branch=board.branch, computer_has=COMPUTER_HAS, cloud_has=CLOUD_HAS)
    check = SECRET_CHECK.format(name=name, how=HOW[config.secret])
    schedule = f'  schedule:\n    - cron: "{cron}"\n' if cron else ""
    return f'''{MARK}
name: Orkboard cloud run
on:
  workflow_dispatch:
{schedule}concurrency:
  group: orkboard
  cancel-in-progress: false
permissions:
  contents: write
jobs:
  cloud-run:
    runs-on: ubuntu-latest
    timeout-minutes: {TIMEOUT_MIN}
    env:
      {name}: ${{{{ secrets.{name} }}}}
    steps:
      - name: Check out the project
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Ask who has the Board
        id: lease
        run: |
{lease}
      - name: Check the secret that pays
        if: steps.lease.outputs.held != 'true'
        run: |
{check}
      - uses: actions/setup-python@v5
        if: steps.lease.outputs.held != 'true'
        with:
          python-version: "3.12"
      - uses: actions/setup-node@v4
        if: steps.lease.outputs.held != 'true'
        with:
          node-version: "20"
      - name: Install Orkboard and Claude Code
        if: steps.lease.outputs.held != 'true'
        run: |
          pip install "{INSTALL}"
          npm install -g @anthropic-ai/claude-code
      - name: Read the goals
        if: steps.lease.outputs.held != 'true'
        run: |
          git config user.name "Orkboard"
          git config user.email "orkboard@localhost"
          orkboard drive cloud-run{usd}
'''


def workflow_path(root: Path) -> Path:
    return Path(root) / WORKFLOW


def workflow_state(root: Path) -> str:
    """`none` (no file), `ours` (written by Orkboard: it carries `MARK`) or `other` (the person's own file of that name)."""
    try:
        head = workflow_path(root).read_text(encoding="utf-8")
    except FileNotFoundError:
        return "none"
    except (OSError, UnicodeDecodeError):
        return "other"
    return "ours" if head.startswith(MARK) else "other"


def write_workflow(root: Path, config: CloudConfig, board: bb.BoardConfig | None = None) -> Path:
    """The workflow written into the project (never into a repository but the person's). A file of the person's own with that name stays: `CloudRunError`."""
    text = workflow_text(config, board)
    if workflow_state(root) == "other":
        raise CloudRunError(f"{WORKFLOW} is a file of your own: Orkboard does not overwrite it")
    path = workflow_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# -- the goals that wait for the work -----------------------------------------------------------------------------------

def mark_planned(state_dir: Path) -> list[str]:
    """The goals with a plan whose tasks wait for the work get the words on those tasks (*Planned: the work starts on your computer*; the runner clears
    them when it starts the task). The slugs, in order. Nothing of a goal that has no plan, or no task left to do."""
    out = []
    folder = Path(state_dir) / "ideas"
    for d in sorted(folder.iterdir()) if folder.is_dir() else []:
        slug = d.name
        try:
            plan = ideas.plan(state_dir, slug)
            if not plan or ideas.state(state_dir, slug)["state"] in ("done", "failed"):
                continue
            left = [t for t in plan.get("tasks", []) if isinstance(t, dict) and t.get("state") in ("waiting", "ready")]
            if not left:
                continue

            def words(p: dict) -> None:
                for t in p.get("tasks", []):
                    if isinstance(t, dict) and t.get("state") in ("waiting", "ready") and not t.get("note"):
                        t["note"] = PLANNED
            ideas.edit_plan(state_dir, slug, words)
            out.append(slug)
        except (OSError, ValueError):
            continue
    return out


# -- the run ---------------------------------------------------------------------------------------------------------------

@dataclass
class Result:
    code: int = 0                                  # the command's exit status
    lines: list[str] = field(default_factory=list)
    held: bool = False                             # the lease was taken
    stopped: str = ""                              # "quiet" (nothing left to read) · "time" · "ceiling" · "lost"
    inbox: dict = field(default_factory=dict)
    planned: list[str] = field(default_factory=list)
    given: bool = False
    spent: float = 0.0
    seconds: float = 0.0


def _said(root: Path, **fields: Any) -> None:
    try:
        event_log.record(root, event_log.CLOUD_RUN, **fields)
    except Exception:
        pass


def _inbox_line(got: dict) -> str:
    if got.get("why"):
        return f"The inbox could not be read: {got['why']}"
    parts = [f"{got.get('laid', 0)} goals laid"] if got.get("laid") else []
    if got.get("answered"):
        parts.append(f"{got['answered']} answers taken in")
    if got.get("errors") or got.get("answer_errors"):
        parts.append(f"{got.get('errors', 0) + got.get('answer_errors', 0)} could not be taken")
    return "The inbox: " + (", ".join(parts) if parts else "nothing waiting")


def run(root: Path, state_dir: Path, config: bb.BoardConfig, reading: Any, me: str, usd: float = 0.0, now: Callable[[], dt.datetime] | None = None,
        clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep, work_s: float = WORK_S, quiet_s: float = QUIET_S,
        poll_s: float = POLL_S, run: Callable = subprocess.run) -> Result:
    """One cloud run. Never raises: what went wrong is in `lines` and `code`. The lease is given back whatever happened (a failure to push it leaves it
    to run out by itself, ten minutes, and the run then ends with exit 1)."""
    root, state_dir = Path(root), Path(state_dir)
    now = now or (lambda: dt.datetime.now(dt.timezone.utc))
    out = Result()
    begun = clock()
    got = bl.take(root, state_dir, config, me, bl.CLOUD_RUN, now(), tree=reading.tree(), run=run)
    if not got.get("held"):
        if got.get("offline"):
            out.code, out.lines = 1, [f"The Board's branch could not be reached: {got.get('why') or 'no answer'}"]
        else:
            out.lines = [(CLOUD_HAS if got.get("kind") == bl.CLOUD_RUN else COMPUTER_HAS) + ": nothing to do this time."]
        return out
    out.held = True
    out.lines.append(f"This cloud run holds the Board ({got.get('files', 0)} files).")
    try:
        reading.begin()
        out.inbox = reading.take_inbox() or {}
        out.lines.append(_inbox_line(out.inbox))
        out.stopped = _read(root, state_dir, config, reading, me, usd, now, clock, sleep, work_s, quiet_s, poll_s, run, begun)
    except Exception as e:
        out.code = 1
        out.lines.append(f"The reading stopped: {' '.join(str(e).split())[:300] or type(e).__name__}")
    finally:
        try:
            reading.end()
        except Exception as e:
            out.lines.append(f"Its last calls could not be stopped: {' '.join(str(e).split())[:200]}")
        out.planned = [] if out.stopped == "lost" else mark_planned(state_dir)
        out.spent = _spent(reading)
        out.seconds = round(clock() - begun, 1)
        if out.stopped != "lost":
            back = bl.give_back(root, state_dir, config, me, bl.CLOUD_RUN, now(), tree=reading.tree(), run=run)
            out.given = bool(back.get("given"))
            if out.given:
                out.lines.append("The Board was pushed and given back.")
            else:
                out.code = 1
                out.lines.append(f"The Board could not be given back: {back.get('why') or 'another worker had it'}. The lease runs out by itself in ten minutes.")
    if out.stopped == "lost":
        out.code = 1
        out.lines.append("Another worker took the Board during this run: what this run read is kept aside on the runner, not pushed.")
    out.lines += _stopped_lines(out, usd)
    if out.planned:
        out.lines.append(f"{PLANNED}: {len(out.planned)} {'goal' if len(out.planned) == 1 else 'goals'}.")
    _said(root, taken=out.held, stopped=out.stopped, laid=int(out.inbox.get("laid") or 0), answered=int(out.inbox.get("answered") or 0),
          planned=len(out.planned), usd=round(out.spent, 2), seconds=out.seconds, given=out.given)
    return out


def _spent(reading: Any) -> float:
    try:
        return float(reading.spent())
    except Exception:
        return 0.0


def _stopped_lines(out: Result, usd: float) -> list[str]:
    return {"quiet": ["Nothing is left to read."],
            "time": [f"The reading stopped at {WORK_S // 60} minutes: the next run goes on."],
            "ceiling": [f"{ceiling_words(usd)} was reached (${out.spent:.2f}): the next run goes on."]}.get(out.stopped, [])


def _read(root, state_dir, config, reading, me, usd, now, clock, sleep, work_s, quiet_s, poll_s, run, begun) -> str:
    """The host's clock, until nothing is at work for `quiet_s`, the time or the ceiling is used; the lease renewed on its way."""
    renewed, quiet_since = clock(), None
    while True:
        if clock() - begun >= work_s:
            return "time"
        if usd and _spent(reading) >= usd:
            return "ceiling"
        reading.step()
        if reading.busy():
            quiet_since = None
        else:
            quiet_since = clock() if quiet_since is None else quiet_since
            if clock() - quiet_since >= quiet_s:
                return "quiet"
        if clock() - renewed >= bl.RENEW_S:
            renewed = clock()
            reading.flush()
            got = bl.renew(root, state_dir, config, me, bl.CLOUD_RUN, now(), tree=reading.tree(), run=run)
            if got.get("lost"):
                return "lost"
        sleep(poll_s)
