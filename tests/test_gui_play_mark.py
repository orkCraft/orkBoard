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
from orkboard.realm import goal_route, goal_team, idea_lens, idea_play, ideas, library, play_place
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


def test_three_quick_presses_on_one_element_are_pressed_again_and_again_and_a_slow_request_follows_the_checks_file(host):
    send(host, press("a.x", 1000, True), press("a.x", 1200, True), press("a.x", 1400, True), req(2000, "/api/slow", 200, 1500, method="GET"))
    assert {h["kind"] for h in host.command("ideas.play_hints", {})["hints"]} == {"again", "slow"}
    (host.ideas.state_dir / "checks.toml").write_text("preview_slow_ms = 2000\n")
    assert {h["kind"] for h in host.command("ideas.play_hints", {})["hints"]} == {"again"}


def test_the_ring_is_this_plays_only_and_goes_when_play_stops_or_a_new_play_comes(host):
    assert send(host, err())["kept"] == 1
    assert send(host, err(), play="another-play")["kept"] == 0                           # another play's events are not this one's
    play = host.ideas._play
    play.play_id = "play-2"                                                              # a new play: its ring is new
    assert host.command("ideas.play_hints", {})["hints"] == []
    assert send(host, req(), play="play-1")["kept"] == 0 and send(host, req(), play="play-2")["kept"] == 1
    play.state = ""                                                                      # Play stopped
    assert send(host, err(), play="play-2")["kept"] == 0 and host.command("ideas.play_hints", {})["hints"] == []
    assert host.ideas.__dict__["_play_rings"] == {}
    play.state = "playing"
    assert host.command("ideas.play_hints", {})["hints"] == []                           # not the old ring back


def test_a_batch_is_bounded_and_what_an_event_says_is_cut(host):
    got = send(host, *[err(at=1000 + n, message=f"m{n}" + "x" * 900) for n in range(300)])
    assert got["kept"] == ideas_play_mark.MAX_BATCH
    ring = host.ideas._ring()
    assert all(len(e["message"]) <= 300 for e in ring.events())
    with pytest.raises(CommandError, match="Events are a list"):
        host.command("ideas.play_events", {"play": "play-1", "events": "x"})


def test_the_play_commands_are_the_computers_the_phone_has_none(host):
    for name, args in (("ideas.play_events", {"events": []}), ("ideas.play_place", {"path": "/"}), ("ideas.play_hints", {}), ("ideas.play_mark", {"text": "x", "kind": "bug", "box": BOX}),
                       ("ideas.play_mark_offer", {"kind": "bug", "path": "/"})):
        with pytest.raises(CommandError, match="Play on the computer"):
            host.command(name, {**args, "device": "phone"})


def test_the_place_is_the_screen_and_the_parts_and_a_file_in_plays_worktree_is_the_repositorys(host, monkeypatch):
    got = host.command("ideas.play_place", {"path": "/orders"})
    assert got["screen"] == {"id": "orders", "name": "Orders", "step": 2} and got["parts"]["screens"] == [{"id": "orders", "name": "Orders"}]
    seen = []
    real = play_place.parts
    monkeypatch.setattr(play_place, "parts", lambda *a, **k: seen.append(a[3]) or real(*a, **k))
    work = host.ideas._play.path
    host.command("ideas.play_place", {"path": "/orders", "files": [f"{work}/src/pages/Orders.tsx:7:3", f"file://{work}/src/Layout.tsx", "src/pages/Home.tsx", 7]})
    assert seen == [["src/pages/Orders.tsx:7:3", "src/Layout.tsx", "src/pages/Home.tsx"]]


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


def test_a_party_that_takes_no_goal_of_the_kinds_type_gets_the_goal_with_none_and_the_play_keeps_the_kind(host, parties, drawn):
    got = mark(host, party=parties["tech"], kind="confusing", text="Nobody finds the cart")
    assert state_of(host, got["slug"])["type"] == "" and play_of(host, got["slug"])[0]["kind"] == "confusing"
    assert ideas.idea_page(host.ideas.root(), got["slug"]).get("track") == parties["tech"]


def test_the_answer_says_the_goal_its_party_and_what_was_kept(host, parties, drawn):
    send(host, err(), req())
    got = mark(host, party=parties["tech"], under=[{"selector": "button.save", "role": "button", "text": "Save", "rect": {"x": 1, "y": 2, "w": 3, "h": 4}}], state={"level": 3}, picture=SNAP_PICTURE)
    assert got["title"] == "Saving does nothing" and got["party"] == parties["tech"] and got["party_title"] == "Tech" and got["joined"] is False and got["type"] == "bug"
    assert got["kept"] == {"picture": True, "errors": 1, "requests": 1, "lines": 3, "state": True, "under": 1, "marks": got["kept"]["marks"]}
    assert got["kept"]["marks"] >= 1 and got["element"]
    page = ideas.idea_page(host.ideas.root(), got["slug"])
    assert page is not None and "Saving does nothing" in page.section("Gist") + page.title


