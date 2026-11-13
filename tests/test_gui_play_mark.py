"""Spec 115 D (docs/specs/115-the-live-product-under-each-leaders-eyes.md §5; decisions §193): the mark on the live product, `gui/ideas_play_mark.py`. `ideas.play_events` (the probe's events
in batches, one ring a play), `ideas.play_place`, `ideas.play_hints`, `ideas.play_mark` (the goal through `ideas.add`'s way, its screen lens with the box and the picture, its play) and `ideas.play_mark_offer`.

Play is a stand-in that plays (its id, commit, worktree and server lines); the picture is drawn by the real Chromium once (a snapshot, and a page drawn anew) and by a stand-in elsewhere."""
from __future__ import annotations

import base64
import http.server
import threading
import time
from pathlib import Path

import pytest

from orkboard.core import idea_shot
from orkboard.gui import ideas_play_mark
from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import goal_route, goal_team, idea_lens, idea_play, ideas, library
from tests.test_commit_goal import repo  # noqa: F401  (the fixture)
from tests.test_screen_map import REACT, on_dev

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
needs_browser = pytest.mark.skipif(idea_shot.browser() is None, reason="no Chromium here")
BOX = {"x": 0.2, "y": 0.1, "w": 0.25, "h": 0.2}
AGENTS = ["architect", "grunt", "tester", "product-manager", "copywriter", "product-designer", "artist", "ui-kit"]


class Playing:
    """Play, playing: what the commands read of it."""

    def __init__(self, path: Path, port: int | None = None) -> None:
        self.state, self.play_id, self.commit, self.port, self.path, self.probe = "playing", "play-1", "abc1234def5678", port, path, True
        self.lines = ["vite ready", "GET /api/orders 500", "Error: boom at save (src/a.js:3:5)"]
        self.asked: list = []

    def lines_before(self, t=None, n=40) -> list[str]:
        self.asked.append((t, n))
        return self.lines[-n:]

    def stop(self, *_a, **_k) -> bool:
        return False

    def tick(self, _now) -> None:
        pass


@pytest.fixture
def host(repo, tmp_path):  # noqa: F811
    on_dev(repo, REACT)
    h = Orkboard(repo)
    h.ideas._play = Playing(h.ideas.state_dir / "play")
    yield h
    h.close()


def party(host, title, leader, team, craft):
    root, state = host.ideas.root(), host.ideas.state_dir
    library.install(state, [s for s in (*team, leader) if library.get(s) is not None])
    slug, _new = ideas.save_goal(root, None, title, "About " + title, None, "normal", craft=craft)
    goal_team.set_team(root, slug, list(team), leader=leader)
    return slug


@pytest.fixture
def parties(host):
    library.install(host.ideas.state_dir, AGENTS)
    return {"tech": party(host, "Tech", "architect", ["grunt", "tester"], "engineering"),
            "design": party(host, "Design", "product-designer", ["artist", "ui-kit"], "design"),
            "product": party(host, "Product", "product-manager", ["copywriter"], "product")}


@pytest.fixture
def drawn(monkeypatch):
    """The Chromium stood in for: it writes a PNG and notes what it was asked to draw."""
    calls: list[dict] = []

    def draw(url, dest, size=idea_shot.SIZE, seconds=25.0) -> bool:
        calls.append({"url": url, "size": size, "html": Path(url[7:]).read_text() if url.startswith("file://") else ""})
        Path(dest).write_bytes(PNG + str(len(calls)).encode())            # each picture its own, as two pages are
        return True

    monkeypatch.setattr(ideas_play_mark.idea_shot, "draw", draw)
    return calls


def mark(host, **more) -> dict:
    return host.command("ideas.play_mark", {"text": "Saving does nothing", "kind": "bug", "box": BOX, "path": "/orders", **more})


def err(at=1000, message="TypeError: x is undefined", page="/orders", **more) -> dict:
    return {"event": "error", "source": "error", "message": message, "stack": "at save (src/Orders.tsx:12:5)", "page": page, "at": at, **more}


def req(at=1000, path="/api/orders", status=500, ms=40, page="/orders", method="POST") -> dict:
    return {"event": "request", "method": method, "path": path, "status": status, "ms": ms, "page": page, "at": at}


