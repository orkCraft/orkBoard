# Spec 91 — The owner's list of 26 October: the limits always seen, a quieter top bar, Play that breathes, an AI tool for each seat, New party in two halves, parties and goals beside the Orkmaster

The owner, 26 October (decisions §107), after a day on their AR party game, and the mockups drawn and agreed the same day
(the canvas *Orkboard — макеты*: New party, a seat's AI tool, the top bar and its usage, the Orkmaster's two rows). The
look is orkUI 0.13.0's (decisions §106). **Builds:** Claude · **Review:** full · P1.

**What it is, and is not:** the top bar's right holds only the AI tools' limits and *Stop all*; a limit pressed shows what
used it, by party and member; *Agents* and *Files* leave the top bar (the Orkmaster's *Assets* tab takes the files);
*Settings* is a word beside the product's name; the toasts go back to the page's foot; Play's start screen breathes while the
build starts and says what it waits for; a party's seats each have their own AI tool, the list saying which tools can do
what the role needs; New party is presets on the left and the team by seats on the right; the Orkmaster's level has a
parties row and a new-goal row. Not: the phone's top bar (it has none: its limits stay where they are), a new AI tool, a
tool that makes audio (none can: the list says so).

| part | builds | files (and their tests) |
|---|---|---|
| **A. Top bar** | §1, §3, §4 | `js/shell/topbar.js`, `js/shell/shell.css`, `page.css`, `js/arena/project.js` (the tabs), `js/arena/assets.js`, `js/shell/files.js`, `js/shell/store.js`; their desktop browser tests |
| **B. What used a limit** | §2 | `gui/ideas_limits.py` (or a new `gui/ideas_usage.py`), `realm/idea_spend.py` readers, `js/arena/limits.js`; new `tests/test_limits_usage.py` and a desktop browser test |
| **C. Play breathes** | §5 | `js/arena/play.js`, its CSS, `gui/ideas_assets.py` (`stage`, the output's tail), `core/idea_shot.py` (`opened` keeps the tail); `tests/test_play.py` and Play's browser test |
| **D. A tool a seat** | §6 | `realm/goal_team.py` (`tools_of`, `set_tools`, `tool_for`), `realm/harnesses.py` (`makes`), `core/idea_runner.py`, `core/idea_keeper.py`, `gui/ideas_goals.py` (`goal_save {tools}`), `gui/ideas_project.py` (`ideas.tools` with `makes`), `realm/library.py` (`needs`); new `tests/test_seat_tool.py` |
| **E. New party** | §7 | `js/shell/goalwizard.js`, `js/shell/goaldialog.js`, `js/shell/partysize.js`, `js/shell/toolpick.js` (split before ~600 lines); the phone's `pwa/shell-goal-new.js`, `pwa/shell-party.js`, `pwa/app.css`, `pwa/sw.js` (`CACHE` one up); their browser tests |
| **F. The Orkmaster's two rows** | §8 | `js/arena/projectdeal.js`, `js/arena/newgoal.js`, `js/shell/proposals.js`, `gui/ideas_goals.py` or `core/idea_kind.py` (the kind guessed); the phone's project screen; their tests |

## 0. The words
*Settings*; a limit's chip: `<mark> <tool> <n> %` and its window (*5h*, *week*), or `$<n> today` for a tool paid by use;
the panel *What used it*: *This project* / *All projects*, a row per party and, under it, per member, *Outside Orkboard*,
and the line *Each share is estimated: the limit read before and after, split by the tokens of each call.* Play: *Making
its worktree*, *Starting `<command>`*, *Waiting for a page on :<port>*, the seconds; failed: *The build stopped* with its
last lines. A seat's tool: *Its AI tool*, its first row *The party's tool (<name>)*; the groups *Can do what <role> needs*
and *Cannot <need>* (*make pictures*, *make sound*), the reason in words (*draws no pictures*, *not installed*, *not signed
in*). New party: *By stage of the project*, *By craft*, *Your own party*; the bands *Leads*, *Does*, *Checks*. The
Orkmaster's rows: *Parties* (*New party*, a proposal's *Add*), *New goal* (*for <party>*, *Add goal*, *More kinds…*).

## 1. The top bar (A)
Left: the product's name, then **Settings** as a word (a link-styled button, the button face; it opens Settings as the gear
did; the gear goes). Right, and only these: a **chip per AI tool** whose limits were read (B's panel on a press; warning at
20 % or less left, danger at 5 %, as today's `levelOf`), then **Stop all**. *Spend* and *Last week* move into B's panel
(the week's work stays reachable from it). *Agents* and *Files* leave the top bar: what Agents showed of a member at work is
in its party's column and B's panel; the files are in the Orkmaster's *Assets* tab (§3).

## 2. What used a limit (B)
`ideas.usage {provider, scope: "project" | "all"}` → `{provider, left, window, reset, rows: [{party, title, share, members:
[{agent, name, share}]}], outside}`: for the limit's current window, each `limits_read` pair (before, after) gives the share
used between them; the project's calls in that span (`spend.jsonl` lines of the tool, their tokens) split it by party and
member in proportion; what the reads say was used and no call of ours accounts for is *Outside Orkboard*. Shares are whole
percents of the window; no read pair yet: the rows give tokens only and say so. No model. The panel (limits.js) opens
under its chip: the tool's line as today (left, reset, diamonds), the scope switch, the rows, the line of §0.

## 3. Files in Assets (A)
The Orkmaster's tabs become *Field*, *Assets and files*, *Play*. *Assets and files* is Assets (spec 88) with, at its top
right, a switch *Assets* / *Files*: *Files* is today's Files pane (the tree, a file opened in the right column).

## 4. The toasts (A)
At the page's foot, centred, above the hand (never over a dialog's buttons): the rule of spec 90 that put them at the top
goes.

## 5. Play breathes (C)
While Play starts, the project's name in the pixel face **fades in and out in a slow loop** (2.4 s, steps, never a spin;
still under `prefers-reduced-motion`), and under it a line says the stage and the seconds (§0): `ideas.play` answers
`stage` (`worktree` · `command` · `page`) and `ports` asked so far. Failed: the line says why and the last 30 lines of the
command's output show in a quiet box (`opened` keeps the tail, ANSI codes out). Play's own wait for a page is 60 s
(`PLAY_OPEN_S`), not the picture's 20.

