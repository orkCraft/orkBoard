"""What a `?mock=1` browser test lays in the recording it serves (goal 171, stage G; decisions §301.1).

`orkboard/gui/static/mock/board.json` is a recording of a real host (tools/record_mock.py): this repository's Board, as quiet as it was.
A test presses things only an example holds (a goal for main, a goal in talk, new goals to sort, the leaders' words on a card, a kept
Jobs to be done); it lays them itself, in the copy of the recording it serves (`tools/serve_mock.py` `serve(port, lay)`), with the lays
below. Each text an example lays says so (" · example"). js/mock/ holds none of it: the page on mocks answers the host's own commands.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

EXAMPLE = " · example"
RECORDING = Path(__file__).resolve().parents[1] / "orkboard" / "gui" / "static" / "mock" / "board.json"
SHOWN = {"new", "talk", "spec", "idea", "ready", "running", "testing", "picking", "failed", "review"}


def reply(data: dict, name: str) -> dict | None:
    return next((r for r in data["replies"] if r["name"] == name), None)


def nodes(data: dict) -> list[dict]:
    return reply(data, "ideas.map")["result"]["nodes"]


def number(n: dict) -> int:
    head = n["slug"].split("-")[0]
    return int(head) if head.isdigit() else 0


def latest(data: dict, state: str, n: int = 1) -> list[dict]:
    return sorted((x for x in nodes(data) if x["state"] == state), key=number, reverse=True)[:n]


def ensure(data: dict, name: str, result: dict) -> dict:
    r = reply(data, name)
    if r:
        return r["result"]
    data["replies"].append({"name": name, "args": {}, "ok": True, "result": result})
    return result


def mark(n: dict) -> dict:
    if not n["title"].endswith(EXAMPLE):
        n["title"] += EXAMPLE
        n["short"] = (n.get("short") or n["title"]) + EXAMPLE
    return n


def at(h: int, m: int) -> str:
    return datetime.now().replace(hour=h, minute=m, second=0, microsecond=0).isoformat()


def lay_examples(data: dict) -> None:
    """This Board is quiet: nothing waits for main, nothing is to review. Lay a few goals in those states, a leader's ask,
    a change with its words before it and a change in Tech's architecture in the feed, and the same question in the hand."""
    # two goals in talk (the recording has three) are dealt to Tech and Product, so the deal has chairs dealt and chairs not
    for n in latest(data, "talk", 2):
        n["route"] = [{"step": "party", "party": p, "goal": n["slug"], "at": "", "state": "talk", "done": 0, "total": 0} for p in ("tech", "product")]
    m1, m2, seen, wait = (mark(n) for n in latest(data, "done", 4))
    for n in (m1, m2, seen, wait):
        n["place"] = "discard"
    gate = ensure(data, "ideas.gate", {"into": "dev", "main": "main", "same": False, "commits": 0, "files": 0, "ideas": []})
    gate.update(commits=6, files=11, ideas=[{"slug": n["slug"], "title": n["title"], "goal": n["goal"]} for n in (m1, m2)])
    board = reply(data, "ideas.board")["result"]
    board["review"] = True
    board["ideas"] = [*(board.get("ideas") or []), {"slug": wait["slug"], "waits_for_dev": True}]
    for rev in map(mark, latest(data, "ready", 1)):
        rev["state"] = "review"                                 # one goal at work comes to review: the gate can be opened from it
    feed = ensure(data, "ideas.feed", {"since": "", "heads": [], "waits": [], "posts": [], "seen": None})
    talk = latest(data, "talk", 1)
    if talk:
        t = talk[0]
        feed["waits"] = [{"kind": "starts", "goal": t["slug"], "short": (t.get("short") or t["title"]) + EXAMPLE, "leader": "orkmaster", "at": at(13, 40),
                          "acts": [{"act": "change_spec", "command": "ideas.spec_change", "args": {"idea": t["slug"]}},
                                   {"act": "start_now", "command": "ideas.start_now", "args": {"slug": t["slug"]}}]}]
    goal = talk[0]["slug"] if talk else m1["slug"]
    feed["posts"] = [
        {"leader": "tech", "post": {"leader": "tech", "at": at(11, 58), "kind": "concern", "goal": goal, "asks": True, "text": "Which way does the table open first, the lanes or the dealer?" + EXAMPLE, "acts": []}, "more": []},
        {"leader": "design", "post": {"leader": "design", "at": at(10, 5), "kind": "change", "goal": goal, "text": "The lanes keep a card's ratio; a post lies on its side, an open card stands up." + EXAMPLE,
                                      "before": "The lanes draw a post as tall as its words; an open post is a drawer.", "acts": []}, "more": []},
        {"leader": "tech", "post": {"leader": "tech", "at": at(11, 20), "kind": "change", "text": "gui/ is past its line: board_host.py and ideas.py are over 600 lines; split before they grow." + EXAMPLE,
                                    "why": "CLAUDE.md: split a module before it grows past ~600 lines.", "table": {"party": "tech", "framework": "architecture", "card": "gui/"}, "acts": []}, "more": []},
        {"leader": "design", "post": {"leader": "design", "at": at(9, 40), "kind": "news", "text": "The heads are drawn in the cartoon now; the runes go next." + EXAMPLE, "acts": []}, "more": []},
        *[{"leader": p, "post": {"leader": p, "at": at(9, 10), "kind": "concern", "goal": goal, "text": "Doubts Product's tree" + EXAMPLE, "event": "leader_objected", "acts": []}, "more": []} for p in ("tech", "design", "product")],
        *(feed.get("posts") or []),
    ]
    # the same question waits in the hand (decisions §145): a goal's open question, as the host keeps it in the Board's needs
    ask = {"id": "page-example", "by": "claude-code", "leader": "architect", "q": "Which way does the table open first, the lanes or the dealer?" + EXAMPLE,
           "choices": ["The lanes first", "The dealer first", "Both at once"], "pick": 0, "why": "Tech's view: the lanes are what is read most" + EXAMPLE, "project": False,
           "kinds": ["take", "take", "other"], "lines": ["The leaders' words are seen first", "What waits is seen first", "Both stand at once, the lanes narrower"]}
    if talk:
        t = talk[0]
        needs = board.get("needs_you") or []
        had = next((x for x in needs if x.get("idea") == t["slug"]), None)
        if had:
            had["questions"] = [ask, *(had.get("questions") or [])]
        else:
            board["needs_you"] = [{"idea": t["slug"], "goal": t.get("goal") or "tech", "title": t["title"], "priority": "normal", "blocks": False, "at": at(11, 58), "kind": "talk", "round": 1,
                                   "stances": [], "text": ask["q"], "outside": True, "questions": [ask]}, *needs]
    feed["heads"] = [({**h, "asks": True, "news": True} if h["leader"] == "tech" else h) for h in feed.get("heads") or []]


