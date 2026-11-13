"""Orkboard's words: one word for each concept (CLAUDE.md, Wording).

    term("track")                  == "party"
    term("ork", many=True)         == "orks"
    words("3 ideas on the map")    == "3 goals on the table"

An ork keeps its orkish name (the Orkmaster, the Taskmaster, a Grunt); everything else takes the word
for what it does, what it costs or what it risks (a party, a goal, the spend, Stop all). `TERMS` is the
glossary: a new concept gets its one word there, and new code writes that word. A concept whose word
changed keeps the spelling it had in `was` (the code's `track` is a party, its `idea` a goal, an old
*deck* is *in line*), and `words` says such a label in today's word. It is meant for the interface
(titles, labels, hints, toasts), not for what people or agents wrote.

Pure module.
"""
from __future__ import annotations

import re

from orkboard.realm import lexicon_table
from orkboard.realm.lexicon_table import SLOTS, WINDOW
from orkboard.realm.lexicon_term import Term, _t     # noqa: F401  (the glossary's type and maker, said from here as before)



# The glossary, keyed by what each concept is; an ork keeps the key the code gave it (`orc.fields` the
# Taskmaster, `orc.barracks` a Grunt).
TERMS: tuple[Term, ...] = (
    # -- who: the orks, and the words of orkestration ------------------------------------------------
    _t("ork", "ork", "orks"),
    _t("orkestration", "orkestration"),
    _t("orkestrate", "orkestrate"),
    _t("keeper", "steward", "stewards", "keeper", "keepers"),     # a building's steward, asked in plain words
    _t("dnd", "Do not disturb"),                                   # pushes to a paired phone wait, until it is turned off or its time ends (settings `dnd_until`, gui/phone_push.py)
    # -- what a thing does, costs or risks: plain words ---------------------------------------------
    # today's spend under the AI tools' limits (the snapshot's `hud.gold`, `hud.lumber`: table/over.js)
    _t("gold", "spend", "", "gold"),
    _t("lumber", "context", "", "lumber"),
    _t("maker", "maker", "makers"),
    _t("picture_maker", "Picture maker"),
    _t("sound_maker", "Sound maker"),
    _t("its_makers", "Its makers"),
    _t("set_a_cap", "Set a cap"),
    _t("ai_tool", "AI tool", "AI tools"),
    # a model's tier says how seasoned the mind is (realm/tiers.py), drawn as the gear on a head
    _t("tier.laborer", "Novice", "Novices", "Laborer", "Laborers"),
    _t("tier.warrior", "Seasoned", "", "Warrior", "Warriors"),
    _t("tier.elder", "Veteran", "Veterans", "Elder"),                          # a CLI an ork thinks with: Claude Code, Codex… (realm/harnesses.py)
    _t("tool_error", "Tool error", "Tool errors"),                 # an AI tool failed: Switch, Retry, Details (realm/tool_errors.py)
    _t("sign_in", "Sign-in", "Sign-ins"),                          # a tool's own way to sign in to its account (realm/sign_in.py; Sign in the button)
    _t("main_tool", "Main tool", "Main tools"),                    # the AI tool decisions run on (realm/harnesses.py)
    # screens and actions
    _t("war_horn", "Stop all", "", "War Horn"),
    _t("war_raven", "Phone", "Phones", "War Raven", "War Ravens"),   # a phone paired with the computer (gui/pairing.py; Settings → Phones)
    _t("place", "place", "places"),                                # one at the hand's right, each opening a table: the die, the backpack, the history book (decisions §145)
    _t("update", "update", "updates"),                             # a newer Orkboard (core/updates.py, docs/updates.md)
    _t("critical_update", "critical update", "critical updates"),  # …that installs by itself when Orkboard opens
    _t("major_update", "major update", "major updates"),           # …that starts a later line (0.1 → 0.2), offered louder
    _t("project", "Project", "Projects"),                           # the folder Orkboard opens, with its Board (gui/board_projects.py)
    # a to-do, a party, the Target and an agent
    _t("chore", "to-do", "to-dos", "chore", "chores"),             # a to-do of the person's own
    _t("track", "party", "parties", "track", "tracks"),            # a team you picked and the goals dealt to it, in order (decisions §63; the code's track, goal)
    _t("steward_goal", "Target"),                                  # the Board's one setting, Thrift, Balance or Quality, and a party's size's (spec 35 §11.1, spec 75 §5.5; board/target.js); "Goal" is today's word for a goal
    _t("agent", "agent", "agents"),                                # a role: a model, an instruction, a limit (realm/roles.py, spec 34)
    # an agent's craft, drawn as the head of its race in orkUI (realm/roles.py CRAFTS, RACES; decisions §53): the race says
    # what the agent does, the gear on its head its tier (a novice bare, a seasoned in iron, a veteran hooded)
    _t("craft", "craft", "crafts"),
    _t("team", "team", "teams"),                                   # a party's agents, picked from the library (realm/goal_team.py)
    _t("library", "library"),                                      # the agents that come with Orkboard (realm/library.py)
    _t("check", "check", "checks"),                                # what a team's checker holds each goal to (realm/idea_checks.py)
    _t("checker", "checker", "checkers"),                          # an agent of the library that brings a check
    _t("pace", "the week's pace"),                                  # the Claude week's share left against the share of it still to come (spec 44)
    _t("party_work", "What the party did"),                         # a party's work, member by member and check by check (spec 43 §2)
    _t("party_proposal", "party proposal", "party proposals"),      # the night's proposal to take a checker out of a party (spec 43 §4)
    _t("own_party", "your party", "your parties"),                  # a party the person saved from one of theirs, kept in their own folder and picked in any project (spec 43 §6)
    _t("party_price", "This party"),                                # about what a goal costs with a party, before it starts (spec 43 §3)
    _t("check_finding", "finding", "findings"),                    # one thing a check found: where, what goes wrong, fixed or left (spec 43 §0; `quality_finding` is the quality card's)
    _t("tag", "tag", "tags"),                                      # a task's kind of work: who of the team does it (roles.TASK_KINDS)
    _t("craft.engineering", "Engineering"),                        # an ork: the Taskmaster, the Grunts, a role of code
    _t("craft.design", "Design"),                                  # an elf
    _t("craft.data", "Data"),                                      # a goblin
    _t("craft.marketing", "Marketing"),                            # a gnome
    _t("craft.product", "Product"),                                # the undead: a lich
    _t("canvas", "canvas", "canvases"),                             # what an AI tool drew outside the code: a page, a design, a deck, a document, a picture (spec 78)
    _t("race", "race", "races"),                                   # orkUI's heads (races/<race>-<tier>.png)
    _t("race.peon", "ork", "orks"),                                # orkUI's id for the ork's head is the site's class, peon
    _t("race.elf", "elf", "elves"),
    _t("race.goblin", "goblin", "goblins"),
    _t("race.gnome", "gnome", "gnomes"),
    _t("race.lich", "lich", "liches"),
    _t("race.skeleton", "skeleton", "skeletons"),                  # the Release manager's and checker's race (spec 68 §1; orkUI 0.5.0 draws it, a lich until then)
    _t("leader", "leader", "leaders"),                             # a party's: its steps run as it (core/idea_lead.py)
    _t("party", "party", "parties"),                               # a party's leader, builders and checkers (realm/goal_team.py)
    _t("undo", "Undo"),                                            # the toast's button after a one-press move: it puts the goal's page back (core/idea_undo.py; js/cards/played.js, goal 171 K)
    _t("verdict", "verdict", "verdicts"),                         # a party's old verdict against its metrics, kept as history (realm/goal_verdict.py)
    _t("lens", "lens", "lenses"),                                  # what a new goal points at, the party's way: code, a screen, a pain (realm/idea_lens.py)
    _t("segment", "segment", "segments"),                          # whom a goal is for, a product manager's lens
    _t("task_kind", "task type", "task types"),                    # code · tests · docs · text for people · research
    _t("ask", "Ask"),                                              # the line on the open tab and its button: a quick question about the project, answered once, never a card (spec 106)
    _t("board_map", "Map"),                                        # a project's parties, goals and tasks on one screen (spec 39)
    _t("stage", "stage", "stages"),                                # a party's step a goal goes through, one a band; its leader words them (Concept, Build, Playtest for a Game designer; Planning, Implementation, Checking by default; spec 48, spec 59 §3)
    _t("wave", "wave", "waves"),                                   # a task's depth in its plan by `after`: a column of the Map's goal (spec 48)
    _t("gate", "gate", "gates"),                                   # the one press that merges dev into main (decisions §49.5, spec 49 §2.1)
    _t("fix_it", "Fix it"),                                        # a red gate's way: its stage again where the goal is on its branch, a new Fix goal where it is done (decisions §303.5; js/cards/spreads/gate.js)
    _t("fix_it_stage", "back to work: its stage again, sealed with its cost"),     # Fix it's line on the way to dev
    _t("fix_it_goal", "makes a new Fix goal; one press, you can undo it"),         # Fix it's line on the way to main
    _t("test_out_of_date", "The test is out of date"),             # a red gate's other way: Tech is asked and a new decision comes first (a paid pass on the seal)
    _t("test_out_of_date_line", "asks Tech; a new decision comes first, sealed with its cost"),
    _t("recap", "While you were away"),                            # the card of what the Board did since this device's last look (spec 42 §1)
    _t("flag", "flag", "flags"),                                   # a goal the gate took into main (spec 50 §2.2); a party's old flag is its verdict met (spec 42 §2)
    _t("goal_look", "look", "looks"),                              # how a goal's screen looks: asked by the elf, picked before it is built (spec 85)
    _t("task_picture", "picture", "pictures"),                     # what a task that changed what people see looks like, drawn from the project's preview (spec 85)
    _t("asset", "asset", "assets"),                                # a file the project is made of that people see or hear: a screen's picture, art, an icon, a sound, music, a clip, a font (spec 88; realm/assets.py)
    _t("lens_view", "view", "views"),                              # one map of a leader's lens: the Architect's System, read from the code (spec 89; decisions §104.1, realm/project_map.py)
    _t("container", "container", "containers"),                    # a part of the project that is built and runs on its own (a client, a server): a folder with its own manifest, on System (spec 90 §6; decisions §105.6, realm/system_overview.py)
    _t("pick", "pick", "picks"),                                  # the stop Pick one and its screen: a task left two to six variants of one kind for the person to pick from (spec 51)
    _t("plan_change", "plan change", "plan changes"),              # the leader's re-plan of what is left, after a goal's spec changed: the tasks not started changed, dropped or added, answered Take the new plan or Keep the plan (spec 62; the code's `change`, plan_change.json)
    _t("goal_type", "goal type", "goal types"),                    # what kind of goal a party's team can take on: New logo, Fix a bug; realm/goal_types.py, specs 52 and 59
    _t("pitch", "pitch", "pitches"),                               # a goal of an Ideation party: a small idea to judge, not to build (spec 65; realm/pitches.py)
    _t("pitch_view", "view", "views"),                             # one side's read of a pitch: what speaks for it, what against, one question (spec 65 §3)
    _t("pitch_case", "the case against"),                          # the skeptic's strongest case not to do a pitch (spec 65 §3)
    _t("pitch_decision", "decision", "decisions"),                 # the Investor's answer: Invest, Reshape or Pass, with why (spec 65 §3); not a verdict, which is a party's old one against its metrics
    _t("pitch_passed", "passed"),                                  # a pitch the person passed on, kept with its why, read by every later pitch (spec 65 §5)
    _t("idea_route", "route", "routes"),                           # a goal's way across parties: where it came from, where it is, where it went (spec 68 §2; realm/idea_route.py)
    _t("release", "release", "releases"),                          # a goal of A release: a version, the goals that go in, its notes and the stores' list (spec 68 §3; realm/releases.py)
    _t("release_out", "out"),                                      # a release the person said is out in the stores: Mark it out, Out in 1.4 (spec 68 §3.5)
    _t("orkmaster", "Orkmaster"),                                  # the project's ork: it deals the parties and a goal's party; it plans nothing (spec 70; realm/orkmaster.py)
    _t("collide", "collision", "collisions"),                      # two goals of different parties that change the same thing; the Orkmaster finds them and asks what goes first (spec 71; realm/collide.py)
    _t("party_size", "size", "sizes"),                             # a party's Lean, Standard or Full: how many agents, of what tiers, and so its Target (spec 75; realm/party_recipes.py)
    _t("project_kind", "what the project is"),                     # an empty folder, a mobile app, a web app, a backend, a game, data work, a team's wiki, a designer's folder, texts, code (spec 75; realm/project_kind.py)
    _t("project_level", "The project"),                           # the project's level: its parties as columns, their goals in them (spec 70 §2)
    _t("notification", "notification", "notifications"),          # a push to a paired phone: an answer that waits, the morning (spec 42 §3)
    _t("feed", "feed", "feeds"),                                   # the phone's project screen: what waits first, then each leader's posts since this phone's last look, the heads on top (decisions §291.5–§291.9; realm/board_feed.py)
    _t("record", "record"),                                        # what an agent did in the last 30 days, in its dialog (spec 42 §4)
    _t("this_week", "This week"),                                  # the work of the last seven days, at API prices, beside today's spend (spec 42 §6)
    _t("last_week", "Last week"),                                  # the card of the week before this one, Monday to Sunday (spec 42 §7)
    _t("night_low", "Low work may run at night"),                  # the one standing permission for the night (spec 83, decisions §100): asked once, changed in Settings
    _t("nights_in_a_row", "nights in a row"),                     # the Board's nights with work done, one after another, up to last night (spec 42 §8)
    _t("short_name", "short name", "short names"),                 # a goal's, a party's or a task's name in 24 characters (spec 41 §3)
    _t("recommended_answer", "recommended answer", "recommended answers"),   # the choice the Taskmaster picks for its question (spec 41 §9)
    _t("idea", "goal", "goals", "idea", "ideas"),                 # a goal: a page with its spec and plan, done in dev, its flag raised in main (spec 29, 50; the code's idea)
    _t("proposal", "proposal", "proposals"),                       # a goal the keeper proposes at night, for the morning (spec 35 §8)
    *WINDOW,                                                         # the window's words (realm/lexicon_table.py)
    _t("keep_awake", "Keep the computer awake"),                   # the computer does not sleep by itself, on power (spec 47 §0)
    _t("run", "Run"),                                              # a project's running when it runs: an app, a site, a service, code, data; a stage party by the project's kind, with recurring goals (spec 92 §1)
    _t("upkeep", "Upkeep"),                                        # a project's running when it is kept true: a wiki, a design, texts (spec 92 §1)
    _t("liveops", "LiveOps"),                                      # a game's running, after launch: events, numbers, small fixes (spec 91 §7); Run and Upkeep are the other kinds'
    _t("recurring_goal", "recurring goal", "recurring goals"),     # a goal that comes back every day, week or month once it is done; a running party proposes some when it is made (spec 92 §2; realm/recurring.py)
    # a task's area in work: two tasks whose areas meet do not land side by side (realm/claims.py, core/idea_landing.py)
    _t("claim", "Area in work", "Areas in work"),                   # the files an open task changes, until merged
    _t("overlap", "Overlap", "Overlaps"),                           # a task on another open task's area
    _t("fix", "Fix", "Fixes"),                                      # Claude Code started on Orkboard's own code with the logs, to fix it and push to main (spec 119, decisions §197)
    # -- the orks of a goal's work, by their orkish names (CLAUDE.md, Wording) -----------------------
    _t("orc.fields", "Taskmaster"),                                 # plans a goal's work in stages and tasks (llm-wiki/general/roles/taskmaster.md)
    _t("orc.barracks", "Grunt", "Grunts"),                          # an ork in Tech: does a task in its own worktree (llm-wiki/general/roles/grunt.md)
    _t("orc.warder", "Warder"),                                     # judges an AI tool's commands and keeps the secrets' files from the orks (hooks/warder.py)
    *SLOTS,                                                          # the inventory and a way's kind (realm/lexicon_table.py)
)

