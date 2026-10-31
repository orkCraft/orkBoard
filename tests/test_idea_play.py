"""Spec 115 D (docs/specs/115-the-live-product-under-each-leaders-eyes.md §5): `realm/idea_play.py`, what the live product knew when a place on it was marked: kept beside the goal
(`play.json`), bounded, secrets out, several marks on one goal in a list, read into the goal's calls after the lens. No model, no face."""
from __future__ import annotations

import json

import pytest

from orkboard.realm import idea_lens, idea_play, ideas


def mark(**more) -> dict:
    return {"kind": "bug", "text": "Saving does nothing", "path": "/orders", "screen": {"id": "orders", "name": "Orders"}, "box": {"x": 0.2, "y": 0.1, "w": 0.25, "h": 0.2},
            "commit": "abcdef0123456789", "at": "2026-10-31T10:00:00", **more}


@pytest.fixture
def state(tmp_path):
    return tmp_path / ".orkcraft"


def test_a_mark_is_kept_beside_the_goal_and_read_back_as_it_was_given(state):
    got = idea_play.save(state, "fix-save", mark(under=[{"selector": "button.save", "role": "button", "text": "Save", "rect": {"x": 1, "y": 2, "w": 30, "h": 10}, "file": "src/Orders.tsx", "line": 12}],
                                                  errors=[{"message": "TypeError: x is undefined", "stack": "at save (src/a.js:3:5)", "source": "error", "count": 2}],
                                                  requests=[{"method": "post", "path": "/api/orders", "status": 500, "ms": 120}], lines=["GET /api/orders 500"], state={"level": 3}, picture="abc123"))
    assert (state / "ideas" / "fix-save" / "play.json").is_file()
    (one,) = idea_play.read(state, "fix-save")
    assert one == got
    assert one["kind"] == "bug" and one["path"] == "/orders" and one["screen"] == {"id": "orders", "name": "Orders"} and one["box"] == {"x": 0.2, "y": 0.1, "w": 0.25, "h": 0.2}
    assert one["under"][0]["file"] == "src/Orders.tsx" and one["under"][0]["line"] == 12
    assert one["errors"][0]["count"] == 2 and one["requests"][0]["method"] == "POST" and one["lines"] == ["GET /api/orders 500"] and one["state"] == {"level": 3} and one["picture"] == "abc123"
    assert idea_play.read(state, "no-play") == [] and idea_play.read(state, "Not A Slug") == []


def test_several_marks_on_one_goal_are_a_list_the_oldest_dropped_after_eight(state):
    for n in range(10):
        idea_play.save(state, "g", mark(text=f"mark {n}"))
    marks = idea_play.read(state, "g")
    assert [m["text"] for m in marks] == [f"mark {n}" for n in range(2, 10)]
    assert len(json.loads((state / "ideas" / "g" / "play.json").read_text())["marks"]) == idea_play.MAX_MARKS


def test_a_file_of_the_flat_first_shape_is_read_as_one_mark(state):
    (state / "ideas" / "g").mkdir(parents=True)
    (state / "ideas" / "g" / "play.json").write_text(json.dumps(mark(errors=[{"message": "boom"}])))
    (one,) = idea_play.read(state, "g")
    assert one["errors"][0]["message"] == "boom"


def test_what_is_no_mark_is_refused_in_words(state):
    with pytest.raises(ValueError, match="bug, looks wrong, missing or confusing"):
        idea_play.save(state, "g", {"kind": "praise"})
    with pytest.raises(ValueError):
        idea_play.save(state, "g", "nonsense")


def test_every_part_is_bounded(state):
    got = idea_play.save(state, "g", mark(
        errors=[{"message": f"error {n}", "stack": "s" * 900} for n in range(30)],
        requests=[{"method": "GET", "path": f"/r/{n}", "status": 500, "ms": 5} for n in range(30)],
        lines=[f"line {n}" for n in range(100)] + ["x" * 900],
        under=[{"selector": f"div.{n}", "text": "t" * 500} for n in range(9)],
        text="w" * 900, state={f"k{n}": "z" * 100 for n in range(50)}))
    assert len(got["errors"]) == 10 and got["errors"][-1]["message"] == "error 29" and len(got["errors"][0]["stack"]) <= 300
    assert len(got["requests"]) == 10 and got["requests"][-1]["path"] == "/r/29"
    assert len(got["lines"]) == 40 and len(got["lines"][-1]) <= 300
    assert len(got["under"]) == 3 and len(got["under"][0]["text"]) <= 80
    assert len(got["text"]) <= 300
    assert got["state"] is None                                                       # 2 KB of state at most: a larger one is none
    small = idea_play.save(state, "g", mark(state={"level": 3, "coins": [1, 2, 3]}))
    assert small["state"] == {"level": 3, "coins": [1, 2, 3]}


def test_the_box_is_kept_in_shares_inside_the_frame(state):
    got = idea_play.save(state, "g", mark(box={"x": -1, "y": 0.5, "w": 4, "h": "x"}))
    assert got["box"] == {"x": 0.0, "y": 0.5, "w": 1.0, "h": 0.0}


