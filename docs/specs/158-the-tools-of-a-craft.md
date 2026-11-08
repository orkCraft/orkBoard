# 158. The tools of a craft: one shape for every craft's makers, Art's Picture maker and Sound maker in it, run by Orkboard in a pick under a cap

Goal: `llm-wiki/general/pages/ideas/158-the-tools-of-a-craft.md` (route: product, design, tech). The person's request is the page's *Gist*. This spec is the leaders' sections of that page as they wrote them in the Board's flow (Talk, then their sections), with the person's answers above them; each leader's *Talk* and *Accepted* stay in the page. **Builds:** the goal's stages (the page's *Stages*, the Taskmaster's), each task on local Codex, in the branch `claude/specialization-tools-32f7c8`, into a pull request; main is the person's.

## The person's answers (8 November 2026)

1. Art only, or one frame for all? — **one shape for every craft, only Art's tools in it**. (it replaces their first answer, every craft's tools at once)
2. Own money gateway now or later? — **later: a cap a run in code first**.
3. Suno: official API or a wrapper? — **ElevenLabs's official API first, Suno once official**.
4. Which word, beside "AI tool"? — **maker: Harness.makes' word, a Picture maker, a Sound maker**. (it replaces their first answer, tool and the AI tool renamed harness)
5. Where is a paid run's money agreed? — **its cap on the stall's plate, each run's cost in its receipt line**.
6. Where does a tool's run sit? — **in a pick task: the tool makes its variants**.

## Product