def press(selector="button.save", at=1000, changed=False, page="/orders") -> dict:
    return {"event": "press", "selector": selector, "rect": {"x": 1, "y": 2, "w": 30, "h": 10}, "role": "button", "pressable": True, "dom": changed, "moved": False, "request": False,
            "changed": changed, "page": page, "at": at}


def send(host, *events, play="play-1") -> dict:
    return host.command("ideas.play_events", {"play": play, "events": list(events)})


def state_of(host, slug):
    return ideas.state(host.ideas.state_dir, slug)


def play_of(host, slug):
    return idea_play.read(host.ideas.state_dir, slug)


# -- the events and the hints ------------------------------------------------------------------------------------------------------------

def test_the_probes_events_become_hints_in_the_shape_the_signals_read(host):
    got = send(host, err(), req(), press(), press("button.save", 1300), {"event": "wheel", "at": 1}, "nonsense", {"event": "error"})
    assert got == {"ok": True, "kept": 3 + 1}                                           # an event of another kind, none, or with no time is not kept
    hints = host.command("ideas.play_hints", {"path": "/orders"})["hints"]
    kinds = {h["kind"]: h for h in hints}
    assert set(kinds) == {"error", "failed", "dead_press"}
    assert kinds["error"]["words"] == "An error here: TypeError: x is undefined"
    assert kinds["failed"]["words"] == "A request failed: POST /api/orders 500"
    assert kinds["dead_press"]["on"]["selector"] == "button.save" and kinds["dead_press"]["on"]["rect"] == {"x": 1.0, "y": 2.0, "w": 30.0, "h": 10.0}
    assert host.command("ideas.play_hints", {"path": "/cart"})["hints"][0]["kind"] == "failed"      # the page's own errors and presses; the play's requests (they carry no page)
    assert [h["kind"] for h in host.command("ideas.play_hints", {"path": "/cart"})["hints"]] == ["failed"]


# -- the mark: its kind, its party, its goal -----------------------------------------------------------------------------------------------

def test_each_kind_makes_a_goal_of_its_type_looks_wrong_has_none(host, parties, drawn):
    got = mark(host, party=parties["tech"])
    assert state_of(host, got["slug"])["type"] == "bug"
    got = mark(host, party=parties["tech"], kind="missing", text="There is no export")
    assert state_of(host, got["slug"])["type"] == "shaped-feature"   # an architect's party offers its feature as the shaped one, which stands in for it
    got = mark(host, party=parties["product"], kind="confusing", text="Nobody finds the cart")
    assert state_of(host, got["slug"])["type"] == "pain"
    got = mark(host, party=parties["design"], kind="looks", text="The button is too small")
    assert state_of(host, got["slug"])["type"] == ""
    assert [m["kind"] for m in play_of(host, got["slug"])] == ["looks"]
    with pytest.raises(CommandError, match="bug, looks wrong, missing or confusing"):
        mark(host, kind="praise")


def test_the_answer_says_the_goal_its_party_and_what_was_kept(host, parties, drawn):
    send(host, err(), req())
    got = mark(host, party=parties["tech"], under=[{"selector": "button.save", "role": "button", "text": "Save", "rect": {"x": 1, "y": 2, "w": 3, "h": 4}}], state={"level": 3}, picture=SNAP_PICTURE)
    assert got["title"] == "Saving does nothing" and got["party"] == parties["tech"] and got["party_title"] == "Tech" and got["joined"] is False and got["type"] == "bug"
    assert got["kept"] == {"picture": True, "errors": 1, "requests": 1, "lines": 3, "state": True, "under": 1, "marks": got["kept"]["marks"]}
    assert got["kept"]["marks"] >= 1 and got["element"]
    page = ideas.idea_page(host.ideas.root(), got["slug"])
    assert page is not None and "Saving does nothing" in page.section("Gist") + page.title


# -- the chips -------------------------------------------------------------------------------------------------------------------------------

