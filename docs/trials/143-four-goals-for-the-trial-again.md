# Four goals for the trial again (spec 143, *The trial again*)

After spec 143 A, B and C are in `main`, on the owner's computer, with real tools: a clone of this repository (no remote, an
empty `HOME`, as the first trial), `orkboard drive start <clone> --real-tools` or by hand, a Tech party at Lean. Each goal is
written on the + card as it stands below, one at a time or all four at once. They are left out of the cloud's build on purpose:
each is built here only by the trial.

Why these four: each is code the gate can check (host tests, and a page's change brings its browser tests, spec 143 B), each is
already specified (so Talk and the decision have little to add, and the cost is the work's), and between them they touch the
table, the hand, a potion's card and a new host command: what the first trial broke.

| # | Goal (the + card's words) | Spec | What the trial watches |
|---|---|---|---|
| 1 | **The pane's marks say Decision · Spec · Work · Quality.** The picked goal's title says *Decision · Spec · Work · Quality* in place of *Talk · Spec · Work · Done*; *Decision* opens Talk's page, *Quality* the quality record; a mark is lit, with no number, when the goal's `levels` holds its level. Spec 132 B. | 132 B | the browser tests of `table/pane.js` run at the gate (`[gate] browser`); the marks' tests green on `dev`; no page of the Board edited |
| 2 | **A potion's card names the models of its tiers again.** The models by tier that spec 130 D took out of Settings come back on the potion's lifted card (`hand/toolcard.js`): each tier's model, changed there, kept in the machine's `tier_models` (`settings.py`, read by `realm/harnesses.py` today, set and shown by nothing since spec 130 D); a host command sets it. Spec 130 B.3. | 130 B.3, D | a host command and its test plus a page change and its browser test in one goal; the plan keeps a code task and the tests it breaks together (143 B.4) |
| 3 | **Split a goal in two.** A goal not yet at work can be split: `ideas.split {idea, parts}` makes two goals of one, each with its part of the words and the spec's sections, the first keeping the rune; the goal's page has *Split…*. Spec 135 C. | 135 C | a new host module and a page's act; a task that would edit `pages/ideas/` has it put back by code (143 A.4), never refused |
| 4 | **The field's Rune square shows the hue the host will pick.** While a goal is written on the + card, its Rune square shows the hue the host will give it (`realm/idea_element.py`), not a fixed one; the phone's `nextElement` counts by the project, as the host does. Spec 128 G. | 128 G | a small change on the desktop and the phone; the gate's browser tests for `hand/` and the PWA's; tokens of `work` well under the first trial's |

**Good when** (spec 143): no log says *A task never edits the Board's pages* (`task_pages_put_back` may appear and spends nothing);
every task ends merged or stops on a real red test; the four goals' tests are green on `dev`; the tokens of `work` are well under
the first trial's 2.49 million for four tasks. What it shows goes into a decision, as §250 did.
