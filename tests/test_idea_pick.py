"""Pick one (docs/specs/51-pick-one.md §2, §8 A): what a task leaves in its worktree is read and checked (a type sniffed from the
bytes, the limits, the plain-words reasons), moved to the goal's state folder with its `pick.json`, and put to the person;
`ideas.pick` writes the one picked at its target and commits it, or asks for new ones; the Needs you row, the Map's task, the
events, today's rows and the push."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import event_log, idea_pick, lexicon, media_sniff
from tests import pick_files as pf
from tests.pick_files import ask, leave, task  # noqa: F401


# -- sniffing: the type is the bytes' --------------------------------------------------------------------------------

@pytest.mark.parametrize("name, data, mime", [
    ("a.png", pf.png(), "image/png"), ("a.jpg", pf.jpeg(), "image/jpeg"), ("a.gif", pf.gif(), "image/gif"),
    ("a.webp", pf.webp(), "image/webp"), ("a.svg", pf.svg(), "image/svg+xml"), ("a.wav", pf.wav(), "audio/wav"),
    ("a.mp3", pf.mp3(), "audio/mpeg"), ("a.ogg", pf.ogg(), "audio/ogg"), ("a.webm", pf.webm(), "video/webm"),
    ("a.mp4", pf.mp4(b"vide"), "video/mp4"), ("a.m4a", pf.mp4(b"soun"), "audio/mp4"),
    ("a.mp4", pf.mp4(moov=False), "video/mp4"),                                     # an `ftyp` box alone: a clip
    ("a.m4a", pf.mp4(moov=False, brand=b"M4A "), "audio/mp4"),                      # … unless its brand is a sound's
    ("a.txt", pf.text(), "text/plain"), ("a.txt", "Ork — «zug»".encode(), "text/plain"),
])
def test_a_files_type_is_sniffed_from_its_bytes(tmp_path, name, data, mime):
    assert media_sniff.sniff(pf.write(tmp_path, name, data)) == mime


@pytest.mark.parametrize("name, data, mime, expect", [
    ("a.png", pf.png(3, 2), "image/png", (3, 2, None)), ("a.jpg", pf.jpeg(40, 30), "image/jpeg", (40, 30, None)),
    ("a.gif", pf.gif(7, 5), "image/gif", (7, 5, None)), ("a.webp", pf.webp(16, 12), "image/webp", (16, 12, None)),
    ("b.webp", pf.webp(20, 10, "VP8 "), "image/webp", (20, 10, None)), ("c.webp", pf.webp(33, 9, "VP8X"), "image/webp", (33, 9, None)),
    ("a.svg", pf.svg(24, 12), "image/svg+xml", (24, 12, None)), ("b.svg", pf.svg(None, None), "image/svg+xml", (48, 36, None)),
    ("a.wav", pf.wav(0.5), "audio/wav", (None, None, 0.5)), ("a.mp3", pf.mp3(1000), "audio/mpeg", (None, None, 26.1)),
    ("b.mp3", pf.mp3(xing=False), "audio/mpeg", (None, None, None)),                            # no Xing header: null, not a guess
    ("a.ogg", pf.ogg(), "audio/ogg", (None, None, None)), ("a.webm", pf.webm(), "video/webm", (None, None, None)),
    ("a.mp4", pf.mp4(b"vide", 5, 320, 240), "video/mp4", (320, 240, 5.0)), ("a.m4a", pf.mp4(b"soun", 7), "audio/mp4", (None, None, 7.0)),
    ("b.mp4", pf.mp4(moov=False), "video/mp4", (None, None, None)), ("a.txt", pf.text(), "text/plain", (None, None, None)),
])
def test_the_size_and_the_length_are_read_from_the_header_else_null(tmp_path, name, data, mime, expect):
    got = media_sniff.measure(pf.write(tmp_path, name, data), mime)
    assert (got["w"], got["h"], got["seconds"]) == expect


# -- the plan's ask --------------------------------------------------------------------------------------------------



# -- reading what the task left ----------------------------------------------------------------------------------------

def test_a_valid_pick_is_read_with_its_keys_names_types_sizes_and_what_the_headers_say(tmp_path):
    leave(tmp_path, {"anchor.png": pf.png(3, 2), "wolf.svg": pf.svg(24, 12), "mark.jpg": pf.jpeg(40, 30)},
          names={"anchor.png": "anchor", "wolf.svg": "  wolf\n head  ", "mark.jpg": "x" * 40})
    got, why = idea_pick.read(tmp_path, task(3))
    assert why == "" and [v["key"] for v in got] == ["A", "B", "C"]
    assert [v["file"] for v in got] == ["a.png", "b.svg", "c.jpg"]                              # stored under the key, never the task's name
    assert [v["mime"] for v in got] == ["image/png", "image/svg+xml", "image/jpeg"]
    assert [(v["w"], v["h"]) for v in got] == [(3, 2), (24, 12), (40, 30)] and all(v["seconds"] is None for v in got)
    assert [v["name"] for v in got] == ["anchor", "wolf head", "x" * idea_pick.NAME_MAX]         # a name is one line, 24 characters
    assert got[0]["bytes"] == len(pf.png(3, 2)) and got[1]["why"] == "why wolf.svg"
    assert got[0]["src"] == tmp_path / ".orkcraft-pick" / "anchor.png"


@pytest.mark.parametrize("what, expect", [
    ("no manifest", "The task left no variants: its list (.orkcraft-pick.json) is missing"),
    ("not json", "The task's list of variants is not valid JSON"),
    ("no list", "The task's list of variants is not as asked"),
    ("rows are not objects", "The task's list of variants is not as asked"),
    ("too many bytes", "The task's list of variants is too long"),
])
def test_a_manifest_missing_broken_or_odd_fails_in_plain_words(tmp_path, what, expect):
    pf.write(tmp_path / ".orkcraft-pick", "a.png", pf.png())
    manifest = tmp_path / ".orkcraft-pick.json"
    body = {"not json": "{no", "no list": '{"variants": 3}', "rows are not objects": '{"variants": [1, 2, 3]}',
            "too many bytes": json.dumps({"variants": [], "x": "y" * 70000})}
    if what != "no manifest":
        manifest.write_text(body[what], encoding="utf-8")
    got, why = idea_pick.read(tmp_path, task(3))
    assert got == [] and why.startswith(expect), why


def test_a_file_outside_the_folder_a_missing_one_or_a_link_is_refused(tmp_path):
    secret = pf.write(tmp_path, "secret.png", pf.png())
    tree = tmp_path / "tree"
    leave(tree, {"a.png": pf.png()}, rows=[{"name": "a", "file": "a.png"}, {"name": "b", "file": "../../secret.png"}])
    got, why = idea_pick.read(tree, task(2))
    assert got == [] and why.startswith("B is not a file in the variants' folder")
    for bad in ("/etc/passwd", str(secret), "sub/a.png", ".", "", None, 3, "missing.png", "a\x00.png"):
        leave(tree, {"a.png": pf.png()}, rows=[{"name": "a", "file": "a.png"}, {"name": "b", "file": bad}])
        got, why = idea_pick.read(tree, task(2))
        assert got == [] and why.startswith("B is not a file in the variants' folder"), bad
    (tree / ".orkcraft-pick" / "link.png").symlink_to(secret)                                      # a link out of the folder
    leave(tree, {"a.png": pf.png()}, rows=[{"name": "a", "file": "a.png"}, {"name": "b", "file": "link.png"}])
    assert idea_pick.read(tree, task(2))[1].startswith("B is not a file in the variants' folder")
    (tree / ".orkcraft-pick" / "b.png").write_bytes(pf.png())
    leave(tree, {"a.png": pf.png()}, rows=[{"name": "a", "file": "a.png"}, {"name": "b", "file": "a.png"}])
    assert idea_pick.read(tree, task(2)) == ([], "B is the same file as an earlier variant")
    (tree / ".orkcraft-pick").rename(tmp_path / "moved")                                          # no folder at all
    assert idea_pick.read(tree, task(2))[1].startswith("A is not a file in the variants' folder")


# -- the move to the state folder ----------------------------------------------------------------------------------------

def test_the_files_move_to_the_goals_state_folder_with_their_pick_json_and_the_worktree_is_left_clean(tmp_path):
    tree, state = tmp_path / "tree", tmp_path / "state"
    leave(tree, {"anchor.png": pf.png(3, 2), "wolf.svg": pf.svg()}, names={"anchor.png": "anchor", "wolf.svg": "wolf"})
    t = task(2)
    variants, why = idea_pick.read(tree, t)
    got = idea_pick.store(state, "dark-mode", t, 1, variants, by="grunt", now="2026-10-21T10:00:00")
    folder = state / "ideas" / "dark-mode" / "picks" / "k1-r1"
    assert sorted(p.name for p in folder.iterdir()) == ["a.png", "b.svg", "pick.json"]
    assert (folder / "a.png").read_bytes() == pf.png(3, 2) and (folder / "b.svg").read_bytes() == pf.svg()
    kept = json.loads((folder / "pick.json").read_text())
    assert kept == got == {"id": "k1-r1", "task": "k1", "round": 1, "by": "grunt", "kind": "image", "ask": "A logo for the app",
                           "target": "assets/logo.png", "at": "2026-10-21T10:00:00", "variants": [
                               {"key": "A", "name": "anchor", "file": "a.png", "mime": "image/png", "bytes": len(pf.png(3, 2)), "w": 3, "h": 2,
                                "seconds": None, "why": "why anchor.png"},
                               {"key": "B", "name": "wolf", "file": "b.svg", "mime": "image/svg+xml", "bytes": len(pf.svg()), "w": 24, "h": 12,
                                "seconds": None, "why": "why wolf.svg"}]}
    assert not (tree / ".orkcraft-pick").exists() or not any((tree / ".orkcraft-pick").iterdir())      # moved, not copied
    idea_pick.discard(tree)
    assert not (tree / ".orkcraft-pick").exists() and not (tree / ".orkcraft-pick.json").exists()      # … and the folder and the manifest go
    assert idea_pick.load(state, "dark-mode", "k1-r1") == kept and idea_pick.current(state, "dark-mode", t) == kept
    assert idea_pick.load(state, "dark-mode", "k1-r2") is None and idea_pick.current(state, "dark-mode", {**t, "round": 2}) is None


def test_an_answer_is_kept_in_the_pick_and_the_old_round_stays_as_history(tmp_path):
    tree, state = tmp_path / "tree", tmp_path / "state"
    t = task(2)
    for rnd in (1, 2):
        leave(tree, {"a.png": pf.png(rnd, 1), "b.png": pf.png(rnd, 2)})
        variants, _ = idea_pick.read(tree, t)
        pick = idea_pick.store(state, "g", t, rnd, variants, now=f"2026-10-21T1{rnd}:00:00")
        idea_pick.discard(tree)
        if rnd == 1:
            assert not idea_pick.answered(pick)
            done = idea_pick.answer(state, "g", pick, None, "make them rounder", now="2026-10-21T11:30:00")
            assert done["picked"] is None and done["note"] == "make them rounder" and done["at"] == "2026-10-21T11:30:00"
            assert done["asked_at"] == "2026-10-21T11:00:00" and idea_pick.answered(idea_pick.load(state, "g", "k1-r1"))
    assert [p["round"] for p in idea_pick.history(state, "g", "k1")] == [1, 2]
    assert idea_pick.answered(idea_pick.history(state, "g", "k1")[0]) and not idea_pick.answered(idea_pick.history(state, "g", "k1")[1])
    assert (state / "ideas" / "g" / "picks" / "k1-r1" / "a.png").is_file()                              # the first round's files stay
    assert idea_pick.history(state, "g", "k9") == []


# -- the runner: a task that makes variants ----------------------------------------------------------------------------------

import os  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from orkboard.core.idea_review import RunnerError  # noqa: E402
from orkboard.core.idea_runner import IdeaRunner  # noqa: E402

PICK_STUB = r'''#!{python}
import json, os, subprocess, sys
sys.path.insert(0, os.environ["STUB_TESTS"])
from tests import pick_files as pf
argv = sys.argv[1:]
resume = "--resume" in argv
branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
tid = branch.rsplit("/", 1)[-1]
modes = dict(p.split("=", 1) for p in os.environ.get("STUB_MODE", "").split(",") if "=" in p)
mode = modes.get(tid, modes.get("*", "edit")).split(":")

def git(*a):
    subprocess.run(["git", *a], check=True, capture_output=True)

def commit(path, text, msg):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w").write(text)
    git("add", "-A")
    git("-c", "user.name=Stub", "-c", "user.email=stub@x", "commit", "-m", msg)

def leave(files, rows=None):
    os.makedirs(".orkcraft-pick", exist_ok=True)
    for name, data in files.items():
        open(os.path.join(".orkcraft-pick", name), "wb").write(data)
    rows = rows if rows is not None else [{"name": n.split(".")[0], "file": n, "why": "because " + n} for n in files]
    open(".orkcraft-pick.json", "w").write(json.dumps({"variants": rows}))

round_ = 2 if resume else 1
if mode[0] == "pick":
    n = int(mode[1])
    leave({f"v{i}.png": pf.png(round_ * 10 + i, 2) for i in range(1, n + 1)})
    open("stray.txt", "w").write("not wanted\n")                        # "change nothing else": this is not kept
elif mode[0] == "pickcommit":                                          # it commits its own file besides
    leave({f"v{i}.png": pf.png(i, 2) for i in (1, 2)})
    commit("tool.py", "print(1)\n", "a script that made them")
elif mode[0] == "picknothing":
    pass
elif mode[0] == "pickwav":
    leave({"v1.png": pf.png(), "v2.png": pf.wav()})
elif mode[0] == "pickonly":
    leave({"v1.png": pf.png()})
elif mode[0] == "edit":
    commit(f"{tid}.txt", f"done by {tid}\n", f"{tid}: add {tid}.txt")
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps({"tid": tid, "resume": resume, "argv": argv}) + "\n")
print(json.dumps({"result": "done", "session_id": f"s-{tid}", "total_cost_usd": 0.01, "usage": {"input_tokens": 10, "output_tokens": 5}}))
'''


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@x")
    git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text(".orkcraft/\n__pycache__/\n.pytest_cache/\nignored/\n")
    (repo / "tests").mkdir()
    for name in ("test_architecture.py", "test_cli.py", "test_updates.py"):
        (repo / "tests" / name).write_text("def test_ok():\n    assert True\n")
    (repo / "conftest.py").write_text("")
    # The project's own gate, written down: a task that changed only documents runs no derived gate (spec 107 §1.2), and its stub writes a `.txt`.
    (repo / "orkcraft.toml").write_text('[gate]\nalways = ["tests/test_architecture.py", "tests/test_cli.py", "tests/test_updates.py"]\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "start")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "claude"
    stub.write_text(PICK_STUB.replace("{python}", sys.executable))
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("STUB_LOG", str(tmp_path / "stub.jsonl"))
    monkeypatch.setenv("STUB_TESTS", str(Path(__file__).resolve().parents[1]))
    page = repo / "llm-wiki" / "general" / "pages" / "ideas" / "demo.md"
    page.parent.mkdir(parents=True)
    page.write_text("---\nowner: board\n---\n# Demo\n\n## Gist\nA demo goal.\n")
    made = SimpleNamespace(repo=repo, state=repo / ".orkcraft", log=tmp_path / "stub.jsonl", runners=[])
    yield made
    for runner in made.runners:                 # a task still running when the test ends must not write into the next test's log
        runner.stop_all()
        end = time.time() + 30
        while runner.busy() and time.time() < end:
            time.sleep(0.05)


def plan_of(rig, tasks: list[dict], slug: str = "demo") -> None:
    folder = rig.state / "ideas" / slug
    folder.mkdir(parents=True, exist_ok=True)
    full = [{"id": t["id"], "title": t.get("title", t["id"]), "brief": t.get("brief", "do " + t["id"]), "tier": "laborer",
             "kind": t.get("kind", "art"), "after": t.get("after", []), "state": "waiting", "branch": "", "commit": "", "session": "",
             "cost": None, "tokens": None, "started": "", "finished": "", "error": "", "note": "",
             **({"pick": t["pick"]} if "pick" in t else {})} for t in tasks]
    (folder / "plan.json").write_text(json.dumps({"idea": slug, "made_at": "x", "passed_at": "y", "todos": [], "tasks": full}))
    (folder / "state.json").write_text(json.dumps({"state": "plan"}))


def runner_of(rig, goal_branches=True, **ideas) -> IdeaRunner:
    bus = SimpleNamespace(publish=lambda topic, **data: None)
    settings = SimpleNamespace(ideas={"max_parallel": 1, "merge_into": "main", "push": False, "review": False, **ideas})
    runner = IdeaRunner(rig.repo, rig.state, settings, bus, limits=lambda: [], goal_branches=goal_branches)
    rig.runners.append(runner)
    return runner


def tasks_of(rig, slug: str = "demo") -> dict:
    return {t["id"]: t for t in json.loads((rig.state / "ideas" / slug / "plan.json").read_text())["tasks"]}


def wait_for(runner: IdeaRunner, rig, tid: str, states: tuple[str, ...], timeout: float = 90) -> dict:
    end = time.time() + timeout
    while time.time() < end:
        runner.tick()
        task = tasks_of(rig)[tid]
        if task["state"] in states and not runner.busy():
            return task
        time.sleep(0.1)
    raise AssertionError(f"{tid} did not reach {states}: {tasks_of(rig)[tid]}")


def events_of(rig, name: str) -> list[dict]:
    return [r for r in event_log.read(rig.repo) if r["event"] == name]


def calls(rig) -> list[dict]:
    return [json.loads(ln) for ln in rig.log.read_text().splitlines()] if rig.log.exists() else []


PICK = {"n": 3, "kind": "image", "ask": "A logo for the app", "target": "assets/logo.png"}


def start_pick(rig, monkeypatch, mode: str = "pick:3", goal_branches=True, **ideas) -> IdeaRunner:
    monkeypatch.setenv("STUB_MODE", f"k1={mode}")
    plan_of(rig, [{"id": "k1", "title": "Draw the logo", "pick": PICK}, {"id": "k2", "title": "Use the logo", "after": ["k1"], "kind": "code"}])
    runner = runner_of(rig, goal_branches=goal_branches, **ideas)
    runner.start("demo")
    return runner


def test_a_task_that_makes_variants_waits_picking_with_its_files_in_the_state_folder_and_nothing_committed(rig, monkeypatch):
    runner = start_pick(rig, monkeypatch)
    task = wait_for(runner, rig, "k1", ("picking",))
    assert task["commit"] == "" and task["error"] == "" and task["finished"] and task["round"] == 1
    folder = rig.state / "ideas" / "demo" / "picks" / "k1-r1"
    pick = json.loads((folder / "pick.json").read_text())
    assert (pick["id"], pick["task"], pick["round"], pick["kind"], pick["ask"], pick["target"]) == (
        "k1-r1", "k1", 1, "image", "A logo for the app", "assets/logo.png")
    assert [(v["key"], v["name"], v["file"], v["mime"], v["w"], v["h"]) for v in pick["variants"]] == [
        ("A", "v1", "a.png", "image/png", 11, 2), ("B", "v2", "b.png", "image/png", 12, 2), ("C", "v3", "c.png", "image/png", 13, 2)]
    assert sorted(p.name for p in folder.iterdir()) == ["a.png", "b.png", "c.png", "pick.json"]
    assert pick["by"] == "grunt"
    # the worktree is as it was cut: no variants, no manifest, nothing the session did besides, and the branch has no commit
    path = rig.state / "worktrees"
    tree = next(path.iterdir())
    assert sorted(p.name for p in tree.iterdir() if not p.name.startswith(".git")) == ["conftest.py", "orkcraft.toml", "tests"]
    assert not (tree / "stray.txt").exists() and not (tree / ".orkcraft-pick").exists() and not (tree / ".orkcraft-pick.json").exists()
    assert git(tree, "rev-parse", "HEAD") == git(rig.repo, "rev-parse", "main") and git(rig.repo, "rev-parse", "main") == task["base"]
    assert tasks_of(rig)["k2"]["state"] == "waiting"                       # what waits for it waits
    state = json.loads((rig.state / "ideas" / "demo" / "state.json").read_text())
    assert state["state"] == "working"
    assert [(e["task"], e["n"], e["media"], e["round"]) for e in events_of(rig, "pick_asked")] == [("k1", 3, "image", 1)]
    assert [(e["task"], e["state"], e["was"]) for e in events_of(rig, "task_state") if e["state"] == "picking"] == [("k1", "picking", "running")]
    assert len(calls(rig)) == 1 and "pick_answered" not in {r["event"] for r in event_log.read(rig.repo)}
    assert (tasks_of(rig)["k1"]["pick"]) == PICK                            # the plan's ask stays on the task


@pytest.mark.parametrize("mode, reason", [
    ("pick:2", "The task left 2 pictures; its plan asked for 3"),
    ("picknothing", "The task left no variants: its list (.orkcraft-pick.json) is missing"),
    ("pickwav", "The task left 2 pictures; its plan asked for 3"),
    ("edit", "The task left no variants"),
])
def test_a_manifest_missing_or_a_wrong_count_fails_the_task_in_plain_words_and_the_files_go(rig, monkeypatch, mode, reason):
    runner = start_pick(rig, monkeypatch, mode)
    task = wait_for(runner, rig, "k1", ("failed",))
    assert task["error"].startswith(reason) and task["commit"] == ""
    assert not (rig.state / "ideas" / "demo" / "picks").exists()
    tree = next((rig.state / "worktrees").iterdir())
    assert not (tree / ".orkcraft-pick").exists() and not (tree / ".orkcraft-pick.json").exists()
    state = json.loads((rig.state / "ideas" / "demo" / "state.json").read_text())
    assert state["state"] == "failed" and "The task left" in state["error"]


def test_a_key_commits_the_picked_file_at_its_target_with_its_message_and_the_task_lands(rig, monkeypatch):
    runner = start_pick(rig, monkeypatch)
    wait_for(runner, rig, "k1", ("picking",))
    runner.pick("demo", "k1", "b", "  a bit bluer\n", device="phone", via="drawer")
    task = wait_for(runner, rig, "k1", ("merged",))
    assert git(rig.repo, "log", "-1", "--format=%s", task["commit"]) == "Draw the logo: B · v2"
    assert git(rig.repo, "show", "--stat", "--format=", task["commit"]).split()[0] == "assets/logo.png"      # that file alone
    assert (rig.repo / "assets" / "logo.png").read_bytes() == pf.png(12, 2)                   # B's file, nowhere else
    assert not (rig.repo / "stray.txt").exists() and task["picked"] == {"key": "B", "name": "v2", "note": "a bit bluer"}
    pick = json.loads((rig.state / "ideas" / "demo" / "picks" / "k1-r1" / "pick.json").read_text())
    assert (pick["picked"], pick["note"]) == ("B", "a bit bluer") and pick["asked_at"] and pick["at"] >= pick["asked_at"]
    [answer] = events_of(rig, "pick_answered")
    assert (answer["task"], answer["key"], answer["note_chars"], answer["via"], answer["device"], answer["round"]) == (
        "k1", "B", len("a bit bluer"), "drawer", "phone", 1)
    assert isinstance(answer["seconds"], float)
    wait_for(runner, rig, "k2", ("merged",))
    assert [c["tid"] for c in calls(rig)] == ["k1", "k2"]                                      # no new turn for k1: the gate went on from the commit
    assert 'The person picked B · v2: "a bit bluer"' in calls(rig)[1]["argv"][1]               # the note, told to the task that waits for it
    assert json.loads((rig.state / "ideas" / "demo" / "state.json").read_text())["state"] == "done"


def test_none_of_them_needs_a_note_then_runs_the_task_again_as_its_next_round_and_the_old_variants_stay(rig, monkeypatch):
    runner = start_pick(rig, monkeypatch)
    wait_for(runner, rig, "k1", ("picking",))
    for note in ("", "   \n"):
        with pytest.raises(RunnerError, match="A note says what to change: write one first"):
            runner.pick("demo", "k1", None, note)
    assert tasks_of(rig)["k1"]["state"] == "picking"                                            # a refusal leaves it asked
    runner.pick("demo", "k1", None, "rounder, and no anchor", via="screen")
    task = wait_for(runner, rig, "k1", ("picking",))
    assert task["round"] == 2 and len(calls(rig)) == 2 and calls(rig)[1]["resume"] is True
    first, second = (json.loads((rig.state / "ideas" / "demo" / "picks" / f"k1-r{n}" / "pick.json").read_text()) for n in (1, 2))
    assert first["picked"] is None and first["note"] == "rounder, and no anchor"                # the history keeps the answer
    assert "picked" not in second and [v["w"] for v in second["variants"]] == [21, 22, 23]
    assert (rig.state / "ideas" / "demo" / "picks" / "k1-r1" / "a.png").is_file()
    log = runner.log("demo", "k1")
    assert 'None of the last variants: "rounder, and no anchor"' in log and "Make 3 new ones" in log and "`.orkcraft-pick/`" in log
    [answer] = events_of(rig, "pick_answered")
    assert (answer["key"], answer["note_chars"], answer["via"]) == (None, len("rounder, and no anchor"), "screen")
    assert [(e["round"]) for e in events_of(rig, "pick_asked")] == [1, 2] and answer["round"] == 1
    runner.pick("demo", "k1", "C", "")                                                         # the second round's, then
    wait_for(runner, rig, "k1", ("merged",))
    assert (rig.repo / "assets" / "logo.png").read_bytes() == pf.png(23, 2)


# -- the host: ideas.pick, the Needs you row, the Map's task, today's rows and the push ------------------------------------------

import sys  # noqa: E402
import types  # noqa: E402

from orkboard.gui import media, phone_push  # noqa: E402
from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard  # noqa: E402
from orkboard.realm import board_today, ideas  # noqa: E402


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def waiting_pick(host, scratch: Path, files: dict[str, bytes] | None = None, kind: str = "image", extra_task: bool = True) -> str:
    """A goal whose task k1 made variants and waits for the pick (and k2 after it), as the runner leaves it; the goal's slug."""
    root, state = host.ideas.root(), host.ideas.state_dir
    party = ideas.save_goal(root, None, "Brand", "About the brand", None, "normal")[0]
    slug = ideas.add_idea(root, "A logo for the app", party, state)
    ideas.save_state(state, slug, state="working")
    files = files or {"a.png": pf.png(3, 2), "b.svg": pf.svg(24, 12), "c.jpg": pf.jpeg(40, 30)}
    base = {"brief": "b", "tier": "warrior", "branch": "", "commit": "", "session": "", "cost": None, "tokens": None, "started": "", "error": "", "note": ""}
    tasks = [{**base, "id": "k1", "title": "Draw the logo", "short": "Logo", "kind": "art", "after": [], "state": "picking", "round": 1,
              "finished": "2026-10-21T10:00:00", "role": "grunt", "pick": ask(len(files), kind)},
             *([{**base, "id": "k2", "title": "Use the logo", "short": "Use it", "kind": "code", "after": ["k1"], "state": "waiting"}] if extra_task else [])]
    ideas.save_plan(state, slug, {"idea": slug, "made_at": "2026-10-21T09:00:00", "passed_at": None, "todos": [], "tasks": tasks})
    ideas.edit_plan(state, slug, lambda p: p.update(passed_at="2026-10-21T09:30:00"))
    pf.make_pick(state, scratch, files, slug=slug, kind=kind)
    host.ideas.rev += 1
    return slug


