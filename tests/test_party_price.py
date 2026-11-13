"""Spec 43 C (docs/specs/43-party-measured.md §3, Tests → C): what a party costs before it starts — a first guess with no basis, learned from
`TOO_FEW` priced ideas, `every` giving a share of 1, a check's learned share, a party with no builder taking the Grunt's cost — and
`ideas.party_price`. Code, no model."""
from __future__ import annotations

import datetime as dt
import json

import pytest

from orkboard.gui.board_host import BoardPhone, CommandError, Orkboard
from orkboard.realm import goal_types, idea_spend, ideas, library, party_price


ACCEPT = 0.25                       # the leader's acceptance of its step: one call at the floor of accept_step's tier (elder) until goals have priced it (spec 152 B.4)


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def task(tid, kind, role, state="merged", cost=None, **more):
    return {"id": tid, "title": tid, "brief": "b", "tier": "warrior", "kind": kind, "role": role, "after": [], "state": state, "round": 1, "note": "",
            "branch": "", "commit": "", "cost": cost, "ran_tier": "warrior", "finished": dt.datetime.now().isoformat(timespec="seconds"), **more}


def add(host, text, tasks, checks, made=0):
    root, state = host.ideas.root(), host.ideas.state_dir
    goal = next((t["slug"] for t in ideas.tracks(root, make=False) if t["slug"] != "general"), None) or ideas.add_track(root, "Billing")
    s = ideas.add_idea(root, text, goal, state)
    made_at = (dt.datetime(2026, 10, 1) + dt.timedelta(hours=made)).isoformat(timespec="seconds")
    ideas.save_plan(state, s, {"idea": s, "made_at": made_at, "passed_at": None, "todos": [], "tasks": tasks})
    ideas.set_meta(root, s, checks=json.dumps(checks))
    return s


def line(host, idea, step, role, cost, tid="", rnd=1):
    idea_spend.append(host.ideas.state_dir, idea_spend.line(step, role, "claude", "m", "warrior", "", None, cost, tid, rnd), idea=idea)


def price(host, leader="architect", team=("grunt", "tester", "reviewer"), every=(), target="balance"):
    return party_price.price(host.ideas.root(), host.ideas.state_dir, {"target": target}, leader, list(team), list(every))


def test_a_first_guess_with_no_basis_takes_the_defaults_at_the_tiers_the_target_gives(host):
    got = price(host)
    # architect (a leader of the library: elder) 1.00 × 2; 3 tasks at the Grunt's warrior 0.30 and the Tester's laborer 0.05; the Reviewer's elder 1.00 × ½
    base = 2.0 + ACCEPT + 3 * (0.30 + 0.05) / 2 + 1.0 * 0.5
    assert got["learned"] is False and got["ideas"] == 0
    assert got["low"] == pytest.approx(base * 0.5, abs=0.006) and got["high"] == pytest.approx(base * 1.5, abs=0.006)
    assert got["checks"] == [{"by": "reviewer", "name": "Reviewer", "usd": 1.0, "share": 0.5, "every": False}]
    thrift = price(host, target="thrift")                                       # the Target shifts the tiers: the architect a warrior, the Reviewer too
    assert thrift["checks"][0]["usd"] == 0.3 and thrift["high"] < got["high"]
    json.dumps(got)


def test_learned_from_three_priced_ideas_the_steps_the_tasks_and_a_check_s_share(host):
    for n in range(3):                                                                                # 3 ideas: draft 0.4 + plan 0.6, 3 tasks at 0.5, a review at 0.2
        tasks = [task(f"k{i}", "code", "grunt", cost=0.5) for i in (1, 2, 3)] + [task("k4", "review", "reviewer", cost=0.2)]
        s = add(host, f"Idea {n}", tasks, [{"by": "reviewer", "applies": True, "why": "", **({"skipped": True} if n == 2 else {})}], made=n)
        line(host, s, "draft", "architect", 0.4)
        line(host, s, "plan", "architect", 0.6)
        for i in (1, 2, 3):
            line(host, s, "task", "grunt", 0.5, f"k{i}")
        line(host, s, "task", "reviewer", 0.2, "k4")
    got = price(host, team=("grunt", "reviewer"))
    assert got["learned"] is True and got["ideas"] == 3
    assert got["checks"] == [{"by": "reviewer", "name": "Reviewer", "usd": 0.2, "share": 0.67, "every": False}]        # 2 of 3 applied, one skipped
    base = 1.0 + ACCEPT + 3 * 0.5 + 0.2 * (2 / 3)
    assert got["low"] == pytest.approx(base * 0.5, abs=0.006) and got["high"] == pytest.approx(base * 1.5, abs=0.006)
    every = price(host, team=("grunt", "reviewer"), every=["reviewer"])
    assert every["checks"][0]["share"] == 1.0 and every["high"] == pytest.approx((1.0 + ACCEPT + 1.5 + 0.2) * 1.5, abs=0.006)


