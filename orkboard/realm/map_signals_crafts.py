"""What the maps of Art, Release and Marketing say is wrong, by code (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §3; decisions §184): the hints of `realm/map_signals.py` for the three
crafts that had none, each grounded in what the map holds. A hint is not a verdict (the leader judges it, `core/idea_concerns.py`). Read from dev's tree, git and the Board; no model, no face; nothing
is written. `realm/map_signals.py` dispatches to it; it imports none of that module.

    map_signals_crafts.art(state_dir, root, ref="dev")                  # [{on, kind, words}]: Art's assets
    map_signals_crafts.release(state_dir, root, pages=None, into="dev")  # [{on, kind, words}]: what waits in `into` for main
    map_signals_crafts.marketing(state_dir, root, ref="dev")            # [{on, kind, words}]: the way in

`on` is the id of a part of the map as it is drawn (`realm/map_parts.py`: an asset's path, a goal's slug, a file of the way in), "" where a hint belongs to no part; `kind` names the rule; `words` is a
line for a model, in plain English. Each list is in the order of the kinds below, and [] for a map that cannot be read, a project with no `ref` and a repository git cannot read (a hint that cannot be
read is no hint, never an error for a caller; `MAX_SIGNALS` cuts them in `map_signals.signals`).
- `art` (from `art_map.read`, Art's own kinds): `mixed_sizes` (a folder of pictures of MIXED_SIZES different sizes or more, on its first picture), `naming` (a file whose name has a space or a capital
  in a folder where most names are lower-case with none), `heavy` (a picture of HEAVY_ART bytes or more, a sound of HEAVY_SOUND), `unused` (an asset whose file name no source file at the ref names:
  one `git grep -F -o -h` of at most UNUSED_NAMES names in the code_map source kinds and `.json .html .css`; none when the project has no such file).
- `release` (from `release_map.read`, when goals or commits wait): `big_batch` (BATCH_GOALS goals or BATCH_FILES files or more wait), `stale` (a goal whose commit is STALE_DAYS days old or more),
  `no_changelog` (`into` holds no CHANGELOG*, CHANGES*, HISTORY* or NEWS* at its top while goals wait), `reverts` (commits waiting whose subject begins `Revert`).
- `marketing` (from `way_map.read` and dev's tree; the files' contents only for the store's two texts and the code's `git grep`): `no_channel` (the channels step holds nothing), `aso_title` (a store
  `title.txt` or `name.txt` of more than TITLE_MAX characters), `aso_short` (a `short_description.txt` or `subtitle.txt` of more than SHORT_MAX), `no_shots` (store metadata and no screenshots),
  `no_onboarding` (no file or folder named onboarding, tutorial, welcome, intro or walkthrough; on the first session's file), `no_return` (no source file names a notification, a push, a daily reward or a
  streak), `no_share` (none names sharing, an invite or a referral), `no_revenue` (no manifest names a payment library).
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path, PurePosixPath

from orkboard.realm import art_map, code_map, commit_goal, release_map, way_map

MIXED_SIZES = 4                     # a folder of pictures of this many sizes
HEAVY_ART, HEAVY_SOUND = 1 << 20, 1 << 20   # a picture, a sound of this many bytes (1 MB)
UNUSED_NAMES = 200                  # the most asset names `git grep` is asked for
BATCH_GOALS, BATCH_FILES = 8, 60    # goals, files waiting for main
STALE_DAYS = 7                      # a goal's commit this many days old
TITLE_MAX, SHORT_MAX = 30, 80       # the App Store's title, Google Play's short description
READ_CHARS = 4000                   # a store text is read this far
DAY_S = 86400
CHANGELOGS = ("changelog", "changes", "history", "news")
ONBOARDING = ("onboarding", "tutorial", "welcome", "intro", "walkthrough")
TITLE_FILES, SHORT_FILES = ("title.txt", "name.txt"), ("short_description.txt", "subtitle.txt")
IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".gif")
SOURCE = tuple(sorted(code_map.PY | code_map.JS | {".vue", ".svelte", ".dart", ".swift", ".kt", ".java", ".cs", ".gd", ".go", ".rs", ".rb", ".php"}))     # what "the code" is
NAMED_IN = tuple(f"*{e}" for e in sorted(code_map.PY | code_map.JS | {".json", ".html", ".css"}))      # where an asset's name is looked for
MANIFESTS = tuple(f":(glob)**/{m}" for m in ("package.json", "pubspec.yaml", "Podfile", "build.gradle*", "requirements*.txt", "pyproject.toml", "Gemfile", "go.mod", "Cargo.toml"))
RETURN = r"notification|streak|daily[ _-]?reward|(^|[^[:alnum:]_])push([^[:alnum:]_(]|$)"       # a push, but not an array's push(
SHARE = r"navigator\.share|invite|referral|share[_-]?(button|sheet|link|plus|intent)|(^|[^[:alnum:]])share([^[:alnum:]]|$)"
REVENUE = r"stripe|revenuecat|purchases|billing|in_app_purchase|storekit|paddle|lemonsqueezy|paypal"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    try:
        return commit_goal.git(Path(root), *args)
    except (OSError, subprocess.SubprocessError):
        return None


def _out(root: Path, *args: str) -> str:
    got = _git(root, *args)
    return got.stdout if got is not None and got.returncode == 0 else ""


def _megabytes(n: int) -> str:
    return f"{n / (1 << 20):.1f} MB"


def _folder(path: str) -> str:
    return path.rpartition("/")[0] + "/" if "/" in path else "./"


# -- Art: the assets ------------------------------------------------------------------------------------------------------------------

def _named(root: Path, sha: str, names: list[str]) -> set[str] | None:
    """The names among `names` that a source file of `sha` holds (`git grep -F -o -h`); None when git could not say (no match is an empty set)."""
    args = ["grep", "-F", "-o", "-h", "-I", *[x for n in names for x in ("-e", n)], sha, "--", *NAMED_IN]
    got = _git(root, *args)
    if got is None or got.returncode not in (0, 1):
        return None
    return set(got.stdout.splitlines())


def _art(state_dir: Path, root: Path, ref: str) -> list[dict]:
    got = art_map.read(state_dir, root, ref=ref)
    if not got["commit"]:
        return []
    rows = sorted((a for k in got["kinds"] if k["own"] for a in k["assets"]), key=lambda a: a["id"])
    out: dict[str, list[dict]] = {k: [] for k in ("mixed_sizes", "naming", "heavy", "unused")}
    pictures: dict[str, dict[tuple[int, int], str]] = {}
    for a in rows:
        if a["kind"] == "art" and isinstance(a.get("w"), int) and isinstance(a.get("h"), int):
            pictures.setdefault(a["folder"], {}).setdefault((a["w"], a["h"]), a["id"])
    for folder, sizes in sorted(pictures.items()):
        if len(sizes) >= MIXED_SIZES:
            shown = sorted(sizes)
            first = min(sizes.values())
            out["mixed_sizes"].append({"on": first, "kind": "mixed_sizes", "words": f"{folder} holds pictures of {len(sizes)} sizes: "
                                       + ", ".join(f"{w}×{h}" for w, h in shown[:3]) + (", …" if len(shown) > 3 else "")})
    by_folder: dict[str, list[dict]] = {}
    for a in rows:
        by_folder.setdefault(a["folder"], []).append(a)
    for folder, here in sorted(by_folder.items()):
        clean = [a for a in here if a["name"] == a["name"].lower() and " " not in a["name"]]
        if len(clean) * 2 > len(here):
            out["naming"] += [{"on": a["id"], "kind": "naming", "words": f"{a['id']} has a space or a capital in its name, where the names of {folder} are lower-case with none"}
                              for a in here if a not in clean]
    for a in rows:
        if (a["kind"] == "art" and a["bytes"] >= HEAVY_ART) or (a["kind"] == "sound" and a["bytes"] >= HEAVY_SOUND):
            out["heavy"].append({"on": a["id"], "kind": "heavy", "words": f"{a['id']} is {_megabytes(a['bytes'])}: a {'picture' if a['kind'] == 'art' else 'sound'} that heavy slows the load"})
    names = sorted({a["name"] for a in rows})[:UNUSED_NAMES]
    if names and any(PurePosixPath(p).suffix in SOURCE for p in way_map._tree(Path(root), ref)):
        found = _named(root, got["commit"], names)
        if found is not None:
            out["unused"] = [{"on": a["id"], "kind": "unused", "words": f"No source file names {a['name']} ({a['id']})"} for a in rows if a["name"] in names and a["name"] not in found]
    return [s for k in out for s in out[k]]


def art(state_dir: Path, root: Path, ref: str = "dev") -> list[dict]:
    """The hints of Art's map at `ref`'s head (see the module): `[{on, kind, words}]`; [] for a map that cannot be read."""
    try:
        return _art(Path(state_dir), Path(root), ref)
    except Exception:                                # a hint that cannot be read is no hint
        return []


# -- Release: dev against main --------------------------------------------------------------------------------------------------------

def _top_has_changelog(root: Path, sha: str) -> bool:
    for row in _out(root, "ls-tree", "-z", sha).split("\0"):
        head, _sep, name = row.partition("\t")
        if head.split()[1:2] == ["blob"] and name.lower().startswith(CHANGELOGS):
            return True
    return False


def _age_days(root: Path, sha: str, now: float) -> float | None:
    stamp = _out(root, "log", "-1", "--format=%ct", sha).strip()
    return (now - int(stamp)) / DAY_S if stamp.isdigit() else None


def _release(state_dir: Path, root: Path, pages: Path | None, into: str) -> list[dict]:
    got = release_map.read(state_dir, root, pages, into)
    if got["same"] or not got["commits"]:
        return []
    main, goals, out = got["main"], got["goals"], []
    if len(goals) >= BATCH_GOALS or got["files"] >= BATCH_FILES:
        out.append({"on": "", "kind": "big_batch", "words": f"{len(goals)} goals and {got['files']} files wait for {main}: a batch that big is hard to ship and to take back"})
    now = time.time()
    for g in goals:
        days = _age_days(root, g["commit"], now)
        if days is not None and days >= STALE_DAYS:
            out.append({"on": g["idea"], "kind": "stale", "words": f"{g['title']} landed {int(days)} days ago and still waits for {main}"})
    tip, base = commit_goal.head(root, into), commit_goal.head(root, main)
    if goals and tip and not _top_has_changelog(root, tip):
        out.append({"on": "", "kind": "no_changelog", "words": f"{into} holds no changelog while {len(goals)} {'goal waits' if len(goals) == 1 else 'goals wait'} for {main}"})
    if tip and base:
        undone = [s for s in _out(root, "log", f"{base}..{tip}", "--format=%s", "--").splitlines() if s.startswith("Revert")]
        if undone:
            out.append({"on": "", "kind": "reverts", "words": f"{len(undone)} {'change' if len(undone) == 1 else 'changes'} waiting for {main} {'was a revert' if len(undone) == 1 else 'were reverts'}: "
                        + "; ".join(s[:60] for s in undone[:3])})
    order = ("big_batch", "stale", "no_changelog", "reverts")
    return sorted(out, key=lambda s: order.index(s["kind"]))


def release(state_dir: Path, root: Path, pages: Path | None = None, into: str = "dev") -> list[dict]:
    """The hints of Release's map, `into` against main (see the module): `[{on, kind, words}]`; [] for a map that cannot be read, no gate and nothing waiting."""
    try:
        return _release(Path(state_dir), Path(root), pages, into)
    except Exception:                                # a hint that cannot be read is no hint
        return []


