---
owner: board
kind: idea
track: tech
order: 109
size: M
priority: normal
short: Shared seat rules
phase: done
by: person
schema: 3
risk_model: medium
touches: ["orkboard/realm/seat_frames.py", "orkboard/realm/agent_rules_text.py", "orkboard/realm/seat_*_rules.py (new pure text modules, split by responsibility before ~600 lines)", "orkboard/core/idea_talk.py", "orkboard/core/idea_sections.py", "orkboard/core/idea_accept.py", "tests/test_architecture.py", "tests/test_*seat*.py", "tests/test_agent_rules*.py", "tests/test_idea_talk*.py", "tests/test_idea_sections*.py", "tests/test_idea_accept*.py", "tests/fixtures/seat_rules/* (new baseline outputs)"]
depends_on: ["154-a-leader-is-a-skill-in-claude-code"]
checks: [{"by": "reviewer", "applies": true, "why": ""}]
risk: medium
risk_triggers: []
gate: 14d463f · 36 files · green
---
# Break the realm and core import cycle

## Gist
Move shared seat rules into pure realm modules so realm no longer imports core.
Core prompts and agent frames read the same text; every generated prompt stays character-for-character identical.

## Why
Lazy imports hide a reversed dependency. Shared rule ownership makes imports flow one way and keeps each seat's rules consistent.

## Done when
- Shared Talk, section, join and acceptance rules live in pure realm modules with no direct or transitive core dependency.
- An architecture test rejects core imports in seat_frames, agent_rules_text and the extracted rules, including lazy imports.
- Before-and-after fixtures prove identical full prompts, role texts and agent frames across supported seats, crafts and rule options.
- Critical tests and affected module tests pass; existing core rule entry points remain compatible.
- The change was reviewed and no blocking finding is left

## Out
- Changing prompt wording, output formats or Board schemas
- Changing Talk, spec or acceptance behavior
- Refactoring unrelated lazy imports

## Risks
Risk: Medium

The extraction is bounded, but shared prompts have many parameterized variants that must remain exact.

Product:
- A whitespace or interpolation change could alter model instructions.

Tech:
- Leaving a helper or constant behind could retain an indirect core dependency.
- Moving rule entry points could break callers or tests.

## Depends on
- 154-a-leader-is-a-skill-in-claude-code — A leader is a skill in Claude Code

## Stages
1. k1 Extract shared seat rules into realm (L)

## Open questions

## Decisions
