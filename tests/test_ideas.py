"""The board's tracks and ideas as Wiki pages (spec 29 §2, spec 29a §2): round trips, General, order, hand edits,
the librarian's skip, the state beside the page, and the secret store."""
from __future__ import annotations

import os
import stat

import pytest

from orkboard.realm import idea_secrets, ideas


@pytest.fixture
def root(tmp_path):
    return tmp_path / "llm-wiki" / "general"


def test_general_is_made_once_and_the_wiki_is_scaffolded(root):
    (t,) = ideas.tracks(root)
    assert (t["slug"], t["title"], t["count"]) == ("general", "General", 0)
    assert (root / "WIKI.md").exists() and (root / "pages/tracks/index.md").exists()
    assert [x["slug"] for x in ideas.tracks(root)] == ["general"]
    page = (root / "pages/tracks/general.md").read_text()
    assert page.startswith("---\nowner: board\nkind: track\norder: 1\n---\n# General\n")


def test_a_dropped_idea_is_its_text_under_gist_in_the_fixed_order(root, tmp_path):
    state = tmp_path / ".orkcraft"
    slug = ideas.add_idea(root, "Dark mode for the board\nso it reads at night", state_dir=state)
    assert slug == "dark-mode-for-the-board"
    page = ideas.idea_page(root, slug)
    assert [n for n, _t in page.sections] == list(ideas.SECTIONS)
    assert page.section("Gist") == "Dark mode for the board\nso it reads at night"
    assert (page.get("owner"), page.get("kind"), page.get("track"), page.get("order")) == ("board", "idea", "general", "1")
    assert ideas.state(state, slug)["state"] == "raw"
    assert "state" not in dict(page.meta)                       # the state lives beside the page, never in it
    (i,) = ideas.ideas(root)
    assert i["thesis"] == "Dark mode for the board" and i["size"] == ""
    assert "dark-mode-for-the-board.md" in (root / "pages/ideas/index.md").read_text()
    assert ideas.add_idea(root, "Dark mode for the board") == "dark-mode-for-the-board-2"


def test_a_write_keeps_what_it_does_not_know_and_a_hand_edit_is_read_as_written(root):
    slug = ideas.add_idea(root, "Export to CSV")
    path = root / "pages/ideas" / f"{slug}.md"
    text = path.read_text().replace("kind: idea\n", "kind: idea\naliases: [csv, export]\n")
    text = text.replace("## Why\n", "## Why\nPeople ask for it **weekly**.\n")
    text += "\n## Notes of mine\nkeep me\n"
    path.write_text(text)
    assert ideas.idea_page(root, slug).section("Why") == "People ask for it **weekly**."
    ideas.set_section(root, slug, "Risks", "- big files\n## sneaky heading")
    page = ideas.idea_page(root, slug)
    assert page.get("aliases") == "[csv, export]" and page.section("Notes of mine") == "keep me"
    assert page.section("Risks") == "- big files\n### sneaky heading"       # a section never splits the page
    assert [n for n, _t in page.sections][-1] == "Notes of mine"
    with pytest.raises(ValueError):
        ideas.set_section(root, slug, "Nonsense", "x")


def test_the_keepers_update_writes_known_sections_and_appends_decisions(root):
    slug = ideas.add_idea(root, "x")
    assert ideas.update(root, slug, {"Why": "because", "Bogus": "no", "Decisions": "no"}, ["one", "two"]) \
        == ["Why", "Decisions"]
    ideas.update(root, slug, {}, ["three"])
    page = ideas.idea_page(root, slug)
    assert page.section("Why") == "because" and page.section("Bogus") == ""
    assert [ln.split(": ", 1)[1] for ln in page.section("Decisions").splitlines()] == ["one", "two", "three"]


def test_drop_takes_the_page_and_its_state(root, tmp_path):
    state = tmp_path / ".orkcraft"
    slug = ideas.add_idea(root, "go away", state_dir=state)
    ideas.add_turn(state, slug, "you", "hello")
    ideas.drop(root, slug, state)
    assert ideas.idea_page(root, slug) is None and not (state / "ideas" / slug).exists()


