"""The v1 shell on the desktop (docs/specs/33-v1-shell.md §6–§7), in a real browser at 1 440 × 900 against a stub host that
answers the §5 commands: the Board on the left, the preview in the centre (the Map: its ideas carry their results, spec 48) and Agents under it as VS Code's
terminal. A click on an idea, a to-do, a chip and a result opens the right preview; Merge is off on red with its reason; Send
back needs its line; no camp. Screenshots to docs/design/img/v1/ when ORKCRAFT_SHOTS is set."""
from __future__ import annotations

import copy
import datetime as dt
import json
import os
import re
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.browser_kit import WAIT_MS, gui, open_pane  # noqa: E402,F401  (fixture)
from orkboard.realm import library, plans, roles  # noqa: E402

_TODAY = dt.date.today().isoformat()                 # a reset today reads "resets at 18:00", whatever the day
_IN_TWO_DAYS = (dt.date.today() + dt.timedelta(days=2)).isoformat()

pytestmark = pytest.mark.browser

QR = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

SHOTS = Path(__file__).resolve().parent.parent / "docs" / "design" / "img" / "v1"
SECTIONS = ["Gist", "Why", "Done when", "Out", "Risks", "Depends on", "Stages", "Open questions", "Decisions"]      # spec 35 §3
STAGES = "1. k1 Read the sync code (S)\n2. k2 Add the queue (M) ∥ k3 Retry on a lost signal (M)\n3. k4 Test it offline (L), after k3"
GREEN = {"passed": 20, "failed": 0, "failing": [], "tail": "20 passed in 1.1s", "green": True}
RED = {"passed": 10, "failed": 10, "failing": ["tests/test_sync.py::test_retry", "tests/test_sync.py::test_queue", "t3"],
       "tail": "10 failed, 10 passed in 2.0s", "green": False}
PATCH = "diff --git a/sync.py b/sync.py\n--- a/sync.py\n+++ b/sync.py\n@@ -1,2 +1,3 @@\n keep = 1\n-old = 2\n+new = 3\n+more = 4\n"


def task(tid, title, state, after=(), **more):
    return {"id": tid, "title": title, "brief": f"Brief of {title}", "tier": "warrior", "after": list(after), "state": state,
            "branch": f"idea/sync/{tid}", "commit": "", "session": "s", "cost": 0.42, "tokens": 10, "started": "", "finished": "2026-10-17T10:00:00",
            "error": "", "note": "", "round": 1, "tests": None, "diff": None, "conflict": "", "why": "", **more}


def make_plan():
    return {"idea": "sync", "made_at": "2026-10-17T10:00:00", "passed_at": "2026-10-17T10:05:00",
            "estimate": {"tasks": 5, "usd_low": 1.2, "usd_high": 3.5},
            "todos": [{"id": "t1", "title": "API_KEY", "kind": "secret", "why": "The sync service needs it", "choices": [], "steps": [],
                       "for": ["k2", "k3"], "done": False, "value": None}],
            "tasks": [task("k1", "Read the sync code", "merged"), task("k2", "Add the queue", "review", ["k1"], tests=GREEN,
                      diff={"files": 14, "added": 320, "removed": 41}),
                      task("k3", "Retry on a lost signal", "running", ["k2"]),
                      task("k4", "Test it offline", "review", ["k3"], tests=RED, round=2, diff={"files": 3, "added": 12, "removed": 0},
                           conflict="conflicts with dev in a.py, b.py"),
                      task("k5", "Write the notes", "waiting", ["k4"])]}


_HEAD = {"craft": "engineering", "race": "peon", "tier": "warrior"}
LEAD = {"slug": "taskmaster", "name": "Taskmaster", "head": {"craft": "engineering", "race": "peon", "tier": "elder"}}
PARTY = {"ideas": 9, "leader": {"slug": "product-manager", "name": "Product manager", "head": {"craft": "product", "race": "lich", "tier": "elder"}, "usd": 4.1},
         "members": [{"slug": "grunt", "name": "Grunt", "head": _HEAD, "tasks": 14, "merged": 13, "first_time": 12, "usd": 9.2}],
         "checks": [{"by": "accessibility-reviewer", "name": "Accessibility reviewer", "head": {"craft": "design", "race": "elf", "tier": "warrior"}, "applied": 6,
                     "skipped": 1, "clean": 4, "caught": 2, "left": 1, "before": 2, "usd": 1.8},
                    {"by": "reviewer", "name": "Reviewer", "head": _HEAD, "applied": 1, "skipped": 0, "clean": 1, "caught": 0, "left": 0, "before": 0, "usd": None}]}
PARTY_LINES = ["Product manager (leads): ≈$4.10 for the party, the drafts and the plans", "Grunt: 14 tasks, 12 merged the first time · ≈$9.20",
               "Accessibility reviewer: checked 6 goals: 4 clean, caught 2 (1 left) · ≈$1.80 · skipped 1 · 2 ended without findings",
               "Reviewer: checked 1 goal: 1 clean, caught 0"]
def party_price(a, learned=True, hints=()):
    """What `ideas.party_price` answers for a party (spec 43 §3): $0.35 a check, about half of the ideas, all of them with `every`."""
    from orkboard.realm import library
    checks = [{"by": s, "name": library.get(s).name, "usd": 0.35, "share": 1.0 if s in (a.get("every") or []) else 0.5, "every": s in (a.get("every") or [])}
              for s in a.get("team") or [] if library.get(s) is not None and library.get(s).check is not None]
    return {"low": 1.9, "high": 5.7, "learned": learned, "ideas": 12 if learned else 0, "checks": checks, "hints": list(hints)}


SAVED = "/home/me/Downloads/orkboard-logs-2026-10-19-120000.zip"            # what logs.save answers

