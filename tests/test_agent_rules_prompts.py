"""Spec 151 C.3: the seats' fixed instruction texts moved into functions their prompts are built from, and **no prompt changed by a character**.
Each prompt is built on a fixture goal and compared with the exact text stored in `tests/prompts_151/` (made once from the code before the move;
`ORKCRAFT_WRITE_PROMPTS=1 pytest tests/test_agent_rules_prompts.py` writes them again, for a change of a prompt that is meant)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_route, goal_team, ideas, library

STORED = Path(__file__).parent / "prompts_151"
MAP = "THE MAP TEXT\nsecond line of the map"


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.ideas.keeper._map = lambda party: MAP
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


def _same(name: str, text: str) -> None:
    path = STORED / f"{name}.txt"
    if os.environ.get("ORKCRAFT_WRITE_PROMPTS"):
        STORED.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == text, f"the prompt {name} changed"


def test_every_seats_prompt_is_the_text_it_was_before_its_fixed_part_became_a_function(host):
    k = host.ideas.keeper
    tech = _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")
    design = _party(host, "Design", "product-designer", ["artist"], "design")
    product = _party(host, "Product", "product-manager", ["copywriter"], "product")
    root = host.ideas.root()
    goal = ideas.add_idea(root, "add a score board", tech, host.ideas.state_dir, "normal", "hold")
    ideas.save_state(host.ideas.state_dir, goal, marks=[{"map": "screens", "id": "step:1", "name": "Step 1"}])
    route = [{"party": p, "leader": goal_team.leader_of(root, p)} for p in (product, design, tech)]
    entry = {t: next(r for r in route if r["party"] == p) for t, p in (("tech", tech), ("design", design), ("product", product))}
    line = [{"slug": "dark-mode", "title": "Dark mode", "party_title": "Design"}]

    _same("route", goal_route.prompt("Add a score board that shows the best three players", goal_route.parties(root)))
    _same("route_one_party", goal_route.prompt("Fix the crash", goal_route.parties(root)[:1]))
    _same("talk_tech", k.round_prompt(goal, entry["tech"], route, 1, "", False, set()))
    _same("talk_tech_first_goal", k.round_prompt(goal, entry["tech"], route, 1, "", True, {"stack"}))
    _same("talk_tech_first_goal_nothing_known", k.round_prompt(goal, entry["tech"], route, 1, "", True, set()))
    _same("talk_design", k.round_prompt(goal, entry["design"], route, 1, "", False, set()))
    _same("talk_product_with_a_line", k.round_prompt(goal, entry["product"], route, 1, "", False, set(), line))
    _same("talk_tech_with_a_line", k.round_prompt(goal, entry["tech"], route, 1, "", False, set(), line))
    _same("talk_tech_second_round", k.round_prompt(goal, entry["tech"], route, 2, "Which store first? Google Play.", False, set()))
    _same("section_tech_first", k.section_prompt(goal, entry["tech"], route, True))
    _same("section_design", k.section_prompt(goal, entry["design"], route, False))
    _same("section_product_after_a_fork", k.section_prompt(goal, entry["product"], route, False, ["Fork: a number"]))
    texts = {e["party"]: {"parts": {"Why": "Because " + e["party"], "Done when": "- When it runs, then it shows", "Will be": "- changed src/app.py — the board", "Out": "- the phone"}}
             for e in route}
    _same("join", k.join_prompt(goal, route, texts))


def test_the_acceptances_prompt_is_the_text_it_was_before_its_fixed_part_became_a_function(host):
    """Spec 152 D.1: the acceptance of a step, on a fixture goal of Tech with one landed task, stored as `accept_tech.txt`."""
    k = host.ideas.keeper
    tech = _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")
    goal = ideas.add_idea(host.ideas.root(), "add a score board", tech, host.ideas.state_dir, "normal", "hold")
    ideas.save_plan(host.ideas.state_dir, goal, {"tasks": [{"id": "k1", "title": "Build the board", "state": "merged", "step": 1, "tests": {"passed": 4, "failed": 0}}]})
    _same("accept_tech", k.accept_step_prompt(goal, 1, tech, 1))
