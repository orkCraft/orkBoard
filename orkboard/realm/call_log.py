"""📜 Every model call, kept: a project's by day and building, a block's (`kept`) in its own folder.

    with call_log.kept(folder / "calls", "building"):   the calls in this block are kept there, as this side's
        …
    with call_log.of_project(root):                      this thread's calls: the project's day log and ledger
    call_log.keep_days(root)                             from now on, every other call goes to the day's log
    with call_log.bounded(n):                            the read calls here are held to n files: their line says if they went over
    call_log.record(env, "work", harness, model, prompt, stdout, stderr, code, seconds, cost, tokens, …)
    call_log.read(folder)                                the lines, oldest first
    call_log.totals(lines)                               by side, ork and purpose: calls, seconds, tokens, $
    call_log.floor(lines)                                a keeper's read calls before and after the bare floor (spec 97 §4)
    python -m orkboard.realm.call_log floor <project>    … of the project's last 7 days
    call_log.talk_floor(lines)                           a Talk round's calls by their place in the round, and a leader's calls that follow each other (spec 120 §5.1)
    python -m orkboard.realm.call_log talk <project>     … of the project's last 7 days

`calls.jsonl` holds one line per call: when, which side, who (an ork, the steward), what it was for, the tool and
model, its seconds, exit code, cost, tokens and the usage the tool printed (input, output, cache). The call itself
goes gzipped beside it (`<n>-<who>.json.gz`): the prompt, the tool's whole output, its errors, and the way it worked
when the tool keeps one (`trail`: Claude Code's transcript of the session, with its thinking and tool calls; agy's
brain folder). A Claude read call's line says what it read (`reads`, from its stream-json), the bound it was given (`bound`,
`over` when it read more files) and the flags that kept the person's MCP servers and skills out (`bare`). The environment
is never written.

A `kept` block's calls go to its `calls/` (process-wide: it wins). Outside one, a call goes where its caller placed it
on its thread: a project's Board to that project's `.orkcraft/logs/<day>/<building>/` (`of_project`), whichever project
is shown; a call placed nowhere goes to the day log the host named (`keep_days`: the shown project's; realm/day_log.py
keeps and clears those days), else it is not kept. The place also names the call's ledger (sources/telemetry.py
`ledger_at`).

The calls come from every seam that starts an AI tool: an ork's work and a reader (realm/jobs.py) and a one-off answer
(realm/tool_run.py `ask`).
"""
from __future__ import annotations

import contextlib
import contextvars
import datetime as dt
import gzip
import json
import re
import threading
from pathlib import Path

from orkboard.realm import harnesses
from orkboard.sources import telemetry

LINES = "calls.jsonl"
DAYS = Path(".orkcraft") / "logs"
UNPLACED = "town"                 # the day's folder of a call no project made: its name stays on disk, where machines already keep it
TRAIL_MAX = 8 * 1024 * 1024       # characters of a session's trail kept with a call (its end)
_LOCK = threading.Lock()
_KEPT: dict = {"folder": None, "side": "", "days": None}
_COUNT: dict[Path, int] = {}
_HERE: contextvars.ContextVar[tuple[Path | None, Path | None, str] | None] = contextvars.ContextVar(
    "orkcraft_call_place", default=None)                     # this thread's (days root, folder, side)
_BOUND: contextvars.ContextVar[int | None] = contextvars.ContextVar("orkcraft_call_bound", default=None)   # the files a read may read
_SAFE = re.compile(r"[^A-Za-z0-9_-]+")


@contextlib.contextmanager
def kept(folder: Path, side: str = ""):
    """The calls made in this block, on any thread, are kept in `folder` as `side`'s."""
    with _LOCK:
        outer = {k: _KEPT[k] for k in ("folder", "side")}
        folder.mkdir(parents=True, exist_ok=True)
        _KEPT.update(folder=folder, side=side)
    try:
        yield folder
    finally:
        with _LOCK:
            _KEPT.update(outer)


