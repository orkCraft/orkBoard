---
owner: board
kind: idea
track: design
order: 16
size:
priority: normal
short: The readable look and the phone's feed
phase: work
route: design, tech
by: claude-code
schema: 3
gate: 13478e2 · 0 files · green
---
# The readable look and the phone's feed: Rubik, lifted colours, round corners; the phone's tables as a feed of blocks

## Gist
The person, 10 November 2026: «Как ты думаешь как дизайнер, учитывая что мы начинаем отходить от пиксельной графики, можем ли мы в
угоду читаемости и отображению на мобилах поменять шрифты, цвета и может быть форму/закругления карточек?» — «Мне больше всего
нравится Rubik». — «Ещё одно предложение для телефона, разбить текущие столы на зоны в виде блоков и сделать скролл этих блоков как
в соц сетях». — «Я согласен с твоими предложениями по картам. 1) в начале что ждет 2) сужает 3) давай в одну строку». — «В общем мне нравится, давай тогда по
твоим рекомендациям переделываем дизайн мобилы и десктопа (только имплементация на более простых моделях)».

## Why

## Done when

## Out

## Risks

## Depends on
Decision §291 (what was decided); the mockups `docs/mockups/readable-look/` and `docs/mockups/phone/feed.html` (v2). The look is
made in orkUI first, then copied here.

