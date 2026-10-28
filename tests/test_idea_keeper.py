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


def test_a_broken_answer_leaves_the_idea_new(keeper):
    slug = ideas.add_idea(keeper.root, "x", state_dir=keeper.state)
    keeper.call = Model("no json here")
    keeper.draft_one(slug)
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "raw" and "JSON" in st["error"]
    assert ideas.idea_page(keeper.root, slug).section("Gist") == "x"


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


def test_compaction_after_a_day_or_past_60_percent(keeper):
    # spec 35 §0: the session per idea and its compaction went: there is nothing to compact
    assert not hasattr(keeper, "fresh") and not hasattr(idea_keeper, "WINDOW")


def test_a_failed_turn_is_said_in_the_talk(keeper):
    slug = ideas.add_idea(keeper.root, "x", state_dir=keeper.state)
    keeper.call = Model(RuntimeError("claude: not logged in"))
    keeper.say(slug, "hello")
    _wait(keeper, slug)
    assert "not logged in" in ideas.talk(keeper.state, slug)[-1]["text"]


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


def test_first_json_reads_through_prose():
    assert idea_keeper.first_json('x {bad} y {"a": 1} z') == {"a": 1}
    assert idea_keeper.first_json("[1, 2]") is None and idea_keeper.first_json("") is None


# -- spec 36 §1: the ledger line of each keeper call ---------------------------------------------------------

def test_a_keeper_call_writes_its_line_to_its_ideas_ledger(keeper):
    from orkboard.realm import idea_spend
    ux = ideas.add_track(keeper.root, "UX")
    slug = ideas.add_idea(keeper.root, "dark mode pls", ux, state_dir=keeper.state)
    keeper.call = Model({"gist": "Dark mode.", "why": "calm", "size": "s", "questions": []})
    keeper._claim(slug, "drafting")
    keeper._run(slug, "drafting", lambda: keeper.draft_one(slug), slug)
    (row,) = idea_spend.read(keeper.state / "ideas" / slug / "spend.jsonl")
    assert row["step"] == "draft" and row["role"] == "taskmaster" and row["tool"] == "claude"
    assert row["tier"] == "elder" and row["effort"] == "medium" and row["model"] and row["cost"] == 0.01
    assert set(row["tokens"]) >= {"in", "out", "cache_read", "cache_write"} and row["tokens"]["total"] == 1000
    assert "task" not in row and "round" not in row


def test_an_unpriced_call_writes_null_a_goals_goes_to_the_goal_and_one_of_no_idea_to_the_board(keeper):
    from orkboard.realm import idea_spend
    keeper.call = lambda tier, prompt, effort="", budget=None: ("{}", None, None, "")
    keeper._claim("goal:speed", "goal")
    keeper._run("goal:speed", "goal", lambda: keeper.ask("goal", "read it"), "goal-speed")
    (row,) = idea_spend.read(keeper.state / "goals" / "speed" / "spend.jsonl")
    assert row["step"] == "goal" and row["cost"] is None and row["tokens"]["in"] is None
    keeper.ask("kind", "kind", tools=False)
    (board,) = idea_spend.read(keeper.state / "ideas" / "spend-board.jsonl")
    assert board["step"] == "kind" and board["role"] == "taskmaster"


def test_a_plan_says_the_kinds_no_one_of_its_party_does_and_its_prompt_says_the_goals_type_spec_52(keeper):
    """Spec 52 §2.5, §2.6: after the roles are given, `missing` (kinds the party does not meet, with who would, once each in the
    plan's order); a goal with no team has none; the plan prompt's type line."""
    from orkboard.realm import goal_team, goal_types, library
    party = ideas.add_track(keeper.root, "Brand")
    library.install(keeper.state, ["grunt", "product-designer"])
    goal_team.set_team(keeper.root, party, ["grunt"], leader="product-designer")
    slug = ideas.add_idea(keeper.root, "a logo for the app", party, state_dir=keeper.state)
    ideas.save_state(keeper.state, slug, type="product-designer/logo")
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "art"},
                                   {"id": "b", "title": "Wire", "brief": "Use it", "kind": "code"},
                                   {"id": "c", "title": "Kit", "brief": "Add it", "kind": "uikit"},
                                   {"id": "d", "title": "Again", "brief": "Draw more", "kind": "art"},
                                   {"id": "e", "title": "Flows", "brief": "Write them", "kind": "design"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    plan = ideas.plan(keeper.state, slug)
    assert [t["role"] for t in plan["tasks"]] == ["grunt", "grunt", "grunt", "grunt", "product-designer"]
    assert plan["missing"] == [{"kind": "art", "agent": "artist"}, {"kind": "uikit", "agent": "ui-kit"}]
    assert f"Its type: New logo. {goal_types.get('product-designer/logo').plan}\n" in keeper.call.asked[0]["prompt"]
    bare = ideas.add_idea(keeper.root, "export csv", state_dir=keeper.state)
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "art"}]})
    keeper.plan(bare)
    _wait(keeper, bare)
    assert ideas.plan(keeper.state, bare)["missing"] == [] and "Its type:" not in keeper.call.asked[0]["prompt"]


