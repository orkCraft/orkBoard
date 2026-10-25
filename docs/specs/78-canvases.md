# Spec 78 — Canvases: what an AI tool draws outside the code is a card with the elf's head

The owner, 25 October (decisions §93): *can Orkboard catch a canvas made in Claude and show it as a card, an elf's, the
designer's?* A model in Claude Code, Antigravity or Codex makes more than code: a Claude artifact (a page, a Design, a
deck, a doc), a picture Antigravity or Codex generates, a file on a canvas tool (Figma, tldraw, Canva) through MCP. Today
Orkboard sees none of it: it lives in a link or a folder of the tool's. So Orkboard **reads the canvases its project's
sessions made and lays each out as a card**, drawn with the head of design's race, the elf (decisions §53). **Builds:**
Claude · **Review:** full (§0 and §1 read three tools' private formats) · P3. **§0 first** (on the owner's machine:
this container has none of agy and Codex, and no session of theirs). **The core first** (§7, by Claude: the store, the
commands, the snapshot), **then A, B, C and D at once** on cheaper models, each against §7; until §0 is recorded, A's
readers are built to fixtures written from the tools' sources (§0's *Until then*), which §0's recordings replace.

Wording: CLAUDE.md. **This file is the contract.**

**What it is, and is not:** a reader of what each tool already writes on the person's machine, one card a canvas, a
link out or a look at a local file, and a hook that tells Orkboard at once. Not: a canvas drawn inside Orkboard (the
card shows the canvas's title and kind, never its content: a claude.ai page is private, behind a sign-in); Orkboard
fetching a link (it opens it in the person's browser, nothing more); Orkboard publishing a canvas, or any run of its own
getting a tool it lacks today to make one (a Claude worker runs `acceptEdits`, and publishing is outward-facing: it stays
refused); a plan, a walkthrough, a screenshot or a browser recording of agy's (they say how the work went, not what it
drew); a file a change adds to the repository (the diff's, at Review); a cloud session of Claude Code (its transcript is
in its container: only the `Claude-Session` trailer reaches the machine, spec 37); a chat on claude.ai or in the Claude
app (no hook, no transcript on the machine).

| part | builds | files (and their tests) |
|---|---|---|
| **0. The probe** | §0 | `tests/fixtures/canvases/` (one recorded session a tool), `docs/specs/78-canvases.md` *As found* |
| **Core** (no face, built first) | §2, §7 | new `core/canvases.py` (the store, the bus), `sources/canvases.py` (`Canvas`, `link_host`, the readers' stubs), new `gui/ideas_canvases.py` (the commands), `gui/ideas.py` (wired), `realm/lexicon.py` (`canvas`), `realm/event_log.py` (`CANVAS_MADE`, `CANVAS_SEEN`); new `tests/test_canvases.py` |
| **A. The readers** (no face) | §1 | `sources/canvases.py` (`read_claude`, `read_codex`, `read_agy`), new `tests/fixtures/canvases/`, new `tests/test_canvas_readers.py` |
| **B. Desktop** | §3 | new `js/arena/canvases.js`, `js/arena/waits.js` (the row), `arena.css`, the preview's canvas (`js/shell/preview.js`); new `tests/test_canvases_desktop_browser.py` |
| **C. Phone** | §4 | `pwa/shell-review*.js` (the row), `pwa/app.css`, `pwa/sw.js` `CACHE` one up with every phone test's pin; new `tests/test_pwa_canvases_browser.py` |
| **D. The hook** | §5 | new `hooks/canvas.py`; in Orkline, the same day: `orkcraft hooks install` writes its entries (Orkline's commit names this one); `hooks/warder.py` `SELF` gains it; new `tests/test_canvas_hook.py` |

## 0. The probe: one real session a tool, recorded, before a line of the reader
The formats below are read from each tool's sources and docs (25 October), not from a session; each is checked once
on the owner's machine and kept as a fixture, private paths and texts cut:
1. **Claude Code**: a local session that runs `Artifact` once (a page, `file_path` → its URL) and once from a type
   (`type_url`, Design). Found: whether a local `claude` has the tool at all, the `tool_result`'s text (the URL's
   place in it), and whether `claude -p` refuses it in `acceptEdits` (expected: refused, and nothing is changed for it).
2. **Codex** (≥ 0.145, hooks on by default): a session that generates one picture. Found: the rollout's
   `response_item` `image_generation_call` and its `event_msg` `image_generation_end` (`saved_path`), the file under
   `$CODEX_HOME/generated_images/<session>/<call>.png`; and that `codex exec --json` prints **no** item for it (its
   `exec_events.rs` has none: agent_message, reasoning, command_execution, file_change, mcp_tool_call,
   collab_tool_call, web_search, todo_list, error).
3. **agy**: a session that runs `generate_image` once. Found: the file in `brain/<conversation>/` and its
   `.metadata.json`, whether a `PostToolUse` with matcher `generate_image` fires (the embedded doc lists the tool;
   probes so far saw only run_command, write_to_file, view_file, list_dir, read_url_content fire), and its payload
   (`toolCall`, `workspacePaths`, `artifactDirectoryPath`, `transcriptPath`).
Each finding goes under *As found* below; where a tool says other than this spec, *As found* wins and §1 follows it.
**Until then**: `tests/fixtures/canvases/` holds one file a tool written by hand from the formats above (its README says
so, file by file); a recorded session replaces its file and the readers' tests stay as they are, or say what changed.

## 1. What a canvas is, by tool (A)
A **canvas** is one thing a tool drew, keyed by `(tool, its URL or its file)`; drawing it again (an update, a new
version) moves the same card to now. Each has: its **kind** (*Design*, *Slides*, *Document*, *Page*, *Picture*), its
**title** (the tool's or the agent's words, kept as written), **when**, **where** (an `https` link, or a local file),
the **session** and the **model** that made it.
1. **Claude Code**, from its transcripts (`sources/transcripts.py`'s blocks; `sessions.claude_projects_dir`):
   `Artifact` (`action` publish or none) with its `tool_result`'s `claude.ai/…/artifact/…` URL: from a `type_url`, the
   type's kind (Design, Slides, Docs → *Document*); else *Page*, its `file_path` kept as the local file.
   `mcp__Claude_Docs__batch` with `container.create` → *Document*. `mcp__Figma__create_new_file` → *Design*, its
   `figma.com` URL. A call that failed (`is_error`) is no canvas.
2. **Codex**, from its rollouts (`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, read as `sources/telemetry.py` reads
   them): `image_generation_call` → *Picture*, its file `saved_path` (or `generated_images/<session>/<call>.png`), its
   title the revised prompt cut to a line; a canvas tool's MCP call (`mcp__figma__*`, `mcp__tldraw__*`,
   `mcp__canva__*`: `KNOWN_MCP`, one table) that answered with an `https` link → *Design*. Orkboard's own Codex runs
   need nothing more: their thread's rollout is read as any.
3. **agy**, from a conversation's brain folder (`sessions.agy_brain_dir() / <id>`): each image `generate_image` wrote
   → *Picture* (which files are its: §0.3). The brain does not say a conversation's project; a conversation is the
   project's when Orkboard ran it (its session id is a task's) or when the hook (§5) named the project's folder.
4. **Whose project**: a Claude transcript in the project's folder or one of its worktrees (`.orkcraft/worktrees/`); a
   Codex rollout whose `session_meta.cwd` is under the project's root; an agy conversation as §1.3. A canvas whose
   session is a task's (`session` in the plan) **names that task and its goal**.
5. **Bounded**: the newest 60 sessions a tool (`sessions.MAX_LOCAL`), a file read from where it was last read (its size
   and mtime kept), at most `transcripts.MAX_BYTES` each; the reader runs every 30 s while the page is open, and at
   once when the hook writes (§5).

## 2. The store and the bus (A)
1. `<project>/.orkcraft/canvases.jsonl`: one line a canvas when it is made or drawn again, one line when it is seen
   (`{"key", "seen": <iso>}`); kept by hand, readable, never more than the last 200 canvases (older lines go on a
   rewrite).
2. `core/canvases.py` keeps it and publishes `canvas.made` (the canvas) and `canvas.seen` on the bus (`core/bus.py`);
   `realm/event_log.py` logs `CANVAS_MADE` (tool, kind, task) and `CANVAS_SEEN`. It shows no toast and no dialog.
3. **Its head**: design's race, the elf (`roles.RACES["design"]`), at the tier of the model that drew it
   (`harnesses.tier_of_model`; unknown: `warrior`). A canvas from a task of a design-craft role wears that role's head
   (`roles.task_head`). The head is an accent, small (CLAUDE.md, decisions §53.8).
4. `TERMS` gains `canvas` / `canvases`: *what an AI tool drew outside the code: a page, a design, a deck, a document, a
   picture*. The interface says *canvas*; the code says `canvas`; the tools' own words (artifact, generated image)
   stay in the code and in the tools.

## 3. The desktop's card (B)
1. **Where**: the right column, above *Waits for your look*, a fold row *Canvases · n* (`FoldRow`, spec 73 §3), folded
   by default; n counts the ones not seen. None: no row. A canvas is **not a signal** and not a result (decisions
   §54.1): no alert colour, no Merge, no count in the top bar.
2. **The card** (`.ork-frame`, as a result's): the head, the kind in the pixel face's small caps, the title in the text
   face (a person's or an agent's words never in the pixel face), *Claude* · *Antigravity* · *Codex* and when, and,
   when it has one, its task and goal (a link to the task as a result's title is).
3. **What it offers**, each saying what it does: **Open on claude.ai** / **Open in Figma** (… the link's host, from an
   allow-list: claude.ai, figma.com, tldraw.com, canva.com; another host is shown as text, never a link) opens the
   person's browser; **Show here** opens a local file in the preview (a picture, a page; only from the project, the
   Codex `generated_images` folder or the agy brain folder: `gui/server.py` `resolve`'s rule); **Seen** folds it into
   *Seen* at the row's foot (the last 20).
4. A canvas that comes while the page is seen draws in once (spec 74 §0: tied to its event, ≤ 0.42 s, none under
   reduced motion).

## 4. The phone's card (C)
The Review screen's foot gets the same row and cards, one a line: the head, the kind, the title, the tool; a tap opens
the link (the phone's browser) or the picture; *Seen* as on the desktop. *Show here* for a page is the desktop's only
(the phone shows a picture, never a local page). `pwa/sw.js` `CACHE` one up.

## 5. The hook: at once, not in 30 s (D)
`python -m orkboard.hooks.canvas <tool>` as a **PostToolUse** hook: reads the payload on stdin, and when it is a
canvas (§1) appends its line to `<project>/.orkcraft/canvases.jsonl` (the project from `cwd` / `workspacePaths`).
1. **It never blocks, never decides**: it prints `{}` (agy reads every hook's stdout as its answer and fails closed on
   anything not JSON, as the Warder knows), exits 0, gives up after 5 s; an error is swallowed.
2. **Its entries** (written by Orkline's `orkcraft hooks install`, beside the Warder's):
   `.claude/settings.json` `hooks.PostToolUse`, matcher `Artifact|mcp__Claude_Docs__batch|mcp__Figma__create_new_file`;
   `.codex/hooks.json` `hooks.PostToolUse`, matcher `mcp__(figma|tldraw|canva)__.*` (Codex's picture is a hosted tool
   and not a hook's: §1.2 reads it from the rollout); agy's `.agents/hooks.json` (a trusted folder) or
   `~/.gemini/config/hooks.json`, `orkcraft.PostToolUse`, matcher `generate_image` — when §0.3 shows it fires; until
   then agy's canvases come from Orkboard's own runs only.
3. The reader (§1) still runs: the hook is the fast path, never the only one, so a missed hook loses nothing.
4. The Warder guards the hook's file and its entries as its own (`SELF`).

## 6. Tests
`tests/test_canvases.py`: each tool's fixture (§0) read into its canvases (kind, title, where, session, model, task);
a failed call is none; a link of another host is no link; a canvas drawn again is one card, moved; the store keeps 200;
*seen* survives a restart; the head (elf, its tier, a design role's own); the hook's stdout is `{}` and its exit 0 on
a bad payload. The browser tests: the row and its count, the card's words, the three offers, *Seen*; the phone's row.
The critical tests (CLAUDE.md *Alpha*) and `tests/test_gui_wording.py` pass.

## 7. The contract (the core, built first)
1. **The store** (`core/canvases.py` `Canvases`): `add(canvas)`, `refresh(agy_sessions)`, `shown()` → (not seen, the last
   20 seen; newest first), `seen(key)`, `get(key)`, `new_count()`, `rev`; it publishes `canvas.made` and `canvas.seen`.
   A line of `.orkcraft/canvases.jsonl` is `Canvas.line()`: `{key, tool, kind, title, at, url, file, session, model}`,
   or `{key, seen}`. The hook (D) writes the first kind of line, nothing else.
2. **The commands** (`gui/ideas_canvases.py`; the phone may call all but `canvas_open`):
   - `ideas.canvases {}` → `{canvases: [card], seen: [card]}`; a card is `{key, tool, tool_word (Claude · Codex ·
     Antigravity), kind, title, at, url (an allowed host's, else ""), host ("claude.ai", …, else ""), link_text (a link of
     another host, as text), local (a file the preview may show), session, model, idea, idea_title, task, head {craft,
     race, tier}}`;
   - `ideas.canvas_seen {key}` → `{ok}`; `ideas.canvas_open {key}` → `{ok}` (the computer's browser; refused from the
     phone and for a link of another host); `ideas.canvas_file {key}` → `{name, mime, data}` (a picture, base64) or
     `{name, mime, text}` (a page: HTML or Markdown), refused outside the project, `$CODEX_HOME/generated_images` and
     agy's brain folder.
3. **The snapshot** carries `canvases_new` (how many not seen) and `canvases_rev` (one up at each change): a face reads
   `ideas.canvases` again when the rev moves.
4. **The readers** (A) fill `read_claude(repo_root)`, `read_codex(repo_root)`, `read_agy(repo_root, sessions)` in
   `sources/canvases.py`: each returns `Canvas`es and never raises; the host runs them every 30 s off its thread.
5. **One call as a canvas**: `from_call(tool, name, args, result, at, session, model)` (`sources/canvases.py`) is §1's
   table for one tool call, shared by the readers (A) and the hook (D): `Artifact` (publish, not an asset),
   `mcp__Claude_Docs__batch` (a create), a `KNOWN_MCP` server's call answering an allowed link (Figma's
   `create_new_file` only), `generate_image` (an image's path in its answer or args). A reader or the hook that finds the
   tool's format otherwise changes this one function, with its test.

## As found
(§0's findings, by tool, once recorded.)
