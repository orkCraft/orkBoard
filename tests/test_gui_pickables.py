"""`ideas.pickables {party, q}` (docs/specs/107-what-the-owners-day-said.md §11.4, gui/ideas_pickables.py): the parts of a party's map for the `@` of New goal's field. The ids and names are the
ones the maps stamp as `data-pick-id` and `data-pick-name`, so the parts are compared with what the maps' own commands answer (`ideas.screens`, `ideas.system`, `ideas.loop`)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.gui.ideas_pickables import loop_parts, pickables_commands
from orkboard.realm import goal_team, ideas, library, loop

APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\n'
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /></Routes>;\n',
    "src/Home.jsx": 'export default () => <Link to="/cart">Cart</Link>;\n',
    "src/Cart.jsx": "export default () => null;\n",
    "src/ui/hud.py": "X = 1\n",
    "src/game/loop.py": "import src.ui.hud\n",
}


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def host(fake_repo) -> Orkboard:
    run(fake_repo, "checkout", "-q", "-b", "dev")
    for name, text in APP.items():
        (fake_repo / name).parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / name).write_text(text)
    run(fake_repo, "add", "-A")
    run(fake_repo, "commit", "-q", "-m", "an app")
    h = Orkboard(fake_repo)
    assert "ideas.pickables" in h.commands and set(pickables_commands(h.ideas)) <= set(h.commands)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [leader])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal")
    goal_team.set_team(root, slug, [], leader=leader)
    return slug


def test_designs_parts_are_the_screens_and_the_steps_the_map_stamps(host):
    design = _party(host, "Design", "product-designer", "design")
    got = host.command("ideas.pickables", {"party": design})
    screens = host.command("ideas.screens", {})
    steps = [f"step:{n}" for n in range(1, len(screens["steps"]) + 1)]
    assert got["map"] == "screens" and [p["id"] for p in got["parts"]] == steps + [s["id"] for s in screens["screens"]]
    assert {p["map"] for p in got["parts"]} == {"screens"} and [p["name"] for p in got["parts"]][:2] == ["Step 1", "Step 2"]
    assert [p["id"] for p in host.command("ideas.pickables", {"party": design, "q": "car"})["parts"]] == ["cart"]


def test_techs_parts_are_the_systems_part_paths(host):
    tech = _party(host, "Tech", "architect", "tech")
    got = host.command("ideas.pickables", {"party": tech})
    system = host.command("ideas.system", {"party": tech})
    drawn = {p["path"] for c in system["columns"] for p in c["parts"]}
    assert drawn and drawn <= {p["id"] for p in got["parts"]} and got["map"] == "system"
    assert all(p["name"] == p["id"] and p["label"] == p["id"].rsplit("/", 1)[-1] for p in got["parts"]), "a part's name is its path, as syspane.js stamps it"
    assert [p["id"] for p in host.command("ideas.pickables", {"party": tech, "q": "ui"})["parts"]] == ["src/ui"]


def test_game_designs_parts_are_the_loops_steps_and_currencies_as_the_map_stamps_them(host):
    game = _party(host, "Game design", "game-designer", "game-design")
    assert host.command("ideas.pickables", {"party": game}) == {"party": game, "map": "game-design", "parts": []}
    loop.keep(host.ideas.state_dir, Path(host.ideas.host.repo_root), [{"name": n, "line": "A line", "rests_on": []} for n in ("Spawn", "Fight", "Loot", "Upgrade")], "person")
    steps = [st for lp in host.command("ideas.loop", {})["loops"] for st in lp["steps"]]       # a first version reads as one core loop
    got = host.command("ideas.pickables", {"party": game})
    assert [(p["id"], p["name"], p["map"]) for p in got["parts"]] == [(st["id"], st["name"], "game-design") for st in steps]
    assert [p["name"] for p in host.command("ideas.pickables", {"party": game, "q": "loo"})["parts"]] == ["Loot"]
    loop.keep(host.ideas.state_dir, Path(host.ideas.host.repo_root), {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [
        {"name": n, "line": "A line", "gives": ["gold"] if n == "Hit" else [], "takes": ["gold"] if n == "Buy" else []} for n in ("Hit", "Dodge", "Buy")]}],
        "currencies": [{"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins"}]}, "person")
    parts = loop_parts(host.ideas.state_dir)
    assert [p["name"] for p in parts] == ["Hit", "Dodge", "Buy", "Gold"]
    assert parts[-1] == {"id": "cur:gold", "name": "Gold", "group": "economy"}          # loopparts.js stamps a currency `cur:<id>`, a step its own id
    assert {p["group"] for p in parts[:-1]} == {"loop"}


def test_a_party_with_no_map_or_that_is_gone(host):
    tech = _party(host, "Plain", "taskmaster", "")
    assert host.command("ideas.pickables", {"party": tech})["parts"] == []
    with pytest.raises(CommandError):
        host.command("ideas.pickables", {"party": "nobody"})
    with pytest.raises(CommandError):
        host.command("ideas.pickables", {})


def test_at_most_thirty_parts(host):
    design = _party(host, "Design", "product-designer", "design")
    many = {f"src/p{n}.jsx": "export default () => null;\n" for n in range(40)}
    routes = "".join(f'<Route path="/p{n}" element={{<P />}} />' for n in range(40))
    many["src/App.jsx"] = f'import {{ Routes, Route }} from "react-router-dom";\nexport default () => <Routes>{routes}</Routes>;\n'
    for name, text in many.items():
        (Path(host.ideas.host.repo_root) / name).write_text(text)
    run(Path(host.ideas.host.repo_root), "add", "-A")
    run(Path(host.ideas.host.repo_root), "commit", "-q", "-m", "many")
    assert len(host.command("ideas.pickables", {"party": design})["parts"]) <= 30
