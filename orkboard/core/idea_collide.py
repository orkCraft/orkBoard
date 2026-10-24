"""The judge of a collision (docs/specs/71-orkmaster-keeps-parties-apart.md §2.2, §3): two goals of different parties that the code found to
touch the same files, and one cheap model call, as the Orkmaster, to tell a collision from a coincidence. It runs only on what the finder
found (realm/collide.py `overlaps`); a project whose parties touch different things never calls it.

    judge(keeper, a, b, by="plan", words="")   # {"collide": bool, "why": "…" (≤ 200), "first": slug | "", "tokens", "cost"}
    prompt(root, state_dir, a, b, by, words)   # what it is given: titles, Done when and touches of both (≤ 3 000 characters)
    read_answer(text, a, b)                    # the answer, strictly: ValueError when it is not the JSON asked for

One shot, read-only, no tools, as the `orkmaster` role (realm/orkmaster.py) on the Target's `collide` step (the cheaper tier). `a` is the
goal asked about, `b` the one beside it. `keeper` has `ask`, `wiki_root`, `state_dir`, `measure`, `_tls` (core/idea_keeper.py). It writes
nothing and decides nothing: the person answers.
"""
from __future__ import annotations

from pathlib import Path

from orkboard.core.idea_keeper import first_json
from orkboard.realm import collide, idea_target, ideas, orkmaster

CHARS = 3_000                      # the most a call reads of the two goals
WHY_CHARS = collide.WHY_CHARS
WORDS_CHARS = 1_200                # of the words that changed a spec


def _block(root: Path, state_dir: Path, slug: str) -> str:
    page = ideas.idea_page(root, slug)
    party = next((t["title"] for t in ideas.tracks(root, make=False) if t["slug"] == (page.get("track") if page else "")), "")
    done = ideas.clean_text(page.section("Done when")) if page else ""
    return (f"{page.title if page else slug} (slug {slug}, party {party})\nDone when:\n{done[:700] or '(none)'}\n"
            f"Touches: {', '.join(collide.touches(root, state_dir, slug)[:12]) or '(none)'}")


def prompt(root: Path, state_dir: Path, a: str, b: str, by: str = "plan", words: str = "") -> str:
    """The call's prompt. By a plan: the two goals. By a change: the goal whose spec changed (`b`) and the words that changed."""
    common = collide.shared(collide.touches(root, state_dir, a), collide.touches(root, state_dir, b))
    parts = [("The goal asked about" if by == "plan" else "The goal that rests on what it was", _block(root, state_dir, a)),
             ("The goal beside it" if by == "plan" else "The goal whose spec changed", _block(root, state_dir, b)),
             ("Both touch", ", ".join(common[:12]) or "(nothing)")]
    if by == "change":
        parts.append(("What changed in its spec", " ".join(str(words).split())[:WORDS_CHARS] or "(not said)"))
    context = idea_target.cut(parts, CHARS)
    ask = ("Say whether the first goal's work rests on what the second goal's spec said before it changed" if by == "change" else
           "Say whether the two goals change the same thing")
    return f"""Two goals of different parties of this project touch the same files. {ask}: a collision is work done twice, undone or
broken by the other; two goals that only sit near each other in the same folder are a coincidence. Answer from what is here; read no file.

{context}Answer with one JSON object and nothing else:
{{"collide": true or false, "why": "one line for the person, at most {WHY_CHARS} characters", "first": "the slug of the goal that should go first, or empty"}}"""


def read_answer(text: str, a: str, b: str) -> dict:
    """`{"collide": bool, "why": str (≤ 200), "first": a | b | ""}` from the model's text; ValueError when it is not the JSON asked for
    (`collide` must be true or false)."""
    got = first_json(text)
    if not isinstance(got, dict) or not isinstance(got.get("collide"), bool):
        raise ValueError("the Orkmaster's answer was not the JSON it was asked for")
    first = str(got.get("first") or "").strip()
    return {"collide": got["collide"], "why": " ".join(str(got.get("why") or "").split())[:WHY_CHARS], "first": first if first in (a, b) else ""}


def judge(keeper, a: str, b: str, by: str = "plan", words: str = "") -> dict:
    """The call, measured. Raises what the keeper's `ask` raises (no model, a spent budget, a stop) or ValueError for an answer that is no
    JSON; the caller logs it and goes on."""
    root, state = keeper.wiki_root(), keeper.state_dir
    orkmaster.install(state)
    keeper._tls.key = keeper._tls.slug = a                 # its spend is the goal asked about's
    text, *_rest = keeper.ask("collide", prompt(root, state, a, b, by, words), tools=False, as_role=orkmaster.ROLE)
    got = read_answer(text, a, b)
    m = keeper.measure()
    return {**got, "tokens": m.get("tokens"), "cost": m.get("cost")}