## 6. An AI tool for each seat (D)
- A party page keeps `tools` `{agent: tool}` beside `tiers` (`goal_team.tools_of` / `set_tools`); a seat with none runs on
  the party's tool, the party's on the Main tool (spec 81). `goal_team.tool_for(root, party, agent)` is the one answer.
- The runner runs a task on its taker's seat's tool; the keeper runs a goal's leader's steps on the leader's seat's tool.
- `Harness.makes`: what a tool can make beside code and text — agy `("pictures",)`, the others `()`. A library role may
  say what it `needs` (`artist`, `icon-artist`, `animator`, `aso`: pictures; `sound-designer`, `composer`: sound).
- `ideas.tools` rows carry `makes`. `goal_save {…, tools}` keeps the seats' tools (refused: *No AI tool <id>*, a seat not in
  the team).
- A tool that cannot do what its seat needs may still be picked (the person decides); the list shows it under *Cannot …*.

## 7. New party (E)
One dialog, two halves (the mockup's *New party*). **Left**: presets *By stage of the project* (Ideation, Concept, Build,
Release, LiveOps; for the project's kind, `party_recipes`), *By craft* (Tech, Design, Data, Marketing, Product, Art and
sound), *Your own party* (the Taskmaster alone). **Right**: the name, *What it is for*, the size switch (Lean · Standard ·
Full: the seats and tiers change at once, spec 81 §2) and the bands *Leads*, *Does*, *Checks*: a seat a row (its head by
race and tier, its role, its tier and race and what it does, what it needs, **its AI tool**, ×), an empty seat a dashed
*Add a member* that opens the library's roles for that band. *Edit the party* is the same dialog on the party. The phone:
the same steps one under another (presets first). Stage presets that are not recipes yet (Concept, Build, LiveOps) are
added to `party_recipes` for the kinds they fit.