def lay_new_goals(data: dict) -> None:
    """Four new goals, for the sort and the duel to work on."""
    new = [("The timer stops at a round's end", "lava", "bug", "tech", "a play test"), ("Coins in the sky", "ice", "balance", "design", "a play test"),
           ("Store page", "dust", "store", "product", "its first page"), ("A glint on every coin", "meadow", "picture", "design", "a play test")]
    top = max(number(n) for n in nodes(data))
    for i, (title, element, sign, goal, origin) in enumerate(new):
        nodes(data).append({"slug": f"{top + 1 + i}-example-{i + 1}", "goal": goal, "title": title + EXAMPLE, "short": title + EXAMPLE, "state": "new", "queue": "", "agreed": False,
                            "element": element, "hue": element, "flag": None, "type": {"sign": sign}, "route": [], "decided": [], "origin": origin + EXAMPLE})


def _hash(s: str) -> int:
    h = 7
    for c in s:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h


def _leaders(n: dict, parties: list[str]) -> list[str]:
    if (n.get("type") or {}).get("sign") == "bug":
        return ["tech"]
    own = [n["goal"], *[r["party"] for r in n.get("route") or [] if r.get("step") == "party"], "product", "tech", "design"]
    return [p for p in dict.fromkeys(own) if p in parties and p != "release"][:3]


