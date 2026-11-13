"""Spec 109 B (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §3): `realm/map_signals_crafts.py`, what the maps of Art, Release and Marketing say is wrong by code. Each kind is shown
firing on a small git project made here and not firing where its rule does not hold: Art's mixed sizes, odd names, heavy files and unused assets; Release's big batch, stale goal, goal left out, missing
changelog and reverts; Marketing's missing channel, long store title and short text, missing screenshots, onboarding, way back, way to share and way to earn. Every `on` is a part of the craft's map or "".
Real git repositories (tests/test_commit_goal.py's: main at the start, dev ahead), no model."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from orkboard.realm import map_parts, map_signals, map_signals_crafts as crafts, release_map
from tests import pick_files as pf
from tests.test_assets import put
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)
from tests.test_release_map import goal


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    return tmp_path / "pages"


def kinds(got: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in got:
        out.setdefault(s["kind"], []).append(s["on"])
    return out


def parts_of(repo: Path, craft: str, pages: Path | None = None) -> set[str]:
    return {p["id"] for p in map_parts.parts(state(repo), repo, craft, pages)} | {""}


# -- Art ---------------------------------------------------------------------------------------------------------------------------

def test_a_folder_of_pictures_of_four_sizes_or_more_is_mixed_and_three_sizes_are_not(repo):
    put(repo, {**{f"sprites/s{n}.png": pf.png(16 * (n + 1), 16 * (n + 1)) for n in range(crafts.MIXED_SIZES)}, **{f"icons/i{n}.png": pf.png(8 * (n + 1), 8) for n in range(3)}})
    got = crafts.art(state(repo), repo)
    assert kinds(got) == {"mixed_sizes": ["sprites/s0.png"]}
    assert got[0]["words"] == "sprites/ holds pictures of 4 sizes: 16×16, 32×32, 48×48, …" and got[0]["on"] in parts_of(repo, "art")


def test_an_asset_no_source_file_names_is_unused_and_a_project_with_no_source_has_none_unused(repo):
    put(repo, {"art/hero.png": pf.png(4, 4), "art/orphan.png": pf.png(4, 4), "game/sfx/jump.wav": pf.wav(0.5), "art/logo.svg": pf.svg(8, 8), "README.md": b"orphan.png is in the readme"})
    assert crafts.art(state(repo), repo) == [], "no source file at all: nothing to be named by"
    put(repo, {"src/game.js": b"load('art/hero.png'); play('jump.wav');\n", "index.html": b'<img src="art/logo.svg">\n'})
    got = crafts.art(state(repo), repo)
    assert kinds(got) == {"unused": ["art/orphan.png"]} and got[0]["words"] == "No source file names orphan.png (art/orphan.png)"
    put(repo, {"src/more.css": b".x { background: url(orphan.png) }\n"})
    assert crafts.art(state(repo), repo) == []
    assert crafts.UNUSED_NAMES == 200


# -- Release -----------------------------------------------------------------------------------------------------------------------

def test_eight_goals_or_sixty_files_waiting_for_main_are_a_big_batch(repo, pages):
    for n in range(crafts.BATCH_GOALS - 1):
        land(repo, goal(pages, repo, f"Goal {n}"), "k1", {f"f{n}.txt": "x\n"})
    assert "big_batch" not in kinds(crafts.release(state(repo), repo, pages))
    land(repo, goal(pages, repo, "The eighth"), "k1", {"g.txt": "x\n"})
    got = crafts.release(state(repo), repo, pages)
    assert kinds(got)["big_batch"] == [""] and got[0]["words"] == "8 goals and 8 files wait for main: a batch that big is hard to ship and to take back"


def test_dev_with_no_changelog_while_goals_wait_and_one_with_a_changelog(repo, pages):
    land(repo, goal(pages, repo, "Dark mode"), "k1", {"x.css": "x\n"})
    got = crafts.release(state(repo), repo, pages)
    assert kinds(got) == {"no_changelog": [""]} and got[0]["words"] == "dev holds no changelog while 1 goal waits for main"
    for name in ("CHANGELOG.md", "History.txt", "news"):
        commit(repo, name, "1.0: first\n")
        assert crafts.release(state(repo), repo, pages) == [], name
        git(repo, "rm", "-q", name)
        git(repo, "commit", "-q", "-m", "drop it")
    commit(repo, "docs/CHANGELOG.md", "1.0: first\n")
    assert "no_changelog" in kinds(crafts.release(state(repo), repo, pages)), "a changelog below the top is not at its top"


# -- Marketing ---------------------------------------------------------------------------------------------------------------------


def test_a_store_title_over_thirty_characters_and_a_short_text_over_eighty(repo):
    fit, long = "x" * crafts.TITLE_MAX, "x" * (crafts.TITLE_MAX + 1)
    put(repo, {"fastlane/metadata/en-US/title.txt": (fit + "\n").encode(), "fastlane/metadata/en-US/short_description.txt": ("y" * crafts.SHORT_MAX + "\n").encode()})
    assert not {"aso_title", "aso_short"} & set(kinds(crafts.marketing(state(repo), repo)))
    put(repo, {"fastlane/metadata/en-US/title.txt": (long + "\n").encode(), "fastlane/metadata/de-DE/name.txt": (long + "\n").encode(),
               "fastlane/metadata/en-US/short_description.txt": ("y" * (crafts.SHORT_MAX + 1) + "\n").encode(), "fastlane/metadata/de-DE/subtitle.txt": b"short\n"})
    got = crafts.marketing(state(repo), repo)
    found = kinds(got)
    assert found["aso_title"] == ["fastlane/metadata/de-DE/name.txt", "fastlane/metadata/en-US/title.txt"] and found["aso_short"] == ["fastlane/metadata/en-US/short_description.txt"]
    assert next(s for s in got if s["kind"] == "aso_title")["words"] == "fastlane/metadata/de-DE/name.txt is 31 characters long, and the App Store cuts a title at 30"
    assert next(s for s in got if s["kind"] == "aso_short")["words"] == "fastlane/metadata/en-US/short_description.txt is 81 characters long, and Google Play cuts a short description at 80"
    assert {s["on"] for s in got} <= parts_of(repo, "marketing")


def test_a_first_session_with_no_onboarding_file_is_on_its_file(repo):
    put(repo, {"src/App.tsx": b"export default () => null;\n"})
    got = crafts.marketing(state(repo), repo)
    assert kinds(got)["no_onboarding"] == ["src/App.tsx"] and {s["on"] for s in got} <= parts_of(repo, "marketing")
    for name in ("src/Onboarding.tsx", "tutorial/step.md", "src/welcome.js", "docs/Intro.md", "walkthrough.json"):
        put(repo, {name: b"x"})
        assert "no_onboarding" not in kinds(crafts.marketing(state(repo), repo)), name
        git(repo, "rm", "-q", name)
        git(repo, "commit", "-q", "-m", "drop")


def test_a_way_back_is_a_notification_a_push_a_daily_reward_or_a_streak(repo):
    put(repo, {"src/a.js": b"list.push(1);\npushed = 2;\nconst x = 'unpushed';\n"})
    assert "no_return" in kinds(crafts.marketing(state(repo), repo)), "an array's push is no push notification"
    for n, text in enumerate((b"registerForNotifications();", b"const STREAK = 3;", b"giveDailyReward();", b"git push origin", b"await push.subscribe(); ")):
        put(repo, {"src/b.js": text}, f"b {n}")
        assert "no_return" not in kinds(crafts.marketing(state(repo), repo)), text
    put(repo, {"src/b.js": b"x = 1;"})
    assert "no_return" in kinds(crafts.marketing(state(repo), repo)) and crafts.RETURN


def test_the_signals_dispatch_each_craft_to_this_module_and_keep_the_limit(repo, pages):
    put(repo, {"art/hero.png": pf.png(4, 4)})
    for craft, fn in (("art", crafts.art), ("marketing", crafts.marketing)):
        assert map_signals.signals(state(repo), repo, craft, pages) == fn(state(repo), repo)[:map_signals.MAX_SIGNALS]
    land(repo, goal(pages, repo, "Dark mode"), "k1", {"x.css": "x\n"})
    assert map_signals.signals(state(repo), repo, "release", pages) == crafts.release(state(repo), repo, pages) != []
    put(repo, {f"ui/{n}.png": pf.png(4, 4) for n in range(40)} | {"ui/Odd Name.png": pf.png(4, 4), "src/a.js": b"x"})
    put(repo, {f"ui/Big{n}.png": pf.png(4, 4) for n in range(30)} | {f"ui/low{n}.png": pf.png(4, 4) for n in range(100)})
    assert len(map_signals.signals(state(repo), repo, "art")) == map_signals.MAX_SIGNALS
