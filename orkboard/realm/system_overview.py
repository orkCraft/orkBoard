"""The Architect's *System* as the project's architecture (docs/specs/90-what-the-first-look-said.md §6.1–§6.6, decisions §105.6): its
containers, each one's stack, its ways in and its layers, the links between the containers (the HTTP routes one calls and another
answers, the socket events one emits and another handles) and the parts two containers or more share. Read from a tree's files with no
model, beside realm/code_map.py's parts (kept together in a snapshot, realm/project_map.py).

    read(tree)            # {"containers": [...], "links": [...], "shared": [...]}
    read(tree, parts)     # the same, given code_map.parts(tree) already read
    owner(path, paths)    # the container a part's path lies in, of the containers' paths
    matters("client/package.json")  # whether a changed file may change the overview (a source, a manifest, an index.html)

Bounded: the source files code_map reads (at most code_map.MAX_FILES, none over code_map.MAX_BYTES, none in code_map.SKIP, none that may
hold a secret), manifests two folders deep at most; every pattern has bounded repeats. Nothing is run, nothing fetched. No face.
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path, PurePosixPath

from orkboard.hooks.warder import is_secret
from orkboard.realm import code_map, stacks_known

MANIFESTS = ("package.json", "pyproject.toml", "go.mod", "Cargo.toml")
ALSO = ("index.html", "requirements.txt", "requirements-dev.txt")   # read beside a manifest: a page, Python's other list
DEPTH = 2                                  # a container's folder lies at most two folders under the project's
ROOT, ROOT_NAME = ".", "Root"
SCRIPTS = ("dev", "start", "build")        # a package.json's scripts that are ways in
CAP = 400                                  # the most calls, answers or events kept of one container
LISTENS = 5                                # the most files that `listen(` named as ways in, a container
MOUNTS = 20                                # the most mounts (`app.use("/api", …)`) a container's routes are matched under
RESERVED = {"connect", "connection", "disconnect", "disconnecting", "connect_error", "error", "reconnect", "reconnect_attempt",
            "reconnect_error", "reconnect_failed", "ping", "pong", "newListener", "removeListener", "open", "close"}
SOCKET_NAMES = {"io", "sio", "sock", "ws", "nsp", "namespace", "socketio"}
VERBS = ("get", "post", "put", "patch", "delete", "head", "options")

_STR = r"""["'`]([^"'`\n]{1,300})["'`]"""                 # a string literal (a quote of any kind each side)
_FETCH = re.compile(r"(?<![\w.$])fetch\s*\(\s*" + _STR)
_METHOD = re.compile(r"""method\s*:\s*["'`](\w{3,7})["'`]""", re.I)
_AXIOS_MADE = re.compile(r"\b(\w{1,40})\s*=\s*axios\s*\.\s*create\b")
_VERB = re.compile(r"\.\s*(?:get|post|put|patch|delete|head|options|all)\s*\(")
_SERVER_MADE = re.compile(r"\b(\w{1,40})\s*=\s*(?:new\s+)?(?:express\s*\.\s*)?(?:Router|express|fastify|Fastify|Koa|Hono|Elysia)\s*\(")
_CALL = re.compile(r"\b(\w{1,40})\s*\.\s*(get|post|put|patch|delete|head|options)\s*\(\s*f?" + _STR)
_ANSWER = re.compile(r"""\b(\w{1,40})\s*\.\s*(get|post|put|patch|delete|head|options|all)\s*\(\s*(["'`])(/[^"'`\n]{0,300})\3""")
_MOUNT = re.compile(r"""\b\w{1,40}\s*\.\s*use\s*\(\s*(["'`])(/[^"'`\n]{0,200})\1|\b(?:url_)?prefix\s*=\s*(["'])(/[^"'\n]{0,200})\3""")
_PY_ROUTE = re.compile(r"""^[ \t]*@[ \t]*\w{1,40}(?:\.\w{1,40})?\s*\.\s*(route|get|post|put|patch|delete|api_route|websocket)\s*\(\s*"""
                       r"""(["'])(/[^"'\n]{0,300})\2([^\n]{0,200})""", re.M)
