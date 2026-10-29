# Spec 94 — One page fitted to the width: the phone's app is its frame

The owner and the PM, 27 October (decisions §128): *after the first slice, one face for the desktop and the phone: one page
fitted to the width, the phone's app its frame.* **Builds:** Claude · **Review:** full · P1. **When:** §1 at once, as the
rule every spec of the first slice (§123.2) is written to, so nothing of it is built twice; §2–§5 after the owner's yes to
that slice (§128.2, §129.2), in their order. Until then the phone stays as it is.

**What it is, and is not:** the desktop's page (`static/board.js`, `js/shell`, `js/board`, `js/arena`) drawn at every
width, and the phone's app cut down to what only a phone has: its pairing, its cache, its push, its updates, and what it
keeps while there is no signal. Not: a new feature on either face; a change to what a phone may do (`gui/board_host.py`
`BoardPhone`: the Board's commands, Stop all, the projects' switcher, a Markdown file read; no terminal, no edit, no git,
spec 37 §8); a tablet's own layout (a wide tablet gets the wide one); Play on the phone beyond §113; Orkline's phone
(`app.js`), which follows later (§121).

| part | builds | files (and their tests) |
|---|---|---|
| **A. The rules, now** | §1 | the first slice's specs and faces; new `tests/narrow.py` (the narrow browser: 390 × 844, touch), which the slice's browser tests use |
| **B. The paired link** | §2 | `js/link.js` (one link, two ways: on the computer, paired), new `js/linkpaired.js` (the phone's protocol `orkcraft.v1`, the kept snapshot, the outbox; moved from `pwa/board-app.js` and `pwa/util.js`), `gui/board_host.py` (`phone_snapshot`), `gui/phones.py`; `tests/test_phones.py`, new `tests/test_link_paired_browser.py` |
| **C. The narrow width** | §3 | new `js/shell/narrow.js` (the width, the screens, the history), `js/shell/shell.js`, `js/shell/shell.css`, `js/shell/tabs.js`, the hand (`js/arena/stops.js`, `js/arena/stacks.js`), the blank card (`js/arena/newgoal.js`), the maps' sheets; every browser test of the page at both widths |
| **D. The frame** | §4 | `pwa/index.html` (the page's import map and styles), new `pwa/frame.js` (pairing, the worker, push, the arrival, the update: what `pwa/board-app.js` does today besides drawing), `pwa/sw.js` (`CACHE` one up, `SHELL` the page's files), `gui/pwa.py` (`files()`, the CSP); `tests/test_pwa.py` |
| **E. The phone's face removed** | §5 | `pwa/board-app.js`'s screens, `pwa/board.js`, `pwa/shell-*.js`, `pwa/app.css` and `pwa/party.css` (the frame's few lines kept); the `tests/test_pwa_*_browser.py` moved to the page at the narrow width, or removed with what they test; `tests/test_architecture.py` |

## 0. The words
The narrow width says what the wide one says: one wording, one place it is written. New: the blank card's **Send** (§3.6,
the narrow width only); the picking line **Pick a part to point at it** and **Stop picking** (§1.5, §140.4). Kept from the phone as they
are: *As of 14:02.* and its reason while the computer cannot be reached, and *Sent when the computer answers* on what the
outbox keeps. No new concept, so nothing new in `TERMS`; *narrow* and *wide* are the code's words, never the person's.

## 1. The rules every new face keeps, from the first slice on (A)
1. **Nothing only on hover, nothing only on a right click.** What a hover says today is said by a press too: a card's
   whole name (§104.2) on the lifted card; a member's description (§110.6) in its head's popover; a tab's party name when
   the tabs are heads (§110.3) in the pane's title; what a task waits for (spec 67 §3.2) on its lifted card. A tab's menu
   is its **…** (§110.3); the right click stays a shortcut to it.
2. **No fixed width a part of the window**: the table and the hand (§145.1) take their widths from orkUI's tokens
   and the window; a map lays its cards out in rows that wrap (spec 67 §1), never wider than the pane.
3. **A press is at least 44 × 44 px** under `pointer: coarse` (the visible thing may be smaller, its target is not).
4. **What opens is a screen's or a sheet's at the narrow width** (§3): a popover, a lifted card, what the pane opens (§142). A face
   is written once and told where it lies, never drawn twice.
5. **Picking a part for an idea is a mode the person sees** (§124.5 made precise; decided in §136.9).
   An idea addressed to a party (**→ Tech ×**) puts its party's view in picking only while the blank card holds the caret
   or its text: a line over the view says **Pick a part to point at it** and **Stop picking**. In picking, a press on a part
   (of System, a screen, a pain) **pins it** to the blank card as a mark (its name and ×) and never lifts it; with the
   mode off, a press lifts it as always (§120.1). **Stop picking**, Esc, sending the idea or taking off **→ Tech** ends it. On a
   touch screen there is no hover to tell the two presses apart, so the mode is always seen, at both widths. **A box**
   takes several cards (§152): on the desktop a drag from the table's empty place (Shift and a press for one), on a touch
   screen a long press then a drag, a drag alone still scrolling; a box that takes a whole group pins the group.
6. **Each browser test of the slice runs at both widths** (`tests/narrow.py`: 1280 × 800 and 390 × 844 with touch): no
   sideways scroll at 390, every press of §1.1 reaches what the hover showed.

## 2. One link, two ways (B)
1. **The page talks to the host through `js/link.js` alone** (today's `town`, `command`, `act`, `toast`, `connect`).
   `connect()` picks its way: **on the computer** the local socket with the page's token (today's); **paired** (the frame
   says so, §4) the phone's socket, `wss://…/ws` with the device's bearer and the protocol `orkcraft.v1` (`gui/phones.py`:
   `state`, a command and its `reply`, `news`), moved from `pwa/board-app.js` into `js/linkpaired.js`. The page's other
   modules never know which.
2. **What a phone may not do is not offered**: the paired link reads `mobile.hello`'s `commands` and a face whose
   command is not among them is not drawn (a terminal, the editor, git, Settings' computer-only rows, pairing a phone,
   the onboarding). Never a button that fails; `BoardPhone.allowed` stays the guard.
3. **The phone's snapshot is the page's**: `phone_snapshot` gives what the page reads (`snapshot()`'s Board, the
   projects, the limits, the update), less the computer's own (`onboarding`, the sign-ins' flows, `repo`'s path), with
   its `rev` as today. A view's own data is asked as on the computer (`ideas.*`, already allowed).
4. **No signal**: the last snapshot is kept on the phone and drawn greyed with *As of 14:02.* on the Orkmaster's tab
   (§145.6); an answer or an idea given meanwhile is kept (`outbox`) and sent when the computer answers,
   marked *Sent when the computer answers* in the hand. Both moved as they are from `pwa/util.js`.

## 3. The narrow width (C)
1. **One threshold, the window's width**: under 760 CSS px the page is narrow, whatever the device (a narrow desktop
   window is narrow too, so it is tried on the computer). `js/shell/narrow.js` keeps one signal of it; the sheets read
   the same width by a media query.
   VS Code's side bar is a narrow width too (§146.3). **A low window** (under 500 CSS px of height, 760 or more of
   width: a phone on its side) keeps the wide layout made compact, the hand a fan of overlapping cards (§150).
