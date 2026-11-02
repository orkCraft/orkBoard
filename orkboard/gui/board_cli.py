"""`orkboard usage …` and `orkboard update …` (docs/specs/41-orkget.md §7): the machine's answer about usage stats and
crash reports, and the updates, from the terminal, as Orkline's `orkcraft usage` and `orkcraft update`. `orkboard measures` and
`orkboard trial` (docs/specs/124-the-brief-the-measures-and-the-trial.md B, C): how the leaders' arguing turned out in a project, read
from its own event log, and hypothesis H1's head-to-head tallied. `main` in gui/board_host.py hands them over; a folder named `usage`,
`update`, `measures` or `trial` opens as `orkboard ./usage`.

    run(["usage", "on", "--id", "<32 hex>"])     # the installer's yes, with the id it drew (install.sh)
    run(["update", "check"])                     # what is out, nothing installed
    run(["measures", "~/game", "--since", "2026-11-01"])   # the project's measures (realm/measures.py), `--json` as data
    run(["trial", "new", "h1.csv", "--tasks", "tasks.txt"])  # a CSV to fill, each way shown as A or B (realm/trial.py)
    run(["trial", "h1.csv"])                     # the tally and the verdict
    run(["import", "~/game", "--dry-run"])       # what of the project's own documents would be read in (realm/read_in.py, spec 126 B)
    run(["export", "~/game", "--to", "out"])     # the decisions, the brief and the journals written out in common formats (realm/write_out.py, spec 126 C)
    run(["steps-check", "--tool", "codex"])      # one small real task on that tool: which steps its card would show, from where (realm/steps_check.py, spec 129 H1.6)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orkboard import __version__, settings
from orkboard.core import updates, usage
from orkboard.realm import measures, trial

WORDS = ("usage", "update", "measures", "trial", "import", "export", "steps-check")

POLICY_WHAT = {
    "auto": "every update installs when Orkboard opens",
    "critical": "critical updates install when Orkboard opens; the others wait for `orkboard update` or the window",
    "ask": "nothing installs by itself; `orkboard update` or the window installs",
}


def run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="orkboard")
    sub = parser.add_subparsers(dest="word", required=True)
    usage_p = sub.add_parser("usage", help="Anonymous usage stats and crash reports: share them, stop, or see what is set")
    usage_p.add_argument("action", choices=("on", "off", "status"))
    usage_p.add_argument("--id", dest="install_id", default=None, metavar="HEX",
                         help="With on: the install id the installer drew (32 hex digits)")
    up_p = sub.add_parser("update", help="Install the latest version, see what is out, or say what installs by itself")
    up_p.add_argument("action", nargs="?", choices=("check", *updates.POLICIES), default=None,
                      help="check: only say what is out · auto | critical | ask: which updates install by themselves "
                           "when Orkboard opens (default: critical)")
    m_p = sub.add_parser("measures", help="How the leaders' arguing turned out in a project, from its own event log")
    m_p.add_argument("folder", nargs="?", default=".", help="The project's folder (default: this one)")
    m_p.add_argument("--since", default="", metavar="DAY", help="From this day on (YYYY-MM-DD)")
    m_p.add_argument("--until", default="", metavar="DAY", help="Before this day (YYYY-MM-DD)")
    m_p.add_argument("--json", action="store_true", help="The measures as data")
    t_p = sub.add_parser("trial", help="Hypothesis H1's head-to-head: a CSV to fill (new), or its tally and verdict")
    t_p.add_argument("what", nargs="+", metavar="ARG", help="new <file.csv> --tasks <tasks.txt> · <file.csv>")
    t_p.add_argument("--tasks", default=None, metavar="FILE", help="With new: the tasks, one a line")
    t_p.add_argument("--seed", type=int, default=None, help="With new: the draw of A and B, to make it again")
    t_p.add_argument("--json", action="store_true", help="The tally as data")
    i_p = sub.add_parser("import", help="Read a project's own decisions, specs and notes (ADRs, Spec Kit, Kiro, OpenSpec, BMAD, a memory bank…) into its journals")
    i_p.add_argument("folder", nargs="?", default=".", help="The project's folder (default: this one)")
    i_p.add_argument("--dry-run", action="store_true", help="Only say what would be read in")
    e_p = sub.add_parser("export", help="Write the project's decisions, brief and journals out in common formats (MADR, a memory bank, Markdown)")
    e_p.add_argument("folder", nargs="?", default=".", help="The project's folder (default: this one)")
    e_p.add_argument("--to", default="", metavar="DIR", help="Where to write (default: <folder>/.orkcraft/export)")
    e_p.add_argument("--as", dest="fmt", choices=("madr", "nygard"), default="madr", help="The decisions' format (default: madr)")
    s_p = sub.add_parser("steps-check", help="Run one small real task on an AI tool in a scratch folder and say which steps a card would show, from where")
    s_p.add_argument("--tool", required=True, choices=("claude", "codex", "agy"), help="The tool to check (it must be installed and signed in)")
    s_p.add_argument("--yes", action="store_true", help="Do not ask before spending a little of the tool's limit")
    args = parser.parse_args(argv)
    if args.word == "steps-check":
        from orkboard.realm import steps_check
        return steps_check.run(args.tool, args.yes)
    if args.word in ("import", "export"):
        return _read_or_write(args)
    if args.word == "usage":
        return _usage(args.action, args.install_id)
    if args.word == "measures":
        return _measures(args.folder, args.since, args.until, args.json)
    if args.word == "trial":
        return _trial(args.what, args.tasks, args.seed, args.json)
    return _update(args.action)


def _read_or_write(args) -> int:
    """`orkboard import` (realm/read_in.py `run_cli`) and `orkboard export` (realm/write_out.py `run_cli`): each answers (exit code, the lines to print)."""
    root = Path(args.folder).expanduser()
    if not root.is_dir():
        print(f"orkboard {args.word}: no folder {args.folder}", file=sys.stderr)
        return 2
    try:
        if args.word == "import":
            from orkboard.realm import read_in
            code, text = read_in.run_cli(root, dry=args.dry_run)
        else:
            from orkboard.realm import write_out
            code, text = write_out.run_cli(root, Path(args.to).expanduser() if args.to else None, args.fmt)
    except (ValueError, OSError) as e:
        print(f"orkboard {args.word}: {e}", file=sys.stderr)
        return 2
    print(text, file=sys.stdout if code == 0 else sys.stderr)
    return code


def _measures(folder: str, since: str, until: str, as_json: bool) -> int:
    root = Path(folder).expanduser()
    if not root.is_dir():
        print(f"orkboard measures: no folder {folder}", file=sys.stderr)
        return 2
    got = measures.of(root, since, until)
    print(json.dumps(got, indent=2) if as_json else measures.text(got))
    return 0


def _trial(what: list[str], tasks: str | None, seed: int | None, as_json: bool) -> int:
    try:
        if what[0] == "new":
            if len(what) != 2 or not tasks:
                print("orkboard trial: new <file.csv> --tasks <tasks.txt>", file=sys.stderr)
                return 2
            out = Path(what[1]).expanduser()
            if out.exists():
                print(f"orkboard trial: {out} is there already; name another file", file=sys.stderr)
                return 2
            names = [line for line in Path(tasks).expanduser().read_text(encoding="utf-8").splitlines() if line.strip()]
            trial.template(out, names, seed)
            print(f"{out}: {len(names)} tasks, two rows each; judge A and B blind, then fill accepted, changes, questions, minutes and tokens")
            return 0
        got = trial.tally(trial.read(Path(what[0]).expanduser()))
    except (ValueError, OSError) as e:
        print(f"orkboard trial: {e}", file=sys.stderr)
        return 2
    print(json.dumps(got, indent=2) if as_json else trial.text(got))
    return 0


def _usage(action: str, install_id: str | None = None) -> int:
    """One answer for this computer, for Orkline and Orkboard alike (`machine.usage`); `on --id` keeps the id the
    installer drew, so the install and the app's events are one install."""
    machine = settings.load()
    if install_id is not None and not usage.ID.fullmatch(install_id):
        print("orkboard usage: --id must be 32 hex digits", file=sys.stderr)
        return 2
    if action != "status":
        usage.share(machine, action == "on", install_id)
        settings.save(machine)
    said = {True: "on", False: "off", None: "not asked yet (off)"}[machine.usage]
    print(f"usage stats and crash reports: {said} (one answer for this computer)")
    if machine.usage and machine.install_id:
        print(f"install id: {machine.install_id}")
    if usage.blocked():
        print(f"nothing is collected here: {usage.blocked()}")
    print("what Orkboard sends: that it opened (with the AI tools on) and closed (how long, in buckets), and where in "
          "its own code something broke; never your code, prompts, paths or project names")
    return 0


