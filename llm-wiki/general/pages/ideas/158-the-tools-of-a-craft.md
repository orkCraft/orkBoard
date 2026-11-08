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
Tech's stages first (the registry, the makers, the pick and the cap: what the faces read), then Design's (the makers' shelf, its *not here*, the cap field, the receipt line), then Product's (money end to end, the answer counted). Each party's leader accepts its stages before the next party's begin. A–D were built and accepted against Tech's first section (its words then *tool* and *harness*); the person's answers 1 and 4 changed after, so E and F bring them to the rewritten one. No stage renames the AI tool: *AI tool* stays in every face, code keeps its names (`craft_tools`, `pick.tool`, `tool`, `tools`, `realm/craft_tools.py`, `core/craft_*.py`).

- [x] A. The tools' registry and a party's taken tools
  - Tech. A realm module of its own, named apart from `orkboard/tools.py` (e.g. `realm/craft_tools.py`): every craft's tools, each with its kind (code, MCP, API), its fixed host, its dated price table in money and whether its API is official; OpenAI's Images API (Art, picture) and ElevenLabs's sound effects (Art, sound), no Suno. Here or not here with its why: no key on this computer (keychain `orkcraft-ideas`, account `tools/<tool id>`, else `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`), its harness cannot make it, no official API. A party page's `craft_tools` (taken tools and each one's cap in money) read and written; a page without it reads as none taken; `tool` and `tools` keep naming the harness.
  - Proves (Tech): When a party's tools are read for its chair, then each says here or not here with its why (no key on this computer, its harness cannot make it, no official API) — the reading half; the runner's refusal is C.
- [x] B. The makers, faked in the gate
  - Tech. A core module of its own (e.g. `core/craft_run.py`): a Picture maker and a Sound maker, each over HTTPS to its tool's fixed host with a timeout, its transport injectable; an answer over idea_pick's limits (120 MB, its mimes) or of the wrong mime fails in words, its files removed. A guard in `tests/conftest.py` fails any test that opens a connection to a paid tool's host; each maker's tests run on a fake transport.
  - Proves (Tech): When the gate runs the suite, then no test reaches a paid tool's host: each maker is faked, and a test fails when a real endpoint is called.
- [x] C. A pick a tool makes
  - Tech. `idea_pick.clean_ask` keeps `pick.tool`; the plan's prompt (`core/idea_plan.py`) offers the party's taken tools that are here, and a plan naming another is cleaned to none. The runner gains one call where a pick's session runs (`idea_runner.py` ~511): a pick naming a tool runs its maker into `.orkcraft-pick/` and its manifest, then `_variants` as today; pick.json keeps the tool, the round's cost and its cap in money. A pick with a tool not here is refused in words, no session started. Nothing new imports `gui/`.
  - Proves (Tech): When a pick task names a tool its party has taken, then Orkboard runs that tool's maker instead of a harness session, the pick opens as today's, and pick.json keeps the tool, the round's cost and its cap in money. · When a party's tools are read for its chair, then each says here or not here with its why (no key on this computer, its harness cannot make it, no official API), and the runner refuses a pick with a tool not here.
- [x] D. The spend held under its cap
  - Tech. Before each request the price is reserved, written atomically in the goal's state, and settled after it; a request that would bring the round above its cap is not sent, and the task stops with the price and the cap in words. A run again after a crash or a send back reads the reserves already written. The key is read only at the request; a test runs a pick with a fake key and greps the page, plan.json, pick.json, the log, the events and the prompt for it.
  - Proves (Tech): When a tool's next request would bring the round's spend above its cap, then no request leaves the computer and the task stops with the price and the cap in words. · When a tool's task is run again after a crash or a send back, then the spend reserved before each earlier request is still counted, so the round never pays above its cap.
  - The Tech leader accepted A–D against its first section (its *Accepted* above).
- [ ] E. The host says *maker* and *AI tool*
  - Tech. Only the words a person reads change, the ids and module names stay. `realm/craft_tools.py`: each registry row gains the maker's word a face shows (*Picture maker*, *Sound maker*) beside its service (*OpenAI Images*, *ElevenLabs Sound Effects*), and `for_party` sends both; `availability`'s why reads *its AI tool cannot make it* (not *its harness cannot make it*); `set_taken`'s errors say *maker* (*Each maker needs a known name and a positive cap in its currency*, *That maker is not for this party's craft*). `core/craft_run.py`'s `MakerError`s say the maker by its word (*The Picture maker has no key on this computer*, *The Sound maker's request failed or timed out*, *The Picture maker's answer is too large*…), `core/craft_pick.py`'s refusals (*The party has not taken that maker*, *<Picture maker> is not here: <why>*, *That maker cannot make this pick's kind*) and `core/craft_spend.py`'s stop and currency error (*The Picture maker's next request costs about …*, *about* before an estimate) likewise. `tests/test_craft_tools.py`, `test_craft_pick.py`, `test_craft_run.py` and `test_craft_spend.py` expect the new words, and one test collects every why, error and stop the four modules can send (each reason of `availability`, each `MakerError`, each refusal, the cap's stop) and finds *maker* or *AI tool* in each and "harness" (any case) in none.
  - Proves (Tech): When a party's makers are read for its chair, then only Art's lays any (a Picture maker, a Sound maker), each here or not here with its why (no key on this computer, its AI tool cannot make it, no official API), and the runner refuses a maker not here.
- [ ] F. A missing key reserves nothing
  - Tech. Today `craft_run._Maker._request` reserves the price before it reads the key, so a pick with no key leaves a reservation in `craft-spend.json` that is never settled and counts against the round's cap ever after. Read the key first (still at the request, never kept), and reserve only when a credential is in hand; `craft_pick.session` reads the maker's presence with its key (`check_key=True`) so *not here: no key on this computer* is said before a `Spend` is made. A request refused before it is handed to the transport writes no reserve; one handed to it stays reserved as today (it may be billed). Tests: a pick with no key leaves `craft-spend.json` absent or unchanged and calls no transport; then, with a fake key and a cap equal to one request's price, the same task's next run sends its one request and is not stopped by the cap.
  - Proves (Tech): When a maker's next request would bring the round's spend above its cap, then no request leaves the computer and the task stops with the price and the cap in words. · When a maker's task is run again after a crash or a send back, then the spend reserved before each earlier request is still counted, so the round never pays above its cap.
  - Then the Tech leader accepts A–F against its rewritten section: the five *Done when* lines in today's words, A–D's gate record with E's and F's.
- [ ] G. The makers' shelf on Art's rug
  - Design. `TERMS` (`realm/lexicon.py`) gains *maker* (*makers*), *Picture maker*, *Sound maker*, *Its makers*, *Set a cap*; *AI tool* and *What leaves this computer* kept as they are, nothing renamed. `gui/ideas_stall.py` lays a shelf *Its makers* after *Its AI tool* and *Its seats' tier*, read from `craft_tools.for_party`, on a chair whose craft has a maker (Art) only; another craft's chair lays no shelf. A plate is named by its maker's word, its service under it, its mark an orkUI sign (picture, sound) or icon; it says its cap in money (*about* before an estimate) in the warning colour with its words, and what leaves this computer (`leaves`). Keyboard order on Art's rug: heroes, the ways, its AI tool, its tier, its makers (`table/stall.js`, `stallfaces.js`, `stall.css`); a ware's fly honours `prefers-reduced-motion`. Tests: the stall's data for Art's chair and for Tech's, the shelf's place and order, `tests/test_design_system.py` and `tests/test_gui_wording.py` green.
  - Proves (Design): When the person opens the inventory on Art's chair, as first met, then the rug lays a shelf *Its makers* (a Picture maker, a Sound maker) apart from *Its AI tool*; another craft's chair lays none.
- [ ] H. *Not here* and its why
  - Design. A plate whose maker is not here reads *not here*, its why (the host's words from E: *no key on this computer*, *its AI tool cannot make it*, *no official API*) a visible line on focus and on hover, never a `title` alone, at 4.5:1 on the rug; *not here — no key* points to Settings' sign-ins, no key face of its own. A browser test focuses and hovers a no-key plate and reads the line; a wording test scans the rendered stall, its plates and the host strings it shows for "harness" and finds none.
  - Proves (Design): When a maker has no key on this computer or its AI tool cannot run it, then its plate reads *not here*, its why in words seen on focus and on hover, never a title alone, and never says "harness".
- [ ] I. Set a cap
  - Design. A paid maker with no cap reads *Set a cap*; pressed or Enter, a money field with a visible label and the API's currency opens on the plate (24 × 24 px at least, a wrong amount said in words beside it, never by colour alone); `ideas.stall_take` takes a paid maker only with a cap and writes `craft_tools` through `craft_tools.set_taken`, sending nothing until a cap is given; Esc closes the field before the inventory; focus seen and kept after the stall redraws. The stall drawn on Art's chair at 1280 × 800 in a browser test and a picture, the cap field open and closed.
  - Proves (Design): When a paid maker's ware lies on Art's rug with no cap, as first met, then its plate reads *Set a cap*; pressed or Enter, a labelled money field opens, and no take is sent until a cap is given. · When the stall is drawn on Art's chair at 1280 × 800, then the makers' shelf fits the rug in orkUI's tokens, money in the warning colour with its words, and nothing overflows the table.
- [ ] J. The receipt line under a maker's pick
  - Design. The pick's host sends from pick.json the maker's word (from `tool`), its cost and its cap; a pick the cap stopped sends the price, the cap, its party and the maker's id from the task's stop. The pick in the hand (`table/picking.js`, `pickbox.js`) shows *Made by the <maker> · <cost> of a <cap> cap* under its variants (*about* before an estimate); a pick the cap stopped says the price and the cap, and one press opens that party's inventory on the maker's plate. Tests: the line for a Picture maker's pick, the stopped pick's press.
  - Proves (Design): When a pick a maker made opens in the hand, as first met, then a receipt line under its variants names the maker and its cost of its cap in money; a pick the cap stopped opens that plate in one press.
  - Then the Design leader accepts G–J.
- [ ] K. Money said and agreed, end to end
  - Product. Tests across the plate, the run and the pick, on fake transports and a fake key: a cap set on Art's Picture maker plate stops a pick whose maker would cost more, no call made, the pick saying the price and the cap in words; a run's receipt line in money and the sum of its calls never above its cap; the inventory as first met, Art's chair alone laying makers, each paid plate with its cap in money and what leaves this computer, one with no key *not here* with why. Money as an amount and its currency on the plate, the pick and the receipt (ElevenLabs's price said in money, an estimate said *about*), never tokens, credits or a percentage; the registry holds the two makers only, no Suno and no other craft's.
  - Proves (Product): When a pick task's maker would cost more than the cap set on its plate, then no call is made and the pick says in words the price and the cap. · When a paid maker's run ends, then its receipt line says what the run cost in money, and the sum of its calls is never above its cap. · When the person opens the inventory, as first met, then Art's chair alone lays makers, each paid plate saying its cap in money and what leaves this computer, one with no key not here with why.
- [ ] L. The answer counted, and H5
  - Product. `pick_answered` (`realm/event_log.py`'s line, `core/idea_picking.py`'s emit) gains the maker's id and the run's cost for a maker's pick, from pick.json, never a prompt, a key or a file; a test answers a maker's pick (picked, then skipped) with a fake key and reads the event. H5 written in `docs/hypotheses.md` after H4 (a paid asset is kept at its price), its signal the kept share of Art's first ten paid picks, measured on a project that seats Art; Product's map reads it (`realm/hypotheses_file.py`).
  - Proves (Product): When the person answers a pick a maker made (picked or skipped), then an event keeps the maker, the run's cost and the answer, with no prompt text and no key in it. · When Product's map is read, then its hypotheses hold H5 (a paid asset is kept at its price), its signal the kept share of Art's first ten paid picks.
  - Then the Product leader accepts K–L.

## Product
### Talk
- verdict: doubt — it rests on §256.7's `tool` step, not built (§256.9 orders it after the dossier and the cache); go if cut to Art's pictures and sound on official APIs, run as today's pick
- stance: Product backs the job (Art writes briefs and SVG, not assets), not a frame for every craft before one Art asset is picked and kept
- for: Art cannot do its job today: pictures only through agy, experimental with a ban risk; sound by no tool, though the library's sound-designer and composer need it
- against: this repository seats no Art party, so its owner's week cannot measure it; a gateway, machine keys and a new concept are a big cost before one paid asset is kept
- instead: one Orkboard-run pick for Art (an image API, ElevenLabs for sound), a money cap a run said in money; other crafts' tools once one is asked for
- assumes: a generated asset is good enough to pick and keep, at a price per asset worth paying — shown by: of Art's first ten paid picks, how many are kept in the project's tree
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
### Talk
- verdict: doubt — a leader's rug already says "Its AI tool" (ideas_stall.py LABELS); go once tools get a word of their own and a paid run says its money before it runs
- stance: Design lays it with no new face: a small ware on the leader's rug, its plate's money in words, and the pick card that already shows pictures and plays sound
- for: a ware "not here" with its why (no key on this computer, not in this AI tool) shows the person what is missing, where today Art only writes briefs and SVG
- against: two "tool" wares on one rug break consistency (Nielsen 4); a plate prices only what an estimator knows (spec 157 C.2), so money could show only after it is spent
- assumes: each paid tool's price a call is known before the call — shown by: the image API's and ElevenLabs's prices read by code, and a run's receipt matching its bill
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
### Accepted
- met: When the person opens the inventory on Art's chair, as first met, then the rug lays a shelf *Its makers* (a Picture maker, a Sound maker) apart from *Its AI tool*; another craft's chair lays none.
- met: When a paid maker's ware lies on Art's rug with no cap, as first met, then its plate reads *Set a cap*; pressed or Enter, a labelled money field opens, and no take is sent until a cap is given.
- met: When a maker has no key on this computer or its AI tool cannot run it, then its plate reads *not here*, its why in words seen on focus and on hover, never a title alone, and never says "harness".
- met: When a pick a maker made opens in the hand, as first met, then a receipt line under its variants names the maker and its cost of its cap in money; a pick the cap stopped opens that plate in one press.
- met: When the stall is drawn on Art's chair at 1280 × 800, then the makers' shelf fits the rug in orkUI's tokens, money in the warning colour with its words, and nothing overflows the table.

## Tech
### Talk
- verdict: doubt — core/idea_runner.py is 611 lines and §256.9 puts the `tool` step after the dossier and the cache; go if a tool fills today's pick (idea_pick's files) from a module of its own
- stance: Tech builds it in a step as a maker behind today's pick: Orkboard calls the API, writes idea_pick's variants and manifest, and PickMixin._variants carries on unchanged
- for: the seam is there: a pick already takes pictures and sounds as files (idea_pick.read), keys already live in the keychain (idea_secrets), so no new face and no new store
- against: a paid call from the runner is a new outbound caller holding a key; a retry or a crash after the call spends twice, and the gate must never reach a paid API
- instead: one Picture maker and one Sound maker in a core module of their own, faked in the gate, priced and capped before each call; the recipe engine and a gateway wait
- assumes: each API returns its variants within a task's time and inside idea_pick's limits (120 MB, its mimes) — shown by: one real call each, its seconds, bytes and mime logged
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
### Accepted
- met: When a pick task names a maker its party has taken, then Orkboard runs that maker instead of an AI tool's session, the pick opens as today's, and pick.json keeps the maker, the round's cost and its cap in money.
- met: When a maker's next request would bring the round's spend above its cap, then no request leaves the computer and the task stops with the price and the cap in words.
- met: When a maker's task is run again after a crash or a send back, then the spend reserved before each earlier request is still counted, so the round never pays above its cap.
- met: When the gate runs the suite, then no test reaches a paid maker's host: each maker is faked, and a test fails when a real endpoint is called.
- met: When a party's makers are read for its chair, then only Art's lays any (a Picture maker, a Sound maker), each here or not here with its why (no key on this computer, its AI tool cannot make it, no official API), and the runner refuses a maker not here.

## Open questions
- Art only, or one frame for all? (**one shape for every craft, only Art's tools in it** / Art only, a shape of its own / every craft's tools at once) — one shape costs little more and §256.6's code tools fit it later; tools no party asked for wait
  - Answered: one shape for every craft, only Art's tools in it (the person, 2026-11-08; it replaces their first answer, every craft's tools at once)