2. **One screen for two parts** (§145.1, §145.9): **the table** above (the row of heads, the pane's map) and **the
   hand** at the foot, with the deck at its left and the discard at its right (§145.3–§145.4). A goal is picked by its
   stack, a card of it on the table, or in the opened deck or discard (§145.5). A lifted card and what the pane opens over
   its map are screens of their own (§120.5, §142.7).
3. **Back is the browser's**: each screen is a history entry (`history.pushState`), so the phone's back gesture and
   button go back a screen, a lifted card lowered first. Reloading opens the screen it was on.
4. **The tabs are a row of heads** (§110.9: six at 44 px fit 390 px); the picked tab's party name in the pane's title.
   **A party's header is one line**: its name and the squad's heads (§134.3); a head pressed opens its popover as a
   sheet from the foot. Every tab is one map (§134.2, §135.1); *Play* stands alone in the pane's title (§136.3).
   **Stop all** stands at the end of the row of heads; the limits' chips are in the Orkmaster's **…** (§145.6).
5. **A map at the narrow width**: cards as spec 67's tokens (74 px, 5:7) in rows that wrap; System opens on its
   containers (§112.4), which are few; a container pressed opens its parts as the next screen. No sideways scroll.
   **The Board** at the narrow width keeps its columns under the row of heads, a head's width each, its tasks as tokens
   (§143.4).
6. **The hand at the foot**: spec 67's front card and fan; a card lifted from it is a sheet over the view it is about,
   its answers on it (§104.8). **The blank card** lies at the hand's left as on the wide width; pressed, it grows into a
   field over the keyboard (it rides `visualViewport`) with **Send** beside it: Enter writes a new line on a touch
   keyboard (`enterkeyhint="send"` on its key) and sends with a hardware one (§124.1). The microphone is the phone's
   dictation (§125.2). The foot keeps clear of the home bar (`env(safe-area-inset-bottom)`).
7. **What stays the computer's**: Play says *Play it on the computer* (§111.6) unless §113's phone play is allowed; a diff
   and a log opened over the pane (§142.2) are read, never edited.

## 4. The frame (D)
1. **`pwa/index.html` loads the page**: orkUI's styles, the page's styles, the import map of `vendor/` (Preact, its hooks,
   htm, signals; no xterm), and `frame.js`, which then imports `board.js`. The app's CSP stays `script-src 'self'`, the
   import map allowed by its hash (`gui/pwa.py` computes it from the file it serves).
2. **`pwa/frame.js` is what only a phone has**, moved from `pwa/board-app.js`: the pairing (the code from the QR, the
   device token, *This phone is not paired with the board yet.*), the worker's registration, push (`shell-push.js`'s
   renew and drop), the update (`shell-update.js`'s), and **the arrival**: opened from a notification (`#from=push-…`),
   it tells the page which hand card to lift. Then it tells `link.js` it is paired (§2.1).
3. **`gui/pwa.py` serves the page's files under `/app/`**: `board.js`, `js/**`, `vendor/`'s modules and their licences,
   beside today's; `sw.js`'s `SHELL` lists them (`CACHE` one up, `tests/test_pwa.py`'s pin with it).
4. Pairing, the listener, Tailscale and the certificates are unchanged (`gui/pairing.py`, `gui/phone_tls.py`,
   `gui/tailnet.py`).

## 5. The phone's face removed (E)
1. Once §2–§4 hold on the owner's phone, **the phone's own face goes**: `pwa/board.js`, every `pwa/shell-*.js`, the
   screens of `pwa/board-app.js` (what is left of it is `frame.js`), and `pwa/app.css` and `pwa/party.css` but the frame's
   own lines (the pairing card).
2. **Its tests move**: a `tests/test_pwa_*_browser.py` whose behaviour the page has becomes the page's test at the narrow
   width (`tests/narrow.py`); one whose behaviour went with §109–§131 goes with it. `tests/test_pwa.py` keeps the frame.
3. **`tests/test_architecture.py` keeps one face**: no module under `pwa/` but the frame's (`frame.js`, `sw.js`,
   `index.html`, the manifest, the icons) draws; a face is under `js/`.

## 6. Asked again later
Side by side on a wide tablet (§120.4); Orkline's phone on the same page (§121). A phone on its side is decided (§150).

## As built B (the paired link)

Built in `orkboard/gui/static/js/link.js` (changed), `js/linkpaired.js` (new), `gui/board_host.py` (`phone_snapshot`, `COMPUTER_ONLY`, `_phone_update`) and
`gui/phones.py` (`mobile.hello`). Tests: `tests/test_phones.py` (the snapshot's fields, `hello`'s commands), `tests/test_link_paired_browser.py` (new, both widths of
`tests/narrow.py`). Decisions §178.1 puts B–E before spec 103. The phone's old face (`pwa/board-app.js`, `pwa/util.js`, `pwa/shell-*.js`) is **untouched** and works on its own copy.

What it is, and what differs from §2 or is not said there:

- **`link.js` picks its way.** On the computer nothing changed. `pairWith(device)` (the frame calls it, §4.2; `device` is `{id, token, name}`, default the stored one) makes the link paired, and `connect()`, `command()` then go by
  `js/linkpaired.js`; it returns `{opened(fn), news(fn), close(), unpair()}` for the frame's push renewal and unpairing. `isPaired()` says which. New in `link.js` for every face: `deliver(name, args, label)`
  (on the computer a command; paired with no signal it is kept and sent later, `{ok, kept}`), `can(name)` and the signal `allowed`, `stale`, `offlineLine`, `waiting`, `forgotten`, and the constant `SENT_WHEN`.
- **`linkpaired.js`** is the phone's protocol moved: `wss://<host>/ws`, subprotocols `orkcraft.v1` and `bearer.<token>`, `state` into `town`, a command and its `reply`, `news` (a toast, the OS notification when the page is hidden,
  the vibration), reconnect with back-off (1 s doubling to 30 s) and on `visibilitychange`, a close with code 1008 = *forgotten* (the pairing, the kept snapshot and the outbox wiped, `forgotten` says *The board forgot this phone. Pair it again to use it.*).
  Its `kept` (the last snapshot), `outbox` (claimed before it is sent, restored if the signal goes again: never sent twice) and `store` are **copies** of `pwa/util.js`'s, on the **same `localStorage` keys** (`orkcraft.town`,
  `orkcraft.outbox`, `orkcraft.device`, `orkcraft.orkspace`), so the old face and the new share one pairing and one outbox while both exist; spec 94 E removes the old copy. Sent items are toasted *Sent: …* (the old *flash*).
