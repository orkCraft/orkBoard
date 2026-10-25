"""Spec 85 §1 and §2 (docs/specs/85-the-elf-asks-and-shows.md), the model call stubbed: a visual goal's draft is asked of its look by the
party's design member, a code goal's is not, never more than three questions in all; a screen's plan begins with the look's pick."""
from __future__ import annotations

import json

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_keeper import IdeaKeeper
from orkboard.realm import board_map, goal_team, idea_look, idea_pick, idea_questions, ideas, library, roles
from tests.test_idea_draft import DRAFT, PLAN, Model

LOOK = [{"ask": "What mood?", "choices": ["Calm", "Loud", "Playful"], "pick": 0, "why": "the product is a tool"},
        {"ask": "Which palette?", "choices": ["Dark", "Light"], "pick": 0},
        {"ask": "Any references?", "choices": ["pictures you like", "None", "Links"], "pick": 1}]
OWN = [{"ask": "Which columns?", "choices": ["All five", "Name and state"], "pick": 0},
       {"ask": "Sorted how?", "choices": ["Newest", "By name"], "pick": 0},
       {"ask": "Keep old rows?", "choices": ["Yes", "No"], "pick": 0}]


@pytest.fixture
def keeper(fake_repo, tmp_path):
    root, state = tmp_path / "wiki", fake_repo / ".orkcraft"
    settings = {"target": "balance", "autostart": True, "night": "01:00-07:00"}
    k = IdeaKeeper(fake_repo, state, lambda: root, lambda: settings, on_plan=lambda slug: None)
    k.root, k.state = root, state
    k.limits = lambda: []
    return k


def _party(keeper, team=(), leader="taskmaster", title="Ship"):
    slug = ideas.add_track(keeper.root, title)
    library.install(keeper.state, [s for s in (*team, leader) if library.get(s) is not None])
    goal_team.set_team(keeper.root, slug, list(team), leader=leader)
    return slug


def _goal(keeper, party, kind="", text="a table of runs"):
    slug = ideas.add_idea(keeper.root, text, party, keeper.state)
    if kind:
        ideas.save_state(keeper.state, slug, type=kind)
    return slug


def _asked(keeper, slug):
    return [idea_questions.parse(q) for q in ideas.items(ideas.idea_page(keeper.root, slug).section("Open questions"))]


# -- which goals are visual ------------------------------------------------------------------------------------------

def test_a_goal_is_visual_by_its_type_or_when_it_has_none_by_a_design_seat_and_a_code_type_never_is(keeper):
    elf, code = _party(keeper, ["product-designer"], title="Design"), _party(keeper, [], title="Code")
    for kind in idea_look.VISUAL:
        assert idea_look.visual(keeper.state, keeper.root, _goal(keeper, code, kind)), kind
    for kind in ("feature", "bug", "tidy", "balance", "sound", "tagline", "metric"):
        assert not idea_look.visual(keeper.state, keeper.root, _goal(keeper, elf, kind)), kind       # a type of code or words: no look, whoever is in the party
    assert idea_look.visual(keeper.state, keeper.root, _goal(keeper, elf))                         # no type, and an elf sits in the party
    assert not idea_look.visual(keeper.state, keeper.root, _goal(keeper, code))                    # no type, no elf


def test_the_look_is_asked_by_the_design_member_else_the_leader(keeper):
    elf = _party(keeper, ["grunt", "product-designer"], title="Design")
    assert idea_look.asker(keeper.state, keeper.root, _goal(keeper, elf, "screen")) == "product-designer"
    game = _party(keeper, [], leader="game-designer", title="Game")                                # a leader of design craft asks itself
    assert idea_look.asker(keeper.state, keeper.root, _goal(keeper, game, "level")) == "game-designer"
    plain = _party(keeper, [], title="Plain")
    assert idea_look.asker(keeper.state, keeper.root, _goal(keeper, plain, "logo")) == "taskmaster"


# -- the draft ------------------------------------------------------------------------------------------------------

def test_a_visual_goals_draft_asks_for_the_look_and_its_questions_are_the_elfs_the_look_first_three_in_all(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "screen", "a runs screen")
    keeper.call = model = Model(draft={**DRAFT, "look": LOOK, "questions": OWN}, plan=PLAN)
    keeper.draft_one(slug)
    prompt = model.asked[0]["prompt"]
    assert '"look": [' in prompt and "LOOK" in prompt and "Product designer" in prompt and f'exactly "{idea_look.PICTURES}"' in prompt
    got = _asked(keeper, slug)
    assert [q["ask"] for q in got] == ["What mood?", "Which palette?", "Any references?"]            # three in all: the look's, the leader's cut
    assert got[2]["choices"] == [idea_look.PICTURES, "None", "Links"] and got[0]["pick"] == 0 and got[0]["why"]
    assert ideas.state(keeper.state, slug)["asks_by"] == ["product-designer"] * 3 and ideas.state(keeper.state, slug)["state"] == "asks"