def test_a_tasks_title_is_asked_short_kept_to_eighty_and_a_longer_one_cut_at_a_word_spec_87(keeper):
    """Spec 87 §3: the prompt asks a title in 60 characters at most, the verb first; `make_plan` keeps one up to 80 as it is and cuts a longer one at
    the last word under 80, with "…" (80 characters at most)."""
    slug = ideas.add_idea(keeper.root, "waves", state_dir=keeper.state)
    keeper.call = model = Model({"tasks": [{"id": "a", "title": "Spawn enemies from the wave director", "brief": "b"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    prompt = " ".join(model.asked[0]["prompt"].split())
    assert "Each task's `title` is a name, 60 characters at most, the verb first (e.g. \"Spawn enemies from the wave director\")" in prompt
    exact = "Write the long title of a task that is exactly eighty characters in all, no more"[:80]
    assert len(exact) == 80
    long = "Spawn the enemies of every wave from the wave director, then count the survivors of each wave after it"
    one_word = "x" * 120
    got = idea_keeper.make_plan("w", {"tasks": [{"title": t, "brief": "b"} for t in ("Short title", exact, long, one_word, "  Two   spaces\nhere ")]})["tasks"]
    titles = [t["title"] for t in got]
    assert titles[0] == "Short title" and titles[1] == exact                                     # up to 80: as it is
    assert titles[2] == "Spawn the enemies of every wave from the wave director, then count the…" and len(titles[2]) <= 80
    assert titles[3] == "x" * 79 + "…"                                                           # no word to cut at
    assert titles[4] == "Two spaces here"
    assert all(len(t) <= 80 for t in titles)
    assert long.startswith(titles[2][:-1])                                                        # a cut, never a rewrite


def test_a_keeper_call_runs_inside_its_steps_bound_and_its_line_says_when_it_read_more_spec_97(keeper, tmp_path):
    """Spec 97 §3: `ask` sets the bound the step's prompt names (`idea_target.READS`); the call's line in the day's log says
    the files it read, the bound and `over` (a stub call that read 3 files on `talk`, bounded at 2)."""
    from orkboard.realm import call_log, idea_target
    folder = tmp_path / "cx"

    def reading(files):
        out = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"r{n}", "name": "Read",
                                                             "input": {"file_path": str(tmp_path / f)}}]}} for n, f in enumerate(files)]
        out.append({"type": "result", "subtype": "success", "result": "{}", "total_cost_usd": 0.01, "session_id": "s"})

        def call(tier, prompt, effort="", budget=None):
            call_log.record(None, "read", "claude", "opus", prompt, "\n".join(json.dumps(e) for e in out), "", 0, 1.0, workdir=tmp_path)
            return "{}", 0.01, 1000, "s"
        return call

    assert idea_target.READS["talk"] == 2 and "kind" in idea_target.READS and "op_prepare" not in idea_target.READS
    with call_log.kept(folder, "board"):
        keeper.call = reading(["a.py", "b.py", "c.py"])
        keeper.ask("talk", "talk")
        keeper.call = reading(["a.py", "b.py"])
        keeper.ask("talk", "talk")
        keeper.call = reading(["a.py", "b.py", "c.py"])
        keeper.ask("op_prepare", "prepare")                                  # a step that names no number: no bound
        keeper.call = reading([])
        keeper.ask("kind", "kind", tools=False)                              # reads no file: a bound of none
    over, within, unbounded, none = call_log.read(folder)
    assert (over["bound"], over["over"], over["reads"]["files"], over["reads"]["paths"]) == (2, True, 3, ["a.py", "b.py", "c.py"])
    assert within["bound"] == 2 and "over" not in within and within["reads"]["files"] == 2
    assert "bound" not in unbounded and "over" not in unbounded and unbounded["reads"]["files"] == 3
    assert none["bound"] == 0 and "over" not in none
    assert call_log._BOUND.get() is None                                    # the bound ends with the call
    keeper.call = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    with pytest.raises(RuntimeError):
        keeper.ask("talk", "talk")
    assert call_log._BOUND.get() is None


def test_the_night_is_gone_the_clock_runs_only_what_the_limits_held_and_a_night_queue_is_never_drafted(keeper):
    """Spec 99 §3: no night run, refresh, proposal or pace; `tick` runs again an idea the limits held (`held_until`) and nothing else."""
    import importlib
    from orkboard.realm import idea_target
    with pytest.raises(ImportError):
        importlib.import_module("orkboard.core.idea_night")
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
    keeper.call = model = Model({"tasks": [{"id": "a", "title": "Draw the settings screen", "brief": "Draw it", "kind": "design"}]})
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


def test_a_page_of_the_new_format_gets_no_flat_stages_and_no_risk_line_but_its_steps_plan_in_its_section_and_its_risk_in_its_front_matter(keeper):
    from orkboard.realm import spec_sections
    slug, _parties = _routed(keeper)
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "design"}, {"id": "b", "title": "Wire", "brief": "Wire it", "after": ["a"]}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    page = ideas.idea_page(keeper.root, slug)
    names = [n for n, _t in page.sections]
    assert "Stages" not in names and "Risks" not in names and names[-2:] == ["Design", "Tech"]
    plan_part = spec_sections.split(page.section("Design"))["Plan"]
    assert plan_part.startswith("1. k1 Draw (M)") and "2. k2 Wire (M), after k1" in plan_part and "Plan" not in spec_sections.split(page.section("Tech"))
    assert page.get("risk") in ("low", "medium", "high") and "risk_triggers" in dict(page.meta)


