"""`orkboard init | goal … | gate | check` (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md part E.1; decisions §255.9): the Board worked from a terminal, on the checkout the word is run in.

    run(["init", "--ci"])                         # the rules (part C) and the CI step written into the working tree; refused in a public GitHub repository
    run(["goal", "list", "--phase", "work"])      # slug, phase, asks, taken, title
    run(["goal", "add", "Add a score board", "--party", "tech", "--by", "codex"])     # a page in `new`, `by: codex`
    run(["goal", "take", "add-a-score-board", "--by", "codex"])                       # one taker at a time (realm/goal_take.py)
    run(["goal", "phase", "add-a-score-board", "talk"])                               # a known phase: one step on, or any step back
    run(["goal", "ask", "add-a-score-board", "Which store first?", "--choices", "App Store/Google Play", "--pick", "App Store"])
    run(["goal", "answer", "add-a-score-board", "1", "App Store"])                    # the person's words, heard in the chat (question 1 is the first)
    run(["gate", "--base", "main", "--record", "add-a-score-board"])                   # the project's gate on this checkout; `--record` writes `gate` into the page
    run(["check"])                                # realm/board_check.py: every fault, in words

No app runs, no model is called, and **nothing is committed**: a word writes the working tree (the Board's pages, the rules) and the person or the tool commits. Exit 0 done, 1 refused (its words on
stderr), 2 a bad call. The Board's folder is found as the app finds it (`board_check.wiki_of`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import threading
from pathlib import Path

from orkboard.realm import agent_rules, agent_rules_text, board_check, goal_phase, goal_take, idea_questions, ideas
from orkboard.realm.idea_page import Page

PHASE_WORDS = ", ".join(goal_phase.PHASES)
BY = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}")
NO_GIT = "This is not a git checkout; run the word inside the project."
NO_RULES_WRITTEN = "nothing to write: the rules are as this Orkboard makes them"
COMMIT_YOURSELF = "Orkboard commits nothing from a terminal: commit these files as you commit your work."


class Refused(Exception):
    """A word that cannot be done (exit 1): the message is what is said."""


class BadCall(Exception):
    """A call that is not well formed (exit 2)."""


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return done.stdout.rstrip("\n") if done.returncode == 0 else ""


def checkout() -> Path:
    """The git checkout the word runs in (its top folder), from the working folder."""
    top = _git(Path.cwd(), "rev-parse", "--show-toplevel")
    if not top:
        raise Refused(NO_GIT)
    return Path(top)


def _wiki(root: Path) -> tuple[str, Path]:
    try:
        rel = board_check.wiki_of(root)
    except ValueError as e:
        raise Refused(str(e)) from None
    return rel, (root / rel if rel else root)


def _by(value: str) -> str:
    if not BY.fullmatch(value or ""):
        raise BadCall("--by names the tool in a few plain characters (letters, digits, space, . _ -), e.g. --by codex")
    return value


def _page(wiki: Path, slug: str) -> Page:
    page = ideas.idea_page(wiki, slug)
    if page is None:
        raise Refused(f"No goal {slug!r} in the Board (orkboard goal list)")
    return page


def _phase_of(root: Path, wiki: Path, slug: str, page: Page) -> str:
    """The phase the page says; for a page of before, its state's when the app kept one here, else `new`."""
    got = goal_phase.phase_of_page(page)
    if got:
        return got
    state = root / ".orkcraft"
    if (ideas.state_folder(state, slug) / "state.json").is_file():
        return goal_phase.of(ideas.state(state, slug))
    return "new"


def _unset(wiki: Path, slug: str, key: str) -> None:
    with ideas.LOCK:
        page = _page(wiki, slug)
        page.meta = [(k, v) for k, v in page.meta if k != key]
        ideas._write(wiki / ideas.IDEAS / f"{slug}.md", page.text())


# -- init, check ---------------------------------------------------------------------------------------------------------------------

