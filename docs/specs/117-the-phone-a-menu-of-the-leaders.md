# 117. The phone: a menu of the leaders from the crown, what is picked in the middle, the hand at the foot; the PWA first

Decisions §195. The owner, 31 October, on `docs/mockups/phone/sidebar.html`: A (the menu from the crown, not the row of
heads), and the top card answered with one tap. **Builds:** the cheaper model; the spec's author reviews · **Review:**
full · P1. **Waves** (parts in a wave share no file): **1** A and B; **2** C; **3** D.

**What it is, and is not:** the phone (a touch window, narrow or low: `frame/upright.js` `uprightNow`) gets the Board as a
menu: a party a row, its goals at work under it, the Orkmaster's goals at its head. What is picked lies in the middle (a
goal's way with its top card answered in place, or a party's leader), the hand's row at the foot, and the installed app
(the PWA) shows this page instead of its old face. Not: the desktop (unchanged, byte for byte: its screenshots before and
after are the same); a narrow window with a mouse (spec 94 §3's table, unchanged); a leader's map on the phone (§195.5);
the quick question on the phone (§181.8); the native frame (§174.4); the old face's removal (spec 94 E); a new command
or a new field in the snapshot (everything below is read from what the page has: `mapData`, `board`, `town`, `gateData`).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The PWA loads the page** | spec 94 §4 (D) as written there: `pwa/index.html` loads the page; `pwa/frame.js` the pairing, the worker, push, the arrival, the update; `gui/pwa.py` serves the page's files under `/app/`; the old face kept at `/app/old.html` until spec 94 E | `pwa/index.html`, new `pwa/old.html` (today's `index.html`), new `pwa/frame.js`, `pwa/sw.js`, `gui/pwa.py`, `gui/phone_http.py` if it must; `tests/test_pwa.py`, the `tests/test_pwa_*_browser.py` pointed at `old.html`, new `tests/test_pwa_frame_browser.py` |
| **B. The top row and the hand's row** | the crown (a button only, the menu is C), the potions as bottles, the die, the discard; the hand a row of the entries' upper parts with the + card at its right end; the picked entry's card in the middle with its answers (one tap); the arrows, the swipe, the fan of edges and the deck go | `js/hand/upright.js`, `js/hand/upright.css`, `js/hand/updeck.js`, `js/hand/upnav.js` (removed or cut to what stays), new `js/hand/uprow.js` (the hand's row), new `js/hand/uptop.js` (the top row); `tests/test_hand_context_narrow_browser.py` (rewritten to this) |
| **C. The menu** | the crown's menu: the project, *Settings*, *Stop all*; the Orkmaster's goals; each party with its sword and shield and its goals at work; a press picks and closes | new `js/hand/upmenu.js`, new `js/hand/upmenu.css` (or in `upright.css` if it stays under ~600 lines), `js/hand/uptop.js`; new `tests/test_phone_menu_browser.py` |
| **D. The middle** | a goal picked: its way (phases, route, why, its step's tasks) under its card; a party picked: its leader's header, its goals at work, its concerns; nothing picked and nothing in the hand: *Nothing waits for you.* | new `js/hand/uplook.js` (what is looked at, and its faces), `js/hand/upright.js`; new `tests/test_phone_look_browser.py` |

## 1. The words

No new concept, so nothing in `TERMS`. New lines: the crown's label **The leaders and their goals**; the menu's group
**Being talked about** under the Orkmaster; a goal's phase as the person reads it (**Talk**, **Spec**, **In line**,
**Work**, **Done**: `table/data.js` `PHASES`, *In line* for a goal of `lineNow`); a party's **Concerns**; a goal's
**<Party>'s tasks**; the die's line on a phone **Play it on the computer**. Kept: *Nothing waits for you.*, *New goal*,
*Stop all*, *Switch project*, *Settings*, the potions' words (`mana.js`), the cards' words. The interface says *goal* and
*party* (CLAUDE.md), never *idea* or *track*; the crown is the Orkmaster's, never called *menu* where a person reads it.