def test_a_goal_has_its_route_and_the_states_of_its_way_beside_its_page(tmp_path):
    """Spec 99 §4: the states `routed` · `talk` · `decided` · `sections`, and `route` (the parties, in order) with `route_how` in the state; an older state reads none."""
    assert ideas.STATES[-5:] == ("routed", "talk", "decided", "sketch", "sections")
    assert ideas.STATE_DEFAULT["route"] == [] and ideas.STATE_DEFAULT["route_how"] == {}
    state = tmp_path / "state"
    assert ideas.state(state, "a")["route"] == []
    ideas.save_state(state, "a", state="routed", route=[{"party": "tech", "leader": "architect"}], route_how={"by": "party", "short": False})
    got = ideas.state(state, "a")
    assert got["state"] == "routed" and got["route"] == [{"party": "tech", "leader": "architect"}] and got["route_how"]["by"] == "party"
    ideas.save_state(state, "a", state="talk")
    assert ideas.state(state, "a")["route"] and ideas.state(state, "a")["state"] == "talk"          # the rest of the file is kept
    for way in ("decided", "sections"):
        assert ideas.save_state(state, "a", state=way)["state"] == way and ideas.state(state, "a")["state"] == way


def test_a_secret_goes_to_the_store_never_to_the_plan(tmp_path):
    state = tmp_path / ".orkcraft"
    assert idea_secrets.put(state, "idea", "t1", "sk-123") == "file"          # the tests keep the keychain out
    assert idea_secrets.get(state, "idea", "t1") == "sk-123"
    assert stat.S_IMODE(os.stat(state / "secrets.json").st_mode) == 0o600
    assert "secrets.json" in (state / ".gitignore").read_text()
    idea_secrets.forget(state, "idea", ["t1"])
    assert idea_secrets.get(state, "idea", "t1") is None
    with pytest.raises(ValueError):
        idea_secrets.put(state, "../x", "t1", "v")


def test_a_goal_has_a_short_name_from_its_words_then_the_reading_unless_the_person_titled_it(root):
    # spec 41 §3
    slug, _new = ideas.save_goal(root, None, about="Давай сделаем оплату картой. Stripe first.")
    g = next(t for t in ideas.tracks(root) if t["slug"] == slug)
    assert g["short"] == "Сделаем оплату картой"
    ideas.write_goal_reading(root, slug, "Summary.", {}, [], title="Card payments with Stripe", short="Card payments")
    assert next(t for t in ideas.tracks(root) if t["slug"] == slug)["short"] == "Card payments"
    ideas.save_goal(root, slug, title="Pay by card", about="Payments.")
    ideas.write_goal_reading(root, slug, "Summary.", {}, [], title="Another title", short="Another")
    assert next(t for t in ideas.tracks(root) if t["slug"] == slug)["short"] == "Pay by card"     # the person's title
    idea = ideas.add_idea(root, "Let's export the runs to CSV please", slug)
    assert next(i for i in ideas.ideas(root) if i["slug"] == idea)["short"] == "Export the runs to CSV"


def test_a_page_keeps_the_keys_it_does_not_know_and_an_answered_question_is_not_open(tmp_path):
    root = tmp_path / "wiki"
    slug = ideas.add_idea(root, "a goal")
    ideas.set_meta(root, slug, phase="work", by="Codex", spec="docs/specs/9-x.md")
    ideas.set_section(root, slug, "Open questions", "- One? (a / b)\n  - Answered: a (the person, 2026-11-06)\n- Two?")
    page = ideas.idea_page(root, slug)
    assert [page.get(k) for k in ("phase", "by", "spec")] == ["work", "Codex", "docs/specs/9-x.md"]
    assert ideas.items(page.section("Open questions")) == ["Two?"]

