"""Machine settings: what onboarding asks once per machine (tools, billing, the quiet hours)."""
from __future__ import annotations

import json
from pathlib import Path

from orkboard import schedule, settings


def test_defaults_when_there_is_no_file(tmp_path: Path):
    s = settings.load(tmp_path / "none.json")
    assert not s.onboarded and s.quiet is None
    assert set(s.tools) == set(settings.TOOLS)
    assert all(not c.enabled and c.billing == "subscription" for c in s.tools.values())


def test_round_trip(tmp_path: Path):
    f = tmp_path / "deep" / "settings.json"
    s = settings.MachineSettings(onboarded=True, quiet=schedule.DEFAULT_QUIET)
    s.tools["claude"] = settings.ToolChoice(enabled=True, billing="api")
    settings.save(s, f)
    back = settings.load(f)
    assert back.onboarded and back.quiet == schedule.DEFAULT_QUIET
    assert back.tools["claude"].enabled and back.tools["claude"].billing == "api"
    assert not back.tools["agy"].enabled


def test_broken_or_unknown_values_fall_back(tmp_path: Path):
    f = tmp_path / "settings.json"
    f.write_text("{not json", encoding="utf-8")
    assert not settings.load(f).onboarded
    f.write_text('{"tools": {"claude": {"enabled": true, "billing": "barter"}, "gpt": {}}}', encoding="utf-8")
    s = settings.load(f)
    assert s.tools["claude"].enabled and s.tools["claude"].billing == "subscription"
    assert "gpt" not in s.tools


# -- spec 84 §1: review is off by default, and a file that asked for it before is moved off once ----------------------------------

def test_an_old_settings_file_with_review_on_is_moved_off_once_and_said_once(tmp_path: Path):
    f = tmp_path / "settings.json"
    f.write_text(json.dumps({"onboarded": True, "ideas": {"review": True, "max_parallel": 2}}), encoding="utf-8")
    s = settings.load(f)
    assert s.ideas["review"] is False and s.ideas["review_v"] == 2 and s.ideas["max_parallel"] == 2 and s.review_notice
    settings.save(s, f)
    kept = json.loads(f.read_text(encoding="utf-8"))
    assert kept["ideas"]["review"] is False and kept["ideas"]["review_v"] == 2 and kept["review_notice"] is True
    kept["ideas"]["review"] = True                       # the person turned it on after the move: never moved again
    kept["review_notice"] = False
    f.write_text(json.dumps(kept), encoding="utf-8")
    again = settings.load(f)
    assert again.ideas["review"] is True and again.ideas["review_v"] == 2 and not again.review_notice


def test_a_projects_board_json_naming_review_is_moved_off_once(tmp_path: Path):
    (tmp_path / ".orkcraft").mkdir()
    file = tmp_path / ".orkcraft" / "board.json"
    file.write_text(json.dumps({"review": True, "push": True}), encoding="utf-8")
    got = settings.board_of(tmp_path, settings.MachineSettings().ideas)
    assert got["review"] is False and got["push"] is True
    kept = json.loads(file.read_text(encoding="utf-8"))
    assert kept["review"] is False and kept["review_v"] == 2
    file.write_text(json.dumps({**kept, "review": True}), encoding="utf-8")            # set again by the person: it stays
    assert settings.board_of(tmp_path, settings.MachineSettings().ideas)["review"] is True
    settings.save_board(tmp_path, {"review": True})
    assert json.loads(file.read_text(encoding="utf-8"))["review_v"] == 2
    other = tmp_path / "other"
    (other / ".orkcraft").mkdir(parents=True)
    (other / ".orkcraft" / "board.json").write_text(json.dumps({"push": True}), encoding="utf-8")
    assert settings.board_of(other, {**settings.IDEAS, "review": True})["review"] is True      # no `review` named: the machine's stands


def test_work_at_night_is_off_by_default_cleaned_to_a_boolean_and_the_projects_own(tmp_path: Path):
    """Spec 121 §4.1: the Board's setting, `False` until the person says; a value that is no boolean is the default; the project's `board.json` keeps it."""
    assert settings.IDEAS["work_at_night"] is False and settings.MachineSettings().ideas["work_at_night"] is False
    assert settings.clean_ideas({"work_at_night": True})["work_at_night"] is True
    for broken in ("yes", 1, None, [], {"on": True}):
        assert settings.clean_ideas({"work_at_night": broken})["work_at_night"] is False, broken
    assert settings.MachineSettings.from_dict({"ideas": {"work_at_night": True}}).ideas["work_at_night"] is True
    assert "work_at_night" in settings.BOARD
    assert settings.board_of(tmp_path, settings.MachineSettings().ideas)["work_at_night"] is False
    settings.save_board(tmp_path, {"work_at_night": True})
    assert json.loads((tmp_path / ".orkcraft" / "board.json").read_text(encoding="utf-8"))["work_at_night"] is True
    assert settings.board_of(tmp_path, settings.MachineSettings().ideas)["work_at_night"] is True
    other = tmp_path / "other"                                                              # a project that names none: the machine's stands
    other.mkdir()
    assert settings.board_of(other, {**settings.IDEAS, "work_at_night": True})["work_at_night"] is True
