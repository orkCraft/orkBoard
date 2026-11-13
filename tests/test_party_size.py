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

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, goal_team, idea_target, ideas, orkmaster, party_recipes

APP = ["product", "design", "tech", "release", "run", "marketing"]          # one craft a party (spec 99 §1.1): what every kind but a game proposes

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


# -- §3: a party's size is no Target of its own (spec 168 H4, decisions §283.33) ------------------------------------------------------------------------------------------------

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


def test_a_size_that_lets_a_member_with_work_open_go_is_refused_and_one_that_does_not_is_kept(host):
    h = host
    slug = save(h, size="full")
    idea = ideas.add_idea(h.root, "A goal", slug, h.state)
    ideas.save_state(h.state, idea, state="working")
    ideas.save_plan(h.state, idea, {"idea": idea, "todos": [], "tasks": [{"id": "t1", "title": "T", "state": "running", "role": "grunt", "kind": "code"}]})
    with pytest.raises(CommandError, match="Grunt has work open: it cannot leave"):
        h.command("ideas.goal_save", {"slug": slug, "size": "lean", "leader": "architect", "team": ["tester"]})
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
    assert [picked[n][0] for n in ("lean", "full", "old")] == ["balance"] * 3                  # the size is no Target: every party works at *How deep*
    assert picked["lean"][1:] == picked["full"][1:] == picked["old"][1:] and picked["lean"][1][1] == "medium"
    assert picked["lean_party"] == picked["full_party"] == ("balance", idea_target.pick("goal", "balance"))
    h.command("ideas.board_set", {"target": "quality"})
    keeper._tls.key = keeper._tls.slug = ideas.add_idea(h.root, "Another in lean", lean, h.state)
    assert keeper.target() == "quality" and keeper.pick("draft")[1] == "high"


def test_the_runner_runs_a_task_on_its_partys_target_and_on_the_setting_for_a_party_with_none(host):
    h = host
    lean, full = save(h, size="lean"), save(h, size="full", title="Big")
    old = h.command("ideas.goal_save", {"title": "Older", "about": "Older.", "craft": "engineering"})["slug"]
    ideas_of = {n: ideas.add_idea(h.root, f"A goal in {n}", p, h.state) for n, p in (("lean", lean), ("full", full), ("old", old))}
    runner = h.ideas.runner(need=True)
    task = {"id": "t1", "tier": "warrior", "kind": "code", "role": "grunt"}
    got = {n: runner.ran_on(task, s) for n, s in ideas_of.items()}
    # the Target gives the effort; the party's size gives its seats' tiers (spec 81 §2: Seasoned all through for Lean and for Full's builders)
    assert got["lean"] == got["full"] == idea_target.task_pick("warrior", "balance", "warrior") == ("warrior", "medium")      # the size gives the seats' tiers, never a Target
    assert got["old"] == idea_target.task_pick("warrior", "balance", "") == runner.ran_on(task)
    h.command("ideas.board_set", {"target": "quality"})
    assert runner.ran_on(task, ideas_of["old"]) == ("elder", "high") and runner.ran_on(task, ideas_of["lean"]) == ("warrior", "high")


# -- §4: the proposals -----------------------------------------------------------------------------------------------------------------

