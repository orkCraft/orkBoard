"""The look (docs/specs/85-the-elf-asks-and-shows.md §1, §2, decisions §102): a goal that changes what people see is asked about its look
before it is built, and a screen's look is picked before it is built. Thrift (§49) holds: the look's questions are asked at the draft, one
round a goal, and only for a visual goal; a code goal never has them.

    idea_look.visual(state_dir, root, "dark-mode")              # a goal of a visual type, or an untyped one of a party with a design seat
    idea_look.asker(state_dir, root, track)                     # the role that asks: the party's design member, else its leader ("" with no leader)
    idea_look.draft_lines(True)                                 # the draft prompt's lines of the look ("" for a code goal)
    lines, by, n = idea_look.questions(answer, 3, True, elf, leader)    # the draft's questions in all (the look's first), who asks each, how many are of the look
    idea_look.screens(state_dir, "dark-mode")                   # a screen's, a flow's or a landing's goal: its plan begins with a pick
    idea_look.screen_title(state_dir, root, slug)               # the title that asks make_plan for it ("" for any other goal)
    idea_look.pick_task(title, slug)                            # that pick, as the plan's first task

No face, no model.
"""
from __future__ import annotations

import re
from pathlib import Path

from orkboard.realm import goal_team, goal_types, idea_questions, ideas, library, roles

VISUAL = ("screen", "flow-feature", "landing", "level", "character", "icon", "logo")     # the types that change what people see (§1)
SCREENS = ("screen", "flow-feature", "landing")                                           # the types whose look is picked first (§2)
PICTURES = "Pictures you like"                      # an answer that takes pictures (the faces add them, the keeper reads them)
LOOK_MAX = 3                                        # of the look, the most asked beside the leader's
LOOK_ID = "look"                                    # the id the pick task has until the plan renames its tasks
LOOK_DIR = "design/looks"                           # where the look picked is written, beside the project's design


def _type(state_dir: Path, slug: str) -> str:
    t = goal_types.get(ideas.state(state_dir, slug).get("type"))
    return t.id if t is not None else ""


def design_member(state_dir: Path, root: Path, track: str) -> str:
    """The slug of the party's design member (craft design: the elf), the leader first, then its team's builders, then its checkers;
    "" with none."""
    lead = goal_team.leader_of(root, track)
    team = goal_team.team_of(root, track)
    pool = [lead, *[s for s in team if goal_team.band_of(s) == "build"], *[s for s in team if goal_team.band_of(s) != "build"]]
    return next((s for s in pool if (r := roles.role(state_dir, s)) is not None and r.get("craft") == "design"), "")


def visual(state_dir: Path, root: Path, slug: str) -> bool:
    """Whether the goal changes what people see: its type is one of VISUAL; or it has no type and its party has a design seat. A goal of
    any other type (a bug, a clean up, a balance pass, a sound) is code or words, and is not asked about its look."""
    kind = _type(state_dir, slug)
    if kind:
        return kind in VISUAL
    page = ideas.idea_page(root, slug)
    return bool(page is not None and design_member(state_dir, root, page.get("track") or ideas.GENERAL))


def asker(state_dir: Path, root: Path, slug: str) -> str:
    """The role that asks the look's questions of a goal: its party's design member, else its party's leader ("" with no page)."""
    page = ideas.idea_page(root, slug)
    if page is None:
        return ""
    track = page.get("track") or ideas.GENERAL
    return design_member(state_dir, root, track) or goal_team.leader_of(root, track)


def draft_lines(on: bool, who: str = "") -> str:
    """The draft prompt's lines for a visual goal ("" for any other): the look's questions go in `look`, beside `questions`."""
    if not on:
        return ""
    return ("This goal changes what people see. Beside `questions`, put up to three questions of its LOOK in `look`"
            + (f" (they are asked by {who})" if who else "")
            + ": its mood, its palette, the pictures or products that are its references. Each is a question in the same shape, with the answer you "
              "recommend picked and two or three others, in the person's words, not design terms. Ask the look only where the idea and the "
              f'repository do not say it. For the references, one of the choices is exactly "{PICTURES}" (the person adds them). '
              "Ask nothing of the look that the code can decide. At most three questions in all are kept, the look's first.\n")


