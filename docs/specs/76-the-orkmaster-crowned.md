# Spec 76 — The Orkmaster is crowned: its head is the ork's with a crown, a rank and not a tier

The owner, 25 October (decisions §91): *the Orkmaster could be an ork with a crown, so it stands out at once.* Today the
Orkmaster's head is `peon` · `elder` (`realm/orkmaster.py` `ORKMASTER`), the very head the Taskmaster wears by default:
on the project's line and at a party's heading two equal heads stand side by side and say nothing of who is who. So the
Orkmaster wears **a crown**: orkUI's emblem `crown` already means *a rank*, and the Orkmaster is the project's ork, above
the parties, not an agent on a tier. **Builds:** a cheaper model, reviewed by Claude · **Review:** light · P3.
**A first, then B**: B copies A's sprites.

**What it is, and is not:** one new head in orkUI (`peon-crown`, both looks, both sizes) and the Orkmaster drawn in it on
both faces. Not: a fourth tier (no role picks *crown*, no model list shows it, `roles.TIERS` stays three); a crown for
the Taskmaster or any agent; an emblem laid over a head by CSS (§53.8: a head is an accent, one picture); a colour new
to orkUI; a new word in `TERMS` (the crown is how the Orkmaster is drawn, not a concept).

| part | builds | files (and their tests) |
|---|---|---|
| **A. orkUI** (github.com/orkCraft/orkUI) | §1 | `races/races.json` (a `ranks` block, two role letters `g`, `r`), `tools/build_races.py` (writes the ranks), `office/races/`, `game/races/` (generated), `office/preview.html` (the gallery's Races row), `races/README.md`, `README.md`, `CHANGELOG.md`, `pyproject.toml` (0.7.0), `tests/test_orkui.py` |
| **B. Orkboard** | §2 | `design-system/orkui` (the copy: `python -m orkboard.design.orkui <orkUI>`, never by hand), `realm/orkmaster.py` (`ORKMASTER`'s tier), the faces' fallbacks (`js/shell/proposals.js`, `pwa/shell-project.js`, `pwa/shell-proposals.js`, and any other `{race: "peon", tier: "elder"}` that stands for the Orkmaster), `pwa/sw.js` (`CACHE` one up, every phone test's pin with it); `tests/test_orkmaster.py` and the tests that pin the Orkmaster's head |

## 1. The crown in orkUI (A)
1. **A rank, beside the tiers**: `races.json` gains `"ranks": {"crown": {"peon": [11 rows of 12]}}`. A rank is gear as a
   tier is, on the same 12 x 11 grid; it is not a tier: `races.<race>` keeps its three tiers, and the test of seven
   races in three tiers stays as it is. `build_races.py` writes each rank's head as `<race>-<rank>.png` (24 x 22) and
   `@2x` (48 x 44) for every look, as it writes the tiers; `--check` covers them.
2. **The head is orkCraft's logo's crown on the peon** (the owner: *take the ork with the crown of orkcraft's logo*;
   orkPage `public/favicon.svg`): the logo's two crown rows exactly, three points and a gem, sitting on the top of the
   peon's head; the peon's face exactly as in its three tiers (rows 3 to 10 of `laborer`: the eyes and the mouth where
   they are, so the Orkmaster is the Taskmaster's own race, crowned):
   ```
   ............
   ...g.gg.g...
   ...ggrrgg...
   ...ssssss...
   s.ssssssss.s
   ssszzsszzsss
   .sseesseess.
   ..suussuus..
   ..sbssssbs..
   ..sbssssbs..
   ...ssssss...
   ```
   The logo's own face (no shade, no cheeks) and its collar are not taken: a race's head is a head, and its face is the
   race's.
3. **Its colour**: two new role letters, `g` *crown* and `r` *the crown's gem*. The logo's gold (`#e3b23c`) is 13 from
   `alert` and its red 20 from `danger` (CIE76): they would pass for signals, so the shapes are the logo's and the colours
   toned under the race rules (`races/README.md` *Colour*): chroma at most 40 in office, at least 20 from `danger`,
   `alert` and `success`, every edge pixel 3:1 on `canvas`, `panel`, `raised`. Office: brass `#ac8b4d`, garnet `#9a6050`;
   game: brass `#b08a3a`, garnet `#a0584c`.
4. **The gallery** (`office/preview.html`, Races): the crowned peon after the peon's three tiers, with its word
   (`peon crown`). **README** (`races/README.md`): a section *The ranks*: `crown`, the peon's only; who wears it is the
   product's to decide. **CHANGELOG**: 0.7.0, citing Orkboard's spec 76 and decisions §91.
5. Tests (`tests/test_orkui.py`): the rank's grid (11 x 12, known roles), its face rows equal to the peon's tiers', its
   colours in every look under the race rules, its files written and checked; the version at least 0.7.0.

## 2. The Orkmaster wears it (B)
1. **The copy**: after A is on orkUI's `main`, `python -m orkboard.design.orkui <orkUI>` refreshes `design-system/orkui`
   and `ORKUI.json` (0.7.0, the commit). Nothing in the copy is edited by hand.
2. **The head**: `ORKMASTER = {"id": "orkmaster", "name": "Orkmaster", "race": "peon", "tier": "crown"}`; `ideas.map`'s
   `project.orkmaster` carries it as now. The faces draw `races/peon-crown` where they drew `peon-elder` for it: the
   desktop's project line, a party's heading led by it, New party's proposals, the collision's stop; the phone's *The
   project* row, its sheet, its proposals, its stop. Their fallbacks for a host that sends none (`{race: "peon", tier:
   "elder"}` as the Orkmaster) become `crown`.
3. **Its words**: the Orkmaster's head keeps the title *Orkmaster* everywhere; it never goes through `headWords` (which
   would say a tier's words). A head of `tier: "crown"` that does reach `headWords` says *Orkmaster* for the tier part
   only where a test shows it is drawn there; otherwise no change to `TIER_WORDS`.
4. **Agents stay as they are**: the Taskmaster's head is still its tier's (`elder` by default), a role cannot pick
   `crown`, `roles.TIERS` and the model list are unchanged; `roles.own_race` never returns a rank.
5. `pwa/sw.js` `CACHE` one up (the head is a new file the phone caches), with every phone test's pin.
6. Tests: `tests/test_orkmaster.py` (`ORKMASTER["tier"] == "crown"`, the copy has `races/peon-crown.png` and `@2x`); the
   desktop and phone tests that pin the Orkmaster's head (`peon-elder` beside *Orkmaster*) now pin `peon-crown`; a test
   that the Taskmaster's head is still `peon-elder` where both stand (the project's line beside a party Taskmaster leads).
   The critical tests (CLAUDE.md *Alpha*) and `tests/test_design_system.py` pass.

## As built (A)
- orkUI 0.7.0 on its `main` (`8682903`, then the logo's crown): `ranks.crown.peon` in `races.json`, roles `g` and `r`,
  `peon-crown.png` and `@2x` in `office/races/` and `game/races/`; the gallery's Races row, *The ranks* in
  `races/README.md`, the CHANGELOG; `tests/test_orkui.py` pins the grid (its crown rows the logo's), the face against the
  peon's tiers, the colours and edges in both looks, the files. 241 passed.