def test_on_the_projects_tab_a_bug_goes_to_tech_and_any_other_kind_is_routed_by_code(host, parties, drawn):
    got = mark(host, text="The save button does nothing")
    st = state_of(host, got["slug"])
    assert st["state"] == "routed" and [s["party"] for s in st["route"]] == [parties["tech"]] and ideas.idea_page(host.ideas.root(), got["slug"]).get("track") == parties["tech"]
    assert st["route_how"]["kind"] == "bug" and st["route_how"]["short"] is True
    other = mark(host, kind="looks", text="The cart looks cramped")
    assert state_of(host, other["slug"])["state"] == "routed" and state_of(host, other["slug"])["route_how"]["kind"] != "bug"      # the Orkmaster routes it by its words, as ever


def test_the_open_tabs_party_is_the_goals_and_ideation_is_not_one_a_mark_goes_to(host, parties, drawn):
    got = mark(host, party=parties["design"], kind="looks", text="The headline is crowded")
    assert [s["party"] for s in state_of(host, got["slug"])["route"]] == [parties["design"]]
    with pytest.raises(CommandError, match="That party is gone"):
        mark(host, party="nowhere")
    with pytest.raises(CommandError, match="text is missing"):
        mark(host, text="  ")
    for bad in (None, {"x": 0.1}, {"x": 0.1, "y": 0.1, "w": 0, "h": 0.2}, {"x": 2, "y": 0.1, "w": 0.2, "h": 0.2}):
        with pytest.raises(CommandError, match="Draw a box or press a part"):
            mark(host, box=bad)


def test_the_maps_parts_the_place_touches_are_the_goals_marks(host, parties, drawn):
    got = mark(host, party=parties["tech"], under=[{"selector": "li", "file": "src/pages/Orders.tsx"}])
    marks = state_of(host, got["slug"])["marks"]
    assert {"map": "screens", "id": "orders", "name": "Orders"} in marks
    assert any(m["map"] == "system" for m in marks)


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


def test_errors_are_the_pages_own_said_once_and_requests_are_the_failed_or_slow_ones(host, parties, drawn):
    send(host, err(1000), err(1100), err(1200, "Another"), err(1300, "On another page", page="/cart"), req(1400, "/api/ok", 200, 20), req(1500, "/api/slow", 200, 4000, method="GET"),
         req(1600, "/api/me", 401), req(1700, "/api/orders", 500))
    one = play_of(host, mark(host, party=parties["tech"])["slug"])[0]
    assert [(e["message"], e["count"]) for e in one["errors"]] == [("Another", 1), ("TypeError: x is undefined", 2)] or [(e["message"], e["count"]) for e in one["errors"]] == [("TypeError: x is undefined", 2), ("Another", 1)]
    assert [(r["method"], r["path"], r["status"]) for r in one["requests"]] == [("GET", "/api/slow", 200), ("POST", "/api/orders", 500)]


def test_the_servers_lines_are_the_last_forty_before_the_mark_with_secrets_out(host, parties, drawn):
    host.ideas._play.lines = [f"line {n}" for n in range(60)]
    one = play_of(host, mark(host, party=parties["tech"])["slug"])[0]
    assert one["lines"] == [f"line {n}" for n in range(20, 60)]
    t, n = host.ideas._play.asked[-1]
    assert n == 40 and abs(t - time.time()) < 30                                      # wall-clock seconds
    host.ideas._play.lines = ["ready", "using .env.local", "key sk-abcdefghij1234", "done"]            # Play keeps a line that names a secret out; the goal's play does again
    assert play_of(host, mark(host, party=parties["tech"])["slug"])[0]["lines"] == ["ready", "done"]
    host.ideas._play.lines = ["ready", "using .env.local", "key sk-abcdefghij1234", "done"]


def test_a_secret_in_what_the_page_sent_is_not_kept(host, parties, drawn):
    send(host, err(message="fetch failed: sk-abcdefghij1234"))
    slug = mark(host, party=parties["tech"], state={"password": "hunter2", "level": 1}, under=[{"selector": "div", "file": ".env", "text": "ghp_abcdefghijkl"}])["slug"]
    kept = (host.ideas.state_dir / "ideas" / slug / "play.json").read_text()
    for leak in ("sk-abc", "ghp_abc", "hunter2", '".env"'):
        assert leak not in kept


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


def test_a_request_that_failed_is_a_failure_too(host, parties, drawn):
    send(host, req())
    got = mark(host, text="Orders never load")
    assert state_of(host, got["slug"])["route_how"]["reproduces"] is True


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


