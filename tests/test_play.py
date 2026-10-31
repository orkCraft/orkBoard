"""Spec 88 §5 (docs/specs/88-assets-and-play.md): Play opens the project's own preview of dev's head in a worktree of its own, on the
machine's own address; one a project, answered the same while it runs; stopped by its command, by ten minutes with no face, and by
closing the project, its worktree removed; `play_started` and `play_stopped`; never for a phone. A stub preview, as tests/test_idea_shot.py's."""
from __future__ import annotations

import inspect
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from orkboard.core import idea_shot
from orkboard.gui import ideas_assets
from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas import IdeasError
from orkboard.realm import event_log

PAGE = "<!doctype html><title>Game</title><h1>dev's build</h1>"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str = "work") -> str:
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(fake_repo: Path) -> Path:
    (fake_repo / ".gitignore").write_text(".orkcraft/\n")
    git(fake_repo, "checkout", "-q", "-b", "dev")
    commit(fake_repo, {"index.html": PAGE})
    return fake_repo


@pytest.fixture
def host(repo: Path):
    h = Orkboard(repo)
    yield h
    play = h.ideas._play if h.ideas is not None else None
    if play is not None:
        play.stop("stopped", wait=True)
    h.close()


def settle(host, seconds: float = 25.0) -> dict:
    """`ideas.play {peek}` until it is no longer starting."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        got = host.command("ideas.play", {"peek": True})
        if got["state"] != "starting":
            return got
        time.sleep(0.1)
    raise AssertionError("Play never settled")


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read().decode()


def events(repo: Path, name: str) -> list[dict]:
    return [e for e in event_log.read(repo) if e["event"] == name]


def test_play_opens_devs_preview_in_its_own_worktree_and_answers_the_same_while_it_runs(host, repo):
    (repo / "index.html").write_text("the working tree's own")                                   # never what plays
    head = git(repo, "rev-parse", "dev")
    first = host.command("ideas.play", {})
    assert {k: first[k] for k in ("state", "commit", "short", "stage", "command", "ports")} == {"state": "starting", "commit": head, "short": head[:7], "stage": "worktree", "command": "", "ports": []}
    assert isinstance(first["since"], float) and first["since"] >= 0
    got = settle(host)
    assert got["state"] == "playing" and got["commit"] == head and got["dev"] == head and got["short"] == head[:7]
    assert got["url"].startswith("http://127.0.0.1:") and got["url"].endswith("/")
    assert "dev's build" in fetch(got["url"])
    tree = host.ideas.state_dir / "play"
    assert (tree / "index.html").read_text() == PAGE and git(tree, "rev-parse", "HEAD") == head
    assert host.command("ideas.play", {}) == got                                                   # one Play: the same answer
    started = events(repo, event_log.PLAY_STARTED)
    assert len(started) == 1 and started[0]["ok"] is True and started[0]["why"] == "" and isinstance(started[0]["seconds"], float)


def test_a_merge_into_dev_changes_nothing_until_play_is_pressed_fresh(host, repo):
    head = git(repo, "rev-parse", "dev")
    host.command("ideas.play", {})
    got = settle(host)
    new = commit(repo, {"index.html": "<h1>newer</h1>"})
    again = host.command("ideas.play", {})
    assert again["commit"] == head and again["dev"] == new and again["url"] == got["url"]       # it says which it plays
    host.command("ideas.play", {"fresh": True})
    fresh = settle(host)
    assert fresh["commit"] == new and "newer" in fetch(fresh["url"])
    assert [e["why"] for e in events(repo, event_log.PLAY_STOPPED)] == ["again"]


def test_the_build_state_carries_the_projects_logo_signed_as_an_asset_of_devs_head(host, repo):
    """Spec 107 §9.2: `logo` is the address of the project's logo in dev's head while it starts and plays, "" with none."""
    from orkboard.gui import media

    first = host.command("ideas.play", {})
    assert first["logo"] == ""
    assert settle(host)["logo"] == ""
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()
    head = commit(repo, {"brand/logo.svg": "<svg xmlns='http://www.w3.org/2000/svg' width='8' height='8'/>", "logo.txt": "not a picture"})
    starting = host.command("ideas.play", {})
    assert starting["state"] == "starting" and starting["logo"] == media.asset_url(head, "brand/logo.svg")
    playing = settle(host)
    assert playing["logo"] == starting["logo"]
    served = media.serve("GET", playing["logo"], "", media.state_dirs(host)).read()
    assert b"<svg" in served                                                                         # served as the assets' files are


def test_play_stop_kills_the_preview_and_removes_its_worktree(host, repo):
    host.command("ideas.play", {})
    got = settle(host)
    port = int(got["url"].rsplit(":", 1)[1].split("/")[0])
    assert host.command("ideas.play_stop", {}) == {"ok": True, "stopped": True}
    host.ideas.player.wait()
    assert not idea_shot._listening(port) and not (host.ideas.state_dir / "play").exists()
    assert ".orkcraft/play" not in git(repo, "worktree", "list")
    assert host.command("ideas.play", {"peek": True}) == {"state": "stopped"}
    assert host.command("ideas.play_stop", {}) == {"ok": True, "stopped": False}
    assert [e["why"] for e in events(repo, event_log.PLAY_STOPPED)] == ["stopped"]


def test_ten_minutes_with_no_face_asking_stops_it(host, repo):
    host.command("ideas.play", {})
    settle(host)
    play = host.ideas.player
    host.ideas.tick(time.monotonic())
    assert play.state == "playing"                                                                  # a face asked just now
    play.seen_at = time.monotonic() - ideas_assets.IDLE_S - 1
    host.ideas.tick(time.monotonic())
    play.wait()
    assert play.state == "" and not (host.ideas.state_dir / "play").exists()
    assert [e["why"] for e in events(repo, event_log.PLAY_STOPPED)] == ["idle"]


def test_closing_the_project_stops_it(host, repo):
    host.command("ideas.play", {})
    settle(host)
    play = host.ideas.player
    host.projects.close(str(repo), stop=True)
    play.wait()
    assert play.state == "" and not (repo / ".orkcraft" / "play").exists()
    assert [e["why"] for e in events(repo, event_log.PLAY_STOPPED)] == ["closed"]


def test_a_command_preview_runs_in_the_worktree_bound_to_the_machines_own_address(host, repo):
    commit(repo, {"serve.py": "import http.server, os\nhttp.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, "
                              "port=int(os.environ['PORT']), bind=os.environ['HOST'])\n", "page.html": "<h1>from the command</h1>"})
    state = host.ideas.state_dir
    state.mkdir(exist_ok=True)
    (state / "checks.toml").write_text(f'preview = "{sys.executable} serve.py"\npreview_path = "/page.html"\n')
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "playing" and got["url"].startswith("http://127.0.0.1:") and got["url"].endswith("/page.html")
    assert "from the command" in fetch(got["url"])
    started = events(repo, event_log.PLAY_STARTED)[-1]                        # spec 107 §2: what it ran and the page it opened
    assert started["command"] == f"{sys.executable} serve.py" and started["url"] == got["url"]


def test_no_preview_or_one_that_never_opens_says_why_and_leaves_no_worktree(host, repo, monkeypatch):
    git(repo, "rm", "-q", "index.html")
    git(repo, "commit", "-q", "-m", "no page")
    host.command("ideas.play", {})
    got = settle(host)
    assert got == {"state": "failed", "error": "no preview", "none": True}
    assert not (host.ideas.state_dir / "play").exists()
    e = events(repo, event_log.PLAY_STARTED)[-1]
    assert (e["ok"], e["why"]) == (False, "no preview")
    (host.ideas.state_dir / "checks.toml").write_text(f'preview = "{sys.executable} -c \\"import time; time.sleep(60)\\""\n')
    monkeypatch.setattr(ideas_assets, "PLAY_OPEN_S", 1.0)
    host.command("ideas.play", {})
    got = settle(host)
    assert got == {"state": "failed", "error": "did not open", "tail": []} and not (host.ideas.state_dir / "play").exists()


def test_no_dev_branch_is_said(host, repo):
    git(repo, "checkout", "-q", "-b", "other")
    git(repo, "branch", "-q", "-D", "dev")
    got = host.command("ideas.play", {})
    assert got["state"] == "failed" and "no dev branch" in got["error"]


def test_a_phone_never_gets_play(host):
    for name in ("ideas.play", "ideas.play_stop"):
        with pytest.raises(Exception, match="Play on the computer"):
            host.command(name, {"device": "phone"})
    with pytest.raises(IdeasError):
        host.ideas.play({"device": "phone"})
    assert host.ideas._play is None                                                                # nothing was started


# -- the page, not the first port (spec 90 §1) ---------------------------------------------------------------------------------------

def _two_ports(host, repo, monkeypatch, page: bool) -> None:
    """A preview that prints two ports: the first (`PORT`) answers 404 at `/`, the second a page when `page`."""
    from tests.test_idea_shot import TWO_PORTS
    commit(repo, {"twoports.py": TWO_PORTS})
    state = host.ideas.state_dir
    state.mkdir(exist_ok=True)
    (state / "checks.toml").write_text(f'preview = "{sys.executable} twoports.py"\n')
    monkeypatch.setenv("TWO_PORTS_PAGE", "yes" if page else "none")


def test_play_shows_the_port_that_gives_a_page_not_the_first_that_listens(host, repo, monkeypatch):
    _two_ports(host, repo, monkeypatch, page=True)
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "playing" and got["url"].endswith("/")
    assert "the client" in fetch(got["url"])                                              # Vite's page, not Express's "Cannot GET /"
    assert [e["ok"] for e in events(repo, event_log.PLAY_STARTED)] == [True]


def test_play_with_no_port_that_gives_a_page_says_nopage_with_the_ports_it_asked(host, repo, monkeypatch):
    _two_ports(host, repo, monkeypatch, page=False)
    monkeypatch.setattr(ideas_assets, "PLAY_OPEN_S", 4.0)
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "failed" and got["why"] == "nopage" and len(got["ports"]) == 2 and any("server listening on" in line for line in got["tail"]) and all(isinstance(p, int) for p in got["ports"])
    assert "no port gives a page" in got["error"] and "preview_port or preview_path" in got["error"]
    assert not (host.ideas.state_dir / "play").exists()
    e = events(repo, event_log.PLAY_STARTED)[-1]
    assert (e["ok"], e["why"]) == (False, "nopage")
    assert host.command("ideas.play", {"peek": True}) == got                              # it stays said until Play is pressed again


# -- Play breathes (spec 91 §5, decisions §107) ----------------------------------------------------------------------------------------

# A preview that listens after a while and answers 404 for some time more (the page "building"), then serves the page: the start has time to be in each stage.
SLOW_PAGE = """import http.server, os, time
began = time.monotonic()
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        ready = time.monotonic() - began > 1.8
        body = b"<!doctype html><title>Game</title><h1>built</h1>" if ready else b"building"
        self.send_response(200 if ready else 404)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
