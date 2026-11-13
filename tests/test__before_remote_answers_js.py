"""The phone's answer file (pwa/shell-answer-file.js, spec 137 C) keeps to realm/remote_answers.py: the same kinds with the same answer keys, the
same card id, a file the host reads back as the answer it was made from. Run by node (no page needed); skipped without it."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import remote_answers as ra

JS = Path(ra.__file__).resolve().parents[1] / "gui" / "static" / "pwa" / "shell-answer-file.js"
node = shutil.which("node")
pytestmark = pytest.mark.skipif(node is None, reason="node is not installed")

SCRIPT = """
const m = await import(process.argv[1]);
const rows = JSON.parse(process.argv[2]);
const out = {kinds: m.KINDS, ids: [m.newId(1730728000000, () => 0.5), m.newId(1730728001000, () => 0.5)], files: rows.map(([row, args]) => m.answerFile(row, args, {device: "phone1", id: "01JC00000000000000A1", at: "2026-11-04T14:00:00.000Z"})),
  keys: rows.map(([row]) => m.cardKey(row))};
console.log(JSON.stringify(out));
"""


def run(rows: list) -> dict:
    done = subprocess.run([node, "--input-type=module", "-e", SCRIPT, JS.as_uri(), json.dumps(rows)], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_the_kinds_and_their_answer_keys_are_the_hosts():
    got = run([])
    assert {k: tuple(v) for k, v in got["kinds"].items()} == {k: v[2] for k, v in ra.KINDS.items()}


def test_an_id_sorts_by_time_and_is_a_valid_inbox_id():
    a, b = run([])["ids"]
    assert a < b and len(a) == 26 and __import__("re").fullmatch(r"[A-Za-z0-9_-]{8,40}", a)


def test_the_file_is_read_back_by_the_host_as_the_answer_it_was_made_from():
    rows = [[{"kind": "talk", "idea": "goal-1", "goal": "tech"}, {"idea": "x", "answers": [{"id": "q1", "pick": 1}], "decide": True}],
            [{"kind": "collide", "idea": "i", "collide": {"id": "a|b"}}, {"answer": "leave"}],
            [{"kind": "pick", "idea": "i"}, {"x": 1}]]
    got = run(rows)
    talk, stop, none = got["files"]
    assert talk["path"] == "inbox/phone1/01JC00000000000000A1.answer.json" and none is None
    assert talk["body"]["answer"] == {"answers": [{"id": "q1", "pick": 1}], "decide": True}      # `idea` is not the answer's: left out
    entry = ra.Answer("01JC00000000000000A1", "phone1", talk["path"])
    read, err = ra.clean(json.dumps(talk["body"]), entry)
    assert err == "" and (read["card"], read["kind"]) == ("goal-1", "talk")
    assert got["keys"][:2] == [ra.card_key(rows[0][0]), ra.card_key(rows[1][0])]
    assert stop["body"]["card"] == "a|b" and ra.clean(json.dumps(stop["body"]), entry)[1] == ""
