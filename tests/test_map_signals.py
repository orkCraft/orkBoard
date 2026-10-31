"""Spec 108 A (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.2), spec 109 B (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §3): `realm/map_signals.py`, what a party's
map says is wrong by code, each hint grounded in what the map holds: Tech's hotspot and unstable part, Design's screens with no states or a lapse of accessibility, Product's vague outcome, job with no
evidence and goals off the tree, Game design's findings by kind, spike, missing D1 hook and step that rests on no file. Real git repositories with real commits (churn needs them); no model."""
from __future__ import annotations

import json
import os
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

from orkboard.realm import hypotheses as hyp, idea_lens, ideas, loop, map_parts, map_signals, map_signals_crafts, opportunity_tree as tree

PNG = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0) + b"\x00" * 4 + struct.pack(">I", 0) + b"IEND" + b"\x00" * 4


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def put(repo: Path, files: dict[str, str], message: str = "work", old: bool = False) -> None:
    """A commit of `files`; `old`: dated years ago, outside the last month's churn."""
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    git(repo, "add", "-A")
    when = {"GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"} if old else {}
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True, capture_output=True, env={**os.environ, **when})


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "project"
    r.mkdir()
    git(r, "init", "-q", "-b", "dev")
    git(r, "config", "user.email", "test@orkcraft.local")
    git(r, "config", "user.name", "Test Runner")
    return r


