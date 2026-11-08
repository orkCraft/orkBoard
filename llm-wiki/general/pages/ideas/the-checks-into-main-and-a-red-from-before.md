---
owner: board
kind: idea
track: tech
order: 111
size: M
priority: normal
short: Main checks
phase: done
by: person
schema: 3
risk_model: medium
touches: ["orkboard/realm/main_checks.py", "orkboard/realm/gate_rerun.py", "orkboard/gui/ideas_gate.py", "orkboard/gui/static/js/table/{checks,portal,discard,tomain}.js", "tests/test_main_checks.py", "tests/test_gate_rerun.py", "tests/test_goal_main.py", "tests/test_to_main_browser.py", "tests/test_discard_table_browser.py"]
depends_on: ["149-what-a-goal-on-local-codex-found"]
checks: [{"by": "reviewer", "applies": true, "why": ""}]
risk: medium
risk_triggers: ["CI and deploy"]
gate: 41aac74 · 14 files · green
---
# Main checks explain and remember failures

## Gist
Main checks distinguish old failures and show what blocks main.
Keep failed test names; clear readiness after red.
Retry only through an explicit action.

## Why
Existing failures should not blame new work, and a failed check must not leave the page promising that main is ready.

## Done when
- Main checks retry named pytest failures alone, then compare remaining failures against the checked main base within the remaining timeout, following spec 149 E; flaky and pre-existing failures are reported, while new or unresolved failures block main.
- The check record retains failed test identities and their classification, not merely counts or the first failure; incomplete diagnostics never imply a pass.
- After a blocking red, reopening the discard shows its reason and failed tests; Ready for main and To main no longer appear enabled for the failed candidate.
- To main never silently retries a failed check; an explicit Test again action shows progress, and passing results authorize only the unchanged candidate and main base.
- The change was reviewed and no blocking finding is left

## Out
- Repairing unrelated pre-existing test failures.
- Redesigning the discard or Release lane.
- Changing task-gate policy or allowing automatic merges.

## Risks
Risk: Medium — CI and deploy (`Release`)

The change affects merge eligibility and shared check state across backend and page.

Product:
- Calling inherited failures green without explaining them could hide repository health problems.
- Removing readiness without a visible retry action could strand the person.

Tech:
- Comparing counts instead of test identities could excuse a new failure.
- Stale results could authorize a changed candidate or main base.
- Diagnostic reruns must share the timeout and remove temporary worktrees.

## Depends on
- 149-what-a-goal-on-local-codex-found — What a goal on local Codex found

## Stages
1. k1 Explain failures and enforce main eligibility (L)
2. k2 Review failure handling before merge (L), after k1
3. k3 Fix: on reopening the discard after red, show the retained reason and failed tests
4. k4 Fix: separate reading checks from retrying: only an explicit Test again
5. r1 The review's fixes (trial 152 E §8): a written command's red is never excused; a green Test again lifts the seal; no lock through the tests

## Open questions

## Decisions
- Only the gate's own pytest run may let a flaky or pre-existing red through; a check the project wrote as a command is red whatever its tests were
  (trial 152 E §8, R1).
