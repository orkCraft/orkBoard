"""Spec 71 A (docs/specs/71-orkmaster-keeps-parties-apart.md §2–§5, Tests → A, the judge): the finder runs when a plan is made and a spec
changes, the judge (the keeper's model call stubbed) only when it found an overlap, as the Orkmaster on the cheaper tier; `false` is kept and
never asked again, `true` is a stop; each answer; a spec change judged and *Re-plan it*; a wait across parties held and then started at the
flag; the events hold no goal's words; no model, no broken plan."""
from __future__ import annotations

import json
import types

import pytest

from orkboard.core import idea_collide
from orkboard.gui.board_host import CommandError
from orkboard.realm import collide, event_log, idea_change, ideas, orkmaster, roles
from tests.test_collide import EARLY, LATE, node, planned, stop_of, two  # noqa: F401
from tests.test_idea_route import events, flag, goal, host  # noqa: F401  (`host`: the fixture of spec 68's route tests)

MARK = "Two goals of different parties"


class Judge:
    """The keeper's model call: answers a collision's prompt with `answer` (a dict, text, an Exception, or a callable of the prompt); any other
    call gets an empty goal. Remembers the calls the judge made, with the thread's tools and the role it spoke as."""

    def __init__(self, keeper, answer=None) -> None:
        self.keeper, self.answer, self.asked = keeper, answer, []

    def __call__(self, tier, prompt, effort="", budget=None):
        if MARK not in prompt:
            return json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, ""
        tls = self.keeper._tls
        self.asked.append({"tier": tier, "effort": effort, "budget": budget, "prompt": prompt, "tools": getattr(tls, "tools", None),
                           "as": getattr(tls, "as_role", "")})
        got = self.answer(prompt) if callable(self.answer) else self.answer
        if isinstance(got, Exception):
            raise got
        return (got if isinstance(got, str) else json.dumps(got)), 0.02, 120, ""


def judged(h, answer, **kw):
    h.model = Judge(h.ideas.keeper, answer)
    h.ideas.keeper.call = h.model
    return h.model


YES = {"collide": True, "why": "Both change how a session token is issued", "first": ""}


def run(h, slug, by="plan", words=""):
    h.ideas.collide_run(slug, by, words)
    h.ideas.collide_join()                                      # (the bus may have started another finder on a goal: let it end)


def found(h):
    return events(h, "collide_found")


# -- §2.1: no overlap, no call ---------------------------------------------------------------------------------------------

def test_a_plan_with_no_overlap_costs_nothing_and_asks_no_model(host):
    h = host
    model = judged(h, YES)
    a = planned(h, h.web, "Docs site", ["site/"])
    planned(h, h.app, "Sign-in screen", ["app/screens/"])
    run(h, a)
    assert model.asked == [] and found(h) == [] and collide.read(h.state) == {"open": [], "answered": []}
    assert roles.role(h.state, "orkmaster") is None            # the Orkmaster is not even installed


# -- §2.2: the judge ---------------------------------------------------------------------------------------------------------

def test_an_overlap_is_judged_as_the_orkmaster_on_the_cheaper_tier_with_the_two_goals_and_their_touches(two):
    h = two
    model = judged(h, YES)
    run(h, h.api)
    assert len(model.asked) == 1
    call = model.asked[0]
    assert (call["tier"], call["effort"], call["tools"], call["as"]) == ("warrior", "low", False, "orkmaster")         # the Target's `collide` step: balance
    assert call["prompt"].startswith("You are the Orkmaster of this project.") and "invent nothing" in call["prompt"]
    for text in ("Auth API", "Sign-in screen", "a token is issued once", "the screen asks for a token", "orkboard/realm/auth.py", "app/screens/signin.js"):
        assert text in call["prompt"]
    assert call["budget"] == 0.05 and len(call["prompt"].split(MARK)[1]) <= 3_000 + 600           # the goals' part is at most 3 000 characters
    r = roles.role(h.state, "orkmaster")                                                          # installed as a role of the project
    assert (r["name"], r["model"], r["takes"], r["builtin"]) == ("Orkmaster", "warrior", [], False)
    assert orkmaster.role(h.state) == r and "orkmaster" not in roles.kinds(h.state).values()      # it takes no task
    h.ideas.keeper.settings = lambda: {"target": "thrift"}
    run(h, h.screen, "plan")                                                                      # (the pair is asked already: no second call)
    assert len(model.asked) == 1
    ideas.set_meta(h.root, h.api, touches=json.dumps(["orkboard/realm/auth.py", "orkboard/realm/new.py"]))
    collide.read(h.state)
    collide.take_open(h.state, collide.pair_id(h.api, h.screen))
    run(h, h.api)
    assert (model.asked[-1]["tier"], model.asked[-1]["effort"]) == ("laborer", "")                 # thrift: the laborer, no effort


