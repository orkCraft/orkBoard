"""Spec 35 §0, §3, §4, §6 on the keeper, the model call stubbed: the draft, one round of answers, the plan at once, its
Stages and risk, the context caps, the window and the keeper's own stop."""
from __future__ import annotations

import datetime as dt
import json
import time

import pytest

from orkboard.core.idea_keeper import IdeaKeeper, KeeperError
from orkboard.realm import event_log, ideas
from orkboard.sources.limits import Limit

STEPS = (("write its spec", "draft"), ("answered the questions", "answer"), ("turn it into a plan", "plan"),
         ("saved a goal", "goal"), ("It is night", "propose"), ("Rewrite only that section", "talk"))
PLAN = {"tasks": [{"id": "a", "title": "The table", "brief": "Add it. Proves: the table shows", "tier": "laborer"},
                  {"id": "b", "title": "The form", "brief": "Add it", "tier": "warrior"},
                  {"id": "c", "title": "The checks", "brief": "Test it", "tier": "elder", "after": ["a"]}]}


class Model:
    """Answers by what it is asked (the step the prompt says); remembers every call; `gate` holds a step's call."""

    def __init__(self, **answers) -> None:
        self.answers, self.asked, self.gate = answers, [], {}

    def __call__(self, tier, prompt, effort="", budget=None):
        step = next((s for k, s in STEPS if k in prompt), "?")
        self.asked.append({"step": step, "tier": tier, "prompt": prompt, "effort": effort, "budget": budget})
        if step in self.gate:
            self.gate[step].wait(5)
        got = self.answers.get(step, {})
        got = got(prompt) if callable(got) else got
        if isinstance(got, Exception):
            raise got
        return json.dumps(got), None, 1000, ""

    def steps(self):
        return [a["step"] for a in self.asked]


@pytest.fixture
def keeper(fake_repo, tmp_path):
    root, state = tmp_path / "wiki", fake_repo / ".orkcraft"
    settings = {"target": "balance", "autostart": True, "night": "01:00-07:00"}
    plans = []
    k = IdeaKeeper(fake_repo, state, lambda: root, lambda: settings, on_plan=plans.append)
    k.root, k.state, k.settings_now, k.plans, k.limits_now = root, state, settings, plans, []
    k.limits = lambda: k.limits_now
    goal = ideas.add_track(root, "Ship the table")
    ideas.write_goal_reading(root, goal, "The table lives in src/app.py.", {}, [],
                             metrics=[{"name": "done when the table shows", "target": "1", "how": "a test"}], links=["src/app.py"])
    k.goal = goal
    return k