## 2. A. The PWA loads the page

As spec 94 §4 says, read with As built B (the paired link is built: `js/link.js` `pairWith`, `js/linkpaired.js`). In short:
1. `pwa/index.html` is the page's: orkUI's styles, the page's styles, the import map of `vendor/` as the desktop's page
   has it, `board.js` as the module, and `pwa/frame.js` before it. Today's `index.html` is kept as `pwa/old.html` (its
   `board-app.js` and the rest untouched), so the old face and its tests keep working until spec 94 E.
2. `pwa/frame.js` is what only a phone has, moved from `pwa/board-app.js` (it is not deleted, `old.html` still uses it):
   the pairing (the code from the QR or the link, `pairWith(device)`), the service worker's registration, push (the key, on,
   off, quiet), the arrival from a notification (it picks the goal it names: `frame/state.js` `picked`), the update's bar.
   It draws nothing of the Board.
3. `gui/pwa.py` serves under `/app/` the page's files the page imports (`board.js`, `js/**`, the page's CSS, `vendor/`
   and its licences, orkUI's copy), with the CSP as today's (`script-src 'self'`; no inline script: the import map is a
   file if a CSP forbids it inline). `sw.js`'s `CACHE` goes one up and its `SHELL` lists the page's files, so the app opens
   with no signal on the kept snapshot (spec 94 §2.4, `linkpaired.js` `kept`).
4. **Tests**: `tests/test_pwa.py` (the files served, their types, the CSP, `old.html` served); each `tests/test_pwa_*_browser.py`
   that loads `/app/` loads `/app/old.html` (one line each); new `tests/test_pwa_frame_browser.py`: `/app/` at 390 × 844
   with touch draws the page's upright hand from a paired snapshot (`route_web_socket`, as `test_link_paired_browser.py`),
   an answer goes as a command, and with the socket gone the kept snapshot is drawn with *As of …*.

## 3. B. The top row and the hand's row

