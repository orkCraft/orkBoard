"""Spec 99 E (docs/specs/99-a-goals-way.md §7) on the keeper: every leader on the route writes its section at once (the first step's on its party's tier, the others on the cheaper
one), the Orkmaster joins them without changing a word (a *Gist* and the forks), a disagreement is a fork in the person's hand, its answer writes again only the sections it
changes, and with nothing to settle the plan follows and the goal starts as it always did. The model call is stubbed (`keeper.call`)."""
from __future__ import annotations

import json
import sys
import threading
import time

import pytest

from orkboard.core import idea_keeper
from orkboard.core.idea_sections import clean_join
from orkboard.gui.board_host import Orkboard
from orkboard.realm import goal_team, idea_questions, idea_target, ideas, library, map_text, spec_sections


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.command("ideas.board_set", {"autostart": False})                      # a plan made waits for the person unless a test says otherwise
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


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
            "tech": _party(host, "Tech", "architect", ["grunt", "tester"], "engineering")}


def section(why="Because.", done=("It works",), will=("changed src — the theme",), risk="low", **more):
    return {"why": why, "done_when": list(done), "checks": [], "will_be": list(will), "out": [], "risks": [], "risk": risk, **more}


PLAN = {"tasks": [{"id": "k1", "title": "Do it", "brief": "Do the thing.", "kind": "code", "tier": "warrior", "after": []}], "todos": []}
DECISION = {"title": "Dark mode ships as a setting", "why": "People read at night.", "points": ["Product asks for it.", "Tech adds it."]}


class Model:
    """The keeper's call stubbed: `said[(step, party)]` the JSON answered (or a callable of the call), `calls` every call made, each with when it began and ended."""

    def __init__(self, host):
        self.host, self.calls, self.said, self.lock = host, [], {}, threading.Lock()
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        row = {"tier": tier, "prompt": prompt, "effort": effort, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"], "party": getattr(k._tls, "party", ""),
               "as_role": getattr(k._tls, "as_role", ""), "thread": threading.current_thread().name, "at": time.monotonic()}
        with self.lock:
            self.calls.append(row)
        time.sleep(0.1)                                          # long enough for the calls of a step to overlap
        row["end"] = time.monotonic()
        answer = self.said.get((row["step"], row["party"]), self.said.get((row["step"], "")))
        if callable(answer):
            answer = answer(row)
        if isinstance(answer, str):
            return answer, 0.01, 10, ""
        return json.dumps(answer if answer is not None else {"title": "A goal", "questions": []}), 0.01, 10, ""

    def steps(self, step):
        return [c for c in self.calls if c["step"] == step]


@pytest.fixture
def model(host, parties):
    m = Model(host)
    m.said[("decide", "")] = DECISION
    m.said[("section_first", "")] = section("Product's why.", ["Players can pick a theme"], ["changed src/ui — the settings screen"])
    m.said[("section", "")] = section("Tech's why.", ["The theme is one file"], ["changed src — the theme file", "new src/theme"])
    m.said[("join", "")] = {"gist": "Dark mode as a setting", "forks": []}
    m.said[("plan", "")] = PLAN
    return m


def _state(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def _until(host, slug, state, seconds=15):
    for _ in range(int(seconds * 100)):
        if _state(host, slug)["state"] == state and not host.ideas.keeper.busy(slug):
            return
        time.sleep(0.01)
    raise AssertionError(f"the goal never reached {state}: {_state(host, slug)['state']} {_state(host, slug)['error']}")


def _row(host, slug, kind):
    return next((n for n in host.command("ideas.board")["needs_you"] if n["idea"] == slug and n["kind"] == kind), None)


def _page(host, slug):
    return ideas.idea_page(host.ideas.root(), slug)


def _confirmed(host, parties, model, which=("product", "tech"), until="plan", text="add a dark mode option", per=0):
    """A goal through Talk and the decision to *Confirm and start*; returns its slug once it is at `until`."""
    for who in which:
        model.said[("talk_round", parties[who])] = {"stance": f"{who} stance", "for": "f", "against": "a", "second_round": False,
                                                    "questions": [{"ask": f"{who} question {n}", "choices": ["A", "B"], "pick": 0, "why": "because", "blocks": False} for n in range(per)]}
    slug = host.command("ideas.add", {"text": text, "track": parties[which[0]]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties[w] for w in which]})
    host.command("ideas.talk", {"idea": slug})
    if per:
        for _ in range(1000):
            if _row(host, slug, "talk"):
                break
            time.sleep(0.01)
        host.command("ideas.talk_answer", {"idea": slug, "answers": [], "decide": True})
    _until(host, slug, "decided")
    host.command("ideas.confirm", {"idea": slug})
    _until(host, slug, until)
    return slug