_PY_METHODS = re.compile(r"methods\s*=\s*[\[(]([^\])\n]{0,100})[\])]")
_SOCKET = re.compile(r"\b(\w{1,40})(?:\s*\.\s*current)?((?:\s*\.\s*(?:to|in|broadcast|volatile|compress|timeout|local|except)\b"
                     r"(?:\s*\([^()\n]{0,120}\))?){0,4})\s*\.\s*(emit|on|once)\s*\(\s*" + _STR)
_PY_EVENT = re.compile(r"@\s*(\w{1,40})\s*\.\s*event[ \t]*\n\s*(?:async\s+)?def\s+(\w{1,80})")
_CONNECTS = re.compile(r"(?<![\w.$])io\s*\(|\bsocketio\s*\.\s*(?:Async)?Client\s*\(")
_SERVES = re.compile(r"""(?:from\s*|require\s*\(\s*)["']socket\.io["']|\bSocketIO\s*\(|\bsocketio\s*\.\s*(?:Async)?Server\s*\("""
                     r"""|\bnew\s+(?:WebSocket)?Server\s*\(|\bWebSocketServer\s*\(""")
_LISTEN = re.compile(r"\.\s*listen\s*\(|\b(?:app|uvicorn|socketio|sio|web)\s*\.\s*run(?:_app)?\s*\(")
_ALIAS = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(\s*|\brequire\s*\(\s*|^[ \t]*import\s+)["']([@~][^"'\s]{0,200})["']""", re.M)
_PARAM = re.compile(r"\$\{[^}\n]{0,80}\}|\{[^}\n]{0,80}\}|<[^>\n]{0,80}>")
_HOST = re.compile(r"^[a-z]{2,8}://[^/\s]{1,200}", re.I)
_REQ = re.compile(r"^[ \t]*([A-Za-z0-9][A-Za-z0-9._-]{0,100})", re.M)
_GO_REQ = re.compile(r"^[ \t]*(?:require[ \t]+)?([a-z0-9][\w.\-]{0,100}\.[a-z]{2,}/[\w.\-/]{1,200})[ \t]+v[\w.\-+]{1,60}", re.M)


# -- reading files --------------------------------------------------------------------------------------------------------------------

def matters(path: str) -> bool:
    """Whether a file changed between two commits may change the overview: a source code_map reads, a manifest, a page or a list."""
    p = PurePosixPath(path)
    return p.suffix in code_map.PY | code_map.JS or p.name in MANIFESTS or p.name in ALSO


def _text(root: Path, rel: str) -> str | None:
    """A file's text when it may be read: a file (no link), not secret, at most code_map.MAX_BYTES; None otherwise."""
    f = root / rel
    try:
        if is_secret(rel) or f.is_symlink() or not f.is_file() or f.stat().st_size > code_map.MAX_BYTES:
            return None
        return f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _is(root: Path, rel: str) -> bool:
    f = root / rel
    return not f.is_symlink() and f.is_file() and not is_secret(rel)


def _skipped(d: Path) -> bool:
    return d.name in code_map.SKIP or d.name.startswith(".") or d.is_symlink() or not d.is_dir()


def _folders(root: Path) -> list[str]:
    """The containers' folders: the root's when it has a manifest, then each folder at most DEPTH deep that has one and lies under no
    other (a folder under a container belongs to it)."""
    def has(rel: str) -> bool:
        return any(_is(root, f"{rel}/{m}" if rel != ROOT else m) for m in MANIFESTS)
    out = [ROOT] if has(ROOT) else []
    try:
        firsts = sorted(d for d in root.iterdir() if not _skipped(d))
    except OSError:
        return out
    for d in firsts:
        if has(d.name):
            out.append(d.name)
            continue
        if DEPTH < 2:
            continue
        try:
            seconds = sorted(e for e in d.iterdir() if not _skipped(e))
        except OSError:
            continue
        out += [f"{d.name}/{e.name}" for e in seconds if has(f"{d.name}/{e.name}")]
    return out


def owner(path: str, paths: list[str]) -> str | None:
    """The container (of `paths`) a part's or a file's path lies in: the deepest whose folder holds it; the root's ("."), when one is, for
    the rest; None when no container holds it."""
    best = None
    for c in paths:
        if c != ROOT and (path == c or path.startswith(c + "/")) and (best is None or len(c) > len(best)):
            best = c
    return best if best is not None else (ROOT if ROOT in paths else None)


def _rel(folder: str, name: str) -> str:
    return name if folder == ROOT else f"{folder}/{name}"


def _clean(path: str) -> str:
    return PurePosixPath(path.strip().lstrip("./") or ".").as_posix()


# -- a container's manifests: its stack and its ways in (§6.2, §6.4) -----------------------------------------------------------------------

def _npm(root: Path, folder: str, deps: list[tuple[str, str]], ways: list[dict]) -> None:
    text = _text(root, _rel(folder, "package.json"))
    try:
        pkg = json.loads(text) if text else None
    except ValueError:
        pkg = None
    if not isinstance(pkg, dict):
        return
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        if isinstance(pkg.get(key), dict):
            deps += [(str(n), "npm") for n in pkg[key]]
    if isinstance(pkg.get("main"), str) and pkg["main"].strip():
        ways.append({"kind": "main", "name": "", "path": _rel(folder, _clean(pkg["main"]))})
    bins = pkg.get("bin")
    if isinstance(bins, str):
        bins = {str(pkg.get("name") or PurePosixPath(folder).name): bins}
    for name, target in (bins.items() if isinstance(bins, dict) else []):
        if isinstance(target, str):
            ways.append({"kind": "bin", "name": str(name)[:80], "path": _rel(folder, _clean(target))})
    scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
    ways += [{"kind": "script", "name": s, "path": _rel(folder, "package.json")} for s in SCRIPTS if s in scripts]


def _pep508(spec: object) -> str:
    m = _REQ.match(spec) if isinstance(spec, str) else None
    return m.group(1) if m else ""


def _py(root: Path, folder: str, deps: list[tuple[str, str]], ways: list[dict]) -> None:
    text = _text(root, _rel(folder, "pyproject.toml"))
    try:
        doc = tomllib.loads(text) if text else {}
    except (tomllib.TOMLDecodeError, ValueError):
        doc = {}
    project = doc.get("project") if isinstance(doc.get("project"), dict) else {}
    names = list(project.get("dependencies") or []) if isinstance(project.get("dependencies"), list) else []
    for group in (project.get("optional-dependencies") or {}, doc.get("dependency-groups") or {}):
        for rows in (group.values() if isinstance(group, dict) else []):
            names += list(rows) if isinstance(rows, list) else []
    deps += [(n, "pypi") for n in map(_pep508, names) if n]
    poetry = ((doc.get("tool") or {}).get("poetry") or {}) if isinstance(doc.get("tool"), dict) else {}
    tables = [poetry.get("dependencies"), poetry.get("dev-dependencies")]
    tables += [g.get("dependencies") for g in (poetry.get("group") or {}).values() if isinstance(g, dict)] if isinstance(poetry.get("group"), dict) else []
    for t in tables:
        deps += [(str(n), "pypi") for n in (t if isinstance(t, dict) else {}) if str(n).lower() != "python"]
    for name, target in ((project.get("scripts") or {}).items() if isinstance(project.get("scripts"), dict) else []):
        ways.append({"kind": "bin", "name": str(name)[:80], "path": str(target)[:200]})
    for req in ("requirements.txt", "requirements-dev.txt"):
        lines = _text(root, _rel(folder, req)) or ""
        deps += [(n, "pypi") for n in _REQ.findall("\n".join(ln for ln in lines.splitlines() if not ln.lstrip().startswith(("#", "-"))))]


def _go(root: Path, folder: str, deps: list[tuple[str, str]], ways: list[dict]) -> None:
    text = _text(root, _rel(folder, "go.mod")) or ""
    deps += [(m, "go") for m in _GO_REQ.findall(text)]
    mains = ["main.go"]
    try:
        cmd = root / _rel(folder, "cmd")
        mains += [f"cmd/{d.name}/main.go" for d in sorted(cmd.iterdir()) if not _skipped(d)] if cmd.is_dir() else []
    except OSError:
        pass
    ways += [{"kind": "main", "name": "", "path": _rel(folder, m)} for m in mains[:LISTENS] if _is(root, _rel(folder, m))]


def _cargo(root: Path, folder: str, deps: list[tuple[str, str]], ways: list[dict]) -> None:
    text = _text(root, _rel(folder, "Cargo.toml"))
    try:
        doc = tomllib.loads(text) if text else {}
    except (tomllib.TOMLDecodeError, ValueError):
        doc = {}
    for key in ("dependencies", "dev-dependencies", "build-dependencies"):
        deps += [(str(n), "cargo") for n in (doc.get(key) if isinstance(doc.get(key), dict) else {})]
    if _is(root, _rel(folder, "src/main.rs")):
        ways.append({"kind": "main", "name": "", "path": _rel(folder, "src/main.rs")})
    for b in doc.get("bin") if isinstance(doc.get("bin"), list) else []:
        if isinstance(b, dict) and isinstance(b.get("name"), str):
            ways.append({"kind": "bin", "name": b["name"][:80], "path": _rel(folder, _clean(str(b.get("path") or "")) if b.get("path") else "")})


def _stack(deps: list[tuple[str, str]]) -> tuple[list[dict], int]:
    """The known packages as `{name, role}` (one each by the name a person knows it by), in STACK_ROLES' order; and how many are not
    known (types-only packages, `@types/…`, not counted)."""
    known: dict[str, str] = {}
    unknown: set[str] = set()
    for name, registry in deps:
        if registry == "npm" and name.startswith("@types/"):
            continue
        got = stacks_known.lib(name, registry)
        if got:
            known.setdefault(got[0], got[1])
        else:
            unknown.add(stacks_known.norm(name, registry))
    order = {r: n for n, r in enumerate(stacks_known.STACK_ROLES)}
    rows = sorted(known.items(), key=lambda kv: (order.get(kv[1], 99), kv[0].lower()))
    return [{"name": n, "role": r} for n, r in rows], len(unknown)


def _manifest(root: Path, folder: str) -> dict:
    deps: list[tuple[str, str]] = []
    ways: list[dict] = []
    for page in ("index.html", "public/index.html", "src/index.html"):
        if _is(root, _rel(folder, page)):
            ways.append({"kind": "page", "name": "", "path": _rel(folder, page)})
            break
    readers = {"package.json": _npm, "pyproject.toml": _py, "go.mod": _go, "Cargo.toml": _cargo}
    have = [m for m in MANIFESTS if _is(root, _rel(folder, m))]
    for m in have:
        readers[m](root, folder, deps, ways)
    if "pyproject.toml" not in have and any(_is(root, _rel(folder, r)) for r in ("requirements.txt", "requirements-dev.txt")):
        _py(root, folder, deps, ways)
    stack, unknown = _stack(deps)
    return {"manifests": have, "stack": stack, "unknown": unknown, "ways_in": ways}


# -- the sources: calls, answers, events (§6.3) ---------------------------------------------------------------------------------------

def _route(raw: str) -> str:
    """A path as called or answered, its parameters (`${id}`, `{id}`, `<int:id>`, `:id`) read as `*`, its host, query and fragment off;
    "" when it is no path of this project's (a host's root only, or no leading `/`)."""
    p = _HOST.sub("", raw.strip())
    p = _PARAM.sub("*", p).split("?", 1)[0].split("#", 1)[0]
    if p.startswith("*/"):                      # `${API}/api/x`: a base read from a variable
        p = p[1:]
    if not p.startswith("/"):
        return ""
    bits = ["*" if b.startswith(":") else b for b in p.split("/") if b]
    return "/" + "/".join(bits)


def _part_of(rel: str) -> str:
    parent = PurePosixPath(rel).parent.as_posix()
    return ROOT if parent in ("", ".") else parent


def _scan(rel: str, text: str, got: dict, made: dict[str, set[str]]) -> None:
    """One source file's calls out and answers into its container's `got`. `made`: the container's names of an HTTP client
    (`api = axios.create()`, "clients") and of a server or router (`rooms = Router()`, "servers")."""
    js = PurePosixPath(rel).suffix in code_map.JS

    def add(key: str, item: object) -> None:
        if len(got[key]) < CAP:
            got[key].append(item)

    if js:
        for m in _FETCH.finditer(text):
            path = _route(m.group(1))
            if path:
                window = text[m.end():m.end() + 240].split("fetch(", 1)[0]
                meth = _METHOD.search(window)
                add("calls", ("*" if meth is None and "method" in window else (meth.group(1).upper() if meth else "GET"), path, rel))
    calls = ("axios" in text or bool(made["clients"])) if js else _has(text, "requests", "httpx")
    for m in _CALL.finditer(text) if calls else ():
        who, verb, raw = m.group(1), m.group(2), m.group(3)
        caller = (who == "axios" or who in made["clients"]) if js else who in ("requests", "httpx")
        path = _route(raw) if caller else ""
        if path:
            add("calls", (verb.upper(), path, rel))
    if js:
        for m in _ANSWER.finditer(text) if _VERB.search(text) else ():
            who = m.group(1)
            low = who.lower()
            if who in made["servers"] or (who not in made["clients"] and (low in ("app", "router", "server", "fastify")
                                                                          or low.endswith(("router", "app")))):
                path = _route(m.group(4))
                if path:
                    add("answers", ("*" if m.group(2) == "all" else m.group(2).upper(), path, rel, m.group(4).strip()))
    else:
        for m in _PY_ROUTE.finditer(text):
            path = _route(m.group(3))
            if not path:
                continue
            kind, rest = m.group(1), m.group(4)
            meths = _PY_METHODS.search(rest)
            if kind in ("route", "api_route"):
                verbs = [v.upper() for v in re.findall(r"\w+", meths.group(1))] if meths else ["GET"]
            else:
                verbs = ["*" if kind == "websocket" else kind.upper()]
            for v in verbs:
                add("answers", (v, path, rel, m.group(3).strip()))
    for m in _MOUNT.finditer(text) if _has(text, "use(", "use (", "prefix") else ():
        prefix = _route(m.group(2) or m.group(4) or "")
        if prefix and prefix != "/" and len(got["mounts"]) < MOUNTS:
            got["mounts"].add(prefix)
    socketish = "socket" in text.lower() or _has(text, "io.", "sio.", "ws.", "sock.", "nsp.", "namespace.")
    for m in _SOCKET.finditer(text) if socketish else ():
        who, verb, event = m.group(1), m.group(3), m.group(4)
        if not (who in SOCKET_NAMES or "socket" in who.lower()) or "${" in event or "{" in event:
            continue
        if verb in ("on", "once") and event in ("connection", "connect") and who in SOCKET_NAMES - {"ws", "sock"}:
            got["serves"] = True
        if event in RESERVED:
            continue
        side = "emits" if verb == "emit" else "handles"
        if len(got[side]) < CAP:
            got[side].setdefault(event, rel)
    for who, event in _PY_EVENT.findall(text) if socketish else ():
        if who in SOCKET_NAMES and event not in RESERVED and len(got["handles"]) < CAP:
            got["handles"].setdefault(event, rel)
    if _has(text, "io(", "io (", "Client(") and _CONNECTS.search(text):
        got["connects"] = True
    if (socketish or "Server" in text) and _SERVES.search(text):
        got["serves"] = True
    if _has(text, "listen", ".run") and _LISTEN.search(text) and len(got["listens"]) < LISTENS:
        got["listens"].append(rel)


def _has(text: str, *words: str) -> bool:
    """Whether any of `words` is in `text`: a pattern is looked for only in a file that may hold it."""
    return any(w in text for w in words)


def _new() -> dict:
    return {"calls": [], "answers": [], "mounts": set(), "emits": {}, "handles": {}, "connects": False, "serves": False, "listens": []}


def _alias(rel: str, spec: str, container: str, known: set[str]) -> str | None:
    """A file of the project an import names by an alias (`@config/balance`, `~/net`, `@/views/Tv`), when the name resolves to one;
    an installed package (`@vitejs/plugin-react`) resolves to none."""
    bits = spec.split("/")
    if len(bits) < 2:
        return None
    head, rest = bits[0].lstrip("@~"), "/".join(bits[1:])
    base = "" if container == ROOT else container + "/"
    tries = [f"{base}src/{rest}", f"{base}{rest}"] if not head else [f"{head}/{rest}", f"{base}{head}/{rest}", f"{base}src/{head}/{rest}"]
    for t in tries:
        for cand in (t, *(t + e for e in code_map.JS), *(f"{t}/index{e}" for e in code_map.JS)):
            if cand in known and cand != rel:
                return cand
    return None


# -- the layers (§6.5) -----------------------------------------------------------------------------------------------------------------

def _role(path: str, container: str) -> str:
    bits = PurePosixPath(path).parts if container == ROOT else PurePosixPath(path).parts[len(PurePosixPath(container).parts):]
    for b in reversed(bits):
        role = stacks_known.ROLES.get(b.lower())
        if role:
            return role
    return ""


def _levels(paths: list[str], uses: dict[str, list[str]]) -> dict[str, int]:
    """Each part's level by the imports inside its container: 0 for a part no other part uses, else one more than the deepest part that
    uses it (a cycle broken where the fewest uses still wait)."""
    mine = set(paths)
    users: dict[str, set[str]] = {p: set() for p in paths}
    for u in paths:
        for t in uses.get(u, ()):
            if t in mine and t != u:
                users[t].add(u)
    level: dict[str, int] = {}
    waiting = {p: set(users[p]) for p in paths}
    while waiting:
        ready = sorted(p for p, w in waiting.items() if not w) or [min(waiting, key=lambda p: (len(waiting[p]), p))]
        for p in ready:
            level[p] = max((level[u] + 1 for u in users[p] if u in level), default=0)
            del waiting[p]
        for w in waiting.values():
            w.difference_update(ready)
    return level


def _layers(paths: list[str], container: str, uses: dict[str, list[str]]) -> list[dict]:
    """The container's parts top to bottom as rows `{role, parts}`: the parts no other uses (role ""), its face, its doors, the rest by
    their level, its data, its settings. A folder's role (stacks_known.ROLES) places it before its level does."""
    level = _levels(paths, uses)
    roles = {p: _role(p, container) for p in paths}
    rows: list[dict] = []

    def row(role: str, ps: list[str]) -> None:
        if ps:
            rows.append({"role": role, "parts": sorted(ps)})
    row("", [p for p in paths if not roles[p] and level[p] == 0])
    row("face", [p for p in paths if roles[p] == "face"])
    row("doors", [p for p in paths if roles[p] == "doors"])
    for n in sorted({level[p] for p in paths if not roles[p] and level[p] > 0}):
        row("", [p for p in paths if not roles[p] and level[p] == n])
    row("data", [p for p in paths if roles[p] == "data"])
    row("settings", [p for p in paths if roles[p] == "settings"])
    return rows


# -- the overview ------------------------------------------------------------------------------------------------------------------

def _routes(scan: dict) -> dict[int, list[tuple[list[str], str, str, str]]]:
    """A container's routes by their number of segments: `(segments, method, the path as written, the file)`, each also under every
    mount (`app.use("/api", router)`: a router's routes are answered under it)."""
    out: dict[int, list] = {}
    mounts = [""] + sorted(scan["mounts"])[:MOUNTS]
    for verb, route, answered, raw in scan["answers"]:
        for m in mounts:
            segs = [x for x in (m + route).split("/") if x]
            out.setdefault(len(segs), []).append((segs, verb, m + raw, answered))
    return out


def _links(ids: list[str], scans: dict[str, dict]) -> list[dict]:
    """The links between containers: `{from, to, http, socket}` for each ordered pair where `from` calls what `to` answers."""
    out = []
    routes = {c: _routes(scans[c]) for c in ids}
    for a in ids:
        for b in ids:
            if a == b:
                continue
            A, B = scans[a], scans[b]
            http, seen = [], set()
            for meth, path, called in A["calls"]:
                segs = [x for x in path.split("/") if x]
                for r, verb, shown, answered in routes[b].get(len(segs), ()):
                    if all(x == y or "*" in (x, y) for x, y in zip(segs, r)) and (meth == verb or "*" in (meth, verb)):
                        if (verb, shown) not in seen:                 # a call is one route: the first it matches
                            seen.add((verb, shown))
                            http.append({"method": verb, "path": shown, "called_in": called, "answered_in": answered})
                        break
            socket = []
            if B["serves"] and not A["serves"]:
                out_ = set(A["emits"]) & set(B["handles"])
                back = set(B["emits"]) & set(A["handles"])
                for ev in sorted(out_ | back):
                    way = "both" if ev in out_ and ev in back else "out" if ev in out_ else "back"
                    em, ha = (A["emits"], B["handles"]) if ev in out_ else (B["emits"], A["handles"])
                    socket.append({"event": ev, "way": way, "emitted_in": em[ev], "handled_in": ha[ev]})
                talks = A["connects"] or bool(socket)
            else:
                talks = False
            if http or talks:
                out.append({"from": a, "to": b, "http": sorted(http, key=lambda r: (r["path"], r["method"])), "socket": socket})
    return out


def empty() -> dict:
    return {"containers": [], "links": [], "shared": []}


def read(tree: Path, parts: list[dict] | None = None) -> dict:
    """`{containers, links, shared}` of a tree (As built (E1), docs/specs/90-what-the-first-look-said.md)."""
    root = Path(tree)
    parts = code_map.parts(root) if parts is None else parts
    files = [f.relative_to(root).as_posix() for f in code_map.sources(root)]
    ids = _folders(root)
    if ROOT not in ids and (any(owner(f, ids) is None for f in files) or any(owner(p["path"], ids) is None for p in parts)):
        ids.insert(0, ROOT)                                       # the root's own code, outside every container
    scans = {c: _new() for c in ids}
    known = set(files)
    alias_uses: dict[str, set[str]] = {}                          # a part: the parts that import it by an alias
    scripts = [f for f in files if PurePosixPath(f).suffix in code_map.JS]
    made: dict[str, dict[str, set[str]]] = {c: {"clients": set(), "servers": set()} for c in ids}
    for rel in scripts:                                           # first the names a container gives its clients and servers
        text = _text(root, rel) or ""
        if "axios" in text:
            made[owner(rel, ids)]["clients"] |= set(_AXIOS_MADE.findall(text))
        if _has(text, "Router", "express", "astify", "Koa", "Hono", "Elysia"):
            made[owner(rel, ids)]["servers"] |= set(_SERVER_MADE.findall(text))
    for rel in files:
        text = _text(root, rel)
        if text is None:
            continue
        c = owner(rel, ids)
        _scan(rel, text, scans[c], made[c])
        if PurePosixPath(rel).suffix in code_map.JS:
            for spec in _ALIAS.findall(text) if _has(text, "'@", '"@', "'~", '"~') else ():
                hit = _alias(rel, spec, c, known)
                if hit:
                    alias_uses.setdefault(_part_of(hit), set()).add(_part_of(rel))
    uses = {p["path"]: list(p.get("uses") or []) for p in parts}
    for target, users in alias_uses.items():
        for u in users:
            if u != target and target not in uses.setdefault(u, []):
                uses[u].append(target)
    used_by: dict[str, set[str]] = {}
    for u, ts in uses.items():
        for t in ts:
            used_by.setdefault(t, set()).add(u)
    containers = []
    for c in ids:
        mine = [p["path"] for p in parts if owner(p["path"], ids) == c]
        info = _manifest(root, c)
        ways = info["ways_in"] + [{"kind": "listen", "name": "", "path": f} for f in scans[c]["listens"]]
        containers.append({"path": c, "name": ROOT_NAME if c == ROOT else PurePosixPath(c).name, "manifests": info["manifests"],
                           "stack": info["stack"], "unknown": info["unknown"], "ways_in": ways, "layers": _layers(mine, c, uses),
                           "parts": sorted(mine)})
    shared = []
    for p in parts:
        by = {owner(u, ids) for u in used_by.get(p["path"], ())} - {None}
        if len(by) >= 2:
            shared.append({"path": p["path"], "container": owner(p["path"], ids), "containers": sorted(by),
                           "used_by": sorted(used_by[p["path"]])})
    return {"containers": containers, "links": _links(ids, scans), "shared": shared}
