# 127. The field's best in the Board's formats: a decision's year and what it changes, MADR for a new project, Done when as scenarios, living specs, a readable journal

Decisions §205 (1–6). **Builds:** A and D by the spec's author (built); B and C by the cheaper model, the spec's author
reviewing · **Review:** full · P1. After spec 126. No new face (§104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. A decision's year and lines** (built) | the year in the heading; `Status:` and `Changes:` read; this repository's 160 headings given 2026 | `core/idea_decide.py` (`entry_of`), `realm/doc_formats.py` (`parse_log`: `day`, `who`, `status`, `extra.changes`; `day_of`), `realm/write_out.py`, `realm/read_in.py`, `docs/decisions.md`; `tests/test_idea_decide.py`, `tests/test_doc_formats.py` |
| **B. What a decision changes; MADR for a new project; Done when as scenarios** | the Orkmaster names the decisions it changes; the line and its readers; a new project's first decision a MADR file; the sections' Done when as *When …, then …* | `core/idea_decide.py` (`decision_prompt`, `clean_decision`, `_enter`, `_write_record`), `realm/decisions_log.py` (`path`, `headings`, `context`), `core/idea_sections.py` (the prompt), `realm/spec_sections.py` (`clean_section` keeps the bounds); `tests/test_idea_decide.py`, `tests/test_decisions_log.py`, `tests/test_idea_sections*.py`, new `tests/test_decision_changes.py` |
| **C. Living specs** | the capability specs, folded at main, read by the leaders, written out and read in as OpenSpec | new `realm/living_specs.py`, new `core/idea_fold.py` (a keeper mixin), `core/idea_keeper.py` (bases), `realm/idea_target.py` (step `fold`, `CONTEXT`), `realm/idea_spend.py` (`STEP_STAGE`), `realm/event_log.py` (`spec_folded`), `gui/ideas_gate.py` (the trigger), `core/idea_talk.py` and `core/idea_sections.py` (the part), `realm/write_out.py`, `realm/read_in.py`; new `tests/test_living_specs.py`, `tests/test_idea_fold.py` |
| **D. The journal's mirror** (built) | `<state_dir>/journals/<scope>.md` written again after each add, strike and digest | `realm/journals.py` (`mirror`); `tests/test_journals.py` |

B and C are built side by side; they share `core/idea_sections.py` (B: the Done when rule in the prompt's rules; C: one
context part) and nothing else. Neither changes A's or D's files beyond what is listed.

## A. Built

`entry_of` writes `(<day> <month> <year>, …)`; `doc_formats.day_of` reads `17 October 2026` or `2026-10-17`; `parse_log`
gives each entry `day` (ISO, "" when its heading has no year), `who`, and reads the lines under the heading
`Status: <word>` (the status) and `Changes: 110, 183` (`extra.changes`, ints). Export and import use `day`.

## B. What a decision changes; MADR for a new project; Done when as scenarios

1. **The Orkmaster names what it changes**: `decision_prompt` already gives the project's decisions file's last headings
   (`decisions_log.context`); its answer gains `"changes": [numbers]`, *the earlier decisions this one changes or
   replaces, from the headings above; [] when none*. `clean_decision` keeps the ints that are among the headings' numbers
   (at most 6). The decision kept (`spec_sections.record(...)["decision"]`) holds `changes`.
2. **Written**: in the one file, the entry's body starts with the line `Changes: 110, 183.` (`entry_of` unchanged: `_enter`
   puts the line first in the body); in an ADR folder (`_write_record`), MADR's front matter `ork-changes: [110, 183]`, and
   a Nygard record a line `Changes: 110, 183.` at the top of its *Decision*. The person's correction keeps what they write.
3. **Read**: `decisions_log.headings` (one file and folder) appends ` (changed by 205)` to a heading that a later entry's
   `Changes:` names (the folder: its `ork-changes`), so every leader's context shows what no longer stands as written;
   `context` the same. The project's journal's `decision` line (spec 125, `journal_notes`) gains ` (changes 110, 183)`.
4. **A new project gets MADR**: `decisions_log.path(root, chosen)` with nothing chosen, no `docs/decisions.md`, and no log
   `found` returns the folder `docs/decisions` (made by the first `write_decision`, `BoardTree.add_file`), so its first
   decision is `docs/decisions/0001-<title>.md` in MADR. **A project with any log is unchanged**, and so is every test
   project that has `docs/decisions.md`; a test that relied on the one file being made from nothing is changed to the
   folder and says so.