# -- the join, strictly -------------------------------------------------------------------------------------------------------------------

def test_a_joins_answer_is_a_gist_and_forks_of_the_routes_parties_and_nothing_else():
    leaders = {"product": "product-manager", "tech": "architect"}
    got = clean_join({"gist": "  Dark   mode ", "sections": {"Tech": "rewritten"},
                      "forks": [{"about": "The waves", "sides": [{"party": "product", "says": "ten", "why": "pace"}, {"party": "tech", "says": "six", "why": "the server"},
                                                                 {"party": "nobody", "says": "x"}, {"party": "tech", "says": "again"}]},
                                {"about": "One side only", "sides": [{"party": "tech", "says": "x"}]}, {"about": "", "sides": []}, "junk"]}, leaders)
    assert got == {"gist": "Dark mode", "forks": [{"about": "The waves", "sides": [{"party": "product", "leader": "product-manager", "says": "ten", "why": "pace"},
                                                                                   {"party": "tech", "leader": "architect", "says": "six", "why": "the server"}]}]}
    assert clean_join("no", leaders) is None and clean_join({"gist": "g"}, leaders) == {"gist": "g", "forks": []}
    many = [{"about": f"a{n}", "sides": [{"party": "product", "says": "x"}, {"party": "tech", "says": "y"}]} for n in range(6)]
    assert len(clean_join({"forks": many}, leaders)["forks"]) == 3


# -- every leader at once, the join, the page ----------------------------------------------------------------------------------------------

def test_every_leader_writes_its_section_at_once_the_first_on_its_partys_tier_and_the_others_on_the_cheaper(host, parties, model, monkeypatch):
    monkeypatch.setattr(map_text, "of", lambda party, *a, **k: "THE MAP OF " + party if party == "tech" else None)
    monkeypatch.setattr(map_text, "detail", lambda *a, **k: "THE PARTS IN DETAIL")
    slug = _confirmed(host, parties, model, ("product", "design", "tech"), per=1, text="add a dark mode option in src/app.py")
    first, others = model.steps("section_first"), model.steps("section")
    assert [c["party"] for c in first] == [parties["product"]] and sorted(c["party"] for c in others) == sorted([parties["design"], parties["tech"]])
    calls = first + others
    assert len({c["thread"] for c in calls}) == 3 and max(c["at"] for c in calls) < min(c["end"] for c in calls)           # a thread each, all begun before any ended
    assert (first[0]["tier"], first[0]["effort"]) == idea_target.pick("section_first", "balance") == idea_target.pick("draft", "balance") == ("elder", "medium")
    assert all((c["tier"], c["effort"]) == idea_target.pick("section", "balance") == ("warrior", "low") for c in others) and all(c["tools"] is True for c in calls)
    tech = next(c for c in calls if c["party"] == parties["tech"])["prompt"]
    assert "add a dark mode option in src/app.py" in tech and "Read at most 6 files" in tech and "src/app.py" in tech                 # the words, the reads bounded, the files they name
    assert "THE MAP OF tech" in tech and "THE PARTS IN DETAIL" in tech and "## 1. Dark mode ships as a setting" in tech            # the map, the parts, the decision's entry
    assert "tech question 0 — A" in tech and "Product, then Design, then Tech" in tech and "You are" in tech                       # the answers, the route, its voice
    assert "THE MAP OF" not in next(c for c in calls if c["party"] == parties["product"])["prompt"]                              # a party with no map is given none


