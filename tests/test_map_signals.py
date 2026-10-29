"""Spec 108 A (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.2): `realm/map_signals.py`, what a party's map says is wrong by code, each hint grounded in what the map holds. Real git
repositories with real commits (churn needs them); no model."""
from __future__ import annotations

import json
import os
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

from orkboard.realm import idea_lens, ideas, loop, map_parts, map_signals, opportunity_tree as tree

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
    assert {s["on"] for s in got} <= ids and {s["kind"] for s in got} == {"loop"}
    assert [(s["on"], s["words"]) for s in got] == [("cur:gold", "Gold is only earned: it will pile up"), ("cur:gems", "Nothing gives Gems")]
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


# -- the rest -----------------------------------------------------------------------------------------------------------------------------

def test_art_release_and_marketing_have_none_by_code_yet(repo, tmp_path):
    put(repo, {"assets/hero.png": "png", "marketing/launch.md": "# Launch\n"})
    for craft in ("art", "release", "marketing", "run", "liveops", ""):
        assert map_signals.signals(tmp_path / "state", repo, craft) == []
