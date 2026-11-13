"""The board's keeper (spec 29a §4, spec 35) with the model call stubbed: the draft, the talk (an edit, no session), the plan."""
from __future__ import annotations

import datetime as dt
import json
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_keeper import IdeaKeeper, KeeperError
from orkboard.realm import ideas


class Model:
    """Answers in turn; remembers what it was asked."""

    def __init__(self, *answers) -> None:
        self.answers, self.asked = list(answers), []

    def __call__(self, tier, prompt, effort="", budget=None):       # spec 35 §0: no resume; effort and budget
        self.asked.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget})
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 1000, "sess-1"


@pytest.fixture
def keeper(tmp_path):
    root, state = tmp_path / "wiki", tmp_path / ".orkcraft"
    settings = {"batch_minutes": 30, "idle_hours": 24}
    published = []
    k = IdeaKeeper(tmp_path, state, lambda: root, lambda: settings, published.append)
    k.root, k.state, k.published, k.settings_now = root, state, published, settings
    k._context = lambda session, tokens: int(tokens or 0)
    return k


def _wait(k, slug):
    for _ in range(200):
        if not k.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def test_the_draft_reads_a_raw_idea_on_the_draft_step(keeper):
    # spec 35 §3: the batch on the laborer tier went; a raw idea is drafted (elder · medium on balance), its goal given
    ux = ideas.add_track(keeper.root, "UX")
    slug = ideas.add_idea(keeper.root, "dark mode pls", ux, state_dir=keeper.state)
    keeper.call = model = Model("Sure! ```json\n" + json.dumps(
        {"gist": "Dark mode for the board.\nAt night it glares.", "why": "Moves: calm at night", "size": "m",
         "questions": ["Every screen or the board only?", "Follow the OS?"], "evil": "x"}) + "\n```")
    keeper.draft_one(slug)
    assert model.asked[0]["tier"] == "elder" and "dark mode pls" in model.asked[0]["prompt"]
    assert "index.md" not in model.asked[0]["prompt"]          # spec 35 §0: under a goal, its Summary is the map
    page = ideas.idea_page(keeper.root, slug)
    assert page.section("Gist").startswith("Dark mode for the board.") and page.section("Why") == "Moves: calm at night"
    assert page.get("size") == "M" and page.get("track") == ux
    assert ideas.items(page.section("Open questions")) == ["Every screen or the board only?", "Follow the OS?"]
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "asks" and st["batch_at"]


def test_tick_drafts_no_raw_idea_by_day_and_never_in_the_demo(keeper):
    # spec 35 §3: no 30-minute batch; a raw idea of before the night went is held (spec 99 §3), and one asked for is drafted at once
    slug = ideas.add_idea(keeper.root, "y", state_dir=keeper.state)
    keeper.settings_now["night"] = "00:00-00:01"
    keeper.call = Model()
    noon = dt.datetime.now().replace(hour=12, minute=0).timestamp()
    assert not keeper.tick(noon) and not keeper.tick(noon + 31 * 60)
    assert ideas.state(keeper.state, slug)["state"] == "raw" and keeper.call.asked == []
    keeper.demo = True
    ideas.add_idea(keeper.root, "z", state_dir=keeper.state)
    assert not keeper.tick(noon + 120 * 60)
    with pytest.raises(KeeperError, match="demo"):
        keeper.say(slug, "hi")