def lay_verdicts(data: dict) -> None:
    """The leaders' words on the cards, as the host answers them (`ideas.verdicts`: each leader's `### Talk` of a goal's page: verdict, why, for, against,
    instead): a feature has Product, Tech and Design, a bug Tech alone; some doubt, some find a risk, one goal's Tech says no (a risk that blocks)."""
    parties = [g["slug"] for g in reply(data, "ideas.map")["result"].get("goals") or []]
    work = latest(data, "ready", 12)
    if len(work) > 3 and not work[3].get("type"):
        work[3]["type"] = {"sign": "bug"}
        mark(work[3])
    blocked = work[1]["slug"] if len(work) > 1 else ""
    out = dict(reply(data, "ideas.verdicts")["result"] if reply(data, "ideas.verdicts") else {})
    for n in (x for x in nodes(data) if x["state"] in SHOWN):
        tokens = []
        for leader in _leaders(n, parties):
            h = _hash(n["slug"] + leader)
            t = {"leader": leader, "verdict": "go", "why": "", "stance": "", "for": f"{leader.title()} agrees with the way it is made" + EXAMPLE, "against": "", "instead": "", "assumes": None}
            if h % 2:
                t["why"] = "The change has its test" + EXAMPLE
            if h % 4 == 0:
                t.update(verdict="doubt", why="Does it need its own order?" + EXAMPLE)
            if h % 5 == 1:
                t.update(against="Two faces share one sort" + EXAMPLE, instead="each face keeps its order, one reader below" + EXAMPLE)
            if n["slug"] == blocked and leader == "tech":
                t.update(verdict="no", why="A change here breaks the phone's cache name" + EXAMPLE, instead="keep the cache name and bump its version" + EXAMPLE)
            tokens.append(t)
        if tokens:
            out[n["slug"]] = tokens
    ensure(data, "ideas.verdicts", {})
    reply(data, "ideas.verdicts")["result"] = out


def lay_jobs(data: dict) -> None:
    """A Board that keeps its Jobs to be done (this repository keeps none): the personas, a job, its forces, the smaller jobs, what is hired and fired."""
    jtbd = {
        "title": "Jobs to be done", "line": "Who hires Orkboard, for what job", "party": "product",
        "personas": [{"id": "solo", "title": "Solo developer", "line": "Runs AI tools on their own project and wants the work to go on while they look away."},
                     {"id": "lead", "title": "The reviewing lead", "line": "Reads what the orks made and decides what goes into main."}],
        "job": {"id": "main", "when": "I have several AI tools going on my project", "want": "one place where each tool's work is a goal I can see and answer",
                "so": "I stay the one who decides, not the one who watches terminals", "persona": "solo"},
        "forces": [{"dir": "in", "kind": "Push", "text": "terminals scroll past and I lose what each tool did"}, {"dir": "in", "kind": "Pull", "text": "one Board, a card a goal, a gate before main"},
                   {"dir": "out", "kind": "Anxiety", "text": "will the orks break main?"}, {"dir": "out", "kind": "Habit", "text": "I just talk to one tool in a terminal"}],
        "jobs": [{"id": "waits", "title": "Know what waits for me", "line": "One look says what asks, what is ready."},
                 {"id": "changed", "title": "See what changed before main", "line": "The gate's tests and the diff, then my yes."},
                 {"id": "stop", "title": "Stop a tool that runs away", "line": ""}],
        "hired": {"id": "orkboard", "title": "Orkboard", "line": "One Board for the goals: the orks do them, you decide what goes into main."},
        "fired": [{"id": "tabs", "title": "A terminal tab per tool", "line": "Each tool alone; nothing says what is done or what waits."},
                  {"id": "todo", "title": "A TODO file", "line": "Written once, never read; the tools do not take it."}],
    }

    def marked(x):
        x["title"] += EXAMPLE
    for x in [*jtbd["personas"], *jtbd["jobs"], *jtbd["fired"], jtbd["hired"]]:
        marked(x)
    jtbd["job"]["so"] += EXAMPLE
    tables = ensure(data, "ideas.tables", {})
    tables.setdefault("product", {})["jtbd"] = jtbd


def lay_limits(data: dict) -> None:
    """The AI tools' limits the host reads (the snapshot's `limits`): what is left of each today, for the potions of the costs' mat and the header's bottles."""
    row = lambda name, left: {"provider": name.lower(), "name": name, "left": left, "rows": [{"window": "5h", "left": left, "reset": ""}]}  # noqa: E731
    data["state"]["limits"] = [row("Claude", 0.62), row("Codex", 0.18)]


def lay_standard(data: dict) -> None:
    """Everything above, for the tests that press a goal in talk, a gate, a deck, a leader's word or a table."""
    lay_examples(data)
    lay_new_goals(data)
    lay_verdicts(data)
    lay_jobs(data)


def recording() -> dict:
    return copy.deepcopy(json.loads(RECORDING.read_text(encoding="utf-8")))