## 8. The Orkmaster's two rows (F)
Beside the Orkmaster's head on its level: **Parties**: *New party* (opens §7) and the two or three proposals for this
project (`ideas.proposals`) each with *Add*; **New goal**: one line for the goal, *for <party>* (the party it goes to,
the Orkmaster's guess first), *Add goal*; under it at most three kinds for that party (the guessed one marked) and *More
kinds…* (the full list, grouped). The kind is guessed from the line when it is typed (`idea_kind`), never asked first.
The project line's separate *New goal* and *New party* piles go, and so does its **+** of New goal (a host with no Orkmaster, from before spec 70, keeps it: it has no level to hold the rows).
`ideas.kind_for {text, party?}` → `{type: id | "", types: [ids]}` (`core/idea_kind.py` `guess` / `ranked`: the words each goal type says, no model, nothing written): the kind the line says among the kinds the
party is offered (all of the catalog's with no `party`), the guessed one first. The row asks it as the line rests (≈ 0.25 s), then `ideas.party_for` of that kind for the party the Orkmaster picks (a party the person
picked stays), then the kind among that party's. *Add goal* sends `ideas.add` as New goal does (`text`, `track`, the party's `priority`, `type` when one is picked or guessed; a pitch has none). *More kinds…* deals the
party's kinds, then the others', under their headings (`js/arena/types.js`) and opens New goal on the kind picked with the line in it. The phone's project sheet has the same two rows, one under the other, every target
44 px at least (`pwa/shell-project.js`); its *More kinds…* opens today's New goal form with the line and the party picked.

