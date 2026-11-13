"""A goal's sketch, faceless (docs/specs/121-the-day-the-morning-and-the-night.md §2; decisions §199.3): before the spec of a goal that is seen or heard is written, its craft's leader makes two or three
throwaway variants (a screen as one HTML page, a loop on a page, pictures or a sound), kept beside the goal and never in the project's tree, touched and picked on the phone; the spec rests on the one
picked. This module is the rules, with no model and no face; the call is `core/idea_sketch.py`'s.

    wanted(route, how, types, ground=True)   # the craft that sketches this goal ("design" · "game-design" · "art"), "" for a goal that gets none
    craft_for(route, types)                  # …the same without the short way and the ground: the first craft of the route that sketches, else the one a goal type names
    look(root, ref="")                       # the project's look, as text: its design tokens, else its top stylesheet (at `ref` when the repository has it), at most `LOOK_CHARS`
    media_ready(kind, which=shutil.which)    # the media tools an Art sketch of this kind (image · audio) is made with are on the machine
    art_kind(types)                          # the kind of pick an Art sketch makes: "audio" for a sound, else "image"
    parse_pages(answer)                      # the leader's answer strictly: [{name, why, html}], two or three, each one self-contained page; None when it is not
    left(round_)                             # how many rounds of sketching are left after round `round_` (`ROUNDS` in all)
    record(state_dir, slug) / save(state_dir, slug, **fields)   # `<state>/ideas/<goal>/sketch.json`: where the goal's sketch stands

**Which goals** (§2.1): a goal whose route has Design, Art or Game design, or whose goal types are a screen, art, a sound or a balance of the loop, **and** that is not the short way (a bug, a tidy) nor a
pitch, **and** whose project has something to sketch from (`ground`: a look, screens or assets). The person can ask for one on any goal and turn it off for one (`prefer`: the goal's state keeps it).

**A page** is one self-contained HTML document: inline style and script, no network, no font from outside, at most `PAGE_KB` KB. Parsed strictly: a `src`, `href`, `srcset`, `poster`, `action` or `url(` that is
not a `data:` address or a `#` anchor, an `@import`, or a page that does not begin as a page does, is refused (§3.2: the page's own policy refuses it again where it is served, `gui/media.py`).
"""
from __future__ import annotations

import html as html_lib
import json
import re
import shutil
import subprocess
from pathlib import Path

from orkboard.realm import ideas

PAGE_KB = 60                                   # the most a variant's page weighs
ROUNDS = 3                                     # the rounds of variants a goal's sketch may have: the fourth is refused
LOOK_CHARS = 4_000                             # the project's look, as much of it as the call is given
VARIANTS = (2, 3)                              # a round's variants: at least, at most
NAME_CHARS, WHY_CHARS = 24, 300                # as a pick's (realm/idea_pick.py NAME_MAX, WHY_MAX)
FILE = "sketch.json"                           # in the goal's state folder: where its sketch stands
CRAFTS = ("design", "game-design", "art")      # the crafts that sketch: a screen, a loop on a page, a picture or a sound
TYPE_CRAFT = {"screen": "design", "flow-feature": "design", "icon": "art", "logo": "art", "character": "art", "sound": "art", "balance": "game-design"}     # a goal type that is seen or heard names its craft
NOT_SKETCHED = ("bug", "tidy", "pitch")        # the short way, and a pitch (judged, never built)
MEDIA = {"image": ("python3", "node", "ffmpeg"), "audio": ("ffmpeg", "sox")}      # a tool of each kind of pick (realm/task_commands.py `MEDIA`): one of them on the machine is the media tools set up
TOKEN_FILES = ("design-tokens.json", "tokens.json", "design/tokens.json", "src/tokens.css", "src/styles/tokens.css", "src/theme/tokens.css", "tokens.css", "theme.css", "src/theme.css")
SHEETS = ("src/index.css", "src/styles.css", "src/style.css", "src/App.css", "src/app.css", "styles.css", "style.css", "index.css", "app.css", "public/style.css", "public/styles.css", "static/style.css",
          "static/css/style.css", "assets/style.css", "assets/css/style.css", "css/style.css", "css/styles.css")
_START = re.compile(r"\A﻿?\s*(?:<!--.*?-->\s*)*(?:<!doctype\s+html[\s>]|<html[\s>])", re.S | re.I)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ATTR = re.compile(r"""(?<![\w-])(src|srcset|href|poster|action|formaction)\s*=\s*(["'])(.*?)\2""", re.S | re.I)
_URL = re.compile(r"""url\(\s*(["']?)(.*?)\1\s*\)""", re.S | re.I)
_IMPORT = re.compile(r"@import\b", re.I)