def test_the_page_is_the_common_part_and_a_section_a_party_each_its_leaders_words_untouched(host, parties, model):
    model.said[("join", "")] = {"gist": "Dark mode as a setting", "forks": [], "sections": {"Tech": "REWRITTEN BY THE JOIN"}, "Tech": "REWRITTEN"}
    slug = _confirmed(host, parties, model, ("product", "tech"), text="add a dark mode option")
    page = _page(host, slug)
    names = [n for n, _t in page.sections if n not in ("Risks", "Stages")]     # (the plan of today writes a risk line under a flat *Risks* and its *Stages*: part H drops them)
    assert names[:5] == ["Asked", "Gist", "Route", "Depends on", "Decisions"] and names[5:7] == ["Product", "Tech"]
    assert page.section("Asked") == "add a dark mode option" and page.section("Gist") == "Dark mode as a setting"                   # the person's words as they are; one line at the join
    assert page.section("Route").splitlines()[0].startswith("1. Product · ") and page.section("Route").splitlines()[1].startswith("2. Tech · ")
    assert "Decision 1: Dark mode ships as a setting" in page.section("Decisions")
    parts = page.parts("Tech")
    assert parts["Why"] == "Tech's why." and parts["Done when"] == "- The theme is one file" and parts["Will be"] == "- changed src — the theme file\n- new src/theme"
    assert "REWRITTEN" not in page.text() and spec_sections.join(parts) == page.section("Tech")                                 # the join cannot change a word
    assert not any(n in ("Why", "Done when", "Out", "Open questions") for n, _t in page.sections)                # the empty old sections went
    read = spec_sections.read(page, [{"slug": s, "title": t} for s, t in ((parties["product"], "Product"), (parties["tech"], "Tech"))])
    assert [s.party for s in read["sections"]] == [parties["product"], parties["tech"]] and not any(s.older for s in read["sections"])


def test_the_join_is_the_orkmasters_on_the_cheaper_tier_with_no_tools_given_each_sections_theses_and_what_changes(host, parties, model):
    slug = _confirmed(host, parties, model, ("product", "tech"))
    join = model.steps("join")
    assert len(join) == 1 and join[0]["tools"] is False and join[0]["as_role"] == "orkmaster" and (join[0]["tier"], join[0]["effort"]) == idea_target.pick("route", "balance")
    p = join[0]["prompt"]
    assert "Players can pick a theme" in p and "The theme is one file" in p and "changed src/ui" in p and "new src/theme" in p and "Read no file" in p
    assert f"id {parties['product']}" in p and f"id {parties['tech']}" in p and "you change none of their words" in p
    assert spec_sections.record(host.ideas.state_dir, slug)["joined"] is True


def test_a_goal_of_one_party_has_no_join_its_gist_is_its_words_first_line_and_it_lies_in_its_party(host, parties, model):
    slug = _confirmed(host, parties, model, ("tech",), text="add a dark mode option\nand more words")
    assert model.steps("join") == [] and [c["step"] for c in model.calls if c["step"].startswith("section")] == ["section_first"]
    page = _page(host, slug)
    assert page.section("Asked") == "add a dark mode option\nand more words" and page.section("Gist") == "add a dark mode option"
    assert [n for n, _t in page.sections if spec_sections.is_party(n, _t)] == ["Tech"] and "1. Tech · " in page.section("Route")


def test_a_goal_lies_in_its_first_steps_party_which_plans_it(host, parties, model):
    slug = host.command("ideas.add", {"text": "add a dark mode option", "track": parties["tech"]})["slug"]
    host.command("ideas.route_set", {"idea": slug, "route": [parties["product"], parties["tech"]]})            # the route's edit: Product first
    model.said[("talk_round", "")] = {"stance": "s", "for": "f", "against": "a", "second_round": False, "questions": []}
    host.command("ideas.talk", {"idea": slug})
    _until(host, slug, "decided")
    host.command("ideas.confirm", {"idea": slug})
    _until(host, slug, "plan")
    assert _page(host, slug).get("track") == parties["product"]


def test_touches_and_the_risk_come_from_the_sections_and_a_high_risk_waits_for_the_person(host, parties, model, monkeypatch):
    host.command("ideas.board_set", {"autostart": True})
    passed = []
    monkeypatch.setattr(host.ideas, "pass_plan", lambda slug, by, args=None: passed.append((slug, by)))
    model.said[("section", "")] = section("Tech's why.", ["The theme is one file"], ["changed src/theme", "new src/dark", "gone src/old", "nonsense line"], risk="high")
    slug = _confirmed(host, parties, model, ("product", "tech"))
    page = _page(host, slug)
    assert json.loads(page.get("touches")) == ["src/ui", "src/theme", "src/dark", "src/old"] and page.get("risk_model") == "high"
    assert passed == []                                                                                                  # a high risk waits for the person (idea_risk.decide)


# -- the plan and the start ----------------------------------------------------------------------------------------------------------------