5. **Done when as scenarios**: the sections' prompt (`core/idea_sections.py`) says each *Done when* line is one
   scenario, `When <a person or the product does something>, then <what is seen or kept>`, checkable by a test, five at
   most; `clean_section` keeps its bounds and takes any line (an older page's theses still read). The plan's and the
   checks' prompts are not changed.

## C. Living specs

### C.1 The store (`realm/living_specs.py`, no model)

`<board>/specs/<capability>.md`, where `<board>` is the Board's pages root (the root the goals' and parties' pages are read
from: `ideas.track_page(root, …)`'s `root`, as `gui/ideas.py` `self.root()`), so the specs are committed with the Board's
pages as the pages are. `<capability>` is a slug (`[a-z0-9-]`, at most 60). The file is OpenSpec's shape with front matter:

```
---
capability: Sign-in
parties: [design, tech]
goals: [add-lobby, magic-link]
updated: 2026-11-01
---

# Sign-in

## Purpose

How a player gets into a game.

## Requirements

### Requirement: Magic link

The product SHALL send a link that signs the player in.

#### Scenario: A link is asked for

- **WHEN** a player types their address and presses Send
- **THEN** a link arrives within a minute
```

`read(board, cap)` → `{capability, title, purpose, parties, goals, updated, requirements: [{name, text, scenarios: [{name,
when, then}]}]}` or None; `list_(board)` → `[{capability, title, purpose, parties, requirements: [names]}]`;
`render(spec)` → the text; `apply(board, cap, delta, goal, party, title=, purpose=)` → the spec after OpenSpec's archive
semantics: `added` appended (a name already there is *modified*), `modified` replaces the requirement of that name whole,
`removed` drops it by name; `goals` and `parties` gain the goal and the party; `updated` today. `text(board, party, chars)`
→ what a call is given: *How the product works now*: every capability one line (`Title: purpose`), then the
requirements of the capabilities whose `parties` hold `party`, the latest updated first, within `chars` (2,500).

### C.2 The fold (`core/idea_fold.py` `FoldMixin`, a base of `IdeaKeeper`)

When a goal reaches main — `gui/ideas_gate.py` where it raises its flag (the place spec 125 B writes the project's `done`)
— `keeper.fold(slug)` starts in the background, quietly (`try`/`except`, busy or not allowed: skipped, never an error), one
call of the goal's home party's leader, **step `fold`** (`realm/idea_target.py`: in `STEPS` and every per-step table, the
cheaper tier as `concerns`, `CONTEXT` 12,000, reads 0, budget 0.05; `realm/idea_spend.py` `STEP_STAGE` `"fold": "spec"`),
**no tools**, key `goal:<party>`, given: the goal's title and its sections' *Why*, *Done when*, *Will be* and *Out*
(`spec_sections.read`), and `living_specs.list_` (names, purposes, requirement names). It answers:

```
{"capability": "sign-in", "title": "Sign-in", "purpose": "one line, for a new capability",
 "added": [{"name": "…", "text": "The product SHALL …", "scenarios": [{"name": "…", "when": "…", "then": "…"}]}],
 "modified": [ …the whole requirement, as added… ], "removed": ["name"]}
```

cleaned strictly (a capability slug; at most 8 requirements in all; a requirement with a name and text; at most 4
scenarios each, each with when and then; lines cut at 300) and applied with `living_specs.apply`. A goal with nothing to
fold (no *Done when*) is not called. Event `spec_folded` (`idea`, `capability`, `added`, `modified`, `removed`, `cost`)
in `realm/event_log.py`. A fold that fails keeps nothing.

### C.3 Read by the leaders

`core/idea_talk.py` `round_prompt` and `core/idea_sections.py`'s prompt add `living_specs.text(board, party)` as a part
of its own, *How the product works now*, after the journals and before the map; `CONTEXT["talk_round"]`,
`CONTEXT["section_first"]` and `CONTEXT["section"]` each grow by 2,500.

### C.4 Out and in

- `realm/write_out.py` `write` also writes each living spec as `openspec/specs/<capability>/spec.md` under `to` (the text
  as kept, front matter and all), counted as `specs` in its answer and the terminal's line.
- `realm/read_in.py` `take` also reads OpenSpec's current specs (`openspec/specs/*/spec.md`) and Kiro's requirements
  (`.kiro/specs/*/requirements.md`: each `### Requirement N` or user story as a requirement, its `WHEN … SHALL …` lines as
  scenarios) into living specs **only where no living spec of that capability is kept** (never over one), counted as
  `specs_read`. A file written by Orkboard's export is the same spec and is not read twice.

## Tests

- A, D: built (`tests/test_doc_formats.py`, `tests/test_idea_decide.py`, `tests/test_journals.py`).
- B: `tests/test_decision_changes.py` (the answer's `changes` cleaned to the headings' numbers; the line in the one file and
  the front matter in a folder; `headings` and `context` say *changed by*; the journal's line), `tests/test_decisions_log.py`
  (a new project's path is the folder; a project with a log unchanged), the sections' prompt says *When …, then …*.
- C: `tests/test_living_specs.py` (read, render, read back the same; apply: added, modified by name, removed, a name added
  twice is modified; list; text within its chars, the party's first), `tests/test_idea_fold.py` (the call's step, tier, no
  tools; the answer cleaned and applied; nothing to fold, not called; a failed call keeps nothing; the trigger at the flag;
  the event; the part in Talk's and the sections' prompts; export and import of OpenSpec and Kiro).
- The critical tests and the test files of every module touched.
