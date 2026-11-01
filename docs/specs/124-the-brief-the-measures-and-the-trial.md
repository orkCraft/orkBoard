# 124. The brief every leader reads, the measures of the arguing, and H1's trial

Decisions §202 (1–5). The owner, 1 November: *Orkboard is where you think out your product with a set of specialists who
discuss your ideas, criticise them and polish them.* Hypothesis H1 (`docs/hypotheses.md`) lists what that lacks before more
faces: a brief every leader reads, any measure of how good the arguing turned out, and the head-to-head. **Builds:** Claude ·
**Review:** full · P1. No new face, no new event, no new pane, column or dialog (§104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The brief** | six lines in the common core; the second sitting; Ideation reads it | `realm/project_facts.py` (`COMMON_KEYS`, `LABELS`, `COMMON_CHARS`), `realm/project_questions.py` (`SITTINGS`, `BRIEF`, `due`, `keys_of`), `core/idea_project_q.py`, `gui/ideas_project_q.py` (`brief_more`), `gui/ideas.py` (`add`), `core/idea_judge.py` (`pitch_parts`); `tests/test_project_facts.py`, `tests/test_idea_project_q.py` |
| **B. The measures** | the arguing measured from the event log; `orkboard measures` | new `realm/measures.py`, `gui/board_cli.py`; new `tests/test_measures.py` |
| **C. The trial** | H1's head-to-head: the protocol, the blind CSV, the tally | new `docs/trials/h1-head-to-head.md`, new `realm/trial.py`, `gui/board_cli.py`; new `tests/test_trial.py` |
| **D. The words** | the README's first line; H1 updated | `README.md`, `docs/hypotheses.md` |

## 0. What is there today

- **The common core** (spec 99 §2.2, `project_facts.common`): whom it is for, what hurts them, what it leaves out, about 600
  characters, read into every leader's call (`for_call`: Talk, verdicts, sections, concerns, the tree, hypotheses, the loop,
  a quick question). Asked once at the first start (`core/idea_project_q.py`), three cards of Product's leader (Game design's
  in a game), the Orkmaster's one card with neither party.
- **Ideation's calls** (spec 65, `core/idea_judge.py`) read the pitch, the parties, the goals and the pitches passed, **not the
  core**: a view judged a pitch without knowing whom the product is for.
- **The event log** (`realm/event_log.py`) keeps, since specs 65, 108, 120 and 121, every event a measure needs:
  `leader_objected`, `objection_answered`, `talk_verdict`, `talk_heard`, `hearing_thrown`, `concerns_made`, `concern_goal`,
  `concern_dismissed`, `pitch_judged`, `pitch_sent`, `pitch_passed`, `sketch_made`, `sketch_answered`, `result_decided`,
  `plan_passed`, `plan_change_answered`, `idea_edited`. Nothing reads them as measures.

## A. The brief

1. **Six lines** (`COMMON_KEYS`, in the order they are read): *Whom it is for*, *What hurts them*, *Why this, not what they
   use now* (`why_us`), *What it must always be* (`pillars`), *What it leaves out*, *How it earns* (`earns`). The core is cut
   to 1,000 characters, each line its share, cut with a mark. A hobby's *How it earns* is an answer (*Nothing: a hobby*).
2. **Two sittings** (`project_questions.SITTINGS`): the first start's three (whom, hurts, leaves out) as before; the brief's
   other half (why this, what it must always be, how it earns) is the same call's second sitting, its prompt saying the brief
   *still lacks* them. The record keeps `sitting`; a record of before this spec reads as the first. `due(rec, known)` is the
   sitting to ask: the first with a key not answered, from the one after a sitting done (the same one when it failed or was
   never begun), 0 while one waits. A sitting answered or let go is never asked again.
3. **When**: the second sitting is asked when a goal is added (`ideas.add` → `brief_more`) after the first sitting is done,
   quietly: no refusal, no toast, a call that cannot be made now is asked at the goal after; it never troubles the goal. Never
   the first sitting from a goal: that one is the first start's. With neither Product's nor Game design's party, nothing (the
   Orkmaster asks only what the project is for). A second sitting stopped or not begun leaves the first done.
4. **Ideation reads it**: `pitch_parts` adds *What the project is (its brief: judge the pitch against it)* after the pitch,
   when the core has a line, so every view, the case against and the Investor judge against it.

## B. The measures

`measures.of(root, since, until)` reads the project's event log; `measures.text(m)` says it. Each a count and a share
(`None` and *—* when there is nothing to share):

- **talk**: goals talked over; a no, a doubt (and how many named a smaller or other goal); the objections answered, **heeded**
  (`drop` · `smaller` · `later`) or **overruled** (`go`), the share heeded; the leaders who changed their verdict after the
  person's answers; hearings by kind; **the overruled goals decided at Review and how many came back** (a result sent back,
  fixed or dropped), **beside the same share of the goals no leader objected to**. A no earns its noise when the goals it lost
  came back more often than the others; a no that never does is noise, a leader that never objects is a yes-man.
- **concerns**: looks, concerns found, opened, made a goal, not a problem, the share made a goal.
- **pitches**: judged (invest · reshape · pass), decided by the person, as the Investor said, the share.
- **sketches**: made, picked, asked again, skipped, the share picked.
- **results**: goals decided at Review (a merge, a send back, a fix or a drop), **accepted the first time** (the first decisive
  answer a merge), the share.
- **after_start**: goals started (`plan_passed`), the changes after it (a plan change taken, a section written by hand on a
  passed plan), the goals changed, a goal's average.

`orkboard measures [<folder>] [--since DAY] [--until DAY] [--json]` prints them. **Not in the window**: no count of anything
in the frame (§104.0); a later spec may give Product's leader its party's lines to calibrate on.

## C. The trial

The protocol is `docs/trials/h1-head-to-head.md`. `realm/trial.py`: `template(path, tasks, seed)` a CSV of two rows a task
(`task, way, shown_as, accepted, changes, questions, minutes, tokens`), each way shown as A or B at random so the judge never
sees the way; `read(path)` checks the filled rows in plain words, a row not judged yet left out; `tally(rows)` over the tasks
done both ways: each way's share accepted the first time, its averages, the gap in points, the minutes' ratio and **the
verdict**: `holds` (Orkboard wins by `GAP` = 20 points or more at no more than `MINUTES_RATIO` = 2× the minutes),
`does not hold` (with which of the two failed), `too few` (under `MIN_TASKS` = 10). `orkboard trial new <file.csv> --tasks
<tasks.txt> [--seed N]` writes the CSV (never over a file that is there); `orkboard trial <file.csv> [--json]` tallies it.

## D. The words

- README's first line: *Orkboard is where you think out your product with a table of leaders — product, design, tech, art,
  marketing, release — who judge each goal against your real code and running product, say no where it hurts, and hand
  what you decide to your own AI tools to build and check.*
- H1: *What already exists* gains the brief, the measures and the trial; *Missing* keeps the stage-weighted rubrics and the
  shorter way; *How we test it* names `orkboard trial` and `orkboard measures`.

## Tests

`tests/test_project_facts.py` (six lines in their order, every leader reads them, cut to 1,000), `tests/test_idea_project_q.py`
(the second sitting asked once, after the first, at a goal added, never before; stopped, the first stays done; `due`),
`tests/test_measures.py`, `tests/test_trial.py`; the critical tests.
