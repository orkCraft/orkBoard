"""Spec 121 A (docs/specs/121-the-day-the-morning-and-the-night.md §2): the sketch's rules, with no model and no face (realm/sketches.py) — which goals get one (each craft, a goal type, the short way and a pitch
none, a project with nothing to sketch from none), the project's look, the leader's page answer parsed strictly (two or three, the size, an outside address refused), where a goal's sketch stands, and what
the work reads of the sketch picked."""
from __future__ import annotations

import subprocess

import pytest

from orkboard.realm import sketches
from tests import pick_files as pf

PAGE = "<!doctype html><html><head><style>body{margin:0}</style></head><body><button onclick=\"this.textContent='Done'\">Press</button></body></html>"


def variant(name="Quiet", why="A calm list", html=PAGE):
    return {"name": name, "why": why, "html": html}


# -- which goals ------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("route, expect", [
    (["product", "design", "tech"], "design"), (["design"], "design"), (["game-design", "tech"], "game-design"), (["tech", "art"], "art"),
    (["product", "art", "design"], "art"), (["design", "game-design"], "design"),                     # several crafts: the first one on the route sketches
    ([{"party": "p1", "craft": "tech"}, {"party": "p2", "craft": "design"}], "design"),                # rows with a craft, as the keeper has them
])
def test_a_goal_whose_route_has_design_art_or_game_design_is_sketched_by_the_first_of_them(route, expect):
    assert sketches.wanted(route, {}, []) == expect and sketches.craft_for(route, []) == expect


@pytest.mark.parametrize("types, expect", [
    (["screen"], "design"), (["flow-feature"], "design"), (["icon"], "art"), (["logo"], "art"), (["character"], "art"), (["sound"], "art"), (["balance"], "game-design"),
    (["feature", "screen"], "design"), (["screen", "sound"], "design"),                                # the first type that is seen or heard
])
def test_a_goal_type_that_is_seen_or_heard_names_its_craft_when_the_route_names_none(types, expect):
    assert sketches.wanted(["tech", "product"], {}, types) == expect


def test_the_route_wins_over_the_type_and_a_goal_of_no_craft_and_no_type_gets_none():
    assert sketches.wanted(["design"], {}, ["sound"]) == "design"
    assert sketches.wanted(["tech", "product"], {}, ["feature"]) == "" and sketches.wanted([], {}, []) == "" and sketches.wanted(["tech"], None) == ""
    assert sketches.wanted(["tech", "release", "marketing", "run", "liveops"], {}, ["bug"]) == ""


# -- the project's look -----------------------------------------------------------------------------------------------------------------------

def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def test_the_look_is_the_design_tokens_else_the_top_stylesheet_cut_at_four_thousand(tmp_path):
    assert sketches.look(tmp_path) == ""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.css").write_text("body { color: red; }\n", encoding="utf-8")
    assert sketches.look(tmp_path) == "/* src/index.css */\nbody { color: red; }"
    (tmp_path / "tokens.css").write_text(":root { --ink: #111; }\n", encoding="utf-8")
    assert sketches.look(tmp_path).startswith("/* tokens.css */\n:root { --ink: #111; }")                   # the tokens before any stylesheet
    (tmp_path / "design-tokens.json").write_text('{"ink": "#111"}', encoding="utf-8")
    assert sketches.look(tmp_path).startswith("/* design-tokens.json */")
    (tmp_path / "design-tokens.json").write_text("x" * 9000, encoding="utf-8")
    got = sketches.look(tmp_path)
    assert len(got) <= sketches.LOOK_CHARS and got.startswith("/* design-tokens.json */\nxxxx")
    (tmp_path / "design-tokens.json").write_text("  \n", encoding="utf-8")                                    # an empty one is none
    assert sketches.look(tmp_path).startswith("/* tokens.css */")


# -- a page, strictly -------------------------------------------------------------------------------------------------------------------------

def test_two_or_three_clean_variants_are_a_sketch_and_nothing_else_is():
    two, three = [variant("A"), variant("B")], [variant("A"), variant("B"), variant("C")]
    assert sketches.parse_pages({"variants": two}) == two and sketches.parse_pages({"variants": three}) == three
    assert sketches.parse_pages({"variants": [variant("A")]}) is None and sketches.parse_pages({"variants": [*three, variant("D")]}) is None
    assert sketches.parse_pages({"variants": []}) is None and sketches.parse_pages({}) is None and sketches.parse_pages(None) is None and sketches.parse_pages([variant("A"), variant("B")]) is None
    assert sketches.parse_pages({"variants": "two"}) is None and sketches.parse_pages({"variants": [variant("A"), "B"]}) is None
    assert sketches.parse_pages({"variants": [variant("A"), variant("a")]}) is None                  # the same name twice
    assert sketches.parse_pages({"variants": [variant("A"), variant("")]}) is None and sketches.parse_pages({"variants": [variant("A"), {"name": "B", "why": "x"}]}) is None
    assert sketches.parse_pages({"variants": [variant("A"), variant("B", html="   ")]}) is None and sketches.parse_pages({"variants": [variant("A"), variant("B", html=3)]}) is None


def test_a_page_over_sixty_kilobytes_or_with_a_control_character_is_refused():
    fill = "<!doctype html><body>" + "a" * (sketches.PAGE_KB * 1024 - 40) + "</body>"
    assert len(fill.encode()) < sketches.PAGE_KB * 1024 and sketches.clean_page(variant(html=fill)) is not None
    assert sketches.clean_page(variant(html=fill + "b" * 100)) is None
    wide = "<!doctype html><body>" + "é" * (sketches.PAGE_KB * 1024 // 2 - 10) + "</body>"             # bytes, not characters
    assert len(wide) < sketches.PAGE_KB * 1024 < len(wide.encode()) and sketches.clean_page(variant(html=wide)) is None
    assert sketches.clean_page(variant(html=PAGE + "\x00")) is None and sketches.clean_page(variant(html=PAGE + "\x07")) is None
    assert sketches.clean_page(variant(html=PAGE + "\ttab\r\nline\n")) is not None


# -- where a goal's sketch stands -------------------------------------------------------------------------------------------------------------



# -- what the work reads of the sketch picked -------------------------------------------------------------------------------------------------

def _picked(tmp_path, html=PAGE, **more):
    pick = pf.make_page_pick(tmp_path / "state", tmp_path / "scratch", html.encode(), slug="g", tid="sketch")
    sketches.save(tmp_path / "state", "g", status="picked", picked={"key": "A", "name": "Quiet", "why": "A calm list", "note": "", "file": "a.html", "mime": "text/html", "kind": "page", "round": 1,
                                                                     "pick": pick["id"], **more})
    return tmp_path / "state"


def test_the_sections_read_the_page_picked_cut_at_six_thousand_characters_with_the_note(tmp_path):
    state = _picked(tmp_path, html="<!doctype html><body>" + "x" * 9000 + "</body>", note="Bigger buttons")
    got = sketches.context(state, "g")
    assert got.startswith("Sketch A · Quiet — A calm list\nThe person said: \"Bigger buttons\"\nIts page (the first 6,000 characters):\n<!doctype html>") and got.endswith("…")
    assert len(got) < 6000 + 300 and "x" * 5000 in got and "x" * 6001 not in got

