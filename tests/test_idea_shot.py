"""Spec 85 §3 (docs/specs/85-the-elf-asks-and-shows.md): the picture of what a task changed. The project's preview is a tiny static page (and a
command that serves one), drawn in the preinstalled Chromium; no model. A task that changed nothing people see gets none; one whose project has
no preview that opens says so. The picture stays with the goal's candidates and is served by the pick route. Spec 85 §2 rides here too: the
look picked first is written with the extension of the file picked."""
from __future__ import annotations

import json
import shutil
import sys
import time
import socket
from pathlib import Path

import pytest

from orkboard.core import idea_shot
from orkboard.gui import media
from orkboard.realm import event_log, idea_pick, idea_shots
from tests import pick_files as pf
from tests.test_idea_pick import PICK_STUB, calls, events_of, git, plan_of, rig, runner_of, tasks_of, wait_for  # noqa: F401  (rig is a fixture)

needs_browser = pytest.mark.skipif(idea_shot.browser() is None, reason="no Chromium here")
PAGE = "<!doctype html><title>Runs</title><body style='background:#123456'><h1>Runs</h1></body>"


# -- what people see -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("files, seen", [
    (["index.html"], True), (["src/App.css"], True), (["web/components/Table.js"], True), (["assets/logo.svg"], True),
    (["src/app.py"], False), (["README.md"], False), (["tests/test_ui.html"], False), (["docs/shot.png"], False),
    (["design/looks/demo.png"], False), (["node_modules/x/y.css"], False), (["src/app.py", "public/index.js"], True), ([], False)])
def test_what_a_diff_touches_is_seen_or_not(files, seen):
    assert idea_shot.sees(files) is seen


# -- how the preview opens -----------------------------------------------------------------------------------------------

def test_the_preview_is_the_checks_line_else_a_static_page_else_the_projects_script(tmp_path):
    work, state = tmp_path / "work", tmp_path / "state"
    work.mkdir()
    state.mkdir()
    assert idea_shot.preview_of(state, work) is None
    (work / "package.json").write_text(json.dumps({"scripts": {"test": "x", "start": "node s.js", "dev": "vite"}}))
    assert idea_shot.preview_of(state, work) == {"how": "command", "run": ["npm", "run", "dev"], "port": None}
    (work / "package.json").write_text(json.dumps({"scripts": {"build": "x", "preview": "vite preview"}}))
    assert idea_shot.preview_of(state, work)["run"] == ["npm", "run", "preview"]
    (work / "index.html").write_text(PAGE)
    assert idea_shot.preview_of(state, work) == {"how": "static"}                 # a static page before a script
    (state / "checks.toml").write_text('preview = "python3 -m http.server 8123"\npreview_port = 8123\n')
    assert idea_shot.preview_of(state, work) == {"how": "command", "run": ["python3", "-m", "http.server", "8123"], "port": 8123}


# -- the page, not the first port (spec 90 §1) ---------------------------------------------------------------------------

# A monorepo's `dev`: Express answers on `PORT` (404 at `/`), Vite prints its own port later and serves the page. `TWO_PORTS_PAGE=none`: no page anywhere.
TWO_PORTS = """import http.server, os, socket, sys, threading, time
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        page = self.server.page and self.path.split("?")[0] in ("/", "/index.html")
        body = b"<!doctype html><title>Vite</title><h1>the client</h1>" if page else b"Cannot GET " + self.path.encode()
        self.send_response(200 if page else 404)
        self.send_header("Content-Type", "text/html; charset=utf-8" if page else "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
def serve(port, page):
    s = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    s.page = page
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s
serve(int(os.environ["PORT"]), False)
print("server listening on http://localhost:" + os.environ["PORT"], flush=True)
time.sleep(float(os.environ.get("TWO_PORTS_WAIT", "0.6")))
with socket.socket() as probe:
    probe.bind(("127.0.0.1", 0))
    other = probe.getsockname()[1]
serve(other, os.environ.get("TWO_PORTS_PAGE") != "none")
if os.environ.get("TWO_PORTS_COLOUR") and (os.environ.get("TWO_PORTS_COLOUR") == "always" or not os.environ.get("NO_COLOR")):
    print("  \x1b[32m\u279c\x1b[39m  \x1b[1mLocal\x1b[22m:   \x1b[36mhttp://localhost:\x1b[1m%d\x1b[22m/\x1b[39m" % other, flush=True)   # Vite's, coloured
else:
    print("  Local:   http://localhost:%d/" % other, flush=True)
time.sleep(120)
"""


def two_ports(tmp_path, monkeypatch, page=True):
    """A preview command printing two ports (spec 90 §1): the work folder, the state folder and how the preview opens."""
    work, state = tmp_path / "work", tmp_path / "state"
    work.mkdir()
    state.mkdir()
    (work / "twoports.py").write_text(TWO_PORTS)
    (state / "checks.toml").write_text(f'preview = "{sys.executable} twoports.py"\n')
    monkeypatch.setenv("TWO_PORTS_PAGE", "yes" if page else "none")
    return work, state, idea_shot.preview_of(state, work)


