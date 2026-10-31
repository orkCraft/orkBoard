"""Spec 102 C §3.1 (docs/specs/102-the-other-maps-and-picking-on-them.md, decisions §135.3–§135.4): Art's map, the assets by kind with Art's kinds first (art and
icons, sound, music, clips) and the others under them, each file with its folder, a picked file's variants not picked under it; its text bounded and the same
bytes for the same dev, the folders by count's words, the picks, what changed since the last call with its goal; no dev, no map and no text; nothing to read.
Spec 117 §3: an asset's weight at its edges, a kind's bytes, the budget set, unset and unreadable.
`ideas.art_map` on the host, composed as the lead's wiring does. Real git repositories (tests/test_commit_goal.py's), no model."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from orkboard.gui.board_host import Orkboard
from orkboard.gui.ideas_maps import MapsMixin, maps_commands
from orkboard.realm import art_map, idea_pick, idea_shots, ideas, map_text
from tests import pick_files as pf
from tests.test_assets import PNG, land_files, put
from tests.test_commit_goal import git, repo, state  # noqa: F401  (the fixture)


def lane(got: dict, kind: str) -> dict:
    return next(k for k in got["kinds"] if k["kind"] == kind)


@pytest.fixture
def game(repo):
    put(repo, {**{f"sprites/s{n}.png": pf.png(n + 1, 2) for n in range(4)}, "icons/app.png": PNG, "logo.png": PNG, "game/sfx/jump.wav": pf.wav(0.5),
               "game/sfx/hit.wav": pf.wav(0.4), "music/theme.wav": pf.wav(12, rate=200), "clips/intro.mp4": pf.mp4(seconds=5), "fonts/Pixel.ttf": b"\x00\x01\x00\x00font",
               "README.md": b"# hi"})
    return repo


# -- read --------------------------------------------------------------------------------------------------------------------------------

def test_art_kinds_come_first_in_their_order_then_the_others_each_asset_with_its_folder(game):
    got = art_map.read(state(game), game)
    assert [(k["kind"], k["own"], k["n"]) for k in got["kinds"]] == [("art", True, 6), ("sound", True, 2), ("music", True, 1), ("clip", True, 1), ("font", False, 1)]
    assert got["commit"] == git(game, "rev-parse", "dev") and got["short"] == got["commit"][:7] and got["ref"] == "dev" and got["none"] is False
    assert lane(got, "art")["folders"] == [{"folder": "./", "n": 1}, {"folder": "icons/", "n": 1}, {"folder": "sprites/", "n": 4}]
    assert lane(got, "sound")["folders"] == [{"folder": "game/sfx/", "n": 2}]
    one = next(a for a in lane(got, "art")["assets"] if a["id"] == "sprites/s3.png")
    assert (one["folder"], one["kind"], one["w"], one["h"], one["change"]) == ("sprites/", "art", 4, 2, "") and "others" not in one
    assert (got["since"], got["removed"], got["stacks"]) == ("", [], [])


def test_an_art_kind_is_read_even_with_nothing_in_it_and_the_others_only_when_they_have_something(repo):
    put(repo, {"music/theme.wav": pf.wav(12, rate=200)})
    got = art_map.read(state(repo), repo)
    assert [(k["kind"], k["n"]) for k in got["kinds"]] == [("art", 0), ("sound", 0), ("music", 1), ("clip", 0)] and got["none"] is False
    assert lane(got, "art")["assets"] == [] and lane(got, "art")["folders"] == []


def test_the_screens_lie_last_dev_trees_only_and_no_dev_is_an_empty_map(repo, tmp_path):
    s = state(repo)
    png = tmp_path / "shot.png"
    png.write_bytes(pf.png(6, 4))
    idea_shots.store(s, "dark-mode", "k2", 1, png)
    (ideas.state_folder(s, "dark-mode") / "plan.json").write_text(json.dumps({"tasks": [{"id": "k2", "title": "Draw the home screen", "short": "Home screen"}]}))
    put(repo, {"art/hero.png": PNG})
    (repo / "art" / "draft.png").write_bytes(PNG)                                                  # the working tree's: never read
    got = art_map.read(s, repo)
    assert [k["kind"] for k in got["kinds"]] == ["art", "sound", "music", "clip", "screen"] and lane(got, "screen")["assets"][0]["id"] == "screen:dark-mode/k2"
    assert [a["id"] for a in lane(got, "art")["assets"]] == ["art/hero.png"] and lane(got, "screen")["folders"] == []
    none = art_map.read(s, repo, ref="no-such")
    assert (none["commit"], none["kinds"], none["none"]) == ("", [], True) and art_map.text(s, repo, ref="no-such") is None


def test_a_picked_file_keeps_its_variants_not_picked_under_it(repo, tmp_path):
    s = state(repo)
    pick = pf.make_pick(s, tmp_path / "v", {"a.png": pf.png(2, 2), "b.png": pf.png(3, 3), "c.png": pf.png(4, 4)}, slug="logo")
    idea_pick.answer(s, "logo", pick, "B", "the round one")
    (ideas.state_folder(s, "logo") / "plan.json").write_text(json.dumps({"tasks": [pf.task(3, state="merged")]}))
    put(repo, {"assets/logo.png": pf.png(3, 3), "assets/other.png": PNG})
    rows = {a["id"]: a for a in lane(art_map.read(s, repo), "art")["assets"]}
    o = rows["assets/logo.png"]["others"]
    assert (o["goal"], o["pick"], o["picked"]) == ("logo", "k1-r1", "B") and [(v["key"], v["file"]) for v in o["variants"]] == [("A", "a.png"), ("C", "c.png")]
    assert "others" not in rows["assets/other.png"]


def test_the_changed_since_a_commit_are_marked_with_their_goal_and_the_gone_listed(repo):
    since = put(repo, {"art/hero.png": PNG, "art/old.png": PNG, "sfx/hit.wav": pf.wav(0.3)})
    land_files(repo, "dark-mode", "k1", {"art/hero.png": pf.png(8, 8), "art/new.svg": pf.svg()})
    git(repo, "rm", "-q", "art/old.png")
    git(repo, "commit", "-q", "-m", "my own: the old one goes")
    got = art_map.read(state(repo), repo, since)
    assert got["since"] == since
    marks = {a["id"]: (a["change"], a["goal"]) for k in got["kinds"] for a in k["assets"] if a["change"]}
    assert marks == {"art/hero.png": ("changed", "dark-mode"), "art/new.svg": ("added", "dark-mode")}
    assert [(r["id"], r["kind"], r["goal"]) for r in got["removed"]] == [("art/old.png", "art", "")]


# -- the weight, the kinds' bytes and the budget (docs/specs/117-each-lens-a-games-shape.md §3) ------------------------------------------

KB, MB = 1024, 1024 * 1024


def sized(head: bytes, size: int) -> bytes:
    """A file's header padded with zeros to exactly `size` bytes."""
    return head + b"\x00" * (size - len(head))


