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


def test_a_name_with_a_space_or_a_capital_where_most_names_are_lower_case_with_none(repo):
    put(repo, {"ui/a.png": pf.png(4, 4), "ui/b.png": pf.png(4, 4), "ui/Big Button.png": pf.png(4, 4), "ui/Hero.png": pf.png(4, 4), "ui/c.png": pf.png(4, 4),
               "mixed/One.png": pf.png(4, 4), "mixed/two.png": pf.png(4, 4), "caps/A.png": pf.png(4, 4), "caps/B.png": pf.png(4, 4), "caps/c.png": pf.png(4, 4)})
    got = crafts.art(state(repo), repo)
    assert kinds(got) == {"naming": ["ui/Big Button.png", "ui/Hero.png"]}, "mixed/ is half and half, caps/ is mostly capitals: no convention to break"
    assert got[0]["words"] == "ui/Big Button.png has a space or a capital in its name, where the names of ui/ are lower-case with none"
    assert {s["on"] for s in got} <= parts_of(repo, "art")


def test_a_picture_or_a_sound_of_a_megabyte_is_heavy_and_a_music_track_is_not(repo):
    megabyte = b"\0" * crafts.HEAVY_ART
    put(repo, {"art/huge.png": pf.png(4, 4) + megabyte, "art/ok.png": pf.png(4, 4) + b"\0" * (crafts.HEAVY_ART - 1000), "game/sfx/boom.wav": pf.wav(0.5) + megabyte, "game/sfx/tick.wav": pf.wav(0.5),
               "music/theme.wav": pf.wav(12, rate=200) + megabyte})
    got = crafts.art(state(repo), repo)
    assert kinds(got) == {"heavy": ["art/huge.png", "game/sfx/boom.wav"]}
    assert [s["words"] for s in got] == ["art/huge.png is 1.0 MB: a picture that heavy slows the load", "game/sfx/boom.wav is 1.0 MB: a sound that heavy slows the load"]
    assert {s["on"] for s in got} <= parts_of(repo, "art")


def test_an_asset_no_source_file_names_is_unused_and_a_project_with_no_source_has_none_unused(repo):
    put(repo, {"art/hero.png": pf.png(4, 4), "art/orphan.png": pf.png(4, 4), "game/sfx/jump.wav": pf.wav(0.5), "art/logo.svg": pf.svg(8, 8), "README.md": b"orphan.png is in the readme"})
    assert crafts.art(state(repo), repo) == [], "no source file at all: nothing to be named by"
    put(repo, {"src/game.js": b"load('art/hero.png'); play('jump.wav');\n", "index.html": b'<img src="art/logo.svg">\n'})
    got = crafts.art(state(repo), repo)
    assert kinds(got) == {"unused": ["art/orphan.png"]} and got[0]["words"] == "No source file names orphan.png (art/orphan.png)"
    put(repo, {"src/more.css": b".x { background: url(orphan.png) }\n"})
    assert crafts.art(state(repo), repo) == []
    assert crafts.UNUSED_NAMES == 200


def test_an_art_map_with_no_dev_or_nothing_in_it_has_no_hints(repo, tmp_path):
    assert crafts.art(state(repo), repo) == [] and crafts.art(state(repo), repo, "no-such") == []
    bare = tmp_path / "bare"
    bare.mkdir()
    assert crafts.art(state(bare), bare) == []


# -- Release -----------------------------------------------------------------------------------------------------------------------

def test_eight_goals_or_sixty_files_waiting_for_main_are_a_big_batch(repo, pages):
    for n in range(crafts.BATCH_GOALS - 1):
        land(repo, goal(pages, repo, f"Goal {n}"), "k1", {f"f{n}.txt": "x\n"})
    assert "big_batch" not in kinds(crafts.release(state(repo), repo, pages))
    land(repo, goal(pages, repo, "The eighth"), "k1", {"g.txt": "x\n"})
    got = crafts.release(state(repo), repo, pages)
    assert kinds(got)["big_batch"] == [""] and got[0]["words"] == "8 goals and 8 files wait for main: a batch that big is hard to ship and to take back"


