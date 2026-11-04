"""`orkboard drive …`: Orkboard driven from a terminal, or by an agent testing it (decisions §227). It is a client of the
same socket the page uses (gui/server.py): every act is one of the page's own commands (`ideas.add`, `ideas.answer`,
`ideas.start_now` …), so a drive goes the way a person's presses go, never a way of its own.

    orkboard drive start ~/game                      # the project served with no window, the AI tools hidden; its address kept
    orkboard drive start ~/game --real-tools         # … letting it run the AI tools it finds (they spend their limits)
    orkboard drive call ideas.board                  # one command, its answer as JSON (`--args '{"text": "…"}'`)
    orkboard drive state                             # the snapshot the page is sent first
    orkboard drive wait ideas.board --path 'ideas[slug=jump].state' --is routed --timeout 600
    orkboard drive watch --seconds 30                # what the server sends, a JSON line each (states, toasts)
    orkboard drive run scenarios/goal.json           # steps and what each must find; a JSON line a step, then the summary
    orkboard drive shot out.png --width 390          # the page as a phone sees it (Playwright, where it is installed)
    orkboard drive stop                              # the served project stopped
    orkboard drive spend --since 2026-11-03          # what the calls spent, and where tokens went for nothing (realm/spend_report.py)
    orkboard drive journal --dry-run                 # what `[journal]` in orkcraft.toml would send to the project's remote (--now: send it now; decisions §229)

The served project's address (its token inside) is kept in `<project>/.orkcraft/drive.json`, readable by its owner alone,
removed when it stops; `--url` names a server instead (an editor's `--serve`). **The AI tools are hidden unless asked for**:
a drive started without `--real-tools` runs with a PATH that holds no agent CLI (Claude Code, Codex, Antigravity…) and no `gh`,
and reads no limits or model list, so a step that would ask a model fails as a missing tool, spending nothing. The server listens on 127.0.0.1 only and
takes the token and its own Origin, as for the page. A path in a result: keys and list places by dots (`ideas.0.slug`),
and `[key=value]` for the first item of a list whose key has that value (`ideas[slug=jump].state`).
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, urlsplit

SESSION = "drive.json"
STEP_KEYS = ("call", "wait", "shot", "pause")


class DriveError(Exception):
    """What a drive could not do, in words: no server, a command refused, a step not found as expected."""


# -- where the served project is ----------------------------------------------------------------------------------

def session_path(root: Path) -> Path:
    return Path(root) / ".orkcraft" / SESSION


def write_session(root: Path, info: dict) -> Path:
    """The served project's address, for the drive's other commands: its owner's to read alone (the token is in it)."""
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(info, f)
    os.replace(tmp, path)
    return path


def read_session(root: Path) -> dict:
    path = session_path(root)
    if not path.is_file():
        raise DriveError(f"No Orkboard is served for {root}: run `orkboard drive start {root}` first")
    return json.loads(path.read_text(encoding="utf-8"))


def remove_session(root: Path) -> None:
    session_path(root).unlink(missing_ok=True)


def socket_of(url: str, origin: str = "") -> tuple[str, str]:
    """The socket's address and the Origin to give it, from the page's address (`http://127.0.0.1:N/?t=…`)."""
    parts = urlsplit(url)
    token = parse_qs(parts.query).get("t", [""])[0]
    if not token:
        raise DriveError("The address holds no token (`?t=`)")
    origin = origin or f"{parts.scheme}://{parts.netloc}"
    scheme = "wss" if parts.scheme == "https" else "ws"
    return f"{scheme}://{parts.netloc}/ws?t={token}", origin


