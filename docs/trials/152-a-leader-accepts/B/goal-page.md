---
owner: board
kind: idea
track: tech
order: 110
size:
priority: normal
short: A potion's card names
phase: done
route: tech
by: person
schema: 3
touches: ["orkboard/gui/static/js/hand", "orkboard/gui", "tests"]
risk_model: medium
risk: high
risk_triggers: ["secrets, sign-in, payments", "outward and irreversible"]
gate: 1627167 · 4 files · green
---
# A potion's card names the models of its tiers again. The models by tier that…

## Asked
A potion's card names the models of its tiers again. The models by tier that spec 130 D took out of Settings come back on the potion's lifted card (`hand/toolcard.js`): each tier's model, changed there, kept in the machine's `tier_models` (`settings.py`, read by `realm/harnesses.py` today, set and shown by nothing since spec 130 D); a host command sets it. Spec 130 B.3.

## Gist
A potion's card names the models of its tiers again. The models by tier that spec 130 D took out of Settings come back on the potion's lifted card (hand/toolcard.js): each tier's model, changed there,

## Route
1. Tech · Architect · section written

## Depends on

## Decisions
- 2026-11-06: Decision 260: Tier Models Return to the Potion Card

## Tech
### Why
The lifted potion card must expose the tier choices the harness already consumes. Host validation and machine-scoped persistence keep the displayed choice and subsequent model selection consistent.

### Done when
- [test] When a person first opens a lifted potion card for a tool with tiers, then each supported tier shows its saved model or inherited default without changing settings.
- [test] When a person changes a tier to an available model on the lifted card, then a host command saves that tool and tier in machine tier_models, and reopening the card after reload shows the saved choice.
- [test] When a client submits an unknown tool, unsupported tier or unavailable model, then the host rejects the edit with an error and leaves saved tier_models unchanged.
- [test] When a subsequent harness invocation selects an edited tier, then it uses the saved model through the existing Harness.pick resolution.
- [test] When a valid edit is saved, then other tools, other tiers and unrelated machine settings retain their previous values.

### Checks
- Validate on the host against the selected tool's available models; client controls are not the validation boundary.
- Read and write the existing machine-scoped tier_models structure without introducing project-level copies.
- Show command failures without presenting an unsaved selection as saved.
- Preserve existing family resolution and explicit-model behavior in Harness.pick.
- Cover card loading and editing, host rejection, persistence and harness consumption with gate-run tests.

### Will be
- changed orkboard/gui/static/js/hand — load tier models and send edits from the lifted potion card.
- changed orkboard/gui — expose tier choices and handle validated host-command updates to machine settings.
- changed tests — prove card behavior, validation, persistence and existing harness consumption.

### Out
- Restoring tier controls in Settings.
- Changing tier definitions, model-family resolution or routing policy.
- Changing billing, tool order, tool removal or phone configuration.

### Risks
- Some tools cannot enumerate available models; edits must remain unavailable with an explanation rather than accepting unchecked values.
- An existing saved model may no longer be available; opening its card must preserve and identify that value.
- Concurrent card edits could overwrite unrelated choices unless updates merge against current machine settings.

### Defaults
- Assumed: Decision 260 settles the command and validation boundary; no further person decision is needed.
- Assumed: Available models means models reported for the selected tool through existing discovery, not every provider's models.
- Assumed: A missing override displays the existing tier default; adding a reset control is outside this section.
- Assumed: Tools without a tier table expose no tier editor.

### Plan
1. k1 Restore tier models on potion cards (M)

## Open questions
- How does the card set models?
  - Answered: A host command applies each card edit (the person, 2026-11-06)
- What validates model values?
  - Answered: Host command validates against available models (the person, 2026-11-06)
