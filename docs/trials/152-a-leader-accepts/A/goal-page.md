---
owner: board
kind: idea
track: tech
order: 1
size:
priority: normal
short: The field's Rune square
phase: done
route: tech
by: person
schema: 3
touches: ["orkboard/gui", "orkboard/gui/static/js/hand", "orkboard/gui/static/pwa", "tests"]
risk_model: low
risk: low
risk_triggers: []
gate: c6ca700 · 6 files · green
---
# The field's Rune square shows the hue the host will pick. While a goal is…

## Asked
The field's Rune square shows the hue the host will pick. While a goal is written on the + card, its Rune square shows the hue the host will give it (`realm/idea_element.py`), not a fixed one; the phone's `nextElement` counts by the project, as the host does. Spec 128 G.

## Gist
The field's Rune square shows the hue the host will pick. While a goal is written on the + card, its Rune square shows the hue the host will give it (realm/idea_element.py), not a fixed one; the phone

## Route
1. Tech · Architect · section written

## Depends on

## Decisions
- 2026-11-06: Decision 253: The Rune follows the host's hue

## Tech
### Why
The Rune preview must follow the same project-wide allocation rule as the host, so the field predicts the goal’s assigned hue. Keep allocation in realm and presentation in gui, with no reverse imports or new dependency cycle.

### Done when
- [test] When the + card is open for writing with the default Rune, then its Rune square shows the hue realm/idea_element.py would assign against the same project state.
- [test] When a person selects another Rune shape in the opened + card, then its square shows the host’s predicted hue for that shape, including legacy goals whose hue falls back to their element.
- [test] When the project snapshot changes while the + card is open, then its Rune preview updates without assigning or storing a Rune.
- [test] When the phone computes nextElement from a project’s goals across parties, then it matches the host’s shape selection, counting done goals whose results are unseen and freeing seen done goals, with ties in ELEMENTS order.

### Checks
- Compare default and explicitly chosen shape predictions with realm’s pick_rune, including repeated shapes and hue ties.
- Keep host allocation authoritative; previewing must not persist a hue or send a predicted hue as an override.
- Keep fieldsquares.js a renderer of supplied Rune data; never import pluscard.js back into it.
- Run the critical gate tests, affected allocation and phone helper tests, and a browser test of the opened field’s Rune square.
- Keep each touched module below approximately 600 lines; record settled boundaries in the implementation commit message or .ork-commit.md.

### Will be
- changed orkboard/gui — expose host-derived per-shape hue predictions through the existing project snapshot boundary.
- changed orkboard/gui/static/js/hand — consume the predictions in runesOf and render the selected shape’s predicted hue.
- changed orkboard/gui/static/pwa — make nextElement use project-wide host holding and tie-breaking rules.
- changed tests — prove preview and phone parity with host allocation and preserve import boundaries.

### Out
- Changing the host’s Rune allocation or stored Rune migration rules.
- Redesigning the Rune picker or the + card.
- Adding a caller or new phone screen for the currently unused nextElement helper.

### Risks
- A concurrent goal change can alter allocation between the displayed snapshot and submission; the host remains authoritative.
- Phone snapshots must retain enough state to distinguish unseen done goals from seen ones.
- Duplicating hue allocation in the browser could drift from realm; supply host-derived predictions instead.

### Defaults
- Assumed: The existing snapshot can carry per-shape predicted hues without introducing a service or dependency.
- Assumed: Rune choices and the seal’s free runes retain their existing presentation; this change concerns the selected Rune’s hue.
- Assumed: nextElement receives all goal nodes for one project, rather than a party-filtered subset.
- Assumed: This read-only pass supplies the spec only; implementation records the settled architecture in its commit message or .ork-commit.md.

### Plan
1. k1 Match Rune previews to host allocation (M)
