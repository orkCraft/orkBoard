"""Release's map (docs/specs/102-the-other-maps-and-picking-on-them.md §3.2, decisions §137.3): dev against main. A card is a goal that is in dev and not in main (its
element, its name, its commit), ticked by default; the last version that is out is *Since <version>*; **To main** is the gate's merge, by code (`ideas.gate_merge`,
realm/idea_gate.py). Read from git and the goals' plans, never the working tree. No model, no face.

    release_map.read(state_dir, root, pages=None, into="dev")   # {into, main, same, commits, files, big_from, goals: [{idea, title, element, commit, at, ticked}], since: {version, out} | None}
    release_map.text(state_dir, root, since="", pages=None, into="dev")   # Release's leader's map as text: the goals waiting for main and the last version

`goals` are the goals with a task merged into `into` whose commit `main` lacks, the newest landing first (the order dev holds them, not the Board's: no page is read for it);
`commit` is the newest of such commits (full), `at` its time in seconds (0 when git cannot say). The commits are the gate's (`idea_gate.waiting_by_patch`): a goal already sent to main alone, cherry-picked, waits for nothing. `big_from` is the number of goals
(`map_signals_crafts.BATCH_GOALS`) from which a batch is big. `pages` (the Board's pages root) gives a goal its title and drops a goal gone from the Board, and gives `since` its party:
`releases.since` of the project's Release party; without it a goal's title is its slug and `since` is None. `same` (dev and main are one branch, or main is none) is *no gate*:
`goals` is then empty. `since` of `text` is the commit of the party's last call: the map is a state, not a change log, so it is not used.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard.realm import goal_types, idea_element, idea_gate, ideas, releases, worktrees
from orkboard.realm.idea_git import IdeaGit

SHORT = 7


def _main(git: IdeaGit) -> str:
    try:
        return git.default_branch()
    except Exception:                               # not a git folder yet
        return ""


def _times(root: Path, shas: list[str]) -> dict[str, int]:
    """The commit time of each of `shas`, in seconds: one `git log` for all; {} when git cannot say."""
    if not shas:
        return {}
    try:
        got = subprocess.run(["git", "log", "--no-walk=unsorted", "--format=%H %ct", *shas, "--"], cwd=root, capture_output=True, text=True, timeout=worktrees.GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return {}
    rows = (line.split() for line in got.stdout.splitlines()) if got.returncode == 0 else ()
    return {r[0]: int(r[1]) for r in rows if len(r) == 2 and r[1].isdigit()}


def _waiting(state_dir: Path, shas: list[str], pages: Path | None, times: dict[str, int]) -> list[dict]:
    """The goals with a merged task among `shas`, the one whose newest commit stands first in `shas` (newest first) first."""
    place = {s: n for n, s in enumerate(shas)}
    found: list[tuple[int, str, str]] = []
    base = Path(state_dir) / "ideas"
    for slug in sorted(d.name for d in base.iterdir() if d.is_dir()) if base.is_dir() else []:
        try:
            tasks = (ideas.plan(state_dir, slug) or {}).get("tasks") or []
        except ValueError:
            continue
        mine = [str(t.get("commit") or "") for t in tasks if isinstance(t, dict) and t.get("state") == "merged" and str(t.get("commit") or "") in place]
        if mine:
            newest = min(mine, key=lambda c: place[c])
            found.append((place[newest], slug, newest))
    out = []
    for _n, slug, commit in sorted(found):
        title = slug
        if pages is not None:
            try:
                page = ideas.idea_page(Path(pages), slug)
            except (OSError, ValueError):
                page = None
            if page is None:
                continue                            # a goal dropped from the Board waits for nothing
            title = " ".join((page.title or slug).split())
        out.append({"idea": slug, "title": title, "element": idea_element.of(state_dir, slug), "commit": commit, "at": times.get(commit, 0), "ticked": True})
    return out


def _since(state_dir: Path, pages: Path | None) -> dict | None:
    if pages is None:
        return None
    party = goal_types.release_party(Path(pages))
    return releases.since(Path(pages), state_dir, party) if party else None


def read(state_dir: Path, root: Path, pages: Path | None = None, into: str = "dev") -> dict:
    """The map (see the module). A repository git cannot read has nothing waiting that the Board can see."""
    from orkboard.realm import map_signals_crafts           # lazy: that module reads this one
    git = IdeaGit(Path(root))
    main = _main(git)
    out: dict = {"into": into, "main": main, "same": idea_gate.same(into, main), "commits": 0, "files": 0, "big_from": map_signals_crafts.BATCH_GOALS, "goals": [],
                 "since": _since(state_dir, pages)}
    if out["same"]:
        return out
    try:
        shas, files = idea_gate.waiting_by_patch(git, into, main)      # as the gate counts: a goal sent alone is not waiting again
    except Exception:
        return out
    return {**out, "commits": len(shas), "files": files, "goals": _waiting(state_dir, shas, pages, _times(Path(root), shas))}


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def text(state_dir: Path, root: Path, since: str = "", pages: Path | None = None, into: str = "dev") -> str | None:
    """Release's map as text (about `map_text.LIMIT` characters at most): the goals waiting for main, then the last version out. None when the repository has no `into` branch."""
    from orkboard.realm import map_text           # lazy: map_text.of reads this module's text
    if not worktrees.branch_exists(Path(root), into):
        return None
    got = read(state_dir, root, pages, into)
    head = f"The map of Release: {into} against {got['main'] or 'main'}"
    if got["same"]:
        lines = [f"{into} and {got['main'] or 'main'} are one branch here: there is no gate, nothing waits for main."]
    elif not got["commits"]:
        lines = [f"Nothing in {into} waits for {got['main']}."]
    else:
        n = len(got["goals"])
        lines = [f"Waiting for {got['main']} ({_count(n, 'goal', 'goals')}; {_count(got['commits'], 'commit', 'commits')}, {_count(got['files'], 'file', 'files')} changed):"]
        rows = [f"- goal {g['idea']}" + (f' "{map_text._cut(g["title"], map_text.TITLE)}"' if g["title"] != g["idea"] else "") + f" (commit {g['commit'][:SHORT]})"
                for g in got["goals"]]
        lines += map_text._fit(rows, map_text.LIMIT - len(head) - len(lines[0]) - 200, "- and {n} more goals")
        if not n:
            lines.append("- the commits are the person's own, no goal's.")
    last = got["since"]
    lines += ["", f"Last version out: {last['version'] or 'unnamed'}, {str(last['out'])[:10]}." if last else "No version is out yet."]
    return "\n".join([head, ""] + lines)