def test_with_nothing_to_settle_the_plan_follows_and_the_goal_starts_by_itself_as_it_always_did(host, parties, model, monkeypatch):
    host.command("ideas.board_set", {"autostart": True})
    passed = []
    monkeypatch.setattr(host.ideas, "pass_plan", lambda slug, by, args=None: passed.append((slug, by)))
    slug = _confirmed(host, parties, model, ("product", "tech"))
    assert [c["step"] for c in model.calls if c["step"] == "plan"] == ["plan"] and ideas.plan(host.ideas.state_dir, slug) is not None
    assert passed == [(slug, "auto")]
    plan = model.steps("plan")[0]["prompt"]
    assert "Players can pick a theme" in plan and "The theme is one file" in plan                                                  # today's plan reads the new spec's Done when


def test_the_first_steps_plan_reads_its_own_section_whole_and_of_the_others_only_done_when_and_will_be(host, parties, model):
    """Spec 99 §9.1 (H): the plan no longer reads the sections folded as the old page's; the first step's party plans from its section whole."""
    slug = _confirmed(host, parties, model, ("product", "tech"))
    prompt = model.steps("plan")[0]["prompt"]
    assert "Your section, Product, whole:" in prompt and "Product's why." in prompt and "Players can pick a theme" in prompt and "changed src/ui" in prompt
    assert "The section Tech of another party: only its Done when and Will be" in prompt and "The theme is one file" in prompt and "new src/theme" in prompt
    assert "Tech's why." not in prompt and "Dark mode as a setting" in prompt
    assert [t["party"] for t in ideas.plan(host.ideas.state_dir, slug)["tasks"]] == [parties["product"]]


def test_a_plan_that_cannot_be_made_leaves_the_spec_ready_as_the_drafts_did(host, parties, model):
    model.said[("plan", "")] = "no plan at all"
    slug = _confirmed(host, parties, model, ("tech",), until="ready")
    assert _state(host, slug)["error"].startswith("No plan:") and ideas.plan(host.ideas.state_dir, slug) is None


# -- the forks -------------------------------------------------------------------------------------------------------------------------------

def _fork(party_a, party_b, about="How many waves"):
    return {"about": about, "sides": [{"party": party_a, "says": "Ten waves", "why": "the pace"}, {"party": party_b, "says": "Six waves", "why": "the server holds six"}]}


def test_a_disagreement_is_a_fork_in_the_row_and_the_goal_waits_for_the_person_no_plan_is_made(host, parties, model):
    model.said[("join", "")] = {"gist": "Waves", "forks": [_fork(parties["product"], parties["tech"])]}
    slug = _confirmed(host, parties, model, ("product", "tech"), until="sections")
    row = _row(host, slug, "fork")
    assert row == {**row, "kind": "fork", "idea": slug, "about": "How many waves", "id": "f1", "text": "How many waves",
                   "sides": [{"party": parties["product"], "leader": "product-manager", "says": "Ten waves", "why": "the pace"},
                             {"party": parties["tech"], "leader": "architect", "says": "Six waves", "why": "the server holds six"}]}
    assert model.steps("plan") == [] and ideas.plan(host.ideas.state_dir, slug) is None and _row(host, slug, "decision") is None
    assert _page(host, slug).section("Gist") == "Waves"


def test_a_side_picked_writes_again_only_the_other_sides_section_and_names_them_in_decisions_then_the_plan_waits_for_start(host, parties, model, monkeypatch):
    host.command("ideas.board_set", {"autostart": True})
    passed = []
    monkeypatch.setattr(host.ideas, "pass_plan", lambda slug, by, args=None: passed.append((slug, by)))
    model.said[("join", "")] = {"gist": "Waves", "forks": [_fork(parties["product"], parties["tech"])]}
    slug = _confirmed(host, parties, model, ("product", "tech"), until="sections")
    before = len(model.calls)
    model.said[("section", parties["tech"])] = section("Tech's new why.", ["Six waves hold"], ["changed src/waves"])
    assert host.command("ideas.fork_answer", {"idea": slug, "side": parties["product"]}) == {"ok": True}
    _until(host, slug, "plan")
    again = model.calls[before:]
    assert [(c["step"], c["party"]) for c in again if c["step"].startswith("section")] == [("section", parties["tech"])]       # only the section the answer changes
    assert "How many waves: Ten waves" in again[0]["prompt"] and "your section must now agree" in again[0]["prompt"]
    page = _page(host, slug)
    assert page.parts("Tech")["Why"] == "Tech's new why." and page.parts("Product")["Why"] == "Product's why."                    # Product's section is untouched
    assert "Fork — How many waves: Ten waves [sections: Tech]" in page.section("Decisions")
    assert _row(host, slug, "fork") is None and ideas.plan(host.ideas.state_dir, slug) is not None
    assert passed == [] and host.ideas.autostart(slug) == "wait"                                                                  # a goal that had a fork is started by the person


