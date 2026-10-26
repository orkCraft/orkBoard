"""Spec 88 §5 (docs/specs/88-assets-and-play.md): Play opens the project's own preview of dev's head in a worktree of its own, on the
machine's own address; one a project, answered the same while it runs; stopped by its command, by ten minutes with no face, and by
closing the project, its worktree removed; `play_started` and `play_stopped`; never for a phone. A stub preview, as tests/test_idea_shot.py's."""
from __future__ import annotations

import subprocess
import sys
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
    assert first == {"state": "starting", "commit": head, "short": head[:7]}
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
    monkeypatch.setattr(idea_shot, "OPEN_S", 1.0)
    host.command("ideas.play", {})
    got = settle(host)
    assert got == {"state": "failed", "error": "did not open"} and not (host.ideas.state_dir / "play").exists()


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
    monkeypatch.setattr(idea_shot, "OPEN_S", 4.0)
    host.command("ideas.play", {})
    got = settle(host)
    assert got["state"] == "failed" and got["why"] == "nopage" and len(got["ports"]) == 2 and all(isinstance(p, int) for p in got["ports"])
    assert "no port gives a page" in got["error"] and "preview_port or preview_path" in got["error"]
    assert not (host.ideas.state_dir / "play").exists()
    e = events(repo, event_log.PLAY_STARTED)[-1]
    assert (e["ok"], e["why"]) == (False, "nopage")
    assert host.command("ideas.play", {"peek": True}) == got                              # it stays said until Play is pressed again
