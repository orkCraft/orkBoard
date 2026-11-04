# 132. Four levels: a goal refined before Confirm, the way a change goes down, a finding taken up to its cause

Decisions §234 (1–9), with §237.1–3 and §237.7–8 (one quality card a goal, two answers on a finding, one *Change…* on the
decision, a change's cost in one line, the hand kept for what is urgent). **Builds:** C and D on the host first (the
spec's author reviewing and merging), then A, B and the faces of C and D on the cheaper model · **Review:** the critical
tests and each part's own · P1. After spec 131 (the slices and the cascade: the Decision level's mechanism, §234.7). No new
pane, column, drawer or dialog (§104.0, §145); no list of findings and no count (CLAUDE.md's frame).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Refining** (host and face) | the bubble's *Add to the goal*; the decision's one *Change…* (kept as written, or worded again) | `core/idea_decide.py` (`reword`), `core/idea_ask.py` (the bubble's `goal` line on a goal in analysis), new `gui/ideas_refine.py`; the decision card and the bubble in `gui/static/js/hand/*`, `gui/static/js/table/*`; new `tests/test_refine.py` |
| **B. The marks** (face) | the pane's title *Decision · Spec · Work · Quality*; a mark lit while its level holds something open | `gui/static/js/*` (the pane's title: §126.4's marks), `tests/test_gui_wording.py`, the table's browser test |
| **C. The way down** (host first) | what a change pulls below it and its price, on every change's row; the levels open on a goal | new `realm/way_down.py`; the rows of `realm/cascades.py` (spec 131 B.3), `realm/leader_change.py`, `realm/idea_change.py` (a plan change's stop); `gui/ideas_board.py` (a goal's `levels`); new `tests/test_way_down.py` |
| **D. Findings and the quality record** (host first) | a finding gathered where it is found; its content by the finder's leader (`finding`), its level by the Orkmaster (`finding_level`); one quality card a goal; *Fix it there*, *Not now*, *Another level…*; the *Quality* page | new `realm/findings.py`, new `core/idea_findings.py` (a keeper mixin), new `gui/ideas_findings.py`, the sources below, `realm/idea_target.py`, `realm/idea_spend.py`, `realm/event_log.py`, `realm/lexicon.py`; new `tests/test_findings.py`, new `tests/test_idea_findings.py` |

C and D are built side by side in their own worktrees; D's rows read C's `way_down.pulls` (D stubs it until C is merged,
then calls it). A and B stand alone.

## 0. What is there today

- **Decision**: the entry, confirmed by one button or edited by hand (spec 99 §6); spec 131's slices and cascade.
- **Spec**: a goal's sections (spec 99 §7); *Make it a change* to one leader (§206.5, `core/idea_leader_change.py`,
  `realm/leader_change.py`: its record's `before`/`after`, `estimate`).
- **Work**: a plan change (spec 62, `realm/idea_change.py`, `core/idea_revise.py` `change_price`); a failure's *Start again*.
- **Quality**: the discard's verdict against the spec by code (`realm/goal_result.py`: `ok` · `differs` · `missing` ·
  `extra` and *Done when*, shown by `gui/ideas_goalview.py`), the checks (`realm/idea_checks.py`), a leader's concerns
  (`realm/concerns.py`, spec 108), the hypotheses (`realm/hypotheses.py`), the measures (`realm/measures.py`). None knows
  the others; a ≠ becomes a new goal whatever its cause.
- A card's cost is said by the face from `{usd_low, usd_high}` (`gui/static/js/hand/cost.js`: *about 4% of Claude's week*).

## A. Refining before Confirm (§234.5, §237.3)

- **Add to the goal** (the bubble, a goal in analysis: not yet confirmed): `ideas.add_to_goal {idea, text}` appends the
  person's words, kept as written, to the goal's *Asked* (`ideas.update`, a line `Added: <text>`); when its decision is
  worded already (`decided`, not confirmed) it is worded again (`keeper.reword(slug)`: one `decide` call, the person's
  words given with the old wording). Refused in words for a goal confirmed (*This goal is agreed: ask its leader for a
  change*), gone, or the keeper busy with it. The bubble offers it when `ask`'s answer is about a goal in analysis.
