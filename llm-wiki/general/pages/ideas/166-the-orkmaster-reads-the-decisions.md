---
owner: board
kind: idea
track: tech
order: 112
size:
priority: normal
short: The Orkmaster reads decisions
phase: talk
route: tech
by: claude-code
schema: 3
---
# The Orkmaster reads the decisions

## Gist
Build decision §281.7: the Orkmaster's role (llm-wiki/general/roles/orkmaster.md, written by Orkboard from its package's rules, as each seat's role is) reads no decision today: it routes from the goal's Gist and the party pages alone, so a goal resting on a decision is routed without it (goal 165 left Product out because its Gist named §280, not because the Orkmaster read it). The Orkmaster reads the decisions its goal names (§N in its page) and the log's newest before it routes, as the leaders' roles already say (the decisions, the newest first, and the one the goal rests on); the same in Orkboard's own routing call. The words come from one source, so the role file, the skill and the model's prompt agree.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions
- How does Orkboard's routing call read decisions? (**Titles only, named and newest** / Whole entries named / The call left as it is) — headings fit the call's 2,500 chars raised a little; whole entries, 4,000 each, would end a cheap call · Titles only, named and newest: Each §N's title and the log's ten newest; the call's budget grows a little · Whole entries named: The call reads each §N's text; its budget triples or more · The call left as it is: Role and skill only; code and the call route as today, reading nothing
  - Answered: Titles only, named and newest (the person, 2026-11-08)

## Decisions
- §283: the person's answers (8 November 2026)
- §281: the person's answers (8 November 2026)

## Tech
### Talk
- verdict: go
- stance: Tech builds it in one step: one source for the Orkmaster's reads (role file, skill, call) naming §N's and the log's newest; the route by code stays as it is
- for: goal 165 lost Product as no seat read §280; leaders already read the log, and decisions_log.headings and the §N pattern exist: text and wiring, no new part
- against: few goals reach the call (code routes most by goal types), and its budget, CONTEXT route 2,500 chars pinned at most 3,000 by a test, must grow to hold headings
- assumes: a decision's words name the parties it concerns plainly enough to route by — shown by: goals 164 and 165 routed again with the new role add Product