def test_the_persons_own_words_write_again_every_side_and_win_over_a_side(host, parties, model):
    model.said[("join", "")] = {"gist": "Waves", "forks": [_fork(parties["product"], parties["tech"])]}
    slug = _confirmed(host, parties, model, ("product", "tech"), until="sections")
    before = len(model.calls)
    host.command("ideas.fork_answer", {"idea": slug, "side": parties["product"], "text": "  Eight  waves, no more "})
    _until(host, slug, "plan")
    redone = [(c["step"], c["party"]) for c in model.calls[before:] if c["step"].startswith("section")]
    assert sorted(redone) == sorted([("section_first", parties["product"]), ("section", parties["tech"])])
    assert "Fork — How many waves: Eight waves, no more [sections: Product, Tech]" in _page(host, slug).section("Decisions")


def test_two_forks_are_settled_one_after_the_other_and_the_sections_are_written_again_once(host, parties, model):
    model.said[("join", "")] = {"gist": "Waves", "forks": [_fork(parties["product"], parties["tech"]), _fork(parties["tech"], parties["product"], "Which engine")]}
    slug = _confirmed(host, parties, model, ("product", "tech"), until="sections")
    assert _row(host, slug, "fork")["about"] == "How many waves"
    before = len(model.calls)
    host.command("ideas.fork_answer", {"idea": slug, "side": parties["product"]})
    assert _row(host, slug, "fork")["about"] == "Which engine" and len(model.calls) == before and _state(host, slug)["state"] == "sections"      # nothing is written yet
    host.command("ideas.fork_answer", {"idea": slug, "side": parties["tech"]})
    _until(host, slug, "plan")
    redone = [(c["step"], c["party"]) for c in model.calls[before:] if c["step"].startswith("section")]
    assert sorted(redone) == sorted([("section", parties["tech"]), ("section_first", parties["product"])])                                 # each once, told both answers
    tech = next(c for c in model.calls[before:] if c["party"] == parties["tech"] and c["step"] == "section")["prompt"]
    assert "How many waves: Ten waves" in tech


def test_a_fork_is_answered_in_plain_words_or_refused(host, parties, model):
    model.said[("join", "")] = {"gist": "Waves", "forks": [_fork(parties["product"], parties["tech"])]}
    slug = _confirmed(host, parties, model, ("product", "tech"), until="sections")
    k = host.ideas.keeper
    with pytest.raises(idea_keeper.KeeperError, match="Pick a side or write your own answer"):
        k.fork_answer(slug, "", "")
    with pytest.raises(idea_keeper.KeeperError, match="Pick a side"):
        k.fork_answer(slug, "design", "")
    with pytest.raises(idea_keeper.KeeperError, match="gone"):
        k.fork_answer("nobody", parties["tech"])
    other = host.command("ideas.add", {"text": "another goal", "track": parties["tech"]})["slug"]
    with pytest.raises(idea_keeper.KeeperError, match="no fork to settle"):
        k.fork_answer(other, parties["tech"])
    assert _row(host, slug, "fork") is not None                                                                                 # nothing was taken


def test_sections_that_cannot_be_written_again_reopen_the_fork_for_the_person_to_answer_again(host, parties, model):
    model.said[("join", "")] = {"gist": "Waves", "forks": [_fork(parties["product"], parties["tech"])]}
    slug = _confirmed(host, parties, model, ("product", "tech"), until="sections")
    model.said[("section", parties["tech"])] = "not json at all"
    host.command("ideas.fork_answer", {"idea": slug, "side": parties["product"]})
    for _ in range(1000):
        if _row(host, slug, "fork"):
            break
        time.sleep(0.01)
    assert _row(host, slug, "fork") is not None and "The sections failed" in _state(host, slug)["error"] and _state(host, slug)["state"] == "sections"
    assert _page(host, slug).parts("Tech")["Why"] == "Tech's why."                                                              # the section it was is kept


# -- a leader that does not answer, the short way, a bug's cause ----------------------------------------------------------------------------------

