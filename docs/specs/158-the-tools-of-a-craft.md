# 158. The tools of a craft: what each party works with, a tool that is not its harness; every craft's tools at once, Art's paid pictures and sound first

Goal: `llm-wiki/general/pages/ideas/158-the-tools-of-a-craft.md` (route: product, design, tech). The person's request is the page's *Gist*. This spec is the leaders' sections of that page as they wrote them in the Board's flow (Talk, then their sections), with the person's answers above them; each leader's *Talk* stays in the page. **Builds:** the goal's stages (the page's *Stages*, the Taskmaster's), each task on local Codex, in the branch `claude/specialization-tools-32f7c8`, into a pull request; main is the person's.

## The person's answers (8 November 2026)

1. Art only, or one frame for all? — **every craft's tools at once**.
2. Own money gateway now or later? — **later: a cap a run in code first**.
3. Suno: official API or a wrapper? — **ElevenLabs's official API first, Suno once official**.
4. Which word, beside "AI tool"? — **tool, and the AI tool renamed harness**.
5. Where is a paid run's money agreed? — **its cap on the stall's plate, each run's cost in its receipt line**.
6. Where does a tool's run sit? — **in a pick task: the tool makes its variants**.

## Product

### Why
- A party's job is its craft's work, not words about it: today Art writes briefs and SVG because no tool makes a picture safely or a sound at all.
- A tool spends the person's own money on the person's key, so the product's promise is that it never spends above what was agreed, and says it in money.
- Whether a paid asset is worth keeping is untested; the goal must count it, or nobody learns if the tools are worth their price.
### Done when
- [test] When a pick task's tool would cost more than the cap a run set on its stall's plate, then no call is made and the pick says in words the price and the cap.
- [test] When a paid tool's run ends, then its receipt line says what the run cost in money, and the sum of its calls is never above its cap.
- [test] When the person opens the inventory on Art's chair, as first met, then each paid tool's plate says its cap in money and what leaves this computer, and one with no key reads not here with why.
- [test] When the person answers a pick a tool made (picked or skipped), then an event keeps the tool, the run's cost and the answer, with no prompt text and no key in it.
- [test] When Product's map is read, then its hypotheses hold H5 (a paid asset is kept at its price), its signal the kept share of Art's first ten paid picks.
### Checks
- No test of the gate reaches a paid API: every paid tool is faked there, and a test fails if a real endpoint is called.
- Money is said as money (an amount and its currency), never as tokens, credits or a percentage, on the plate, the pick and the receipt.
- No tool without an official API is laid on any rug: Suno is absent until it has one; ElevenLabs is the only sound tool.
- A run above its cap is locked from Silent (§266.5): it asks by Pen or Choice, never spends and says so later.
- The pick's event carries what `orkboard usage` may carry only with the person's yes: no prompt, no key, no file.
### Will be
- new hyp:h5 — the belief the paid tools rest on (a generated asset is kept at its price), with its signal, in docs/hypotheses.md
### Out
- No money gateway: a cap a run in code first, the gateway a step of its own (the person's answer).
- No Suno wrapper and no tool through an unofficial API; no tool a leader proposes (§256.6's later step).
- No recipe engine's `tool` step (§256.7): a tool's run sits in a pick task.
### Risks
- medium
- Every craft's tools at once is a frame before one paid Art asset is kept; it may grow past what Art's two tools need.
- A price a call may not be known before the call; a cap then guards only after the first bill, so the plate must say it is an estimate.
- This repository seats no Art party: H5 is measured on a project with one (the owner's game), not on the owner's week here.
- Renaming the AI tool to harness touches every face's words; Orkline shares the settings, so a missed `was` reads as two concepts.
### Defaults
- A paid tool is off until the person sets its cap on the plate; there is no default amount, so no money is spent unagreed.
- "Every craft's tools at once": each craft's stall lays the tools that exist now; the only paid ones are Art's picture and sound.
- A run's receipt line is the line the pick shows under its variants (and the task's record), saying its cost after the run.
- The cap is a run's, in the currency the API bills; a day's or a month's cap waits for the gateway.

## Design

### Why
- A tool spends the person's money on the person's key; the person must see the cap and what leaves this computer before a run, not learn it from the bill (Nielsen 1, 5).
- Two wares called "tool" on one rug read as one thing (Nielsen 4): the harness and the tools must look and read apart, in every face, in one word each.
- No new face: the tools lie on the stall's rug (spec 157) and their work comes back as today's pick, so the person's way through the screens stays the same.
### Done when
- [test] When the person opens the inventory on a leader's chair of a craft with tools, as first met, then the rug lays a shelf *Its tools* apart from *Its harness*, and no face says "AI tool".
- [test] When a paid tool's ware lies on Art's rug with no cap, as first met, then its plate reads *Set a cap*; pressed or Enter, a labelled money field opens, and no take is sent until a cap is given.
- [test] When a tool has no key on this computer or its harness cannot run it, then its plate reads *not here* and its why is text seen on focus and on hover, never a title alone.
- [test] When a pick a tool made opens in the hand, as first met, then a receipt line under its variants names the tool and its cost of its cap in money; a pick the cap stopped opens that plate in one press.
- [look] When the stall is drawn on Art's chair at 1280 × 800, then the tools' shelf fits the rug in orkUI's tokens, money in the warning colour with its words, and nothing overflows the table.
### Checks
- The plate's money, *not here* and *Set a cap* text meet 4.5:1 on the rug; the cap field's target is 24 × 24 px at least (WCAG 1.4.3, 2.5.8).
- The cap field has a visible label and its currency, and a wrong amount is said in words beside it, never by colour alone (WCAG 3.3.1, 3.3.2, 1.4.1).
- Keyboard order on a leader's rug: heroes, the ways, its harness, its tier, its tools; Esc closes the cap field before the inventory; focus is always seen (WCAG 2.4.3, 2.4.7).
- A tool's mark is an orkUI sign (picture, sound) or icon, no new picture, colour or font (`tests/test_design_system.py`); a ware's fly honours `prefers-reduced-motion`.
- Every word is today's at its source: *harness*, *tool*, *Set a cap*, *What leaves this computer* in `TERMS`, the old *AI tool* in `was` (`tests/test_gui_wording.py`).
### Will be
- none — this repository's screens have no router, so Design's map reads no screen here; the faces changed are the stall (table/stall.js, stallfaces.js) and the pick's line.
### Out
- No new screen, drawer, Settings row or Choice card a run: the cap lives on the plate, the cost on the pick's receipt line (the person's answer).
- No face for the key itself: *not here — no key* points to Settings' sign-ins, where keys are added today.
- No phone inventory and no day's or month's cap face (spec 157's later; the gateway is a step of its own).
### Risks
- medium
- The rename to *harness* touches every face and Orkline's shared words; one missed label reads as two concepts on the same rug.
- A price a call may be an estimate: a plate saying *about* that the bill exceeds breaks the trust the plate is for.
- Art's rug grows crowded (heroes, ways, harness, tier, tools) and may overflow at 1280 × 800 or push the cap field off the table.
- A cap field on a small plate risks a target too small and a focus lost when the stall redraws after a take.
### Defaults
- The tools are a shelf of small wares of their own, *Its tools*, after the harness and the tier; a craft with no tool now lays no tools shelf (§267.5).
- Taking a tool allows it for the party; a paid tool is taken only with a cap, given in the field its plate opens, in the API's currency.
- A plate's why (*no key on this computer*, *its harness cannot run it*) is a visible line on focus and hover, not only a `title`, unlike today's locked plate.
- The receipt line reads *Made by <tool> · <cost> of a <cap> cap*; a pick the cap stopped says the price and the cap and links to that party's plate.

## Tech

### Why
- A tool is the first caller in Orkboard that spends the person's money on the person's key: the cap must be held by code before each request, never by a model's restraint.
- The seam is there: a pick reads files from any maker (idea_pick.read), so a tool fills today's pick and the runner gains a call, not a body; idea_runner.py is already 611 lines.
- One registry for every craft's tools, read by the stall and the runner alike, keeps what a plate says and what a run does from drifting apart.
### Done when
- [test] When a pick task names a tool its party has taken, then Orkboard runs that tool's maker instead of a harness session, the pick opens as today's, and pick.json keeps the tool, the round's cost and its cap in money.
- [test] When a tool's next request would bring the round's spend above its cap, then no request leaves the computer and the task stops with the price and the cap in words.
- [test] When a tool's task is run again after a crash or a send back, then the spend reserved before each earlier request is still counted, so the round never pays above its cap.
- [test] When the gate runs the suite, then no test reaches a paid tool's host: each maker is faked, and a test fails when a real endpoint is called.
- [test] When a party's tools are read for its chair, then each says here or not here with its why (no key on this computer, its harness cannot make it, no official API), and the runner refuses a pick with a tool not here.
### Checks
- A tool's run lives in a core module of its own; idea_runner.py gains one call where a pick's session runs, and nothing new imports gui/ (tests/test_architecture.py).
- A key is read only at the request and appears in no page, plan.json, pick.json, log, event or prompt; a test greps them for a fake key after a run.
- Every request goes over HTTPS to its tool's fixed host with a timeout; an answer over idea_pick's limits or of the wrong mime fails in words, its files removed.
- The spend is written atomically in the goal's state before a request and settled after it, so a retry never pays twice unseen.
- A party page's `tool` and `tools` keep naming its harness (code keeps its names); the taken tools and caps lie under a new key, and a page without it reads as none taken.
### Will be
- changed orkboard/realm — the tools' registry (every craft's tools, their backend, price and why not here), the page's taken tools and caps, TERMS' *harness* and *tool*
- changed orkboard/core — a tool's run beside the pick in a module of its own, the spend and its cap; the runner calls it where a pick's session runs
- changed orkboard/gui — the stall's tools shelf and its cap's take; the pick's cost and cap sent for its receipt line
### Out
- No MCP tool in an agent's hands and no code tool a leader proposes (§256.6): their kinds are in the registry's shape, none is run.
- No money gateway and no day's or month's cap (the person's answer); no recipe engine's `tool` step (§256.7).
- No Suno and no tool through an unofficial API; agy's pictures stay a harness's own making.
### Risks
- medium
- ElevenLabs bills credits from a plan, not money a call: its price in money is an estimate from the plan's rate, so the cap guards an estimate.
- A request that times out may still be billed: the reserve counts it, so a cap may stop a round the bill says had room.
- idea_runner.py and idea_task.py are hotspots; a tool's branch written inside them would push them past the split line.
- A new folder `orkboard/tools/` would shadow `orkboard/tools.py` (the harnesses' detection); the new modules must be named apart.
### Defaults
- The picture tool is OpenAI's Images API and the sound tool ElevenLabs's sound-effects API, each a maker with its fixed host and a dated price table in code.
- A key is read from the keychain (`orkcraft-ideas`, account `tools/<tool id>`), else its API's own variable (`OPENAI_API_KEY`, `ELEVENLABS_API_KEY`).
- A party's taken tools and their caps lie on its page under `craft_tools` (the Board, shared); a key and a host stay on the machine.
- A plan's pick names its tool (`pick.tool`), one its party has taken and that is here; the cap is one round's of a pick task.
