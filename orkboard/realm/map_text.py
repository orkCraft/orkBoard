"""A leader's map as text (docs/specs/99-a-goals-way.md §2.1, decisions §156.1–§156.2): what a leader is given in its call, read by code from
the newest snapshot of dev (realm/project_map.py, realm/system_overview.py), so the leader reads the repository only to read further what the
map names. Tech's *System* is the one map as text today; the other maps' texts are `None` (a party with no map is given none).

    map_text.system(state_dir, root, since="")      # The map of System at dev <short>: containers whole, links, parts a line each; ~3,000 characters
    map_text.system(state_dir, root, since, pages)  # … then *Changed since your last call* (`since`: the commit of the party's last call);
                                                    #   `pages`: the Board's pages, for a goal's title
    map_text.detail(state_dir, root, parts)         # the named parts in full (files, uses, used by): 1,500 characters more at most
    map_text.of(party, state_dir, root, since)      # the party's map as text: System for Tech, else None

The text is plain English for a model: short lines, no table. With `since` empty it is the same bytes for the same snapshot (no time, no
dict order: what a source holds unordered is sorted), which is what the prompt's cache keeps. Past LIMIT the parts keep only their names, and
the text says so. No model, no face.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orkboard.realm import ideas, project_map

REF = "dev"
LIMIT = 3000                     # the map's text, at most (the changes after it have their own bound)
DETAIL = 1500                    # the parts in full, at most
CHANGED = 1200                   # *Changed since your last call*, at most
CONTAINERS = 1500                # of LIMIT, the containers' lines at most (the rest of the top level has less)
LINKS, SHARED = 500, 200         # … the links' and the shared parts'
STACK, WAYS, ROUTES, EVENTS = 6, 4, 3, 4     # the most a container's line names of its stack, ways in; a link of its routes, events
FILES = 12                       # the most files a part in detail names
TITLE = 60
PARTS = "Parts (a part is named by its folder, by its path where two share a name):"
NAMED_ONLY = "The parts are named only: read further what you need."
TECH = "tech"                    # the party whose map is System


# -- the text, bounded -----------------------------------------------------------------------------------------------------------------

def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:max(0, n - 1)].rstrip() + "…"


def _fit(lines: list[str], room: int, more: str) -> list[str]:
    """`lines` as many as fit in `room` characters (joined by newlines); the ones left out are one last line, `more` with their number."""
    if sum(len(ln) + 1 for ln in lines) <= room + 1:
        return list(lines)
    reserve = len(more.format(n=len(lines))) + 1
    out, used = [], 0
    for line in lines:
        if used + len(line) + 1 + reserve > room + 1:
            break
        out.append(line)
        used += len(line) + 1
    return out + [more.format(n=len(lines) - len(out))]


def _snapshot(state_dir: Path, root: Path) -> dict | None:
    """Dev's head snapshot (made when none is kept); the newest kept when it cannot be made; None when the project has no `dev`."""
    try:
        return project_map.ensure(state_dir, Path(root), REF)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        return project_map.newest(state_dir)


def _list(items: list[str], shown: int) -> str:
    out = ", ".join(items[:shown])
    return out + (f", +{len(items) - shown}" if len(items) > shown else "")


# -- the containers, the links, the shared parts (the top level, whole) -----------------------------------------------------------------

def _way(w: dict) -> str:
    kind, name = str(w.get("kind") or ""), str(w.get("name") or "")
    return f"{kind} {name}" if name else f"{kind} {w.get('path') or ''}".strip()


def _container(c: dict) -> str:
    stack = [str(s.get("name") or "") for s in c.get("stack") or [] if isinstance(s, dict) and s.get("name")]
    more = int(c.get("unknown") or 0)
    stack_text = _list(stack, STACK) + (f" and {more} others" if more and stack else f"{more} packages" if more else "")
    ways = _list([_way(w) for w in c.get("ways_in") or [] if isinstance(w, dict)], WAYS)
    line = f"- {c.get('name')} ({c.get('path')}): " + (f"stack {stack_text}" if stack_text else "no stack read")
    return _cut(line + (f"; ways in: {ways}" if ways else ""), 260)