def weights(got: dict) -> dict[str, str]:
    return {a["id"]: a["weight"] for k in got["kinds"] for a in k["assets"]}


def test_a_picture_weighs_light_normal_or_heavy_at_the_edges_of_100_kb_and_1_mb(repo):
    put(repo, {"a/tiny.png": PNG, "a/under.png": sized(PNG, 100 * KB - 1), "a/at.png": sized(PNG, 100 * KB), "a/near.png": sized(PNG, MB - 1), "a/big.png": sized(PNG, MB)})
    assert weights(art_map.read(state(repo), repo)) == {"a/tiny.png": "light", "a/under.png": "light", "a/at.png": "normal", "a/near.png": "normal", "a/big.png": "heavy"}


def test_a_sound_is_heavy_at_1_mb_and_music_clips_fonts_never_are(repo):
    put(repo, {"s/near.wav": sized(pf.wav(0.1), MB - 1), "s/big.wav": sized(pf.wav(0.1), MB), "s/small.wav": pf.wav(0.1), "m/long.wav": sized(pf.wav(12, rate=200), 3 * MB),
               "c/long.mp4": sized(pf.mp4(seconds=1), 3 * MB), "f/Big.ttf": sized(b"\x00\x01\x00\x00font", 3 * MB), "m/small.wav": pf.wav(12, rate=200)})
    got = art_map.read(state(repo), repo)
    kinds = {a["id"]: k["kind"] for k in got["kinds"] for a in k["assets"]}
    assert weights(got)["s/near.wav"] == "normal" and weights(got)["s/big.wav"] == "heavy" and weights(got)["s/small.wav"] == "light"
    assert (kinds["c/long.mp4"], weights(got)["c/long.mp4"], kinds["f/Big.ttf"], weights(got)["f/Big.ttf"]) == ("clip", "normal", "font", "normal")
    assert (kinds["m/long.wav"], weights(got)["m/long.wav"], weights(got)["m/small.wav"]) == ("music", "normal", "light") and list(weights(got).values()).count("heavy") == 1


