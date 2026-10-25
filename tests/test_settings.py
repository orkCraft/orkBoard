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


def test_path_follows_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ORKCRAFT_SETTINGS_FILE")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert settings.path() == tmp_path / "orkcraft" / "settings.json"
    monkeypatch.setenv("ORKCRAFT_SETTINGS_FILE", str(tmp_path / "x.json"))
    assert settings.path() == tmp_path / "x.json"


def test_the_old_look_and_office_hours_load_and_are_not_written_again(tmp_path: Path):
    f = tmp_path / "settings.json"
    f.write_text(json.dumps({"mode": "shift", "onboarded": True, "office": {"start": "09:00", "end": "18:00"},
                             "office_days": [0, 1, 2], "quiet": {"start": "23:00", "end": "08:00"}}),
                 encoding="utf-8")
    s = settings.load(f)
    assert s.onboarded and s.quiet == schedule.DEFAULT_QUIET
    assert not hasattr(s, "mode") and not hasattr(s, "office") and not hasattr(s, "office_days")
    settings.save(s, f)
    assert not {"mode", "office", "office_days"} & set(json.loads(f.read_text(encoding="utf-8")))


def test_the_board_is_in_focus_by_default_and_its_settings_are_cleaned():
    s = settings.MachineSettings()
    assert s.focus == "board" and s.ideas == {"batch_minutes": 30, "idle_hours": 24, "max_parallel": 1,
                                              "merge_into": "dev", "push": False, "review": False, "review_v": 2,      # spec 84 §1: off by default
                                              # spec 35 §12: the Board's Target, autostart, night, reserves, own paths
                                              "target": "balance", "autostart": True, "night": "01:00-07:00",
                                              "reserve_day": 0.3, "reserve_night": 0.1, "risk_paths": []}
    back = settings.MachineSettings.from_dict({"focus": "", "ideas": {"batch_minutes": 0, "max_parallel": 2,
                                                                      "merge_into": "../x", "push": "yes"}})
    assert back.focus == "" and back.ideas["max_parallel"] == 2 and back.ideas["batch_minutes"] == 30
    assert back.ideas["merge_into"] == "dev" and back.ideas["push"] is False and back.ideas["review"] is False
    owner = settings.MachineSettings.from_dict({"ideas": {"merge_into": "main", "push": True, "review": False, "review_v": 2}})
    assert owner.ideas["merge_into"] == "main" and owner.ideas["push"] is True and owner.ideas["review"] is False
    looking = settings.MachineSettings.from_dict({"ideas": {"review": True, "review_v": 2}})
    assert looking.ideas["review"] is True and not looking.review_notice          # what a person set after the move stays
    assert settings.MachineSettings.from_dict({"focus": "town"}).focus == "board"
    assert settings.MachineSettings.from_dict(back.to_dict()).ideas == back.ideas


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


def test_the_notice_is_for_a_machine_that_had_review_on_and_not_for_a_new_one_or_one_that_had_it_off():
    assert not settings.MachineSettings.from_dict({}).review_notice                       # a new machine has nothing to be told
    assert settings.MachineSettings.from_dict({"onboarded": True}).review_notice          # an old one read the default (on) before
    assert not settings.MachineSettings.from_dict({"onboarded": True, "ideas": {"review": False}}).review_notice
    assert settings.MachineSettings.from_dict({"onboarded": True, "ideas": {"max_parallel": 2}}).ideas["review"] is False


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
