# Hypotheses

What we believe and have not yet shown. Each is tested before it becomes a decision (`docs/decisions.md`): what would
prove it, what would refute it, how we test it, and what it changes if it holds. A hypothesis is never a reason to build
by itself.

Status: **open** (not tested) · **testing** · **held** (became decision §N) · **refuted** (with what we learned).

## H1. Orkboard is a studio that sees your real product, not a board of agents nor a spec generator

**Status:** open. **Raised:** the owner, 31 October 2026, after spec 115 (the live product under each leader's eyes).

### The belief

Writing code is becoming a commodity: Claude Code, Codex and their kind do it better and cheaper each month, and Orkboard
already runs on whichever the person has. For a solo maker the bottleneck is no longer the code but **what is wanted**:
what, why, where it ends, what *done* means. So Orkboard's value moves up: from running agents to **turning what the
person wants into specs grounded in the real, running product**, handing them to any agent, and checking what comes back.

**But "we gather specs" alone sets us apart from no one.** Spec-driven development is the most crowded corner of AI
tooling in 2025–2026, much of it free (below). What may set Orkboard apart is the **combination**:

1. **Specs grounded in the real product**: the maps read from the code (spec 89, 102), the live product under each
   leader's lens (spec 115). Others write specs from a prompt and documents.
2. **Disagreement as a feature**: leaders say no (spec 108), a fork goes to the person, the decision is logged.
   Others hand one agreed document down a chain.
3. **The whole studio, not only engineering**: product, design, art, marketing, release, live, by the project's stage.
   Spec tools are for developers; app builders for prototypes.
4. **The loop closed**: what is wanted → spec → any agent's work → the gate → the live product → a mark → what is wanted.
5. **The person's own subscriptions** (Claude Code, Codex; the mana), no new bill for models.

### The statement to test

> **For** solo makers of web apps, mobile apps and games who build with AI coding agents,
> **Orkboard is** an AI studio (product, design, tech, marketing) **that sees your real, running product**, argues about
> what is worth building, and hands your agents specs grounded in it.
> **Unlike** spec kits that turn a prompt into documents, and app builders that lock you into their stack.

In two words: *a studio that sees your product*, not *a spec generator*.

### Who holds the ground (as read in third-party reviews of mid-2026; check the vendors' own pages)

| Kind | Who | Their strength | Where we may be stronger |
|---|---|---|---|
| Spec frameworks over an agent | GitHub Spec Kit (115k+ stars by June 2026, free), OpenSpec, Task Master AI | in any editor, a large audience, free | their specs come from a prompt, not the product; developers only |
| A team of personas | BMAD Method (Analyst, PM, Architect, UX, QA, …; a game development pack) | **close to our parties' leaders**, free | personas hand documents down a chain; ours disagree, fork to the person, read maps of the code and the live product |
| A spec IDE | Kiro (AWS) | integration, AWS's reach | no IDE to adopt; the person's own Claude Code and Codex |
| Spec as source | Tessl | traceability | no platform lock-in |
| Built into the agents | Claude Code's plan mode, Cursor | there by default | (this is the baseline to beat) |
| App builders for indies | Lovable, Bolt, Replit | our audience, instant start, select-and-edit on the preview | any existing codebase and stack; product, marketing, release; no hosting lock-in |
| Feedback on a live site | Jam, BugHerd, FeedBug, Marker.io | point and click, console and network logs, to an agent through MCP | a mark lands in the right party's lens, its map's parts, the decisions' context |

Two warnings from this table: **marking a live page and sending its logs to an agent is table stakes now** (spec 115's
marks alone set us apart from no one), and **"an AI team with roles" reads as derivative** (BMAD; Task Master even has
our Taskmaster's name).

### What would prove it, what would refute it

- **Proves:** on the same real tasks, goals made in Orkboard are accepted the first time clearly more often than plans
  made in Claude Code's plan mode, with fewer plan changes and fewer questions after the start; makers pick the
  *studio that sees your product* headline over the *specs for your agents* one; makers name the grounding in the real
  product (maps, Play) as why they stay.
- **Refutes:** no difference in first-time acceptance against plan mode; makers find the way of a goal (route, Talk,
  decision, sections) slower than it is worth; makers who try it come for the agents' board and ignore the specs.

### How we test it

1. **The head-to-head** (first, cheapest, strongest): 10–15 real tasks on two or three real projects (a web app, a
   mobile app, a game), each done twice: in Orkboard and with Claude Code's plan mode alone, the same model. Measured:
   accepted the first time (yes/no by the person, blind to which way made it), plan changes and forks after the start,
   questions asked during the work, goals back from the discard, the person's minutes, the tokens. **Holds** if
   Orkboard wins first-time acceptance by 20 points or more at no more than twice the person's minutes.
2. **Twenty conversations** with solo makers of web apps, mobile apps and games who build with AI agents: what goes
   wrong between what they want and what the agent builds; how they write it down today; reactions to the two
   statements.
3. **A landing page, two headlines** (*a studio that sees your product* · *specs for your agents*), the same page
   under them, measured by the install or the waitlist.

### What already exists for it, and what is missing

- **Exists:** the maps from code and their leaders' lenses (specs 89, 102, 108, 109); Talk, the decision, the sections,
  forks (spec 99); the decisions log; the gate.
- **Missing:** a one-page brief of the project every leader reads (whom, what hurts, why us, money, pillars, what we
  leave out); rubrics weighted by the project's stage; a shorter way for a goal one party can do alone; Play as a map
  (spec 115); **any measure of how good what was wanted turned out**: first-time acceptance, plan changes after the
  start, forks, goals back from the discard.

### Risks

- **Ceremony**: the reviews' main complaint about Kiro and BMAD is a sledgehammer for a nut on small changes; a goal's
  full way has the same fault. The short way must be the default; the ceremony should grow with the risk.
- **The playful look**: a hook for indie game makers, maybe less so for a SaaS maker. Test it on both.
- **Reach and money**: Spec Kit has GitHub, Kiro has AWS, Lovable spreads by itself; Orkboard is open source
  (Apache-2.0), local, with a VS Code extension. The channels (indie communities, itch, game development) and how it
  earns are not decided.

### If it holds

A decision (the next §) and the README's first line, for example: *Orkboard turns what you want into specs grounded in
your real product, hands them to the AI tools you use, and checks what comes back.* Then the brief, the stage-weighted
rubrics, the shorter way and the measures above come before new faces.

### Sources (read 31 October 2026)

- [7 Spec-Driven Development Tools: Spec Kit, Kiro, OpenSpec, Tessl & More](https://ssojet.com/blog/best-spec-driven-development-tools)
- [Best Spec-Driven Development Tools (2026)](https://codemyspec.com/blog/best-spec-driven-development-tools)
- [GitHub Spec Kit vs Kiro vs Claude Code SDD Workflows](https://glukhov.org/ai-devtools/ai-coding-assistants/spec-kit-vs-kiro-vs-claude-code/)
- [spec-compare](https://github.com/cameronsjo/spec-compare)
- [BMAD Method: AI development](https://www.augmentcode.com/guides/bmad-method-ai-development)
- [BMAD-METHOD: agents](https://www.mintlify.com/bmad-code-org/BMAD-METHOD/concepts/agents)
- [Jam](https://www.jam.dev), [BugHerd](https://www.stork.ai/en/bugherd), [FeedBug](https://webcatalog.io/en/apps/feedbug)