### Why
- A party's job is its craft's work, not words about it: today Art writes briefs and SVG because nothing makes a picture safely or a sound at all.
- A maker spends the person's own money on the person's key, so the product's promise is that it never spends above what was agreed, and says it in money.
- Whether a paid asset is worth keeping is untested: Art's two makers come first and alone, so the goal counts it before any other craft gets one.
### Done when
- [test] When a pick task's maker would cost more than the cap set on its plate, then no call is made and the pick says in words the price and the cap.
- [test] When a paid maker's run ends, then its receipt line says what the run cost in money, and the sum of its calls is never above its cap.
- [test] When the person opens the inventory, as first met, then Art's chair alone lays makers, each paid plate saying its cap in money and what leaves this computer, one with no key not here with why.
- [test] When the person answers a pick a maker made (picked or skipped), then an event keeps the maker, the run's cost and the answer, with no prompt text and no key in it.
- [test] When Product's map is read, then its hypotheses hold H5 (a paid asset is kept at its price), its signal the kept share of Art's first ten paid picks.
### Checks
- Money is said as money (an amount and its currency), never as tokens, credits or a percentage, on the plate, the pick and the receipt.
- One shape, Art's makers only: the registry holds the Picture maker and the Sound maker (ElevenLabs's), no Suno and no other craft's maker.
- A person reads *maker* (a Picture maker, a Sound maker) beside the *AI tool*, which keeps its name; no face renames the AI tool *harness*.
- A run above its cap is locked from Silent (§266.5): it asks by Pen or Choice, never spends and says so later.
- The pick's event carries what `orkboard usage` may carry only with the person's yes: no prompt, no key, no file.
### Will be
- new hyp:h5 — the belief the paid makers rest on (a generated asset is kept at its price), with its signal, in docs/hypotheses.md
### Out
- No money gateway: a cap a run in code first, the gateway a step of its own (the person's answer).
- No Suno wrapper, no maker through an unofficial API, no maker for another craft and no code tool a leader proposes (§256.6's later step).
- No recipe engine's `tool` step (§256.7): a maker's run sits in a pick task.
### Risks
- medium
- The one shape is built for crafts that have no maker yet; it may grow fields Art's two makers never use.
- A price a call may not be known before the call (ElevenLabs bills credits); the cap then guards an estimate, so the plate must say so.
- This repository seats no Art party: H5 is measured on a project with one (the owner's game), not on the owner's week here.
- Stages E and F still rename the AI tool *harness*; done as written they undo the person's answer 4 and touch every face for nothing.
### Defaults
- A paid maker is off until the person sets its cap on the plate; there is no default amount, so no money is spent unagreed.
- One shape: the registry's kinds (code, MCP, API) stand for every craft, but only Art's two makers are in it, so other crafts' rugs lay none.
- *Maker* is the word a person reads; code keeps its names (`craft_tools`, `pick.tool`, `realm/craft_tools.py`), as CLAUDE.md's wording rule says.
- A cap is one round's, in the currency the API bills, its cost said after the run in the receipt line under the pick's variants; a day's or month's cap waits for the gateway.

## Design

### Why
- A maker spends the person's money on the person's key; the person must see the cap and what leaves this computer before a run, not learn it from the bill (Nielsen 1, 5).
- The rug already says *Its AI tool*; a second "tool" beside it would read as the same ware (Nielsen 4), so the maker gets its own word and the AI tool keeps its name everywhere.
- No new face: Art's makers lie on the stall's rug (spec 157) and their work comes back as today's pick, so the person's way through the screens stays the same.
### Done when
- [test] When the person opens the inventory on Art's chair, as first met, then the rug lays a shelf *Its makers* (a Picture maker, a Sound maker) apart from *Its AI tool*; another craft's chair lays none.
- [test] When a paid maker's ware lies on Art's rug with no cap, as first met, then its plate reads *Set a cap*; pressed or Enter, a labelled money field opens, and no take is sent until a cap is given.
- [test] When a maker has no key on this computer or its AI tool cannot run it, then its plate reads *not here*, its why in words seen on focus and on hover, never a title alone, and never says "harness".
- [test] When a pick a maker made opens in the hand, as first met, then a receipt line under its variants names the maker and its cost of its cap in money; a pick the cap stopped opens that plate in one press.
- [look] When the stall is drawn on Art's chair at 1280 × 800, then the makers' shelf fits the rug in orkUI's tokens, money in the warning colour with its words, and nothing overflows the table.
### Checks
- The plate's money, *not here* and *Set a cap* text meet 4.5:1 on the rug; the cap field's target is 24 × 24 px at least (WCAG 1.4.3, 2.5.8).
- The cap field has a visible label and its currency, and a wrong amount is said in words beside it, never by colour alone (WCAG 3.3.1, 3.3.2, 1.4.1).
- Keyboard order on Art's rug: heroes, the ways, its AI tool, its tier, its makers; Esc closes the cap field before the inventory; focus seen and kept after the stall redraws (WCAG 2.4.3, 2.4.7).
- A maker's mark is an orkUI sign (picture, sound) or icon, no new picture, colour or font (`tests/test_design_system.py`); a ware's fly honours `prefers-reduced-motion`.
- Words at their source: *maker*, *Set a cap* in `TERMS`, *AI tool* kept as it is; no face says "harness" (`tests/test_gui_wording.py`); an estimated price reads *about* on plate and receipt.
### Will be
- none — this repository's screens have no router, so Design's map reads no screen here; the faces changed are the stall (table/stall.js, stallfaces.js) and the pick's line.
### Out
- No new screen, drawer, Settings row or Choice card a run: the cap lives on the plate, the cost on the pick's receipt line (the person's answer).
- No rename: the AI tool keeps its name in every face, the phone's too (the person's answer 4); no face for the key, *not here — no key* points to Settings' sign-ins.
- No phone inventory, no makers shelf for a craft but Art (the person's answer 1), and no day's or month's cap face (the gateway is a step of its own).
### Risks
- medium
- The host's whys say *its harness cannot make it* (realm/craft_tools.py); shown raw on a plate, they put a second word for the AI tool on the rug.
- A seat's chip *needs pictures* (Harness.makes) and a Picture maker may read as one thing; the plate must say the maker runs in Orkboard on the person's key.
- A price a call may be an estimate (ElevenLabs's credits): a plate saying *about* that the bill exceeds breaks the trust the plate is for.
- Art's rug grows crowded (heroes, ways, AI tool, tier, makers) and may overflow at 1280 × 800 or push the cap field off the table.
### Defaults
- The makers are a shelf of small wares of their own, *Its makers*, after the AI tool and the tier, on Art's chair only; a craft with no maker lays no shelf (§267.5, one shape).
- A plate is named by what it makes, *Picture maker* or *Sound maker*, its service (OpenAI Images, ElevenLabs Sound Effects) under it; a paid maker is taken only with a cap, in the API's currency.
- A plate's why is a visible line on focus and hover in the face's words: *no key on this computer*, *its AI tool cannot make it*, *no official API*, never a `title` alone.
- The receipt line reads *Made by the <maker> · <cost> of a <cap> cap* (*about* before an estimate); a pick the cap stopped says the price and the cap and opens that party's plate.

## Tech

### Why
- A maker is the first caller in Orkboard that spends the person's money on the person's key: the cap must be held by code before each request, never by a model's restraint.
- The seam is there: a pick reads files from any maker (idea_pick.read), so a maker fills today's pick and the runner gains a call, not a body; idea_runner.py is already 611 lines.
- One shape read by the stall and the runner alike keeps a plate and a run from drifting; with only Art's two makers in it, another craft's maker is a row later, not a frame.
### Done when
- [test] When a pick task names a maker its party has taken, then Orkboard runs that maker instead of an AI tool's session, the pick opens as today's, and pick.json keeps the maker, the round's cost and its cap in money.
- [test] When a maker's next request would bring the round's spend above its cap, then no request leaves the computer and the task stops with the price and the cap in words.
- [test] When a maker's task is run again after a crash or a send back, then the spend reserved before each earlier request is still counted, so the round never pays above its cap.
- [test] When the gate runs the suite, then no test reaches a paid maker's host: each maker is faked, and a test fails when a real endpoint is called.
- [test] When a party's makers are read for its chair, then only Art's lays any (a Picture maker, a Sound maker), each here or not here with its why (no key on this computer, its AI tool cannot make it, no official API), and the runner refuses a maker not here.
### Checks
- A maker's run lives in a core module of its own; idea_runner.py gains one call where a pick's session runs, and nothing new imports gui/ (tests/test_architecture.py).
- A key is read only at the request and appears in no page, plan.json, pick.json, log, event or prompt; a test greps them for a fake key after a run.
- Every request goes over HTTPS to its maker's fixed host with a timeout; an answer over idea_pick's limits or of the wrong mime fails in words, its files removed.
- The spend is written atomically in the goal's state before a request and settled after it, so a retry never pays twice unseen.
- Every why, error and stop the host sends a face says *maker* (Picture maker, Sound maker) and *AI tool*, never "harness"; code keeps its names (`craft_tools`, `pick.tool`, `tool`, `tools`).
### Will be
- changed orkboard/realm — one shape for every craft's makers (kind code, MCP or API; fixed host; dated price; why not here) holding only Art's two, and a party page's makers and caps
- changed orkboard/core — a maker's run beside the pick in a module of its own, the spend and its cap; the runner calls it where a pick's session runs
- changed orkboard/gui — the stall's makers shelf and its cap's take; the pick's maker, cost and cap sent for its receipt line
### Out
- No maker for another craft, no MCP server in an agent's hands and no code tool a leader proposes (§256.6): their kinds are in the shape, none is in the registry (answer 1).
- No money gateway and no day's or month's cap (answer 2); no recipe engine's `tool` step (§256.7).
- No rename: the AI tool keeps its name, code keeps its names; no Suno, no maker through an unofficial API; agy's pictures stay an AI tool's own making.
### Risks
- medium
- ElevenLabs bills credits from a plan, not money a call: its price in money is an estimate from the plan's rate, so the cap guards an estimate.
- A request that times out may still be billed: the reserve counts it, so a cap may stop a round the bill says had room.
- idea_runner.py and idea_task.py are hotspots; a maker's branch written inside them would push them past the split line.
- Stages A–D wrote the host's words as "tool" and "its harness cannot make it" (realm/craft_tools.py, core/craft_run.py, core/craft_pick.py); left, they put a second word on the rug.
### Defaults
- The Picture maker is OpenAI's Images API and the Sound maker ElevenLabs's sound-effects API, each with its fixed host and a dated price table in code.
- A key is read from the keychain (`orkcraft-ideas`, account `tools/<maker id>`), else its API's own variable (`OPENAI_API_KEY`, `ELEVENLABS_API_KEY`).
- A party's taken makers and their caps lie on its page under `craft_tools` (the Board, shared); a key and a host stay on the machine; `pick.tool` names the maker's id.
- The modules keep their names (`realm/craft_tools.py`, `core/craft_*.py`); only what a person reads says *maker*; the cap is one round's of a pick task.