def _wait(k, slug, key=""):
    for _ in range(500):
        if not k._busy.get(key or slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _events(k, name):
    return [r for r in event_log.read(k.repo_root) if r["event"] == name]


DRAFT = {"title": "The table", "gist": "A table of runs.\nIt shows each.", "why": "Moves: the table shows",
         "done_when": ["the table shows", "it sorts"], "out": ["no export"],
         "risks": {"product": ["people miss it"], "tech": ["slow lists"]}, "risk": "low", "risk_why": "small",
         "touches": ["src/app.py"], "depends_on": ["nope", "dep-idea"], "size": "M", "before": "", "questions": []}


def test_the_draft_writes_its_sections_and_front_matter_and_drops_unknown_or_cyclic_depends(keeper):
    dep = ideas.add_idea(keeper.root, "dep idea", keeper.goal, keeper.state)
    slug = ideas.add_idea(keeper.root, "a table of runs please", keeper.goal, keeper.state)
    ideas.set_meta(keeper.root, dep, depends_on=json.dumps([slug]))          # dep → slug: slug → dep would close a cycle
    keeper.call = model = Model(draft={**DRAFT, "depends_on": ["nope", dep]}, plan=PLAN)
    keeper.draft_one(slug)
    page = ideas.idea_page(keeper.root, slug)
    assert page.title == "The table" and page.get("size") == "M" and page.get("risk_model") == "low"
    assert json.loads(page.get("touches")) == ["src/app.py"] and json.loads(page.get("depends_on")) == []
    assert ideas.items(page.section("Done when")) == ["the table shows", "it sorts"]
    assert ideas.items(page.section("Out")) == ["no export"] and page.section("Gist").startswith("A table of runs.")
    assert page.section("Risks").startswith("Risk: Low") and "Product:" in page.section("Risks")
    other = ideas.add_idea(keeper.root, "another", keeper.goal, keeper.state)
    keeper.call = Model(draft={**DRAFT, "depends_on": [dep, "nope"]}, plan=PLAN)
    keeper.draft_one(other)
    assert json.loads(ideas.idea_page(keeper.root, other).get("depends_on")) == [dep]
    first = model.asked[0]
    assert first["step"] == "draft" and first["tier"] == "elder" and first["effort"] == "medium" and first["budget"] == 0.6
    assert "The table lives in src/app.py." in first["prompt"] and "a table of runs please" in first["prompt"]


def test_no_question_makes_the_plan_at_once_with_its_stages_and_risk(keeper):
    slug = ideas.add_idea(keeper.root, "a table", keeper.goal, keeper.state)
    keeper.call = model = Model(draft=DRAFT, plan=PLAN)
    keeper.draft_one(slug)
    assert model.steps() == ["draft", "plan"] and keeper.plans == [slug]
    assert ideas.state(keeper.state, slug)["state"] == "plan"
    page = ideas.idea_page(keeper.root, slug)
    assert page.section("Stages") == "1. k1 The table (S) ∥ k2 The form (M)\n2. k3 The checks (L), after k1"
    assert page.get("risk") == "low" and json.loads(page.get("risk_triggers")) == []
    assert ideas.state(keeper.state, slug)["session"] == ""                  # §0: no session kept


def test_questions_go_to_asks_and_one_round_of_answers_writes_the_rest_then_the_plan(keeper):
    slug = ideas.add_idea(keeper.root, "a table", keeper.goal, keeper.state)
    keeper.call = model = Model(draft={**DRAFT, "questions": ["Which columns?", "Sorted how?"]}, plan=PLAN,
                                answer={"sections": {"Done when": "- the five columns show", "Decisions": "no"},
                                        "decisions": ["Five columns"], "assumed": ["newest first"],
                                        "questions": ["Anything else?"]})
    keeper.draft_one(slug)
    assert ideas.state(keeper.state, slug)["state"] == "asks" and model.steps() == ["draft"]
    with pytest.raises(KeeperError, match="at least one"):
        keeper.answer(slug, ["", ""])
    keeper.answer(slug, ["name, date, state, cost, tokens", ""])
    _wait(keeper, slug)
    assert model.steps() == ["draft", "answer", "plan"]
    ask = model.asked[1]["prompt"]
    assert "Which columns?" in ask and "name, date, state, cost, tokens" in ask and "Sorted how?" in ask
    page = ideas.idea_page(keeper.root, slug)
    assert page.section("Open questions") == "" and "the five columns show" in page.section("Done when")
    decisions = page.section("Decisions")
    assert "Which columns? — name, date, state, cost, tokens" in decisions and "Assumed: newest first" in decisions
    assert "Anything else?" not in page.text()                               # a question in its answer is dropped
    assert ideas.state(keeper.state, slug)["state"] == "plan"
    (e,) = _events(keeper, "idea_answered")
    assert e["idea"] == slug and e["answers"] == 1 and e["step"] == "answer" and e["cost"] is None
    assert e["typed"] == 1 and e["picked"] == 0 and e["decided"] is False


def test_a_spent_window_holds_the_call_until_it_is_back_and_refuses_the_persons(keeper):
    slug = ideas.add_idea(keeper.root, "a table", keeper.goal, keeper.state, queue="now")
    reset = dt.datetime.now() + dt.timedelta(hours=1)
    keeper.limits_now = [Limit("claude", "", "session", 0.01, reset)]
    keeper.call = model = Model(draft=DRAFT, plan=PLAN)
    assert keeper.draft(slug) is False and model.asked == []
    st = ideas.state(keeper.state, slug)
    assert st["state"] == "raw" and st["held_until"] == reset.isoformat(timespec="seconds")
    with pytest.raises(KeeperError, match="spent"):
        keeper.read_now(slug)
    with pytest.raises(KeeperError, match="spent"):
        keeper.say(slug, "hello")
    keeper.limits_now = [Limit("claude", "", "session", 0.8, reset)]
    assert keeper.tick(time.time())
    _wait(keeper, slug)
    assert model.steps()[0] == "draft" and ideas.state(keeper.state, slug)["held_until"] == ""


def test_a_draft_names_its_partys_metrics_and_asks_which_it_moves_only_when_the_party_has_some_spec_50(keeper):
    """Spec 50 §2.5: a party has no end; without metrics the draft has no *Its goal's metrics* part and no which-metric question."""
    with_metrics = ideas.add_idea(keeper.root, "a table of runs please", keeper.goal, keeper.state)
    prompt = keeper.draft_prompt(keeper.root, with_metrics)
    assert "Its goal's metrics:\n- done when the table shows → 1 (counted: a test)" in prompt
    assert '"why": "which of its goal\'s metrics it moves, and why it matters"' in prompt
    bare = ideas.add_track(keeper.root, "No metrics")
    ideas.write_goal_reading(keeper.root, bare, "Just a team.", {}, [])
    slug = ideas.add_idea(keeper.root, "a table of runs please", bare, keeper.state)
    prompt = keeper.draft_prompt(keeper.root, slug)
    assert "Its goal's metrics" not in prompt and "which of its goal's metrics" not in prompt
    assert '"why": "why it matters"' in prompt and "Just a team." in prompt and "Its goal's summary" in prompt   # nothing else changes


def test_the_draft_prompt_says_the_goals_type_beside_what_its_lens_pointed_at_spec_52(keeper):
    """Spec 52 §2.5: a goal of a type has one more line, `Its type: <name>. <plan>`; a blank goal's prompt is as before."""
    from orkboard.realm import goal_types
    slug = ideas.add_idea(keeper.root, "the login breaks", keeper.goal, keeper.state)
    before = keeper.draft_prompt(keeper.root, slug)
    assert "Its type:" not in before
    ideas.save_state(keeper.state, slug, type="taskmaster/bug")
    prompt = keeper.draft_prompt(keeper.root, slug)
    line = f"Its type: Fix a bug. {goal_types.get('taskmaster/bug').plan}\n"
    assert line in prompt and prompt.replace(line, "") == before                                    # nothing else changes
    ideas.save_state(keeper.state, slug, type="growth/landing")
    assert "Its type: A landing page.\n" in keeper.draft_prompt(keeper.root, slug)                 # no plan line: the name alone

