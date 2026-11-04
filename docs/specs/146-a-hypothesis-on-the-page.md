# 146. A hypothesis on the page: its conditions and measures on the tree's card, *Did it hold?* with the values and the draft, and the two host parts spec 133 left

Decisions §235 (§235.1–§235.7) and §237.4, on spec 133's host (its §6 *Not here* and §7 *Not built yet*). **Builds:** the
cheaper model, C first (the host the faces read), then A, then B, each its own commit into `main` as its tests and the
critical ones are green (CLAUDE.md, Alpha) · **Review:** the critical tests and each part's own · P1. Desktop only. No new
pane, column, drawer or dialog. No change to orkUI.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The tree's card** | *More* on a hypothesis: *Holds when*, one to three ways *Refuted when*, *If it holds*, the measures (what, from, whose map, a bar per condition, the span or the day); adding still asks two lines | `gui/static/js/table/treemap.js` and a new `table/hypothesisform.js` (treemap.js is 315 lines); `tests/test_hypotheses_tree_browser.py` (new, or the tree's browser test if one holds the hypotheses) |
| **B. *Did it hold?*** | the card lifted: the measures' values one line each, the condition code met marked, a value not read asked, the way it is refuted picked, the draft under *More* changed in words, *Not sure yet* asks a day | `gui/static/js/hand/hypothesiscard.js` and a new `hand/hypothesisjudge.js`; `tests/test_hypothesis_card_browser.py` (new) |
| **C. The host spec 133 left** | B.3's leader reading (`measure_read`) and C.2's `- Measure:` lines of the file | new `core/idea_hypothesis_values.py`, `realm/idea_target.py` (the step), `realm/event_log.py`, `gui/ideas_route.py` or the keeper's tick (when it is begun), `realm/hypotheses_file.py`; new `tests/test_idea_hypothesis_values.py`, `tests/test_hypotheses_file.py` |

