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
from orkboard.realm import concerns as store, event_log, goal_team, idea_lens, idea_target, ideas, journals, library, map_parts, project_facts

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


def _until(ok, why, s=10.0):
    """`ok()` comes true within `s` seconds: the look runs on the keeper's thread, which may not have started when the command returns (so `_wait` alone can race it)."""
    end = time.monotonic() + s
    while time.monotonic() < end:
        if ok():
            return
        time.sleep(0.02)
    raise AssertionError(why)


def _look(host, party):
    got = host.command("ideas.concerns", {"party": party})
    _wait(host, party)
    return got


def concern(on, level="alert", what="It hurts", **more):
    return {"on": on, "level": level, "what": what, "why": "Because", "fix": "Mend it", **more}


# -- the record ---------------------------------------------------------------------------------------------------------------------------------

def test_the_record_is_kept_checked_and_read_back(tmp_path):
    assert store.read(tmp_path, "design") == {"at": "", "map_hash": "", "by": "", "status": "", "error": "", "measure": None, "concerns": [], "dismissed": [], "hints": [], "head": "", "since": None}
    saved = store.save(tmp_path, "design", at="2026-10-29T10:00:00", map_hash="abc", by="product-designer", status="ready", concerns=[
        {"id": "c-1", "on": "cart", "name": "Cart", "level": "alert", "what": "No way back", "why": "People get stuck", "fix": "Add a back link", "signal": "dead_end"},
        {"id": "c-2", "on": "x", "name": "X", "level": "worry", "what": "A made-up level"}, {"id": "c-3", "on": "", "name": "", "level": "note", "what": "No part"}])
    assert [c["id"] for c in saved["concerns"]] == ["c-1"] and saved["status"] == "ready" and saved["by"] == "product-designer"
    assert (tmp_path / "concerns" / "design.json").is_file() and store.read(tmp_path, "design") == saved
    (tmp_path / "concerns" / "design.json").write_text("not json")
    assert store.read(tmp_path, "design")["concerns"] == [] and store.read(tmp_path, "../x")["status"] == ""


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


def test_at_most_seven_are_kept_and_what_is_not_on_the_map_is_dropped(host, design, model):
    model.answer = {"concerns": [concern("ghost", what="Not a part"), *[concern(p, "note", f"Note {p}") for p in ("home", "cart", "about")], *[concern(f"step:{n}", "alert", f"Alert {n}") for n in (1, 2, 3, 4)],
                                 *[concern("home", "alert", f"More {n}") for n in range(6)]]}
    rec = _look(host, design) and host.command("ideas.concerns", {"party": design})
    assert len(rec["concerns"]) == 7 and {c["on"] for c in rec["concerns"]} <= {p["id"] for p in map_parts.parts(host.ideas.state_dir, host.ideas.keeper.repo_root, "design")}
    assert [c["level"] for c in rec["concerns"]] == ["alert"] * 7 and rec["alerts"] == 7 and rec["notes"] == 0


# -- when ----------------------------------------------------------------------------------------------------------------------------------------

def test_no_call_for_a_party_nobody_opens_or_that_has_no_map(host, design, model):
    plain = _party(host, "Plain", "taskmaster")
    assert model.looks == [] and host.command("ideas.map", {})["goals"]                              # the Board is read, no look is made
    got = host.command("ideas.concerns", {"party": plain})
    assert got["has_map"] is False and got["map"] == "" and got["concerns"] == [] and got["status"] == "" and model.looks == []
    again = host.command("ideas.concerns_again", {"party": plain})        # the whole record, as every concern command answers (spec 108 §2.5)
    assert (again["ok"], again["asked"], again["why"], again["concerns"]) == (True, False, "There is nothing on this map to look at yet", []) and model.looks == []


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
    journals.save_digest(host.ideas.state_dir, design, "Works: x", 0)                          # a view of today: no view call (spec 167 J)
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
    journals.save_digest(host.ideas.state_dir, design, "Works: x", 0)                                           # a view of today: no view call is begun on opening (spec 167 J)
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
    journals.save_digest(host.ideas.state_dir, design, "Works: x", 0)                          # a view of today: no view call (spec 167 J)
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


# -- Spec 121 E: the evening line (docs/specs/121-the-day-the-morning-and-the-night.md §6) -----------------------------------------------------------

