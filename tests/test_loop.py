"""Spec 102 B (docs/specs/102-the-other-maps-and-picking-on-them.md §2; decisions §112.8, §156.3): Game design's loop as code reads it, `realm/loop.py`: four to six cards kept in
`<state_dir>/loop.json`, names and lines bounded, a card's `rests_on` only files and folders of dev's tree, the configs chosen by code (`balance*`, `config/`, `levels/`, `*.config.*`),
the leader's answer taken strictly, the text in order and the same bytes for the same record and dev. Real git repositories (tests/test_commit_goal.py's), no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import loop
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)


def card(name, line="A line", rests_on=(), **more):
    return {"name": name, "line": line, "rests_on": list(rests_on), **more}


FOUR = [card("Spawn"), card("Fight"), card("Loot"), card("Upgrade")]


@pytest.fixture
def game(repo: Path) -> Path:
    """A small game on dev: a balance file, a config folder, levels, a build config and the code."""
    for name, text in {"config/balance.json": '{"hp": 10,\n "dmg": 3}\n', "config/waves.yml": "waves: 5\n", "levels/one.json": '{"name": "one"}\n', "levels/two.json": "{}\n",
                       "vite.config.ts": "export default {}\n", "src/balance_curve.ts": "export const a = 1\n", "src/game.ts": "export const g = 2\n", "README.md": "# Game\n",
                       "assets/hero.png": "png"}.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "the game")
    return repo


# -- the cards kept -----------------------------------------------------------------------------------------------------------------

def test_nothing_is_kept_before_a_loop_and_four_to_six_cards_are_kept_in_order_with_who_kept_them(game):
    s = state(game)
    assert loop.read(s) == [] and loop.text(s, game) is None
    kept, dropped = loop.keep(s, game, [card("Spawn", "Enemies come", ["config/waves.yml"]), card("Fight"), card("Loot"), card("Upgrade", "Spend the loot", ["config/balance.json", "levels"])], "leader")
    assert dropped == [] and [c["id"] for c in kept] == ["spawn", "fight", "loot", "upgrade"]
    assert kept[0] == {"id": "spawn", "name": "Spawn", "line": "Enemies come", "rests_on": ["config/waves.yml"], "by": "leader", "at": kept[0]["at"]} and kept[0]["at"]
    assert kept[3]["rests_on"] == ["config/balance.json", "levels"]                    # a file, and a folder of dev's tree
    assert loop.read(s) == kept and json.loads((s / "loop.json").read_text())["cards"] == kept


def test_the_count_the_names_and_the_lines_are_bounded_and_refused_in_plain_words(game):
    s = state(game)
    for bad, why in (([card("A"), card("B"), card("C")], "4 to 6 cards"), ([card(str(n)) for n in range(7)], "4 to 6 cards"), ("no", "4 to 6 cards"), (None, "4 to 6 cards"),
                     ([*FOUR[:3], "no"], "a name, a line"), ([*FOUR[:3], card("")], "a name and a line"), ([*FOUR[:3], card("Loot2", "")], "a name and a line"),
                     ([*FOUR[:3], card("fight")], "Two cards are named fight"), ([*FOUR[:3], {"name": "X", "line": "l", "rests_on": "config/balance.json"}], "list of files")):
        with pytest.raises(ValueError, match=why):
            loop.keep(s, game, bad, "person")
    with pytest.raises(ValueError, match="person or the leader"):
        loop.keep(s, game, FOUR, "model")
    assert loop.read(s) == []                                                           # a refusal keeps nothing
    kept, _ = loop.keep(s, game, [card("N" * 100, "word  " * 100), *FOUR[1:]], "person")
    assert len(kept[0]["name"]) == loop.NAME_CHARS and len(kept[0]["line"]) <= loop.LINE_CHARS and "  " not in kept[0]["line"]


def test_a_card_rests_only_on_files_and_folders_of_devs_tree_the_rest_is_dropped_and_said(game):
    s = state(game)
    (game / "later.ts").write_text("x")                                                # in the working tree, not on dev
    ask = ["config/balance.json", "./config/balance.json", "levels/", "nope.ts", "later.ts", "../x", "/etc/passwd", ".env", "config\\waves.yml", 7, "src/game.ts", "src/game.ts"]
    kept, dropped = loop.keep(s, game, [card("Spawn", rests_on=ask), *FOUR[1:]], "person")
    assert kept[0]["rests_on"] == ["config/balance.json", "levels", "config/waves.yml", "src/game.ts"]
    assert dropped == [{"name": "Spawn", "path": p} for p in ("nope.ts", "later.ts", "../x", "/etc/passwd", ".env")]
    many = [f"levels/{n}.json" for n in ("one", "two")] + ["config/balance.json", "config/waves.yml", "src/game.ts", "src/balance_curve.ts", "README.md"]
    assert len(loop.keep(s, game, [card("Spawn", rests_on=many), *FOUR[1:]], "person")[0][0]["rests_on"]) == loop.PATHS


def test_a_project_with_no_dev_keeps_no_path(tmp_path):
    r = tmp_path / "plain"
    r.mkdir()
    git(r, "init", "-b", "main")
    (r / "a.json").write_text("{}")
    kept, dropped = loop.keep(r / ".orkcraft", r, [card("Spawn", rests_on=["a.json"]), *FOUR[1:]], "person")
    assert kept[0]["rests_on"] == [] and dropped == [{"name": "Spawn", "path": "a.json"}] and loop.config_files(r) == [] and loop.tree(r) == {}


def test_a_card_kept_again_unchanged_keeps_its_leader_and_time_one_changed_is_the_persons(game):
    s = state(game)
    first, _ = loop.keep(s, game, [card("Spawn", "Enemies come"), *FOUR[1:]], "leader")
    again, _ = loop.keep(s, game, [{**first[0]}, {**first[1], "line": "Changed by the person"}, first[2], {"name": "Grow", "line": "New"}], "person")
    assert [c["by"] for c in again] == ["leader", "person", "leader", "person"] and again[0]["at"] == first[0]["at"] and again[2]["at"] == first[2]["at"]
    assert [c["id"] for c in again] == ["spawn", "fight", "loot", "grow"]               # an id stays; a new card has a name's
    renamed, _ = loop.keep(s, game, [{**first[0], "name": "Spawn"}, {**again[1], "name": "Fight"}, again[2], {"name": "Fight", "line": "Two ids", "id": "fight"}][:3] + [card("Zed", id="loot")], "person")
    assert len({c["id"] for c in renamed}) == 4                                          # no two cards share an id


def test_a_file_that_is_not_of_the_shape_reads_as_nothing(game):
    s = state(game)
    s.mkdir(exist_ok=True)
    (s / "loop.json").write_text(json.dumps({"cards": [{"id": "ok", "name": "A", "line": "b", "rests_on": ["x/../y", "z"], "by": "robot"}, {"id": "Bad Id", "name": "B", "line": "c"},
                                                       "no", {"id": "n", "name": "", "line": "c"}]}))
    assert loop.read(s) == [{"id": "ok", "name": "A", "line": "b", "rests_on": ["z"], "by": "person", "at": ""}]
    (s / "loop.json").write_text("not json")
    assert loop.read(s) == [] and loop.proposal(s) == {"status": "", "error": "", "at": ""}


def test_the_proposal_is_kept_beside_the_cards_and_forgotten_by_an_empty_status(game):
    s = state(game)
    loop.save_proposal(s, "asking")
    assert loop.proposal(s)["status"] == "asking" and loop.read(s) == []
    loop.save_proposal(s, "failed", "Game  design did not answer: try again")
    assert loop.proposal(s)["status"] == "failed" and loop.proposal(s)["error"] == "Game design did not answer: try again"
    loop.keep(s, game, FOUR, "leader")
    assert loop.proposal(s)["status"] == "failed" and len(loop.read(s)) == 4            # the cards do not forget the proposal, nor it them
    loop.save_proposal(s, "")
    assert loop.proposal(s)["status"] == "" and len(loop.read(s)) == 4


# -- the leader's answer, strictly -------------------------------------------------------------------------------------------------

def test_the_leaders_answer_is_four_to_six_cards_each_with_a_name_and_a_line(game):
    good = {"cards": [card("Spawn", "Enemies come", ["config/waves.yml", "ghost.ts"]), card("Fight", rests_on=["levels"]), card("Loot"), {"name": "Upgrade", "line": "Spend"}]}
    got = loop.parse(good, game)
    assert got == [{"name": "Spawn", "line": "Enemies come", "rests_on": ["config/waves.yml"]}, {"name": "Fight", "line": "A line", "rests_on": ["levels"]},
                   {"name": "Loot", "line": "A line", "rests_on": []}, {"name": "Upgrade", "line": "Spend", "rests_on": []}]
    for bad in (None, "text", {}, {"cards": "no"}, {"cards": FOUR[:3]}, {"cards": [card(str(n)) for n in range(7)]}, {"cards": [*FOUR[:3], {"name": "x"}]},
                {"cards": [*FOUR[:3], "no"]}, {"cards": [*FOUR[:3], card("Spawn")]}, {"cards": [*FOUR[:3], {"name": "Z", "line": "l", "rests_on": "config/waves.yml"}]}):
        assert loop.parse(bad, game) is None
    assert loop.parse({"cards": [{**c, "id": "x"} for c in FOUR]}, game) is not None    # an id of the model's is none: it is made at keeping


# -- the configs, chosen by code ---------------------------------------------------------------------------------------------------

def test_the_configs_are_balance_then_config_levels_and_dot_config_files_of_devs_tree(game):
    (game / "node_modules" / "pkg").mkdir(parents=True)
    (game / "node_modules" / "pkg" / "balance.json").write_text("{}")
    (game / "config" / "secrets.env").write_text("KEY=1")
    (game / "config" / "big.png").write_text("png")
    (game / "dist").mkdir()
    (game / "dist" / "app.config.js").write_text("x")
    git(game, "add", "-Af")
    git(game, "commit", "-q", "-m", "more")
    (game / "untracked.config.js").write_text("x")                                      # not on dev
    assert loop.config_files(game) == ["config/balance.json", "src/balance_curve.ts", "config/waves.yml", "levels/one.json", "levels/two.json", "vite.config.ts"]
    assert loop.config_files(game) == loop.config_files(game)                          # the same for the same dev


def test_the_configs_are_bounded_by_their_number_and_by_a_folders(game):
    for n in range(30):
        (game / "levels" / "deep" / f"l{n:02}.json").parent.mkdir(parents=True, exist_ok=True)
        (game / "levels" / "deep" / f"l{n:02}.json").write_text("{}")
        (game / f"area{n}").mkdir(exist_ok=True)
        (game / f"area{n}" / "balance.json").write_text("{}")
    git(game, "add", "-A")
    git(game, "commit", "-q", "-m", "many")
    got = loop.config_files(game)
    assert len(got) == loop.CONFIGS and sum(p.startswith("levels/deep/") for p in got) <= loop.PER_FOLDER


def test_the_first_lines_of_the_first_configs_are_read_bounded_from_dev(game):
    (game / "config" / "long.json").write_text("\n".join(f'"k{n}": "{"v" * 200}"' for n in range(50)))
    (game / "config" / "huge.json").write_text("x" * (loop.READ_BYTES + 1))
    (game / "config" / "bin.json").write_bytes(b"\0\1\2")
    git(game, "add", "-A")
    git(game, "commit", "-q", "-m", "more")
    (game / "config" / "balance.json").write_text("EDITED, NOT ON DEV")
    got = loop.heads(game, ["config/balance.json", "config/long.json", "config/huge.json", "config/bin.json", "ghost.json", ".env"])
    assert got["config/balance.json"] == '{"hp": 10,\n "dmg": 3}'                       # dev's, not the working tree's
    assert len(got["config/long.json"]) <= loop.HEAD_CHARS and got["config/long.json"].endswith("…")
    assert set(got) == {"config/balance.json", "config/long.json"}                      # too large, binary, not on dev: not read
    assert sum(len(t) for t in loop.heads(game, loop.config_files(game) * 2).values()) <= loop.HEAD_TOTAL and len(loop.heads(game, [f"config/{n}" for n in range(30)])) == 0


# -- its text ------------------------------------------------------------------------------------------------------------------------

def test_the_text_is_the_cards_in_order_each_its_name_its_line_and_what_it_rests_on(game):
    s = state(game)
    loop.keep(s, game, [card("Spawn", "Enemies come in waves", ["config/waves.yml"]), card("Fight", "Hit and dodge", ["config/balance.json", "levels", "src/game.ts", "vite.config.ts"]),
                        card("Loot"), card("Upgrade", "Spend the loot")], "leader")
    text = loop.text(s, game)
    assert text == f"""The map of the loop at dev {git(game, 'rev-parse', 'dev')[:7]}

