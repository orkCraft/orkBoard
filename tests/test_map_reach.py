"""Spec 117 A (docs/specs/117-each-lens-a-games-shape.md §1; decisions §195): `realm/map_reach.py`, heat and reach read by code. Heat (every hint by part, three a part, the partless dropped, kept per head),
each map's relation (System's used_by, a screen's linkers, the tree both ways, the loop's ring and its currencies, Release through `goal_main.plan`), `reach`'s two steps with the nearest winning,
`touched`'s three states (a file inside a part, a mark, a group), System's `guard` and `links`. Real git repositories, no model."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orkboard.realm import hypotheses as hyp, ideas, lens_rubrics, loop, map_parts, map_reach, map_signals, opportunity_tree as tree, project_map, spec_sections
from orkboard.realm.idea_git import IdeaGit
from tests.test_map_signals import APP, git, put


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "project"
    r.mkdir()
    git(r, "init", "-q", "-b", "dev")
    git(r, "config", "user.email", "test@orkcraft.local")
    git(r, "config", "user.name", "Test Runner")
    return r


@pytest.fixture
def state(tmp_path: Path) -> Path:
    return tmp_path / "state"


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    return tmp_path / "pages"


CHAIN = {"alpha/one.py": "X = 1\n", "beta/two.py": "import alpha.one\n", "gamma/three.py": "import beta.two\n", "delta/four.py": "import gamma.three\n"}


# -- heat ---------------------------------------------------------------------------------------------------------------------------

def test_heat_is_every_hint_by_its_part_three_at_most_in_signals_order_the_partless_and_other_maps_dropped(repo, state, monkeypatch):
    seen = []
    rows = [{"on": "a", "kind": "cycle", "words": "one"}, {"on": "", "kind": "no_channel", "words": "of no part"}, {"on": "a", "kind": "fan_in", "words": "two"},
            {"on": "b", "kind": "big", "words": "other"}, {"on": "a", "kind": "big", "words": "three"}, {"on": "a", "kind": "hotspot", "words": "four"},
            {"on": "cart", "map": "screens", "kind": "pains", "words": "a pain piled on a screen"}]
    monkeypatch.setattr(map_signals, "signals", lambda *a, **k: seen.append((a, k)) or rows)
    got = map_reach.heat(state, repo, "tech")
    assert seen[0][1]["limit"] is None, "every hint: signals' own cut of twenty is not heat's"
    assert [(h["kind"], h["words"]) for h in got["a"]] == [("cycle", "one"), ("fan_in", "two"), ("big", "three")]
    assert got["a"][0] == {"kind": "cycle", "aspect": lens_rubrics.aspect_of("tech", "cycle"), "words": "one"} and got["a"][0]["aspect"] != ""
    assert set(got) == {"a", "b"} and got["b"] == [{"kind": "big", "aspect": lens_rubrics.aspect_of("tech", "big"), "words": "other"}]
    assert "cart" not in got and set(map_reach.heat(state, repo, "product")) == {"a", "b"}, "a hint of another map's part is not drawn here"


def test_heat_names_each_hints_aspect_and_is_empty_for_a_map_with_nothing_to_say(repo, state):
    put(repo, {"core/base.py": "X = 1\n", **{f"user{n}/m.py": "import core.base\n" for n in range(map_signals.FAN_IN)}}, old=True)
    got = map_reach.heat(state, repo, "tech")
    assert got == {"core": [{"kind": "fan_in", "aspect": lens_rubrics.aspect_of("tech", "fan_in"), "words": f"core is used by {map_signals.FAN_IN} parts"}]}
    assert map_reach.heat(state, repo, "game-design") == {} and map_reach.heat(state, repo, "") == {}
    assert map_reach.heat(state, repo / "nowhere", "tech") == {}


def test_heat_is_kept_per_head_and_a_copy_is_the_callers(repo, state, monkeypatch):
    put(repo, {"core/base.py": "X = 1\n", **{f"user{n}/m.py": "import core.base\n" for n in range(map_signals.FAN_IN)}}, old=True)
    reads = []
    real = map_signals.signals
    monkeypatch.setattr(map_signals, "signals", lambda *a, **k: reads.append(a) or real(*a, **k))
    first = map_reach.heat(state, repo, "tech")
    first["core"].clear()
    assert len(map_reach.heat(state, repo, "tech")["core"]) == 1 and len(reads) == 1, "read once for a head, and the caller's change is not the cache's"
    put(repo, {"core/more.py": "Y = 1\n"}, old=True)
    map_reach.heat(state, repo, "tech")
    assert len(reads) == 2, "a new head is a new read"
    for _ in range(3):
        map_reach.heat(state, repo, "game-design")
    assert len(reads) == 5, "the loop's hints read the state too: they are read each time"
    for n in range(map_reach.CACHE_MAX + 2):
        put(repo, {f"x{n}.txt": "x\n"}, old=True)
        map_reach.heat(state, repo, "tech")
    assert len(map_reach._CACHE) <= map_reach.CACHE_MAX


# -- the relation -------------------------------------------------------------------------------------------------------------------

def test_system_a_part_reaches_what_uses_it(repo, state):
    put(repo, CHAIN, old=True)
    rel = map_reach.relation(state, repo, "tech")
    assert rel == {"alpha": ["beta"], "beta": ["gamma"], "gamma": ["delta"]}
    assert map_reach.reach(rel, ["alpha"]) == {"alpha": 0, "beta": 1, "gamma": 2}, "two steps and no further"


def test_screens_a_screen_reaches_the_screens_that_link_to_it(repo, state):
    put(repo, APP)
    rel = map_reach.relation(state, repo, "design")
    assert rel == {"mid": ["home"], "cart": ["home"], "done": ["cart"]}
    assert map_reach.reach(rel, ["done"]) == {"done": 0, "cart": 1, "home": 2}


def test_the_tree_a_job_reaches_its_goals_a_goal_its_job_and_experiments_an_experiment_its_goal(repo, state, pages):
    tree.keep(state, [{"text": "Cut the time to a first sketch to 2 minutes"}],
              [{"when": "I start", "want": w, "so": "judge it", "segment": "founders"} for w in ("see a sketch", "share it", "compare two")], "person")
    job = tree.read(state)["jobs"][0]["id"]
    goal, other, trial = (ideas.add_idea(pages, t, "general", state) for t in ("Fast sketch", "Share link", "Try two sketches"))
    tree.attach(state, job, goal)
    tree.attach(state, job, other)
    tree.test(state, goal, trial)
    rel = map_reach.relation(state, repo, "product", pages)
    assert rel == {job: [goal, other], goal: [job, trial], other: [job], trial: [goal]}
    assert map_reach.reach(rel, [trial]) == {trial: 0, goal: 1, job: 2}
    ideas.drop(pages, other, state)
    assert map_reach.relation(state, repo, "product", pages) == {job: [goal], goal: [job, trial], trial: [goal]}, "a goal the Board dropped is no part"


def test_the_tree_a_hypothesis_reaches_its_job_and_the_goals_that_rest_on_it_or_test_it_and_they_it(repo, state, pages):
    tree.keep(state, [{"text": "Cut the time to a first sketch to 2 minutes"}],
              [{"when": "I start", "want": w, "so": "judge it", "segment": "founders"} for w in ("see a sketch", "share it", "compare two")], "person")
    job = tree.read(state)["jobs"][0]["id"]
    goal, trial = (ideas.add_idea(pages, t, "general", state) for t in ("Fast sketch", "Try two sketches"))
    tree.attach(state, job, goal)
    tree.test(state, goal, trial)
    h = hyp.add(state, "People want a sketch in a minute", "half open it twice", on=job, rests=[goal])
    hyp.attach(state, h["id"], test=trial)
    hid = f"hyp:{h['id']}"
    rel = map_reach.relation(state, repo, "product", pages)
    assert rel == {job: [goal, hid], goal: [job, trial, hid], trial: [goal, hid], hid: [job, goal, trial]}
    assert map_reach.reach(rel, [trial]) == {trial: 0, goal: 1, hid: 1, job: 2}, "a test reaches its hypothesis, and through it the job"
    hyp.attach(state, "", test=trial)
    tree.test(state, "", trial)
    assert hid not in map_reach.relation(state, repo, "product", pages).get(trial, []), "a goal not on the tree is no part: nothing reaches it"


def test_the_loop_a_step_reaches_the_next_the_last_the_first_and_the_currencies_it_gives_and_a_currency_the_steps_that_take_it(repo, state):
    step = lambda name, **more: {"name": name, "line": "A line", "gives": [], "takes": [], **more}                    # noqa: E731
    got = loop.keep(state, repo, {"loops": [{"span": "core", "name": "Fight", "line": "A line", "steps": [step("Hit", gives=["gold"]), step("Dodge"), step("Buy", takes=["gold"])]}],
                                  "currencies": [{"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins"}]}, "person")[0]
    hit, dodge, buy = (s["id"] for s in got["loops"][0]["steps"])
    rel = map_reach.relation(state, repo, "game-design")
    assert rel == {hit: [dodge, "cur:gold"], dodge: [buy], buy: [hit], "cur:gold": [buy]}
    assert map_reach.reach(rel, [hit]) == {hit: 0, dodge: 1, "cur:gold": 1, buy: 2}, "the nearest wins: Buy is two steps by the ring and two by the currency"


def test_art_and_marketing_have_no_relation_and_nor_a_craft_with_no_map(repo, state, pages):
    put(repo, APP)
    for craft in ("art", "marketing", "", "nothing"):
        assert map_reach.relation(state, repo, craft, pages) == {}
    assert map_reach.relation(state, repo / "nowhere", "tech") == {}


def test_reach_has_the_touched_at_nought_a_cycle_does_not_loop_and_the_nearest_wins():
    rel = {"a": ["b", "c"], "b": ["c", "a"], "c": ["d"], "d": ["e"]}
    assert map_reach.reach(rel, ["a"]) == {"a": 0, "b": 1, "c": 1, "d": 2}
    assert map_reach.reach(rel, ["a", "d"]) == {"a": 0, "d": 0, "b": 1, "c": 1, "e": 1}
    assert map_reach.reach(rel, ["lonely"]) == {"lonely": 0} and map_reach.reach({}, []) == {}


# -- Release ------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def waiting(tmp_path: Path) -> Path:
    """main holds the start; dev is cut from it."""
    r = tmp_path / "release"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@x")
    git(r, "config", "user.name", "T")
    (r / ".gitignore").write_text(".orkcraft/\n")
    (r / "a.txt").write_text("a\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "start")
    git(r, "checkout", "-q", "-b", "dev")
    return r


def land(repo: Path, state: Path, slug: str, tid: str, files: dict[str, str]) -> None:
    g = IdeaGit(repo)
    path, branch = g.prepare(slug, tid, "dev")
    for name, text in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
        subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", f"edit {name}"], cwd=path, check=True, capture_output=True)
    sha, subjects, _note = g.land(path, branch, "dev", push=False)
    g.remove(path)
    plan = ideas.plan(state, slug) or {"tasks": []}
    plan["tasks"].append({"id": tid, "title": f"Task {tid}", "state": "merged", "commit": sha, "subjects": subjects})
    folder = ideas.state_folder(state, slug)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.json").write_text(json.dumps(plan))


def test_release_a_goal_reaches_the_goals_the_gate_takes_to_main_with_it(waiting, pages):
    state = waiting / ".orkcraft"
    one, two, three = (ideas.add_idea(pages, t, "general", state) for t in ("Dark mode", "Faster pages", "Own thing"))
    land(waiting, state, one, "k1", {"theme.css": "one\n"})
    land(waiting, state, two, "k1", {"theme.css": "two\n"})                    # on the file the first changed: it goes to main with it
    land(waiting, state, three, "k1", {"other.css": "x\n"})
    assert map_reach.relation(state, waiting, "release", pages) == {two: [one]}
    assert map_reach.relation(state, waiting, "release", pages, only=[three]) == {}
    assert map_reach.relation(state, waiting, "release", pages, only=[two]) == {two: [one]}
    assert map_reach.reach(map_reach.relation(state, waiting, "release", pages, only=[two]), [two]) == {two: 0, one: 1}
    assert map_reach.touched(state, waiting, two, "release", "release", pages) == {"state": "ok", "ids": [two]}, "the goal itself, whatever its sections"
    assert map_reach.touched(state, waiting, "no-such", "release", "release", pages) == {"state": "none", "ids": []}
    quiet = ideas.add_idea(pages, "Not in dev", "general", state)
    assert map_reach.touched(state, waiting, quiet, "release", "release", pages) == {"state": "none", "ids": []}, "a goal that does not wait"


# -- touched ------------------------------------------------------------------------------------------------------------------------

def sectioned(pages: Path, slug: str, **sections: dict) -> None:
    """The goal's page in the new format: a `## <Party>` section for each (`title=parts`)."""
    page = ideas.idea_page(pages, slug)
    spec_sections.arrange(page, {}, [(title, spec_sections.join(parts)) for title, parts in sections.items()])
    ideas._write(pages / ideas.IDEAS / f"{slug}.md", page.text())


