"""Spec 121 A (docs/specs/121-the-day-the-morning-and-the-night.md §2): the sketch's rules, with no model and no face (realm/sketches.py) — which goals get one (each craft, a goal type, the short way and a pitch
none, a project with nothing to sketch from none), the project's look, the leader's page answer parsed strictly (two or three, the size, an outside address refused), where a goal's sketch stands, and what
the work reads of the sketch picked."""
from __future__ import annotations

import subprocess

import pytest

from orkboard.realm import idea_pick, sketches
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


def test_the_short_way_a_bug_a_tidy_and_a_pitch_get_none_whatever_the_route():
    route = ["design", "tech"]
    assert sketches.wanted(route, {"short": True}, ["screen"]) == "" and sketches.wanted(route, {"kind": "bug"}, ["screen"]) == ""
    assert sketches.wanted(route, {"kind": "tidy"}, []) == "" and sketches.wanted(route, {"kind": "pitch"}, []) == ""
    assert sketches.wanted(route, {}, ["tidy", "screen"]) == "" and sketches.wanted(route, {}, ["bug"]) == ""
    assert sketches.wanted(route, {"kind": "feature", "short": False}, ["screen"]) == "design"


def test_a_project_with_nothing_to_sketch_from_gets_none():
    assert sketches.wanted(["design"], {}, ["screen"], ground=False) == "" and sketches.wanted(["design"], {}, ["screen"], ground=True) == "design"


def test_art_makes_a_sound_or_a_picture_and_needs_the_media_tools_of_its_kind():
    assert sketches.art_kind(["sound"]) == "audio" and sketches.art_kind(["icon"]) == "image" and sketches.art_kind([]) == "image" and sketches.art_kind(["sound", "icon"]) == "audio"
    tools = {"sox"}
    have = lambda cmd: f"/usr/bin/{cmd}" if cmd in tools else None            # noqa: E731
    assert sketches.media_ready("audio", have) and not sketches.media_ready("image", have)
    tools.update({"python3"})
    assert sketches.media_ready("image", have) and sketches.media_ready("audio", have)
    tools.clear()
    assert not sketches.media_ready("audio", have) and not sketches.media_ready("image", have) and not sketches.media_ready("video", have)


def test_the_rounds_are_three_and_the_page_sixty_kilobytes():
    assert (sketches.ROUNDS, sketches.PAGE_KB, sketches.LOOK_CHARS) == (3, 60, 4000) and idea_pick.KINDS["page"].limit == 60 * 1024
    assert [sketches.left(n) for n in (0, 1, 2, 3, 4)] == [3, 2, 1, 0, 0]


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