def questions(answer: dict, limit: int, on: bool, look_by: str = "", lead_by: str = "") -> tuple[list[str], list[str], int]:
    """The draft's questions as page lines, who asks each and how many of them (the first ones) are of the look: a visual goal's look first
    (up to LOOK_MAX), the leader's after, at most `limit` in all. A goal that is not visual has the leader's only: `look` is not read."""
    mine = idea_questions.all_of(answer.get("look"), LOOK_MAX)[:limit] if on else []
    for q in mine:
        q["choices"] = [PICTURES if c.lower() == PICTURES.lower() else c for c in q["choices"]]
    rest = idea_questions.all_of(answer.get("questions"), limit)[:max(0, limit - len(mine))]
    return [idea_questions.line(q) for q in [*mine, *rest]], [look_by] * len(mine) + [lead_by] * len(rest), len(mine)


def takes_pictures(question: str) -> bool:
    """Whether a question (a page line) offers *Pictures you like* as an answer."""
    return PICTURES in idea_questions.parse(question)["choices"]


def screens(state_dir: Path, slug: str) -> bool:
    """Whether the goal's plan begins with a pick of the main screen's look (§2)."""
    return _type(state_dir, slug) in SCREENS


def pick_task(title: str, slug: str) -> dict:
    """The pick that begins a screen's plan, as the model's answer gives a task: two or three looks of the main screen, pictures at phone
    width; the one picked is written to `LOOK_DIR/<goal>` (its name keeps the picture's own extension, `look: true`)."""
    return {"id": LOOK_ID, "title": "Pick a look", "short": "Pick a look", "kind": "design", "tier": "warrior", "after": [],
            "brief": (f"Draw two or three different looks of the main screen of: {title}. Each look is one picture (SVG or PNG) of the "
                      "screen at phone width (390 px wide), in the design system's own tokens and words, with real text on it, not a "
                      "sketch. Make them differ in layout or mood, not in colour only. Change no code. Name each by its mood, and say "
                      "in a line what it favours."),
            "pick": {"n": 3, "kind": "image", "ask": "Which look should the screen have?", "target": f"{LOOK_DIR}/{slug}", "look": True}}


def with_pick(tasks: list[dict], title: str, slug: str, limit: int) -> list[dict]:
    """The plan's tasks (the model's, before they are renamed) with the look's pick first and every other task after it. A plan whose model
    made a pick of its own keeps it as it is (at most one pick a goal at a time)."""
    if any(isinstance(t, dict) and t.get("pick") for t in tasks):
        return tasks
    rest = [dict(t, after=[LOOK_ID, *[a for a in t.get("after") or [] if a != LOOK_ID]]) if isinstance(t, dict) else t
            for t in tasks[:limit - 1]]
    return [pick_task(title, slug), *rest]


def screen_title(state_dir: Path, root: Path, slug: str) -> str:
    """The title of a screen's, a flow's or a landing's goal (its plan begins with the look's pick), else "" (any other goal)."""
    page = ideas.idea_page(root, slug) if screens(state_dir, slug) else None
    return page.title if page is not None else ""


SCREEN = re.compile(r"/[A-Za-z0-9_./#?=&%-]{0,200}")


def clean_screen(value: object) -> str:
    """A task's `screen`, the path of the screen it changes in the project's running preview (`/settings`), as the picture of it is drawn
    (core/idea_shot.py); "" for anything else."""
    return value if isinstance(value, str) and SCREEN.fullmatch(value) and ".." not in value else ""


def instruction(state_dir: Path, root: Path, slug: str) -> str:
    """The plan prompt's lines for a visual goal ("" for any other): a screen's look is picked first (the pick is added by code), and a task
    may name the screen it changes."""
    if not visual(state_dir, root, slug):
        return ""
    lines = ("\n- A task that changes a screen people see may name it, as its path in the running preview: `\"screen\": \"/settings\"`; "
             "the Board draws a picture of it when the task is done.")
    if screens(state_dir, slug):
        lines += ("\n- The plan's first task, a pick of the main screen's look (Pick a look, by the designer), is added for you: plan the tasks that "
                  f"build the screen after it, and let them read the look picked from its note and from `{LOOK_DIR}/{slug}.*`.")
    return lines
