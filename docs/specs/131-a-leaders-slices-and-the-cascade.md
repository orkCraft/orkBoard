# 131. A leader's slices of the decisions, and the cascade a leader's proposal runs

Decisions §233 (1–12), with §237.5–6 (no list of slices; a cascade folds when all agree). The owner, 3 November: *a decision
costs the least: it is quick and cheap to change or to sync with the others; a spec is harder.* **Builds:** the cheaper
model, A then B, the spec's author reviewing and merging; C on the evening's tools · **Review:** the critical tests and each
part's own · P1. After spec 125 (the journals: the digest this spec's fold copies) and spec 127 (`Changes:`). No new pane,
column, drawer or dialog (§104.0, §145).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. Slices** (host only, no face) | the store, the cut at Confirm, the *was* line, the fold, the reading into every leader's call and into the decision's call | new `realm/slices.py`, new `core/idea_slices.py` (a keeper mixin), `core/idea_keeper.py` (its bases), `core/idea_decide.py` (`_enter`: the trigger; `decision_prompt`: the reading), the readers below, `realm/idea_target.py` (steps `slice`, `slice_digest`), `realm/idea_spend.py` (`STEP_STAGE`), `realm/event_log.py`, `realm/lexicon.py`; new `tests/test_slices.py`, new `tests/test_idea_slices.py` |
| **B. The proposal and the cascade** (host only) | the proposal in a leader's answer, the slices that rest on it found by code, the steps, the bounds, the decision worded, the row the hand shows, Confirm and Put it back | new `realm/cascades.py`, new `core/idea_cascade.py` (a keeper mixin), the writers of the proposal below, new `gui/ideas_cascade.py` (the host's commands), `realm/idea_target.py` (step `cascade`), `realm/event_log.py`, `realm/lexicon.py`; new `tests/test_cascades.py`, new `tests/test_idea_cascade.py` |
| **C. Faces** | the cascade's card in the hand; the leader's bubble answering from its slices; a slice's link opening its decision | `gui/static/js/hand/*` (the decision card of §206.5), `gui/static/pwa/*` (the phone's hand); `tests/test_gui_wording.py` and the hand's browser test |

A is merged on its own and is useful alone: every leader is given its part of each new decision from the day it is merged.
B needs A's store; C needs B's rows. Neither B nor C changes `realm/slices.py`: a change it needs is said to the spec's author.

## 0. What is there today

- A leader's call gets the decisions file's **last ten headings** (`decisions_log.context`) and, in a goal's own sections,
  that goal's entry (spec 99 §6.1, §7.2). An earlier decision the call never sees is missed; a conflict with one shows as
  a fork after the sections are paid for, or not at all.
- The brief (`realm/project_facts.py` `for_call`) and the journals (`core/idea_journal.py` `parts`, spec 125 §C) are read
  into the leaders' calls at the sites listed in A.4. Nothing a leader holds of the decisions is kept per leader.
- A leader that finds a decision wrong for its craft can only say so in its words; nothing follows it.
- The decision card *Make it a change* (§206.5, spec 128 E: `core/idea_leader_change.py`, `realm/leader_change.py`,
  `gui/ideas_change.py`) is the person's own words to one leader; B's card is its shape, proposed by a leader.

## A. Slices

### A.1 The store (`realm/slices.py`, no model, no face)

`<state_dir>/slices.json`, written whole under a lock (as `journals`), one file for the project:

```json
{"v": 1, "from": 233, "cut": {"233": ["tech", "art"], "234": []},
 "slices": [{"id": "s-…", "party": "tech", "decision": 233, "points": ["233.3"], "says": "…", "was": "", "at": "2026-11-04T12:00:00",
             "replaced_by": "", "folded": false}],
 "digests": {"tech": {"text": "…", "upto": "s-…", "at": "…"}}}
```

- `from`: the first decision cut (§233.4: only the new); set by the first cut and never moved. The decisions before it
  are never cut.
- `cut`: each decision cut, with the parties it gave a slice to; **a party it touches not is not there, and that is kept**
  (*none* is an answer, §233.1). A decision in `cut` is never cut twice.
