"""Spec 151 C (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md; decisions §255.5–§255.6): the Board's rules for any AI tool, written into the project.

The block into a missing file and into one with the person's text (kept byte for byte), written again in place and never twice, `CLAUDE.md`'s import, the wiki's own pointer kept and added to, each role
file holding its prompt's fixed text, a changed file written back and said, nothing written without the yes, the block at most 60 lines. No model is called."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from orkboard.core import idea_accept, idea_sections, idea_talk
from orkboard.gui import agent_rules_switch
from orkboard.gui.board_host import Orkboard
from orkboard.realm import agent_rules, agent_rules_text, goal_route, goal_team, ideas, library, roles, wiki_rules

WIKI = "llm-wiki/general"
DECISIONS = "docs/decisions.md"
PERSON = "# Our rules\n\nUse tabs.\n\nNever touch the vendor folder.\n"


def project(tmp_path: Path, crafts=("engineering", "design")) -> Path:
    """A project folder with the Board's folder holding a party for each craft."""
    root = tmp_path / "shop"
    wiki = root / WIKI
    wiki.mkdir(parents=True)
    for title, craft, leader in (("Tech", "engineering", "architect"), ("Design", "design", "product-designer"), ("Product", "product", "product-manager")):
        if craft in crafts:
            slug, _new = ideas.save_goal(wiki, None, title, "About " + title, None, "normal", craft=craft)
            goal_team.set_team(wiki, slug, [], leader=leader)
    return root


def write(root: Path, **more) -> list[str]:
    return agent_rules.write(root, WIKI, decisions=DECISIONS, **more)


def check(root: Path) -> list[dict]:
    return agent_rules.check(root, WIKI, decisions=DECISIONS)


def test_the_block_goes_into_a_missing_file_with_the_one_line_and_every_file_is_made(tmp_path):
    root = project(tmp_path)
    written = write(root)
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith(agent_rules_text.OWN_LINE + "\n\n<!-- orkboard:begin schema=2 hash=") and text.endswith("<!-- orkboard:end -->\n")
    assert f"`{WIKI}/pages/ideas/<slug>.md`" in text and f"`{DECISIONS}`" in text and f"`{WIKI}/BOARD.md`" in text
    assert written == ["AGENTS.md", "CLAUDE.md", f"{WIKI}/BOARD.md", f"{WIKI}/AGENTS.md", f"{WIKI}/CLAUDE.md",
                       *[f"{WIKI}/roles/{i}.md" for i in ("orkmaster", "tech-leader", "design-leader", "taskmaster", "grunt")],
                       *[f".claude/agents/ork-{i}.md" for i in ("orkmaster", "tech-leader", "design-leader", "taskmaster", "grunt")], ".claude/skills/orkboard/SKILL.md"]
    assert check(root) == [] and agent_rules.has_rules(root)


def test_the_persons_own_text_above_and_below_the_block_is_kept_byte_for_byte_and_the_block_is_written_in_place(tmp_path, monkeypatch):
    root = project(tmp_path)
    (root / "AGENTS.md").write_bytes("Mine, above — ünï.\r\n\r\n".encode("utf-8"))
    write(root)
    first = (root / "AGENTS.md").read_bytes()
    assert first.startswith("Mine, above — ünï.\r\n\r\n".encode("utf-8")) and b"\r\n<!-- orkboard:end -->\r\n" in first
    below = "\r\n\r\nMine, below.\r\n  indented\twith a tab, no newline at the end".encode("utf-8")
    (root / "AGENTS.md").write_bytes(first + below)
    monkeypatch.setattr(agent_rules_text, "agents_body", lambda wiki, decisions: "## The Board (Orkboard)\n\nA newer text.")      # the package's text changes
    assert [f["what"] for f in check(root) if f["path"] == "AGENTS.md"] == ["outdated"]
    assert write(root, only={"AGENTS.md"}) == ["AGENTS.md"]
    now = (root / "AGENTS.md").read_bytes()
    assert now.startswith("Mine, above — ünï.\r\n\r\n".encode("utf-8")) and now.endswith(below) and b"A newer text." in now and now.count(b"orkboard:begin") == 1
    assert [f for f in check(root) if f["path"] == "AGENTS.md"] == []