## Stages
- [ ] A0. The look in orkUI
  - party: Design (in orkUI, the person's answer: a pull request to orkUI, then copied). orkUI's pull request: Rubik (SIL OFL 1.1, 400 to 800, Latin and Cyrillic woff2) as the heading, button and text face, Pixelify gone from the headings and buttons, Plex Mono kept for code; the lifted colours of §291.2 (card `#33373a` framed `#4c5257`, panel, raised, frame, ink, read, muted, faint); the notch a round corner (card 10 px, button and chip 6 px, a picture's place 4–6 px, a card's top edge a faint light line); type tokens for desktop (body 15, caption 13, floor 12) and phone (body 17, caption 15, label 14, floor 14). The signs and runes stay pixel (§289.2). Orkboard waits for its merge; nothing here changes.
  - proves: none alone; it is what Design's first two *Done when* lines and Tech's last one need
- [ ] A. The copy, the fonts and the phone's cache
  - party: Tech (a simpler model). `python -m orkboard.design.orkui <orkUI>` from the merged commit: design-system/orkui stamped, nothing edited by hand; `gui/pwa.py` serves Rubik's woff2 from orkUI's fonts; `pwa/sw.js` a new `orkcraft-app-v` (after v106), Rubik's files precached and no pixelify-sans file; NOTICE says Rubik's licence; CLAUDE.md's line *The pixel face is for headings and buttons* changed as §291 says; tests that name Pixelify (test_pwa.py, test_pwa_board53_browser.py, test_pwa_pick_browser.py, test_hand_context_narrow_browser.py) say Rubik. Tests in tests/test_pwa.py (every precached path exists in static), tests/test_design_system.py.
  - proves: Tech's "When the service worker installs, then its cache is a new orkcraft-app-v, it precaches Rubik's files and no pixelify-sans file…"; Design's check "CLAUDE.md's line … is changed in the same pull request"
- [ ] B. The desktop's sizes to the tokens
  - party: Tech (a simpler model). The 10–11 px and the other own sizes in `orkboard/gui/static` (board.css, js/shell, js/board sheets; not pwa/) come to orkUI's type tokens; nothing under 12 px; a card's corner and a button's from the tokens; no layout moved (§273, §285). A browser test opens the Board on its first lane and reads the computed font family, the smallest size and a card's radius.
  - proves: Design's "When the desktop's Board opens on its first lane, then headings, buttons and text are Rubik (Plex Mono only for code, paths, ids), nothing under 12 px, a card's corner 10 px"
- [ ] C. The phone's sizes and colours to the tokens
  - party: Tech (a simpler model). pwa/app.css, party.css, frame.css: sizes to the phone's tokens (body 17, captions 15, labels 14, nothing under 14), cards on orkUI's lifted card and frame; a line that wraps or clips at 17 px fixed. tests/test_phone_look_browser.py at 390×844: the body's size, the smallest size, a card's ground and edge, and every visible word's contrast on its ground at 4.5:1 at least.
  - proves: Design's "When the phone opens a project at 390×844, then the body is 17 px, nothing is under 14 px, a card is #33373a framed #4c5257, and every word passes 4.5:1 on its ground"; Design's check that test_design_system finds no colour, font or corner of Orkboard's own
- [ ] D. Design accepts the look
  - party: Design. Pictures of the desktop's first lane and of the phone's project and goal at 390×844, beside the mockup `docs/mockups/readable-look/`; §226.5's check outdoors at the phone's own brightness where the person can; what it does not accept is one more stage of the look before E starts (Design's default, Tech's default).
  - proves: Design's first two *Done when* lines on pictures; Design's *Will be* (tokens.css copied, the notch gone)
- [ ] E. The feed's reader
  - party: Tech (the stronger model, the person's answer). New `orkboard/realm/board_feed.py` over board_recap's events and the Board's rows: what waits first (specs set to start at a clock time, read where the Board keeps them today; goals done and waiting for main), then each leader's posts since `since`, newest first, each with its leader (none in the event: the Orkmaster's) and its time; one leader's posts in a row one stack; what came before the look the one seen line, never news; cut to a route for a goal; no count anywhere. Served as `ideas.feed` in `gui/ideas_recap.py` beside `ideas.recap`, `since` as recap takes it. Tests in tests/test_board_feed.py; tests/test_architecture.py (imports nothing of gui/).
  - proves: Tech's "When realm/board_feed reads a Board with a spec set for a clock time, a goal waiting for main and two leaders' news since a look…", "When one leader has posts in a row since the look, then the reader gives them as one stack…"; Tech's checks on imports and no count
- [ ] F. The project's feed in the live upright page
  - party: Tech (the stronger model). The phone's live face is the desktop's page upright (`gui/static/js/hand/upright.js`, served through `pwa/frame.js`); `pwa/` (the old face at /app/old.html: board-app.js, shell-*.js, app.css) is left alone. New `js/hand/upfeed.js` and its sheet `js/hand/upfeed.css` (registered where frame.js lists the page's sheets; orkUI's tokens only, no colour, font or corner of its own). `uplook.js` draws the feed in place of the project's screen: with no goal picked (today's `none`, and the hand's first entry's goal no longer looked at by itself) the whole feed, the hand's row at the foot unchanged and no card of it raised; a card of the row pressed still picks its goal as today. upfeed asks `ideas.feed` with `{since}` (the page's `command`), again when the Board's snapshot changes; `since` is this device's own last look of this project, kept by `js/linkpaired.js` beside its pairing (a key of its own, wiped with the pairing as `kept` is; the same key in a narrow desktop window, which has no pairing), written when the person leaves the feed (a goal picked, the project switched, the page hidden), never on its first draw. It draws: the heads row on top (the reader's `heads`, the Orkmaster then the leaders, each a 44 px button, a ring with a sign beside it for news and the yellow ring with ! for asking, never a number, names 14 px); the waits first (`waits`, each with only its own `acts`, each act the command the reader names); the posts' stacks newest first, each its leader's head, name and time, *More from <leader>* opening the rest; a block of several goals laid as sideways cards with a button each way (44 px); the seen line *You have seen everything since <time>* with its small heads, pressed it spreads as a deck. A head pressed is `aria-pressed`, the others faint, a line says the feed shows only <leader>, the feed narrowed to its posts with its party's concerns and its goals at work above them (upparty.js's parts reused, the party's long header not drawn); pressed again the whole feed and no line. A party picked in the crown's menu opens the same narrowed feed (it replaces uplook's party look). The crown's menu (upmenu.js) stays as today: neither leader's section moved it. The word *feed* goes in `realm/lexicon.py` `TERMS`. uplook.js and upright.css do not grow; upfeed.js under ~600 lines. Browser tests in a new `tests/test_phone_feed_browser.py` at 390×844 on `UprightHost` (tests/test_hand_context_narrow_browser.py) with a fed `ideas.feed`; the cases of tests/test_phone_look_browser.py (85, 193, 229, 245, 257, 306) and tests/test_phone_menu_browser.py (345) that read the old project and party looks are rewritten for the feed, each named in the pull request as moved or gone, none in silence; tests/test_design_system.py, tests/test_gui_wording.py.
  - proves: Tech's "When the phone opens a project at 390×844, then it asks the host's feed with this phone's own last look and draws its blocks in the reader's order, with no tab of §223 in the page" (no `role=tab` in the hand: the live face has none); Design's "When the phone opens a project with a goal waiting for main and news since this phone's last look…", "When a person presses a head in the feed, then it is aria-pressed…"; Design's checks on keys (Tab walks the heads, the blocks and their arrows), on 44 px targets (the heads, a block's arrows) and on no count; Tech's checks on no count and on tests named moved or gone
- [ ] G. A goal's feed in uplook's goal screen
  - party: Tech (the stronger model). uplook.js's goal screen draws the same upfeed.js over `ideas.feed` with `{since, route: <the goal's slug>}`: under the goal's header, its card with its answers (when it has one in the hand) and its phases, which stay on top as today, the heads row is the route's leaders (the reader's `heads` for the route, in route order) in place of upway.js's route legs, then the goal's waits and posts in the reader's order; upway's Why and the step's Tasks stay under the feed as today (no leader's section moved them). A goal in line (no route yet) keeps its moon, its Waits and its Why as today. A head pressed narrows to that leader's posts as in F. uplook.js keeps no order of its own: every block's order is the reader's (the old face's shell-goal.js is not touched). The goal-screen cases of tests/test_phone_look_browser.py (85, 110, 130, 162, 276, 291, 319) are kept or rewritten for the feed, each named in the pull request when one moves; new cases in tests/test_phone_feed_browser.py.
  - proves: Tech's "When a goal's screen opens on the phone, then its feed is the same reader cut to the goal's route, its heads the route's leaders, and shell-goal.js holds no order of its own" (shown on the live face: uplook.js holds none, the order is `ideas.feed`'s with `route`)
- [ ] H. The folding header, the round button and the chain
  - party: Tech (the stronger model). In uptop.js the top row keeps the crown, the bottles, the lamp's chain (at its right beside the bottles, short at rest, pulled *Here* or *Away* as today: table/presence.js `PresenceChain`) and the discard's pile as today, and gains Stop all (`halt`, as the menu's, which stays; §292.3); its Die and its Backpack leave it. Scrolled, upfeed's heads row goes and the top row folds to one thin row with the bottles, Stop all and the chain, never covering the focused block (WCAG 2.4.11: the middle's `scroll-padding-top` the folded row's height). At the foot's right (§292.1) one round button, its face the die in its state (playdie.js `faceNow`, `asleepNow`), opening a selector of three rising over the foot: Play (the die: still says *Play it on the computer*, `PLAY_UP`), Inventory (the backpack: table/backpack.js's `openInventory`), History (the book: table/history.js `openHistory`), each a picture and its word, 44 px at least, no count; a second press, a tap outside or Esc closes it, focus back on the button. The + card moves to the foot's left (§292.2, feed.html v3; uprow.js's `sideOut` and the kept-in-view scroll read the + card at the left). Today's pictures stand (§292.5). The worker's cache name in `pwa/sw.js` a new `orkcraft-app-v` (after v107), its only change in pwa/. Browser tests in tests/test_phone_feed_browser.py (the fold, focus never covered, the selector's three by keys); tests/test_phone_menu_browser.py, tests/test_play_die_browser.py, tests/test_presence_chain_browser.py, tests/test_stall_browser.py and tests/test_hand_context_narrow_browser.py where they find the die, the backpack or the + card at their old places, each case moved or named gone in the pull request; tests/test_pwa.py.
  - proves: Design's "When the feed is scrolled to its foot at 390×844, then the header is one thin row with Stop all and the chain, a block's sideways cards have a button each way, the seen line spreads as a deck" (the test's half); Design's checks on keys walking the round button's three, on the folded header never covering the focused block and on 44 px targets (the round button, Play, Inventory, History)
- [ ] I. Design accepts the feed
  - party: Design. Pictures of each of the feed's states at 390×844 (top, a head pressed, a stack opened, the seen line spread, scrolled to the foot with the header folded, the round button open), beside `docs/mockups/phone/feed.html` v3.
  - proves: Design's [look] line and its last three [test] lines on pictures

## Open questions
- Where is orkUI's change made? (**A pull request to orkUI, then copied** / The person makes it in orkUI) — CLAUDE.md: the look is made in orkUI, never here; the copy waits for it · A pull request to orkUI, then copied: This goal opens orkUI's pull request; the copy waits for its merge · The person makes it in orkUI: This goal waits until a new orkUI is out to copy
  - Answered: A pull request to orkUI, then copied (the person, 2026-11-10)
- Seen since when, on the phone? (**Since this phone's last look** / Since the last look anywhere) — the desktop's past dot is already per browser (spec 150 E2.3); one rule for both · Since this phone's last look: Kept on the phone; news read on the desktop shows again · Since the last look anywhere: The host keeps it; read once, seen on every screen
  - Answered: Since this phone's last look (the person, 2026-11-10)
- Phone's tabs: gone at once, or kept? (**Gone in the feed's step** / Kept behind a setting a week) — alpha merges fast; two phone layouts double shell-project.js and its browser tests · Gone in the feed's step: One face; the tabs' browser tests are rewritten for the feed · Kept behind a setting a week: A way back while testers try it; two layouts kept and tested
  - Answered: Gone in the feed's step (decided by §291.5, 2026-11-10)
- Which stages go to simpler models? (**Look's copy and sizes; feed's reader stronger** / Every stage on simpler models) — sizes to tokens is wide but plain; the feed's order and narrowing is new logic · Look's copy and sizes; feed's reader stronger: The cheap, wide work goes cheap; the new reader gets a careful pass · Every stage on simpler models: Cheapest; the feed's order and its tests are more likely sent back
  - Answered: Look's copy and sizes; feed's reader stronger (the person, 2026-11-10)

## Decisions
- §291: Rubik, the colours a step lifted, round corners; the phone a feed of blocks, what waits first, a head narrows it, the seen
  in one line that spreads as a deck.
- §292: on a phone the die, the backpack and the book under one round button (its face the die in its state); the lamp's chain
  hangs from the header. The mockup: `docs/mockups/phone/feed.html` v3.

## Design
### Talk
- verdict: doubt — two reworks in one goal on simpler models: I go only if the look (orkUI, then its copy) is its own stage, accepted on pictures, before the phone's feed starts
- stance: Design keeps the look; Rubik, the lifted colours and round corners fix real reading faults, and the feed must keep the hand at the foot and a plain way back
- for: Fixes measured faults: Cyrillic misread in the pixel face, 37 sizes of 9–11 px in the sheets, card frames at 1.25:1; the feed puts what waits first (§291.6)
- against: The feed replaces §223's tabs; a sideways swipe with no button fails WCAG 2.5.1, a folding header can hide focus (2.4.11), a narrowed feed must say it is narrowed
- instead: The look first, on desktop and phone, accepted on pictures; then the feed as a second step on the new look, each of its states pictured
- assumes: Rubik and the lifted colours read better on a phone in daylight — shown by: §226.5's check, the new look opened outdoors at the phone's own brightness
### Why
- Pixelify misreads Cyrillic (*Пусть* as *Пуcтb*) and the sheets set 10–11 px under the tokens: a person's own words must read first.
- The card's frame at 1.25:1 hardly stands off the table on a phone at night; a step lifted keeps the warm room and is seen (§291.2).
- On a phone the tabs hide what waits behind a tap; one feed puts what waits first, the hand still at the foot (§291.5–6).
### Done when
- [test] When the desktop's Board opens on its first lane, then headings, buttons and text are Rubik (Plex Mono only for code, paths, ids), nothing under 12 px, a card's corner 10 px
- [test] When the phone opens a project at 390×844, then the body is 17 px, nothing is under 14 px, a card is #33373a framed #4c5257, and every word passes 4.5:1 on its ground
- [test] When the phone opens a project with a goal waiting for main and news since this phone's last look, then the heads row is on top, what waits comes first, news newest first, the hand at the foot, no tab
- [test] When a person presses a head in the feed, then it is aria-pressed, the others faint, a line says the feed shows only it; pressed again, the whole feed and no line
- [look] When the feed is scrolled to its foot at 390×844, then the header is one thin row with Stop all and the chain, a block's sideways cards have a button each way, the seen line spreads as a deck
### Checks
- `tests/test_design_system.py` still finds no colour, font or corner of Orkboard's own in `orkboard/gui/static`: all come from orkUI's copy, stamped
- Keys alone walk the feed, its heads and the round button's three; the folded header never covers the focused block (WCAG 2.4.11)
- Every target on the phone is 44 px at least: the heads, the round button, its Play, Inventory and History, a block's arrows
- No count anywhere: a head's ring has its sign beside it, the ! for asking (§291.9); the names under the heads are 14 px
- CLAUDE.md's line *The pixel face is for headings and buttons* is changed in the same pull request (§291)
### Will be
- changed design-system/orkui/tokens.css — Rubik, the lifted colours and round corners, copied from orkUI's merged pull request, the notch gone
### Out
- The signs and the runes: they stay pixel until the pictures decide them (§289.2)
- The cartoon objects (die, backpack, book, chain): today's pictures stand until the phone's are redrawn (§292.5)
- The desktop's layout: only its look changes; its places and chain stay where §273 and §285 put them
### Risks
- high
- The feed replaces §223's tabs in shell-project.js and shell-goal.js: many phone browser tests are rewritten at once, one may lose a case
- Sizes to tokens touch most of pwa/app.css: a layout that fit at 14 px may wrap or clip at 17 px
- Simpler models on the look's copy may leave a 10–11 px size or a notch behind that no picture shows
- A sideways-only card row would fail WCAG 2.5.1; a narrowed feed with no word would hide that it is narrowed
### Defaults
- The look is its own step, accepted on pictures of desktop and phone, before the feed's step starts (my Talk, the person's stage answer)
- Rubik's files are orkUI's copy, not the mockup's `fonts/`; the mockup stays the mockup's (§291.4)
- The 1.52:1 card frame is a card's edge, not a control's: WCAG 1.4.11 is checked on buttons and chips, not on the card
- The round button and the chain in the header (§292) are part of the feed's step, as feed.html v3 draws them
### Accepted
- met: When the desktop's Board opens on its first lane, then headings, buttons and text are Rubik (Plex Mono only for code, paths, ids), nothing under 12 px, a card's corner 10 px
- met: When the phone opens a project at 390×844, then the body is 17 px, nothing is under 14 px, a card is #33373a framed #4c5257, and every word passes 4.5:1 on its ground
- not met: When the phone opens a project with a goal waiting for main and news since this phone's last look, then the heads row is on top, what waits comes first, news newest first, the hand at the foot, no tab — stage F's, not in this step; nothing sent back
- not met: When a person presses a head in the feed, then it is aria-pressed, the others faint, a line says the feed shows only it; pressed again, the whole feed and no line — stage F's, not in this step; nothing sent back
- cannot see: When the feed is scrolled to its foot at 390×844, then the header is one thin row with Stop all and the chain, a block's sideways cards have a button each way, the seen line spreads as a deck

## Tech
### Talk
- verdict: doubt — go only if the feed's rules are a sheet of their own (pwa/app.css is 1457 lines) and its order comes from one host reader over board_recap, not a join in shell-project.js
- stance: Tech can build it: the look is orkUI's tokens copied (the sheets already take no font, colour or corner of their own); the feed is a new phone part on readers the host has
- for: test_design_system keeps every corner and font in orkUI; ideas.recap already answers "since the last look" per device; Pixelify's going removes a font from the shell
- against: The feed replaces §223's tabs in shell-project.js and shell-goal.js and their browser tests; sizes to tokens touch most of app.css, the phone's hotspot
- instead: The look first in its own step (orkUI copy, sizes to tokens); then the feed as pwa/shell-feed.js with feed.css, read from a realm reader the gate tests
- assumes: board_recap's rows carry a party and a time each, enough to post them by leader, newest first — shown by: board_recap.build's output over this repo's last week
### Why
- The look is orkUI's tokens copied: done right, no sheet of ours changes a colour, font or corner, and the phone's cache gets Rubik, not a stale Pixelify.
- The feed's order (what waits, then news by leader, newest first) is new logic: it belongs in one realm reader the gate tests, not in a join in shell-project.js.
- shell-project.js, shell-goal.js and pwa/app.css are the phone's hotspots; the feed goes in parts of its own so they shrink, not grow.
### Done when
- [test] When realm/board_feed reads a Board with a spec set for a clock time, a goal waiting for main and two leaders' news since a look, then waits come first, then posts newest first, each with its leader and time
- [test] When one leader has posts in a row since the look, then the reader gives them as one stack, and what came before the look as the one seen line, never as news
- [test] When the phone opens a project at 390×844, then it asks the host's feed with this phone's own last look and draws its blocks in the reader's order, with no tab of §223 in the page
- [test] When a goal's screen opens on the phone, then its feed is the same reader cut to the goal's route, its heads the route's leaders, and shell-goal.js holds no order of its own
- [test] When the service worker installs, then its cache is a new orkcraft-app-v, it precaches Rubik's files and no pixelify-sans file, and every path it precaches exists in static
### Checks
- tests/test_architecture.py: realm/board_feed imports nothing of gui/; no module of Orkline's imported
- Every new module under ~600 lines; the feed's rules in pwa/feed.css, and pwa/app.css, shell-project.js and shell-goal.js do not grow
- Each case of a removed tab browser test has its feed test or is named gone in the pull request, none dropped in silence
- The copy is made by `python -m orkboard.design.orkui` from orkUI's merged commit, its stamp in design-system/orkui, nothing edited by hand
- No count in the reader's output or the page: a head has news or asks, never a number (§291.9)
### Will be
- new orkboard/realm/board_feed.py — the phone's feed as data (waits, then each leader's posts since the look, stacks, the seen line), drawn by pwa/shell-feed.js
### Out
- orkUI's own pull request: it is made in orkUI; Tech copies it here and changes no token
- A last look shared between screens: the person kept it per phone; the desktop's recap and its past dot are unchanged
- The desktop's layout and the VS Code frame: only the copied tokens reach them
### Risks
- high
- Many phone browser tests are rewritten at once and alpha merges on the critical tests only: a lost case may show only in the full CI after the merge
- A precache path that does not exist fails the service worker's install: the phone stays on the old look
- board_recap's events may carry no leader for older lines: posts fall to the Orkmaster and the heads' rings read wrong
- Sizes to tokens across app.css may wrap or clip a 17 px layout no test sizes
### Defaults
- The reader is realm/board_feed.py over board_recap's events, served as `ideas.feed` beside `ideas.recap`; the phone draws it in pwa/shell-feed.js with pwa/feed.css
- The last look stays in the phone's orkcraft.v1 and is sent as `since`, as `ideas.recap` takes it today
- A post with no party in its event is the Orkmaster's; a spec's clock time is read where the Board keeps it today
- The look's step (copy, sizes, sw cache) lands and is accepted before the feed's step starts
### Accepted
- not met: When realm/board_feed reads a Board with a spec set for a clock time, a goal waiting for main and two leaders' news since a look, then waits come first, then posts newest first, each with its leader and time — stage E's, not in this step; nothing sent back
- not met: When one leader has posts in a row since the look, then the reader gives them as one stack, and what came before the look as the one seen line, never as news — stage E's, not in this step; nothing sent back
- not met: When the phone opens a project at 390×844, then it asks the host's feed with this phone's own last look and draws its blocks in the reader's order, with no tab of §223 in the page — stage F's, not in this step; nothing sent back
- not met: When a goal's screen opens on the phone, then its feed is the same reader cut to the goal's route, its heads the route's leaders, and shell-goal.js holds no order of its own — stage G's, not in this step; nothing sent back
- met: When the service worker installs, then its cache is a new orkcraft-app-v, it precaches Rubik's files and no pixelify-sans file, and every path it precaches exists in static
