# A leader accepts, a task is a whole session: two goals on local Codex, against §253's run

Spec 152 E and spec 153 D's measure, on 6 November 2026, at `452c44c0`. What the runs were held to was written before them
(`152-a-leader-accepts/00-criteria.md`). The numbers and the logs are in `152-a-leader-accepts/`; §8 says what is where.

**In short.** The flow costs 40% less on the same goal and no task was split, re-sent or killed. But the two things it was built to catch
never fired: **every *Done when* line was marked `[test]`, so nothing asked for a look, and the leader accepted yesterday's miss as met.**
And **Orkboard at `main` does not open on this repository at all** (§3, F1).

## 1. The runs

| Run | Project | Goal | Ended |
|---|---|---|---|
| **Base** | clone at `64f3abd4`, Orkboard of 5 November | goal 4 of `143-four-goals-for-the-trial-again.md`, the Rune square (spec 149 §0, §253) | on main |
| **A** | the same commit, only `orkboard init`'s files added, Orkboard frozen at `452c44c0` | the same goal, the same words, *To Tech, New feature* | Done; **sealed before main** (F4) |
| **B** | clone of `452c44c0`, the Board in the code, 121 goals | goal 2, the tiers' models on a potion's card (spec 149 K names it) | on main in the clone |

Both: codex-cli 0.166.0 on the ChatGPT plan, Tech and Release at Lean, a HOME of its own, a PATH with no other AI tool, every press in the page.
A has no solution in its repository, so the flow is what changed; B's goal is larger, so only its steps compare with the base's, not its sum.