def kinds(got: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in got:
        out.setdefault(s["kind"], []).append(s["on"])
    return out


def tech(repo: Path, tmp_path: Path) -> list[dict]:
    return map_signals.signals(tmp_path / "state", repo, "tech")


# -- Tech ---------------------------------------------------------------------------------------------------------------------------------

def test_a_cycle_between_parts(repo, tmp_path):
    put(repo, {"alpha/one.py": "import beta.two\n", "beta/two.py": "import alpha.one\n", "gamma/three.py": "import alpha.one\n"}, old=True)
    got = tech(repo, tmp_path)
    assert kinds(got) == {"cycle": ["alpha"]} and "alpha, beta use one another in a cycle" in got[0]["words"]


def test_a_part_used_by_many_and_a_part_using_many(repo, tmp_path):
    files = {"core/base.py": "X = 1\n", **{f"user{n}/m.py": "import core.base\n" for n in range(map_signals.FAN_IN)}}
    files.update({f"lib{n}/x.py": "Y = 1\n" for n in range(map_signals.FAN_OUT)})
    files["hub/h.py"] = "".join(f"import lib{n}.x\n" for n in range(map_signals.FAN_OUT))
    put(repo, files, old=True)
    got = tech(repo, tmp_path)
    assert kinds(got) == {"fan_in": ["core"], "fan_out": ["hub"]}
    assert next(s for s in got if s["kind"] == "fan_in")["words"] == f"core is used by {map_signals.FAN_IN} parts"


def test_one_under_the_thresholds_is_no_signal(repo, tmp_path):
    put(repo, {"core/base.py": "X = 1\n", **{f"user{n}/m.py": "import core.base\n" for n in range(map_signals.FAN_IN - 1)}}, old=True)
    assert tech(repo, tmp_path) == []


def test_a_part_with_a_file_of_eight_hundred_lines(repo, tmp_path):
    put(repo, {"big/huge.py": "x = 1\n" * map_signals.BIG_LINES, "small/ok.py": "x = 1\n" * (map_signals.BIG_LINES - 1)}, old=True)
    got = tech(repo, tmp_path)
    assert got == [{"on": "big", "kind": "big", "words": f"big holds huge.py of {map_signals.BIG_LINES} lines"}]


def test_a_part_changed_often_with_no_test_mapped_and_one_that_has_a_test(repo, tmp_path):
    put(repo, {"hot/motor.py": "n = 0\n", "cool/engine.py": "n = 0\n", "cool/other.py": "n = 0\n", "tests/test_engine.py": "def test_x():\n    pass\n", "calm/calm.py": "n = 0\n"}, old=True)
    for n in range(1, map_signals.CHURN_TIMES + 1):
        put(repo, {"hot/motor.py": f"n = {n}\n"}, f"hot {n}")
    for n in range(1, map_signals.CHURN_TIMES + 1):
        put(repo, {"cool/other.py": f"n = {n}\n"}, f"cool {n}")
    got = tech(repo, tmp_path)
    assert kinds(got) == {"untested_churn": ["hot"]}, "cool's engine.py has tests/test_engine.py by the gate's map"
    assert got[0]["words"] == f"hot changed {map_signals.CHURN_TIMES} times in the last {map_signals.CHURN_DAYS} days and no test is mapped to it"


def test_a_part_changed_five_times_is_no_signal(repo, tmp_path):
    put(repo, {"hot/motor.py": "n = 0\n"}, old=True)
    for n in range(1, map_signals.CHURN_TIMES):
        put(repo, {"hot/motor.py": f"n = {n}\n"}, f"hot {n}")
    assert tech(repo, tmp_path) == []


def test_a_shared_part_changed_along_with_files_of_two_containers(repo, tmp_path):
    put(repo, {"client/package.json": "{}\n", "server/package.json": "{}\n", "shared/util.js": "export const a = 1;\n",
               "client/src/a.js": 'import { a } from "../../shared/util.js";\n', "server/src/b.js": 'import { a } from "../../shared/util.js";\n'}, old=True)
    put(repo, {"shared/util.js": "export const a = 2;\n", "client/src/a.js": 'import { a } from "../../shared/util.js"; // 2\n'}, "from the client")
    assert "shared_churn" not in kinds(tech(repo, tmp_path))                          # one container so far
    put(repo, {"shared/util.js": "export const a = 3;\n", "server/src/b.js": 'import { a } from "../../shared/util.js"; // 3\n'}, "from the server")
    got = tech(repo, tmp_path)
    assert kinds(got)["shared_churn"] == ["shared"]
    assert "2 containers" in next(s for s in got if s["kind"] == "shared_churn")["words"] and "client" in got[-1]["words"] and "server" in got[-1]["words"]


def test_churn_older_than_a_month_does_not_count(repo, tmp_path):
    put(repo, {"hot/motor.py": "n = 0\n"}, old=True)
    for n in range(1, map_signals.CHURN_TIMES + 3):
        put(repo, {"hot/motor.py": f"n = {n}\n"}, f"old {n}", old=True)
    assert tech(repo, tmp_path) == []


def test_a_part_changed_often_that_holds_a_long_file_is_a_hotspot(repo, tmp_path):
    body = lambda n: "x = 1\n" * (map_signals.HOT_LINES - 1) + f"n = {n}\n"                                  # noqa: E731
    put(repo, {"hot/rooms.py": body(0), "short/small.py": "n = 0\n", "long/still.py": body(0)}, old=True)
    for n in range(1, map_signals.HOT_TIMES + 1):
        put(repo, {"hot/rooms.py": body(n), "short/small.py": f"n = {n}\n"}, f"hot {n}")
    for n in range(1, map_signals.HOT_TIMES):
        put(repo, {"long/still.py": body(n)}, f"long {n}")
    got = tech(repo, tmp_path)
    assert kinds(got) == {"hotspot": ["hot"]}, "short is changed as often but small; long is big but changed one time too few"
    assert got[0]["words"] == f"hot changed {map_signals.HOT_TIMES} times in the last {map_signals.CHURN_DAYS} days and holds rooms.py of {map_signals.HOT_LINES} lines"
    assert {s["on"] for s in got} <= {p["id"] for p in map_parts.parts(tmp_path / "state", repo, "tech")}


def test_a_part_many_stand_on_that_itself_uses_many_is_unstable(repo, tmp_path):
    libs = {f"lib{n}/x.py": "Y = 1\n" for n in range(9)}
    put(repo, {"lobby/l.py": "".join(f"import lib{n}.x\n" for n in range(9)), **libs, **{f"user{n}/m.py": "import lobby.l\n" for n in range(map_signals.UNSTABLE_IN + 1)}}, old=True)
    got = tech(repo, tmp_path)
    assert kinds(got) == {"unstable": ["lobby"]}
    assert got[0]["words"] == "lobby is used by 5 parts and itself uses 9: what many stand on keeps changing with what it uses"


def test_a_part_used_by_four_that_uses_few_or_one_used_by_three_is_not_unstable(repo, tmp_path):
    put(repo, {"core/base.py": "".join(f"import lib{n}.x\n" for n in range(6)), **{f"lib{n}/x.py": "Y = 1\n" for n in range(6)},
               **{f"user{n}/m.py": "import core.base\n" for n in range(5)}, "mid/m.py": "".join(f"import lib{n}.x\n" for n in range(9)) + "", **{f"lib{n}/x.py": "Y = 1\n" for n in range(9)},
               **{f"low{n}/m.py": "import mid.m\n" for n in range(map_signals.UNSTABLE_IN - 1)}}, old=True)
    assert "unstable" not in kinds(tech(repo, tmp_path)), "core: 6 / (6 + 5) is under 0.6; mid: used by only 3"


def test_cycles_alone(repo):
    assert map_signals.cycles({"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"], "e": []}) == [["a", "b", "c"]]
    assert map_signals.cycles({"a": ["b"], "b": []}) == [] and map_signals.cycles({"a": ["a"]}) == []