def test_the_talk_keeps_one_session_and_writes_only_known_sections(keeper):
    # spec 35 §0: a talk turn is an edit of the one section pointed at, one shot: no session, no earlier turn
    slug = ideas.add_idea(keeper.root, "export csv", state_dir=keeper.state)
    keeper.call = model = Model(
        {"reply": "Big files stream.", "sections": {"Risks": "Big files.\n## not a heading", "Hacked": "no",
                                                   "Decisions": "no", "Gist": "not this section"},
         "decisions": ["Stream rows, never load the file"]},
        {"reply": "Comma it is.", "sections": {}, "decisions": ["Comma"]})
    keeper.say(slug, "What about big files?", "Risks")
    _wait(keeper, slug)
    first = model.asked[0]
    assert first["tier"] == "elder" and "resume" not in first and "What about big files?" in first["prompt"]
    page = ideas.idea_page(keeper.root, slug)
    assert page.section("Risks") == "Big files.\n### not a heading" and page.section("Hacked") == ""
    assert page.section("Gist") == "export csv" and "Stream rows" in page.section("Decisions")
    keeper.say(slug, "Comma.", "Open questions")
    _wait(keeper, slug)
    assert "What about big files?" not in model.asked[1]["prompt"] and "Big files stream." not in model.asked[1]["prompt"]
    assert ideas.state(keeper.state, slug)["state"] == "ready"
    talk = ideas.talk(keeper.state, slug)
    assert [(t["who"], t["text"]) for t in talk] == [("you", "What about big files?"), ("keeper", "Big files stream."),
                                                     ("you", "Comma."), ("keeper", "Comma it is.")]
    assert "talk.jsonl" not in "".join(a["prompt"] for a in model.asked)   # the archive is never read back