def test_sixty_files_in_one_commit_are_a_big_batch_too(repo, pages):
    put(repo, {f"d/f{n}.txt": b"x\n" for n in range(crafts.BATCH_FILES - 1)}, "files")
    assert "big_batch" not in kinds(crafts.release(state(repo), repo, pages))
    put(repo, {"d/last.txt": b"x\n"}, "one more")
    assert kinds(crafts.release(state(repo), repo, pages))["big_batch"] == [""]


def test_a_goal_whose_commit_is_a_week_old_is_stale(repo, pages, monkeypatch):
    old = (dt.datetime.now() - dt.timedelta(days=crafts.STALE_DAYS + 3)).isoformat(timespec="seconds")
    one, two = goal(pages, repo, "Dark mode"), goal(pages, repo, "Faster pages")
    monkeypatch.setenv("GIT_COMMITTER_DATE", old)
    monkeypatch.setenv("GIT_AUTHOR_DATE", old)
    land(repo, one, "k1", {"x.css": "x\n"})
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    monkeypatch.delenv("GIT_AUTHOR_DATE")
    land(repo, two, "k1", {"y.css": "y\n"})
    got = crafts.release(state(repo), repo, pages)
    assert kinds(got) == {"stale": [one], "no_changelog": [""]}
    assert next(s for s in got if s["kind"] == "stale")["words"] == "Dark mode landed 10 days ago and still waits for main"
    assert {s["on"] for s in got} <= parts_of(repo, "release", pages)


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


def test_changes_waiting_for_main_that_were_reverts(repo, pages):
    commit(repo, "CHANGELOG.md", "x\n")
    land(repo, goal(pages, repo, "Dark mode"), "k1", {"x.css": "x\n"})
    assert crafts.release(state(repo), repo, pages) == []
    commit(repo, "y.txt", "y\n", 'Revert "Add y"')
    commit(repo, "z.txt", "z\n", "Revert the z change")
    commit(repo, "w.txt", "w\n", "Add w, which reverts nothing")
    got = crafts.release(state(repo), repo, pages)
    assert kinds(got) == {"reverts": [""]} and got[0]["words"] == '2 changes waiting for main were reverts: Revert the z change; Revert "Add y"'


def test_no_gate_or_nothing_waiting_or_no_dev_has_no_release_hints(repo, pages):
    assert crafts.release(state(repo), repo, pages) == [] and crafts.release(state(repo), repo, pages, "main") == [] and crafts.release(state(repo), repo, pages, "no-such") == []
    land(repo, goal(pages, repo, "Dark mode"), "k1", {"x.css": "x\n"})
    git(repo, "branch", "-f", "main", "dev")
    assert crafts.release(state(repo), repo, pages) == []


# -- Marketing ---------------------------------------------------------------------------------------------------------------------

def test_a_way_in_with_nothing_in_it_says_all_the_code_can_say(repo):
    put(repo, {"README.md": b"# hi", "src/lib.py": b"x = 1\n"})
    got = crafts.marketing(state(repo), repo)
    assert [s["kind"] for s in got] == ["no_channel", "no_onboarding", "no_return", "no_share", "no_revenue"] and {s["on"] for s in got} == {""}
    assert crafts.marketing(state(repo), repo, "no-such") == []


def test_a_channel_is_named_by_a_folder_for_reaching_people(repo):
    put(repo, {"src/lib.py": b"x = 1\n"})
    assert "no_channel" in kinds(crafts.marketing(state(repo), repo))
    put(repo, {"press/kit.md": b"x"})
    assert "no_channel" not in kinds(crafts.marketing(state(repo), repo))


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