def test_the_chips_left_on_keep_what_they_name_and_a_chip_taken_off_keeps_nothing_of_it(host, parties, drawn):
    send(host, err(), req())
    full = play_of(host, mark(host, party=parties["tech"], under=[{"selector": "button.save", "file": "src/pages/Orders.tsx"}], state={"level": 3}, picture=SNAP_PICTURE)["slug"])[0]
    assert full["errors"] and full["requests"] and full["lines"] and full["under"] and full["state"] == {"level": 3} and full["picture"]
    for chip, key in (("errors", "errors"), ("requests", "requests"), ("lines", "lines"), ("state", "state"), ("part", "under"), ("screen", "picture")):
        keep = [c for c in ideas_play_mark.WITH if c != chip]
        slug = mark(host, party=parties["tech"], under=[{"selector": "button.save", "file": "src/pages/Orders.tsx"}], state={"level": 3}, picture=SNAP_PICTURE, **{"with": keep})["slug"]
        one = play_of(host, slug)[0]
        assert not one[key], chip
        assert all(one[k] for k in ("errors", "requests", "lines", "under", "picture") if k != key), chip
        if chip == "screen":
            assert idea_lens.read(host.ideas.state_dir, slug) == [] and one["box"] == BOX            # no picture: the box stays in the play
        if chip == "part":
            assert not any(m["map"] == "system" for m in state_of(host, slug).get("marks") or [])
    bare = mark(host, party=parties["tech"], picture=SNAP_PICTURE, **{"with": []})
    one = play_of(host, bare["slug"])[0]
    assert one["box"] == BOX and one["path"] == "/orders" and one["commit"] == "abc1234def5678" and not (one["errors"] or one["requests"] or one["lines"] or one["under"] or one["state"] or one["picture"])
    with pytest.raises(CommandError, match="`with` is some of"):
        mark(host, **{"with": ["screen", "money"]})


def test_the_servers_lines_are_the_last_forty_before_the_mark_with_secrets_out(host, parties, drawn):
    host.ideas._play.lines = [f"line {n}" for n in range(60)]
    one = play_of(host, mark(host, party=parties["tech"])["slug"])[0]
    assert one["lines"] == [f"line {n}" for n in range(20, 60)]
    t, n = host.ideas._play.asked[-1]
    assert n == 40 and abs(t - time.time()) < 30                                      # wall-clock seconds
    host.ideas._play.lines = ["ready", "using .env.local", "key sk-abcdefghij1234", "done"]            # Play keeps a line that names a secret out; the goal's play does again
    assert play_of(host, mark(host, party=parties["tech"])["slug"])[0]["lines"] == ["ready", "done"]
    host.ideas._play.lines = ["ready", "using .env.local", "key sk-abcdefghij1234", "done"]


# -- a bug with its failure ----------------------------------------------------------------------------------------------------------------------

def test_a_bug_whose_mark_holds_an_error_or_a_failed_request_reproduces_and_one_without_does_not(host, parties, drawn):
    plain = mark(host, party=parties["tech"], text="The save button does nothing")
    how = state_of(host, plain["slug"])["route_how"]
    assert how["kind"] == "bug" and how["short"] is True and how["reproduces"] is False
    send(host, err())
    failing = mark(host, party=parties["tech"], text="The save button does nothing")
    how = state_of(host, failing["slug"])["route_how"]
    assert how["kind"] == "bug" and how["failure"] is True and how["short"] is True and how["reproduces"] is True
    (row,) = goal_route.rows(host.ideas.root(), host.ideas.state_dir, next(i for i in ideas.ideas(host.ideas.root()) if i["slug"] == failing["slug"]),
                             state_of(host, failing["slug"]), {"order": {}, "low": False})
    assert row["reproduces"] is True and row["short"] is True and row["type"] == "bug"
    off = mark(host, party=parties["tech"], text="The save button does nothing", **{"with": ["screen", "part", "lines"]})       # the chips taken off: the failure is not in the report
    assert state_of(host, off["slug"])["route_how"]["reproduces"] is False
    looks = mark(host, party=parties["design"], kind="looks", text="The save button does nothing")
    assert state_of(host, looks["slug"])["route_how"]["reproduces"] is False          # only a Bug carries a failure


# -- the picture ------------------------------------------------------------------------------------------------------------------------------

SNAP = "<!DOCTYPE html><html><head><base href='http://127.0.0.1:1/'><style>body{margin:0;background:#c00}</style></head><body><h1>Orders</h1></body></html>"
SNAP_PICTURE = {"html": SNAP, "w": 900, "h": 600, "at": 1}