def _line(value: object, limit: int) -> str:
    return " ".join(value.split())[:limit].rstrip() if isinstance(value, str) else ""


# -- which goals -------------------------------------------------------------------------------------------------------------------------

def craft_for(route: list, types: list[str] | tuple[str, ...] = ()) -> str:
    """The craft that makes a goal's sketch, by the route and the goal types, with no regard for the short way: the first craft of `route` (crafts, or rows with a `craft`) that sketches, else the craft
    the first goal type that is seen or heard names ("" with none)."""
    crafts = [str(r.get("craft") if isinstance(r, dict) else r or "") for r in route or []]
    first = next((c for c in crafts if c in CRAFTS), "")
    return first or next((TYPE_CRAFT[t] for t in types or () if t in TYPE_CRAFT), "")


def wanted(route: list, how: dict | None, types: list[str] | tuple[str, ...] = (), ground: bool = True) -> str:
    """The craft that sketches the goal (see the module), "" for a goal that gets none: the short way (`how["short"]`, or a kind that is a bug or a tidy) or a pitch, a goal with no craft that sketches and
    no goal type that is seen or heard, or a project with nothing to sketch from (`ground` False)."""
    how = how if isinstance(how, dict) else {}
    if how.get("short") or how.get("kind") in NOT_SKETCHED or any(t in NOT_SKETCHED for t in types or ()) or not ground:
        return ""
    return craft_for(route, types)


def art_kind(types: list[str] | tuple[str, ...] = ()) -> str:
    """The kind of pick an Art sketch makes (realm/idea_pick.py `KINDS`): `audio` for a sound, else `image`."""
    return "audio" if "sound" in (types or ()) else "image"


def media_ready(kind: str, which=shutil.which) -> bool:
    """The media tools an Art sketch of `kind` is made with are set up on this machine (one of `MEDIA[kind]` is on the path): the commands a pick task is allowed (realm/task_commands.py)."""
    return any(which(cmd) for cmd in MEDIA.get(kind, ()))


def left(round_: int) -> int:
    """How many rounds of sketching a goal has left after round `round_`."""
    return max(ROUNDS - int(round_ or 0), 0)


# -- the project's look ------------------------------------------------------------------------------------------------------------------

def _show(root: Path, ref: str, rel: str) -> str:
    """The file `rel` of the project as `ref` holds it (git alone is read), else as the folder holds it; "" when it is not there."""
    if ref:
        try:
            got = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=str(root), capture_output=True, timeout=20)
            if got.returncode == 0:
                return got.stdout.decode("utf-8", "replace")
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        file = Path(root) / rel
        return file.read_text(encoding="utf-8", errors="replace") if file.is_file() and file.stat().st_size < 2_000_000 else ""
    except OSError:
        return ""


def look(root: Path, ref: str = "") -> str:
    """The project's look as the sketch is told it (§2.3): its design tokens (a file named like one), else its top stylesheet, at `ref` (dev) when the repository has the file there, cut at `LOOK_CHARS`.
    A line is kept with its file's name first (`/* path */`); "" for a project with neither."""
    for rel in (*TOKEN_FILES, *SHEETS):
        text = _show(Path(root), ref, rel).strip()
        if text:
            head = f"/* {rel} */\n"
            return head + text[:max(LOOK_CHARS - len(head), 0)].rstrip()
    return ""


# -- a page, strictly --------------------------------------------------------------------------------------------------------------------

def outside(html: str) -> str:
    """The first address in `html` that leads out of the page (a `src`, `href`, `srcset`, `poster`, `action` or `formaction` that is not a `data:` address or a `#` anchor, a `url(` that is not a `data:`
    address, an `@import`), else "". A page needs none of them: its picture is `data:`, its style and script inline. Read with its character references resolved (`&#104;ttp://` is `http://`)."""
    html = html_lib.unescape(html)

    def open_(value: str) -> bool:
        v = value.strip().lower()
        return bool(v) and not v.startswith(("data:", "#"))

    for m in _ATTR.finditer(html):
        if open_(m.group(3)):
            return f"{m.group(1).lower()}={m.group(3).strip()[:60]}"
    for m in _URL.finditer(html):
        if open_(m.group(2)):
            return f"url({m.group(2).strip()[:60]})"
    if _IMPORT.search(html):
        return "@import"
    return ""


def clean_page(raw: object) -> dict | None:
    """One variant strictly: `{name, why, html}`; None for what is not one — no name, no page, a page over `PAGE_KB`, one that does not begin as a page does (`<!doctype html>` or `<html>`), has a control
    character or leads outside itself (`outside`)."""
    if not isinstance(raw, dict):
        return None
    name, why, html = _line(raw.get("name"), NAME_CHARS), _line(raw.get("why"), WHY_CHARS), raw.get("html")
    if not name or not isinstance(html, str) or not html.strip() or _CONTROL.search(html) or not _START.match(html):
        return None
    if len(html.encode("utf-8")) > PAGE_KB * 1024 or outside(html):
        return None
    return {"name": name, "why": why, "html": html}