class StubHost:
    """What part A's commands answer, in the shapes of §5; every change bumps `ideas_rev` and pushes a snapshot."""

    def __init__(self, look="camp", onboarding=None):
        self.look, self.onboarding, self.rev, self.log, self.ws = look, onboarding, 1, [], None
        self.sign_in: list[dict] = []                 # the snapshot's `sign_in` (spec 45 §4): the tools not signed in, as core/sign_ins.py serves them
        self.sign_in_needs: list[dict] = []           # the sign-in rows of Needs you (realm/board_map.py `sign_in_needs`)
        self.plan = make_plan()
        self.into, self.push = "dev", False
        self.paired = [{"id": "p1", "name": "Pixel 8", "seen": "2026-10-17T09:30:00"}]
        self.target, self.autostart, self.night = "balance", True, "01:00-07:00"
        self.night_low = True                    # spec 83: Low work may run at night (None: not asked yet, False: no); a test of the question sets None
        self.awake = {"mode": "carts", "why": "", "holding": False, "battery": False, "can": True, "how": "systemd-inhibit", "machine": "Mac", "paired": True}   # awake.state (spec 47 §3)
        self.awake_offer = ""                         # phones.list's awake_offer: "Mac" while the offer is to be asked
        self.goals = {"general": self.goal("general", "General", "normal", "ready", order=0),
                      "ship-sync": self.goal("ship-sync", "Ship sync", "normal", "ready", summary="Sync is the first thing a second device needs.\nIt touches sync.py.")}
        self.roles = {"taskmaster": {"slug": "taskmaster", "name": "Taskmaster", "model": "elder", "max_parallel": 1, "instruction": "", "builtin": True},
                      "grunt": {"slug": "grunt", "name": "Grunt", "model": "", "max_parallel": 8, "instruction": "", "builtin": True}}
        self.kinds = {k: "grunt" for k in ("code", "tests", "docs", "text", "research")}
        self.chip_extra: dict[str, dict] = {}             # spec 41 §3: a chip's short / idea_short, by task id
        self.usd_task: dict[str, float | None] = {}       # spec 41 §8: a role's cost a task by slug (`usd_task`)
        self.record: dict[str, dict | None] = {}          # spec 42 §4: a role's record of the last 30 days by slug (`record`)
        self.check_week: dict[str, dict] = {}             # spec 43 §4.1: a checker's check of the last 7 days by slug (`check_week`)
        self.party_rows: list[dict] = []                  # spec 43 §4.2: Needs you's `party` rows
        self.told = {"taskmaster": "The Taskmaster reads each step's prompt.", "grunt": "A Grunt gets the task's brief and the repository."}
        self.limits = [{"provider": "claude", "name": "Claude", "left": 0.62,
                        "rows": [{"window": "5h", "left": 0.62, "reset": f"{_TODAY}T18:00"}, {"window": "week", "left": 0.8, "reset": f"{_IN_TWO_DAYS}T09:00"}]},
                       {"provider": "agy", "name": "Antigravity", "left": 0.15, "rows": [{"window": "daily", "left": 0.15, "reset": ""}]},
                       {"provider": "codex", "name": "Codex", "left": None, "error": "Not logged in", "rows": []}]   # turned on, not read
        self.ideas = {"sync": self.idea("sync", "Sync ideas between the phone and the town", "working", 0),
                      "dark": self.idea("dark", "Dark mode", "plan", 1, start_at="night"),
                      "offline": self.idea("offline", "Offline mode", "raw", 2, queue="night"),
                      "export": self.idea("export", "Export notes", "plan", 3, in_needs_you=True),
                      "search": self.idea("search", "Search the notes", "asks", 4, in_needs_you=True),
                      "tags": self.idea("tags", "Tag the notes", "proposed", 5, in_needs_you=True, track="grow")}
        self.goals["grow"] = self.goal("grow", "Grow installs", "high", "ready", order=2, summary="More people try Orkline.", questions=["Which channel first?"])
        self.proposals, self.asked, self.todo_log = [], [], []
        self.lens = {"lenses": [{"id": "text"}], "default": "text", "segments": [], "screens": []}    # ideas.lens
        self.unplanned = False                        # sync's spec says no plan yet (its tasks stay on the Board)
        self.checks = [{"by": "reviewer", "name": "Reviewer", "applies": True, "why": "", "state": "passed", "task": "k1", "tier": "elder"},   # sync's
                       {"by": "accessibility-reviewer", "name": "Accessibility reviewer", "applies": False, "why": "It changes no screen", "state": "",
                        "task": "", "tier": "warrior"}]
        self.parts: list[dict] = []                                                                  # ideas.lens_code
        self.screen_png = ""                                                                         # ideas.lens_screen
        self.party = copy.deepcopy(PARTY)                                                            # ideas.party (spec 43 B)
        self.hints: list[str] = []                                                                   # ideas.party_price's hints (spec 43 E)
        self.own: list[dict] = []                                                                    # ideas.parties (spec 43 F)
        self.goal_notes: list[str] = []                                                              # what ideas.goal_save says besides its slug
        self.learned = True                                                                          # ideas.party_price: learned from the project's ideas, or a first guess
        self.reserve = {"share": 0.1, "night": False}                                                # the snapshot's reserve (spec 49 §2.3)
        self.rate = None                                                                             # what 1 % of the five-hour window costs (decisions §82)
        self.week: dict[str, dict | None] = {}                                                       # ideas.agents: a role's week by slug (spec 49 §5.2)
        self.harness: dict[str, dict] = {}                                                           # ideas.agents: the tool a role runs on, by slug
        self.gate_doc = {"into": "dev", "main": "main", "same": False, "commits": 3, "files": 7,       # ideas.gate (spec 49 §2.1)
                         "ideas": [{"slug": "export", "title": "Export notes", "goal": "ship-sync", "tasks": 3}]}
        self.today_events: list[dict] = [                                                            # ideas.today (spec 49 §2.2)
            {"at": "12:40", "mark": "✓", "tone": "ok", "words": "merged into dev", "title": "Read the sync code", "goal": "ship-sync", "idea": "sync", "task": "k1",
             "open": {"kind": "result", "slug": "sync", "task": "k1"}},
            {"at": "12:10", "mark": "↺", "tone": "muted", "words": "sent back", "title": "Add the queue", "goal": "ship-sync", "idea": "sync", "task": "k2",
             "open": {"kind": "result", "slug": "sync", "task": "k2"}},
            {"at": "11:55", "mark": "✗", "tone": "danger", "words": "failed", "title": "Secure cookie flags", "goal": "grow", "idea": "tags", "task": "k1",
             "open": {"kind": "task", "slug": "tags", "task": "k1"}},
            {"at": "10:30", "mark": "▸", "tone": "ink", "words": "the work started", "title": "Sync ideas between the phone and the town", "goal": "ship-sync", "idea": "sync",
             "task": "", "open": {"kind": "idea", "slug": "sync"}},
            {"at": "09:00", "mark": "✓", "tone": "ok", "words": "dev merged into main", "title": "dev → main", "goal": "", "idea": "", "task": "", "open": {"kind": "gate", "slug": ""}}]

    def idea(self, slug, title, state, order, **more):
        return {"slug": slug, "title": title, "track": "ship-sync", "order": order, "state": state, "size": "M", "asks": 0, "updated": "x", "talk": [],
                "priority": "normal", "queue": "", "held_until": "", "risk": "low", "risk_triggers": [], "depends_on": [], "waits_on": [],
                "start_at": "", "in_needs_you": False, **more}

    def needs_you(self):
        todo = {"id": "t1", "title": "API_KEY", "kind": "secret", "why": "The sync service needs it", "choices": [], "steps": ["Open the console", "Copy the key"],
                "accept": [], "done": False}
        base = {"goal": "ship-sync", "priority": "normal", "blocks": False, "at": "2026-10-18T09:00:00"}
        out = [base | {"kind": "todo", "idea": "sync", "title": "Sync ideas between the phone and the town", "text": "API_KEY", "blocks": True, "todo": todo},
               base | {"kind": "plan", "idea": "export", "title": "Export notes", "text": "Plan ready · 3 tasks"},
               base | {"kind": "asks", "idea": "search", "title": "Search the notes", "text": "Which fields count?"},
               base | {"kind": "goal", "idea": "", "goal": "grow", "title": "Grow installs", "text": "Which channel first?", "priority": "high",
                       "questions": self.goals.get("grow", {}).get("questions", []),
                       **({"asked": self.goals["grow"]["asked"]} if self.goals.get("grow", {}).get("asked") else {})},
               base | {"kind": "proposal", "idea": "tags", "goal": "grow", "title": "Tag the notes", "text": "Tags make a long list findable."}]
        gone = set(self.proposals) | set(self.asked)            # answered: out of the list
        return [n for n in out if (n["idea"] or n["goal"]) not in gone] + self.party_rows + list(self.sign_in_needs)

    def goal(self, slug, title, priority, state, order=1, **more):
        return {"slug": slug, "title": title, "about": "", "criteria": [], "deadline": "", "order": order, "count": 0, "priority": priority,
                "metrics": [], "links": [], "summary": "", "questions": [], "state": state, "state_error": "", **more}

    @staticmethod
    def leader(slug):
        """A goal's leader as the host serves it (gui/ideas_goals.py `_goal_row`): None when not said."""
        from orkboard.realm import library, roles
        a = library.get(slug or "")
        if a is None:
            return None
        return {"slug": a.id, "name": a.name, "head": {"craft": a.craft, "race": roles.RACES[a.craft], "tier": a.tier}}

    def kind_list(self):
        names = {"code": "Code", "tests": "Tests", "docs": "Docs", "text": "Text for people", "research": "Research"}
        return [{"kind": k, "label": names[k], "role": r} for k, r in self.kinds.items()]

    def results(self):
        return [{"idea": "sync", "idea_title": "Sync ideas between the phone and the town", "task": t["id"], "title": t["title"], "round": t["round"],
                 "tests": t["tests"], "diff": t["diff"], "cost": t["cost"], "conflict": t["conflict"], "finished": t["finished"],
                 **({"check": t["check"], "findings": t["findings"], "same": t.get("same", False)} if "check" in t else {}),       # spec 43 A: a check's result
                 "look": t.get("look", "")}                                                                                  # spec 84: why it waits
                for t in self.plan["tasks"] if t["state"] == "review"]

    def snapshot(self):
        return {"t": "state", "state": {
            "focus": "board", "ideas_rev": self.rev, "look": self.look, "project": "orkline", "demo": False, "onboarding": self.onboarding or False,
            "words": [], "resources": {}, "orkspaces": [], "buildings": [], "roads": [], "alerts": [], "score": {},
            "limits": self.limits, **({"mana": self.mana} if getattr(self, "mana", None) is not None else {}), "reserve": self.reserve, "rate": self.rate, "review_count": len(self.results()), "needs_you": 1, "sign_in": json.loads(json.dumps(self.sign_in)),
            "hud": {"gold": "$2.40", "show_gold": True, "lumber": "120k"}}}

    def page(self, slug):
        if slug not in self.ideas:
            return {"error": "That goal is gone"}
        i = self.ideas[slug]
        secs = [{"name": n, "thesis": f"{n} in one line", "text": f"{n}: the longer text of this section."} for n in SECTIONS]
        if slug == "sync":
            next(x for x in secs if x["name"] == "Stages")["text"] = STAGES
        if slug == "search":
            next(x for x in secs if x["name"] == "Open questions")["text"] = "- Which fields count?\n- Do tags count?"
        return {"slug": slug, "title": i["title"], "track": "general", "state": i["state"], "size": "M", "sections": secs, "talk": i["talk"],
                "plan": self.plan if slug == "sync" and not self.unplanned else None, "busy": False, "state_error": i.get("state_error", ""), "lens": i.get("lens", []),
                "checks": self.checks if slug == "sync" else []}

    def find(self, a):
        return next(t for t in self.plan["tasks"] if t["id"] == a["task"])

    def map_doc(self):
        """`ideas.map` as spec 48 §1 and spec 49 §2.4 have it, for the shell's stub: the ideas of its goals; sync's tasks in waves and its
        results at Review; a party of a leader, a builder and a checker."""
        wave, tasks = {}, []
        for t in [] if self.unplanned else self.plan["tasks"]:
            wave[t["id"]] = 1 + max([wave[a] for a in t["after"] if a in wave], default=0)
            check = bool(t.get("check"))
            tasks.append({"id": t["id"], "title": t["title"], "short": t["title"], "state": t["state"], "after": t["after"], "tier": t["tier"], "head": _HEAD,
                          "by": {"slug": "reviewer" if check else "grunt", "name": "Reviewer" if check else "Grunts"}, "band": "check" if check else "build",
                          "wave": wave[t["id"]], "tag": "Code", "error": t["error"], "note": t["note"], "round": t["round"], "cost": t["cost"],
                          "started": t["started"] or (dt.datetime.now() - dt.timedelta(minutes=4)).isoformat(timespec="seconds") if t["state"] == "running" else t["started"]})
        nodes = []
        for i in self.ideas.values():
            if i["track"] == "general":
                continue
            sync = i["slug"] == "sync"
            need = {"asks": "asks", "plan": "plan", "proposed": "proposal"}.get(i["state"], "") if i["in_needs_you"] else ""
            asked = [{"ask": "Which fields count?", "choices": [], "pick": None, "why": "", "by": LEAD}] if i["state"] == "asks" else []
            nodes.append({"slug": i["slug"], "goal": i["track"], "title": i["title"], "short": i["title"], "state": i["state"], "queue": i["queue"], "held_until": "",
                          "element": "meadow", "flag": None,
                          "start_at": i["start_at"], "priority": "normal", "size": "M", "risk": "low", "tier": 1, "depends_on": [], "waits_on": [], "waits": None,
                          "needs_you": need, "progress": {"done": 1, "total": len(tasks)} if sync else {"done": 0, "total": 0}, "tasks": tasks if sync else [],
                          "estimate": None, "by_itself": False, "folded": False, "updated": "2026-10-17T10:00:00", "checks": [],
                          "stage": "implementation" if sync and not self.unplanned else "planning", "round": 1, "usd": 0.84 if sync else None,
                          "plan_estimate": {"usd_low": 1.0, "usd_high": 2.0} if i["state"] == "plan" else None, "asked": asked,
                          "results": self.results() if sync else []})
        goals = []
        for g in self.goals.values():
            if g["slug"] == "general":
                continue
            lead = g.get("leader") or LEAD
            reading = any(i["track"] == g["slug"] and i["state"] in ("reading", "planning") for i in self.ideas.values())       # spec 48 §1: the leader at work
            party = [{**lead, "band": "lead", "state": "work" if reading else "free", "why": ""}]
            if g["slug"] == "ship-sync":
                party += [{"slug": "grunt", "name": "Grunts", "head": _HEAD, "band": "build", "state": "work", "why": ""},
                          {"slug": "reviewer", "name": "Reviewer", "head": {"craft": "engineering", "race": "peon", "tier": "elder"}, "band": "check", "state": "next", "why": ""}]
            goals.append({"slug": g["slug"], "title": g["title"], "short": g["title"], "priority": g["priority"], "state": g["state"], "done_when": [], "ideas": 5, "done": 0,
                          "usd": None, "leader": lead, "team": [], "party": party, "today": {"merged": 0, "usd": 0.0}, "flags": 0, "waits_main": 0, "brief": ""})
        return {"goals": goals, "nodes": nodes, "edges": [], "rev": self.rev}

    def handle(self, name, a):
        self.log.append((name, a))
        if name == "ideas.map":
            return self.map_doc()
        if name == "ideas.gate":
            return copy.deepcopy(self.gate_doc)
        if name == "ideas.gate_merge":
            self.gate_doc.update(commits=0, files=0, ideas=[])
            return self.bump({"ok": True, "commit": "abc", "note": ""})
        if name == "ideas.today":
            return {"events": copy.deepcopy(self.today_events)}
        if name == "ideas.board":
            ideas = [i | {"thesis": "Gist in one line", "progress": {"done": 1, "total": 5} if i["slug"] == "sync" else {"done": 0, "total": 0}}
                     for i in self.ideas.values()]
            return {"tracks": [g | {"count": sum(1 for i in ideas if i["track"] == g["slug"])} for g in self.goals.values()],
                    "ideas": ideas, "needs_you": self.needs_you(), "target": self.target, "autostart": self.autostart, "night": self.night, "night_low": getattr(self, "night_low", None), "review": getattr(self, "review", False),
                    "review_notice": getattr(self, "review_notice", False),
                    "rev": self.rev}
        if name == "ideas.page":
            return self.page(a["slug"])
        if name == "ideas.lens":                      # the goal's party's lenses (gui/ideas_lens.py)
            return dict(self.lens, track=a["track"])
        if name == "ideas.check_skip":                # a check skipped, or taken again (gui/ideas_review.py)
            for c in self.checks:
                if c["by"] == a["by"]:
                    c.update(skipped=a.get("skip", True) is not False, state="", task="")
            return self.bump({"ok": True})
        if name == "ideas.lens_code":
            return {"parts": self.parts}
        if name == "ideas.lens_screen":
            return {"id": a["id"], "name": "Orders", "type": "image/png", "data": self.screen_png}
        if name == "ideas.review_list":
            return {"into": self.into, "push": self.push, "branches": ["dev", "main"], "results": self.results()}
        if name == "ideas.agents":
            chips = [dict(idea="sync", idea_title="Sync ideas between the phone and the town", task=t["id"], title=t["title"],
                          state=t["state"], tier=t["tier"], note="", by="auto" if t["id"] == "k3" else "person", night=False)
                     for t in self.plan["tasks"] if t["state"] in ("running", "review")]
            chips += [dict(idea="sync", idea_title="Sync ideas between the phone and the town", task="k5", title="Write the notes", state="held",
                           tier="warrior", note="reserve · after 18:00", by="person", night=False),
                      dict(idea="dark", idea_title="Dark mode", task="d1", title="Dark palette", state="ready", tier="warrior", note="", by="auto", night=True),
                      dict(idea="export", idea_title="Export notes", task="e1", title="Write the export", state="held", tier="warrior", note="files · sync",
                           waits_title="Sync ideas between the phone and the town", by="auto", night=False)]
            chips = [c | self.chip_extra.get(c["task"], {}) for c in chips]
            blocks = [{"role": "taskmaster", "name": "Taskmaster", "model": "elder", "max_parallel": 1, "builtin": True, "spend_today": 0, "usd_task": None,
                       "head": {"craft": "engineering", "race": "peon", "tier": "elder"}, "harness": {"id": "claude", "name": "Claude"}, "week": self.week.get("taskmaster"),
                       "state": "waiting", "waits_on": {"idea": "dark", "text": "waiting for your answers on “Dark mode”"}, "chips": []},
                      {"role": "grunt", "name": "Grunts", "model": "", "max_parallel": 8, "builtin": True, "spend_today": 1.25, "chips": chips,
                       "kinds": [k for k, r in self.kinds.items() if r == "grunt"], "usd_task": self.usd_task.get("grunt"),
                       "head": {"craft": "engineering", "race": "peon", "tier": "warrior"}, "harness": self.harness.get("grunt", {"id": "claude", "name": "Claude"}),
                       "week": self.week.get("grunt")}]
            blocks += [{"role": r["slug"], "name": r["name"], "model": r["model"], "max_parallel": r["max_parallel"], "builtin": False, "spend_today": 0,
                        "chips": [], "kinds": [k for k, x in self.kinds.items() if x == r["slug"]], "usd_task": self.usd_task.get(r["slug"]),
                        "head": r.get("head"), "harness": self.harness.get(r["slug"], {"id": "claude", "name": "Claude"}), "week": self.week.get(r["slug"]),
                        **({"check_week": self.check_week[r["slug"]]} if r["slug"] in self.check_week else {})}
                       for r in self.roles.values() if not r["builtin"]]
            return {"roles": blocks, "done_today": [{"idea": "sync", "task": "k1", "title": "Read the sync code", "role": "grunt"}]}
        if name == "ideas.roles":
            return {"roles": [r | {"spend_today": 0, "record": self.record.get(r["slug"])} | ({"check_week": self.check_week[r["slug"]]} if r["slug"] in self.check_week else {}) | ({"told": self.told[r["slug"]]} if r["slug"] in self.told else {}) for r in self.roles.values()],
                    "kinds": self.kind_list(),
                    "models": [{"id": "", "label": "The task's own tier"}, {"id": "elder", "label": "Elder tier (opus)"},
                               {"id": "warrior", "label": "Warrior tier (sonnet)"}, {"id": "laborer", "label": "Laborer tier (haiku)"}],
                    "library": [x | {"installed": x["id"] in self.roles} for x in library.listed()], "suggested": library.SUGGESTED, "seats": library.SEATS,
                    "parties": library.parties(), "presets": library.presets(), "stages": library.stages(), "tier_costs": dict(plans.DEFAULT_COST)}
        if name == "ideas.role_add":                  # an agent of the library made a role of this project (gui/ideas_roles.py)
            lib = library.get(a["id"])
            if lib is None or lib.id in self.roles:
                return {"error": "No such agent, or it is already this project's"}
            self.roles[lib.id] = {"slug": lib.id, "name": lib.name, "model": lib.tier, "max_parallel": 2, "instruction": lib.instruction, "builtin": False,
                                  "craft": lib.craft, "head": {"craft": lib.craft, "race": roles.RACES[lib.craft], "tier": lib.tier}}
            return self.bump({"slug": lib.id})
        if name == "ideas.role_save":
            slug = a.get("slug") or a["name"].lower().replace(" ", "-")
            self.roles[slug] = {"slug": slug, "name": a["name"], "model": a["model"], "max_parallel": a["max_parallel"],
                                "instruction": a.get("instruction", ""), "builtin": slug in ("taskmaster", "grunt")}
            for k in a.get("kinds", []):                                                              # spec 36 §3: the types this agent takes
                self.kinds[k] = slug
            return self.bump({"slug": slug})
        if name == "ideas.role_drop":
            self.roles.pop(a["slug"])
            self.kinds = {k: ("grunt" if r == a["slug"] else r) for k, r in self.kinds.items()}
            return self.bump({"ok": True})
        if name == "ideas.kind_set":
            self.kinds[a["kind"]] = a["role"]
            return self.bump({"ok": True})
        if name == "ideas.goal_save":
            slug = a.get("slug") or "-".join(a["about"].lower().replace(".", "").split()[:2])
            old = self.goals.get(slug, {})
            title = a.get("title") or old.get("title") or a["about"][:30]
            self.goals[slug] = self.goal(slug, title, a["priority"], "reading", about=a["about"], summary=old.get("summary", ""),
                                         title_by="person" if a.get("title") else old.get("title_by", "keeper"),
                                         leader=self.leader(a.get("leader")) or old.get("leader"), party=a.get("party", ""),
                                         team=a.get("team", old.get("team", [])), every=a.get("every", old.get("every", [])), craft=a.get("craft", old.get("craft", "engineering")))
            return self.bump({"slug": slug, **({"notes": self.goal_notes} if self.goal_notes else {})})
        if name == "ideas.parties":                    # spec 43 F: the person's own parties
            return {"parties": copy.deepcopy(self.own)}
        if name == "ideas.party_save":
            taken = next((p for p in self.own if p["name"].lower() == a["name"].lower()), None)
            if taken and not a.get("replace"):
                return {"error": f"You have a party named “{taken['name']}”"}
            if taken:
                taken.update(name=a["name"])
                return {"id": taken["id"]}
            self.own.append({"id": f"p-{len(self.own):08x}", "name": a["name"], "craft": "engineering", "leader": "architect", "team": [], "every": [], "own": [],
                             "goals": 0, "projects": 0, "met": 0, "saved": ""})
            return {"id": self.own[-1]["id"]}
        if name == "ideas.party_drop":
            self.own = [p for p in self.own if p["id"] != a["id"]]
            return {"ok": True}
        if name == "ideas.party_answer":               # spec 43 D: a party's proposal answered
            self.party_rows = [n for n in self.party_rows if n["goal"] != a["goal"]]
            return self.bump({"ok": True})
        if name == "ideas.party_price":                # spec 43 C: about what an idea costs with this party
            return party_price(a, self.learned, self.hints)
        if name == "ideas.party":                      # spec 43 B: what the goal's party did
            return copy.deepcopy(self.party)
        if name == "ideas.goal_accept":
            self.goals[a["slug"]]["busy"] = True
            return self.bump({"ok": True})
        if name == "ideas.goal":
            g = self.goals[a["slug"]]
            return g | {"description": g["about"], "talk": [], "busy": g.get("busy") or g["state"] == "reading", "sections": []}
        if name == "ideas.queue":
            self.ideas[a["slug"]].update(queue=a["queue"], state="reading" if a["queue"] == "now" else "raw")
            return self.bump({"ok": True})
        if name == "ideas.read_stop":
            self.ideas[a["slug"]].update(queue="hold", state="raw")
            return self.bump({"ok": True})
        if name == "ideas.start_now":
            self.ideas[a["slug"]].update(start_at="", state="working")
            return self.bump({"ok": True})
        if name == "ideas.drop":
            self.ideas.pop(a["slug"], None)
            return self.bump({"ok": True})
        if name == "ideas.proposal":
            self.proposals.append(a["slug"])
            return self.bump({"ok": True})
        if name == "ideas.answer":
            self.asked.append(a["slug"])
            return self.bump({"ok": True})
        if name == "ideas.board_set":
            self.target, self.autostart, self.night = a.get("target", self.target), a.get("autostart", self.autostart), a.get("night", self.night)
            self.review = a.get("review", getattr(self, "review", False))
            if a.get("review_notice") is False:
                self.review_notice = False
            return self.bump({"target": self.target, "autostart": self.autostart, "night": self.night})
        if name == "ideas.night_allow":               # spec 83: the one standing permission
            self.night_low = a["allow"]
            return self.bump({"ok": True, "moved": 0})
        if name == "ideas.todo":
            return self.bump({"ok": True})
        if name == "ideas.doc":
            return {"path": a["path"], "text": f"The text of {a['path']}", "truncated": False}
        if name == "phones.pair":
            return {"phones": list(self.paired), "listening": True, "address": "https://192.168.1.20:8443", "tail_address": "https://studio.tail1234.ts.net:8443",
                    "tail_trusted": True, "tailscale": True, "fingerprint": "AB:CD", "open": [], "pairing": 120, "awake_offer": "",
                    "link": "orkcraft://x", "qr": QR, "code": "123456", "app_link": "https://studio.tail1234.ts.net:8443/app", "app_qr": QR}
        if name == "phones.tailnet":
            return {"running": True, "installed": True, "phones": [{"name": "Pixel 8", "os": "Android", "online": True}], "install_qr": QR,
                    "dns_qr": QR, "install": "https://tailscale.com/download", "dns": "https://login.tailscale.com/admin/dns", "account": "me@example.com"}
        if name in ("tools.sign_in", "tools.sign_in_cancel", "tools.sign_in_done"):       # spec 45 §5: the desktop's commands
            e = next((x for x in self.sign_in if x["harness"] == a["harness"]), None)
            if e is None:
                return {"error": "That tool needs no sign-in"}
            if name == "tools.sign_in":
                e.update(state="open", why="", command="", **({"auto": False} if a.get("auto") is not True else {}))
            elif name == "tools.sign_in_cancel":
                e.update(state="failed", why="cancelled")
            else:
                self.sign_in = [x for x in self.sign_in if x is not e]
            return self.bump(dict(e))
        if name == "phones.list":
            return {"phones": self.paired, "listening": True, "address": "https://192.168.1.20:8443", "tail_address": "https://studio.tail1234.ts.net:8443",
                    "tail_trusted": True, "tailscale": True, "fingerprint": "AB:CD", "open": [], "pairing": 100, "awake_offer": self.awake_offer}
        if name == "awake.state":
            return dict(self.awake)
        if name == "awake.set":
            self.awake["mode"] = a["mode"]
            return dict(self.awake)
        if name == "awake.offer":
            self.awake_offer = ""
            if a.get("yes"):
                self.awake["mode"] = "phone"
            return dict(self.awake)
        if name == "phones.forget":
            self.paired = [d for d in self.paired if d["id"] != a["id"]]
            return {"phones": self.paired, "listening": True, "address": "", "tail_address": "", "open": [], "pairing": 0}
        if name == "phones.pair_stop":
            return {"phones": self.paired, "pairing": 0}
        if name == "ideas.task":
            return self.find(a) | {"idea": a["slug"], "idea_title": "Sync ideas between the phone and the town", "log": "== round 1\nreading sync.py\n"}
        if name == "ideas.diff":
            return {"base": self.into, "branch": f"idea/sync/{a['task']}", "commits": [{"sha": "9f2c41d7e0", "subject": "k2: add the queue"}],
                    "files": [{"path": "sync.py", "added": 2, "removed": 1, "patch": PATCH}, {"path": "huge.json", "added": 9000, "removed": 0, "patch": None}],
                    "truncated": True}
        if name == "ideas.merge":
            self.find(a)["state"] = "merged"
            return self.bump({"ok": True, "commit": "abc"})
        if name == "ideas.back":
            self.find(a).update(state="running", round=self.find(a)["round"] + 1, why=a["why"])
            return self.bump({"ok": True})
        if name == "ideas.drop_task":
            self.find(a).update(state="dropped", error="dropped by you")
            return self.bump({"ok": True})
        if name == "ideas.stop_task":
            self.find(a).update(state="ready", note="stopped by you")
            return self.bump({"ok": True})
        if name == "ideas.into":
            self.into, self.push = a.get("branch", self.into), a.get("push", self.push)
            return self.bump({"ok": True})
        if name == "ideas.add":
            if not a.get("track") or a["track"] == "general":
                return {"error": "A goal needs a party"}
            slug = a["text"].lower().replace(" ", "-")
            now = a["priority"] != "low" and not a.get("night") and not a.get("hold")
            queue = "hold" if a.get("hold") else "now" if now else "night"
            self.ideas[slug] = self.idea(slug, a["text"], "reading" if now else "raw", 9, track=a["track"], priority=a["priority"], queue=queue)
            return self.bump({"slug": slug, "queue": queue, "element": "meadow"})
        if name == "onboarding.skip":
            self.onboarding = {"step": "raising", "steps": ["tools"], "n": 0, "raising": {"title": "x", "phase": "done", "steps": [], "buildings": [], "error": ""}}
            return self.bump({})
        if name == "onboarding.close":
            self.onboarding = None
            return self.bump({})
        if name == "ideas.usage":                     # spec 91 §2: what used the pressed tool's limit (js/arena/limits.js)
            return {"provider": a["provider"], "name": a["provider"].title(), "left": 0.62, "window": "5h", "reset": f"{_TODAY}T18:00", "scope": a.get("scope", "project"), "scopes": ["project"],
                    "rows": [{"party": "sync", "title": "Sync ideas", "share": 14, "tokens": 70_000, "members": [{"agent": "grunt", "name": "Grunt", "share": 14, "tokens": 70_000}]}],
                    "outside": 3, "estimated": True, "tokens_only": False}
        if name == "logs.save":
            return {"path": SAVED, "name": SAVED.rsplit("/", 1)[1], "folder": SAVED.rsplit("/", 1)[0]}
        return {"ok": True}

    def bump(self, result):
        self.rev += 1
        if self.ws:
            self.ws.send(json.dumps(self.snapshot()))
        return result

    def on_socket(self, ws):
        self.ws = ws
        ws.send(json.dumps(self.snapshot()))

        def on_message(raw):
            m = json.loads(raw)
            ws.send(json.dumps({"t": "reply", "id": m["id"], "ok": True, "result": self.handle(m["name"], m["args"])}))
        ws.on_message(on_message)