# Short spellings a concept was also written in, beside its `was` (none left).
_ALSO: dict[str, tuple[str, ...]] = {}

# Whole phrases first: where a word for word would read wrong.
_PHRASES = {"Halt All Operations": "Stop all", "Halt All": "Stop all"}

SOURCES = (__file__, lexicon_table.__file__)      # the files the glossary is written in, each word with the line that says where it comes from
_BY_KEY = {t.key: t for t in TERMS}


def known(key: str) -> bool:
    """Whether the glossary has a word for `key`."""
    return key in _BY_KEY


def term(key: str, many: bool = False) -> str:
    """The word for `key`: `term("track", many=True)` → parties."""
    t = _BY_KEY[key]
    return (t.many or t.word) if many else t.word


def _pairs() -> list[tuple[str, str]]:
    """Every old spelling with today's word, longest first."""
    out: dict[str, str] = dict(_PHRASES)
    for t in TERMS:
        for short in _ALSO.get(t.key, ()):
            out.setdefault(short, t.word)
        if not t.was and not t.was_many:
            continue
        if t.was:
            out.setdefault(t.was, t.word)
        if t.was_many:
            out.setdefault(t.was_many, t.many or t.word)
        if t.was.startswith("The "):                        # "The new one replaces §<n>" is also "the new one …" mid-sentence
            out.setdefault("the " + t.was[4:], t.word)
    return sorted(out.items(), key=lambda kv: len(kv[0]), reverse=True)