def parse_pages(answer: object) -> list[dict] | None:
    """The leader's answer strictly: `{"variants": [{name, why, html}, …]}` with two or three variants, each one clean (`clean_page`) and no two of the same name; None when it is not (a call that did not
    keep to it is asked once more, core/idea_sketch.py). The names are kept as written, cut at `NAME_CHARS`."""
    rows = answer.get("variants") if isinstance(answer, dict) else None
    if not isinstance(rows, list) or not VARIANTS[0] <= len(rows) <= VARIANTS[1]:
        return None
    out = [clean_page(r) for r in rows]
    if any(r is None for r in out) or len({r["name"].lower() for r in out}) != len(out):
        return None
    return out


# -- where a goal's sketch stands --------------------------------------------------------------------------------------------------------

def _path(state_dir: Path, slug: str) -> Path:
    return ideas.state_folder(state_dir, slug) / FILE


def record(state_dir: Path, slug: str) -> dict:
    """`<state>/ideas/<goal>/sketch.json`: `{status, round, craft, party, leader, kind, ask, notes, made_at, asked_at, picked, answer, why, cost}` — `status` is "" (none), `making`, `asked` (the variants wait
    for the person), `picked`, `again` (a new round is being made), `skipped`; `{}` for a goal with no sketch."""
    got = ideas._json(_path(state_dir, slug))
    return got if isinstance(got, dict) else {}


def save(state_dir: Path, slug: str, **fields) -> dict:
    """The record with `fields` set (an empty record made first); the whole is returned. Under `ideas.LOCK`."""
    with ideas.LOCK:
        data = {**record(state_dir, slug), **fields}
        path = _path(state_dir, slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        tmp.replace(path)
        return data


# -- what the work reads of the sketch picked --------------------------------------------------------------------------------------------------

HTML_CHARS = 6_000                             # a page's start, as much of it as the sections are given
WILL_BE = ("A sketch was picked (above): the parts it shows are the parts the work changes. Rest `done_when` and `will_be` on it, and say in `assumed` where the work goes past it "
           "or leaves something of it out.")


def picked(state_dir: Path, slug: str) -> dict | None:
    """The sketch the person picked, `{key, name, why, note, file, mime, kind, round, pick}`; None when none was picked (none made, skipped, or still being answered)."""
    rec = record(state_dir, slug)
    got = rec.get("picked") if rec.get("status") == "picked" else None
    return got if isinstance(got, dict) and got.get("file") and got.get("pick") else None


def reference(state_dir: Path, slug: str) -> Path | None:
    """The picked sketch's file in the goal's state folder (outside the project's tree, never committed), where it stands; None with none."""
    from orkboard.realm import idea_pick
    got = picked(state_dir, slug)
    if got is None:
        return None
    path = idea_pick.folder_of(Path(state_dir), slug, str(got["pick"])) / str(got["file"])
    return path if path.is_file() else None


def reference_dirs(state_dir: Path, slug: str) -> tuple[str, ...]:
    """The folder a task may read the picked sketch in besides its worktree (`jobs.run_work` `dirs`): the sketch's pick; none without one."""
    path = reference(state_dir, slug)
    return (str(path.parent),) if path is not None else ()


def context(state_dir: Path, slug: str) -> str:
    """*The sketch the person picked* as the sections are given it (§2.6): its name and line, the person's note, and for a page its HTML cut at `HTML_CHARS` (a picture or a sound: its name and
    the line, not the file); "" with none picked."""
    got = picked(state_dir, slug)
    if got is None:
        return ""
    out = [f"Sketch {got.get('key')} · {got.get('name')}" + (f" — {got['why']}" if got.get("why") else "")]
    if got.get("note"):
        out.append(f"The person said: \"{got['note']}\"")
    path = reference(state_dir, slug)
    if got.get("mime") == "text/html" and path is not None:
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            html = ""
        if html.strip():
            out.append(f"Its page (the first {HTML_CHARS:,} characters):\n{html[:HTML_CHARS]}" + ("…" if len(html) > HTML_CHARS else ""))
    elif got.get("kind"):
        out.append(f"It is {'a sound' if got['kind'] == 'audio' else 'a picture'} (`{got.get('file')}`): its name and line are all that is read here.")
    return "\n".join(out)


def forget(state_dir: Path, slug: str) -> None:
    """A goal's sketch record leaves (its variants stay with its picks until the goal's state goes)."""
    try:
        _path(state_dir, slug).unlink()
    except OSError:
        pass
