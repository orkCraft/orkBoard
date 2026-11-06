---
owner: board
kind: idea
track: tech
order: 109
size:
priority: normal
short: Cut the import cycle
phase: new
by: person
schema: 3
---
# Cut the import cycle between realm and core: realm/seat_frames.py and…

## Gist
Cut the import cycle between realm and core: realm/seat_frames.py and realm/agent_rules_text.py import core/idea_talk, idea_sections and idea_accept, which import realm, a cycle hidden by lazy imports. Move each seat's rules where both read them without the cycle, every prompt unchanged by a character. Found by Tech's leader in goal 154's Talk; the person said: a goal of its own, after 154 D.

## Why

## Done when

## Out

## Risks

## Depends on

## Stages

## Open questions

## Decisions
