"""Spec 88 §5 (docs/specs/88-assets-and-play.md): Play opens the project's own preview of dev's head in a worktree of its own, on the
machine's own address; one a project, answered the same while it runs; stopped by its command, by ten minutes with no face, and by
closing the project, its worktree removed; `play_started` and `play_stopped`; never for a phone. A stub preview, as tests/test_idea_shot.py's."""
from __future__ import annotations

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
from orkboard.realm import event_log, ideas

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




def test_a_phone_never_gets_play(host):
    for name in ("ideas.play", "ideas.play_stop"):
        with pytest.raises(Exception, match="Play on the computer"):
            host.command(name, {"device": "phone"})
    with pytest.raises(IdeasError):
        host.ideas.play({"device": "phone"})
    assert host.ideas._play is None                                                                # nothing was started


# -- the page, not the first port (spec 90 §1) ---------------------------------------------------------------------------------------







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






# -- the snapshot knows before the press whether there is a preview (spec 113 §2, decisions §191.1) ---------------------------------------







# -- the die's up face: the host says whether the last start failed, or dev has something new (spec 118 §3) ----------------------------------

def face(host) -> str:
    host.ideas._head_seen = (0.0, "", "")                     # the snapshot keeps dev's head two seconds: a commit made since is read again
    return host.snapshot()["play_face"]




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














# -- the die's pips: how many goals landed in dev since Play last tried it (decisions §200.5) --------------------------------------------------------

def landed_goal(host, repo, slug, files):
    """A goal's task landed in dev: its commit on dev and the plan the runner keeps (`commit`, `subjects`)."""
    sha = commit(repo, files, f"{slug} work")
    folder = ideas.state_folder(host.ideas.state_dir, slug)
    folder.mkdir(parents=True, exist_ok=True)
    plan = ideas.plan(host.ideas.state_dir, slug) or {"tasks": []}
    plan["tasks"].append({"id": f"k{len(plan['tasks']) + 1}", "state": "merged", "commit": sha, "subjects": [f"{slug} work"]})
    (folder / "plan.json").write_text(json.dumps(plan))
    return sha


def pips(host) -> tuple[str, int]:
    host.ideas._head_seen = (0.0, "", "")
    snap = host.snapshot()
    return snap["play_face"], snap["new_n"]


def tried_once(host):
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    host.command("ideas.play_stop", {})
    host.ideas.player.wait()


def test_the_snapshot_counts_the_goals_new_in_dev_since_the_last_play(host, repo):
    assert pips(host) == ("", 0)                                                                                  # never tried: nothing is new
    tried_once(host)
    assert pips(host) == ("", 0)
    landed_goal(host, repo, "dark-mode", {"dark.css": "a"})
    assert pips(host) == ("new", 1)
    landed_goal(host, repo, "sound", {"sound.js": "b"})
    landed_goal(host, repo, "dark-mode", {"dark2.css": "c"})                                                      # the same goal again counts once
    assert pips(host) == ("new", 2)
    for n in range(3, 9):
        landed_goal(host, repo, f"goal-{n}", {f"g{n}.txt": "x"})
    assert pips(host) == ("new", 8)                                                                               # the face shows six for six or more; the count is the host's whole
    host.command("ideas.play", {})
    assert settle(host)["state"] == "playing"
    assert pips(host) == ("", 0)                                                                                  # tried now






