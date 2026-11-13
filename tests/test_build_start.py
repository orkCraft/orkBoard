"""Spec 168 H2 (decisions §283.31): *The build starts*, `autostart` and `look_wait` as one setting. Both old keys are read and kept; the new value is derived from them."""
from __future__ import annotations

import pytest

from orkboard import settings
from orkboard.gui.board_host import CommandError
from orkboard.realm import look_wait, night_slot
from tests.test_board_35 import host, model, runner  # noqa: F401  (fixtures)


@pytest.mark.parametrize("autostart, look, value", [
    (True, "none", "now"), (True, "30m", "30m"), (True, "2h", "2h"), (True, "tonight", "tonight"),
    (False, "none", "hand"), (False, "2h", "hand"), (False, "tonight", "hand"),
    (True, "junk", "2h"), (True, None, "2h"),             # an unknown look reads as the default, 2 h
])
def test_the_two_old_keys_read_as_the_one_value(autostart, look, value):
    assert look_wait.build_start(autostart, look) == value
    assert settings.clean_ideas({"autostart": autostart, "look_wait": look}) | {} is not None       # and the file that says them loads


def test_a_settings_file_with_only_the_old_keys_reads_the_value():
    for raw, want in (({"autostart": True, "look_wait": "30m"}, "30m"), ({"autostart": False}, "hand"), ({"look_wait": "none"}, "now"), ({}, look_wait.build_start(True, settings.IDEAS["look_wait"]))):
        ideas = settings.clean_ideas(raw)
        assert look_wait.build_start(ideas["autostart"], ideas["look_wait"]) == want


@pytest.mark.parametrize("value, keys", [
    ("now", {"autostart": True, "look_wait": "none"}), ("30m", {"autostart": True, "look_wait": "30m"}), ("2h", {"autostart": True, "look_wait": "2h"}),
    ("tonight", {"autostart": True, "look_wait": "tonight"}),
])
def test_a_value_writes_both_old_keys(value, keys):
    assert look_wait.build_start_keys(value, "2h") == keys
    assert look_wait.build_start(**{"autostart": keys["autostart"], "look": keys["look_wait"]}) == value


def test_by_hand_turns_the_start_off_and_keeps_the_look():
    assert look_wait.build_start_keys("hand", "30m") == {"autostart": False, "look_wait": "30m"}
    assert look_wait.build_start_keys("hand", None) == {"autostart": False, "look_wait": "2h"}
    assert look_wait.build_start_keys("later") == {}


def test_a_file_that_says_the_new_value_is_read_into_the_two_old_keys():
    got = settings.clean_ideas({"build_start": "tonight"})
    assert (got["autostart"], got["look_wait"]) == (True, "tonight") and "build_start" not in got           # the two keys are what is kept
    got = settings.clean_ideas({"build_start": "hand", "look_wait": "30m"})
    assert (got["autostart"], got["look_wait"]) == (False, "30m")
    assert settings.clean_ideas({"build_start": "soon", "autostart": False})["autostart"] is False         # an unknown value says nothing


def test_the_board_says_the_value_and_sets_it(host):
    for value in look_wait.BUILD_STARTS:
        got = host.command("ideas.board_set", {"build_start": value})
        assert got["build_start"] == value
        mine = host.ideas.settings_now()
        assert look_wait.build_start(mine["autostart"], mine["look_wait"]) == value
        assert host.command("ideas.board")["build_start"] == value
    with pytest.raises(CommandError):
        host.command("ideas.board_set", {"build_start": "soon"})


def test_the_old_keys_still_set_it(host):
    host.command("ideas.board_set", {"autostart": True, "look_wait": "30m"})
    assert host.command("ideas.board")["build_start"] == "30m"
    host.command("ideas.board_set", {"autostart": False})
    assert host.command("ideas.board")["build_start"] == "hand"
    host.command("ideas.board_set", {"autostart": True, "look_wait": "none"})
    assert host.command("ideas.board")["build_start"] == "now"


def test_the_night_is_read_through_one_function(host):
    assert night_slot.way({}) == "off" and night_slot.way({"work_at_night": True}) == "builds"
    assert night_slot.way({"night_rung": "ideas", "work_at_night": False}) == "ideas"
    assert night_slot.keys("proposals") == {"night_rung": "proposals", "work_at_night": True} and night_slot.keys("ideas")["work_at_night"] is False
    with pytest.raises(ValueError):
        night_slot.keys("always")
    host.command("ideas.board_set", {"night_rung": "ideas"})
    assert host.command("ideas.board")["night_rung"] == "ideas" and host.ideas.settings_now()["work_at_night"] is False


def test_goals_at_once_is_one_to_eight(host):
    assert host.command("ideas.board_set", {"max_parallel": 3})["max_parallel"] == 3
    for bad in (0, 9, "3", True):
        with pytest.raises(CommandError):
            host.command("ideas.board_set", {"max_parallel": bad})
