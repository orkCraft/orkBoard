---
owner: board
kind: idea
track: design
order: 5
size:
priority: normal
short: Ввести инструменты
phase: work
route: product, design, tech
spec: docs/specs/158-the-tools-of-a-craft.md
by: claude-code
schema: 3
---
# Хочу ввести инструменты специализаций: то, чем пользуется каждая партия,…

## Gist
Хочу ввести инструменты специализаций: то, чем пользуется каждая партия, причём у одного харнеса инструмент может быть, у другого нет. Начать с art: сейчас картинки умеет делать только agy (и он experimental, с риском бана), звук не делает никто, и партия «Art and sound» на деле пишет брифы и SVG.

Что я про это думаю (лидеры пусть спорят):
- Инструмент — не харнес. Харнес думает и тратит ману, инструмент — это руки, часто за настоящие деньги на моём ключе. Место может сделать нужное, если это умеет его харнес или к нему подключён инструмент (Harness.makes и needs ролей уже есть, спека 91 §6).
- Сейчас инструменты у нас в основном код, детерминированные тулы (§256.6). Но инструмент может быть и MCP-сервером или внешним API, например Suno, ElevenLabs или генератор картинок. Это одно понятие с разными бэкендами.
- Для генерации я склоняюсь к шагу рецепта, который запускает сам Orkboard (tool → pick), а не к MCP в руках агента: так деньги считает и режет код, и это работает с любым харнесом. MCP у агента — для работы туда-сюда (Figma, Sentry).
- Что партии разрешено, хранится на Доске; каким сервером и ключом это делается — на машине, как servers у операций.
- Настраивается картами в инвентаре выбранной специализации (лавка, спека 157). На табличке деньги словами, «не здесь» с причиной, что уходит с компьютера.

Вопросы, которые решу я, задайте их мне:
1) Слово для этого в TERMS: «AI tool» уже значит харнес.
2) Только art на старт или каркас сразу на все ремёсла?
3) Свой шлюз для контроля денег сразу или вторым шагом?
4) Suno: ждём официального API или берём обёртку как experimental?

## Why

## Done when

## Out

## Risks

## Depends on

## Stages
Tech's stages first (the registry, the makers, the pick and the cap: what the faces read), then Design's (the words, the shelf, the cap field, the receipt line), then Product's (money end to end, the answer counted). Each party's leader accepts its stages before the next party's begin.

