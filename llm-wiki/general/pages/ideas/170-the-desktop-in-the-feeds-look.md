---
owner: board
kind: idea
track: design
order: 17
size:
priority: normal
short: The desktop in the feed's look
phase: talk
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
давай оставим» and «Я ещё добавил разные стили спинок для лидеров».

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

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

## Design
### Talk
- verdict: doubt — go only after 169's feed reader (stage E) lands, so the lanes' *New since* order is the phone's, and with the mockup's 11 px labels and 55% faded quiet card fixed
- stance: Design wants it: one card as a post on both faces, the asks ringed and first; the mockup's faults must not be built as drawn, and simpler models need pictures per lane to be held to it
- for: The person liked the left lane and the discard; what waits first and asks ringed in yellow put the person's next act in sight (Nielsen 1, 6); one post shape for phone and desktop (4)
- against: The mockup's `.chg .k` is 11 px (§291.1's floor 12) and `.card.dim` at .55 opacity drops a quiet lane's words under 4.5:1 (WCAG 1.4.3); the chain's *Here* is clipped at the right edge
- instead: Every card a post and the discard as drawn first; the leaders' lanes' *New since* order when 169's reader is merged; the places' pictures when orkUI has them
- assumes: Five leaders' lanes of posts at body 15 fit a 1440 px window without clipping a card's acts — shown by: pictures of the Board at 1280 and 1440 px beside the mockup

## Tech
### Talk
- verdict: doubt — go only if a lane's posts come from realm/board_feed (ideas.feed) cut by leader, drawn by one post part both faces share, never a second order in boardmap.js or column.js
- stance: Tech can build it on simpler models: the reader landed (board_feed.py), the look is orkUI's tokens; the risk is in the table's parts (boardmap.js, column.js, card.js, table.css) all changed at once
- for: No new host reader: ideas.feed already gives waits, posts by leader, stacks and the seen line; the discard and the tabs keep their parts (lane.js, plates.js, tabs.js) and change only their look
- against: column.js's piles and their acts (To review's Hold, Back to review) become Waits/Goals/At work, and §143's cascades leave the lanes: many desktop browser tests rewritten at once
- instead: First the cards as posts, the discard and the tabs' rings (look only); then the lanes and the Orkmaster's lane on ideas.feed as a second step
- assumes: board_feed's posts fill each leader's lane enough to read as a feed, not five Quiet lanes — shown by: ideas.feed over this repo since yesterday, its posts counted by leader
