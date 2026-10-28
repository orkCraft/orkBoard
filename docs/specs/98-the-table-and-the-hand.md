# Spec 98 — The table and the hand: the window's frame on today's engine

The owner and the PM, 28 October (decisions §104.0, §131, §136.11–§136.12, §142–§145, §147.1; spec 95 §1–§4, §5.1, §8.1,
§9–§10; spec 94 §1). The first slice of spec 95 cut to **what proves the frame** (spec 95 §11's *Asked*, settled here):
the window made of the table and the hand, drawn over the engine as it is today. What a goal's way adds to it (the route
card, *Talk*, the decision's card, the sections, the forks, the project's questions, the one place of the parties) is
spec 99 (its engine) and spec 100 (its faces), built on this frame; nothing here is built twice for them. **Builds:** a cheaper model, each part reviewed by Claude · **Review:** full · P0. **A first, alone** (it touches
the files everything else does); **then B, C and D at once** (they share no file; C and D read the seams of §0.2, which
the lead writes before they start); **E after C and D**. **C, D and E only after the owner's yes on the mockup**
(`docs/mockups/s1/`) and after orkUI 0.15.0 is copied here (spec 96).

**What it is, and is not:** what goes first (§131's list, *Agents*, Operations in the window); then the window as two
parts: the tabs (the Orkmaster's first, a tab a party, **+**, the limits, *Stop all*), the pane (the Board under the
tabs, Tech's *System* as read today, a party's header and its seats' popovers, one thing opened over the pane), the hand
(the deck with the + card drawn off it, the stacks of today's stops by goal, the discard with what is ready for main, the cost's gem), the goal
picked, a goal's signs, the cards' answers to the hand (§149.1), at the wide and the narrow width (spec 94 §1). Not: the
route card, *Talk*, *Confirm and start*, forks, the project's questions, a question as a card of choices with a pick,
the one place of the parties, the races by party (specs 99, 100); the other maps, picking and the box (S3); Play of a
goal, System read anew (S4); the phone's page, the low window of a phone on its side (§150, S5); the reveal *Since
<version>*, the history, the voice, Settings made small (S6); a read opened in VS Code's editor (§146.1, after this
slice). Until spec 100, a party is made and edited by today's form, opened over the pane.

| part | builds | files (and their tests) |
|---|---|---|
| **A. What goes** | §1 | see §1's table (the faces, the host commands and the tests of §131's list, *Agents* and Operations) |
| **B. The host** | §2 | `gui/ideas_board.py` (a result seen; a goal's place), `realm/board_map.py` (a node's `place` and `seen`), `realm/ideas.py` (`seen_at` in an idea's state), `realm/lexicon.py` (§2.4's words); `tests/test_board_map.py`, `tests/test_ideas.py`, `tests/test_lexicon.py`, `tests/test_gui_ideas.py` (or the file that tests `ideas.board`) |
| **C. The table** | §3, §5, §6 | new `static/js/table/` (`table.js`, `tabs.js`, `header.js`, `seatpop.js`, `boardmap.js`, `pane.js`, `over.js`'s places, `card.js`, `table.css`); `static/js/arena/systemarch.js` and `systemmap.js` read only (imported as they are); new `tests/test_table_desktop_browser.py` |
| **D. The hand** | §4, §5, §6 | new `static/js/hand/` (`hand.js`, `pluscard.js` (the + card and the field), `deck.js`, `deckrow.js`, `stacks.js`, `stopcard.js`, `discard.js`, `cost.js`, `hand.css`); `static/js/arena/stops.js`'s answering parts read only; new `tests/test_hand_desktop_browser.py` |
| **E. The window** | §7 | `static/js/shell/shell.js` (the frame in place of the top bar, the arena and the drawer), `static/board.js`, the modules no longer imported (removed), `static/js/shell/modals.js` and every `openDialog` caller left (each moved over the pane or into the hand), `tests/test_design_system.py` (`SHEETS`), `tests/test_gui_wording.py`, `tests/test_architecture.py` if it names a removed file; the desktop browser tests of the removed faces removed or moved to the frame |

## 0. The words and the seams
1. **Words** (§2.4 puts them in `TERMS`): *table*, *hand*, *deck* (read *In line*), *discard* (read *Done*), *lane*,
   *blank card* (the + card and its field), *lifted card*, *map*, *seat*, *squad*, *size*, *in line*, *Hold*, *To main*. New strings: *Write a
   goal…*, *→ Tech ×* (the party addressed), *In line*, *Done*, *n goals ready for main* (*1 goal ready for main*),
   *The whole project*, *through <party>* (*The whole project · through Tech*), *Open*, *Put it back*, *Stop all*,
   *New party*, *Settings*, *Open a project…*, *Files*, *about n% of <tool>'s week*. The interface says *party* for the
   code's goal and *goal* for the code's idea (CLAUDE.md); a part of a map is never called a *card* where a person reads
   it (spec 95 §12).
2. **The seams C and D share**, written by the lead before C and D start (`static/js/frame/`), never changed by C or D
   (a change they need is asked for):
   - `frame/state.js`: the signals `tab` (the open tab: `"orkmaster"` or a party's slug, kept per project on the device),
     `picked` (the picked goal's slug, `""` the whole project), `over` (what is open over the pane: `null` or
     `{kind, title, from, props}`), `lifted` (the lifted card's key, one at a time on the table and in the hand), and
     the functions `openOver(kind, props, from)`, `closeOver()`, `pick(slug)`, `lift(key)`, `lower()`.
   - `frame/kinds.js`: the kinds `openOver` knows and who draws each (C draws `file`, `diff`, `log`, `task`, `role`,
     `settings`, `projects`, `files`, `party` (today's form), `play`; D draws `deck`, `discard`, `result`, `stop`).
   - `tests/narrow.py` (spec 94 A): the narrow browser, 390 × 844 with touch, beside the wide 1280 × 800.

## 1. What goes first (A; §131, §136.11, §147.1)
**The desktop's window only.** The phone keeps its faces until spec 94 E removes them (spec 94: *until then the phone
stays as it is*), so every host command, snapshot key and Needs you kind the phone or Orkline reads **stays**
(`ideas.agents`, `ideas.night_allow`, `ideas.queue`, `ideas.canvases` and its kin, `ops.*`, `ops_rev`, `ops_team`,
`canvases_new`, `canvases_rev`, `reserve.night`; `tests/test_board_alone.py` pins them). The engine's night (its runs,
its refresh, its proposals: `core/idea_night.py`) goes with spec 99, where the map's text takes the refresh's place
(§156.12). What A removes is drawn by the desktop's page alone:

| item | goes (desktop) | stays |
|---|---|---|
| ***Process now*, *Judge now*** (§131.1) | the `arena-power` button (`arena/goals.js` 100–108, its imports), `pitches.js` 39–48's `power`, `arenawords.js` `powerOf`, `pitchwords.js` `judgePower`, `foldrow.js`'s aside for it, `column.css` `.arena-power`; *Process now* / *Try again* of a raw goal in `board/idea.js` 179–180 keeps *Try again* only; *Judge now* in `shell/pitchview.js` and `shell/ideadialog.js` `PitchGoal` | `ideas.queue`, `ideas.read_now`, `ideas.judge` (host; *Try again* uses it) |
| **the night** (§131.2) | `shell/nightask.js` and its entry in `shell/dialogs.js`; *Tonight*, the Low line and `askAfterLow` in `shell/ideadialog.js`; the night's window and *Low work may run at night* in `shell/settings.js`; `board/cards.js`'s night words, streak and *Tonight: n wait*; `arenawords.js`'s *tonight* words and signs; `pitchwords.js`'s night lines; `goalwords.js` `moonOf` and `goals.js`'s moon on the row; `board/idea.js`'s big moon; `orkui.js` `Moon`; *Start now* on a plan that starts tonight in `stops.js` 109–119 (*Start now* for the reset stays); the night lines of `idle.js`, `limits.js`, `mapstage.js`, `target.js`, `stacks.js`, `stages.js`, `projectrows.js` | the engine (spec 99), the host's commands and keys |
| **the gate's quiet line** (§131.3) | `arena/gate.js` `GateLine` and `IntoLine`, their uses in `partylist.js` and the unused import in `arena.js`, `arena.css` `.arena-gateline*`, `.arena-into*`; `flags.js` `gateButton` flies from the flag line's own place instead | `mergeGate`, `GateView`, `arenawords.js` `gateOf` (the hand's card and the gate's screen) |
| **collisions as stops of their own** (§131.4) | the project level's collision line (`project.js` `orkLinks` use, `collidewords.js` `orkLinks`) | the collision's card in the hand (`collide.js`, its answers): it is the fork §131.4 asks for, a card of its goal's stack in D |
| **a goal type's sign on the row** (§131.5) | `goals.js`'s `typeSign` on the row, `pitches.js`'s blank span, `column.css` `.arena-goal__type` | `stacks.js` `typeSign` (a card's kind) |
| **the row's peek** (§131.6) | `arenastate.js` `peek` (and in `shownGoals`), `goals.js`'s hover, its use in `arena.js` and `shell.js`'s Esc | `members.js` `Peek` (a member's card), `play.js`'s `peek` argument |
| **the analytics page** (§131.7) | nothing: Orkboard draws no analytics page (`realm/analytics.py` is the logs' zip, used by *Download today's logs*) | all |
| **the canvases** (§131.8) | `arena/canvases.js`; the *Canvases* kind in `arena/assets.js` 19, 23, 254–289; the canvas tab in `shell/preview.js`; the canvas state in `shell/store.js`; `arena.css` and `assets.css` canvas rules | the host (`gui/ideas_canvases.py`, `core/canvases.py`, `sources/canvases.py`, the hook): the phone and Orkline read them |
| ***Agents*** (§136.11) | `shell/agents.js`, `shell/agentdialog.js`, their entries in `shell/preview.js`, `shell/store.js` (`showAgents` and the pane), `shell/dialogs.js`, `shell/tabs.js`, `shell.css` 76–86, 245, 449–450 | `ideas.agents` (the members' numbers and `busy()` read it), `ideas.role_*` |
| **Operations in the window** (§147.1) | `board/ops.js`, `shell/opdialog.js`, `shell/opcheck.js`; `arena.js` `OpsField` and the Team party's field; `partylist.js` `OpsHeading` and its uses; `goaltabs.js` `opsOn`, `teamOf`, `opsRow`; `arenawords.js` `isOp`, `opStopsOf`, `handOf`'s `ops`; `stops.js`'s operation stops; `board/store.js` `ops`, `refreshOps` and its `ops_rev` read; `board/today.js`'s operation rows; `shell/dialogs.js`'s entries; `shell/shell.js`'s `ops_rev` effect; `shell/projects.js`'s start-screen entry; `partymenu.js`, `proposals.js`, `partyrun.js` (Team), `partyform.js`, `goalwizard.js`, `partypresets.js` (Team's preset), `project.js`, `cards.js`'s `ops_usd` line, `orkui.js` 73; the rules in `arena.css` 457–460, `board.css` 132–152, `shell.css` 207–230 and 330–331 | `gui/ops.py`, `realm/ops_team.py`, `core/op_*`, `realm/op_*` (the phone and Orkline: §147.1) |

**Tests** that go with what goes (wholly about it, desktop): `tests/test_canvases_desktop_browser.py`,
`test_shell_36_browser.py`, `test_races_browser.py` (the heads on *Agents*), `test_record_desktop_browser.py`,
`test_ops_desktop_browser.py`, `test_ops_briefs_desktop_browser.py`, `test_running_team_desktop_browser.py`,
`test_night_asked_desktop_browser.py`, `test_moon_desktop_browser.py`. The tests that touch an item in part lose that part
only (their other assertions kept): `test_arena_decks_desktop_browser`, `test_arena_desktop_browser`,
`test_lighter_column_desktop_browser`, `test_party_list_desktop_browser`, `test_ideation_desktop_browser`,
`test_flags_raised_desktop_browser`, `test_right_column_desktop_browser`, `test_goal_types_desktop_browser`,
`test_type_top_right_desktop_browser`, `test_project_desktop_browser`, `test_assets_desktop_browser`,
`test_party_proposals_desktop_browser`, `test_week_desktop_browser`, `test_owner_27c_desktop_browser`,
`test_one_hand_desktop_browser`, `test_at_work_line_desktop_browser`, `test_route_desktop_browser`,
`test_quiet_desktop_browser`, `test_shell_browser`, `test_spend_share_desktop_browser` (or its desktop name),
`test_recap_desktop_browser`, `test_field_glance_browser`, `test_field_rows_browser`, `test_map_desktop_browser`. No
`tests/test_pwa_*` test changes. **Done when** no desktop module imports what went, the page loads with no error in the
browser's console, and the critical tests, `tests/test_gui_wording.py`, `tests/test_design_system.py` and every desktop
browser test left pass.

## 2. The host (B; §130.1, §145.2, §121.1)
1. **A goal's place** (§145.2): every node of `ideas.map` (and its row of `ideas.board`) carries `place`:
   `"deck"` (not started and asking nothing: `raw` in the queue `hold` (held by the person), or waiting for the reset
   (`held_until`, a plan's later `start_at`)), `"hand"` (not at work, and it has a Needs you row the person answers: a
   plan ready to start, a question, a failure), `"table"` (the Orkmaster reads or plans it: `raw` in the queue `now`,
   `reading`, `planning`; or at work: `working`, a task running, testing or picking), `"discard"` (`done` and its result
   not seen), `"history"` (`done` and seen). A goal at work that asks is `"table"` with `asks_you: true` (on
   the table and in the hand at once, never in two piles). `waits_as` names why a deck goal waits: `"reset"` (its hour
   in today's `waits.until`), `"held"`, `"line"`; `""` otherwise. (Today's `waits` dict and the row's `asks` count stay as
   they are: the phone reads them.) A pitch or a proposal of before lies on `"table"` while someone works on it, in the
   `"hand"` with a Needs you row; a plan passed whose tasks are held stays `"table"`.
2. **A result seen** (§130.1): `ideas.seen {idea}` writes `seen_at` (ISO) into the idea's state; a node carries `seen`
   (`seen_at` or `""`). Opening a goal's *Result* from the discard sends it; once seen, the goal is in the history.
3. **The deck's order** is the Board's today (`ideas.move` moves a goal among those not started; the order of
   `ideas.map`'s nodes is the Orkmaster's). Nothing new.
4. **The words**: `TERMS` gains each word of §0.1 with its key (`table`, `hand`, `deck`, `discard`, `lane`, `blank_card`,
   `lifted_card`, `map`, `seat`, `squad`, `size`, `in_line`, `hold`, `to_main`), each one line of what it is.

## 3. The table (C; §104.0, §110, §134.2–§134.3, §142–§143, §145.1, §145.6)
1. **The tabs** (spec 95 §2): the Orkmaster's first, its crowned head and *Orkmaster · <project>*; its **…** opens a
   menu: the projects (today's switcher, `shell/projects.js`, its list over the pane), *Settings* (today's, over the
   pane), *Files* (today's tree, over the pane). Then a tab a party in the Board's order: its leader's head and the
   party's name; more than fit, the heads alone (the name in the pane's title and on a long press). At the end **+**
   (*New party*: today's form over the pane), the AI tools' limits as chips (today's `limits.js`, a chip pressed opens
   what used it over the pane), **Stop all**. A party's tab carries a dot when the picked goal's route has it (today's
   `route`). The open tab is the person's: nothing switches it under them.
2. **The pane's title**: *<what> · through <whom>* (*The whole project · through the Orkmaster*, *Reconnect keeps your
   seat · through Tech*), and **▶ Play** (today's Play, opened over the pane).
3. **The Orkmaster's tab is the Board** (§143): a column a party, each standing under its party's tab (the tabs take
   their columns' widths while the Board is shown, in the same order; no header of the Board's own); a column's cards
   are its tasks at work (running, testing, picking, a failure), each with its member's head (turned while it works:
   drawn still in this slice's still frames), its goal's element top left, its name up to four lines. The Orkmaster's
   own column, under its tab, holds what it does itself: a goal being read or routed (`reading`, `planning`) as a card
   with its head. A column narrower than a card lays its tasks as tokens (spec 67), no sideways scroll. A goal picked
   through the Orkmaster's tab: its tasks alone (§136.10).
4. **A party's tab is its header and its map** (§134.2–§134.3, §151.3): the header is its name, its squad's heads
   grouped *Leads* | *Does* | *Checks* (today's seats), each with its tier's gear and its AI tool's mark in ink, and its
   size in one word. A head pressed opens its popover (§110.7; `seatpop.js`): its role, what it does, its AI tool, its
   tier and what it costs, *From the next task*, *Set* with *Undo*, *Take off the seat*, the role's text (**Open**: the
   text over the pane). The party's **…**: *Edit* (today's form over the pane), *Remove party* (today's question,
   `partyremove.js`, over the pane). **The map**: Tech's is *System* as read today (`systemarch.js`, with *Feature
   modules* gone from the tabs: one map a tab); any other party has no map yet, so its tab is its header alone (§112.9).
5. **A card is lifted where it lies** (§120.1) and turns over: its back the details (a part's files, *Uses*, *Used by*,
   its changes and their goals as today's part pane says; a task's brief, state and *What it made*), and **Open** on it
   (a part's file, a task's log, a failure's lines, a diff). Esc or a press away lowers it; one at a time.
6. **One thing over the pane** (§142): `openOver` replaces the map with what is opened, its title saying where it came
   from (*← System · server/lobby.ts*); **←** or Esc goes back to the map as it was, the card it came from lit; the next
   replaces it; nothing pinned; the hand stays under it. Today's renderers (`shell/preview.js`'s file, diff, log, task;
   `shell/settings.js`; `shell/goalwizard.js`/`partyform.js`; `shell/projects.js`; `arena/play.js`) are drawn inside it,
   never in a drawer or a dialog.

## 4. The hand (D; §116.2, §121.2, §124, §144.2, §145.3–§145.4, §159, §160)
Three places, left to right, along the window's foot, under everything opened (§160.1):
1. **The deck, with the + card drawn off it** (§160.2–§160.4): the + card lies a little off the deck, face up, a **+**
   on its face. Pressed (or a key typed with nothing focused), it grows into **the field** over the hand: one field,
   *Write a goal…*; Enter sends, Shift+Enter a new line; a picture pasted goes with it (today's `photos`); Esc or a
   press away closes it, its text kept. No priority, no kind. On a party's tab it is addressed to it (*→ Tech ×*, one
   press takes it off); *@Tech* in the text addresses it too; on the Orkmaster's tab it is general, and the party is
   the Orkmaster's (`ideas.party_for`, as the project's level asks it today). It sends `ideas.add`. While there is no
   goal at all, the + card lies large in the pane's middle (§145.8). **The deck**: the one back (orkUI's), its top back
   sealed with the element of the first goal in line (`place` `deck`, the Orkmaster's order) and the moon when that goal
   waits for the reset; edges hint how many (five at most, never a number). Pressed, it **fans out in a row over the
   hand** (`deckrow.js`): the + card, then the goals in line, each its element and name; a goal dragged moves in the
   line (`ideas.move`); a goal pressed is picked; past seven, the last card is *All · search*, opening them over the
   pane (`deck`: the list with a search). Esc or a press away closes the row.
2. **The stacks** (§121.2): one a goal that has Needs you rows, its most urgent card face up (today's stop as a card:
   `stopcard.js`, drawing today's stop from `stops.js`: a plan ready with *Start*, a question with its answers, a
   failure with *Retry*, a pick, a to-do, a result to look at, a sign-in, a plan change, a collision's two goals), the
   cards under it face down; a stack pressed fans out in place and picks its goal. The stacks lie by their top card's
   urgency (today's `byUrgency`). A stop of no goal (a sign-in) is a stack of its own. A card of another party says its
   party.
3. **The discard** (§145.4, §159): the last goal done face up (*done*, its element, its name), the others' backs under
   it; while dev holds goals main lacks (today's gate), its top card carries the lich's head and *n ready for main*;
   with nothing done to see, that line alone on its back. Pressed, it opens over the pane (`discard`): the goals done and
   not seen (a goal pressed opens its *Result*, today's result, and sends `ideas.seen`; it leaves the discard), and
   *Ready for main* with **To main** (today's merge into main, by code). No act on main lies on the pile (§160.5).
4. **One size, the face and the lifted card** (§160.6, §104.5, §144.3): every card of the hand is one size; its face
   its sign or element, its name (two lines at most), its leader's head and, when it spends, its gem (*4%*: a plan's
   *Start*, a failure's *Retry*, *Start now*). Pressed, a card is **lifted** over the pane's foot with its answers, its
   cost's words (*about 4% of Claude's week*) and *Put it back*; the cards of the table it is about rise a little
   (today's `aboutOf`). A card that spends nothing has no gem.
5. A part comes when it has something to hold (§132.1, §145.8): the deck is the + card alone with nothing in line; no
   discard with nothing done and nothing ready for main.

## 5. A goal picked, and its signs (C, D; §110.1, §138.4, §139, §145.5, §145.7)
1. A goal is picked by its stack, any of its cards on the table (its other cards lit), or a goal in the opened deck or
   discard; Esc, or a press on the picked thing again, picks none (the whole project). Picked, it opens on its party's
   tab (today a goal has one party); through the Orkmaster's tab, at work, it is its Board (§3.3).
2. **Its signs are its places'**: the moon in the deck (waiting for the reset), the leader's head (its party works on
   it) and the alert (it failed) on its cards on the table and its stack, *done* in the discard; the hourglass on a
   card a member works on where no head stands (§136.1). No count anywhere; nothing *waits for you* on a tab.

## 6. The cards answer the hand, and the widths (C, D; §149.1, spec 94 §1, §136.9, §143.4)
1. **As Balatro's**, on orkUI's motion tokens only (none of the page's own): a card under the pointer leans toward it
   (at most the lean token) and rises; pressed it gives and springs back; a card played or dealt flies on its arc; a
   stack fans and closes with the spring; a gone card crumbles; still at rest and while read; none of it under reduced
   motion.
2. **Spec 94 §1**: nothing only on hover (a tab's name, a card's whole name, a head's role also on a press), no fixed
   width a part of the window, a press 44 × 44 under `pointer: coarse`, what opens over the pane a screen at the narrow
   width (**←** the browser's back), every browser test at both widths.
3. **The narrow width** (under 760 CSS px): the table above (the tabs a row of heads with *Stop all* at its end, the
   limits' chips in the Orkmaster's **…**; the Board's columns a head's width, their tasks as tokens), the hand at the
   foot (the deck with its + card and the discard at its ends, the stacks between, scrolled sideways inside the
   hand alone).

## 7. The window (E; §145.1, §127.1, spec 95 §10)
`shell.js` draws the frame: the table (C) over the hand (D), nothing else. The top bar, the left column, the right
column and the drawer go, and with them every module no longer imported; every dialog left (`openDialog`) is moved:
a place over the pane (§3.6), an answer into a lifted card of the hand, a confirmation into the card it confirms. The
start screen with no project (`StartScreen`) and the sign-in page (`signin.js`) stay as they are, the first drawn in the
pane. Keyboard: Esc lowers a lifted card, else closes what is over the pane, else picks none; Ctrl/⌘+O opens the
projects over the pane.

## 8. Tests
A: §1's list. B: a node's `place` in each case and `asks` on a goal at work that asks; `seen` and `ideas.seen`; the
terms. C (both widths, `tests/narrow.py`): the tabs in order with the Orkmaster's first, its **…** and its three places
over the pane; **+**, the chips, *Stop all*; the Board's columns under their tabs and the same widths; a task card's
head, element and name; the Orkmaster's column; a party's header with its groups, a seat's popover and its **Open**;
Tech's *System*; another party's tab its header alone; a card lifted and lowered (Esc, a press away); a file opened
over the pane, its title, **←** back to the card lit; no sideways scroll at 390. D: the + card drawn off the deck, the field it
grows into (a press, a key typed), its send, its address by the tab and by *@*, a pasted picture, the large + card with
no goal; the deck's seal (the first goal's element) and moon, its row (the + card first, a drag, a pick, *All · search*
and the list over the pane); stacks by goal, the urgent first, a stop answered from its card, a stack fanned;
the discard's *n ready for main* and *To main* over the pane; a result opened and seen; one card size, the gem on a card that spends and its words only on the lifted card, none on one that does not; no part with nothing to hold; nothing moving under reduced motion. E: no top bar, left column,
drawer or dialog in the page; every place reached over the pane; the keyboard. The critical tests
(`tests/test_architecture.py`, `tests/test_board_alone.py`, `tests/test_updates.py`), each part's files' tests and the
touched browser tests.

## As built (A)

The desktop's page lost what §1's table says goes (67 files, about 3,500 lines; nothing under `pwa/` nor any host module). **Decided
here:** the pitch's Ctrl+Enter *judge* went with its button (a raw pitch is judged only by *Try again*: Ideation itself goes, §122.3);
the week's pace line keeps only *behind*; the limits' tip says *kept back*; `test_running_team_desktop_browser.py` keeps its two
recurring-goals tests (the feature stays). Left in place: words naming *tonight* in Settings' keep-awake lines and in a few comments,
`board.js`'s header naming *Agents*, the dead `TabMark` and `taskMark`. The desktop browser tests that asserted what went are cleaned
in a second commit.

## As built (B)

New `realm/goal_place.py` (`place_of`, read by `board_map.row`, so a node and a row agree) and `tests/test_goal_place.py`. Every node of
`ideas.map` and row of `ideas.board` carries `place` (`deck` · `hand` · `table` · `discard` · `history`), `asks_you`, `waits_as`
(`reset` · `held` · `line` · `""`, on a deck goal) and `seen`; today's `waits` dict and the row's `asks` count are as they were.
`ideas.seen {idea}` (`BoardMixin.seen`) writes `seen_at` once and records `result_seen`; it refuses a goal gone or not done.
`TERMS` gains the 14 words of §2.4. **Decided here:** a raw goal not in the queue `now` lies in the deck (`held`); `held_until` or a
plan's `start_at` is `reset`; `line` is a deck goal waiting on another (`waits_on`); a failed goal with no Needs you row lies in the
deck; pitches `sent`/`passed` are history; `ideas.board` reads the collision rows once and gives each goal its own, so a collision is
on its row as on its node.
