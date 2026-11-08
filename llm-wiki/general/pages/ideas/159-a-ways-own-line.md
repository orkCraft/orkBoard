---
owner: board
kind: idea
track: product
order: 10
size:
priority: normal
short: A way's own line
phase: work
route: product, design, tech
spec: docs/specs/159-a-ways-own-line.md
decisions: 270
by: claude-code
schema: 3
---
# A way's own line: each way of a question says what it leads to, on its card

## Gist
A way's own line: each way of a leader's question carries one line of what it leads to, written by the leader to fit the card (decisions §270.2, §270.5); the Board's question format holds it, the host carries it, the hand's way cards show it instead of the question's why or 'Answers with this'. The person (8 November 2026): да, заводи цель на строки к вариантам; решай всё сам, главное чтобы имплементация попала в мейн.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
- [ ] A. A way's line in the question
  - party: Tech. `realm/idea_questions.py`: `LINE_CHARS = 80`; `of` and `card` take an optional `lines`, one a way, each through `_plain`, kept only when every way has one within 80 characters (else no `lines`, the card as today); `line` writes after the why ` · <way>: <line>` for each way by its exact name, in the ways' order (no why: the tail starts at the first way); `parse` reads that tail back anchored on every way's name in order, a line of before giving no `lines`; `_asked` carries `lines`. The module's docstring says it. Tests in tests/test_idea_questions.py, with `_LINE` of before kept in the test to read a new line.
  - proves: Tech's "When a leader's Talk answer gives a question with a line for each way… line() then parse() gives back the same ask, ways, pick, why and lines", "When a question line written before this goal, or BOARD.md's example, is parsed…", "When a new line with ways' lines is read by today's pattern…", "When a leader gives a line over 80 characters, or lines for only some ways…"; Product's "When a question written before this goal (no lines) is lifted…" (the engine's half)
- [ ] B. The lines travel to the hand and the page
  - party: Tech. Talk's waiting card keeps `lines` in talk.json (`realm/idea_talk_parse.py` `_cards` through `card`) and `realm/board_map.py` `talk_rows` hands it on as it is; `realm/goal_phase.py` `outside_cards` passes `parse`'s `lines` into `card`; `gui/ideas_phase.py` `answers_written` writes a question the page lacks as its whole `idea_questions.line` (ways, pick, why, lines), not its ask alone, matched as today by its ask. The question stays one line: `questions_of`, `open_of` and the `page-<n>` ids unchanged. Tests in tests/test_goal_phase.py, test_board_map.py, test_idea_talk.py.
  - proves: Tech's "When Talk keeps a waiting card, or a page that asks the person lays its question outside, with ways' lines, then the hand's row carries `lines`…"; Product's "When a leader's Talk asks a question with a line for each way, then the page keeps it and reading the page back gives the same ways, pick and lines."
- [ ] C. The rule for a way's line, from one source
  - party: Tech. `core/idea_talk.py` `CARDS` and both JSON examples of `instruction` gain `"lines": ["…", "…"]` and the rule: one line for each way, at most 80 characters, what that way leads to, its point first, never the why repeated (§270.2, §270.5); `realm/agent_rules_text.py`'s BOARD.md question example and its sentence say the same. Orkboard's own `llm-wiki/general/BOARD.md` and `roles/*-leader.md` are written back from that source. core/idea_talk.py stays under 600 lines (a split if it must). Tests in tests/test_idea_talk.py, test_agent_rules.py, test_agent_rules_prompts.py.
  - proves: Tech's Check "The Talk rules (rules(), the JSON example), roles/<craft>-leader.md and BOARD.md's example are built from one source…"; Design's Check of the 80-character, point-first rule; Product's Check "The leader's role rules ask for a way's line short enough for the card and its point first"
- [ ] D. The way card says and speaks its line
  - party: Design. `gui/static/js/hand/answercards.js` `WayCard`: its aria-label reads the name, "its pick" where it is, its own line, then the question; `title` keeps the line; `lineOf` keeps today's fallback (the pick's why, the rest "Answers with this."). `openedcard.css`'s `.hand-ans__line` stays in the caption face with the 6-line clamp as the fallback, no colour, font or corner of its own. Tests in tests/test_hand_desktop_browser.py at 1280 × 800: 80-character lines shown whole and uncut, none "Answers with this."; each card's accessible name; a question with no lines as today; pressing a way with a line sends the answer and goal_answered says from "hand". tests/test_design_system.py and test_gui_wording.py pass.
  - proves: Design's four Done when lines (the [look] one for the person to see); Product's "When the person lifts a goal card at 1280 × 800 whose question has a way's own line…", "When a question written before this goal (no lines) is lifted…", "When the person presses a way card that carries its own line, then the answer is sent and goal_answered says from \"hand\"."; Product's [person] line is the owner's, read on the first ten questions after it lands