@contextlib.contextmanager
def _placed(place: tuple[Path | None, Path | None, str], ledger: Path | None):
    token = _HERE.set(place)
    try:
        with telemetry.ledger_at(ledger):
            yield
    finally:
        _HERE.reset(token)


@contextlib.contextmanager
def of_project(root: Path):
    """The calls made in this block, on this thread, are kept in `root`'s day log and charged in its ledger, whichever
    project is shown (spec 37 §8): a keeper's or runner's call of a project open but not shown stays its own."""
    with _placed((Path(root), None, ""), telemetry.ledger_of(root)):
        yield


@contextlib.contextmanager
def bounded(files: int | None):
    """The read calls made in this block, on this thread, were told to read `files` files at most: their lines say so, and
    say `over` when they read more (None: no bound). Nothing stops them; the log counts (spec 97 §3)."""
    token = _BOUND.set(files)
    try:
        yield
    finally:
        _BOUND.reset(token)


def keep_days(root: Path | None) -> None:
    """Every call outside a `kept` block that no caller placed (`of_project`) goes to `root`'s day log from now on (None:
    none is kept)."""
    with _LOCK:
        _KEPT["days"] = root


def days_root() -> Path | None:
    """The project whose day log the calls made now go to: the one this thread's calls are placed in (`of_project`), else
    the one `keep_days` named; None when no day log is kept (realm/idea_target.py `floor` reads its calls)."""
    here = _HERE.get()
    return (here[0] if here is not None else None) or _KEPT["days"]


def day_folder(root: Path, day: str, building: str) -> Path:
    return root / DAYS / day / (_SAFE.sub("-", building)[:80] or UNPLACED)


def usage_of(stdout: str) -> dict:
    """The token counts the tool printed, as it named them: the envelope's `usage`, else its last event's."""
    found: dict = {}
    try:
        events = [json.loads(stdout)]
    except ValueError:
        events = harnesses.json_lines(stdout)
    for event in events:
        if not isinstance(event, dict):
            continue
        msg = event.get("message")
        for usage in (event.get("usage"), msg.get("usage") if isinstance(msg, dict) else None, event.get("tokens")):
            if isinstance(usage, dict):
                counts = {k: v for k, v in usage.items() if isinstance(v, int) and not isinstance(v, bool)}
                found = counts or found
    return found


def session_of(stdout: str) -> str:
    """The session the tool says it ran in ("" when it says none): its envelope's, or its stream's last result."""
    env = harnesses.claude_envelope(stdout)
    return str(env.get("session_id") or "") if env else ""


def trail(harness: str, session: str, workdir: Path | None) -> str:
    """How the call went, where the tool keeps it: Claude Code's transcript of the session (its thinking, every tool
    call and result), agy's brain folder; "" for a tool whose output already holds it (codex) or keeps none."""
    from orkboard.sources import sessions
    if not session or _SAFE.search(session):
        return ""                                            # a session id is a name, never a path
    try:
        if harness == "claude" and workdir is not None:
            path = sessions.claude_projects_dir(workdir) / f"{session}.jsonl"
            return path.read_text(encoding="utf-8", errors="replace")[-TRAIL_MAX:] if path.is_file() else ""
        if harness == "agy":
            folder = sessions.agy_brain_dir() / session
            parts = [f"## {p.relative_to(folder)}\n{p.read_text(encoding='utf-8', errors='replace')}"
                     for p in sorted(folder.rglob("*")) if p.is_file()] if folder.is_dir() else []
            return "\n\n".join(parts)[-TRAIL_MAX:]
    except OSError:
        return ""
    return ""


def _reads(harness: str, stdout: str, workdir: Path | None) -> dict:
    """What a read call's line adds (spec 97 §3): the files it read and whether it went over its bound, the bound, and the
    flags that kept the person's MCP servers and skills out of a Claude call. Nothing for a tool that prints no events."""
    out: dict = {}
    bound = _BOUND.get()
    if harness == "claude":
        h = harnesses.get("claude")
        if bare := harnesses.claude_floor(h)[1] if h is not None else []:
            out["bare"] = bare
        if harnesses.claude_events(stdout):
            out["reads"] = harnesses.claude_reads(stdout, workdir or "")
    if bound is not None:
        out["bound"] = bound
        if out.get("reads", {}).get("files", 0) > bound:
            out["over"] = True
    return out