def test_the_look_is_read_at_dev_when_the_repository_has_it_there_and_in_the_folder_else(tmp_path):
    git(tmp_path, "init", "-b", "dev")
    git(tmp_path, "config", "user.email", "t@orkcraft.local")
    git(tmp_path, "config", "user.name", "T")
    (tmp_path / "styles.css").write_text("body { color: black; }\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "a look")
    (tmp_path / "styles.css").write_text("body { color: hotpink; }\n", encoding="utf-8")                  # the folder moved on; dev did not
    assert "black" in sketches.look(tmp_path, "dev") and "hotpink" not in sketches.look(tmp_path, "dev")
    assert "hotpink" in sketches.look(tmp_path) and "hotpink" in sketches.look(tmp_path, "nowhere")


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


def test_a_name_and_a_line_are_cut_and_one_line_each():
    got = sketches.parse_pages({"variants": [variant("  A very\nlong name for a variant of a sketch ", "why\n" + "x" * 500), variant("B")]})
    assert got[0]["name"] == "A very long name for a v" and len(got[0]["name"]) <= sketches.NAME_CHARS and "\n" not in got[0]["why"] and len(got[0]["why"]) <= sketches.WHY_CHARS


def test_a_page_begins_as_a_page_does():
    for html in ("<!doctype html><title>t</title>", "<!DOCTYPE html>\n<html></html>", "<html><body></body></html>", "<!-- a sketch -->\n<!doctype html><title>t</title>", "\n  <html>"):
        assert sketches.clean_page(variant(html=html)) is not None, html
    for html in ("<div>a fragment</div>", "Here is the page: <!doctype html><title>t</title>", "```html\n<!doctype html><title>t</title>\n```", "<style>a{}</style><html></html>"):
        assert sketches.clean_page(variant(html=html)) is None, html


def test_a_page_over_sixty_kilobytes_or_with_a_control_character_is_refused():
    fill = "<!doctype html><body>" + "a" * (sketches.PAGE_KB * 1024 - 40) + "</body>"
    assert len(fill.encode()) < sketches.PAGE_KB * 1024 and sketches.clean_page(variant(html=fill)) is not None
    assert sketches.clean_page(variant(html=fill + "b" * 100)) is None
    wide = "<!doctype html><body>" + "é" * (sketches.PAGE_KB * 1024 // 2 - 10) + "</body>"             # bytes, not characters
    assert len(wide) < sketches.PAGE_KB * 1024 < len(wide.encode()) and sketches.clean_page(variant(html=wide)) is None
    assert sketches.clean_page(variant(html=PAGE + "\x00")) is None and sketches.clean_page(variant(html=PAGE + "\x07")) is None
    assert sketches.clean_page(variant(html=PAGE + "\ttab\r\nline\n")) is not None


@pytest.mark.parametrize("snippet", [
    '<img src="https://example.com/a.png">', "<img src='http://example.com/a.png'>", '<img src="//example.com/a.png">', '<script src="app.js"></script>', '<link rel="stylesheet" href="style.css">',
    '<link rel=stylesheet href="https://fonts.example/css">', '<a href="/about">About</a>', '<a href="https://example.com">x</a>', '<a href="mailto:a@b.c">x</a>', '<a href="javascript:alert(1)">x</a>',
    '<img srcset="a.png 1x, b.png 2x">', '<video poster="p.png"></video>', '<form action="/send"></form>', '<button formaction="/x">x</button>', '<IMG SRC="https://example.com/a.png">',
    '<svg><use xlink:href="icons.svg#a"></use></svg>', '<style>body{background:url(https://example.com/a.png)}</style>', "<style>body{background:url('bg.png')}</style>",
    '<img src="&#104;ttps://example.com/a.png">', '<img src="&#x68;ttp://example.com/a.png">', '<style>@import "other.css";</style>', "<style>@IMPORT url(data:text/css,a{});</style>", '<div style="background:url(  /x.png  )"></div>', '<script>el.src = "https://example.com/x.js"</script>',
])
def test_a_page_that_leads_outside_itself_is_refused(snippet):
    html = f"<!doctype html><html><body>{snippet}</body></html>"
    assert sketches.outside(html) != "" and sketches.clean_page(variant(html=html)) is None
    assert sketches.parse_pages({"variants": [variant("A"), variant("B", html=html)]}) is None


@pytest.mark.parametrize("snippet", [
    '<img src="data:image/svg+xml;utf8,<svg xmlns=&quot;http://www.w3.org/2000/svg&quot;/>">', '<a href="#top">up</a>', '<a href="#">x</a>', '<a href="">x</a>',
    "<style>body{background:url(data:image/png;base64,AAAA)}</style>", '<div style="background:url(&quot;data:image/png;base64,AAAA&quot;)"></div>', "<p>See https://example.com for more</p>",
    '<button data-src="x" data-href="y">x</button>', "<script>const href = 1; let src = 2; function f(){ return href + src }</script>", '<svg><path d="M0 0"/></svg>',
])
def test_a_page_whose_pictures_style_and_script_are_inline_is_kept(snippet):
    html = f"<!doctype html><html><body>{snippet}</body></html>"
    assert sketches.outside(html) == "" and sketches.clean_page(variant(html=html)) is not None


def test_the_refusal_names_what_led_outside():
    assert sketches.outside('<!doctype html><img src="https://example.com/a.png">').startswith("src=https://example.com")
    assert sketches.outside("<!doctype html><style>a{background:url(x.png)}</style>") == "url(x.png)" and sketches.outside("<!doctype html><style>@import 'a.css'</style>") == "@import"


# -- where a goal's sketch stands -------------------------------------------------------------------------------------------------------------

def test_a_goals_sketch_record_is_kept_beside_it_and_forgotten(tmp_path):
    assert sketches.record(tmp_path, "g") == {}
    got = sketches.save(tmp_path, "g", status="making", round=1, craft="design")
    assert got["status"] == "making" and sketches.record(tmp_path, "g") == got
    sketches.save(tmp_path, "g", status="asked")
    assert sketches.record(tmp_path, "g") == {"status": "asked", "round": 1, "craft": "design"}
    assert (tmp_path / "ideas" / "g" / "sketch.json").is_file()
    sketches.forget(tmp_path, "g")
    assert sketches.record(tmp_path, "g") == {} and sketches.picked(tmp_path, "g") is None
    sketches.forget(tmp_path, "g")                                                                   # nothing to forget is fine


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


def test_a_short_page_is_read_whole_and_a_picture_or_a_sound_by_its_name_and_line(tmp_path):
    state = _picked(tmp_path)
    got = sketches.context(state, "g")
    assert PAGE in got and not got.endswith("…") and "The person said" not in got
    sketches.save(state, "g", picked={"key": "B", "name": "Dark", "why": "", "note": "", "file": "b.png", "mime": "image/png", "kind": "image", "round": 1, "pick": "sketch-r1"})
    assert sketches.context(state, "g") == "Sketch B · Dark\nIt is a picture (`b.png`): its name and line are all that is read here."
    sketches.save(state, "g", picked={"key": "C", "name": "Horn", "why": "low", "note": "", "file": "c.wav", "mime": "audio/wav", "kind": "audio", "round": 1, "pick": "sketch-r1"})
    assert "It is a sound (`c.wav`)" in sketches.context(state, "g")


def test_nothing_is_read_of_a_sketch_that_was_not_picked(tmp_path):
    state = _picked(tmp_path)
    for status in ("asked", "skipped", "making", ""):
        sketches.save(state, "g", status=status)
        assert sketches.context(state, "g") == "" and sketches.picked(state, "g") is None and sketches.reference(state, "g") is None and sketches.reference_dirs(state, "g") == ()
    assert sketches.context(tmp_path / "nowhere", "g") == ""


def test_the_picked_file_is_a_reference_in_the_pick_folder_outside_any_worktree(tmp_path):
    state = _picked(tmp_path)
    path = sketches.reference(state, "g")
    assert path == state / "ideas" / "g" / "picks" / "sketch-r1" / "a.html" and path.is_file()
    assert sketches.reference_dirs(state, "g") == (str(path.parent),)
    path.unlink()
    assert sketches.reference(state, "g") is None and sketches.reference_dirs(state, "g") == ()