def tech_goal(pages: Path, state: Path, will: str | None, title: str = "Rework") -> str:
    """A goal of the Tech party with its section; `will` the *Will be* lines (None: a section with no *Will be*)."""
    tech = ideas.add_track(pages, "Tech") if not any(t["slug"] == "tech" for t in ideas.tracks(pages, make=False)) else "tech"
    slug = ideas.add_idea(pages, title, tech, state)
    sectioned(pages, slug, Tech={"Why": "Because.", "Done when": "- It works", **({"Will be": will} if will is not None else {})})
    return slug


def test_touched_the_party_sections_will_be_matched_to_the_maps_parts_a_file_inside_a_part_is_the_part(repo, state, pages):
    put(repo, {**CHAIN, "README.md": "x\n"}, old=True)
    slug = tech_goal(pages, state, "- changed beta/two.py — the import\n- new omega/five.py\n- gone gamma\n- changed README.md")
    got = map_reach.touched(state, repo, slug, "tech", "tech", pages)
    assert got == {"state": "ok", "ids": ["beta", "gamma"]}, "a file is its part, README.md lies in no part (the map holds the folders of source)"
    assert "omega" not in got["ids"], "a part that is not there yet is no part of the map"


def test_touched_the_top_part_is_only_a_file_at_the_top_or_itself(repo, state, pages):
    put(repo, {**CHAIN, "README.md": "x\n", "setup.py": "import alpha.one\n"}, old=True)
    assert "." in [p["id"] for p in map_parts.parts(state, repo, "tech")]
    assert map_reach.touched(state, repo, tech_goal(pages, state, "- changed README.md"), "tech", "tech", pages) == {"state": "ok", "ids": ["."]}
    assert map_reach.touched(state, repo, tech_goal(pages, state, "- changed alpha/one.py", title="Other"), "tech", "tech", pages) == {"state": "ok", "ids": ["alpha"]}