def test_a_judged_text_is_cut_to_three_thousand_characters_and_the_answer_is_read_strictly(two):
    h = two
    ideas.set_section(h.root, h.api, "Done when", "- " + "very long " * 900)
    ideas.set_meta(h.root, h.api, touches=json.dumps([f"orkboard/realm/auth.py"] + [f"orkboard/realm/mod{n}_with_a_long_name.py" for n in range(60)]))
    model = judged(h, {"collide": True, "why": "w" * 500, "first": "somebody-else"})
    run(h, h.api)
    assert len(model.asked[0]["prompt"].split(MARK)[1].split("Answer with one JSON")[0]) <= 3_000 + 300
    stop = collide.read(h.state)["open"][0]
    assert len(stop["why"]) == 200 and stop["first"] == ""                                          # a `first` that is neither goal is no suggestion
    for bad in ("not json", {"collide": "yes", "why": "x"}, {"why": "x"}):
        with pytest.raises(ValueError):
            idea_collide.read_answer(bad if isinstance(bad, str) else json.dumps(bad), "a", "b")
    assert idea_collide.read_answer('Sure: {"collide": false, "why": " a  b ", "first": "b"}', "a", "b") == {"collide": False, "why": "a b", "first": "b"}


def test_false_is_kept_and_never_asked_again_and_true_is_a_stop_with_the_judges_first(two):
    h = two
    model = judged(h, {"collide": False, "why": "They sit in one folder", "first": ""})
    run(h, h.api)
    pair = collide.pair_id(h.api, h.screen)
    assert collide.read(h.state) == {"open": [], "answered": [{"id": pair, "by": "plan", "answer": "no", "at": collide.read(h.state)["answered"][0]["at"]}]}
    assert [(r["pair"], r["by"], r["judged"], r["collide"]) for r in found(h)] == [(pair, "plan", True, False)]
    run(h, h.api)
    run(h, h.screen)
    assert len(model.asked) == 1 and len(found(h)) == 1                                              # a pair answered is never asked again
    assert [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"] == []
    other = planned(h, h.web, "Auth cache", ["orkboard/realm/auth.py"], "2026-10-24T11:00:00")       # a third goal: its own pair
    judged(h, {"collide": True, "why": "Both change the token", "first": h.api})
    run(h, other)
    opened = collide.read(h.state)["open"]
    assert sorted(s["id"] for s in opened) == sorted([collide.pair_id(h.screen, other)]) and opened[0]["asked"] == other.__class__(collide.later_of(h.state, other, h.screen)) \
        and opened[0]["by"] == "plan"
    rows = [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"]
    assert len(rows) == 1 and rows[0]["collide"]["first"] == ""                                      # `first` was neither of this pair: no suggestion


def test_a_true_answer_is_a_stop_on_the_later_goal_and_the_events_hold_no_goals_words(two):
    h = two
    judged(h, {"collide": True, "why": "Both change how a session token is issued", "first": h.api})
    run(h, h.api)
    stop = collide.read(h.state)["open"][0]
    assert (stop["asked"], stop["other"], stop["by"], stop["first"]) == (h.screen, h.api, "plan", h.api)
    row = next(n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide")
    assert row["idea"] == h.screen and row["collide"]["first"] == h.api and row["collide"]["goals"][0]["idea"] == h.api
    got = found(h)
    assert len(got) == 1 and (got[0]["by"], got[0]["judged"], got[0]["collide"], got[0]["cost"]) == ("plan", True, True, 0.02) and got[0]["tokens"] == {"total": 120}
    h.command("ideas.collide_answer", {"id": stop["id"], "answer": "leave", "device": "phone"})
    answered = events(h, "collide_answered")
    assert [(r["pair"], r["answer"], r["device"]) for r in answered] == [(stop["id"], "leave", "phone")]
    log = (h.ideas.host.repo_root / event_log.PATH).read_text(encoding="utf-8")
    for words in ("Auth API", "Sign-in screen", "session token", "a token is issued", "both change"):
        assert words.lower() not in log.lower().replace(h.api, "").replace(h.screen, "")


def test_the_hook_at_a_plan_made_finds_and_judges_in_the_background(two):
    h = two
    model = judged(h, YES)
    ideas.save_state(h.state, h.screen, state="ready")
    h.ideas._seen.pop(h.screen, None)
    ideas.save_state(h.state, h.screen, state="plan")
    h.ideas._state_event(h.screen)                                                                    # the keeper reached `plan`: plan_made
    h.ideas.collide_join()
    assert len(model.asked) == 1 and len(events(h, "plan_made")) == 1 and collide.read(h.state)["open"][0]["id"] == collide.pair_id(h.api, h.screen)
    h.ideas._state_event(h.screen)                                                                    # nothing new: no second call
    h.ideas.collide_join()
    assert len(model.asked) == 1


# -- no model: the plan goes on ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("answer", [RuntimeError("no claude on this machine"), "no json at all", {"collide": "maybe"}])
def test_a_judge_that_cannot_answer_never_breaks_a_plan_and_the_pair_is_asked_again_next_time(two, answer):
    h = two
    judged(h, answer)
    before = ideas.plan(h.state, h.screen)
    run(h, h.screen)
    assert collide.read(h.state) == {"open": [], "answered": []} and ideas.plan(h.state, h.screen) == before
    assert ideas.state(h.state, h.screen)["state"] == "plan"
    assert [(r["judged"], r["collide"], r["cost"]) for r in found(h)] == [(False, False, None)]
    model = judged(h, YES)
    run(h, h.screen)
    assert len(model.asked) == 1 and len(collide.read(h.state)["open"]) == 1


def test_the_demo_and_a_spent_budget_ask_no_model(two):
    h = two
    model = judged(h, YES)
    h.ideas.keeper.budget_ok = lambda: False
    run(h, h.screen)
    assert model.asked == [] and collide.read(h.state)["open"] == []
    h.ideas.keeper.budget_ok = lambda: True
    h.ideas.host.demo = True
    h.ideas._collide_spawn(h.screen, "plan", "")
    h.ideas.collide_join()
    assert model.asked == []


# -- §2.3: the answers ---------------------------------------------------------------------------------------------------------

def test_first_makes_the_other_goal_wait_for_it_held_until_its_flag_then_started_at_the_flag(two, monkeypatch):
    h = two
    judged(h, YES)
    run(h, h.api)
    pair = collide.pair_id(h.api, h.screen)
    started = []
    monkeypatch.setattr(h.ideas, "pass_plan", lambda slug, by, night=False, args=None: started.append(slug))
    ideas.set_meta(h.root, h.screen, risk="low")
    assert h.command("ideas.collide_answer", {"id": pair, "answer": f"first:{h.api}"}) == {"ok": True}
    assert json.loads(ideas.idea_page(h.root, h.screen).get("depends_on")) == [h.api]                # the other goal's depends_on gains it
    assert collide.holds(h.root, h.state, h.screen) == [h.api] and started == []                      # held
    assert node(h, h.screen)["waits_for"] == [{"goal": h.api, "party": h.web, "party_name": "Website", "title": "Auth API", "flag": ""}]
    assert collide.read(h.state)["answered"][-1]["answer"] == f"first:{h.api}" and collide.open_of(h.state, pair) is None
    h.ideas._raise_flag(h.api, "done")
    assert started == [h.screen]                                                                      # started at the flag
    assert [(r["pair"], r["answer"]) for r in events(h, "collide_answered")] == [(pair, f"first:{h.api}")]


def test_first_the_later_goal_makes_the_earlier_wait_and_a_wait_that_closes_a_cycle_is_refused(two):
    h = two
    judged(h, YES)
    run(h, h.api)
    pair = collide.pair_id(h.api, h.screen)
    ideas.set_meta(h.root, h.api, depends_on=json.dumps([h.screen]))                                  # Auth API waits for the screen already
    with pytest.raises(CommandError, match="waits for"):
        h.command("ideas.collide_answer", {"id": pair, "answer": f"first:{h.api}"})                   # …so the screen cannot wait for it
    assert collide.open_of(h.state, pair) is not None                                                  # it waits as it did
    h.command("ideas.collide_answer", {"id": pair, "answer": f"first:{h.screen}"})                    # …but Auth API may wait for the screen (it does)
    assert json.loads(ideas.idea_page(h.root, h.api).get("depends_on")) == [h.screen]


def test_one_goal_joins_the_later_text_into_the_earlier_as_a_change_and_drops_the_later(two):
    h = two
    judged(h, YES)
    run(h, h.api)
    pair = collide.pair_id(h.api, h.screen)
    ideas.set_section(h.root, h.screen, "Gist", "**The screen asks for a token.**")
    assert h.command("ideas.collide_answer", {"id": pair, "answer": "one"}) == {"ok": True}
    assert ideas.idea_page(h.root, h.screen) is None                                                  # the later is dropped
    page = ideas.idea_page(h.root, h.api)
    assert "Joined from «Sign-in screen»: **The screen asks for a token.**" in page.section("Gist")
    assert "- a token is issued once" in page.section("Done when") and "- the screen asks for a token" in page.section("Done when")
    assert "Joined «Sign-in screen» of another party into this goal" in page.section("Decisions")
    assert idea_change.changed_of(ideas.state(h.state, h.api)) == ["Gist", "Done when"]               # spec 62's way: the plan waits to be looked at again
    assert collide.read(h.state)["answered"][-1]["note"] == "joined into «Auth API»" and collide.open_of(h.state, pair) is None
    assert [n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide"] == []


def test_one_goal_is_refused_for_a_later_goal_that_has_started_and_the_stop_waits_as_it_did(two):
    h = two
    judged(h, YES)
    run(h, h.api)
    pair = collide.pair_id(h.api, h.screen)
    ideas.edit_plan(h.state, h.screen, lambda p: p["tasks"][0].update(state="running", started="2026-10-24T10:30:00"))
    with pytest.raises(CommandError, match="has started"):
        h.command("ideas.collide_answer", {"id": pair, "answer": "one"})
    assert ideas.idea_page(h.root, h.screen) is not None and collide.open_of(h.state, pair) is not None
    assert collide.read(h.state)["answered"] == [x for x in collide.read(h.state)["answered"] if x["id"] != pair]


def test_leave_it_keeps_both_as_they_are_and_the_pair_is_never_asked_again(two):
    h = two
    model = judged(h, YES)
    run(h, h.api)
    pair = collide.pair_id(h.api, h.screen)
    before = (ideas.idea_page(h.root, h.screen).text(), ideas.idea_page(h.root, h.api).text(), ideas.plan(h.state, h.screen))
    h.command("ideas.collide_answer", {"id": pair, "answer": "leave"})
    assert before == (ideas.idea_page(h.root, h.screen).text(), ideas.idea_page(h.root, h.api).text(), ideas.plan(h.state, h.screen))
    run(h, h.api)
    run(h, h.screen)
    assert len(model.asked) == 1 and collide.open_of(h.state, pair) is None


# -- §3: a spec changed after the start ----------------------------------------------------------------------------------------

def changed_event(h, slug):
    """The bus's `ideas.changed` for a goal (what `Ideas._changed` hears)."""
    h.ideas._seen.setdefault(slug, ("plan", 0.0))                                                    # (its plan was made long ago)
    h.ideas._changed(types.SimpleNamespace(data={"slug": slug}))
    h.ideas.collide_join()


def test_a_spec_changed_under_another_party_is_judged_with_the_changes_words_and_asks_replan_or_leave(two):
    h = two
    model = judged(h, {"collide": True, "why": "The token's shape changed under it", "first": ""})
    ideas.edit_plan(h.state, h.api, lambda p: p.update(passed_at="2026-10-24T09:30:00"))
    idea_change.set_section(h.root, h.state, h.screen, "Gist", "**The screen asks for a token and a refresh token (SECRET-WORDS).**")
    changed_event(h, h.screen)
    assert len(model.asked) == 1
    prompt = model.asked[0]["prompt"]
    assert "SECRET-WORDS" in prompt and "What changed in its spec" in prompt and "Sign-in screen" in prompt and "Auth API" in prompt
    stop = collide.read(h.state)["open"][0]
    assert (stop["by"], stop["asked"], stop["other"]) == ("change", h.api, h.screen)
    row = next(n for n in h.command("ideas.board", {})["needs_you"] if n["kind"] == "collide")
    assert (row["idea"], row["collide"]["answers"], row["collide"]["goals"][0]["idea"]) == (h.api, ["replan", "leave"], h.screen)
    assert row["text"] == "Mobile app changed «Sign-in screen»: «Auth API» in Website rests on what it was"
    assert [(r["by"], r["judged"], r["collide"]) for r in found(h)] == [("change", True, True)]
    changed_event(h, h.screen)                                                                        # nothing new changed: no second call
    assert len(model.asked) == 1
    idea_change.clear(h.state, h.screen)
    changed_event(h, h.screen)                                                                        # (cleared: forgotten)
    idea_change.set_section(h.root, h.state, h.screen, "Out", "Not the web.")                        # another change of the same spec: the pair is open
    changed_event(h, h.screen)
    assert len(model.asked) == 1


def test_a_spec_with_a_plan_not_passed_or_no_plan_beside_it_is_not_compared_and_a_change_of_nothing_is_not_a_change(two):
    h = two
    model = judged(h, YES)
    bare = goal(h, h.web, "Bare goal")                                                                # no plan: nothing rests on a plan that is not there
    ideas.set_meta(h.root, bare, touches=json.dumps(["orkboard/realm/auth.py"]))
    idea_change.set_section(h.root, h.state, h.screen, "Gist", "Changed.")
    changed_event(h, h.screen)
    assert [json.loads(json.dumps(s["asked"])) for s in collide.read(h.state)["open"]] == [h.api]
    assert len(model.asked) == 1
    idea_change.set_section(h.root, h.state, h.api, "Gist", ideas.idea_page(h.root, h.api).section("Gist"))      # the same text: not a change
    assert idea_change.changed_of(ideas.state(h.state, h.api)) == []


def test_replan_it_has_the_leader_of_the_goal_asked_about_replan_what_is_left_and_tells_it_the_change(two, monkeypatch):
    h = two
    judged(h, {"collide": True, "why": "The token's shape changed under it", "first": ""})
    ideas.edit_plan(h.state, h.api, lambda p: p.update(passed_at="2026-10-24T09:30:00"))
    idea_change.set_section(h.root, h.state, h.screen, "Gist", "**Changed.**")
    changed_event(h, h.screen)
    pair = collide.pair_id(h.api, h.screen)
    calls = []
    monkeypatch.setattr(h.ideas.keeper, "revise", lambda slug: calls.append(("revise", slug)))
    monkeypatch.setattr(h.ideas.keeper, "plan", lambda slug, auto=False: calls.append(("plan", slug)))
    assert h.command("ideas.collide_answer", {"id": pair, "answer": "replan"}) == {"ok": True}
    assert calls == [("revise", h.api)]                                                               # its plan is passed: what is left
    told = collide.told_of(h.state, h.api)
    assert "Sign-in screen" in told and "The token's shape changed under it" in told
    assert "The Orkmaster tells you: " + told in h.ideas.keeper.revise_prompt(h.root, h.api)          # the leader reads it
    assert collide.read(h.state)["answered"][-1]["answer"] == "replan" and collide.open_of(h.state, pair) is None


def test_replan_it_on_a_plan_not_passed_plans_again_and_what_it_was_told_is_used_once(two, monkeypatch):
    h = two
    judged(h, {"collide": True, "why": "Changed under it", "first": ""})
    idea_change.set_section(h.root, h.state, h.screen, "Gist", "**Changed.**")
    changed_event(h, h.screen)
    calls = []
    monkeypatch.setattr(h.ideas.keeper, "plan", lambda slug, auto=False: calls.append(slug))
    h.command("ideas.collide_answer", {"id": collide.pair_id(h.api, h.screen), "answer": "replan"})
    assert calls == [h.api] and "Sign-in screen" in h.ideas.keeper.plan_prompt(h.root, h.api)
    collide.clear_told(h.state, h.api)
    assert collide.told_of(h.state, h.api) == "" and "Orkmaster" not in h.ideas.keeper.plan_prompt(h.root, h.api)


def test_replan_it_that_the_keeper_refuses_leaves_the_stop_open_and_tells_nothing(two, monkeypatch):
    h = two
    judged(h, YES)
    stop_of(h, h.api, h.screen, by="change", asked=h.api)
    pair = collide.pair_id(h.api, h.screen)
    monkeypatch.setattr(h.ideas.keeper, "plan", lambda slug, auto=False: (_ for _ in ()).throw(RuntimeError("busy")))
    with pytest.raises(RuntimeError):
        h.command("ideas.collide_answer", {"id": pair, "answer": "replan"})
    assert collide.open_of(h.state, pair) is not None and collide.told_of(h.state, h.api) == ""


# -- §5: measured and priced ---------------------------------------------------------------------------------------------------

def test_the_orkmasters_week_counts_its_stops_answered_taken_and_what_the_judge_cost(two):
    h = two
    judged(h, YES)
    run(h, h.api)
    other = planned(h, h.web, "Auth cache", ["orkboard/realm/auth.py"], "2026-10-24T11:00:00")
    run(h, other)
    assert collide.work(h.ideas.host.repo_root) == {"asked": 2, "answered": 0, "taken": 0, "usd": 0.04}
    first, second = (s["id"] for s in collide.read(h.state)["open"])
    h.command("ideas.collide_answer", {"id": first, "answer": "leave"})
    h.command("ideas.collide_answer", {"id": second, "answer": [a for a in collide.answers_of(collide.open_of(h.state, second)) if a.startswith("first:")][0]})
    assert collide.work(h.ideas.host.repo_root) == {"asked": 2, "answered": 2, "taken": 1, "usd": 0.04}
    assert h.command("ideas.map", {})["project"]["collide_week"] == {"asked": 2, "answered": 2, "taken": 1, "usd": 0.04}
    assert collide.work(h.ideas.host.repo_root.parent / "nowhere") == {"asked": 0, "answered": 0, "taken": 0, "usd": None}


def test_the_collide_events_are_in_the_closed_list_with_the_spend_on_the_goal_asked_about(two):
    h = two
    assert event_log.COLLIDE_FOUND in event_log.EVENTS and event_log.COLLIDE_ANSWERED in event_log.EVENTS
    judged(h, YES)
    run(h, h.api)
    from orkboard.realm import idea_spend
    steps = [r.get("step") for r in idea_spend.read(ideas.state_folder(h.state, h.screen) / idea_spend.FILE)]
    assert steps == ["collide"] and idea_spend.STEP_STAGE["collide"] == "plan"
