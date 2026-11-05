"""The phone predicts shapes from all project holders; hues stay host-owned."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from orkboard.realm import idea_element

NODE = shutil.which("node")
MARKS = Path(__file__).resolve().parents[1] / "orkboard/gui/static/pwa/shell-marks.js"
SEEN = "2026-11-05T12:00:00"


def goal(element, state="working", seen_at="", party="tech", **extra):
    return dict(element=element, state=state, seen_at=seen_at, party=party, **extra)


@pytest.mark.skipif(NODE is None, reason="node is not installed")
@pytest.mark.parametrize("states", [
    [],
    # Tech alone predicts ice; the complete project predicts dust.
    [goal("meadow"), goal("ice", party="design")],
    [goal("meadow", "done")],
    [goal("meadow", "done", SEEN)],
    [goal("meadow", "dropped"), goal("ice", "dropped", SEEN)],
    [goal("unknown"), goal("", "done"), goal(None), goal("meadow")],
    [goal(shape) for shape in idea_element.ELEMENTS],
    [goal(shape) for shape in idea_element.ELEMENTS if shape != "ice"],
    # Legacy goals deliberately have no hue; a different hue does not change shape usage.
    [goal("meadow"), goal("ice", hue="meadow"), goal("dust", hue="lava")],
    [goal("meadow", "working", SEEN)],
], ids=["empty", "cross-party", "done-unseen", "done-seen", "dropped", "invalid",
        "all-tied", "least-used", "legacy-no-hue", "open-seen"])
def test_phone_shape_matches_host_holders(states):
    expected = idea_element.pick([st["element"] for st in states if idea_element.holds(st)])
    # The snapshot boundary renames the persisted timestamp; never pass seen_at to the face.
    nodes = [{**{k: v for k, v in st.items() if k != "seen_at"}, "seen": st["seen_at"]} for st in states]
    script = r'''
import fs from 'node:fs';
const [path, nodes] = process.argv.slice(1);
// Only the unrelated DOM utility is stubbed; execute the production module unchanged otherwise.
const source = fs.readFileSync(path, 'utf8').replace('import { h } from "./util.js";', 'const h = () => {};');
const { nextElement } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
console.log(JSON.stringify(nextElement(JSON.parse(nodes))));
'''
    result = subprocess.run([NODE, "--input-type=module", "-e", script, str(MARKS), json.dumps(nodes)],
                            capture_output=True, text=True, check=True, timeout=30)
    assert json.loads(result.stdout) == expected