def test_store_metadata_with_no_screenshots_and_one_with_them(repo):
    put(repo, {"store/listing.md": b"x", "fastlane/metadata/en-US/title.txt": b"Short"})
    got = crafts.marketing(state(repo), repo)
    assert kinds(got)["no_shots"] == ["fastlane/metadata/en-US/title.txt"] and next(s for s in got if s["kind"] == "no_shots")["on"] in parts_of(repo, "marketing")
    put(repo, {"store/screenshots/one.png": pf.png(4, 4)})
    assert "no_shots" not in kinds(crafts.marketing(state(repo), repo))
    git(repo, "rm", "-q", "-r", "store/screenshots")
    git(repo, "commit", "-q", "-m", "drop")
    assert "no_shots" in kinds(crafts.marketing(state(repo), repo))
    put(repo, {"fastlane/screenshots/en-US/1.png": pf.png(4, 4)})
    assert "no_shots" not in kinds(crafts.marketing(state(repo), repo))
    put(repo, {"site/index.html": b"<h1>hi</h1>"})
    assert "no_shots" not in kinds(crafts.marketing(state(repo), repo)), "and a project with no store files has no store to show them in"


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


def test_a_way_to_bring_others_is_sharing_an_invite_or_a_referral(repo):
    put(repo, {"src/a.js": b"const shared = 1;\nconst sharedPreferences = 2;\n"})
    assert "no_share" in kinds(crafts.marketing(state(repo), repo)), "shared state is no share button"
    for n, text in enumerate((b"navigator.share({ url });", b"sendInvite();", b"const referral = code;", b"<ShareButton />", b"share(link)")):
        put(repo, {"src/b.js": text}, f"b {n}")
        assert "no_share" not in kinds(crafts.marketing(state(repo), repo)), text


def test_a_way_to_earn_is_a_payment_library_in_a_manifest(repo):
    put(repo, {"package.json": b'{"dependencies": {"react": "18"}}\n', "src/pay.js": b"stripe.charge();\n"})
    assert "no_revenue" in kinds(crafts.marketing(state(repo), repo)), "only a manifest counts, not a word in the code"
    for n, (name, text) in enumerate((("web/package.json", b'{"dependencies": {"@stripe/stripe-js": "1"}}\n'), ("app/pubspec.yaml", b"dependencies:\n  in_app_purchase: ^3\n"),
                                      ("requirements.txt", b"Paddle-Python\n"), ("app/build.gradle.kts", b'implementation("com.revenuecat.purchases:purchases:7")\n'),
                                      ("Gemfile", b"gem 'pay'\ngem 'PayPal-sdk'\n"))):
        put(repo, {name: text}, f"manifest {n}")
        assert "no_revenue" not in kinds(crafts.marketing(state(repo), repo)), name
        git(repo, "rm", "-q", name)
        git(repo, "commit", "-q", "-m", "drop")
    assert "no_revenue" in kinds(crafts.marketing(state(repo), repo))


def test_the_signals_dispatch_each_craft_to_this_module_and_keep_the_limit(repo, pages):
    put(repo, {"art/hero.png": pf.png(4, 4)})
    for craft, fn in (("art", crafts.art), ("marketing", crafts.marketing)):
        assert map_signals.signals(state(repo), repo, craft, pages) == fn(state(repo), repo)[:map_signals.MAX_SIGNALS]
    land(repo, goal(pages, repo, "Dark mode"), "k1", {"x.css": "x\n"})
    assert map_signals.signals(state(repo), repo, "release", pages) == crafts.release(state(repo), repo, pages) != []
    put(repo, {f"ui/{n}.png": pf.png(4, 4) for n in range(40)} | {"ui/Odd Name.png": pf.png(4, 4), "src/a.js": b"x"})
    put(repo, {f"ui/Big{n}.png": pf.png(4, 4) for n in range(30)} | {f"ui/low{n}.png": pf.png(4, 4) for n in range(100)})
    assert len(map_signals.signals(state(repo), repo, "art")) == map_signals.MAX_SIGNALS