def test_the_picture_is_the_snapshot_drawn_at_the_frames_size_with_no_script_running_and_kept_as_the_screens_are(host, parties, drawn):
    got = mark(host, party=parties["design"], kind="looks", picture={"html": SNAP, "w": 900, "h": 600, "at": 1})
    (call,) = drawn
    assert call["size"] == (900, 600) and call["url"].startswith("file://")
    assert call["html"].startswith("<!DOCTYPE html><meta http-equiv=\"Content-Security-Policy\" content=\"script-src 'none'\">") and "<h1>Orders</h1>" in call["html"]
    (item,) = idea_lens.read(host.ideas.state_dir, got["slug"])
    assert item["kind"] == "screen" and item["name"] == "Orders" and item["marks"] == [{**BOX, "note": "Saving does nothing"}]
    assert any(s["id"] == item["screen"] for s in idea_lens.screens(host.ideas.state_dir))                      # kept for the project
    assert (host.ideas.state_dir.parent / item["path"]).read_bytes().startswith(PNG)
    assert play_of(host, got["slug"])[0]["picture"] == item["screen"]
    assert "areas marked" in idea_lens.attached(host.ideas.state_dir, got["slug"]) and "from 20 % to 45 % across" in idea_lens.attached(host.ideas.state_dir, got["slug"])
    assert host.command("ideas.lens_screen", {"id": item["screen"]})["type"] == "image/png"


def test_a_snapshot_that_cannot_be_drawn_falls_back_to_the_page_and_none_at_all_keeps_the_box(host, parties, monkeypatch):
    calls = []
    monkeypatch.setattr(ideas_play_mark.idea_shot, "draw", lambda url, dest, size=idea_shot.SIZE, seconds=25.0: calls.append(url) or False)
    host.ideas._play.port = 41234
    got = mark(host, party=parties["design"], kind="looks", picture={"html": SNAP, "w": 900, "h": 600})
    assert len(calls) == 2 and calls[0].startswith("file://") and calls[1].endswith(":41234/orders")
    one = play_of(host, got["slug"])[0]
    assert idea_lens.read(host.ideas.state_dir, got["slug"]) == [] and one["picture"] == "" and one["box"] == BOX     # the goal is made all the same


@needs_browser
def test_a_snapshot_is_drawn_by_the_real_browser(host, parties):
    got = mark(host, party=parties["design"], kind="looks", picture={"html": SNAP.replace("<h1>", "<script>document.body.style.background='#0c0'</script><h1>"), "w": 600, "h": 400})
    (item,) = idea_lens.read(host.ideas.state_dir, got["slug"])
    raw = (host.ideas.state_dir.parent / item["path"]).read_bytes()
    assert raw.startswith(b"\x89PNG") and len(raw) > 100


@needs_browser
def test_the_page_is_drawn_anew_by_the_real_browser_from_a_page_that_plays(host, parties, tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("<!doctype html><title>x</title><body style='background:#00c'><h1>Hi</h1>")

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(site), **k)

        def log_message(self, *_a) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        host.ideas._play.port = server.server_address[1]
        got = mark(host, party=parties["design"], kind="looks", path="/")
    finally:
        server.shutdown()
        server.server_close()
    (item,) = idea_lens.read(host.ideas.state_dir, got["slug"])
    assert (host.ideas.state_dir.parent / item["path"]).read_bytes().startswith(b"\x89PNG")


# -- no probe, no play --------------------------------------------------------------------------------------------------------------------------

# -- add to a goal --------------------------------------------------------------------------------------------------------------------------------

def test_a_mark_added_to_a_goal_joins_its_lens_picture_of_the_same_page_and_its_play(host, parties, drawn):
    first = mark(host, party=parties["design"], kind="looks", text="The headline is crowded", picture={"html": SNAP, "w": 900, "h": 600})
    send(host, err())
    second = mark(host, kind="looks", text="The button is small", box={"x": 0.6, "y": 0.5, "w": 0.1, "h": 0.1}, add_to=first["slug"], picture={"html": SNAP, "w": 900, "h": 600})
    assert second["slug"] == first["slug"] and second["joined"] is True and len(drawn) == 1             # no second picture of the same page
    (item,) = idea_lens.read(host.ideas.state_dir, first["slug"])
    assert [m["note"] for m in item["marks"]] == ["The headline is crowded", "The button is small"]
    marks = play_of(host, first["slug"])
    assert [m["text"] for m in marks] == ["The headline is crowded", "The button is small"] and marks[1]["picture"] == item["screen"] and marks[1]["errors"] and not marks[0]["errors"]
    assert "The button is small" in [t["text"] for t in ideas.talk(host.ideas.state_dir, first["slug"])]
    assert idea_play.prompt_lines(host.ideas.state_dir, first["slug"]).count("- Mark ") == 2
    assert len([i for i in ideas.ideas(host.ideas.root()) if i["slug"] == first["slug"]]) == 1            # a goal, not a new one