def test_a_project_with_no_dev_has_no_signals(tmp_path):
    bare = tmp_path / "bare"
    bare.mkdir()
    git(bare, "init", "-q", "-b", "main")
    assert map_signals.signals(tmp_path / "state", bare, "tech") == []


# -- Game design --------------------------------------------------------------------------------------------------------------------------

def test_the_loops_findings_each_on_the_part_it_names(repo, tmp_path):
    state = tmp_path / "state"
    loop.keep(state, repo, {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [
        {"name": n, "line": "A line", "gives": ["gold"] if n == "Hit" else [], "takes": []} for n in ("Hit", "Dodge", "Buy")]}],
        "currencies": [{"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins"}, {"id": "gems", "name": "Gems", "kind": "hard", "line": "Rare"}]}, "person")
    got = map_signals.signals(state, repo, "game-design")
    ids = {p["id"] for p in map_parts.parts(state, repo, "game-design")}
    assert {s["on"] for s in got} <= ids and [s["kind"] for s in got] == ["pile_up", "no_source", "no_hook"]
    assert [(s["on"], s["kind"], s["words"]) for s in got if s["kind"] != "no_hook"] == [("cur:gold", "pile_up", "Gold is only earned: it will pile up"), ("cur:gems", "no_source", "Nothing gives Gems")]
    assert [w for _on, w in loop.findings_on(loop.read(state))] == loop.findings(loop.read(state))
    assert map_signals.signals(tmp_path / "none", repo, "game-design") == []


def test_a_flat_loop_and_a_loop_that_rewards_nothing_are_on_the_loops_first_step(repo, tmp_path):
    state = tmp_path / "state"
    loop.keep(state, repo, {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [
        {"name": n, "line": "A line", "feel": "challenge", "intensity": 3, "gives": [], "takes": []} for n in ("Hit", "Dodge", "Buy")]}],
        "currencies": [{"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins"}]}, "person")
    got = map_signals.signals(state, repo, "game-design")
    first = loop.read(state)["loops"][0]["steps"][0]["id"]
    assert ("cur:gold", "Nothing gives Gold") in [(s["on"], s["words"]) for s in got]
    assert (first, "The core loop rewards nothing") in [(s["on"], s["words"]) for s in got] and (first, "The core loop's feeling is flat") in [(s["on"], s["words"]) for s in got]


def test_a_spike_a_missing_first_day_hook_and_a_step_that_rests_on_no_file(repo, tmp_path):
    put(repo, {"config/waves.yml": "waves: 3\n"})
    state = tmp_path / "state"
    card = lambda name, n, **more: {"name": name, "line": "A line", "intensity": n, **more}                       # noqa: E731
    wave = loop.keep(state, repo, {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [
        card("Aim", 2, rests_on=["config/waves.yml"]), card("Shoot", 5), card("Rest", 4)]}], "currencies": []}, "person")[0]
    ids = [s["id"] for s in wave["loops"][0]["steps"]]
    got = map_signals.signals(state, repo, "game-design")
    assert [(s["on"], s["kind"]) for s in got] == [(ids[1], "spike"), (ids[0], "no_hook"), (ids[1], "unground"), (ids[2], "unground")]
    assert got[0]["words"] == "The core loop jumps from intensity 2 at Aim to 5 at Shoot" and got[1]["words"] == "No hook says why a player comes back on the first day (D1)"
    assert got[2]["words"] == "The step Shoot of the core loop rests on no file, though others of it do"
    assert {s["on"] for s in got} <= {p["id"] for p in map_parts.parts(state, repo, "game-design")}
    calm = loop.keep(state, repo, {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [card("Aim", 2), card("Shoot", 4), card("Rest", 3)]}], "currencies": [],
                                   "hooks": [{"when": "D1", "line": "A new weapon on the second day"}]}, "person")[0]
    assert map_signals.signals(state, repo, "game-design") == [] and calm["hooks"], "a step of 2 after 4 is no spike, D1 is said, no step rests on a file"


