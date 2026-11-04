# 134. Release keeps the chronicle: the past past the portal, the discard a pile that empties

Decisions §238 (1–8). The owner, 4 November: *is there a point in a page to look over all the past decisions or all the past
specs?* and *won't a pile that is always there in the discard weigh on the person?* **Builds:** A on the cheaper model, the
spec's author reviewing and merging; B after A on the same · **Review:** the critical tests and each part's own · P1. After
spec 132 D (the goal's quality record, `ideas.quality`) and spec 127 (`Changes:`, the living specs). No tab, page, list
column or drawer of its own (§104.0, §145, §206.2); no count of what waits; the discard is **unchanged** (§238.1).

| Part | What | Where (and its tests) |
|---|---|---|
| **A. The host** | the chapters read from the tags, the changelog or the weeks; the goals through the portal; the decisions by their dates, what they change and what changed them; the search; a goal as it was | new `realm/chronicle_versions.py`, new `realm/chronicle_decisions.py`, new `realm/chronicle.py`, new `realm/chronicle_find.py`, new `gui/ideas_chronicle.py` (a mixin of `Ideas`: `ideas.chronicle*`), `gui/ideas.py` (its base and its table), `realm/lexicon.py`; new `tests/test_chronicle.py`, new `tests/test_ideas_chronicle.py` |
| **B. The face** | the line in Release's lens; the chronicle over the pane; a goal's row and a decision's row opened | `gui/static/js/table/releasemap.js` (the line), new `gui/static/js/table/chronicle.js` (kind `chronicle`, as the pile's list and the place of the parties open over the pane), `js/table/*` (the pane's kinds), `tests/test_gui_wording.py`, a browser test beside `tests/test_maps_desktop_browser.py` |

A is useful alone (a command a later face, a phone or a leader reads). B needs A's answers and changes nothing of A's; a change
it needs is said to the spec's author. **No model call anywhere**: the chronicle is read by code from what is kept.

## 0. What is there today

- **The discard** holds a goal done and not yet seen (`realm/goal_place.py` `place_of`: `discard` while `seen_at` is empty,
  then `history`) and *Ready for main*; `ideas.seen` (`gui/ideas_board.py`) keeps `seen_at` and the goal leaves it. Its spec, its
  decision and its result are then found only in the repository's files. §238.1 keeps it so.
- **Through the portal** a goal gets its **flag** once (`realm/idea_flag.py`: `<state_dir>/ideas/<slug>/flag.json` `{at, by,
  commit, tasks, first_time, usd, days}`, `by` `gate` when `ideas.to_main` took it into main, `done` where the project has no
  gate or all its commits were in main already); `GOAL_TO_MAIN` is the event (`gui/ideas_gate.py` `to_main`, which also gathers
  the goal's verdict, spec 132 D.2). The flag is the one record of *played to the end*, and its `at` the day.
- **A version** is the project's own: a tag in git, a heading of its changelog (`realm/read_in.py` `_releases` reads
  `## [1.2.0] - 2026-10-10`; `realm/map_signals_crafts.py` `CHANGELOGS` names the files), or the Board's own *A release* goal
  (`realm/releases.py`: `release.json` `{version, goals, out, at}`, the Release party's `since`). Release's map
  (`realm/release_map.py`, `ideas.release_map`) is dev against main and says only *Since <version>* of the last release goal out.
- **Decisions** are read by `realm/decisions_log.py` (`path`, `entry`, `headings` with ` (changed by 205)`, `changes_of`) and
  `realm/doc_formats.py` (`parse_log`: `number, title, date, day, extra.changes`; `records` for a folder of ADR files), the
  text or folder by `keeper._log_text()` (`core/idea_decide.py`, where a project chose its place). A decision's number and title
  are kept beside its goal too: `way.json` `decision {number, title, …}` (`spec_sections.record`).
- **A goal's spec as built** is its page (`ideas.idea_page`, `spec_sections.read`); its quality record `ideas.quality {idea}`
  (`gui/ideas_findings.py`); the living spec of its part `living_specs.read(board, cap)` (`goals: [slugs]`).
- Nothing reads the past together: no module says which version a goal went out in.

## A. The host

All of it by code; every answer is **keys and data, never words** (the face says them from `TERMS`, §4).

### A.1 Versions (`realm/chronicle_versions.py`)

```
chronicle_versions.read(repo)       → {kind: "tag" | "changelog" | "week", versions: [{id, name, day}]}   # oldest first
chronicle_versions.week_of(day)     → the Monday of `day`'s week, "YYYY-MM-DD"
```

- **tag** (§238.5, first choice): the project's tags that read as a version (`^[vV]?\d+(\.\d+)*(-|+ suffix)?$`: `v0.3`, `1.2.0`,
  `2.0-rc1`), by `git for-each-ref refs/tags` (`%(refname:short)` and `%(creatordate:short)`: the day of an annotated tag's
  tagger, of a lightweight tag's commit). A git that fails or a folder that is none: no tags, never an error.
- **changelog** (else): the repository's top file `CHANGELOG*`, `CHANGES*`, `HISTORY*` or `NEWS*` (`.md`, `.txt`, `.rst` or no
  extension; read to `READ_MAX = 1_000_000` bytes), each `## [1.2.0] - 2026-10-10` heading (a `v` and the brackets optional; the
  day either `YYYY-MM-DD` or `17 October 2026`, `doc_formats.day_of`). A heading with no version (*Unreleased*) or no day is not
  a version.
- **week** (neither): `versions` is `[]`; the chapters are made from the weeks the past has (A.4).
- `id` is `v:<name>`; a version's `day` is the day it went out; sorted by `(day, its numbers)`, a name once, at most
  `VERSIONS_MAX = 300` (the newest).

### A.2 Decisions (`realm/chronicle_decisions.py`)

```
chronicle_decisions.read(log, text=False)   → [row]    # by number; `log`: the decisions file's text or the folder (`keeper._log_text()`)
row = {number, title, day, changes: [{n, point, title}], changed_by: [{number, title, day, points}], goal: ""}   (+ `text` when asked)
```

- Parsed by `doc_formats.parse_log` (a file) or `doc_formats.records` (a folder). `day` is the entry's own (`day_of` of its
  date); an entry with none takes the day of the last dated one before it (decisions are written in order), the first ones the
  first dated after; "" when none has a day.
