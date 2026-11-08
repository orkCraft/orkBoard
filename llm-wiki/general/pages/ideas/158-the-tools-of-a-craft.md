---
owner: board
kind: idea
track: design
order: 5
size:
priority: normal
short: Ввести инструменты
phase: talk
route: product, design, tech
asks: person
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

## Product

### Talk
- verdict: doubt — it rests on §256.7's `tool` step, not built (§256.9 orders it after the dossier and the cache); go if cut to Art's pictures and sound on official APIs, run as today's pick
- stance: Product backs the job (Art writes briefs and SVG, not assets), not a frame for every craft before one Art asset is picked and kept
- for: Art cannot do its job today: pictures only through agy, experimental with a ban risk; sound by no tool, though the library's sound-designer and composer need it
- against: this repository seats no Art party, so its owner's week cannot measure it; a gateway, machine keys and a new concept are a big cost before one paid asset is kept
- instead: one Orkboard-run pick for Art (an image API, ElevenLabs for sound), a money cap a run said in money; other crafts' tools once one is asked for
- assumes: a generated asset is good enough to pick and keep, at a price per asset worth paying — shown by: of Art's first ten paid picks, how many are kept in the project's tree

## Design

### Talk
- verdict: doubt — a leader's rug already says "Its AI tool" (ideas_stall.py LABELS); go once tools get a word of their own and a paid run says its money before it runs
- stance: Design lays it with no new face: a small ware on the leader's rug, its plate's money in words, and the pick card that already shows pictures and plays sound
- for: a ware "not here" with its why (no key on this computer, not in this AI tool) shows the person what is missing, where today Art only writes briefs and SVG
- against: two "tool" wares on one rug break consistency (Nielsen 4); a plate prices only what an estimator knows (spec 157 C.2), so money could show only after it is spent
- assumes: each paid tool's price a call is known before the call — shown by: the image API's and ElevenLabs's prices read by code, and a run's receipt matching its bill

## Tech

### Talk
- verdict: doubt — core/idea_runner.py is 611 lines and §256.9 puts the `tool` step after the dossier and the cache; go if a tool fills today's pick (idea_pick's files) from a module of its own
- stance: Tech builds it in a step as a maker behind today's pick: Orkboard calls the API, writes idea_pick's variants and manifest, and PickMixin._variants carries on unchanged
- for: the seam is there: a pick already takes pictures and sounds as files (idea_pick.read), keys already live in the keychain (idea_secrets), so no new face and no new store
- against: a paid call from the runner is a new outbound caller holding a key; a retry or a crash after the call spends twice, and the gate must never reach a paid API
- instead: one Picture maker and one Sound maker in a core module of their own, faked in the gate, priced and capped before each call; the recipe engine and a gateway wait
- assumes: each API returns its variants within a task's time and inside idea_pick's limits (120 MB, its mimes) — shown by: one real call each, its seconds, bytes and mime logged

## Open questions
- Art only, or one frame for all? (**one shape for every craft, only Art's tools in it** / Art only, a shape of its own / every craft's tools at once) — one shape costs little more and §256.6's code tools fit it later; tools no party asked for wait
- Own money gateway now or later? (**later: a cap a run in code first** / the gateway now) — Orkboard runs the step itself, so it prices each call before making it; a gateway pays only once an agent's MCP spends
- Suno: official API or a wrapper? (**ElevenLabs's official API first, Suno once official** / Suno through a wrapper, experimental / wait for Suno's API, no sound till then) — a wrapper on the person's key repeats agy's ban risk
- Which word, beside "AI tool"? (**maker: Harness.makes' word, a Picture maker, a Sound maker** / hands, the Gist's word / tool, and the AI tool renamed harness) — a leader's rug already says "Its AI tool"; a second "tool" beside it reads as the same ware
- Where is a paid run's money agreed? (**its cap on the stall's plate, each run's cost in its receipt line** / a Choice card before every paid run / the cap in Settings' … beside the key) — §266.5 locks money above what was agreed from Silent; a card a picture adds a step to every pick
- Where does a tool's run sit? (**in a pick task: the tool makes its variants** / the recipes' `tool` step first, §256.7's engine) — the pick reads files from any maker; the engine is §256.9's fourth spec, not begun

## Decisions
