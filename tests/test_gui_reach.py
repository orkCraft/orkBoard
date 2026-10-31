"""Spec 117 A (docs/specs/117-each-lens-a-games-shape.md §1.4; decisions §195): the two commands the maps paint heat and reach by. `ideas.heat` (the hints of the open tab's party's map by part) and
`ideas.reach` (what a goal changes on that map, how far it spreads, the element, the state; System's guard and links), their refusals in plain words, and that nothing is written. The host
is `Orkboard` on a real git project, no model."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import goal_team, ideas, lens_rubrics, library, map_signals, spec_sections

APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\nimport Done from "./Done";\n'
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /><Route path="/done" element={<Done />} /></Routes>;\n',
    "src/Home.jsx": 'export default () => <Link to="/cart">Cart</Link>;\n',
    "src/Cart.jsx": 'export default () => <Link to="/done">Done</Link>;\n',
    "src/Done.jsx": "export default () => null;\n",
    "web/package.json": json.dumps({"name": "web", "dependencies": {"react": "18"}}),
    "web/src/app.js": 'fetch("/api/items");\n',
    "api/package.json": json.dumps({"name": "api", "dependencies": {"express": "4"}}),
    "api/server.js": 'const app = require("express")();\napp.get("/api/items", (req, res) => res.json([]));\n',
    **{f"core/base{n}.py": "X = 1\n" for n in range(1)},
    **{f"user{n}/m.py": "import core.base0\n" for n in range(map_signals.FAN_IN)},
    "tests/test_base0.py": "import core.base0\n",
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
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [leader])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal")
    goal_team.set_team(root, slug, [], leader=leader)
    return slug


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer")


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect")


def goal(host, party, title, will=None, element=""):
    """A goal of `party` whose page has a section for it (`will`: its *Will be* lines; None: no *Will be*)."""
    root, state = host.ideas.root(), host.ideas.state_dir
    slug = ideas.add_idea(root, title, party, state)
    page = ideas.idea_page(root, slug)
    head = next(t["title"] for t in ideas.tracks(root, make=False) if t["slug"] == party)
    spec_sections.arrange(page, {}, [(head, spec_sections.join({"Why": "Because.", "Done when": "- It works", **({"Will be": will} if will is not None else {})}))])
    ideas._write(root / ideas.IDEAS / f"{slug}.md", page.text())
    if element:
        ideas.save_state(state, slug, element=element)
    return slug


def test_both_commands_are_in_the_hosts_table(host):
    assert {"ideas.heat", "ideas.reach"} <= set(host.commands)


# -- ideas.heat ---------------------------------------------------------------------------------------------------------------------

def test_heat_is_the_hints_of_the_partys_map_by_part(host, design):
    got = host.command("ideas.heat", {"party": design})
    assert got["map"] == "screens" and set(got) == {"map", "parts"}
    assert got["parts"]["home"] == [{"kind": "no_picture", "aspect": lens_rubrics.aspect_of("design", "no_picture"), "words": "The screen Home (/) has no picture kept"},
                                    {"kind": "no_states", "aspect": lens_rubrics.aspect_of("design", "no_states"), "words": "The screen Home (/) says nothing of loading, error or empty states"}]
    assert all(set(h) == {"kind", "aspect", "words"} and len(hs) <= 3 for hs in got["parts"].values() for h in hs)


def test_heat_on_system_names_the_part_and_the_kind(host, tech):
    got = host.command("ideas.heat", {"party": tech})
    assert got["map"] == "system" and [h["kind"] for h in got["parts"]["core"]] == ["fan_in"]
    assert got["parts"]["core"][0]["words"] == f"core is used by {map_signals.FAN_IN + 1} parts"


def test_heat_of_a_party_with_no_map_is_nothing_and_an_unknown_party_is_refused_in_plain_words(host, design):
    plain = _party(host, "Plain", "taskmaster")
    assert host.command("ideas.heat", {"party": plain}) == {"map": "", "parts": {}}
    for party in ("nobody", "", ideas.GENERAL):
        with pytest.raises(CommandError, match="That party is gone"):
            host.command("ideas.heat", {"party": party})


# -- ideas.reach --------------------------------------------------------------------------------------------------------------------

def test_reach_on_screens_what_the_goal_changes_and_what_leads_to_it(host, design):
    slug = goal(host, design, "A way back", will="- changed done", element="ice")
    got = host.command("ideas.reach", {"party": design, "slug": slug})
    assert got == {"map": "screens", "slug": slug, "element": "ice", "state": "ok", "near": {"done": 0, "cart": 1, "home": 2}}, "no guard and no links outside System"


def test_reach_on_system_adds_the_guard_and_the_links_between_the_containers_it_crosses(host, tech):
    slug = goal(host, tech, "Rework base", will="- changed core/base0.py\n- changed web/src/app.js\n- changed api/server.js")
    got = host.command("ideas.reach", {"party": tech, "slug": slug})
    assert got["map"] == "system" and got["state"] == "ok" and got["element"] == ""
    users = {f"user{n}": 1 for n in range(map_signals.FAN_IN)}
    assert got["near"] == {"core": 0, "web/src": 0, "api": 0, "tests": 1, **users}, "what uses core is one step out"
    assert got["guard"] == {"core": True, "web/src": False, "api": False, "tests": True, **{u: False for u in users}}, "a test is mapped to core and to the tests part itself"
    assert got["links"] == [["web", "api"]], "the web calls what the api answers, and both hold a part the goal changes"
    web = goal(host, tech, "Web alone", will="- changed web/src/app.js")
    assert host.command("ideas.reach", {"party": tech, "slug": web})["links"] == [], "a link whose other container holds nothing reached is not crossed"


def test_reach_says_why_it_is_empty(host, design):
    nothing = goal(host, design, "Spec not written", will=None)
    assert host.command("ideas.reach", {"party": design, "slug": nothing}) == {"map": "screens", "slug": nothing, "element": "", "state": "no_will", "near": {}}
    other = _party(host, "Tech", "architect")
    elsewhere = goal(host, other, "Tech only", will="- changed core")
    assert host.command("ideas.reach", {"party": design, "slug": elsewhere})["state"] == "none"
    pinned = goal(host, other, "Pinned", will=None)
    ideas.save_state(host.ideas.state_dir, pinned, marks=[{"map": "screens", "id": "cart", "name": "Cart"}])
    assert host.command("ideas.reach", {"party": design, "slug": pinned})["near"] == {"cart": 0, "home": 1}, "a mark counts without a section"


def test_reach_of_a_party_with_no_map_is_nothing_and_unknowns_are_refused_in_plain_words(host, design):
    plain = _party(host, "Plain", "taskmaster")
    slug = goal(host, design, "A goal", will="- changed cart")
    assert host.command("ideas.reach", {"party": plain, "slug": slug}) == {"map": "", "slug": slug, "element": "", "state": "none", "near": {}}
    with pytest.raises(CommandError, match="That party is gone"):
        host.command("ideas.reach", {"party": "nobody", "slug": slug})
    for bad in ("no-such-goal", "../x"):
        with pytest.raises(CommandError, match="That goal is gone"):
            host.command("ideas.reach", {"party": design, "slug": bad})
    with pytest.raises(CommandError, match="slug is missing"):
        host.command("ideas.reach", {"party": design})


def test_neither_command_writes_anything(host, design, tech):
    slug = goal(host, design, "A way back", will="- changed done")

    def files() -> dict[Path, bytes]:
        """The Board's pages and the state, but for the map snapshots (a cache of the code that `ideas.system` keeps too)."""
        return {p: p.read_bytes() for base in (host.ideas.state_dir, host.ideas.root()) for p in sorted(base.rglob("*")) if p.is_file() and "maps" not in p.parts}

    before = files()
    for party in (design, tech):
        host.command("ideas.heat", {"party": party})
        host.command("ideas.reach", {"party": party, "slug": slug})
    assert files() == before
