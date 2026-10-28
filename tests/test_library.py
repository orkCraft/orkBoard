"""Spec 59 §2.2–§2.4 (docs/specs/59-mixed-parties.md; realm/library.py): the five agents of the mixed parties, the Product manager who takes
screens too, the leaders' stages and seats, and the library's parties (the mixed first). Code, no model."""
from __future__ import annotations

import re

from orkboard.realm import goal_team, library, roles


def test_the_five_new_agents_are_in_the_librarys_order_with_their_craft_tier_kinds_and_band():
    ids = [a.id for a in library.LIBRARY]
    assert ids.index("game-designer") == ids.index("product-designer") + 1                 # the Game designer after the Product designer
    assert ids[ids.index("artist") + 1:ids.index("artist") + 4] == ["level-designer", "sound-designer", "playtester"]     # after the Artist
    assert ids.index("aso") == ids.index("seo") + 1                                         # ASO after SEO
    rows = {a.id: (a.name, a.craft, roles.RACES[a.craft], a.tier, a.takes, a.band) for a in library.LIBRARY}
    assert rows["game-designer"] == ("Game designer", "design", "elf", "elder", ("gamedesign",), "lead")
    assert rows["level-designer"] == ("Level designer", "design", "elf", "warrior", ("level",), "build")
    assert rows["sound-designer"] == ("Sound designer", "design", "elf", "laborer", ("sound",), "build")
    assert rows["playtester"] == ("Playtester", "design", "elf", "warrior", ("playtest",), "check")
    assert rows["aso"] == ("ASO", "marketing", "gnome", "laborer", ("aso",), "build")
    assert [library.get(i).line for i in ("game-designer", "level-designer", "sound-designer", "playtester", "aso")] == [
        "Leads a game party: the rules, the loop, what makes it fun", "Lays out the levels: the path, the beats, where it gets hard",
        "Makes the sound effects, picked by ear", "Plays a change through and says where it breaks or bores",
        "Writes the store pages: keywords, title, texts, screenshots' words"]


def test_each_instruction_is_within_600_in_the_librarys_voice_and_holds_the_agent_to_its_points():
    for a in library.LIBRARY:
        assert len(a.instruction) <= 600, a.id
        assert not re.search(r"\borcs?\b|orchestrat", a.instruction, re.I), a.id
    told = {i: library.get(i).instruction.lower() for i in ("game-designer", "level-designer", "sound-designer", "playtester", "aso")}
    assert all(w in told["game-designer"] for w in ("what the player does, sees and gets", "why it is fun", "before the build", "one balance file", "by playing"))
    assert all(w in told["level-designer"] for w in ("on paper", "the path", "the beats", "gets hard", "how long it plays", "one new idea"))
    assert all(w in told["sound-designer"] for w in ("loopable", "one loudness", "a pick of sounds", "source beside the export"))
    assert all(w in told["playtester"] for w in ("test build", "headless run", "where", "what the player does", "what goes wrong", "fix only what is small"))
    assert all(w in told["aso"] for w in ("search for in the store first", "title and subtitle", "limits", "without the person's yes"))


def test_the_playtesters_check_applies_when_a_player_would_notice():
    check = library.get("playtester").check
    assert check.applies == "when the idea changes what a player does, sees or hears"
    assert check.done == "It was played through: the changed part works and nothing near it broke"
    assert check.task == "Play the idea's change through and write where it breaks, bores or confuses; fix what is small."
    assert check.fits == ("design", "engineering")


def test_the_product_manager_takes_screens_too_in_a_sentence_that_fits():
    pm = library.get("product-manager")
    assert pm.takes == ("research", "design") and pm.band == "lead" and len(pm.instruction) <= 600
    assert ("For a screen, write the flow step by step and what is on each screen and why, at phone width first, in the design "
            "system's words.") in pm.instruction


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