- `changes`: **read here, not by `extra.changes`** (which splits `206.3` into 206 and 3): the `Changes:` line among the first
  four lines of the entry (a folder's record: `decisions_log.changes_of`), the words `spec <n>` and `§<k>` dropped, then each
  `N` or `N.k` → `{n: N, point: k or 0, title}`; an `n` not smaller than the entry's own number is dropped; each once.
- `changed_by` of an entry: the later entries whose `changes` name it, `points` the `k`s they name (never 0), by number.
- `goal` is "" here; `chronicle.read` sets it (A.4). `text`: the entry's body (cut at `doc_formats.BODY_CHARS`), for the search.

### A.3 The goals through the portal (`realm/chronicle.py`)

```
chronicle.goals(state_dir, pages)   → [{idea, title, party, element, hue, at, day, commit, decision}]   # by `at`
```

A goal is **in the chronicle** when its page is on the Board and `idea_flag.flag_of` has a flag (`by` either: *played to the
end*, §238.5), and it is **not a release goal** (`releases.read` is None: a release is a version, not a goal that went in).
`at` is the flag's, `day` its first ten characters (a flag whose `at` is no date is left out), `decision` the number in
`way.json` (`spec_sections.record(...)["decision"]["number"]`; 0 when none). A goal seen but not through the portal is **not**
there; neither is a goal dropped.

### A.4 The chapters (`chronicle.read`)

```
chronicle.read(state_dir, pages, repo, log, text=False)
  → {kind, chapters: [{id, kind, name, day, goals: [goal row], decisions: [decision row]}],   # newest first
     unreleased: {goals, decisions} | None, decisions: {number: row}}
chronicle.earlier(state_dir, pages, repo)  → {kind, name, day} | None
```

- **Placing**: an item's `day` (a goal's flag, a decision's) belongs to the **first version whose day is not before it** (the
  version that goes out that day takes that day's items); after the last version it is `unreleased` (the chronicle's next
  chapter, not out yet: Release's lens shows it, §238.2; it becomes the top chapter when a version goes out). Items before
  the first version are that version's. **Weeks** (kind `week`): the week of the item's Monday (`week_of`), a chapter only for a
  week that has something, `id` `w:<monday>`, `name` "" (the face says *The week of <date>*), `day` the Monday; `unreleased` None.
- A chapter's `goals`: the goals of A.3 placed in it, newest first. Its `decisions`: the decisions written in its span **that no
  goal of the chronicle carries** (`goal` ""), newest first: **a decision of no goal is a row of its own** (a hypothesis's
  verdict, a cascade, §233, §235); a decision a goal carries (its `decision`) is `goal: <slug>` and stands under the goal's row,
  not in the list. The answer's `decisions` holds every decision by its number (for a face that opens one).
- `earlier`: the last version `{kind: "tag"|"changelog", name, day}`; of weeks, the newest week with something
  `{kind: "week", name: "", day}`; None when the past is empty and no version is known. It reads the versions (and, for weeks,
  the flags) only.

### A.5 A goal as it was and a decision (`chronicle.goal`, `chronicle.decision`)

```
chronicle.goal(state_dir, pages, repo, log, slug)  → {idea, title, party, at, day, commit, element, hue,
    spec: {asked, gist, sections: [{party, title, parts: {name: text}}]},
    decision: {number, title, day, entry, changes, changed_by} | None,
    changed_by: [{number, title, day, points}],
    how_now: [{capability, title}]}
chronicle.decision(state_dir, pages, log, n)       → {number, title, day, entry, changes, changed_by, goal} | None
```

- `spec`: the goal's page as it stands (it is the spec as built: a goal that went through the portal is not edited again),
  *Asked* and *Gist* and each party's section's parts (`spec_sections.read`).
- `decision`: the entry by `decisions_log.entry` (cut at `ENTRY_MAX`), `changes` and `changed_by` as A.2.
- `changed_by` of the goal: **the points it rests on** are its decision and the decisions that one `changes`; the later
  decisions (number above the goal's) whose `changes` name one of them, once each, by number: the face marks the spec
  *changed by §<n>* (§238.4).
- `how_now`: the living specs whose `goals` hold the slug (`living_specs.list_` and `read`), the face's **How it works now ›**.
- A goal not in the chronicle: `ValueError("That goal is not in the chronicle")`; a decision not there: None.

### A.6 The search (`realm/chronicle_find.py`)

```
chronicle_find.find(state_dir, pages, repo, log, query) → {query, found, more, chapters: [{id, kind, name, day,
    goals: [{idea, title, in: [...]}], decisions: [{number, title, day}]}], unreleased: {goals, decisions} | None}
```

The query is cut at 80 characters and split in words (at most 6, lower case); an item is found when **every word** is in its
text. A goal's text: its title, its spec (every section's parts) and its decision's title and entry; `in` says where a word was
found: `title`, `spec`, `decision`. A decision of no goal: its title and entry (`in` `decision`). Chapters with none are left
out, **the rest by chapter, newest first**; at most `FIND_MAX = 60` items, `more` the number left out. An empty query finds
nothing (`chapters: []`). Never a model; never writes.

### A.7 The commands (`gui/ideas_chronicle.py`, a mixin of `Ideas`; its table in `chronicle_commands`)

```
ideas.chronicle {}                  → {kind, earlier, chapters: [{id, kind, name, day, open, goals?, decisions?}], unreleased}
ideas.chronicle_line {}             → {earlier}                       # Release's lens: one line, nothing else read
ideas.chronicle_chapter {id}        → the chapter as A.4 (`goals`, `decisions`); "" when the chapter is gone
ideas.chronicle_find {query}        → A.6
ideas.chronicle_goal {idea}         → A.5's `goal` and `quality` (`ideas.quality {idea}`, spec 132 D.4; None when it fails)
ideas.chronicle_decision {number}   → A.5's `decision`
```

`ideas.chronicle`: only the **newest chapter is open** (`open: true`, with its `goals` and `decisions`); the others are a line
(`id, kind, name, day`, `open: false`), opened by `ideas.chronicle_chapter`. The Board's pages are read without making
(`self.root(False)`), the repository is `host.repo_root`, the log `self.keeper._log_text()`. A failure of one read is a
refusal in words (`IdeasError`), never a trace. Each command reads, none writes and none records an event.

## B. The face (after A)

- **Release's lens** (§238.2): under what it shows today, **one line** *Earlier: <name> · <day> ›* (a week: *The week of
  <date>*), from `ideas.chronicle_line`; none when `earlier` is None; no list, no count; pressed it opens the chronicle.
