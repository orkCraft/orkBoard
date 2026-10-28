"""The routes of an app, read from dev's tree (docs/specs/102-the-other-maps-and-picking-on-them.md §1.1, decisions §112.7): the screens of Design's
map, by code with no model. The tree is a commit's (`git ls-tree`, `git cat-file`), never the working tree, so what a person has half-written or an
agent is changing does not show. Used by realm/screen_map.py, which lays the screens out along their flow.

    tree = Tree(root, sha)                    # a commit's files, read through git (listed once, a file read once)
    source, rows = routes(tree)               # ("react-router", [{"path": "/orders/:id", "name": "Order", "file": "src/pages/Order.tsx"}, ...])

A router is read in this order, the first that gives screens wins: Next.js `app/**/page.*`, Next.js and Nuxt `pages/`, SvelteKit `routes/**/+page.svelte`,
Expo Router's `app/`, React Router's `path:` and `<Route path=>`, Vue Router's `path:`, Flutter's `routes:` map (and go_router's `GoRoute`); else a `screens/`,
`views/` or `pages/` folder's files. A row is `{path, name, file}`: the route, its name as a person says it (the component's, else the path's), the file
of its component (else the file the table is in). Bounded: MAX_LIST files listed, MAX_BYTES a file, MAX_TABLES files searched for a table, none that may
hold a secret, none in a folder of dependencies, builds or tests. Nothing is run. No face, no model.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path, PurePosixPath

from orkboard.hooks.warder import is_secret
from orkboard.realm import code_map

MAX_LIST = 60_000                      # the most files of a commit listed
MAX_BYTES = 200_000                    # the most a file read may hold
MAX_TABLES = 80                        # the most files a router's table is read from
MAX_SCAN = 1500                        # the most source files searched for a router's table
SCAN_BYTES = 60_000                    # … and none over this
MAX_ROWS = 400                         # the most routes one router gives
GIT_S = 30
SKIP = set(code_map.SKIP) | {"vendor", "Pods", ".dart_tool", "ios", "android", "macos", "windows", "linux", "test", "tests", "__tests__", "__mocks__",
                             "e2e", "cypress", "spec", "stories", "storybook", ".storybook"}
CODE = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".vue", ".svelte")
FILES = CODE + (".dart",)
NOT_SCREEN = re.compile(r"\.(test|spec|stories|story|d|styles?|module|config)\.|\.(css|scss|less|json|md|snap)$|^_|^\+(layout|error|server)")
FOLDERS = ("screens", "views", "pages")
SUFFIXES = {"screen", "page", "view", "route"}
BARE = {"Scaffold", "MaterialPageRoute", "CupertinoPageRoute", "Builder", "Center", "Container"}

SOURCES = {"next-app": "Next.js app/", "next-pages": "Next.js pages/", "pages": "the pages/ folder", "sveltekit": "SvelteKit routes/",
           "expo-router": "Expo Router app/", "react-router": "React Router", "vue-router": "Vue Router", "flutter": "Flutter routes",
           "screens": "the screens/ folder", "views": "the views/ folder"}


# -- a commit's files --------------------------------------------------------------------------------------------------------------------

def _run(root: Path, args: list[str], data: bytes = b"") -> bytes:
    try:
        got = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, input=data, capture_output=True, timeout=GIT_S)
    except (OSError, subprocess.SubprocessError):
        return b""
    return got.stdout if got.returncode == 0 else b""


def _kept(path: str) -> bool:
    """Whether a file of the tree may be read: no hidden folder, none of dependencies, builds or tests, no secret, no odd name."""
    bits = path.split("/")
    return not (any(b in SKIP or (b.startswith(".") and b != ".") for b in bits[:-1]) or bits[-1].startswith(".") or "\n" in path or is_secret(path))


class Tree:
    """The files of a commit: `files` (sorted paths of the blobs worth reading), `text(path)` (a file's text, "" when it is gone or too big)."""

    def __init__(self, root: Path, sha: str) -> None:
        self.root, self.sha = Path(root), sha
        self.sizes: dict[str, int] = {}
        self._text: dict[str, str] = {}
        raw = _run(self.root, ["ls-tree", "-r", "-l", "-z", "--full-tree", sha])
        for rec in raw.split(b"\0")[:MAX_LIST]:
            meta, _, name = rec.partition(b"\t")
            bits = meta.split()
            if len(bits) != 4 or bits[1] != b"blob" or bits[0] == b"120000":
                continue
            path = name.decode("utf-8", "replace")
            if _kept(path) and PurePosixPath(path).suffix in FILES + (".json",):
                self.sizes[path] = int(bits[3]) if bits[3].isdigit() else MAX_BYTES + 1
        self.files = sorted(self.sizes)
        self.set = set(self.files)

    def load(self, paths: list[str]) -> None:
        """Read `paths` in one call (the ones too big are "")."""
        need = [p for p in dict.fromkeys(paths) if p not in self._text]
        for p in need:
            if p not in self.sizes or self.sizes[p] > MAX_BYTES:
                self._text[p] = ""
        need = [p for p in need if p not in self._text]
        if not need:
            return
        data = _run(self.root, ["cat-file", "--batch"], "".join(f"{self.sha}:{p}\n" for p in need).encode("utf-8"))
        at = 0
        for p in need:
            end = data.find(b"\n", at)
            if end < 0:
                self._text[p] = ""
                continue
            head = data[at:end].split()
            at = end + 1
            if len(head) == 3 and head[1] == b"blob" and head[2].isdigit():
                size = int(head[2])
                self._text[p] = data[at:at + size].decode("utf-8", "replace")
                at += size + 1
            else:
                self._text[p] = ""

    def text(self, path: str) -> str:
        if path not in self._text:
            self.load([path])
        return self._text.get(path, "")


# -- names -------------------------------------------------------------------------------------------------------------------------------

def words(stem: str) -> list[str]:
    """A file's or a component's name as lower-case words: `OrderListScreen` → order, list (a trailing Screen, Page or View left off)."""
    bits = [w for w in re.split(r"[\s_\-.]+", re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", stem)) if w]
    low = [w.lower() for w in bits]
    return low[:-1] if len(low) > 1 and low[-1] in SUFFIXES else low


def name_of(stem: str) -> str:
    w = " ".join(words(stem))
    return (w[:1].upper() + w[1:]) if w else ""


def path_name(path: str) -> str:
    """A route as a name: `/` Home, `/orders/:id` Orders id."""
    bits = [b.lstrip(":") for b in path.split("/") if b and b != "*"]
    return "Home" if not bits else name_of(" ".join(bits))


def file_route(segs: list[str]) -> str:
    """The route of a file-based router's path segments: groups `(g)` and slots `@s` left out, `index` the folder's, `[id]` `:id`, `[...rest]` `*`."""
    out = []
    for s in segs:
        if s == "index" or re.fullmatch(r"\(.*\)", s) or s.startswith("@"):
            continue
        if re.fullmatch(r"\[\[?\.\.\.\w+\]?\]", s):
            out.append("*")
        elif (m := re.fullmatch(r"\[(\w+)\]", s)):
            out.append(":" + m.group(1))
        else:
            out.append(s)
    return "/" + "/".join(out)


def _row(path: str, name: str, file: str) -> dict:
    return {"path": path, "name": name or path_name(path), "file": file}


def _order(rows: list[dict], table: bool = False) -> list[dict]:
    """The rows once each path, the first of a path winning: a table's as it declares them, a file-based router's "/" first then by path (it has no
    order of its own)."""
    seen: dict[str, dict] = {}
    for r in rows:
        seen.setdefault(r["path"], r)
    return (list(seen.values()) if table else sorted(seen.values(), key=lambda r: (r["path"] != "/", r["path"])))[:MAX_ROWS]


# -- file-based routers --------------------------------------------------------------------------------------------------------------------

def _depends(tree: Tree) -> set[str]:
    """The dependencies every `package.json` of the tree (at most 12, two folders deep) names."""
    found: set[str] = set()
    paths = [p for p in tree.files if p.endswith("package.json") and p.count("/") <= 2][:12]
    tree.load(paths)
    for p in paths:
        try:
            got = json.loads(tree.text(p))
        except ValueError:
            continue
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            if isinstance(got, dict) and isinstance(got.get(key), dict):
                found |= set(got[key])
    return found


def _under(tree: Tree, folder: str, exts: tuple[str, ...], depth: int = 3) -> list[tuple[str, list[str]]]:
    """(the file, its path segments below the first `folder` of its path) of every file with an extension in `exts`; `folder` is at most `depth` folders down."""
    out = []
    for p in tree.files:
        bits = p.split("/")
        at = next((i for i, b in enumerate(bits[:-1]) if b == folder and i <= depth), None)
        if at is not None and PurePosixPath(p).suffix in exts:
            out.append((p, bits[at + 1:]))
    return out


def _next_app(tree: Tree) -> list[dict]:
    rows = []
    for p, bits in _under(tree, "app", (".js", ".jsx", ".ts", ".tsx", ".mdx")):
        if PurePosixPath(bits[-1]).stem == "page":
            rows.append(_row(file_route(bits[:-1]), "", p))
    return _order(rows)


def _sveltekit(tree: Tree) -> list[dict]:
    rows = []
    for p, bits in _under(tree, "routes", (".svelte",)):
        if bits[-1] == "+page.svelte":
            rows.append(_row(file_route(bits[:-1]), "", p))
    return _order(rows)


def _expo(tree: Tree) -> list[dict]:
    rows = []
    for p, bits in _under(tree, "app", (".js", ".jsx", ".ts", ".tsx")):
        stem = PurePosixPath(bits[-1]).stem
        if not NOT_SCREEN.search(bits[-1]) and not stem.startswith("+") and stem != "_layout":
            rows.append(_row(file_route(bits[:-1] + [stem]), "", p))
    return _order(rows)


def _pages(tree: Tree) -> list[dict]:
    """Next.js' and Nuxt's `pages/` (and an app's own): a file a route, `index` the folder's, `[id]` a parameter; `_app`, `_document`, `api/` are not screens."""
    rows = []
    for p, bits in _under(tree, "pages", CODE):
        if "api" in bits[:-1] or any(b.startswith("_") for b in bits) or NOT_SCREEN.search(bits[-1]):
            continue
        rows.append(_row(file_route(bits[:-1] + [PurePosixPath(bits[-1]).stem]), "", p))
    return _order(rows)


def _kebab(stem: str) -> str:
    return "-".join(words(stem))


def _folder(tree: Tree, folder: str) -> list[dict]:
    """A `screens/` or `views/` folder's files: a file a screen named after it (`OrderList.tsx` → Order list, `/order-list`); a folder holding an
    `index` file is one screen (its other files are its parts)."""
    files = [(p, bits) for p, bits in _under(tree, folder, FILES, depth=4) if not NOT_SCREEN.search(bits[-1])]
    indexed = {tuple(bits[:-1]) for _p, bits in files if PurePosixPath(bits[-1]).stem == "index" and PurePosixPath(bits[-1]).suffix != ".dart"}
    rows = []
    for p, bits in files:
        stem = PurePosixPath(bits[-1]).stem
        if tuple(bits[:-1]) in indexed and stem != "index":
            continue
        folders = [_kebab(b) for b in bits[:-1] if _kebab(b)]
        if stem == "index":
            if not folders:
                continue
            name, route = name_of(bits[-2]), "/" + "/".join(folders)
        else:
            name, route = name_of(stem), "/" + "/".join(folders + [_kebab(stem)])
        if name:
            rows.append(_row(route, name, p))
    return _order(rows)


# -- routers in code: React Router, Vue Router ------------------------------------------------------------------------------------------------

_TOKEN = re.compile(r"""
    (?P<comment>//[^\n]*|/\*.*?\*/)
  | (?P<path>\bpath\s*[:=]\s*\{?\s*(?P<q>["'`])(?P<p>[^"'`\n]{0,200})(?P=q))
  | (?P<children>\bchildren\s*:)
  | (?P<index>\bindex\s*:\s*true\b|\bindex(?=\s+(?:element|[cC]omponent)\s*=)|\bindex\s*=\s*\{?\s*true\b)
  | (?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`)
  | (?P<jsx><Route\b)
  | (?P<close></Route\s*>)
  | (?P<gt>/?>)
  | (?P<ob>\{) | (?P<cb>\}) | (?P<other>.)
""", re.X | re.S)
_ELEMENT = re.compile(r"""\b(?:element|[cC]omponent)\s*[:=]\s*\{?\s*<?\s*([A-Z]\w*)""")
_LAZY_IN = re.compile(r"""\bimport\(\s*["']([^"']+)["']""")
_IMPORT_DEFAULT = re.compile(r"""\bimport\s+([A-Za-z_$][\w$]*)\s*(?:,\s*\{[^}]*\})?\s+from\s+["']([^"']+)["']""")
_IMPORT_NAMED = re.compile(r"""\bimport\s+(?:[\w$]+\s*,\s*)?\{([^}]*)\}\s*from\s+["']([^"']+)["']""")
_LAZY = re.compile(r"""\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:\w+\.)?lazy\(\s*\(\s*\)\s*=>\s*import\(\s*["']([^"']+)["']""")
_ROUTE_PATH = re.compile(r"[\w:\-./*?\[\]()]*")
EXTS = (".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte", ".mjs")


def _imports(text: str) -> dict[str, str]:
    """A file's imported names and where from: `import A from`, `import { A as B } from`, `const A = lazy(() => import(…))`."""
    got = {m.group(1): m.group(2) for m in _IMPORT_DEFAULT.finditer(text)}
    for m in _IMPORT_NAMED.finditer(text):
        for item in m.group(1).split(","):
            bits = item.replace(" type ", " ").split(" as ")
            if bits[-1].strip():
                got[bits[-1].strip()] = m.group(2)
    got.update({m.group(1): m.group(2) for m in _LAZY.finditer(text)})
    return got


def resolve(tree: Tree, here: str, spec: str) -> str:
    """The file a relative or `@/` import names ("" when it is none of the tree's)."""
    if spec.startswith("."):
        base = PurePosixPath(here).parent.joinpath(spec).as_posix()
        parts: list[str] = []
        for b in base.split("/"):
            if b == "..":
                if parts:
                    parts.pop()
            elif b not in ("", "."):
                parts.append(b)
        bases = ["/".join(parts)]
    elif spec[:2] in ("@/", "~/"):
        bases = ["src/" + spec[2:], spec[2:]]
    else:
        return ""
    for b in bases:
        for cand in [b, *(b + e for e in EXTS), *(f"{b}/index{e}" for e in EXTS)]:
            if cand in tree.set and PurePosixPath(cand).suffix in CODE:
                return cand
    return ""


def _component(tree: Tree, here: str, own: str, known: dict[str, str]) -> tuple[str, str]:
    """(the name, the file) of the component a route's own text names: `element: <Orders />`, `component: Orders`, `component: () => import('./Orders.vue')`."""
    if (m := _ELEMENT.search(own)):
        ident = m.group(1)
        return name_of(ident), (resolve(tree, here, known[ident]) if ident in known else "")
    if (m := _LAZY_IN.search(own)):
        file = resolve(tree, here, m.group(1))
        return name_of(PurePosixPath(file or m.group(1)).stem if (file or "/" in m.group(1)) else m.group(1)), file
    return "", ""


def _join(parent: str, path: str) -> str:
    if path.startswith("/"):
        return path
    return (parent.rstrip("/") + "/" + path.lstrip("./")).replace("//", "/") if parent else "/" + path.lstrip("./")


def table_routes(tree: Tree, here: str, text: str) -> list[dict]:
    """The routes a file's tables declare, parents before their children, a child's relative path under its parent's: `{path: "/a", element: <A />,
    children: [{path: "b"}]}` and `<Route path="/a" element={<A />}><Route path="b" /></Route>` both give /a and /a/b."""
    known = _imports(text)
    stack: list[dict] = []
    rows: list[dict] = []

    def done(frame: dict, end: int) -> None:
        own = text[frame["open"]:min(frame.get("own_end") or end, end)]
        if frame.get("row") is not None:
            if frame["row"].get("indexed"):
                return
            frame["row"]["name"], frame["row"]["file"] = _component(tree, here, own, known)
        elif frame.get("index"):                       # an index route is its parent's screen: the parent's own component is the layout around it
            parent = next((f["row"] for f in reversed(stack) if f is not frame and f.get("row") is not None), None)
            name, file = _component(tree, here, own, known)
            if parent is not None and (name or file):
                parent["name"], parent["file"], parent["indexed"] = name, file, True

    for m in _TOKEN.finditer(text):
        kind = ""
        for k in ("path", "comment", "children", "index", "string", "jsx", "close", "gt", "ob", "cb"):
            if m.group(k) is not None:
                kind = k
                break
        if kind == "jsx":
            stack.append({"kind": "jsx", "open": m.start(), "tag": True, "base": len(stack), "full": ""})
        elif kind == "ob":
            stack.append({"kind": "obj", "open": m.start(), "full": ""})
        elif kind == "cb":
            if stack and stack[-1]["kind"] == "obj":
                done(stack.pop(), m.start())
        elif kind == "gt":
            top = stack[-1] if stack else None
            if top and top["kind"] == "jsx" and top["tag"] and top["base"] == len(stack) - 1:
                top["tag"] = False
                top["own_end"] = m.start()
                if m.group("gt") == "/>":
                    done(stack.pop(), m.start())
        elif kind == "close":
            while stack and stack[-1]["kind"] == "obj":
                stack.pop()
            if stack and stack[-1]["kind"] == "jsx":
                done(stack.pop(), m.start())
        elif kind == "index":
            if stack:
                stack[-1]["index"] = True
        elif kind == "children":
            if stack and stack[-1].get("own_end") is None:
                stack[-1]["own_end"] = m.start()
        elif kind == "path" and stack:
            p = m.group("p").strip()
            top = stack[-1]
            if top.get("row") is not None or not _ROUTE_PATH.fullmatch(p) or not p or "$" in p:
                continue
            parent = next((f["full"] for f in reversed(stack[:-1]) if f.get("full")), "")
            top["full"] = _join(parent, p)
            if top["full"] != "/*" and top["full"] != "*":
                top["row"] = {"path": top["full"].split("?")[0], "name": "", "file": ""}
                rows.append(top["row"])
    for frame in stack:
        done(frame, len(text))
    return [_row(r["path"], r["name"], r["file"] or here) for r in rows]


def _scan(tree: Tree, exts: tuple[str, ...]) -> list[str]:
    """The source files worth searching for a router's table (small ones, at most MAX_SCAN), read in one call."""
    paths = [p for p in tree.files if PurePosixPath(p).suffix in exts and tree.sizes[p] <= SCAN_BYTES][:MAX_SCAN]
    tree.load(paths)
    return paths


def _code_router(tree: Tree, marker: str) -> list[dict]:
    hits = [p for p in _scan(tree, CODE) if marker in tree.text(p)][:MAX_TABLES]
    rows = []
    for p in hits:
        rows += table_routes(tree, p, tree.text(p))
    return _order(rows, table=True)


# -- Flutter ---------------------------------------------------------------------------------------------------------------------------------

_DART_ROUTES = re.compile(r"""\broutes\s*:\s*(?:<[^>{}]*>)?\s*\{""")
_DART_KEY = re.compile(r"""["'](/[^"'\s$]*)["']\s*:""")
_DART_CTOR = re.compile(r"""(?:\bconst\s+)?\b([A-Z]\w*)\s*\(""")
_GO_ROUTE = re.compile(r"""\bGoRoute\s*\(\s*(?:name\s*:\s*["'][^"']*["']\s*,\s*)?path\s*:\s*["']([^"'$]+)["']""")


def _ctor(body: str) -> str:
    return next((m.group(1) for m in _DART_CTOR.finditer(body) if m.group(1) not in BARE), "")


def _dart_file(tree: Tree, cls: str, here: str) -> str:
    snake = "_".join(w.lower() for w in re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", cls).split()) + ".dart"
    return next((p for p in tree.files if p.endswith("/" + snake) or p == snake), here)


def _flutter(tree: Tree) -> list[dict]:
    rows = []
    for p in _scan(tree, (".dart",)):
        if len(rows) >= MAX_ROWS:
            break
        text = tree.text(p)
        if "routes" not in text and "GoRoute" not in text:
            continue
        for m in _DART_ROUTES.finditer(text):
            depth, end = 1, m.end()
            while end < len(text) and depth:
                depth += (text[end] == "{") - (text[end] == "}")
                end += 1
            block = text[m.end():end]
            keys = list(_DART_KEY.finditer(block))
            for i, k in enumerate(keys):
                cls = _ctor(block[k.end():keys[i + 1].start() if i + 1 < len(keys) else len(block)])
                rows.append(_row(k.group(1).rstrip("/") or "/", name_of(cls) if cls else "", _dart_file(tree, cls, p) if cls else p))
        gos = list(_GO_ROUTE.finditer(text))
        for i, g in enumerate(gos):
            cls = _ctor(text[g.end():gos[i + 1].start() if i + 1 < len(gos) else min(len(text), g.end() + 600)][:600])
            path = g.group(1) if g.group(1).startswith("/") else "/" + g.group(1)
            rows.append(_row(path, name_of(cls) if cls else "", _dart_file(tree, cls, p) if cls else p))
    return rows and _order(rows, table=True)


# -- the first router that gives screens -----------------------------------------------------------------------------------------------------------

def routes(tree: Tree) -> tuple[str, list[dict]]:
    """(the router's key, its routes) at the tree; ("", []) for a project with no screen to read (a library, a backend)."""
    if not tree.files:
        return "", []
    dep = _depends(tree)
    steps = [("next-app", lambda: _next_app(tree)), ("sveltekit", lambda: _sveltekit(tree)),
             ("expo-router", lambda: _expo(tree) if "expo-router" in dep or "expo" in dep else []),
             ("next-pages", lambda: _pages(tree) if dep & {"next", "nuxt"} else []),
             ("react-router", lambda: _code_router(tree, "react-router")), ("vue-router", lambda: _code_router(tree, "vue-router")),
             ("flutter", lambda: _flutter(tree)), ("pages", lambda: _pages(tree)),
             ("screens", lambda: _folder(tree, "screens")), ("views", lambda: _folder(tree, "views"))]
    for key, read in steps:
        got = read()
        if got:
            return key, got
    return "", []
