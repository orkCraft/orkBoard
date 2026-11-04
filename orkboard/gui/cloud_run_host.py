"""The host's side of a cloud run (spec 137 D, decisions §244.6–7): `orkboard drive cloud-run`.

    cloud_run_host.command(root, usd=1.0, out=sys.stdout)     # the whole command: its lines on `out`, the exit status

A host with no window and no faces, made as `drive start` makes it, but its clock is only the Board's own (`Ideas.tick`: the keeper, the route, Talk);
the updates, repair, Operations and the phone's pushes are not ticked. `CloudReading` is what `realm/cloud_run.py` asks of it. **The work cannot
start here**: the project's runner is never made (`Ideas._runner_error`), so a task waits and the command that would start it is refused in the words
*Planned: the work starts on your computer*. A ceiling in dollars (`usd`) stops the keeper's next call once what this run spent has reached it.
"""
from __future__ import annotations

import datetime as dt
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any

from orkboard.realm import board_branch, cloud_run, remote_inbox, remote_journal

NO_BOARD = ("This project does not keep the Board in its repository: nothing for a cloud run to do. "
            "Turn on \"Keep the Board in the repository\" in Orkboard's settings first.")


class CloudReading:
    def __init__(self, root: Path, usd: float = 0.0, host: Any = None) -> None:
        if host is None:
            from orkboard.gui.board_host import Orkboard
            host = Orkboard(root)
        self.host, self.usd = host, usd
        self.p = host.project
        if self.p is None:
            raise cloud_run.CloudRunError(f"{root} could not be opened as a project")
        self.me = f"cloud run on {socket.gethostname() or 'a runner'}"

    def tree(self) -> Any:
        ideas = self.p.ideas
        try:
            ideas.root()
            return ideas._tree(ideas.wiki())
        except Exception:
            return None

    def begin(self) -> None:
        ideas = self.p.ideas
        ideas._runner = None
        ideas._runner_error = cloud_run.PLANNED               # `runner()` is None, `runner(need=True)` raises these words: no task starts here
        if self.usd:
            ideas.keeper.budget_ok = lambda: self.spent() < self.usd

    def take_inbox(self) -> dict:
        config = remote_journal.read_config(self.p.root)
        if config is None or not config.inbox:
            return {"why": "", "laid": 0}
        pj, p = self.host.phone_journal, self.p
        return remote_inbox.take(p.root, Path(p.ideas.state_dir), config, pj.context(p), pj.lay(p), pj.find(p), self.me, dt.datetime.now(),
                                 pages=p.ideas.root(False), needs=frozenset(), force=True, apply=pj.apply(p))

    def step(self) -> None:
        self.p.ideas.tick(time.monotonic())

    def busy(self) -> bool:
        return bool(self.p.ideas.keeper.at_work())

    def spent(self) -> float:
        telemetry = self.host.telemetry
        if telemetry is None:
            return 0.0
        self.host.spend = telemetry.refresh()
        return float(self.host.spend.spent_usd)

    def flush(self) -> None:
        self.p.ideas.tree_flush(force=True)

    def end(self) -> None:
        """What is at work stopped (a call raises), the pages committed, the phone's journal sent with what was taken."""
        ideas = self.p.ideas
        try:
            ideas.keeper.stop_all()
            end = time.monotonic() + 60
            while ideas.keeper.at_work() and time.monotonic() < end:
                time.sleep(0.5)
        finally:
            self.flush()
        config = remote_journal.read_config(self.p.root)
        if config is not None:
            try:
                remote_journal.send(self.p.root, Path(ideas.state_dir), config, dt.datetime.now(), pages=ideas.root(False))
            except Exception:
                pass

    def close(self) -> None:
        try:
            self.host.close()
        except Exception:
            pass


def command(root: Path, usd: float = 0.0, out: Any = None, host: Any = None, **times: Any) -> int:
    """`orkboard drive cloud-run`: the lines on `out`, the exit status (0: it ended well or had nothing to do; 1: it could not be done)."""
    out = out or sys.stdout
    root = Path(root).resolve()
    config = board_branch.read_config(root)
    if config is None:
        out.write(NO_BOARD + "\n")
        return 0
    for key in ("ORKCRAFT_MODEL_LIST", ):
        os.environ.setdefault(key, "0")
    os.environ.setdefault("ORKCRAFT_NO_UPDATE", "1")
    if usd and not os.environ.get("ANTHROPIC_API_KEY"):
        out.write(cloud_run.USD_WITH_KEY + ".\n")
        usd = 0.0
    try:
        reading = CloudReading(root, usd, host)
    except Exception as e:
        out.write(f"The cloud run could not start: {' '.join(str(e).split())[:300]}\n")
        return 1
    try:
        got = cloud_run.run(root, Path(reading.p.ideas.state_dir), config, reading, reading.me, usd, **times)
    finally:
        reading.close()
    for line in got.lines:
        out.write(line + "\n")
    return got.code