# -- Design -------------------------------------------------------------------------------------------------------------------------------

APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\n' + "".join(f'import {n} from "./{n}";\n' for n in ("Home", "Mid", "Cart", "Done", "About")) +
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/mid" element={<Mid />} /><Route path="/cart" element={<Cart />} />'
                   '<Route path="/done" element={<Done />} /><Route path="/about" element={<About />} /></Routes>;\n',
    "src/Home.jsx": 'export default () => <><Link to="/mid">Mid</Link><Link to="/cart">Cart</Link></>;\n',
    "src/Mid.jsx": "export default () => null;\n",
    "src/Cart.jsx": 'export default () => <Link to="/done">Done</Link>;\n',
    "src/Done.jsx": "export default () => null;\n",
    "src/About.jsx": "export default () => null;\n",
}


def test_a_screen_nothing_leads_to_one_that_leads_nowhere_and_one_with_no_picture(repo, tmp_path):
    put(repo, APP)
    state = tmp_path / "state"
    got = map_signals.signals(state, repo, "design")
    found = kinds(got)
    ids = {p["id"] for p in map_parts.parts(state, repo, "design")}
    assert found["loose"] == ["about"] and found["dead_end"] == ["mid"]
    assert set(found["no_picture"]) == {"home", "mid", "cart", "done", "about"} and {s["on"] for s in got} <= ids
    idea_lens.keep_screen(state, PNG, "Cart")
    assert "cart" not in kinds(map_signals.signals(state, repo, "design"))["no_picture"]


def test_a_screen_that_names_no_state_and_one_a_keyboard_or_a_reader_would_stumble_on(repo, tmp_path):
    put(repo, {**APP,
               "src/Home.jsx": 'export default () => { if (loading) return <Spinner />; return <><img src="a.png" /><Link to="/mid">Mid</Link><Link to="/cart">Cart</Link></>; };\n',
               "src/Mid.jsx": "export default () => <div onClick={() => go()}>Next</div>;\n",
               "src/Cart.jsx": 'export default () => { try { return <><input type="text" /><Link to="/done">Done</Link></>; } catch (error) { return null; } };\n',
               "src/Done.jsx": 'const empty = true;\nexport default () => <><img alt="" src="a.png" onLoad={() => a > b} /><div onClick={f} role="button" /><input id="q" /><input type="hidden" />'
                               '<input {...props} /><span {...rest} onClick={f} /></>;\n'})
    state = tmp_path / "state"
    got = map_signals.signals(state, repo, "design")
    found = kinds(got)
    assert found["no_states"] == ["mid", "about"] and found["a11y"] == ["home", "mid", "cart"]
    words = {s["on"]: s["words"] for s in got if s["kind"] == "a11y"}
    assert words == {"home": "Home (/): an image with no alt text", "mid": "Mid (/mid): a press on a div with no role", "cart": "Cart (/cart): an input with no label"}
    assert next(s for s in got if s["kind"] == "no_states")["words"] == "The screen Mid (/mid) says nothing of loading, error or empty states"
    assert {s["on"] for s in got} <= {p["id"] for p in map_parts.parts(state, repo, "design")}


def test_a_file_that_several_screens_share_or_one_too_large_says_nothing_of_any_screen(repo, tmp_path):
    put(repo, {"package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
               "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport A from "./A";\nimport B from "./B";\nimport S from "./Shared";\n'
                              'export default () => <Routes><Route path="/" element={<A />} /><Route path="/b" element={<B />} /><Route path="/c" element={<S />} /><Route path="/d" element={<S />} /></Routes>;\n',
               "src/A.jsx": "<img />\n" + "x" * map_signals.SCREEN_BYTES, "src/B.jsx": "<img />\n", "src/Shared.jsx": "<img />\n"})
    got = map_signals.signals(tmp_path / "state", repo, "design")
    assert kinds(got)["a11y"] == ["b"], "A is over 200 KB, C and D share a file: none is read"
    assert kinds(got)["no_states"] == ["b"]


