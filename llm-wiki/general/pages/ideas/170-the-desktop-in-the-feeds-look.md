---
owner: board
kind: idea
track: design
order: 17
size:
priority: normal
short: The desktop in the feed's look
phase: work
route: design, tech
by: claude-code
schema: 3
---
# The desktop in the phone feed's look: every card a post, the Orkmaster's lane and the discard as drawn

## Gist
The person, 10 November 2026, on the desktop drawn in the phone feed's look (`docs/mockups/desktop-look/`): «В целом стиль мне
нравится, в особенности левая колонка и правый сброс давай возьмем адаптацию и десктопа в работу на моделях попроще». Earlier, on
the phone's feed mockup: «Мне очень понравился макет, надо ориентироваться на него». Then, sending the chairs and a sheet of
a back for each race's leader (`docs/mockups/table-template/objects/cartoon/sheets/o3b-chairs.jpg`, `o3c-leaders-backs.jpg`): «Стулья
давай оставим» and «Я ещё добавил разные стили спинок для лидеров». On the tabs: «Да, все верно - десктоп со стульями, мобила с кольцами».

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
- [x] A0. The places' and the chairs' cartoon takes in orkUI
  - party: Design (in orkUI, §290.1, the person's answer: a pull request to orkUI, then copied; runs beside A to F, nothing here waits on it until H). orkUI's own tool (`races/art/`, its `sheets.json`) cuts the takes of `docs/mockups/table-template/objects/cartoon/sheets/`: `o2b-die-2.jpg` (the die at rest, tumbling), `o3a-backpack-book-2.jpg` (the backpack shut and open, the book shut and open), `o4-chain-2.jpg` (the chain at rest, pulled), `o3b-chairs.jpg` (the back, the open leader's grander back, the empty chair, pulled out, simplified for 18 px; tile 5, the new party's chair, waits for its retake as `docs/pictures-cartoon.md` says, and the empty chair of tile 3 stands for it until then), `o3c-leaders-backs.jpg` (a back for each race's leader, the middle plain for the head; the gnomes' glyphs taken as runes). Into orkUI's `die/`, `backpack`/`book/`, `chain/` and `chair/` beside today's pictures, each named in its json with its state, the grey ground and frames cut away, a light rim kept. The mockup's sheets stay the mockup's. Nothing in Orkboard changes.
  - proves: none alone; it is what Design's fourth *Done when* line (the places' picture) and its check *the places' pictures come from design-system/orkui* need
- [x] A. The one post: js/table/post.js and post.css
  - party: Tech (a simpler model). If goal 169's stage F has landed `orkboard/gui/static/js/table/post.js` on main, take it and add only what the desktop needs, never changing how the phone draws it; if not, build it here first and 169 F imports it (the person's answer), its branch rebased on this one. A Preact component like the rest of js/table that takes a post's data and an act callback only: round (orkUI's card radius), the lifted card ground, its party's colour as its top edge, a head row (the leader's round head, its name in the heading face, *when* under it, *···* at its right as a button with its word), the post's own acts only, each a button with its word reached by Tab with a visible focus; a post that asks ringed in the alert's yellow with a sign beside the ring (§291.9); the labels NEW, CHANGED at 12 px caption at least in the heading face (not the mockup's 11 px `.chg .k`); a quiet post told by its muted ink and a *Quiet* plate, never by opacity (not the mockup's `.card.dim` .55). It imports none of frame/state, shell/store or pwa/, so the phone reaches it as `./page/js/table/post.js`. `post.css` (registered where the page's sheets are listed) carries orkUI's tokens only. Tests: a new tests/test_post_browser.py drawing a post on the desktop page and through the phone's `./page/` path (one test of a post, both faces); tests/test_architecture.py (post.js's imports), tests/test_design_system.py, tests/test_gui_wording.py.
  - proves: Tech's "When the Board opens on the desktop, then every post … is drawn by js/table/post.js, which imports none of frame/state, shell/store or pwa/" (the part's half); Tech's check *post.js takes a post's data and an act callback only*; Design's check *one test of a post covers both faces*; Design's defaults on the quiet card and the labels