def _update(action: str | None) -> int:
    machine = settings.load()
    if action in updates.POLICIES:
        machine.updates = action
        settings.save(machine)
    if action not in (None, "check"):
        print(f"updates: {machine.updates} — {POLICY_WHAT[machine.updates]}")
        return 0
    if updates.blocked():
        print(f"updates are off here: {updates.blocked()}")
        return 0
    try:
        found = updates.offer(updates.check(force=True, timeout=15.0).manifest)
    except Exception as e:
        sys.stderr.write(f"orkboard error: the list of updates cannot be read ({e})\n")
        return 1
    if found is None:
        print(f"Orkboard {__version__} is the latest")
        return 0
    kind = " — a critical update" if found.critical else " — a major update" if found.major else ""
    print(f"Orkboard {found.version} is out{kind} (you have {__version__})")
    for line in found.notes:
        print(f"  {line}")
    way = updates.method()
    if action == "check":
        print(f"install it: orkboard update ({way.describe()})" if way.can else way.why)
        return 0
    if not way.can:
        sys.stderr.write(f"orkboard error: {way.why}\n")
        return 1
    print(f"installing ({way.describe()})…")
    result = updates.install(way)
    updates.remember(result, found.version)
    if not result.ok:
        sys.stderr.write(f"orkboard error: the update did not install:\n{result.output}\n")
        return 1
    print(f"installed Orkboard {result.version or found.version}; open Orkboard again to run it")
    return 0