- **What a phone may not do** (§2.2): `mobile.hello`'s `commands` was every command of the host; `phones.py` now answers it with **only those `BoardPhone.allowed`** (`files.read` counted: any `.md`). The paired link reads it once
  per socket into `allowed`; `can(name)` is true for everything on the computer. `BoardPhone.allowed` stays the guard. **No face hides anything yet** (not asked in B). Part C/E must use `can()` for: the **…**/Settings menu's computer-only rows
  (`js/settings.js`, `js/phones.js`: *Pair a phone*; `js/accounts.js`, `js/onboarding.js`, sign-in), the Files pane and its Git section (`js/shell` files/git places), the terminal and editor, `js/settings.js`'s writes (`settings.*`,
  `tools.*`), Play where `ideas.play` is not among them (§3.7), and the project switcher's *Open folder* (`projects.open`; only `projects.use` and `projects.list` are a phone's).
- **No signal** (§2.4): the last snapshot is drawn from the phone's storage at once (`stale` true, `offlineLine` *As of 14:02. Connecting…* / *The board went away: trying again…* / *Cannot reach the board: is it running, and Tailscale on?*;
  the clock is the phone's locale's); the first `state` clears both. The faces still have to **grey and make inert** what `stale` says and to draw `offlineLine` on the Orkmaster's tab (§145.6) and `waiting`'s items, each marked
  *Sent when the computer answers*, in the hand: that is part C. Nothing is drawn differently on the computer. A face gives an answer or an idea with `deliver()`; `command()` with no socket still rejects as `offline` (toast *Not connected to the town*).
