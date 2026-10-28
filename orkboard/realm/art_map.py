"""Art's map (docs/specs/102-the-other-maps-and-picking-on-them.md §3.1, decisions §135.3–§135.4): the project's assets by kind, Art's kinds first (art and
icons, sound, music, clips), the others under them (fonts, the screens' pictures), read from dev's tree (never the working tree) as `realm/assets.py` lists
them; a picked file keeps the variants not picked under it. No model, no face.

    art_map.read(state_dir, root, since="", ref="dev")   # {commit, short, ref, since, none, kinds: [{kind, own, n, folders: [{folder, n}], assets: [...]}], stacks, removed}
    art_map.text(state_dir, root, since="", pages=None, ref="dev")   # Art's leader's map as text: the kinds by folder, the picks, the changed since its last call; None with no dev

An asset is `assets.listed`'s row (`id`, `kind`, `name`, `bytes`, `w`, `h`, `seconds`, `goal`, `task`, `at`, `change`; `stack` in a stack; a screen its `shot`) with its
`folder`; a picked file also has `others` (`{goal, pick, picked, variants: [the variants not picked]}`), the grouping the face lays under the one picked. A kind of Art's
(`own`) is read even with no asset in it (`n` 0), the others only when the project has one. `since` is the commit of the party's last call (a time works too).

The text is bounded as System's (`map_text.LIMIT`, the changes `map_text.CHANGED`): the same bytes for the same dev with no `since`, the kinds' folders keeping their
counts and a line saying how many more past it. No time, no dict order.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.realm import assets, commit_goal

ART = ("art", "sound", "music", "clip")           # Art's kinds, in the order the lanes lie (decisions §135.3)
OTHERS = ("font", "screen")                       # … and the others, under them
WORDS = {"art": ("picture", "pictures"), "sound": ("sound", "sounds"), "music": ("music track", "music tracks"), "clip": ("clip", "clips"),
         "font": ("font", "fonts"), "screen": ("screen picture", "screen pictures")}
HEADS = {"art": "Pictures", "sound": "Sounds", "music": "Music", "clip": "Clips", "font": "Fonts", "screen": "Screens' pictures"}
NOTHING = "Nothing to read yet: the project's pictures, sounds, music and clips."
TOP = "./"                                        # the folder of a file at the project's top
PICKS = 500                                       # of the text, the picks' lines at most


def _folder(path: str) -> str:
    """The folder of an asset's path (`sprites/`), `./` for a file at the project's top."""
    return path.rpartition("/")[0] + "/" if "/" in path else TOP


def read(state_dir: Path, root: Path, since: str = "", ref: str = "dev") -> dict:
    """The map (see the module): `none` is True when dev has no asset to read; with no dev at all the map is empty (`commit` "")."""
    root = Path(root)
    commit = commit_goal.head(root, ref)
    out: dict = {"commit": commit, "short": commit[:7], "ref": ref, "since": "", "none": True, "kinds": [], "stacks": [], "removed": []}
    if not commit:
        return out
    changes = assets.changed(state_dir, root, since, ref) if str(since or "").strip() else {"since": "", "added": [], "changed": [], "removed": []}
    rows = assets.listed(state_dir, root, ref, changes)
    out["stacks"] = assets.stacks(rows)
    out["since"], out["removed"] = changes["since"], changes["removed"]
    for kind in (*ART, *OTHERS):
        mine = [{**r, "folder": _folder(r["id"]) if kind != "screen" else ""} for r in rows if r["kind"] == kind]
        if not mine and kind not in ART:
            continue
        folders: dict[str, int] = {}
        for r in mine:
            if r["folder"]:
                folders[r["folder"]] = folders.get(r["folder"], 0) + 1
        out["kinds"].append({"kind": kind, "own": kind in ART, "n": len(mine), "assets": mine,
                             "folders": [{"folder": f, "n": n} for f, n in sorted(folders.items())]})
    out["none"] = not rows
    return out


# -- the text ----------------------------------------------------------------------------------------------------------------------

def _count(n: int, kind: str) -> str:
    one, many = WORDS[kind]
    return f"{n} {one if n == 1 else many}"


def _kinds(got: dict) -> list[str]:
    lines: list[str] = []
    for k in got["kinds"]:
        if not k["n"]:
            continue
        lines.append(f"{HEADS[k['kind']]} ({k['n']}):")
        if k["kind"] == "screen":
            continue
        lines += [f"- {f['folder']}: {_count(f['n'], k['kind'])}" for f in k["folders"]]
    return lines


def _picks(got: dict) -> list[str]:
    rows = sorted((a for k in got["kinds"] for a in k["assets"] if a.get("others")), key=lambda a: a["id"])
    out = []
    for a in rows:
        n = len(a["others"]["variants"])
        out.append(f"- {a['id']}: picked from {n + 1} variants, {n} not picked")
    return out


def _changed(got: dict, pages: Path | None) -> str:
    from orkboard.realm import map_text           # lazy: map_text.of reads this module's text
    head = "Changed since your last call"
    if not got["since"]:
        return f"{head}: not known (that commit is not in {got['ref']})."
    cache: dict[str, str] = {}
    word = {"added": "new", "changed": "changed"}
    marked = sorted((a for k in got["kinds"] for a in k["assets"] if a["change"]), key=lambda a: (a["change"] != "added", a["id"]))
    rows = [f"- {word[a['change']]} {WORDS[a['kind']][0]} {a['id'] if a['kind'] != 'screen' else a['name']} ({map_text._goal(a['goal'], pages, cache)})"
            for a in marked]
    rows += [f"- gone {WORDS[r['kind']][0]} {r['id']} ({map_text._goal(r['goal'], pages, cache)})" for r in sorted(got["removed"], key=lambda r: r["id"])]
    if not rows:
        return f"{head}: nothing."
    return "\n".join([f"{head}:"] + map_text._fit(rows, map_text.CHANGED - len(head) - 2, "- and {n} more changes"))


def text(state_dir: Path, root: Path, since: str = "", pages: Path | None = None, ref: str = "dev") -> str | None:
    """Art's map as text at dev's head (about `map_text.LIMIT` characters at most), then, when `since` is set, what changed since that commit with its goal.
    `pages`: where the Board's pages are, for a goal's title (else the slug alone). None when the project has no `dev` to read."""
    from orkboard.realm import map_text
    got = read(state_dir, root, since, ref)
    if not got["commit"]:
        return None
    head = f"The map of Art's assets at {ref} {got['short']}"
    if got["none"]:
        body = [NOTHING]
    else:
        body = map_text._fit(_kinds(got), map_text.LIMIT - len(head) - 2, "- and {n} more lines: read further what you need")
        if picks := _picks(got):
            body += ["", "Picked (the variants not picked lie under the one picked):"] + map_text._fit(picks, PICKS, "- and {n} more picks")
    text_ = "\n".join([head, ""] + body)
    since = str(since or "").strip()
    return text_ + "\n\n" + _changed(got, pages) if since else text_