- [x] B. The discard as drawn
  - party: Tech (a simpler model). discard.js, piles.js, plates.js and lane.js keep their parts and change their look (§293.4): under the head (the potions, *Stop all*, the lamp's chain at the right edge lit *Here*, `table/presence.js` as today) the plate *main* (*done in dev · waits for main*) over its cards, the one ready for main ringed by the portal with *To main*, then the plate *dev* (*done · waits for dev*) over its cards; each card a post drawn by post.js, its acts the ones it had, To main sending the command it sent before. No count on a plate. discard.css on orkUI's tokens only. Tests: tests/test_discard_piles_browser.py, tests/test_discard_table_browser.py rewritten for the posts, each removed case naming the case that now holds its act.
  - proves: Design's "When the discard opens with a goal done in dev and one ready for main, then the head (potions, Stop all, the chain lit Here) is over plate main with its ready post ringed and To main, then plate dev" (the places' half in H); Tech's "… a goal to review and one ready for main, then each post carries its act (… To main) …" (To main's part)
- [x] C. The leaders' tabs as rings, on their chairs
  - party: Tech (a simpler model). tabs.js, tabmarks.js and table.css (§293.5): a tab's head ringed in its party's colour, a dot in that colour beside it for news, a yellow **!** when it asks, its name and its line under it (§275), never a number; the ring never alone (a sign beside it says the news, the ! the asking). The chairs stay (the person: «Стулья давай оставим»): each head still stands on its chair's back at the wide width (`Sit`, orkUI's `Chair`), the open leader's grander back; New party's empty chair (chairs.js) and its acts as today. Tests: tests/test_table_look_browser.py and tests/test_table_desktop_browser.py where they read a tab's marks, moved to the rings.
  - proves: Design's third *Done when* line's tab part ("its tab ringed, a dot or a yellow !, no number"); Design's check *No count anywhere: tabs …*