def test_the_librarys_parties_have_known_members_listed_most_needed_first_and_their_first_of_each_fits_the_seats():
    assert [p[0] for p in library.PRESETS] == ["game", "mobile-app", "website", "ideation", "release", "art"]    # Ideation after Website (spec 65 §1), Release after Ideation (spec 68 §1), Art and sound after Release
    for pid, name, line, craft, lead, build, check in library.PRESETS:
        assert library.get(lead).band == "lead" and craft in roles.CRAFTS and name and line, pid
        assert all(library.get(s).band == "build" for s in build) and all(library.get(s).band == "check" for s in check), pid
        assert not goal_team.seats([build[0], check[0]], lead), pid                  # a seat a stage: the first builder and the first checker (spec 87 §5)
    game, app, site, *_rest = library.PRESETS
    assert (game[4], game[5], game[6]) == ("game-designer", ("grunt", "artist", "level-designer", "sound-designer"), ("playtester",))
    assert (app[4], app[5], app[6]) == ("product-manager", ("grunt", "artist", "aso"), ("reviewer", "accessibility-reviewer"))
    assert (site[4], site[5], site[6]) == ("growth", ("grunt", "copywriter", "seo"), ("reviewer", "editor"))


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


def test_parties_keeps_every_craft_and_adds_the_three_mixed_ones_by_their_ids():
    got = library.parties()
    for craft, (lead, build, check) in library.PARTIES.items():
        assert got[craft] == {"lead": lead, "build": list(build), "check": list(check)}      # a face that reads parties[<craft>] is unchanged
    assert {"game", "mobile-app", "website", "ideation", "release", "art"} <= got.keys() and len(got) == len(library.PARTIES) + 6
    assert got["game"] == {"lead": "game-designer", "build": ["grunt", "artist", "level-designer", "sound-designer"], "check": ["playtester"]}


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


def test_the_four_release_agents_follow_ideation_with_their_craft_tier_kind_band_race_and_line():
    ids = [a.id for a in library.LIBRARY]
    assert ids[ids.index("skeptic") + 1:] == ["release-manager", "release-engineer", "release-notes", "release-checker"]
    rows = {i: (a.name, a.craft, a.tier, a.band, a.takes, a.race, a.line) for i in ids[-4:] for a in [library.get(i)]}
    assert rows == {
        "release-manager": ("Release manager", "product", "warrior", "lead", ("research",), "skeleton",
                            "Gathers what goes into a version and gets it out, step by step"),
        "release-engineer": ("Release engineer", "engineering", "laborer", "build", ("code",), "",
                             "Bumps the version, the changelog and the build's config"),
        "release-notes": ("Release notes", "marketing", "laborer", "build", ("text",), "", "Writes what is new, for the stores and the changelog"),
        "release-checker": ("Release checker", "product", "warrior", "check", ("review",), "skeleton",
                            "Checks that the version, its notes and the list agree")}
    assert library.RELEASE_MANAGER == "release-manager" and not any(library.get(i).pitch for i in ids[-4:])
    for i in ids[-4:]:
        told = library.get(i).instruction
        assert 0 < len(told) <= roles.INSTRUCTION_CHARS and not re.search(r"\borcs?\b|orchestrat", told, re.I), i
    assert "never new work" in library.get("release-manager").instruction
    assert "step for the person" in library.get("release-manager").instruction and "never a feature" in library.get("release-engineer").instruction
    assert "one line a goal" in library.get("release-notes").instruction and "did not go in" in library.get("release-notes").instruction
    check = library.get("release-checker").check
    assert check.applies == "when the goal is a release" and check.fits == ("product", "engineering", "marketing")
    assert check.done == "Its version, what is new and the stores' list name exactly the goals that go in, and nothing was submitted"
    assert check.task == ("Check that the version, what is new and the stores' list name exactly the goals that go in, that the build's config "
                          "carries the version, and that nothing was submitted.")


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