- **`phone_snapshot`** (§2.3) is now `snapshot()` less `Orkboard.COMPUTER_ONLY` = `onboarding`, `sign_in`, `repo`, `usage_ask`, `update_policy`, plus the old phone's own fields (`v`, `project`, `look`, `sleep`, `version`, `hud`,
  `canvases_*`), with its `rev` as before. So it now carries **`projects`** (`projects.list`: the shown project, the open ones with their paths, the recent ones), **`mana`** (spec 105 B/D, `paid` among it), the `reserve`, `rate`, the Board's counts,
  `ops_rev`, `ops_team`, `focus`. `update` keeps `_phone_update`'s shape (the old bar reads it) with `critical_notes` added, which `js/shell/update.js` reads. The page's `sign_in` rows reach the phone as *Needs you* rows only (counted in `needs_you` as before).
  `repo`'s path is gone; the `projects` rows still hold the folders' paths (`projects.use` takes one) and `project` the shown folder's name. `tests/test_phones.py`'s old `"projects" not in first["state"]` is now its opposite.
- **Not done / to know**: the snapshot is bigger (the rev changes more often, e.g. with the projects' counts and the mana's `until`); `PUSH_S` still limits it to one push in 2 s. The page's other keys (`words`, `buildings`, `google`,
  `motions`, from Orkline) are not in an Orkboard snapshot on either way. `gui/board_host.py` is 688 lines (it was 684; over the 600 line rule before this part), and wants a split. **The Python browser test could not run here**
  (Playwright for Python is not installed, so `tests/test_link_paired_browser.py` skips); the same checks were run at both widths with the preinstalled Node Playwright against the real `phone_snapshot` and passed, so the file is untried as Python.
  The phone listener's TLS socket is not driven by the browser test (its stand-in is `route_web_socket`); `tests/test_phones.py` covers the listener with the real protocol.