def test_a_leader_that_does_not_answer_puts_the_goal_back_at_its_decision_and_only_the_missing_section_is_asked_again(host, parties, model):
    model.said[("section", parties["tech"])] = {"why": "no theses"}                                  # an answer with no Done when is none
    slug = _confirmed(host, parties, model, ("product", "tech"), until="decided")
    assert "did not answer: try again" in _state(host, slug)["error"] and _state(host, slug)["error"].startswith("The sections failed")
    row = _row(host, slug, "decision")
    assert row["confirmed"] is True and row["error"].startswith("The sections failed") and row["number"] == 1
    assert [c["party"] for c in model.steps("section_first")] == [parties["product"]] and len(model.steps("section")) == 2        # one try more, then it failed
    model.said[("section", parties["tech"])] = section("Tech's why.", ["The theme is one file"])
    before = len(model.calls)
    host.command("ideas.confirm", {"idea": slug})                                                                                # *Confirm and start* again: nothing is written twice
    _until(host, slug, "plan")
    asked = [(c["step"], c["party"]) for c in model.calls[before:] if c["step"].startswith("section")]
    assert asked == [("section", parties["tech"])] and "Dark mode ships" in ideas.idea_page(host.ideas.root(), slug).section("Decisions")
    assert len(model.steps("decide")) == 1


def test_a_spent_window_puts_the_goal_back_where_it_was_asked_from(host, parties, model):
    slug = _confirmed(host, parties, model, ("tech",), until="plan")
    ideas.save_state(host.ideas.state_dir, slug, state="sections")
    host.ideas.keeper.window_until = lambda: time.time() + 3600
    with pytest.raises(idea_keeper.KeeperError, match="window is spent"):
        host.ideas.keeper.sections(slug)
    assert _state(host, slug)["state"] == "decided" and "window is spent" in _state(host, slug)["error"]


def test_the_short_way_starts_tech_alone_with_no_talk_no_decision_and_no_join(host, parties, model):
    text = 'it crashes\nTraceback (most recent call last):\n  File "src/app.py", line 3, in <module>\nValueError: bad'
    slug = host.command("ideas.add", {"text": text})["slug"]
    st = _state(host, slug)
    assert st["route_how"]["short"] and st["route_how"]["reproduces"]
    host.command("ideas.route_start", {"idea": slug})
    _until(host, slug, "plan")
    steps = [c["step"] for c in model.calls]
    assert "section_first" in steps and not any(x in steps for x in ("talk_round", "diagnose", "decide", "join"))
    first = model.steps("section_first")[0]
    assert "The failure's lines" in first["prompt"] and "Traceback (most recent call last)" in first["prompt"] and first["party"] == parties["tech"]
    assert spec_sections.record(host.ideas.state_dir, slug).get("decision") is None and _page(host, slug).parts("Tech")["Why"] == "Product's why."


def test_a_bugs_why_is_the_cause_talk_found_set_by_code(host, parties, model):
    slug = host.command("ideas.add", {"text": "the lobby timer is wrong", "track": parties["tech"]})["slug"]
    idea_questions.save_record(host.ideas.state_dir, slug, {"mode": "bug", "cause": {"text": "the timer is not reset on reconnect", "where": ["src/app.py"], "confirmed": True},
                                                            "answers": [{"q": "Where?", "answer": "Lobby", "how": "pick"}], "defaults": []})
    ideas.save_state(host.ideas.state_dir, slug, state="sections", route=[{"party": parties["tech"], "leader": "architect"}], route_how={"kind": "bug", "short": True})
    model.said[("section_first", "")] = section("the leader's own guess", ["The timer is reset"])
    host.ideas.keeper.sections(slug)
    _until(host, slug, "plan")
    prompt = model.steps("section_first")[0]["prompt"]
    assert "The cause found (this is your Why)" in prompt and "the timer is not reset on reconnect (src/app.py)" in prompt and "Where? — Lobby" in prompt
    assert _page(host, slug).parts("Tech")["Why"] == "the timer is not reset on reconnect" and model.steps("decide") == []


def test_defaults_are_seen_in_the_section_and_what_a_leader_assumed_with_them_and_no_question_is_ever_written(host, parties, model):
    model.said[("section", "")] = section("Tech's why.", ["The theme is one file"], assumed=["the theme file is CSS"], questions=[{"ask": "Which?", "choices": ["a", "b"]}])
    slug = _confirmed(host, parties, model, ("product", "tech"), per=3)                       # six questions, the three the person is dealt are Product's: Tech's are closed by its picks
    parts = _page(host, slug).parts("Tech")
    assert parts["Defaults"].splitlines() == [f"- tech question {n} — A (its leader's pick)" for n in range(3)] + ["- Assumed: the theme file is CSS"] and "Questions" not in parts
    assert "Defaults" not in _page(host, slug).parts("Product")                                                                  # each its own leader's
