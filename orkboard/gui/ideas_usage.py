"""What used an AI tool's limit (docs/specs/91-the-owners-list.md §2), as `gui/ideas.py`'s `Ideas` has it.

    ideas.usage {provider, scope?}    # scope "project" (default) or "all" (every project open on this machine)

→ `{provider, name, left, window, reset, scope, scopes, rows: [{party, title, share, tokens, members: [{agent, name, share,
tokens}]}], outside, estimated: true, tokens_only}`. `left` is what is left of the tool's tightest window (a fraction, as the
top bar's `ideas.limits` row says it), `window` its name ("5h", "week"), `reset` when it resets (ISO, or ""). The computation is
code (realm/limit_usage.py), no model: the `limits_read` events of that window, paired, split by the tokens of the project's
calls between them. `scopes` says which switch the face offers: "all" only for a host that has several projects open, and it
reaches those (a closed project's Board is not read).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import IdeasError, _opt, _text
from orkboard.realm import harnesses, limit_usage

SCOPES = ("project", "all")
NO_SPAN = dt.timedelta(days=7)            # the calls a tool with no window known shows in tokens: the last week's


def _boards(m: Any, scope: str) -> list[tuple[str, Path, Path, Path]]:
    """`(name, repo_root, state_dir, pages root)` of this project, then (scope "all") of every other project open."""
    repo = Path(m.host.repo_root)
    here = (repo.name or str(repo), repo, m.state_dir, m.root(False))
    if scope == "project":
        return [here]
    others = [p for p in m.host.open_boards() if Path(p.root) != repo]
    return [here, *[(p.name, Path(p.root), p.ideas.state_dir, p.ideas.root(False)) for p in others]]


def usage(m: Any, args: dict) -> dict:
    provider = _text(args, "provider", 40)
    if harnesses.get(provider) is None:
        raise IdeasError(f"No AI tool {provider}")
    scope = _opt(args, "scope") or "project"
    if scope not in SCOPES:
        raise IdeasError(f"No scope {scope}")
    shown = next((l for l in m.limits() if l["provider"] == provider), None) or {}
    tight = min((r for r in shown.get("rows") or [] if isinstance(r.get("left"), (int, float))), key=lambda r: r["left"], default=None)
    left = tight["left"] if tight else None
    window, reset = (tight["window"], tight.get("reset") or "") if tight else ("", "")
    now = dt.datetime.now().astimezone()
    end, span = (limit_usage.when(reset) if reset else None), limit_usage.window_span(window)
    start = end - span if end is not None and span is not None and end > now else None

    boards = _boards(m, scope)
    reads, seen = [], set()
    for _name, repo, _state, _root in boards:                     # the reads are the machine's: every project's, once
        for r in limit_usage.reads_of(limit_usage.events_of(repo), provider, window) if window else []:
            if (r["at"], r["left"]) not in seen:
                seen.add((r["at"], r["left"]))
                reads.append(r)
    reads.sort(key=lambda r: r["at"])
    if left is not None and (not reads or reads[-1]["at"] < now):
        reads.append({"at": now, "left": float(left)})            # the read of this moment closes the last pair

    calls, titles, agents = [], {}, set()
    since = start or now - (span or NO_SPAN)
    for name, repo, state, root in boards:
        got, said = limit_usage.calls_of(root, state, provider, since)
        key = (lambda k: k) if scope == "project" else (lambda k, repo=repo: f"{repo}::{k}")
        for c in got:
            c["party"] = key(c["party"])
            agents.add(c["agent"])
        calls += got
        titles.update({key(k): (v if scope == "project" else f"{v} · {name}") for k, v in said.items()})
    split = limit_usage.split(reads, calls, start)
    names = limit_usage.names_of(m.state_dir, agents)
    for r in split["rows"]:
        r["title"] = titles.get(r["party"]) or r["party"]
        for member in r["members"]:
            member["name"] = names.get(member["agent"]) or member["agent"]
    return {"provider": provider, "name": harnesses.title(provider).split()[0], "left": left, "window": window, "reset": reset,
            "scope": scope, "scopes": list(SCOPES) if m.host.open_boards() else ["project"], **split, "estimated": True}


def usage_commands(m: Any) -> dict:
    return {"ideas.usage": lambda a: usage(m, a)}
