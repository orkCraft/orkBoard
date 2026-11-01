# 125. The journals: the project's and each leader's, what was said and what came of it

Decisions §203 (1–7). The owner, 1 November: *the main thing is to keep, all the time, the project's common history and the
history of each of the leaders' views.* **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:**
full · P1. After spec 124 (the brief, the measures). No new face, no new pane, column, drawer or dialog (§104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The journals** (built by the spec's author) | the store: entries, strikes, the digest, the text a call is given | new `realm/journals.py`; new `tests/test_journals.py` |
| **B. The writers** | an entry written by code where each thing happens; the host's commands | `core/idea_decide.py` (`_enter`), `core/idea_talk.py` (`talk_run`), `core/idea_objection.py`, `core/idea_concerns.py` (`concerns_run`), `gui/ideas_concerns.py`, `gui/ideas_review.py` (or where a result is decided), `gui/ideas_gate.py`, `gui/ideas.py` (`drop`), `gui/ideas_hypotheses.py`, `gui/ideas_pitch.py`, `gui/ideas_project_q.py`, `gui/ideas_facts.py`; new `gui/ideas_journal.py`; `realm/lexicon.py`; new `tests/test_journal_writers.py` |
| **C. The readers** | both journals in every leader's call; the calibration line | `core/idea_talk.py` (`round_prompt`), `core/idea_verdict.py`, `core/idea_sections.py`, `core/idea_concerns.py` (its prompt), `core/idea_ask.py`, `core/idea_decide.py` (`decision_prompt`), `realm/idea_target.py` (`CONTEXT`), `realm/measures.py` (`of_party`); new `tests/test_journal_readers.py` |
| **D. The digest** | the leader's *in short*, written in the background on the cheaper tier | new `core/idea_journal.py` (a keeper mixin), `core/idea_keeper.py` (its bases), `realm/idea_target.py` (the step `journal`), `realm/event_log.py` (`journal_digested`), `gui/ideas.py` (`add`: the trigger); new `tests/test_idea_journal.py` |

B and C+D are built side by side in their own worktrees; they share `core/idea_talk.py`, `core/idea_decide.py` and
`core/idea_concerns.py`, B in the functions that act, C in the ones that write prompts. Neither changes `realm/journals.py`:
a change it needs is said to the spec's author.

## 0. What is there today

- The decisions file (`realm/decisions_log.py`): a leader's call gets its last ten headings and its own goal's entry
  (`context`), in a quick question, the decision's wording and the sections; **Talk gets none**.
- The brief (`realm/project_facts.py`): a state; a changed answer replaces the old, its why lost.
- Concerns (`realm/concerns.py`): the open ones and the dismissed; one fixed is forgotten; the evening line (`since`) keeps
  only its last.
- A leader's no (`idea_objections`) and what came of it: in the event log with no words (spec 124's measures count them).
- A pitch passed keeps its why (`pitches.passed`); a goal dropped does not.

## A. The journals (`realm/journals.py`, built)

`add(state_dir, scope, kind, text, *, idea, on, ref)` → the entry or None; `read`, `of_goal`, `strike`, `digest`,
`save_digest`, `since_digest`, `text(state_dir, scope, *, idea, on, chars)`. A scope is `journals.PROJECT` or a party's
slug. An entry `{id, at, kind, text, idea, on, ref}`; `text` one line, at most 300 characters, **in the product's words, in
the second person for a leader's journal** (*You said no to “Add a lobby”: it would break the cache.*) and the third for the
project's (*Decision 12: no accounts in the first release.*). Kinds:

- **project**: `decision` · `done` (a goal reached main) · `dropped` · `hypothesis` (judged) · `brief` (a line of the brief
  answered or changed by the person) · `pitch_passed`.
- **leader**: `stance` · `heeded` · `overruled` · `came_back` · `went_through` · `concern_goal` · `concern_dismissed` ·
  `since` (the evening line) · `calibration` (reserved; C's line is computed, never kept).

## B. The writers

Each writer is **one call to `journals.add` after the thing has happened and been kept**, inside a `try` that never lets a
journal fail what it records (`except Exception: pass`, as the event log never troubles the town). A goal's title is read
with `ideas.idea_page(root, slug).title` (its slug when there is no page). A party's leader's journal is the party's slug.

| When | Where | Scope · kind | The line (`idea`, `on`, `ref`) |
|---|---|---|---|
| a decision confirmed | `core/idea_decide.py` `_enter`, after `write_decision` | project · `decision` | `Decision {n}: {title}` and, when the person overruled leaders, ` (against {Leader}: {why})` from `idea_objections.lines` (`idea` the slug, `ref` the number) |
| a hypothesis judged held or refuted | `gui/ideas_hypotheses.py`, after `hypotheses.judge` | project · `hypothesis` | `“{text}” held: {why}` / `… was refuted: {why}` (`ref` the decision's number, when one) |
| a goal reaches main | `gui/ideas_gate.py`, where `idea_flagged` and `goal_to_main` are recorded (once a goal: skip when `of_goal` already has a `done`) | project · `done` | `“{title}” is in main` |
| a goal dropped by the person | `gui/ideas.py` `drop`, before the page is gone (read the title first) | project · `dropped` | `“{title}” was dropped` and `: {why}` when the command carried one |
| a pitch passed | `gui/ideas_pitch.py`, after `pitches.save(... passed=...)` | project · `pitch_passed` | `Pitch “{title}” passed: {why}` |
| a line of the brief answered or changed by the person (`by == "person"`, a key of `project_facts.COMMON_KEYS`) | `gui/ideas_project_q.py` `project_answer` and `gui/ideas_facts.py` `project_fact_set` | project · `brief` | `{LABELS[key]}: {text}` (a dropped line: `{LABELS[key]}: dropped`) |
| a leader's stance in Talk's first round | `core/idea_talk.py` `talk_run`, after the stances are kept | the leader's party · `stance` | `On “{title}” you said {verdict}: {why or stance}` (`on`: the goal's `marks` ids, `ideas.state(...).get("marks")`) |
| an objection answered | `core/idea_objection.py` (`objection_answer` and `throw`, wherever `objection_answered` is recorded) | that party · `heeded` (drop · smaller · later) or `overruled` (go) | `Your no to “{title}” was heeded: the person {dropped it · made it smaller · put it later}` / `The person went on with “{title}” against your no: {why}` |
| a result decided at Review, for each party whose leader said `no` or `doubt` on that goal (its Talk stances, `idea_questions.record(state_dir, slug)["stances"]`) | where `result_decided` is decided on the host's side (`gui/ideas_review.py`), after the runner's call returns | that party · `came_back` on the first send back, fix or drop; `went_through` on a merge with no `came_back` before (each once a goal) | `“{title}”, which you doubted, came back at Review: {why}` / `“{title}”, which you said no to, went through at Review the first time` |
| a concern made a goal | `gui/ideas_concerns.py`, after `made_goal` | that party · `concern_goal` | `Your concern on {part name} became the goal “{title}”` (`on`: the part's id) |
| a concern called not a problem | `gui/ideas_concerns.py`, after `dismiss` | that party · `concern_dismissed` | `The person said your concern on {part name} is not a problem: {what}` (`on`: the part's id) |
| the evening line | `core/idea_concerns.py` `concerns_run`, when a `since` is kept | that party · `since` | `Since your last look the {map} went {toward · away from} what you keep: {line}` (`unclear`: `… changed; it is unclear which way: {line}`) |

**The host's commands** (`gui/ideas_journal.py`, a mixin of `Ideas`, its commands added as `project_q_commands` are):
`ideas.journal {party?}` → `{"entries": [...], "digest": {...}}` (no party: the project's; struck entries with `struck`);
`ideas.journal_strike {party?, id, why?}` → `{"ok": true, "entry": ...}`, *No such entry* refused in plain words. A party is
one of the project's (*No such party* else). The host returns data, never interface words but a refusal's.

**The word**: `TERMS` gains `_t("journal", "journal", "journals")` with its line (decisions §203.1).

## C. The readers

Every leader's call is given, as parts of its context, **its own journal** (`journals.text(state_dir, party, idea=slug,
on=marks)`) and **the project's journal** (`journals.text(state_dir, journals.PROJECT, idea=slug)`), each a part of its
own, *after* the project's facts and **before** the map (the map is what is cut when the context is full); `CONTEXT` of
each step below grows by 3,000 characters so that nothing that fit before is cut now. A member's call gets none.

| Step | Where | Given |
|---|---|---|
| `talk_round` (both rounds) | `core/idea_talk.py` `round_prompt` | both, the goal's slug and marks |
| `talk_verdict` | `core/idea_verdict.py` | both |
| `section_first`, `section` | `core/idea_sections.py` | both |
| `concerns` (the leader's look) | `core/idea_concerns.py` | its own (`on`: none), the project's |
| `ask` (a quick question) | `core/idea_ask.py` | the asked party's leader: both; the Orkmaster's tab: the project's alone |
| `decide` (the decision's wording, the Orkmaster's) | `core/idea_decide.py` `decision_prompt` | the project's alone |

**Calibration** (decisions §203.5): `measures.of_party(root, party)` → `{objections, overruled, overruled_decided,
overruled_came_back, unobjected_came_back_share}` over the party's own `leader_objected` / `objection_answered` lines and
the goals' `result_decided`; `journals`' text for a leader's call is followed, when the leader has had a no overruled and
decided, by one line: `Your record: {overruled} of your {objections} no's were overruled; {came_back} of the {decided}
decided came back at Review ({share}), against {other} of the goals no one objected to.` Computed at the call, never kept.

## D. The digest

`core/idea_journal.py` `JournalMixin` (a base of `IdeaKeeper`): `journal_due(party)` → True when the party's journal has
`DIGEST_AFTER` = 12 entries or more after its digest (`since_digest`) and the digest is a day old or more (or none);
`journal_digest(party)` starts, in the background, `_start(party, "digesting", ..., key=f"goal:{party}")` (busy: skipped,
never an error), one call of the party's leader, **step `journal`** (`realm/idea_target.py`: in `STEPS`, the cheaper tier as
`concerns`: `{"thrift": ("laborer", ""), "balance": ("warrior", "low"), "quality": ("warrior", "medium")}`, `CONTEXT` 10,000,
reads 0, budget 0.05), **no tools**, given its old digest and the entries since; it answers `{"digest": "…"}` (at most 900
characters: what its lens knows of the product and of how the person decides, never a list of entries), kept with
`journals.save_digest(..., upto=<the last entry's id>)`. A call that fails keeps nothing; the next trigger tries again. The
project's journal has no digest (its entries are short and few).
**The trigger**: `gui/ideas.py` `add`, after the goal is added (where spec 124's `brief_more` is), for each party on the
goal's route whose journal is due, quietly (`try`/`except`), as `brief_more` is. **The event**: `journal_digested` (`party`,
`entries` read, `chars`, `seconds`, `cost`) in `realm/event_log.py` `EVENTS`, never a word of the digest.

## Tests

- `tests/test_journals.py` (A, built).
- `tests/test_journal_writers.py`: each row of B's table writes its one entry with its kind, its goal and its parts
  (a host and its stubbed keeper, as `tests/test_idea_project_q.py` composes them); a journal that cannot be written fails
  nothing; `came_back` and `went_through` once a goal; the commands and their refusals.
- `tests/test_journal_readers.py`: each step of C's table has both journals (or the one it is given) in its prompt, before
  the map; a member's call has none; the calibration line and `measures.of_party`.
- `tests/test_idea_journal.py`: due and not due; the call's step, tier and no tools; the digest kept with its `upto`; a
  failed call keeps nothing; the trigger on `ideas.add`; the event.
- The critical tests (`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`) and the test files
  of every module touched.

## As built (1 November)

- **B** (`realm/journal_notes.py` holds every line's words and the wrapper that swallows a failure, so each hook is one line;
  `gui/ideas_journal.py` the commands). Where it differs: in a hearing thrown to *drop* or *later*, only the leaders on the
  chosen side get `heeded`, the others no `overruled` (the goal was not gone on with), so the journals and spec 124's
  measures may count an overruled no a little differently; Review cannot tell a *fix* from a *back* on the host's side, both
  are `came_back`; a goal dropped by a hearing writes `heeded` but no project `dropped` (only `ideas.drop` does); the evening
  line names the map (*the screens map*).
- **C** (`core/idea_journal.py` `parts`): in a quick question the journals follow the facts, which already follow the map,
  so they come after the map there; a leader with a record line and an empty journal still gets the part with the line;
  `realm/idea_spend.py` `STEP_STAGE` gains `journal` (its cost in the *spec* stage).
- **D** as written. `measures.of_party` reads the whole event log at each call: a cache is for when the log grows large.
