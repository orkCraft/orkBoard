"""The mark on the live product (docs/specs/115-the-live-product-under-each-leaders-eyes.md §5, decisions §193), as `gui/ideas.py`'s `Ideas` has it: the commands the page marks a place on Play's
product by. Data only; a refusal is an `IdeasError` in plain words. The phone has none of them (it has no Play).

    ideas.play_events {play, events}       # the probe's events, forwarded by the page in batches (the probe's own shapes: `event` error | request | press, `at`, `page`); kept in one ring a play
                                           #   (realm/play_signals.py `Ring`), dropped when Play stops or a new play id comes → {ok, kept}; an event of another play or of none is not kept
    ideas.play_place {path, files?}        # → {screen: {id, name, step} | None, parts: {map: [{id, name}]}} (realm/play_place.py); `files` the repository files the probe named, or paths inside Play's worktree
    ideas.play_hints {path?}               # → {hints: [{kind, on, words, at}]} of this play's ring (realm/play_signals.py `hints`; `preview_slow_ms` of .orkcraft/checks.toml is its `slow_ms`)
    ideas.play_mark {text, kind, box, path, party?, under?, picture?, state?, viewport?, with?, add_to?}
        # `kind`: bug · looks · missing · confusing (goal types bug, none, feature, pain); `box`: {x, y, w, h} in shares of the frame, 0..1; `party`: the open tab's (none on the project's tab:
        #   the Orkmaster routes it; a Bug goes to Tech); `under`: the probe's elements under the box; `picture`: {html, w, h} the probe's snapshot; `state`: the game's; `viewport`: {w, h} of
        #   the frame, for a page drawn anew; `with`: the chips left on, of screen · part · errors · requests · lines · state (omitted: all);
        #   `add_to`: the slug of a goal not started, instead of a new goal.
        # → {slug, title, party, party_title, type, element, route?, joined, kept: {picture, errors, requests, lines, state, under, marks}}
    ideas.play_mark_offer {path, kind}     # → {goal: {slug, title}} or {}: a goal not started with a mark of the same kind on the same screen, by code

**What a chip keeps.** `screen`: the lens `{kind: "screen", screen, marks: [{x, y, w, h, note: text}]}` with its picture (realm/idea_lens.py), kept for the project as the screens kept are; the picture is the
probe's snapshot drawn by the host's Chromium at the frame's size (core/idea_shot.py), else the page's path drawn anew from Play (the picture is of the page, not of the moment), else none: the
box stays in the goal's play. `part`: the elements under the box and, as the goal's `marks`, the parts of every map the place touches (realm/play_place.py; with only `screen` on, Design's screen).
`errors`: the page's errors, `requests`: its failed or slow requests, each from this play's ring (ten at most); `lines`: the server's last 40 lines before the mark; `state`: the game's. What is kept is the
goal's play (realm/idea_play.py), read into its calls after the lens. A Play with no probe has no errors, requests, element, snapshot or state: a box, a path and (if it plays) the server's lines.
A Bug whose play holds an error or a failed request `reproduces` (realm/goal_route.py `with_play`).
"""
from __future__ import annotations

import base64
import datetime as dt
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from orkboard.core import idea_shot
from orkboard.gui.ideas_args import IdeasError, _device, _opt, _text
from orkboard.realm import goal_route, goal_types, idea_element, idea_lens, idea_photos, idea_play, ideas, pitches, play_place, play_signals

KIND_TYPE = {"bug": "bug", "looks": "", "missing": "feature", "confusing": "pain"}      # the kind's goal type; *Looks wrong* has none: its party's own
WITH = ("screen", "part", "errors", "requests", "lines", "state")
MAX_BATCH = 200                       # the events one batch carries
MAX_HTML = 4_200_000                  # the probe's snapshot, at most (it says 4 MB)
SIZE_MIN, SIZE_MAX = 200, 2400        # the frame, in pixels, a picture is drawn at
NO_SCRIPTS = '<meta http-equiv="Content-Security-Policy" content="script-src \'none\'">'
DOCTYPE = re.compile(r"^\s*<!doctype[^>]*>", re.I)
_LOCK = threading.Lock()


def _num(v: object) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _short(v: object, n: int) -> str:
    return " ".join(str(v if isinstance(v, (str, int, float)) else "").split())[:n]