# -- Marketing: the way in ------------------------------------------------------------------------------------------------------------

def _grep(root: Path, sha: str, pattern: str, globs: tuple[str, ...]) -> bool | None:
    """Whether a file of `sha` under `globs` holds `pattern` (`git grep -i -E -q`, an extended expression); None when git could not say."""
    got = _git(root, "grep", "-i", "-E", "-q", "-I", "-e", pattern, sha, "--", *globs)
    return None if got is None or got.returncode not in (0, 1) else got.returncode == 0


def _text(root: Path, sha: str, path: str) -> str:
    return _out(root, "--literal-pathspecs", "show", f"{sha}:{path}")[:READ_CHARS]


def _marketing(state_dir: Path, root: Path, ref: str) -> list[dict]:
    got = way_map.read(state_dir, root, ref)
    sha = got["commit"]
    if not sha:
        return []
    paths = way_map._tree(root, ref)
    parts = {h["path"] for step in got["steps"] for h in got[step]["holds"]}
    out: dict[str, list[dict]] = {k: [] for k in ("no_channel", "aso_title", "aso_short", "no_shots", "no_onboarding", "no_return", "no_share", "no_revenue")}
    if got["channels"]["none"]:
        out["no_channel"].append({"on": "", "kind": "no_channel", "words": "Nothing in the project names a way to reach people: no marketing, campaigns, ads, social or press folder"})
    stored = [p for p in paths if way_map._under(p, way_map.STORE_DIRS)]
    for kind, files, limit, store in (("aso_title", TITLE_FILES, TITLE_MAX, "the App Store cuts a title at"), ("aso_short", SHORT_FILES, SHORT_MAX, "Google Play cuts a short description at")):
        for p in stored:
            if p.rsplit("/", 1)[-1].lower() in files and len(n := _text(root, sha, p).strip()) > limit:
                out[kind].append({"on": p if p in parts else "", "kind": kind, "words": f"{p} is {len(n)} characters long, and {store} {limit}"})
    first = next((h["path"] for h in got["store"]["holds"] if h["kind"] == "store"), "")
    shots = any("screenshots" in p.lower().split("/")[:-1] or (p in stored and p.lower().endswith(IMAGES)) for p in paths)
    if first and not shots:
        out["no_shots"].append({"on": first, "kind": "no_shots", "words": "The store's files hold no screenshots: a store page shows them before its text"})
    if not any(w in p.lower() for p in paths for w in ONBOARDING):
        entry = (got["first_session"]["holds"] or [{"path": ""}])[0]["path"]
        out["no_onboarding"].append({"on": entry, "kind": "no_onboarding", "words": "No file is named onboarding, tutorial, welcome, intro or walkthrough: nothing leads a new person to the first win"})
    for kind, pattern, globs, words in (
            ("no_return", RETURN, tuple(f"*{e}" for e in SOURCE), "No source file names a notification, a push, a daily reward or a streak: nothing brings a person back"),
            ("no_share", SHARE, tuple(f"*{e}" for e in SOURCE), "No source file names sharing, an invite or a referral: a person cannot bring others"),
            ("no_revenue", REVENUE, MANIFESTS, "No manifest names a payment library (Stripe, RevenueCat, StoreKit, billing and the like): nothing says where it earns")):
        if _grep(root, sha, pattern, globs) is False:
            out[kind].append({"on": "", "kind": kind, "words": words})
    return [s for k in out for s in out[k]]


def marketing(state_dir: Path, root: Path, ref: str = "dev") -> list[dict]:
    """The hints of Marketing's map, the way in at `ref`'s head (see the module): `[{on, kind, words}]`; [] for a map that cannot be read."""
    try:
        return _marketing(Path(state_dir), Path(root), ref)
    except Exception:                                # a hint that cannot be read is no hint
        return []
