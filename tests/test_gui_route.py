"""Spec 99 C (docs/specs/99-a-goals-way.md §4) on the host: a goal sent makes no model call and waits as `routed` with its route row; the route's
edits, Talk, *Later, by itself*, the short way's Start and the `start` row. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import backlog_groups, goal_route, goal_team, idea_spend, ideas, library
from orkboard.sources.limits import Limit



@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def calls(host):
    """The keeper's model call stubbed: `calls` holds every one; it answers a draft with a spec that asks nothing, a route with `answer["route"]`."""
    class Seen(list):
        answer: dict
    seen = Seen()
    answer = {"route": ""}

    def call(tier, prompt, effort="", budget=None):
        seen.append({"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(host.ideas.keeper._tls, "tools", True),
                     "step": host.ideas.keeper.measure()["step"]})
        if "Say which of the project's parties" in prompt:
            return answer["route"], 0.01, 10, ""
        return json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, ""

    host.ideas.keeper.call = call
    seen.answer = answer
    return seen


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def parties(host):
    return {"product": _party(host, "Product", "product-manager", ["copywriter"], "product"),
            "design": _party(host, "Design", "product-designer", ["artist", "ui-kit"], "design"),
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering"),
            "release": _party(host, "Release", "release-manager", [], "engineering")}


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _wait(host, slug):
    for _ in range(500):
        if not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)




def test_a_goal_sent_makes_no_call_and_waits_routed_with_its_route_row(host, parties, calls):
    got = host.command("ideas.add", {"text": "A new logo for the app", "track": parties["tech"]})
    slug = got["slug"]
    assert calls == [] and got["route"] == [parties["tech"]] and got["queue"] == "now"
    st = _state(host, slug)
    assert st["state"] == "routed" and st["queue"] == "" and st["route"] == [{"party": parties["tech"], "leader": "architect"}]
    assert st["route_how"]["by"] == "party" and st["route_how"]["short"] is False
    host.ideas.keeper.tick()                                                    # the keeper's clock drafts nothing that is routed
    assert calls == [] and not host.ideas.keeper.busy(slug)
    row = _row(host, slug, "route")
    assert row["route"][0]["party"] == parties["tech"] and row["place"] == 1 and row["short"] is False and row["low"] is False
    assert row["cost"]["calls"] == 5 and row["goal"] == parties["tech"] and row["blocks"] is False
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert node["state"] == "routed" and node["place"] == "table" and node["asks_you"] is True
    page = host.command("ideas.page", {"slug": slug})
    assert page["state"] == "routed" and page["busy"] is False
    mapped = next(n for n in host.command("ideas.map", {})["nodes"] if n["slug"] == slug)
    assert mapped["needs_you"] == "route" and mapped["place"] == "table"
    assert host.ideas.snapshot()["needs_you"] == 1


def test_a_goal_sent_to_no_party_is_routed_by_code_and_a_bug_is_techs_alone(host, parties, calls):
    bug = host.command("ideas.add", {"text": "Saving crashes: Traceback (most recent call last):\n  File \"a.py\", line 1\nValueError: x"})
    assert calls == [] and bug["route"] == [parties["tech"]]
    st = _state(host, bug["slug"])
    assert st["route_how"]["short"] is True and st["route_how"]["reproduces"] is True and st["route_how"]["by"] == "code"
    row = _row(host, bug["slug"], "route")
    assert row["short"] is True and row["reproduces"] is True and row["cost"]["calls"] == 3           # no Talk, no decision: the draft, the plan, the acceptance
    assert ideas.idea_page(host.ideas.root(), bug["slug"]).get("track") == parties["tech"]                 # it lies in the first party of its route
    two = host.command("ideas.add", {"text": "a new logo and a launch post", "general": True, "track": "general", "marks": ["orkboard/gui"]})
    assert two["route"] == [parties["product"], parties["design"]] and ideas.idea_page(host.ideas.root(), two["slug"]).get("track") == parties["product"]
    assert _row(host, two["slug"], "route")["offer"] == [parties["tech"]]                                    # the marks of System offer Tech, which the route lacks