def test_a_page_of_before_plans_as_it_always_did_flat_stages_and_a_risk_line(keeper):
    slug = ideas.add_idea(keeper.root, "export csv", state_dir=keeper.state)
    ideas.update(keeper.root, slug, {"Gist": "CSV export", "Done when": "- a file", "Out": "- images"})
    keeper.call = model = Model({"tasks": [{"id": "a", "title": "Writer", "brief": "Write rows"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    page = ideas.idea_page(keeper.root, slug)
    assert page.section("Stages").startswith("1. k1 Writer") and page.section("Risks").startswith("Risk:")
    assert "Your section" not in model.asked[0]["prompt"] and "Done when:\n- a file" in model.asked[0]["prompt"]
    plan = ideas.plan(keeper.state, slug)
    assert "route" not in plan and plan["tasks"][0]["step"] == 1 and "section" not in plan["tasks"][0]


def test_a_goal_of_one_step_plans_its_section_and_goes_as_today_with_no_route_in_its_plan(keeper):
    slug, (design,) = _routed(keeper, parties=(("Design", "product-designer", ["artist"]),))
    keeper.call = model = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "design"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    plan = ideas.plan(keeper.state, slug)
    assert ideas.state(keeper.state, slug)["state"] == "plan" and "route" not in plan and plan["tasks"][0]["party"] == design
    assert "step 1 of" not in model.asked[0]["prompt"] and "Your section's Will be names the parts of your map" in model.asked[0]["prompt"]
    assert keeper.next_step(slug) is None and keeper.plan_next(slug) is False


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
    keeper.call = model = Model({"tasks": [{"id": "a", "title": "Draw the screen", "brief": "Draw it", "kind": "design"}], "todos": []},
                                {"tasks": [{"id": "a", "title": "Build the setting", "brief": "Build it", "kind": "code"}, {"id": "b", "title": "Test it", "brief": "Test", "after": ["a"]}],
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


def test_a_next_step_that_cannot_be_planned_puts_the_goal_at_failed_with_why_and_the_clock_does_not_try_again(keeper):
    slug, _parties = _routed(keeper)
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it"}]}, "no json at all")
    keeper.plan(slug)
    _wait(keeper, slug)
    _pass(keeper, slug)
    _merge(keeper, slug, "k1")
    assert keeper.plan_next(slug) is True
    _wait(keeper, slug)
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "failed" and st["error"].startswith("No plan for the next step:") and len(ideas.plan(keeper.state, slug)["tasks"]) == 1
    assert keeper.tick(time.time() + 100) is False and keeper.plan_next(slug) is False


def test_the_clock_plans_no_next_step_while_the_keeper_is_busy_or_the_demo_runs(keeper):
    slug, _parties = _routed(keeper)
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    _pass(keeper, slug)
    _merge(keeper, slug, "k1")
    keeper.demo = True
    assert keeper.plan_next(slug) is False and keeper.tick(time.time() + 100) is False
    keeper.demo = False
    keeper._busy[slug] = "planning"
    assert keeper.plan_next(slug) is False
    keeper._busy.pop(slug)
    assert keeper.next_step(slug) is not None


def test_a_step_whose_tasks_were_all_dropped_landed_nothing_and_no_step_follows(keeper):
    slug, _parties = _routed(keeper)
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    _pass(keeper, slug)
    ideas.edit_plan(keeper.state, slug, lambda p: p["tasks"][0].update(state="dropped"))
    assert keeper.next_step(slug) is None


def test_the_plan_a_leader_makes_for_its_step_is_stamped_so_its_tasks_wear_its_partys_race(keeper):
    from orkboard.realm import roles
    slug, (design, tech) = _routed(keeper)
    keeper.call = Model({"tasks": [{"id": "a", "title": "Draw", "brief": "Draw it", "kind": "design"}]}, {"tasks": [{"id": "a", "title": "Build", "brief": "Build it", "kind": "code"}]})
    keeper.plan(slug)
    _wait(keeper, slug)
    _pass(keeper, slug)
    _merge(keeper, slug, "k1")
    keeper.plan_next(slug)
    _wait(keeper, slug)
    first, second = ideas.plan(keeper.state, slug)["tasks"]
    heads = [roles.task_head(keeper.state, t, "balance") for t in (first, second)]
    assert [h["race"] for h in heads] == ["dryad", "peon"]          # Design's task is its leader's (no builder takes a design tag): its higher form; Tech's a Grunt's: an ork
    assert roles.task_head(keeper.state, {**second, "role": "architect"}, "balance")["race"] == "shaman"      # its leader's higher form
    assert roles.task_head(keeper.state, {k: v for k, v in second.items() if k not in ("craft", "leader")}, "balance")["race"] == "peon"