def test_touched_no_will_when_the_party_has_a_section_and_nothing_matched_and_none_when_it_has_none(repo, state, pages):
    put(repo, CHAIN, old=True)
    assert map_reach.touched(state, repo, tech_goal(pages, state, None), "tech", "tech", pages) == {"state": "no_will", "ids": []}
    assert map_reach.touched(state, repo, tech_goal(pages, state, "- new omega/five.py", title="Later"), "tech", "tech", pages) == {"state": "no_will", "ids": []}
    design = ideas.add_idea(pages, "Look", "general", state)
    ideas.add_track(pages, "Design")
    sectioned(pages, design, Design={"Why": "Because.", "Will be": "- changed alpha"})
    assert map_reach.touched(state, repo, design, "tech", "tech", pages) == {"state": "none", "ids": []}, "another party's Will be is not this tab's"
    plain = ideas.add_idea(pages, "A page of before", "general", state)
    assert map_reach.touched(state, repo, plain, "tech", "tech", pages) == {"state": "none", "ids": []}
    assert map_reach.touched(state, repo, "no-such", "tech", "tech", pages) == {"state": "none", "ids": []}
    assert map_reach.touched(state, repo, plain, "tech", "", pages) == {"state": "none", "ids": []}, "a craft with no map"


def test_touched_a_page_of_before_in_the_party_is_its_one_section_with_no_will_be(repo, state, pages):
    put(repo, CHAIN, old=True)
    tech = ideas.add_track(pages, "Tech")
    old = ideas.add_idea(pages, "Old page", tech, state)
    ideas.set_section(pages, old, "Why", "Because.")
    assert map_reach.touched(state, repo, old, tech, "tech", pages) == {"state": "no_will", "ids": []}


