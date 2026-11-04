"""The project's journal on its own remote (decisions §229): asked for once, a branch of its own, small, no code, sent by code.

    # orkcraft.toml: nothing is sent until the project asks for it, in plain words
    #   [journal]
    #   remote = "origin"             # the remote's name
    #   branch = "orkboard/journal"   # a branch of its own: it shares no history with the code and is never merged
    #   every  = 15                   # minutes, at most
    #   prompts = false               # true: the calls' whole prompts and answers too (for a private repository only)

    config = remote_journal.read_config(root)                 # None: the project has no [journal] (off, never on by itself)
    files = remote_journal.pack(root, state_dir)              # path -> text (bytes for a .json.gz), secrets held back
    remote_journal.due(state_dir, config, now)                # `every` minutes since the last attempt?
    remote_journal.send(root, state_dir, config)              # {"sent": True, "commit": …, "files": n, "held_back": n}

What goes: `status.md` and `status.json` (spec 136 A: when it was written, the parties and their goals by state and phase, which need the person, what failed; the Markdown is written from the data), `taken.json` (the goals of the phone's inbox taken, decisions §243.4, realm/remote_inbox.py), `events.jsonl` (the event
log's lines of the last 3 days), `spend.json` and `spend.txt` (realm/spend_report.py, the last 7 days) and
`calls/<day>-<building>.jsonl` (each call's tool, model, step, tokens, cost and exit code, the last 3 days). Only with
`prompts = true`, the `*.json.gz` call files beside them. **Never** `.orkcraft/drive.json` (the server's token), an `.env` or
anything not listed here, and every line of every text file is read for a secret's shape (`scrub`): a line that has one is
replaced by words, the count is told.

It is committed by git's plumbing and nothing else (a temporary index in the state folder, `hash-object`, `update-index`,
`write-tree`, `commit-tree`, `update-ref refs/orkboard/journal`, then `push <remote> <commit>:refs/heads/<branch>`, never
`--force`): no checkout, the person's working tree, index and branch untouched. When the tree is the parent's, nothing is
committed or pushed. A push that fails (offline, no right, no such remote) is a result in words, never an exception: it
troubles no work.

No face, no model, no network but that `git push`.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from orkboard.realm import event_log, ideas, plumbing, spend_report

FILE = "orkcraft.toml"
LOCAL_REF = "refs/orkboard/journal"
EVENT_DAYS, CALL_DAYS, SPEND_DAYS = 3, 3, 7
HELD, AUTHOR, _SECRETS = plumbing.HELD, plumbing.AUTHOR, plumbing.SECRETS     # the plumbing is shared (realm/plumbing.py)
STATE_FILE = "journal.json"

_SECRETS = re.compile("|".join((
    r"sk-[A-Za-z0-9_-]{20,}", r"sk-ant-[A-Za-z0-9_-]{20,}", r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}", r"AKIA[0-9A-Z]{16}", r"AIza[0-9A-Za-z_-]{35}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i:(?:api[_-]?key|secret|token|password)\s*[=:]\s*\S{12,})")))


@dataclass(frozen=True)
class JournalConfig:
    remote: str = "origin"
    branch: str = "orkboard/journal"
    every: int = 15
    prompts: bool = False
    inbox: str = ""             # the branch the phone drops goals into (decisions §243.2, spec 136): "" reads none


def read_config(root: Path) -> JournalConfig | None:
    """The `[journal]` of `orkcraft.toml`; None with no file, a bad file or no `[journal]` (off). A bad value is ignored."""
    try:
        table = tomllib.loads((Path(root) / FILE).read_text(encoding="utf-8")).get("journal")
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None
    if not isinstance(table, dict):
        return None
    d = JournalConfig()
    remote, branch, every, prompts, inbox = (table.get(k, v) for k, v in
                                             (("remote", d.remote), ("branch", d.branch), ("every", d.every), ("prompts", d.prompts), ("inbox", d.inbox)))
    ok = lambda s: isinstance(s, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,100}", s) and not s.startswith("-") and ".." not in s
    return JournalConfig(remote if ok(remote) else d.remote, branch if ok(branch) else d.branch,
                         every if isinstance(every, int) and not isinstance(every, bool) and every >= 1 else d.every,
                         prompts if isinstance(prompts, bool) else d.prompts, inbox if ok(inbox) and inbox != branch else d.inbox)


def turn_on(root: Path, inbox: str = "orkboard/inbox") -> JournalConfig:
    """Write `[journal]` with `inbox` into `orkcraft.toml` (spec 136 A.2; the person said yes): the table made when missing, `inbox` added to
    one that has none, every other line kept. Raises OSError when the file cannot be written."""
    path = Path(root) / FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    if not re.search(r"^\[journal\]\s*$", text, flags=re.M):
        text += ("\n" if text and not text.endswith("\n") else "") + ("\n" if text else "") + \
            f'[journal]\nremote = "origin"\nbranch = "orkboard/journal"\nevery = 15\ninbox = "{inbox}"\n'
    elif not re.search(r"^inbox\s*=", text.split("[journal]", 1)[1].split("\n[", 1)[0], flags=re.M):
        text = re.sub(r"^\[journal\]\s*$", lambda m: m.group(0) + f'\ninbox = "{inbox}"', text, count=1, flags=re.M)
    path.write_text(text, encoding="utf-8")
    return read_config(root) or JournalConfig(inbox=inbox)



scrub = plumbing.scrub


def _day(now: dt.datetime, back: int) -> str:
    return (now - dt.timedelta(days=back)).strftime("%Y-%m-%d")


PHASES = {"routed": "talk", "talk": "talk", "decided": "talk", "raw": "spec", "reading": "spec", "asks": "spec", "ready": "spec",
          "sketch": "spec", "sections": "spec", "planning": "work", "plan": "work", "working": "work", "failed": "work", "done": "done"}
TAKEN_FILE, TAKEN_DAYS, TAKEN_SHOWN_DAYS = "taken.json", 30, 7


def _naive(t: dt.datetime) -> dt.datetime:
    return t.astimezone().replace(tzinfo=None) if t.tzinfo else t


def read_taken(state_dir: Path, now: dt.datetime | None = None, days: int = TAKEN_DAYS) -> list[dict]:
    """The goals taken from the inbox (decisions §243.4), as this machine keeps them in `<state_dir>/taken.json`:
    `[{id, by, at, slug, error}]`, the last `days` days. Spec 136 A."""
    try:
        data = json.loads((Path(state_dir) / TAKEN_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rows = data.get("taken") if isinstance(data, dict) else data
    cut = _naive(now or dt.datetime.now()) - dt.timedelta(days=days)
    out = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or not isinstance(r.get("id"), str):
            continue
        try:
            if _naive(dt.datetime.fromisoformat(str(r.get("at") or ""))) < cut:
                continue
        except ValueError:
            pass                                    # no readable time: kept, it is not old for that
        out.append({"id": r["id"], "by": str(r.get("by") or ""), "at": str(r.get("at") or ""), "slug": str(r.get("slug") or ""),
                    "error": str(r.get("error") or "")})
    return out


def write_taken(state_dir: Path, taken: list[dict]) -> None:
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    tmp = Path(state_dir) / (TAKEN_FILE + ".tmp")
    tmp.write_text(json.dumps({"v": 1, "taken": taken}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, Path(state_dir) / TAKEN_FILE)


def status_data(root: Path, state_dir: Path, now: dt.datetime, pages: Path, needs: frozenset[str] | set[str] = frozenset()) -> dict:
    """What `status.json` holds (spec 136 A): `{v, written, parties: [{slug, title, goals: [{slug, title, state, phase, needs_you,
    error}]}], failed: [{slug, title, error}], taken}`. `needs`: the slugs of the goals a card waits for in the hand (the host
    reads them from the Board's Needs you; this module knows no face). `status.md` is written from it."""
    try:
        parties = ideas.tracks(pages, make=False)
    except Exception:
        parties = []
    try:
        titles = {i["slug"]: (i["title"], i["track"]) for i in ideas.ideas(pages)}
    except Exception:
        titles = {}
    by_party: dict[str, list[dict]] = {}
    failed: list[dict] = []
    folder = Path(state_dir) / "ideas"
    for d in sorted(folder.iterdir()) if folder.is_dir() else []:
        title, party = titles.get(d.name, (d.name, ""))
        try:
            st = json.loads((d / "state.json").read_text(encoding="utf-8"))
            word = str(st.get("state") or "unknown") if isinstance(st, dict) else "unreadable"
            err = str(st.get("error") or "") if isinstance(st, dict) else ""
        except (OSError, ValueError):
            word, err = "unreadable", ""
        err = " ".join(err.split())[:200]
        by_party.setdefault(party, []).append({"slug": d.name, "title": title, "state": word, "phase": PHASES.get(word, ""),
                                               "needs_you": d.name in needs, "error": err})
        if word == "failed":
            failed.append({"slug": d.name, "title": title, "error": err})
    names = {p["slug"]: p["title"] for p in parties}
    out = [{"slug": slug, "title": names.get(slug) or slug or "No party", "goals": by_party.get(slug, [])}
           for slug in [*names, *(k for k in by_party if k not in names)]]
    return {"v": 1, "written": now.isoformat(timespec="seconds"), "parties": out, "failed": failed,
            "taken": read_taken(state_dir, now, TAKEN_SHOWN_DAYS)}


def status_md(data: dict) -> str:
    """`status.md`, from `status_data`'s data."""
    written = str(data.get("written") or "").replace("T", " ")[:19]
    lines = ["# Orkboard journal", "", f"Written {written}.", "", "## Parties and goals", ""]
    for party in data["parties"]:
        lines += [f"### {party['title']}", "", *([f"- {g['title']} (`{g['slug']}`): {g['state']}" for g in party["goals"]] or ["- no goals"]), ""]
    if not data["parties"]:
        lines += ["No parties or goals yet.", ""]
    lines += ["## Failed", "", *([f"- {f['title']} (`{f['slug']}`)" + (f": {f['error']}" if f["error"] else "") for f in data["failed"]]
                                 or ["Nothing failed."]), ""]
    return "\n".join(lines)


def pack(root: Path, state_dir: Path, now: dt.datetime | None = None, pages: Path | None = None,
         prompts: bool = False, needs: frozenset[str] | set[str] = frozenset()) -> dict[str, str | bytes]:
    """The files to send, path -> text (bytes for a `.json.gz`). `pages`: where the Board's pages are (default `root`);
    `needs`: the goals a card waits for in the hand (`status_data`)."""
    return pack_counted(root, state_dir, now, pages, prompts, needs)[0]


def pack_counted(root: Path, state_dir: Path, now: dt.datetime | None = None, pages: Path | None = None,
                 prompts: bool = False, needs: frozenset[str] | set[str] = frozenset()) -> tuple[dict[str, str | bytes], int]:
    """`pack` and how many lines were held back."""
    root, now = Path(root), now or dt.datetime.now()
    data = status_data(root, Path(state_dir), now, Path(pages or root), needs)
    files: dict[str, str | bytes] = {"status.md": status_md(data),
                                     "status.json": json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                                     TAKEN_FILE: json.dumps({"v": 1, "taken": read_taken(state_dir, now)}, ensure_ascii=False, indent=1) + "\n"}
    try:
        events = [r for r in event_log.read(root, since=_day(now, EVENT_DAYS)) if r.get("event") != event_log.JOURNAL_SENT]   # its own line would change what it sends
        files["events.jsonl"] = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in events)
    except Exception:
        files["events.jsonl"] = ""
    try:
        rep = spend_report.report(spend_report.lines_of(root, since=_day(now, SPEND_DAYS)))
        files["spend.json"] = json.dumps(rep, ensure_ascii=False, indent=2) + "\n"
        files["spend.txt"] = spend_report.text(rep) + "\n"
    except Exception:
        pass
    logs = root / ".orkcraft" / "logs"
    for day in sorted(p for p in logs.iterdir() if p.is_dir() and p.name >= _day(now, CALL_DAYS)) if logs.is_dir() else []:
        for b in sorted(p for p in day.iterdir() if p.is_dir()):
            try:
                files[f"calls/{day.name}-{b.name}.jsonl"] = (b / "calls.jsonl").read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
            for gz in sorted(b.glob("*.json.gz")) if prompts else []:
                try:
                    files[f"calls/{day.name}-{b.name}-{gz.name}"] = gz.read_bytes()
                except OSError:
                    pass
    held = 0
    for name, body in list(files.items()):
        if isinstance(body, str):
            files[name], n = scrub(body)
            held += n
    return files, held


