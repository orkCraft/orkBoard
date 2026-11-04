"""What a project's model calls spent, and where tokens went for nothing (decisions §228): read from the day logs every
call is kept in (`.orkcraft/logs/<day>/<building>/calls.jsonl`, realm/call_log.py), by code, no model. No face: `orkboard
drive spend` prints it (gui/drive.py), and the beta's run reports it (docs/beta/run-the-whole-way.md).

    spend_report.lines_of(root, since="2026-11-03")   # the calls, oldest first, from that day on ("" for every day kept)
    spend_report.report(lines, goal="jump")            # the totals, by tool and model, by step, by goal, the dearest, the waste
    spend_report.text(report)                          # the same in plain lines, for a terminal

**The waste** names what is worth a look, never a verdict: a call that **failed** (its exit code not 0) and what it cost;
a call that **wrote a big cache and read none** (`CACHE_BIG` tokens or more written: the same prefix paid again, as when
leaders of one round start at once, spec 120 §5.1); a **heavy read** (`HEAVY_IN` tokens or more in, under `SMALL_OUT`
out); a step **asked again** (`AGAIN` calls or more of one step for one goal). A tool that names its tokens otherwise
has them read by their names (`input`/`prompt`, `cache_read`/`cached`, `cache_creation`); a cost the tool did not give
is counted apart, never as $0.
"""
from __future__ import annotations

import json
from pathlib import Path

CACHE_BIG = 20_000
HEAVY_IN = 60_000
SMALL_OUT = 1_000
AGAIN = 3
TOP = 5


def lines_of(root: Path, since: str = "") -> list[dict]:
    logs = Path(root) / ".orkcraft" / "logs"
    out: list[dict] = []
    if not logs.is_dir():
        return out
    for day in sorted(p for p in logs.iterdir() if p.is_dir() and p.name >= since):
        for path in sorted(day.glob("*/calls.jsonl")):
            for row in path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    line = json.loads(row)
                except ValueError:
                    continue
                if isinstance(line, dict):
                    line.setdefault("day", day.name)
                    out.append(line)
    return sorted(out, key=lambda r: (str(r.get("at") or r.get("day")), r.get("n") or 0))


def tokens_of(line: dict) -> dict:
    """`{in, out, cache_read, cache_write, total}` of a call, whichever names its tool gave them."""
    usage = line.get("usage") if isinstance(line.get("usage"), dict) else {}

    def num(key: str) -> int:
        v = usage.get(key)
        return int(v) if isinstance(v, (int, float)) else 0

    def like(*parts: str) -> int:
        return sum(int(v) for k, v in usage.items() if isinstance(v, (int, float)) and any(p in k for p in parts))
    cache_read = like("cache_read", "cached")
    cache_write = like("cache_creation", "cache_write")
    given_in = num("input_tokens") or num("prompt_tokens")
    # Claude counts its input apart from the cache; an OpenAI-shaped usage (`cached_input_tokens`) counts it within
    out = {"in": max(given_in - cache_read, 0) if "cached_input_tokens" in usage or "cached_tokens" in usage else given_in,
           "out": num("output_tokens") or num("completion_tokens"), "cache_read": cache_read, "cache_write": cache_write}
    total = line.get("tokens")
    out["total"] = int(total) if isinstance(total, (int, float)) else out["in"] + out["out"] + out["cache_read"] + out["cache_write"]
    return out


def _add(row: dict, line: dict) -> None:
    t = tokens_of(line)
    row["calls"] += 1
    row["tokens"] += t["total"]
    cost = line.get("cost")
    if isinstance(cost, (int, float)):
        row["cost"] = round(row["cost"] + float(cost), 6)
    else:
        row["unpriced"] += 1


def _group(lines: list[dict], key) -> list[dict]:
    rows: dict[tuple, dict] = {}
    for line in lines:
        k = key(line)
        row = rows.setdefault(k, {**dict(zip(("a", "b"), k)), "calls": 0, "tokens": 0, "cost": 0.0, "unpriced": 0})
        _add(row, line)
    return sorted(rows.values(), key=lambda r: (-r["cost"], -r["tokens"]))