- A slice: `points` the decision's points it rests on, each `"N.k"` (decision N, its point k) or `"N"` (the decision as a
  whole); `says` one or two lines, at most `SAYS_CHARS = 300`, in the second person (*Your screens hold 6 seconds.*);
  `was` the slice it replaced, one line with its link (*was 10 seconds (§159.1)*), "" when none; `replaced_by` the id of
  the slice that replaced it ("" while it stands); `folded` true once the fold read it.
- **A slice is never edited** (§233.2): a replacement adds a new slice and sets the old one's `replaced_by`. The new
  slice's `was` is the old one's `says` with its first link, cut to `WAS_CHARS = 160`; **a `was` goes at the next
  replacement** (the newer slice says only what it replaced itself).

Functions (each tolerant of a missing or broken file: an empty store, never an error to the caller but `save`'s):

| | |
|---|---|
| `read(state_dir)` → the store | `from_(state_dir)` → int or None |
| `is_cut(state_dir, n)` → bool | `add_cut(state_dir, n, answers, at="")` → the slices added: `answers` `{party: {"says", "points", "replaces": [ids]} or None}`; a `replaces` id of another party's or a replaced slice is ignored |
| `standing(state_dir, party)` → the party's slices not replaced, newest first | `resting_on(state_dir, points, but="")` → `[slice]`: the standing slices of every party (but `but`) with a point in `points`; `"240"` matches `"240.2"` and back |
| `text(state_dir, party, chars=CALL_CHARS)` → the part a call is given (A.4), "" with none | `past_bound(state_dir, party)` → the standing, unfolded slices that do not fit `CALL_CHARS` beside the digest, oldest first |
| `digest(state_dir, party)` / `save_digest(state_dir, party, text, folded_ids)` | `link(points)` → `§233.3, §233.4` |

`CALL_CHARS = 1000` (§233.3: as the brief is). `text`'s shape, newest first, the digest before the slices that are not in it:

```
What you hold of the project's decisions (newest first; read the decision for the rest):
In short: <the digest>
- Your screens hold 6 seconds (§240.2); was 10 seconds (§159.1)
- …
```

A slice replaced after a fold is said by the next fold to have gone (A.3).

**When the file is missing** (§233.2: the slices are derived) and the project's `<state_dir>/project.json` holds
`slices_from` (written with the first cut, beside the store's `from`): the keeper cuts again the decisions from it on,
oldest first, at most `RECUT_MAX = 12` in one go and one call each, in the background, the first time a leader's call is
made after the keeper starts. Past twelve the rest wait for the next start; each call is a cut as A.2.

### A.2 The cut (`core/idea_slices.py`, step `slice`)

**When**: in `_enter` (`core/idea_decide.py`), once the entry is written and committed, `self.slices_cut(number)` begins
the cut in the background (`self._start("slices", "slicing", …, key="slices")`, one at a time for the project; a cut
waiting for another queues behind it). The goal's sections never wait for it: they are given the goal's own decision as
today. A decision written with no goal (a hypothesis's verdict, spec 116 §4) is cut too: it is a decision. In a demo, with
no model, a spent window or the day's cap, nothing is cut and nothing is kept; the cut is not tried again for it (the
next decision's cut does not read it), and `is_cut` stays false: A.1's recut takes it up when the store is missing only.

**The call** (step `slice`: the Orkmaster's voice, `as_role=orkmaster.ROLE`, the cheaper tier as `decide`'s, **no tools,
READS 0**, `CONTEXT["slice"] = 9000`) is given, in this order, cut from the end by `idea_target.cut`:

1. *The decision* — the entry as written (`decisions_log.entry`), its points numbered as the file has them.
2. *The project's leaders* — every party of the project (`ideas.tracks`), Release too, one line each:
   `<slug> — <its leader's name>, <its craft>: <the first line of its map's text>` (`map_text.of(...)`, its first line; none
   when the party has no map).
3. *What each holds now of what this decision changes* — for each `Changes:` number of the entry (`decision.changes`), the
   standing slices resting on it, `<slice id> <party>: <says> (<link>)`. None when it changes nothing.

It answers one JSON object, every party of the project a key:

```json
{"slices": {"tech": {"says": "…", "points": ["233.3"], "replaces": ["s-…"]}, "art": null}}
```

`clean_cut(raw, parties, n, points_known, standing_ids)`: a party not of the project is dropped; **a party left out is
`null`** (none, kept as none: no leader is left out unseen); `says` one or two lines cut to `SAYS_CHARS`; `points` only
`"n"` or `"n.k"` with k among the entry's points (`"n"` when none is left); `replaces` only ids given in 3. A whole
answer that is no object keeps nothing (a failed cut, below). Kept with `slices.add_cut`.

A cut that fails (the tool fails twice, a stop) keeps nothing, records event `slices_cut` with `failed: true`, and is
never shown to the person: the leaders read the last ten headings as before (§233.4).

**The cost** is the Orkmaster's ledger's, stage *spec* (`STEP_STAGE["slice"] = "spec"`), the goal's when there is one.
Event `slices_cut` (`decision`, `parties`: how many got one, `none`: how many none, `replaced`, `seconds`, `cost`,
`failed`). Never a word of a slice.

### A.3 The fold (step `slice_digest`)

After a cut is kept, `slices_fold_for(parties)` begins, for each party a slice was given to whose `past_bound` is not
empty, one call of **the party's leader** (step `slice_digest`: as the journal's digest, spec 125 §D: the cheaper tier,
no tools, READS 0, the party's own step `goal:<party>`, its cost in the party's ledger, `CONTEXT["slice_digest"] = 8000`),
given its old digest and the slices past the bound (with their links; a slice in the digest that was replaced since,
with *gone: replaced by <the new one's link>*). It answers `{"digest": "…"}`: at most `DIGEST_CHARS = 600`, plain prose in
the second person, **the links kept** (*You keep screens short (§240.2) …*), never a list. Kept with
`slices.save_digest(..., folded_ids)`, which marks those slices `folded`. A fold that fails keeps nothing; the call's
`text` meanwhile shows the newest that fit and ends `(N older not shown)`. Event `slices_folded` (`party`, `slices`,
`chars`, `seconds`, `cost`, `failed`).

### A.4 Read into every leader's call (§233.3)

`idea_slices.parts(state_dir, party)` → `[(heading, text)]`, `[]` with none, never an error: the part is placed **right
after the project's facts** (`project_facts.for_call`) and **before the journals and the map**, in each of these, and each
step's `CONTEXT` grows by `1200` so that nothing that fit before is cut now:

| Step | Where |
|---|---|
| `talk_round`, the diagnosis (`diagnose`) | `core/idea_talk.py` (both `for_call` sites) |
| `talk_verdict` | `core/idea_verdict.py` |
| `section_first`, `section` | `core/idea_sections.py` |
| `plan` (a party's plan, a change asked of a leader) | `core/idea_plan.py`, `core/idea_leader_change.py` |
| `accept` (a leader's look at a task's result) | `core/idea_lead.py` |
| `ask` (the leader's bubble) | `core/idea_ask.py` (a party's tab only; the Orkmaster's tab reads none: it has no slice) |
| `concerns`, `tree`, `hypotheses`, `loop`, `project_q`, the pass (`idea_pass`) | `core/idea_concerns.py`, `core/idea_tree.py`, `core/idea_hypotheses.py`, `core/idea_loop.py`, `core/idea_project_q.py`, `core/idea_pass.py` |

**A member reads none** (its leader's brief carries what it needs): no task's prompt changes.

**The decision's call** (`decision_prompt`, step `decide`) is given, after the journals and before the decisions file, a
part *What the leaders hold that this goal touches*: the standing slices of the route's parties and of the parties whose
map a mark of the goal names (`ideas.state(...)["marks"]`, a mark's `map` read to its craft's parties), each line
`<Leader> (<party>): <says> (<link>)`, at most `DECIDE_CHARS = 2500`, the newest first; and one rule more: *Where the goal
goes against a line under *What the leaders hold*, say so in a point and put that decision's number in `changes`.*
`clean_decision`'s known numbers then include the slices' decisions as well as the last ten headings.

**The last ten headings stay** in every call as today (§233.4): they go when a decision says so.

### A.5 The words, the tests

`TERMS` gains `_t("slice", "slice", "slices")`: *a leader's part of a decision: the key conclusion for its craft and the
points it rests on*. Nothing of A is shown, so no other word.

`tests/test_slices.py`: the store from nothing; `add_cut` keeps none as none and a decision once; a replacement keeps the
old and sets `was` (and the `was` goes at the next); `resting_on` matches `"N"` with `"N.k"` both ways; `text` fits
`CALL_CHARS`, the digest first, `(N older not shown)`; a broken file reads empty. `tests/test_idea_slices.py` (the
keeper's fakes, as `tests/test_idea_journal.py`): Confirm begins one cut; the call is given every party and the standing
slices of the decisions changed; `clean_cut` (a party left out is none, an unknown point and an unknown replace id are
dropped); a failed cut keeps nothing; the fold marks what it read; each reader of A.4 has the part after the facts (one
test a site, by its prompt); a member's prompt has none; the decision's prompt has the touched leaders' slices.

## B. The proposal and the cascade

### B.1 A proposal (§233.5)

The leaders' answers in **`talk_round`, `talk_verdict`, `section_first`, `section`, `plan`, `accept` and `ask`** may carry,
beside what they answer today, one key more, asked by one rule added to each prompt that was given a slices part (A.4):

```json
"propose": {"slice": "s-…", "says": "the slice as it would read", "why": "what the project or the work showed", "points": ["240.2"]}
```

*Only when a line under *What you hold* is wrong for your craft (the project says otherwise, or the work ran into it);
else leave it out.* No call is made to look for one (nothing runs in the background to find them, spec 99 §3).
`cascades.clean_proposal(raw, party, standing)`: `slice` must be a standing slice of the answering party; `says` and `why`
one line each (`SAYS_CHARS`, `WHY_CHARS = 300`); `points` default to the slice's own. Anything else drops the proposal and
never the answer. **A proposal changes nothing by itself.** The keeper keeps it (`cascades.add`) and begins its cascade
(B.2) at once in the background, one cascade at a time for the project (`key="cascade"`); a second proposal while one runs
waits behind it. A slice with a cascade open (not confirmed or put back) is not proposed on again: the proposal is dropped,
event `slice_proposed` with `dropped: "open"`.

### B.2 The cascade (`core/idea_cascade.py`, step `cascade`)

`realm/cascades.py` keeps `<state_dir>/cascades.json` `{"cascades": [record]}`, a record:

```json
{"id": "c-…", "at": "…", "party": "tech", "from_step": "section", "idea": "<the goal's slug or ''>",
 "slice": "s-…", "says": "…", "why": "…", "points": ["240.2"],
 "status": "asking", "steps": [{"n": 1, "party": "art", "slice": "s-…", "answer": "agrees", "says": "…", "why": "…", "cost": 0.03}],
 "forks": [{"party": "design", "slice": "s-…", "why": "…"}], "stopped": "", "changed": ["240.2"],
 "decision": {"title": "…", "text": "…", "changes": [240]}, "sections": [{"idea": "…", "party": "…"}], "cost": 0.11, "error": ""}
```

`status`: `asking` → `ready` (waits in the hand) or `failed`; then `confirmed` or `put_back`.

**The steps, by code and short answers** (§233.6): step 1's frontier is the proposal's `points`. For each point of the
frontier code finds the **other** parties' standing slices resting on it (`slices.resting_on(points, but=<the proposer>)`,
no model); each such slice's leader is asked (step `cascade`: the party's leader, its own step `goal:<party>`, the
cheaper tier, no tools, READS 0, `CONTEXT["cascade"] = 3000`), given its slice and the change (*Tech proposes: <says>,
because <why>; it changes §240.2*), and answers `{"answer": "agrees" | "disagrees", "says": "your slice as it would read",
"why": "…"}`. An agreeing leader's slice, changed, is the next step's frontier (its points); a disagreeing one is **a
fork** for the person (as spec 99 §7.3's). The leaders of one step are asked one after another.

**Its bounds** (§233.7), whichever comes first, said in `stopped`:

1. **Three steps** from the proposer (`STEPS_MAX = 3`): what the fourth would ask is not asked
   (*Stopped after three steps: Marketing was not asked*).
2. **A point changed once in a cascade is not changed again in it** (`changed`): a slice that would change it a second
   time is a fork, not a step.
3. **A price**: before each leader is asked, its call is priced (`idea_target.budget("cascade", target)`); the cascade stops
   where what it spent and the next call's price would pass **2% of the main tool's week** (`CASCADE_SHARE = 0.02`, a
   default, tuned by H1's trial, spec 124 C): with a week read (`idea_target.week`), the share it has used since the
   cascade began, read again after each call; with none (an API key), `CASCADE_USD = 0.50` in all.

**The decision** once the steps end: one call of the Orkmaster (step `decide`, as `decision_prompt`'s rules: a title, *Why*,
points, `changes`) given the proposal, the chain (each slice before and after) and the forks; its `changes` must name the
decisions whose points changed (code adds any it left out). A call that cannot be had: worded by code (*<Leader> proposes:
<says>* as the title, the chain as the points). **What follows** is found by code: the goals not done (not in the discard,
§206.8) whose way's sections were written by a party whose slice changed and whose decision is one of `changes` or reads
one (`spec_sections.record(...)["decision"]["changes"]`), as `sections` `[{idea, party}]`; their price is said with
`idea_target.budget("section", target)` each. Then `status: ready`, event `cascade_ready`.

A cascade that fails (the proposer's party gone, every call failing) is `failed` with its `error` in plain words and is
shown nowhere but the log; nothing changed.

### B.3 The row, Confirm, Put it back (§233.8–9; §237.6)

`cascades.rows(state_dir)` → the Needs-you rows (`kind: "cascade"`) of the cascades `ready`, as `leader_change.rows`' are
shaped, each: `{kind, id, party, title, line, chain: [{party, before, after}], forks, stopped, cost, sections}`.
`line` is **one line when no leader disagreed** (§237.6: *Tech and Art agree*; the chain under **More** on the card),
else the forks first. The hand reads these rows through the host's commands; **nothing changes until Confirm**.

The host's commands (`gui/ideas_cascade.py`, a mixin of `Ideas` as `ideas_change`'s):

- `ideas.cascade_confirm {id, fork_answers?, text?}`: refused while a fork has no answer (*Answer the fork first*); then
  the entry written and committed through `write_decision` (by `"person"`, `changes` the record's), the slices cut as A.2
  does for any decision — **the chain's slices become the cut's answer** (no call: each changed slice replaces its old
  one, `was` set), the other parties `null` — and the goals of `sections` have those sections written again, one call a
  section, a goal at work re-planning what is left (spec 62); `status: confirmed`; event `cascade_confirmed`.
- `ideas.cascade_back {id}`: `status: put_back`; every slice stands; event `cascade_put_back`.
- `ideas.cascades` → the rows (for C).

### B.4 The words, the tests

`TERMS`: `_t("cascade", "cascade", "cascades")` (*what a leader's proposal changes in the other leaders' slices, step by
step, before it is a decision*); the lines B gives the face: *Proposes*, *Agrees*, *Disagrees*, *Stopped after <n>
steps*, *<A> and <B> agree*, *Answer the fork first*.

`tests/test_cascades.py`: `clean_proposal` (another party's slice, a replaced slice, no words: dropped); the store; `rows`
one line when all agree, the forks first when not. `tests/test_idea_cascade.py` (fakes): a proposal in a section's answer
is kept and the section kept unchanged; the steps follow the links (two steps deep); three steps stop (`stopped` says who
was not asked); a point changed twice is a fork; the price stops it (a fake week); the decision's `changes` include the
changed decisions; *What follows* leaves the discard out; Confirm refuses an open fork, writes one entry, replaces the
chain's slices with `was`, asks the sections again; Put it back changes nothing.

## C. Faces (the evening's)

- **The card in the hand**: the decision card of §206.5 (`kind: "cascade"`): the proposing leader's head and *Proposes*;
  the new decision's title; with no fork, one line (*Tech and Art agree*) and **More** opening the chain (the heads in order,
  each slice before and after); with a fork, the fork first, its sides as a fork's card's; *Stopped after <n> steps* when it
  stopped; the cost of what follows (the sections to write again); **Confirm and start** and **Put it back**.
- **No list of slices** (§237.5): the one place of the parties draws none. The leader's bubble (`ask`) answers from them
  (*what do you hold about the timer?*); a slice's link (*§240.2*) in any answer opens its decision, as a *§N* in an
  answer's sources does today.
- The phone's hand shows the same card, as it shows `leader_change`'s.