def _init(args: argparse.Namespace) -> int:
    from orkboard.gui import agent_rules_switch as switch
    root = checkout()
    if switch._public(root):
        raise Refused(switch.PUBLIC_WAIT)
    rel, _wiki_path = _wiki(root)
    try:
        written = agent_rules.write(root, rel, decisions=agent_rules.decisions_of(root))
    except (OSError, ValueError) as e:
        raise Refused(f"The Board's rules could not be written: {' '.join(str(e).split())[:200]}") from None
    for path in written:
        print(f"wrote {path}")
    if not written:
        print(NO_RULES_WRITTEN)
    if args.ci:
        if board_check.write_workflow(root, rel):
            print(f"wrote {board_check.WORKFLOW}")
        else:
            print(f"{board_check.WORKFLOW} is your own file and stays; add `{agent_rules_text.RUN} check` to it, or move it and run this again")
    if written or args.ci:
        print(COMMIT_YOURSELF)
    return 0


def _check(_args: argparse.Namespace) -> int:
    root = checkout()
    try:
        found = board_check.run(root)
    except ValueError as e:
        raise Refused(str(e)) from None
    for f in found:
        print(board_check.say(f), file=sys.stderr)
    if found:
        print(f"{len(found)} fault{'' if len(found) == 1 else 's'} in the Board", file=sys.stderr)
        return 1
    print("The Board is clean")
    return 0


# -- goals ---------------------------------------------------------------------------------------------------------------------------

def _list(args: argparse.Namespace) -> int:
    root = checkout()
    _rel, wiki = _wiki(root)
    found, pages = ideas.ideas_and_pages(wiki)
    held = goal_take.read_all(root) if found else {}
    rows = []
    for i in found:
        page = pages[i["slug"]]
        phase = _phase_of(root, wiki, i["slug"], page)
        if args.phase and phase != args.phase:
            continue
        hold = (held or {}).get(i["slug"])
        rows.append((i["slug"], phase, "person" if page.get("asks") == goal_phase.PERSON else "", goal_take.line_of(hold)[len("Taken by "):] if hold else "", i["title"]))
    if not rows:
        print("No goals" + (f" in {args.phase}" if args.phase else ""))
        return 0
    head = ("goal", "phase", "asks", "taken", "title")
    widths = [max(len(r[n]) for r in [head, *rows]) for n in range(4)]
    for r in [head, *rows]:
        print("  ".join(r[n].ljust(widths[n]) for n in range(4)) + "  " + r[4])
    if held is None:
        print("(who has taken what could not be read: the remote did not answer)", file=sys.stderr)
    return 0


def _add(args: argparse.Namespace) -> int:
    root = checkout()
    by = _by(args.by)
    text = " ".join(args.words.split()) if "\n" not in args.words else args.words.strip()
    if not text:
        raise BadCall("A goal needs a few words")
    _rel, wiki = _wiki(root)
    party = args.party or ideas.GENERAL
    known = [t["slug"] for t in ideas.tracks(wiki, make=False)]
    if party != ideas.GENERAL and party not in known:
        raise Refused(f"No party {args.party!r}; the parties are: {', '.join(known) or 'none yet'}")
    slug = ideas.add_idea(wiki, text, track=party)
    ideas.set_meta(wiki, slug, phase="new", by=by, schema=goal_phase.SCHEMA)
    print(f"{slug}  (new, by {by}) in {(wiki / ideas.IDEAS / (slug + '.md')).relative_to(root).as_posix()}")
    return 0


def _take(args: argparse.Namespace) -> int:
    root = checkout()
    by = _by(args.by)
    _rel, wiki = _wiki(root)
    _page(wiki, args.slug)
    got = goal_take.take(root, args.slug, by, goal_take.TOOL, dt.datetime.now(dt.timezone.utc))
    if not got["taken"]:
        raise Refused(f"{goal_take.line_of(got)}; leave {args.slug} to them")
    note = f" (the remote could not be reached: {got.get('why', '')}; the push decides when it is back)" if got.get("offline") else " (no remote: nothing is kept)" if got.get("local") else ""
    print(f"{args.slug} is taken by {by} until {got['until']}{note}")
    return 0


def _needs(page: Page, root: Path, wiki: Path, phase: str) -> None:
    """What a goal must hold to be in `phase` (E.1): `spec` its *Done when*, `work` its stages, `done` a green gate record of `HEAD`."""
    if phase in ("spec", "work") and not board_check.has_done_when(page, root):
        raise Refused(f"A goal in {phase} needs a *Done when* in its page: write it first")
    if phase == "work" and not board_check.has_stages(page, root):
        raise Refused("A goal in work needs its stages in its page (*Stages*, or *Plan* in a party's section): write them first")
    if phase == "done":
        record = page.get("gate").strip()
        if not board_check.GREEN.match(record):
            raise Refused("A goal is done only with a green gate record: run orkboard gate --record <goal> first")
        head = _git(root, "rev-parse", "HEAD")
        short = record.split("·")[0].strip()
        if not head or not head.startswith(short):
            raise Refused(f"The gate's record is for {short}, not for HEAD ({head[:7] or 'no commit'}): run orkboard gate --record again on this commit")