The screen, from the top: the Orkmaster's line (`table/notice.js` `Notice`, as today), **the top row**, **the middle**
(it scrolls), **the hand's row**. Under `uprightNow` only.
1. **The top row** (`uptop.js`, 60 px): at its left **the crown** (the Orkmaster's crowned head, `orkui.js` `Head`, 44 × 44,
   `aria-label` *The leaders and their goals*, `aria-expanded`; in B a press does nothing yet); then **the potions**: each
   tool as the desktop's potion (`mana.js` `potionOf`, `framedOf`: its bottle by §192's four sizes at `.small`, its liquid
   the 5 hours, the default framed, its words on press as today), its mark small at its corner and its share under it, each
   a 44 px target, at most four, a fifth or the paid slot *+n* as `Tools` does; at the right **the die** (`playdie.js`
   `PlayDie` at a small size; on a phone a press says *Play it on the computer* as a line in the toast's place, nothing
   thrown) and **the discard** (`table/discard.js`: its top card small, 32 × 44; a press opens `DiscardView` over the pane;
   none while `hasDiscard()` is false). **…** goes from the top row (its rows move to the menu in C; until C lands they stay
   reachable from the crown: in B the crown opens `updeck.js` `More`'s menu).
2. **The hand's row** (`uprow.js`, 112 px, at the screen's foot over the home bar's safe area): one card an entry
   (`entries.js` `entriesOf`, unchanged: a goal's cards one entry, a card of no goal one, a goal ready for main one), each
   88 × 124 showing its upper part: its element, its name (three lines at most: `stopcard.js` `upName`), its window with the
   action's sign and its asker's head small in the corner (the alert's colour when it asks or failed). The row scrolls
   sideways; **the picked entry is raised 6 px with the ink's frame**; a press picks it (`entries.js` `at`). No count, no
   edges for a goal's other cards. **The + card** (`pluscard.js`'s face, the action's green, 64 × 90) lies at the row's right
   end, fixed, the row's cards passing under its left; a press opens the field over the keyboard as the deck did
   (`updeck.js` `DeckField`, the microphone in it). With no entry the row is the + card alone.
3. **The picked entry's card lies in the middle with its answers** (`stopcard.js` `Lifted` with `inline`, as today's top
   card; `readycard.js` `ReadyCard` for a goal ready for main), full width less the gutters, not turned; above it the
   context's lines that are not the goal's way (`context.js`: whose question, why, *Recommended*, what waits). **One tap
   answers** a question's choice as today. Answering an entry's last card picks the next entry (`placeOf`, as today).
4. **What goes**: the arrows and the swipe (`upnav.js` `Arrow`, `swipeOf`), the fan of edges (`Edges`), the deck
   (`updeck.js` `Deck`; `DeckField` stays), *Spec* under the context (`SpecButton`: the way is the middle's in D; until D
   lands it stays under the card).
5. **Tests** (`tests/test_hand_context_narrow_browser.py`, rewritten; Python Playwright, else the same checks with the
   preinstalled Node Playwright, said in As built): the order of the screen; the potions as bottles with their shares and
   the default framed; the die's line; the discard opens its view; the row draws every entry, the first picked and raised;
   a press on another picks it and its card is in the middle; one tap on a choice answers (the command sent) and the next
   card comes; the + card opens the field; the empty hand; the desktop at 1280 × 800 and the narrow window with a mouse
   unchanged (their screenshots byte for byte).

## 4. C. The menu

1. **The crown opens it** (`upmenu.js`): a sheet from the left, 312 px (at most 80% of the width), over a scrim
   (`--ork-scrim`); the scrim's press, Esc, the phone's back (one history entry while it is open) and any pick close it.
   Never an edge swipe. Focus goes into it and back to the crown.
2. **Its head** (60 px): the crowned head, the project's name with a chevron (a press opens *Switch project* over the pane),
   *Settings* (`sliders`) and *Stop all* (`boarded`, the danger colour, the tabs' own `halt` as `More` does): each 44 px,
   each with its words for a screen reader.
3. **The Orkmaster's goals**, under the label *Orkmaster · Being talked about*: the goals in Talk and in Spec
   (`table/data.js` `phaseOf` `talk` or `spec`) in the Board's order, then the goals in line (`lineNow`, the moon beside the
   name when `reset`). A row (40 px, indented to the heads' column): the element, the type's sign (`typeSignOf`), the short
   name, the phase's word at the right.
4. **Each party** (`partiesNow()`, the tabs' order; Release too): its leader's head, its name, its sword and shield as the
   desktop's tab draws them (`table/tabmarks.js`: the framed mark follows the default, the bare one is set, Lean's shield
   faint), then its goals at work (`laneOf(g)`, their nodes) as rows like 3, the phase's word *Work* (or *Checks* for a goal
   whose front task is `checking`). A party with no goal at work is its row alone.
5. **No count, no alert, no *waits for you*** anywhere in the menu (§195.1). The picked row (a goal or a party) has the
   ink's bar at its left and the panel's fill.
6. **A press** on a goal picks it (`frame/state.js` `picked`), on a party picks that party (`tab`, and `picked` emptied);
   the menu closes. On the head's rows as 2.
7. **Tests** (`tests/test_phone_menu_browser.py`): the crown opens and closes it (scrim, Esc, back); its groups in order
   with the stand-in Board's goals and parties; the sword and shield marks; no digit in any row's text but a goal's own
   name; a goal pressed is picked and the menu closed; *Stop all* sends `halt`; the desktop has no crown.

## 5. D. The middle

What is looked at (`uplook.js`): **a goal** when `picked` names one; **a party** when the person picked one in the menu
(`tab` a party's slug and `picked` empty); **else the picked entry's goal** (the hand's first, §195.2), and with no entry
**nothing**. The phone keeps no state of its own beyond what `frame/state.js` and `entries.js` hold.
1. **A goal**: its element (big), its short name in the body face (20 px), its type's sign and *<Type> · at work in
   <Party>* (or its phase's word); **its top card with its answers** (B.3) when it has an entry in the hand; then the phases
   (`PHASES`, the past ones muted, its own in the ink), its route (the parties of `routeParties` in its `route`'s order, each
   its leader's head and name: done with the check, the one at work turned, the next faint), why (its spec's *Why*, else
   the node's description, at most four lines), and **<Party>'s tasks**: the tasks of the step at work (`cascadeOf`), each its
   doer's head or its stage's sign, its name, its stage's word (`footWords`), a task that asks or failed in the alert's frame.
   A press on the phases opens the goal's page of that phase over the pane (what `SpecButton` did). A goal in line: its
   phases and why only, the moon and its hour when it waits for the reset.
2. **A party**: its leader's head (48 × 44), its name in the heading face and what it does in one line, its size's word;
   its squad grouped *Leads* | *Does* | *Checks* (`groupsOf`, the heads only; a head pressed opens its popover as on the
   desktop, `seatpop.js`, as a sheet); the tools of its sword and shield in words (`doesWords`, §192.4's words); its goals at
   work as the menu's rows (a press picks the goal); its **Concerns** (`table/concerns.js` `recordOf(party).concerns`: the
   alert sign, the line, what it is on in the caption), none when it has none.
3. **Nothing waits and nothing is picked**: *Nothing waits for you.* in the middle; the crown and the + card are the ways on.
4. **Tests** (`tests/test_phone_look_browser.py`): with a hand, the first entry's goal is looked at and its card is on it;
   a goal picked from the menu with no card shows its way alone; a party picked shows its header, squad and concerns; the
   phases' press opens the page; a goal in line shows the moon; the empty case.

## 6. Done when

The owner's phone, with the app added to its home screen from the paired link, opens on this page: the potions, the die and
the discard at the top, the goal of the first card in the middle with its question answered by one tap, the menu from the
crown with the leaders and their goals, a party's leader picked from it; the desktop unchanged. The critical tests pass
(CLAUDE.md) and each part's tests above; each part writes its *As built* here.

## As built B

Built in `orkboard/gui/static/js/hand/`: new `uptop.js` (the top row: `Top`, `Bottle`, `PaidBottle`, `Die`, `Pile`) and `uprow.js` (the hand's row: `Row`, `Entry`); `upright.js` and `upright.css` rewritten; `updeck.js` (`More` is the crown, `Deck` is gone, `DeckField` stays), `upnav.js` (cut to `SpecButton`), `entries.js` (`pickEntry`, `goalOfEntry`; `step` is gone), `mana.js` (`Tools`, `Tool`, `PaidTool` removed, `Who` exported), `stopcard.js` (`headOf` exported), `context.js` (`orkHeadOf` exported), and `table/menu.js` (`Menu` takes `face` and `own`, for the crown only). Tests: `tests/test_hand_context_narrow_browser.py` rewritten (27, run for real with Python Playwright 1.63: `pip install playwright==1.63.0`, `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`), and the two phone cases of `tests/test_mana_two_windows_browser.py` and `tests/test_play_die_browser.py` that met the old face. Looked at in 390×844 and 844×390 with touch. The desktop (1280×800) and the narrow window with a mouse (390×844) were drawn before and after in four scenarios (a question, two goals ready for main, a paid question, nothing): the eight screenshots are byte for byte the same.

What it is, and what differs from §3 or is not said there:

- **The screen**: `Notice`, `Top` (60 px), `.up-look` (the middle: the context, the card, *Spec*; it scrolls as a whole, so the context has no quarter-of-the-screen limit and no scroll of its own), `Row` (112 px, plus the home bar's safe area). The arrows, the swipe, the edges and the green deck are gone; `.up-stack`, `.up-nav*`, `.up-edge`, `.up-deck` are not in the page.
- **The crown** (`updeck.js` `More`): the Orkmaster's crowned head (`orkHeadOf`), 44 × 44 in a frame, `aria-label` *The leaders and their goals*, `aria-expanded`. Until C it opens the page's `Menu` (*Stop all*, the project's name over *Switch project*, *Settings*), its list anchored at the left. C replaces it with the sheet and takes `face` and `own` out of `Menu` again.
- **The potions** are `Bottle`s: `potionOf` and `framedOf` as the desktop's, `ork-potion small` in a 28 × 36 slot (so every bottle stands on its floor), the mark 12 × 12 at the corner, the now share under it (the warn and danger colours), 48 × 56. Places: four; a fifth tool or the paid slot makes *+n* (`PLACES_UP`). The default's frame is a class (`is-default`: the ink's border, the notch, the panel), not the sliding element of the desktop's potions: there is nothing to slide between on a phone. The paid slot shows orkUI's coins and *API*.
- **The die** is orkUI's `.ork-die` at two pixels a cell (`--_n: 2`, as the mockup sets it; orkUI has no small die of its own), turned by the lean token, grey when the project has no preview (`asleepNow`). `aria-label` and `title` *Play it on the computer*; a press toasts that line and does nothing else (no view, no throw, no command). The desktop's `PlayDie` is not drawn.
- **The discard** is `Pile` in `uptop.js`, not `table/discard.js` `Discard`: that one is sized by the table's card sheet. A back under, a top card 32 × 44 with the check in the success colour (with only goals ready for main, a back with the lich's head); `aria-label` the pile's words (*Done: <goal>. 2 goals ready for main*); a press opens `discard` over the pane, again closes it; none while `hasDiscard()` is false.
- **The row**: `Entry` is a `.ork-card.up-card` 88 × 124 clipped by the row's 112 px (the upper part shows: the window is cut at its middle, as in the mockup); the asker's head 16 × 15; the alert's colour for a card that asks and the danger's for one that failed; a goal ready for main shows its element, *<Goal> is ready for main*, the check and the lich. The picked card is raised 6 px with the ink's frame and kept in the row's clear part (`scrollLeft`). The + card is `PlusCard` at 64 × 90 with its seal of runes hidden (the circle is 136 px) and turned half the lean; the row's cards pass under it (`padding-right: 92px`). No count, no edge for a goal's other cards (a goal that asks two questions is one card, the second comes on the same card after the first is answered). A press is `pickEntry`: `at` and `picked`.
- **The card** in the middle is `Lifted` `inline` / `ReadyCard` in its place: `position: relative`, full width less the 8 px gutters (`--ork-4`, as the mockup's `.mid`), not turned, its height its content's. *Spec* (`SpecButton`) lies under it until D.
- **Not changed**: `picked` is still written by the hand when the entry on the screen changes (D replaces that); a push or the arrival from a notification still picks a goal; the field is `DeckField` (`.up-field`) as before.
- **On its side** (a low window) the row is 76 px and the top row 60: not in the spec, only so that the middle keeps room (390 − 136 px); the screen is otherwise the same.
- **Not done / to know**: no real phone and no real swipe sideways of the row (tested by `scrollLeft`); `tests/test_architecture.py::test_orkboard_starts_alone` needs the package installed (`pip install -e .`) where it runs, which is not B's. The other browser tests that load a touch window and read the hand (`test_hand_*`, `test_talk_*` …, spec 103's list) were not run again.

## As built C

Built in `orkboard/gui/static/js/hand/`: new `upmenu.js` (`Crown`, `Sheet`, `talkedOf`, `workOf`, `menuOpen`) and `upmenu.css` (loaded by `frame/frame.js`); `entries.js` (`pickGoal`, `pickParty`; `pickEntry` lets a party go), `uptop.js` (the crown is `upmenu.js` `Crown`), `upright.js` (draws `Sheet` with the entries), `updeck.js` (`More` is gone, the field stays), `upright.css` (the old **…** menu's rules out); `table/menu.js` is as it was before B (`face` and `own` are out again). Tests: new `tests/test_phone_menu_browser.py` (15, against the table's stub host with a goal in Talk and one in Spec added; `tests/test_hand_context_narrow_browser.py`'s crown test now only checks the crown and that it opens the sheet). Looked at in 390×844 with touch. The desktop and the narrow window with a mouse: the same eight screenshots as in B, byte for byte the same.

What it is, and what differs from §4 or is not said there:

- **The sheet** is `role="dialog" aria-modal="true"` named *The leaders and their goals*, `position: fixed`, 312 px (`min(312px, 80%)`), the whole height, over `.up-scrim` (`--ork-scrim`). The scrim's press, Esc and the phone's back close it. **One history entry while it is open**: `useSheet` pushes it on opening and a pick (or the scrim, or Esc) leaves through `history.back()`, **the thing the pick does comes after the back** (`close(then)`), so that the table's own entry (a *Settings* or *Switch project* opened over the pane pushes one) never meets this one. The focus goes to the first button and back to the crown; Tab turns round inside. No edge swipe (a mouse swipe from the left edge is tested to open nothing). No motion of its own.
- **Its head** (60 px): the crowned head, the project's name with a chevron (*Switch project: <name>*, over the pane), *Settings*, *Stop all* (`halt`, the danger colour, no confirm as the tabs' own has none; its `title` says *Stop every ork, script and browser at once*). Each button is 44 px.
- **The Orkmaster's goals** (`talkedOf`): the goals whose phase is Talk or Spec (`phaseOf`), in the Board's order, **not** those in line, done or at work in a party (so none is in two places), then `lineNow()`'s with the moon where `reset`; the label is *Orkmaster · Being talked about*, set at the heads' column (the indent of 44 px does not leave it room in 312 px). A goal row is 40 px: its element, the type's sign (`typeSignOf`), its short name, its phase at the right (*Talk*, *Spec*, *In line*; the sign's place is kept with none).
- **Each party** (`partiesAll()` in the Board's order, not `partiesNow()`: Release and Live are in it, on its side too): a 48 px row, its leader's head, its name, `Marks` of `tabmarks.js` in ink (the sword and shield, a Lean party's shield faint, the dot of a column on more than one tool); its words (*Tech · Does on Claude · Checks on Codex*) are the row's `aria-label` and `title`. Its goals at work are `laneOf(g)`'s in the lane's order, the phase *Work*, or *Checks* when the front task is a check (`stageOf`). No digit and no alert in any row (tested).
- **A press**: a goal is `pickGoal` (`picked` the goal, `tab` the Orkmaster's, and its entry in the hand, when it has one, is the one on the screen: `at`), a party is `pickParty` (`tab` its slug, `picked` emptied); the menu closes. A press on a card of the hand's row while a party is picked lets the party go. The picked row has `is-on` (the panel's fill, the ink's bar at its left) and `aria-current`. **Until D the middle does not look at a picked goal that has no card in the hand, nor at a party**: only the hand's card shows. And `picked` is still written by the hand when its card changes (B), so a goal picked in the menu that has no entry is replaced when the hand's card changes.
- **Not done / to know**: `openTab` keeps the party picked on this device (`orkboard.frame.tab`), as the tabs do; D must not show a party on a phone's start because of it. The sheet is not dragged shut and has no swipe. `tests/test_play_die_browser.py::test_a_start_is_thrown_rolls…` failed once under `-n 4` (a timing test of the desktop's throw) and passed alone; it is not touched by C.
