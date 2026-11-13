---
owner: board
kind: idea
track: design
order: 20
size:
priority: normal
short: The compare mat
phase: talk
route: product, design, tech
asks: person
by: claude-code
schema: 3
---
# The compare mat: up to six cards with their price, and above them what the…

## Gist
The compare mat: up to six cards with their price, and above them what the card in focus would make, laid small in its own layout (§300.1, §300.7, §301.4)

The person, 12 November 2026, on the mockups `docs/mockups/mats/` (decisions §300, §301): «сравнение (до 6 карт сеткой, на мобиле 2*3, на десктопе наоборот, с контентом если это ресурсы и со стоимостью), действие - выбор одной»; «планшет сравнения сможет сверху показать результат выбора при выделении карты: например если это разная архитектура или дизайн». Split from goal 171 (the person: «да», on a goal for each mat), built on the Board's own data with its logic in the host, no mock data on the page (§301.1).

Goal 171's stage G changed `tests/test_cards_spreads2_browser.py`'s cost case: the muted card a tool cannot pay and its two ways (*play it on <another tool>*, *Wait for 04:00* with `ideas.route_later`) are held by no case now: this goal brings them back with the costs it lays.

## Why

## Done when

## Out

## Risks

## Depends on
- 171-the-mats-as-laid: the mat's frame (its felt, plates, zones, seal and address) and the hand.

## Stages

## Open questions
- Which cards does compare lay first? (**Variants and goals** / Goals in line only / All of §301.4 now) — Pick one (§64) and the goals' estimates are the host's, read free; no host draws a way's scheme or screen (§301.2) · Variants and goals: Pick one's 2 to 6 variants, then the goals in line; a way's view later · Goals in line only: The Orkmaster's three mats as one; Pick one keeps the old drawer · All of §301.4 now: Ways' schemes and screens too, each view a leader's paid pass
- What price does a goal card say? (**Plan's, else route's** / Its route's only / The Orkmaster prices each) — cost_of prices a goal by its route and tiers, not its size: six goals of one route show one price · Plan's, else route's: The Taskmaster's estimate where a plan is, else the route's; both free · Its route's only: cost_of for every routed goal: one route, one price, said so · The Orkmaster prices each: A paid pass reads each goal's size; its cost said before it runs
- What does picking a goal do? (**First in line** / Start it now) — the mockup's *Start it first* is two acts: ideas.move puts a goal before another; a start begins a paid pass · First in line: ideas.move before the line's first: one press, its Undo; it starts in turn · Start it now: Its Talk or work begins at once: sealed, its cost said first (§302.4)
- Past six, where do the others lie? (**A pile dealt six at a time** / Weigh two until six are left / The first six only) — Ten goals wait in line (5 new, 5 at talk); a pile by its thickness (§302.1) keeps the rest in sight with no count · A pile dealt six at a time: The line's first six laid; the rest a pile at the edge, pressed deals six more · Weigh two until six are left: Over six, pairs weighed as duel.js does, then the last six laid on compare · The first six only: The line's first six; under them a line says more wait, no count
- Do new goals keep their three piles? (**Sort keeps its piles** / One compare, as §300.7) — Sort's move is three piles, not one pick (spreads/sort.js); folded in, five new goals take five picks, no Later · Sort keeps its piles: To work, Later, Drop stay a piles mat of the Orkmaster's; compare picks only · One compare, as §300.7: New goals laid as the rest; Hold and Drop only from each goal's own card

## Decisions

## Product
### Talk
- verdict: doubt — go if a card's price is one the host reads free (a plan's or route's estimate, a pick's run) and said as such, and the view above only what is made; no way is drawn yet
- stance: Product wants one mat to pick one of a few: the goals in line by what each costs against what is left, and a task's variants; the pick a move counted, never a price invented
- for: Pick one (§64) makes 2 to 6 variants with no mat on the cards' table to pick them; cost_of and a plan's estimate price a goal free; §300.7 folds the Orkmaster's three spreads into one
- against: cost_of prices a goal by its route, not its size: six goals of one route show one price; ideas.order, ideas.sort and the muted card's ideas.tool_for have no host
- instead: Compare on what the host keeps: Pick one's variants and the goals in line at their estimate, pick one; a way's scheme or screen once a leader's pass draws it
- assumes: the person picks the goal to play first by its price against what is left, not the Orkmaster's line — shown by: compare's picks moving a goal before the line's first, over weeks

## Design
### Talk
- verdict: doubt — go if Pick one keeps its note, None of them and Play apart from the pick (spec 51), the view stays in sight of its cards on a phone, and a price all share is said once
- stance: Design wants one compare for each pick of one: Pick one's variants, the goals in line, a hero; focus shows a card's result above, a press picks it, the move dim at its foot's right till then
- for: Pick one has no mat on the cards: its variants open the old drawer in a stop (hand/stopface.js PickView); one grid learnt once, a pick's result seen before its move (Nielsen 1, 4, 5)
- against: Ten goals wait in line for six cards, the rest unsaid; at 390×844 the view, 2×3 S cards and the hand overflow, the view off row three; a view changed above focus is unheard (WCAG 4.1.3)
- instead: Compare as Pick one's mat first: the picked variant whole above with its Play, the note and None of them in the hand; the goals in line once their price differs by goal
- assumes: the person reads the view before a pick, focus crossing two cards or more — shown by: how many cards a pick's focus crossed, kept in its move_played (no word)
