"""Spec 102 B, spec 107 N (docs/specs/102-the-other-maps-and-picking-on-them.md §2; docs/specs/107-what-the-owners-day-said.md §14; decisions §112.8, §156.3, §182): Game design's loops as code reads
them, `realm/loop.py`: one to three loops (core, session, meta) of three to six steps, the currencies with what gives and takes them, why a player comes back, kept in `<state_dir>/loop.json`;
names and lines bounded, a feeling one of MDA's eight, an intensity clamped to 1–5, a step's `rests_on` only files and folders of dev's tree, a version 1 file read as one core loop, what the loop says
by code, the person's version put aside in `was` when the leader proposes over it, the configs chosen by code (`balance*`, `config/`, `levels/`, `*.config.*`), the leader's answer taken strictly, the text
in order and the same bytes for the same record and dev. Real git repositories (tests/test_commit_goal.py's), no model."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orkboard.realm import loop
from tests.test_commit_goal import commit, git, land, repo, state  # noqa: F401  (the fixture)


def card(name, line="A line", rests_on=(), **more):
    return {"name": name, "line": line, "rests_on": list(rests_on), **more}


def one(span, *steps, name="", feeds="", **more):
    return {"span": span, "name": name or f"The {span} loop", "line": f"What the {span} loop is", "feeds": feeds, "steps": list(steps), **more}


def whole(*loops, currencies=(), hooks=()):
    return {"loops": list(loops), "currencies": list(currencies), "hooks": list(hooks)}


FOUR = [card("Spawn"), card("Fight"), card("Loot"), card("Upgrade")]
CORE = whole(one("core", *FOUR))
GOLD = {"id": "gold", "name": "Gold", "kind": "soft", "line": "Coins from the fights"}
GEMS = {"id": "gems", "name": "Gems", "kind": "hard", "line": "Bought or won in a season"}


def rich():
    """A game as the leader would give it: three loops, two currencies, three hooks; the feelings and intensities rise and fall."""
    return whole(
        one("core", card("Aim", feel="challenge", intensity=3), card("Shoot", feel="sensation", intensity=5, gives=["gold"]), card("Reload", feel="submission", intensity=1), name="Hit", feeds="session"),
        one("session", card("Join", feel="fellowship", intensity=2), card("Hold", feel="challenge", intensity=5, takes=["gold"]), card("Score", feel="fantasy", intensity=3, gives=["gems"]), name="A match", feeds="meta"),
        one("meta", card("Unlock", feel="discovery", intensity=2, takes=["gems"]), card("Climb", feel="challenge", intensity=4, gives=["gold"]), card("Boast", feel="expression", intensity=3), name="The season"),
        currencies=[GOLD, GEMS], hooks=[{"when": "D7", "line": "The season ends on Sunday"}, {"when": "D1", "line": "A daily chest waits"}])


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


def steps_of(data, span="core"):
    return next(lp for lp in data["loops"] if lp["span"] == span)["steps"]


# -- what is kept -------------------------------------------------------------------------------------------------------------------

def test_nothing_is_kept_before_a_loop_and_the_loops_are_kept_from_the_core_out_with_who_kept_them(game):
    s = state(game)
    assert loop.read(s) == {"version": 2, "loops": [], "currencies": [], "hooks": [], "by": "", "at": ""} and not loop.kept(loop.read(s)) and loop.text(s, game) is None
    data = rich()
    data["loops"].reverse()                                                              # the order given is not the order kept
    data["loops"][-1]["steps"][0]["rests_on"] = ["config/waves.yml", "levels"]
    kept, dropped = loop.keep(s, game, data, "leader")
    assert dropped == [] and [lp["id"] for lp in kept["loops"]] == ["core", "session", "meta"] and kept["by"] == "leader" and kept["at"]
    assert [c["id"] for c in kept["currencies"]] == ["gold", "gems"] and [h["when"] for h in kept["hooks"]] == ["D1", "D7"]            # the hooks in the days' order
    shoot = steps_of(kept)[1]
    assert shoot == {"id": "shoot", "name": "Shoot", "line": "A line", "feel": "sensation", "intensity": 5, "gives": ["gold"], "takes": [], "rests_on": [], "by": "leader", "at": shoot["at"]} and shoot["at"]
    assert steps_of(kept, "core")[0]["rests_on"] == ["config/waves.yml", "levels"]      # a file, and a folder of dev's tree
    assert loop.read(s) == kept and json.loads((s / "loop.json").read_text())["version"] == 2 and "cards" not in json.loads((s / "loop.json").read_text())


def test_the_limits_are_refused_in_plain_words_and_a_refusal_keeps_nothing(game):
    s = state(game)
    base = lambda **k: whole(one("core", *FOUR), **k)       # noqa: E731
    for bad, why in ((None, "loops, currencies and hooks"), ("no", "loops, currencies and hooks"), ({}, "one to three loops"), ({"loops": "no"}, "one to three loops"), (whole(), "one to three loops"),
                     (whole(*[one("core", *FOUR)] * 4), "one to three loops"), (whole(one("core", *FOUR), one("core", *FOUR)), "Two loops are the core loop"),
                     (whole(one("tomorrow", *FOUR)), "core, session or meta"), (whole("no"), "core, session or meta"), (whole({**one("core", *FOUR), "name": ""}), "core loop has a name"),
                     (whole(one("core", *FOUR[:2])), "core loop has 3 to 6 steps"), (whole(one("core", *[card(str(n)) for n in range(7)])), "core loop has 3 to 6 steps"),
                     (whole(one("core", *FOUR[:2], "no")), "a name and a line"), (whole(one("core", *FOUR[:3], card(""))), "a name and a line"), (whole(one("core", *FOUR[:3], card("Loot2", ""))), "a name and a line"),
                     (whole(one("core", *FOUR[:3], card("fight"))), "Two steps of the core loop are named fight"), (whole(one("core", *FOUR[:3], {"name": "X", "line": "l", "rests_on": "config/balance.json"})), "list of files"),
                     (whole(one("core", *FOUR[:3], card("X", feel="joy"))), "A feeling is one of sensation"), (whole(one("core", *FOUR[:3], card("X", intensity="loud"))), "number from 1 to 5"),
                     (base(currencies=[GOLD, GEMS, {"name": "C"}, {"name": "D"}, {"name": "E"}]), "at most 4 currencies"), (base(currencies=[{"name": ""}]), "currency has a name"),
                     (base(currencies=[GOLD, {**GOLD, "id": "g2", "name": "gold"}]), "Two currencies are named gold"), (base(currencies=[{**GOLD, "kind": "magic"}]), "A currency is soft"),
                     (base(hooks=[{"when": "D2", "line": "x"}]), "D1, D7 or D30"), (base(hooks=[{"when": "D1", "line": "x"}, {"when": "D1", "line": "y"}]), "once each"),
                     (base(hooks=[{"when": "D1", "line": ""}]), "with a line"), (base(hooks=[{"when": w, "line": "x"} for w in ("D1", "D7", "D30", "D1")]), "once each")):
        with pytest.raises(ValueError, match=why):
            loop.keep(s, game, bad, "person")
    with pytest.raises(ValueError, match="person or the leader"):
        loop.keep(s, game, CORE, "model")
    assert not loop.kept(loop.read(s))
    kept, _ = loop.keep(s, game, whole(one("core", card("N" * 100, "word  " * 100, intensity=9), card("Calm", intensity=-4), card("Mid", intensity="4.4"), card("None")), currencies=[{"name": "Coin"}]), "person")
    first = steps_of(kept)[0]
    assert len(first["name"]) == loop.NAME_CHARS and len(first["line"]) <= loop.LINE_CHARS and "  " not in first["line"]
    assert [s["intensity"] for s in steps_of(kept)] == [5, 1, 4, 3]                       # clamped to 1–5; 3 where none was said
    assert kept["currencies"] == [{"id": "coin", "name": "Coin", "kind": "soft", "line": ""}]


def test_a_step_gives_and_takes_only_currencies_the_game_has_by_their_id_or_their_name(game):
    s = state(game)
    data = whole(one("core", card("Aim", gives=["Gold", "gold", "nope"]), card("Shoot", takes=[" GEMS ", 7, "gold"]), card("Reload", gives="gold"), card("Rest")), currencies=[GOLD, GEMS])
    kept, _ = loop.keep(s, game, data, "person")
    assert [(x["gives"], x["takes"]) for x in steps_of(kept)] == [(["gold"], []), ([], ["gems", "gold"]), ([], []), ([], [])]
    kept, _ = loop.keep(s, game, whole(one("core", card("Aim", gives=["gold"]), *FOUR[1:]), currencies=[]), "person")
    assert steps_of(kept)[0]["gives"] == []                                              # no currency, no give


def test_a_step_rests_only_on_files_and_folders_of_devs_tree_the_rest_is_dropped_and_said(game):
    s = state(game)
    (game / "later.ts").write_text("x")                                                # in the working tree, not on dev
    ask = ["config/balance.json", "./config/balance.json", "levels/", "nope.ts", "later.ts", "../x", "/etc/passwd", ".env", "config\\waves.yml", 7, "src/game.ts", "src/game.ts"]
    kept, dropped = loop.keep(s, game, whole(one("core", card("Spawn", rests_on=ask), *FOUR[1:])), "person")
    assert steps_of(kept)[0]["rests_on"] == ["config/balance.json", "levels", "config/waves.yml", "src/game.ts"]
    assert dropped == [{"name": "Spawn", "path": p} for p in ("nope.ts", "later.ts", "../x", "/etc/passwd", ".env")]
    many = [f"levels/{n}.json" for n in ("one", "two")] + ["config/balance.json", "config/waves.yml", "src/game.ts", "src/balance_curve.ts", "README.md"]
    assert len(steps_of(loop.keep(s, game, whole(one("core", card("Spawn", rests_on=many), *FOUR[1:])), "person")[0])[0]["rests_on"]) == loop.PATHS


def test_a_project_with_no_dev_keeps_no_path(tmp_path):
    r = tmp_path / "plain"
    r.mkdir()
    git(r, "init", "-b", "main")
    (r / "a.json").write_text("{}")
    kept, dropped = loop.keep(r / ".orkcraft", r, whole(one("core", card("Spawn", rests_on=["a.json"]), *FOUR[1:])), "person")
    assert steps_of(kept)[0]["rests_on"] == [] and dropped == [{"name": "Spawn", "path": "a.json"}] and loop.config_files(r) == [] and loop.tree(r) == {}


def test_a_step_kept_again_unchanged_keeps_its_leader_and_time_one_changed_is_the_persons(game):
    s = state(game)
    first, _ = loop.keep(s, game, whole(one("core", card("Spawn", "Enemies come"), *FOUR[1:])), "leader")
    old = steps_of(first)
    again, _ = loop.keep(s, game, whole(one("core", {**old[0]}, {**old[1], "line": "Changed by the person"}, old[2], {"name": "Grow", "line": "New"})), "person")
    now = steps_of(again)
    assert [c["by"] for c in now] == ["leader", "person", "leader", "person"] and now[0]["at"] == old[0]["at"] and now[2]["at"] == old[2]["at"]
    assert [c["id"] for c in now] == ["spawn", "fight", "loot", "grow"]                  # an id stays; a new step has a name's
    renamed, _ = loop.keep(s, game, whole(one("core", {**now[0]}, {**now[1]}, now[2], card("Zed", id="loot"))), "person")
    assert len({c["id"] for c in steps_of(renamed)}) == 4                                # no two steps share an id
    same, _ = loop.keep(s, game, whole(one("core", *steps_of(renamed))), "leader")
    assert (same["by"], same["at"]) == (renamed["by"], renamed["at"])                  # nothing changed: nothing is kept anew, nobody is the keeper


def test_a_file_that_is_not_of_the_shape_reads_as_nothing(game):
    s = state(game)
    s.mkdir(exist_ok=True)
    ok = {"id": "ok", "name": "A", "line": "b", "rests_on": ["x/../y", "z"], "by": "robot", "feel": "joy", "intensity": 99, "gives": ["gold", "ghost", ["x"]], "takes": "gold"}
    (s / "loop.json").write_text(json.dumps({"version": 2, "loops": [
        {"span": "core", "name": "Hit", "feeds": "core", "steps": [ok, {**ok, "id": "ok"}, {"id": "Bad Id", "name": "B", "line": "c"}, "no", {"id": "n", "name": "", "line": "c"}]},
        {"span": "core", "name": "Twice", "steps": [ok]}, {"span": "year", "name": "Odd", "steps": [ok]}, {"span": "meta", "name": "Empty", "steps": []}, "no"],
        "currencies": [GOLD, {**GOLD, "name": "Again"}, {"id": "Bad", "name": "x"}, {"id": "k", "name": "K", "kind": "magic"}],
        "hooks": [{"when": "D30", "line": "l"}, {"when": "D30", "line": "dup"}, {"when": "D3", "line": "x"}, {"when": "D1", "line": ""}]}))
    got = loop.read(s)
    assert [lp["span"] for lp in got["loops"]] == ["core"] and got["loops"][0]["feeds"] == "" and len(got["loops"][0]["steps"]) == 1
    assert got["loops"][0]["steps"][0] == {"id": "ok", "name": "A", "line": "b", "feel": "", "intensity": 5, "gives": ["gold"], "takes": [], "rests_on": ["z"], "by": "person", "at": ""}
    assert [(c["id"], c["kind"]) for c in got["currencies"]] == [("gold", "soft"), ("k", "soft")] and got["hooks"] == [{"when": "D30", "line": "l"}]
    (s / "loop.json").write_text("not json")
    assert not loop.kept(loop.read(s)) and loop.proposal(s) == {"status": "", "error": "", "at": ""}


def test_the_proposal_is_kept_beside_the_loops_and_forgotten_by_an_empty_status(game):
    s = state(game)
    loop.save_proposal(s, "asking")
    assert loop.proposal(s)["status"] == "asking" and not loop.kept(loop.read(s))
    loop.save_proposal(s, "failed", "Game  design did not answer: try again")
    assert loop.proposal(s)["status"] == "failed" and loop.proposal(s)["error"] == "Game design did not answer: try again"
    loop.keep(s, game, CORE, "leader")
    assert loop.proposal(s)["status"] == "failed" and len(steps_of(loop.read(s))) == 4  # the loops do not forget the proposal, nor it them
    loop.save_proposal(s, "")
    assert loop.proposal(s)["status"] == "" and len(steps_of(loop.read(s))) == 4


# -- a version 1 file ---------------------------------------------------------------------------------------------------------------

V1 = {"cards": [{"id": f"c{n}", "name": f"Card {n}", "line": f"Line {n}", "rests_on": ["config/balance.json", "x/../y"], "by": "leader" if n else "person", "at": f"2026-10-2{n}T08:00:00"} for n in range(5)],
      "proposal": {"status": "done", "error": "", "at": "2026-10-20T08:00:00"}}


def test_a_version_1_file_reads_as_one_core_loop_with_no_feeling_and_intensity_3(game):
    s = state(game)
    s.mkdir(exist_ok=True)
    (s / "loop.json").write_text(json.dumps(V1))
    got = loop.read(s)
    assert [lp["span"] for lp in got["loops"]] == ["core"] and got["currencies"] == [] and got["hooks"] == [] and (got["by"], got["at"]) == ("person", "2026-10-24T08:00:00")
    steps = steps_of(got)
    assert [x["id"] for x in steps] == ["c0", "c1", "c2", "c3", "c4"] and {(x["feel"], x["intensity"], tuple(x["gives"]), tuple(x["takes"])) for x in steps} == {("", 3, (), ())}
    assert steps[0]["rests_on"] == ["config/balance.json"] and [x["by"] for x in steps] == ["person", "leader", "leader", "leader", "leader"] and steps[2]["at"] == "2026-10-22T08:00:00"
    assert loop.findings(got) == [] and "Rests on: config/balance.json" in loop.text(s, game)                  # nothing is said of what was never described
    kept, _ = loop.keep(s, game, got, "person")                                                              # kept again, it is written as version 2, the proposal's state kept
    rec = json.loads((s / "loop.json").read_text())
    assert rec["version"] == 2 and "cards" not in rec and rec["proposal"]["status"] == "done" and steps_of(kept)[1]["by"] == "leader"
    kept, _ = loop.keep(s, game, {"cards": [card(f"Old {n}") for n in range(4)]}, "person")                  # a version 1 answer to a set is one core loop too
    assert [lp["span"] for lp in kept["loops"]] == ["core"] and len(steps_of(kept)) == 4


# -- the leader's proposal over the person's version -------------------------------------------------------------------------------------

def test_the_leaders_keeping_over_the_persons_version_puts_it_aside_in_was(game):
    s = state(game)
    loop.keep(s, game, CORE, "leader")
    assert "was" not in loop.read(s)
    mine, _ = loop.keep(s, game, whole(one("core", *[{**c, "name": c["name"] + "!"} for c in FOUR])), "person")
    assert "was" not in mine
    theirs, _ = loop.keep(s, game, rich(), "leader")
    assert [lp["span"] for lp in theirs["loops"]] == ["core", "session", "meta"] and theirs["by"] == "leader"
    assert theirs["was"]["by"] == "person" and [c["name"] for c in steps_of(theirs["was"])] == ["Spawn!", "Fight!", "Loot!", "Upgrade!"] and theirs["was"]["at"] == mine["at"]
    assert "was" not in theirs["was"] and [c["by"] for c in steps_of(theirs["was"])] == ["person"] * 4
    again, _ = loop.keep(s, game, whole(one("core", *FOUR)), "leader")                                         # the leader's own earlier version is not the person's: `was` stays theirs
    assert again["was"] == theirs["was"] and again["by"] == "leader"
    edited, _ = loop.keep(s, game, {k: v for k, v in again.items() if k in ("loops", "currencies", "hooks")}, "person")
    assert (edited["by"], edited["at"], edited["was"]) == (again["by"], again["at"], theirs["was"])             # unchanged: nothing is kept anew
    mine2, _ = loop.keep(s, game, whole(one("core", *[card(f"Mine {n}") for n in range(3)])), "person")
    assert mine2["was"] == theirs["was"]                                                                       # the person keeping does not touch `was`
    last, _ = loop.keep(s, game, CORE, "leader")
    assert [c["name"] for c in steps_of(last["was"])] == ["Mine 0", "Mine 1", "Mine 2"]                        # a newer version of theirs replaces the older one aside


# -- what the loop says ------------------------------------------------------------------------------------------------------------

def test_the_loop_says_what_is_wrong_by_code_in_the_words_of_the_spec(game):
    s = state(game)
    assert loop.findings(loop.keep(s, game, rich(), "leader")[0]) == []                                          # a loop that breathes, with an economy, says nothing
    gold_only = whole(one("core", card("Aim", feel="challenge", intensity=2, gives=["gold"]), card("Shoot", feel="sensation", intensity=5), card("Rest", feel="submission", intensity=1)), currencies=[GOLD])
    assert loop.findings(loop.keep(s, game, gold_only, "leader")[0]) == ["Gold is only earned: it will pile up"]
    nobody = whole(one("core", card("Aim", feel="challenge", intensity=2, takes=["gold"]), card("Shoot", feel="sensation", intensity=5), card("Rest", feel="submission", intensity=1)), currencies=[GOLD])
    assert loop.findings(loop.keep(s, game, nobody, "leader")[0]) == ["Nothing gives Gold", "The core loop rewards nothing"]
    unused = whole(one("core", card("Aim", feel="challenge", intensity=2, gives=["gems"]), card("Shoot", feel="sensation", intensity=5, takes=["gems"]), card("Rest", feel="submission", intensity=1)), currencies=[GOLD, GEMS])
    assert loop.findings(loop.keep(s, game, unused, "leader")[0]) == ["Nothing gives Gold"]                      # a currency nothing touches: nothing gives it
    flat = rich()
    flat["loops"][1]["steps"] = [{**c, "intensity": 4} for c in flat["loops"][1]["steps"]]
    assert loop.findings(loop.keep(s, game, flat, "leader")[0]) == ["The session loop's feeling is flat"]
    unfed = rich()
    unfed["loops"][0]["feeds"] = ""
    unfed["loops"][1]["feeds"] = "meta"
    assert loop.findings(loop.keep(s, game, unfed, "leader")[0]) == ["Nothing feeds the session loop"]
    unfed["loops"][1]["feeds"] = ""
    assert loop.findings(loop.keep(s, game, unfed, "leader")[0]) == ["Nothing feeds the session loop", "Nothing feeds the meta loop"]
    bare = rich()
    bare["loops"][2]["steps"] = [{**c, "gives": []} for c in bare["loops"][2]["steps"]]
    assert loop.findings(loop.keep(s, game, bare, "leader")[0]) == ["The meta loop rewards nothing"]
    no_economy = whole(one("core", *FOUR))                                                                       # no currency: nothing to reward, no feeling said: nothing flat
    assert loop.findings(loop.keep(s, game, no_economy, "leader")[0]) == []
    assert loop.findings({"loops": [], "currencies": []}) == [] and loop.findings({}) == []
    skip = whole(one("core", *[card(c["name"], feel="challenge", intensity=2) for c in FOUR], feeds="session"), one("meta", *FOUR[:3]))
    assert loop.findings(loop.keep(s, game, skip, "leader")[0]) == ["The core loop's feeling is flat"]            # a core with no session loop feeds the meta loop


# -- the leader's answer, strictly -------------------------------------------------------------------------------------------------

def test_the_leaders_answer_is_loops_currencies_and_hooks_clamped_to_the_limits(game):
    good = whole(one("core", card("Spawn", "Enemies come", ["config/waves.yml", "ghost.ts"], gives=["Gold"], feel="joy", intensity=8), card("Fight", rests_on=["levels"], feel="challenge"), card("Loot"), card("Upgrade"),
                     *[card(f"More {n}") for n in range(5)], feeds="session"),
                 one("meta", *FOUR[:3]), one("session", *FOUR[:3]), {"span": "meta", "name": "Over the limit"},
                 currencies=[{"name": "Gold", "kind": "magic"}, GEMS, {"name": "C"}, {"name": "D"}, {"name": "E"}], hooks=[{"when": w, "line": "x"} for w in ("D1", "D7", "D30")] + [{"when": "D1", "line": "y"}, "no"])
    got = loop.parse(good, game)
    assert [lp["span"] for lp in got["loops"]] == ["core", "session", "meta"] and len(got["loops"][0]["steps"]) == loop.MAX_STEPS
    spawn = got["loops"][0]["steps"][0]
    assert spawn == {"name": "Spawn", "line": "Enemies come", "feel": "", "intensity": 5, "gives": ["gold"], "takes": [], "rests_on": ["config/waves.yml"]}      # an id of the model's is none: made at keeping
    assert got["loops"][0]["feeds"] == "session"                                            # an id of the model's is none: it is made at keeping
    assert [c["id"] for c in got["currencies"]] == ["gold", "gems", "c", "d"] and got["currencies"][0]["kind"] == "soft" and len(got["hooks"]) == loop.MAX_HOOKS
    assert loop.keep(state(game), game, got, "leader")[0]["by"] == "leader"                                       # and what it gives can be kept as it is
    for bad in (None, "text", {}, {"loops": "no"}, {"loops": []}, whole(one("core", *FOUR[:2])), whole(one("core", *FOUR[:3], card("x", ""))), whole(one("core", *FOUR[:3], {"name": "x"})),
                whole(one("core", *FOUR[:3], "no")), whole(one("core", *FOUR[:3], card("Spawn"))), whole(one("core", *FOUR[:3], {"name": "Z", "line": "l", "rests_on": "config/waves.yml"})),
                whole(one("core", *FOUR), one("core", *FOUR)), whole(one("later", *FOUR)), whole({**one("core", *FOUR), "name": ""}), whole(one("core", *FOUR), currencies=[{"name": ""}])):
        assert loop.parse(bad, game) is None
    assert loop.parse(whole(one("core", *[{**c, "id": "x"} for c in FOUR])), game) is not None                     # the same id twice is made over


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

def test_the_text_is_the_loops_from_the_core_out_then_the_economy_the_hooks_and_what_the_loop_says(game):
    s = state(game)
    data = whole(one("core", card("Spawn", "Enemies come in waves", ["config/waves.yml"], feel="challenge", intensity=4, gives=["gold"]),
                     card("Fight", "Hit and dodge", ["config/balance.json", "levels", "src/game.ts", "vite.config.ts"], feel="sensation", intensity=5), card("Loot"), name="Hit", feeds="session"),
                 one("session", *FOUR[:3], name="A wave"), currencies=[GOLD, GEMS], hooks=[{"when": "D1", "line": "A daily chest"}])
    loop.keep(s, game, data, "leader")
    assert loop.text(s, game) == f"""The map of the loop at dev {git(game, 'rev-parse', 'dev')[:7]}