- **Change…** (the decision's card, one button beside *Confirm and start*): the entry opens as a field; under it one line,
  *Or say what to change*. `ideas.decision_change {idea, text?, say?}`: `text` is kept as written (as *Edit* was:
  `way.json`'s `decision` takes it, `by: "person"`); `say` is worded again by the Orkmaster (`reword(slug, say)`: one
  `decide` call given the old entry and the person's words; *its cost* said on the line, `idea_target.budget("decide", …)`).
  *Edit* and *Change it in words* are this one button. Neither has a bound of rounds.
- **Talk stays** one round and its verdict (§121.2): refining is the decision's.

## B. The marks (§234.6)

The pane's title says **Decision · Spec · Work · Quality** in place of *Talk · Spec · Work · Done* (§126.4): *Decision*
opens Talk's page (the stances, then the decision's entry once worded); *Quality* opens the quality record (D.4). A mark
is lit (no number) when the goal's `levels` (C.3) holds its level. The words in `TERMS` (D.6) and in the tests that say
the marks' words.

## C. The way down (§234.2, §237.7)

### C.1 `realm/way_down.py` (no model, no face)

```
way_down.pulls(state_dir, root, level, *, slug="", party="", changes=(), parties=()) → {level, sections, tasks, checks, estimate}
```

- `level` **decision** (`changes`: the decision numbers changed; `parties`: the parties whose slices changed): the goals
  **not done** (not in the discard, §206.8) whose decision is one of `changes` or names one in its `changes`
  (`spec_sections.record(...)["decision"]`), each section of theirs written by one of `parties` → `sections`
  `[{idea, party}]`; then for each, as **spec** below.
- `level` **spec** (`slug`, `party`): that goal's open tasks of the party (`idea_change.open_task`, `leader_change.owned`)
  → `tasks` `[{idea, id}]`; then **work**.
- `level` **work** (`slug`, the tasks): each task's checks (`idea_checks`) → `checks` (a count).
- Nothing above the level is pulled, nor what the change does not touch.
- `estimate` `{usd_low, usd_high}`: the sections at `idea_target.budget("section", target)` each, the tasks at the
  board's learnt cost of their tier (`idea_spend`, as a plan's estimate is made; `idea_target.floor` with none learnt), a
  check at `budget("accept", target)`; `target` the goal's party's (`idea_target.target_for`).

### C.2 On every change's row