def test_writing_twice_changes_nothing(tmp_path):
    root = project(tmp_path)
    write(root)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    stamps = {p: p.stat().st_mtime_ns for p in before}
    assert write(root) == []
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before and {p: p.stat().st_mtime_ns for p in before} == stamps


def test_a_person_file_without_the_block_gets_it_at_the_end_after_a_blank_line_and_claudes_block_imports_agents(tmp_path):
    root = project(tmp_path)
    (root / "CLAUDE.md").write_text(PERSON.rstrip("\n"), encoding="utf-8")                  # no newline at the end
    write(root)
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith(PERSON.rstrip("\n") + "\n\n<!-- orkboard:begin") and "@AGENTS.md" in text and agent_rules_text.OWN_WIN in text
    assert text.count("@AGENTS.md") == 1


def test_a_wiki_that_has_its_own_pointer_keeps_it_and_gets_the_boards_block_added(tmp_path):
    root = project(tmp_path)
    pointer = wiki_rules.POINTER.format(topic="the project's knowledge")
    (root / WIKI / "CLAUDE.md").write_text(pointer, encoding="utf-8")
    write(root)
    text = (root / WIKI / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith(pointer) and agent_rules_text.POINTER in text and text.count("orkboard:begin") == 1
    assert (root / WIKI / "AGENTS.md").read_text(encoding="utf-8").count(agent_rules_text.POINTER) == 1          # a folder without one: the block alone


def test_each_role_file_holds_its_prompts_fixed_text_and_its_front_matter(tmp_path):
    root = project(tmp_path, crafts=("engineering", "design", "product"))
    write(root)
    roles_dir = root / WIKI / "roles"
    assert sorted(p.stem for p in roles_dir.glob("*.md")) == sorted(["orkmaster", "tech-leader", "design-leader", "product-leader", "taskmaster", "grunt"])
    orkmaster = (roles_dir / "orkmaster.md").read_text(encoding="utf-8")
    assert goal_route.instruction() in orkmaster and idea_sections.join_instruction() in orkmaster
    for craft in ("tech", "design", "product"):
        text = (roles_dir / f"{craft}-leader.md").read_text(encoding="utf-8")
        assert idea_talk.instruction(craft) in text and idea_sections.instruction(craft) in text and "## Accepting a step\n\n" + idea_accept.instruction(craft) in text and "## What it reads" in text
        assert f"seat: leader\ncraft: {craft}\nrace: " in text and "schema: 2\nhash: " in text
    assert "race: elf\n" in (roles_dir / "design-leader.md").read_text(encoding="utf-8") and "race: knight\n" in (roles_dir / "product-leader.md").read_text(encoding="utf-8")
    assert "race: ork\n" in (roles_dir / "tech-leader.md").read_text(encoding="utf-8")
    for seat in ("taskmaster", "grunt"):
        assert roles.instruction(seat) in (roles_dir / f"{seat}.md").read_text(encoding="utf-8")
    assert f"`{WIKI}/journals/tech.md`" not in (roles_dir / "grunt.md").read_text(encoding="utf-8")
    agent = (root / ".claude/agents/ork-tech-leader.md").read_text(encoding="utf-8")
    assert agent.startswith("---\nname: ork-tech-leader\ndescription: \"") and idea_talk.instruction("tech") in agent and f"Read `{WIKI}/BOARD.md` first" in agent
    skill = (root / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: orkboard\ndescription: \"" + agent_rules_text.SKILL_DESCRIPTION + "\"\n") and f"{WIKI}/BOARD.md" in skill


def test_a_prompt_is_built_from_its_seats_function():
    ps = [{"slug": "tech", "title": "Tech"}, {"slug": "design", "title": "Design"}]
    assert goal_route.prompt("Add a  score board", ps) == goal_route.instruction("Add a score board", "- tech: Tech\n- design: Design")
    assert "Rules:\n" in idea_talk.instruction("tech") and idea_talk.instruction("tech") != idea_talk.instruction("design")        # the lens is the craft's
    assert idea_sections.instruction("tech") == idea_sections.instruction("design")
    assert roles.TOLD == {seat: roles.instruction(seat) for seat in roles.BUILTIN} and roles.instruction("a-role-of-the-projects") == ""


def test_board_md_says_the_real_format_of_part_a(tmp_path):
    from orkboard.realm import goal_phase, idea_page, idea_questions
    root = project(tmp_path)
    write(root)
    text = (root / WIKI / "BOARD.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- orkboard:file schema=2 hash=") and "Orkboard's file" in text
    for key in goal_phase.MANAGED + ("spec",):
        assert f"`{key}`" in text, key
    for phase in goal_phase.PHASES:
        assert f"- `{phase}`: " in text
    assert idea_questions.line({"ask": "Which store first?", "choices": ["App Store", "Google Play"], "pick": 0, "why": "most of its users are on iPhone"}) in text
    assert idea_questions.answer_line("App Store", "2026-11-06") in text
    assert all(f"*{s}*" in text for s in idea_page.SECTIONS) and "<short commit> · <n> files · green" in text and "board: <title> — <what>" in text and "orkboard/taken" in text
    assert not re.search(r"\borcs?\b|orchestrat", text, re.I)                                              # ork, never orc; orkestration, never orchestration


def test_a_block_or_file_changed_by_hand_is_found_and_written_back_and_said_once(tmp_path):
    root = project(tmp_path)
    write(root)
    role = root / WIKI / "roles/tech-leader.md"
    role.write_text(role.read_text(encoding="utf-8").replace("You are not here to agree.", "You agree."), encoding="utf-8")
    block = (root / "AGENTS.md").read_text(encoding="utf-8")
    (root / "AGENTS.md").write_text(block.replace("Main is the person's.", "Main is anyone's."), encoding="utf-8")
    assert {(f["path"], f["what"]) for f in check(root)} == {(f"{WIKI}/roles/tech-leader.md", "changed"), ("AGENTS.md", "changed")}
    got = agent_rules.refresh(root, WIKI, decisions=DECISIONS)
    assert sorted(got["written"]) == sorted(["AGENTS.md", f"{WIKI}/roles/tech-leader.md"])
    assert "roles/tech-leader.md was changed by hand: Orkboard's own is written back; a project's own role is made on Agents." in got["by_hand"]
    assert "AGENTS.md was changed by hand: Orkboard's own is written back; a project's own role is made on Agents." in got["by_hand"]
    assert check(root) == [] and "Main is the person's." in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert agent_rules.refresh(root, WIKI, decisions=DECISIONS) == {"written": [], "by_hand": []}                  # said once: the next start finds nothing


def test_an_outdated_file_is_written_again_without_a_word_and_a_project_without_the_rules_is_left_alone(tmp_path, monkeypatch):
    root = project(tmp_path)
    assert agent_rules.refresh(root, WIKI, decisions=DECISIONS) == {"written": [], "by_hand": []} and not (root / "AGENTS.md").exists()
    write(root)
    monkeypatch.setattr(agent_rules_text, "skill_body", lambda wiki: "# A newer skill\n")
    assert [f["what"] for f in check(root)] == ["outdated"]
    got = agent_rules.refresh(root, WIKI, decisions=DECISIONS)
    assert got == {"written": [".claude/skills/orkboard/SKILL.md"], "by_hand": []} and "A newer skill" in (root / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8")


def test_a_file_at_an_orkboard_path_that_is_the_persons_own_stays_and_a_broken_block_is_left(tmp_path):
    root = project(tmp_path)
    (root / ".claude/skills/orkboard").mkdir(parents=True)
    (root / ".claude/skills/orkboard/SKILL.md").write_text("my own skill\n", encoding="utf-8")
    broken = "mine\n<!-- orkboard:begin schema=1 hash=abc123 -->\nno end\n"
    (root / "CLAUDE.md").write_text(broken, encoding="utf-8")
    written = write(root)
    assert ".claude/skills/orkboard/SKILL.md" not in written and "CLAUDE.md" not in written
    assert (root / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8") == "my own skill\n" and (root / "CLAUDE.md").read_text(encoding="utf-8") == broken
    assert {(f["path"], f["what"]) for f in check(root)} == {(".claude/skills/orkboard/SKILL.md", "not ours"), ("CLAUDE.md", "broken")}


def test_the_block_is_at_most_sixty_lines_even_with_long_places(tmp_path):
    root = project(tmp_path)
    long = "docs/" + "architecture/" * 5 + "decisions/"
    agent_rules.write(root, WIKI, decisions=long)
    lines = (root / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    block = lines[lines.index(next(x for x in lines if x.startswith("<!-- orkboard:begin"))):]
    assert block[-1] == "<!-- orkboard:end -->" and len(block) <= 60 and long in "\n".join(block)


def test_the_way_of_a_goal_has_accept_and_the_rules_are_schema_two_spec_152_d(tmp_path):
    """Spec 152 D.1, D.2: the block's step 4 and BOARD.md say how a party's leader accepts; the leader's role file carries the acceptance's text."""
    assert agent_rules_text.SCHEMA == 2
    root = project(tmp_path)
    write(root)
    text = (root / "AGENTS.md").read_text(encoding="utf-8")
    block = text[text.index("<!-- orkboard:begin"):].splitlines()
    assert len(block) <= 60 and "schema=2" in block[0]
    body = "\n".join(block)
    assert "Accept: after a party's stages, before" in body and "twice at most; what is" in body and "“Not accepted”" in body
    assert body.index("Work: the stages") < body.index("Accept: after") < body.index("5. Done")
    board = (root / WIKI / "BOARD.md").read_text(encoding="utf-8")
    assert "## Accepting a step" in board and "twice at most" in board and "“Not accepted”" in board and "Schema 2." in board
    leader = agent_rules_text.seat_text("leader", "tech")
    assert leader.index("## Your section of the spec") < leader.index("## Accepting a step\n\n" + idea_accept.instruction("tech"))
    assert "## Accepting a step" in (root / WIKI / "roles/tech-leader.md").read_text(encoding="utf-8")
    assert "## Accepting a step" not in agent_rules_text.seat_text("grunt")


def test_the_wiki_outside_the_project_is_refused(tmp_path):
    with pytest.raises(ValueError):
        agent_rules.write(project(tmp_path), "../elsewhere")


# -- Settings' line and the host (C.4, C.5) ---------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def host(fake_repo) -> Orkboard:
    h = Orkboard(fake_repo)
    yield h
    sys.modules.pop("orkboard.core.idea_runner", None)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def seed(host) -> None:
    """A party and a goal, so the Board has pages and its tree stands."""
    root = host.ideas.root()
    slug, _new = ideas.save_goal(root, None, "Tech", "About Tech", None, "normal", craft="engineering")
    library.install(host.ideas.state_dir, ["architect"])
    goal_team.set_team(root, slug, [], leader="architect")
    ideas.add_idea(root, "add a score board", slug, host.ideas.state_dir, "normal", "hold")


def test_the_line_is_shown_with_its_words_and_reading_it_writes_nothing(host, fake_repo):
    seed(host)
    s = host.command("rules.switch", {})
    assert s["show"] and not s["on"] and not s["asked"] and s["label"] == "Let any AI tool work the Board" and s["write"] == "Write the rules" and s["not_now"] == "Not now"
    assert s["line"].startswith("Writes the Board's rules into AGENTS.md and CLAUDE.md, so Claude Code, Codex, Cursor and others take your goals") and s["line"].endswith("what is yours to decide.")
    assert not (fake_repo / "AGENTS.md").exists() and not agent_rules.has_rules(host.ideas.state_dir / "board")
    host.command("rules.not_now", {})
    again = host.command("rules.switch", {})
    assert again["asked"] and not again["on"] and not (fake_repo / "AGENTS.md").exists()


def test_the_yes_writes_the_rules_in_one_board_commit(host, fake_repo):
    seed(host)
    before = git(fake_repo, "rev-list", "--count", "--all")
    got = host.command("rules.write", {})
    assert got["ok"] and "AGENTS.md" in got["written"] and ".claude/skills/orkboard/SKILL.md" in got["written"] and got["commit"]
    assert git(host.ideas.state_dir / "board", "log", "-1", "--format=%s") == "board: the Board's rules (schema 2)"
    assert int(git(fake_repo, "rev-list", "--count", "--all")) > int(before)
    changed = git(host.ideas.state_dir / "board", "show", "--name-only", "--format=", "HEAD").splitlines()
    assert set(got["written"]) <= set(changed)
    s = host.command("rules.switch", {})
    assert s["on"] and s["status"].startswith("The Board's rules are in this project (schema 2)")
    assert host.command("rules.write", {})["written"] == []                                   # a second yes writes nothing more


def test_at_the_start_the_rules_are_written_again_where_the_package_differs_and_a_hand_change_is_said(host, fake_repo, monkeypatch):
    seed(host)
    host.command("rules.write", {})
    board = host.ideas.state_dir / "board"
    role = board / host.ideas._decision_tree().wiki_rel / "roles/tech-leader.md"
    role.write_text(role.read_text(encoding="utf-8") + "\nA line by hand.\n", encoding="utf-8")
    git(board, "add", "-A")
    git(board, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "by hand")
    toasts = []
    host.projects.current().toast = lambda message, **kw: toasts.append(message)
    monkeypatch.setattr(agent_rules_text, "skill_body", lambda wiki: "# A newer skill\n")
    host.agent_rules.start()
    assert "A line by hand." not in role.read_text(encoding="utf-8") and "A newer skill" in (board / ".claude/skills/orkboard/SKILL.md").read_text(encoding="utf-8")
    assert toasts == ["roles/tech-leader.md was changed by hand: Orkboard's own is written back; a project's own role is made on Agents."]
    assert host.command("rules.switch", {})["said"] == toasts
    assert git(board, "log", "-1", "--format=%s") == "board: the Board's rules (schema 2)"
    host.agent_rules.start()
    assert len(toasts) == 1                                                                   # said once


def test_the_start_of_a_project_without_the_rules_writes_nothing(host, fake_repo):
    seed(host)
    head = git(fake_repo, "rev-parse", "--all")
    host.agent_rules.start()
    assert git(fake_repo, "rev-parse", "--all") == head and not agent_rules_switch.agent_rules.has_rules(host.ideas.state_dir / "board")


def test_the_commit_words_come_from_the_glossary():
    from orkboard.realm import lexicon
    assert lexicon.term("board_rules") == "the Board's rules" and agent_rules_switch.message() == "board: the Board's rules (schema 2)"


def test_a_direct_write_is_refused_in_words_while_fs_question_is_unanswered_or_answered_no(tmp_path, monkeypatch):
    """Spec 151 C.4, F: the switch shows F's question first (tests/test_board_in_code_card.py); a `rules.write` sent anyway is refused in words and writes nothing."""
    from types import SimpleNamespace
    from orkboard.gui import agent_rules_switch as sw
    rules = sw.AgentRules(SimpleNamespace(project=SimpleNamespace(root=tmp_path, ideas=SimpleNamespace(state_dir=tmp_path / ".orkcraft"))))
    monkeypatch.setattr(sw, "standing", lambda root, state_dir: "ask")
    with pytest.raises(ValueError) as got:
        rules.write()
    assert str(got.value) == sw.ANSWER_FIRST and not (tmp_path / "AGENTS.md").exists()
    monkeypatch.setattr(sw, "standing", lambda root, state_dir: "off")
    with pytest.raises(ValueError) as off:
        rules.write()
    assert str(off.value) == "The Board is kept off this repository: the rules would find no Board" and not (tmp_path / "AGENTS.md").exists()


def test_board_md_says_a_leaders_talk_and_accepted_with_an_example_each_and_who_writes_them(tmp_path):
    """Spec 154 B.4: both parts, their lines, where they go, that each leader writes its own and the conductor none, and that questions stay in Open questions."""
    from orkboard.realm import page_talk
    root = project(tmp_path)
    write(root)
    text = (root / WIKI / "BOARD.md").read_text(encoding="utf-8")
    assert "### Talk" in text and "### Accepted" in text and "`go`, `doubt` or `no`" in text and "`cannot see`" in text and "`## <Party title>`" in text
    for line in ("- verdict: doubt — the cache adds a second caller to the store", "- assumes: players reload less than once a minute — shown by: the reload events of a week",
                 "- met: the board shows the best three players", "- not met: a tie is ordered by the earlier score — the order is by name", "- cannot see: the board loads in under a second"):
        assert line in text, line
    assert "Each leader writes only its own" in text and "the conductor" in text and "writes nothing of a leader's" in text and "stays under *Open questions*" in text
    # the examples are read by the code that reads the parts
    found = {name: [ln.removeprefix("    ") for ln in text.split(f"    ### {name}\n", 1)[1].split("\n\n", 1)[0].split("\n")] for name in ("Talk", "Accepted")}
    assert page_talk.talk_problems(found["Talk"]) == []
    assert page_talk.accepted_problems(found["Accepted"], ["the board shows the best three players", "a tie is ordered by the earlier score", "the board loads in under a second"]) == []
