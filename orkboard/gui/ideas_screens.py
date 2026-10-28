"""Design's map and Product's pains on it (docs/specs/102-the-other-maps-and-picking-on-them.md §1, realm/screen_map.py), as `gui/ideas.py`'s `Ideas` has them:
`ideas.screens` (the screens of the app at dev's head, along their flow, each with its newest picture, and the project's segments with their pains' places) and
`ideas.pain_pin` (a pain pinned to a screen or a step, or taken off it). The host returns keys and data, never interface words but a refusal's.

    ideas.screens {}                           # {head, source, entry, screens: [{id, name, path, file, picture?}], links: [{from, to}], steps: [[id…]], loose: [id…], more,
                                               #  segments: [{segment, pains: [{text, on}]}]}; a picture is {kind: "shot", goal, task, id, file, w, h, at, url}
                                               #  (the signed address of the task's picture) or {kind: "lens", id, name, at} (`ideas.lens_screen {id}` gives it)
    ideas.pain_pin {segment, pain, on}         # `on` a screen's id or a step's ("step:2"), "" to take the pain off its place; {"ok": true, "segments": […]}

A step's id is "step:<n>" from 1. A project with no screen to read (a library, a backend) answers `screens: []`: the face says *Nothing to read yet*.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from orkboard.gui import media
from orkboard.gui.ideas_args import IdeasError, _str, _text
from orkboard.realm import idea_lens, screen_map


class ScreensMixin:
    def _screens_read(self) -> dict:
        got = screen_map.read(self.state_dir, Path(self.host.repo_root))
        for s in got["screens"]:
            pic = s.get("picture")
            if pic and pic.get("kind") == "shot":
                s["picture"] = {**pic, "url": media.url(pic["goal"], pic["id"], pic["file"])}
        return got

    def screens(self, args: dict) -> dict:
        return {**self._screens_read(), "segments": idea_lens.segments_placed(self.state_dir)}

    def pain_pin(self, args: dict) -> dict:
        segment, pain, on = _text(args, "segment", 120), _text(args, "pain", 300), _str(args, "on", 80).strip()
        mine = next((s for s in idea_lens.segments_placed(self.state_dir) if s["segment"].lower() == segment.lower()), None)
        kept = next((p["text"] for p in (mine or {}).get("pains", []) if p["text"].lower() == pain.lower()), None)
        if mine is None or kept is None:
            raise IdeasError("That pain is gone")
        if on:
            got = screen_map.read(self.state_dir, Path(self.host.repo_root))
            if on not in {s["id"] for s in got["screens"]} | {screen_map.step_id(n) for n in range(1, len(got["steps"]) + 1)}:
                raise IdeasError("That screen is gone")
        idea_lens.keep_segment(self.state_dir, mine["segment"], kept, on)
        self.changed("")
        return {"ok": True, "segments": idea_lens.segments_placed(self.state_dir)}


def screens_commands(ideas_: Any) -> dict:
    """Design's map and the pains' places by name (`gui/ideas.py` adds them to its table: `**screens_commands(self)`)."""
    return {"ideas.screens": ideas_.screens, "ideas.pain_pin": ideas_.pain_pin}