Each row the hand shows of a change gains `level` and `pulls` (C.1's dict): a cascade's (spec 131 B.3, `level:
"decision"`), a leader's change (`leader_change.rows`, `level: "spec"`), a plan change's stop (`level: "work"`), a
finding's fix (D.3). The face says it in **one line** (§237.7), its level's sign first: *About 4% of Claude's week: 2
sections, 3 tasks* (the share from `cost.js` as every gem's), what each is under **More**. *Changes the decision:* is the
sign's title, not a word on the card.

### C.3 The levels open on a goal

`way_down.open_levels(state_dir, slug)` → the levels that hold something open of the goal: `decision` (a cascade `ready`
whose `sections` name it, or its decision `decided` and not confirmed), `spec` (a leader's change `ready`, a fork open),
`work` (a plan change live, a task failed), `quality` (a finding not answered, D). The goal's row in `ideas.board` (`gui/ideas_board.py`) and the
pane read it as `levels`.

### C.4 Tests

`tests/test_way_down.py`: a decision changed pulls only the goals not done that rest on it and only the changed parties'
sections; spec pulls the party's open tasks only (a task at work or merged, and another party's, stay); work pulls checks;
nothing above; the estimate adds up its parts; `open_levels` for each kind; each row of C.2 carries `level` and `pulls`.

## D. Findings and the quality record (§234.3–4, §237.1–2, §237.8)

### D.1 The store (`realm/findings.py`, no model, no face)

- A goal's **quality record**: `<state_dir>/ideas/<slug>/quality.json`
  `{verdict: [goal_result rows], checks: [...], findings: [finding], hypothesis: {...} | null, at, status}`.
- A finding of no goal (a lens's alarm or a concern outside a goal's work): `<state_dir>/findings.json` `{findings: [...]}`.
- A finding: `{id, at, source, idea, party, on, found, what, shows, promised, cause, level, change, status, answer, fix}`:
  `source` `verdict` (a `differs` or `missing` of `goal_result`) · `check` (a check red after the goal landed) · `lens` (an
  alarm of the party's concerns on a part the goal touched, spec 108) · `concern` (outside a goal) · `hypothesis` (refuted,
  spec 133 D) · `measure` (missed, §202); `found` code's words of what was found; `what`, `shows`, `promised`, `cause` the
  finder's (D.2); `level` `work` · `spec` · `decision` and `change` the Orkmaster's (D.2); `status` `found` → `told`
  (content in) → `sorted` (level in) → `answered`; `answer` `fix` · `later` · `moved`; `fix` what was made of it
  (`{idea}` a goal, `{cascade}`, `{change}`).
- `add(state_dir, finding)` (one finding a source's thing, by `source`+`on`+`idea`: kept once), `of_goal`, `open_of_goal`,
  `answer(state_dir, id, answer, fix)`, `move(state_dir, id, level)`.

### D.2 Gathered, told, sorted

**Gathered by code** where each thing is known, each a `findings.add` inside a `try` that never fails what it records:

| Source | Where |
|---|---|
| `verdict` | when a goal reaches the discard (`gui/ideas_gate.py`, where `goal_to_main` is recorded): `goal_result.of(...)` read once; each `differs` / `missing` line a finding (`on` the part's id, `party` its party) |
| `check` | a check of the goal red after it landed (`idea_checks`, where a landed goal's checks are recorded) |
| `lens` | a party's look (`core/idea_concerns.py` `concerns_run`): an `alert` on a part a goal in the discard touched within its last `LENS_DAYS = 14` days (`goal_result.touched`) is that goal's; else a finding of no goal (`concern`) |
| `hypothesis`, `measure` | the entry `findings.add` only: spec 133 D and a later spec call it |

**When a goal's findings are in** (§237.1): its verdict read, its checks done and the lenses' looks of the day after
(or `QUIET_H = 24` hours after it reached the discard, whichever first: `keeper.findings_due()` on the clock's tick), the
keeper tells and sorts them, in the background, `key=f"quality:{slug}"`:

1. **Told** — for each party with findings, **one call of its leader** (step `finding`: the cheaper tier, **tools**, reads
   at most `READS["finding"] = 4`, its map, the party's own step `goal:<party>`, `CONTEXT["finding"] = 9000`), given each
   finding's `found`, the party's section's *Will be* and *Done when*, the goal's decision entry and the slices it rests on
   (spec 131), and the files the goal's commits changed in the part; it answers
   `{"findings": [{"id", "what", "shows", "promised", "cause"}]}`, each one line (`LINE_CHARS = 300`). A member's finding
   (a check a member ran) goes to its leader the same way.
2. **Sorted** — **one call of the Orkmaster** for the goal (step `finding_level`: the cheaper tier, no tools, READS 0,
   `CONTEXT["finding_level"] = 9000`), given every finding told, the decision's entry, the slices, the sections, the tasks;
   it answers `{"levels": [{"id", "level": "work" | "spec" | "decision", "change": "what would change there"}]}`. A finding
   the call left out is `work` (the cheapest fix, the person moves it).

A call that fails keeps what it had (a finding not told keeps code's `found` as `what`; one not sorted is `work`), never
stops the card. Events `findings_told` (`idea`, `party`, `findings`, `seconds`, `cost`) and `findings_sorted` (`idea`,
`findings`, `levels`: `{work, spec, decision}` counts, `seconds`, `cost`). Never a word of a finding.

### D.3 One quality card a goal (§237.1–2, §237.8)

`findings.rows(state_dir)` → one Needs-you row `kind: "quality"` a goal with findings sorted and not all answered:
`{kind, idea, title, findings: [{id, party, level, what, cause, change, pulls}], pulls}` — the findings **in order of their
level, Decision first**; `pulls` each its fix's way down (C.1) and the card's sum (*Fix all there*). A finding of no goal
is a row of its own, `kind: "finding"`. **Never urgent**: these rows lie after a failure and a question (the hand's order,
`js/table/piles.js`), push nothing to the phone and show no toast; **one quality card a goal**: a later finding joins its card.

The host's commands (`gui/ideas_findings.py`, a mixin of `Ideas`):

- `ideas.finding_fix {id}` — **Fix it there**, by its level: **work** → a fix goal on the same route, a bug (§158.3) whose
  diagnosis is the finding's content (no `diagnose` call: `what`, `shows`, `cause` are its diagnosis), titled
  *Fix: <what>*, marked `fixes: <slug>`; **spec** → the same, its finder's party's section written again from the
  finding before its plan (one `section` call); **decision** → a proposal into spec 131's cascade (`cascades.add`,
  `from_step: "finding"`, the slice the finding names or, with none, the decision as a whole). `answer: fix`, `fix` kept.
- `ideas.finding_fix_all {idea}` — **Fix all there**: each finding of the card, its cost said before (the card's `pulls`).
- `ideas.finding_later {id}` — **Not now**: `answer: later`; the finding stays on the goal's quality record and leaves
  the hand; taken again from the record with no new call.
- `ideas.finding_move {id, level}` — **Another level…** (under the finding's **…**): the level moved by the person, its
  `pulls` said again.

### D.4 The *Quality* page

`ideas.quality {idea}` → the record: the verdict against the spec (✓ ≠ + ✗ by *Done when*, as `goal_result` gives it), the
checks, the lenses' alarms on its parts, the hypothesis's outcome when it tested one, and each finding with its level and
what became of it (fixed there and by what, put off, moved). Picked in the discard, the *Quality* page shows it (it
replaces *Done*'s result, §126.4); the findings put off stay there, never in a list of their own.

### D.5 Tests

`tests/test_findings.py`: `add` keeps a thing once; the record's shape; `rows` one card a goal, levels in order, a finding of
no goal its own row; `answer`/`move`. `tests/test_idea_findings.py` (fakes): a goal reaching the discard with a ≠ gathers
one finding a line; a lens alarm on a touched part is the goal's, elsewhere of no goal; the told call is one a party and the
sorted one a goal; a failed call keeps code's words and `work`; *Fix it there* makes a bug fix goal (work), a section's
change (spec), a cascade's proposal (decision); *Not now* keeps it on the record; *Fix all there*.

### D.6 The words

`TERMS`: `level` (*level*), `quality_finding` (*finding*: `finding` is the Mine's already, which Orkline reads), `quality_record` (*quality record*). The face's lines (A–D): *Decision*,
*Spec*, *Work*, *Quality*; *Quality of <goal>*; *<Party> found: …*; *The cause is in the code* / *the spec* / *the
decision*; *Fix it there*, *Fix all there*, *Another level…*, *Not now*; *Add to the goal*; *Change…*, *Or say what to
change*.