def pick_rows(host) -> list[dict]:
    return [n for n in host.command("ideas.board")["needs_you"] if n["kind"] == "pick"]


def test_a_task_that_waits_for_a_pick_is_a_needs_you_row_with_its_variants_and_their_signed_addresses(host, tmp_path):
    slug = waiting_pick(host, tmp_path / "s")
    [row] = pick_rows(host)
    assert set(row) == {"kind", "slug", "idea", "goal", "task", "title", "short", "idea_title", "priority", "blocks", "by", "ask", "n", "media",
                        "variants", "round", "at"}
    assert (row["kind"], row["slug"], row["idea"], row["task"], row["title"], row["short"]) == ("pick", slug, slug, "k1", "Draw the logo", "Logo")
    assert (row["ask"], row["n"], row["media"], row["round"], row["at"], row["blocks"]) == ("A logo for the app", 3, "image", 1, row["at"], True)
    assert row["goal"] == ideas.tracks(host.ideas.root(), make=False)[-1]["slug"] and row["idea_title"] and row["priority"] == "normal"
    assert row["by"]["slug"] == "grunt" and row["by"]["name"] == "Grunt" and set(row["by"]["head"]) == {"craft", "race", "tier"}
    assert [(v["key"], v["name"], v["mime"], v["w"], v["h"], v["seconds"]) for v in row["variants"]] == [
        ("A", "a", "image/png", 3, 2, None), ("B", "b", "image/svg+xml", 24, 12, None), ("C", "c", "image/jpeg", 40, 30, None)]
    assert all(set(v) == {"key", "name", "why", "url", "mime", "w", "h", "seconds"} for v in row["variants"]) and row["variants"][0]["why"] == "why a.png"
    for v, data in zip(row["variants"], (pf.png(3, 2), pf.svg(24, 12), pf.jpeg(40, 30))):
        path, sig = v["url"].split("?s=")
        assert path == f"/media/{slug}/k1-r1/{v['key'].lower()}.{ {'image/png': 'png', 'image/svg+xml': 'svg', 'image/jpeg': 'jpg'}[v['mime']] }"
        assert media.check(path, sig) and media.serve("GET", v["url"], "", media.state_dirs(host)).read() == data       # the address opens the file
    assert host.ideas.snapshot()["needs_you"] == 1                                                    # it is an answer that waits


