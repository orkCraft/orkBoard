"""Art's assets, Release's dev against main and Marketing's way in, as `gui/ideas.py`'s `Ideas` has them (docs/specs/102-the-other-maps-and-picking-on-them.md §3,
decisions §135.3–§135.4, §137.3, §151.7). Read from dev's tree and git (realm/art_map.py, realm/release_map.py, realm/way_map.py), no model. Keys and data, never words.

    ideas.art_map {since?}       # {commit, short, ref, since, none, kinds: [{kind, own, n, folders, assets}], stacks, removed, goals}: Art's kinds first, a picked file's variants under it
    ideas.release_map {}         # {into, main, same, commits, files, goals: [{idea, title, element, commit, ticked}], since: {version, out} | null}: the goals in dev and not in main
    ideas.way_map {}             # {commit, short, ref, steps, channels, store, install, first_session}: each step {holds: [{path, kind}], none, more}

`art_map`'s assets are signed as `ideas.assets`' are (a `url` to look at, the variants' too); `goals` names the goals that made them (`title`, `element`). `release_map`'s
**To main** is `ideas.gate_merge`, as today: this answers what is ticked, not the merge.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui.ideas_args import _str
from orkboard.realm import art_map, release_map, way_map


class MapsMixin:
    """Needs `host`, `state_dir`, `root()`, `_into()`, `_ref()`, `_signed()` and `_goals()` (gui/ideas.py, gui/ideas_assets.py, gui/ideas_review.py)."""

    def art_map(self, args: dict) -> dict:
        root, ref = Path(self.host.repo_root), self._ref()
        since = _str(args, "since", 100).strip() if args.get("since") is not None else ""
        got = art_map.read(self.state_dir, root, since, ref)
        slugs: set[str] = set()
        for lane in got["kinds"]:
            lane["assets"] = [self._signed(dict(a), got["commit"]) for a in lane["assets"]]
            slugs |= {a.get("goal") or "" for a in lane["assets"]}
        slugs |= {r.get("goal") or "" for r in got["removed"]}
        return {**got, "goals": self._goals(slugs)}

    def release_map(self, args: dict) -> dict:
        return release_map.read(self.state_dir, Path(self.host.repo_root), self.root(False), self._into())

    def way_map(self, args: dict) -> dict:
        return way_map.read(self.state_dir, Path(self.host.repo_root), self._ref())


def maps_commands(m: Any) -> dict:
    """The maps' reads by name (`gui/ideas.py` adds them to its table: `**maps_commands(self)`)."""
    return {"ideas.art_map": m.art_map, "ideas.release_map": m.release_map, "ideas.way_map": m.way_map}
