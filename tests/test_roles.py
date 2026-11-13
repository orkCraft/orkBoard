"""The agents' roles and the task types (spec 34 §3): the files, the two built-ins, dropping a role, the type → role table."""
from __future__ import annotations

import pytest

from orkboard.realm import roles


def test_the_two_built_in_roles_exist_by_themselves_and_can_be_edited_not_dropped(tmp_path):
    got = roles.roles(tmp_path)
    assert [r["slug"] for r in got] == ["taskmaster", "grunt"] and all(r["builtin"] for r in got)
    assert got[0]["name"] == "Taskmaster" and got[0]["model"] == "elder" and got[1]["name"] == "Grunt"
    roles.save(tmp_path, "Grunt", "warrior", 3, "Be quick.", "grunt")
    grunt = roles.role(tmp_path, "grunt")
    assert (grunt["model"], grunt["max_parallel"], grunt["instruction"]) == ("warrior", 3, "Be quick.")
    for slug in roles.BUILTIN:
        with pytest.raises(ValueError, match="edited, not deleted"):
            roles.drop(tmp_path, slug)


def test_each_task_type_has_a_role_grunt_by_default_and_a_dropped_role_sends_them_back(tmp_path):
    assert roles.TASK_KINDS[:5] == ("code", "tests", "docs", "text", "research")                 # the tags a team splits by follow
    assert set(roles.kinds(tmp_path).values()) == {"grunt"}
    slug = roles.save(tmp_path, "Writer", "laborer", 2, "Plain words.")
    roles.set_kind(tmp_path, "docs", slug)
    roles.set_kind(tmp_path, "text", slug)
    assert roles.role_for(tmp_path, "docs")["slug"] == slug and roles.role_for(tmp_path, "code")["slug"] == "grunt"
    assert roles.role_for(tmp_path, "")["slug"] == "grunt" and roles.role_for(tmp_path, "nonsense")["slug"] == "grunt"
    assert sorted(roles.drop(tmp_path, slug)) == ["docs", "text"]
    assert roles.role(tmp_path, slug) is None and roles.role_for(tmp_path, "docs")["slug"] == "grunt"
    with pytest.raises(ValueError, match="No task type"):
        roles.set_kind(tmp_path, "poetry", "grunt")
    with pytest.raises(ValueError, match="No agent"):
        roles.set_kind(tmp_path, "docs", "ghost")
    with pytest.raises(ValueError, match="does not do tasks"):
        roles.set_kind(tmp_path, "docs", "taskmaster")


# -- spec 36 §3: a role is who; the Target is how much thinking; an agent takes its task types --------------------

def test_the_model_list_is_by_target_and_the_three_tiers_and_a_hand_set_model_only_for_its_role(tmp_path):
    got = roles.models()
    assert got[0] == {"id": "", "label": "By Target"}
    assert [m["label"].split(" · ")[0] for m in got[1:]] == ["Veteran", "Seasoned", "Novice"]       # the tiers in today's words
    assert " · " in got[1]["label"]                                    # the harness's model, small: Veteran · opus
    (tmp_path / "roles").mkdir()
    (tmp_path / "roles" / "old-hand.md").write_text("---\nname: Old hand\nmodel: opus\nmax_parallel: 1\n---\n")
    r = roles.role(tmp_path, "old-hand")
    assert r["model"] == "opus" and roles.hand_set(r) and not roles.hand_set(roles.role(tmp_path, "grunt"))
    mine = roles.models(r["model"])
    assert mine[-1] == {"id": "opus", "label": "opus (set by hand)"} and len(mine) == 5
    assert roles.save(tmp_path, "Old hand", "opus", 2, "", "old-hand") == "old-hand"      # kept, never changed silently
    assert roles.role(tmp_path, "old-hand")["model"] == "opus"
    with pytest.raises(ValueError, match="from the list"):
        roles.save(tmp_path, "Old hand", "sonnet", 2, "", "old-hand")                  # a new raw model: not on the list


def test_an_agent_takes_its_task_types(tmp_path):
    a = roles.save(tmp_path, "Scribe", "", 1, "", None, ["docs", "text"])
    assert {k for k, v in roles.kinds(tmp_path).items() if v == a} == {"docs", "text"}
    b = roles.save(tmp_path, "Tester", "", 1, "", None, ["tests", "docs"])            # docs moves from Scribe
    kinds = roles.kinds(tmp_path)
    assert kinds["docs"] == b and kinds["tests"] == b and kinds["text"] == a and kinds["code"] == "grunt"
    roles.save(tmp_path, "Scribe", "", 1, "", a, [])                                  # unticked: back to Grunt
    assert roles.kinds(tmp_path)["text"] == "grunt" and roles.kinds(tmp_path)["docs"] == b
    roles.save(tmp_path, "Tester", "", 1, "", b)                                      # no kinds: as they were
    assert roles.kinds(tmp_path)["tests"] == b
    for slug in ("grunt", "taskmaster"):
        with pytest.raises(ValueError):
            roles.save(tmp_path, slug.capitalize(), "elder", 1, "", slug, ["code"])
    with pytest.raises(ValueError, match="No task type"):
        roles.save(tmp_path, "Tester", "", 1, "", b, ["poetry"])