def test_at_most_twenty_signals(repo, tmp_path):
    routes = "".join(f'<Route path="/p{n}" element={{<P />}} />' for n in range(40))
    put(repo, {"src/App.jsx": f'import {{ Routes, Route }} from "react-router-dom";\nexport default () => <Routes>{routes}</Routes>;\n',
               **{f"src/p{n}.jsx": "export default () => null;\n" for n in range(40)}, "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}})})
    assert len(map_signals.signals(tmp_path / "state", repo, "design")) == map_signals.MAX_SIGNALS


def test_the_pictures_of_the_screens_kept_since_a_look(repo, tmp_path):
    put(repo, APP)
    state = repo / ".orkcraft"
    state.mkdir()
    idea_lens.keep_screen(state, PNG, "Cart")
    got = map_signals.pictures(state, repo)
    assert [(p["id"], p["name"]) for p in got] == [("cart", "Cart")] and (repo / got[0]["path"]).is_file() and got[0]["path"].startswith(".orkcraft/")
    assert map_signals.pictures(state, repo, since="2999-01-01T00:00:00") == []
    assert map_signals.pictures(state, repo, since="2000-01-01T00:00:00")[0]["id"] == "cart" and map_signals.pictures(state, repo, limit=0) == []


# -- Product ------------------------------------------------------------------------------------------------------------------------------

def test_a_job_no_goal_serves_pains_piled_on_a_screen_and_pains_pinned_to_nothing(repo, tmp_path):
    put(repo, APP)
    state = repo / ".orkcraft"
    pages = tmp_path / "pages"
    tree.keep(state, [{"text": "Cut the time to a first sketch from ten minutes to two"}],
              [{"when": "I start", "want": w, "so": "judge it", "segment": "founders"} for w in ("see a sketch", "share it", "compare two")], "person")
    goal = ideas.add_idea(pages, "Fast checkout", "general", state)
    first = tree.read(state)["jobs"][0]["id"]
    tree.attach(state, first, goal)
    for pain in ("Cart is slow", "Cart loses items", "Cart is confusing"):
        idea_lens.keep_segment(state, "Shoppers", pain, on="cart")
    idea_lens.keep_segment(state, "Shoppers", "Nobody knows what it is for")
    idea_lens.keep_segment(state, "Shoppers", "Checkout is slow", on="done")
    got = map_signals.signals(state, repo, "product", pages)
    found = kinds(got)
    assert sorted(found["unserved"]) == sorted(j["id"] for j in tree.read(state)["jobs"][1:]) and found["pains"] == ["cart"] and found["pain_loose"] == [""]
    piled = next(s for s in got if s["kind"] == "pains")
    assert piled["map"] == "screens" and "3 pains are pinned to cart" in piled["words"] and "Cart is slow" in piled["words"]
    assert {s["on"] for s in got if s["kind"] == "unserved"} <= {p["id"] for p in map_parts.parts(state, repo, "product", pages)}


def test_an_outcome_with_no_number_a_job_with_two_goals_and_no_experiment_and_goals_in_line_off_the_tree(repo, tmp_path):
    put(repo, APP)
    state, pages = repo / ".orkcraft", tmp_path / "pages"
    tree.keep(state, [{"text": "Make sketching easy"}, {"text": "Cut the time to a first sketch to 2 minutes"}],
              [{"when": "I start", "want": w, "so": "judge it", "segment": "founders"} for w in ("see a sketch", "share it", "compare two")], "person")
    jobs = [j["id"] for j in tree.read(state)["jobs"]]
    goals = [ideas.add_idea(pages, f"Goal number {n}", "general", state) for n in range(6)]
    for g in goals[:2]:
        tree.attach(state, jobs[0], g)
    tree.attach(state, jobs[1], goals[2])
    got = map_signals.signals(state, repo, "product", pages)
    found = kinds(got)
    assert found["vague_outcome"] == [""] and found["no_evidence"] == [jobs[0]] and found["off_tree"] == [""]
    assert next(s for s in got if s["kind"] == "vague_outcome")["words"].endswith("Make sketching easy")
    assert next(s for s in got if s["kind"] == "no_evidence")["words"] == "2 goals serve the job see a sketch and no experiment tests any of them"
    assert next(s for s in got if s["kind"] == "off_tree")["words"].startswith("3 goals in line serve no job: ") and {s["on"] for s in got} <= {p["id"] for p in map_parts.parts(state, repo, "product", pages)} | {""}
    tree.test(state, goals[0], goals[3])                                                                     # an experiment tests one of the two goals: evidence
    assert "no_evidence" not in kinds(map_signals.signals(state, repo, "product", pages))
    assert "off_tree" not in kinds(map_signals.signals(state, repo, "product")), "off_tree needs the Board's pages"
    tree.attach(state, jobs[2], goals[4])
    assert "off_tree" not in kinds(map_signals.signals(state, repo, "product", pages)), "two goals off the tree are under OFF_TREE"


def test_a_goal_in_line_or_at_work_on_an_open_hypothesis_with_no_test_is_untested_once_a_goal(repo, tmp_path):
    """Spec 116 D: `untested`, on the goal's id as the tree names it (else ""), for the first such hypothesis."""
    put(repo, APP)
    state, pages = repo / ".orkcraft", tmp_path / "pages"
    tree.keep(state, [{"text": "Cut the time to a first sketch to 2 minutes"}],
              [{"when": "I start", "want": w, "so": "judge it", "segment": "founders"} for w in ("see a sketch", "share it", "compare two")], "person")
    job = tree.read(state)["jobs"][0]["id"]
    line, work, off = (ideas.add_idea(pages, t, "general", state) for t in ("Sketch pad", "Share links", "Loose goal"))
    ideas.save_state(state, work, state="working")
    tree.attach(state, job, line)
    tree.attach(state, job, work)
    first = hyp.add(state, "People want to share a sketch", "Three of five ask for a link", rests=[line, work])
    hyp.add(state, "People draw on a phone", "A third open it there", rests=[line, off])
    got = [s for s in map_signals.signals(state, repo, "product", pages) if s["kind"] == "untested"]
    assert [(s["on"], s["words"]) for s in got] == [(line, f"Sketch pad rests on an untested hypothesis: {first['text']}"), (work, f"Share links rests on an untested hypothesis: {first['text']}"),
                                                    ("", f"Loose goal rests on an untested hypothesis: People draw on a phone")], "one a goal, the first hypothesis; a goal off the tree is on no part"
    assert {s["on"] for s in got} - {""} <= {p["id"] for p in map_parts.parts(state, repo, "product", pages)}
    assert not [s for s in map_signals.signals(state, repo, "product") if s["kind"] == "untested"], "untested needs the Board's pages"


def test_untested_is_off_for_a_hypothesis_with_a_test_that_is_held_or_proposed_and_for_a_goal_done_or_gone(repo, tmp_path):
    put(repo, APP)
    state, pages = repo / ".orkcraft", tmp_path / "pages"
    mine, experiment = ideas.add_idea(pages, "Sketch pad", "general", state), ideas.add_idea(pages, "Ask five people", "general", state)
    def untested() -> list[str]:
        return [s["words"] for s in map_signals.signals(state, repo, "product", pages) if s["kind"] == "untested"]
    one = hyp.add(state, "People want to share", "Links are asked for", rests=[mine])
    assert len(untested()) == 1
    hyp.attach(state, one["id"], test=experiment)
    assert untested() == [], "a hypothesis with a test is no longer untested"
    hyp.attach(state, "", test=experiment)
    assert len(untested()) == 1
    hyp.judge(state, one["id"], "held")
    assert untested() == [], "a held hypothesis is not open"
    hyp.drop(state, one["id"])
    hyp.add(state, "People pay for it", "Two sign up", by="leader", party="product", rests=[mine])
    assert untested() == [], "a proposed hypothesis is not yet the project's"
    hyp.keep(state, "people-pay-for-it")
    assert len(untested()) == 1
    ideas.save_state(state, mine, state="done")
    assert untested() == [], "a goal done is no longer built on it"
    ideas.save_state(state, mine, state="")
    assert len(untested()) == 1
    hyp.edit(state, "people-pay-for-it", rests=["gone-from-the-board"])
    assert untested() == [], "a goal the Board no longer has is none"


# -- the rest ---------------------------------------------------------------------------------------------------------------------------

def test_a_craft_with_no_map_has_none_by_code(repo, tmp_path):
    put(repo, {"assets/hero.png": "png", "marketing/launch.md": "# Launch\n"})
    for craft in ("run", "liveops", ""):
        assert map_signals.signals(tmp_path / "state", repo, craft) == []


def test_art_release_and_marketing_are_read_by_the_crafts_module(repo, tmp_path):
    put(repo, {"assets/hero.png": "png", "marketing/launch.md": "# Launch\n"})
    got = map_signals.signals(tmp_path / "state", repo, "marketing")
    assert got == map_signals_crafts.marketing(tmp_path / "state", repo) and {"no_onboarding", "no_return", "no_share", "no_revenue"} <= {s["kind"] for s in got}
    assert map_signals.signals(tmp_path / "state", repo, "art") == map_signals_crafts.art(tmp_path / "state", repo)
    assert map_signals.signals(tmp_path / "state", repo, "release") == map_signals_crafts.release(tmp_path / "state", repo) == []      # dev and main are one branch here