def test_a_goal_code_cannot_route_is_routed_by_one_call_on_the_cheaper_tier_with_no_tools(host, parties, calls):
    calls.answer["route"] = json.dumps({"route": [parties["design"], parties["tech"], parties["release"], "nope"]})
    got = host.command("ideas.add", {"text": "make it nicer", "general": True})
    slug = got["slug"]
    assert got["route"] == []                                            # nothing yet: the call is made in the background
    _wait(host, slug)
    (call,) = calls
    assert "make it nicer" in call["prompt"] and call["tools"] is False and call["tier"] == "warrior" and call["effort"] == "low"
    assert call["budget"] == 0.15                                        # the step's cap, never under the tier's floor
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["design"], parties["tech"]]           # Release is never a step
    assert _state(host, slug)["route_how"]["by"] == "call" and _state(host, slug)["state"] == "routed"
    assert idea_spend.of_idea(host.ideas.state_dir, slug)["usd"] == pytest.approx(0.01)                     # its cost is the goal's
    assert _row(host, slug, "route")["route"][0]["party"] == parties["design"]


def test_a_call_that_names_none_or_fails_leaves_the_goal_on_the_first_party_to_change(host, parties, calls):
    calls.answer["route"] = "I cannot say"
    slug = host.command("ideas.add", {"text": "make it nicer", "general": True})["slug"]
    _wait(host, slug)
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["product"]] and _state(host, slug)["route_how"]["by"] == "default"

    def broken(*a, **k):
        raise RuntimeError("no model")
    host.ideas.keeper.call = broken
    again = host.command("ideas.add", {"text": "make it prettier", "general": True})["slug"]
    _wait(host, again)
    assert _state(host, again)["route"] and _state(host, again)["route_how"]["by"] == "default"