def test_a_mobile_folder_is_proposed_three_parties_each_in_three_sizes_with_prices_rising(mobile):
    h = mobile
    got = h.command("ideas.proposals", {})
    assert got["kind"] == {"id": "mobile", "words": "a mobile app", "signs": ["ios/", "android/"]} and got["ask"] is False and "read" not in got
    assert [p["id"] for p in got["proposals"]] == APP
    first = got["proposals"][0]
    assert set(first) == {"id", "name", "line", "why", "craft", "from", "size", "squad", "locked", "have", "sizes"} and first["name"] == "Product" and first["have"] is False
    assert (first["craft"], first["from"], first["size"], first["locked"]) == ("product", "idea", "lean", False) and first["squad"] == party_recipes.squad_of(party_recipes.get("product"))
    assert first["why"].startswith("ios/ and android/ are here") and len(first["why"]) <= 120
    assert list(first["sizes"]) == ["lean", "standard", "full"]
    for p in got["proposals"]:
        lean, std, full = (p["sizes"][s] for s in ("lean", "standard", "full"))
        assert [x["target"] for x in (lean, std, full)] == ["balance"] * 3                              # a size is no Target: the setting's
        assert set(lean) == {"leader", "team", "agents", "target", "price", "heads", "tiers"}
        assert set(lean["price"]) == {"low", "high"} and all(isinstance(v, float) for v in lean["price"].values())
        assert lean["price"]["high"] <= std["price"]["high"] <= full["price"]["high"] and lean["price"]["low"] <= std["price"]["low"] <= full["price"]["low"]
        for x in (lean, std, full):
            assert x["agents"] == 1 + len(x["team"]) and len(x["heads"]) == x["agents"] and x["leader"] == p["sizes"]["lean"]["leader"]
            assert all(set(hd) == {"race", "tier"} and hd["tier"] in ("laborer", "warrior", "elder") for hd in x["heads"])
        assert goal_team.seats(full["team"], full["leader"]) == ""
    feat = got["proposals"][0]["sizes"]
    squad = first["squad"]
    assert feat["lean"]["team"] == feat["standard"]["team"] == feat["full"]["team"] == squad and feat["lean"]["agents"] == 1 + len(squad)       # the squad and the size are apart
    assert feat["lean"]["price"]["high"] < feat["standard"]["price"]["high"] < feat["full"]["price"]["high"]
    assert feat["lean"]["heads"][0] == {"race": "unicorn", "tier": "elder"} and feat["standard"]["heads"][0] == {"race": "unicorn", "tier": "elder"}     # the leader first: Product's higher form
    assert {h["race"] for h in feat["standard"]["heads"][1:]} == {"knight"}                                          # its seats, the knights (decisions §162)
    tech = {p["id"]: p for p in got["proposals"]}["tech"]["sizes"]["full"]["heads"]
    assert tech[0] == {"race": "shaman", "tier": "elder"} and {h["race"] for h in tech[1:]} == {"peon"}
    release = got["proposals"][3]                                                                                   # Release: in every project, its leader alone, locked
    assert release["id"] == "release" and release["name"] == "Release" and release["locked"] is False and release["squad"] == ["release-engineer", "release-notes"]
    assert [release["sizes"][s]["team"] for s in ("lean", "standard", "full")] == [["release-engineer", "release-notes"]] * 3
    assert release["sizes"]["full"]["heads"] == [{"race": "lich", "tier": "warrior"}, {"race": "skeleton", "tier": "warrior"}, {"race": "skeleton", "tier": "warrior"}]


def test_proposals_write_nothing_and_ask_no_model(mobile):
    h = mobile
    h.ideas.keeper.call = lambda *a, **k: (_ for _ in ()).throw(AssertionError("a folder of a known kind asks no model"))
    before = sorted((p, p.stat().st_mtime_ns) for p in list(h.root.rglob("*")) + list(h.state.rglob("*")) if p.is_file() and p.name != "events.jsonl")
    h.command("ideas.proposals", {"about": "ignored: the folder says what it is"})
    assert before == sorted((p, p.stat().st_mtime_ns) for p in list(h.root.rglob("*")) + list(h.state.rglob("*")) if p.is_file() and p.name != "events.jsonl")
    got = h.command("ideas.proposals", {"about": "a team wiki"})
    assert got["kind"]["id"] == "mobile" and "read" not in got


def test_an_empty_folder_asks_its_line_and_is_proposed_the_crafts_never_ideation(empty):
    got = empty.command("ideas.proposals", {})
    assert got["kind"] == {"id": "empty", "words": "an empty folder", "signs": []} and got["ask"] is True and "read" not in got
    assert [p["id"] for p in got["proposals"]] == APP and got["proposals"][0]["sizes"]["lean"]["agents"] == got["proposals"][0]["sizes"]["full"]["agents"] == 1 + len(got["proposals"][0]["squad"])
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