def _link(link: dict, names: dict[str, str]) -> str:
    http = [f"{r['method']} {r['path']}" for r in link.get("http") or []]
    events = [str(e["event"]) for e in link.get("socket") or []]
    bits = ([f"{len(http)} routes ({_list(http, ROUTES)})"] if http else []) + ([f"{len(events)} events ({_list(events, EVENTS)})"] if events else [])
    return f"- {names.get(link['from'], link['from'])} to {names.get(link['to'], link['to'])}: " + (" · ".join(bits) or "connects")


def _top(snap: dict) -> tuple[list[str], list[str], list[str]]:
    """(the containers' lines, the links', the shared parts') of the snapshot's overview, each in a fixed order."""
    ov = snap.get("overview") or {}
    cs = sorted((c for c in ov.get("containers") or [] if isinstance(c, dict)), key=lambda c: (c["path"] != ".", c["path"]))
    names = {c["path"]: str(c.get("name") or c["path"]) for c in cs}
    links = sorted((k for k in ov.get("links") or [] if isinstance(k, dict)), key=lambda k: (k["from"], k["to"]))
    shared = sorted((s for s in ov.get("shared") or [] if isinstance(s, dict)), key=lambda s: s["path"])
    return ([_container(c) for c in cs], [_link(k, names) for k in links],
            [f"- {s['path']}: used by {_list([names.get(x, x) for x in s.get('containers') or []], 4)}" for s in shared])


# -- the parts, a line each -------------------------------------------------------------------------------------------------------------

def _layers(snap: dict) -> dict[str, str]:
    """Each part's layer, as its container's rows number them from the top: `layer 2` (`layer 2, data` when its row has a role)."""
    out = {}
    for c in (snap.get("overview") or {}).get("containers") or []:
        for n, row in enumerate(c.get("layers") or []):
            for p in row.get("parts") or []:
                out[p] = f"layer {n + 1}" + (f", {row['role']}" if row.get("role") else "")
    return out


def _names(paths: list[str], project: str) -> dict[str, str]:
    """A part's name (its folder's), its path where two parts would have one."""
    names = {p: project_map.name_of(p, project) for p in paths}
    count: dict[str, int] = {}
    for n in names.values():
        count[n] = count.get(n, 0) + 1
    return {p: (n if count[n] == 1 else p) for p, n in names.items()}


def _parts(snap: dict, project: str) -> tuple[list[str], list[str]]:
    """(the parts' lines in full, the parts' names), by path."""
    parts = sorted((p for p in snap.get("parts") or [] if isinstance(p, dict)), key=lambda p: p["path"])
    name, layer = _names([p["path"] for p in parts], project), _layers(snap)
    full = []
    for p in parts:
        uses = ", ".join(name.get(u, u) for u in sorted(p.get("uses") or []))
        used = ", ".join(name.get(u, u) for u in sorted(p.get("used_by") or []))
        bits = [layer.get(p["path"]) or "", f"Uses: {uses}" if uses else "", f"Used by: {used}" if used else ""]
        full.append(f"- {p['path']}: " + "; ".join(b for b in bits if b) if any(bits) else f"- {p['path']}")
    return full, [f"- {p['path']}" for p in parts]


def _map(snap: dict, project: str) -> str:
    head = f"The map of System at dev {snap['commit'][:7]}"
    containers, links, shared = _top(snap)
    top = [head, "", "Containers:"] + _fit(containers, CONTAINERS, "- and {n} more containers: read further what you need")
    if links:
        top += ["", "Links:"] + _fit(links, LINKS, "- and {n} more links")
    if shared:
        top += ["", "Shared by two containers or more:"] + _fit(shared, SHARED, "- and {n} more")
    full, names = _parts(snap, project)
    if not full:
        return "\n".join(top)
    room = LIMIT - len("\n".join(top)) - len("\n\n" + PARTS + "\n")
    if len("\n".join(full)) <= room:
        body = full
    else:
        note = "\n" + NAMED_ONLY
        body = _fit(names, room - len(note), "- and {n} more parts: read further what you need")
        body = body + [NAMED_ONLY] if body else [NAMED_ONLY]
    return "\n".join(top + ["", PARTS] + body)[:LIMIT]


# -- what changed since the party's last call -------------------------------------------------------------------------------------------

