"""Orc tiers: how heavy a model an orc thinks with. The code keeps its words; a person reads how seasoned the
mind is, with as many chevrons (realm/lexicon.py):

    ★★★ elder     Veteran: the heavy models: opus, gemini pro, gpt astra
    ★★  warrior   Seasoned: the middle: sonnet, gemini flash with high reasoning, gpt sol
    ★   laborer   Novice: the light ones: haiku, gemini flash with low reasoning, gpt luna

A harness step picks its tier (`{"role": "run", "harness": "claude", "tier": "elder"}`) and the
model follows from the harness; a step may name its `model` outright, and the tier is read from
it.
"""
from __future__ import annotations

from orkboard.realm import harnesses

TIERS = ("elder", "warrior", "laborer")          # heaviest first
TIER_ICONS = {"elder": "★★★", "warrior": "★★", "laborer": "★"}     # chevrons
TIER_LABELS = {"elder": "Veteran", "warrior": "Seasoned", "laborer": "Novice"}
# The model family of each tier, per harness (realm/harnesses.py holds them; a run names its newest model).
MODELS = {h.id: dict(h.models) for h in harnesses.REGISTRY.values()}
# What a step runs on when it names neither: agy's own default is flash-high.
DEFAULT_MODEL = {h.id: h.default_model for h in harnesses.REGISTRY.values() if h.default_model}




def tool_of(step: dict) -> str:
    """The tool a step runs on: `main` (or none) follows the machine's main tool, the tool now while it is out (docs/specs/105 §2.3, realm/tool_now.py); any
    other id was set on purpose and is never moved."""
    harness = str(step.get("harness") or "")
    if harness in ("", harnesses.MAIN):
        from orkboard import settings
        from orkboard.realm import tool_now
        return tool_now.following(settings.main_tool())
    return harness


def tier_of_model(model: str) -> str | None:
    """opus / gemini pro / gpt astra → elder; sonnet / flash-high / gpt sol → warrior;
    haiku / flash-low / gpt luna → laborer (and every tool's own table, realm/harnesses.py)."""
    return harnesses.tier_of_model(model)


def step_model(step: dict) -> str:
    """The model a harness step runs on: its own, else its tier's, else "" (the CLI's default)."""
    if step.get("model"):
        return str(step["model"])
    tier = step.get("tier")
    return MODELS.get(tool_of(step), {}).get(str(tier), "") if tier else ""


def resolve(harness: str, model: str) -> str:
    """`claude:elder` → opus: a tier word in place of a model names its model; anything else stays."""
    return MODELS.get(tool_of({"harness": harness}), {}).get(model, model) if model in TIERS else model




def step_tier(step: dict) -> str | None:
    model = step_model(step) or DEFAULT_MODEL.get(tool_of(step), "")
    return tier_of_model(model) or (step.get("tier") if step.get("tier") in TIERS else None)




def icon(tier: str | None) -> str:
    return TIER_ICONS.get(tier or "", "")


def label(tier: str | None) -> str:
    return f"{TIER_ICONS[tier]} {TIER_LABELS[tier]}" if tier in TIER_ICONS else ""