def test_the_route_is_edited_with_no_call_and_the_cost_is_answered_again(host, parties, calls):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "general": True})["slug"]
    assert _state(host, slug)["route"][0]["party"] == parties["tech"]
    one = _row(host, slug, "route")["cost"]
    got = host.command("ideas.route_set", {"idea": slug, "route": [parties["design"], parties["tech"]]})
    assert calls == [] and [r["party"] for r in got["route"]] == [parties["design"], parties["tech"]] and got["cost"]["calls"] == 10
    assert got["cost"]["usd_high"] > one["usd_high"] and got["short"] is False and got["changed"] is False
    assert _row(host, slug, "route")["cost"] == got["cost"] and _state(host, slug)["route_how"]["by"] == "person"
    host.command("ideas.route_set", {"idea": slug, "route": [{"party": parties["design"]}]})              # a party taken off
    assert [r["party"] for r in _state(host, slug)["route"]] == [parties["design"]]
    for wanted, why in (([parties["release"]], "Release is never a step"), ([], "needs a party"), (["nope"], "That party is gone")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.route_set", {"idea": slug, "route": wanted})
    with pytest.raises(CommandError, match="gone"):
        host.command("ideas.route_set", {"idea": "nope", "route": [parties["tech"]]})
    assert calls == []


def test_talk_sets_the_state_and_hands_the_goal_to_the_keepers_talk_when_it_has_one(host, parties, calls, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    went = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append((s, _state(host, s)["state"])), raising=False)       # part D's seam
    assert host.command("ideas.talk", {"idea": slug}) == {"ok": True}
    assert went == [(slug, "talk")] and calls == [] and _state(host, slug)["state"] == "talk"
    said = _state(host, slug)["route_how"]
    assert said["said"] == goal_route.cost_of(host.ideas.root(), host.ideas.state_dir, _state(host, slug)) and said["changed"] is False
    assert _row(host, slug, "route") is None and _row(host, slug, "start") is None
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert node["place"] == "table" and node["asks_you"] is False
    with pytest.raises(CommandError, match="no route to answer"):
        host.command("ideas.talk", {"idea": slug})                                                          # Talk is pressed once






def test_later_by_itself_is_offered_only_when_the_limits_run_low_and_talk_starts_at_the_reset(host, parties, calls, monkeypatch):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    with pytest.raises(CommandError, match="only when the limits run low"):
        host.command("ideas.route_later", {"idea": slug})
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    rows = [Limit("claude", "", "session", 0.1, reset)]                                                    # 0.1 ≤ the reserve
    monkeypatch.setattr(host, "limits", lambda: rows)
    assert _row(host, slug, "route")["low"] is True
    went = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append(s), raising=False)
    got = host.command("ideas.route_later", {"idea": slug})
    assert got["ok"] is True and _state(host, slug)["held_until"] == got["held_until"] and _state(host, slug)["state"] == "routed"
    node = next(i for i in host.command("ideas.board")["ideas"] if i["slug"] == slug)
    assert (node["place"], node["waits_as"]) == ("deck", "reset") and _row(host, slug, "route") is None      # waits in the deck, nothing to decide
    host.ideas.route_tick(time.monotonic())
    assert went == [] and _state(host, slug)["state"] == "routed"                                          # before the reset: nothing
    ideas.save_state(host.ideas.state_dir, slug, held_until=(dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds"))
    host.ideas.route_tick(time.monotonic() + 100)
    assert went == [] and _state(host, slug)["held_until"] > dt.datetime.now().isoformat(timespec="seconds")   # the reserve is spent again: it waits for the next reset
    rows[:] = []                                                                                           # the window is back
    ideas.save_state(host.ideas.state_dir, slug, held_until=(dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds"))
    host.ideas.route_tick(time.monotonic() + 200)
    assert went == [slug] and _state(host, slug)["state"] == "talk" and _state(host, slug)["held_until"] == ""


def test_the_short_ways_start_skips_talk_and_the_decision_and_a_bug_without_a_failure_goes_to_talk(host, parties, calls, monkeypatch):
    went = []
    monkeypatch.setattr(host.ideas.keeper, "sections", lambda s: went.append(("sections", s)), raising=False)       # part E's seam
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: went.append(("talk", s)), raising=False)             # part D's
    failing = host.command("ideas.add", {"text": "Saving crashes, tests/test_save.py::test_it FAILED"})["slug"]
    assert host.command("ideas.route_start", {"idea": failing}) == {"ok": True}
    assert went == [("sections", failing)] and _state(host, failing)["state"] == "sections"
    reported = host.command("ideas.add", {"text": "Saving crashes when the file is empty"})["slug"]
    assert _state(host, reported)["route_how"]["short"] is True and _state(host, reported)["route_how"]["reproduces"] is False
    host.command("ideas.route_start", {"idea": reported})                                                  # nothing to start from: Talk is the diagnosis
    assert went[-1] == ("talk", reported) and _state(host, reported)["state"] == "talk" and _state(host, reported)["route_how"]["short"] is True
    long = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    with pytest.raises(CommandError, match="Only the short way"):
        host.command("ideas.route_start", {"idea": long})
    again = host.command("ideas.add", {"text": "Saving crashes, tests/test_save.py::test_it FAILED"})["slug"]
    host.command("ideas.talk", {"idea": again})                                                            # *The long way*
    assert _state(host, again)["route_how"]["short"] is False and went[-1] == ("talk", again)
    assert calls == []




# -- decisions §239: the goals put off start Talk one at a time, in the Orkmaster's order, by the week's pace ------------------------------------

def _put_off(host, parties, n=3):
    """`n` goals put off with *Later, by itself*, in the Orkmaster's order (the line: priority, then the person's order), their reset passed."""
    slugs = [host.command("ideas.add", {"text": f"idea number {k}", "track": parties["tech"]})["slug"] for k in range(n)]
    gone = (dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds")
    for s in slugs:
        ideas.save_state(host.ideas.state_dir, s, held_until=gone)
    backlog_groups.save(host.ideas.state_dir, backlog_groups.new(gone, []))     # these tests are of the queue: the groups of this reset (spec 135 B) were asked and named none
    root = host.ideas.root()
    found = ideas.ideas(root)
    order = goal_route.context(found, {i["slug"]: ideas.state(host.ideas.state_dir, i["slug"]) for i in found})["order"]
    return sorted(slugs, key=lambda s: order[s])


@pytest.fixture
def went(host, monkeypatch):
    seen = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: seen.append(s), raising=False)
    return seen


def _pass(host, k):
    host.ideas._route_at = float("-inf")
    host.ideas.route_tick(time.monotonic() + 1000 * k)


def test_goals_put_off_start_talk_one_per_pass_the_first_in_the_orkmasters_order(host, parties, calls, went):
    first, second, third = _put_off(host, parties)
    _pass(host, 1)
    assert went == [first] and _state(host, first)["state"] == "talk" and _state(host, first)["from_backlog"] is True
    assert _state(host, second)["state"] == "routed" and _state(host, third)["state"] == "routed"
    _pass(host, 2)
    assert went == [first]                                                      # the first is still in Talk: the next waits
    ideas.save_state(host.ideas.state_dir, first, state="decided")              # out of its Talk
    _pass(host, 3)
    assert went == [first, second] and _state(host, first)["from_backlog"] is False
    _pass(host, 4)
    assert went == [first, second]
    ideas.save_state(host.ideas.state_dir, second, state="decided")
    _pass(host, 5)
    assert went == [first, second, third]










def test_a_goal_whose_next_step_does_not_fit_the_window_waits_for_the_next_reset_and_the_next_in_order_goes(host, parties, calls, went, monkeypatch):
    """Spec 138 B.4 (decisions §245.4): the cost of the next step (the route's estimate) against what the window holds above the reserve; the order never changes."""
    monkeypatch.setattr("orkboard.realm.idea_target.in_night", lambda spec, now=None: False)                   # the day's reserve, whatever the hour the suite runs at
    first, second, third = _put_off(host, parties)
    host.command("ideas.route_set", {"idea": first, "route": [parties["tech"], parties["design"]]})            # the first goal's route is dearer than the others'
    root, state, settings = host.ideas.root(), host.ideas.state_dir, host.ideas.settings_now()

    def price(slug):
        got = goal_route.cost_of(root, state, ideas.state(state, slug), settings)
        return (got["usd_low"] + got["usd_high"]) / 2
    small, big = price(second), price(first)
    assert big > small > 0
    per = small / 0.05 / 100                                                                                       # the cheaper goal is 5 % of the window, the dearer more
    monkeypatch.setattr("orkboard.sources.window_rate.shown", lambda machine: {"usd_per_pct": per})
    room = ((small + big) / 2) / per / 100                                                                         # what the window holds above the reserve: between the two
    reset = dt.datetime.now() + dt.timedelta(hours=2)
    monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", room + 0.3, reset)])
    _pass(host, 1)
    assert went == [second], "the first does not fit: the next in order goes"
    held = dt.datetime.fromisoformat(_state(host, first)["held_until"])
    assert _state(host, first)["state"] == "routed" and abs((held - reset).total_seconds()) < 2, "its hold moves to the window's next reset"
    assert _state(host, third)["state"] == "routed" and _state(host, third)["held_until"] < dt.datetime.now().isoformat(timespec="seconds"), "the one behind is not touched"
    ideas.save_state(state, second, state="decided")
    _pass(host, 2)
    assert went == [second, third], "the first still waits for its reset; the third goes"
    ideas.save_state(state, third, state="decided")
    ideas.save_state(state, first, held_until=(dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec="seconds"))      # its reset came
    monkeypatch.setattr(host, "limits", lambda: [Limit("claude", "", "session", 0.95, reset)])                     # a whole window
    _pass(host, 3)
    assert went == [second, third, first]


# -- spec 149 A ---------------------------------------------------------------------------------------------------------------------------

def test_a_type_chosen_is_what_the_goal_is_routed_as_and_the_card_and_talk_agree(host, parties, calls):
    got = host.command("ideas.add", {"text": "The host should predict per shape, a bug of its own kind", "track": parties["tech"], "type": "shaped-feature"})
    st = _state(host, got["slug"])
    assert st["route_how"]["kind"] == "shaped-feature" and st["route_how"]["short"] is False
    row = _row(host, got["slug"], "route")
    assert row["type"] == "shaped-feature" and row["short"] is False
    typed = host.command("ideas.add", {"text": "Saving crashes when the file is empty", "track": parties["tech"]})
    st = _state(host, typed["slug"])
    assert st["route_how"]["kind"] == "bug" and st["route_how"]["short"] is True and _row(host, typed["slug"], "route")["type"] == "bug"


def test_it_is_no_bug_routes_the_goal_again_with_no_call(host, parties, calls):
    assert "ideas.route_kind" in host.commands
    got = host.command("ideas.add", {"text": "Saving crashes when the file is empty", "track": parties["tech"]})
    slug = got["slug"]
    assert _state(host, slug)["route_how"]["kind"] == "bug"
    n = len(calls)
    ans = host.command("ideas.route_kind", {"idea": slug})
    assert len(calls) == n and ans["kind"] == "feature" and ans["short"] is False and ans["cost"]["calls"] >= 4
    st = _state(host, slug)
    assert st["state"] == "routed" and st["route_how"]["kind"] == "feature" and st["route_how"]["short"] is False
    assert _row(host, slug, "route")["type"] == "feature"
    with pytest.raises(CommandError):                                              # no longer a bug
        host.command("ideas.route_kind", {"idea": slug})