**Off the plan:** B needed goal 96's page renamed in the clone before it would open (F1). A's checks into main were stopped at their second run (F4). The owner also clicked around the
page in both runs, watching; no such press moved a goal. **The share of the window is not a measure here:** Codex was in use elsewhere on the same plan (the mana fell from 92% to 84% between 09:49 and
10:01 with no call of A's running). Use the tokens.

## 2. The numbers

| Step | Base | **A** | **B** |
|---|---|---|---|
| Test of the tool | 11,611 | 11,611 | 11,611 |
| Tech's reading, the project's question | 111,311 | 89,052 | 16,043 (no reading: the Board is in the code) |
| Talk (`diagnose` · `talk_round`, `talk_verdict`, `decide`, `slice`) | 84,743 | 42,399 | 83,937 |
| The section | 85,045 | 122,389 | 62,972 |
| The plan | 133,420 | 106,438 | 143,110 |
| **Tasks' sessions** | 5 sessions, 2,221,056 | **1 session, 1,384,853** | **1 session, 589,488** |
| of which sent back or started again | 915,042 | 0 | 0 |
| **The check** (Lean review · acceptance) | **556,105** | **102,333** | **107,905** |
| `concerns` | | 15,814 | |
| Release's reading | 84,932 | 94,218 | 85,593 |
| The fold | 13,806 | not reached | 13,086 |
| **All calls** | **13 calls, 3,302,029** | **11 calls, 1,969,107 (−40%)** | **14 calls, 1,113,745** |
| Read from the cache | 88% | 87% | 76% |
| Seconds of the model | 937 | 581 | 427 |
| Goal sent → Done, by the clock | 82 min | 16 min | 9 min |
| The task's gate | 22 s, 237 s twice, 900 s killed, 11 s | 88 s | 77 s |
| The checks into main | none ran | 1,167 s, 6 red of 747 | 80 s, green |
| Product's change | 4 lines in 3 files, about 250 of tests | +9 −6 in 3 files, 161 of tests | +82 −2 in 2 files, 140 of tests |

**The session's tokens are not cheaper by being one.** A's 1,384,853 is 6% *more* than the base's three clean tasks together (1,306,014). The 40% comes from what §256, §257 and spec 149 removed
around the session: no review, no send-back for a red from before, no restart after a killed gate. What drives a session is its turns times its context: A ran 26 commands with 343 thousand characters of
output, B 17 with 131 thousand (F5).

## 3. Findings

### F1. Orkboard at `main` does not open on this repository

`llm-wiki/general/pages/ideas/96-orkui-0.15.0-copied.md` has dots in its slug; `realm/ideas.py` `state_folder` takes only `[a-z0-9-]+` and raises *No goal '96-orkui-0.15.0-copied'* from the
town clock's tick (`gui/ideas_route.py` `ripe_tick`). Every `ideas.*` is refused, five red toasts, *No parties yet*: `152-a-leader-accepts/B/first-try/` and the first tile of B's sheet. `orkboard import --goals` (spec 151 H) laid the
page from the spec's file name, and `orkboard check` does not find it. It is the only such page here, but any project with a dot in a spec's file name is the same, and one bad page takes the whole Board down.

### F2. The base's miss came back, and every step passed it on

§253.10's miss: *To the Orkmaster*, what the + card opens with, the square shows no host's hue. Spec 149 J.3 and §257.4–5 were written so that this is caught. On A's merged code, read by its computed colour
(`A/50-verify-default-address.png`): *To the Orkmaster* `ork-elem dust big dim`, *Its rune: none yet*, **as in the base**. *To Tech* is right. The chain:

1. **The section:** `[test] When the + card is open for writing with the default Rune, then its Rune square shows the hue…`. It does not name the state a person first meets (J.3's rule; B's first line does: *When a person first opens…*).
2. **The plan:** the brief says *Preserve the current unaddressed default presentation*, against that line. Nothing compares a brief with the lines it claims.
3. **The task:** writes `[test]`s, all green, none at the default address for the default rune.
4. **The acceptance:** line 1 *met*: *…supported by the reported browser gate*. 4 of 4, nothing sent back. It read the code and took the gate's word for the screen.
5. **The result:** four *Done when* lines and *6 files · 231 passed*. Nobody is told anything.

### F3. `[look]`, `[person]` and *cannot see* never fired

All 9 *Done when* lines of the two runs are `[test]`, though five of them are about what a person sees on a screen. Both runs logged `shot_taken: no preview`, and neither said *Nobody could look at*. The escape is the author's own: a
leader who marks a screen's line `[test]` turns off the only step that would have stopped F2. So in these runs §257.4–5 did nothing, and the acceptance's *cannot see*, its send-back, a base accepted early and a `[person]` question are **not exercised**.

### F4. The way into main sealed A with nothing said

The checks ran the browser folders whole: 747 tests, 19 min 27 s, *6 failed, 741 passed*, kept only as those words in `main_checks`.

- **The page says nothing.** After the run the discard's page still says *Ready for main* with **To main** lit (A's sheet, tile 10). The red appears only in the snapshot.
- **Pressing To main silently starts the 19 minutes again.** Nothing said why.
- **Which six is kept nowhere** (`realm/main_checks.py` keeps the last line). Run again by hand on the same tree, with the machine idle: *3 failed, 744 passed in 17 min 42 s* (`A/main-gate-run.log`). Two are the same reds from before as at the task's gate (`test_hand_mention_browser.py`: red again on the clean base, `A/main-gate-reds-on-base.log`); `test_pwa_party_gather_browser.py::test_the_gather_waits_six_seconds…` passes alone on the base, so it is a timing. **The first run's other three cannot be named:** nothing kept them. None of the three named is this goal's.
- **A red from before seals the goal.** Spec 149 E lets a task's gate tell a red from before, and it worked (two of `test_hand_mention_browser.py`, no session called); the checks into main do not. There is no way on but a hand edit, so A stopped here.

B, with no such red and no `pwa/` file: 80 s, green, merged, the fold 13,086. To main does what spec 149 G asked.

### F5. A brief asks for what the sandbox cannot do

The task's prompt says *A browser cannot start here: do not look for one; the gate runs the browser tests*. A's brief, from the plan, says *run … the affected GUI and phone tests, and the opened-field browser coverage*. So the session ran them: 6 of 26 commands failed,
outputs of 78 and 53 thousand characters, and in its own words *ten failures, all localhost bind PermissionErrors, before being interrupted*. The phone's integration tests need a socket the sandbox refuses. Each such output is then read again on every later turn, at 1.3 million cached tokens in all.
B's plan did not ask it and its session is 43% of A's.