def _phase(args: argparse.Namespace) -> int:
    if args.phase not in goal_phase.PHASES:
        raise BadCall(f"No phase {args.phase!r}; the phases are {PHASE_WORDS}")
    root = checkout()
    _rel, wiki = _wiki(root)
    page = _page(wiki, args.slug)
    now = _phase_of(root, wiki, args.slug, page)
    at, to = goal_phase.PHASES.index(now), goal_phase.PHASES.index(args.phase)
    if to > at + 1:
        raise Refused(f"{args.slug} is in {now}: it moves one phase on ({goal_phase.PHASES[at + 1]}) or any step back, not to {args.phase}")
    if to > at:
        _needs(page, root, wiki, args.phase)
    ideas.set_meta(wiki, args.slug, phase=args.phase, schema=goal_phase.SCHEMA)
    print(f"{args.slug}: {now} -> {args.phase}" if to != at else f"{args.slug} is in {args.phase} already")
    return 0


def _ask(args: argparse.Namespace) -> int:
    root = checkout()
    _rel, wiki = _wiki(root)
    page = _page(wiki, args.slug)
    choices = [c.strip() for c in args.choices.split("/")] if args.choices else []
    q = idea_questions.of({"ask": args.ask, "choices": choices, "pick": args.pick or None, "why": args.why})
    if q is None:
        raise BadCall("A question needs its words")
    if choices and not q["choices"]:
        raise BadCall(f"--choices is two to four answers of at most {idea_questions.CHOICE_CHARS} characters, each different, written a/b/c")
    if args.pick and q["pick"] is None:
        raise BadCall(f"--pick {args.pick!r} is none of the choices")
    old = page.section("Open questions")
    text = (old.rstrip() + "\n" if old.strip() else "") + "- " + idea_questions.line(q)
    ideas.set_section(wiki, args.slug, "Open questions", text)
    ideas.set_meta(wiki, args.slug, asks=goal_phase.PERSON)
    n = len(idea_questions.questions_of(text))
    print(f"question {n} of {args.slug} written; asks: person. Say it to the person and stop; the answer comes with: orkboard goal answer {args.slug} {n} \"<answer>\"")
    return 0


def _answer(args: argparse.Namespace) -> int:
    root = checkout()
    _rel, wiki = _wiki(root)
    page = _page(wiki, args.slug)
    said = " ".join(args.answer.split())
    if not said:
        raise BadCall("An answer needs its words")
    old = page.section("Open questions")
    try:
        text = idea_questions.with_answer(old, args.n - 1, said, dt.date.today().isoformat()) if args.n >= 1 else ""
    except ValueError:
        text = ""
    if not text:
        raise Refused(f"{args.slug} has no question {args.n} (it has {len(idea_questions.questions_of(old))})")
    ideas.set_section(wiki, args.slug, "Open questions", text)
    if not idea_questions.open_of(text):
        _unset(wiki, args.slug, "asks")
    print(f"question {args.n} of {args.slug} answered" + ("" if idea_questions.open_of(text) else "; none is left, asks is cleared"))
    return 0


# -- the gate ------------------------------------------------------------------------------------------------------------------------

def _dirty(root: Path, rel: str) -> list[str]:
    """The tracked files outside the Board's folder that differ from HEAD: a record names HEAD, so the tests must have run on it."""
    out = _git(root, "status", "--porcelain", "-uno")
    names = [ln[3:].strip().strip('"') for ln in out.splitlines() if ln[3:].strip()]
    prefix = f"{rel}/" if rel else "pages/"
    return [n for n in names if not n.startswith(prefix)]


