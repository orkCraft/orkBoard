"""Settings' switch for the Board's branch (spec 137 E, decisions §244.1, §244.11, §244.14).

    board_switch.commands(host)      # board.switch (what Settings shows) · board.turn_on · board.not_now (the desktop's Settings; not a phone's)

**Written only by the person's yes.** *Turn it on* asks `board_branch.private_check` (a public GitHub repository is refused in words, a
remote not on GitHub goes on with the line that it must be private), then writes `[board]` into `orkcraft.toml` (`board_branch.turn_on`);
the host's tick (gui/board_sync.py) takes it from there. *Not now* is remembered in `<state_dir>/board_asked.json` and the switch stays in
Settings, with *Turn it on* alone. Once on, the switch says so, and says in words when a cloud run or another computer holds the Board or
when changes were kept aside (`board_sync.status`).

**The cloud run's settings** (spec 137 D, decisions §244.6–8) sit under the switch once it is on (`switch()["cloud"]`): which secret pays, the schedule, the
ceiling in dollars of an API key's calls, and *Write the workflow into this project* (`board.cloud_write`): the one yes that writes `[cloud_run]` into
`orkcraft.toml` and `.github/workflows/orkboard.yml` into the project (realm/cloud_run.py). Choosing in the selects writes nothing; the workflow is the
person's file, committed by them; a file of that name that is not ours is never overwritten.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from orkboard.gui import board_sync
from orkboard.realm import board_branch, board_lease, cloud_run, plumbing

ASKED_FILE = "board_asked.json"
LABEL = "Keep the Board in the repository"
LINE = ("Its pages and its state go to a branch of their own, orkboard/board. Secrets, sign-ins and logs stay on this computer. "
        "The repository must be private.")
ON_LINE = "The Board is kept on {branch} on {remote}."
CLOUD_LABEL = "Cloud run"
CLOUD_LINE = ("While your computer is off, a cloud run on GitHub Actions reads your goals and takes your answers in. It never does the work: "
              + cloud_run.PLANNED + ".")
SECRET_LINES = {"oauth": "Your Claude subscription pays: a cloud run shares this week's limits with your computer. The secret is CLAUDE_CODE_OAUTH_TOKEN.",
                "api_key": "An API key pays, by the token. The secret is ANTHROPIC_API_KEY."}
WRITE = "Write the workflow into this project"
WRITE_LINE = ("Writes " + cloud_run.WORKFLOW + " and the settings above into this project. You commit it to your default branch: until then nothing runs. "
              "The secret is yours to add under Settings > Secrets and variables > Actions on GitHub.")
WRITTEN = "Written to " + cloud_run.WORKFLOW + ". Commit it to your default branch for the cloud run to start."
RUNS_A_DAY = {"2h": 12}

http_status: Callable[[str], int] = board_branch.http_status       # tests put a fake here


def _asked(state_dir: Path) -> bool:
    try:
        data = json.loads((Path(state_dir) / ASKED_FILE).read_text(encoding="utf-8"))
        return isinstance(data, dict) and data.get("answer") == "no"
    except (OSError, ValueError):
        return False


def _remember(state_dir: Path, answer: str) -> None:
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    (Path(state_dir) / ASKED_FILE).write_text(json.dumps({"answer": answer, "at": dt.datetime.now().isoformat(timespec="seconds")}), encoding="utf-8")


def has_remote(root: Path, remote: str = "origin", run: Callable = subprocess.run) -> bool:
    try:
        plumbing.git(root, run, plumbing.env(), "remote", "get-url", remote)
        return True
    except Exception:
        return False


def _clock(iso: str) -> str:
    try:
        return dt.datetime.fromisoformat(iso).astimezone().strftime("%H:%M")
    except (ValueError, TypeError):
        return "the last push"


def cloud(root: Path, board: board_branch.BoardConfig) -> dict:
    """What Settings shows of the cloud run: the saved settings (the defaults while none), the words of each choice, and whether the workflow is in the project
    (`none` · `ours` · `other`, a file of the person's own) and is what these settings would write (`current`)."""
    saved = cloud_run.read_config(root)
    config = saved or cloud_run.CloudConfig()
    state = cloud_run.workflow_state(root)
    try:
        current = state == "ours" and saved is not None and cloud_run.workflow_path(root).read_text(encoding="utf-8") == cloud_run.workflow_text(config, board)
    except (OSError, cloud_run.CloudRunError):
        current = False
    return {"label": CLOUD_LABEL, "line": CLOUD_LINE, "set_up": saved is not None, "secret": config.secret, "schedule": config.schedule, "usd": config.usd,
            "secrets": [{"id": k, "label": cloud_run.SECRET_WORDS[k], "name": v, "line": SECRET_LINES[k]} for k, v in cloud_run.SECRETS.items()],
            "schedules": [{"id": k, "label": label} for k, (label, _) in cloud_run.SCHEDULES.items()],
            "minute": cloud_run.MINUTE, "ceiling": cloud_run.ceiling_words(config.usd), "usd_line": cloud_run.USD_WITH_KEY,
            "runs_a_day": RUNS_A_DAY.get(config.schedule, 0), "workflow": state, "current": current, "write": WRITE, "write_line": WRITE_LINE,
            "path": cloud_run.WORKFLOW}


class BoardSwitch:
    def __init__(self, host: Any) -> None:
        self.host = host

    def commands(self) -> dict[str, Callable[[dict], Any]]:
        return {"board.switch": lambda a: self.switch(), "board.turn_on": lambda a: self.turn_on(), "board.not_now": lambda a: self.not_now(),
                "board.cloud_write": self.cloud_write}

    def _project(self):
        p = self.host.project
        if p is None:
            raise ValueError("No project is open")
        return p

    def switch(self) -> dict:
        """`{show, on, asked, label, line, status, held, aside}` for the shown project. Nothing is shown with no project or no remote to keep it on."""
        p = self.host.project
        out: dict = {"show": False, "on": False, "asked": False, "label": LABEL, "line": LINE, "status": "", "held": "", "aside": ""}
        if p is None:
            return out
        config = board_branch.read_config(p.root)
        if config is not None:
            out.update(show=True, on=True, status=ON_LINE.format(branch=config.branch, remote=config.remote))
            sync = getattr(self.host, "board_sync", None)
            seen = sync.status(p) if sync is not None else {}
            held = seen.get("board_held")
            if held:
                out["held"] = board_sync.CLOUD_HELD if held.get("kind") == board_lease.CLOUD_RUN else board_sync.COMPUTER_HELD
            aside = seen.get("board_aside")
            if aside:
                out["aside"] = board_sync.ASIDE_LINE.format(since=_clock(str(aside.get("since") or "")))
            out["cloud"] = cloud(p.root, config)
            return out
        if has_remote(p.root):
            out.update(show=True, asked=_asked(Path(p.ideas.state_dir)))
        return out

    def turn_on(self) -> dict:
        p = self._project()
        config = board_branch.BoardConfig()
        if board_branch.read_config(p.root) is not None:
            return {"ok": True, "line": ""}
        ok, line = board_branch.private_check(p.root, config, http_status)
        if not ok:
            raise ValueError(line)
        try:
            config = board_branch.turn_on(p.root, config)
        except OSError as e:
            raise ValueError(f"orkcraft.toml could not be written: {e}") from None
        _remember(Path(p.ideas.state_dir), "yes")
        return {"ok": True, "remote": config.remote, "branch": config.branch, "line": line}

    def cloud_write(self, args: dict) -> dict:
        """The person's yes to the cloud run: the settings in `orkcraft.toml` and the workflow in the project. A file of that name that is not ours stays."""
        p = self._project()
        board = board_branch.read_config(p.root)
        if board is None:
            raise ValueError("Turn on \"Keep the Board in the repository\" first")
        config = cloud_run.clean(args.get("secret"), args.get("schedule"), args.get("usd"))
        try:
            cloud_run.write_workflow(p.root, config, board)
            cloud_run.write_config(p.root, config)
        except cloud_run.CloudRunError as e:
            raise ValueError(str(e)) from None
        except OSError as e:
            raise ValueError(f"The workflow could not be written: {e}") from None
        return {"ok": True, "line": WRITTEN, "path": cloud_run.WORKFLOW, "cloud": cloud(p.root, board)}

    def not_now(self) -> dict:
        _remember(Path(self._project().ideas.state_dir), "no")
        return {"ok": True}


def commands(host: Any) -> dict[str, Callable[[dict], Any]]:
    host.board_switch = BoardSwitch(host)
    return host.board_switch.commands()