def test_a_play_that_stopped_keeps_its_hints_and_a_bad_mark_or_a_phone_or_a_started_goal_is_refused(host, parties, drawn):
    send(host, err(), req())
    host.ideas._play.state = "stopped"                                               # the play ends: its hints stay for the morning's card
    assert {h["kind"] for h in host.ideas.last_play_hints()} == {"error", "failed"}
    assert send(host, err())["kept"] == 0 and host.command("ideas.play_hints", {"path": "/orders"})["hints"] == []
    host.ideas._play.state = "playing"
    base = host.ideas._play.path.as_posix()
    placed = host.command("ideas.play_place", {"path": "/orders", "files": [f"file://{base}/src/Orders.tsx", "src/a.js", 7]})
    assert set(placed) == {"screen", "parts"}
    for call, args in (("play_events", {"events": [], "device": "phone"}), ("play_events", {"events": "x"}), ("play_mark", {"text": "t", "kind": "bug", "box": None})):
        with pytest.raises(CommandError):
            host.command(f"ideas.{call}", args)
    got = mark(host, text="Broken save")                                             # a bug with no party goes to Tech's
    assert got["type"] == "bug" and got["party"]
    with pytest.raises(CommandError, match="gone"):
        mark(host, add_to="no-such-goal")
    ideas.save_state(host.ideas.state_dir, got["slug"], state="working")
    with pytest.raises(CommandError, match="started"):
        mark(host, add_to=got["slug"])


# -- the offer ---------------------------------------------------------------------------------------------------------------------------------

def test_the_offer_is_the_goal_not_started_with_a_mark_of_the_kind_on_the_screen(host, parties, drawn):
    assert host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "bug"}) == {}
    first = mark(host, party=parties["tech"], text="Saving does nothing")
    assert host.command("ideas.play_mark_offer", {"path": "/orders/7?x=1", "kind": "bug"}) == {}                  # another screen (the detail)
    assert host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "looks"}) == {}                       # another kind
    got = host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "bug"})
    assert got == {"goal": {"slug": first["slug"], "title": "Saving does nothing"}}
    newer = mark(host, party=parties["tech"], text="Saving still does nothing")
    assert host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "bug"})["goal"]["slug"] == newer["slug"]       # the latest
    ideas.save_state(host.ideas.state_dir, newer["slug"], state="working")
    assert host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "bug"})["goal"]["slug"] == first["slug"]       # a goal started is not offered
    ideas.save_state(host.ideas.state_dir, first["slug"], state="done")
    assert host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "bug"}) == {}
    with pytest.raises(CommandError, match="bug, looks wrong"):
        host.command("ideas.play_mark_offer", {"path": "/orders", "kind": "nope"})


# -- the mark as an event (spec 121 G, hypothesis H2) ---------------------------------------------------------------------------------------------

def test_a_mark_is_one_event_without_a_word_of_it_and_the_first_after_the_morning_card_says_the_minutes(host, parties, drawn):
    import datetime as dt
    from orkboard.realm import event_log
    marks = lambda: [e for e in event_log.read(Path(host.ideas.host.repo_root)) if e["event"] == event_log.PLAY_MARK]       # noqa: E731
    first = mark(host, party=parties["tech"], text="A secret word of mine")
    assert [(e["idea"], e["kind"], e["joined"], e["minutes_since_open"]) for e in marks()] == [(first["slug"], "bug", False, None)], "no card was lifted: no minutes"
    host.ideas.__dict__["_card_opened_at"] = dt.datetime.now().astimezone() - dt.timedelta(seconds=90)               # the morning's card was lifted a minute and a half ago
    second = mark(host, party=parties["tech"], text="Another one")
    third = mark(host, party=parties["tech"], text="And a third")
    got = marks()
    assert [e["idea"] for e in got] == [first["slug"], second["slug"], third["slug"]]
    assert 1.4 <= got[1]["minutes_since_open"] <= 1.7 and got[2]["minutes_since_open"] is None, "only the first mark after an opening is timed"
    assert "A secret word of mine" not in str(got) and event_log.PLAY_MARK in event_log.EVENTS
