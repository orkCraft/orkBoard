"""Marketing's map, the way in (docs/specs/102-the-other-maps-and-picking-on-them.md §3.3, decisions §151.7): how people come to the project, in four steps, *channels* →
*the store page or the site* → *the install* → *the first session*, each read by name from dev's tree (never the working tree, never a file's contents). No model, no face.

    way_map.read(state_dir, root, ref="dev")             # {commit, short, ref, steps: [...], channels, store, install, first_session}: each step {holds: [{path, kind}], none, more}
    way_map.text(state_dir, root, since="", pages=None, ref="dev")   # Marketing's leader's map as text; None with no dev

What a step holds, by name (the lists are this module's constants):
- **channels**: the files of a folder named for reaching people (`marketing/`, `campaigns/`, `ads/`, `social/`, `press/`, `press-kit/`, `newsletter/`, `outreach/`, `seo/`) and
  `sitemap.xml` and `robots.txt` at the top. `kind` "channel".
- **store**: the store's metadata (`fastlane/metadata/**` at the top or under `ios/` or `android/`, `store/`, `appstore/`, `play-store/`, `playstore/`, `metadata/`), kind
  "store"; and the pages (`.html .htm .md .mdx`) of a `landing/`, `site/` or `web/` folder at the top, kind "site".
- **install**: the files that put the project on a machine (`install.sh`, `install.ps1`, `INSTALL.md`, `Dockerfile`, `docker-compose.yml`, `fastlane/Fastfile`, `fastlane/Appfile`,
  `eas.json`, `electron-builder.*`, `snap/snapcraft.yaml`, `Formula/*.rb`, `homebrew/*`), kind "install".
- **first_session**: the app's entry screen, **one file**, kind "entry". `realm/screen_map.py` (spec 102 A) is not part of this tree, so it is found here by the router's own names, the
  first that exists: Next.js `app/page.*` · `pages/index.*`, SvelteKit `src/routes/+page.svelte`, Expo Router `app/index.*`, Flutter `lib/main.dart`, `src/App.*` · `App.*`, `index.html`
  (`public/` too), else the first file of a `screens/`, `pages/` or `views/` folder named home, index, main, welcome, onboarding, start or landing. When screen_map is in the
  tree, its entry screen replaces this (one place for it).

A step holds at most HOLDS files (`more`: how many were left out), sorted by path; `none` is True when it holds nothing. A secret's path, a hidden folder and the folders
code_map.SKIP names are never read.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from orkboard.hooks.warder import is_secret
from orkboard.realm import code_map, commit_goal

STEPS = ("channels", "store", "install", "first_session")
LINE = 500                                        # a step's line of the text, at most
HOLDS = 24                                        # the most files a step lists
FILES_MAX = 50_000                                # the most paths of the tree read
CHANNEL_DIRS = ("marketing", "campaigns", "ads", "social", "press", "press-kit", "newsletter", "outreach", "seo")
CHANNEL_FILES = ("sitemap.xml", "robots.txt")
STORE_DIRS = ("fastlane/metadata", "ios/fastlane/metadata", "android/fastlane/metadata", "store", "appstore", "play-store", "playstore", "metadata")
SITE_DIRS = ("landing", "site", "web")
SITE_PAGES = (".html", ".htm", ".md", ".mdx")
INSTALL_FILES = ("install.sh", "install.ps1", "install.md", "dockerfile", "docker-compose.yml", "docker-compose.yaml", "fastlane/fastfile", "fastlane/appfile",
                 "eas.json", "snap/snapcraft.yaml")
INSTALL_DIRS = ("formula", "homebrew")
ENTRY = (r"app/page\.\w+", r"src/app/page\.\w+", r"pages/index\.\w+", r"src/pages/index\.\w+", r"src/routes/\+page\.svelte", r"app/index\.\w+", r"lib/main\.dart",
         r"src/App\.\w+", r"App\.\w+", r"index\.html", r"public/index\.html")
ENTRY_FOLDERS = ("screens", "pages", "views")
ENTRY_NAMES = ("home", "index", "main", "welcome", "onboarding", "start", "landing")
CODE = {".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".dart", ".swift", ".kt", ".html"}
WHAT = {"channels": "the campaigns' folders (marketing/, campaigns/, ads/, social/, press/)",
        "store": "the store's metadata (fastlane/metadata/, store/) or the site's pages (landing/, site/, web/)",
        "install": "the install's files (install.sh, a Dockerfile, fastlane/Fastfile)",
        "first_session": "the app's entry screen"}
TITLES = {"channels": "Channels", "store": "The store page or the site", "install": "The install", "first_session": "The first session"}


def _tree(root: Path, ref: str) -> list[str]:
    """The paths of `ref`'s head tree (files, sorted): none that a secret names, in a hidden folder or in a folder code_map.SKIP names; [] with no such branch."""
    tip = commit_goal.head(root, ref)
    if not tip:
        return []
    try:
        got = subprocess.run(["git", "--literal-pathspecs", "-c", "core.quotePath=false", "ls-tree", "-r", "--name-only", "-z", tip], cwd=root, capture_output=True,
                             text=True, errors="replace", timeout=commit_goal.GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return []
    paths = []
    for p in got.stdout.split("\0")[:FILES_MAX] if got.returncode == 0 else []:
        bits = p.split("/")
        if p and not any(b in code_map.SKIP or b.startswith(".") for b in bits[:-1]) and not is_secret(p):
            paths.append(p)
    return sorted(paths)


def _under(path: str, folders: tuple[str, ...]) -> bool:
    return any(path.startswith(f + "/") for f in folders)


def _holds(rows: list[tuple[str, str]]) -> dict:
    rows = sorted(set(rows))
    return {"holds": [{"path": p, "kind": k} for p, k in rows[:HOLDS]], "none": not rows, "more": max(0, len(rows) - HOLDS)}


def _entry(paths: list[str]) -> list[tuple[str, str]]:
    have = set(paths)
    for pattern in ENTRY:
        found = sorted(p for p in have if re.fullmatch(pattern, p))
        if found:
            return [(found[0], "entry")]
    for stem in ENTRY_NAMES:
        for p in paths:
            folder, _, name = p.rpartition("/")
            stem_, _, ext = name.rpartition(".")
            if folder.rpartition("/")[2] in ENTRY_FOLDERS and stem_.lower() == stem and "." + ext.lower() in CODE:
                return [(p, "entry")]
    return []


def read(state_dir: Path, root: Path, ref: str = "dev") -> dict:
    """The map (see the module). With no dev branch: every step holds nothing and `commit` is ""."""
    root = Path(root)
    paths = _tree(root, ref)
    lower = {p: p.lower() for p in paths}
    channels = [(p, "channel") for p in paths if _under(p, CHANNEL_DIRS) or lower[p] in CHANNEL_FILES]
    store = [(p, "store") for p in paths if _under(p, STORE_DIRS)]
    store += [(p, "site") for p in paths if _under(p, SITE_DIRS) and lower[p].endswith(SITE_PAGES)]
    install = [(p, "install") for p in paths if lower[p] in INSTALL_FILES or _under(lower[p], INSTALL_DIRS) or lower[p].startswith("electron-builder.")]
    tip = commit_goal.head(root, ref)
    return {"commit": tip, "short": tip[:7], "ref": ref, "steps": list(STEPS), "channels": _holds(channels), "store": _holds(store), "install": _holds(install),
            "first_session": _holds(_entry(paths))}


def _line(step: str, got: dict) -> str:
    if got["none"]:
        return f"{TITLES[step]}: Nothing to read yet: {WHAT[step]}."
    names = ", ".join(h["path"] for h in got["holds"][:6])
    left = len(got["holds"]) - 6 + got["more"]
    return (f"{TITLES[step]}: {names}" + (f" and {left} more" if left > 0 else ""))[:LINE]


def text(state_dir: Path, root: Path, since: str = "", pages: Path | None = None, ref: str = "dev") -> str | None:
    """Marketing's map as text: the four steps and what each holds, a step with nothing *Nothing to read yet: …*. None when the project has no `dev` to read.
    `since` and `pages` are the other maps' (the call's last commit, the Board's pages): this map is a state read by names, so it uses neither."""
    got = read(state_dir, root, ref)
    if not got["commit"]:
        return None
    n = 0
    lines = []
    for step in STEPS:
        n += 1
        lines.append(f"{n}. {_line(step, got[step])}")
    return "\n".join([f"The map of the way in at {ref} {got['short']} (how people come, read from the project's files by name)", ""] + lines)
