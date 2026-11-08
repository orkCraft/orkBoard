"""A craft's tools, apart from the harnesses in tools.py (spec 158, stage A).

Only permissions and money caps live on the Board. Hosts and prices are fixed here;
keys stay on the machine and never occur in the chair's rows. API makers run in
Orkboard, so they do not require a harness's native `makes` capability.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal

from orkboard.realm import harnesses, idea_secrets, ideas, party_recipes


@dataclass(frozen=True)
class Price:
    dated: str
    amount: str
    currency: str
    unit: str
    source: str
    estimate: bool = False


@dataclass(frozen=True)
class Tool:
    id: str
    title: str
    crafts: tuple[str, ...]
    makes: str
    kind: Literal["code", "mcp", "api"]
    host: str
    official_api: bool
    prices: tuple[Price, ...]
    maker: str
    key_env: str = ""
    needs: tuple[str, ...] = ()   # harness capabilities, only when the harness runs it
    leaves: str = ""


# Dated published rates, not a live quote. Image input and output are separate
# charges; later makers must reserve both, never use the output rate as a call price.
REGISTRY = {
    "openai-images": Tool(
        "openai-images", "OpenAI Images", ("art",), "pictures", "api", "api.openai.com", True,
        tuple(Price("2026-11-08", amount, "USD", unit, "https://developers.openai.com/api/docs/pricing")
              for amount, unit in (("2.50", "gpt-image-2 text input / 1M tokens"),
                                   ("4.00", "gpt-image-2 image input / 1M tokens"),
                                   ("15.00", "gpt-image-2 image output / 1M tokens"))),
        "Picture maker", "OPENAI_API_KEY", leaves="The picture prompt is sent to OpenAI."),
    "elevenlabs-sound": Tool(
        "elevenlabs-sound", "ElevenLabs Sound Effects", ("art",), "sound", "api", "api.elevenlabs.io", True,
        (Price("2026-11-08", "0.12", "USD", "minute of sound", "https://elevenlabs.io/pricing/api", True),),
        "Sound maker", "ELEVENLABS_API_KEY", leaves="The sound prompt is sent to ElevenLabs."),
}


def get(tool_id: str) -> Tool | None:
    return REGISTRY.get(tool_id)


def key(tool_id: str) -> str | None:
    """Request-time key lookup; the keychain wins over the provider's variable.

    No file fallback: tool keys are machine credentials, never project state.
    The existing test isolation switch keeps the real keychain out of tests.
    """
    tool = get(tool_id)
    if tool is None or not tool.key_env:
        return None
    kc = idea_secrets._keychain()
    if kc is not None:
        try:
            value = kc.get_password(idea_secrets.SERVICE, f"tools/{tool_id}")
            if isinstance(value, str) and value.strip():
                return value
        except Exception:
            pass
    return os.environ.get(tool.key_env, "").strip() or None


def availability(tool: Tool, harness: str, *, check_key: bool = True) -> tuple[bool, str]:
    """Here and its why. A chair exposes presence only, never the credential."""
    if tool.kind == "api" and not tool.official_api:
        return False, "no official API"
    h = harnesses.get(harness)
    if tool.needs and (h is None or not set(tool.needs).issubset(h.makes)):
        return False, "its AI tool cannot make it"
    if check_key and tool.key_env and key(tool.id) is None:
        return False, "no key on this computer"
    return True, ""


def _cap(raw: object, currency: str) -> dict:
    if not isinstance(raw, dict) or raw.get("currency") != currency or isinstance(raw.get("amount"), bool):
        raise ValueError(f"Set a maker's cap as an amount in {currency}")
    try:
        amount = Decimal(str(raw.get("amount")))
    except InvalidOperation:
        raise ValueError(f"Set a maker's cap as an amount in {currency}") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"Set a positive maker cap in {currency}")
    return {"amount": format(amount, "f"), "currency": currency}


def clean_taken(raw: object) -> dict[str, dict]:
    """`craft_tools: {id: {cap: {amount, currency}}}`; malformed entries are off."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {}
    if not isinstance(raw, dict):
        return {}
    out = {}
    for tool_id, value in raw.items():
        tool = get(tool_id)
        if tool is None or not isinstance(value, dict):
            continue
        try:
            out[tool_id] = {"cap": _cap(value.get("cap"), tool.prices[0].currency)}
        except ValueError:
            pass
    return out


def taken(root: Path, party: str) -> dict[str, dict]:
    page = ideas.track_page(root, party)
    return clean_taken(page.get("craft_tools")) if page is not None else {}


def set_taken(root: Path, party: str, tools: dict) -> None:
    """Replace taken tools; paid tools require a positive cap, with no default."""
    kept = clean_taken(tools)
    if not isinstance(tools, dict) or len(kept) != len(tools):
        raise ValueError("Each maker needs a known name and a positive cap in its currency")
    with ideas.LOCK:
        page = ideas.track_page(root, party)
        if page is None:
            raise ValueError(f"No party {party!r} to take makers")
        craft = party_recipes.craft_of(page.get("recipe"), page.get("leader"))
        if any(craft not in REGISTRY[t].crafts for t in kept):
            raise ValueError("That maker is not for this party's craft")
        page.set("craft_tools", json.dumps(kept) if kept else "")
        ideas._write(Path(root) / ideas.TRACKS / f"{party}.md", page.text())


def for_party(root: Path, party: str, harness: str, *, check_key: bool = True) -> list[dict]:
    """The chair's tools, taken or not, with machine availability and money only."""
    page = ideas.track_page(root, party)
    if page is None:
        return []
    craft = party_recipes.craft_of(page.get("recipe"), page.get("leader"))
    allowed = clean_taken(page.get("craft_tools"))
    rows = []
    for tool in REGISTRY.values():
        if craft not in tool.crafts:
            continue
        here, why = availability(tool, harness, check_key=check_key)
        rows.append({"id": tool.id, "title": tool.title, "maker": tool.maker, "kind": tool.kind, "makes": tool.makes,
                     "official_api": tool.official_api, "prices": [asdict(p) for p in tool.prices],
                     "here": here, "why": why, "taken": tool.id in allowed,
                     "cap": allowed.get(tool.id, {}).get("cap"), "leaves": tool.leaves})
    return rows
