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


def test_a_path_that_is_missing_stays_as_it_was(tmp_path):
    root = _project(tmp_path)
    for text in ("Fix @src/nowhere.py", "Tell @Tech about it", "mail me@example.com", "see @../outside.txt", "@.git/config and @.orkcraft", "an @ alone and @"):
        assert goal_mentions.files(root, text) == (text, 0), text


def test_two_mentions_and_a_sentences_punctuation(tmp_path):
    root = _project(tmp_path)
    assert goal_mentions.files(root, "Compare @README.md, then @src/lobby/room.py.") == ("Compare `README.md`, then `src/lobby/room.py`.", 2)
    assert goal_mentions.files(root, "(see @README.md)\n@src/lobby/room.py?") == ("(see `README.md`)\n`src/lobby/room.py`?", 2)
    assert goal_mentions.files(root, "@README.md and @missing.md and @src/") == ("`README.md` and @missing.md and `src/`", 2)


def test_a_path_in_backticks_already_is_left_alone(tmp_path):
    root = _project(tmp_path)
    text = "Fix `src/lobby/room.py` and `@README.md`, then ```\n@src/lobby/room.py\n``` and @README.md"
    assert goal_mentions.files(root, text) == (text.replace("and @README.md", "and `README.md`"), 1)
    assert goal_mentions.files(root, "`src/lobby/room.py` only") == ("`src/lobby/room.py` only", 0)


def test_ideas_add_writes_the_paths_and_the_event_counts_them(fake_repo):
    host = Orkboard(fake_repo)
    goal = ideas.save_goal(host.ideas.root(), None, "Lobby", "About the lobby", None, "normal")[0]
    got = host.command("ideas.add", {"text": "Rework @src/app.py and @README.md, not @nowhere.py", "track": goal, "hold": True})
    said = " ".join(t["text"] for t in ideas.talk(host.ideas.state_dir, got["slug"]))
    assert "Rework `src/app.py` and `README.md`, not @nowhere.py" in said
    (added,) = [r for r in event_log.read(Path(fake_repo)) if r["event"] == "idea_added"]
    assert added["files"] == 2