def test_the_leaders_questions_fill_what_the_look_leaves_and_say_the_leader_asks_them(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "landing")
    keeper.call = Model(draft={**DRAFT, "look": LOOK[:1], "questions": OWN}, plan=PLAN)
    keeper.draft_one(slug)
    assert [q["ask"] for q in _asked(keeper, slug)] == ["What mood?", "Which columns?", "Sorted how?"]
    assert ideas.state(keeper.state, slug)["asks_by"] == ["product-designer", "", ""]


def test_a_code_goal_is_not_asked_its_look_even_if_the_model_gives_one_and_keeps_its_three(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "feature")
    keeper.call = model = Model(draft={**DRAFT, "look": LOOK, "questions": OWN}, plan=PLAN)
    keeper.draft_one(slug)
    assert '"look"' not in model.asked[0]["prompt"] and "LOOK" not in model.asked[0]["prompt"]
    assert [q["ask"] for q in _asked(keeper, slug)] == ["Which columns?", "Sorted how?", "Keep old rows?"]
    assert ideas.state(keeper.state, slug)["asks_by"] == ["", "", ""]


def test_a_visual_goal_with_no_look_to_ask_asks_nothing_and_goes_to_its_plan(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "icon")
    keeper.call = model = Model(draft={**DRAFT, "look": [], "questions": []}, plan=PLAN)
    keeper.draft_one(slug)
    assert model.steps() == ["draft", "plan"] and ideas.state(keeper.state, slug)["asks_by"] == []


def test_the_map_names_the_elf_as_the_asker_of_the_look_and_the_leader_of_the_rest(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "screen")
    keeper.call = Model(draft={**DRAFT, "look": LOOK[:2], "questions": OWN[:1]}, plan=PLAN)
    keeper.draft_one(slug)
    got = board_map.build(keeper.root, keeper.state)
    (node,) = [n for n in got["nodes"] if n["slug"] == slug]
    assert [(q["ask"], q["by"]["slug"]) for q in node["asked"]] == [
        ("What mood?", "product-designer"), ("Which palette?", "product-designer"), ("Which columns?", "taskmaster")]
    assert node["asked"][0]["by"]["head"]["craft"] == "design"
    assert [q["look"] for q in node["asked"]] == [True, True, False]


def test_the_answer_clears_who_asked_and_a_picture_given_with_it_is_read_by_the_keeper(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "screen")
    keeper.call = model = Model(draft={**DRAFT, "look": LOOK, "questions": []}, plan=PLAN,
                                answer={"sections": {}, "decisions": [], "assumed": []})
    keeper.draft_one(slug)
    from orkboard.realm import idea_photos
    idea_photos.put(keeper.state, slug, b"\xff\xd8\xff\xe0" + bytes(20))
    keeper.answer(slug, ["Calm", "Dark", idea_look.PICTURES])
    for _ in range(500):
        if not keeper._busy.get(slug):
            break
        import time
        time.sleep(0.01)
    prompt = next(a["prompt"] for a in model.asked if a["step"] == "answer")
    assert "attached photos" in prompt and ".orkcraft/ideas/" in prompt and idea_look.PICTURES in prompt
    assert ideas.state(keeper.state, slug)["asks_by"] == [] and ideas.state(keeper.state, slug)["asks_look"] == 0


# -- the question's words --------------------------------------------------------------------------------------------

def test_pictures_you_like_is_one_answer_that_takes_pictures_and_is_told_by_its_words():
    out, by, looks = idea_look.questions({"look": LOOK}, 3, True, "elf", "lead")
    assert [idea_look.takes_pictures(x) for x in out] == [False, False, True] and by == ["elf"] * 3 and looks == 3


def test_the_look_is_at_most_three_and_never_over_the_limit_in_all():
    many = LOOK + [{"ask": "A fourth?", "choices": ["a", "b"], "pick": 0}]
    out, by, looks = idea_look.questions({"look": many, "questions": OWN}, 3, True, "elf", "lead")
    assert len(out) == 3 and by == ["elf"] * 3 and looks == 3
    out, by, looks = idea_look.questions({"look": many, "questions": OWN}, 2, True, "elf", "lead")
    assert len(out) == 2 and looks == 2
    out, by, looks = idea_look.questions({"look": many, "questions": OWN}, 3, False, "elf", "lead")
    assert len(out) == 3 and by == ["lead"] * 3 and "mood" not in out[0] and looks == 0


# -- a screen's look is picked first -----------------------------------------------------------------------------------

BUILD = {"tasks": [{"id": "a", "title": "The screen", "brief": "Build it", "tier": "warrior"},
                   {"id": "b", "title": "Its tests", "brief": "Test it", "tier": "laborer", "after": ["a"]}]}