# -- when ----------------------------------------------------------------------------------------------------------

def _stamp(state_dir: Path) -> dict:
    try:
        data = json.loads((Path(state_dir) / STATE_FILE).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def due(state_dir: Path, config: JournalConfig, now: dt.datetime, urgent: bool = False) -> bool:
    """`urgent`, or `every` minutes since the last attempt (kept in `<state_dir>/journal.json`)."""
    if urgent:
        return True
    try:
        last = dt.datetime.fromisoformat(str(_stamp(state_dir).get("at") or ""))
    except ValueError:
        return True
    return (now - last).total_seconds() >= config.every * 60


def _digest(files: dict[str, str | bytes], where: str = "") -> str:
    """What the files say, the time `status.md` was written left out (it changes every time and is not news)."""
    h = hashlib.sha256(where.encode())
    for name in sorted(files):
        body = files[name]
        if isinstance(body, str) and name == "status.md":
            body = re.sub(r"^Written .*$", "", body, count=1, flags=re.M)
        elif isinstance(body, str) and name == "status.json":
            body = re.sub(r'^ *"written": .*$', "", body, count=1, flags=re.M)
        h.update(name.encode() + b"\0" + (body if isinstance(body, bytes) else body.encode("utf-8")) + b"\0")
    return h.hexdigest()


def _mark(state_dir: Path, now: dt.datetime, result: dict) -> None:
    try:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        digest = result.get("digest") or _stamp(state_dir).get("digest", "")
        (Path(state_dir) / STATE_FILE).write_text(
            json.dumps({"at": now.isoformat(timespec="seconds"), "sent": bool(result.get("sent")), "why": result.get("why", ""),
                        "digest": digest}), encoding="utf-8")
    except OSError:
        pass


# -- sending, by git's plumbing -------------------------------------------------------------------------------------

def _git(root: Path, run: Callable, env: dict, *args: str, data: bytes | None = None) -> str:
    return plumbing.git(root, run, env, *args, data=data)


def send(root: Path, state_dir: Path, config: JournalConfig, now: dt.datetime | None = None,
         run: Callable = subprocess.run, pages: Path | None = None, needs: frozenset[str] | set[str] = frozenset()) -> dict:
    """Pack, commit to the journal branch by plumbing and push without force. Never raises."""
    now = now or dt.datetime.now()
    root, state_dir = Path(root), Path(state_dir)
    index = state_dir / "journal.index"
    try:
        result = _send(root, state_dir, config, now, run, pages, index, needs)
        digest = result.pop("digest", "")
    except Exception as e:                      # offline, no right, no such remote, no git: said, not raised
        result, digest = {"sent": False, "why": " ".join(str(e).split())[:300] or type(e).__name__}, ""
    try:
        index.unlink(missing_ok=True)
    except OSError:
        pass
    _mark(state_dir, now, {**result, "digest": digest} if result["sent"] else result)
    if result.get("why") != "nothing changed":
        event_log.record(root, event_log.JOURNAL_SENT, sent=result["sent"], remote=config.remote, branch=config.branch,
                         files=result.get("files"), held_back=result.get("held_back"), commit=result.get("commit", ""),
                         why=result.get("why", ""))
    return result


def _send(root: Path, state_dir: Path, config: JournalConfig, now: dt.datetime, run: Callable, pages: Path | None, index: Path,
          needs: frozenset[str] | set[str] = frozenset()) -> dict:
    files, held = pack_counted(root, state_dir, now, pages, config.prompts, needs)
    state_dir.mkdir(parents=True, exist_ok=True)
    digest = _digest(files, f"{config.remote}:{config.branch}")
    if digest == _stamp(state_dir).get("digest"):
        return {"sent": False, "why": "nothing changed"}
    index.unlink(missing_ok=True)
    env = plumbing.env(index)
    tree = plumbing.tree_of(root, run, env, {n: b if isinstance(b, bytes) else b.encode("utf-8") for n, b in files.items()})
    try:
        parent = _git(root, run, env, "rev-parse", "--verify", "-q", LOCAL_REF)
    except RuntimeError:
        parent = ""
    if parent and _git(root, run, env, "rev-parse", f"{parent}^{{tree}}") == tree:
        return {"sent": False, "why": "nothing changed"}
    stamp = now.isoformat(timespec="seconds")
    commit = _git(root, run, env, "commit-tree", tree, *(["-p", parent] if parent else []), "-m", f"Orkboard journal {stamp}")
    _git(root, run, env, "update-ref", LOCAL_REF, commit)
    try:
        _git(root, run, env, "push", config.remote, f"{commit}:refs/heads/{config.branch}")
    except RuntimeError as e:
        if parent:                              # not sent: the next try packs against what the remote really has
            _git(root, run, env, "update-ref", LOCAL_REF, parent)
        else:
            _git(root, run, env, "update-ref", "-d", LOCAL_REF)
        return {"sent": False, "why": str(e)[:300]}
    return {"sent": True, "commit": commit, "files": len(files), "held_back": held, "digest": digest}
