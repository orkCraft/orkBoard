"""The machine's settings that are cleaned on load and kept apart from the Board's: keeping the computer awake, Do not disturb, the phones,
the push notifications, the growth and the person's profile. Pure; `orkboard/settings.py` says them as its own (it was past 600 lines:
CLAUDE.md, *Where code goes*)."""
from __future__ import annotations

import re

PROFILE_TEXT = ("orchestration", "role", "role_other", "industry", "industry_other", "day_other", "kin")
PROFILE_LISTS = ("day", "mcp")   # mcp: the MCP servers the orks may use (gui/onboarding.py)
KEEP_AWAKE = ("off", "carts", "phone")


def awake_mode(raw: object) -> str:
    """One of KEEP_AWAKE; the old true / false (and nothing) read as "carts" / "off", as they behaved."""
    if raw in KEEP_AWAKE:
        return str(raw)
    return "off" if raw is False else "carts"


def clean_dnd(raw: object) -> str:
    """Do not disturb as stored: "on", an ISO time it ends at, else "" (off)."""
    if raw == "on":
        return "on"
    if isinstance(raw, str) and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d)?", raw):
        return raw
    return ""


def clean_phones(raw: object) -> list[dict]:
    """The paired phones that are whole: an id, a name, a token's hash; anything else is dropped (a phone
    whose entry broke pairs again)."""
    out: list[dict] = []
    for p in raw if isinstance(raw, list) else []:
        if not isinstance(p, dict):
            continue
        pid, name, digest = p.get("id"), p.get("name"), p.get("hash")
        if not (isinstance(pid, str) and re.fullmatch(r"[0-9a-f]{16}", pid) and isinstance(digest, str)
                and re.fullmatch(r"[0-9a-f]{64}", digest) and isinstance(name, str) and name.strip()):
            continue
        if any(o["id"] == pid for o in out):
            continue
        entry = {"id": pid, "name": name.strip()[:60], "hash": digest,
                 "paired": str(p.get("paired") or "")[:32], "seen": str(p.get("seen") or "")[:32]}
        if (push := clean_push(p.get("push"))) is not None:
            entry["push"] = push
        out.append(entry)
    return out


PUSH_KEY = re.compile(r"[A-Za-z0-9_-]{1,200}")


def clean_push(raw: object) -> dict | None:
    """A phone's Web Push subscription (docs/specs/42-coming-back.md §3.3): its push service's endpoint, the two keys, when it
    was made and the day the morning's push was sent; None for anything else (a bad one drops the whole subscription)."""
    if not isinstance(raw, dict):
        return None
    endpoint, p256dh, auth = raw.get("endpoint"), raw.get("p256dh"), raw.get("auth")
    morning = raw.get("morning") or ""
    if not (isinstance(endpoint, str) and re.fullmatch(r"https://[^\s]{1,1016}", endpoint) and len(endpoint) <= 1024
            and isinstance(p256dh, str) and PUSH_KEY.fullmatch(p256dh) and isinstance(auth, str) and PUSH_KEY.fullmatch(auth)
            and isinstance(morning, str) and (not morning or re.fullmatch(r"\d{4}-\d\d-\d\d", morning))):
        return None
    return {"endpoint": endpoint, "p256dh": p256dh, "auth": auth, "at": str(raw.get("at") or "")[:32], "morning": morning}


def clean_growth(raw: object) -> dict:
    """The mascot's stage (1–4) and the deeds done with their dates; {} for anything else."""
    if not isinstance(raw, dict):
        return {}
    out: dict = {}
    if isinstance(raw.get("stage"), int) and 1 <= raw["stage"] <= 4:
        out["stage"] = raw["stage"]
    deeds = raw.get("deeds")
    if isinstance(deeds, dict):
        out["deeds"] = {str(k)[:40]: str(v)[:20] for k, v in list(deeds.items())[:40] if isinstance(v, str)}
    return out


def clean_profile(raw: object) -> dict:
    """Only the known keys, as strings and lists of strings; {} for anything else."""
    if not isinstance(raw, dict):
        return {}
    out: dict = {k: str(raw[k])[:200] for k in PROFILE_TEXT if isinstance(raw.get(k), str) and raw[k].strip()}
    for k in PROFILE_LISTS:
        if isinstance(raw.get(k), list):
            out[k] = [str(x)[:40] for x in raw[k] if isinstance(x, str)][:20]
    tools_ = raw.get("ai_tools")
    if isinstance(tools_, dict):
        rated = {}
        for t, r in list(tools_.items())[:20]:
            if not isinstance(r, dict):
                continue
            keep: dict = {k: bool(r.get(k)) for k in ("like", "dislike")}
            keep.update({k: str(r[k])[:40] for k in ("title", "good", "weak") if isinstance(r.get(k), str) and r[k]})
            rated[str(t)[:40]] = keep
        if rated:
            out["ai_tools"] = rated
    return out