def test_a_roles_craft_is_its_race_engineering_by_default_and_the_built_in_two_are_orks(tmp_path):
    assert roles.RACES == {"engineering": "peon", "design": "elf", "data": "goblin", "marketing": "gnome", "product": "lich"}   # product: undead
    slug = roles.save(tmp_path, "Layout", "elder", 1, "", craft="design")
    assert "craft: design" in (tmp_path / "roles" / f"{slug}.md").read_text() and roles.role(tmp_path, slug)["craft"] == "design"
    assert roles.save(tmp_path, "Layout", "warrior", 1, "", slug) == slug and roles.role(tmp_path, slug)["craft"] == "design"   # kept
    assert roles.role(tmp_path, roles.save(tmp_path, "Coder", "", 2))["craft"] == "engineering"                           # a new one's
    (tmp_path / "roles" / "old.md").write_text("---\nname: Old\nmodel: warrior\nmax_parallel: 1\n---\n")
    assert roles.role(tmp_path, "old")["craft"] == "engineering"                                                          # before crafts
    (tmp_path / "roles" / "odd.md").write_text("---\nname: Odd\nmodel: warrior\nmax_parallel: 1\ncraft: sorcery\n---\n")
    assert roles.role(tmp_path, "odd")["craft"] == "engineering"
    assert roles.role(tmp_path, "taskmaster")["craft"] == roles.role(tmp_path, "grunt")["craft"] == "engineering"
    with pytest.raises(ValueError, match="engineering, design, data or marketing"):
        roles.save(tmp_path, "Seer", "", 1, craft="sorcery")
    with pytest.raises(ValueError, match="orks"):
        roles.save(tmp_path, "Grunt", "", 8, slug="grunt", craft="design")
    assert roles.save(tmp_path, "Grunt", "", 8, slug="grunt", craft="engineering") == "grunt"


def test_a_tasks_head_is_who_runs_it_at_the_tier_it_runs_at(tmp_path):
    seer = roles.save(tmp_path, "Seer", "", 1, takes=["research"], craft="data")
    assert roles.task_head(tmp_path, {"kind": "research", "tier": "warrior"}, "thrift") == {"craft": "data", "race": "goblin", "tier": "laborer"}
    assert roles.task_head(tmp_path, {"kind": "code", "tier": "elder"}, "balance") == {"craft": "engineering", "race": "peon", "tier": "elder"}
    ran = {"kind": "code", "tier": "elder", "role": seer, "ran_tier": "warrior"}                          # what it ran as, at what it ran at
    assert roles.task_head(tmp_path, ran, "quality", roles.known(tmp_path)) == {"craft": "data", "race": "goblin", "tier": "warrior"}
    assert roles.task_head(tmp_path, {"role": "gone", "tier": "laborer"}, "balance")["race"] == "peon"     # a dropped role: Grunt's


def test_every_seat_of_a_party_wears_its_partys_race_and_its_leader_that_races_higher_form(tmp_path):
    """Spec 99 §1.4 (decisions §158.4–§158.5, §162): knights for Product and Game design, orks for Tech, elves for Design and Art, goblins for Run and LiveOps, gnomes for
    Marketing, the undead for Release; the leader the shaman, dryad, imp, fairy, unicorn or lich. A role's own race and craft no longer choose its head in a party."""
    assert roles.PARTY_RACES == {"product": ("knight", "unicorn"), "game-design": ("knight", "unicorn"), "tech": ("peon", "shaman"), "design": ("elf", "dryad"),
                                 "art": ("elf", "dryad"), "run": ("goblin", "imp"), "liveops": ("goblin", "imp"), "marketing": ("gnome", "fairy"), "release": ("skeleton", "lich")}
    grunt = roles.role(tmp_path, "grunt")
    manager = {"slug": "release-manager", "craft": "product", "race": "skeleton", "model": "warrior"}
    for party, (members, leader) in roles.PARTY_RACES.items():
        for tier in roles.TIERS:
            assert (roles.RACE_FILES / f"{members}-{tier}.png").is_file() and (roles.RACE_FILES / f"{leader}-{tier}.png").is_file(), (party, tier)
            assert roles.head({**grunt, "model": tier}, "balance", party=party)["race"] == members
            assert roles.head({**manager, "model": tier}, "balance", party=party, lead=True)["race"] == leader
    assert roles.head({"slug": "copywriter", "craft": "marketing", "model": "warrior"}, "balance", party="product") == {"craft": "marketing", "race": "knight", "tier": "warrior"}
    assert roles.head(manager, "balance") == {"craft": "product", "race": "skeleton", "tier": "warrior"}          # alone, as before
    assert roles.head(manager, "balance", party="") == roles.head(manager, "balance", party="nope")              # a party with no craft: the role's own
    taskmaster = roles.role(tmp_path, "taskmaster")
    assert roles.head(taskmaster, "balance", party="tech", lead=True)["race"] == "peon"                         # the Taskmaster and the Orkmaster are orks in any party
    assert roles.head({"slug": "orkmaster", "model": "warrior"}, "balance", party="release")["race"] == "peon"


def test_a_tasks_head_in_a_party_wears_the_partys_race_and_the_leaders_its_higher_form(tmp_path):
    seer = roles.save(tmp_path, "Seer", "", 1, takes=["research"], craft="data")
    task = {"kind": "research", "tier": "warrior", "role": seer}
    assert roles.task_head(tmp_path, task, "balance", party="run", leader="analyst")["race"] == "goblin"
    assert roles.task_head(tmp_path, task, "balance", party="product")["race"] == "knight"                     # a goblin's role in the knights' party
    assert roles.task_head(tmp_path, task, "balance", party="product", leader=seer)["race"] == "unicorn"
    assert roles.task_head(tmp_path, {"kind": "code", "tier": "warrior"}, "balance", party="tech", leader="architect")["race"] == "peon"   # a Grunt is an ork in Tech
    assert roles.task_head(tmp_path, task, "balance") == {"craft": "data", "race": "goblin", "tier": "warrior"}   # no party: as before
