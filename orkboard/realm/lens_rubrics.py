"""The frame each craft's senior reviews its map by (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §2.1–§2.2; decisions §184): a few *aspects* a leader looks at, each with the question it asks
and the kinds of hints of code (`realm/map_signals.py`) that ground it. Pure data and code; no face, no model.

    lens_rubrics.RUBRICS[craft] = {"framework": str, "short": str, "aspects": ({"id", "name", "ask", "signals": (kind, …)}, …)}     # the crafts: tech, design, product, game-design, art, release, marketing, run, liveops
    lens_rubrics.rubric(craft)                       # the craft's rubric, or None (a craft with none)
    lens_rubrics.aspect_of(craft, kind)              # the aspect (its id) a hint's kind belongs to, "" for none
    lens_rubrics.prompt_lines(craft)                 # the rubric as lines for a model: "How a senior of <craft> reviews this map: <framework>." then "- <id>: <name>. <ask>"; "" for none
    lens_rubrics.scorecard(craft, rec)               # [{id, name, ask, state, n, hints: [words]}] in the rubric's order, from a concerns record (`realm/concerns.py`); [] for none

`framework` is a line for the model, `short` the few words the strip shows. The ids are code's; the names and asks are the interface's and the model's. Every kind of hint of a craft is in exactly one
of its aspects. An aspect's `state` in the scorecard: `alert` (an open concern of the aspect at alert), else `note` (an open one at note), else `hint` (code noticed something on the aspect and the
leader let it be), else `clear` (a look was made: nothing), else `unlooked` (no look yet: `rec.at` empty). `n` is the open concerns of the aspect (a concern made into a goal is not open, as
`concerns.counts`); `hints` the words of the aspect's hints, three at most. Run and LiveOps have no map: their rubrics judge in Talk only (`realm/idea_objections.py`) and name no signals.
"""
from __future__ import annotations

HINT_WORDS = 3                       # the words of an aspect's hints the scorecard gives, at most


def _a(id_: str, name: str, ask: str, *signals: str) -> dict:
    return {"id": id_, "name": name, "ask": ask, "signals": signals}