def test_the_plan_is_strict_and_estimated(keeper):
    slug = ideas.add_idea(keeper.root, "export csv", state_dir=keeper.state)
    tasks = [{"id": "a", "title": "Writer", "short": "CSV writer", "brief": "Write rows", "tier": "warrior"},
             {"id": "b", "title": "Button", "brief": "Add a button", "tier": "laborer", "after": ["a", "zzz"]},
             {"id": "c", "title": "no brief"},
             {"id": "d", "title": "Hard", "brief": "Think", "tier": "god"}]
    tasks += [{"id": f"x{n}", "title": f"T{n}", "brief": "b", "tier": "elder"} for n in range(10)]
    keeper.call = Model({"tasks": tasks, "todos": [
        {"id": "s", "title": "api key", "kind": "secret", "why": "to call it", "for": ["b"]},
        {"id": "q", "title": "Delimiter", "kind": "choice", "choices": [",", ";"], "for": ["a"]},
        {"id": "z", "title": "bad", "kind": "magic"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    plan = ideas.plan(keeper.state, slug)
    assert ideas.state(keeper.state, slug)["state"] == "plan"
    ids = [t["id"] for t in plan["tasks"]]
    assert ids == [f"k{n}" for n in range(1, 9)]                       # at most 8, renamed
    assert plan["tasks"][1]["after"] == ["k1"] and plan["tasks"][2]["tier"] == "warrior"
    assert [t["short"] for t in plan["tasks"][:2]] == ["CSV writer", "Button"]      # the plan's, else its title's (spec 41 §3)
    assert [t["title"] for t in plan["todos"]] == ["API_KEY", "Delimiter"]
    assert plan["todos"][0] == {"id": "t1", "title": "API_KEY", "kind": "secret", "why": "to call it", "choices": [],
                                "steps": [], "for": ["k2"], "done": False, "value": None}
    assert [t["state"] for t in plan["tasks"][:3]] == ["waiting", "waiting", "ready"]
    tiers = [t["tier"] for t in plan["tasks"]]
    base = sum({"elder": 1.0, "warrior": 0.3, "laborer": 0.05}[t] for t in tiers)
    assert plan["estimate"] == {"tasks": 8, "usd_low": round(base * 0.5, 2), "usd_high": round(base * 1.5, 2)}
    assert plan["passed_at"] is None and plan["idea"] == slug


def test_a_task_that_makes_variants_carries_a_clean_pick_and_the_prompt_says_when_spec_51(keeper):
    """Spec 51 §2.1: a task of the plan may carry `pick` ({n 2–6, kind, ask, target}); a bad one is dropped, a check never has one, a plan
    written before has none; the Taskmaster's prompt says when."""
    slug = ideas.add_idea(keeper.root, "a logo for the app", state_dir=keeper.state)
    good = {"n": 4, "kind": "image", "ask": "  A logo\nfor the app ", "target": "assets/logo.png", "evil": 1}
    keeper.call = Model({"tasks": [
        {"id": "a", "title": "Draw the logo", "brief": "Draw it", "kind": "art", "pick": good},
        {"id": "b", "title": "Name it", "brief": "Three names", "kind": "text", "pick": {**good, "n": 9}},
        {"id": "c", "title": "Wire it", "brief": "Use it", "kind": "code", "after": ["a"], "pick": {**good, "target": "../x.png"}},
        {"id": "d", "title": "Plain", "brief": "No pick"},
        {"id": "e", "title": "Check", "brief": "Look", "kind": idea_keeper.idea_checks.TAGS[0], "pick": good}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    tasks = ideas.plan(keeper.state, slug)["tasks"]
    assert tasks[0]["pick"] == {"n": 4, "kind": "image", "ask": "A logo for the app", "target": "assets/logo.png"}
    assert all("pick" not in t for t in tasks[1:])
    prompt = " ".join(keeper.call.asked[0]["prompt"].split())
    assert ('give it `"pick": {"n": 2 to 6, "kind": "image" | "audio" | "video" | "text", "ask": "<the question, one line>", '
            '"target": "<the repository path the picked one is written to>"}`') in prompt
    assert "only when the spec asks to choose by eye or by ear (a logo, an icon, a sound, a clip, a name or a tagline)" in prompt
    assert "At most one such task per goal at a time; never for code." in prompt


def test_a_plan_with_no_task_goes_back_and_a_passed_plan_is_never_rewritten(keeper):
    slug = ideas.add_idea(keeper.root, "x", state_dir=keeper.state)
    ideas.save_state(keeper.state, slug, state="ready")
    keeper.call = Model({"tasks": []})
    keeper.plan(slug)
    _wait(keeper, slug)
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "ready" and "No plan" in st["error"]
    ideas.save_plan(keeper.state, slug, {"idea": slug, "passed_at": "2026-10-17T10:00:00", "tasks": [], "todos": []})
    with pytest.raises(KeeperError, match="passed"):
        keeper.plan(slug)


# -- spec 36 §1: the ledger line of each keeper call ---------------------------------------------------------

def test_the_night_is_gone_the_clock_runs_only_what_the_limits_held_and_a_night_queue_is_never_drafted(keeper):
    """Spec 99 §3: no night run, refresh or pace on the keeper; `tick` runs again an idea the limits held (`held_until`) and nothing else. The night's
    ladder (spec 168 H3, decisions §283.32, which brings the leaders' proposals back) lives in core/idea_night.py, read by the route's tick, never the keeper's."""
    from orkboard.realm import idea_target
    for name in ("run_night", "night_tick", "pace_tick", "run_pace", "propose_prompt", "tonight", "night_allowed", "week_is_behind", "start_night"):
        assert not hasattr(keeper, name), name
    assert not {"refresh", "propose"} & set(idea_target.STEPS) and not hasattr(idea_target, "PROPOSALS")
    ux = ideas.add_track(keeper.root, "UX")
    older = ideas.add_idea(keeper.root, "an older state said night", ux, state_dir=keeper.state, queue="night")
    plain = ideas.add_idea(keeper.root, "waits, held by nothing", ux, state_dir=keeper.state, queue="hold")
    held = ideas.add_idea(keeper.root, "held by the limits", ux, state_dir=keeper.state, queue="now")
    ideas.save_state(keeper.state, held, held_until="2026-10-19T20:00:00")
    keeper.call = model = Model({"gist": "Held.", "why": "calm", "size": "s", "questions": ["Which one?"]})
    assert keeper.tick(time.time()) is True
    _wait(keeper, held)
    assert len(model.asked) == 1 and "held by the limits" in model.asked[0]["prompt"]
    assert ideas.state(keeper.state, held)["state"] == "asks"
    assert ideas.state(keeper.state, older)["state"] == "raw" and ideas.state(keeper.state, plain)["state"] == "raw"
    assert keeper.at_work() is False


# -- spec 99 §9: the work by steps -------------------------------------------------------------------------------------------------------

def _routed(keeper, text="add a dark mode option", parties=(("Design", "product-designer", ["artist"]), ("Tech", "architect", ["grunt"])), state="ready"):
    """A goal with a route of `parties` ((title, leader, team)): the page in the new format (a section a party, its leader's), the goal in its first step's party, at `state`.
    Returns (the slug, the parties' slugs)."""
    from orkboard.realm import goal_team, library, spec_sections
    slugs = []
    for title, leader, team in parties:
        library.install(keeper.state, [s for s in (*team, leader) if library.get(s) is not None])
        slugs.append(ideas.add_track(keeper.root, title))
        goal_team.set_team(keeper.root, slugs[-1], list(team), leader=leader)
    slug = ideas.add_idea(keeper.root, text, slugs[0], state_dir=keeper.state)
    page = ideas.idea_page(keeper.root, slug)
    heads = [(title, spec_sections.join({"Why": f"{title}'s why.", "Done when": f"- {title} is done", "Checks": f"- {title} checks",
                                         "Will be": f"changed {title.lower()}/part — the {title.lower()} part", "Out": f"- {title}'s out", "Risks": f"- {title}'s risk"}))
             for title, _l, _t in parties]
    spec_sections.arrange(page, {"Asked": text, "Gist": "Dark mode as a setting", "Route": "1. Design\n2. Tech"}, heads)
    ideas._write(keeper.root / ideas.IDEAS / f"{slug}.md", page.text())
    ideas.save_state(keeper.state, slug, state=state, route=[{"party": s, "leader": p[1]} for s, p in zip(slugs, parties)])
    return slug, slugs


def _asked(model, n):
    return " ".join(model.asked[n]["prompt"].split())


def test_the_first_steps_party_plans_its_own_step_from_its_section_whole_and_of_the_others_only_done_when_and_will_be(keeper):
    slug, (design, tech) = _routed(keeper)
    keeper.call = model = Model({"tasks": [{"id": "a", "proves": [1], "title": "Draw the settings screen", "brief": "Draw it", "kind": "design"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    prompt = model.asked[0]["prompt"]
    assert "Your section, Design, whole:" in prompt and "Design's why." in prompt and "Design's risk" in prompt and "changed design/part" in prompt        # its own, whole, its Will be too
    assert "The section Tech of another party: only its Done when and Will be" in prompt
    assert "Tech is done" in prompt and "changed tech/part" in prompt                                                                                  # the contract of the other
    assert "Tech's why." not in prompt and "Tech's out" not in prompt and "Tech's risk" not in prompt and "Tech checks" not in prompt                  # nothing else of it
    assert "step 1 of 2 of the goal's route" in _asked(model, 0) and "Dark mode as a setting" in prompt
    plan = ideas.plan(keeper.state, slug)
    assert ideas.state(keeper.state, slug)["state"] == "plan" and ideas.idea_page(keeper.root, slug).get("track") == design
    (task,) = plan["tasks"]
    assert (task["step"], task["party"], task["section"]) == (1, design, "Design") and task["craft"] == "design" and task["leader"] == "product-designer"
    assert plan["route"] == [{"party": design, "leader": "product-designer"}, {"party": tech, "leader": "architect"}]


def _pass(keeper, slug, **more):
    ideas.edit_plan(keeper.state, slug, lambda p: p.update(passed_at="2026-10-28T10:00:00", passed_by="person", **more))
    ideas.save_state(keeper.state, slug, state="working")


def _merge(keeper, slug, *ids):
    def done(p):
        for t in p["tasks"]:
            if t["id"] in ids:
                t.update(state="merged", commit="c" * 40, subjects=[f"{t['title']} landed"])
    ideas.edit_plan(keeper.state, slug, done)


def test_the_next_steps_party_plans_when_the_first_is_merged_in_dev_and_its_tasks_join_the_passed_plan(keeper):
    from orkboard.realm import idea_route
    slug, (design, tech) = _routed(keeper)
    keeper.call = model = Model({"tasks": [{"id": "a", "proves": [1], "title": "Draw the screen", "brief": "Draw it", "kind": "design"}], "todos": []},
                                {"tasks": [{"id": "a", "proves": [1], "title": "Build the setting", "brief": "Build it", "kind": "code"}, {"id": "b", "title": "Test it", "brief": "Test", "after": ["a"]}],
                                 "todos": [{"id": "x", "title": "Confirm the theme", "kind": "confirm", "for": ["b"]}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    assert keeper.next_step(slug) is None                                                         # the plan is not passed yet
    _pass(keeper, slug)
    assert keeper.next_step(slug) is None and keeper.tick(time.time()) is False                  # its step is not merged
    _merge(keeper, slug, "k1")
    assert keeper.next_step(slug) == {"n": 2, "party": tech, "leader": "architect"}
    assert keeper.tick(time.time() + 100) is True                                                 # the clock has the next step's party plan it
    _wait(keeper, slug)
    st = ideas.state(keeper.state, slug)
    plan = ideas.plan(keeper.state, slug)
    assert st["state"] == "working" and st["error"] == "" and ideas.idea_page(keeper.root, slug).get("track") == tech
    assert [(t["id"], t["step"], t["party"], t["state"]) for t in plan["tasks"]] == [("k1", 1, design, "merged"), ("k2", 2, tech, "ready"), ("k3", 2, tech, "waiting")]
    assert plan["tasks"][2]["after"] == ["k2"] and [(d["id"], d["for"]) for d in plan["todos"]] == [("t1", ["k3"])]       # numbered on
    assert plan["tasks"][1]["craft"] == "tech" and plan["tasks"][1]["leader"] == "architect" and plan["tasks"][1]["section"] == "Tech"
    assert plan["passed_at"] and plan["estimate"]["tasks"] == 3
    prompt = model.asked[1]["prompt"]
    assert "Your section, Tech, whole:" in prompt and "Tech's why." in prompt and "Design is done" in prompt and "Design's why." not in prompt
    assert "Made by the steps before yours (merged in dev)" in prompt and "Draw the screen landed" in prompt and "step 2 of 2 of the goal's route" in _asked(model, 1)
    assert [(s["n"], s["party"]) for s in idea_route.recorded(keeper.state, slug)] == [(1, design), (2, tech)]
    page = ideas.idea_page(keeper.root, slug)
    assert "Plan" in page.parts("Tech") and "Plan" in page.parts("Design")
    assert keeper.next_step(slug) is None                                                         # the last step: nothing follows
    assert keeper.tick(time.time() + 200) is False


# -- spec 153: a task is a whole session ----------------------------------------------------------------------------------------------------------

def _lined(keeper, slug, lines):
    """The first section (Design) of a routed goal given `lines` as its Done when."""
    from orkboard.realm import spec_sections
    page = ideas.idea_page(keeper.root, slug)
    head, text = spec_sections.sections_of(page)[0]
    parts = spec_sections.split(text)
    parts["Done when"] = "\n".join(f"- {x}" for x in lines)
    page.set_section(head, spec_sections.join(parts))
    ideas._write(keeper.root / ideas.IDEAS / f"{slug}.md", page.text())


def test_lines_no_task_proves_are_asked_once_more_and_never_a_third_time_and_what_is_left_is_kept_spec_153_c3(keeper, monkeypatch):
    from orkboard.realm import event_log
    slug, _parties = _routed(keeper)
    _lined(keeper, slug, ["one", "two", "three"])
    seen = []
    monkeypatch.setattr(event_log, "record", lambda root, event, **fields: seen.append((event, fields)))
    keeper.events = True
    first = {"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "design", "proves": [1]}]}
    keeper.call = model = Model(first, {"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "design", "proves": [1, 3]}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    assert len(model.asked) == 2 and model.asked[1]["prompt"].startswith(model.asked[0]["prompt"][:200])
    assert model.asked[1]["prompt"].endswith("\n\nThese Done when lines no task proves: 2. two; 3. three. Give each to a task, or a task of its own.")
    plan = ideas.plan(keeper.state, slug)
    assert plan["unclaimed"] == [2] and plan["tasks"][0]["proves"] == [1, 3]                         # the second answer is the plan; 2 is kept
    assert [(e, f["idea"], f["step"], f["lines"], f["asked_again"]) for e, f in seen if e == event_log.PLAN_UNCLAIMED] == [("plan_unclaimed", slug, 1, ["2"], True)]
    assert ideas.state(keeper.state, slug)["state"] == "plan"                                       # the plan goes on