def journal(root: Path, dry_run: bool = False, now: bool = False) -> int:
    """`drive journal`: what the project's `[journal]` would send (`--dry-run`), or its sending (due, else `--now`)."""
    import datetime as dt
    from orkboard.realm import remote_journal as rj
    config = rj.read_config(root)
    if config is None:
        print("This project has no journal: nothing is sent. To turn it on, add a [journal] table to orkcraft.toml "
              "(remote = \"origin\", branch = \"orkboard/journal\", every = 15, prompts = false).")
        return 0
    state = root / ".orkcraft"
    if dry_run:
        files, held = rj.pack_counted(root, state, prompts=config.prompts)
        for name, body in files.items():
            print(f"{name}  {len(body)} bytes")
        print(f"{len(files)} files; {held} lines held back (they looked like a secret). Would go to {config.remote} "
              f"as {config.branch}. Nothing was sent.")
        return 0
    when = dt.datetime.now()
    if not now and not rj.due(state, config, when):
        print(f"Not due yet (every {config.every} minutes); --now sends it anyway.")
        return 0
    result = rj.send(root, state, config, when)
    print(f"Sent {result['files']} files as {result['commit'][:10]} to {config.remote}/{config.branch} "
          f"({result['held_back']} lines held back)." if result["sent"] else f"Not sent: {result['why']}")
    return 0 if result["sent"] or result["why"] == "nothing changed" else 1


def find_root(folder: str | None) -> Path:
    from orkboard.config import find_project_root
    try:
        return Path(find_project_root(Path(folder or ".").expanduser().resolve()))
    except FileNotFoundError:
        raise DriveError(f"No project at {folder or '.'} (no .git and no .orkcraft.json above it)") from None


# -- the link ----------------------------------------------------------------------------------------------------------

class Link:
    """One socket to a served Orkboard: commands by their names, the first snapshot, what came between."""

    def __init__(self, url: str, origin: str = "", timeout: float = 30) -> None:
        from websockets.sync.client import connect
        address, self.origin = socket_of(url, origin)
        self.url, self.timeout, self._id = url, timeout, 0
        self.toasts: list[dict] = []
        try:
            self._opened = connect(address, origin=self.origin, max_size=None, open_timeout=timeout)
            self.ws = self._opened.__enter__()
        except OSError as e:
            raise DriveError(f"Orkboard does not answer at {self.origin}: {e}") from None
        first = json.loads(self.ws.recv(timeout=timeout))
        self.state = first.get("state") if first.get("t") == "state" else None

    def call(self, name: str, args: dict | None = None, timeout: float | None = None) -> Any:
        """The command's result; DriveError with the host's words when it refused or broke."""
        self._id += 1
        cid = self._id
        self.ws.send(json.dumps({"t": "cmd", "id": cid, "name": name, "args": args or {}}))
        end = time.monotonic() + (timeout or self.timeout)
        while True:
            left = end - time.monotonic()
            if left <= 0:
                raise DriveError(f"{name}: no answer in {timeout or self.timeout:g} s")
            msg = self._take(left)
            if msg is not None and msg.get("t") == "reply" and msg.get("id") == cid:
                if not msg.get("ok"):
                    raise DriveError(f"{name}: {msg.get('error') or 'refused'}")
                return msg.get("result")

    def messages(self, seconds: float) -> Iterator[dict]:
        """What the server sends for `seconds`: states, toasts, details (a terminal's bytes are left out)."""
        end = time.monotonic() + seconds
        while (left := end - time.monotonic()) > 0:
            msg = self._take(left)
            if msg is not None:
                yield msg

    def _take(self, timeout: float) -> dict | None:
        try:
            raw = self.ws.recv(timeout=timeout)
        except TimeoutError:
            return None
        if isinstance(raw, bytes):
            return None
        msg = json.loads(raw)
        if msg.get("t") == "state":
            self.state = msg.get("state")
        elif msg.get("t") == "toast":
            self.toasts.append(msg)
        return msg

    def close(self) -> None:
        self._opened.__exit__(None, None, None)


def link_for(folder: str | None, url: str | None, timeout: float = 30) -> Link:
    if url:
        return Link(url, timeout=timeout)
    info = read_session(find_root(folder))
    return Link(info["url"], info.get("origin", ""), timeout=timeout)


# -- paths and what is expected -----------------------------------------------------------------------------------