Core loop (seconds): Hit. What the core loop is. Feeds the session loop.
1. Spawn: Enemies come in waves
   feels challenge, intensity 4/5; gives Gold. Rests on: config/waves.yml
2. Fight: Hit and dodge
   feels sensation, intensity 5/5. Rests on: config/balance.json, levels, src/game.ts, +1
3. Loot: A line
   Rests on: no file named

Session loop (minutes): A wave. What the session loop is.
1. Spawn: A line
   Rests on: no file named
2. Fight: A line
   Rests on: no file named
3. Loot: A line
   Rests on: no file named

Currencies:
- Gold (soft): Coins from the fights. Given by: Spawn. Taken by: nothing.
- Gems (hard): Bought or won in a season. Given by: nothing. Taken by: nothing.

Why a player comes back:
- D1: A daily chest

What the loop says:
- Gold is only earned: it will pile up
- Nothing gives Gems
- The session loop rewards nothing"""


def test_the_same_record_and_dev_are_the_same_bytes_and_a_later_head_changes_only_its_line(game):
    s = state(game)
    loop.keep(s, game, CORE, "leader")
    first = loop.text(s, game)
    assert loop.text(s, game) == first == loop.text(s, game, "")
    commit(game, "README.md", "# Game, changed\n")
    two = loop.text(s, game)
    assert two != first and two.split("\n", 1)[1] == first.split("\n", 1)[1]


def test_the_text_is_bounded_whatever_the_loops_hold_the_lines_and_files_are_shortened_before_anything_is_cut(game):
    s = state(game)
    deep = "/".join(["d" * 30] * 6)
    (game / deep).mkdir(parents=True)
    names = []
    for n in range(6):
        (game / deep / f"{'f' * 30}{n}.json").write_text("{}")
        names.append(f"{deep}/{'f' * 30}{n}.json")
    git(game, "add", "-A")
    git(game, "commit", "-q", "-m", "deep")
    cur = [{"id": f"c{n}", "name": f"{n}" * 40, "kind": "soft", "line": "l" * 160} for n in range(4)]
    big = whole(*[one(span, *[card(f"{n}" * 40, "l" * 160, names, feel="challenge", intensity=n % 5 + 1, gives=["c0"], takes=["c1"]) for n in range(6)], name=span * 8, feeds=nxt)
                  for span, nxt in (("core", "session"), ("session", "meta"), ("meta", ""))], currencies=cur, hooks=[{"when": w, "line": "h" * 160} for w in loop.WHENS])
    loop.keep(s, game, big, "person")
    text = loop.text(s, game)
    assert len(text) <= loop.LIMIT and all(f"{n}. " in text for n in range(1, 7)) and text.count("Core loop") == text.count("Meta loop") == 1
    assert "Why a player comes back:" in text and "D30" in text                         # the lines and names were shortened first: the economy and the hooks are still there


def test_with_since_the_text_ends_with_what_changed_under_the_steps_files_and_the_goal_that_changed_it(game):
    s = state(game)
    loop.keep(s, game, whole(one("core", card("Spawn", rests_on=["config/waves.yml"]), card("Fight", rests_on=["config/balance.json", "levels"]), card("Loot"), card("Upgrade"))), "leader")
    before = git(game, "rev-parse", "dev")
    base = loop.text(s, game, before)
    assert base.endswith("Changed under the loop since your last call: nothing.") and base.startswith(loop.text(s, game))
    land(game, "tougher-waves", "k1", {"config/waves.yml": "waves: 9\n", "src/game.ts": "export const g = 3\n"})
    commit(game, "levels/three.json", "{}\n", "my own level")
    got = loop.text(s, game, before)
    assert got.rsplit("\n\n", 1)[1] == "Changed under the loop since your last call:\n- Spawn: config/waves.yml (goal tougher-waves)\n- Fight: levels/three.json (by you)"
    assert "src/game.ts" not in got                                                     # a file no step rests on is not said
    assert loop.text(s, game, "not a commit").endswith("Changed under the loop since your last call: not known (no map was kept at that commit).")