def test_a_screens_plan_begins_with_one_pick_of_its_look_and_every_other_task_comes_after_it():
    plan = idea_keeper.make_plan("runs", BUILD, look="A runs screen")
    first, *rest = plan["tasks"]
    assert first["id"] == "k1" and first["kind"] == "design" and first["after"] == [] and first["state"] == "ready"
    assert first["pick"] == {"n": 3, "kind": "image", "ask": "Which look should the screen have?", "target": "design/looks/runs", "look": True}
    assert "A runs screen" in first["brief"] and "Change no code" in first["brief"]
    assert [(t["id"], t["after"]) for t in rest] == [("k2", ["k1"]), ("k3", ["k1", "k2"])]
    assert all(t["state"] == "waiting" for t in rest) and plan["estimate"]["tasks"] == 3
    assert idea_pick.ask_of(first)["look"] is True


def test_a_plan_of_a_model_that_made_its_own_pick_or_of_another_goal_is_as_it_was():
    own = {"tasks": [{"id": "a", "title": "Logo", "brief": "Draw", "kind": "art",
                      "pick": {"n": 4, "kind": "image", "ask": "A logo", "target": "assets/logo.png"}}, BUILD["tasks"][0]]}
    plan = idea_keeper.make_plan("runs", own, look="A runs screen")
    assert [t["id"] for t in plan["tasks"]] == ["k1", "k2"] and "look" not in plan["tasks"][0]["pick"]
    plain = idea_keeper.make_plan("runs", BUILD)
    assert [t["id"] for t in plain["tasks"]] == ["k1", "k2"] and all("pick" not in t for t in plain["tasks"])


def test_the_pick_takes_a_task_of_the_eight_and_the_rest_are_cut():
    big = {"tasks": [{"id": f"t{n}", "title": f"Task {n}", "brief": "Do it"} for n in range(10)]}
    plan = idea_keeper.make_plan("runs", big, look="A screen")
    assert len(plan["tasks"]) == idea_keeper.MAX_TASKS and plan["tasks"][0]["pick"]["look"] is True


@pytest.mark.parametrize("kind, screens", [("screen", True), ("flow-feature", True), ("landing", True), ("icon", False), ("logo", False),
                                            ("level", False), ("character", False), ("feature", False), ("", False)])
def test_only_a_screen_a_flow_or_a_landing_has_its_look_picked_first(keeper, kind, screens):
    slug = _goal(keeper, _party(keeper, ["product-designer"], title="Design"), kind)
    assert idea_look.screens(keeper.state, slug) is screens
    assert bool(idea_look.screen_title(keeper.state, keeper.root, slug)) is screens


def test_the_plan_of_a_screen_is_made_with_the_pick_first_and_told_in_the_prompt(keeper):
    party = _party(keeper, ["product-designer"], title="Design")
    slug = _goal(keeper, party, "screen", "a runs screen")
    keeper.call = model = Model(draft={**DRAFT, "look": [], "questions": []}, plan=PLAN)
    keeper.draft_one(slug)
    ask = next(a["prompt"] for a in model.asked if a["step"] == "plan")
    assert "Pick a look" in ask and "design/looks/" in ask
    tasks = ideas.plan(keeper.state, slug)["tasks"]
    assert tasks[0]["pick"]["look"] is True and tasks[0]["kind"] == "design" and all(t["after"] and "k1" in t["after"] for t in tasks[1:])
    assert roles.role(keeper.state, tasks[0].get("role") or "product-designer") is not None
    json.dumps(tasks)


# -- a task names the screen it changes (§3) ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("value, kept", [("/settings", "/settings"), ("/", "/"), ("/a/b?x=1#top", "/a/b?x=1#top"), ("settings", ""), ("/../etc/passwd", ""),
                                         ("http://x/y", ""), ("/a b", ""), (None, ""), (7, ""), ("/" + "a" * 300, "")])
def test_a_screen_a_task_names_is_a_path_of_the_preview_or_nothing(value, kept):
    assert idea_look.clean_screen(value) == kept


def test_a_plan_keeps_the_screen_a_task_names_and_a_visual_goals_prompt_says_it_may(keeper):
    plan = idea_keeper.make_plan("runs", {"tasks": [{"id": "a", "title": "The screen", "brief": "Build it", "screen": "/runs"},
                                                    {"id": "b", "title": "Tests", "brief": "Test it", "screen": "javascript:1"}]})
    assert plan["tasks"][0]["screen"] == "/runs" and "screen" not in plan["tasks"][1]
    party = _party(keeper, ["product-designer"], title="Design")
    visual, code = _goal(keeper, party, "icon"), _goal(keeper, party, "feature")
    assert '"screen": "/settings"' in idea_look.instruction(keeper.state, keeper.root, visual) and "Pick a look" not in idea_look.instruction(keeper.state, keeper.root, visual)
    assert idea_look.instruction(keeper.state, keeper.root, code) == ""
    assert "Pick a look" in idea_look.instruction(keeper.state, keeper.root, _goal(keeper, party, "landing"))
