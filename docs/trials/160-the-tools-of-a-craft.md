# The tools of a craft: one goal through the orkboard skill in Claude Code, its work on local Codex

8 November 2026, 09:34–11:50. A Claude Code session ran the person's request through this repository's `orkboard` skill (spec 154): laid, routed, Talk,
the person's questions, sections and spec, plan, stages on local Codex (codex-cli 0.166.0), each leader's acceptance, the gate, a pull request
([orkCraft/orkBoard#7](https://github.com/orkCraft/orkBoard/pull/7)). A second session watched it: each commit, the session's own reports, and pictures of
Orkboard's window served over a clone kept at the branch (frozen Orkboard of `61208bc4`, a HOME of its own, no AI tool on PATH). It then reviewed the
result, fixed what the review found and merged it into main with this report. The goal is **160** (laid as 158: §F6).

**In short.** The flow reached a working, tested feature in 2 h 16 min with no hand edit of its code: 12 stages, each one Codex run of 2–10 minutes,
2,300 lines with 1,100 of tests. The skill's half held. **Orkboard's own window did not follow it**: the goal was invisible until its branch was taken
for the work branch, then shown as a fresh Orkmaster's card routed to Tech alone, and after the spec not at all; and opening Orkboard on the result
**strips `gate:`, `route:` and `asks:` from every goal page the skill wrote** (§F1). Every leader accepted every line on its first look, one with a
bug it had seen; an outside review found two money bugs they passed (§F4).

## 1. The run

| Time | Commit | Step |
|---|---|---|
| 09:35 | `b3861792` `bbdf4eb7` | laid and taken; routed product, design, tech |
| 09:41 | `b47ff27f` | Talk: three *doubt*, six questions for the person (none settled by a written decision) |
| 09:48 | `eccd3b72` | the person's six answers |
| 09:56 | `357926e3` | the three sections and spec 158 |
| 09:59 | `74179193` | planned, 11 stages |
| 10:03–10:19 | `045fc6aa` … `c7f2dba9` | A–D on Codex (the registry, the makers, the pick, the spend) |
| 10:21 | `e324ec40` | Tech accepts A–D |
| 10:23–10:31 | `8253dfb3` `1a71f6c0` `643e16d4` | the person takes the recommended answers to two questions; sections rewritten, re-planned to 12 stages |
| 10:33–11:37 | `0a2855eb` … `a22bc9f1` | E–L on Codex; Tech accepts A–F, Design G–J, Product K–L |
| 11:44 | `44d8d14b` | the gate red: four browser tests, red on main too |
| 11:47–11:50 | `5f5c4544` `316b4fcc` | origin/main merged in, the goal renumbered 160; the gate green (660 passed); done; the PR |
| review | `5cd5c526` | the review's fixes (§F4) |

**The person's answers** (the questions as Talk put them): the word **maker** (first *tool*, the AI tool renamed *harness*, then the recommended
one); **one shape, only Art's makers** (first *every craft at once*, then the recommended); **a cap a run in code first**, the gateway later;
**ElevenLabs's official API first**, Suno once it has one; **the cap on the stall's plate**, each run's cost on its receipt line; **in a pick task**,
not the recipes' `tool` step. The first answers came through the watching session; the change came from the person in the working session
(*Take all recommended*). It cost one Codex run of E thrown away and a re-plan.

**What was built** (spec 160): `realm/craft_tools.py` (the makers' registry: OpenAI Images, ElevenLabs Sound Effects; here or *not here* with why;
a party page's `craft_tools` with each cap), `core/craft_run.py` (the makers over HTTPS on an injectable transport), `core/craft_pick.py` (a pick that
names a maker runs it instead of an AI tool's session: one call in `idea_runner.py`), `core/craft_spend.py` (each request's price reserved on disk
before it leaves, settled after, never above the cap), the stall's *Its makers* shelf with *Set a cap*, the receipt line under a maker's pick, the
`pick_answered` event's maker and cost, H5 in `docs/hypotheses.md`, and an autouse guard in `tests/conftest.py` that fails any test reaching a paid
host.

## 2. Findings

### F1. Orkboard's window and the skill's Board disagree, and the window wins by erasing

1. **A goal on the skill's branch is not on the Board.** Orkboard reads its tree `.orkcraft/board`, at the tip of the work branch (`merge_into`,
   `dev`); the skill works in a branch of its own (AGENTS.md) and commits the page there. Restarted fresh, the window showed no goal 158 anywhere. Spec 151
   A.4 and §255.2 say nothing of a goal laid on another branch. Every later picture here is of a clone whose `dev` was moved to the goal's branch.