def _change_map(host) -> None:
    """A screen comes to dev: the map of Design is not what it was."""
    repo = Path(host.ideas.keeper.repo_root)
    (repo / "src/Help.jsx").write_text("export default () => null;\n")
    (repo / "src/App.jsx").write_text(APP["src/App.jsx"].replace('<Route path="/about"', '<Route path="/help" element={<Help />} /><Route path="/about"').replace(
        'import About from "./About";', 'import About from "./About";\nimport Help from "./Help";'))
    run(repo, "add", "-A")
    run(repo, "commit", "-q", "-m", "a help screen")


def _a_day_ago(host, party) -> None:
    store.save(host.ideas.state_dir, party, at=(dt.datetime.now() - dt.timedelta(days=2)).isoformat(timespec="seconds"))


def test_a_look_of_a_map_that_changed_asks_for_the_line_and_keeps_it_with_its_time_and_map(host, design, model):
    _look(host, design)
    first = store.read(host.ideas.state_dir, design)
    _change_map(host)
    _a_day_ago(host, design)
    model.answer = {"concerns": [], "since": {"way": "toward", "line": "Help is a step nearer, nothing broke"}}
    _look(host, design)
    p = model.looks[1]["prompt"]
    assert '"since": {"way": "toward"' in p and "`toward` the way through the screens" in p and f"{store.LINE} characters" in p
    assert "What changed since your last look" in p and "Changed since your last call:" in p and "new screen" in p and "Help" in p, "it is given what changed, with the map"
    rec = host.command("ideas.concerns", {"party": design})
    assert rec["since"]["way"] == "toward" and rec["since"]["line"] == "Help is a step nearer, nothing broke"
    assert rec["since"]["map_hash"] == rec["map_hash"] != first["map_hash"] and rec["since"]["at"] == rec["at"]
    assert rec["head"] != first["head"]
    row = [r for r in event_log.read(host.ideas.keeper.repo_root) if r["event"] == event_log.CONCERNS_MADE][-1]
    assert row["since"] == "toward" and "Help is a step" not in json.dumps(row), "the log says the way, never the leader's words"


def test_a_bad_way_is_unclear_and_a_look_that_says_no_line_keeps_none(host, design, model):
    journals.save_digest(host.ideas.state_dir, design, "Works: x", 0)                          # a view of today: no view call (spec 167 J)
    _look(host, design)
    _change_map(host)
    _a_day_ago(host, design)
    model.answer = {"concerns": [], "since": {"way": "better", "line": "Hard to say"}}
    _look(host, design)
    assert host.command("ideas.concerns", {"party": design})["since"]["way"] == "unclear"
    _a_day_ago(host, design)
    store.save(host.ideas.state_dir, design, map_hash="a map that was")
    model.answer = {"concerns": []}
    _look(host, design)
    assert host.command("ideas.concerns", {"party": design})["since"] is None


# -- the leader's view on opening a tab (spec 167 J) ----------------------------------------------------------------------------------------------

def _views(model):
    return [c for c in model.calls if c["step"] != "concerns"]


def test_opening_a_tab_begins_the_view_only_when_it_is_a_day_old_or_there_is_none(host, design, model):
    state = host.ideas.state_dir
    journals.save_digest(state, design, "Works: x", 0)                                         # a view of today
    _look(host, design)                                                                        # the map's look, no view
    _wait(host, design)
    assert _views(model) == []
    _look(host, design)
    _wait(host, design)
    assert _views(model) == [], "a view of today begins none"
    journals.save_digest(state, design, "Works: x", 0, at=(dt.datetime.now() - dt.timedelta(days=2)).isoformat(timespec="seconds"))
    _look(host, design)
    _wait(host, design)
    assert len(_views(model)) >= 1, "a view two days old begins one (a failed answer is tried twice)"


# -- Spec 168 D4: a concern at the alert's level is a card in the hand; Later lays it face down (decisions §283.21) ----------------------------------------

