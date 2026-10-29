"""Spec 108 A (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.1): `realm/map_parts.py`, the cards every party's map draws with the ids the faces stamp as `data-pick-id`. The ids are compared with
what the maps' own commands answer (`ideas.screens`, `ideas.system`, `ideas.loop`, `ideas.tree`, `ideas.art_map`, `ideas.way_map`, `ideas.release_map`); a craft with no map has none."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, ideas, library, loop, map_parts, opportunity_tree as tree
from tests.test_commit_goal import land, repo, state  # noqa: F401  (the fixture)

APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\n'
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /></Routes>;\n',
    "src/Home.jsx": 'export default () => <Link to="/cart">Cart</Link>;\n',
    "src/Cart.jsx": "export default () => null;\n",
    "src/ui/hud.py": "X = 1\n",
    "src/game/loop.py": "import src.ui.hud\n",
    "assets/hero.png": "png",
    "assets/theme.ogg": "ogg",
    "marketing/launch.md": "# Launch\n",
    "landing/index.html": "<html></html>\n",
}


def run(repo_: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_, check=True, capture_output=True)


@pytest.fixture
def host(fake_repo) -> Orkboard:
    run(fake_repo, "checkout", "-q", "-b", "dev")
    for name, text in APP.items():
        (fake_repo / name).parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / name).write_text(text)
    run(fake_repo, "add", "-A")
    run(fake_repo, "commit", "-q", "-m", "an app")
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def parts(host, craft):
    return map_parts.parts(host.ideas.state_dir, Path(host.ideas.host.repo_root), craft, host.ideas.root(make=False))


def test_designs_parts_are_the_steps_and_screens_the_command_gives_each_in_its_step(host):
    got = parts(host, "design")
    screens = host.command("ideas.screens", {})
    assert [p["id"] for p in got] == [f"step:{n}" for n in range(1, len(screens["steps"]) + 1)] + [s["id"] for s in screens["screens"]]
    assert {p["map"] for p in got} == {"screens"} and [p["name"] for p in got][:2] == ["Step 1", "Step 2"]
    in_step = {p["id"]: p["group"] for p in got if "group" in p}
    assert all(in_step[sid] == f"step:{n}" for n, row in enumerate(screens["steps"], 1) for sid in row)


def test_techs_parts_are_the_systems_part_paths_each_in_its_container(host):
    root, state_dir = host.ideas.root(), host.ideas.state_dir
    library.install(state_dir, ["architect"])
    tech, _new = ideas.save_goal(root, None, "Tech", "About tech", None, "normal", craft="engineering")
    goal_team.set_team(root, tech, [], leader="architect")
    got = parts(host, "tech")
    drawn = {p["path"] for c in host.command("ideas.system", {"party": tech})["columns"] for p in c["parts"]}
    assert drawn and drawn <= {p["id"] for p in got} and {"src/ui", "src/game"} <= {p["id"] for p in got}
    assert all(p["name"] == p["id"] and p["map"] == "system" for p in got)
    assert all("group" in p for p in got) and next(p for p in got if p["id"] == "src/ui")["group"] == "."


def test_game_designs_parts_are_the_loops_steps_then_its_currencies(host):
    assert parts(host, "game-design") == []
    loop.keep(host.ideas.state_dir, Path(host.ideas.host.repo_root), {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [
        {"name": n, "line": "A line", "gives": ["gold"] if n == "Hit" else [], "takes": ["gold"] if n == "Buy" else []} for n in ("Hit", "Dodge", "Buy")]}],
        "currencies": [{"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins"}]}, "person")
    got = parts(host, "game-design")
    shown = host.command("ideas.loop", {})
    assert [p["id"] for p in got] == [st["id"] for lp in shown["loops"] for st in lp["steps"]] + [f"cur:{c['id']}" for c in shown["currencies"]]
    assert [p["name"] for p in got] == ["Hit", "Dodge", "Buy", "Gold"] and {p["map"] for p in got} == {"game-design"}
    assert [p["group"] for p in got] == ["loop", "loop", "loop", "economy"]


def test_products_parts_are_the_jobs_then_the_goals_the_tree_names_that_the_board_has(host):
    assert parts(host, "product") == []
    state_dir, pages = host.ideas.state_dir, host.ideas.root()
    goal = ideas.add_idea(pages, "Fast checkout", "general", state_dir)
    tree.keep(state_dir, [{"text": "Cut the time to a first sketch from ten minutes to two"}],
              [{"when": "I start", "want": w, "so": "judge it", "segment": "founders"} for w in ("see a sketch", "share it", "compare two")], "person")
    job = tree.read(state_dir)["jobs"][0]["id"]
    tree.attach(state_dir, job, goal)
    got = parts(host, "product")
    shown = host.command("ideas.tree", {})
    assert [p["id"] for p in got] == [j["id"] for j in shown["jobs"]] + [s["goal"] for s in shown["serves"]] == [j["id"] for j in tree.read(state_dir)["jobs"]] + [goal]
    assert [p["name"] for p in got][-1] == "Fast checkout" and [p["group"] for p in got] == ["jobs"] * 3 + ["goals"] and {p["map"] for p in got} == {"product"}


def test_arts_parts_are_the_assets_the_map_draws_by_their_path(host):
    got = parts(host, "art")
    shown = host.command("ideas.art_map", {})
    assert {p["id"] for p in got} == {a["id"] for k in shown["kinds"] for a in k["assets"]} and {"assets/hero.png", "assets/theme.ogg"} <= {p["id"] for p in got}
    assert {p["map"] for p in got} == {"art"} and next(p for p in got if p["id"] == "assets/hero.png")["name"] == "hero.png"


def test_marketings_parts_are_the_files_of_the_way_in_by_their_path(host):
    got = parts(host, "marketing")
    shown = host.command("ideas.way_map", {})
    assert [p["id"] for p in got] == [h["path"] for step in shown["steps"] for h in shown[step]["holds"]] and "marketing/launch.md" in {p["id"] for p in got}
    assert next(p for p in got if p["id"] == "marketing/launch.md") == {"map": "marketing", "id": "marketing/launch.md", "name": "launch.md", "group": "channels"}


def test_releases_parts_are_the_goals_waiting_for_main(repo, tmp_path):
    pages = tmp_path / "pages"
    one = ideas.add_idea(pages, "Dark mode", "general", state(repo))
    assert map_parts.parts(state(repo), repo, "release", pages) == []
    land(repo, one, "k1", {"x.css": "x\n"})
    assert map_parts.parts(state(repo), repo, "release", pages) == [{"map": "release", "id": one, "name": "Dark mode", "group": "dev"}]


def test_a_craft_with_no_map_has_no_parts_and_a_map_that_cannot_be_read_none(host, tmp_path):
    assert parts(host, "run") == [] and parts(host, "") == [] and parts(host, "liveops") == []
    assert map_parts.parts(tmp_path / "nowhere", tmp_path / "nowhere", "tech") == []            # no repository: nothing to read, no error


def test_the_craft_of_a_party_is_techs_when_the_architect_leads_it(host):
    root, state_dir = host.ideas.root(), host.ideas.state_dir
    library.install(state_dir, ["architect", "product-designer"])
    tech, _new = ideas.save_goal(root, None, "Tech", "About tech", None, "normal", craft="engineering")
    goal_team.set_team(root, tech, [], leader="architect")
    design, _new = ideas.save_goal(root, None, "Design", "About design", None, "normal", craft="design")
    goal_team.set_team(root, design, [], leader="product-designer")
    assert map_parts.craft_of(root, tech) == "tech" and map_parts.craft_of(root, design) == "design"