2. **Seen, it is the Orkmaster's fresh card.** With its page at `phase: talk`, `route: product, design, tech`, three Talks and six questions
   `asks: person`, the window lays a route card *Route: Tech*, Talk and Hold, *$0.82–2.47, 8th in line* (`02-talk-phone.png`, the sheet's first tile).
   `phase_moved` gives a page laid outside the state `first("talk")`; the page's route and questions are not read into it. From the spec on the
   window shows the goal nowhere: no card in the hand, nothing at work, no discard.
3. **Opening Orkboard strips the skill's record.** Served over the merged branch (this branch's own code), Orkboard committed within seconds
   `board: The table, its edge and the past through the open tab — moved`: `gate:` and `route:` removed from goals 154–160, `asks: person` from one, and
   `project.md` and a journal written. `goal_phase.keys` builds a page's front matter from Orkboard's state, which holds no route or gate for a goal the
   skill moved, and the writer drops every `MANAGED` key not in it. `orkboard check` then finds a `done` with no green gate. The frozen Orkboard of the
   morning did the same and also rewrote `roles/*.md` with its older rules (*the Board's rules (schema 3)*).

### F2. Laying the goal

- `orkboard goal add` named the page `idea.md` from the Russian words; the session renamed it and fixed its index line by hand.
- It laid only the first paragraph; the person's views and four questions were put in the Gist by hand, so the leaders could argue them.
- The title stayed the first Russian sentence cut with *…*, `short: Ввести инструменты`; the pane draws it in the pixel face, uppercase (CLAUDE.md:
  never for a person's words).
- There is no `llm-wiki/general/project.md`: the Orkmaster routed from the Gist and the party pages alone.

### F3. Talk and the questions

- Product's Talk holds three questions and dropped the person's first (the word); Design asked it.
- The lines under *Open questions* carry no numbers; `goal answer <slug> <n>` takes one.
- Two leaders' recommendations went against the person's lean (*the recipe step*; *every craft*); the person took them in the end.

### F4. Every acceptance passed on its first look; the review did not

- Tech accepted A–D 5 of 5 *met* while saying, in the session's words, that *a pick refused for a missing key still holds its reserved money*. It was
  fixed only because the re-plan (after the person's change) gave it stage F.
- An outside review of the merged branch (a subagent with the code, not the leaders' sections) found what all three acceptances passed:
  1. **A send back from Review ran the paid maker again** (`idea_runner.py` called `craft_pick.session` for every `again` but a pick's or a
     re-gate): it paid for new variants, wrote them into the worktree, and never acted on the person's note or the conflict. **Fixed**: only new
     variants run the maker; a send back is the AI tool's work.
  2. **A refused request held its money for good**: any non-2xx answer stayed reserved, so two 429s used a 0.13 USD cap whole. **Fixed**: a 4xx (but a
     408) is released; a timeout or a 5xx stays held, as it may be billed.
  3. **Stop did not stop the spending**: `cancel` was read once, before six requests of 120 s each. **Fixed**: read before each request.
  4. **A keychain key was not stripped** (the variable's was): a trailing newline failed in the header, reserved. **Fixed.**
  5. **`STALL_SHOTS=1` made a `1/` folder in the tree**, which Codex's `git add` committed with stage I (`ba425ec2` removed it; the pictures stay in
     history). **Fixed**: only a folder named in full.
  6. **The cap counted a task's whole life, not one round** (spec 160's Tech *Defaults* say *one round's*): after a round that used most of it,
     *make new ones* was always stopped, and the receipt said the sum. **The person chose the spec's word; fixed**: the ledger is a round's, a
     round run again after a crash keeps its number and what it held, a new round of variants has its own cap.
  7. **Not fixed**: *about* is on the plate's cap for ElevenLabs only, and on every receipt's cost.
- The leaders' `[look]` line (*drawn on Art's chair at 1280 × 800 … nothing overflows*) is proved by `test_stall_browser.py` on a fake host whose
  chair says *tech party* with orks' heads (the sheet's last two tiles). The opened cap field pushes *What leaves this computer* to the rug's edge.
  The real stall did not open in the watching session's isolated window, on Tech's chair either (not this goal's).

### F5. Money that nobody checked

- **The price tables were written by Codex with no network** (the session's own warning). ElevenLabs's 0.12 USD a minute matches its page.
  OpenAI's `gpt-image-2` is priced 2.50 / 4.00 / 15.00 USD a million tokens (text in, image in, image out); third-party listings say 5 / 8 / 30, none of
  them OpenAI's own. The estimate allows 4,096 output tokens a picture, which may cover it. **Check both against the providers' pages before the
  first paid run**; the cap guards an estimate.
- OpenAI as the picture maker and where the keys are read from (`tools/<id>` in the keychain, else the API's variable) are the leaders' defaults,
  not the person's choices.

### F6. Two sessions took the same number

While this goal ran, other sessions laid goals and specs **158** and **159** on main. This one merged main and renumbered itself 160 (`5f5c4544`);
its commits before that say 158. Nothing reserves a goal's number against the remote before it is laid.

### F7. Codex as the hands

- 12 stages, each one `codex exec` in the session's worktree (`-s workspace-write`, `approval_policy=never`), 2–10 minutes; three went back once for a
  browser failure (one a real bug: focus not moving into the cap field).
- Codex's sandbox cannot start a browser, so the session ran every browser test itself; asking for network in the sandbox was refused, once.
- `idea_runner.py` (612) and `lexicon.py` (635) are past the ~600 line split and grew by one and five lines.

### F8. Tests

- The critical tests and the touched modules': 274 passed (an xdist race in `test_design_system.py`'s orkUI check, green alone, not this goal's).
- The goal's browser tests 20 of 22; the hand and table modules 248 of 249. Every red here is red on `origin/main` at `4bcd6c76` too:
  `test_stall_browser.py`'s *a tab pressed while open* and *settings ends with the inventory line*, `test_table_desktop_browser.py`'s *plus … potion
  [wide]*, `test_one_pick_browser.py`'s two and `test_picking_desktop_browser.py`'s *a press on a part* (the 390 px one passes and fails by turns on
  both).
- After the review's fixes: `test_craft_*`, `test_maker_*`, the runners, the picks, the architecture: green; seven new tests for the fixes.

## 3. What is where

- `160-the-tools-of-a-craft/contact-sheet.png`: Talk, the spec, the plan and done in the window (the clone's `dev` at the branch), and the stall
  test's two pictures. `02-talk-phone.png`: the window's route card at 390 px.
- The goal's page `llm-wiki/general/pages/ideas/160-the-tools-of-a-craft.md`, its spec `docs/specs/160-the-tools-of-a-craft.md`.
- The other pictures and the watching session's log stay local.
