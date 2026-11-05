"""Snapshot-to-face selection and unchanged-state host allocation, without a browser."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import idea_element, ideas

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")
PLUSCARD = Path(__file__).resolve().parents[1] / "orkboard/gui/static/js/hand/pluscard.js"


@pytest.mark.parametrize("chosen", ["", "dust"])
def test_snapshot_preview_selection_writes_nothing_and_matches_submission(fake_repo, chosen):
    host = Orkboard(fake_repo)
    try:
        root, state = host.ideas.root(), host.ideas.state_dir
        party = ideas.add_track(root, "Tech")
        for shape in idea_element.ELEMENTS:
            slug = ideas.add_idea(root, f"Holder {shape}", party, state)
            ideas.save_state(state, slug, state="working", element=shape, hue=shape)
        snapshot = host.command("ideas.map", {})
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in state.rglob("state.json")}
        rev = host.snapshot()["ideas_rev"]
        # Run the production selector with its imported signals/data boundary supplied.
        # Browser coverage exercises the component render paths and draft lifecycle.
        script = r'''
import fs from 'node:fs';
const [path, snapshot, party, chosen] = process.argv.slice(1);
const source = fs.readFileSync(path, 'utf8');
const selector = source.slice(source.indexOf('export function runesOf('), source.indexOf('/** The + card.')).replace('export ', '');
const mapData = {value: JSON.parse(snapshot)}, fieldRune = {value: ''};
const partiesOf = data => data.goals;
const ELEMENTS = ['meadow', 'ice', 'dust', 'void', 'lava'];
const select = new Function('mapData', 'fieldRune', 'partiesOf', 'ELEMENTS', selector + '; return runesOf;')(mapData, fieldRune, partiesOf, ELEMENTS);
const initial = select({party});
fieldRune.value = chosen;
const changed = select({party});
console.log(JSON.stringify({initial, changed, reopened: select({party})}));
'''
        result = subprocess.run([NODE, "--input-type=module", "-e", script, str(PLUSCARD), json.dumps(snapshot), party, chosen],
                                capture_output=True, text=True, check=True, timeout=30)
        previews = json.loads(result.stdout)
        assert previews["initial"]["shown"] == "meadow"
        assert previews["initial"]["hue"] == "ice"
        preview = previews["changed"]
        shape = chosen or "meadow"
        assert preview["shown"] == shape
        assert preview["hue"] == ("meadow" if chosen else "ice")
        assert preview == previews["reopened"]
        assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in state.rglob("state.json")} == before
        assert host.snapshot()["ideas_rev"] == rev
        allocated = host.command("ideas.add", {"text": "Preview probe", "party": party, "hold": True,
                                               **({"element": chosen} if chosen else {})})
        assert (allocated["element"], allocated["hue"]) == (preview["shown"], preview["hue"])
    finally:
        host.close()
