# 159. A way's own line: each way of a question says what it leads to, on its card

Decisions §270.2 (a way with one line of what it leads to, its point in its first words) and §270.5 (a way's line is its
leader's, written to fit the card). Goal 158 drew the ways as hand cards; their line is today the question's why or
*Answers with this*, because the Board's question carries no line per way. **The goal's page**
`llm-wiki/general/pages/ideas/159-a-ways-own-line.md` holds the spec: the leaders' sections (*Product*, *Design*, *Tech*) and
the Taskmaster's *Stages*. The person, on 8 November 2026: *decide everything yourselves; what matters is that it reaches main*.

**The format** (Tech's section): a question stays one line on the page; each way's line follows the why as
` · <way>: <line>`, every way named exactly and in the ways' order, a line at most 80 characters (Design's limit). Kept only
when every way has one; a question written before reads as it does today, and today's parsers read the new one with the
lines inside its why (the `page-<n>` ids unchanged).

**Builds:** a stage a Grunt in its own worktree, merged into the goal's branch, then into `main` on the critical tests and
the stage's own (CLAUDE.md, alpha). Tech first (A–C), then Design (D).

| Stage | What | Where |
|---|---|---|
| **A. A way's line in the question** | `lines` read and written, one per way, after the why | `realm/idea_questions.py` |
| **B. The lines travel** | from Talk to the hand's row and the page's outside cards | `core/idea_talk.py`, `realm/board_map.py`, `realm/goal_phase.py`, `gui/ideas_phase.py` |
| **C. The rule the leaders follow** | at most 80 characters, its point first; Talk's prompt and BOARD.md's example from one source | `core/idea_talk.py`, `realm/agent_rules_text.py`, the roles |
| **D. The card shows and says it** | the way card's line and its screen reader's label | `gui/static/js/hand/answercards.js` |

## Later

The phone (§270.7); a failure's ways, the new chair's crafts and the project's kind and stage (§272) with lines of their own.