def test_listed_says_an_agents_own_race_only_once_orkui_has_its_head(tmp_path, monkeypatch):
    assert {a["id"]: a["race"] for a in library.listed()}["release-manager"] == "skeleton"                       # orkUI 0.5.0's copy has it
    monkeypatch.setattr(roles, "RACE_FILES", tmp_path / "nowhere")
    listed = {a["id"]: a for a in library.listed()}
    assert listed["release-manager"]["race"] == "lich" and listed["release-checker"]["race"] == "lich"          # a copy without it: the craft's
    assert listed["release-engineer"]["race"] == "peon" and listed["release-notes"]["race"] == "gnome" and listed["investor"]["race"] == "lich"
    _skeletons(tmp_path, monkeypatch)
    listed = {a["id"]: a for a in library.listed()}
    assert listed["release-manager"]["race"] == "skeleton" and listed["release-checker"]["race"] == "skeleton"
    assert listed["release-engineer"]["race"] == "peon" and listed["grunt"]["race"] == "peon"
    assert [p["race"] for p in library.presets() if p["id"] == "release"] == ["skeleton"]
    monkeypatch.setattr(roles, "RACE_FILES", tmp_path / "nowhere")
    assert {a["id"]: a["race"] for a in library.listed()}["release-manager"] == "lich"


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


def test_a_head_needs_the_race_at_the_tier_it_is_drawn_at(tmp_path, monkeypatch):
    state = tmp_path / ".orkcraft"
    library.install(state, ["release-manager"])
    _skeletons(tmp_path, monkeypatch, tiers=("warrior",))
    manager = roles.role(state, "release-manager")
    by_target = {**manager, "model": ""}                       # By Target: the task's tier shifted by the Target
    assert roles.head(by_target, "balance") == {"craft": "product", "race": "skeleton", "tier": "warrior"}
    assert roles.head(by_target, "quality") == {"craft": "product", "race": "lich", "tier": "elder"}      # no elder gear yet: the lich's


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


def test_the_art_party_is_a_preset_of_elves_with_the_art_director_leading_and_the_art_reviewer_checking():
    art = next(p for p in library.PRESETS if p[0] == "art")
    assert art == ("art", "Art and sound", "Pictures, icons, motion, sounds and music, in one style", "design", "art-director",
                   ("artist", "sound-designer", "animator", "composer", "icon-artist"), ("art-reviewer",))
    assert not goal_team.seats([art[5][0], art[6][0]], art[4]) and library.seats_of("art-director") == {"lead": 1, "build": 5, "check": 2}
    rows = {i: (a.name, a.craft, a.tier, a.band, a.takes) for i in ART_IDS for a in [library.get(i)]}
    assert rows == {"art-director": ("Art director", "design", "elder", "lead", ("artdirection",)),
                    "animator": ("Animator", "design", "warrior", "build", ("motion",)),
                    "composer": ("Composer", "design", "laborer", "build", ("music",)),
                    "icon-artist": ("Icon artist", "design", "laborer", "build", ("art",)),
                    "art-reviewer": ("Art reviewer", "design", "warrior", "check", ("artcheck",))}
    assert (library.get("artist").tier, library.get("artist").takes, library.get("sound-designer").tier, library.get("sound-designer").takes) == (
        "laborer", ("art",), "laborer", ("sound",))                                                  # the two that were there keep their tier and skill
    ids = [a.id for a in library.LIBRARY]
    assert ids[ids.index("playtester") + 1:ids.index("playtester") + 6] == ART_IDS                  # after the Game's agents, before the data ones
    row = next(p for p in library.presets() if p["id"] == "art")
    assert row["race"] == "elf" and row["mixed"] and row["lead"] == "art-director" and row["check"] == ["art-reviewer"]
    assert library.parties()["art"] == {"lead": "art-director", "build": list(art[5]), "check": ["art-reviewer"]}


def test_every_art_agent_wears_an_elf_head_at_its_tier_in_the_library_and_as_a_role(tmp_path):
    listed = {a["id"]: a for a in library.listed()}
    state = tmp_path / ".orkcraft"
    library.install(state, ["artist", "sound-designer", *ART_IDS])
    for i in ["artist", "sound-designer", *ART_IDS]:
        a = library.get(i)
        assert listed[i]["race"] == "elf" and roles.RACES[a.craft] == "elf", i
        assert roles.head(roles.role(state, i), "balance")["race"] == "elf", i
        assert roles.head({**roles.role(state, i), "model": a.tier}, "balance") == {"craft": "design", "race": "elf", "tier": a.tier}, i
    assert listed["art-reviewer"]["check"]["applies"] == "when the idea adds or changes pictures, icons, motion, sounds or music"


