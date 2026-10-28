"""The lens a new idea is written with (decisions §53; realm/idea_lens.py, realm/code_map.py): the goal's party offers its
crafts' lenses, its leader's open first; what the person points at — parts of the repository, a screen with areas marked,
a segment and its pain — is kept with the idea and given to the keeper with its text."""
from __future__ import annotations

import base64
import json
import sys

import pytest

from orkboard.gui.board_host import CommandError, Orkboard
from orkboard.realm import code_map, idea_lens, ideas

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 32


@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def test_the_repository_s_parts_and_what_each_uses_python_and_javascript_relative_and_absolute(tmp_path):
    (tmp_path / "app" / "core").mkdir(parents=True)
    (tmp_path / "app" / "__init__.py").write_text("")
    (tmp_path / "app" / "core" / "__init__.py").write_text("")
    (tmp_path / "app" / "core" / "bus.py").write_text("import json\n")
    (tmp_path / "app" / "main.py").write_text("from app.core import bus\nfrom .core.bus import x\nimport requests\n")
    (tmp_path / "web" / "lib").mkdir(parents=True)
    (tmp_path / "web" / "lib" / "x.js").write_text("export const x = 1;\n")
    (tmp_path / "web" / "app.js").write_text('import { x } from "./lib/x.js";\nimport y from "react";\n')
    (tmp_path / ".orkcraft").mkdir()
    (tmp_path / ".orkcraft" / "kept.py").write_text("import app\n")                 # the machine's own: not read
    (tmp_path / "node_modules" / "react").mkdir(parents=True)
    (tmp_path / "node_modules" / "react" / "index.js").write_text("")
    got = {p["path"]: p for p in code_map.parts(tmp_path)}
    assert sorted(got) == ["app", "app/core", "web", "web/lib"]
    assert got["app"]["uses"] == ["app/core"] and got["app/core"]["used_by"] == ["app"]
    assert got["web"]["uses"] == ["web/lib"] and got["web/lib"]["used_by"] == ["web"] and got["web"]["files"] == ["app.js"]
    assert got["app/core"]["count"] == 2


def test_the_party_offers_its_crafts_lenses_and_the_leader_s_is_open_first(host):
    slug = host.command("ideas.goal_save", {"about": "Settings people can find.", "craft": "engineering", "leader": "architect",
                                            "team": ["ui-kit", "reviewer"]})["slug"]
    got = host.command("ideas.lens", {"track": slug})
    assert [x["id"] for x in got["lenses"]] == ["text", "code", "screen"] and got["default"] == "code"   # no product manager: no pain
    assert next(x for x in got["lenses"] if x["id"] == "code")["by"] == "Architect"
    plain = host.command("ideas.goal_save", {"about": "Anything.", "craft": "engineering", "team": ["artist"]})["slug"]
    got = host.command("ideas.lens", {"track": plain})
    assert got["default"] == "text" and [x["id"] for x in got["lenses"]] == ["text", "screen"]   # the Taskmaster leads: text first
    pm = host.command("ideas.goal_save", {"about": "Who buys.", "craft": "product", "leader": "product-manager"})["slug"]
    assert host.command("ideas.lens", {"track": pm})["default"] == "pain"