def report(lines: list[dict], goal: str = "") -> dict:
    lines = [ln for ln in lines if not goal or ln.get("idea") == goal]
    total = {"calls": 0, "tokens": 0, "cost": 0.0, "unpriced": 0, "seconds": 0.0, "in": 0, "out": 0, "cache_read": 0, "cache_write": 0}
    for line in lines:
        _add(total, line)
        total["seconds"] = round(total["seconds"] + float(line.get("seconds") or 0), 1)
        t = tokens_of(line)
        for k in ("in", "out", "cache_read", "cache_write"):
            total[k] += t[k]
    fed = total["in"] + total["cache_read"] + total["cache_write"]
    total["cache_share"] = round(total["cache_read"] / fed, 3) if fed else None
    rename = lambda rows, a, b: [{a: r.pop("a"), **({b: r.pop("b")} if b else {}), **{k: v for k, v in r.items() if k != "b"}} for r in rows]
    by_tool = rename(_group(lines, lambda ln: (ln.get("tool") or "?", ln.get("model") or "")), "tool", "model")
    by_step = rename(_group(lines, lambda ln: (ln.get("step") or ln.get("purpose") or "?", "")), "step", "")
    by_goal = rename(_group([ln for ln in lines if ln.get("idea")], lambda ln: (ln["idea"], "")), "goal", "")
    dear = sorted(lines, key=lambda ln: (-(ln.get("cost") or 0), -tokens_of(ln)["total"]))[:TOP]
    failed = [ln for ln in lines if ln.get("code")]
    rewritten = [ln for ln in lines if tokens_of(ln)["cache_write"] >= CACHE_BIG and not tokens_of(ln)["cache_read"]]
    heavy = [ln for ln in lines if tokens_of(ln)["in"] + tokens_of(ln)["cache_write"] >= HEAVY_IN and tokens_of(ln)["out"] < SMALL_OUT]
    counts: dict[tuple, int] = {}
    for ln in lines:
        if ln.get("idea") and ln.get("step"):
            counts[(ln["idea"], ln["step"])] = counts.get((ln["idea"], ln["step"]), 0) + 1

    def money(rows: list[dict]) -> float:
        return round(sum(float(r.get("cost") or 0) for r in rows), 6)
    return {"goal": goal, "total": total, "by_tool": by_tool, "by_step": by_step, "by_goal": by_goal,
            "dearest": [{k: ln.get(k) for k in ("at", "idea", "step", "purpose", "tool", "model", "cost", "seconds")} | {"tokens": tokens_of(ln)["total"]}
                        for ln in dear],
            "waste": {"failed": {"calls": len(failed), "cost": money(failed)},
                      "cache_rewritten": {"calls": len(rewritten), "tokens": sum(tokens_of(ln)["cache_write"] for ln in rewritten), "cost": money(rewritten)},
                      "heavy_reads": {"calls": len(heavy), "tokens": sum(tokens_of(ln)["total"] for ln in heavy), "cost": money(heavy)},
                      "asked_again": [{"goal": g, "step": s, "calls": n} for (g, s), n in sorted(counts.items()) if n >= AGAIN]}}


def _usd(cost: float, unpriced: int, calls: int | None = None) -> str:
    """Unknown is not zero (spec 143 G.2): with every call of `calls` unpriced there is no figure, only that no price is known."""
    if unpriced and calls is not None and unpriced >= calls:
        return "no price known for these models"
    return f"${cost:.2f}" + (f" + {unpriced} call{'s' if unpriced != 1 else ''} with no price known" if unpriced else "")


def text(r: dict) -> str:
    t = r["total"]
    out = [f"{t['calls']} calls{' for ' + r['goal'] if r['goal'] else ''}: {t['tokens']:,} tokens, {_usd(t['cost'], t['unpriced'], t['calls'])}{'' if t['unpriced'] >= t['calls'] and t['unpriced'] else ' at API prices'}, "
           f"{t['seconds']:g} s",
           f"  in {t['in']:,} · out {t['out']:,} · cache read {t['cache_read']:,} · cache written {t['cache_write']:,}"
           + (f" · read from the cache: {t['cache_share']:.0%}" if t["cache_share"] is not None else "")]
    for title, rows, keys in (("By tool and model", r["by_tool"], ("tool", "model")), ("By step", r["by_step"], ("step",)),
                              ("By goal", r["by_goal"], ("goal",))):
        if rows:
            out.append(title)
            out += [f"  {' '.join(str(row[k]) for k in keys if row.get(k)):<32} {row['calls']:>4} calls {row['tokens']:>11,} tokens  "
                    f"{_usd(row['cost'], row['unpriced'], row['calls'])}" for row in rows]
    if r["dearest"]:
        out.append("The dearest calls")
        out += [f"  {d['at']}  {d.get('idea') or '-'} · {d.get('step') or d.get('purpose') or '?'} · {d['tool']} {d.get('model') or ''}: "
                f"{d['tokens']:,} tokens, {_usd(float(d.get('cost') or 0), 0 if d.get('cost') is not None else 1, 1)}" for d in r["dearest"]]
    w = r["waste"]
    out.append("Worth a look")
    out.append(f"  failed calls: {w['failed']['calls']} ({_usd(w['failed']['cost'], 0)})")
    out.append(f"  a big cache written and none read: {w['cache_rewritten']['calls']} calls, {w['cache_rewritten']['tokens']:,} tokens "
               f"({_usd(w['cache_rewritten']['cost'], 0)})")
    out.append(f"  heavy reads with a short answer: {w['heavy_reads']['calls']} calls, {w['heavy_reads']['tokens']:,} tokens "
               f"({_usd(w['heavy_reads']['cost'], 0)})")
    out += [f"  asked again: {a['goal']} · {a['step']}, {a['calls']} calls" for a in w["asked_again"]] or ["  no step asked again"]
    return "\n".join(out)
