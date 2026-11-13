---
owner: board
kind: idea
track: tech
order: 114
size:
priority: normal
short: The discard as piles
phase: talk
route: product, design, tech
asks: person
by: claude-code
schema: 3
---
# The discard as piles by branch: each pile's into and Merge into its branch,…

## Gist
The discard as piles by branch: each pile's into and Merge into its branch, into main the person's, what goes into main into the book (§300.9, §301.3)

The person, 12 November 2026, on the mockups `docs/mockups/mats/` (decisions §300, §301): «планшет сброса колоды и над каждой выпадающий список ветки и действие залить». Split from goal 171 (the person: «да», on a goal for each mat), built on the Board's own data with its logic in the host, no mock data on the page (§301.1).

## Why

## Done when

## Out

## Risks

## Depends on
- 171-the-mats-as-laid: the mat's frame (its felt, plates, zones, seal and address) and the hand.

## Stages

## Open questions
- Which branch is a goal's pile? (**The one its page names** / Its own goal branch only / Each branch holding its gate commit) — §300.4 makes a pile the goal whose branch it is, yet only the window's goals keep one (goal/<slug>); a skill-run goal's gate commit lies on many (154's on six) · The one its page names: Heavier: the gate's record names its branch; this Board's goals pile too · Its own goal branch only: The window's goals pile; this Board's skill-run goals lie as today · Each branch holding its gate commit: Read by git alone; a card lies in a pile for each branch
- What does Merge into main send? (**Dev's whole pile** / One card of the pile) — a pile is a branch: merged, all of it goes, each card face up before the seal; today's To main sends one goal (ideas.to_main) · Dev's whole pile: All of dev goes at one seal, every card seen; no goal sent apart · One card of the pile: A card picked goes with what it stands on; the rest waits in dev's pile
- What does a pile's into list offer? (**Where the host merges it** / Every branch of the repository / dev, main and release branches) — the host merges a goal's branch only into dev and dev only into main; a list of more asks a choice no press carries out · Where the host merges it: One target reads as words on the pile; a list appears once there are two · Every branch of the repository: git lists 149 here; a claude/* target has no merge in the host · dev, main and release branches: Release branches join the list; this project keeps none yet
- One word for the merge? (**Merge into <branch>** / To <branch> / Each its own word) — one move, one word (Nielsen 4): into dev is To dev in the hand, Send to dev on the gate, Merge into dev on the pile · Merge into <branch>: To dev, To main and Send to renamed; TERMS keeps the old words in was · To <branch>: The hand's short word everywhere; the gate's Send and the pile's Merge renamed · Each its own word: Three words for one move stay, as §300.8, §300.9 and the hand name them

## Decisions

## Product
### Talk
- verdict: doubt — go once one card lies in one pile: 154's gate commit lies on six claude/* branches, and this Board's goals, run by the skills, keep no goal/<slug> to pile on
- stance: Product wants the discard where done work is sent on: one card in one pile, read from the Board's own branches, each Merge kept as move_played with its goal and from (H7)
- for: Every goal ends in the discard and the person asked for it (§300.9); into main's seal and the book are built (171, §283.28), so what is new is the piles, their into and Merge
- against: No merge has been logged from the discard (this repository's usage log has none); its goals reach main by a session's merge («Merge goal The battle and the gate into main»)
- assumes: the person sends done work on from the discard, not by asking a session to merge — shown by: the discard's Merge moves (move_played) against merges into main made outside it

## Design
### Talk
- verdict: doubt — go once a merge has one face: the pile in focus lights the mat's one seal (§302.4), its cards face up, and the gate's seal is that same move in the same words
- stance: Design wants the column and the Orkmaster's mat to lay the same piles: a stack a branch, its name as git writes it, its into, one seal for the pile in focus, its cards face up first
- for: A stack a branch is git's own model (Nielsen 2); a pile not through the gate says which card and why before a press (1, 9); into main asks once, by 171's seal (§302.4)
- against: The mock lays a green Merge on every pile, not one seal (§302.4), counts *and 2 more*, uppercases branch names; into dev is already *To dev* and *Send to <branch>*
- instead: the column's piles by branch, each pressed opening its top goal's gate mat, whose seal already merges: no second merge face until the gate and the pile share one move
- assumes: the branches with done cards fit as piles in one row at 1440×900, as the mock's three — shown by: git's count of branches holding a done goal not in main on this Board
