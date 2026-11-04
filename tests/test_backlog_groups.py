"""Spec 135 B (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §B; decisions §242.5, §239) on the host: the one call at a reset over the goals put off (the keeper's model call stubbed),
its answer cleaned strictly and bounded by code, the record and its one row, the card's answers (Join, Keep apart, Not now) and the queue's wait. No AI tool is called for real."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import BoardPhone, Orkboard
from orkboard.gui.ideas_groups import groups_commands
from orkboard.realm import backlog_groups, board_rows, event_log, goal_refine, goal_team, idea_element, idea_target, ideas, library, spec_sections

DECISION = {"title": "Dark mode ships", "why": "People read at night.", "points": ["Tech adds it.", "Off by default."]}


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    (h.ideas.state_dir / "project.json").write_text('{"decisions": "docs/decisions.md"}', encoding="utf-8")
    h.command("ideas.board_set", {"autostart": False})
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer", ["artist", "ui-kit"], "design")


class Model(list):
    """Every call the stub saw (`step`, `prompt`); `answer` is what the `groups` step answers (a dict, text, an Exception or a callable of the prompt)."""

    answer: object


@pytest.fixture
def model(host):
    seen = Model()
    seen.answer = {"groups": []}

    def call(tier, prompt, effort="", budget=None):
        keeper = host.ideas.keeper
        step = keeper.measure()["step"]
        seen.append({"step": step, "prompt": prompt, "tier": tier, "effort": effort, "tools": getattr(keeper._tls, "tools", None), "as": getattr(keeper._tls, "as_role", "")})
        if step == "groups":
            got = seen.answer(prompt) if callable(seen.answer) else seen.answer
            if isinstance(got, Exception):
                raise got
            return (got if isinstance(got, str) else json.dumps(got)), 0.02, 120, ""
        if step == "decide":
            return json.dumps({**DECISION, "title": "Dark mode ships, with a timer"}), 0.01, 10, ""
        return json.dumps({"stance": "For it", "for": "f", "against": "a", "questions": []}), 0.01, 10, ""

    host.ideas.keeper.call = call
    return seen


@pytest.fixture
def went(host, monkeypatch):
    seen = []
    monkeypatch.setattr(host.ideas.keeper, "talk", lambda s: seen.append(s), raising=False)
    return seen


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _gone(minutes=1):
    return (dt.datetime.now() - dt.timedelta(minutes=minutes)).isoformat(timespec="seconds")


def _off(host, party, texts, minutes=1):
    """Goals put off with *Later, by itself*, their reset passed; the slugs in the Orkmaster's order."""
    slugs = [host.command("ideas.add", {"text": t, "track": party})["slug"] for t in texts]
    for s in slugs:
        ideas.save_state(host.ideas.state_dir, s, held_until=_gone(minutes))
    return slugs


def _pass(host, k=1):
    host.ideas._route_at = float("-inf")
    host.ideas.route_tick(time.monotonic() + 1000 * k)


def _quiet(host):
    for _ in range(1500):
        if not host.ideas.keeper.busy("groups"):
            return
        time.sleep(0.01)
    raise AssertionError("the groups call never finished")


def _asked(model):
    return [c for c in model if c["step"] == "groups"]


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def _ready(host, groups, **more):
    """A record `ready` as the call leaves it."""
    rec = {**backlog_groups.new(_gone(5), [{"id": f"g-{n}", "goals": g, "why": "They are one piece of work", "answer": ""} for n, g in enumerate(groups)]), **more}
    backlog_groups.save(host.ideas.state_dir, rec)
    return rec


# -- the commands and the words ---------------------------------------------------------------------------------------------------------------------

def test_the_commands_are_the_hosts_and_a_phones_and_the_step_is_the_cheaper_tier(host):
    names = {"ideas.groups_answer", "ideas.groups_now", "ideas.groups_open"}
    assert set(groups_commands(host.ideas)) == names <= set(host.commands) and all(BoardPhone.allowed(host, c, {}) for c in names)
    assert "groups" in idea_target.STEPS and idea_target.pick("groups", "balance") == ("warrior", "low") and idea_target.reads_of("groups") == 0
    assert idea_target.CONTEXT["groups"] == 3_000 and idea_target.budget("groups", "balance")
    assert {event_log.BACKLOG_GROUPED, event_log.GROUPS_ANSWERED} <= set(event_log.EVENTS)