print("building...", flush=True)
time.sleep(0.8)
s = http.server.ThreadingHTTPServer(("127.0.0.1", int(os.environ["PORT"])), H)
print("Local: http://localhost:%s/" % os.environ["PORT"], flush=True)
s.serve_forever()
"""

# A preview that prints 40 lines in colour, then its error, and ends.
FAILS = """import sys
for i in range(40):
    print("\\x1b[2mline %d\\x1b[0m" % i)
print("\\x1b[31;1merror\\x1b[0m: the build broke \\x1b[4mhere\\x1b[24m", flush=True)
sys.exit(1)
"""


def test_play_waits_sixty_seconds_for_a_page_and_the_pictures_wait_stays_twenty():
    assert ideas_assets.PLAY_OPEN_S == 60.0 and idea_shot.OPEN_S == 20.0
    assert inspect.signature(idea_shot.opened).parameters["seconds"].default == idea_shot.OPEN_S      # `opened` itself still waits the picture's 20 by default
    assert inspect.signature(ideas_assets.Play.wait).parameters["seconds"].default is None            # the join follows PLAY_OPEN_S (read when it is called)


def test_the_start_moves_from_the_worktree_to_the_command_to_the_page_to_playing(repo, monkeypatch):
    commit(repo, {"slow.py": SLOW_PAGE})
    state = repo / ".orkcraft"
    state.mkdir(exist_ok=True)
    (state / "checks.toml").write_text(f'preview = "{sys.executable} slow.py"\n')
    make = ideas_assets.Play._worktree

    def slow_worktree(self, commit_):                                                       # long enough for a poll to see the stage
        time.sleep(0.5)
        make(self, commit_)

    monkeypatch.setattr(ideas_assets.Play, "_worktree", slow_worktree)
    published: list[dict] = []
    play = ideas_assets.Play(repo, state, lambda e, **f: None, lambda: published.append(play.answer("dev")))
    try:
        play.start("dev")
        seen: list[dict] = []
        end = time.monotonic() + 30
        while time.monotonic() < end:
            got = play.answer("dev")
            if not seen or (got.get("stage") or got["state"]) != (seen[-1].get("stage") or seen[-1]["state"]):
                seen.append(got)
            if got["state"] != "starting":
                break
            time.sleep(0.05)
        assert [g.get("stage") or g["state"] for g in seen] == ["worktree", "command", "page", "playing"]
        worktree, command, page, playing = seen
        assert worktree["command"] == "" and worktree["ports"] == []
        assert command["command"] == f"{sys.executable} slow.py" and command["ports"] == []                  # the command as words
        assert page["command"] == command["command"] and len(page["ports"]) >= 1 and all(isinstance(p, int) for p in page["ports"])
        assert worktree["since"] <= command["since"] <= page["since"] and page["since"] >= 1.0                   # seconds since the start
        assert playing["url"].startswith("http://127.0.0.1:") and "built" in fetch(playing["url"])
        until = time.monotonic() + 10                                                                             # the bus is told after the state is: wait for its last word
        while time.monotonic() < until and not any((p.get("stage") or p["state"]) == "playing" for p in published):
            time.sleep(0.05)
        stages = [p.get("stage") or p["state"] for p in published]                                                # the bus is told of each change
        assert [s for i, s in enumerate(stages) if i == 0 or s != stages[i - 1]][:3] == ["command", "page", "playing"]
        assert stages.count("command") == 1 and stages.count("page") == 1                                         # not on every look at the ports
    finally:
        play.stop("stopped", wait=True)


def test_a_failure_carries_the_commands_last_30_lines_without_colour_codes(host, repo):
    commit(repo, {"fails.py": FAILS})
    state = host.ideas.state_dir
    state.mkdir(exist_ok=True)
    (state / "checks.toml").write_text(f'preview = "{sys.executable} fails.py"\n')
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "failed" and got["error"] == "did not open"                                             # the command ended before a page
    tail = got["tail"]
    assert len(tail) == idea_shot.TAIL_LINES == 30 and tail[0] == "line 11" and tail[-1] == "error: the build broke here"
    assert not any("\x1b" in line for line in tail)
    failed = events(repo, event_log.PLAY_STARTED)[-1]                          # spec 107 §2: the command and its last output are in the day's log too
    assert failed["ok"] is False and failed["command"] == f"{sys.executable} fails.py" and failed["url"] == ""
    assert failed["tail"].endswith("error: the build broke here") and len(failed["tail"]) <= 600
    assert host.command("ideas.play", {"peek": True}) == got                                                       # it stays said until Play is pressed again
    assert not (state / "play").exists()


def test_an_exception_says_why_and_answers_a_tail_too(host, monkeypatch):
    def broken(self, commit_):
        raise RuntimeError("could not make its worktree: disk full")

    monkeypatch.setattr(ideas_assets.Play, "_worktree", broken)
    host.command("ideas.play", {})
    got = settle(host)
    assert got == {"state": "failed", "error": "could not make its worktree: disk full", "tail": []}


# -- the snapshot knows before the press whether there is a preview (spec 113 §2, decisions §191.1) ---------------------------------------

def preview_of_snapshot(host) -> str:
    host.ideas._cache = None                                  # the snapshot keeps its Board's read ten seconds: a file changed since is read again
    return host.snapshot()["preview"]


def test_the_snapshot_says_how_the_project_opens_a_preview(host, repo):
    state = host.ideas.state_dir
    assert preview_of_snapshot(host) == "static"                                                                  # an index.html at its root
    (repo / "index.html").unlink()
    assert preview_of_snapshot(host) == ""                                                                        # none: the die sleeps
    (repo / "package.json").write_text('{"scripts": {"test": "jest", "dev": "vite"}}')
    assert preview_of_snapshot(host) == "command"                                                                 # a package's dev script
    (repo / "package.json").write_text('{"scripts": {"test": "jest"}}')
    assert preview_of_snapshot(host) == ""                                                                        # a package with no script that serves
    (state / "checks.toml").write_text('preview = "mkdocs serve"\n')
    assert preview_of_snapshot(host) == "command"                                                                 # a wiki with a site to serve: the die wakes as a game's does
    (state / "checks.toml").write_text('preview = "   "\n')
    assert preview_of_snapshot(host) == ""                                                                        # a blank command is none


def test_the_phone_is_not_told_of_a_preview(host):
    from orkboard.gui.board_host import BoardPhone
    assert "preview" in host.snapshot() and "preview" not in BoardPhone.phone_snapshot(host)                      # the phone has no Play


# -- the die's up face: the host says whether the last start failed, or dev has something new (spec 118 §3) ----------------------------------

def face(host) -> str:
    host.ideas._head_seen = (0.0, "", "")                     # the snapshot keeps dev's head two seconds: a commit made since is read again
    return host.snapshot()["play_face"]


def test_a_project_never_tried_says_nothing_and_a_head_tried_says_nothing(host, repo):
    assert face(host) == ""                                                                                       # nothing it could be new against
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    head = git(repo, "rev-parse", "dev")
    assert ideas_assets.tried_commit(host.ideas.state_dir) == head                                                # it came to playing: that is the commit tried
    assert face(host) == ""                                                                                       # playing head
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()
    assert face(host) == ""                                                                                       # stopped, tried at head


def test_dev_moved_since_the_last_play_says_new(host, repo):
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()
    commit(repo, {"index.html": PAGE + "<p>more</p>"}, "more")
    assert face(host) == "new"
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    assert face(host) == ""                                                                                       # playing the new head: it is tried now
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()
    assert face(host) == ""


def test_dev_moving_while_playing_says_new_and_starting_head_says_nothing(host, repo, monkeypatch):
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    commit(repo, {"index.html": PAGE + "<p>more</p>"}, "more")
    assert face(host) == "new"                                                                                    # playing an older head: the new one is news
    host.ideas.player.stop("stopped", wait=True)
    release = threading.Event()
    real = ideas_assets.Play._worktree
    monkeypatch.setattr(ideas_assets.Play, "_worktree", lambda self, c: (release.wait(10), real(self, c))[1])
    host.command("ideas.play", {})
    assert host.ideas.player.state == "starting"
    assert face(host) == ""                                                                                       # starting head now
    release.set()
    assert settle(host)["state"] == "playing"


def test_a_failed_start_at_head_says_failed_and_dev_moving_after_it_says_new(host, repo, monkeypatch):
    def broken(self, commit):
        raise RuntimeError("disk full")

    monkeypatch.setattr(ideas_assets.Play, "_worktree", broken)
    host.command("ideas.play", {})
    assert settle(host)["state"] == "failed"
    head = git(repo, "rev-parse", "dev")
    assert ideas_assets.tried_commit(host.ideas.state_dir) == head                                                # a failure is a start tried too
    assert face(host) == "failed"                                                                                 # the cross stays while it did not start
    commit(repo, {"index.html": PAGE + "<p>fixed</p>"}, "fixed")
    assert face(host) == "new"                                                                                    # a head not tried since
    monkeypatch.undo()
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    assert face(host) == ""


def test_a_start_stopped_before_it_came_to_anything_is_not_tried(host, repo, monkeypatch):
    release = threading.Event()
    real = ideas_assets.Play._worktree
    monkeypatch.setattr(ideas_assets.Play, "_worktree", lambda self, c: (release.wait(10), real(self, c))[1])
    host.command("ideas.play", {})
    host.ideas.player.stop("stopped")
    release.set()
    host.ideas.player.wait()
    assert host.ideas.player.state == "" and not (host.ideas.state_dir / ideas_assets.TRIED_FILE).exists() and face(host) == ""


def test_no_preview_is_not_tried(host, repo):
    (repo / "index.html").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "no page")
    host.command("ideas.play", {})
    assert settle(host) == {"state": "failed", "error": "no preview", "none": True}
    assert ideas_assets.tried_commit(host.ideas.state_dir) == "" and face(host) == ""                             # a project with no preview has nothing to fail
    assert not (host.ideas.state_dir / ideas_assets.TRIED_FILE).exists()


def test_the_commit_last_tried_survives_a_new_play_and_an_unreadable_file_is_none(host, repo):
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    head = git(repo, "rev-parse", "dev")
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()
    state = host.ideas.state_dir
    assert json.loads((state / ideas_assets.TRIED_FILE).read_text()) == {"commit": head}
    again = ideas_assets.Play(repo, state, lambda *a, **k: None, lambda: None)
    assert again.tried == head                                                                                    # read back from the file
    (state / ideas_assets.TRIED_FILE).write_text("{not json")
    assert ideas_assets.Play(repo, state, lambda *a, **k: None, lambda: None).tried == ""


def test_the_face_is_said_before_any_play_exists_and_never_breaks_the_snapshot(host, repo, monkeypatch):
    state = host.ideas.state_dir
    state.mkdir(parents=True, exist_ok=True)
    (state / ideas_assets.TRIED_FILE).write_text(json.dumps({"commit": "0" * 40}))
    assert host.ideas._play is None and face(host) == "new"                                                       # read from the file; no Play was made to answer
    assert host.ideas._play is None
    monkeypatch.setattr(ideas_assets.commit_goal, "head", lambda *a: (_ for _ in ()).throw(OSError("git")))
    assert face(host) == ""


def test_the_phone_is_not_told_of_the_face(host):
    from orkboard.gui.board_host import BoardPhone
    assert "play_face" in host.snapshot() and "play_face" not in BoardPhone.phone_snapshot(host)