def test_touched_a_mark_on_this_map_counts_with_or_without_a_will_be_and_a_mark_on_another_map_does_not(repo, state, pages):
    put(repo, CHAIN, old=True)
    plain = ideas.add_idea(pages, "From a concern", "general", state)
    ideas.save_state(state, plain, marks=[{"map": "system", "id": "gamma", "name": "gamma"}, {"map": "screens", "id": "alpha", "name": "alpha"}])
    assert map_reach.touched(state, repo, plain, "tech", "tech", pages) == {"state": "ok", "ids": ["gamma"]}
    both = tech_goal(pages, state, "- changed alpha")
    ideas.save_state(state, both, marks=[{"map": "system", "id": "delta", "name": "delta"}, {"map": "system", "id": "gone-part", "name": "x"}])
    assert map_reach.touched(state, repo, both, "tech", "tech", pages) == {"state": "ok", "ids": ["alpha", "delta"]}, "in the map's order, a mark of a part not there left out"


def test_touched_a_mark_on_a_whole_group_is_the_parts_in_it(repo, state, pages):
    put(repo, APP)
    plain = ideas.add_idea(pages, "A step", "general", state)
    ideas.save_state(state, plain, marks=[{"map": "screens", "group": "step:2", "name": "Step 2"}])
    got = map_reach.touched(state, repo, plain, "design", "design", pages)
    assert got["state"] == "ok" and set(got["ids"]) == {"mid", "cart"}


