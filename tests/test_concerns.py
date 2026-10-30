"""Spec 108 A (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §2.3–§2.6; decisions §183.4–§183.6): a party's concerns. The record (`realm/concerns.py`: kept, strictly parsed, dismissed, a goal made of
one), the leader's look (`core/idea_concerns.py`: one call on the step `concerns`, the cheaper tier, no tools, given its map, the hints of code, what was dismissed and the parts it may speak of; an `on` that is no part
dropped, seven at most; when it is made and when it is not) and the commands (`ideas.concerns`, `ideas.concerns_again`, `ideas.concern_dismiss`, `ideas.concern_goal`). The model call is stubbed
(`keeper.call`), as Talk's tests do."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import concerns as store, event_log, goal_team, idea_lens, idea_spend, idea_target, ideas, lens_rubrics, lexicon, library, map_parts, project_facts

APP = {
    "package.json": json.dumps({"dependencies": {"react-router-dom": "6"}}),
    "src/App.jsx": 'import { Routes, Route } from "react-router-dom";\nimport Home from "./Home";\nimport Cart from "./Cart";\nimport About from "./About";\n'
                   'export default () => <Routes><Route path="/" element={<Home />} /><Route path="/cart" element={<Cart />} /><Route path="/about" element={<About />} /></Routes>;\n',
    "src/Home.jsx": 'export default () => <Link to="/cart">Cart</Link>;\n',
    "src/Cart.jsx": "export default () => null;\n",
    "src/About.jsx": "export default () => null;\n",
}
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def host(fake_repo) -> Orkboard:
    run(fake_repo, "checkout", "-q", "-b", "dev")
    for name, text in APP.items():
        (fake_repo / name).parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / name).write_text(text)
    run(fake_repo, "add", "-A")
    run(fake_repo, "commit", "-q", "-m", "an app")
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def _party(host, title, leader, craft=""):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [leader])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal")
    goal_team.set_team(root, slug, [], leader=leader)
    return slug


@pytest.fixture
def design(host):
    return _party(host, "Design", "product-designer")


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "architect")


class Model:
    """The keeper's call stubbed: `answer` the JSON (or a callable of the call) every call gets, `calls` every call made (`only` the concerns')."""

    def __init__(self, host, answer=None):
        self.host, self.calls, self.answer, self.gate = host, [], {"concerns": []} if answer is None else answer, None
        host.ideas.keeper.call = self

    def __call__(self, tier, prompt, effort="", budget=None):
        k = self.host.ideas.keeper
        row = {"tier": tier, "prompt": prompt, "effort": effort, "budget": budget, "tools": getattr(k._tls, "tools", True), "step": k.measure()["step"], "key": getattr(k._tls, "key", ""),
               "reads": prompt.split("Read at most ")[1][:2].strip() if "Read at most" in prompt else "0"}
        self.calls.append(row)
        if self.gate is not None:
            self.gate.wait(10)
        answer = self.answer(row) if callable(self.answer) else self.answer
        return (answer if isinstance(answer, str) else json.dumps(answer)), 0.01, 10, ""

    @property
    def looks(self):
        return [c for c in self.calls if c["step"] == "concerns"]


@pytest.fixture
def model(host):
    return Model(host)


def _wait(host, party):
    for _ in range(1000):
        if not host.ideas.keeper.busy_goal(party):
            return
        time.sleep(0.01)
    raise AssertionError("the keeper never finished")


def _look(host, party):
    got = host.command("ideas.concerns", {"party": party})
    _wait(host, party)
    return got


def concern(on, level="alert", what="It hurts", **more):
    return {"on": on, "level": level, "what": what, "why": "Because", "fix": "Mend it", **more}


# -- the record ---------------------------------------------------------------------------------------------------------------------------------

def test_the_record_is_kept_checked_and_read_back(tmp_path):
    assert store.read(tmp_path, "design") == {"at": "", "map_hash": "", "by": "", "status": "", "error": "", "measure": None, "concerns": [], "dismissed": [], "hints": []}
    saved = store.save(tmp_path, "design", at="2026-10-29T10:00:00", map_hash="abc", by="product-designer", status="ready", concerns=[
        {"id": "c-1", "on": "cart", "name": "Cart", "level": "alert", "what": "No way back", "why": "People get stuck", "fix": "Add a back link", "signal": "dead_end"},
        {"id": "c-2", "on": "x", "name": "X", "level": "worry", "what": "A made-up level"}, {"id": "c-3", "on": "", "name": "", "level": "note", "what": "No part"}])
    assert [c["id"] for c in saved["concerns"]] == ["c-1"] and saved["status"] == "ready" and saved["by"] == "product-designer"
    assert (tmp_path / "concerns" / "design.json").is_file() and store.read(tmp_path, "design") == saved
    (tmp_path / "concerns" / "design.json").write_text("not json")
    assert store.read(tmp_path, "design")["concerns"] == [] and store.read(tmp_path, "../x")["status"] == ""


def test_a_concern_names_its_aspect_from_the_answer_else_from_the_hint_on_its_part_and_an_unknown_id_is_not_kept(tmp_path):
    parts = [{"map": "screens", "id": "cart", "name": "Cart"}, {"map": "screens", "id": "home", "name": "Home"}, {"map": "screens", "id": "about", "name": "About"}]
    signals = [{"on": "cart", "kind": "a11y", "words": "an image with no alt text"}, {"on": "home", "kind": "dead_end", "words": "a dead end"}]
    answer = {"concerns": [concern("cart", what="One", aspect="flow"), concern("home", what="Two"), concern("about", what="Three", aspect="no-such-aspect"),
                           concern("about", what="Four", aspect="status"), concern("home", what="Five", aspect="hotspots")]}
    got = {c["what"]: c["aspect"] for c in store.parse("design", answer, parts, signals=signals, craft="design")}
    assert got == {"One": "flow", "Two": "flow", "Three": "", "Four": "status", "Five": "flow"}, "the answer's own id when it is one of the craft's, else the hint's aspect, else none"
    assert {c["what"]: c["aspect"] for c in store.parse("design", {"concerns": [concern("cart", what="One", aspect="flow")]}, parts, signals=signals)} == {"One": ""}, "no craft: no aspect"
    saved = store.save(tmp_path, "design", concerns=store.parse("design", answer, parts, signals=signals, craft="design"))
    assert [c["aspect"] for c in saved["concerns"]] == ["flow", "flow", "", "status", "flow"] and store.read(tmp_path, "design")["concerns"][0]["aspect"] == "flow"
    store.save(tmp_path, "design", concerns=[{"id": "c-1", "on": "cart", "name": "Cart", "level": "note", "what": "Old", "why": "", "fix": ""}])
    assert store.read(tmp_path, "design")["concerns"][0]["aspect"] == "", "a record from before has no aspect"
    assert len(store.save(tmp_path, "design", concerns=[{"id": "c-1", "on": "cart", "name": "Cart", "level": "note", "what": "Long", "aspect": "x" * 90}])["concerns"][0]["aspect"]) == 40


def test_the_record_keeps_the_hints_of_code_well_formed_ones_and_twenty_at_most(tmp_path):
    good = [{"on": f"p{n}", "kind": "big", "aspect": "hotspots", "words": f"p{n} is big"} for n in range(25)]
    bad = [{"on": "p", "kind": "", "words": "no kind"}, {"on": "p", "kind": "big", "words": ""}, {"kind": "big", "words": "no on"}, "not a hint", {"on": 3, "kind": "big", "words": "on is no text"}]
    saved = store.save(tmp_path, "tech", hints=[*bad, {"on": "", "kind": "no_channel", "words": "a hint of no part\nin two lines"}, *good])
    assert len(saved["hints"]) == store.HINTS == 20 and saved["hints"][0] == {"on": "", "kind": "no_channel", "aspect": "", "words": "a hint of no part in two lines"}
    assert saved["hints"][1] == {"on": "p0", "kind": "big", "aspect": "hotspots", "words": "p0 is big"} and store.read(tmp_path, "tech")["hints"] == saved["hints"]
    assert store.save(tmp_path, "tech", hints="x")["hints"] == []


def test_the_words_are_one_line_each_and_cut(tmp_path):
    long = "w " * 300
    got = store.save(tmp_path, "design", concerns=[{"id": "c-1", "on": "cart", "name": "Cart", "level": "note", "what": long, "why": "two\nlines", "fix": ""}])["concerns"][0]
    assert len(got["what"]) == store.LINE and got["why"] == "two lines"


def test_a_look_is_due_when_none_was_made_the_map_changed_a_day_ago_or_it_is_asked_again():
    now = dt.datetime(2026, 10, 29, 12, 0)
    ago = lambda **k: (now - dt.timedelta(**k)).isoformat(timespec="seconds")      # noqa: E731
    assert store.look_due({"at": "", "status": ""}, "h", now)                                                   # opened with no look
    assert not store.look_due({"at": ago(days=9), "map_hash": "h", "status": "ready"}, "h", now)               # the map did not change
    assert not store.look_due({"at": ago(hours=23), "map_hash": "old", "status": "ready"}, "h", now)           # changed, the last look not a day old
    assert store.look_due({"at": ago(hours=24), "map_hash": "old", "status": "ready"}, "h", now)               # changed, a day old
    assert store.look_due({"at": ago(minutes=1), "map_hash": "h", "status": "ready"}, "h", now, again=True)   # asked again
    assert not store.look_due({"at": "", "status": "looking"}, "h", now, again=True)                           # one at a time
    assert not store.look_due({"at": ago(minutes=5), "map_hash": "", "status": "failed"}, "h", now)           # a look that failed waits for a day or a press
    assert store.look_due({"at": ago(days=2), "map_hash": "", "status": "failed"}, "h", now)


def test_the_answer_is_parsed_strictly_an_on_that_is_no_part_dropped_seven_at_most_alerts_first():
    parts = [{"map": "screens", "id": f"p{n}", "name": f"Part {n}"} for n in range(12)]
    answer = {"concerns": [concern("nowhere"), concern("p0", "note", "A note"), concern("p1", "weird", "An odd level"), *[concern(f"p{n}", "alert", f"Alert {n}") for n in range(2, 12)],
                           concern("p3", "alert", "Alert 3"), concern("p4", "alert", "")]}
    got = store.parse("design", answer, parts, signals=[{"on": "p2", "kind": "dead_end", "words": "…"}])
    assert len(got) == store.MAX == 7 and {c["on"] for c in got} <= {p["id"] for p in parts}
    assert [c["level"] for c in got] == ["alert"] * 7, "alerts come before notes, so the notes were the ones cut"
    assert got[0]["signal"] == "dead_end" and got[0]["name"] == "Part 2" and len({c["id"] for c in got}) == 7                      # the same part and words once
    assert store.parse("design", {"concerns": []}, parts) == [] and store.parse("design", {"concerns": "x"}, parts) is None and store.parse("design", "x", parts) is None
    assert [c["level"] for c in store.parse("design", {"concerns": [concern("p0", "note"), concern("p1", "weird")]}, parts)] == ["note", "note"]


def test_a_concern_dismissed_is_not_raised_again_while_its_part_is_as_it_was(tmp_path):
    parts = [{"map": "screens", "id": "cart", "name": "Cart"}]
    first = store.parse("design", {"concerns": [concern("cart", what="No way back")]}, parts)
    store.save(tmp_path, "design", concerns=first, map_hash="m1")
    assert store.dismiss(tmp_path, "design", first[0]["id"], "part-v1")["what"] == "No way back"
    rec = store.read(tmp_path, "design")
    assert rec["concerns"] == [] and rec["dismissed"][0]["on"] == "cart" and rec["dismissed"][0]["part_hash"] == "part-v1" and rec["dismissed"][0]["map_hash"] == "m1"
    again = {"concerns": [concern("cart", what="No way back"), concern("cart", what="Another thing")]}
    assert [c["what"] for c in store.parse("design", again, parts, rec["dismissed"], {"cart": "part-v1"})] == ["Another thing"]
    assert [c["what"] for c in store.parse("design", again, parts, rec["dismissed"], {"cart": "part-v2"})] == ["No way back", "Another thing"], "the part changed: it may be raised again"
    assert store.dismiss(tmp_path, "design", "c-none") is None


def test_a_goal_made_of_a_concern_is_noted_and_the_counts_are_the_open_ones(tmp_path):
    parts = [{"map": "screens", "id": "cart", "name": "Cart"}, {"map": "screens", "id": "home", "name": "Home"}]
    got = store.parse("design", {"concerns": [concern("cart", what="One"), concern("home", "note", "Two"), concern("home", "alert", "Three")]}, parts)
    store.save(tmp_path, "design", concerns=got)
    assert store.counts(store.read(tmp_path, "design")) == {"alerts": 2, "notes": 1}
    assert store.made_goal(tmp_path, "design", got[0]["id"], "fix-cart")["idea"] == "fix-cart"
    rec = store.read(tmp_path, "design")
    assert next(c for c in rec["concerns"] if c["id"] == got[0]["id"])["idea"] == "fix-cart" and store.counts(rec) == {"alerts": 1, "notes": 1}
    assert store.made_goal(tmp_path, "design", "c-none", "x") is None
    assert store.text(rec).splitlines()[0].startswith("- [alert] Home (home): Three Why: Because Fix: Mend it") and "One" not in store.text(rec)


def test_a_part_hash_is_the_hash_of_the_lines_that_name_the_part():
    text = "Screens\n- Cart (/cart) leads to Home\n- About (/about) leads nowhere\n"
    cart = {"id": "cart", "name": "Cart"}
    assert store.part_hash(text, cart) == store.part_hash(text.replace("About (/about) leads nowhere", "About (/about) leads to Home"), cart) != "", "a line that does not name the part is not the part's"
    assert store.part_hash(text, cart) != store.part_hash(text.replace("Cart (/cart) leads to Home", "Cart (/cart) leads nowhere"), cart) and store.part_hash("nothing", cart) == ""
    assert store.map_hash(text) == store.map_hash(text) != store.map_hash(text + " ")


def test_the_word_is_in_the_glossary():
    assert lexicon.term("concern") == "concern" and lexicon.term("concern", many=True) == "concerns"
    assert {event_log.CONCERNS_MADE, event_log.CONCERN_OPENED, event_log.CONCERN_GOAL, event_log.CONCERN_DISMISSED} <= set(event_log.EVENTS)


# -- the look: the leader's one call ---------------------------------------------------------------------------------------------------------

def test_a_look_is_one_call_of_the_leader_on_the_cheaper_tier_with_no_tools_given_its_map_the_hints_and_the_parts(host, design, model):
    project_facts.keep(host.ideas.state_dir, design, "for_whom", "Shoppers on phones", "person")
    model.answer = {"concerns": [concern("cart", what="No way back", why="People get stuck", fix="Add a back link"), concern("nowhere", what="Not a part"), concern("about", "note", "Nothing leads here")]}
    got = _look(host, design)
    assert got["has_map"] and got["map"] == "screens" and got["leader"] == "product-designer"
    (call,) = model.looks
    assert call["tools"] is False and call["key"] == f"goal:{design}" and (call["tier"], call["effort"]) == idea_target.pick("concerns", "balance") == ("warrior", "low")
    assert call["budget"] == idea_target.budget("concerns", "balance")
    p = call["prompt"]
    assert p.startswith("You are Product designer, the leader of this goal's party") and "Read no file" in p and "Shoppers on phones" in p       # its voice, no file, the project's facts
    assert "Cart (/cart)" in p and "Nothing leads to the screen About" in p and "no picture kept" in p                                         # its map and the hints of code
    assert "- cart: Cart (step:2)" in p and "- step:1: Step 1" in p and '"concerns"' in p and "At most 7" in p                                    # the parts it may speak of, by id
    rec = host.command("ideas.concerns", {"party": design})
    assert rec["status"] == "ready" and rec["by"] == "product-designer" and rec["at"] and rec["map_hash"] and rec["error"] == ""
    assert [(c["on"], c["name"], c["level"], c["what"], c["why"], c["fix"]) for c in rec["concerns"]] == [("cart", "Cart", "alert", "No way back", "People get stuck", "Add a back link"),
                                                                                                          ("about", "About", "note", "Nothing leads here", "Because", "Mend it")]
    assert (rec["alerts"], rec["notes"]) == (1, 1) and rec["concerns"][1]["signal"] == "loose" and rec["measure"]["step"] == "concerns" and "waits" not in rec
    assert len(model.looks) == 1, "reading the record is no second look"


def test_the_prompt_names_the_crafts_rubric_before_the_map_the_aspect_of_each_hint_and_asks_for_an_aspect(host, design, tech, model):
    model.answer = {"concerns": [concern("about", "note", "Nothing leads here", aspect="flow"), concern("cart", what="Not looked at", aspect="seen")]}
    _look(host, design)
    p = model.looks[0]["prompt"]
    assert "How a senior of design reviews this map: Nielsen's ten usability heuristics, WCAG 2.2 AA" in p and "Judge by these aspects:\n- flow: The way through. " in p
    assert "- consistency: Consistency. Do the screens use one set of words" in p and p.index("How a senior of design") < p.index("Your party's map:")
    assert "Nothing leads to the screen About" in p and "[on about] (aspect flow)" in p and "no picture kept" in p and "(aspect seen)" in p, "each hint line ends with its aspect"
    assert "Give each concern its `aspect`, one id of the aspects above. Look at every aspect, not only those the hints name" in p and '"aspect": "flow", "level": "alert"' in p
    _look(host, tech)
    q = model.looks[-1]["prompt"]
    assert "How a senior of tech reviews this map: C4's containers and parts" in q and "- safety: Security and reliability. " in q and "(aspect flow)" not in q and '"aspect": "modularity"' in q
    rec = host.command("ideas.concerns", {"party": design})
    assert [(c["on"], c["aspect"]) for c in rec["concerns"]] == [("cart", "seen"), ("about", "flow")]


def test_the_look_keeps_the_hints_it_was_given_with_their_aspects(host, design, model):
    _look(host, design)
    rec = host.command("ideas.concerns", {"party": design})
    assert rec["hints"] and len(rec["hints"]) <= store.HINTS and all(set(h) == {"on", "kind", "aspect", "words"} and h["words"] for h in rec["hints"])
    assert all(h["aspect"] == lens_rubrics.aspect_of("design", h["kind"]) for h in rec["hints"]) and {"loose", "no_picture"} <= {h["kind"] for h in rec["hints"]}
    assert [h["aspect"] for h in rec["hints"] if h["kind"] == "loose"] == ["flow"] * sum(h["kind"] == "loose" for h in rec["hints"])
    assert store.read(host.ideas.state_dir, design)["hints"] == rec["hints"]


def test_every_concern_command_carries_the_rubric_with_the_scorecard_and_none_for_a_party_with_no_map(host, design, tech, model):
    model.answer = {"concerns": [concern("about", "alert", "Nothing leads here", aspect="flow"), concern("cart", "note", "Not looked at", aspect="seen")]}
    first = _look(host, design) and host.command("ideas.concerns", {"party": design})
    r = lens_rubrics.RUBRICS["design"]
    assert first["rubric"]["framework"] == r["framework"] and first["rubric"]["short"] == "Nielsen · WCAG 2.2"
    card = {a["id"]: a for a in first["rubric"]["aspects"]}
    assert list(card) == [a["id"] for a in r["aspects"]] and (card["flow"]["state"], card["flow"]["n"]) == ("alert", 1) and (card["seen"]["state"], card["seen"]["n"]) == ("note", 1)
    assert card["consistency"]["state"] == "clear" and card["flow"]["name"] == "The way through" and card["flow"]["ask"] == r["aspects"][0]["ask"]
    assert first["rubric"]["aspects"] == lens_rubrics.scorecard("design", store.read(host.ideas.state_dir, design))
    made = host.command("ideas.concern_goal", {"party": design, "id": first["concerns"][0]["id"]})
    assert {a["id"]: a["state"] for a in made["rubric"]["aspects"]}["flow"] == "hint", "a goal was made: the concern is not open, code's hint stays"
    assert made["concerns"][0]["aspect"] == "flow"
    gone = host.command("ideas.concern_dismiss", {"party": design, "id": first["concerns"][1]["id"]})
    assert gone["rubric"] and {a["id"]: a["state"] for a in gone["rubric"]["aspects"]}["seen"] == "hint"
    again = host.command("ideas.concerns_again", {"party": design})
    assert again["rubric"]["framework"] == r["framework"]
    plain = _party(host, "Plain", "taskmaster")
    for rec in (host.command("ideas.concerns", {"party": plain}), host.command("ideas.concerns_again", {"party": plain})):
        assert rec["rubric"] is None and rec["has_map"] is False
    unlooked = host.command("ideas.concerns", {"party": tech})
    assert unlooked["rubric"]["short"] == "C4 · ISO 25010 · hotspots"


def test_at_most_seven_are_kept_and_what_is_not_on_the_map_is_dropped(host, design, model):
    model.answer = {"concerns": [concern("ghost", what="Not a part"), *[concern(p, "note", f"Note {p}") for p in ("home", "cart", "about")], *[concern(f"step:{n}", "alert", f"Alert {n}") for n in (1, 2, 3, 4)],
                                 *[concern("home", "alert", f"More {n}") for n in range(6)]]}
    rec = _look(host, design) and host.command("ideas.concerns", {"party": design})
    assert len(rec["concerns"]) == 7 and {c["on"] for c in rec["concerns"]} <= {p["id"] for p in map_parts.parts(host.ideas.state_dir, host.ideas.keeper.repo_root, "design")}
    assert [c["level"] for c in rec["concerns"]] == ["alert"] * 7 and rec["alerts"] == 7 and rec["notes"] == 0


def test_the_step_is_in_the_specs_stage_of_its_partys_ledger_and_is_as_talks_round(host, design, model):
    _look(host, design)
    spent = idea_spend.of_goal(host.ideas.state_dir, design)
    assert spent["stages"]["spec"]["usd"] == 0.01 and idea_spend.STEP_STAGE["concerns"] == "spec" and "concerns" in idea_target.STEPS and set(idea_target.MATRIX) >= set(idea_target.STEPS)
    for target in idea_target.TARGETS:
        assert idea_target.pick("concerns", target) == idea_target.pick("talk_round", target)
    assert idea_target.READS["concerns"] == 0 and idea_target.reads_of("concerns", "design") == 4 and idea_target.reads_of("concerns", "tech") == 0


def test_a_look_is_logged_without_a_word_of_the_leaders(host, design, model):
    model.answer = {"concerns": [concern("cart", what="SECRET WORDS"), concern("about", "note", "Other")]}
    _look(host, design)
    (row,) = [r for r in event_log.read(host.ideas.keeper.repo_root) if r["event"] == event_log.CONCERNS_MADE]
    assert {k: row[k] for k in ("party", "n", "alerts", "notes", "why")} == {"party": design, "n": 2, "alerts": 1, "notes": 1, "why": "open"} and row["signals"] >= 1 and row["cost"] == 0.01 and "seconds" in row
    assert "SECRET WORDS" not in json.dumps(row)


# -- when ----------------------------------------------------------------------------------------------------------------------------------------

def test_no_call_for_a_party_nobody_opens_or_that_has_no_map(host, design, model):
    plain = _party(host, "Plain", "taskmaster")
    assert model.looks == [] and host.command("ideas.map", {})["goals"]                              # the Board is read, no look is made
    got = host.command("ideas.concerns", {"party": plain})
    assert got["has_map"] is False and got["map"] == "" and got["concerns"] == [] and got["status"] == "" and model.looks == []
    again = host.command("ideas.concerns_again", {"party": plain})        # the whole record, as every concern command answers (spec 108 §2.5)
    assert (again["ok"], again["asked"], again["why"], again["concerns"]) == (True, False, "There is nothing on this map to look at yet", []) and model.looks == []


def test_a_party_whose_map_has_nothing_to_look_at_yet_is_not_looked_at(host, model):
    game = _party(host, "Game design", "game-designer")
    assert host.command("ideas.concerns", {"party": game})["status"] == "" and model.looks == []                 # no loop is kept yet
    assert host.command("ideas.concerns_again", {"party": game})["asked"] is False


def test_the_first_opening_asks_the_second_does_not_and_again_does(host, design, model):
    _look(host, design)
    _look(host, design)
    assert len(model.looks) == 1, "the map did not change"
    again = host.command("ideas.concerns_again", {"party": design})
    assert (again["ok"], again["asked"], again["party"]) == (True, True, design) and isinstance(again["concerns"], list)
    _wait(host, design)
    assert len(model.looks) == 2
    rows = [r for r in event_log.read(host.ideas.keeper.repo_root) if r["event"] == event_log.CONCERNS_MADE]
    assert [r["why"] for r in rows] == ["open", "again"]


def test_a_map_that_changed_is_looked_at_again_only_when_the_last_look_is_a_day_old(host, design, model):
    state = host.ideas.state_dir
    _look(host, design)
    store.save(state, design, map_hash="a map that was")                                                       # the map has changed since the look
    _look(host, design)
    assert len(model.looks) == 1, "the last look is not a day old"
    store.save(state, design, at=(dt.datetime.now() - dt.timedelta(days=2)).isoformat(timespec="seconds"))
    _look(host, design)
    assert len(model.looks) == 2 and store.read(state, design)["map_hash"] != "a map that was"


def test_one_look_at_a_time_a_party_and_a_stale_looking_is_not_looking(host, design, model):
    model.gate = threading.Event()
    host.command("ideas.concerns", {"party": design})
    for _ in range(300):
        if model.calls:
            break
        time.sleep(0.01)
    got = host.command("ideas.concerns", {"party": design})
    assert got["status"] == "looking" and len(model.calls) == 1
    again = host.command("ideas.concerns_again", {"party": design})
    assert again["asked"] is False and "looking" in again["why"] and len(model.calls) == 1
    model.gate.set()
    _wait(host, design)
    assert host.command("ideas.concerns", {"party": design})["status"] == "ready"
    store.save(host.ideas.state_dir, design, status="looking")                                                  # lost with the process: nobody is at it
    assert host.command("ideas.concerns", {"party": design})["status"] == ""


def test_a_spent_window_or_limit_is_said_and_the_record_is_not_touched(host, design, model):
    host.ideas.keeper.budget_ok = lambda: False
    got = host.command("ideas.concerns", {"party": design})
    assert "limit" in got["waits"] and got["status"] == "" and got["at"] == "" and model.looks == []
    assert store.read(host.ideas.state_dir, design)["status"] == ""
    again = host.command("ideas.concerns_again", {"party": design})
    assert again["asked"] is False and "limit" in again["why"]
    host.ideas.keeper.budget_ok = lambda: True
    assert "waits" not in _look(host, design) and len(model.looks) == 1                                         # the next opening asks


def test_a_leader_that_does_not_answer_fails_the_look_and_the_next_opening_does_not_ask_at_once(host, design, model):
    model.answer = "not the json"
    _look(host, design)
    rec = host.command("ideas.concerns", {"party": design})
    assert rec["status"] == "failed" and "did not answer" in rec["error"] and rec["at"] and len(model.looks) == 2, "one more try"
    host.command("ideas.concerns", {"party": design})
    assert len(model.looks) == 2, "a failed look waits for a day or the person's press"
    model.answer = {"concerns": [concern("cart")]}
    host.command("ideas.concerns_again", {"party": design})
    _wait(host, design)
    ready = host.command("ideas.concerns", {"party": design})
    assert ready["status"] == "ready" and ready["error"] == "" and len(ready["concerns"]) == 1


# -- what the person dismissed, what a goal was made of --------------------------------------------------------------------------------------------

def test_what_the_person_dismissed_is_told_to_the_leader_and_not_kept_when_it_says_it_again(host, design, model):
    model.answer = {"concerns": [concern("cart", what="No way back"), concern("about", "note", "Nothing leads here")]}
    first = _look(host, design) and host.command("ideas.concerns", {"party": design})
    gone = first["concerns"][0]
    got = host.command("ideas.concern_dismiss", {"party": design, "id": gone["id"]})
    assert [c["what"] for c in got["concerns"]] == ["Nothing leads here"] and (got["alerts"], got["notes"]) == (0, 1)
    host.command("ideas.concerns_again", {"party": design})
    _wait(host, design)
    p = model.looks[-1]["prompt"]
    assert "The person said these are not a problem" in p and "- on cart: No way back" in p
    rec = host.command("ideas.concerns", {"party": design})
    assert [c["what"] for c in rec["concerns"]] == ["Nothing leads here"], "the same words on the same part are dropped"
    assert rec["dismissed"][0]["on"] == "cart" and rec["dismissed"][0]["what"] == "No way back"
    assert [r["level"] for r in event_log.read(host.ideas.keeper.repo_root) if r["event"] == event_log.CONCERN_DISMISSED] == ["alert"]
    with pytest.raises(CommandError):
        host.command("ideas.concern_dismiss", {"party": design, "id": gone["id"]})


def test_a_concern_made_a_goal_is_a_goal_of_the_party_with_its_part_as_the_mark_and_stays_across_a_new_look(host, design, model):
    model.answer = {"concerns": [concern("cart", what="No way back", fix="Add a back link"), concern("about", "note", "Nothing leads here")]}
    first = _look(host, design) and host.command("ideas.concerns", {"party": design})
    made = host.command("ideas.concern_goal", {"party": design, "id": first["concerns"][0]["id"]})
    assert made["ok"] and made["idea"] and (made["alerts"], made["notes"]) == (0, 1)
    page = ideas.idea_page(host.ideas.root(), made["idea"])
    assert page is not None and page.get("track") == design and "No way back" in page.section("Gist") and "Add a back link" in page.section("Gist")
    st = ideas.state(host.ideas.state_dir, made["idea"])
    assert st["marks"] == [{"map": "screens", "name": "Cart", "id": "cart"}]
    assert made["type"] in ("", "screen") and st["type"] == made["type"]
    assert next(c for c in made["concerns"] if c["on"] == "cart")["idea"] == made["idea"]
    host.command("ideas.concerns_again", {"party": design})
    _wait(host, design)
    again = host.command("ideas.concerns", {"party": design})
    assert next(c for c in again["concerns"] if c["on"] == "cart")["idea"] == made["idea"] and (again["alerts"], again["notes"]) == (0, 1), "a new look keeps the goal made"
    assert [(r["party"], r["level"], r["idea"]) for r in event_log.read(host.ideas.keeper.repo_root) if r["event"] == event_log.CONCERN_GOAL] == [(design, "alert", made["idea"])]


def test_the_type_of_the_goal_is_its_maps_default_when_the_party_is_offered_it(host, tech, model):
    from orkboard.realm import goal_types
    model.answer = lambda call: {"concerns": [concern("src", what="Too much in one place", fix="Split it")]}
    rec = _look(host, tech) and host.command("ideas.concerns", {"party": tech})
    assert rec["map"] == "system" and [c["on"] for c in rec["concerns"]] == ["src"]
    offered = {t.id for t, _m in goal_types.offered(host.ideas.state_dir, host.ideas.root(), tech)}
    made = host.command("ideas.concern_goal", {"party": tech, "id": rec["concerns"][0]["id"]})
    assert made["type"] == ("restructure" if "restructure" in offered else "")
    assert ideas.state(host.ideas.state_dir, made["idea"])["marks"] == [{"map": "system", "name": "src", "id": "src"}]


def test_opening_a_map_that_has_concerns_is_logged_once_as_its_highest_level(host, design, model):
    model.answer = {"concerns": [concern("about", "note", "Nothing leads here")]}
    _look(host, design)                                                       # the first opening: no concerns yet when it answered
    opened = lambda: [(r["party"], r["level"]) for r in event_log.read(host.ideas.keeper.repo_root) if r["event"] == event_log.CONCERN_OPENED]      # noqa: E731
    assert opened() == []
    host.command("ideas.concerns", {"party": design})
    assert opened() == [(design, "note")]
    store.save(host.ideas.state_dir, design, concerns=store.read(host.ideas.state_dir, design)["concerns"] + [{"id": "c-9", "on": "cart", "name": "Cart", "level": "alert", "what": "Stuck"}])
    host.command("ideas.concerns", {"party": design})
    assert opened() == [(design, "note"), (design, "alert")]


def test_a_gone_party_or_concern_is_refused_in_plain_words(host, design, model):
    for name in ("ideas.concerns", "ideas.concerns_again", "ideas.concern_dismiss", "ideas.concern_goal"):
        with pytest.raises(CommandError):
            host.command(name, {"party": "nobody", "id": "c-1"})
        with pytest.raises(CommandError):
            host.command(name, {})
    for name in ("ideas.concern_dismiss", "ideas.concern_goal"):
        with pytest.raises(CommandError, match="gone"):
            host.command(name, {"party": design, "id": "c-none"})


# -- the snapshot, Talk, the pictures ------------------------------------------------------------------------------------------------------

def test_the_partys_row_in_the_map_carries_its_counts_for_its_tab(host, design, model):
    row = lambda: next(g for g in host.command("ideas.map", {})["goals"] if g["slug"] == design)["concerns"]      # noqa: E731
    assert row() == {"alerts": 0, "notes": 0, "status": ""}
    model.answer = {"concerns": [concern("cart"), concern("home", "alert", "Two"), concern("about", "note", "Three")]}
    _look(host, design)
    assert row() == {"alerts": 2, "notes": 1, "status": "ready"}
    store.save(host.ideas.state_dir, design, status="failed", error="x")
    assert row()["status"] == "failed"


def test_the_concerns_of_a_party_are_the_text_its_leader_is_given_in_a_talk_round(host, design, model):
    keeper = host.ideas.keeper
    assert keeper.concerns_text(design) == ""
    model.answer = {"concerns": [concern("cart", what="No way back", fix="Add a back link"), concern("about", "note", "Nothing leads here")]}
    _look(host, design)
    text = keeper.concerns_text(design)
    assert text.splitlines()[0] == "- [alert] Cart (cart): No way back Why: Because Fix: Add a back link" and "- [note] About (about): Nothing leads here" in text


def test_design_reads_the_pictures_of_the_screens_kept_since_its_last_look_and_no_other_party_does(host, design, tech, model):
    state = host.ideas.state_dir
    idea_lens.keep_screen(state, PNG, "Cart")
    _look(host, design)
    (first,) = model.looks
    assert first["tools"] is True and first["reads"] == "4" and "Pictures of the screens changed since your last look" in first["prompt"]
    assert ".orkcraft/screens/" in first["prompt"] and "(Cart, screen id cart)" in first["prompt"] and "contrast" in first["prompt"]
    host.command("ideas.concerns_again", {"party": design})
    _wait(host, design)
    second = model.looks[-1]
    assert second["tools"] is False and "Pictures of the screens" not in second["prompt"] and "Read no file" in second["prompt"], "nothing changed since the last look"
    _look(host, tech)
    assert model.looks[-1]["tools"] is False and "Pictures" not in model.looks[-1]["prompt"]
