"""The Board's Target (docs/specs/35-goals-window.md §1): thrift · balance · quality picks the tier and the reasoning
(effort) of every step of the Board, the keeper's and the orks'; and the clock the Board's reserve reads.

    pick("draft", "balance")                       # ("elder", "medium")
    pick("op_act", "balance")                      # ("laborer", ""): an operation's action (spec 38 §4)
    keeper_pick("talk", "quality", "haiku")        # ("haiku", "high"): the Taskmaster's own model wins
    task_pick("warrior", "thrift", "")             # ("laborer", "low"): Grunt runs on the shifted tier
    target_for(settings, party)                    # a party's size's Target (lean thrift, standard balance, full quality), else the setting (spec 75 §3)
    in_night("01:00-07:00", now)                   # inside the night window (the machine's local time)
    reserve_held(limits, settings, now)            # the reserve left for the person: None, or until when
    week(limits, now), pace(limits, now)           # the Claude week's share left against the share of it still to come (spec 44 §1)

One Target per Board, for the whole route board → pool → gate (decisions §44.3, §47.6). A role with a model set
(spec 34 §3) runs on it; the Target still gives the effort. No face, no model.
"""
from __future__ import annotations

import datetime as dt
import math
import statistics
import time
from pathlib import Path
from typing import Any

from orkboard.realm import plans

TARGETS = ("thrift", "balance", "quality")
DEFAULT = "balance"
EFFORTS = ("low", "medium", "high", "xhigh", "max")      # the Claude CLI's `--effort` levels
STEPS = ("goal", "draft", "answer", "talk", "plan", "task", "pitch_view", "pitch_case", "pitch_decide", "collide", "kind", "route", "talk_round", "diagnose", "decide", "section_first", "section", "join", "project_q")
PITCH_STEPS = ("pitch_view", "pitch_case", "pitch_decide")   # a pitch's three calls (spec 65 §3, core/idea_judge.py)
SIZES = ("lean", "standard", "full")                     # a party's size (spec 75 §3): its Target, for its goals
SIZE_TARGET = {"lean": "thrift", "standard": "balance", "full": "quality"}
TIER_ROLE = "elder"                                    # the Taskmaster's default: its model is not the person's pick