def record(env: dict | None, mode: str, harness: str, model: str, prompt: str, stdout: str, stderr: str,
           code: int, seconds: float, cost: float | None = None, tokens: int | None = None,
           session: str = "", workdir: Path | None = None, who: str = "", purpose: str = "", cost_own: float | None = None) -> None:
    """One call, where calls are kept now. Never raises: a call is not lost for its log. `who` and `purpose` name
    a call that carries no ork (`ORKCRAFT_ORC`) or was not tagged (a one-off `-p`, a connector's look)."""
    orc = str((env or {}).get("ORKCRAFT_ORC") or "")
    building, _, ork = orc.partition("/")
    here = _HERE.get()
    with _LOCK:
        folder, side, days = _KEPT["folder"], _KEPT["side"], _KEPT["days"]
        if folder is None and here is not None:              # a bench run's block wins; else the call's own place
            days, folder, side = here
        if folder is None and days is None:
            return
        if folder is None:
            side = ""
            folder = day_folder(days, dt.date.today().isoformat(), building or telemetry.building_now() or UNPLACED)
        if folder not in _COUNT:
            _COUNT[folder] = len(read(folder))
        _COUNT[folder] += 1
        n = _COUNT[folder]
    who = ork or who or ("" if side == "bare" else "agent")
    raw = f"{n:03d}-{_SAFE.sub('-', who or side or 'call')[:40]}.json.gz"
    session = session or session_of(stdout)
    line = {"n": n, "at": dt.datetime.now().isoformat(timespec="seconds"), "side": side, "who": who,
            "purpose": purpose or telemetry.purpose_now(), "mode": mode, "tool": harness, "model": model,
            "seconds": round(seconds, 1), "code": code, "cost": cost, "tokens": tokens, "usage": usage_of(stdout),
            "session": session, "prompt_chars": len(prompt or ""), "output_chars": len(stdout or ""), "raw": raw}
    for key, name in (("idea", "ORKCRAFT_IDEA"), ("task", "ORKCRAFT_TASK"), ("step", "ORKCRAFT_STEP"), ("party", "ORKCRAFT_PARTY")):     # the board's calls join the event log; a keeper's say their step and party (`talk_floor`)
        if (env or {}).get(name):
            line[key] = str(env[name])
    if mode == "read":
        line.update(_reads(harness, stdout, workdir))
    if cost_own is not None:                 # a resumed session's cost is its running total: this call's own is the difference (spec 86 §1)
        line["cost_own"] = cost_own
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with gzip.open(folder / raw, "wt", encoding="utf-8") as f:
            json.dump({"prompt": prompt, "stdout": stdout, "stderr": stderr,
                       "trail": trail(harness, session, workdir)}, f, ensure_ascii=False)
        with _LOCK, (folder / LINES).open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        pass


def read(folder: Path) -> list[dict]:
    try:
        text = (folder / LINES).read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for row in text.splitlines():
        try:
            line = json.loads(row)
        except ValueError:
            continue
        if isinstance(line, dict):
            out.append(line)
    return out