RUBRICS = {
    "tech": {"framework": "C4's containers and parts; ISO/IEC 25010's maintainability, security and reliability; hotspots, where change and size meet; the stable-dependencies principle",
             "short": "C4 · ISO 25010 · hotspots",
             "aspects": (_a("modularity", "Modularity", "Are the parts' edges clean: no cycles, no part reaching into many others?", "cycle", "fan_out", "unstable"),
                         _a("coupling", "Coupling", "Does a change ripple: a part everyone needs, a shared part changed from many containers?", "fan_in", "shared_churn"),
                         _a("hotspots", "Hotspots", "Where is code both big and often changed, where bugs and slow work collect?", "big", "hotspot"),
                         _a("testability", "Testability", "Is what changes often covered by tests?", "untested_churn"),
                         _a("safety", "Security and reliability", "Does a part take people's input, secrets or money without a guard; is one part a single point of failure?"))},
    "design": {"framework": "Nielsen's ten usability heuristics, WCAG 2.2 AA, and the person's way through the screens",
               "short": "Nielsen · WCAG 2.2",
               "aspects": (_a("flow", "The way through", "Can a person reach every screen and finish what they came for?", "loose", "dead_end"),
                           _a("status", "State and errors", "Does each screen show loading, empty and error states and say what happened?", "no_states"),
                           _a("access", "Accessibility", "Text alternatives, keyboard, labels, contrast and touch targets of 24 px or more?", "a11y"),
                           _a("consistency", "Consistency", "Do the screens use one set of words, controls and layouts for the same thing?"),
                           _a("seen", "Seen", "Has each screen been looked at as a picture?", "no_picture"))},
    "product": {"framework": "Teresa Torres' opportunity solution tree, jobs to be done, and prioritising by reach, impact, confidence and effort",
                "short": "OST · JTBD · RICE",
                "aspects": (_a("outcome", "Outcome", "Is the outcome one number the team can move?", "vague_outcome"),
                            _a("opportunities", "Opportunities", "Is every job served, and where do pains pile up?", "unserved", "pains", "pain_loose"),
                            _a("evidence", "Evidence", "Is a bet tested by an experiment before it is built big?", "no_evidence"),
                            _a("focus", "Focus", "Do the goals in line serve the outcome, the best bets first?", "off_tree"))},
    "game-design": {"framework": "MDA and the eight kinds of fun, core, session and meta loops, an economy of sources and sinks, flow, and why a player comes back",
                    "short": "MDA · loops · economy",
                    "aspects": (_a("loop", "Core loop", "Does every loop reward the player, and does each span feed the next?", "no_reward", "unfed"),
                                _a("economy", "Economy", "Does every currency have a source and a sink?", "no_source", "pile_up"),
                                _a("pacing", "Pacing and flow", "Do the intensities rise and rest, with no flat stretch or sudden spike?", "flat", "spike"),
                                _a("retention", "Retention", "Is there a reason to come back on day 1, day 7 and day 30?", "no_hook"),
                                _a("grounded", "Grounded", "Does each step rest on the files that make it?", "unground"))},
    "art": {"framework": "an art bible (one style, one grid of sizes), the asset pipeline (names, folders, every asset used), and a budget for what ships",
            "short": "Art bible · pipeline · budget",
            "aspects": (_a("style", "Style", "Do the pictures keep one style and one grid of sizes?", "mixed_sizes"),
                        _a("pipeline", "Pipeline", "Are files named and kept by one convention, and is every asset used?", "naming", "unused"),
                        _a("budget", "Budget", "Are files light enough for where they ship?", "heavy"),
                        _a("sound", "Sound", "Do the sounds and music share one loudness and cover the game's moments?"))},
    "release": {"framework": "DORA's four keys (how often, how fast, how often it fails, how fast it recovers), small batches, a release-readiness checklist and semantic versioning",
                "short": "DORA · readiness · semver",
                "aspects": (_a("batch", "Batch size", "Is what waits for main small enough to ship and to take back?", "big_batch"),
                            _a("lead_time", "Lead time", "How long has done work waited for main?", "stale"),
                            _a("readiness", "Readiness", "Is the changelog written and the version said?", "no_changelog"),
                            _a("failure", "Change failure", "How often must a change be reverted or fixed again?", "reverts"))},
    "marketing": {"framework": "AARRR (acquisition, activation, retention, referral, revenue), app store optimisation, and April Dunford's positioning",
                  "short": "AARRR · ASO · positioning",
                  "aspects": (_a("acquisition", "Acquisition", "Where do people first hear of it?", "no_channel"),
                              _a("store", "Store page", "Does the store page or site say who it is for and why, within the stores' limits?", "aso_title", "aso_short", "no_shots"),
                              _a("activation", "Activation", "Does the first session reach the moment the product is worth it?", "no_onboarding"),
                              _a("retention", "Retention", "What brings people back?", "no_return"),
                              _a("referral", "Referral", "Can people bring others?", "no_share"),
                              _a("revenue", "Revenue", "Where does it earn?", "no_revenue"))},
    "run": {"framework": "Google SRE: SLOs and error budgets, the four golden signals (latency, traffic, errors, saturation), runbooks",
            "short": "SRE",
            "aspects": (_a("slo", "SLOs", "Is there a number for how well it must work, and an error budget to spend?"),
                        _a("signals", "Golden signals", "Are latency, traffic, errors and saturation watched?"),
                        _a("runbooks", "Runbooks", "Does each thing that can break say how to mend it?"))},
    "liveops": {"framework": "LiveOps: an events calendar, KPIs (daily players, retention, revenue per player), remote config",
                "short": "LiveOps",
                "aspects": (_a("calendar", "Events", "Is there a calendar of what happens when, and who runs it?"),
                            _a("kpis", "KPIs", "Are daily players, retention and revenue per player watched?"),
                            _a("config", "Remote config", "Can what is live be changed without a release?"))},
}


def rubric(craft: str) -> dict | None:
    """The craft's rubric (see the module), or None for a craft with none."""
    return RUBRICS.get(craft)


def aspect_of(craft: str, kind: str) -> str:
    """The id of the aspect a hint's `kind` belongs to in the craft's rubric; "" for none."""
    for a in (RUBRICS.get(craft) or {}).get("aspects", ()):
        if kind in a["signals"]:
            return a["id"]
    return ""


def prompt_lines(craft: str) -> str:
    """The rubric as lines for a model: how a senior of the craft reviews the map, then one line an aspect (`- <id>: <name>. <ask>`); "" for a craft with none."""
    r = RUBRICS.get(craft)
    if r is None:
        return ""
    return "\n".join([f"How a senior of {craft} reviews this map: {r['framework']}.", *[f"- {a['id']}: {a['name']}. {a['ask']}" for a in r["aspects"]]])


def scorecard(craft: str, rec: dict) -> list[dict]:
    """Each aspect of the craft's rubric in its state (see the module) from a concerns record: `[{id, name, ask, state, n, hints}]` in the rubric's order; [] for a craft with none."""
    r = RUBRICS.get(craft)
    if r is None:
        return []
    open_ = [c for c in rec.get("concerns") or [] if not c.get("idea")]
    hints = rec.get("hints") or []
    out = []
    for a in r["aspects"]:
        mine = [c for c in open_ if c.get("aspect") == a["id"]]
        words = [h["words"] for h in hints if (h.get("aspect") or aspect_of(craft, h.get("kind") or "")) == a["id"] and h.get("words")][:HINT_WORDS]
        if any(c["level"] == "alert" for c in mine):
            state = "alert"
        elif mine:
            state = "note"
        elif words:
            state = "hint"
        else:
            state = "clear" if rec.get("at") else "unlooked"
        out.append({"id": a["id"], "name": a["name"], "ask": a["ask"], "state": state, "n": len(mine), "hints": words})
    return out