- Own money gateway now or later? (**later: a cap a run in code first** / the gateway now) — Orkboard runs the step itself, so it prices each call before making it; a gateway pays only once an agent's MCP spends
  - Answered: later: a cap a run in code first (the person, 2026-11-08)
- Suno: official API or a wrapper? (**ElevenLabs's official API first, Suno once official** / Suno through a wrapper, experimental / wait for Suno's API, no sound till then) — a wrapper on the person's key repeats agy's ban risk
  - Answered: ElevenLabs's official API first, Suno once official (the person, 2026-11-08)
- Which word, beside "AI tool"? (**maker: Harness.makes' word, a Picture maker, a Sound maker** / hands, the Gist's word / tool, and the AI tool renamed harness) — a leader's rug already says "Its AI tool"; a second "tool" beside it reads as the same ware
  - Answered: maker: Harness.makes' word, a Picture maker, a Sound maker (the person, 2026-11-08; it replaces their first answer, tool and the AI tool renamed harness)
- Where is a paid run's money agreed? (**its cap on the stall's plate, each run's cost in its receipt line** / a Choice card before every paid run / the cap in Settings' … beside the key) — §266.5 locks money above what was agreed from Silent; a card a picture adds a step to every pick
  - Answered: its cap on the stall's plate, each run's cost in its receipt line (the person, 2026-11-08)
- Where does a tool's run sit? (**in a pick task: the tool makes its variants** / the recipes' `tool` step first, §256.7's engine) — the pick reads files from any maker; the engine is §256.9's fourth spec, not begun
  - Answered: in a pick task: the tool makes its variants (the person, 2026-11-08)

## Decisions