_PAIRS = _pairs()
_TODAY = dict(_PAIRS)
_LOWER = {old.lower(): new for old, new in _PAIRS if old[:1].islower()}
_UPPER = {old.upper(): new for old, new in _PAIRS}


def _alternation() -> str:
    names: list[str] = []
    for old, _ in _PAIRS:
        names += [old, old.upper()]                         # a heading may shout: TRACKS
        if old[:1].islower():                               # a common noun also opens a sentence
            names.append(old[:1].upper() + old[1:])
    return "|".join(re.escape(n) for n in sorted(set(names), key=len, reverse=True))


# A name stands alone: not inside another word (`map` in `roadmap`, `track` in `racetrack`, `idea` in `ideas_map`)
# nor in a path (`./ideas/`, `ideas/screenshots`, `src/tracks.py`): those name files, not concepts.
_WORD = re.compile(rf"(?<![\w\-/\\.])(?:{_alternation()})(?![\w\-/\\]|\.\w)")


def _swap(m: re.Match) -> str:
    found = m.group(0)
    if found in _TODAY:
        return _TODAY[found]
    if found.isupper() and found in _UPPER:
        return _UPPER[found].upper()
    word = _LOWER[found.lower()]                            # `Chores` opening a sentence → `To-dos`
    return word[:1].upper() + word[1:]


