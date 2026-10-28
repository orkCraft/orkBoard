"""Spec 75 A (docs/specs/75-parties-fitted-to-the-project.md §3, §4, Tests → A): a party's size is its Target (`target_for`; a goal's task, draft and plan
picking its party's tier; `ideas.goal_save` keeping `size`), `ideas.proposals` (a mobile folder's three proposals with prices rising with size, an
empty folder's ask, its line read by a stub model: `wiki`, garbage → `code`, no model → `read: false`), `project.kind` and the deal in `ideas.map`, the
events (no line of the person's). The model is stubbed."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.core import idea_kind
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, goal_team, idea_target, ideas, library, orkmaster, party_recipes, project_kind

LINE = "Zanzibar-quokka spreadsheet of our team's wiki"          # a person's words nothing may keep


def stub(tier, prompt, effort="", budget=None):
    return json.dumps({"summary": "", "questions": [], "title": "A goal"}), 0.01, 10, ""


@pytest.fixture
def host(fake_repo):
    h = Orkboard(fake_repo)
    h.ideas.keeper.call = stub
    h.root, h.state = h.ideas.root(), h.ideas.state_dir
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def folder(tmp_path: Path, *names: str) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    for n in names:
        (root / n).parent.mkdir(parents=True, exist_ok=True)
        (root / n).write_text("x", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=str(root), check=True, capture_output=True)
    return root


def open_host(root: Path) -> Orkboard:
    h = Orkboard(root)
    h.ideas.keeper.call = stub
    h.root, h.state = h.ideas.root(), h.ideas.state_dir
    return h


@pytest.fixture
def mobile(tmp_path):
    h = open_host(folder(tmp_path, "ios/App.swift", "android/App.kt", "README.md"))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def empty(tmp_path):
    h = open_host(folder(tmp_path, "README.md"))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def events(h, name):
    return [r for r in event_log.read(h.ideas.host.repo_root) if r["event"] == name]


def save(h, **more):
    return h.command("ideas.goal_save", {"title": "Engineering", "about": "Code.", "craft": "engineering", "leader": "architect",
                                         "team": ["grunt", "reviewer"], **more})["slug"]


def track(h, slug):
    return next(t for t in ideas.tracks(h.root, make=False) if t["slug"] == slug)


# -- §3: a party's size is its Target ------------------------------------------------------------------------------------------------

def test_a_sizes_target_else_the_setting():
    assert [idea_target.target_for({"target": "quality"}, {"size": s}) for s in ("lean", "standard", "full")] == ["thrift", "balance", "quality"]
    assert idea_target.target_for({"target": "quality"}, {"size": ""}) == "quality"             # a party made before has no size
    assert idea_target.target_for({"target": "thrift"}, None) == "thrift" and idea_target.target_for({"target": "x"}, {}) == idea_target.DEFAULT
    assert idea_target.target_for({"target": "thrift"}, "full") == "quality" and idea_target.target_for({"target": "thrift"}, "huge") == "thrift"
    assert idea_target.target_for(None, {"size": "lean"}) == "thrift" and idea_target.target_of({"target": "quality"}) == "quality"
    assert idea_target.SIZES == ("lean", "standard", "full")


def test_goal_save_keeps_a_size_on_the_partys_page_and_the_board_reads_it(host):
    h = host
    slug = save(h, size="lean")
    assert track(h, slug)["size"] == "lean" and goal_team.size_of(h.root, slug) == "lean"
    assert "size: lean" in (h.root / ideas.TRACKS / f"{slug}.md").read_text(encoding="utf-8")
    assert h.command("ideas.goal", {"slug": slug})["size"] == "lean"
    assert next(g for g in h.command("ideas.map", {})["goals"] if g["slug"] == slug)["size"] == "lean"
    assert next(g for g in h.command("ideas.board", {})["tracks"] if g["slug"] == slug)["size"] == "lean"
    older = h.command("ideas.goal_save", {"title": "Old", "about": "Old.", "craft": "engineering"})["slug"]            # made without one
    assert track(h, older)["size"] == "" and next(g for g in h.command("ideas.map", {})["goals"] if g["slug"] == older)["size"] == ""
    h.command("ideas.goal_save", {"slug": slug, "about": "Code, changed."})                                         # saved again with none sent: it keeps its size
    assert track(h, slug)["size"] == "lean"


def test_a_size_that_is_none_is_refused(host):
    with pytest.raises(CommandError, match="A size is lean, standard or full"):
        save(host, size="huge")
    with pytest.raises(CommandError, match="A size is lean, standard or full"):
        host.command("ideas.party_price", {"leader": "architect", "team": [], "size": "huge"})


def test_a_resize_says_party_resized_and_a_first_size_says_none(host):
    h = host
    slug = save(h, size="standard")
    assert events(h, "party_resized") == []                                                                       # a new party: no resize
    h.command("ideas.goal_save", {"slug": slug, "size": "full", "device": "phone"})
    h.command("ideas.goal_save", {"slug": slug, "size": "full"})                                                   # the same: nothing
    [row] = events(h, "party_resized")
    assert (row["party"], row["from"], row["to"], row["device"]) == (slug, "standard", "full", "phone")


def test_a_size_that_lets_a_member_with_work_open_go_is_refused_and_one_that_does_not_is_kept(host):
    h = host
    slug = save(h, size="full")
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    ideas.save_state(h.state, idea, state="working")
    ideas.save_plan(h.state, idea, {"idea": idea, "todos": [], "tasks": [{"id": "t1", "title": "T", "state": "running", "role": "grunt", "kind": "code"}]})
    with pytest.raises(CommandError, match="Grunt has work open: it cannot leave"):
        h.command("ideas.goal_save", {"slug": slug, "size": "lean", "leader": "architect", "team": []})
    assert track(h, slug)["size"] == "full" and track(h, slug)["team"] == ["grunt", "reviewer"]
    h.command("ideas.goal_save", {"slug": slug, "size": "standard", "leader": "architect", "team": ["grunt"]})      # (the reviewer has none open)
    assert track(h, slug)["size"] == "standard" and track(h, slug)["team"] == ["grunt"]


def test_a_goals_draft_plan_and_task_pick_their_partys_tier_not_the_settings(host):
    h = host
    lean, full = save(h, size="lean"), save(h, size="full", title="Big")
    old = h.command("ideas.goal_save", {"title": "Older", "about": "Older.", "craft": "engineering"})["slug"]
    h.command("ideas.board_set", {"target": "balance"})
    keeper = h.ideas.keeper
    picked = {}
    for name, party in (("lean", lean), ("full", full), ("old", old)):
        slug = ideas.add_idea(h.root, f"A goal in {name}", party, h.state)
        keeper._tls.key = keeper._tls.slug = slug
        picked[name] = (keeper.target(), keeper.pick("draft"), keeper.pick("plan"))
        keeper._tls.key = keeper._tls.slug = f"goal:{party}"
        picked[name + "_party"] = (keeper.target(), keeper.pick("goal"))
    keeper._tls.key = keeper._tls.slug = ""
    assert keeper.target() == "balance" and picked["old"][0] == "balance"
    assert picked["lean"][0] == "thrift" and picked["lean"][1][1] == "low"
    assert picked["full"][0] == "quality" and picked["full"][1][1] == "high"
    assert picked["old"][1][1] == "medium"
    assert picked["lean_party"][0] == "thrift" and picked["lean_party"][1] == ("warrior", idea_target.pick("goal", "thrift")[1])   # (spec 81: the Lean leader is Seasoned)
    assert picked["full_party"][1][1] == "xhigh"
    # the budget of a call follows the party's Target too
    keeper._tls.key = keeper._tls.slug = ideas.add_idea(h.root, "Another in lean", lean, h.state)
    assert idea_target.budget("draft", keeper.target()) == idea_target.budget("draft", "thrift") < idea_target.budget("draft", "quality")


def test_the_runner_runs_a_task_on_its_partys_target_and_on_the_setting_for_a_party_with_none(host):
    h = host
    lean, full = save(h, size="lean"), save(h, size="full", title="Big")
    old = h.command("ideas.goal_save", {"title": "Older", "about": "Older.", "craft": "engineering"})["slug"]
    ideas_of = {n: ideas.add_idea(h.root, f"A goal in {n}", p, h.state) for n, p in (("lean", lean), ("full", full), ("old", old))}
    runner = h.ideas.runner(need=True)
    task = {"id": "t1", "tier": "warrior", "kind": "code", "role": "grunt"}
    got = {n: runner.ran_on(task, s) for n, s in ideas_of.items()}
    # the Target gives the effort; the party's size gives its seats' tiers (spec 81 §2: Seasoned all through for Lean and for Full's builders)
    assert got["lean"] == idea_target.task_pick("warrior", "thrift", "warrior") == ("warrior", "low")
    assert got["full"] == idea_target.task_pick("warrior", "quality", "warrior") and got["full"][1] == "high"
    assert got["old"] == idea_target.task_pick("warrior", "balance", "") == runner.ran_on(task)
    h.command("ideas.board_set", {"target": "quality"})
    assert runner.ran_on(task, ideas_of["old"]) == ("elder", "high") and runner.ran_on(task, ideas_of["lean"]) == ("warrior", "low")


def test_a_plans_heads_and_the_map_wear_the_partys_tier(host):
    h = host
    lean = save(h, size="lean")
    full = save(h, size="full", title="Big")
    heads = {}
    for name, party in (("lean", lean), ("full", full)):
        idea = ideas.add_idea(h.root, f"A goal {name}", party, h.state)
        ideas.save_state(h.state, idea, state="plan")
        ideas.save_plan(h.state, idea, {"idea": idea, "todos": [], "tasks": [{"id": "t1", "title": "T", "state": "ready", "tier": "warrior", "role": "grunt", "kind": "code"}]})
        node = next(n for n in h.command("ideas.map", {})["nodes"] if n["slug"] == idea)
        heads[name] = h.command("ideas.page", {"slug": idea})["plan"]["tasks"][0]["head"], node["tasks"][0]["head"]
    assert heads["lean"][1]["tier"] == "warrior" and heads["full"][1]["tier"] == "warrior"           # (spec 81: the size's tiers: no seat below Seasoned)
    assert heads["lean"][0]["tier"] == "warrior" and heads["full"][0]["tier"] == "warrior"


def test_the_price_reads_a_sizes_target_and_a_size_sent_changes_it(host):
    h = host
    args = {"leader": "architect", "team": ["grunt", "tester", "reviewer"], "every": []}
    plain = h.command("ideas.party_price", args)
    thrift, quality = h.command("ideas.party_price", {**args, "size": "lean"}), h.command("ideas.party_price", {**args, "size": "full"})
    assert thrift["high"] < plain["high"] < quality["high"]
    assert thrift["high"] < h.command("ideas.party_price", {**args, "size": "standard"})["high"] < quality["high"]       # (its seats at the size's tiers)


# -- §4: the proposals -----------------------------------------------------------------------------------------------------------------

def test_a_mobile_folder_is_proposed_three_parties_each_in_three_sizes_with_prices_rising(mobile):
    h = mobile
    got = h.command("ideas.proposals", {})
    assert got["kind"] == {"id": "mobile", "words": "a mobile app", "signs": ["ios/", "android/"]} and got["ask"] is False and "read" not in got
    assert [p["id"] for p in got["proposals"]] == ["mobile-features", "mobile-architecture", "release"]
    first = got["proposals"][0]
    assert set(first) == {"id", "name", "line", "why", "have", "sizes"} and first["name"] == "Mobile app: features" and first["have"] is False
    assert first["why"].startswith("ios/ and android/ are here") and len(first["why"]) <= 120
    assert list(first["sizes"]) == ["lean", "standard", "full"]
    for p in got["proposals"]:
        lean, std, full = (p["sizes"][s] for s in ("lean", "standard", "full"))
        assert [x["target"] for x in (lean, std, full)] == ["thrift", "balance", "quality"]
        assert set(lean) == {"leader", "team", "agents", "target", "price", "heads", "tiers"}
        assert set(lean["price"]) == {"low", "high"} and all(isinstance(v, float) for v in lean["price"].values())
        assert lean["price"]["high"] <= std["price"]["high"] <= full["price"]["high"] and lean["price"]["low"] <= std["price"]["low"] <= full["price"]["low"]
        for x in (lean, std, full):
            assert x["agents"] == 1 + len(x["team"]) and len(x["heads"]) == x["agents"] and x["leader"] == p["sizes"]["lean"]["leader"]
            assert all(set(hd) == {"race", "tier"} and hd["tier"] in ("laborer", "warrior", "elder") for hd in x["heads"])
        assert goal_team.seats(full["team"], full["leader"]) == ""
    feat = got["proposals"][0]["sizes"]
    assert feat["lean"]["team"] == [] and feat["lean"]["agents"] == 1 and feat["standard"]["team"] == ["grunt"] and feat["standard"]["agents"] == 2 and feat["full"]["team"] == ["grunt", "reviewer"]
    assert feat["lean"]["price"]["high"] < feat["standard"]["price"]["high"] < feat["full"]["price"]["high"]
    assert feat["lean"]["heads"][0] == {"race": "lich", "tier": "warrior"} and feat["standard"]["heads"][0] == {"race": "lich", "tier": "elder"}                                          # the leader first
    release = got["proposals"][2]["sizes"]                                                                          # (spec 81 §2: Release is sized too)
    assert release["lean"]["team"] == [] and len(release["standard"]["team"]) == 1 and len(release["full"]["team"]) == 2 and got["proposals"][2]["name"] == "Release"


def test_a_party_the_project_has_is_proposed_last_as_have(mobile):
    h = mobile
    std = party_recipes.sized(party_recipes.get("mobile-features"), "standard")
    h.command("ideas.goal_save", {"title": "Features", "about": "Features.", "craft": "product", "leader": std["leader"], "team": std["team"]})
    got = h.command("ideas.proposals", {})
    assert [(p["id"], p["have"]) for p in got["proposals"]] == [("mobile-architecture", False), ("release", False), ("mobile-features", True)]
    deal = h.command("ideas.map", {})["project"]["deal"]
    assert [r["id"] for r in deal[:2]] == ["mobile-architecture", "release"] and "mobile-features" not in [r["id"] for r in deal[:2]]


def test_proposals_write_nothing_and_ask_no_model(mobile):
    h = mobile
    h.ideas.keeper.call = lambda *a, **k: (_ for _ in ()).throw(AssertionError("a folder of a known kind asks no model"))
    before = sorted((p, p.stat().st_mtime_ns) for p in list(h.root.rglob("*")) + list(h.state.rglob("*")) if p.is_file() and p.name != "events.jsonl")
    h.command("ideas.proposals", {"about": "ignored: the folder says what it is"})
    assert before == sorted((p, p.stat().st_mtime_ns) for p in list(h.root.rglob("*")) + list(h.state.rglob("*")) if p.is_file() and p.name != "events.jsonl")
    got = h.command("ideas.proposals", {"about": "a team wiki"})
    assert got["kind"]["id"] == "mobile" and "read" not in got


def test_an_empty_folder_asks_its_line_and_is_proposed_ideation(empty):
    got = empty.command("ideas.proposals", {})
    assert got["kind"] == {"id": "empty", "words": "an empty folder", "signs": []} and got["ask"] is True and "read" not in got
    assert [p["id"] for p in got["proposals"]] == ["ideation"] and got["proposals"][0]["sizes"]["lean"]["agents"] == 1 and got["proposals"][0]["sizes"]["full"]["agents"] == 3
    assert empty.command("ideas.proposals", {"about": ""})["ask"] is True and empty.command("ideas.proposals", {"about": "   "})["ask"] is True


class Reads:
    """The keeper's model call, answering the kind's prompt with `answer`; remembers what it was asked and on what."""

    def __init__(self, keeper, answer) -> None:
        self.keeper, self.answer, self.asked = keeper, answer, []

    def __call__(self, tier, prompt, effort="", budget=None):
        tls = self.keeper._tls
        self.asked.append({"tier": tier, "effort": effort, "budget": budget, "prompt": prompt, "tools": getattr(tls, "tools", None),
                           "as": getattr(tls, "as_role", "")})
        if isinstance(self.answer, Exception):
            raise self.answer
        return (self.answer if isinstance(self.answer, str) else json.dumps(self.answer)), 0.01, 40, ""


def test_a_line_is_read_by_one_cheap_call_as_the_orkmaster_into_a_kind_and_ideation_comes_first(empty):
    h = empty
    h.model = h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "wiki"})
    got = h.command("ideas.proposals", {"about": f"  {LINE}  ", "device": "phone"})
    assert got["kind"] == {"id": "wiki", "words": "a team's wiki", "signs": []} and got["ask"] is False and got["read"] is True
    assert [p["id"] for p in got["proposals"]] == ["ideation", "wiki"]
    assert got["proposals"][1]["why"].startswith("by what you said")
    [call] = h.model.asked
    assert call["as"] == orkmaster.ROLE and call["tools"] is False and LINE in call["prompt"]
    assert call["tier"] == "warrior" and call["effort"] == "low" and call["budget"] == idea_target.budget("kind", "balance") == 0.15        # the cheaper tier, as the judge, its budget 1.5 floors (spec 86 §5)
    assert {t: idea_target.MATRIX["kind"][t] for t in ("balance", "quality")} == {t: idea_target.MATRIX["collide"][t] for t in ("balance", "quality")} and "kind" in idea_target.STEPS
    assert orkmaster.role(h.state)["slug"] == "orkmaster" and (h.state / "roles" / "orkmaster.md").is_file()


def test_a_garbled_answer_or_another_kind_is_code_and_the_kind_empty_is_never_asked_for(empty):
    h = empty
    for answer in ("I think it is a wiki, honestly", {"kind": "banana"}, {"kind": "empty"}, {"kind": 7}, {"nothing": 1}, "", "[1, 2]"):
        h.model = h.ideas.keeper.call = Reads(h.ideas.keeper, answer)
        got = h.command("ideas.proposals", {"about": "something"})
        assert got["kind"]["id"] == "code" and got["read"] is True and [p["id"] for p in got["proposals"]] == ["ideation", "engineering-code"], answer
    assert idea_kind.read_answer('prose before {"kind": "game"} and after') == "game"
    assert idea_kind.read_answer(json.dumps({"kind": "data"})) == "data" and "empty" not in idea_kind.ASKED
    assert all(k in project_kind.KINDS for k in idea_kind.ASKED) and len(idea_kind.ASKED) == len(project_kind.KINDS) - 1


def test_no_model_is_codes_proposals_said_so(empty):
    h = empty
    h.ideas.keeper.call = Reads(h.ideas.keeper, RuntimeError("no claude on this machine"))
    got = h.command("ideas.proposals", {"about": "my game"})
    assert got["kind"]["id"] == "code" and got["read"] is False and [p["id"] for p in got["proposals"]] == ["ideation", "engineering-code"]
    assert got["proposals"][1]["why"].startswith("nothing here says more")
    h.ideas.keeper.budget_ok = lambda: False                                                    # today's spend limit
    h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "game"})
    again = h.command("ideas.proposals", {"about": "my game"})
    assert again["read"] is False and again["kind"]["id"] == "code" and h.ideas.keeper.call.asked == []


def test_a_demo_reads_no_line(empty):
    h = empty
    h.ideas.host.demo = True
    h.ideas.keeper.demo = True
    h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "game"})
    got = h.command("ideas.proposals", {"about": "my game"})
    assert got["read"] is False and h.ideas.keeper.call.asked == []


def test_the_line_is_cut_to_three_hundred_characters_and_must_be_text(empty):
    h = empty
    h.model = h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "game"})
    h.command("ideas.proposals", {"about": "x" * 900})
    assert "x" * 300 in h.model.asked[0]["prompt"] and "x" * 301 not in h.model.asked[0]["prompt"]
    with pytest.raises(CommandError, match="about is not text"):
        h.command("ideas.proposals", {"about": 7})


def test_the_events_hold_the_kind_and_the_recipe_never_the_line(empty, tmp_path):
    h = empty
    h.model = h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "wiki"})
    h.command("ideas.proposals", {})
    h.command("ideas.proposals", {"about": LINE, "device": "phone"})
    shown = events(h, "proposals_shown")
    assert [(r["kind"], r["n"], r["ask"], r["read"]) for r in shown] == [("empty", 1, True, None), ("wiki", 2, False, True)] and shown[1]["device"] == "phone"
    std = party_recipes.sized(party_recipes.get("wiki"), "standard")
    h.command("ideas.goal_save", {"title": "Wiki", "about": "The team's pages.", "craft": "product", "leader": std["leader"], "team": std["team"],
                                  "size": "standard", "proposal": "wiki"})
    [taken] = events(h, "proposal_taken")
    assert (taken["recipe"], taken["size"], taken["kind"]) == ("wiki", "standard", "wiki")
    log = event_log.path(h.ideas.host.repo_root).read_text(encoding="utf-8")
    assert "Zanzibar" not in log and "quokka" not in log
    for path in h.state.rglob("*"):                                                             # nor the ledger, nor any file of the Board's
        if path.is_file():
            assert "Zanzibar" not in path.read_text(encoding="utf-8", errors="ignore"), path
    assert event_log.PROPOSALS_SHOWN == "proposals_shown" and event_log.PROPOSAL_TAKEN == "proposal_taken" and event_log.PARTY_RESIZED == "party_resized"
    assert {event_log.PROPOSALS_SHOWN, event_log.PROPOSAL_TAKEN, event_log.PARTY_RESIZED} <= set(event_log.EVENTS)


def test_the_calls_spend_is_the_boards_own_and_names_no_goal(empty):
    from orkboard.realm import idea_spend
    h = empty
    h.model = h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "game"})
    h.command("ideas.proposals", {"about": "my game"})
    rows = [r for p in h.state.rglob("*.jsonl") for r in idea_spend.read(p)]
    mine = [r for r in rows if r.get("step") == "kind"]
    assert len(mine) == 1 and mine[0]["role"] == "orkmaster"


def test_a_proposal_taken_from_a_preset_id_is_counted_and_a_party_made_otherwise_is_not(mobile):
    h = mobile
    std = party_recipes.sized(party_recipes.get("release"), "standard")
    h.command("ideas.goal_save", {"title": "Release", "about": "Out.", "craft": "product", "leader": std["leader"], "team": std["team"], "size": "standard", "preset": "release"})
    h.command("ideas.goal_save", {"title": "Mine", "about": "Mine.", "craft": "engineering", "leader": "architect", "team": ["grunt"], "size": "lean"})
    h.command("ideas.goal_save", {"title": "Mine too", "about": "Mine.", "craft": "engineering"})
    assert [(r["kind"], r["recipe"], r["size"]) for r in events(h, "proposal_taken")] == [("mobile", "release", "standard")]


# -- §4.3: the map ----------------------------------------------------------------------------------------------------------------------

def test_the_map_carries_the_kind_with_no_call_and_the_deal_puts_the_proposals_first(mobile):
    h = mobile
    project = h.command("ideas.map", {})["project"]
    assert project["kind"] == {"id": "mobile", "words": "a mobile app", "signs": ["ios/", "android/"]}
    ids = [r["id"] for r in project["deal"]]
    assert ids[:3] == ["mobile-features", "mobile-architecture", "release"] and sorted(ids) == sorted(
        {*[p["id"] for p in library.presets()], "mobile-features", "mobile-architecture"})
    assert project["deal"][0] == {"id": "mobile-features", "why": "proposal", "n": 0}
    assert project["deal"][2]["id"] == "release"                                               # a preset's row keeps the deal's own


def test_an_empty_folders_deal_is_ideation_first_and_a_known_kind_costs_one_read(empty, monkeypatch):
    h = empty
    assert h.command("ideas.map", {})["project"]["deal"][0] == {"id": "ideation", "why": "no_pitches", "n": 0}
    calls = []
    real = project_kind.scan
    monkeypatch.setattr(project_kind, "scan", lambda r: calls.append(r) or real(r))
    for _ in range(4):
        h.command("ideas.map", {})
    assert len(calls) <= 1                                                                      # kept by the root and its top level's times


def test_deal_first_is_the_deal_when_the_kind_proposes_nothing_new():
    deal = [{"id": "ideation", "why": "have", "n": 0}, {"id": "game", "why": "", "n": 0}]
    tracks = [{"leader": "investor", "team": [*library.VIEWS, library.SKEPTIC]}]
    assert orkmaster.deal_first(deal, tracks, "empty", {}) == deal
    assert [r["id"] for r in orkmaster.deal_first(deal, [], "empty", {})] == ["ideation", "game"]


def test_a_party_made_before_keeps_its_saved_team_and_a_size_gives_one_seat_a_stage_spec_87(host):
    h = host
    old = save(h, title="Older")
    goal_team.set_team(h.root, old, ["grunt", "tester", "reviewer", "security-reviewer"])                          # made when a party had three builders and two checkers
    h.command("ideas.goal_save", {"slug": old, "about": "Code, changed."})                                           # saved again with no team sent: kept
    assert track(h, old)["team"] == ["grunt", "tester", "reviewer", "security-reviewer"]
    h.command("ideas.goal_save", {"slug": old, "team": ["grunt", "tester", "reviewer", "security-reviewer"], "leader": "architect"})    # sent as it is: kept, not refused
    assert track(h, old)["team"] == ["grunt", "tester", "reviewer", "security-reviewer"]
    sizes = h.command("ideas.party_sizes", {"slug": old})["sizes"]
    assert sizes["lean"]["team"] == [] and sizes["standard"]["team"] == ["grunt"] and sizes["full"]["team"] == ["grunt", "reviewer"]
    assert [x["slug"] for x in sizes["standard"]["leaves"]] == ["tester", "reviewer", "security-reviewer"]                               # the switch says who leaves …
    assert track(h, old)["team"] == ["grunt", "tester", "reviewer", "security-reviewer"]                            # … and takes no one away by itself
    assert sizes["full"]["tiers"] == {"architect": "elder", "grunt": "warrior", "reviewer": "elder"}
    h.command("ideas.goal_save", {"slug": old, "size": "standard"})                                                  # pressed: the size's team
    assert track(h, old)["team"] == ["grunt"] and goal_team.tiers_of(h.root, old) == {"architect": "elder", "grunt": "warrior"}