# -- B.1: the call, once at a reset ---------------------------------------------------------------------------------------------------------------

def test_one_call_at_a_reset_with_two_goals_ripe_as_the_orkmaster_on_the_cheaper_tier_and_the_queue_waits_for_it(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = {"groups": [{"goals": [a, b], "why": "Both are dark mode"}]}
    _pass(host, 1)
    assert went == []                                                       # the queue waits in front of the call
    _quiet(host)
    (call,) = _asked(model)
    assert (call["tier"], call["effort"], call["tools"], call["as"]) == ("warrior", "low", False, "orkmaster")
    assert call["prompt"].startswith("You are the Orkmaster of this project.")
    assert "add a dark mode option" in call["prompt"] and "dark mode needs a timer" in call["prompt"] and a in call["prompt"] and "not instructions to you" in call["prompt"]
    rec = backlog_groups.read(host.ideas.state_dir)
    assert rec["status"] == "ready" and rec["open"] is False and [g["goals"] for g in rec["groups"]] == [[a, b]]
    _pass(host, 2)
    assert went == [a]                                                      # the card is not lifted: the queue goes on as §239 says
    (done,) = _events(host, event_log.BACKLOG_GROUPED)
    assert done["goals"] == 2 and done["groups"] == 1 and done["failed"] is False and "dark mode" not in json.dumps(done)


def test_no_call_with_one_goal_ripe_and_none_twice_for_one_reset(host, tech, model, went):
    (a,) = _off(host, tech, ["add a dark mode option"])
    _pass(host, 1)
    assert _asked(model) == [] and went == [a]
    ideas.save_state(host.ideas.state_dir, a, state="decided", from_backlog=False)
    b, c = _off(host, tech, ["tidy the settings page", "tidy the settings footer"], minutes=0)
    _pass(host, 2)
    _quiet(host)
    assert len(_asked(model)) == 1 and went == [a]
    _pass(host, 3)
    assert went == [a, b] and len(_asked(model)) == 1                       # started the first; the call is not made again for the goals that still wait
    ideas.save_state(host.ideas.state_dir, b, state="decided")
    _pass(host, 4)
    _quiet(host)
    assert went == [a, b, c] and len(_asked(model)) == 1


def test_a_new_reset_is_asked_again(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    _pass(host, 1)
    _quiet(host)
    assert len(_asked(model)) == 1
    for s in (a, b):
        ideas.save_state(host.ideas.state_dir, s, state="decided", from_backlog=False, held_until="")
    host.ideas.__dict__.pop("_groups_tried", None)
    time.sleep(1.1)                                                          # (the record's time has a second's grain)
    _off(host, tech, ["tidy the settings page", "tidy the settings footer"], minutes=0)
    _pass(host, 2)
    _quiet(host)
    assert len(_asked(model)) == 2


def test_the_prompt_holds_the_titles_cut_and_no_more_than_forty_goals(host, tech):
    keeper = host.ideas.keeper
    short = keeper.groups_prompt([{"slug": f"g{n}", "title": f"title {n}", "party": tech, "parties": [tech]} for n in range(45)])
    assert "g39 |" in short and "g40 |" not in short
    long = keeper.groups_prompt([{"slug": f"g{n}", "title": "word " * 40, "party": tech, "parties": [tech]} for n in range(10)])
    assert "word " * 40 not in long and ("word " * 15).strip() in long and "g0 |" in long        # a title is cut to TITLE_CHARS
    many = keeper.groups_prompt([{"slug": f"s{n}", "title": "x" * 80, "party": tech, "parties": [tech]} for n in range(40)])
    assert many.count("\n- ") < 40 and many.count("\n- ") + 1 > 15                                  # the whole is cut to CHARS


def test_a_call_that_fails_leaves_the_queue_going_and_is_not_made_again(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = RuntimeError("no model")
    _pass(host, 1)
    _quiet(host)
    assert backlog_groups.read(host.ideas.state_dir) == {} and went == []
    _pass(host, 2)
    assert went == [a] and len(_asked(model)) == 1
    assert _events(host, event_log.BACKLOG_GROUPED)[0]["failed"] is True


@pytest.mark.parametrize("answer", ["no json at all", {"groups": []}, {"groups": [{"goals": ["nope", "nothing"], "why": "x"}]}, {"nothing": 1}])
def test_an_answer_that_is_no_json_or_names_no_group_is_the_record_with_none_and_the_queue_goes_on(host, tech, model, went, answer):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = answer
    _pass(host, 1)
    _quiet(host)
    rec = backlog_groups.read(host.ideas.state_dir)
    assert rec["status"] == "none" and rec["groups"] == []
    assert board_rows.rows(host.ideas.state_dir, host.ideas.root()) == []
    _pass(host, 2)
    assert went == [a]


def test_no_call_when_the_demo_or_a_spent_window_or_a_stop_forbids_it(host, tech, model, went, monkeypatch):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    monkeypatch.setattr(host.ideas.keeper, "window_until", lambda: time.time() + 3600)
    _pass(host, 1)
    assert _asked(model) == [] and went == [] and backlog_groups.read(host.ideas.state_dir) == {}      # the window holds the whole queue
    monkeypatch.setattr(host.ideas.keeper, "window_until", lambda: None)
    monkeypatch.setattr(host.ideas.keeper, "demo", True)
    _pass(host, 2)
    _quiet(host)
    assert _asked(model) == [] and went == [a] and backlog_groups.read(host.ideas.state_dir) == {}   # a call that cannot be had records nothing and the queue goes on


# -- B.1: the answer, strictly --------------------------------------------------------------------------------------------------------------------

def test_clean_drops_an_unknown_slug_a_goal_in_two_groups_a_group_of_one_and_cuts_a_big_group():
    ripe = ["a", "b", "c", "d", "e", "f", "g"]
    got = backlog_groups.clean({"groups": [
        {"goals": ["a", "ghost", "b"], "why": "  one\nline  "},
        {"goals": ["b", "c"], "why": "b is taken"},                          # b is in the first group: c is alone
        {"goals": ["d", "e", "f", "g", "a"], "why": "x" * 400},               # at most GROUP_MAX goals
        {"goals": ["a", "a"], "why": "one goal twice"},
        "nonsense", {"goals": "d,e"}]}, ripe)
    assert [g["goals"] for g in got] == [["a", "b"], ["d", "e", "f", "g"]]
    assert got[0]["why"] == "one line" and len(got[1]["why"]) == backlog_groups.WHY_CHARS and all(g["answer"] == "" and g["id"].startswith("g-") for g in got)
    assert backlog_groups.clean("x", ripe) == [] and backlog_groups.clean({"groups": "x"}, ripe) == [] and backlog_groups.clean(None, ripe) == []


def test_clean_keeps_at_most_five_groups_and_the_orkmasters_order_inside_a_group():
    ripe = [f"s{n}" for n in range(14)]
    got = backlog_groups.clean({"groups": [{"goals": [ripe[2 * n + 1], ripe[2 * n]], "why": ""} for n in range(7)]}, ripe)
    assert len(got) == backlog_groups.GROUPS_MAX and got[0]["goals"] == ["s0", "s1"]


def test_a_group_that_does_not_fit_goes_on_alone(host, tech, design):
    root, state = host.ideas.root(), host.ideas.state_dir
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    c = host.command("ideas.add", {"text": "a dark mode for the screens", "track": design})["slug"]
    big = host.command("ideas.add", {"text": "dark " * 300, "track": tech})["slug"]
    big2 = host.command("ideas.add", {"text": "mode " * 300, "track": tech})["slug"]
    ripe = [a, b, c, big, big2]
    got = backlog_groups.clean({"groups": [{"goals": [a, b], "why": "ok"}, {"goals": [big, big2], "why": "too much words"}]}, ripe, root, state)
    assert [g["goals"] for g in got] == [[a, b]]                              # the second would pass JOIN_CHARS
    assert backlog_groups.fits_group(root, state, [a, c]) and not backlog_groups.fits_group(root, state, [big, big2]) and not backlog_groups.fits_group(root, state, [a])
    d = _party(host, "Run", "architect", ["grunt"], "engineering")
    e = host.command("ideas.add", {"text": "dark mode in the dashboard", "track": d})["slug"]
    assert not backlog_groups.fits_group(root, state, [a, c, e]) and backlog_groups.fits_group(root, state, [a, c])      # a second party more is too much: one is the limit


# -- B.2: the record and the row --------------------------------------------------------------------------------------------------------------------

def test_one_row_while_the_groups_are_ready_and_none_after_the_answer_or_not_now(host, tech):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    state, root = host.ideas.state_dir, host.ideas.root()
    assert board_rows.rows(state, root) == []
    _ready(host, [[a, b]])
    (row,) = [r for r in host.command("ideas.board")["needs_you"] if r["kind"] == "groups"]
    (g,) = row["groups"]
    assert row["id"] == backlog_groups.read(state)["reset"] and row["blocks"] is False and row["cost"] is None
    assert [x["idea"] for x in g["goals"]] == [a, b] and g["goals"][0]["title"] == "add a dark mode option" and g["goals"][0]["party"] == tech and g["goals"][0]["head"]["race"]
    assert g["why"] == "They are one piece of work" and g["adds"] == [] and "idea" not in row
    host.command("ideas.groups_now", {})
    assert [r for r in host.command("ideas.board")["needs_you"] if r["kind"] == "groups"] == []
    _ready(host, [[a, b]])
    host.command("ideas.groups_answer", {"id": backlog_groups.read(state)["reset"], "join": []})
    assert board_rows.rows(state, root) == []


def test_the_row_leaves_out_a_goal_that_is_gone_and_its_cost_is_one_decide_call_for_a_first_goal_whose_decision_is_worded(host, tech, model):
    state, root = host.ideas.state_dir, host.ideas.root()
    a, b, c = _off(host, tech, ["add a dark mode option", "dark mode needs a timer", "tidy the footer"])
    _ready(host, [[a, b], [b, c]])
    ideas.save_state(state, a, state="decided")
    (row,) = board_rows.rows(state, root, host.ideas.settings_now())
    assert row["cost"] == {"calls": 1, "usd_high": round(idea_target.budget("decide", idea_target.target_for(host.ideas.settings_now(), ideas.track_page(root, tech))), 4)}
    ideas.drop(root, c, state)
    (row,) = board_rows.rows(state, root)
    assert [g["id"] for g in row["groups"]] == ["g-0"]                        # [b, c] is left with one goal
    ideas.drop(root, b, state)
    assert board_rows.rows(state, root) == []


# -- B.3: the answers -----------------------------------------------------------------------------------------------------------------------------

def _decided(host, tech, model, text="add a dark mode option"):
    slug = host.command("ideas.add", {"text": text, "track": tech})["slug"]
    host.command("ideas.talk", {"idea": slug})
    for _ in range(1500):
        if _state(host, slug)["state"] == "decided" and not host.ideas.keeper.busy(slug):
            break
        time.sleep(0.01)
    model.clear()
    return slug


def test_join_puts_the_others_words_in_the_first_drops_them_and_words_its_decision_once(host, tech, model):
    state, root = host.ideas.state_dir, host.ideas.root()
    first = _decided(host, tech, model)
    second = host.command("ideas.add", {"text": "dark mode needs a timer", "track": tech})["slug"]
    third = host.command("ideas.add", {"text": "dark mode for the logo", "track": tech})["slug"]
    ideas.save_state(state, second, element="ice")
    ideas.save_state(state, third, element="dust")
    rec = _ready(host, [[first, second, third]])
    got = host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-0"]})
    assert got["ok"] is True and got["apart"] == [] and len(got["joined"]) == 1
    (j,) = got["joined"]
    assert j["idea"] == first and j["dropped"] == [second, third] and j["reworded"] is True and j["cost"]["calls"] == 1
    for _ in range(1500):
        if not host.ideas.keeper.busy(first):
            break
        time.sleep(0.01)
    assert len([c for c in model if c["step"] == "decide"]) == 1               # once, not once for each joined goal
    gist = ideas.idea_page(root, first).section("Gist")
    assert gist == "add a dark mode option\n\nAdded: dark mode needs a timer\n\nAdded: dark mode for the logo"
    assert [(r["text"], r["element"], r["via"]) for r in goal_refine.added_rows(state, first)] == [("dark mode needs a timer", "ice", "groups"), ("dark mode for the logo", "dust", "groups")]
    assert ideas.idea_page(root, second) is None and ideas.idea_page(root, third) is None and ideas.idea_page(root, first) is not None
    assert spec_sections.record(state, first)["decision"]["title"] == "Dark mode ships, with a timer"
    assert backlog_groups.read(state)["status"] == "answered" and backlog_groups.read(state)["groups"][0]["answer"] == "join"
    (ev,) = _events(host, event_log.GROUPS_ANSWERED)
    assert (ev["joined"], ev["apart"], ev["dropped"], ev["not_now"]) == (1, 0, 2, False)
    assert [e["via"] for e in _events(host, event_log.GOAL_ADDED_TO)] == ["groups", "groups"]


def test_the_first_goal_in_the_orkmasters_order_takes_the_others_and_a_goal_before_its_decision_costs_no_call(host, tech, model):
    state, root = host.ideas.state_dir, host.ideas.root()
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    late = host.command("ideas.add", {"text": "urgent dark mode", "track": tech, "priority": "high"})["slug"]
    rec = _ready(host, [[a, b, late]])
    got = host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-0"]})
    (j,) = got["joined"]
    assert j["idea"] == late and sorted(j["dropped"]) == sorted([a, b]) and j["reworded"] is False and "cost" not in j
    assert [c for c in model if c["step"] == "decide"] == []
    assert ideas.idea_page(root, late) is not None and ideas.idea_page(root, a) is None


def test_an_unnamed_group_is_kept_apart_and_nothing_is_dropped(host, tech):
    state, root = host.ideas.state_dir, host.ideas.root()
    a, b, c, d = _off(host, tech, ["add a dark mode option", "dark mode needs a timer", "tidy the footer", "tidy the footer links"])
    rec = _ready(host, [[a, b], [c, d]])
    got = host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-1"]})
    assert [x["id"] for x in got["apart"]] == ["g-0"] and len(got["joined"]) == 1
    assert ideas.idea_page(root, a) is not None and ideas.idea_page(root, b) is not None
    assert {g["id"]: g["answer"] for g in backlog_groups.read(state)["groups"]} == {"g-0": "apart", "g-1": "join"}


def test_a_group_with_a_goal_that_left_the_pile_is_kept_apart_alone_and_the_others_join(host, tech):
    state, root = host.ideas.state_dir, host.ideas.root()
    a, b, c, d = _off(host, tech, ["add a dark mode option", "dark mode needs a timer", "tidy the footer", "tidy the footer links"])
    rec = _ready(host, [[a, b], [c, d]])
    ideas.save_state(state, b, state="done")                                  # b left the pile meanwhile
    got = host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-0", "g-1"]})
    (kept,) = got["apart"]
    assert kept["id"] == "g-0" and kept["why"] == "A goal of it is not in analysis any more" and len(got["joined"]) == 1
    assert ideas.idea_page(root, a) is not None and ideas.idea_page(root, b) is not None and ideas.idea_page(root, d) is None
    drop = ideas.idea_page(root, c)
    assert drop is not None and "Added: tidy the footer links" in drop.section("Gist")
    gone = _off(host, tech, ["one more", "one more thing"])
    rec = _ready(host, [gone])
    ideas.drop(root, gone[0], state)
    got = host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-0"]})
    assert got["joined"] == [] and got["apart"][0]["why"] == "A goal of it is not in analysis any more"


def test_the_answer_is_refused_in_words_for_a_card_that_is_not_there_or_a_group_it_does_not_have(host, tech):
    from orkboard.gui.board_host import CommandError
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    with pytest.raises(CommandError, match="No goals wait to be joined"):
        host.command("ideas.groups_answer", {"id": "x"})
    rec = _ready(host, [[a, b]])
    with pytest.raises(CommandError, match="names the groups of the card"):
        host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-9"]})
    with pytest.raises(CommandError, match="not both"):
        host.command("ideas.groups_answer", {"id": rec["reset"], "join": ["g-0"], "apart": ["g-0"]})
    assert backlog_groups.read(host.ideas.state_dir)["status"] == "ready"


def test_not_now_joins_nothing_and_the_groups_are_not_asked_again_at_this_reset(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = {"groups": [{"goals": [a, b], "why": "Both are dark mode"}]}
    _pass(host, 1)
    _quiet(host)
    host.command("ideas.groups_now", {})
    assert backlog_groups.read(host.ideas.state_dir)["status"] == "none"
    _pass(host, 2)
    assert went == [a] and len(_asked(model)) == 1 and ideas.idea_page(host.ideas.root(), b) is not None
    (ev,) = _events(host, event_log.GROUPS_ANSWERED)
    assert ev["not_now"] is True and ev["joined"] == 0


# -- B.3: the queue's wait ------------------------------------------------------------------------------------------------------------------------

def test_the_queue_waits_while_the_card_lies_lifted_and_goes_on_when_it_is_put_down_answered_or_stale(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = {"groups": [{"goals": [a, b], "why": "Both are dark mode"}]}
    _pass(host, 1)
    _quiet(host)
    rid = backlog_groups.read(host.ideas.state_dir)["reset"]
    host.command("ideas.groups_open", {"id": rid, "open": True})
    assert backlog_groups.read(host.ideas.state_dir)["open"] is True and backlog_groups.read(host.ideas.state_dir)["open_at"]
    _pass(host, 2)
    _pass(host, 3)
    assert went == []                                                         # lifted: the queue waits
    host.command("ideas.groups_open", {"id": rid, "open": False})
    _pass(host, 4)
    assert went == [a]                                                        # put down: it goes on


def test_a_card_lifted_and_forgotten_never_holds_the_queue_past_the_lift_time(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = {"groups": [{"goals": [a, b], "why": "Both are dark mode"}]}
    _pass(host, 1)
    _quiet(host)
    rid = backlog_groups.read(host.ideas.state_dir)["reset"]
    host.command("ideas.groups_open", {"id": rid, "open": True})
    _pass(host, 2)
    assert went == []
    old = (dt.datetime.now() - dt.timedelta(seconds=backlog_groups.LIFT_S + 5)).isoformat(timespec="seconds")
    backlog_groups.update(host.ideas.state_dir, rid, open_at=old)             # a face that is gone never holds the queue
    _pass(host, 3)
    assert went == [a]


def test_the_queue_goes_on_once_the_card_is_answered(host, tech, model, went):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    model.answer = {"groups": [{"goals": [a, b], "why": "Both are dark mode"}]}
    _pass(host, 1)
    _quiet(host)
    rid = backlog_groups.read(host.ideas.state_dir)["reset"]
    host.command("ideas.groups_open", {"id": rid, "open": True})
    _pass(host, 2)
    assert went == []
    host.command("ideas.groups_answer", {"id": rid, "join": []})
    assert backlog_groups.read(host.ideas.state_dir)["open"] is False
    _pass(host, 3)
    assert went == [a]


def test_a_lift_of_another_card_changes_nothing(host, tech):
    a, b = _off(host, tech, ["add a dark mode option", "dark mode needs a timer"])
    _ready(host, [[a, b]])
    host.command("ideas.groups_open", {"id": "not-this-one", "open": True})
    assert backlog_groups.read(host.ideas.state_dir)["open"] is False
    from orkboard.gui.board_host import CommandError
    with pytest.raises(CommandError, match="true or false"):
        host.command("ideas.groups_open", {"id": "x", "open": "yes"})


def test_the_added_words_and_the_plain_add_still_work_through_the_shared_path(host, tech, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": tech, "hold": True})["slug"]
    got = host.command("ideas.add_to_goal", {"idea": slug, "text": "Also a timer.", "element": "ice", "via": "bubble"})
    assert got["ok"] is True and goal_refine.added_rows(host.ideas.state_dir, slug)[0]["element"] == "ice"
    assert idea_element.of(host.ideas.state_dir, slug) in idea_element.ELEMENTS