def test_the_open_concerns_are_cards_an_alert_in_the_hand_a_note_never_one_and_a_goal_made_of_one_takes_it_out(tmp_path):
    store.save(tmp_path, "design", status="ready", concerns=[
        {"id": "c-1", "on": "cart", "name": "Cart", "level": "alert", "what": "No way back", "why": "People get stuck", "fix": "Add a link", "aspect": "flow"},
        {"id": "c-2", "on": "home", "name": "Home", "level": "note", "what": "Plain"}, {"id": "c-3", "on": "about", "name": "About", "level": "alert", "what": "Orphan", "idea": "orphan-goal"}])
    got = store.cards(store.read(tmp_path, "design"))
    assert [(c["id"], c["level"], c["in_hand"], c["later"]) for c in got] == [("c-1", "alert", True, False), ("c-2", "note", False, False)], "a note stays on the scheme and in the header; a goal made of one is no card"
    assert got[0]["what"] == "No way back" and got[0]["why"] == "People get stuck" and got[0]["fix"] == "Add a link" and got[0]["aspect"] == "flow" and got[0]["name"] == "Cart"


def test_later_lays_the_concern_face_down_out_of_the_hand_and_it_survives_a_reread(tmp_path):
    store.save(tmp_path, "design", concerns=[{"id": "c-1", "on": "cart", "name": "Cart", "level": "alert", "what": "No way back"}])
    assert store.lay_later(tmp_path, "design", "c-none") is None
    assert store.lay_later(tmp_path, "design", "c-1")["later"] is True
    (card,) = store.cards(store.read(tmp_path, "design"))
    assert card["later"] is True and card["in_hand"] is False, "face down in the header, not in the hand"
    assert store.counts(store.read(tmp_path, "design")) == {"alerts": 1, "notes": 0}, "it is still a concern of the scheme"
    store.save(tmp_path, "design", concerns=[{"id": "c-1", "on": "cart", "name": "Cart", "level": "alert", "what": "No way back", "later": "yes"}])
    assert "later" not in store.read(tmp_path, "design")["concerns"][0], "only a true mark is kept"


def test_the_command_lays_it_later_and_the_partys_row_in_the_map_says_so_and_the_next_look_that_finds_it_again_deals_it_back(host, design, model):
    row = lambda: next(g for g in host.command("ideas.map", {})["goals"] if g["slug"] == design)["concerns"]["list"]      # noqa: E731
    model.answer = {"concerns": [concern("cart", what="No way back"), concern("home", "note", "Plain")]}
    first = _look(host, design) and host.command("ideas.concerns", {"party": design})
    cid = first["concerns"][0]["id"]
    assert [(c["id"], c["in_hand"]) for c in row()] == [(cid, True), (first["concerns"][1]["id"], False)]
    got = host.command("ideas.concern_later", {"party": design, "id": cid})
    assert got["ok"] and next(c for c in got["concerns"] if c["id"] == cid)["later"] is True
    assert [(c["id"], c["later"], c["in_hand"]) for c in row()][0] == (cid, True, False)
    host.command("ideas.concerns_again", {"party": design})
    _until(lambda: [(c["id"], c["later"], c["in_hand"]) for c in row()][0] == (cid, False, True), "the leader's next look found it again: it is a card in the hand again")
    model.answer = {"concerns": [concern("home", "note", "Plain")]}
    host.command("ideas.concerns_again", {"party": design})
    _until(lambda: [c["id"] for c in row()] == [first["concerns"][1]["id"]], "a look that does not find it again drops it")


def test_the_ways_of_a_concern_in_the_hand_each_take_it_out_of_the_hand_and_a_gone_one_is_refused_in_plain_words(host, design, model):
    model.answer = {"concerns": [concern("cart", what="One"), concern("home", what="Two"), concern("about", what="Three")]}
    ids = [c["id"] for c in (_look(host, design) and host.command("ideas.concerns", {"party": design}))["concerns"]]
    row = lambda: [c["id"] for c in next(g for g in host.command("ideas.map", {})["goals"] if g["slug"] == design)["concerns"]["list"] if c["in_hand"]]      # noqa: E731
    assert row() == ids
    host.command("ideas.concern_later", {"party": design, "id": ids[0]})
    host.command("ideas.concern_dismiss", {"party": design, "id": ids[1]})
    host.command("ideas.concern_goal", {"party": design, "id": ids[2]})
    assert row() == []
    with pytest.raises(CommandError, match="gone"):
        host.command("ideas.concern_later", {"party": design, "id": "c-none"})
    with pytest.raises(CommandError):
        host.command("ideas.concern_later", {"party": "nobody", "id": ids[0]})