def test_secrets_are_out_a_line_that_names_one_whole_and_a_token_masked_elsewhere(state):
    got = idea_play.save(state, "g", mark(
        lines=["listening on 3000", "loaded .env.local ok", "key sk-abcdefghij1234 used", "token ghp_abcdefghijkl", "read id_rsa", "fine"],
        errors=[{"message": "fetch failed with sk-abcdefghij1234 for /api", "stack": "at x (/home/me/.ssh/id_rsa:1:1)"}],
        requests=[{"method": "GET", "path": "/api/me", "status": 500, "ms": 5, "host": "api.example.com"}],
        under=[{"selector": "div", "file": ".env"}, {"selector": "p", "file": "src/ok.tsx"}],
        state={"user": "ann", "apiKey": "abc", "password": "hunter2", "level": 2, "nested": {"authToken": "t", "ok": True}}))
    assert got["lines"] == ["listening on 3000", "fine"]
    assert "sk-" not in got["errors"][0]["message"] and "***" in got["errors"][0]["message"] and "id_rsa" not in got["errors"][0]["stack"]
    assert [u.get("file") for u in got["under"]] == [None, "src/ok.tsx"]
    assert got["state"] == {"user": "ann", "apiKey": "***", "password": "***", "level": 2, "nested": {"authToken": "***", "ok": True}}
    kept = (state / "ideas" / "g" / "play.json").read_text()
    for leak in ("sk-abc", "ghp_abc", "hunter2", "id_rsa", ".env"):
        assert leak not in kept


def test_prompt_lines_say_the_failure_first_and_the_element_and_state_after_and_nothing_with_no_mark(state):
    assert idea_play.prompt_lines(state, "g") == ""
    idea_play.save(state, "g", mark(errors=[{"message": "TypeError: x is undefined", "stack": "at save (src/a.js:3:5)", "count": 3}],
                                    requests=[{"method": "POST", "path": "/api/orders", "status": 500, "ms": 120}], lines=["POST /api/orders 500", "stack…"],
                                    under=[{"selector": "button.save", "role": "button", "text": "Save", "file": "src/Orders.tsx", "line": 12}], state={"level": 3}))
    text = idea_play.prompt_lines(state, "g")
    assert text.startswith("The person marked places on the running product")
    assert "Mark 1: a bug on the page /orders (the screen \"Orders\"), at commit abcdef0, the box from 20 % to 45 % across and 10 % to 30 % down: Saving does nothing" in text   # no picture kept: the box is said here
    order = [text.index(x) for x in ("TypeError: x is undefined (x3)", "POST /api/orders 500, 120 ms", "The server's last lines", "The element: button.save (button) saying \"Save\" in src/Orders.tsx:12", "The game's state: {\"level\": 3}")]
    assert order == sorted(order)


def test_with_a_picture_the_lens_says_the_box_so_the_play_does_not(state):
    idea_play.save(state, "g", mark(picture="abc123"))
    assert "from 20 %" not in idea_play.prompt_lines(state, "g")


def test_the_play_is_read_into_the_calls_after_the_lens(state):
    assert idea_lens.attached(state, "g") == ""
    idea_play.save(state, "g", mark(errors=[{"message": "boom"}]))
    ideas._write_json(state / "ideas" / "g" / "state.json", {"marks": [{"map": "system", "id": "src/pages", "name": "src/pages"}]})
    got = idea_lens.attached(state, "g")
    assert got.index("The person pointed at these places of the project's maps") < got.index("The person marked places on the running product")
    assert got.endswith(idea_play.prompt_lines(state, "g"))


def test_a_bug_marks_failure_is_an_error_or_a_failed_request_of_a_mark_of_that_kind(state):
    assert idea_play.failed(state, "g") is False
    idea_play.save(state, "g", mark())
    assert idea_play.failed(state, "g") is False
    idea_play.save(state, "g", mark(kind="looks", errors=[{"message": "boom"}]))
    assert idea_play.failed(state, "g") is False and idea_play.failed(state, "g", "looks") is True
    idea_play.save(state, "g", mark(requests=[{"method": "GET", "path": "/x", "status": 500, "ms": 1}]))
    assert idea_play.failed(state, "g") is True


def test_the_newest_goal_with_a_mark_of_that_kind_on_that_screen_or_page(state):
    idea_play.save(state, "old", mark(at="2026-10-31T09:00:00"))
    idea_play.save(state, "new", mark(at="2026-10-31T10:00:00"))
    idea_play.save(state, "other-kind", mark(kind="looks", at="2026-10-31T11:00:00"))
    idea_play.save(state, "other-screen", mark(screen={"id": "cart", "name": "Cart"}, path="/cart", at="2026-10-31T12:00:00"))
    slugs = ["old", "new", "other-kind", "other-screen", "none"]
    assert idea_play.newest(state, slugs, "orders", "bug") == "new"
    assert idea_play.newest(state, slugs, "orders", "looks") == "other-kind"
    assert idea_play.newest(state, slugs, "orders", "missing") == ""
    idea_play.save(state, "bare", mark(screen=None, path="/lost?x=1", at="2026-10-31T13:00:00"))
    assert idea_play.newest(state, [*slugs, "bare"], "", "bug", "/lost#top") == "bare"                  # a place no screen fits is told by its page
    assert idea_play.newest(state, slugs, "", "bug", "/lost") == ""
