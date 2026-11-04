"""Spec 135 A (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md; decisions §242.1–§242.4) on the host: `goal_match` (the words, the face-down goals, the score and its bars, not too
big), `ideas.add {match: true}` (the field's line as data, nothing written, no call; `apart: true` adds), and *Add to it* through `ideas.add_to_goal` with its record of added words."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import event_log, goal_match, goal_refine, goal_team, idea_ripe, ideas, library, lexicon, spec_sections


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    h.command("ideas.board_set", {"autostart": False})
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


@pytest.fixture
def calls(host):
    """Every model call the keeper makes, counted (the stub answers a plain decision)."""
    seen: list[str] = []

    def call(tier, prompt, effort="", budget=None):
        step = host.ideas.keeper.measure()["step"]
        seen.append(step)
        out = {"decide": {"title": "Dark mode with a timer", "why": "Night.", "points": ["Tech adds it.", "Off by default."]}}.get(step, {})
        return json.dumps(out), 0.01, 10, ""

    host.ideas.keeper.call = call
    return seen


def _party(host, title, craft, leader, team):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def tech(host):
    return _party(host, "Tech", "engineering", "architect", ["grunt", "tester"])


@pytest.fixture
def art(host):
    return _party(host, "Art", "design", "art-director", ["artist"])


def _held(host, party, text, state="raw", route=None, marks=None):
    """A goal lying face down: added on hold (raw), then set to `state` with its route and marks."""
    slug = host.command("ideas.add", {"text": text, "track": party, "hold": True})["slug"]
    ideas.save_state(host.ideas.state_dir, slug, state=state, **({"route": [{"party": p, "leader": ""} for p in route]} if route else {}), **({"marks": marks} if marks else {}))
    return slug


def _match(host, text, route=(), marks=(), home=""):
    return goal_match.match(host.ideas.root(), host.ideas.state_dir, text, [{"party": p} for p in route], marks, home)


def _events(host, name):
    return [e for e in event_log.read(Path(host.repo_root)) if e["event"] == name]


def test_words_are_the_significant_ones_lightly_stemmed():
    assert goal_match.words("Add a dark mode, with timers!") == {"dark", "mode", "timer"}
    assert goal_match.words("Timer timers TIMING ed up") == {"timer", "tim"}
    assert goal_match.words("do it") == set() and goal_match.words("ab") == set()
    assert goal_match.words("x " * 5000 + "lobby") == set()                       # a text is cut at JOIN_CHARS: what is past it is not read
    assert goal_match.words("lobby " + "x " * 5000) == {"lobby"}


def test_the_face_down_goals_are_those_before_their_spec_in_the_orkmasters_order(host, tech, calls):
    a = _held(host, tech, "first goal about lobbies", "raw")
    b = _held(host, tech, "second goal about lobbies", "routed", route=[tech])
    c = _held(host, tech, "third goal about lobbies", "talk", route=[tech])
    d = _held(host, tech, "fourth goal about lobbies", "decided", route=[tech])
    spec_sections.save_record(host.ideas.state_dir, d, {"decision": {"title": "t", "text": "x", "confirmed": False}})
    _held(host, tech, "fifth goal about lobbies", "sections", route=[tech])                   # its spec is being written: never offered
    _held(host, tech, "sixth goal about lobbies", "ready", route=[tech])
    e = _held(host, tech, "seventh goal about lobbies", "decided", route=[tech])
    spec_sections.save_record(host.ideas.state_dir, e, {"decision": {"title": "t", "text": "x", "confirmed": True}})      # agreed already
    f = _held(host, tech, "eighth goal about lobbies", "decided", route=[tech])
    spec_sections.save_record(host.ideas.state_dir, f, {"decision": {"title": "t", "text": "x", "confirmed": False}, "ripe": {"left_s": 0.0, "held": True, "by": "person"}})   # put off
    assert idea_ripe.of(host.ideas.state_dir, f)["held"]
    got = goal_match.candidates(host.ideas.root(), host.ideas.state_dir)
    assert [c_["slug"] for c_ in got] == [a, b, c, d] and got[0] == {"slug": a, "title": ideas.idea_page(host.ideas.root(), a).title, "party": tech, "state": "raw"}


def test_the_same_words_make_a_match_one_word_never_does(host, tech, calls):
    slug = _held(host, tech, "Add a dark mode switch to the settings page")
    got = _match(host, "dark mode toggle for the settings", home=tech)
    assert got["idea"] == slug and got["why"] == ["words", "route"] and got["shared"] == ["dark", "mode", "setting"] and 0.3 <= got["score"] <= 1 and got["adds"] == []         # both lie in Tech: the same route
    assert _match(host, "dark theme for the printer", home=tech) is None                  # one shared word is no match, whatever its score
    assert _match(host, "ok", home=tech) is None


def test_the_same_route_lowers_the_bar_and_the_same_place_lowers_it_more(host, tech, art, calls):
    marks = [{"map": "system", "id": "server/lobby.ts", "name": "lobby.ts"}]
    slug = _held(host, tech, "dark mode toggle settings menu page sidebar layout theme colours", "routed", route=[tech], marks=marks)
    text = "dark mode timer evening schedule"
    mine, theirs = goal_match.words(text), goal_match.words(f"dark mode toggle settings menu page sidebar layout theme colours {''}")
    score = 2 * len(mine & theirs) / (len(mine) + len(theirs))
    assert goal_match.BAR_ROUTE <= score < goal_match.BAR
    assert _match(host, text, home="") is None                                             # words alone: below the bar
    assert _match(host, text, route=[art]) is None and _match(host, text, route=[art], home=art) is None          # another route: still below it
    got = _match(host, text, route=[tech])
    assert got["idea"] == slug and got["why"] == ["words", "route"] and got["adds"] == []
    deeper = _held(host, tech, " ".join(["dark mode"] + [f"filler{n}" for n in range(14)]), "routed", route=[tech], marks=marks)
    low = 2 * 2 / (len(goal_match.words(text)) + len(goal_match.words("dark mode " + " ".join(f"filler{n}" for n in range(14)))))
    assert goal_match.BAR_PART <= low < goal_match.BAR_ROUTE
    assert _match(host, text, route=[tech], marks=[])["idea"] == slug                      # the nearer goal wins; the second is under its bar with no place
    ideas.drop(host.ideas.root(), slug, host.ideas.state_dir)
    assert _match(host, text, route=[tech]) is None
    got = _match(host, text, route=[tech], marks=[{"map": "system", "id": "server/lobby.ts"}])
    assert got["idea"] == deeper and got["why"] == ["words", "route", "part"]
    assert _match(host, text, route=[tech], marks=[{"map": "system", "id": "server/other.ts"}]) is None


def test_the_best_score_wins_and_a_tie_goes_to_the_earlier(host, tech, calls):
    _held(host, tech, "dark mode switch for the settings page with a long list of other wishes around it")
    best = _held(host, tech, "dark mode switch settings")
    assert _match(host, "dark mode switch settings", home=tech)["idea"] == best
    a = _held(host, tech, "lobby reconnect timeout fix")
    _held(host, tech, "lobby reconnect timeout fix again")
    assert _match(host, "lobby reconnect timeout fix", home=tech)["idea"] == a            # …the earlier in the Orkmaster's order (the first scores higher: fewer words)


def test_not_too_big_a_goal_that_would_gain_two_parties_or_pass_its_words_is_skipped(host, tech, art, calls):
    big = _held(host, tech, "dark mode switch settings " + "word " * 10)
    near = _held(host, tech, "dark mode switch settings page", "routed", route=[tech])
    assert goal_match.fits(host.ideas.root(), host.ideas.state_dir, near, "dark mode", [tech, art]) is True            # one party added
    third = _party(host, "Run", "data", "ops-lead", ["sre"])
    assert goal_match.fits(host.ideas.root(), host.ideas.state_dir, near, "dark mode", [tech, art, third]) is False   # two
    assert _match(host, "dark mode switch settings", route=[tech, art, third])is None
    ideas.update(host.ideas.root(), big, {"Gist": "dark mode switch settings " + "w" * goal_match.JOIN_CHARS})
    assert goal_match.fits(host.ideas.root(), host.ideas.state_dir, big, "more", [tech]) is False                      # its words would pass JOIN_CHARS
    assert _match(host, "dark mode switch settings", home=tech)["idea"] == near


def test_the_field_is_told_of_a_match_and_nothing_is_written_nor_called(host, tech, calls):
    slug = _held(host, tech, "Add a dark mode switch to the settings page")
    before = (sorted(p.name for p in (host.ideas.root() / ideas.IDEAS).glob("*.md")), len(event_log.read(Path(host.repo_root))))
    got = host.command("ideas.add", {"text": "dark mode toggle for the settings", "track": tech, "match": True, "element": "ice"})
    assert got["slug"] == "" and got["match"]["idea"] == slug and got["match"]["title"] and got["match"]["why"] == ["words", "route"]
    assert got["match"]["reworded"] is False and got["match"]["cost"] is None and calls == []
    assert sorted(p.name for p in (host.ideas.root() / ideas.IDEAS).glob("*.md")) == before[0]
    names = [e["event"] for e in event_log.read(Path(host.repo_root))][before[1]:]
    assert names == [event_log.GOAL_MATCHED]
    assert _events(host, event_log.GOAL_MATCHED)[0]["idea"] == slug


def test_a_match_on_a_decided_goal_says_it_is_worded_again_and_its_cost(host, tech, calls):
    slug = _held(host, tech, "Add a dark mode switch to the settings page", "decided", route=[tech])
    spec_sections.save_record(host.ideas.state_dir, slug, {"decision": {"title": "Dark mode", "text": "Why: x.\n\n1. y", "confirmed": False}})
    got = host.command("ideas.add", {"text": "dark mode toggle for the settings", "track": tech, "match": True})["match"]
    assert got["state"] == "decided" and got["reworded"] is True and got["cost"]["calls"] == 1 and got["cost"]["usd_high"]


def test_no_match_adds_as_today_and_keep_apart_adds_and_says_so(host, tech, calls):
    slug = _held(host, tech, "Add a dark mode switch to the settings page")
    got = host.command("ideas.add", {"text": "reconnect the lobby after a drop", "track": tech, "match": True})
    assert got["slug"] and "match" not in got
    apart = host.command("ideas.add", {"text": "dark mode toggle for the settings", "track": tech, "match": True, "apart": True, "with": slug})
    assert apart["slug"] and "match" not in apart
    (ev,) = _events(host, event_log.GOAL_KEPT_APART)
    assert ev["with"] == slug and not _events(host, event_log.GOAL_MATCHED)


def test_only_the_field_matches_a_plain_add_a_hold_a_type_a_recurring_goal_never(host, tech, calls):
    _held(host, tech, "Add a dark mode switch to the settings page")
    same = {"text": "dark mode toggle for the settings", "track": tech}
    assert host.command("ideas.add", dict(same))["slug"]                                   # a phone's, a script's, Orkline's: no `match`, never matched
    assert host.command("ideas.add", {**same, "match": True, "hold": True})["slug"]
    assert host.command("ideas.add", {**same, "match": True, "recurring": True})["slug"]
    assert not _events(host, event_log.GOAL_MATCHED)


def test_add_to_it_is_add_to_the_goal_with_its_rune_and_its_record(host, tech, calls):
    slug = _held(host, tech, "Add a dark mode switch to the settings page")
    got = host.command("ideas.add_to_goal", {"idea": slug, "text": "Also a timer for the evening", "element": "ice", "via": "match"})
    assert got["ok"] is True and got["reworded"] is False
    rows = goal_refine.added_rows(host.ideas.state_dir, slug)
    assert [(r["text"], r["element"], r["via"]) for r in rows] == [("Also a timer for the evening", "ice", "match")] and rows[0]["at"]
    assert ideas.idea_page(host.ideas.root(), slug).section("Gist").endswith("Added: Also a timer for the evening")
    host.command("ideas.add_to_goal", {"idea": slug, "text": "And a sunset mode"})
    assert [r["via"] for r in goal_refine.added_rows(host.ideas.state_dir, slug)] == ["match", ""]
    (first, _second) = _events(host, event_log.GOAL_ADDED_TO)
    assert first["via"] == "match" and first["element"] == "ice" and "text" not in first
    with pytest.raises(CommandError, match="Pick one of the five runes"):
        host.command("ideas.add_to_goal", {"idea": slug, "text": "x", "element": "mud"})
    ideas.save_state(host.ideas.state_dir, slug, state="sections")
    with pytest.raises(CommandError, match="agreed"):
        host.command("ideas.add_to_goal", {"idea": slug, "text": "too late", "via": "match"})
    assert len(goal_refine.added_rows(host.ideas.state_dir, slug)) == 2


def test_the_added_words_record_reads_a_broken_file_as_none(host, tech, calls):
    slug = _held(host, tech, "Add a dark mode switch to the settings page")
    (ideas.state_folder(host.ideas.state_dir, slug) / goal_refine.FILE).write_text("{not json", encoding="utf-8")
    assert goal_refine.added_rows(host.ideas.state_dir, slug) == []
    assert goal_refine.add_record(host.ideas.state_dir, slug, " words ", "lava", "nonsense") == [{**goal_refine.added_rows(host.ideas.state_dir, slug)[0]}]
    assert goal_refine.added_rows(host.ideas.state_dir, slug)[0]["via"] == "" and goal_refine.added_rows(host.ideas.state_dir, slug)[0]["text"] == "words"


def test_the_words_are_in_the_glossary():
    assert [lexicon.term(k) for k in ("looks_like_part_of", "add_to_it", "keep_apart", "look_like_one", "join", "split")] == [
        "Looks like part of: <title>", "Add to it", "Keep apart", "These look like one goal", "Join", "Split"]
    assert event_log.GOAL_MATCHED in event_log.EVENTS and event_log.GOAL_KEPT_APART in event_log.EVENTS