def test_what_the_lens_points_at_is_kept_with_the_idea_shown_with_its_page_and_given_to_the_keeper(host, fake_repo):
    slug = host.command("ideas.goal_save", {"about": "Orders that do not get lost.", "craft": "product", "leader": "product-manager",
                                            "team": ["ui-kit"]})["slug"]
    (fake_repo / "src").mkdir(exist_ok=True)
    (fake_repo / "src" / "orders.py").write_text("x = 1\n")
    lens = [{"kind": "pain", "segment": "Shop owners", "pain": "Orders get lost between the phone and the till"},
            {"kind": "code", "paths": ["src"], "note": "Keep each order until the till says it has it"},
            {"kind": "screen", "image": {"data": base64.b64encode(PNG).decode()}, "name": "Orders",
             "marks": [{"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.1, "note": "Say which orders wait"}, {"x": 0.9, "y": 0.9, "w": 0, "h": 0.1}]}]
    idea = host.command("ideas.add", {"text": "Orders are never lost", "track": slug, "priority": "low", "lens": lens})["slug"]
    page = host.command("ideas.page", {"slug": idea})
    kinds = [a["kind"] for a in page["lens"]]
    assert kinds == ["pain", "code", "screen"]
    screen = page["lens"][2]
    assert screen["name"] == "Orders" and len(screen["marks"]) == 1 and screen["path"].startswith(".orkcraft/screens/")   # an empty mark is left out
    prompt = host.ideas.keeper.draft_prompt(host.ideas.root(), idea)
    assert "Whom it is for: Shop owners; what hurts them: Orders get lost between the phone and the till" in prompt
    assert "These parts of the repository (read them first): src. What to change there: Keep each order" in prompt
    assert 'The screen "Orders"' in prompt and "from 10 % to 60 % across and 20 % to 30 % down: Say which orders wait" in prompt
    got = host.command("ideas.lens", {"track": slug})                                      # the project keeps them for the next idea
    assert got["segments"] == [{"segment": "Shop owners", "pains": ["Orders get lost between the phone and the till"]}]
    assert got["screens"][0]["name"] == "Orders" and got["default"] == "pain"
    shown = host.command("ideas.lens_screen", {"id": got["screens"][0]["id"]})
    assert base64.b64decode(shown["data"]) == PNG and shown["type"] == "image/png"
    again = host.command("ideas.add", {"text": "The same screen again", "track": slug, "priority": "low",
                                       "lens": [{"kind": "screen", "screen": got["screens"][0]["id"], "marks": []}]})["slug"]
    assert host.command("ideas.page", {"slug": again})["lens"][0]["name"] == "Orders"
    assert len(idea_lens.screens(host.ideas.state_dir)) == 1


def test_the_lens_points_at_the_repository_only_never_at_a_secret_or_the_machine_s_own(host, fake_repo):
    slug = host.command("ideas.goal_save", {"about": "x", "craft": "engineering", "leader": "architect"})["slug"]
    (fake_repo / ".env").write_text("KEY=1\n")
    for paths, why in ((["../etc"], "Not a part"), ([".env"], "Not a part"), ([".orkcraft"], "Not a part"), (["nowhere"], "Not a part")):
        with pytest.raises(CommandError, match=why):
            host.command("ideas.add", {"text": "x", "track": slug, "priority": "low", "lens": [{"kind": "code", "paths": paths}]})
    with pytest.raises(CommandError, match="code, a screen or a pain"):
        host.command("ideas.add", {"text": "x", "track": slug, "priority": "low", "lens": [{"kind": "wish"}]})
    with pytest.raises(CommandError, match="screen is gone"):
        host.command("ideas.add", {"text": "x", "track": slug, "priority": "low", "lens": [{"kind": "screen", "screen": "abc"}]})
    assert not [i for i in ideas.ideas(host.ideas.root()) if i["track"] == slug]           # nothing added
    assert host.command("ideas.lens_code", {})["parts"]                                      # the fake repository's own parts


# -- spec 102 §1.3: a pain's place ---------------------------------------------------------------------------------------------------------------

def test_a_pain_kept_before_has_no_place_and_stays_a_string_in_the_file_every_reader_reads_on(tmp_path):
    state = tmp_path / ".orkcraft"
    state.mkdir()
    (state / "segments.json").write_text('{"segments": [{"segment": "Shop owners", "pains": ["Orders get lost", "Refunds take a week"]}]}')   # as kept before
    assert idea_lens.segments(state) == [{"segment": "Shop owners", "pains": ["Orders get lost", "Refunds take a week"]}]
    assert idea_lens.segments_placed(state) == [{"segment": "Shop owners", "pains": [{"text": "Orders get lost", "on": ""}, {"text": "Refunds take a week", "on": ""}]}]
    idea_lens.keep_segment(state, "Shop owners", "New one")                                  # keeping a pain with no place writes the strings it always wrote
    assert json.loads((state / "segments.json").read_text())["segments"][0]["pains"] == ["New one", "Orders get lost", "Refunds take a week"]


def test_a_pinned_pain_is_an_object_in_the_file_the_lens_still_offers_its_text_and_keeping_it_again_keeps_its_place(tmp_path):
    state = tmp_path / ".orkcraft"
    state.mkdir()
    idea_lens.keep_segment(state, "Shop owners", "Orders get lost", on="orders")
    idea_lens.keep_segment(state, "Shop owners", "Refunds take a week")
    assert json.loads((state / "segments.json").read_text())["segments"][0]["pains"] == ["Refunds take a week", {"text": "Orders get lost", "on": "orders"}]
    assert idea_lens.segments(state) == [{"segment": "Shop owners", "pains": ["Refunds take a week", "Orders get lost"]}]
    idea_lens.keep_segment(state, "shop owners", "ORDERS get lost")                          # an idea that brings the same pain again: first, same place, the person's words
    assert idea_lens.segments_placed(state) == [{"segment": "Shop owners", "pains": [{"text": "ORDERS get lost", "on": "orders"}, {"text": "Refunds take a week", "on": ""}]}]
    idea_lens.keep_segment(state, "Shop owners", "Orders get lost", on="step:2")             # moved
    assert idea_lens.segments_placed(state)[0]["pains"][0] == {"text": "Orders get lost", "on": "step:2"}
    idea_lens.keep_segment(state, "Shop owners", "Orders get lost", on="")                   # taken off its place
    assert idea_lens.segments_placed(state)[0]["pains"][0] == {"text": "Orders get lost", "on": ""}
    assert json.loads((state / "segments.json").read_text())["segments"][0]["pains"] == ["Orders get lost", "Refunds take a week"]


def test_an_idea_s_pain_kept_with_it_does_not_move_a_pinned_one_off_its_screen(host):
    slug = host.command("ideas.goal_save", {"about": "x", "craft": "product", "leader": "product-manager"})["slug"]
    idea_lens.keep_segment(host.ideas.state_dir, "Shop owners", "Orders get lost", on="orders")
    host.command("ideas.add", {"text": "Fix it", "track": slug, "priority": "low",
                               "lens": [{"kind": "pain", "segment": "Shop owners", "pain": "Orders get lost"}]})
    assert idea_lens.segments_placed(host.ideas.state_dir)[0]["pains"] == [{"text": "Orders get lost", "on": "orders"}]
    assert host.command("ideas.lens", {"track": slug})["segments"] == [{"segment": "Shop owners", "pains": ["Orders get lost"]}]