- **The chronicle** (§238.3, kind `chronicle` over the pane; ← or Esc back to the lens): a chapter a version, newest first,
  the newest open, each older one a line *v0.3 · 28 Oct* opened by a press (`ideas.chronicle_chapter`); a search at its top
  (`ideas.chronicle_find`; its finds by chapter, the others folded away).
- **A goal's row** opens the goal as it was (`ideas.chronicle_goal`): its spec marked *changed by §<n>*, its decision, its
  quality record, **How it works now ›**; **a decision's row** opens its entry, its *Changes* and *changed by* links
  (`ideas.chronicle_decision`). The phone: not for now (§238.6).
- Words only from `TERMS` (§4); the page says a date as the page's other dates are said. Pixel face for headings only.

## C. Tests

`tests/test_chronicle.py` (real git in a temp repository, no model): tags that read as a version and the others not, dated by
tag; the changelog's headings when no tag, *Unreleased* and an undated heading skipped; weeks when neither; a git that fails; the
`Changes:` line (`206.3`, `spec 120 §3.5` dropped, an own or later number dropped); `changed_by` with points; a decision with no
day takes the one before it; the goals through the portal (a flag by `gate` or `done`; none without a flag; a release goal, a
goal dropped and a goal seen without a flag are not there); placing by day (a same-day item belongs to that version; after the
last one, `unreleased`; before the first, the first); weeks; the decisions of no goal as rows and a carried decision not; `earlier`
for a tag, a changelog, weeks, nothing; a goal as it was (its spec, its decision's entry, `changed_by` through a decision its
own decision changes, `how_now`); a goal not in the chronicle refused; the search (all words, `in`, chapters with none left
out, `FIND_MAX` and `more`, an empty query, a decision's text, a section's).
`tests/test_ideas_chronicle.py` (a host as `tests/test_findings.py`'s): each command's shape, only the newest chapter open,
`ideas.chronicle_chapter` of an older id and of a gone one, `ideas.chronicle_goal` carrying the quality record, the commands
reading and writing nothing (the state folder as it was). `tests/test_lexicon.py` and `tests/test_gui_wording.py` for the words.

## D. The words (`TERMS`, new keys; none renamed)

`chronicle` *Chronicle* · `chronicle_earlier` *Earlier* (the lens's line: *Earlier: v0.3 · 28 Oct*) · `chronicle_week` *The week of*
(then the date) · `how_works_now` *How it works now* · `changed_by` *changed by* (then *§<n>*). The chapters' names are the
versions' own, never a word of ours.