def at(value: Any, path: str) -> Any:
    """The value at `path` in a result (module docstring); DriveError naming the step that found nothing."""
    if not path:
        return value
    for raw in path.replace("[", ".[").split("."):
        if not raw:
            continue
        if raw.startswith("[") and raw.endswith("]") and "=" in raw:
            key, want = raw[1:-1].split("=", 1)
            if not isinstance(value, list):
                raise DriveError(f"{path}: [{key}={want}] needs a list")
            found = next((v for v in value if isinstance(v, dict) and str(v.get(key)) == want), None)
            if found is None:
                raise DriveError(f"{path}: no item with {key}={want}")
            value = found
        elif isinstance(value, list):
            try:
                value = value[int(raw)]
            except (ValueError, IndexError):
                raise DriveError(f"{path}: no place {raw}") from None
        elif isinstance(value, dict):
            if raw not in value:
                raise DriveError(f"{path}: no key {raw}")
            value = value[raw]
        else:
            raise DriveError(f"{path}: {raw} under a {type(value).__name__}")
    return value


def meets(value: Any, expect: dict) -> bool:
    """`is` (equal, a string compared with the value's text), `has` (in its text, or in a list), `not` (unequal),
    `exists` (only that the path is there): all that are given must hold."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if "is" in expect and not (value == expect["is"] or (isinstance(expect["is"], str) and text == expect["is"])):
        return False
    if "not" in expect and (value == expect["not"] or (isinstance(expect["not"], str) and text == expect["not"])):
        return False
    if "has" in expect:
        want = expect["has"]
        if isinstance(value, list) and want in value:
            pass
        elif str(want) not in text:
            return False
    return True


def wait_for(link: Link, name: str, args: dict | None, path: str, expect: dict, timeout: float,
             every: float = 2.0) -> Any:
    """The command asked again every `every` seconds until its result at `path` meets `expect`; the value found."""
    end = time.monotonic() + timeout
    last: Any = None
    while True:
        try:
            last = at(link.call(name, args), path)
            if meets(last, expect):
                return last
        except DriveError as e:
            last = str(e)
        if time.monotonic() >= end:
            raise DriveError(f"{name} {path}: not as expected after {timeout:g} s (last: {json.dumps(last, ensure_ascii=False)[:300]})")
        for _ in link.messages(min(every, max(0.0, end - time.monotonic()))):
            pass


# -- scenarios -------------------------------------------------------------------------------------------------------

def fill(value: Any, kept: dict) -> Any:
    """`${name}` in a step's strings replaced by what an earlier step kept (`keep`)."""
    if isinstance(value, str):
        for k, v in kept.items():
            value = value.replace("${" + k + "}", v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        return value
    if isinstance(value, list):
        return [fill(v, kept) for v in value]
    if isinstance(value, dict):
        return {k: fill(v, kept) for k, v in value.items()}
    return value


def run_steps(link: Link, steps: list[dict], out=None, shot_dir: Path | None = None) -> dict:
    """A scenario's steps in order, a JSON line each on `out`; the summary (`ok`, `steps`, `failed`, `seconds`). A step is
    `{"call": name, "args": {}, "expect": {"path": "", "is"|"has"|"not"|"exists": …}, "keep": {"var": "path"}}`,
    `{"wait": name, "args": {}, "path": "", "is"|"has"|"not"|"exists": …, "timeout": 600}`,
    `{"shot": "name", "width": 390, "height": 844}` or `{"pause": seconds}`; `"say"` names it in the report. The first
    step that fails ends the run."""
    out = out or sys.stdout
    kept: dict = {}
    t0 = time.monotonic()
    done = 0
    for i, raw in enumerate(steps, 1):
        step = fill(raw, kept)
        kind = next((k for k in STEP_KEYS if k in step), "")
        row: dict = {"step": i, "say": step.get("say", ""), "kind": kind}
        started = time.monotonic()
        try:
            if kind == "call":
                result = link.call(step["call"], step.get("args"), timeout=step.get("timeout"))
                expect = step.get("expect") or {}
                if expect:
                    value = at(result, expect.get("path", ""))
                    if not meets(value, expect):
                        raise DriveError(f"{step['call']} {expect.get('path', '')}: found {json.dumps(value, ensure_ascii=False)[:300]}")
                for var, path in (step.get("keep") or {}).items():
                    kept[var] = at(result, path)
            elif kind == "wait":
                expect = {k: step[k] for k in ("is", "has", "not", "exists") if k in step}
                row["found"] = wait_for(link, step["wait"], step.get("args"), step.get("path", ""), expect,
                                        float(step.get("timeout", 300)), float(step.get("every", 2)))
            elif kind == "shot":
                path = (shot_dir or Path(".")) / f"{i:02d}-{step['shot']}.png"
                shoot(link.url, path, int(step.get("width", 390)), int(step.get("height", 844)))
                row["file"] = str(path)
            elif kind == "pause":
                for _ in link.messages(float(step["pause"])):
                    pass
            else:
                raise DriveError(f"step {i}: one of {', '.join(STEP_KEYS)}")
        except DriveError as e:
            row.update(ok=False, error=str(e), seconds=round(time.monotonic() - started, 2))
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            return {"ok": False, "steps": done, "failed": i, "error": str(e), "seconds": round(time.monotonic() - t0, 2),
                    "toasts": [t.get("message") for t in link.toasts if t.get("severity") == "error"]}
        done += 1
        row.update(ok=True, seconds=round(time.monotonic() - started, 2))
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        out.flush()
    return {"ok": True, "steps": done, "failed": None, "seconds": round(time.monotonic() - t0, 2),
            "toasts": [t.get("message") for t in link.toasts if t.get("severity") == "error"]}


# -- a picture of the page -------------------------------------------------------------------------------------------

def shoot(url: str, path: Path, width: int = 390, height: int = 844) -> Path:
    """The page at `url` as a browser of that size draws it, saved to `path` (Playwright's Chromium, where it is)."""
    chromium = next((p for p in (os.environ.get("ORKCRAFT_CHROMIUM", ""), "/opt/pw-browsers/chromium") if p and Path(p).exists()), None)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _shoot_with_node(url, path, width, height, chromium)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2,
                                    has_touch=width < 760, is_mobile=width < 760)
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(800)
            page.screenshot(path=str(path))
        finally:
            browser.close()
    return path


