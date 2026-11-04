# 133. A hypothesis: its two conditions, its test, its file

Decisions §235 (1–9), with §237.4 (a hypothesis is short until *More*). The owner, 3 November, after writing H4 in
Orkboard's own `docs/hypotheses.md`: the hypotheses Orkboard is run by say **when they hold and each way they are
refuted**, are tested by **measures over weeks** and say **what changes if they hold**; Orkboard's own hypothesis (spec 116)
has one signal, a goal for a test, no date and no draft. **Builds:** A, C and D on the host first (the spec's author
reviewing and merging), B's code with them, then B's leaders' call and every face on the cheaper model · **Review:** the
critical tests and each part's own · P1. After spec 116 (the record this spec widens) and spec 132 D (`findings.add`, where
D hands a refuted hypothesis). No new pane, column, drawer or dialog (§104.0, §145); no list and no count of hypotheses
(CLAUDE.md's frame). The host returns keys and data, never the words of §8.

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Conditions and the draft** | *Holds when* and one to three ways *Refuted when*, what changes if it holds or is refuted this way, in the record, the proposal, the tree's text, the row and the commands | `realm/hypotheses.py` (the item, `add`, `edit`, `judge`, `draft`, `parse`, `_sentence`), `core/idea_hypotheses.py` (the proposal's prompt), `realm/board_rows.py`, `gui/ideas_hypotheses.py`, `realm/lexicon.py`; `tests/test_hypotheses.py`, `tests/test_idea_hypotheses.py`, `tests/test_gui_hypotheses.py`, `tests/test_board_rows.py`, `tests/test_opportunity_tree.py`, `tests/test_lexicon.py` |
| **B. Measures and the date** | a test that is a measure with its bars and its date; *Did it hold?* due at the later of the goals and the date; the values read by a leader or typed; the card's values against the bars | new `realm/hypothesis_measures.py` (the measure, the date, `met`), `realm/hypotheses.py` (`due`, `value`), new `core/idea_hypothesis_values.py` (a keeper mixin: the leader's reading), `realm/idea_target.py` and `realm/idea_spend.py` (step `measure_read`), `realm/event_log.py`, `gui/ideas_hypotheses.py` (`hypothesis_value`), `realm/board_rows.py`; new `tests/test_hypothesis_measures.py`, new `tests/test_idea_hypothesis_values.py` |
| **C. The file** | the project's own hypotheses file is the source: read in, written out, committed with the Board's pages | new `realm/hypotheses_file.py` (the Markdown: `find`, `parse`, `apply`, `render`), `realm/hypotheses.py` (the read overlaid by the file, the write through it, `bind`), `gui/ideas_hypotheses.py` (the writer given to the record); new `tests/test_hypotheses_file.py`, `tests/test_hypotheses.py` |
| **D. Refuted as a finding** | a refuted verdict is a finding the Product leader tells and the Orkmaster sorts; the goals that rested on it named in it | `realm/findings_gather.py` (`hypothesis`), `core/idea_findings.py` (the told prompt), `core/idea_hypotheses.py` (`assumed_text(only=)`), `gui/ideas_hypotheses.py` (`hypothesis_judge`), `realm/findings.py` (the goals' record); `tests/test_findings.py`, `tests/test_idea_findings.py`, `tests/test_gui_hypotheses.py` |

A first; C stands alone (it needs only A's fields to carry); D needs A's `judge(way=)` and spec 132 D. B needs A and is
the one part whose values are a call. Parts that share `realm/hypotheses.py` (A, B, C) are built one after another, not
side by side; D shares only `gui/ideas_hypotheses.py`.

## 0. What is there today

- **The record** (`realm/hypotheses.py`, spec 116 §2): an item is `{id, text, signal, axis, on, rests, tests, by, party,
  state, evidence, verdict, at}`; `signal` is the one line *We'll know when*; `tests` are goals' slugs; `state` is
  `proposed` · `open` · `held` · `refuted` (`testing` is read from the goals' places); seven open at most, twelve proposed,
  forty in all; `due(state_dir, places)` is the open items with a test, every test done; `judge(state_dir, id, state, why,
  decision)` ends or keeps one. `parse` takes a leader's `{"hypotheses": [{text, signal, axis?, on?, rests?}]}`.
- **The proposal** (`core/idea_hypotheses.py`, spec 116 §3): Product's leader, one call, up to three items `by: "leader"`,
  `proposed`; the person keeps or drops them.
- **The row** (`realm/board_rows.py` `hypothesis`): *Did it hold?* for each due item: `{kind, id, text, signal, evidence,
  tests, party, leader, blocks, priority, at}`.
- **The commands** (`gui/ideas_hypotheses.py`): `ideas.hypothesis_set {id?, text, signal, axis?, on?}`, `_keep`, `_drop`,
  `_attach`, `_evidence`, `_judge {id, state, why?}` (a decision written by `keeper.write_decision`: title `Hypothesis
  held: <text>`, body *Signal*, *Evidence*, *Tests*, *Why*; `keeper.slices_cut` after it), `ideas.hypotheses`,
  `ideas.hypotheses_propose`.
- **The tree's text** (`realm/opportunity_tree.py` `text`) and **the call's text** (`hypotheses.text`) say a hypothesis as
  `Hypothesis (open): <text> — we'll know when <signal>` (`hypotheses._sentence`, cut by `CAPS` to 800 characters).
- **No file**: `docs/hypotheses.md` is read by people only. Its sections (`## H<n>. <title>`, `**Status:**`, *The belief*,
  *What would prove it, what would refute it*, *How we test it*, *If it holds*) are Orkboard's own hypotheses H1–H4; none of
  them can be kept in the record as it is.
- **Findings** (spec 132 D, `realm/findings.py`): `findings.add(state_dir, {source, idea, party, on, found})`; `source`
  `hypothesis` is in `SOURCES` and nothing calls it yet. A finding of no goal (`idea: ""`) is ripe at once; the keeper tells
  it by its party's leader (step `finding`) and sorts it by the Orkmaster (`finding_level`) (`core/idea_findings.py`
  `findings_begin("")`), and `findings.rows` lays it as a `finding` row once sorted.
- **`measures`** (`realm/measures.py`, `TERMS` key `measure`) are how the arguing turned out, read from the event log: **not
  this spec's measure**. This spec's is `realm/hypothesis_measures.py`, its word the key `test_measure` (§8).

## A. Conditions and the draft (§235.1, §235.4, §237.4)

### A.1 The item

Each item gains, read as empty where an item kept before has none (an item kept before **reads its `signal` as its *Holds
when*** and has no refuted way until one is written: `signal` keeps its key, the face says *Holds when*):

- `refuted`: a list of **one to three ways**, `[{name, when, change}]`: `name` what the way would teach (*the hook*, *the
  noise*), one line, `NAME_CHARS = 40`, unique in the item where it is not empty (a way read from a file with no name has
  `""`); `when` one line, `TEXT_CHARS = 200`, required; `change` what changes if it is refuted this way, `DRAFT_CHARS =
  600`, optional. `MAX_WAYS = 3`. An item may have none (the short form).
- `if_holds`: what changes if it holds, `DRAFT_CHARS`, "" when not said.

`verdict` gains `way`: the name of the refuted way the person picked ("" for a way with no name, for *held* and for an
item with no ways). B adds `values`, `look_on` and `measures`; C and D add nothing to the item.

```
hypotheses.add(state_dir, text, signal, *, axis="", on="", rests=(), by="person", party="", refuted=(), if_holds="") -> item
hypotheses.edit(state_dir, id, **fields)       # FIELDS gains refuted, if_holds
hypotheses.judge(state_dir, id, state, why="", decision=0, way="") -> item
hypotheses.draft(item, state, way="") -> str   # the draft of the decision: if_holds for "held"; for "refuted" the named way's `change` (the only way's when the item has one and `way` is ""); "" with none
hypotheses.parse(answer)                       # each item {text, signal, axis, on, rests, refuted, if_holds}
```

- **Adding asks only text and signal** (§237.4): `add` with no `refuted` and no `if_holds` is as it was; *More* is the face's.
- `refuted` is checked by `_ways(value)`: a list of dicts (or `()`), `{name, when, change}` each; a way with no `when` is a
  ValueError in plain words (*A way it is refuted says when*), more than three another (*A hypothesis is refuted in three
  ways at most*), a name twice another (*Two ways it is refuted have the same name*); words are cut as `_words` cuts them.
  `if_holds` is `_words(value, DRAFT_CHARS)`.
- `judge(..., "refuted", way=w)`: `w` must be the name of one of the item's ways when it has any (ValueError *Pick the way it
  is refuted*, with the ways named, for one that is none; `""` is taken for an item with one way, the way's name for it);
  an item with no ways takes `""` only. `way` with any other state is a ValueError (*Only a refuted hypothesis has a way it
  is refuted*). A way is kept in `verdict.way`.
- `parse` (a leader's proposal, §235.1: *a leader's proposal answers both*): `refuted` is read as `[{name, when}]` (`change`
  not asked), each cleaned as `_ways` does but **dropping** a bad one rather than refusing; `if_holds` a line; an answer with
  neither is as before. The proposal's prompt (`hypotheses_prompt`) asks for both: *`signal`: what we would see that shows it
  (Holds when …). `refuted`: one to three ways it would be refuted, each `name` what it would teach (the hook, the noise) and
  `when` what we would see. `if_holds`: what would change if it holds, one or two sentences*; and shows the answer's shape
  with them. A proposal is kept with them, shown short (§237.4).

### A.2 The lines

`hypotheses._sentence(item, state, cap)` ends with `— refuted when <when>` for the item's ways, each cut to `cap`, joined
with ` / ` and a name given as `<name>: <when>`: `Hypothesis (open): <text> — we'll know when <signal> — refuted when the
hook: <when> / the noise: <when>`. **An item with no way has the line it had** (the tree's bytes and the leaders' calls stay
the same for every record kept before). `CAPS` still tries each length in turn until the lines fit `LIMIT`, then drops the
last lines. `opportunity_tree.text` reads `_sentence`; it changes only through it.

### A.3 The row and the commands

- `board_rows.hypothesis` rows gain `refuted` (the item's ways), `if_holds` and `draft`: `{held: <if_holds>, refuted:
  {<name>: <the way's change>}}` (the card shows the draft; a face that does not draw the kind still has `text`).
- `ideas.hypothesis_set {id?, text, signal, axis?, on?, refuted?, if_holds?}`: `refuted` a list of `{name, when, change?}`
  (anything else is *refuted is not a list of ways*, `IdeasError`), `if_holds` a line; each only when given (as `axis` is).
- `ideas.hypothesis_judge {id, state, why?, way?, draft?}`: `way` as A.1. **The draft is the decision**: for `held` and
  `refuted` the decision's body is `draft` (the person's own words, at most `TEXT_CHARS = 6000`, *Change it in words*,
  *Edit*: §234.5 already settled that the face's one *Change…* sends them here) when given, else
  `hypotheses.draft(item, state, way)`, and then, as today's body has them, the *Signal*, *Evidence*, *Tests* and *Why*; for
  a refuted item with a way a first line `Refuted: <name> — <when>` before them. **With no draft at all the body is today's**
  (code words it; the Orkmaster's `decide` call for it, §235.4's last clause, is left to a later spec and is not built
  here). The title is as today (`Hypothesis held: <text>`, `Hypothesis refuted: <text>`). It is written in the same press as
  the verdict (`write_decision`, then `judge`), as today. The answer gains `way`.
- `ideas.hypotheses` data carries the new fields with each item (it already carries the item whole).

### A.4 Tests

`tests/test_hypotheses.py`: an item kept before reads with `refuted: []`, `if_holds: ""` and its `signal`; `add` with ways
(three; a fourth, a way with no `when`, a repeated name refused in words); `edit` of each new field; `judge` with a way, with
a wrong way, with a way and *held*; `draft` for each case; `parse` with and without the new keys, a bad way dropped;
`_sentence` unchanged without ways and with them; `text` still within `LIMIT` and byte-stable.
`tests/test_idea_hypotheses.py`: the prompt asks for both and the proposal is kept with them. `tests/test_gui_hypotheses.py`:
`hypothesis_set` with ways; `hypothesis_judge` writes the draft as the decision's body, the person's own draft over the
saved one, and today's body with none. `tests/test_board_rows.py`: the row's new keys. `tests/test_opportunity_tree.py`: the
line with a way.

## B. Measures and the date (§235.2, §235.3)

### B.1 The measure (`realm/hypothesis_measures.py`, no model, no face)

A test is a goal, a measure or both. An item gains `measures` (four at most, `MAX_MEASURES = 4`), `look_on` ("" or a day)
and `started` (the day it was first open, `YYYY-MM-DD`). A measure:

```
{"id": "m1", "what": "the cost of an install, the Camp clip", "from": "the ads' platforms", "by": "marketing" | "",
 "bars": {"holds": {"op": "<=", "n": 70, "unit": "% of the Work clip's"}, "refuted": [{"way": "the look", "op": ">", "n": 100, "unit": "%"}]},
 "span_days": 28, "date": "2026-12-01", "value": null | {"n": 64.0, "by": "marketing" | "person", "at": "…", "from": "…"}}
```

- `what`, `from`: one line, 120 characters. `by`: the slug of the party whose map holds the source (§235.2: Run's or LiveOps'
  at the stage *live*, spec 115; Marketing's store page, §214), `""` for the person. `bars`: the threshold **in each
  condition** it bears on: `holds` and a bar per way (`way` the way's name, `""` for a way with no name); `op` one of `>=`
  `>` `<=` `<` `=`, `n` a number, `unit` ≤ 24 characters; a condition with no bar is not judged by this measure.
- **The date** (§235.2): `span_days` (*four weeks* = 28) from the test's start: `started`; `date` is `started + span_days`,
  kept as the day (`hypothesis_measures.date_of(started, span_days)`); the person may set the day (`date`) and `span_days`
  follows. A measure added later starts that day. `started` is set by the first `keep` (or a person's `add`) and moves for
  nothing.
- `value` is None until read (B.3). **No measure is shown counting before its date** (§235.2: no number in the window,
  CLAUDE.md's frame): the host strips every `value` of an item from `ideas.hypotheses` while its measure's `date` is in the
  future; the value is kept all the same.
- `hypothesis_measures.clean(raw)` → the list (a measure with no `what`, no bar, an `op` or a `n` that is none dropped; more
  than four ValueError, as `_ways`); `date_of(started, span_days)`; `reached(m, today)`; `met(item)` →
  `{"holds": True | False | None, "refuted": [<names of the ways met>]}`: a condition is **met** when at least one measure
  has a bar for it, every such measure has a value, and every such value meets its bar (`n op bar`); `None` for *holds* when
  no value has come. Code marks the condition; the person judges.

### B.2 Due (`hypotheses.due(state_dir, places, today="")`)

`today` is `YYYY-MM-DD` (the clock's, when ""). An item is due when it is open, has a test (a goal or a measure), **every test
goal is done and every measure's date is reached** (the later of the two when it has both), and its `look_on` is not in the
future. An item with no test is never due, as today. *Not sure yet* (`judge(..., "unsure", date="YYYY-MM-DD")`) sets
`look_on` to the day given (the why kept as evidence, as today; a day in the past or not a day is a ValueError, *Pick a day
to look again*); with none given nothing is set. `hypotheses.value(state_dir, id, mid, n, by, source="")` keeps a value
(`by` the party's slug or `person`; ValueError for a measure gone or a number that is none); `hypotheses.measure_set(state_dir,
id, **measure)` and `measure_drop(state_dir, id, mid)` keep the measures (`MAX_MEASURES`; a measure of a hypothesis judged is
not changed).

### B.3 The values: a leader, else the person (the call: the cheaper model builds it)

At the date, `keeper.measures_read(id)` (`core/idea_hypothesis_values.py`, step `measure_read`, the cheaper tier, tools,
`READS["measure_read"] = 4`, the party's own step `goal:<party>`, `CONTEXT["measure_read"] = 9000`) asks **the leader whose
map holds the source** (the measure's `by`), one call for all of an item's measures of that party, given each measure's
`what` and `from`, its span (`started` to `date`), the party's map and its live product at the stage *live* (spec 115): it
answers `{"values": [{"id", "n", "from"}]}` (a number and where it read it), each taken strictly; what it leaves out is asked
of the person. **Else** (`by` ""; no such party; the call failed; no value for it) **from the person**: the hand's card asks
a number for each measure (`ideas.hypothesis_value {id, measure, n, from?}`: *the one answer here that is typed*). When
it is begun: on the clock's tick, once for an item that is open, whose goals are all done (or has none) and whose date is
reached and has a measure with a `by` and no value; never by a press; a call that cannot be made (no model, a spent window)
leaves the person to type. Events `measure_read` (`idea`, `party`, `measures`, `read`, `seconds`, `cost`) — never a number.

### B.4 The row

`board_rows.hypothesis` rows gain `measures` — each `{id, what, from, value, unit, bars}` with the bars as B.1 says — and
`met`: B.1's. The face marks the condition code met (*Holds: +24%, the bar 20%*; *Refuted, the noise: 1 in 4 turned it
off*) and shows the values in one line each; the draft under *More* (§237.4). A value not yet read is asked on the card.
*Not sure yet* asks a day (*look again on <date>*).

### B.5 Tests

`tests/test_hypothesis_measures.py`: `clean`; `date_of` (28 days from a day; a month's end); `met` with one measure, two
(one missing: `None`), a way met and *holds* not; the date not shown before it. `tests/test_hypotheses.py`: `due` with a goal
and a measure (the later of the two), a measure only (the date), a goal only (as before); `look_on`; `value`.
`tests/test_idea_hypothesis_values.py` (fakes): the call asked at the date and not before, the party's values kept, a value
left out asked of the person, a failed call asks the person; `tests/test_gui_hypotheses.py`: `hypothesis_value`, the values
stripped before the date.

## C. The file (§235.6, §235.7)

### C.1 Where, and which one

`hypotheses_file.find(root, chosen="")` → the path from the root, or None: the person's chosen path (`<state_dir>/project.json`
`hypotheses`, set as `decisions` is, and read by the host: `gui/ideas_hypotheses.py` `_hyp_chosen`) when it lies inside the root
and is a file; else `docs/hypotheses.md` when it is a file; else None. Never outside the root, never a link. A project with
no file keeps its hypotheses in `hypotheses.json` **as today**; nothing in this part changes it.

**Bound** (`hypotheses.bind(state_dir, base, rel)`): the host tells the record where the file is read (`base`: the Board's tree
`<state_dir>/board` when its `.git` is there, as dev holds the project's files, else the project's folder: `_decisions`' rule)
and its path from the root `rel`; the record keeps `file` (the path) in `hypotheses.json` and the base in memory. A project that
had hypotheses in the record before it had a file **adopts** them when it is bound the first time: each item not `proposed`
and not in the file is appended to it as a section (C.3), its id becomes `h<n>` (its goals' `rests`/`tests` come with it) and the
change is one commit. A file that is gone reads as no file: the record's own copy is read.

### C.2 The format (`realm/hypotheses_file.py`, no git, no model, no face)

Markdown of `docs/hypotheses.md`'s shape; a line it does not know is kept as written.

```
## H<n>. <title>                                   → id `h<n>` (lower case); text = the title, cut to 200 at a word (the heading is the belief in one line)
**Status:** <word>[; <note>]. **Raised:** <…>      → state: open · testing (read as open: `testing` is the goals') · held · refuted; anything else open
### The belief                                     → never read, never written
### What would prove it, what would refute it
- **Holds** when <line>   |  - **Proves:** <line>  → signal = the first such bullet (its continuation lines joined), cut to 200
- **Refuted, <name>**: <line>  |  - **Refuted** when <line>  |  - **Refutes:** <line>   → one way each, `name` "" without one; three at most (the rest are left in the file, not read)
### How we test it
- Measure: <what> — from <source>[ (by <party>)] — holds <op> <n>[ <unit>][, refuted <way> <op> <n>[ <unit>]] — <N> weeks | <N> days | until <YYYY-MM-DD>
                                                   → a measure of B.1 (only a line of exactly this shape names one; the other lines are kept and read by no one)
### If it holds                                    → if_holds = its first paragraph, cut to 600
### If it is refuted, <name>                       → that way's change
### Evidence                                       → `- <text> (<ref>) — <day>`, the newest twelve
### Verdict                                        → `<state>: <why> (decision §<n>, <way>)` one line
```

- `parse(text)` → `{"items": [file item], "skipped": [n]}`; a file item has the record's fields for what the file holds
  (`id, text, signal, refuted, if_holds, measures, state, evidence, verdict`); **a section with no *Holds when* is skipped**
  (its number in `skipped`) rather than made up.
- **`apply(old, items)` → the new text** changes only the parts of a section whose parsed value differs from the item's, so
  a section nobody changed is returned **byte for byte**: the title for `text`; the Status line's word (and, for a verdict,
  its note: `became decision §<n>` for held, the why for refuted) with `**Raised:**` and the rest kept; the first *Holds*
  bullet for `signal` (a *Holds* bullet is added when none); every *Refuted* bullet together for `refuted` (and each *If it is
  refuted* section for a `change`); the *If it holds* section's body for `if_holds`; the *Measure:* lines for `measures`; the
  *Evidence* and *Verdict* sections. An item of the record with no section is **appended** (`render`: the heading `## H<n+1>.
  <title>`, `<n+1>` after the highest in the file; its Status line `**Status:** open. **Raised:** <day>.`; the rest as above,
  only what it has). A section the items no longer have (a `drop`) is removed. `proposed` items are never in the file.
- Something the format cannot hold is cut as the record cuts it; nothing is invented.

### C.3 Read and written through (`realm/hypotheses.py`)

- **`read`** with a bound file: the items are the file's (in its order: `parse`), each **overlaid on the record's copy** of the
  same id for what the file has no place for (`axis`, `on`, `rests`, `tests`, `by`, `party`, `at`; an item with no copy has a
  person's defaults), then the record's `proposed` items. The file's words, state, evidence and verdict win. A record item
  the file does not have (and not `proposed`) is not an item: the file is the source. The record keeps its whole copy as
  it did (`hypotheses.json` follows the file; what it keeps for itself is what the file cannot hold).
- **The bound** (§235.7): of the file's `open` items the **seven with the highest `h<n>`** (the newest) stay `open`; any other
  reads as state **`waiting`** (never dropped, never kept, never due, not counted among the seven; `judge`, `keep` and `attach`
  refuse it, *Seven are open or being tested: it waits*); when one is judged the next newest opens by itself. `state_of`
  says `waiting`. The record's other bounds hold.
- **Written through**: every change of an item that is not `proposed` — `add` (a person's), `keep`, `edit`, `evidence`,
  `judge`, `drop` — computes the file's new text (`apply(old, items)`) **inside the repository's lock** and commits it
  with the Board's pages: the host gives the record its writer (`hypotheses.set_writer(state_dir, put)`, `put(rel, edit,
  message)` the Board's `BoardTree.edit_file`), commit `board: hypothesis <id> — <what>`; with no writer (the demo, a folder
  with no history) the file is written in the working copy only, as `write_decision` does. A write that fails is a ValueError
  in plain words (*The hypotheses file could not be written: …*) and **nothing is changed**: the file first, the record
  after. `attach` and a `proposed` item's changes touch the record only. The commit is the Board's, one file besides its
  pages; nothing outside the repository is ever written.
- **`ideas.hypotheses`** data gains `file`: the path ("" with none); each command is as before.

### C.4 Tests

`tests/test_hypotheses_file.py`: `find` (chosen, default, outside the root, a link, none); `parse` of **this repository's own
`docs/hypotheses.md`** (H1–H4: ids, titles as text, H3's two refuted ways with their names, H2's, H1's `Proves`/`Refutes`
bullets, states open/testing, `If it holds` first paragraphs, the length cuts); a section with no *Holds* skipped;
`apply` of the unchanged items returns the text byte for byte (on the repository's file too); a changed state, signal, way,
`if_holds` and evidence each change only their own lines; a new item appended as `H5`; a drop removes its section; a measure
line parsed and written in the same shape. `tests/test_hypotheses.py`: with a file the items are the file's, overlaid with
the record's goals; a judged item's Status line and Verdict are written and `read` gives them back; **eight opens: the newest
seven open, the eldest `waiting`**, and one judged opens it; a failed write changes neither; a project with no file is as
before (the older tests pass unchanged); a `proposed` item is never in the file; adopting the record's items on the first bind.
`tests/test_gui_hypotheses.py` (a project with a git history, the Board's tree): a person's `hypothesis_set` writes the file
and commits it with the Board's pages in one commit (`git log` names the file), a verdict too.

## D. Refuted as a finding (§235.5)

- **`findings_gather.hypothesis(state_dir, item, party, rests)`** (no model, a `try` that never fails what it records, as the
  other sources): for a hypothesis judged `refuted`, `findings.add(state_dir, {"source": "hypothesis", "idea": "", "party":
  <Product's party>, "on": <the item's id>, "found": …})`; `found` (≤ `FOUND_CHARS = 400`, cut from its end): `Refuted: <text>
  (<the way's name: when>). Believed: <signal>. Measured: <each value against its bar, B.4, else the evidence's lines>.
  Goals that rested on it: <slug (title)>, …` — **the goals that rest on it (`rests`) are named in it**, so a decision they
  stood on reaches them by §233's cascade (a finding at the level *decision* is a proposal into the cascade: spec 132 D.3).
  One finding a hypothesis (`source` + `on` + `idea` make its id).
- **When**: `hypothesis_judge` calls it after the verdict is kept, for `refuted` only (a *held* hypothesis's decision is cut
  into slices as any decision is: `slices_cut`, as today), then begins the run (`keeper.findings_begin("")`, which never
  raises). Each goal that tested it gets the outcome in its quality record (`findings.save_record(state_dir, goal,
  hypothesis={id, text, state, way, why, at})`, spec 132 D.4's *the hypothesis's outcome when it tested one*), a goal gone
  left out. The answer gains `finding` (its id) and the verdict keeps it (`verdict.finding`).
- **Told by Product's leader**: `findings_told_prompt` for a row whose `source` is `hypothesis` says *A hypothesis the project
  believed was refuted* in place of *A goal is done…*, and gives, beside what was found, **what was believed** (the item:
  text, *Holds when*, the way, the draft), **what was measured** (the values and the bars, the evidence) and **what the goals
  resting on it assumed** (`keeper.assumed_text(only=<their slugs>)`: the *Defaults* of those goals' sections, the same
  reading the proposal has); the leader answers `what`, `shows`, `promised`, `cause` as for any finding (the cause of a
  refuted hypothesis is in the decision it stood on, or in the code, or in the spec). The party is **Product's leader's**
  (`keeper.tree_party()`), none when the project has no Product party (code's words stand and the Orkmaster sorts).
- **Sorted by the Orkmaster**, as any finding; **one card** (§237.4): the finding is the verdict card's next face (the
  *Fix it there*, *Not now*, *Another level…* of spec 132 D.3), never a second card beside the hypothesis's: a judged
  hypothesis has no row of its own (`due` leaves it), so the finding's row (`kind: "finding"`) is the only one.
- **Held**: the decision is cut into slices (§233.1) as any other: nothing more is done here.
- **Tests**: `tests/test_findings.py` (`findings_gather.hypothesis` adds one finding of no goal, once; `found` names the goals
  and the way; cut to 400; a second call changes nothing); `tests/test_idea_findings.py` (fakes: the told prompt carries the
  hypothesis, the values and the resting goals' defaults and goes to Product's leader; no Product party keeps code's words);
  `tests/test_gui_hypotheses.py` (a refuted verdict returns the finding's id and the goals' quality record holds the outcome; a
  held verdict adds no finding; a failing gatherer never fails the verdict).

## 8. The words (`realm/lexicon.py` `TERMS`)

New keys (checked free; none renamed): `refuted_way` (*way it is refuted*, *ways it is refuted*), `test_measure` (*measure*, *measures*: **`measure` is the table's already**, `realm/measures.py`, which Orkline
reads, so a hypothesis's measure takes this key). The face's lines (not in this spec's host parts): *Holds when*, *Refuted
when*, *If it holds*, *If it is refuted*, *Read on <date>*, *The bar*, *Not sure yet: look again on <date>*, *More*; the
verdicts *Held*, *Refuted* with its way picked, *Not sure yet*. The host returns keys and data, never these words.

## 9. Not here

The faces (the card's *More*, the conditions' fields, the measures' list, the values typed, the verdict card turning into the
finding's); the Orkmaster's `decide` call wording a decision from a hypothesis with no draft (§235.4's last clause; today
code words the body); a measure read from an analytics service (§235.2 reads it from a leader's map, else asks); the
*measure* finding source (§202: a measure missed); Talk's `assumes` carrying conditions (a proposal does; Talk's is as spec 116
§3.2 made it).

## 10. Tests

Each part's above; the critical tests (`tests/test_architecture.py`: `realm/hypotheses_file.py` and
`realm/hypothesis_measures.py` import no `gui/`), `tests/test_board_alone.py`, `tests/test_updates.py`, `tests/test_lexicon.py`,
`tests/test_gui_wording.py`, and every touched module's.