def test_ideas_party_price_is_the_hosts_and_a_phones_and_checks_the_party(host):
    assert BoardPhone.allowed(host, "ideas.party_price", {})
    got = host.command("ideas.party_price", {"leader": "architect", "team": ["grunt", "tester", "reviewer"], "every": ["reviewer", "not-in-the-team"]})
    json.dumps(got)
    assert got["checks"][0]["every"] is True and got["checks"][0]["share"] == 1.0 and set(got) == {"low", "high", "learned", "ideas", "checks", "hints", "types", "way"} and got["way"] is None
    assert host.command("ideas.party_price", {})["checks"] == []                                      # the Taskmaster alone
    for bad, why in (({"leader": "nobody"}, "No agent"), ({"team": "grunt"}, "list of agents"),
                     ({"leader": "grunt"}, "does not lead")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.party_price", bad)


# -- the goal types the party would be offered (spec 63 §1) --------------------------------------------------------------

def types(host, leader="", team=()):
    """`ideas.party_price`'s `types` as `[(name, missing)]`."""
    got = host.command("ideas.party_price", {"leader": leader, "team": list(team)})["types"]
    return [(t["name"], t["missing"]) for t in got]


def preset(i):
    p = next(p for p in library.PRESETS if p[0] == i)
    return p[4], [*p[5], *p[6]]


def test_the_game_party_is_offered_spec_59s_game_list_each_with_its_sign_and_nothing_missing(host):
    leader, team = preset("game")
    got = host.command("ideas.party_price", {"leader": leader, "team": team})["types"]
    json.dumps(got)
    assert [t["name"] for t in got] == ["New feature", "Fix a bug", "Clean up", "New icon", "New logo", "New mechanic", "New level", "New character", "Balance pass", "New sound"]
    assert all(set(t) == {"id", "name", "sign", "missing"} and t["missing"] == "" for t in got)
    assert got[5] == {"id": "mechanic", "name": "New mechanic", "sign": "mechanic", "missing": ""}
    assert got[-1] == {"id": "sound", "name": "New sound", "sign": "tune", "missing": ""}                  # a sign is the type's, not its id
    assert [t["id"] for t in got] == [t.id for t in goal_types.CATALOG if t.id in {g["id"] for g in got}]    # in the catalog's order


def test_a_size_prices_the_party_at_its_target_and_its_tiers_and_none_at_the_setting(host):
    """Spec 168 H4: a size is no Target of its own: it prices the part of the squad it uses at the setting's Target (spec 75 §3.3 before); without it the whole squad. Spec 81 §2: the
    size's tiers (Seasoned all through for Lean, the leader Veteran for Standard…) are what its seats are priced at."""
    from orkboard.realm import goal_team, party_recipes
    team = ("grunt", "tester", "reviewer", "security-reviewer")

    def at(size, target):         # a size prices the part of the squad it uses (goal_team.price_team), at its tiers
        return party_price.price(host.ideas.root(), host.ideas.state_dir, {"target": target}, "architect", goal_team.price_team(size, list(team)), [], tiers=party_recipes.tiers_for("architect", list(team), size))
    by_size = {s: at(s, "balance") for s in ("lean", "standard", "full")}
    sent = {"leader": "architect", "team": list(team), "every": []}
    for size, want in by_size.items():
        got = host.command("ideas.party_price", {**sent, "size": size})
        assert (got["low"], got["high"]) == (want["low"], want["high"]), size
    assert by_size["lean"]["high"] < by_size["standard"]["high"] < by_size["full"]["high"]
    plain = price(host, team=team)                                                                         # no size: the setting's Target, the roles' own tiers
    assert host.command("ideas.party_price", sent)["high"] == plain["high"]
    host.command("ideas.board_set", {"target": "quality"})
    assert host.command("ideas.party_price", sent)["high"] == price(host, team=team, target="quality")["high"]
    assert host.command("ideas.party_price", {**sent, "size": "lean"})["high"] == at("lean", "quality")["high"]       # a size does not change the Target: the setting's reaches it
    views = [*library.VIEWS, library.SKEPTIC]
    lean = host.command("ideas.party_price", {"leader": "investor", "team": views, "size": "lean"})
    assert lean["pitch"] is True and lean["high"] == host.command("ideas.party_price", {"leader": "investor", "team": views, "size": "full"})["high"]      # a pitch is priced at the setting, a size no Target


def test_the_price_adds_the_leaders_acceptance_one_call_at_the_floor_until_goals_have_priced_it_then_what_they_spent_spec_152_b4(host, monkeypatch):
    from orkboard.realm import idea_target
    monkeypatch.setattr(idea_target, "floor", lambda tier, tool="claude": 0.7)
    state = host.ideas.state_dir
    assert party_price.accept_usd(state, [], "balance") == 0.7                                      # one call at the floor of accept_step's tier
    first = price(host)
    monkeypatch.setattr(idea_target, "floor", lambda tier, tool="claude": 0.0)
    zero = price(host)
    monkeypatch.setattr(idea_target, "floor", lambda tier, tool="claude": 0.7)
    assert first["low"] - zero["low"] == pytest.approx(0.35, abs=0.011) and first["high"] - zero["high"] == pytest.approx(1.05, abs=0.011)      # the price counts the acceptance
    goals = [add(host, f"goal {n}", [task("k1", "code", "grunt")], [], made=n) for n in range(4)]
    line(host, goals[0], "accept_step", "architect", 0.2)
    line(host, goals[1], "accept_step", "architect", 0.4)
    rows = party_price.basis(host.ideas.root(), state)
    assert party_price.accept_usd(state, rows, "balance") == 0.7                                    # two have priced it: still the floor
    line(host, goals[2], "accept_step", "architect", 0.6)
    line(host, goals[2], "accept_step", "architect", 0.2)                                           # a goal's lines are summed: 0.8
    assert party_price.accept_usd(state, rows, "balance") == pytest.approx((0.2 + 0.4 + 0.8) / 3)  # from TOO_FEW goals: what they spent, the mean a goal
    unpriced = add(host, "no price", [task("k1", "code", "grunt")], [], made=9)
    idea_spend.append(state, idea_spend.line("accept_step", "architect", "claude", "m", "elder", "", None, None), idea=unpriced)
    assert party_price.accept_usd(state, party_price.basis(host.ideas.root(), state), "balance") == pytest.approx((0.2 + 0.4 + 0.8) / 3)      # a line with no price says nothing
