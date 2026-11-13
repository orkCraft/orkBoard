"""Machine settings (`$XDG_CONFIG_HOME/orkcraft/settings.json`): what onboarding asks once per machine.

    s = settings.load()              # never raises; defaults for anything missing or broken
    s.tools["claude"].billing        # "subscription" | "api"
    s.quiet                          # 🌙 do-not-disturb hours (schedule.py)
    s.usage, s.install_id            # anonymous usage stats: None not asked yet (core/usage.py)
    s.updates                        # auto | critical | ask: which updates install by themselves (core/updates.py)
    s.phones, s.phone_port           # the paired phones (only their tokens' hashes) and their listener's port (gui/pairing.py)
    s.dnd_until                      # Do not disturb: "" off, "on" until turned off, else an ISO time (gui/phone_push.py)
    s.ideas                          # the board's keeper and runner: batch_minutes, idle_hours, max_parallel, … (IDEAS;
                                     # `wiki`, the Board's Wiki folder, only when set: spec 37 §3.5); a project's own
                                     # Board settings start from them (`board_of`)
    s.projects_open                  # the open projects' folders, in the switcher's order (spec 37 §8)
    s.projects_recent                # the projects last shown, newest first (at most PROJECTS_RECENT)
    settings.save(s)

    board_of(repo_root, s.ideas)     # a project's Board settings: `<repo>/.orkcraft/board.json` over the machine's
    save_board(repo_root, values)    # … written there (machine-local, git-ignored)

The tools the operator leads and how each is paid for, and the quiet hours of their day (design:
docs/design/onboarding.md). A key an older settings file has that is not read here (`look`, `mode`, `work`,
`autonomy`, `profile`, `focus`, `ops`, …) still loads, is ignored, and is no longer written.
Orkboard never stores an API key here: `billing` only says how the CLI is paid for.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from orkboard.env import getenv
from orkboard.realm import harnesses, hours, look_wait
from orkboard.settings_ways import (PUSH_WAYS, NIGHT_RUNGS, push_way, clean_push_way, pushes_dev, pushes_main,  # noqa: F401  (said from here as before)
                                    clean_night_leaders, night_rung, night_leaders, night_values)
from orkboard.settings_clean import (KEEP_AWAKE, PUSH_KEY, awake_mode, clean_dnd, clean_phones, clean_push)  # noqa: F401
from orkboard.schedule import Span

TOOLS = harnesses.ids()
BILLINGS = ("subscription", "api")
UPDATES = ("auto", "critical", "ask")   # core/updates.py POLICIES
# Fix it (spec 119 §2.4, core/repair.py): the command that starts Claude Code's Remote Control on Orkboard's own code.
REPAIR_COMMAND = ("claude", "remote-control", "--name", "Fix Orkboard", "--permission-mode", "auto")
# The board's keeper and runner (spec 29a): how often the batch reads new ideas, when a talk's session is
# compacted, how many tasks run at once, which branch they merge into (`dev`: the testers' default, spec 33 §4),
# whether it is pushed (off), and whether every result waits for the person at Review (off: a result that holds lands by
# itself, spec 84; `review_v` 2 marks a file that was moved to that default once, the notice said once: `review_notice`).
# Spec 35: the Board's Target (thrift · balance · quality), whether a safe plan starts by itself, the night's window
# (local time), the share of the window kept for the person by day and at night, and the repository's own risky paths.
# `batch_minutes` is kept, unused (the batch went in spec 35), so older settings keep loading.
REVIEW_V = 2
LOOK_WAIT_DEFAULT = "2h"            # spec 144 A.1: Give me time to look
IDEAS = {"batch_minutes": 30, "idle_hours": 24, "max_parallel": 1, "merge_into": "dev", "push": False, "review": False,
         "review_v": REVIEW_V,
         "target": "balance", "autostart": True, "night": "01:00-07:00", "reserve_day": 0.3, "reserve_night": 0.1,
         "risk_paths": [], "work_at_night": False,   # spec 121 C: plans that would start by themselves wait for the night's window (off until the person says)
         "look_wait": LOOK_WAIT_DEFAULT,   # spec 144 A: how long a spec made waits for the person's look before its plan is passed by itself (realm/look_wait.py)
         "hours": [], "presence": None}   # spec 138 B.1, spec 139 C.1: the person's hours (realm/hours.py) and the door's hold
IDEA_TARGETS = ("thrift", "balance", "quality")
LOOK_WAITS = ("30m", "2h", "tonight", "none")           # spec 144 A.1: *Give me time to look*
NIGHT = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$")
PROJECTS_RECENT = 10                     # the projects the switcher's Recent remembers (spec 37 §8)
PROJECTS_OPEN = 20                       # the most projects open at once
# The Board's settings that are the project's (spec 37 §8): read from `<repo>/.orkcraft/board.json`, the machine's
# `ideas` being the defaults a new project starts from; `risk_paths` is the tracked `orkcraft.toml`'s `[board]`.
BOARD = ("target", "autostart", "night", "work_at_night", "merge_into", "push", "review", "review_v", "wiki", "max_parallel", "reserve_day",
         "reserve_night", "hours", "presence", "look_wait", "night_rung", "night_leaders")
BOARD_FILE = Path(".orkcraft") / "board.json"


@dataclass
class ToolChoice:
    enabled: bool = False
    billing: str = "subscription"


@dataclass
class MachineSettings:
    tools: dict[str, ToolChoice] = field(default_factory=lambda: {t: ToolChoice() for t in TOOLS})
    onboarded: bool = False       # the machine's part of onboarding is done
    quiet: Span | None = None     # 🌙 do-not-disturb hours; None = off
    usage: bool | None = None     # anonymous usage stats (core/usage.py): None until the operator answers
    install_id: str = ""          # a random id while they share them; forgotten when they stop
    keep_awake: str = "carts"     # KEEP_AWAKE: when the computer does not sleep by itself, on power (gui/keep_awake.py)
    review_notice: bool = False   # "results that hold now land in dev by themselves" is to be said once (spec 84 §1; the faces clear it)
    awake_offered: bool = False   # "keep it awake for the phone" was asked once, when a phone paired (js/phones.js; gui/keep_awake.py `offer`)
    updates: str = "critical"     # which updates install by themselves when Orkboard opens (core/updates.py)
    repair_command: list = field(default_factory=lambda: list(REPAIR_COMMAND))   # what Fix it starts on Orkboard's own code (core/repair.py, spec 119)
    main_tool: str = ""           # the tool decisions run on (realm/harnesses.py); "" the first one on
    tool_order: list = field(default_factory=list)   # the order the work moves on in: the AI tools in the person's order (the potions', left to right; decisions §232.5); [] the registry's
    # The phones paired with this machine (docs/design/mobile.md §2): id, name, the SHA-256 of the device token
    # (never the token), when paired and when last seen. No project's file ever holds them.
    phones: list = field(default_factory=list)
    phone_port: int = 0           # the phone listener's port, kept so a paired phone finds it again; 0 not chosen
    dnd_until: str = ""           # Do not disturb: "" off, "on" until turned off, else when it ends (gui/phone_push.py)
    # The model a tier runs on, per tool, chosen in Settings → AI tools: {"agy": {"elder": "gemini-3.1-pro-high"}}.
    # A family (`gemini-flash-high`) is its newest model; absent, the tier's own family (realm/harnesses.py `pick`).
    tier_models: dict = field(default_factory=dict)
    ideas: dict = field(default_factory=lambda: dict(IDEAS))   # the board's keeper and runner (IDEAS)
    projects_open: list = field(default_factory=list)     # the open projects' folders, in the switcher's order
    projects_recent: list = field(default_factory=list)   # the projects last shown, newest first

    def to_dict(self) -> dict:
        return {
            "tools": {t: {"enabled": c.enabled, "billing": c.billing} for t, c in self.tools.items()},
            "onboarded": self.onboarded,
            "quiet": self.quiet.to_dict() if self.quiet else None,
            "usage": {"share": self.usage, "id": self.install_id},
            "keep_awake": self.keep_awake,
            "awake_offered": self.awake_offered,
            "review_notice": self.review_notice,
            "updates": self.updates,
            "repair_command": list(self.repair_command),
            "main_tool": self.main_tool,
            "tool_order": list(self.tool_order),
            "phones": [dict(p) for p in self.phones],
            "phone_port": self.phone_port,
            "dnd_until": self.dnd_until,
            "tier_models": {t: dict(m) for t, m in self.tier_models.items()},
            "ideas": dict(self.ideas),
            "projects_open": list(self.projects_open),
            "projects_recent": list(self.projects_recent),
        }

    @classmethod
    def from_dict(cls, data: dict) -> MachineSettings:
        s = cls()
        tools = data.get("tools") if isinstance(data.get("tools"), dict) else {}
        for t in TOOLS:
            raw = tools.get(t)
            if isinstance(raw, dict):
                billing = raw.get("billing")
                s.tools[t] = ToolChoice(enabled=bool(raw.get("enabled", False)),
                                        billing=billing if billing in BILLINGS else "subscription")
        s.onboarded = bool(data.get("onboarded", False))
        s.quiet = Span.from_dict(data.get("quiet"))
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        s.usage = usage.get("share") if isinstance(usage.get("share"), bool) else None
        s.keep_awake = awake_mode(data.get("keep_awake"))
        s.awake_offered = data.get("awake_offered") is True
        s.review_notice = data.get("review_notice") is True
        s.updates = data["updates"] if data.get("updates") in UPDATES else "critical"
        s.repair_command = clean_repair_command(data.get("repair_command"))
        s.main_tool = data["main_tool"] if data.get("main_tool") in TOOLS else ""
        s.tool_order = clean_tool_order(data.get("tool_order"))
        s.phones = clean_phones(data.get("phones"))
        port = data.get("phone_port")
        s.phone_port = port if isinstance(port, int) and not isinstance(port, bool) and 1024 <= port <= 65535 else 0
        s.dnd_until = clean_dnd(data.get("dnd_until"))
        s.tier_models = clean_tier_models(data.get("tier_models"))
        s.ideas = clean_ideas(data.get("ideas"))
        raw = data.get("ideas") if isinstance(data.get("ideas"), dict) else {}
        if raw.get("review_v") != REVIEW_V:                       # spec 84 §1: once, a file moved off the old default is read as off
            if data and raw.get("review", True) is not False:     # …and said once when it had asked to look at each result
                s.review_notice = True
            s.ideas["review"] = False
        s.projects_open = clean_folders(data.get("projects_open"), PROJECTS_OPEN)
        s.projects_recent = clean_folders(data.get("projects_recent"), PROJECTS_RECENT)
        install_id = usage.get("id")
        if s.usage:                   # a broken id is drawn again: the stats never carry what was in the file
            ok = isinstance(install_id, str) and re.fullmatch(r"[0-9a-f]{32}", install_id)
            s.install_id = install_id if ok else uuid.uuid4().hex
        return s


def clean_tool_order(raw: object) -> list[str]:
    """`machine.tool_order` as stored: the known tools, each once, in the order given; the rest dropped (a tool turned on that is not in it
    comes after them, in the registry's order: `tool_order`)."""
    if not isinstance(raw, list):
        return []
    return list(dict.fromkeys(t for t in raw if isinstance(t, str) and t in TOOLS))


def clean_repair_command(raw: object) -> list[str]:
    """The command Fix it starts (spec 119 §2.4): a list of a few words, each a non-empty line of text; a broken value is the default."""
    if isinstance(raw, list) and 1 <= len(raw) <= 24 and all(isinstance(w, str) and w.strip() and "\n" not in w and len(w) <= 500 for w in raw):
        return [w.strip() for w in raw]
    return list(REPAIR_COMMAND)


def clean_tier_models(raw: object) -> dict[str, dict[str, str]]:
    """{tool: {tier: model}} as stored: known tools and tiers, a model of a few words; the rest dropped."""
    out: dict[str, dict[str, str]] = {}
    for tool, tiers in (raw.items() if isinstance(raw, dict) else ()):
        if tool not in TOOLS or not isinstance(tiers, dict):
            continue
        kept = {tier: model.strip()[:100] for tier, model in tiers.items()
                if tier in harnesses.TIERS and isinstance(model, str) and re.fullmatch(r"[\w.:/@\[\]()][\w.:/@\[\]() -]{0,99}", model.strip())}
        if kept:
            out[tool] = kept
    return out


def clean_ideas(raw: object) -> dict:
    """The board's keeper and runner settings: every key of IDEAS, a broken value as its default."""
    raw = raw if isinstance(raw, dict) else {}
    out = {**IDEAS, "risk_paths": []}
    for k, lo, hi in (("batch_minutes", 1, 24 * 60), ("idle_hours", 1, 24 * 14), ("max_parallel", 1, 8)):
        v = raw.get(k)
        if isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi:
            out[k] = v
    branch = raw.get("merge_into")
    if isinstance(branch, str) and re.fullmatch(r"[\w./-]{1,100}", branch) and ".." not in branch:
        out["merge_into"] = branch
    for k in ("review", "autostart", "work_at_night"):
        if isinstance(raw.get(k), bool):
            out[k] = raw[k]
    if (way := clean_push_way(raw.get("push"))) is not None:
        out["push"] = way
    if raw.get("target") in IDEA_TARGETS:
        out["target"] = raw["target"]
    if raw.get("night_rung") in NIGHT_RUNGS:        # spec 168 H3: the night's ladder (`night_rung` reads it with the old `work_at_night`)
        out["night_rung"] = raw["night_rung"]
    if (picked := clean_night_leaders(raw.get("night_leaders"))) is not None:
        out["night_leaders"] = picked
    if raw.get("look_wait") in LOOK_WAITS:          # an unknown value reads as the default, 2 h (spec 144 A.1)
        out["look_wait"] = raw["look_wait"]
    if raw.get("build_start") in look_wait.BUILD_STARTS:     # spec 168 H2: *The build starts* as one value, read when a file says it; the two keys stay the ones kept
        out.update(look_wait.build_start_keys(raw["build_start"], out["look_wait"]))
    night = raw.get("night")
    if isinstance(night, str) and NIGHT.match(night.strip()) and night.strip()[:5] != night.strip()[6:]:
        out["night"] = night.strip()
    for k in ("reserve_day", "reserve_night"):
        v = raw.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 0.9:
            out[k] = round(float(v), 3)
    out["hours"] = hours.clean_hours(raw.get("hours"))        # spec 138 B.1: when the person is at the computer
    out["presence"] = hours.clean_hold(raw.get("presence"))   # spec 139 C.1: the door's press, held until the hours' next edge
    paths = raw.get("risk_paths")
    if isinstance(paths, list):
        out["risk_paths"] = [p.strip()[:200] for p in paths if isinstance(p, str) and p.strip()][:50]
    wiki = raw.get("wiki")              # the Board's Wiki, a folder in the repository (spec 37 §3.5); kept only when set
    if isinstance(wiki, str) and (wiki := wiki.strip().strip("/")) and re.fullmatch(r"[\w. /-]{1,200}", wiki) \
            and ".." not in wiki.split("/"):
        out["wiki"] = wiki
    return out


def clean_folders(raw: object, most: int) -> list[str]:
    """Absolute folders as stored, each once, at most `most`; anything else dropped."""
    out: list[str] = []
    for x in raw if isinstance(raw, list) else []:
        if isinstance(x, str) and x.strip() and len(x) <= 1000 and "\0" not in x and Path(x).is_absolute() \
                and x not in out:
            out.append(x)
    return out[:most]


# -- a project's Board settings (spec 37 §8) ---------------------------------------------------------------------

_BOARD_CACHE: dict = {}


def _read_cached(file: Path, parse) -> object:
    """`parse(text)` of a file, read again only when it changed (the runner asks for a setting often); None when
    there is no file or it is broken."""
    try:
        st = file.stat()
    except OSError:
        return None
    stamp = (st.st_mtime_ns, st.st_size)
    got = _BOARD_CACHE.get(str(file))
    if got is None or got[0] != stamp:
        try:
            value = parse(file.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            value = None
        got = (stamp, value)
        _BOARD_CACHE[str(file)] = got
    return got[1]


def risk_paths_of(repo_root: Path) -> list[str] | None:
    """The repository's own risky paths, `orkcraft.toml` `[board] risk_paths` (tracked: a fact of the repository);
    None when it names none."""
    import tomllib
    table = _read_cached(Path(repo_root) / "orkcraft.toml", tomllib.loads)
    board = table.get("board") if isinstance(table, dict) else None
    paths = board.get("risk_paths") if isinstance(board, dict) else None
    if not isinstance(paths, list):
        return None
    return clean_ideas({"risk_paths": paths})["risk_paths"]


def board_of(repo_root: Path, defaults: dict | None) -> dict:
    """A project's Board settings: the machine's `ideas` (`defaults`), the project's `board.json` over them (only
    the keys of BOARD), `risk_paths` from its `orkcraft.toml` when it names some; every key of IDEAS."""
    own = _read_cached(Path(repo_root) / BOARD_FILE, json.loads)
    merged = dict(defaults or IDEAS)
    if isinstance(own, dict):
        if "review" in own and own.get("review_v") != REVIEW_V:   # spec 84 §1: the project's file moves off once, as the machine's did
            own = {**own, "review": False, "review_v": REVIEW_V}
            try:
                _write(Path(repo_root) / BOARD_FILE, own)
            except OSError:
                pass                                              # read as moved all the same; written at the next save
            _BOARD_CACHE.pop(str(Path(repo_root) / BOARD_FILE), None)
        merged.update({k: own[k] for k in BOARD if k in own})
    out = clean_ideas(merged)
    paths = risk_paths_of(repo_root)
    if paths is not None:
        out["risk_paths"] = paths
    return out


def save_board(repo_root: Path, values: dict) -> dict:
    """The project's Board settings, written to `<repo>/.orkcraft/board.json` (git-ignored there): the keys of BOARD
    as `clean_ideas` keeps them. What was written."""
    cleaned = clean_ideas(values)
    data = {k: cleaned[k] for k in BOARD if k in cleaned}
    if "wiki" not in cleaned:
        data["wiki"] = ""                   # no Wiki of its own: the machine's is not taken either
    file = Path(repo_root) / BOARD_FILE
    _write(file, data)
    _BOARD_CACHE.pop(str(file), None)
    ignore = file.parent / ".gitignore"
    try:
        have = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
        if file.name not in have:
            ignore.write_text("\n".join([*have, file.name]) + "\n", encoding="utf-8")
    except OSError:
        pass
    return data


def path() -> Path:
    """`$ORKCRAFT_SETTINGS_FILE`, else `$XDG_CONFIG_HOME/orkcraft/settings.json`."""
    env = getenv("SETTINGS_FILE")
    if env:
        return Path(env).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME", "").strip() or str(Path.home() / ".config")
    return Path(base) / "orkcraft" / "settings.json"


def load(file: Path | None = None) -> MachineSettings:
    file = file or path()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return MachineSettings()
    return MachineSettings.from_dict(data) if isinstance(data, dict) else MachineSettings()


_CACHE: dict = {}


def cached() -> MachineSettings:
    """The machine settings on disk, read again only when the file changed (the map, a step's tool and its tiers
    ask often)."""
    file = path()
    try:
        key = (str(file), file.stat().st_mtime_ns)
    except OSError:
        key = (str(file), None)
    if _CACHE.get("key") != key:
        _CACHE.update(key=key, machine=load(file))
    return _CACHE["machine"]


def main_tool(machine: MachineSettings | None = None) -> str:
    """The machine's main tool (read from disk when not given: the chosen one if it is on, else the first on);
    Claude Code when none is on, as before there was a choice."""
    machine = machine or cached()
    return harnesses.main([t for t, c in machine.tools.items() if c.enabled], machine.main_tool, getattr(machine, "tool_order", ()) or ()) or "claude"     # settings of before spec 130 (a test's) have no order


def tool_order(machine: MachineSettings | None = None) -> list[str]:
    """The AI tools turned on, in the person's order (`machine.tool_order`; the tools it does not name after them, in the registry's order): the
    potions' order left to right, and the order the work moves on in when the Main tool is dry (docs/specs/105 §2.1, realm/tool_now.py;
    decisions §232.5, spec 130 A.1). Read from disk when not given."""
    machine = machine or cached()
    on = [t for t, c in machine.tools.items() if c.enabled]
    order = list(getattr(machine, "tool_order", ()) or ())                 # settings of before spec 130 have none
    return sorted(on, key=lambda t: order.index(t) if t in order else len(order))   # a stable sort: the registry's order within the rest


def _raw(file: Path) -> dict:
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write(file: Path, data: dict) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_suffix(file.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(file)


def save(s: MachineSettings, file: Path | None = None) -> None:
    """The settings as `s` has them, but the paired phones as the file has them: only `save_phones`
    writes those, so a host that loaded the settings before a phone was forgotten never brings it back."""
    file = file or path()
    data = s.to_dict()
    raw = _raw(file)
    data["phones"], data["phone_port"] = raw.get("phones", []), raw.get("phone_port", 0)
    _write(file, data)


def save_phones(phones: list[dict], port: int, file: Path | None = None) -> None:
    """The paired phones and their listener's port, everything else in the file as it is (gui/pairing.py)."""
    file = file or path()
    raw = _raw(file)
    raw["phones"], raw["phone_port"] = clean_phones(phones), port
    _write(file, raw)


