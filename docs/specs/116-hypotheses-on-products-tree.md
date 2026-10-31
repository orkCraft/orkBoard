# 116. Hypotheses on Product's tree: proposed by the leaders, tested by goals, judged in the hand

Decisions §194. The owner, 31 October: *do we have a place for hypotheses in the product? I think we need one, maybe on the
analytics' or the product's leader's tab.* Following `docs/hypotheses.md` H1 (the value of Orkboard is how well what the
person wants is found out). **Builds:** Claude (the cheaper model builds, the spec's author reviews) · **Review:** full ·
P1. No mockup (the owner: straight to the build). **Waves** (parts in a wave share no file): **1** A; **2** B, C, D;
**3** E.

**What it is, and is not:** a **hypothesis** is what the project believes and has not shown: one line (*We believe …*),
the signal that would show it (*We'll know when …*), what it rests on. It lives **on Product's map, the opportunity tree**,
between a job and the goals that serve it (Torres' assumptions); Product's leader keeps them, **any leader may propose one**
from its Talk, and Product's leader proposes the riskiest from what the leaders assumed. **A test is an ordinary goal**
(an experiment, a playtest, an interview, an A/B test): through line, hand, table and discard as any goal. When a test is
done, **the hand asks the person *Did it hold?*** with what was found; *Held* and *Refuted* write a decision. Not: a new
tab, column, drawer or count (decisions §104.0, §145); an Analytics party (there is none, and the analyst leads Run only once
a project is live, when hypotheses matter least); numbers of real people read from analytics (a later spec: they become
evidence); the project's brief (a later spec: its riskiest claims will become hypotheses on the outcome).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The record** | hypotheses kept, bounded, their state, their text for the leaders' calls | new `realm/hypotheses.py`; `realm/opportunity_tree.py` (`text`: the hypotheses under their job); new `tests/test_hypotheses.py`, `tests/test_opportunity_tree.py` |
| **B. Proposed by the leaders** | Product's leader proposes from the tree, the facts and the leaders' assumptions (one call, on a press); a leader's Talk may name what it assumes | new `core/idea_hypotheses.py` (a mixin of `IdeaKeeper`, wired in its bases), `core/idea_talk.py`, `realm/idea_talk_parse.py`, `realm/idea_target.py` (the step `hypotheses`); new `tests/test_idea_hypotheses.py`, `tests/test_idea_talk.py` |
| **C. Judged in the hand, and the commands** | the row *Did it hold?* when a test is done; the commands; the verdict written as a decision | `realm/board_rows.py` (the row `hypothesis`), new `gui/ideas_hypotheses.py` (wired in `gui/ideas.py`), `core/idea_decide.py` (a decision written with no goal: `write_decision`); new `tests/test_gui_hypotheses.py`, `tests/test_board_rows.py`, `tests/test_idea_decide.py` |
| **D. Evidence's hint, the leaders' lens** | the hint `untested`; Product's Talk and look read the open hypotheses | `realm/map_signals.py` (product), `realm/lens_rubrics.py` (`untested` in *Evidence*), `realm/idea_objections.py` (`LENS["product"]`); `tests/test_map_signals.py`, `tests/test_lens_rubrics.py` |
| **E. The faces** | hypotheses on the tree, picked as its parts; the hand's card *Did it hold?* | `js/table/treemap.js`, `js/table/tree.css`, new `js/hand/hypothesiscard.js` (registered with `hand/ways.js`), `realm/map_parts.py` (product: the hypotheses as parts); new `tests/test_hypotheses_desktop_browser.py`, `tests/test_map_parts.py` |

## 1. The words

`TERMS`: **hypothesis** / **hypotheses** (in the lead's commit). The interface: *We believe*, *We'll know when*; the states
**Proposed**, **Open**, **Testing**, **Held**, **Refuted**; *Proposed by <Leader>*; **Keep**, **Drop**; **+ Hypothesis**;
**Test it**; **Propose hypotheses**; the hand's card **Did it hold?** with **Held**, **Refuted**, **Not sure yet**, and
*Why* (a line); *Rests on an untested hypothesis* (the hint). The host returns keys and data, never these words.

## 2. Part A: the record (`realm/hypotheses.py`; no model, no face)

```
hypotheses.read(state_dir)                         # {items: [item]}; an item {id, text, signal, axis, on, rests, tests, by, party, state, evidence, verdict, at}
hypotheses.add(state_dir, text, signal, *, axis="", on="", rests=(), by="person", party="") -> item     # ValueError in plain words past the bounds
hypotheses.edit(state_dir, id, **fields) -> item   # text, signal, axis, on, rests; a proposed one kept (`state: "open"`) by `keep(id)`
hypotheses.keep(state_dir, id) / drop(state_dir, id)
hypotheses.attach(state_dir, id, goal="", test="") # a goal that rests on it (`rests`), or a goal that tests it (`tests`); "" with the other detaches
hypotheses.evidence(state_dir, id, text, ref="")   # a line of what was found (a goal's slug, a mark's, or none), at most 12, the newest kept
hypotheses.judge(state_dir, id, state, why="", decision=0) -> item     # held · refuted (with the decision's number) · unsure (back to open or testing)
hypotheses.state_of(item, places)                  # the state as shown: `testing` while a test goal is in line or at work (`places`: {slug: line|work|done})
hypotheses.due(state_dir, places)                  # the items whose every test is done and that are not judged: the hand's rows (C)
hypotheses.text(state_dir, places)                 # for a leader's call: the open and testing ones, a line each, ~800 characters at most; "" with none
hypotheses.parse(answer)                           # a leader's proposal, strictly → [{text, signal, axis, on, rests}] or None
```

`<state_dir>/hypotheses.json` `{items: [...]}`. An item: `id` (its text's slug, unique, kept when its words change), `text`
(≤ 200, *We believe* is the face's, not kept), `signal` (≤ 200), `axis` one of `desirable` · `viable` · `feasible` ·
`usable` · "" (assumption mapping's four), `on` a job's id or an outcome's id of the tree or "", `rests` and `tests` goal
slugs (≤ 12 each; a goal tests one hypothesis at most: it moves), `by` `person` · `leader`, `party` the proposer's party
slug ("" for the person), `state` `proposed` · `open` · `held` · `refuted` (`testing` is never kept: `state_of` reads it),
`evidence` `[{text, ref, at}]`, `verdict` `{state, why, decision, at}` or `{}`. Bounds: **seven open or testing at most**
(a proposal past them is refused, a person's says so), twelve proposed at most, forty in all (the oldest judged go first).
`parse` takes `{"hypotheses": [{text, signal, axis?, on?, rests?}]}`, at most three, dropping what is not of the shape.
`opportunity_tree.text` adds, under each job, its hypotheses (*Hypothesis (open): … — we'll know when …*), and the ones on no
job after the jobs. Tests: bounds, ids, the moves, `state_of`, `due`, `text`'s bytes stable, `parse` strict.

## 3. Part B: proposed by the leaders

1. **`keeper.hypotheses_propose()`** (`core/idea_hypotheses.py`, as `core/idea_tree.py`'s `tree_propose`; step
   `hypotheses`, the cheaper tier, no tools, READS 0; Product's party's own step, its cost in that ledger as *spec*): Product's
   leader is given its voice, the tree's text (with the hypotheses), the common facts (`project_facts.for_call`), the project's
   stage (`project_stage`), and **what the leaders assumed**: the *Defaults* of the sections of the goals in line and at work
   (`spec_sections`, ten at most, newest first). It answers up to three hypotheses, the riskiest first; at the stage `idea`
   with none kept, one an axis that matters (desirable, viable, feasible, usable). Kept `by: "leader"`, `party` Product's,
   `state: "proposed"`. Never asked unasked: the press *Propose hypotheses* (`ideas.hypotheses_propose`). A call that fails
   says why; nothing half-kept.
2. **Talk** (`core/idea_talk.py`, `realm/idea_talk_parse.py`): a round's stance may carry `assumes` (one line, optional, the
   leader's riskiest assumption about this goal). Its prompt asks for it in one sentence (*If this goal rests on something
   no one has shown, say it in `assumes`; else leave it out*). Each `assumes` becomes a proposed hypothesis `by: "leader"`,
   `party` the stance's, `rests` this goal; the same text twice is kept once. Nothing else in Talk changes.
3. Tests: the proposal kept, refused past the bounds, the call's inputs (the Defaults read), a failed call; Talk's
   `assumes` parsed, kept, absent.

## 4. Part C: judged in the hand, and the commands

1. **The row** (`realm/board_rows.py`): `hypothesis` for each `hypotheses.due` item: `{kind: "hypothesis", id, text, signal,
   evidence, tests: [{slug, title}], party, leader, blocks: false, priority: "normal", at, text}` (`text` the question line for
   a face that does not draw the kind). It lies after the others, as `project_q` does; judged, it leaves the hand.
2. **Commands** (`gui/ideas_hypotheses.py`):
   - `ideas.hypotheses {}` → `{items: [item with `state` as shown and `tests`/`rests` with each goal's title, element, place], party, proposing, status}`;
   - `ideas.hypothesis_set {id?, text, signal, axis?, on?}` (the person's: a new one is `open` at once) → `{ok, item}`;
   - `ideas.hypothesis_keep {id}`, `ideas.hypothesis_drop {id}`;
   - `ideas.hypothesis_attach {id, goal?, test?}` (empty `id` with a `goal` or `test` detaches it);
   - `ideas.hypothesis_evidence {id, text, ref?}`;
   - `ideas.hypothesis_judge {id, state: held|refuted|unsure, why?}`: **held** and **refuted** write a decision
     (`keeper.write_decision(title, body)`: the entry's way of `core/idea_decide.py` `_enter`, taken out so a decision can
     be written with no goal: `## <n>. Hypothesis held: <text> (<date>, the person and <host>)`, its body the signal, the
     evidence's lines, the tests' titles and the why), its number kept in the verdict; **unsure** keeps it open with the why
     as evidence;
   - `ideas.hypotheses_propose {}` → `{ok, asked, why?}`.
   Refusals in plain words (a hypothesis gone, past the bounds, no words).
3. Tests: each command; the row when the last test is done and not before; judging writes the decision (numbered after the
   others) and the row leaves; `unsure`.

## 5. Part D: Evidence's hint, the leaders' lens

`map_signals` (product): `untested`: a goal in line or at work that rests on a hypothesis still open with no test (`on` the
goal's id as the tree's parts name it; words *<goal> rests on an untested hypothesis: <text>*). `lens_rubrics` product:
`untested` in *Evidence* (every kind in one aspect, as the tests keep). `idea_objections.LENS["product"]` gains: *and the
open hypotheses: is this goal built on one no one has tested?*, and Product's Talk is given `hypotheses.text`. Tests: the
hint on and off; the rubric; the lens's words.

## 6. Part E: the faces

1. **On the tree** (`treemap.js`, `tree.css`): under a job, before its goals, its hypotheses as small cards (a hypothesis on
   no job in a row of its own under the outcome): *We believe* muted then the text, *We'll know when* muted then the signal,
   its state as an orkUI chip (*Proposed*, *Open*, *Testing*, *Held*, *Refuted*; held in the success colour, refuted in the
   danger colour, proposed dashed), the proposer's small head with *Proposed by <Leader>*; a proposed one has **Keep** and
   **Drop**; an open one **Test it** (the + card's field addressed to Product with the type *Try an experiment* and the
   hypothesis as a mark; its goal, once added, is attached as a test). **+ Hypothesis** at the end of a job's row opens a
   small field (*We believe*, *We'll know when*). With none, **Propose hypotheses**. Each card is `Pickable` (map `product`,
   id `hyp:<id>`, name its text); `map_parts` product lists them (group `hypotheses`).
2. **In the hand** (`hand/hypothesiscard.js`, `way("hypothesis", {sign: "flask", Lifted})`): the card's window the flask, its
   name the hypothesis; lifted: the text, the signal, the evidence as lines (each with its goal's element when it has one),
   the tests' names, **Held**, **Refuted**, **Not sure yet**, a *Why* line; answered, the card leaves.
3. No count anywhere; the aspect *Evidence* on the strip says the rest (spec 109).
4. Tests: the cards on the tree in each state, Keep, Drop, + Hypothesis, Test it, picking a hypothesis; the hand's card and
   its three answers.

## 7. Tests

Each part's above; the critical tests (`tests/test_architecture.py`: `realm/hypotheses.py` imports no `gui/`),
`tests/test_board_alone.py`, `tests/test_updates.py`, and every touched module's.

## As built

Built by the cheaper model, a part a branch, each reviewed and merged by the spec's author.

**A** (`realm/hypotheses.py`, `opportunity_tree.text`). Items keep the file's order (the clock's one-second grain would scramble a sort by `at`). A leader's proposal is refused at seven open or twelve proposed; the fortieth item drops the oldest judged, and with none judged the add is refused. A hypothesis is judged once, and only once kept (*Keep it first*). `due` reads a test goal gone from the Board as not done. `on` is checked for its shape only (a job gone reads as no job). The tree's text cuts the hypotheses' words first, then the goals, then drops the last hypotheses before it cuts a job; with none its bytes are as before.

**B** (`core/idea_hypotheses.py`, Talk). The proposal's status is kept in `hypotheses.json` (`proposal`), read through `keeper.hypotheses_proposal()`; no *once* block (the bounds limit it); with no room left the press is refused before any call. The call is given the stage, the tree's text, the jobs' and outcomes' ids, the common facts and the *Defaults* of the goals not done, newest page first (ten, three lines each); an `on` or a `rests` not given is dropped. Talk's `assumes` is `{text, signal}` (a bare line is taken too, its signal *someone shows it*); a repeated text makes the goal rest on the one kept. `realm/idea_spend.py` counts the step as *spec*.

**C** (`board_rows.hypothesis`, `gui/ideas_hypotheses.py`, `write_decision`). `write_decision(title, body, tree=None)` is `_enter`'s writing taken out; a verdict is committed to dev as a goal's decision is, and nothing is written for a hypothesis gone, not kept or judged already. A person's hypothesis has the Orkmaster as the row's leader. The row is data only (the face words *Did it hold?*); it is left out of the snapshot's count and laid after the others. `ideas.hypothesis_set` refuses an `on` the tree does not have.

**D** (`untested`). Only with the Board's pages; `on` is the goal's id when the product map names it, else "". Product's Talk sees the hypotheses through the tree's text (no other change); proposed ones are not in it.

**E** (the faces). `hand/data.js` lays the `hypothesis` stop under its proposer's lane (the first lane for the person's own); the tree reads `ideas.hypotheses` with its own hook so a proposal's `error` never hides the cards; the outcome's row always stands (with *+ Hypothesis*, and *Propose hypotheses* while none is kept). `ideas.add` attaches a goal carrying a `hyp:<id>` mark: an experiment as the first marked hypothesis's test, any other goal as resting on each; a hypothesis gone or full is skipped and never fails the add.