## Open questions

## Decisions
§270.2, §270.5.

## Product
### Talk
- verdict: go — the owner decided it (§270.2, §270.5) and said to settle the rest; every question card on the desktop gains, and answercards.js already reads q.lines
- stance: Product backs it: a way card that says what it leads to is how the person answers from the hand without opening the question
- for: wide reach (every lifted question), small face work: lineOf already prefers a leader's line; the gap is the question format, the role rules and the host
- against: a change to BOARD.md's question line other AI tools write and read; old questions with no lines must still read, and a line that fits 144 × 202 is a new limit
- assumes: a way's own line lets the person pick from the hand, not Open… or own words — shown by: the share of answers sent with from: "hand" before and after
### Why
- The person's job on a lifted card is to decide; today every way but the pick says only "Answers with this.", so the choice is read elsewhere.
- A way that says what it leads to lets the person answer from the hand (§270.2, §270.5), which is the bet 158 already measures.
- The line is the leader's, so it must travel from the leader's Talk through the page to the card without being lost or cut.
### Done when
- [test] When a leader's Talk asks a question with a line for each way, then the page keeps it and reading the page back gives the same ways, pick and lines.
- [test] When the person lifts a goal card at 1280 × 800 whose question has a way's own line, then that way's hand card shows its leader's line whole.
- [test] When a question written before this goal (no lines) is lifted, then its way cards read as today: the pick its why, the rest "Answers with this."
- [test] When the person presses a way card that carries its own line, then the answer is sent and goal_answered says from "hand".
- [person] When the owner reads the first ten questions asked after this lands, then each way's line says what it leads to in its first words.
### Checks
- Each way's line on a card is its leader's own words, never the question's why repeated for every way (§270.5).
- A question line another AI tool writes by hand, without lines, still reads with its ways and pick unchanged.
- The leader's role rules ask for a way's line short enough for the card and its point first (§270.2).
- goal_answered keeps its from "hand" / "open" so the week can compare answers before and after.
### Will be
- changed 159-a-ways-own-line — its hypothesis (a way's own line lets the person answer from the hand) gets its signal in goal_answered's from
### Out
- The phone's hand (§270.7, a goal of its own).
- Lines for a failure's ways, the new chair's crafts and the project's kind and stage (§270.2, §272): they keep what they say today.
- Rewriting the lines of questions already asked and answered.
### Risks
- medium
- BOARD.md's question line is a contract other AI tools write; a line they do not know must not break their questions or their answers.
- A leader may write a line that restates the way's name, so the card gains words but not meaning.
- A line too long for 144 × 202 is clamped and its point lost, unless the rule puts the point first.
### Defaults
- The owner said to decide the rest: the line's place in the page and its length are Tech's and Design's to set, kept readable by old parsers.
- A question with no line for a way keeps today's fallback; nothing is invented for it.
- The signal is the event log's from "hand" read by the owner, no new counter or screen.
- Desktop only; the phone follows with §270.7.

## Design
### Talk
- verdict: go — no new screen or step: the way card (answercards.js WayCard, 144 × 202) already has the line's place; it trades a generic "Answers with this." for words that match the real world
- stance: Design backs it if the line is short enough to show whole (about 80 characters under the name's 3 lines) and is heard, not only seen: the card's aria-label must carry it
- for: recognition over recall (Nielsen 6): each way says what it leads to on the card the person presses, so the question's why no longer stands in for every way
- against: today .hand-ans__line clamps at 6 caption lines and the aria-label says only the name and the question, so a long or unread line is lost to a screen reader (WCAG 1.3.1, 2.5.3)
- assumes: a leader can say what a way leads to in about 80 characters with its point first — shown by: the lines of the first ten questions asked after it, none cut by the clamp
### Why
- The way card is where the person decides; a generic "Answers with this." makes them recall the choice from elsewhere (Nielsen 6, recognition over recall).
- A line that is shown cut, or seen but not heard, fails the person who reads by a screen reader or zooms (WCAG 1.3.1, 2.5.3, 4.1.2).
- The card is 144 × 202: the line's length is a design limit, so the leader's rule and the clamp must agree.
### Done when
- [test] When the person lifts at 1280 × 800 a goal card whose one question has a line of 80 characters for each way, then each way card shows its line whole, uncut, and none says "Answers with this."
- [test] When that card is lifted at 1280 × 800, then each way card's accessible name says its name, "its pick" where it is the pick, and its own line.
- [test] When a question with no lines is lifted at 1280 × 800, then the pick shows the question's why and every other way "Answers with this.", as today.
- [look] When the person lifts such a card at 1280 × 800, then the line reads in the body face under the name, the pick marked by its head, in orkUI's office.
### Checks
- The way's line is drawn in the caption (body) face, never the pixel face: it is a leader's words.
- The sheets add no colour, font or corner of their own (tests/test_design_system.py).
- The leader's role rule for a way's line says at most 80 characters, its point first, so it fits under a name of three lines.
- The narrow page and the phone keep the inline lifted card unchanged (§270.7).
- Tab order, Esc and Put it back on the lifted card stay as spec 158 G has them.
### Will be
- changed orkboard/gui/static/js/hand/answercards.js — the way card's aria-label carries its own line, and its line is the leader's when the question has one
### Out
- The table's lane (§270.4): the asking leader's question keeps its ways without lines.
- The phone's hand and the narrow page's inline card (§270.7).
- The way cards of a failure, the new chair and the project's kind and stage (§272).
### Risks
- low
- A line over 80 characters is cut at the clamp of 6 caption lines; its point survives only if written first.
- An aria-label with name, pick, line and question grows long for a screen reader at each Tab.
- A name of three lines leaves less room for the line than the 80-character limit assumes at a large text size.
### Defaults
- The line's limit is 80 characters (the card's caption lines under a name of three lines), the clamp kept as the fallback.
- The aria-label reads name, its pick, line, then the question; the title keeps the line for the pointer.
- The table's lane gains no lines in this goal: the way card is where the line matters.
- Desktop at 760 px and over only; the narrow page and phone follow with §270.7.

## Tech
### Talk
- verdict: doubt — only if the lines stay in the question's one page line: idea_questions._rows reads any other line as a question, so sub-lines break page-<n> ids and Orkline's copy
- stance: Tech can build it in one step as an optional `lines` beside `choices` in idea_questions (33 modules depend on it), additive, with old lines and old readers still reading
- for: the face already reads q.lines (answercards.js lineOf); the gap is narrow: of/card/line/parse, the Talk prompt, board_map._asked, goal_phase.outside_cards and BOARD.md's example
- against: BOARD.md's question line is a contract other AI tools write by hand; core/idea_talk.py is 507 lines, near the 600 split, and its prompt grows
- instead: carry the lines in talk.json and the card only, leaving the page line as it is; the page and BOARD.md gain them in a later goal
- assumes: a way and its line fit one page line other parsers still read (the lines fall into why) — shown by: parse() of today on a new line giving the same choices and pick
### Why
- A way's line must travel from the leader's answer through talk.json and the page to the hand whole; one lost step and the card falls back to "Answers with this.".
- The question line is a contract other AI tools and Orkline's frozen copy read: it must stay one page line, so page-<n> ids and old parsers keep working.
- idea_questions is a stable part 33 modules lean on: the change is additive, an optional `lines`, never a new shape.
### Done when
- [test] When a leader's Talk answer gives a question with a line for each way, then its card keeps `lines`, and line() then parse() gives back the same ask, ways, pick, why and lines.
- [test] When a question line written before this goal, or BOARD.md's example, is parsed, then it gives the same ask, ways, pick and why as today and no lines.
- [test] When a new line with ways' lines is read by today's pattern (the regex of before), then its ask, ways and pick are unchanged and the lines fall into its why.
- [test] When Talk keeps a waiting card, or a page that asks the person lays its question outside, with ways' lines, then the hand's row carries `lines`, one a way, in the ways' order.
- [test] When a leader gives a line over 80 characters, or lines for only some ways, then the card keeps no lines and its ways read as today.
### Checks
- The question stays one line under *Open questions*: no sub-line, so questions_of, open_of and the page-<n> ids are unchanged.
- core/idea_talk.py and realm/board_map.py stay under 600 lines; nothing new under realm/ or core/ imports gui/ (tests/test_architecture.py).
- A way's line is taken through _plain like the why: one line, no newline, no markdown that ends the list item.
- The Talk rules (rules(), the JSON example), roles/<craft>-leader.md and BOARD.md's example are built from one source and say the same 80-character, point-first rule.
- The gate's always (test_architecture, test_board_alone, test_updates) and tests/test_idea_questions.py pass.
### Will be
- changed orkboard/realm/idea_questions.py — a question gains an optional `lines`, one a way: of, card, line, parse and _asked carry it, old lines still read
### Out
- The way card's face (answercards.js, its aria-label and clamp): Design's section.
- Orkline's frozen copy: its parser reads the new lines' tail as the why, unchanged.
- Lines for a failure's ways, the new chair's crafts and the project's kind and stage (§272).
### Risks
- medium
- A why that happens to hold " · <a way's name>: " would be read as lines; the parse anchors on every way's exact name in order to make it unlikely.
- core/idea_talk.py is 507 lines and its prompt grows; a split may be forced before 600.
- An old parser shows the lines inside the pick's why, so in Orkline the pick's card reads longer until it learns them.
- A model that gives lines for some ways only loses them all, by the every-way-or-none rule.
### Defaults
- My Talk's doubt is settled by keeping one line: after the why, ` · <way>: <line>` for each way, by its exact name, in the ways' order; no why, the tail starts at the first way.
- A way's line is at most 80 characters (Design's limit), kept only when every way has one; else the card has no lines and today's fallback stands.
- `lines` rides in the card in talk.json and in _asked as it is; the face already reads q.lines, so the host changes no route.
- goal_answered and its from "hand" are unchanged: Product's signal needs no new event.
### Accepted
- met: When a leader's Talk answer gives a question with a line for each way, then its card keeps `lines`, and line() then parse() gives back the same ask, ways, pick, why and lines.
- met: When a question line written before this goal, or BOARD.md's example, is parsed, then it gives the same ask, ways, pick and why as today and no lines.
- met: When a new line with ways' lines is read by today's pattern (the regex of before), then its ask, ways and pick are unchanged and the lines fall into its why.
- met: When Talk keeps a waiting card, or a page that asks the person lays its question outside, with ways' lines, then the hand's row carries `lines`, one a way, in the ways' order.
- met: When a leader gives a line over 80 characters, or lines for only some ways, then the card keeps no lines and its ways read as today.