def test_a_line_is_read_by_one_cheap_call_as_the_orkmaster_into_a_kind(empty):
    h = empty
    h.model = h.ideas.keeper.call = Reads(h.ideas.keeper, {"kind": "wiki"})
    got = h.command("ideas.proposals", {"about": f"  {LINE}  ", "device": "phone"})
    assert got["kind"] == {"id": "wiki", "words": "a team's wiki", "signs": []} and got["ask"] is False and got["read"] is True
    assert [p["id"] for p in got["proposals"]] == APP                                           # (Ideation is never proposed: decisions §122.3)
    assert got["proposals"][0]["why"].startswith("by what you said")
    [call] = h.model.asked
    assert call["as"] == orkmaster.ROLE and call["tools"] is False and LINE in call["prompt"]
    assert call["tier"] == "warrior" and call["effort"] == "low" and call["budget"] == idea_target.budget("kind", "balance") == 0.15        # the cheaper tier, as the judge, its budget 1.5 floors (spec 86 §5)
    assert {t: idea_target.MATRIX["kind"][t] for t in ("balance", "quality")} == {t: idea_target.MATRIX["collide"][t] for t in ("balance", "quality")} and "kind" in idea_target.STEPS
    assert orkmaster.role(h.state)["slug"] == "orkmaster" and (h.state / "roles" / "orkmaster.md").is_file()


# -- §4.3: the map ----------------------------------------------------------------------------------------------------------------------

def test_the_map_carries_the_kind_with_no_call_and_the_deal_puts_the_proposals_first(mobile):
    h = mobile
    project = h.command("ideas.map", {})["project"]
    assert project["kind"] == {"id": "mobile", "words": "a mobile app", "signs": ["ios/", "android/"]}
    ids = [r["id"] for r in project["deal"]]
    assert ids[:6] == APP and sorted(ids) == sorted(party_recipes.CRAFTS)                         # one craft a party: the deal has no mixed preset and no Ideation
    assert project["deal"][0] == {"id": "product", "why": "", "n": 0}
    assert project["deal"][3]["id"] == "release"                                               # a craft's row keeps the deal's own


def test_a_party_made_before_keeps_its_saved_team_and_a_size_changes_its_tiers_never_its_squad(host):
    h = host
    old = save(h, title="Older")
    goal_team.set_team(h.root, old, ["grunt", "tester", "reviewer", "security-reviewer"])                          # made when a party had three builders and two checkers
    h.command("ideas.goal_save", {"slug": old, "about": "Code, changed."})                                           # saved again with no team sent: kept
    assert track(h, old)["team"] == ["grunt", "tester", "reviewer", "security-reviewer"]
    h.command("ideas.goal_save", {"slug": old, "team": ["grunt", "tester", "reviewer", "security-reviewer"], "leader": "architect"})    # sent as it is: kept, not refused
    assert track(h, old)["team"] == ["grunt", "tester", "reviewer", "security-reviewer"]
    sizes = h.command("ideas.party_sizes", {"slug": old})["sizes"]
    team = ["grunt", "tester", "reviewer", "security-reviewer"]
    assert sizes["lean"]["team"] == sizes["standard"]["team"] == sizes["full"]["team"] == team                       # the squad and the size are apart (spec 99 §1.3)
    assert all(sizes[k]["joins"] == [] and sizes[k]["leaves"] == [] for k in sizes) and track(h, old)["team"] == team      # the switch joins no one and takes no one away
    assert sizes["full"]["tiers"] == {"architect": "elder", "grunt": "warrior", "tester": "warrior", "reviewer": "elder", "security-reviewer": "elder"}
    h.command("ideas.goal_save", {"slug": old, "size": "standard"})                                                  # pressed: the size's tiers
    assert track(h, old)["team"] == team and goal_team.tiers_of(h.root, old) == {"architect": "elder", "grunt": "warrior"}