# -- System: guard and links --------------------------------------------------------------------------------------------------------

def test_guard_a_part_is_guarded_when_a_test_is_mapped_to_it(repo, state):
    put(repo, {**CHAIN, "tests/test_two.py": "import beta.two\n"}, old=True)
    assert map_reach.guard(state, repo, ["alpha", "beta", "gamma", "nowhere"]) == {"alpha": False, "beta": True, "gamma": False, "nowhere": False}
    assert map_reach.guard(state, repo, []) == {} and map_reach.guard(state, repo / "nowhere", ["alpha"]) == {"alpha": False}


def test_links_are_the_architectures_whose_two_containers_both_hold_a_reached_part(repo, state):
    put(repo, {"web/package.json": json.dumps({"name": "web", "dependencies": {"react": "18"}}), "web/src/app.js": 'fetch("/api/items");\n',
               "api/package.json": json.dumps({"name": "api", "dependencies": {"express": "4"}}), "api/server.js": 'const app = require("express")();\napp.get("/api/items", (req, res) => res.json([]));\n',
               "docs/notes.md": "x\n"}, old=True)
    ov = project_map.ensure(state, repo, "dev")["overview"]
    assert [[k["from"], k["to"]] for k in ov["links"]] == [["web", "api"]], ov
    parts = [p["path"] for p in project_map.ensure(state, repo, "dev")["parts"]]
    web, api = next(p for p in parts if p.startswith("web")), next(p for p in parts if p.startswith("api"))
    assert map_reach.links(state, repo, [web, api]) == [["web", "api"]]
    assert map_reach.links(state, repo, [web]) == [] and map_reach.links(state, repo, []) == []
    assert map_reach.links(state, repo / "nowhere", [web, api]) == []

