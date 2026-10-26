# Spec 92 — Running the project is a party; working with people is a party called Team; Operations stop being a tab

The owner, 26 October (decisions §108): *Operations should not be a permanent tab but a party. We have LiveOps for games;
something like it should exist for other kinds of project: apps, services, an LLM wiki, and managing a team of people.* The
design was agreed the same day. **Builds:** Claude · **Review:** full · P1.

**What it is, and is not:** the fifth stage of New party, the project's running, is a party for every kind of project, named
for what the project does when it runs (*LiveOps* for a game, *Run* for an app, a site, a service, code and data, *Upkeep*
for a wiki, a design and texts) and made with two to four **recurring goals** that come back once they are done; working
with people is one party, **Team**, which the person puts in the one project they choose and which holds today's
Operations; the permanent *Operations* row leaves the left column once a Team party exists. Not: a change to what
Operations do or where they are kept (the person's folder, decisions §51.1, as before); a second place for Operations
(there is one Team party across all projects); goals in the Team party (it holds Operations, not goals); a new AI tool, a
new role in the library (the running parties are made of the library's roles); a recurring goal that starts a model by
itself (a renewed goal is added as the person's own New goal is, and the keeper drafts it as it drafts any).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Running by kind** | §1 | `realm/party_recipes.py` (`running_name`, the `<kind>-liveops` recipes), `realm/party_presets.py`; `tests/test_party_presets.py`, `tests/test_running_team.py` |
| **B. Recurring goals** | §2 | new `realm/recurring.py`, new `gui/ideas_running.py` (`goal_save {routines}`, `ideas.repeat`, the clock), `gui/ideas.py` (`ideas.page` says `repeat`), `js/shell/partyrun.js` + `js/shell/partyform.js` + `js/shell/goalwizard.js`, `js/board/idea.js`; the phone's `pwa/shell-party-run.js`, `pwa/shell-party-new.js`, `pwa/shell-preview.js`; `tests/test_running_team.py`, both browser tests |
| **C. The Team party** | §3 | `realm/party_recipes.py` (`TEAM`, `is_team`), new `realm/ops_team.py`, `gui/ops.py` (`team`, `moved`), `gui/board_host.py` (`ops_team` in both snapshots), `gui/ideas_running.py` (`ideas.team`, one Team party), `gui/ideas_map.py` (`ops` on the party), `gui/ideas_release.py`, `realm/pitches.py`, `realm/releases.py`, `realm/orkmaster.py`; `tests/test_running_team.py` |
| **D. Operations leave the column** | §4 | `js/arena/goaltabs.js` (`teamOf`, `opsRow`), `js/arena/arena.js` (`OpsField` for the Team party), `js/arena/partylist.js`, `js/arena/arenawords.js`, `js/arena/stops.js`, `js/arena/partymenu.js`, `js/board/store.js`, `js/shell/proposals.js`; the phone's `pwa/shell-arena.js`, `pwa/shell-arena-words.js`, `pwa/shell-where.js`, `pwa/shell-stops.js`, `pwa/shell-ideas.js`, `pwa/shell-party.js`, `pwa/shell-party-new.js`, `pwa/board.js`; `tests/test_running_team_desktop_browser.py`, `tests/test_running_team_pwa_browser.py`, `tests/test_running_team_real_browser.py` |
| **E. Words, cache** | §0, §5 | `realm/lexicon.py`; `pwa/sw.js` (`CACHE` one up, with its pins) |

## 0. The words
*Run* (the project's running when it runs), *Upkeep* (when it is kept true), *LiveOps* (a game's), *Team* (the party that
holds the person's Operations), *recurring goal*. New party: under the team of a running party **Recurring goals it
proposes** (*Made with the party and drafted at once; each comes back when it is done and its time has passed. Leave out the
ones you do not want.*), each with *every day* · *every week* · *every month*. Team in New party: *Your work with people:
the daily, 1:1s, the retro, mail and Jira*; in place of a team: *Team holds your Operations: the daily brief, 1:1s, the
retro, mail and Jira.* and *They stay yours, in your own folder, the same in every project; Team only shows them here.
There is one Team party, in one project: this one.*; the foot: *Your Operations stay yours: Team only shows them here*;
greyed, where one exists: *Team is in this project* · *Team is in <project>*. The line under the Operations row while there
is no Team party: *Make it a Team party*. A goal that comes back: *Comes back every week once it is done.* and *Stop
repeating*. Refused: *Team is in <project>*, *Team holds your Operations, not goals: add the goal to another party*, *No
recurring goal <id>*, *A goal comes back every day, week or month*. `TERMS`: `operations` (the person's list, one for all
projects, reached through Team once there is one), `team_party`, `run`, `upkeep`, `liveops`, `recurring_goal`. `LiveOps` is
not a `was` of *Run*: `words` replaces a `was` everywhere, and a game keeps *LiveOps*.

## 1. Running the project, by kind (A)
The fifth stage of `party_recipes.stages_of(kind)` is `<kind>-liveops` as an id (a party made from it keeps the id, so a
Lean party grows back) and `running_name(kind)` as a name. Its leader, builders and checkers are the library's roles, the
first of each seated by a size (spec 91 §7):

| kind | name | leader | builders | checkers | recurring goals (how often) |
|---|---|---|---|---|---|
| game | LiveOps | Analyst | Data engineer, Grunt, Copywriter | Data reviewer | Read the week's numbers (week) · Read what players say (week) · Look at the crash reports (week) · Plan the next event (month) |
| mobile | Run | Product manager | Grunt, Tester, Community | Reviewer | Weekly dependency check · Read the new reviews · Look at the crashes (all week) |
| web | Run | Architect | Grunt, Tester, Community | Reviewer | Weekly dependency check · Look at errors and speed · Read what people write (all week) |
| backend | Run | Architect | Grunt, Tester, Data engineer | Reviewer, Security reviewer | Weekly dependency check · Read the week's incidents · Find the slowest calls (all week) |
| code (and an empty folder) | Run | Architect | Grunt, Tester, Copywriter | Reviewer, Security reviewer | Weekly dependency check · Look at the failing builds (week) |
| data | Run | Analyst | Data engineer, SQL, Grunt | Data reviewer | Check the data is fresh (day) · Recount the key numbers (week) |
| wiki | Upkeep | Product manager | Copywriter, Community | Editor | Find stale pages · Check the links · Take in the new sources (all week) |
| design | Upkeep | Product designer | UI kit, Artist, Copywriter | Accessibility reviewer | Find what drifted from the kit · Check contrast and tap sizes (month) |
| texts | Upkeep | Growth | Copywriter, SEO, Community | Editor | Find stale texts (month) · Check the links (week) |

A party made before this spec keeps the team it was made with. `party_presets.listed(kind)` gives a stage row its
`routines` (`recurring.listed`, `[{id, title, every, words}]`): the other stages, the crafts and Team have none.

## 2. Recurring goals (B)
There was no recurring goal; this is the mechanism (`realm/recurring.py`). A recurring goal is an ordinary goal of the party
with `repeat` (`day` · `week` · `month`) on its page, beside `repeat_from` (the day it was first seen done) and
`repeat_text` (the words it comes back as: the routine's own, not the keeper's rewritten Gist).
- **Made with the party.** `ideas.goal_save {…, routines: [ids]}`, with `proposal` the stage recipe, adds each kept routine
  as the person's New goal is added (`ideas.add`, drafted at once by the keeper) and sets its repeat. A routine id the recipe
  does not have is refused before anything is made; none kept makes the party alone. The dialog ticks them all; the person
  leaves out the ones they do not want; another preset pressed ticks afresh.
- **Coming back.** The host's clock (`routines_tick`, at most once a minute) asks `recurring.due`: a recurring goal that is
  done is stamped with the day it was first seen done, and is due `EVERY` days after (1, 7, 30); one reopened forgets the day.
  A due goal is renewed (`routines_renew`): the repeat is stopped on the old goal first, a new goal with the same words is
  added to the same party, and the repeat moves to it; the done goal stays as the record of that round. A failure (a disk that
  refuses, a spent window) puts the repeat back on the old goal, to try again later. A party that is gone ends the repeat.
- **Seen and stopped.** `ideas.page` says `repeat`; a goal's drawer on the desktop and its screen on the phone say *Comes
  back every week once it is done.* with *Stop repeating* (`ideas.repeat {slug, every: ""}`). `ideas.repeat {slug, every,
  words?}` also sets one by hand (refused: *A goal comes back every day, week or month*). No model.

## 3. The Team party (C)
- **What it is.** A party of the recipe `team` (`party_recipes.TEAM`): the Product manager leads, nobody builds or checks (the
  work is the Operations' templates, which run as they always did). It is New party's, the last of *By craft*, for every kind
  of project, proposed to no one. New party shows no team, no size, no price and no checks for it, only the name and the note
  of §0.
- **One, in a project of the person's choosing.** Operations are the person's, one for all projects (decisions §51.1), so
  there is one Team party across all of them. The person's own note of where (`~/.config/orkcraft/ops/team.json`, mode 600,
  never in a repository: `realm/ops_team.py`) is written when the party is saved and removed when the party is. A second is
  refused (*Team is in <project>*), and the preset is offered greyed with that line. A note about a folder that is gone reads as
  none; a note whose party was taken out of its Board by hand is dropped (only while that Board has other parties).
- **Its Board is Operations'.** `ideas.map` says `ops` on the party; the desktop's field and the phone's are today's
  Operations list with its *New…* and *Settings*, its templates, runs, checks and history, unchanged in behaviour and storage.
  Its heading in the column has no *k/n* (it has no goals); its stops are Operations' stops, answered in place from any project.
  **Save** shows it at once (no screen of goals opens, no heads gather). Its menu has only *Remove party…* on the desktop; on
  the phone its field has *About Team* (what it is, and *Remove party*, which gives the row back).
- **No goals.** `ideas.add`, `ideas.move`, the Orkmaster's `party_for`, the pitches' `offers`, a Release party's sources and
  the party lists of both faces leave it out; the keeper never reads it.
- **Where it is reached.** Only in the project that has it. In another project there is no row and no party: New party offers
  Team greyed (*Team is in <project>*), and Operations' stops, which wait for the person wherever they are, still say *Team* and
  answer in place. A project closed in Orkboard hides its Team party until it is opened again.

## 4. The Operations row (D)
- **While no Team party exists anywhere** (`snapshot.ops_team` is null): the row is where it is today, in the left column of
  the desktop and in the phone's *where* sheet, and under it the line *Make it a Team party*, which opens New party on Team.
  Existing Operations (runs, kept rules, standing, history) are the person's and are not touched.
- **Once there is one** (here or in another project): the row and the line go, on both faces. The Team party's heading is the
  open one in its project; Operations' stops count under *Team*.
- **When it is removed** (from the party's menu, or by hand): the note goes and the row is back, with everything as it was.
- A host with no Operations (Orkline's page) has none of this: Team is not offered to it.

## 5. The cache
`pwa/sw.js` `CACHE` goes up and lists `shell-party-run.js`; the tests that pin it follow (`tests/test_pwa.py` and the
browser tests that name the version). Main had `orkcraft-app-v100`; the work is `orkcraft-app-v102` (the first session's
unfinished save already took v101, this one's second bump the next), so the part that merges after keeps the higher.

## 6. Order
A, B, C in parallel (B needs A's recipes for the ids, C is alone); D after C (it reads `ops_team`); E last. Each part merges
into `main` when its tests pass (the alpha rule).

## As built
- The saved work of the first session was completed and corrected in the second: nothing in it was left half-done except
  what is listed under *Not built*; `recurring.hand_over` (written, never used) went.
- **Python**: `realm/recurring.py` (`ROUTINES` by recipe id, `listed`, `get`, `text_of`, `every_of`, `words_of`, `set_every`,
  `due`), `realm/ops_team.py` (`get`, `set`, `clear`, `where`), `party_recipes.py` (`TEAM_ID`, `TEAM`, `is_team`,
  `running_name`, `RUNNING_NAMES`), `party_presets.listed(kind, team_at, ops)`, `gui/ideas_running.py` (`RunningMixin`:
  `team_at`, `team_heal`, `team_refuse`, `team_made`, `team_dropped`, `ideas.team`, `ideas.repeat`, `routines_*`),
  `gui/ops.py` (`Ops.team`, `Ops.moved`), `gui/board_host.py` (`BoardHost.ops`, `ops_team` in both snapshots).
- **Desktop**: `js/shell/partyrun.js` (`useRoutines`, `Routines`, `TeamNote`), `js/arena/goaltabs.js` (`teamOf`, `opsRow`),
  `OpsField` serves the Team party. **Phone**: `pwa/shell-party-run.js`, `shell-arena.js` (`opsView(team)`, `pickOps`),
  `shell-arena-words.js` (`teamOf`, `partiesOf().onTeam`), `shell-where.js` (the line), `shell-stops.js`.
- **Tests**: `tests/test_running_team.py` (recipes and routines by kind, the presets, one Team party, its note and its
  healing, no goals in it, a host with no Operations, recurring goals made, renewed, reopened, stopped),
  `tests/test_running_team_desktop_browser.py` and `tests/test_running_team_pwa_browser.py` (stub hosts: the row and its
  line, a Team party made and its Board, Team greyed, a Run party's recurring goals, on both faces),
  `tests/test_running_team_real_browser.py` (Orkboard's own host: the line, Save, the real Operations list in the Team party's
  field, the person's note outside the repository, Team greyed, removing it); `tests/test_party_presets.py` and the browser
  tests that list New party's presets (Team is the last of *By craft*) follow the new names and leaders; the ops tests' `StubOps`
  says it has no Team party.
- **`tests/test_arena_magic_desktop_browser.py`** waited for *No parties yet* in vain: the stub host of
  `tests/test_arena_desktop_browser.py` looked up a node (`cookie`) that an empty Board does not have, so every `ideas.board`
  call raised and the page never read the Board. The test's stub was wrong, not the page; it now asks for no node that is not there.
- **Not built**: a face to make an ordinary goal recurring (`ideas.repeat` does it; the running parties are where the
  person meets it); moving a Team party from one project to another (remove it, make it again: the Operations stay);
  reaching Operations from a project other than the Team party's.