def test_the_art_instructions_hold_each_agent_to_its_work_in_the_librarys_voice():
    told = {i: library.get(i).instruction.lower() for i in [*ART_IDS, "artist", "sound-designer"]}
    for i, text in told.items():
        assert text.startswith("you "), i
        assert 0 < len(library.get(i).instruction) <= roles.INSTRUCTION_CHARS and library.get(i).instruction.endswith("."), i
    assert all(w in told["art-director"] for w in ("style guide", "docs/style-guide.md", "palette", "loudness", "list of assets", "who makes it", "unless the party is lean"))
    assert all(w in told["icon-artist"] for w in ("sizes the project uses", "readable at its size", "one family", "svg source"))
    assert all(w in told["animator"] for w in ("sprite sheets", "lottie", "css", "loopable", "one place", "still frame"))
    assert all(w in told["composer"] for w in ("midi", "tone.js", "brief", "loop", "no click", "one loudness"))
    assert all(w in told["art-reviewer"] for w in ("style guide", "size and format", "one loudness", "loop", "source", "licence", "the asset, what is wrong and the fix"))


def test_the_artist_draws_in_the_projects_own_style_never_orkboards():
    told = library.get("artist").instruction.lower()
    assert "orkui" not in told and "pixel" not in told and "24 px" not in told and "a head is an accent" not in told      # Orkboard's own look is no rule for a project
    assert all(w in told for w in ("the project's own style", "style guide the art director keeps", "the look the project already has", "source beside the export",
                                   "draw only what the task asks", "say what you would add"))
    assert "pixel" not in library.get("artist").line.lower() and (library.get("artist").id, library.get("artist").name, library.get("artist").craft) == ("artist", "Artist", "design")


def test_the_sound_designer_makes_sound_effects_and_leaves_the_music_to_the_composer():
    sound, composer = library.get("sound-designer"), library.get("composer")
    told = sound.instruction.lower()
    assert "sound effects" in told and "music goes to the composer" in told and "music" not in sound.line.lower()
    assert all(w in told for w in ("jsfxr", "web audio", "write the brief", "say which", "one loudness", "loopable", "a pick of sounds"))
    assert composer.takes == ("music",) and "music" in composer.line.lower() and sound.takes == ("sound",)


def test_the_art_reviewers_check_applies_when_assets_change_and_its_tag_is_its_own():
    check = library.get("art-reviewer").check
    assert check.applies == "when the idea adds or changes pictures, icons, motion, sounds or music"
    assert check.done == "Its assets follow the style guide, in the sizes and formats named, at one loudness, with their sources and licences named"
    assert check.task == "Check the idea's assets against the style guide: sizes and formats, loudness and loops, sources and licences; fix what is small."
    assert check.fits == ("design", "engineering") and library.get("art-reviewer").band == "check"
    assert [a.id for a in library.LIBRARY if a.check and a.takes[0] == "artcheck"] == ["art-reviewer"]


def test_a_task_of_an_art_kind_goes_to_the_art_party_member_who_takes_it(tmp_path):
    library.install(tmp_path, ["art-director", "artist", "animator", "composer", "sound-designer", "icon-artist", "art-reviewer"])
    team = ["artist", "sound-designer", "animator", "composer", "icon-artist", "art-reviewer"]
    got = {k: roles.role_for(tmp_path, k, team)["slug"] for k in ("art", "sound", "motion", "music", "artcheck")}
    assert got == {"art": "artist", "sound": "sound-designer", "motion": "animator", "music": "composer", "artcheck": "art-reviewer"}
    assert roles.role_for(tmp_path, "artdirection", ["art-director", "artist"])["slug"] == "art-director"
    assert roles.role_for(tmp_path, "art", ["icon-artist"])["slug"] == "icon-artist"              # as the party's one builder, it draws the pictures too
    assert roles.role_for(tmp_path, "motion", ["artist"])["slug"] == "grunt"                      # no animator in the party: the Grunt fills in