## 9. Order
A, B, C, D in parallel; E and F after D (E needs `tools`, F the proposals and E's dialog). Each part merges into `main` when
its tests pass (the alpha rule).

## As built (E)

- **The presets** (`realm/party_recipes.py`, new `realm/party_presets.py`, `ideas.party_presets`): `party_recipes.STAGE_RECIPES[kind]` has each kind's **Concept**, **Build** and **LiveOps** (ids `<kind>-concept` · `-build` · `-liveops`, made of the library's agents; an empty folder and an unknown kind have `code`'s), proposed to no one (`for_kind` does not list them; `get` and `kind_of` find them); `stages_of(kind)` is the five stages in order, Ideation and Release the library's presets. `party_presets.listed(kind)` is New party's left half: rows `{id, name, line, group: stage|craft|own, stage, craft, recipe, whole, leader, build, check, sizes}`, `sizes` as `sized` gives them (leader, team, tiers); **By craft** is the library's parties of one craft and Art and sound; **Your own party** is the Taskmaster alone (`mixed`). `ideas.party_presets` answers `{kind: {id, words}, presets}` for what the folder is; no model, nothing written.
- **A seat is a stage** (spec 87 §5 stands): each band's seats come from the leader's stages (`ideas.roles` `stages[leader].seats`, one a stage), so *k of n seats* reads *1 of 1 seats*; a recipe lists its builders and checkers most needed first and a size seats the first of each (Lean none, Standard the first builder, Full the first builder and the first checker). The rest are the band's list under *Add a member* (the preset's own first, then the leader's craft's). A party made before keeps its members over its seats (marked, saved as it was).
- **The stages per kind** (leader · builders · checkers; the first of each is the seated one): game Concept game-designer · level-designer, artist · playtester; Build game-designer · grunt, artist, sound-designer · playtester, reviewer; LiveOps analyst · data-engineer, grunt, copywriter · data-reviewer. mobile Concept product-designer · ui-kit, artist · accessibility-reviewer; Build product-manager · grunt, ui-kit, artist, aso · reviewer, accessibility-reviewer; LiveOps analyst · data-engineer, aso, community · data-reviewer. web Concept product-designer · copywriter, ui-kit · accessibility-reviewer; Build product-designer · grunt, ui-kit, copywriter, seo · reviewer, accessibility-reviewer; LiveOps growth · seo, copywriter, community · editor. backend Concept architect · data-engineer, grunt · security-reviewer; Build architect · grunt, tester · reviewer, security-reviewer; LiveOps analyst · data-engineer, sql, grunt · data-reviewer. data Concept analyst · experimenter, sql · data-reviewer; Build analyst · data-engineer, sql, experimenter · data-reviewer; LiveOps analyst · data-engineer, sql, grunt · data-reviewer. wiki Concept product-manager · copywriter · editor; Build product-manager · copywriter, seo · editor; LiveOps product-manager · copywriter, community · editor. design Concept product-designer · artist, ui-kit · accessibility-reviewer; Build product-designer · ui-kit, artist, animator · accessibility-reviewer, art-reviewer; LiveOps analyst · experimenter, copywriter · data-reviewer. texts Concept growth · copywriter · editor; Build growth · copywriter, seo · editor; LiveOps growth · seo, community, copywriter · editor. code (and empty) Concept product-manager · grunt, copywriter · reviewer; Build architect · grunt, tester · reviewer, security-reviewer; LiveOps analyst · data-engineer, grunt, copywriter · data-reviewer.
- **Desktop** (`js/shell/`): `partymodel.js` (the presets as the host or an older host gives them, `sizedTeam`, `tiersFor` — the same rule as `party_recipes.tiers_for`, so a seat's head changes at once —, the tool groups), `partydraft.js` (one hook: the leader, the team, the size, the candidates, the party's tool and each seat's), `partypresets.js` (the left half), `partyseats.js` (the bands, a seat's row, a free seat's short list: six roles and *More roles*), `seattool.js` (a seat's tool list), `partypop.js` (a popover: Esc closes it, not the dialog; `modals.js` leaves an Esc inside `[data-pop]` to it), `partysize.js` `SizeBar`, `partyform.js` (`usePartyForm`, `PartyBody`: both dialogs), `goalwizard.js` (New party) and `goaldialog.js` (Edit the party, with *Remove party* at its foot), `party.css` (loaded after `shell.css`); `party.js` lost `LibraryTiles` and `PartyBands`. New party opens on the project's **Build** (the library's Tech for a host with no presets), or on the preset asked for by id, or on a proposal of the Orkmaster's deal (`proposal`: its seats at Full); a name the person has not typed follows the preset. Save sends `size`, `tool` (the party's, when picked), `tools` (the seats whose tool is not the party's), `proposal` (a stage or recipe kept as the party's recipe) or `preset` (a craft's), `party` for a saved party; Edit sends only what changed. A member with work open is refused in place (its ×, a size that would let it go). The Orkmaster's proposals screen is no longer in New party (spec 91 §8, part F, puts the proposals beside the Orkmaster); `proposals.js` is as it was.
- **Phone** (`pwa/`): `shell-party-new.js` (New party: the presets, then the name, the size and the team, Save party pinned at the foot with *<n> agents · …*), `shell-party-presets.js`, `shell-party-seats.js`, `shell-party-model.js` (the desktop's twins), `shell-seat-tool.js` (a seat's tool as a sheet), `party.css`; `shell-party.js` (*About this party*) gives each member **Its AI tool** (a pick saves `tools` at once); `shell-goal-new.js` keeps `makeParty` (the folds of *Add to the party*). `sw.js` `CACHE` is `orkcraft-app-v100` (E added `shell-party-price.js` to SHELL; the merge with F is one above both).
- Tests: `tests/test_party_presets.py`, `tests/test_new_party_91_desktop_browser.py`, `tests/test_pwa_new_party_91_browser.py`; the New party, Edit the party, size and tool tests of both faces follow the new dialog.
- **E with F**: the Orkmaster's *Parties* row (`js/arena/projectrows.js`, the phone's `pwa/shell-project.js`) opens E's dialog: *New party* is `openDialog("goal")`, *Add* on a card is `openDialog("goal", {proposal})` or `{preset}` (the phone: `core.newParty("proposal:<id>")` or `core.newParty(<preset>)`); E's dialog picks that proposal's stage (the row whose `recipe` it is) or the library's party, seats and all. The dialog's own old proposals screen and the project line's piles are gone.