def _gate(args: argparse.Namespace) -> int:
    from orkboard.realm.idea_git import IdeaGit
    root = checkout()
    rel, wiki = _wiki(root)
    if args.record:
        _page(wiki, args.record)
        if (dirty := _dirty(root, rel)):
            raise Refused(f"{dirty[0]} has changes that are not committed; the record names HEAD, so commit them and run the gate again")
    git = IdeaGit(root)
    base = args.base or git.default_branch() or "HEAD"
    if not _git(root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"):
        raise BadCall(f"--base {base!r} is no commit of this checkout")
    run = git.gate_run(root, base, threading.Event())
    print(run.out.rstrip())
    if not run.ran:
        raise Refused("no tests ran: " + (run.out.splitlines()[0] if run.out else "the gate found nothing to run") + "; nothing is recorded")
    green = run.ok
    verdict = "green" if green else ("did not finish" if run.env else "red")
    print(f"gate: {verdict}" + (f" ({run.env})" if run.env and not green else ""))
    if args.record:
        files = len([f for f in git.touched(root, base) if f])
        record = goal_phase.gate_of({"tasks": [{"commit": _git(root, "rev-parse", "--short=7", "HEAD"), "finished": "1", "diff": {"files": files},
                                                "tests": {"green": green, "env": "" if green else run.env, "ran": True}}]})
        ideas.set_meta(wiki, args.record, gate=record)
        print(f"{args.record}: gate: {record}")
    return 0 if green else 1


# -- the words -----------------------------------------------------------------------------------------------------------------------

def add_parsers(sub) -> None:
    """The words of this file, added to `orkboard`'s sub-commands."""
    p = sub.add_parser("init", help="Write the Board's rules for any AI tool into this project (not committed)")
    p.add_argument("--ci", action="store_true", help="Also write .github/workflows/orkboard-check.yml: checks the Board on each pull request")
    g = sub.add_parser("goal", help="Work the Board's goals from this checkout: list, add, take, phase, ask, answer (nothing is committed)")
    w = g.add_subparsers(dest="goal_word", required=True)
    s = w.add_parser("list", help="The goals: slug, phase, asks, taken, title")
    s.add_argument("--phase", choices=goal_phase.PHASES, default="", help="Only the goals in this phase")
    s = w.add_parser("add", help="Lay a goal in phase new")
    s.add_argument("words", metavar="WORDS", help="What the goal is, in the person's words")
    s.add_argument("--party", default="", help="The party's slug (default: General)")
    s.add_argument("--by", required=True, help="Your tool's name, e.g. codex")
    s = w.add_parser("take", help="Take a goal: one taker at a time, refused while another holds it")
    s.add_argument("slug")
    s.add_argument("--by", default="tool", help="Your tool's name, e.g. codex")
    s = w.add_parser("phase", help="Move a goal: one phase on, or any step back")
    s.add_argument("slug")
    s.add_argument("phase", metavar="PHASE", help=PHASE_WORDS)
    s = w.add_parser("ask", help="Ask the person: a line under Open questions, asks: person")
    s.add_argument("slug")
    s.add_argument("ask", metavar="QUESTION")
    s.add_argument("--choices", default="", metavar="A/B", help="Two to four answers, written a/b/c")
    s.add_argument("--pick", default="", help="The choice you recommend")
    s.add_argument("--why", default="", help="Why, in a few words")
    s = w.add_parser("answer", help="Write the person's answer under a question")
    s.add_argument("slug")
    s.add_argument("n", type=int, help="The question's number (the first is 1)")
    s.add_argument("answer", metavar="ANSWER")
    p = sub.add_parser("gate", help="Run the project's gate on this checkout and say the result")
    p.add_argument("--base", default="", metavar="REF", help="The ref the touched files are counted from (default: the repository's main branch)")
    p.add_argument("--record", default="", metavar="GOAL", help="Write the result into this goal's page (the gate key)")
    sub.add_parser("check", help="Check the Board's pages, rules and journals; exit 1 on any fault")


def run(args: argparse.Namespace) -> int:
    """The word parsed by `board_cli`: 0 done, 1 refused (its words on stderr), 2 a bad call."""
    do = {"init": _init, "check": _check, "gate": _gate}.get(args.word)
    if do is None:
        do = {"list": _list, "add": _add, "take": _take, "phase": _phase, "ask": _ask, "answer": _answer}[args.goal_word]
    try:
        return do(args)
    except Refused as e:
        print(f"orkboard {args.word}: {e}", file=sys.stderr)
        return 1
    except BadCall as e:
        print(f"orkboard {args.word}: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print(f"orkboard {args.word}: {' '.join(str(e).split())[:300]}", file=sys.stderr)
        return 1
