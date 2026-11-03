# The beta's run: one goal the whole way, on real tools, driven by an agent

Decisions §227. A local Claude Code session drives Orkboard by `orkboard drive` (gui/drive.py), takes pictures at each
stage, and says whether the flow holds. What is checked is what is built today; decisions §208–§226 are not built and
are not checked here.

## 1. Before the run (the owner, once)

- Orkboard installed as a tool, not from the clone it will work on:
  `uv tool install --force 'orkboard[gui] @ git+https://github.com/orkCraft/orkBoard'`.
- Codex signed in (`codex login`, the ChatGPT plan). Antigravity signed in on a spare Google account (`agy login`), or
  `GEMINI_API_KEY` set (Orkboard then counts it as paid by the API). Antigravity through another program has had Google
  accounts suspended; a second flag is said to be permanent: never the main account.
- Settings → AI tools, in the window, then the window closed: Codex on, Antigravity on (its warning accepted), **Claude
  Code off** (the driving session is Claude: Orkboard must not spend the same limits), the main tool Antigravity or Codex.
  Tech's party: *Does* and *Checks* on Codex; the leaders and the Orkmaster on Antigravity's Veteran (Gemini Pro), or
  on Codex if Antigravity is not there.

## 2. The run (the driving session)

```bash
orkboard drive start ~/code/orkBoard --real-tools &
orkboard drive watch --seconds 14400 > beta-run/drive-log.jsonl &
orkboard drive call ideas.board --path tracks                      # a Tech party is there, or:
orkboard drive call ideas.goal_save --args '{"preset": "tech", "title": "Tech"}'
orkboard drive call ideas.add --args '{"text": "<the goal>"}'      # its answer's slug is the goal's id
orkboard drive call ideas.talk --args '{"idea": "<slug>"}'
orkboard drive call ideas.board --path 'ideas[slug=<slug>]'        # where it is, at any time
orkboard drive call ideas.board --path needs_you                   # the hand: what waits for an answer
orkboard drive shot beta-run/<nn>-<stage>-phone.png --width 390
orkboard drive shot beta-run/<nn>-<stage>-desktop.png --width 1360 --height 860
```

The goal: a small, real one on this repository (the first is §208.5's Godot reading for System, as its text in
docs/decisions.md says). Each hand card is answered by the command the page sends for it (`ideas.talk_answer`,
`ideas.answer`, `ideas.confirm`, `ideas.start_now`, `ideas.gate_merge` …: `orkboard/gui/ideas*.py` say their arguments);
a card the session cannot answer from its row is answered in the page (the `url` in `.orkcraft/drive.json`) and said so.

The stages, a picture of the phone and of the desktop at each: **dropped** (the route card) · **Talk** (the leaders'
questions, one answered) · **the sections** (the spec) · **To review** (its start time) · **at work** (a task's steps) ·
**the gate** (its tests) · **ready for main** · **merged** (the discard).

## 3. What is written down

`beta-run/report.md` in the project (not committed): for each stage its time, the tool and model of each call, its cost,
the pictures; `orkboard drive spend --goal <slug>` (decisions §228) for the goal's tokens and money by tool, step and
call, and **what is worth a look**: failed calls, a big cache written and none read, heavy reads with a short answer, a
step asked again (each with its tokens; a call's whole prompt and answer are in `.orkcraft/logs/<day>/board/`, beside
its line); every refusal and every broken command (`command_refused` in the event
log), every error toast; what was done by hand and why; what looked wrong in a picture.

## 4. The verdict: beta when all hold

1. The goal reaches main on real tools with no hand edit of Orkboard's state or files.
2. Every hand card of the run is answered, by its command or in the page.
3. No broken command (a `broken` refusal) and no error toast left unexplained.
4. Each stage's pictures, phone and desktop, show the stage as the decisions describe it, nothing cut or overlapping.
5. The gate ran the project's critical tests (`orkcraft.toml`'s `always`) and they passed.
6. What the run cost is known per tool, and each line of *worth a look* is explained or made a goal of its own.

Not beta: say which of the six failed, with its picture and its log lines.
