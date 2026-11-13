---
owner: board
kind: idea
track: design
order: 19
size:
priority: normal
short: The discussion mat
phase: talk
route: product, design, tech
asks: person
by: claude-code
schema: 3
---
# The discussion mat: a card in the middle, its route's tokens on a ring, each…

## Gist
The discussion mat: a card in the middle, its route's tokens on a ring, each its slip, the thread folded; Rating its first case (§300.1, §300.5, §300.6)

The person, 12 November 2026, on the mockups `docs/mockups/mats/` (decisions §300, §301): «Только фишка подразумевает вопрос и ответ на него»; on a discussion mat of its own: the recommended way taken, the ring, Rating its first case (§300.6). Split from goal 171 (the person: «да», on a goal for each mat), built on the Board's own data with its logic in the host, no mock data on the page (§301.1).

## Why

## Done when

## Out

## Risks

## Depends on
- 171-the-mats-as-laid: the mat's frame (its felt, plates, zones, seal and address) and the hand.

## Stages

## Open questions
- Where is a token's thread kept? (**On the page, under its Talk** / In this machine's state / No thread yet) — a reply's answer is one ask.json record and a journal line: nothing keeps a goal's thread, so *2 earlier* folds none · On the page, under its Talk: Every tool and the leader's next pass read the reply; each reply writes the page · In this machine's state: Nothing in git; a leader run by the skills never reads the reply · No thread yet: Lighter: the slip is its Talk alone, a reply answered in the hand as today
- Which moments does the ring lay? (**Rating now, the others later** / Rating and Spec now / Rating, Spec and Accept now) — §300.1 lays a mat where the person moves: Rating has answers, Spec's Start is on the track mat, Accept is the leader's · Rating now, the others later: The ring at Talk; sections and Accepted read in the card's L as today · Rating and Spec now: Start the work leaves the track mat for the ring's seal at Spec · Rating, Spec and Accept now: Accept laid too, with no move of the person's on it
- Does an asked leader join the route? (**Its token only, the route kept** / It joins the route, its price said) — §300.5 seats a leader asked from the ring, filled when it answers; the route and its price are the Orkmaster's deal · Its token only, the route kept: Its answer is a word on the ring: no section, no stage, no new cost · It joins the route, its price said: It writes a section and works a stage; the goal's price rises first
- Whose is a question on the ring? (**The goal's, in the hand** / Its leader's, the line names it) — a page's question line names no asker (idea_questions.parse), so no token holds it; a token's question square is a doubt · The goal's, in the hand: Its ways in the hand; the foot says a question waits, naming no leader · Its leader's, the line names it: Square and slip point to its ways; BOARD.md's line gains its asker, every tool
- Where does a leader's no lie? (**Its ways in Rating's hand** / The hearing, as today / Its token only) — a no's ways are the hearing's sides, a face of their own, on goals the engine runs; on one run by the skills it has none · Its ways in Rating's hand: Do it, Drop it, Do the smaller one, After <goal>: one press each, one face · The hearing, as today: Rating opens, and a no lifts the hearing's own card beside it: two faces · Its token only: A no is its token and slip; nothing on the mat answers it
- What is Rating's one move? (**Go on to the spec, sealed** / None, as drawn / The track mat's, as today) — §300.1 lays a mat where the person has a move, one at its foot; the shot draws none; the track mat at Talk only Drop · Go on to the spec, sealed: Lit when all have said and no question waits; the sections' passes, cost said · None, as drawn: Ways and replies only; rated, the card comes back to the hand to go on · The track mat's, as today: The talk turn opens the stages; Rating only reads and replies: two mats
- Can a reply turn its token? (**Yes, its leader heard again** / No, a quick question as today) — idea_verdict.py hears a leader again at a quick call's tier and turns its token; a quick question leaves a stale one · Yes, its leader heard again: The verdict pass reruns with the reply and rewrites the token, twice at most · No, a quick question as today: Words under the slip; the token keeps its first Talk's verdict
- Which Talk does the ring read? (**Both, through one reader** / The page, the engine writing it / The page only, as today) — ideas.verdicts reads only ### Talk; the engine keeps its verdicts in talk.json, so an engine goal's ring lies empty · Both, through one reader: A realm reader lays talk.json's and ### Talk's tokens alike; no format moves · The page, the engine writing it: One keeper for every tool; idea_talk and idea_verdict write ### Talk first · The page only, as today: Goals the skills run get a ring; one the engine runs lies empty

## Decisions

## Product
### Talk
- verdict: doubt — go if the ring lays what the page keeps (Talk, who still looks, a no's ways) and a reply's answer gets a keeper first: today it is ask.json's one record
- stance: Product wants Rating on every goal's path, its ring the route's Talk read free (§301.2), and a reply's answer kept by goal and leader where the leaders' next pass reads it
- for: Every routed goal passes Rating, so the ring is met on each; its tokens are read free (ideas.verdicts); a leader still looking, dashed, says whom the decision waits on
- against: The thread has no keeper: a reply's answer is one ask.json record and a journal line, never under its Talk; behind ?table=cards, met little until goal 170 turns the cards on
- instead: The ring of Talk tokens, who still looks and a no's ways (ideas.objection) first; the folded thread and the Orkmaster's balloon once a reply is kept by goal and leader
- assumes: the person talks back to a leader's token before deciding, often enough for a thread to fold — shown by: ideas.reply sent on a goal in three at Talk, some twice to one leader

## Design
### Talk
- verdict: doubt — go if Rating is Talk's one face on the cards: the talk turn and a card opened at Talk open it, the L's reply slips move onto it, seated in the route's order, never free on a ring
- stance: Design wants one place where a goal's Talk is read and decided: the card in the middle, the route's tokens round it, a slip each in route order, the questions' ways in the hand (§302.4)
- for: The talk turn says *you decide* yet opens the track mat, Drop its one way and no seal at Talk (hand/turncards.js); Rating lays the leaders' words where it is decided, who still looks too
- against: Talk has two faces on the cards already, the L's slips with Reply and Ask (cards/around.js) and the hearing; slips free on a ring overlap (rate-desk) and lose Tab's order (WCAG 2.4.3)
- instead: Rating as the card opened at Talk on 171's felt: tokens on the card's edge, slips in two seated columns, the questions' ways in the hand; the drawn ring, balloon and folded thread later
- assumes: three route tokens, one asked and the Orkmaster's balloon fit round one card at 1280×800 with a reply open — shown by: Rating in tests/test_cards_fit_browser.py at 1280×800 and 390×844

## Tech
### Talk
- verdict: doubt — go if the ring reads one source of Talk, the engine's too, and a reply turns its token by its leader heard again: today ideas.verdicts misses talk.json and a reply is one ask.json
- stance: Tech lays Rating as a spread on 171's frame over one realm reader of Talk (### Talk and talk.json), the L's slips moved there from cards/around.js, a reply sent to its leader heard again
- for: Read free: ### Talk (page_talk), the questions and turns (board_turns), who still looks (route less heard); Reply and the slips exist (around.js); idea_verdict.py already hears a leader again
- against: ideas.verdicts reads only ### Talk, never written by the engine: its goals' rings lie empty; ideas.reply is board_ask: one ask.json for the Board, its call shown a title, not the Talk
- instead: Rating on one reader of Talk with its questions and who still looks, a reply heard again; the folded thread and the Orkmaster's balloon once a reply has its keeper
- assumes: a leader heard again on a reply, cheaper tier and no tools, turns its token only where its full Talk would — shown by: a week of replies whose turned verdicts its next Talk keeps
