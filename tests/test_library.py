"""Spec 59 §2.2–§2.4 (docs/specs/59-mixed-parties.md; realm/library.py): the five agents of the mixed parties, the Product manager who takes
screens too, the leaders' stages and seats, and the library's parties (the mixed first). Code, no model."""
from __future__ import annotations


from orkboard.realm import goal_team, library, roles


def test_a_leaders_stages_each_have_one_seat_and_the_default_is_for_any_other():
    one = {"lead": 1, "build": 1, "check": 1}                                                 # Ideation's: its four views and the skeptic are its stages whole (spec 65 §1)
    squad = {"lead": 1, "build": 5, "check": 2}                                               # spec 99 §1.3: a party's squad is its leader, up to five who do, up to two who check
    for leader, s in {**library.STAGES, "default": library.DEFAULT_STAGES}.items():
        assert s.seats == (one if leader == "investor" else squad), leader
        assert not hasattr(s, "build_seats") and not hasattr(s, "check_seats"), leader
    assert library.STAGES.keys() == {"game-designer", "investor", "release-manager"}      # the Investor's: spec 65 §1; the Release manager's: spec 68 §1
    game = library.stages_of("game-designer")
    assert (game.lead, game.build, game.check) == ("Concept", "Build", "Playtest")           # the stage words stay
    assert (library.stages_of("investor").lead, library.stages_of("investor").build, library.stages_of("investor").check) == ("Pitch", "Views", "Decision")
    for other in ("architect", "taskmaster", "product-manager", "a-persons-own", ""):
        s = library.stages_of(other)
        assert (s.lead, s.build, s.check) == ("Planning", "Implementation", "Checking"), other
        assert library.seats_of(other) == squad
    assert library.seats_of("game-designer") == squad == library.seats_of("growth") and library.seats_of("investor") == one
    assert library.SEATS == squad                                                            # for older faces


def test_presets_answer_the_mixed_first_then_each_craft_then_the_taskmaster_alone():
    got = library.presets()
    assert [p["id"] for p in got] == ["game", "mobile-app", "website", "ideation", "release", "art", "engineering", "design", "data", "marketing", "product", "mixed"]
    assert [p["mixed"] for p in got] == [True] * 6 + [False] * 6
    game, eng, alone = got[0], got[6], got[-1]
    assert game == {"id": "game", "name": "Game", "line": "Rules, levels, art and sound, played through", "craft": "design", "race": "elf",
                    "mixed": True, "lead": "game-designer", "build": ["grunt", "artist", "level-designer", "sound-designer"], "check": ["playtester"]}
    assert (eng["name"], eng["line"], eng["lead"], eng["race"]) == ("Tech", "How it is built: its parts, its tests and the build", "architect", "peon")   # spec 89 §5
    assert (alone["name"], alone["lead"], alone["build"], alone["check"]) == ("Taskmaster alone", "taskmaster", [], [])
    assert [p["name"] for p in got[7:11]] == [roles.CRAFT_LABELS[c] for c in ("design", "data", "marketing", "product")]


def test_listed_and_stages_answer_the_new_agents_and_every_leader():
    listed = {a["id"]: a for a in library.listed()}
    assert listed["playtester"]["band"] == "check" and listed["playtester"]["check"]["applies"].startswith("when the idea changes what a player")
    stages = library.stages()
    assert stages["game-designer"] == {"lead": "Concept", "build": "Build", "check": "Playtest", "seats": {"lead": 1, "build": 5, "check": 2}}
    assert stages["architect"] == stages["default"] == {"lead": "Planning", "build": "Implementation", "check": "Checking",
                                                       "seats": {"lead": 1, "build": 5, "check": 2}}
    assert set(stages) == {a.id for a in library.LIBRARY if a.band == "lead"} | {"default"}


# -- spec 68 §1: the Release manager and its hands, the preset, an agent's own race ---------------------------------------

def _skeletons(tmp_path, monkeypatch, tiers=roles.TIERS):
    """orkUI's copy with the skeleton drawn at `tiers` (A0's files), else as it is."""
    folder = tmp_path / "races"
    folder.mkdir()
    for t in tiers:
        (folder / f"skeleton-{t}.png").write_bytes(b"png")
    monkeypatch.setattr(roles, "RACE_FILES", folder)