def test_with_no_snapshot_the_page_is_drawn_anew_from_plays_port_at_the_frames_size(host, parties, drawn):
    host.ideas._play.port = 41234
    mark(host, party=parties["design"], kind="looks", picture={"none": True}, viewport={"w": 800, "h": 500}, path="/orders?tab=lines")
    (call,) = drawn
    assert call["url"].endswith(":41234/orders?tab=lines") and call["size"] == (800, 500)
    mark(host, party=parties["design"], kind="looks", path="/odd path<>")
    assert drawn[-1]["url"].endswith(":41234/") and drawn[-1]["size"] == idea_shot.SIZE                         # a path that is no address is the page's root


def test_a_snapshot_that_cannot_be_drawn_falls_back_to_the_page_and_none_at_all_keeps_the_box(host, parties, monkeypatch):
    calls = []
    monkeypatch.setattr(ideas_play_mark.idea_shot, "draw", lambda url, dest, size=idea_shot.SIZE, seconds=25.0: calls.append(url) or False)
    host.ideas._play.port = 41234
    got = mark(host, party=parties["design"], kind="looks", picture={"html": SNAP, "w": 900, "h": 600})
    assert len(calls) == 2 and calls[0].startswith("file://") and calls[1].endswith(":41234/orders")
    one = play_of(host, got["slug"])[0]
    assert idea_lens.read(host.ideas.state_dir, got["slug"]) == [] and one["picture"] == "" and one["box"] == BOX     # the goal is made all the same


def test_a_picture_larger_than_a_goal_may_carry_is_left_out(host, parties, monkeypatch):
    big = PNG + b"\0" * (4 * 2**20)
    monkeypatch.setattr(ideas_play_mark.idea_shot, "draw", lambda url, dest, size=idea_shot.SIZE, seconds=25.0: Path(dest).write_bytes(big) or True)
    got = mark(host, party=parties["design"], kind="looks", picture={"html": SNAP, "w": 900, "h": 600})
    assert idea_lens.read(host.ideas.state_dir, got["slug"]) == [] and play_of(host, got["slug"])[0]["picture"] == ""


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

def test_with_no_probe_nothing_is_known_but_the_box_and_the_path(host, parties, drawn):
    host.ideas._play = None                                                       # nothing plays: no commit, no ring, no lines, no snapshot, no page to draw
    got = mark(host, party=parties["design"], kind="looks", under=[], state=None, picture={"none": True})
    one = play_of(host, got["slug"])[0]
    assert one["box"] == BOX and one["path"] == "/orders" and one["screen"] == {"id": "orders", "name": "Orders"}
    assert not (one["commit"] or one["errors"] or one["requests"] or one["lines"] or one["under"] or one["state"] or one["picture"])
    assert drawn == [] and idea_lens.read(host.ideas.state_dir, got["slug"]) == []
    assert host.ideas._play is None                                               # the mark made no Play


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


def test_a_mark_on_another_page_added_to_a_goal_brings_its_own_picture(host, parties, drawn):
    first = mark(host, party=parties["design"], kind="looks", text="Crowded", picture={"html": SNAP, "w": 900, "h": 600})
    again = mark(host, kind="looks", text="Also here", path="/settings", add_to=first["slug"], picture={"html": SNAP, "w": 900, "h": 600})
    assert again["joined"] and len(drawn) == 2
    lens = idea_lens.read(host.ideas.state_dir, first["slug"])
    assert len(lens) == 2 and lens[0]["screen"] != lens[1]["screen"] and lens[1]["marks"][0]["note"] == "Also here"


def test_add_to_a_goal_that_is_gone_or_has_started_is_refused_in_words(host, parties, drawn):
    with pytest.raises(CommandError, match="That goal is gone"):
        mark(host, add_to="nowhere")
    first = mark(host, party=parties["design"], kind="looks", text="Crowded")
    ideas.save_state(host.ideas.state_dir, first["slug"], state="working")
    with pytest.raises(CommandError, match="That goal has started"):
        mark(host, add_to=first["slug"])


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


def test_a_place_no_screen_fits_is_offered_by_its_page(host, parties, drawn):
    first = mark(host, party=parties["design"], kind="looks", path="/nowhere/at/all", text="Odd")
    assert host.command("ideas.play_mark_offer", {"path": "/nowhere/at/all?x=1", "kind": "looks"})["goal"]["slug"] == first["slug"]
    assert host.command("ideas.play_mark_offer", {"path": "/elsewhere", "kind": "looks"}) == {}


def test_the_play_is_in_the_goals_calls_after_its_lens(host, parties, drawn):
    send(host, err())
    got = mark(host, party=parties["tech"], picture={"html": SNAP, "w": 900, "h": 600})
    text = idea_lens.attached(host.ideas.state_dir, got["slug"])
    assert text.index("The screen \"Orders\"") < text.index("The person marked places on the running product") and "TypeError: x is undefined" in text