def test_a_kind_has_the_bytes_of_its_assets(game):
    got = art_map.read(state(game), game)
    for kind in ("art", "sound", "music", "clip", "font"):
        assert lane(got, kind)["bytes"] == sum(a["bytes"] for a in lane(got, kind)["assets"]) > 0
    assert lane(got, "art")["bytes"] == sum(len(pf.png(n + 1, 2)) for n in range(4)) + 2 * len(PNG)


def test_a_kind_with_nothing_in_it_has_no_bytes(repo):
    put(repo, {"music/theme.wav": pf.wav(12, rate=200)})
    got = art_map.read(state(repo), repo)
    assert (lane(got, "art")["bytes"], lane(got, "sound")["bytes"]) == (0, 0) and lane(got, "music")["bytes"] > 0


def budgeted(repo: Path, toml: str) -> dict | None:
    (repo / "orkcraft.toml").write_text(toml, encoding="utf-8")
    return art_map.read(state(repo), repo)["budget"]


def test_the_budget_is_the_art_kinds_sum_against_the_toml_in_bytes_and_none_without_one(repo):
    put(repo, {"a/one.png": sized(PNG, 300 * KB), "s/hit.wav": sized(pf.wav(0.1), 200 * KB), "f/x.ttf": sized(b"\x00\x01\x00\x00font", 400 * KB)})
    assert art_map.read(state(repo), repo)["budget"] is None                                    # no orkcraft.toml
    assert budgeted(repo, "[art]\nbudget_mb = 2\n") == {"bytes": 500 * KB, "of": 2 * MB}          # the font is not Art's
    assert budgeted(repo, "[art]\nbudget_mb = 0.5\n") == {"bytes": 500 * KB, "of": MB // 2}


def test_no_budget_when_it_is_not_a_number_above_zero_or_the_file_does_not_parse(repo):
    put(repo, {"a/one.png": PNG})
    for toml in ("", "[gate]\nalways = []\n", "[art]\n", "[art]\nbudget_mb = 0\n", "[art]\nbudget_mb = -3\n", '[art]\nbudget_mb = "10"\n', "[art]\nbudget_mb = true\n",
                 "art = 5\n", "[art\nbudget_mb = = 10\n"):
        assert budgeted(repo, toml) is None, toml
    (repo / "orkcraft.toml").write_bytes(b"\xff\xfe[art]\nbudget_mb = 2\n")                       # not text at all
    assert art_map.read(state(repo), repo)["budget"] is None
    assert art_map.read(state(repo), repo, ref="no-such")["budget"] is None


# -- the text ---------------------------------------------------------------------------------------------------------------------------

def test_the_text_counts_the_kinds_by_folder_in_words_and_is_the_same_bytes_for_the_same_dev(game):
    text = art_map.text(state(game), game)
    assert text == art_map.text(state(game), game) == art_map.text(state(game), game, "")
    assert text.startswith(f"The map of Art's assets at dev {git(game, 'rev-parse', 'dev')[:7]}\n\nPictures (6):\n")
    for line in ("- ./: 1 picture", "- icons/: 1 picture", "- sprites/: 4 pictures", "Sounds (2):", "- game/sfx/: 2 sounds", "Music (1):", "- music/: 1 music track",
                 "Clips (1):", "- clips/: 1 clip", "Fonts (1):", "- fonts/: 1 font"):
        assert line in text.split("\n"), line
    assert text.index("Pictures") < text.index("Sounds") < text.index("Music") < text.index("Clips") < text.index("Fonts") and "Picked" not in text
    put(game, {"README.md": b"# changed\n"})                                      # a head that changed no asset: only the head line differs
    assert art_map.text(state(game), game).split("\n", 1)[1] == text.split("\n", 1)[1]


def test_nothing_to_read_when_dev_holds_no_asset(repo):
    assert art_map.text(state(repo), repo).endswith("\n\nNothing to read yet: the project's pictures, sounds, music and clips.")


def test_the_picks_lines_and_the_changed_since_with_the_goal_and_by_you(repo, tmp_path):
    s = state(repo)
    pick = pf.make_pick(s, tmp_path / "v", {"a.png": pf.png(2, 2), "b.png": pf.png(3, 3), "c.png": pf.png(4, 4)}, slug="logo")
    idea_pick.answer(s, "logo", pick, "B", "")
    (ideas.state_folder(s, "logo") / "plan.json").write_text(json.dumps({"tasks": [pf.task(3, state="merged")]}))
    since = put(repo, {"assets/logo.png": pf.png(3, 3), "art/hero.png": PNG, "art/old.png": PNG})
    land_files(repo, "dark-mode", "k1", {"art/hero.png": pf.png(8, 8), "art/new.svg": pf.svg()})
    git(repo, "rm", "-q", "art/old.png")
    git(repo, "commit", "-q", "-m", "mine")
    text = art_map.text(s, repo, since)
    assert "Picked (the variants not picked lie under the one picked):\n- assets/logo.png: picked from 3 variants, 2 not picked" in text
    changed = text.split("Changed since your last call:\n")[1].split("\n")
    assert changed == ["- new picture art/new.svg (goal dark-mode)", "- changed picture art/hero.png (goal dark-mode)", "- gone picture art/old.png (by you)"]
    assert art_map.text(s, repo, "nonsense").endswith("Changed since your last call: not known (that commit is not in dev).")
    assert art_map.text(s, repo, git(repo, "rev-parse", "dev")).endswith("Changed since your last call: nothing.")


def test_the_text_is_bounded_and_says_how_many_lines_it_left_out(repo):
    put(repo, {f"folder{n:04d}/pic.png": pf.png(2, 2) for n in range(400)})
    text = art_map.text(state(repo), repo)
    assert len(text) <= map_text.LIMIT and text.splitlines()[-1].startswith("- and ") and text.splitlines()[-1].endswith(" more lines: read further what you need")
    assert text == art_map.text(state(repo), repo)


# -- ideas.art_map ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo):
    git(fake_repo, "branch", "dev")
    h = Orkboard(fake_repo)
    if not isinstance(h.ideas, MapsMixin):                                       # wired by the lead: the host's bases and its table
        h.ideas.__class__ = type("IdeasWithMaps", (MapsMixin, type(h.ideas)), {})
        h.commands.update(maps_commands(h.ideas))
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_command_answers_the_map_with_its_assets_signed(host, fake_repo):
    put(fake_repo, {"art/hero.png": PNG})
    git(fake_repo, "branch", "-f", "dev", "HEAD")
    got = host.command("ideas.art_map", {})
    art = lane(got, "art")
    assert [a["id"] for a in art["assets"]] == ["art/hero.png"] and art["assets"][0]["url"] and got["goals"] == {}
    assert got["commit"] == git(fake_repo, "rev-parse", "dev") and host.command("ideas.art_map", {"since": got["commit"]})["since"] == got["commit"]
