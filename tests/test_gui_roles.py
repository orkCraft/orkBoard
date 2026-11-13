"""Spec 59 §2.4 (gui/ideas_roles.py): `ideas.roles` answers the library's parties (`presets`) and every leader's stages (`stages`), and
the five new kinds. Code, no model."""
from __future__ import annotations

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import library


@pytest.fixture
def host(fake_repo) -> Orkboard:
    return Orkboard(fake_repo)


def test_ideas_roles_answers_the_presets_the_mixed_first_and_the_old_parties_as_before(host):
    got = host.command("ideas.roles")
    assert [p["id"] for p in got["presets"]] == ["game", "mobile-app", "website", "ideation", "release", "art", "engineering", "design", "data",
                                                 "marketing", "product", "mixed"]          # Ideation after Website (spec 65 §1), Art and sound after Release
    game = got["presets"][0]
    assert (game["name"], game["craft"], game["race"], game["mixed"], game["lead"]) == ("Game", "design", "elf", True, "game-designer")
    assert game["build"] == ["grunt", "artist", "level-designer", "sound-designer"] and game["check"] == ["playtester"]
    assert set(game) == {"id", "name", "line", "craft", "race", "mixed", "lead", "build", "check"}
    assert got["parties"]["engineering"] == {"lead": "architect", "build": ["grunt", "tester"], "check": ["reviewer"]}      # by craft, as before
    assert got["parties"]["game"]["lead"] == "game-designer" and got["seats"] == {"lead": 1, "build": 5, "check": 2}


def test_ideas_roles_answers_every_leaders_stages_and_the_default(host):
    stages = host.command("ideas.roles")["stages"]
    assert stages["game-designer"] == {"lead": "Concept", "build": "Build", "check": "Playtest", "seats": {"lead": 1, "build": 5, "check": 2}}
    assert stages["default"]["build"] == "Implementation" and stages["default"]["seats"] == {"lead": 1, "build": 5, "check": 2}
    assert set(stages) == {a.id for a in library.LIBRARY if a.band == "lead"} | {"default"}



def test_an_agent_of_the_library_is_added_given_a_kind_and_dropped_and_the_spend_is_asked_of_a_goal_or_a_party(host):
    slug = host.command("ideas.role_add", {"id": "tester"})["slug"]
    assert slug == "tester" and any(r["slug"] == "tester" for r in host.command("ideas.roles")["roles"])
    for again, bad in (("ideas.role_add", {"id": "tester"}), ("ideas.role_add", {"id": "no-such"}), ("ideas.kind_set", {"kind": "nope", "role": "tester"})):
        with pytest.raises(CommandError):
            host.command(again, bad)
    assert host.command("ideas.kind_set", {"kind": "tests", "role": "tester"}) == {"ok": True}
    assert host.command("ideas.role_drop", {"slug": "tester"}) == {"ok": True}
    assert all(r["slug"] != "tester" for r in host.command("ideas.roles")["roles"])
    for args in ({"idea": "no-goal"}, {"goal": "no-party"}):
        with pytest.raises(CommandError, match="gone"):
            host.command("ideas.spend", args)