CHATTY = """import os, sys, time
for i in range(45):
    print("\\x1b[32mlog %d\\x1b[0m" % i)
    if i % 10 == 0:
        print()                                              # a blank line is not kept
print("x" * 900, flush=True)                                 # a long line is cut
print("done", flush=True)
time.sleep(60)
"""


# -- the picture ---------------------------------------------------------------------------------------------------------

@needs_browser
def test_a_static_page_is_drawn_into_a_png_of_the_asked_size(tmp_path):
    work, state = tmp_path / "work", tmp_path / "state"
    work.mkdir()
    state.mkdir()
    (work / "index.html").write_text(PAGE)
    ok, why = idea_shot.make(state, work, tmp_path / "shot.png")
    assert (ok, why) == (True, "")
    assert (tmp_path / "shot.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    (state / "checks.toml").write_text('preview_size = "390x844"\n')
    ok, _why = idea_shot.make(state, work, tmp_path / "phone.png")
    from orkboard.realm import media_sniff
    got = media_sniff.measure(tmp_path / "phone.png", "image/png")
    assert ok and (got["w"], got["h"]) == (390, 844)


@needs_browser
def test_a_command_that_serves_a_page_is_opened_drawn_and_killed(tmp_path):
    work, state = tmp_path / "work", tmp_path / "state"
    work.mkdir()
    state.mkdir()
    (work / "page.html").write_text(PAGE)
    (work / "serve.py").write_text("import http.server, os, sys\nhttp.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, "
                                   "port=int(os.environ['PORT']), bind='127.0.0.1')\n")
    (state / "checks.toml").write_text(f'preview = "{sys.executable} serve.py"\npreview_path = "/page.html"\n')
    ok, why = idea_shot.make(state, work, tmp_path / "shot.png")
    assert (ok, why) == (True, "") and (tmp_path / "shot.png").stat().st_size > 0
    how = idea_shot.preview_of(state, work)
    with idea_shot.opened(how, work, 10) as port:
        assert port and idea_shot._listening(port)
    assert not idea_shot._listening(port)                                           # closed on leaving


def test_a_project_with_no_preview_or_one_that_never_opens_has_no_picture_and_waits_no_longer_than_it_may(tmp_path, monkeypatch):
    work, state = tmp_path / "work", tmp_path / "state"
    work.mkdir()
    state.mkdir()
    assert idea_shot.make(state, work, tmp_path / "shot.png") == (False, "no preview") or idea_shot.browser() is None
    (state / "checks.toml").write_text(f'preview = "{sys.executable} -c \\"import time; time.sleep(60)\\""\n')
    monkeypatch.setattr(idea_shot, "OPEN_S", 1.0)
    started = time.monotonic()
    got = idea_shot.make(state, work, tmp_path / "shot.png")
    assert got in ((False, "no preview"), (False, "no browser")) and time.monotonic() - started < 10
    assert not (tmp_path / "shot.png").exists()


def test_no_browser_is_said_and_never_raises(tmp_path, monkeypatch):
    work, state = tmp_path / "work", tmp_path / "state"
    work.mkdir()
    state.mkdir()
    (work / "index.html").write_text(PAGE)
    monkeypatch.setattr(idea_shot, "browser", lambda: None)
    assert idea_shot.make(state, work, tmp_path / "shot.png") == (False, "no browser")


# -- kept and served -----------------------------------------------------------------------------------------------------

def test_a_picture_is_kept_beside_the_candidates_served_by_the_pick_route_and_not_listed_as_a_pick(tmp_path):
    png = tmp_path / "in.png"
    png.write_bytes(pf.png(30, 20))
    state = tmp_path / "state"
    got = idea_shots.store(state, "demo", "k2", 1, png)
    assert (got["id"], got["file"], got["w"], got["h"]) == ("k2-shot-r1", "shot.png", 30, 20)
    folder = state / "ideas" / "demo" / "picks" / "k2-shot-r1"
    assert sorted(p.name for p in folder.iterdir()) == ["pick.json", "shot.png"]
    assert idea_pick.history(state, "demo", "k2") == [] and idea_pick.next_round(state, "demo", "k2") == 1      # not a pick of the task
    reply = media.serve("GET", media.url("demo", got["id"], got["file"]), "", [state])
    assert reply.status == 200 and reply.read()[:8] == b"\x89PNG\r\n\x1a\n" and dict(reply.headers)["Content-Type"] == "image/png"
    assert media.serve("GET", f"/media/demo/{got['id']}/shot.png", "", [state]).status == 404                    # unsigned
    assert idea_shots.store(state, "demo", "k2", 1, tmp_path / "gone.png") is None
    junk = tmp_path / "junk.png"
    junk.write_bytes(b"not a picture")
    assert idea_shots.store(state, "demo", "k2", 2, junk) is None and not (state / "ideas" / "demo" / "picks" / "k2-shot-r2").exists()
    assert idea_shots.map_of({"shot": got}) == {k: got[k] for k in ("id", "file", "w", "h")}
    assert idea_shots.map_of({"shot": {"none": True}}) == {"none": idea_shots.NONE} == {"none": "no picture: no preview"}
    assert idea_shots.map_of({}) is None and idea_shots.map_of({"shot": "x"}) is None


# -- in the runner -------------------------------------------------------------------------------------------------------

STUB = PICK_STUB.replace('elif mode[0] == "edit":', '''elif mode[0] == "page":
    commit("index.html", "<!doctype html><h1>Runs</h1>", f"{tid}: a page")
elif mode[0] == "edit":''')


def _runner(rig, monkeypatch, mode, files=None, **ideas):
    path = Path(shutil.which("claude"))
    path.write_text(STUB.replace("{python}", sys.executable))
    monkeypatch.setenv("STUB_MODE", f"k1={mode}")
    plan_of(rig, [{"id": "k1", "title": "The page", "kind": "code"}])
    return runner_of(rig, **ideas)


@needs_browser
def test_a_task_that_changed_a_page_keeps_its_picture_and_the_map_and_review_carry_it(rig, monkeypatch):
    runner = _runner(rig, monkeypatch, "page", review=True)
    runner.start("demo")
    task = wait_for(runner, rig, "k1", ("review", "merged"))
    assert task["shot"]["id"] == "k1-shot-r1" and task["shot"]["file"] == "shot.png" and task["shot"]["w"] and task["shot"]["h"]
    assert (rig.state / "ideas" / "demo" / "picks" / "k1-shot-r1" / "shot.png").read_bytes()[:4] == b"\x89PNG"
    (e,) = events_of(rig, event_log.SHOT_TAKEN)
    assert (e["idea"], e["task"], e["ok"], e["why"], e["round"]) == ("demo", "k1", True, "", 1) and e["seconds"] < 30
    assert idea_shots.map_of(task)["id"] == "k1-shot-r1"


def test_a_task_that_changed_nothing_people_see_has_no_picture_and_no_event(rig, monkeypatch):
    runner = _runner(rig, monkeypatch, "edit")
    runner.start("demo")
    task = wait_for(runner, rig, "k1", ("review", "merged"))
    assert task.get("shot") is None and events_of(rig, event_log.SHOT_TAKEN) == []


def test_a_task_that_changed_a_page_in_a_project_with_no_preview_says_so(rig, monkeypatch):
    runner = _runner(rig, monkeypatch, "page")
    monkeypatch.setattr(idea_shot, "preview_of", lambda *a: None)
    runner.start("demo")
    task = wait_for(runner, rig, "k1", ("review", "merged"))
    assert task["shot"] == {"none": True} and idea_shots.map_of(task) == {"none": "no picture: no preview"}
    (e,) = events_of(rig, event_log.SHOT_TAKEN)
    assert (e["ok"], e["why"]) == (False, "no preview")


def test_the_setting_shots_off_draws_nothing(rig, monkeypatch):
    runner = _runner(rig, monkeypatch, "page", shots=False)
    runner.start("demo")
    task = wait_for(runner, rig, "k1", ("review", "merged"))
    assert task.get("shot") is None and events_of(rig, event_log.SHOT_TAKEN) == []


def test_a_look_picked_is_written_at_the_goals_look_with_the_extension_of_the_file_picked(rig, monkeypatch):
    path = Path(shutil.which("claude"))
    path.write_text(STUB.replace("{python}", sys.executable))
    monkeypatch.setenv("STUB_MODE", "k1=pick:3")
    ask = {"n": 3, "kind": "image", "ask": "Which look should the screen have?", "target": "design/looks/demo", "look": True}
    plan_of(rig, [{"id": "k1", "title": "Pick a look", "kind": "design", "pick": ask},
                  {"id": "k2", "title": "Build it", "kind": "code", "after": ["k1"]}])
    runner = runner_of(rig)
    runner.start("demo")
    wait_for(runner, rig, "k1", ("picking",))
    pick = json.loads((rig.state / "ideas" / "demo" / "picks" / "k1-r1" / "pick.json").read_text())
    assert pick["look"] is True and pick["target"] == "design/looks/demo"
    runner.pick("demo", "k1", "B", "calmer", device="desktop", via="hand")
    task = wait_for(runner, rig, "k1", ("merged",))
    assert (rig.repo / "design" / "looks" / "demo.png").read_bytes() == pf.png(12, 2)
    assert git(rig.repo, "log", "-1", "--format=%s", task["commit"]) == "Pick a look: B · v2"
    assert task.get("shot") is None                                                  # a look picked is a file of the design, not the product
    wait_for(runner, rig, "k2", ("merged",))
    assert 'The person picked B · v2: "calmer"' in calls(rig)[1]["argv"][1]


def _v6_page_server():
    """A page served on ::1 only, as Vite on a Mac serves `localhost`; None where this machine has no IPv6 loopback."""
    import http.server
    import threading

    class V6(http.server.ThreadingHTTPServer):
        address_family = socket.AF_INET6

    class Page(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"<!doctype html><title>game</title>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_a):
            pass

    try:
        srv = V6(("::1", 0), Page)
    except OSError:
        return None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