### F6. Talk: cheap, and it does not see the code

- **A doubt from not looking.** `talk_round` is 15 thousand tokens with no file read. A: *The touched modules are missing from the map; go once their boundaries confirm…*. The person is asked to rule on what one `rg` answers. The base's `diagnose` was twice Talk's price and right about the code.
- **§259 is not in the app.** B's first question, *How does the card set models?*, is answered by the goal's own words (*a host command sets it*) and by spec 130 B.3. It reached the hand; §259 is built only for a tool that works the Board's rules.
- **A leader off the route doubts.** B's route is Tech; Product weighed in (`weigher: true`), with *no tested job shows…*, and had the person swipe past a goal spec 130 decided, naming the import-cycle goal, which is on Hold. Talk's record then reads *Product manager: For: — Against: —*.

### F7. The acceptance: cheap, and the verdict is not yet earned

102,333 and 107,905 against the review's 556,105: **about −81%**, on `gpt-6-astra`; A's read 45 thousand characters of files. Both accepted on the first round, nothing sent back; **in A one of the four *met* is wrong** (F2). Its `learned` lines in the journal are about the call and not the slice: *Reviewed dev changes; the working checkout is main. The 231-pass gate was supplied evidence, not rerun here*. The result page does not show the person that a leader accepted anything, nor how.

### F8. Orkboard on the Board in the code (B)

- **The repository's parties are asked for again:** the Board has Tech, Design, Product and Release with their seats, and the first open shows empty chairs and *Who shall work on it?*.
- **Who they are is lost:** after Start every leader wears the peon's head and `craft: engineering`, and Tech's tab says *Taskmaster* (`tech.md` says `leader: architect`, `recipe: tech`). The races are the project's frame (CLAUDE.md).
- **Parties left out come back:** Design and Product unticked, then tabs on the table and leaders in Talk.
- **The first open commits 121 pages to `dev`**, the schema moved (`board: v1… moved`, 144 lines), and `project.md` written with *The brief: Nothing yet*.
- **History is unseen news:** *Done, not yet seen* lists 115 goals laid from history, each with its Result, and **To main is under them all**, reached by scrolling. The discard's top card says *V1 · 1 goal ready for main*.
- **Held:** nothing ran on its own. The goal in `new` stayed on Hold, the five in `work` stayed *To review*, and `orkboard check` is clean at the end.

### F9. Small words