def test_ideas_pick_reaches_the_runner_with_its_key_note_and_where_and_its_refusals_are_plain_words(host, tmp_path, monkeypatch):
    seen = []

    class FakeRunner:
        def __init__(self, *a, **k):
            pass

        def pick(self, slug, tid, key, note, device="", via=""):
            seen.append((slug, tid, key, note, device, via))
            if note == "refuse":
                raise type("RunnerError", (Exception,), {})("That pick is answered already")

    monkeypatch.setitem(sys.modules, "orkboard.core.idea_runner", types.SimpleNamespace(IdeaRunner=FakeRunner))
    slug = waiting_pick(host, tmp_path / "s")
    a = {"slug": slug, "task": "k1"}
    assert host.command("ideas.pick", {**a, "key": "B", "note": "bluer", "via": "drawer"}) == {"ok": True}
    assert host.command("ideas.pick", {**a, "key": None, "note": "rounder", "via": "hand"}) == {"ok": True}
    assert host.command("ideas.pick", {**a, "key": "A"}) == {"ok": True}
    assert host.command("ideas.pick", {**a, "key": "C", "via": "screen", "device": "phone"}) == {"ok": True}
    assert host.command("ideas.pick", {**a, "key": "C", "via": "nowhere"}) == {"ok": True}
    assert host.command("ideas.pick", {**a, "key": "C", "via": "map"}) == {"ok": True}
    assert host.command("ideas.pick", {**a, "key": "C", "note": "x" * 3000}) == {"ok": True}
    assert seen[:3] == [(slug, "k1", "B", "bluer", "desktop", "drawer"), (slug, "k1", None, "rounder", "desktop", "hand"), (slug, "k1", "A", "", "desktop", "idea")]
    assert seen[3][4:] == ("phone", "screen") and seen[4][5] == "idea" and seen[5][5] == "map" and len(seen[6][3]) == 2000
    for bad, why in (({"key": 3}, "key is a variant's letter"), ({"key": "A", "note": 4}, "note is not text"), ({"key": "A", "task": ""}, "task is missing"),
                     ({"key": "A", "slug": ""}, "slug is missing")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.pick", {**a, **bad})
    with pytest.raises(CommandError, match="That pick is answered already"):
        host.command("ideas.pick", {**a, "key": "A", "note": "refuse"})


# -- a leader's sketch: the kind `page` (spec 121 A, docs/specs/121-the-day-the-morning-and-the-night.md §2.4) -------------------------------------

PAGE = b"<!doctype html><html><body><button>Press</button></body></html>"


def _sketch_task(n=2, kind="page", ask="A list of goals"):
    return idea_pick.leader_task(n, kind, ask)


def test_a_sketch_is_a_task_of_a_leader_with_no_target_and_a_plans_task_never_asks_for_a_page():
    t = _sketch_task()
    assert t == {"id": "sketch", "leader": True, "title": "Sketch", "pick": {"n": 2, "kind": "page", "ask": "A list of goals", "target": ""}}
    assert idea_pick.ask_of(t) == {"n": 2, "kind": "page", "ask": "A list of goals", "target": ""}
    page = {"n": 2, "kind": "page", "ask": "x", "target": "docs/x.html"}
    assert idea_pick.clean_ask(page) is None and idea_pick.ask_of({"pick": page}) is None                    # a plan's task makes no pages
    assert idea_pick.clean_ask(page, leader=True)["kind"] == "page" and idea_pick.clean_ask({**page, "target": "../etc"}, leader=True)["target"] == ""       # a leader's has no target
    assert idea_pick.ask_of({**t, "leader": False}) is None and idea_pick.ask_of({"id": "sketch", "pick": t["pick"]}) is None                # only a task marked a leader's
    assert idea_pick.clean_ask({"n": 7, "kind": "page", "ask": "x"}, leader=True) is None and idea_pick.clean_ask({"n": 2, "kind": "page", "ask": " "}, leader=True) is None
    assert idea_pick.clean_ask({"n": 2, "kind": "code", "ask": "x"}, leader=True) is None
    assert idea_pick.clean_ask({"n": 3, "kind": "image", "ask": "x", "target": "a.png", "look": True}, leader=True) == {"n": 3, "kind": "image", "ask": "x", "target": ""}


def test_a_page_is_read_stored_by_its_leader_and_never_written_into_a_project(tmp_path):
    tree, state = tmp_path / "scratch", tmp_path / "state"
    leave(tree, {"a.html": PAGE, "b.html": PAGE + b"<!-- b -->"}, names={"a.html": "Quiet", "b.html": "Loud"})
    got, why = idea_pick.read(tree, _sketch_task())
    assert why == "" and [(v["key"], v["name"], v["file"], v["mime"], v["w"], v["h"]) for v in got] == [("A", "Quiet", "a.html", "text/html", None, None), ("B", "Loud", "b.html", "text/html", None, None)]
    pick = idea_pick.store(state, "g", _sketch_task(), 1, got, by="leader")
    assert pick["id"] == "sketch-r1" and pick["by"] == "leader" and pick["kind"] == "page" and pick["target"] == "" and pick["task"] == "sketch" and pick["round"] == 1
    folder = state / "ideas" / "g" / "picks" / "sketch-r1"
    assert sorted(p.name for p in folder.iterdir()) == ["a.html", "b.html", "pick.json"] and (folder / "a.html").read_bytes() == PAGE
    idea_pick.discard(tree)
    assert not (tree / idea_pick.PICK_DIR).exists() and not (tree / idea_pick.PICK_FILE).exists()
    assert idea_pick.load(state, "g", "sketch-r1")["variants"][0]["mime"] == "text/html" and idea_pick.history(state, "g", "sketch")[0]["id"] == "sketch-r1"