def _goal(slug: str, pages: Path | None, cache: dict[str, str]) -> str:
    """`by you` for the person's own commit, else `goal <slug> "<title>"`."""
    if not slug:
        return "by you"
    if slug not in cache:
        title = ""
        try:
            page = ideas.idea_page(Path(pages), slug) if pages is not None else None
            title = " ".join((page.title if page else "").split())
        except (OSError, ValueError):
            pass
        cache[slug] = f"goal {slug}" + (f' "{_cut(title, TITLE)}"' if title else "")
    return cache[slug]


def _changed(state_dir: Path, root: Path, since: str, pages: Path | None) -> str:
    """*Changed since your last call*: each part new, changed or gone and each use new or gone, with the goal that made it (`by you` for the
    person's own). Who decided it is not read: nothing stored says (spec 99 §2.1, decisions §112.6)."""
    head = "Changed since your last call"
    try:
        got = project_map.changed(state_dir, Path(root), since, REF)
    except (OSError, ValueError, subprocess.SubprocessError):
        got = project_map.nothing()
    if not got["since"]:
        return f"{head}: not known (no map was kept at that commit)."
    cache: dict[str, str] = {}
    order = {"new": 0, "changed": 1, "gone": 2}
    rows = [f"- {c['kind']} part {p} ({_goal(c['goal'], pages, cache)})"
            for p, c in sorted(got["parts"].items(), key=lambda kv: (order.get(kv[1]["kind"], 3), kv[0]))]
    rows += [f"- {u['kind']} use {u['from']} to {u['to']} ({_goal(u['goal'], pages, cache)})"
             for u in sorted(got["uses"], key=lambda u: (u["kind"] != "new", u["from"], u["to"]))]
    if not rows:
        return f"{head}: nothing."
    return "\n".join([f"{head}:"] + _fit(rows, CHANGED - len(head) - 2, "- and {n} more changes"))


# -- the calls ----------------------------------------------------------------------------------------------------------------------------

def system(state_dir: Path, root: Path, since: str = "", pages: Path | None = None) -> str | None:
    """Tech's map as text at dev's head (about LIMIT characters at most), then, when `since` is set, what changed since that commit with its
    goal. `pages`: where the Board's pages are, for a goal's title (else the slug alone). None when the project has no `dev` to read."""
    snap = _snapshot(Path(state_dir), Path(root))
    if snap is None:
        return None
    text = _map(snap, Path(root).name)
    since = str(since or "").strip()
    return text + "\n\n" + _changed(Path(state_dir), Path(root), since, pages) if since else text


def detail(state_dir: Path, root: Path, parts: list[str]) -> str:
    """The named parts in full: files, Uses, Used by (DETAIL characters at most). A path inside a part names that part; one that is no part's
    is left out; "" when none is known."""
    snap = _snapshot(Path(state_dir), Path(root))
    have = {p["path"]: p for p in (snap or {}).get("parts") or [] if isinstance(p, dict)}
    picked: list[str] = []
    for want in parts if isinstance(parts, (list, tuple)) else []:
        want = str(want or "").strip().strip("/") or "."
        path = want if want in have else max((p for p in have if p != "." and want.startswith(p + "/")), key=len, default="")
        if path and path not in picked:
            picked.append(path)
    if not picked:
        return ""
    head = f"Parts in detail at dev {snap['commit'][:7]}:"
    lines = []
    for path in picked:
        p = have[path]
        files = list(p.get("files") or [])
        n = int(p.get("count") or len(files))
        lines += [f"- {path} ({n} file{'' if n == 1 else 's'})",
                  "  Files: " + _list(files, FILES) if files else "",
                  "  Uses: " + ", ".join(sorted(p.get("uses") or [])) if p.get("uses") else "",
                  "  Used by: " + ", ".join(sorted(p.get("used_by") or [])) if p.get("used_by") else ""]
    return "\n".join([head] + _fit([ln for ln in lines if ln], DETAIL - len(head) - 1, "- and more parts: read further what you need"))


def of(party: str, state_dir: Path, root: Path, since: str = "", pages: Path | None = None) -> str | None:
    """The map of `party` as text: System for Tech; the other maps' texts come with their parties (spec 99 S3), so a party with none is given none."""
    return system(state_dir, root, since, pages) if party == TECH else None