**Not this spec:** the phone's faces of a hypothesis; the Orkmaster's `decide` call wording a decision from a hypothesis with no
draft (code words its body, as spec 133 A.3 built); a measure read from an analytics service (spec 115's later one); a measure
missed as a finding's source; Talk's `assumes` carrying conditions.

## 0. What is there today

- The host of spec 133 A, B (but B.3), C (but C.2's measure lines) and D: `realm/hypotheses.py` (`add`, `edit`, `judge(…, way, date)`,
  `draft`, `due`, `value`, `measure_set`, `measure_drop`), `realm/hypothesis_measures.py` (`clean`, `date_of`, `met`, `shown`),
  `realm/hypotheses_file.py`, `realm/hypotheses_bind.py`, `realm/board_rows.py` (`hypothesis` rows with `refuted`, `if_holds`,
  `draft`, `measures`, `met`), `gui/ideas_hypotheses.py` (`ideas.hypothesis_set {…, refuted?, if_holds?}`, `hypothesis_judge {id,
  state, why?, way?, draft?, date?}`, `hypothesis_measure_set`, `hypothesis_measure_drop`, `hypothesis_value`, `hypotheses`).
- The page knows none of it: `table/treemap.js`'s card shows the text and *We'll know when*; its field asks *We believe* and
  *We'll know when*; `hand/hypothesiscard.js` asks *Did it hold?* with **Held**, **Refuted**, **Not sure yet** and a *Why* line.
- Nothing reads a measure's value from a leader (`measure_read`); a bound file's measures live in the record only.

Read spec 133 §A–§D whole before building: its words and shapes are this spec's; what follows says only where they go on the page.

## A. The tree's card (§235.1, §235.2, §237.4)

1. **Adding stays two lines** (§237.4): *We believe* and *Holds when* (the field's second line renamed from *We'll know when*: the
   record's `signal`, spec 133 A.1), **Save**, **Cancel**. Nothing else is asked to add one.
2. **More** on a kept hypothesis's card (proposed or open; a judged one shows its verdict and no *More*) opens, in the card's own
   place (it grows; nothing opens beside it):
   - *Holds when* (the `signal`), *If it holds* (`if_holds`, a few lines);
   - *Refuted when*: one to three ways, each *What it would teach* (`name`, short), *When* (`when`) and *Then* (`change`), **+ A way**
     while there are fewer than three, a way's **Remove**;
   - *Measures*: up to four, each *What* (`what`), *From* (`from`), *Whose map* (a party of the project, or *You*: `by`), a bar for
     *Holds* and for each way (`op` from a short list *at least · more than · at most · less than · exactly*, a number, a unit), and
     *For* (`span_days`: *2 weeks · 4 weeks · 8 weeks*) or *Until* a day (`date`); **+ A measure**, a measure's **Remove**;
   - **Save** sends `ideas.hypothesis_set {id, signal, if_holds, refuted}` and each changed measure's `ideas.hypothesis_measure_set`
     (a removed one `ideas.hypothesis_measure_drop`); the host's refusal (*A way it is refuted says when*, …) is said under the field,
     in its words; **Cancel** puts it back.
3. **What the card says closed**: its text; *Holds when* and its signal; under it one line a way, *Refuted when <name>: <when>*
   (§A.2's words); one line a measure, *<what> · until 1 Dec* (the date). **No value before its date** (the host strips them,
   `hypothesis_measures.shown`): never a number, a bar filling or a count in the window.
4. **Tests**: the two lines to add; *More* shows the conditions of a kept one and saves the ways and a measure through the commands
   (a stub host records them); a refusal is said; a judged one has no *More*; no number on a card whose measure's date is ahead.

## B. *Did it hold?* (§235.2, §235.3, §235.5, §237.4)

1. **Lifted** (`hand/hypothesiscard.js`), under the hypothesis and *Holds when*:
   - the measures, one line each: *<what>: 64 % of the Work clip's — the bar ≤ 70* (the value, its unit, the condition's bar), and
     where code met a condition (the row's `met`) the line says it: *Holds: met* or *Refuted, <name>: met*; never a verdict of its own;
   - a measure with no value: a number field and *From* (optional) and **Keep** (`ideas.hypothesis_value {id, measure, n, from?}`):
     *the one answer here that is typed* (spec 133 B.3); the card reads the Board again after it;
   - the answers: **Held**; **Refuted**, which with ways asks *Which way?* (the item's ways as choices, the one met by code first;
     one way is taken at once); **Not sure yet**, which asks a day (*Look again on*, a date field, today + 7 at first) and sends
     `ideas.hypothesis_judge {id, state: "unsure", date}`.
2. **The draft is the decision** (§237.4, spec 133 A.3): for Held and Refuted, under *More*, the draft (`row.draft.held`, or the
   picked way's `row.draft.refuted[<name>]`) as text, with **Change it in words** (a text field with the draft in it, sent as
   `draft`); with no draft *More* is not shown and the host words the body. The *Why* line stays.
3. **Tests**: a row with two measures, one with a value (its line, its bar, *Holds: met* from `met`) and one without (the field;
   **Keep** sends `hypothesis_value`); Refuted with two ways asks which, with one sends it; the draft changed in words is sent as
   `draft`; *Not sure yet* sends the day; a row with no measure and no draft looks as today.

## C. The host spec 133 left (§235.2, §235.6)

1. **The leader reads the values** exactly as spec 133 B.3 says: `core/idea_hypothesis_values.py`, `keeper.measures_read(id)`, the
   step `measure_read` in `realm/idea_target.py` (the cheaper tier, tools, `READS["measure_read"] = 4`, the party's own step,
   `CONTEXT["measure_read"] = 9000`); begun on the clock's tick, once, for an item that is open, whose goals are all done (or has
   none), whose date is reached and which has a measure with a `by` and no value; never by a press; strict answers
   `{"values": [{"id", "n", "from"}]}`; what it leaves out, a failed call, no model or a spent window: the person types it (B.1).
   Events `measure_read` (`idea`, `party`, `measures`, `read`, `seconds`, `cost`), never a number. Read a sibling step (the slices',
   `core/idea_slices.py`; the findings', `core/idea_findings.py`) for how a step is asked, cleaned and recorded.
2. **The file's measure lines** exactly as spec 133 C.2 says: `- Measure: <what> — from <source>[ (by <party>)] — holds <op> <n>[ <unit>][,
   refuted <way> <op> <n>[ <unit>]] — <N> weeks | <N> days | until <YYYY-MM-DD>` under *How we test it*, read into `measures` and written
   from them (`realm/hypotheses_file.py` `parse` and `apply`); only a line of exactly that shape names one; every other line is kept as
   it is; a measure's value is never written to the file.
3. **Tests**: spec 133 B.5's `tests/test_idea_hypothesis_values.py` (fakes: asked at the date and not before, the party's values kept, a
   value left out asked of the person, a failed call asks the person, the event with no number); in `tests/test_hypotheses_file.py` a
   section with two measure lines read, one changed and written back with the other lines untouched, a line of another shape kept and
   read as no measure, no value in the file.
