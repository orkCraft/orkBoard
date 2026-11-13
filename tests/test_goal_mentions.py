"""The files a goal's text names with `@` (docs/specs/107-what-the-owners-day-said.md part K, decisions §182.13; realm/goal_mentions.py): each `@path` that exists becomes the path in
backticks, nothing else is touched, and `ideas.add` applies it before the route reads the text and counts the paths in `idea_added`."""
from __future__ import annotations

from pathlib import Path

from orkboard.gui.board_host import Orkboard
from orkboard.realm import event_log, goal_mentions, ideas


def _project(tmp_path):
    (tmp_path / "src" / "lobby").mkdir(parents=True)
    (tmp_path / "src" / "lobby" / "room.py").write_text("x\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".orkcraft").mkdir()
    return tmp_path


def test_a_path_that_exists_is_written_in_backticks(tmp_path):
    root = _project(tmp_path)
    assert goal_mentions.files(root, "Fix @src/lobby/room.py now") == ("Fix `src/lobby/room.py` now", 1)
    assert goal_mentions.files(root, "@README.md") == ("`README.md`", 1)
    assert goal_mentions.files(root, "Look in @src/lobby/ and @src") == ("Look in `src/lobby/` and `src`", 2), "a folder too"


def test_ideas_add_writes_the_paths_and_the_event_counts_them(fake_repo):
    host = Orkboard(fake_repo)
    goal = ideas.save_goal(host.ideas.root(), None, "Lobby", "About the lobby", None, "normal")[0]
    got = host.command("ideas.add", {"text": "Rework @src/app.py and @README.md, not @nowhere.py", "track": goal, "hold": True})
    said = " ".join(t["text"] for t in ideas.talk(host.ideas.state_dir, got["slug"]))
    assert "Rework `src/app.py` and `README.md`, not @nowhere.py" in said
    (added,) = [r for r in event_log.read(Path(fake_repo)) if r["event"] == "idea_added"]
    assert added["files"] == 2