def _sent(pg, host, entry, ms=WAIT_MS) -> bool:
    """The stub got `entry`. A command goes over the page's socket to the stub, whose handler runs only while Playwright
    is called (the sync API): the page is given a moment, up to `ms`, until it has (on a busy machine one call was not
    enough)."""
    for _ in range(ms // 50):
        if entry in host.log:
            return True
        pg.wait_for_timeout(50)
    return entry in host.log


def _calls(pg, host, name, at_least=1, ms=WAIT_MS) -> list[dict]:
    """The arguments of every `name` the stub got, once it got at least `at_least` of them (as `_sent`)."""
    for _ in range(ms // 50):
        got = [a for n, a in host.log if n == name]
        if len(got) >= at_least:
            return got
        pg.wait_for_timeout(50)
    return [a for n, a in host.log if n == name]


def _open(gui, viewport=None, host=None, ready=".arena-hc[data-kind=result]", query=""):
    """The window against a stub host. The goals are tabs and the first by priority is shown: the stub's Ship sync (most of its ideas)
    is picked, and its results are the hand's cards (`ready`, spec 90 §2.3)."""
    server, browser = gui
    host = host or StubHost()
    pg = browser.new_page(viewport=viewport or {"width": 1440, "height": 900})
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    pg.route_web_socket("**/ws*", host.on_socket)
    pg.goto(server.url + query)
    if ready == ".arena-hc[data-kind=result]":
        pg.wait_for_selector(".arena-phead", timeout=WAIT_MS)
        _show_goal(pg)
        pg.wait_for_selector(ready, timeout=WAIT_MS)
    elif ready:
        pg.wait_for_selector(ready, timeout=WAIT_MS)
    return pg, host, errors


def _parties(pg):
    """The left column's list of the parties (docs/specs/69-parties-in-the-column.md): waited for; a heading for each party."""
    col = pg.get_by_role("complementary", name="Parties")
    col.wait_for(timeout=WAIT_MS)
    return col


def _party_card(pg, slug):
    """A party's heading in the column."""
    return _parties(pg).locator(f'.arena-phead[data-goal="{slug}"]')


def _show_goal(pg, slug="ship-sync"):
    """The window shows one party: this one, its heading pressed in the column (and kept, as the person's last)."""
    _parties(pg).locator(".arena-phead").first.wait_for(timeout=WAIT_MS)
    if not pg.locator(f'.arena[data-goal="{slug}"]').count() or slug == "@operations":
        _party_card(pg, slug).click()
    if slug == "@operations":
        pg.locator(".arena-ops").wait_for(timeout=WAIT_MS)
    else:
        pg.locator(f'.arena[data-goal="{slug}"]').wait_for(timeout=WAIT_MS)
        pg.wait_for_function("() => !document.querySelector('.is-leaving') && !document.querySelector('.is-drawn')", timeout=WAIT_MS)


def _stop(pg, kind, nth=0):
    """A stop in the fan along the bottom, raised (its quick answers are then in reach): the focus brings it up, as a hover does."""
    item = pg.locator(f".arena-hc[data-kind={kind}]").nth(nth)
    item.wait_for(timeout=WAIT_MS)
    item.locator(".arena-hc__open").focus()
    pg.wait_for_function("(el) => getComputedStyle(el).transform === 'matrix(1, 0, 0, 1, 0, -184)'", arg=item.element_handle(), timeout=WAIT_MS)   # it stands whole before a press
    return item


def _look_card(pg, title):
    """A result to look at: its card in the hand (docs/specs/90-what-the-first-look-said.md §2.3), raised (its answers then in reach)."""
    item = pg.locator(f'.arena-hc[data-kind=result]:has(.arena-hc__open[aria-label="To look at: {title}"])')
    item.wait_for(timeout=WAIT_MS)
    item.locator(".arena-hc__open").focus()
    pg.wait_for_function("(el) => getComputedStyle(el).transform === 'matrix(1, 0, 0, 1, 0, -184)'", arg=item.element_handle(), timeout=WAIT_MS)
    return item


def _look_open(pg, title):
    """A result to look at opened from its card: its code, tests and answers in the right column."""
    _look_card(pg, title).locator(".arena-hc__open").press("Enter")
    pg.wait_for_function("(t) => document.querySelector('.shell-drawer .shell-ptab.is-on')?.textContent.includes(t)", arg=title, timeout=WAIT_MS)
    got = pg.locator(".shell-drawer .shell-result")
    got.wait_for(timeout=WAIT_MS)
    return got


def _drawer(pg):
    """The right column (the drawer that was), once it is out."""
    pg.locator(".shell-drawer").wait_for(timeout=WAIT_MS)
    return pg.locator(".shell-drawer")


def _new_ideas(pg):
    """The goals list's *New · n* row, its fold open: its rows (a goal is a row of the list: `.arena-goal`)."""
    fold = pg.locator(".arena-raw .arena-frow__main")
    if fold.get_attribute("aria-expanded") != "true":
        fold.click()
    return pg.locator(".arena-goal")


def _goal_row(pg, title):
    """A goal of the party shown, by its title: its row in the goals list."""
    return pg.locator(".arena-goal", has_text=title)


def _said(row):
    """What a goal's row says besides its title (spec 73 §1.2): its old second line, in the title of its button, after the goal's whole title."""
    return row.locator(".arena-goal__main").get_attribute("title")


def _open_goal(pg, title):
    """A goal's row opens its screen in the drawer (its spec, its plan when the plan waits): a press picks it, a second press on the picked row opens it (spec 73 §1.2);
    a goal not yet read opens on a press."""
    _press_row(_goal_row(pg, title).locator(".arena-goal__main"))


def _press_row(main):
    """The presses that open a goal's screen, as › did (spec 73 §1.2): the first picks the row, the second opens it; a raw goal has no pick, its press opens. The pick that
    the first made is taken out again (Show all), so the board stands as it did when › opened a goal."""
    picked = main.get_attribute("aria-pressed")
    if picked == "false":
        main.click()
    main.click()
    if picked == "false":
        main.page.locator(".arena-showall").get_by_role("button", name="Show all").click()


def _open_slug(pg, slug):
    """A goal's screen, by its slug: a press picks its row, a second press opens it (spec 73 §1.2)."""
    _press_row(pg.locator(f'.arena-goal[data-slug="{slug}"] .arena-goal__main'))


def _new_goal(pg):
    """New goal: the + in the project line (spec 73 §4); a host with no goal types opens the dialog at once."""
    pg.locator(".arena-left__proj").get_by_role("button", name="New goal").click()
    dlg = pg.get_by_role("dialog", name="New goal")
    dlg.wait_for(timeout=WAIT_MS)
    return dlg


@pytest.fixture
def shell(gui):
    pg, host, errors = _open(gui)
    yield pg, host
    pg.close()
    assert not errors, "\n".join(errors)


def box(pg, selector):
    return pg.locator(selector).first.bounding_box()



# -- spec 34 round 2: dialogs, agents by task type, the phone from the shell -----------------------------------------

def adds(host):
    return [a for n, a in host.log if n == "ideas.add"]


def _awake_field(pg):
    pg.get_by_role("button", name="Settings").click()
    group = pg.get_by_role("group", name="Keep the computer awake")
    group.wait_for(timeout=WAIT_MS)
    return group


def _after_pairing(pg, host, answer):
    host.awake_offer = "Mac"
    pg.get_by_role("button", name="Settings").click()
    pg.get_by_role("button", name="Pair a phone").click()
    dlg = pg.get_by_role("dialog", name="Pair a phone")
    dlg.locator("img.gui-phones__qr").wait_for(timeout=WAIT_MS)
    host.paired = host.paired + [{"id": "p2", "name": "iPhone 15", "seen": "2026-10-20T09:30:00"}]       # a phone scans the code
    offer = dlg.get_by_role("group", name="Keep the computer awake")
    offer.wait_for(timeout=5000)
    assert "Paired: iPhone 15." in dlg.inner_text()
    assert "Keep this Mac awake so your phone can reach it all day? Only on power." in offer.inner_text()
    offer.get_by_role("button", name=answer).click()
    offer.wait_for(state="detached", timeout=WAIT_MS)
    return dlg