def _event(raw: object) -> dict | None:
    """One probe event in the shape realm/play_signals.py reads: `{kind: event, at, path: page, …}` (a request keeps its own `path`); only what is known is kept, bounded. None for any other."""
    if not isinstance(raw, dict) or raw.get("event") not in ("error", "request", "press") or _num(raw.get("at")) is None:
        return None
    kind, page = raw["event"], _short(raw.get("page"), 300)
    out: dict[str, Any] = {"kind": kind, "at": _num(raw["at"]), "page": page}
    if kind == "error":
        out.update(path=page, message=_short(raw.get("message"), 300), stack=_short(raw.get("stack"), 300), source=_short(raw.get("source"), 20))
    elif kind == "request":
        out.update(method=_short(raw.get("method"), 10) or "GET", path=_short(raw.get("path"), 300), status=_num(raw.get("status")) or 0, ms=_num(raw.get("ms")) or 0)
        if host := _short(raw.get("host"), 100):
            out["host"] = host
    else:
        rect = raw.get("rect") if isinstance(raw.get("rect"), dict) else None
        out.update(path=page, selector=_short(raw.get("selector"), 300), role=_short(raw.get("role"), 40), pressable=raw.get("pressable") is True, changed=bool(raw.get("changed")),
                   rect={k: _num(rect.get(k)) or 0 for k in ("x", "y", "w", "h")} if rect else None,
                   **{k: bool(raw.get(k)) for k in ("dom", "moved", "request")})
    return out


def _box(raw: object) -> dict:
    """The mark's box in shares of the frame, inside it; IdeasError when there is none to draw."""
    if not isinstance(raw, dict):
        raise IdeasError("Draw a box or press a part")
    x, y, w, h = (_num(raw.get(k)) for k in ("x", "y", "w", "h"))
    if None in (x, y, w, h):
        raise IdeasError("Draw a box or press a part")
    x, y = min(1.0, max(0.0, x)), min(1.0, max(0.0, y))
    w, h = min(w, 1 - x), min(h, 1 - y)
    if w <= 0 or h <= 0:
        raise IdeasError("Draw a box or press a part")
    return {"x": round(x, 4), "y": round(y, 4), "w": round(w, 4), "h": round(h, 4)}


def _with(raw: object) -> set[str]:
    if raw is None:
        return set(WITH)
    if not isinstance(raw, list) or any(not isinstance(x, str) or x not in WITH for x in raw):
        raise IdeasError(f"`with` is some of {', '.join(WITH)}")
    return set(raw)


def _path(raw: object) -> str:
    text = _short(raw, 300)
    return text if text.startswith("/") else "/" + text


def _kind(args: dict) -> str:
    kind = _opt(args, "kind")
    if kind not in KIND_TYPE:
        raise IdeasError("A mark is a bug, looks wrong, missing or confusing")
    return kind


def _html(picture: object) -> tuple[str, tuple[int, int]] | None:
    """The probe's snapshot and the frame it was taken in; None when there is none (`{none: true}`, or it is not one)."""
    if not isinstance(picture, dict) or not isinstance(picture.get("html"), str) or not picture["html"] or len(picture["html"]) > MAX_HTML:
        return None
    w, h = _num(picture.get("w")), _num(picture.get("h"))
    return picture["html"], _frame(w, h)


def _frame(w: float | None, h: float | None, default: tuple[int, int] = idea_shot.SIZE) -> tuple[int, int]:
    return (int(min(SIZE_MAX, max(SIZE_MIN, w))), int(min(SIZE_MAX, max(SIZE_MIN, h)))) if w and h else default