1. Spawn: Enemies come in waves
   Rests on: config/waves.yml
2. Fight: Hit and dodge
   Rests on: config/balance.json, levels, src/game.ts, +1
3. Loot: A line
   Rests on: no file named
4. Upgrade: Spend the loot
   Rests on: no file named"""


def test_the_same_record_and_dev_are_the_same_bytes_and_a_later_head_changes_only_its_line(game):
    s = state(game)
    loop.keep(s, game, FOUR, "leader")
    one = loop.text(s, game)
    assert loop.text(s, game) == one == loop.text(s, game, "")
    commit(game, "README.md", "# Game, changed\n")
    two = loop.text(s, game)
    assert two != one and two.split("\n", 1)[1] == one.split("\n", 1)[1]


def test_the_text_is_bounded_whatever_the_cards_hold(game):
    s = state(game)
    deep = "/".join(["d" * 30] * 6)
    (game / deep).mkdir(parents=True)
    names = []
    for n in range(6):
        (game / deep / f"{'f' * 30}{n}.json").write_text("{}")
        names.append(f"{deep}/{'f' * 30}{n}.json")
    git(game, "add", "-A")
    git(game, "commit", "-q", "-m", "deep")
    loop.keep(s, game, [card(f"{n}" * 40, "l" * 160, names) for n in range(6)], "person")
    text = loop.text(s, game)
    assert len(text) <= loop.LIMIT and all(f"{n}. " in text for n in range(1, 7))


def test_with_since_the_text_ends_with_what_changed_under_the_cards_files_and_the_goal_that_changed_it(game):
    s = state(game)
    loop.keep(s, game, [card("Spawn", rests_on=["config/waves.yml"]), card("Fight", rests_on=["config/balance.json", "levels"]), card("Loot"), card("Upgrade")], "leader")
    before = git(game, "rev-parse", "dev")
    base = loop.text(s, game, before)
    assert base.endswith("Changed under the loop since your last call: nothing.") and base.startswith(loop.text(s, game))
    land(game, "tougher-waves", "k1", {"config/waves.yml": "waves: 9\n", "src/game.ts": "export const g = 3\n"})
    commit(game, "levels/three.json", "{}\n", "my own level")
    got = loop.text(s, game, before)
    assert got.rsplit("\n\n", 1)[1] == "Changed under the loop since your last call:\n- Spawn: config/waves.yml (goal tougher-waves)\n- Fight: levels/three.json (by you)"
    assert "src/game.ts" not in got                                                     # a file no card rests on is not said
    assert loop.text(s, game, "not a commit").endswith("Changed under the loop since your last call: not known (no map was kept at that commit).")