def raw(folder: Path, line: dict) -> dict:
    """The call itself: its prompt, the tool's output, its errors and its trail ({} when it is gone)."""
    try:
        with gzip.open(folder / str(line.get("raw") or ""), "rt", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def totals(lines: list[dict]) -> list[dict]:
    """The calls by side, then by who and what for: [{side, who, purpose, calls, seconds, tokens, cost, usage}],
    in the order they first came."""
    rows: dict[tuple, dict] = {}
    for line in lines:
        key = (line.get("side") or "", line.get("who") or "", line.get("purpose") or "")
        row = rows.setdefault(key, {"side": key[0], "who": key[1], "purpose": key[2], "calls": 0, "seconds": 0.0,
                                    "tokens": 0, "cost": 0.0, "usage": {}})
        row["calls"] += 1
        row["seconds"] = round(row["seconds"] + float(line.get("seconds") or 0.0), 1)
        row["tokens"] += int(line.get("tokens") or 0)
        row["cost"] = round(row["cost"] + float(line["cost_own"] if line.get("cost_own") is not None else line.get("cost") or 0.0), 4)   # a resumed session counted once
        for k, v in (line.get("usage") or {}).items():
            if isinstance(v, int):
                row["usage"][k] = row["usage"].get(k, 0) + v
    return list(rows.values())


# -- the bare floor, measured (spec 97 §4) ------------------------------------------------------------------------------

def _median(values: list) -> float | None:
    import statistics
    return round(statistics.median(values), 4) if values else None


def floor(lines: list[dict]) -> dict:
    """What a keeper's one-turn read calls (`read`, a `plan` or `sort`, Claude's, ended well) cost the cache and the person,
    before and after the bare floor: {"before": {...}, "after": {...}}, each side its `calls` and the median of the usage's
    `cache_creation_input_tokens` and of the `cost`, a line with `bare` being after."""
    from orkboard.realm import idea_target
    sides: dict[str, list[dict]] = {"before": [], "after": []}
    for line in lines:
        if (line.get("mode") == "read" and line.get("tool") == "claude" and line.get("purpose") in idea_target.FLOOR_PURPOSES
                and not line.get("code") and (line.get("usage") or {}).get("output_tokens", 0) <= idea_target.FLOOR_OUT):
            sides["after" if line.get("bare") else "before"].append(line)
    return {side: {"calls": len(rows),
                   "cache_creation_input_tokens": _median([r["usage"]["cache_creation_input_tokens"] for r in rows
                                                           if isinstance((r.get("usage") or {}).get("cache_creation_input_tokens"), int)]),
                   "cost": _median([r["cost"] for r in rows if isinstance(r.get("cost"), (int, float)) and not isinstance(r["cost"], bool)])}
            for side, rows in sides.items()}


TALK_STEP = "talk_round"      # the keeper's step a leader's call in Talk is (core/idea_talk.py); its line says so (`step`) and says the party (`party`)
ROUND_GAP_S = 90              # calls of one goal that end further apart than this are not one round's
CACHE_TTL_S = 300             # Claude's prompt cache lives five minutes: a leader's next call inside it can read what the first wrote
SAY_FROM = 3                  # the least calls a side needs for the floor to say what it does


def _stamp(line: dict) -> float:
    try:
        return dt.datetime.fromisoformat(str(line.get("at"))).timestamp()
    except ValueError:
        return 0.0


def _cache(line: dict, key: str) -> int:
    got = (line.get("usage") or {}).get(key)
    return got if isinstance(got, int) and not isinstance(got, bool) else 0


def _usage_of(rows: list[dict]) -> dict:
    """`{calls, wrote, read, cache_creation_input_tokens, cache_read_input_tokens}`: how many calls wrote the cache anew (a creation and no read) and how many read it, and the medians of both counts."""
    made, read = "cache_creation_input_tokens", "cache_read_input_tokens"
    return {"calls": len(rows), "wrote": sum(_cache(r, made) > 0 and _cache(r, read) == 0 for r in rows), "read": sum(_cache(r, read) > 0 for r in rows),
            made: _median([_cache(r, made) for r in rows]), read: _median([_cache(r, read) for r in rows])}


def talk_floor(lines: list[dict]) -> dict:
    """What a leader's call in Talk does to the cache (spec 120 §5.1), from the `talk_round` lines (a line says its `step` and `party`): grouped by goal into rounds (a party twice, or a gap above
    `ROUND_GAP_S`, begins the next), each call by its place in its round (`first`, `rest`), and the calls of one leader that follow a call of its own within `CACHE_TTL_S` (`again`).
    `{calls, goals, rounds, first, rest, again, stagger, system_prompt}`, each side as `_usage_of` has it. `stagger` is true when most of the `rest` wrote the shared prefix again (a creation and
    no read: starting the first leader alone would let the rest read it); `system_prompt` is true when most of the `again` read nothing (the map is not read from a cache between two calls of one
    leader: its text belongs in the system prompt). Both are false with fewer than `SAY_FROM` calls to say it. A line from before lines said their step is not counted."""
    rows = sorted((r for r in lines if r.get("step") == TALK_STEP and r.get("idea") and not r.get("code")), key=lambda r: (_stamp(r), r.get("n") or 0))
    first: list[dict] = []
    rest: list[dict] = []
    rounds = 0
    by_goal: dict[str, list[dict]] = {}
    for r in rows:
        by_goal.setdefault(str(r["idea"]), []).append(r)
    for goal in by_goal.values():
        seen: set[str] = set()
        last = 0.0
        for r in goal:
            at, party = _stamp(r), str(r.get("party") or "")
            if not seen or party in seen or at - last > ROUND_GAP_S:
                seen, rounds = set(), rounds + 1
                first.append(r)
            else:
                rest.append(r)
            seen.add(party)
            last = at
    again: list[dict] = []
    before: dict[str, float] = {}
    for r in rows:
        who = str(r.get("party") or "")
        if who and who in before and _stamp(r) - before[who] <= CACHE_TTL_S:
            again.append(r)
        before[who] = _stamp(r)
    out = {"calls": len(rows), "goals": len(by_goal), "rounds": rounds, "first": _usage_of(first), "rest": _usage_of(rest), "again": _usage_of(again)}
    out["stagger"] = out["rest"]["calls"] >= SAY_FROM and out["rest"]["wrote"] * 2 > out["rest"]["calls"]
    out["system_prompt"] = out["again"]["calls"] >= SAY_FROM and out["again"]["read"] * 2 < out["again"]["calls"]
    return out


def week(root: Path, days: int = 7, today: dt.date | None = None) -> list[dict]:
    """The lines of the project's last `days` days (`.orkcraft/logs/<day>/*/calls.jsonl`)."""
    since = ((today or dt.date.today()) - dt.timedelta(days=days - 1)).isoformat()
    out: list[dict] = []
    try:
        folders = sorted(d for d in (Path(root) / DAYS).iterdir() if d.is_dir() and d.name >= since)
    except OSError:
        return out
    for day in folders:
        for building in sorted(p for p in day.iterdir() if p.is_dir()):
            out += read(building)
    return out


def main(argv: list[str] | None = None) -> int:
    """`python -m orkboard.realm.call_log floor <project>`: the measure of the project's last 7 days, printed; `talk <project>`: a Talk round's calls and the cache (spec 120 §5.1)."""
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] not in ("floor", "talk"):
        print("usage: python -m orkboard.realm.call_log floor|talk <project>", file=sys.stderr)
        return 2
    if args[0] == "talk":
        got = talk_floor(week(Path(args[1])))
        print(f"{got['calls']} talk_round calls · {got['goals']} goals · {got['rounds']} rounds")
        for side, what in (("first", "the first call of a round"), ("rest", "the calls after the first"), ("again", "a leader's next call within five minutes")):
            row = got[side]
            print(f"{side} ({what}): {row['calls']} calls · wrote the cache anew: {row['wrote']} · read it: {row['read']}"
                  f" · written, median: {row['cache_creation_input_tokens']} · read, median: {row['cache_read_input_tokens']}")
        print(f"the calls after the first write the shared prefix again: {'yes: a staggered start would pay' if got['stagger'] else 'no (or too few calls to say)'}")
        print(f"a leader's map is not read from the cache between its calls: {'yes: the system prompt would pay' if got['system_prompt'] else 'no (or too few calls to say)'}")
        return 0
    got = floor(week(Path(args[1])))
    for side, what in (("before", "without the bare floor"), ("after", "on the bare floor")):
        row = got[side]
        print(f"{side} ({what}): {row['calls']} calls · cache written, median: {row['cache_creation_input_tokens']} tokens"
              f" · cost, median: {'$' + format(row['cost'], '.4f') if row['cost'] is not None else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