class PlayMarkMixin:
    """Needs `host`, `state_dir`, `root()`, `settings_now()`, `add`, `changed`, `_state`, `player`, `_play` (gui/ideas.py and gui/ideas_assets.py)."""

    # -- the play's events ------------------------------------------------------------------------------------------

    def _computer(self, args: dict) -> None:
        if _device(args) == "phone":
            raise IdeasError("Play on the computer")

    def _playing(self) -> Any:
        """Play while it plays (without making one), else None."""
        play = self._play
        return play if play is not None and play.state == "playing" else None

    def _ring(self, play_id: str = "") -> "play_signals.Ring | None":
        """This play's ring (made when its first batch comes); None when Play does not play, or `play_id` is another play's. A ring of a play that stopped or was replaced is dropped here."""
        play = self._playing()
        current = play.play_id if play is not None else ""
        with _LOCK:
            rings = self.__dict__.setdefault("_play_rings", {})
            for key in [k for k in rings if k != current]:
                del rings[key]
            if not current or (play_id and play_id != current):
                return None
            return rings.setdefault(current, play_signals.Ring())

    def play_events(self, args: dict) -> dict:
        self._computer(args)
        events = args.get("events")
        if not isinstance(events, list):
            raise IdeasError("Events are a list")
        ring = self._ring(_opt(args, "play"))
        kept = 0
        for raw in events[:MAX_BATCH] if ring is not None else ():
            if (e := _event(raw)) is not None:
                ring.add(e)
                kept += 1
        return {"ok": True, "kept": kept}

    def _slow_ms(self) -> float:
        got = _num(idea_shot._config(self.state_dir).get("preview_slow_ms"))
        return got if got and got > 0 else play_signals.SLOW_MS

    def play_hints(self, args: dict) -> dict:
        self._computer(args)
        ring = self._ring(_opt(args, "play"))
        return {"hints": play_signals.hints(ring.events(), _short(args.get("path"), 300), self._slow_ms()) if ring is not None else []}

    # -- where the place is ----------------------------------------------------------------------------------------

    def _relative(self, files: object) -> list[str]:
        """The files the probe named as paths of the repository: one inside Play's own worktree (the dev build names it so) is made relative to it."""
        play, out = self._play, []
        bases = []
        if play is not None:
            bases = [play.path.as_posix().rstrip("/") + "/", play.path.resolve().as_posix().rstrip("/") + "/"]
        for f in (files if isinstance(files, list) else [])[:play_place.MAX_FILES]:
            if not isinstance(f, str):
                continue
            text = f.replace("\\", "/").removeprefix("file://")
            for base in bases:
                if text.startswith(base):
                    text = text[len(base):]
                    break
            out.append(text)
        return out

    def _parts(self, path: str, files: list[str]) -> dict:
        return play_place.parts(self.state_dir, Path(self.host.repo_root), path, files, pages=self.root(False))

    def play_place(self, args: dict) -> dict:
        self._computer(args)
        path = _path(args.get("path"))
        return {"screen": play_place.screen(self.state_dir, Path(self.host.repo_root), path), "parts": self._parts(path, self._relative(args.get("files")))}

    # -- what the ring knows ---------------------------------------------------------------------------------------

    def _ring_seen(self, path: str) -> tuple[list[dict], list[dict]]:
        """(the page's errors, its failed or slow requests) from this play's ring: the newest ten of each, oldest first; an error said again is counted once."""
        ring = self._ring()
        events = ring.events() if ring is not None else []
        slow = self._slow_ms()
        asked: dict[str, int] = {}
        for e in events:
            if e["kind"] == "request":
                asked[e["path"]] = asked.get(e["path"], 0) + 1
        errors: dict[str, dict] = {}
        requests: list[dict] = []
        for e in events:
            if e["kind"] == "error" and e["path"] == path and e["message"]:
                old = errors.pop(e["message"], None)
                errors[e["message"]] = {"message": e["message"], "stack": e["stack"], "source": e["source"], "count": (old["count"] if old else 0) + 1}
            elif e["kind"] == "request":
                status = e["status"]
                failed = status >= 500 or (400 <= status < 500 and status != 401 and not (status == 404 and asked.get(e["path"], 0) < 2))
                if failed or e["ms"] > slow:
                    requests.append({k: e[k] for k in ("method", "path", "status", "ms", "host") if k in e})
        return list(errors.values())[-idea_play.MAX_ERRORS:], requests[-idea_play.MAX_REQUESTS:]

    # -- the picture -----------------------------------------------------------------------------------------------

    def _draw(self, picture: object, path: str, viewport: object) -> bytes | None:
        """The mark's picture as PNG bytes: the probe's snapshot drawn at the frame's size by the host's Chromium, else the page's path drawn anew from Play (the picture is of the page,
        not of the moment), else None (no browser, no page, a picture larger than a goal may carry)."""
        snap = _html(picture)
        playing = self._playing()
        port = playing.port if playing is not None else None
        view = viewport if isinstance(viewport, dict) else {}
        with tempfile.TemporaryDirectory(prefix="orkboard-mark-") as tmp:
            dest = Path(tmp) / "mark.png"
            ok = False
            if snap is not None:
                html, size = snap
                head = DOCTYPE.match(html)
                page = Path(tmp) / "snapshot.html"       # no script runs while it is drawn: what the page sent is a picture, never a program
                page.write_text(html[:head.end()] + NO_SCRIPTS + html[head.end():] if head else NO_SCRIPTS + html, encoding="utf-8")
                ok = idea_shot.draw(page.as_uri(), dest, size)
            if not ok and port:
                conf = idea_shot._config(self.state_dir)
                ok = idea_shot.draw(idea_shot.url_of(port, idea_shot._path(path, conf)), dest, _frame(_num(view.get("w")), _num(view.get("h")), idea_shot._size(conf)))
            raw = dest.read_bytes() if ok and dest.is_file() else b""
        return raw if raw and len(raw) <= idea_photos.MAX_BYTES and idea_photos._kind(raw) else None

    # -- the mark --------------------------------------------------------------------------------------------------

    def _mark_of(self, args: dict, kind: str, text: str, path: str, box: dict, keep: set[str]) -> dict:
        """What the live product knew at the mark, for the goal's play (the chips left on only; the picture is added by the caller)."""
        play = self._playing()
        here = play_place.screen(self.state_dir, Path(self.host.repo_root), path)
        errors, requests = self._ring_seen(path) if play is not None else ([], [])
        under = idea_play.elements(args.get("under")) if "part" in keep else []
        return {"kind": kind, "text": text, "path": path, "screen": {"id": here["id"], "name": here["name"]} if here else None, "box": box,
                "commit": play.commit if play is not None else "", "at": dt.datetime.now().isoformat(timespec="seconds"), "under": under,
                "errors": errors if "errors" in keep else [], "requests": requests if "requests" in keep else [],
                "lines": play.lines_before(time.time(), idea_play.MAX_LINES) if play is not None and "lines" in keep else [],
                "state": args.get("state") if "state" in keep and isinstance(args.get("state"), dict) and not args["state"].get("none") else None, "picture": ""}

    def _marks_of(self, path: str, under: list[dict], keep: set[str]) -> list[dict]:
        """The parts of the maps the place touches as a goal's `marks`: every map's with `part`, Design's screen alone with only `screen`."""
        if not ({"part", "screen"} & keep):
            return []
        got = self._parts(path, [u["file"] for u in under if u.get("file")])
        rows = [{"map": where, "id": p["id"], "name": p["name"]} for where, parts in got.items() for p in parts if "part" in keep or where == "screens"]
        return idea_lens.clean_marks(rows)

    def _lens_item(self, raw: bytes, mark: dict) -> dict:
        name = (mark["screen"] or {}).get("name") or mark["path"]
        return {"kind": "screen", "image": {"data": base64.b64encode(raw).decode("ascii")}, "name": name[:60],
                "marks": [{**mark["box"], "note": mark["text"]}]}

    def play_mark(self, args: dict) -> dict:
        self._computer(args)
        text = _text(args, "text", ideas.SECTION_CHARS)
        kind, box, path, keep = _kind(args), _box(args.get("box")), _path(args.get("path")), _with(args.get("with"))
        add_to, root = _opt(args, "add_to"), self.root()
        party = _opt(args, "party") or _opt(args, "track")
        if add_to:
            self._joinable(add_to)
        elif party and pitches.is_ideation(root, party):
            raise IdeasError("Ideation judges pitches: send the mark to another party")
        elif not party and kind == "bug":
            party = goal_route.tech_party(root)                       # a bug is Tech's alone, by the Orkmaster's rule, whatever the words say
        mark = self._mark_of(args, kind, text, path, box, keep)
        marks = self._marks_of(path, mark["under"], keep)
        out = self._mark_join(add_to, mark, marks, args, keep) if add_to else self._mark_new(party, text, mark, marks, args, keep)
        slug = out["slug"]
        page = ideas.idea_page(root, slug)
        track = (page.get("track") if page else "") or ""
        tp = ideas.track_page(root, track) if track else None
        self.changed(slug)
        return {**out, "title": (page.title if page else "") or slug, "party": track, "party_title": (tp.title if tp else "") or track,
                "kept": {"picture": bool(mark["picture"]), "errors": len(mark["errors"]), "requests": len(mark["requests"]), "lines": len(mark["lines"]),
                         "state": mark["state"] is not None, "under": len(mark["under"]), "marks": len(marks)}}

    def _mark_new(self, party: str, text: str, mark: dict, marks: list[dict], args: dict, keep: set[str]) -> dict:
        """A new goal with the mark: `ideas.add`'s, the screen lens with its picture, the play kept, a bug read for its failure."""
        raw = self._draw(args.get("picture"), mark["path"], args.get("viewport")) if "screen" in keep else None
        lens = [self._lens_item(raw, mark)] if raw else []
        add = {"text": text, "party": party, "marks": marks, "lens": lens}
        made = None
        for type_id in self._types_for(mark["kind"]):
            try:
                made = self.add({**add, "type": type_id})
                break
            except IdeasError as e:
                if not type_id or " cannot take " not in str(e):
                    raise
        if made is None:
            raise IdeasError("The party takes no goal of this kind")
        slug = made["slug"]
        mark["picture"] = next((a["screen"] for a in idea_lens.read(self.state_dir, slug) if a["kind"] == "screen"), "")
        idea_play.save(self.state_dir, slug, mark)
        self._read_play(slug)
        return {"slug": slug, "type": made["type"], "element": made["element"], "joined": False, **({"route": made["route"]} if "route" in made else {})}

    @staticmethod
    def _types_for(kind: str) -> list[str]:
        """The goal types a mark of `kind` is tried as, in order: its type, then the types that stand in for it (a *feature* a party offers as a shaped one), then none (the party takes none of them: the
        goal is its own, and its kind is kept in its play)."""
        want = KIND_TYPE[kind]
        return [want, *[t.id for t in goal_types.CATALOG if want and t.over == want], ""] if want else [""]

    def _read_play(self, slug: str) -> None:
        """A goal on its route reads its kept play: a bug is a bug, and one whose mark holds a failure `reproduces` (realm/goal_route.py `with_play`)."""
        with ideas.LOCK:
            st = ideas.state(self.state_dir, slug)
            if st["state"] == "routed":
                how = goal_route.with_play(self.root(), self.state_dir, slug, st["route_how"], st["route"])
                if how != st["route_how"]:
                    ideas.save_state(self.state_dir, slug, route_how=how)

    # -- a mark added to a goal --------------------------------------------------------------------------------------

    def _joinable(self, slug: str) -> None:
        if ideas.idea_page(self.root(), slug) is None:
            raise IdeasError("That goal is gone")
        if self._state(slug)["state"] not in goal_route.LINE_STATES:
            raise IdeasError("That goal has started: send the mark as a goal of its own")

    def _mark_join(self, slug: str, mark: dict, marks: list[dict], args: dict, keep: set[str]) -> dict:
        """The mark joins a goal not started: its box on the lens's picture of the same page (else a picture of its own), its play, its text among the goal's turns, its map parts among its marks."""
        lens = [{k: v for k, v in a.items() if k not in ("name", "path")} for a in idea_lens.read(self.state_dir, slug)]
        here = mark["path"].split("?")[0]
        same = next((m["picture"] for m in reversed(idea_play.read(self.state_dir, slug)) if m["picture"] and m["path"].split("?")[0] == here
                     and any(a["kind"] == "screen" and a["screen"] == m["picture"] for a in lens)), "")
        item = next((a for a in lens if a["kind"] == "screen" and a["screen"] == same), None) if same else None
        if item is not None and len(item["marks"]) < idea_lens.MAX_MARKS:
            item["marks"] += idea_lens.clean(self.state_dir, [{"kind": "screen", "screen": same, "marks": [{**mark["box"], "note": mark["text"]}]}])[0]["marks"]
            mark["picture"] = same
        elif len(lens) < idea_lens.MAX_ATTACHED and "screen" in keep and (raw := self._draw(args.get("picture"), mark["path"], args.get("viewport"))):
            made = idea_lens.clean(self.state_dir, [self._lens_item(raw, mark)])
            lens += made
            mark["picture"] = made[0]["screen"]
        idea_lens.save(self.state_dir, slug, lens)
        if marks:
            ideas.save_state(self.state_dir, slug, marks=idea_lens.clean_marks([*(ideas.state(self.state_dir, slug).get("marks") or []), *marks]))
        ideas.add_turn(self.state_dir, slug, "you", mark["text"], "Gist")
        idea_play.save(self.state_dir, slug, mark)
        self._read_play(slug)
        return {"slug": slug, "type": ideas.state(self.state_dir, slug).get("type") or "", "element": idea_element.of(self.state_dir, slug), "joined": True}

    def play_mark_offer(self, args: dict) -> dict:
        """A goal not started that has a mark of this kind on this screen (else on this page), the latest first; `{}` with none."""
        self._computer(args)
        kind, path, root = _kind(args), _path(args.get("path")), self.root(False)
        here = play_place.screen(self.state_dir, Path(self.host.repo_root), path)
        folder = self.state_dir / "ideas"
        slugs = sorted(p.parent.name for p in folder.glob("*/play.json")) if folder.is_dir() else []
        open_ = [s for s in slugs if ideas.idea_page(root, s) is not None and self._state(s)["state"] in goal_route.LINE_STATES]
        found = idea_play.newest(self.state_dir, open_, here["id"] if here else "", kind, path)
        if not found:
            return {}
        page = ideas.idea_page(root, found)
        return {"goal": {"slug": found, "title": (page.title if page else "") or found}}


def play_mark_commands(m: PlayMarkMixin) -> dict:
    """The mark's commands by name (`gui/ideas.py` adds them to its table: `**play_mark_commands(self)`)."""
    return {"ideas.play_events": m.play_events, "ideas.play_place": m.play_place, "ideas.play_hints": m.play_hints,
            "ideas.play_mark": m.play_mark, "ideas.play_mark_offer": m.play_mark_offer}
