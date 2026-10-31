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

## As built A (the PWA loads the page)

Built in `orkboard/gui/pwa.py` (changed), `gui/static/pwa/index.html` (now the page's), `pwa/old.html` (new: today's `index.html`, untouched), `pwa/frame.js`, `pwa/frame.css` (new), `pwa/sw.js` (changed) and
`gui/static/js/linkpaired.js` (one line, below). `gui/phone_http.py` needed no change: it already hands every `pwa.wants(path)` to `pwa.serve`. Tests: `tests/test_pwa.py` (changed, three new),
`tests/test_board_alone.py` (the page's `/app/` check), `tests/test_pwa_frame_browser.py` (new, 7 tests, Python Playwright at `narrow.NARROW`); `tests/test_pwa_shell_browser.py` (the base of the old face's browser
tests) and `tests/test_board_browser.py` load `/app/old.html` (one line each; the other `test_pwa_*_browser.py` reach the app through the first). The old face (`board-app.js`, `shell-*.js`, `util.js`, `app.css`,
`party.css`) is untouched.

What it is, and what differs from §2 or is not said there:

- **The page's files are served under `/app/page/`, not `/app/`.** The old face has its own `pwa/board.js`, which `old.html` still loads as `/app/board.js`; the page's `board.js` would have taken its name. So `board.js`,
  `page.css`, `js/**` (every `.js` and `.css`) and `vendor/` (`*.mjs` and the licences; **no xterm**: its module, stylesheet and licence are left out) are served as `page/board.js`, `page/js/…`, `page/vendor/…`
  (`pwa.page_files()`, read from `gui/static/`, so the phone never has an older copy than the desktop). The modules link their sheets with `new URL("./x.css", import.meta.url)`, which resolves under `/app/page/js/…`, so
  nothing in the page changed. `roles.css` (the page's `ok-font-*` and `ok-tone-*`, which the desktop gets from `/roles.css`) is made from the tokens (`pwa.GENERATED`) and served as `/app/roles.css`.
- **`/ds/orkui/…` is served by the phone listener too.** The page's code names orkUI by an absolute address (`js/orkui.js` `ORKUI = "/ds/orkui"`: the heads, the marks, the pixel icons; `table/card.js`), which `/app/`
  does not cover, and the desktop is not to change. `pwa.wants` takes `/ds/orkui/` and `pwa.serve` answers it from the same files as `/app/<name>` (only orkUI's, `ds_files()`, never the app's own; `/ds/sprites/…`, a
  camp's, is a 404). The worker answers it too, keeping each file under its `/app/<name>` key.
- **More of orkUI is served than the old face needed.** `components.css` masks `signs/big/*.svg` (100 files), `potion/`, `runes/`, `tools/` and `backs/` by relative addresses, none of which `/app/` served (the first
  browser run showed `signs/big/bug.svg` as 404s). `ds_files()` now serves them; `tests/test_pwa.py` checks every `url()` of `components.css` is served.
- **CSP: the import map is allowed by its hash.** The page's import map has to be inline (an external one is not supported by browsers), so `script-src 'self' 'sha256-…'`: `pwa.csp(page)` hashes each
  `<script type="importmap">` of the file it serves and adds it. It works in the preinstalled Chromium (build 1243). No `unsafe-inline`, no other inline script (`test_pwa.py` checks the page has exactly one); `old.html`
  keeps the CSP as it was. The import map's addresses are relative (`./page/vendor/preact.mjs`, …). Styles stay `style-src 'self'`, and the page needed no inline style.
- **`sw.js`: `CACHE` is `orkcraft-app-v104`; the page's list is written in by `pwa.serve`.** The file keeps a `const PAGE = [];` and `serve` fills it with `pwa.page_shell()`: the page's files, `roles.css`, and orkUI's
  faces, heads, marks and pictures (about 490 files with the old face's `SHELL`, which stays for `old.html`, with `frame.js`, `frame.css` and `old.html` added). This differs from "list the page's files in `SHELL`": a new
  module under `js/` (B, C and D add five) needs no edit of the worker, and the worker's bytes change with the list, so a browser installs the new one. Install fetches `[...new Set([...SHELL, ...PAGE])]` past the HTTP
  cache, as before. Without orkUI's faces and pictures in the list the app offline lacked IBM Plex Sans (the old face did not use it), the heads and the bottles.
- **`frame.js`** (what only a phone has; it draws nothing of the Board, only its own cards): reads the address (`#pair=` the code, `#k=` an iOS Home Screen app's token, `#from=push-<tag>`), wipes it, registers
  `sw.js?app=board` (the same worker as `old.html`) and pairs as `board-app.js` did (`/api/version`, `/api/pair`; the cards *This phone is not paired with the board yet.*, *Pairing this phone*, *Paired: …* with the iOS
  `handOff`). **Paired, it calls `pairWith(device)` and only then `import("./page/board.js")`**, so the page's first `connect()` goes by the phone's socket; `linkpaired.js` keeps the old face's `localStorage` keys, so the two
  faces share one pairing. It draws: the pairing cards (`#phone`, over the page; `frame.css`, orkUI's tokens only); **a status line** (`#phone-status`, from `link.js` `offlineLine`: *As of 14:02. The board went
  away: trying again…*), since no face draws it yet (spec 94 B left it to "part C"); and the card *The board forgot this phone. Pair it again to use it.* over the page when `forgotten` is set (a code scanned while the app is
  open pairs again and the page starts anew). `frame.css` gives `body` the status bar's inset (`env(safe-area-inset-top)`: the installed app's bar is translucent) and makes `#app` the rest of the window; with nothing
  hidden the page's `[data-frame]` fills the window exactly (a test).
- **The arrival**: `#from=push-<tag>` (and the worker's `push-open` message when the app was open) logs `ideas.log {event: "opened", what: "push", ref: <tag>, device: "phone"}` once, as before, and a **`goal=<slug>`**
  (new: in the push's address, `./#goal=<slug>`) picks that goal in `frame/state.js` `picked` as soon as `mapData` names it. **No push names a goal yet** (`gui/phone_push.py` sends `./#needs` and `./`), so today an
  arrival only logs: the hand's first card is what the phone starts on anyway. Naming the goal in the push is left open.
- **Push**: `renewPush` runs on every socket open (the subscription sent again). Turning it on and off and the quiet hours are `pushOn`, `pushOff`, `pushQuiet`, offered to the page as
  **`globalThis.orkboardPhone.push`** (`state()`, `on()`, `off()`, `setQuiet(from, to)`) with **`orkboardPhone.unpair()`**. **Nothing in the page calls them yet**: the old face had a *This phone* row in its drawer
  for them, the page has none. Until a face (the crown's menu *Settings*, C) calls them, a phone paired on the new app cannot turn notifications on or unpair itself (it can still be forgotten on the computer, and
  `/app/old.html` has the rows). That row must also hide the computer-only rows by `can()` (spec 94 B's note).
- **The update**: none of its own. The computer's update is the page's (`js/shell/update.js` `UpdateAsk`, in `Board`): it reads `town.update` from the paired snapshot and sends `update.install`, which a phone may.
  The app's own files update by the worker (network first).
- **`js/linkpaired.js`: "Not connected to the town" is toasted once in ten seconds.** A page opened with no signal asks the Board's commands (`ideas.map`, `ideas.board`, …) one after another and showed five error
  toasts; the line over the page already says *As of …*. The paired link only; the desktop's link is unchanged.
- **`pwa.serve`'s `entry`** (the listener's host's script, Orkline's `app.js`) now applies to `old.html` and `index.html` alike; `index.html` has no `board-app.js` any more, so Orkline's frozen phone would need its own
  change (§121, later). The brand: `old.html` and the new `index.html` say the host's name as `index.html` did.

Tests: `tests/test_pwa.py` (the files served and their types; the page's files byte for byte from `gui/static/`, no xterm; `roles.css`; orkUI by `/ds/orkui/` and only orkUI's; every `url()` of `components.css` served;
the CSP with its one hash and no other inline script; the import map's addresses all served; every import of every served module resolves, the old test, now over the page too; the worker served with `PAGE` equal to the
page's files; `old.html` served; and over the real TLS listener `/app/page/board.js`, `/ds/orkui/…` and `/app/old.html`). `tests/test_pwa_frame_browser.py`: paired, the upright hand is drawn from the stub host's snapshot
over the phone's socket (`wss://…/ws`, `orkcraft.v1`, `bearer.<token>`) under the strict CSP with no console error, and *Passkey* pressed sends `ideas.talk_answer`; the frame adds nothing to the page's window; unpaired
says so, opens no socket and loads no page; a code in the address pairs and the page opens; a notification's arrival logs once and picks the goal it names; forgotten says so, keeps nothing and a new code pairs again;
the worker's cache holds every file it lists and, with the computer's files and socket both gone, the app opens from the cache on the kept snapshot with *As of …*, at most one "Not connected" toast and no console error.
Its stand-in for the listener is `pwa.serve` through Playwright's `route` (so the CSP header is the real one) and `route_web_socket`, as `test_link_paired_browser.py`; it looks for `[data-frame][data-upright]` and the
question's own words, not B's classes. Python Playwright 1.63 installed with pip and ran with the preinstalled Chromium (`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`); no Node run was needed.

Not done / untested:

- **No real phone.** Everything ran in Chromium (touch, `is_mobile`, 390 × 844). The worker's install on iOS Safari, the Home Screen app's `#k=` hand-off, `env(safe-area-inset-top)` under the translucent bar, the install's
  weight over Tailscale (about 490 small requests once per version) and push on a device are untried. A one-off run (not committed) of the page through the **real phone listener over TLS** (paired by the code; the
  page and its files from the listener, the worker in control) showed the page's start screen with the heads, no console error, and no request outside `/app/`, `/ds/` and `/api/`.
- **Offline, the Board is not kept**, only the snapshot (`linkpaired.js` `kept`, spec 94 B): the page's goals, cards and hand come from commands (`ideas.map`, `ideas.board`, …), so an app opened with no signal draws
  the potions (the snapshot's `mana`), the line *As of …* and an empty hand. Keeping `mapData` and `board` beside the snapshot is a change in `js/shell/store.js` and `linkpaired.js`, not A's.
- Nothing greys the page or marks what waits to be sent (*Sent when the computer answers*, `link.js` `waiting`): spec 94 C, still no face.
- The old face is served beside the page and shares its worker, so its files are in the install. Its removal (spec 94 E) takes `old.html`, `board-app.js`, the `shell-*.js`, the old `SHELL` entries and the `entry` line of
  `pwa.serve`.
- The old face's browser tests all ran against `old.html` (every `tests/test_pwa_*_browser.py`, `test_running_team_pwa_browser`, `test_gate_phone_browser`, `test_orkmaster_rows_91_phone_browser`, `test_board_browser`): green
  once the service worker's version pins (`orkcraft-app-v103` → `v104`, five files) and `test_pwa_new_party_91_browser`'s read of `index.html` (now `old.html`) were moved. They take about 55 minutes together.