# step → target → (tier, effort); a task's tier is relative: -1 one lighter, 0 its own, +1 one heavier.
MATRIX: dict[str, dict[str, tuple[Any, str] | None]] = {
    "goal": {"thrift": ("elder", "medium"), "balance": ("elder", "high"), "quality": ("elder", "xhigh")},
    # Lean (thrift) runs the draft, its answer and the talk on the Seasoned tier: a leader's call costs $0.18-0.22 on the
    # Veteran tier however little it writes (spec 86 §5); its goal reading and plan stay on the Veteran
    "draft": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    # the answer to a spec's questions (§0) is not in the spec's table: it finishes the draft, so it runs as the draft
    "answer": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "talk": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "plan": {"thrift": ("elder", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    # a party's leader accepts it against its metrics when the person asks, for a party with metrics of before (core/idea_lead.py; spec 50 §2.2)
    "accept": {"thrift": ("elder", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "task": {"thrift": (-1, "low"), "balance": (0, "medium"), "quality": (1, "high")},
    # a pitch's views, the case against and the Investor's decision (spec 65 §3): no effort on the laborer tier
    "pitch_view": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    "pitch_case": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    "pitch_decide": {"thrift": ("warrior", "medium"), "balance": ("elder", "low"), "quality": ("elder", "medium")},
    # the Orkmaster's judge (spec 71 §2): two goals that touch the same files, a collision or a coincidence; the cheaper tier
    "collide": {"thrift": ("warrior", "low"), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    # what an empty folder is for (spec 75 §4.2): the Orkmaster reads one line into a kind, on the cheaper tier as its judge
    "kind": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    # a goal's route when code finds no party (spec 99 §4): the Orkmaster names the parties in one call, on the cheaper tier as its `kind`; the route's cost
    # counts the Orkmaster's decision and join at this tier too (realm/goal_route.py)
    "route": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    # Talk (spec 99 §5): a call a leader of the route, at once, on the cheaper tier as the Orkmaster's `route`; and a bug's diagnosis (one call of Tech's, which
    # reads a few files), on the tiers of the Orkmaster's judge `collide`
    "talk_round": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    "diagnose": {"thrift": ("warrior", "low"), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    # The project's questions at the first start (spec 99 §8): Product's leader (in a game Game design's) reads the README and the docs, no tools, on the cheaper tier as Talk's round
    "project_q": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    # The decision and the sections (spec 99 §6, §7): the Orkmaster words the decision and joins the sections on the cheaper tier as its `route`, no tools; every leader of
    # the route writes its section at once, reading a few files as the draft did: the first step's leader on its party's tier (the draft's rows), the others on the
    # cheaper one (the diagnosis's rows)
    "decide": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    "section_first": {"thrift": ("warrior", "low"), "balance": ("elder", "medium"), "quality": ("elder", "high")},
    "section": {"thrift": ("warrior", "low"), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    "join": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
    # Operations' calls (docs/specs/38-operations.md §4), under Operations' own Target: no effort on the laborer tier
    "op_prepare": {"thrift": ("warrior", "low"), "balance": ("warrior", "medium"), "quality": ("elder", "medium")},
    "op_act": {"thrift": ("laborer", ""), "balance": ("laborer", ""), "quality": ("warrior", "low")},
    "op_learn": {"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")},
}
OP_STEPS = ("op_prepare", "op_act", "op_learn")


# §0: one call, one job. What a keeper call is given is built by code and cut to a cap (characters of the prompt, the
# call's own instructions not counted); how many files it may read; its budget in USD (`--max-budget-usd`) in balance,
# half in thrift, double in quality.
CONTEXT = {"goal": 12_000, "draft": 8_000, "answer": 8_000, "talk": 6_000, "plan": 10_000, "accept": 10_000,
           "op_prepare": 12_000, "op_act": 6_000, "op_learn": 6_000,
           "pitch_view": 6_000, "pitch_case": 6_000, "pitch_decide": 8_000, "collide": 3_000, "kind": 1_500, "route": 2_500,
           "talk_round": 8_000, "diagnose": 10_000, "decide": 8_000, "section_first": 12_000, "section": 12_000, "join": 8_000, "project_q": 12_000}
READS = {"goal": 8, "draft": 6, "plan": 6, "talk": 2, "answer": 2, "accept": 4,
         "pitch_view": 4, "pitch_case": 0, "pitch_decide": 0, "collide": 0, "kind": 0, "route": 0,
         "talk_round": 0, "diagnose": 4, "decide": 0, "section_first": 6, "section": 6, "join": 0, "project_q": 0}    # a view's reads: the Engineering view's only (the others get no tools); a leader's Talk reads no file (its map's text is enough: §156.8)
CAPS = {"goal": 1.00, "draft": 0.60, "answer": 0.40, "talk": 0.20, "plan": 0.60, "accept": 0.60,
        "op_prepare": 0.30, "op_act": 0.10, "op_learn": 0.10, "pitch_view": 0.08, "pitch_case": 0.06, "pitch_decide": 0.20, "collide": 0.05, "kind": 0.03, "route": 0.03,
        "talk_round": 0.08, "diagnose": 0.20, "decide": 0.08, "section_first": 0.60, "section": 0.30, "join": 0.08, "project_q": 0.10}
BUDGET_SHARE = {"thrift": 0.5, "balance": 1.0, "quality": 2.0}


# What one call of a tier costs however little it writes (Claude Code's own context, written to the cache anew each time:
# spec 86 §5), measured from the last calls when the day log has them, else this table.
FLOOR = {"elder": 0.25, "warrior": 0.10, "laborer": 0.03}
FLOOR_CALLS = 10                                         # the median of this many of the last one-turn keeper calls
FLOOR_FROM = 3                                           # … and only when at least this many were read
FLOOR_PURPOSES = ("plan", "sort")                        # a keeper call's purpose in the log (core/idea_keeper.py)
FLOOR_OUT = 400                                          # a one-turn call wrote at most this many tokens
FLOOR_DAYS = 4                                           # day folders back that are read
FLOOR_TTL_S = 300                                        # a measure is kept this long
HEADROOM = 1.5                                           # a budget is never under this many floors
_FLOORS: dict[tuple, tuple[float, float]] = {}


def _kept_costs(root: Path, tier: str, tool: str) -> list[float]:
    """The costs of the last FLOOR_CALLS one-turn keeper calls of `tier` on `tool` in `root`'s day log, newest first."""
    from orkboard.realm import call_log, harnesses
    try:
        days = sorted((d for d in (root / call_log.DAYS).iterdir() if d.is_dir()), reverse=True)[:FLOOR_DAYS]
    except OSError:
        return []
    rows: list[dict] = []
    for day in days:
        for building in sorted(p for p in day.iterdir() if p.is_dir()):
            rows += [r for r in call_log.read(building) if r.get("tool") == tool and r.get("mode") == "read"
                     and r.get("purpose") in FLOOR_PURPOSES and not r.get("code")
                     and isinstance(r.get("cost"), (int, float)) and r["cost"] > 0
                     and (r.get("usage") or {}).get("output_tokens", 0) <= FLOOR_OUT
                     and harnesses.tier_of_model(str(r.get("model") or "")) == tier]
        if len(rows) >= FLOOR_CALLS:
            break
    rows.sort(key=lambda r: str(r.get("at") or ""), reverse=True)
    return [float(r["cost"]) for r in rows[:FLOOR_CALLS]]


def floor(tier: str, tool: str = "claude") -> float:
    """The least one call of `tier` on `tool` costs, in USD: the median cost of the last ten one-turn keeper calls of it in
    the shown project's day log (`calls.jsonl`, realm/call_log.py), else the table `FLOOR`. Kept for five minutes."""
    from orkboard.realm import call_log
    root = call_log.days_root()
    key = (str(root), tier, tool)
    now = time.monotonic()
    got = _FLOORS.get(key)
    if got is not None and now - got[1] < FLOOR_TTL_S:
        return got[0]
    costs = _kept_costs(root, tier, tool) if root is not None else []
    value = round(statistics.median(costs), 4) if len(costs) >= FLOOR_FROM else FLOOR.get(tier, FLOOR["warrior"])
    _FLOORS[key] = (value, now)
    return value


def budget(step: str, target: str) -> float | None:
    """A keeper call's budget in USD under the Target; None for a step with no cap. Never under HEADROOM times the floor of
    the tier the step runs on under the Target (spec 86 §5): a cap under what one call costs ends every call of it."""
    if step not in CAPS:
        return None
    target = target if target in TARGETS else DEFAULT
    cap = CAPS[step] * BUDGET_SHARE.get(target, 1.0)
    got = pick(step, target) if step in MATRIX else None
    if got is not None:
        cap = max(cap, math.ceil(HEADROOM * floor(got[0]) * 100 - 1e-6) / 100)
    return round(cap, 2)


def cut(parts: list[tuple[str, str]], cap: int) -> str:
    """A call's context from its parts ((heading, text), in the order they matter), cut so the whole stays within
    `cap` characters: a part that does not fit is cut, the ones after it are left out."""
    out, left = [], cap
    for head, text in parts:
        block = f"{head}:\n{(text or '').strip() or '(none)'}\n\n"
        if len(block) <= left:
            out.append(block)
            left -= len(block)
            continue
        if left > len(head) + 40:
            out.append(block[:left - 2].rstrip() + "…\n")
        break
    return "".join(out)


def target_of(settings: dict | None) -> str:
    value = (settings or {}).get("target")
    return value if value in TARGETS else DEFAULT


def target_for(settings: dict | None, party: Any = None) -> str:
    """The Target a party's goals work at (spec 75 §3): its size's (`lean` thrift, `standard` balance, `full` quality), else the setting's
    (`target_of`: a party made before has no size). `party`: a party's row or page (anything with `.get("size")`) or its size as text."""
    size = party if isinstance(party, str) else (party.get("size") if party is not None else None)
    return SIZE_TARGET.get(size) or target_of(settings)


def pick(step: str, target: str, tier: str = "warrior") -> tuple[str, str] | None:
    """(tier, effort) of a step under a target; None when the target skips the step. `tier`: a task's planned tier."""
    row = MATRIX[step].get(target if target in TARGETS else DEFAULT)
    if row is None:
        return None
    what, effort = row
    return (plans.shift(tier, what) if step == "task" else what), effort


def keeper_pick(step: str, target: str, taskmaster: str = TIER_ROLE) -> tuple[str, str] | None:
    """A keeper step's (model or tier, effort): the Taskmaster's model, when it is not its default elder, replaces
    the tier; the Target still gives the effort."""
    got = pick(step, target)
    if got is None:
        return None
    tier, effort = got
    return (taskmaster if taskmaster and taskmaster != TIER_ROLE else tier), effort


def task_pick(tier: str, target: str, role_model: str = "") -> tuple[str, str]:
    """A task's (model or tier it runs on, effort): a role with a model keeps it; Grunt ("") the shifted tier."""
    shifted, effort = pick("task", target, tier or "warrior")
    return (role_model or shifted), effort


def tier_of(model: str) -> str:
    """The tier a model or tier counts as in an estimate (a model the tables do not know: warrior)."""
    if model in plans.tiers.TIERS:
        return model
    from orkboard.realm import harnesses
    return harnesses.tier_of_model(model) or "warrior"


# -- the night and the reserve (§6, §7) -------------------------------------------------------------------------

def _minutes(text: str) -> int:
    hh, mm = text.split(":")
    return int(hh) * 60 + int(mm)


def night_start(spec: str, now: dt.datetime) -> dt.datetime | None:
    """When the night window `now` is in began ("01:00-07:00", local time; it may cross midnight); None outside it."""
    try:
        a, b = (_minutes(x) for x in str(spec).split("-"))
    except ValueError:
        return None
    m = now.hour * 60 + now.minute
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if a < b:
        return day + dt.timedelta(minutes=a) if a <= m < b else None
    if m >= a:
        return day + dt.timedelta(minutes=a)
    if m < b:
        return day - dt.timedelta(days=1) + dt.timedelta(minutes=a)
    return None


def in_night(spec: str, now: dt.datetime | None = None) -> bool:
    return night_start(spec, now or dt.datetime.now()) is not None


def left_of(limits, provider: str = "claude") -> float | None:
    """The smallest share left among the tool's windows, None when none was read."""
    left = [lim.remaining for lim in limits or () if getattr(lim, "provider", "") == provider
            and getattr(lim, "remaining", None) is not None]
    return min(left) if left else None


def reserve(settings: dict | None, night: bool) -> float:
    s = settings or {}
    key, default = ("reserve_night", 0.1) if night else ("reserve_day", 0.3)
    value = s.get(key, default)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


MARGIN = 0.10                                            # the week is ahead of its pace by at least this much (spec 44 §1)
SOON_S = 3600                                            # within this long of the five-hour window's reset, its reserve is the night's
WEEK_S = 7 * 24 * 3600


def week(limits, now: float, provider: str = "claude") -> dict | None:
    """The tool's weekly window as {"left", "rest", "reset"}: its share left, the share of the week still to come
    ((reset − now) / 7 days, between 0 and 1) and its reset in epoch seconds. None when no weekly limit has a share
    and a reset read (not read, an error, another tool, an API key): every rule that reads the pace is then today's."""
    from orkboard.realm import status
    rows = [(lim.remaining, r) for lim in limits or () if getattr(lim, "provider", "") == provider and getattr(lim, "window", "") == "weekly"
            and getattr(lim, "remaining", None) is not None and (r := status._reset_s(lim)) is not None]
    if not rows:
        return None
    left, reset = min(rows)                               # the tightest, when a tool has several
    return {"left": left, "rest": min(1.0, max(0.0, (reset - now) / WEEK_S)), "reset": reset}


def pace(limits, now: float, provider: str = "claude") -> str | None:
    """The week's pace: "ahead" (its share left at least MARGIN above the share to come), "behind" (below it), else
    "even"; None with no week."""
    got = week(limits, now, provider)
    if got is None:
        return None
    if got["left"] - got["rest"] >= MARGIN - 1e-9:
        return "ahead"
    return "behind" if got["left"] < got["rest"] else "even"


def reserve_held(limits, settings: dict | None, now: float, provider: str = "claude") -> float | None:
    """What starts by itself waits while any of the tool's windows has its share or less left (by day the day's reserve, inside
    the night window the night's): until when (epoch seconds), else None. By day, within SOON_S of the five-hour window's
    (`session`) reset and while the week is not behind, that window's share is the night's. With no limits read for the
    tool, no reserve applies; with no window near its reset this is the smallest window against one share."""
    rows = [lim for lim in limits or () if getattr(lim, "provider", "") == provider and getattr(lim, "remaining", None) is not None]
    if not rows:
        return None
    from orkboard.realm import status
    night = in_night(str((settings or {}).get("night") or "01:00-07:00"), dt.datetime.fromtimestamp(now))
    eased = not night and pace(limits, now, provider) in ("ahead", "even")
    spent = []
    for lim in rows:
        share = reserve(settings, night)
        reset = status._reset_s(lim)
        if eased and getattr(lim, "window", "") == "session" and reset is not None and 0 < reset - now <= SOON_S:
            share = reserve(settings, True)               # the hour before the five hours come back: they ease the reserve
        if lim.remaining <= share:
            spent.append(lim)
    if not spent:
        return None
    resets = [r for lim in spent if (r := status._reset_s(lim)) is not None and r > now]
    return max(resets) if resets else now + status.UNKNOWN_RESET_S


def gate(plan: dict, limits, board: dict, now: float, provider: str = "claude") -> float | None:
    """What holds a passed plan's tasks besides the spent window: the reserve's reset (it started by itself), else None (spec 35
    §6). A plan of before the night went, with `start_at: "night"`, is read as one the Board passed by itself: it waits for the
    reserve as today's do, and is never held for a night window. The reserve is that of `provider`, the tool the task runs on (a
    tool with no limits read has none)."""
    if plan.get("passed_by") == "auto" or plan.get("start_at") == "night":
        return reserve_held(limits, board, now, provider)
    return None


WINDOW_WORDS = {"weekly": "week", "session": "five hours"}


def hold_line(limits, provider: str, kind: str, until: float, now: float) -> str:
    """What a task held by the person's reserve (`kind` "reserve") or by the week's pace ("week") says, in plain words, with the tool it
    waits on, its share left and until when: *Waits for Claude's limit: 14 % of the week left, kept for you until 12:00* (the owner, 26
    October: a held task must say what is happening). A tool with no share read says only whose limit it is."""
    from orkboard.realm import harnesses
    tool = harnesses.title(provider)
    rows = [lim for lim in limits or () if getattr(lim, "provider", "") == provider and getattr(lim, "remaining", None) is not None]
    if kind == "week":
        got = week(limits, now, provider)
        share = f" {tool} has {round(got['left'] * 100)} % of its week left." if got else ""
        return f"Waits for the week's pace:{share} The Board holds its own work until {_when(until, now)}."
    if not rows:
        return f"Waits for {tool}'s limit: kept for you until {_when(until, now)}"
    low = min(rows, key=lambda lim: lim.remaining)
    window = WINDOW_WORDS.get(getattr(low, "window", ""), getattr(low, "window", "") or "limit")
    return f"Waits for {tool}'s limit: {round(low.remaining * 100)} % of the {window} left, kept for you until {_when(until, now)}"


def _when(at: float, now: float) -> str:
    """*12:00* today, else *Mon 09:00*."""
    d, today = dt.datetime.fromtimestamp(at), dt.datetime.fromtimestamp(now).date()
    return f"{d:%H:%M}" if d.date() == today else f"{d:%a %H:%M}"