NODE_SHOT = """
const { chromium } = require('playwright');
const [url, file, w, h, exe] = process.argv.slice(1);
(async () => {
  const b = await chromium.launch(exe ? { executablePath: exe } : {});
  const small = Number(w) < 760;
  const p = await b.newPage({ viewport: { width: Number(w), height: Number(h) }, deviceScaleFactor: 2, hasTouch: small, isMobile: small });
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.waitForTimeout(800);
  await p.screenshot({ path: file });
  await b.close();
})().catch((e) => { console.error(String(e)); process.exit(1); });
"""


def _shoot_with_node(url: str, path: Path, width: int, height: int, chromium: str | None) -> Path:
    """The same picture through Node's Playwright, where Python's is not installed (a cloud machine has Node's)."""
    import shutil
    import subprocess
    node = shutil.which("node")
    if node is None:
        raise DriveError("A picture needs Playwright (pip install playwright, or Node's)")
    done = subprocess.run([node, "-e", NODE_SHOT, url, str(path), str(width), str(height), chromium or ""],
                          capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        raise DriveError(f"No picture: {(done.stderr or done.stdout).strip()[:300]}")
    return path


# -- serving -----------------------------------------------------------------------------------------------------------

def quiet_path(path: str | None = None) -> str:
    """$PATH with each folder that holds an agent CLI or `gh` replaced by a folder of links to the rest of it."""
    import tempfile
    from orkboard.realm import harnesses
    tools = {h.default_bin for h in harnesses.REGISTRY.values()} | {"gh"}
    dirs = []
    for d in (os.environ.get("PATH", "") if path is None else path).split(os.pathsep):
        folder = Path(d)
        if d and folder.is_dir() and any((folder / t).exists() for t in tools):
            copy = Path(tempfile.mkdtemp(prefix="orkboard-drive-path-"))
            for entry in folder.iterdir():
                if entry.name not in tools:
                    (copy / entry.name).symlink_to(entry)
            d = str(copy)
        dirs.append(d)
    return os.pathsep.join(dirs)


def start(root: Path, port: int = 0, out=None, real_tools: bool = False) -> int:
    """The project served with no window until stopped (`drive stop`, SIGTERM or Ctrl+C): its address as one JSON line on
    `out` and in its session file, which goes when it stops. Without `real_tools` no AI tool can be run (`quiet_path`)."""
    from orkboard import __version__
    from orkboard.gui import server_log
    from orkboard.gui.board_host import Orkboard
    from orkboard.gui.server import Server
    out = out or sys.stdout
    root = Path(root).resolve()
    if not real_tools:
        os.environ["PATH"] = quiet_path()
        for key in ("ORKCRAFT_LIMITS", "ORKCRAFT_MODEL_LIST"):
            os.environ[key] = "0"
        os.environ["ORKCRAFT_NO_UPDATE"] = "1"
    server_log.install()
    host = Orkboard(root)
    host.opened()
    server = Server(host, port)
    thread = server.start_thread()
    info = {"url": server.url, "origin": server.origin, "pid": os.getpid(), "project": str(root), "version": __version__,
            "tools": "real" if real_tools else "hidden"}
    write_session(root, info)
    out.write(json.dumps(info) + "\n")
    out.flush()
    signal.signal(signal.SIGTERM, lambda *_: server.stop())
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        remove_session(root)
        server.stop()
        thread.join(10)
    return 0


def stop(root: Path) -> int:
    info = read_session(root)
    try:
        os.kill(int(info["pid"]), signal.SIGTERM)
    except ProcessLookupError:
        remove_session(root)
        raise DriveError("Its server had already gone; its address is forgotten") from None
    return 0


# -- the command line --------------------------------------------------------------------------------------------------

def _json_arg(text: str | None) -> dict:
    if not text:
        return {}
    try:
        value = json.loads(text)
    except ValueError as e:
        raise DriveError(f"--args is not JSON: {e}") from None
    if not isinstance(value, dict):
        raise DriveError("--args is a JSON object")
    return value


def _expect_of(a: argparse.Namespace) -> dict:
    expect = {}
    for key in ("is", "has", "not"):
        v = getattr(a, key.replace("is", "is_") if key == "is" else key, None)
        if v is not None:
            try:
                expect[key] = json.loads(v)
            except ValueError:
                expect[key] = v
    return expect


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="orkboard drive", description="Orkboard driven from a terminal, by the page's own commands")
    sub = parser.add_subparsers(dest="act", required=True)

    def where(p: argparse.ArgumentParser) -> None:
        p.add_argument("--folder", default=None, help="The project (default: the one this folder is in)")
        p.add_argument("--url", default=None, help="A server's page address instead (an editor's --serve)")
        p.add_argument("--timeout", type=float, default=30, help="Seconds to wait for an answer")

    s = sub.add_parser("start", help="Serve the project with no window, until `drive stop`")
    s.add_argument("folder", nargs="?", default=".")
    s.add_argument("--port", type=int, default=0)
    s.add_argument("--real-tools", action="store_true",
                   help="Let it run the AI tools it finds: they spend their limits (without it they are hidden)")
    st = sub.add_parser("stop", help="Stop the served project")
    st.add_argument("folder", nargs="?", default=None, help="The project, as `start` takes it (`--folder` names it too, as on the other acts)")
    st.add_argument("--folder", dest="folder_opt", default=None, help="The project (default: the one this folder is in)")
    c = sub.add_parser("call", help="One of the page's commands; its answer as JSON")
    c.add_argument("name")
    c.add_argument("--args", default=None, help="Its arguments, a JSON object")
    c.add_argument("--path", default="", help="Only the value at this path")
    where(c)
    where(sub.add_parser("state", help="The snapshot the page is sent first"))
    w = sub.add_parser("wait", help="Ask a command again until the value at a path is as expected")
    w.add_argument("name")
    w.add_argument("--args", default=None)
    w.add_argument("--path", default="")
    w.add_argument("--is", dest="is_", default=None)
    w.add_argument("--has", default=None)
    w.add_argument("--not", dest="not", default=None)
    w.add_argument("--every", type=float, default=2)
    w.add_argument("--for", dest="for_", type=float, default=300, help="Seconds before it gives up")
    where(w)
    t = sub.add_parser("watch", help="What the server sends, a JSON line each")
    t.add_argument("--seconds", type=float, default=30)
    where(t)
    r = sub.add_parser("run", help="A scenario: steps, and what each must find")
    r.add_argument("scenario")
    r.add_argument("--shots", default=None, help="Where its pictures go (default: beside the scenario)")
    where(r)
    sp = sub.add_parser("spend", help="What the project's model calls spent, by tool, step and goal, and what is worth a look")
    sp.add_argument("--folder", default=None, help="The project (default: the one this folder is in)")
    sp.add_argument("--since", default="", metavar="DAY", help="From this day on (YYYY-MM-DD)")
    sp.add_argument("--goal", default="", help="One goal's calls only (its slug)")
    sp.add_argument("--json", action="store_true", help="As data")
    jn = sub.add_parser("journal", help="The project's journal on its own remote (needs [journal] in orkcraft.toml)")
    jn.add_argument("--folder", default=None, help="The project (default: the one this folder is in)")
    jn.add_argument("--dry-run", action="store_true", help="Say what would go (names, sizes, lines held back); send nothing")
    jn.add_argument("--now", action="store_true", help="Send it now, even if it is not due")
    p = sub.add_parser("shot", help="A picture of the page (a phone's size by default)")
    p.add_argument("file")
    p.add_argument("--width", type=int, default=390)
    p.add_argument("--height", type=int, default=844)
    where(p)
    a = parser.parse_args(argv)
    try:
        if a.act == "start":
            return start(find_root(a.folder), a.port, real_tools=a.real_tools)
        if a.act == "stop":
            return stop(find_root(a.folder_opt or a.folder))
        if a.act == "spend":
            from orkboard.realm import spend_report
            found = spend_report.report(spend_report.lines_of(find_root(a.folder), a.since), a.goal)
            print(json.dumps(found, ensure_ascii=False, indent=2) if a.json else spend_report.text(found))
            return 0
        if a.act == "journal":
            return journal(find_root(a.folder), a.dry_run, a.now)
        if a.act == "shot":
            url = a.url or read_session(find_root(a.folder))["url"]
            print(shoot(url, Path(a.file), a.width, a.height))
            return 0
        link = link_for(a.folder, a.url, a.timeout)
        try:
            if a.act == "call":
                print(json.dumps(at(link.call(a.name, _json_arg(a.args)), a.path), ensure_ascii=False, indent=2))
            elif a.act == "state":
                print(json.dumps(link.state, ensure_ascii=False, indent=2))
            elif a.act == "wait":
                found = wait_for(link, a.name, _json_arg(a.args), a.path, _expect_of(a), a.for_, a.every)
                print(json.dumps(found, ensure_ascii=False))
            elif a.act == "watch":
                for msg in link.messages(a.seconds):
                    print(json.dumps(msg, ensure_ascii=False), flush=True)
            elif a.act == "run":
                scenario = Path(a.scenario)
                steps = json.loads(scenario.read_text(encoding="utf-8"))
                steps = steps.get("steps", []) if isinstance(steps, dict) else steps
                summary = run_steps(link, steps, shot_dir=Path(a.shots) if a.shots else scenario.parent / (scenario.stem + "-shots"))
                print(json.dumps({"summary": summary}, ensure_ascii=False))
                return 0 if summary["ok"] else 1
        finally:
            link.close()
        return 0
    except DriveError as e:
        print(f"orkboard drive: {e}", file=sys.stderr)
        return 1