- [ ] A. The tools' registry and a party's taken tools
  - Tech. A realm module of its own, named apart from `orkboard/tools.py` (e.g. `realm/craft_tools.py`): every craft's tools, each with its kind (code, MCP, API), its fixed host, its dated price table in money and whether its API is official; OpenAI's Images API (Art, picture) and ElevenLabs's sound effects (Art, sound), no Suno. Here or not here with its why: no key on this computer (keychain `orkcraft-ideas`, account `tools/<tool id>`, else `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`), its harness cannot make it, no official API. A party page's `craft_tools` (taken tools and each one's cap in money) read and written; a page without it reads as none taken; `tool` and `tools` keep naming the harness.
  - Proves (Tech): When a party's tools are read for its chair, then each says here or not here with its why (no key on this computer, its harness cannot make it, no official API) — the reading half; the runner's refusal is C.
- [ ] B. The makers, faked in the gate
  - Tech. A core module of its own (e.g. `core/craft_run.py`): a Picture maker and a Sound maker, each over HTTPS to its tool's fixed host with a timeout, its transport injectable; an answer over idea_pick's limits (120 MB, its mimes) or of the wrong mime fails in words, its files removed. A guard in `tests/conftest.py` fails any test that opens a connection to a paid tool's host; each maker's tests run on a fake transport.
  - Proves (Tech): When the gate runs the suite, then no test reaches a paid tool's host: each maker is faked, and a test fails when a real endpoint is called.
- [ ] C. A pick a tool makes
  - Tech. `idea_pick.clean_ask` keeps `pick.tool`; the plan's prompt (`core/idea_plan.py`) offers the party's taken tools that are here, and a plan naming another is cleaned to none. The runner gains one call where a pick's session runs (`idea_runner.py` ~511): a pick naming a tool runs its maker into `.orkcraft-pick/` and its manifest, then `_variants` as today; pick.json keeps the tool, the round's cost and its cap in money. A pick with a tool not here is refused in words, no session started. Nothing new imports `gui/`.
  - Proves (Tech): When a pick task names a tool its party has taken, then Orkboard runs that tool's maker instead of a harness session, the pick opens as today's, and pick.json keeps the tool, the round's cost and its cap in money. · When a party's tools are read for its chair, then each says here or not here with its why (no key on this computer, its harness cannot make it, no official API), and the runner refuses a pick with a tool not here.
- [ ] D. The spend held under its cap
  - Tech. Before each request the price is reserved, written atomically in the goal's state, and settled after it; a request that would bring the round above its cap is not sent, and the task stops with the price and the cap in words. A run again after a crash or a send back reads the reserves already written. The key is read only at the request; a test runs a pick with a fake key and greps the page, plan.json, pick.json, the log, the events and the prompt for it.
  - Proves (Tech): When a tool's next request would bring the round's spend above its cap, then no request leaves the computer and the task stops with the price and the cap in words. · When a tool's task is run again after a crash or a send back, then the spend reserved before each earlier request is still counted, so the round never pays above its cap.
  - Then the Tech leader accepts A–D.
- [ ] E. Harness and tool: the words and the desktop
  - Design. `TERMS`: *harness* (the AI tool, its old spelling *AI tool* in `was`), *tool*, *Set a cap*; *What leaves this computer* kept. Every desktop face (`static/js/**`, `board.js`) and every host string a face shows (`gui/*.py`, `realm/*.py` labels and errors, `ideas_stall.LABELS` *Its harness*) says *harness*; the tests that check those strings follow. Code keeps its names (`ai_tool`, `tool`, `tools`).
  - Proves (Design): When the person opens the inventory on a leader's chair of a craft with tools, as first met, then the rug lays a shelf *Its tools* apart from *Its harness*, and no face says "AI tool" — the words half, on the desktop.
- [ ] F. Harness on the phone
  - Design. The phone's faces (`static/pwa/*.js`, `party.css`, `app.css`) and their browser tests say *harness* where they said *AI tool*; a test scans the page's and the phone's templates for "AI tool" and finds none.
  - Proves (Design): When the person opens the inventory on a leader's chair of a craft with tools, as first met, then the rug lays a shelf *Its tools* apart from *Its harness*, and no face says "AI tool" — every face.
- [ ] G. The tools' shelf on the rug
  - Design. `ideas_stall.py` lays *Its tools* after the harness and the tier, for a craft with tools only (none for a craft with none); a tool's plate says its cap in money, what leaves this computer, and *not here* with its why as a visible line on focus and hover (`table/stall.js`, `stallfaces.js`, `stall.css`). The mark an orkUI sign; keyboard order heroes, ways, harness, tier, tools.
  - Proves (Design): When the person opens the inventory on a leader's chair of a craft with tools, as first met, then the rug lays a shelf *Its tools* apart from *Its harness*, and no face says "AI tool". · When a tool has no key on this computer or its harness cannot run it, then its plate reads *not here* and its why is text seen on focus and on hover, never a title alone.
- [ ] H. Set a cap
  - Design. A paid tool with no cap reads *Set a cap*; pressed or Enter, a labelled money field in the API's currency opens on the plate (24 × 24 px at least, a wrong amount said in words beside it); `ideas.stall_take` takes a paid tool only with a cap and writes `craft_tools`; Esc closes the field before the inventory; focus kept after the stall redraws. The stall drawn on Art's chair at 1280 × 800 in a browser test and a picture.
  - Proves (Design): When a paid tool's ware lies on Art's rug with no cap, as first met, then its plate reads *Set a cap*; pressed or Enter, a labelled money field opens, and no take is sent until a cap is given. · When the stall is drawn on Art's chair at 1280 × 800, then the tools' shelf fits the rug in orkUI's tokens, money in the warning colour with its words, and nothing overflows the table.
- [ ] I. The receipt line under a tool's pick
  - Design. The pick's host sends the tool, its cost and its cap from pick.json; the pick in the hand (`table/picking.js`, `pickbox.js`) shows *Made by <tool> · <cost> of a <cap> cap* under its variants; a pick the cap stopped says the price and the cap, and one press opens that party's plate in the inventory.
  - Proves (Design): When a pick a tool made opens in the hand, as first met, then a receipt line under its variants names the tool and its cost of its cap in money; a pick the cap stopped opens that plate in one press.
  - Then the Design leader accepts E–I.
- [ ] J. Money said and agreed, end to end
  - Product. Tests across the plate, the run and the pick: a cap set on Art's plate stops a pick whose tool would cost more, no call made, the pick saying the price and the cap; a run's receipt line in money and its calls' sum never above its cap; Art's chair as first met, each paid plate with its cap and what leaves this computer, one with no key *not here* with why. Money as an amount and its currency everywhere (ElevenLabs's credits said in money, an estimate said so); no Suno on any rug.
  - Proves (Product): When a pick task's tool would cost more than the cap a run set on its stall's plate, then no call is made and the pick says in words the price and the cap. · When a paid tool's run ends, then its receipt line says what the run cost in money, and the sum of its calls is never above its cap. · When the person opens the inventory on Art's chair, as first met, then each paid tool's plate says its cap in money and what leaves this computer, and one with no key reads not here with why.
- [ ] K. The answer counted, and H5
  - Product. `pick_answered` (`realm/event_log.py`, `core/idea_picking.py`) gains the tool and the run's cost for a tool's pick, never a prompt, a key or a file; H5 written in `docs/hypotheses.md` (a paid asset is kept at its price), its signal the kept share of Art's first ten paid picks, and Product's map reads it.
  - Proves (Product): When the person answers a pick a tool made (picked or skipped), then an event keeps the tool, the run's cost and the answer, with no prompt text and no key in it. · When Product's map is read, then its hypotheses hold H5 (a paid asset is kept at its price), its signal the kept share of Art's first ten paid picks.
  - Then the Product leader accepts J–K.

## Product
### Talk
- verdict: doubt — it rests on §256.7's `tool` step, not built (§256.9 orders it after the dossier and the cache); go if cut to Art's pictures and sound on official APIs, run as today's pick
- stance: Product backs the job (Art writes briefs and SVG, not assets), not a frame for every craft before one Art asset is picked and kept
- for: Art cannot do its job today: pictures only through agy, experimental with a ban risk; sound by no tool, though the library's sound-designer and composer need it
- against: this repository seats no Art party, so its owner's week cannot measure it; a gateway, machine keys and a new concept are a big cost before one paid asset is kept
- instead: one Orkboard-run pick for Art (an image API, ElevenLabs for sound), a money cap a run said in money; other crafts' tools once one is asked for
- assumes: a generated asset is good enough to pick and keep, at a price per asset worth paying — shown by: of Art's first ten paid picks, how many are kept in the project's tree
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
### Talk
- verdict: doubt — a leader's rug already says "Its AI tool" (ideas_stall.py LABELS); go once tools get a word of their own and a paid run says its money before it runs
- stance: Design lays it with no new face: a small ware on the leader's rug, its plate's money in words, and the pick card that already shows pictures and plays sound
- for: a ware "not here" with its why (no key on this computer, not in this AI tool) shows the person what is missing, where today Art only writes briefs and SVG
- against: two "tool" wares on one rug break consistency (Nielsen 4); a plate prices only what an estimator knows (spec 157 C.2), so money could show only after it is spent
- assumes: each paid tool's price a call is known before the call — shown by: the image API's and ElevenLabs's prices read by code, and a run's receipt matching its bill
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
### Talk
- verdict: doubt — core/idea_runner.py is 611 lines and §256.9 puts the `tool` step after the dossier and the cache; go if a tool fills today's pick (idea_pick's files) from a module of its own
- stance: Tech builds it in a step as a maker behind today's pick: Orkboard calls the API, writes idea_pick's variants and manifest, and PickMixin._variants carries on unchanged
- for: the seam is there: a pick already takes pictures and sounds as files (idea_pick.read), keys already live in the keychain (idea_secrets), so no new face and no new store
- against: a paid call from the runner is a new outbound caller holding a key; a retry or a crash after the call spends twice, and the gate must never reach a paid API
- instead: one Picture maker and one Sound maker in a core module of their own, faked in the gate, priced and capped before each call; the recipe engine and a gateway wait
- assumes: each API returns its variants within a task's time and inside idea_pick's limits (120 MB, its mimes) — shown by: one real call each, its seconds, bytes and mime logged
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

## Open questions
- Art only, or one frame for all? (**one shape for every craft, only Art's tools in it** / Art only, a shape of its own / every craft's tools at once) — one shape costs little more and §256.6's code tools fit it later; tools no party asked for wait
  - Answered: every craft's tools at once (the person, 2026-11-08)
- Own money gateway now or later? (**later: a cap a run in code first** / the gateway now) — Orkboard runs the step itself, so it prices each call before making it; a gateway pays only once an agent's MCP spends
  - Answered: later: a cap a run in code first (the person, 2026-11-08)
- Suno: official API or a wrapper? (**ElevenLabs's official API first, Suno once official** / Suno through a wrapper, experimental / wait for Suno's API, no sound till then) — a wrapper on the person's key repeats agy's ban risk
  - Answered: ElevenLabs's official API first, Suno once official (the person, 2026-11-08)
- Which word, beside "AI tool"? (**maker: Harness.makes' word, a Picture maker, a Sound maker** / hands, the Gist's word / tool, and the AI tool renamed harness) — a leader's rug already says "Its AI tool"; a second "tool" beside it reads as the same ware
  - Answered: tool, and the AI tool renamed harness (the person, 2026-11-08)
- Where is a paid run's money agreed? (**its cap on the stall's plate, each run's cost in its receipt line** / a Choice card before every paid run / the cap in Settings' … beside the key) — §266.5 locks money above what was agreed from Silent; a card a picture adds a step to every pick
  - Answered: its cap on the stall's plate, each run's cost in its receipt line (the person, 2026-11-08)
- Where does a tool's run sit? (**in a pick task: the tool makes its variants** / the recipes' `tool` step first, §256.7's engine) — the pick reads files from any maker; the engine is §256.9's fourth spec, not begun
  - Answered: in a pick task: the tool makes its variants (the person, 2026-11-08)

## Decisions
