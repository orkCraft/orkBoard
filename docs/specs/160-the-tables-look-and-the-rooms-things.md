# 160. The table's look and the room's things

Decisions §268 (colour is the party, the element and a signal), §269 (the table's look), §271 (the lamp is the person), §272
(the backpack and the new chair), §273 (the discard beside the table), §275 (a tab's name light, words on a flat plate, the phone
in this goal); §274.1 (Release a craft as any). **Mockups:** `docs/mockups/table-look/` (the colour layer, the felts, the steps,
the bronze, the pennants) and `docs/mockups/room-things/` (the lamp's chain, the backpack shut and open with the leather, the
chair dealing its crafts, the stall open on a new craft). **The goal's page**
`llm-wiki/general/pages/ideas/160-the-tables-look-and-the-rooms-things.md` holds the spec: Design's and Tech's sections and the
Taskmaster's twelve *Stages*; this file is their summary, kept with it.

**orkUI first** (§269.9, CLAUDE.md): stages A and B are made in orkUI (github.com/orkCraft/orkUI), released as **0.35.0**, then
copied here (C, `python -m orkboard.design.orkui <orkUI>`); `design-system/orkui` is never edited by hand. **Builds:** a stage a
Grunt, merged into the goal's branch, then `main` on the critical tests and the stage's own (CLAUDE.md, alpha); the sheets,
drawings and tokens on simpler models, the discard's move (D) and the chair's seating (I) on a stronger one (the person's answer).
No `orkboard/gui/*.py`, `core/` or `realm/` module changes: the host's commands are enough (`presence.set`, `ideas.goal_save`,
`ideas.party_presets`, `ideas.party_price`, `ideas.project_kind_set`, `ideas.stage_set`).

| Stage | What | Where |
|---|---|---|
| **A** | orkUI's colours: the parties by race, each felt lit and out, five light steps, the flat plate, bronze and gilt; a contrast test | orkUI `office/tokens.json`, `tools/build_tokens.py`, `tests/` |
| **B** | orkUI's drawings: the table (felt, dithered steps, bronze, rivets), plaque, pennant, the lamp's chain, the backpack shut and open, the leather; released 0.35.0 | orkUI `office/components.css`, new drawings, preview, CHANGELOG |
| **C** | orkUI 0.35.0 copied; the contrast and no-gradient tests here | `design-system/orkui`, `tests/test_design_system.py` |
| **D** | the discard the window's right column beside the table; Release's tab in the leaders' row | `table/lane.js`, `table/tabs.js` |
| **E** | the table's look on the desktop: felt, light, plates, bronze, plaques, pennants, light names | `table/*.css`, `table/tabs.js` |
| **F** | the cards' faces and the hand's fan | `hand/*.css`, `table/card.js` |
| **G** | the lamp's chain in place of the door, at the column's head | `table/presence.js` |
| **H** | the backpack at the column's head; open, the leather | `table/backpack.js` |
| **I** | the chair deals its crafts, a card seats one and opens the backpack on it | `table/chairs.js` |
| **J** | the project's name, kind and stage in the Orkmaster's header; kind and stage dealt as cards | `table/column.js` |
| **K** | the phone's table, lamp and backpack | `pwa/`, `hand/uptop.js` |
| **L** | the pictures, for the person to judge | `docs/mockups/*/shoot.py` |

## Later

The new goal made in the Orkmaster's first lane with its settings at its corners (§270.6); the chair's deal and the header's
cards on the phone.