- [x] M. The page on mocks (the person, 11 November 2026: «сделать кликабельную максимально близкую версию к реальной … потыкать весь новый интерфейс и потом уже дописывать бизнес логику»)
  - party: Tech. `?mock=1` opens the real page with no host: js/link.js opens no socket and js/mock/mocklink.js answers from `static/mock/board.json`, recorded from a real host on this repository (tools/record_mock.py); a change it does not hold is kept, said once, never sent; a plate says so (js/mock/plate.js). tools/serve_mock.py serves the page with no host. What the host does not answer yet (tokens, a card's cost, a framework's entities) the recording's `proposed` part holds, as the contract the host is to answer. Tests: tests/test_mock_link_browser.py.
  - proves: the new faces (D to F, and the spreads and the leaders' tables of the talk of 11 November) can be drawn and pressed on real data before the host answers them
- [ ] T. The table of cards on mocks (the talk of 11 November 2026: one card ratio, three sizes; docs/mockups/table-cards/)
  - party: Tech. `js/cards/`, drawn on mocks and with `?table=cards` (cards/on.js), the table as it is otherwise until the decisions on the cards are written: S a goal upright (card.js `CardS`, its rune and kind in its corners, its bar, its leaders' tokens), M a leader's word on its side (`CardM`, table/post.js's head and body), L a card opened over the table (`CardL`, Esc or Close), the token (`Token`); the leaders' lanes from `ideas.feed` (lanes.js, in table/pane.js instead of the map), the Orkmaster's lane as the dealer's (dealer.js, in table/column.js's scroll: waits, the deck, at work). Done so far: these; still to come: the discard and the hand as S cards, the spreads, the leaders' tables, the phone.
  - proves: the person can press the table of cards on this repository's own Board before the host answers tokens and costs
- [ ] D. The Orkmaster's lane as drawn
  - party: Tech (a simpler model). column.js, column.css and fan.js (§293.2, §206): *Waits for you* first (a spec that starts by itself at a clock time: its clock row, its bar and its acts; a goal to review with its Hold and Back to review, each sending the command it sent before), then *Goals* (the fan, *Being read: <goal>*), then *At work* (each goal at work a post with its live bar in its party's colour, pressed it opens its plan as today); whole cards drawn by post.js, pinned, no list, no count. What waits is read from `ideas.feed`'s `waits` (asked once a refresh by the page, Tech's default; no new host command) and the Board's rows the page already has; column.js sorts none of it. column.js stays under ~600 lines. Tests: tests/test_column_browser.py, tests/test_column_fan_browser.py, tests/test_card_life_browser.py where they read the piles, rewritten for the three parts, each removed case naming the one that holds its act.
  - proves: Design's "When the Board opens with a spec that starts by itself at a clock time and a goal at work, then the Orkmaster's lane reads Waits for you, Goals (the fan, Being read), At work, whole cards, no list, no count"; Tech's "… a goal to review …, then each post carries its act (Hold, Back to review …) and pressing it sends the command it sent before" (Hold's and Back to review's part)
- [ ] E. A leader's lane on ideas.feed
  - party: Tech (a simpler model). A new `js/table/feedlane.js` (with its sheet, orkUI's tokens only) draws each leader's lane from the one `ideas.feed` answer of D's refresh, cut by leader in the page (no `leader` argument to the host, Tech's default), in the feed's order: what it asks first, then *New since your last look · <time>* newest first, one leader's posts in a row one stack with *More from <leader>* (a button with its word), what was seen one line *Seen since <when>* with its heads small that spreads pressed (§291.8, §293.3); every post by post.js; `since` the desktop's last look as `ideas.recap` takes it today. boardmap.js no longer draws a lane and sorts nothing. Tests: a new tests/test_feed_lane_browser.py on a fed `ideas.feed` with posts by two leaders since the last look.
  - proves: Design's "When a leader's lane opens with news since the last look, then its ask is first, then New since <time> newest first, a leader's posts in a row one stack with More from <leader>, the seen one line that spreads pressed" (the lane's part); Tech's "When the Board opens with posts by two leaders since the last look, then each leader's lane holds ideas.feed's posts of its leader in the feed's order, and column.js and boardmap.js sort none"; Tech's check *No new host command*
- [ ] F. A goal at work a post; the cascades leave the lanes
  - party: Tech (a simpler model). In a leader's lane a goal at work is one post with its live bar (the person's answer), pressed it opens its plan as today; pane.js stops drawing `BoardMap`'s lanes, cascade.js is imported only by a goal's plan screen (or gone where nothing imports it), card.js's `TaskCard`/`OwnCard` drawn inside post.js where they stay. card.js and boardmap.js shrink, not grow. The browser tests that read the cascades in the lanes (tests/test_cascade_card_browser.py, tests/test_table_desktop_browser.py, tests/test_window_desktop_browser.py, tests/test_stage_tables_browser.py, tests/test_task_steps_browser.py, tests/test_pass_on_browser.py, tests/test_hand_desktop_browser.py, tests/test_history_browser.py where they do) moved to the posts or to the plan screen, each removed case named in the pull request with the case that now holds its act, none loosened in silence.
  - proves: Tech's "When the Board opens with a goal at work, then no lane draws cascade.js's blocks; the goal is one post with its live bar, and pressing it opens its plan as today"; Tech's first *Done when* line whole (every post in the lanes and the discard by post.js); Design's first *Done when* line; Tech's checks on removed tests and on cascade.js and boardmap.js
- [ ] G. The sizes, the contrast and the fit at 1280 and 1440 px
  - party: Tech (a simpler model). A new tests/test_desktop_look_browser.py opens the Board at 1280×800 and 1440×900 with a goal that asks, a quiet lane, news, a goal at work and both discard piles: no text under 12 px, every text (a quiet post's too) at 4.5:1 on its ground, no post's act nor the chain's *Here* clipped, every act on a post a button with its word reached by Tab with a visible focus. What fails is fixed in post.css, feedlane's sheet, column.css or discard.css with orkUI's tokens only; a lane too narrow for its acts at 1280 wraps its acts, never hides one. The gate on the step: test_architecture, test_board_alone, test_updates, and no touched module past 600 lines.
  - proves: Design's "When the Board opens at 1280 and 1440 px, then no text is under 12 px, every text and a quiet card's too meets 4.5:1 on its ground, and no card's act nor the chain's Here is clipped"; Tech's "When the gate runs on the step, then test_architecture, test_board_alone and test_updates are green and no module the step touched passes 600 lines"; Design's check on keys and focus
- [ ] H. The cartoon places and chairs copied
  - party: Tech (a simpler model), after A0's merge in orkUI. `python -m orkboard.design.orkui <orkUI>` from the merged commit, nothing edited by hand; the places at the hand's right end (hand/hand.js, hand/places.css: the die lit when something can be run, §223.7; the backpack; the book) each its cartoon picture and its word; the lamp's chain in the discard's head (table/presence.js) and the chairs (orkui.js `Chair`: each race's leader's back from O3c, the open leader's grander back, the empty chair) in the cartoon; the phone's places under its round button take the same pictures (§293 changes 292.5). If a precached picture changes, `pwa/sw.js` a new `orkcraft-app-v`. Until the copy lands, today's pictures stand (Design's default). Tests: tests/test_design_system.py (the pictures come from design-system/orkui), tests/test_pwa.py (every precached path exists), tests/test_play_die_browser.py and tests/test_presence_chain_browser.py where they read a picture.
  - proves: Design's fourth *Done when* line's places part ("the places show their picture and word"); Design's check *the places' pictures come from design-system/orkui*
- [ ] I. Tech accepts the step
  - party: Tech. Its pass of its own (its role file, its section, the gate's record of A to H, the files they changed), against its *Done when* and *Will be* (post.js the one post column.js, card.js and boardmap.js call); what it does not accept is one more stage, twice at most.
  - proves: Tech's *Done when* and *Will be*, accepted
- [ ] J. Design accepts on pictures
  - party: Design. Pictures of the Board at 1280 and 1440 px (the Orkmaster's lane, a leader's lane with news and a stack, the seen line spread, the discard's two plates, the tabs' rings, the places) laid beside `docs/mockups/desktop-look/desktop-look.png`, the frame unchanged (§104.0, §145, §273, §285); what it does not accept is one more stage, twice at most.
  - proves: Design's *Done when* lines on pictures and its checks; Design's *Will be* (the table's cards posts, the lanes, the tabs and the discard as drawn in §293, a goal's cascades gone from the lanes)

## Open questions
- Places' cartoon pictures: from where? (**Into orkUI first, then copied** / The mockup's feed-pics copied / Today's pictures until retaken) — CLAUDE.md: the pictures are orkUI's own; O2b, O3a and O4 are marked to be taken again · Into orkUI first, then copied: One source for both faces; the places wait for orkUI's merge · The mockup's feed-pics copied: Fastest; a picture outside orkUI that the phone does not share · Today's pictures until retaken: The cards change now; the die, backpack, book and chain later
  - Answered: Into orkUI first, then copied (decided by §290.1, 2026-11-10)
- A party's lane: posts or its cascades? (**Posts; a goal at work a post** / Posts above its goals' cascades / Cascades kept; posts on its tab) — §293.3 draws posts, yet §143's lanes of cascades (boardmap.js) are not in its Changes · Posts; a goal at work a post: As drawn; cascade.js leaves the Board, a picked goal's plan stays · Posts above its goals' cascades: Both kept; a lane grows long, two orders in one lane · Cascades kept; posts on its tab: The Board's lanes unchanged; the posts only through a leader's eyes
  - Answered: Posts; a goal at work a post (the person, 2026-11-10)
- One post part for both faces? (**One post.js, the phone's feed reuses it** / The desktop waits for 169's upfeed.js / Each face draws its own) — 169's stage F (upfeed.js) has not landed; two drawers of one post drift on simpler models · One post.js, the phone's feed reuses it: The desktop goes now; 169 F imports it, one test of a post · The desktop waits for 169's upfeed.js: One drawer; this goal waits for 169 F to land · Each face draws its own: Fastest now; two posts to keep alike, twice the tests
  - Answered: One post.js, the phone's feed reuses it (the person, 2026-11-10)

## Decisions
- §293: the desktop in the feed's look (every card a post; the Orkmaster's lane and the discard as drawn; the leaders' tabs as rings;
  the places in the cartoon takes). Built on goal 169's look (§291, orkUI 0.40.1).
- §294: the desktop's tabs stand on their race's chair backs with a sign beside the head, no ring; the phone keeps the rings.

## Design
### Talk
- verdict: doubt — go only after 169's feed reader (stage E) lands, so the lanes' *New since* order is the phone's, and with the mockup's 11 px labels and 55% faded quiet card fixed
- stance: Design wants it: one card as a post on both faces, the asks ringed and first; the mockup's faults must not be built as drawn, and simpler models need pictures per lane to be held to it
- for: The person liked the left lane and the discard; what waits first and asks ringed in yellow put the person's next act in sight (Nielsen 1, 6); one post shape for phone and desktop (4)
- against: The mockup's `.chg .k` is 11 px (§291.1's floor 12) and `.card.dim` at .55 opacity drops a quiet lane's words under 4.5:1 (WCAG 1.4.3); the chain's *Here* is clipped at the right edge
- instead: Every card a post and the discard as drawn first; the leaders' lanes' *New since* order when 169's reader is merged; the places' pictures when orkUI has them
- assumes: Five leaders' lanes of posts at body 15 fit a 1440 px window without clipping a card's acts — shown by: pictures of the Board at 1280 and 1440 px beside the mockup
### Why
- One card shape on both faces: a post reads the same on the phone and the desktop, so the person learns it once (Nielsen 4).
- What waits for the person first and the asks ringed put the next act in sight (Nielsen 1, 6); the mockup's small and faded words must not come with it (WCAG 1.4.3).
### Done when
- [test] When the Board opens on the desktop at 1440 px with a goal that asks, then every card in the lanes and the discard is a post drawn by one post.js (round, its party's top edge, round head, name, when, ···), the asking one ringed in yellow
- [test] When the Board opens with a spec that starts by itself at a clock time and a goal at work, then the Orkmaster's lane reads Waits for you, Goals (the fan, Being read), At work, whole cards, no list, no count
- [test] When a leader's lane opens with news since the last look, then its ask is first, then New since <time> newest first, a leader's posts in a row one stack with More from <leader>, the seen one line that spreads pressed; its tab ringed, a dot or a yellow !, no number
- [test] When the discard opens with a goal done in dev and one ready for main, then the head (potions, Stop all, the chain lit Here) is over plate main with its ready post ringed and To main, then plate dev; the places show their picture and word
- [test] When the Board opens at 1280 and 1440 px, then no text is under 12 px, every text and a quiet card's too meets 4.5:1 on its ground, and no card's act nor the chain's Here is clipped
### Checks
- Pictures of the Board at 1280 and 1440 px laid beside `docs/mockups/desktop-look/desktop-look.png`, the frame unchanged (§104.0, §145, §273, §285)
- The phone's feed and the desktop draw a post from the same post.js, and one test of a post covers both faces
- No colour, font, corner or size in Orkboard's sheets outside orkUI's tokens (`tests/test_design_system.py`); the places' pictures come from `design-system/orkui`
- Every act on a post is a button with its word, 44 px on the phone, reached by Tab with a visible focus; the ring and the ! never alone (§291.9)
- No count anywhere: tabs, plates, the Orkmaster's lane and Seen since carry no number (§223, §291.9)
### Will be
- changed home — the table's cards become posts, the Orkmaster's lane, the leaders' lanes, the tabs and the discard as drawn in §293; a goal's cascades leave the lanes
### Out
- The cards' own pictures stay pixel (§290.2); only the places' pictures take the cartoon
- No change to the frame, the hand, the lifted card or a goal's plan screen
- The mockup's 11 px `.chg .k` and 55% faded `.card.dim` are not built as drawn
### Risks
- risk: medium
- Five lanes of posts at body 15 may not fit 1280 px without a lane's acts clipped
- Many desktop browser tests (column, cascade, discard piles) rewritten at once; a lost act (Hold, Back to review) unnoticed
- The places' cartoon pictures wait for orkUI's copy; the step may land with today's pictures
- Simpler models drift from the mockup without pictures of each lane to hold them
### Defaults
- A quiet card is told by its muted ink and its *Quiet* plate, never by opacity under the 4.5:1 line
- The post's labels (NEW, CHANGED) at 12 px caption at least, in the heading face
- A goal at work in a leader's lane is one post with its live bar; its plan opens from the post as today (the person's answer)
- Until orkUI's copy has the places' cartoon takes, today's pictures stand and line 4 checks the word and a picture only

## Tech
### Talk
- verdict: doubt — go only if a lane's posts come from realm/board_feed (ideas.feed) cut by leader, drawn by one post part both faces share, never a second order in boardmap.js or column.js
- stance: Tech can build it on simpler models: the reader landed (board_feed.py), the look is orkUI's tokens; the risk is in the table's parts (boardmap.js, column.js, card.js, table.css) all changed at once
- for: No new host reader: ideas.feed already gives waits, posts by leader, stacks and the seen line; the discard and the tabs keep their parts (lane.js, plates.js, tabs.js) and change only their look
- against: column.js's piles and their acts (To review's Hold, Back to review) become Waits/Goals/At work, and §143's cascades leave the lanes: many desktop browser tests rewritten at once
- instead: First the cards as posts, the discard and the tabs' rings (look only); then the lanes and the Orkmaster's lane on ideas.feed as a second step
- assumes: board_feed's posts fill each leader's lane enough to read as a feed, not five Quiet lanes — shown by: ideas.feed over this repo since yesterday, its posts counted by leader
### Why
- One order of the news: the lanes read the host's `ideas.feed` (realm/board_feed.py), so the desktop and the phone never sort the same posts two ways.
- One post part both faces import keeps a card's drawing in one place; simpler models then change one file, not column.js, card.js and the phone's each.
- The table's parts (column.js, card.js, boardmap.js, cascade.js) change at once: their acts and tests must survive the move whole.
### Done when
- [test] When the Board opens on the desktop, then every post in the lanes and the discard is drawn by js/table/post.js, which imports none of frame/state, shell/store or pwa/
- [test] When the Board opens with posts by two leaders since the last look, then each leader's lane holds ideas.feed's posts of its leader in the feed's order, and column.js and boardmap.js sort none
- [test] When the Board opens with a goal to review and one ready for main, then each post carries its act (Hold, Back to review, To main) and pressing it sends the command it sent before
- [test] When the Board opens with a goal at work, then no lane draws cascade.js's blocks; the goal is one post with its live bar, and pressing it opens its plan as today
- [test] When the gate runs on the step, then test_architecture, test_board_alone and test_updates are green and no module the step touched passes 600 lines
### Checks
- No new host command: the lanes and the Orkmaster's lane read ideas.feed and the Board's rows the page already has
- post.js takes a post's data and an act callback only, so the phone's feed (169 F) can import it as `./page/js/table/post.js`
- Each browser test of column, cascade and the discard's piles that is removed names the test that now holds its act
- cascade.js is imported only by a goal's plan screen, or is gone; boardmap.js no longer draws a lane
- orkUI's tokens only in post.css (`tests/test_design_system.py`)
### Will be
- new orkboard/gui/static/js/table/post.js — the one post both faces draw; column.js, card.js and boardmap.js call it in place of their own cards
### Out
- No change to realm/board_feed.py's order or to ideas.feed's answer, beyond what a test shows missing
- The phone's feed (169's upfeed.js) is not written here; it imports post.js when 169 F lands
- A goal's plan screen and cascade.js's drawing inside it stay as they are
### Risks
- risk: high
- column.js's piles and their acts (Hold, Back to review) move to posts on simpler models; one lost act goes unseen in a red full CI after the merge
- About twenty test files read column, cascade or boardmap; rewritten at once, a test may be loosened instead of moved
- ideas.feed is a phone's reader: asked on each desktop refresh it may be slow over a long event log
- card.js (258 lines) and column.js (173) grow by the post's wrappers instead of shrinking
### Defaults
- The desktop asks ideas.feed once a refresh and cuts its posts by leader in the page; no `leader` argument is added to the host
- post.js is a Preact component like the rest of js/table, the phone reaching it through `./page/js/` as frame.js already does
- The step lands in two stages: the cards as posts and the discard (look), then the lanes on ideas.feed with the acts moved
- A goal's cascades leave the lanes only; cascade.js stays for the plan screen until no import of it is left