- **The diff's minus is always 0:** the result says *+170 −0* and *+222 −0*; git says 6 and 2 removed (`plan.tasks[].diff`).
- **Spec 149 K's *the share of the week*** is not on the result, only *1.8 million tokens*.
- **B's card says *Elder model*, *Warrior model*, *Laborer model*:** old spellings; `realm/lexicon.py` has Veteran, Seasoned, Novice. It prints the key, and no test reads it (CLAUDE.md, Wording).
- **B's card says *Inherited default* twice a tier and names a family:** `gpt-astra` is no model in its own list. It works: changed, saved in `tier_models`, kept through a reload, the others untouched (`B/51-verify-card-open.png`).
- **Release in A** hands a card of three questions about a release nobody asked for; 94 thousand tokens. B's hands none.
- **To Tech** still starts picking at once with the field open (spec 149's *Not this spec*).

## 4. What held

| From | Held |
|---|---|
| §257.1 | **One task in each run**, no split to justify; four in the base |
| §257.2 | 6 files named in each, all existing, all opened; A changed 4 and 2 new ones, B 4 |
| §257.3 | every line claimed, no second call of the planner (`proves`) |
| §257.4 | B's commit says its tests failed first; A's first test run is red |
| §256.1, 152 E | every task's role is `grunt`; the leader's seat is `elder`; the checkers planned nothing at Lean |
| §257.6 | no task read `BOARD.md`, moved a phase or wrote a page, with the rules' block now in `AGENTS.md` |
| 149 A | the type chosen is the route (`shaped-feature`, `feature`); nothing dropped and sent again |
| 149 B | *a backend*, from `pyproject.toml`; no game asked |
| 149 C, D | the gates end in 88 s and 77 s, a `pwa/` file's too; no gate killed |
| 149 E | a red from before called no session, and the result says *2 tests were red before this goal* |
| 149 F | no session hunted `index.lock` or a browser |
| 149 G | To main runs its checks |
| 149 H | the result says the tokens and what was promised |
| 149 K | no hand edit of `orkcraft.toml` |

No broken command, no error toast and no console error in either run, but F1's. The one `command_refused` in A is this driver's.

## 5. What these runs cannot say

- **Spec 154's skills are not touched:** they are Claude Code's, and §258.8's *one voice* arm (`151-the-board-in-three-tools.md`) has not run. On Codex through the page, §258's `### Talk` and `### Accepted` are written by nobody: Orkboard's own Talk stays `talk.jsonl`, as spec 154 says.
- **Spec 152 E's run at Standard with two checkers** is still to do. A party's acceptance *between* two parties too: both routes built by one party.
- **Whether the acceptance sends back rightly:** in two runs it never sent back. One of 9 lines was wrongly met.
- Two runs are not a distribution. A's and B's sessions differ by a factor of 2.3.

## 6. Against the criteria

| # | Question | Result |
|---|---|---|
| 1 | How many tasks, and why each split | **holds**: 1 and 1 |
| 2 | A session under the base's three (1.31 million) | **no in A** (1.38), yes in B on another goal |
| 3 | Named files read and changed | **holds** |
| 4 | Each line claimed | **holds** |
| 5 | A screen's line is `[look]` | **no**: 0 of 9 |
| 6 | The base's miss caught | **no** (F2) |
| 7 | Every task's role, the leader's tier | **holds** |
| 8 | The acceptance against 556,105, and right | **cheaper; not right in A** |
| 9 | No task touched the Board | **holds** |
| 10 | Spec 149 K | holds but for the share of the week; **A sealed by a red from before** |
| 11 | The Board readable, nothing worked alone | `check` clean, nothing ran alone; **F1 and F8** |

Against `docs/beta/run-the-whole-way.md` §4: B reaches main with one hand edit (F1), so condition 1 fails; A does not reach it.

## 7. For the owner to decide

1. **F1**, first: the slug, and one bad page never stopping the Board. It blocks everything else here on this repository.
2. **How a screen's line gets looked at** (F2, F3). The leader's choice of mark has shown it does not hold: a line about what a person sees could be made `[look]` by code, or a `[test]` line of a screen could say at which state it runs; and a brief could be read against the lines it claims.
3. **What the checks into main do with a red from before** (F4), and what the page says on a red; which tests failed kept, not only their count.
4. **The Board in the code as a first open** (F8): the parties and their faces, and history not being news.
5. **Talk's cheap call without the code** (F6): whether a doubt that says *not on the map* goes to the person; §259 in the app; who weighs when the route does not name them.
6. **A brief's test commands against the sandbox** (F5).

## 8. What is where

`152-a-leader-accepts/`: `00-criteria.md` · `A/`, `B/`, each: `00-contact-sheet.png` (a run's stages), `calls-table.txt`, `calls/` (each call's tool, model, tokens: no prompt, no answer), `spend.txt`, `spend.json`, `events.jsonl`, `watch.log`, `plan.json` (the brief, `proves`, `files`, `accepts`), `way.json` (the decision and the section), `talk.jsonl`, `goal-page.md`, `journal-tech.md`, and the verifying pictures · `A/main-gate-run.log`, `A/main-gate-reds-on-base.log` (the 747 tests by hand, and the reds on the base) · `B/first-try/` (F1: its picture and events) · `base/`: yesterday's `spend.json`, `calls/`, `watch.log`, its sheet.

Not here, on the owner's computer in the session's scratch until it is cleaned: every picture of each stage (`A/shots`, `B/shots`, with the pane's), the clones with each call's whole prompt and answer (`.orkcraft/logs/<day>/`), `drive-log.jsonl`. The servers' logs and `drive.json` hold their tokens and do not go.