def words(text: str) -> str:
    """`text` in today's words: `📯 War Horn` → `📯 Stop all`, `3 chores` → `3 to-dos`.

    Proper names (War Horn, War Raven) match as written; common nouns (chore, track) in any case,
    keeping it (`Chores` → `To-dos`, `TRACKS` → `PARTIES`). Emoji stay."""
    if not text:
        return text
    return _WORD.sub(_swap, str(text))


def spans(text: str) -> list[tuple[int, int, str]]:
    """Where `words` changes `text`: (start, end, today's word), left to right (for styled text)."""
    return [(m.start(), m.end(), _swap(m)) for m in _WORD.finditer(text or "")]


def table() -> list[tuple[str, str]]:
    """Every way an old word is written, with today's, longest first: what a face that cannot import
    this module (the GUI's page) needs to do `words` itself."""
    out = {}
    for old, _ in _PAIRS:
        for found in (old, old.upper(), old[:1].upper() + old[1:]):
            m = _WORD.fullmatch(found)
            if m:
                out.setdefault(found, _swap(m))
    return sorted(out.items(), key=lambda kv: len(kv[0]), reverse=True)


def glossary() -> list[tuple[str, str, str]]:
    """(key, word, the spelling it replaced or "") for every concept, in the glossary's order."""
    return [(t.key, t.word, t.was or t.was_many) for t in TERMS]