def test_the_release_preset_follows_ideation_and_the_release_managers_stages_are_gather_prepare_check():
    got = library.presets()
    i = [p["id"] for p in got].index("release")
    assert got[i - 1]["id"] == "ideation" and got[i] == {
        "id": "release", "name": "Release", "line": "A version out: what goes in, its notes, the stores' list", "craft": "product", "race": "skeleton",
        "mixed": True, "lead": "release-manager", "build": ["release-engineer", "release-notes", "aso"], "check": ["release-checker"]}
    assert library.stages()["release-manager"] == {"lead": "Gather", "build": "Prepare", "check": "Check", "seats": {"lead": 1, "build": 5, "check": 2}}
    assert not goal_team.seats(["release-engineer", "release-checker"], "release-manager")
    assert not goal_team.seats(["release-engineer", "release-notes", "release-checker"], "release-manager")           # three who do and one who checks: within a squad
    assert library.parties()["release"] == {"lead": "release-manager", "build": ["release-engineer", "release-notes", "aso"], "check": ["release-checker"]}


def test_a_role_wears_its_own_race_when_its_file_is_in_orkuis_copy_else_its_crafts(tmp_path, monkeypatch):
    state = tmp_path / ".orkcraft"
    library.install(state, ["release-manager", "release-engineer"])
    manager, engineer = roles.role(state, "release-manager"), roles.role(state, "release-engineer")
    assert manager["race"] == "skeleton" and engineer["race"] == "" and "race: skeleton" in (state / "roles" / "release-manager.md").read_text()
    monkeypatch.setattr(roles, "RACE_FILES", tmp_path / "nowhere")
    assert roles.head(manager, "balance") == {"craft": "product", "race": "lich", "tier": "warrior"}              # the file is missing: the craft's
    assert roles.head(engineer, "balance")["race"] == "peon"
    _skeletons(tmp_path, monkeypatch)
    assert roles.head(manager, "balance") == {"craft": "product", "race": "skeleton", "tier": "warrior"}
    assert roles.head({**manager, "race": "dragon"}, "balance")["race"] == "lich" and roles.head({**manager, "race": "../x"}, "balance")["race"] == "lich"


def test_saving_a_role_keeps_its_race_and_a_role_without_one_reads_empty(tmp_path):
    state = tmp_path / ".orkcraft"
    library.install(state, ["release-manager"])
    roles.save(state, "Release manager", "warrior", 2, "Gather what goes in.", slug="release-manager")
    assert roles.role(state, "release-manager")["race"] == "skeleton" and "race: skeleton" in (state / "roles" / "release-manager.md").read_text()
    roles.save(state, "Docs scribe", "warrior", 2, "Write plainly.")
    assert roles.role(state, "docs-scribe")["race"] == "" and "race:" not in (state / "roles" / "docs-scribe.md").read_text()
    assert roles.role(state, "grunt")["craft"] == "engineering" and roles.head(roles.role(state, "grunt"), "balance")["race"] == "peon"


# -- Art and sound: the Art director's party (pictures, icons, motion, sounds and music of a project's own) ---------------------

ART_IDS = ["art-director", "animator", "composer", "icon-artist", "art-reviewer"]


def test_a_task_of_an_art_kind_goes_to_the_art_party_member_who_takes_it(tmp_path):
    library.install(tmp_path, ["art-director", "artist", "animator", "composer", "sound-designer", "icon-artist", "art-reviewer"])
    team = ["artist", "sound-designer", "animator", "composer", "icon-artist", "art-reviewer"]
    got = {k: roles.role_for(tmp_path, k, team)["slug"] for k in ("art", "sound", "motion", "music", "artcheck")}
    assert got == {"art": "artist", "sound": "sound-designer", "motion": "animator", "music": "composer", "artcheck": "art-reviewer"}
    assert roles.role_for(tmp_path, "artdirection", ["art-director", "artist"])["slug"] == "art-director"
    assert roles.role_for(tmp_path, "art", ["icon-artist"])["slug"] == "icon-artist"              # as the party's one builder, it draws the pictures too
    assert roles.role_for(tmp_path, "motion", ["artist"])["slug"] == "grunt"                      # no animator in the party: the Grunt fills in
