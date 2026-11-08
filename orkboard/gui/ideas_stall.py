"""The stall's host (docs/specs/157-the-inventory-a-merchants-stall.md §C; decisions §266.2, §267.1): what a chair of the Board carries, what it could take, and the takes.

    ideas.stall {chair}                  # {chair, whose, say, shelves: [{id, label, sub, kind, slot, wares: [{id, word, line, head?, stats?, price, before}]}], hand: [{slot, label, word, line, head?, yours, fixed}]}
    ideas.stall_take {chair, slot, value}   # {stall, undo: {slot, value}}: the slot written through its own writer, `changed` published
    ideas.stall_back {chair, slot}          # the same, the slot's default written (the setting's, the craft's default hero, the potions' order, the recipe's tier)
    ideas.hero_table {party}                # `hero_table.read` and the hero's `layout`, and `elements` {goal slug: element} of the goals its cards name

The chair `""` is the Orkmaster's (the project's settings), a party's slug its leader's, Release's party its locked chair. `kind` is `heroes` (the top shelf) or `small`.
`yours` in the hand is the id of the value carried ("" when the seats' own tiers differ). **A price is never made up**: `{mine: true}` for what is carried, `{locked: why}`,
else a `{word}` (`lighter`, `heavier`, `one pass`, `same cost`); a `{share}` is sent only from an estimator that measures the first potion's week, and none does today, so none
is sent. A tier's word is the difference of `party_price.price` at that tier and now; a setting that takes no model's work is `same cost`. `before` marks the value carried before
the last take of the slot (kept on the instance, for the run of the host).
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from orkboard import settings
from orkboard.gui.ideas_args import IdeasError, _text
from orkboard.realm import craft_tools, goal_team, hero_table, heroes, ideas, library, look_wait, map_parts, party_price, party_recipes

ON_OFF = (("on", "On"), ("off", "Off"))
TARGETS = (("thrift", "Thrift", "Cheaper models, fewer checks"), ("balance", "Balance", "The usual mix"), ("quality", "Quality", "Better models, more checks"))
TIERS = (("laborer", "Laborer", "The lightest model of its tool"), ("warrior", "Warrior", "The middle model"), ("elder", "Elder", "The strongest model"))
ORKMASTER = (       # (slot, label, sub, [(value, word, line)])
    ("target", "How deep", "How much the orks spend on a goal", TARGETS),
    ("look_wait", "Give me time to look", "How long a spec waits for your look", tuple((c, look_wait.LABELS[c], look_wait.LINES[c]) for c in look_wait.CHOICES)),
    ("autostart", "Starts by itself", "A safe plan starts without asking", tuple((v, w, "A safe plan starts by itself" if v == "on" else "Every plan waits for you") for v, w in ON_OFF)),
    ("work_at_night", "Works at night", "Plans that would start by themselves wait for the night", tuple((v, w, "The orks work in the night's hours" if v == "on" else "The orks do not start work at night") for v, w in ON_OFF)),
    ("push", "Push after merging", "Whether a merge into the work branch is pushed", tuple((v, w, "Results are pushed after they merge" if v == "on" else "Results stay on this computer") for v, w in ON_OFF)),
)
LABELS = {"hero": "Its hero", "tool": "Its AI tool", "tier": "Its seats' tier", "gate": "The gate"}
LOCKED_HERO = "Release's hero is fixed"
LOCKED_GATE = "The gate is set in orkcraft.toml"
LOCKED_SEATS = "Release's seats are fixed"


def _onoff(v: object) -> str:
    return "on" if v else "off"


class StallMixin:
    """Needs `root()`, `state_dir`, `settings_now()`, `board_settings()`, `board_set()`, `into()`, `tools()`, `changed()`, `host` (gui/ideas.py and its mixins)."""

    # -- the chairs ------------------------------------------------------------------------------------------

    def _chair(self, args: dict) -> tuple[str, Path, str]:
        """(chair, root, craft): `""` the Orkmaster's; a party's slug its leader's; else *That party is gone*."""
        chair = args.get("chair", "")
        if not isinstance(chair, str):
            raise IdeasError("chair is missing")
        root = self.root(False)
        if chair and (chair == ideas.GENERAL or ideas.track_page(root, chair) is None):
            raise IdeasError("That party is gone")
        return chair, root, (map_parts.craft_of(root, chair) if chair else "")

    def _carried(self, chair: str, root: Path, slot: str) -> str:
        if not chair:
            s = self.settings_now()
            return {"target": str(s.get("target") or settings.IDEAS["target"]), "look_wait": look_wait.clean(s.get("look_wait")),
                    "autostart": _onoff(s.get("autostart", True)), "work_at_night": _onoff(s.get("work_at_night") is True),
                    "push": _onoff(s.get("push") is True)}[slot]
        if slot == "hero":
            h = goal_team.hero_of(root, chair)
            return h.id if h is not None else ""
        if slot == "tool":
            return goal_team.tool_of(root, chair)
        if slot == "tier":
            got = {self._seat_tier(root, chair, s) for s in goal_team.team_of(root, chair)}
            return got.pop() if len(got) == 1 else ""
        return "gate"

    def _recipe_tiers(self, root: Path, chair: str) -> dict[str, str]:
        return party_recipes.tiers_for(goal_team.leader_of(root, chair), goal_team.team_of(root, chair), goal_team.size_of(root, chair) or "standard")

    def _seat_tier(self, root: Path, chair: str, seat: str) -> str:
        a = library.get(seat)
        return goal_team.tiers_of(root, chair).get(seat) or self._recipe_tiers(root, chair).get(seat) or (a.tier if a is not None else "warrior")

    def _tool_ids(self) -> list[tuple[str, str]]:
        """The AI tools signed in, `(id, name)` (the ready tools of `ideas.tools`, the order of the potions' list)."""
        return [(t["id"], t["name"]) for t in self.tools({})["tools"] if t.get("ready")]

    def _slot_values(self, chair: str, root: Path, slot: str) -> list[tuple[str, str, str]]:
        """`[(value, word, line)]` a slot can take."""
        if not chair:
            return list(next(v for s, _l, _s, v in ORKMASTER if s == slot))
        if slot == "hero":
            return [(h.id, h.name, h.flow) for h in heroes.of(map_parts.craft_of(root, chair))]
        if slot == "tool":
            return [("", "Main tool", "The potions' order: the first AI tool in your hand that has mana")] + [(i, n, "Runs this party's goals") for i, n in self._tool_ids()]
        return list(TIERS)

    # -- the price (never made up) -----------------------------------------------------------------------------

    def _tier_cost(self, root: Path, chair: str, tier: str | None) -> float:
        team = goal_team.team_of(root, chair)
        tiers = goal_team.tiers_of(root, chair)
        if tier is not None:
            tiers = {**tiers, **{s: tier for s in team}}
        got = party_price.price(root, self.state_dir, self.board_settings(), goal_team.leader_of(root, chair), team, goal_team.every_of(root, chair),
                                goal_team.size_of(root, chair) or None, tiers)
        return (got["low"] + got["high"]) / 2

    def _price(self, chair: str, root: Path, slot: str, value: str, mine: str, cache: dict) -> dict:
        if value == mine:
            return {"mine": True}
        if slot == "hero":
            return {"word": "one pass"}                 # a hero lays its table in one pass of its leader (spec 157 F)
        if slot == "target":
            order = [v for v, _w, _l in TARGETS]
            d = order.index(value) - order.index(mine) if mine in order else 0
            return {"word": "lighter" if d < 0 else "heavier" if d > 0 else "same cost"}
        if slot == "tier":
            try:
                if "now" not in cache:
                    cache["now"] = self._tier_cost(root, chair, None)
                if value not in cache:
                    cache[value] = self._tier_cost(root, chair, value)
            except Exception:                           # an estimate that cannot be read says no more than that
                return {"word": "same cost"}
            return {"word": "lighter" if cache[value] < cache["now"] - 1e-9 else "heavier" if cache[value] > cache["now"] + 1e-9 else "same cost"}
        return {"word": "same cost"}                    # a setting that takes no model's work

    # -- ideas.stall ------------------------------------------------------------------------------------------------

    def stall(self, args: dict) -> dict:
        chair, root, craft = self._chair(args)
        before = self.__dict__.setdefault("_stall_before", {})
        slots: list[tuple[str, str, str, str]] = []
        if not chair:
            slots = [(s, lab, sub, "small") for s, lab, sub, _v in ORKMASTER]
            say = "Every ware has its price in words: lighter or heavier than what you carry, one pass, or the same cost. Nothing is guessed."
            whose = "The Orkmaster"
        else:
            page = ideas.track_page(root, chair)
            whose = (page.title if page is not None else "") or chair
            if craft:
                slots.append(("hero", LABELS["hero"], "The school its leader looks by", "heroes"))
            if craft != "release":
                slots.append(("tool", LABELS["tool"], "What runs this party's goals", "small"))
                if goal_team.team_of(root, chair):
                    slots.append(("tier", LABELS["tier"], "The model each seat of the party gets", "small"))
            h = goal_team.hero_of(root, chair) if craft else None
            if h is None:
                say = "This party has no hero: its goals run as the Taskmaster plans them."
            elif h.default:
                say = f"{h.name} looks by {h.school}. It lays its craft's map."
            else:
                say = f"{h.name} looks by {h.school}. It lays {len(h.places)} places: {', '.join(n for n, _a in h.places)}."
        shelves, hand, cache = [], [], {}
        for slot, label, sub, kind in slots:
            mine = self._carried(chair, root, slot)
            wares = []
            for value, word, line in self._slot_values(chair, root, slot):
                ware: dict[str, Any] = {"id": value, "word": word, "line": line}
                if slot == "hero":
                    hero = heroes.get(value)
                    ware["head"] = heroes.head(hero)
                    ware["stats"] = {"school": hero.school, "flow": hero.flow, "size": hero.size, "decides": hero.decides, "says_no": hero.says_no}
                    ware["line"] = hero.school
                ware["price"] = {"locked": LOCKED_HERO} if craft == "release" and slot == "hero" and value != mine else self._price(chair, root, slot, value, mine, cache)
                ware["before"] = before.get((chair, slot)) == value and value != mine
                wares.append(ware)
            shelves.append({"id": slot, "label": label, "sub": sub, "kind": kind, "slot": slot, "wares": wares})
            have = next((w for w in wares if w["id"] == mine), None)
            card: dict[str, Any] = {"slot": slot, "label": label, "word": have["word"] if have else "Mixed" if slot == "tier" else "", "yours": mine,
                                    "line": have["line"] if have else "", "fixed": craft == "release" and slot == "hero"}
            if have and "head" in have:
                card["head"] = have["head"]
            hand.append(card)
        makers = craft_tools.for_party(root, chair, goal_team.tool_of(root, chair)) if chair else []
        if makers:
            wares = []
            for maker in makers:
                cap = maker["cap"]
                estimate = any(p["estimate"] for p in maker["prices"])
                money = f"{'about ' if estimate else ''}{cap['amount']} {cap['currency']} cap" if cap else ""
                wares.append({**maker, "word": maker["maker"], "line": maker["title"],
                              "price": {"money": money} if cap else {"word": "Set a cap"}, "before": False})
            shelves.append({"id": "craft_tools", "slot": "craft_tools", "label": "Its makers", "kind": "makers",
                            "sub": "Run in Orkboard on your key", "wares": wares})
        if craft == "release":                      # the gate: read from orkcraft.toml, locked
            from orkboard.realm import gate_config
            always = ", ".join(gate_config.read(Path(self.host.repo_root)).always) or "None set"
            shelves.append({"id": "gate", "label": LABELS["gate"], "sub": "What always runs before a result is merged", "kind": "small", "slot": "gate",
                            "wares": [{"id": "gate", "word": "The critical tests", "line": always, "price": {"locked": LOCKED_GATE}, "before": False}]})
            hand.append({"slot": "gate", "label": LABELS["gate"], "word": "The critical tests", "line": always, "yours": "gate", "fixed": True})
        return {"chair": chair, "whose": whose, "say": say, "shelves": shelves, "hand": hand}

    # -- the takes ------------------------------------------------------------------------------------------------

    def _write(self, chair: str, root: Path, slot: str, value: str) -> None:
        """The slot written through its own writer (`board_set`, `into`, `goal_team`)."""
        if not chair:
            if slot in ("autostart", "work_at_night"):
                self.board_set({slot: value == "on"})
            elif slot == "push":
                self.into({"push": value == "on"})
            else:
                self.board_set({slot: value})
        elif slot == "hero":
            goal_team.set_hero(root, chair, value)
        elif slot == "tool":
            goal_team.set_tool(root, chair, value)
        else:
            team = goal_team.team_of(root, chair)
            kept = {s: t for s, t in goal_team.tiers_of(root, chair).items() if s not in team}
            goal_team.set_tiers(root, chair, {**kept, **({s: value for s in team} if value else {s: t for s, t in self._recipe_tiers(root, chair).items() if s in team})})

    def _slot(self, args: dict, taking: bool) -> tuple[str, Path, str, str, str]:
        chair, root, craft = self._chair(args)
        slot = _text(args, "slot", 40)
        if slot not in ([s for s, *_ in ORKMASTER] if not chair else ["hero", "tool", "tier", "gate"]):
            raise IdeasError(f"There is no {slot} to take here")
        if craft == "release":
            raise IdeasError(LOCKED_GATE if slot == "gate" else LOCKED_HERO if slot == "hero" else LOCKED_SEATS)
        if chair and slot == "hero" and not craft:
            raise IdeasError("This party has no hero")
        if chair and slot == "tier" and not goal_team.team_of(root, chair):
            raise IdeasError("This party has no seats")
        value = ""
        if taking:
            value = args.get("value")
            if not isinstance(value, str):
                raise IdeasError("value is missing")
            if value not in [v for v, _w, _l in self._slot_values(chair, root, slot)]:
                raise IdeasError(f"{value or 'That'} is not a ware of {LABELS.get(slot, slot)}")
        return chair, root, craft, slot, value

    def _default(self, chair: str, craft: str, slot: str) -> str:
        if not chair:
            return _onoff(True if slot == "autostart" else settings.IDEAS[slot]) if slot in ("autostart", "work_at_night", "push") else str(settings.IDEAS[slot])
        return heroes.default(craft).id if slot == "hero" else ""      # the potions' order (the Main tool) and the recipe's tiers are the empty value

    def _done(self, chair: str, root: Path, slot: str, value: str) -> dict:
        old = self._carried(chair, root, slot)
        self._write(chair, root, slot, value)
        self.__dict__.setdefault("_stall_before", {})[(chair, slot)] = old
        if chair and slot == "hero" and not heroes.get(value).default:
            try:
                lay_tables = importlib.import_module("orkboard.realm.lay_tables")      # part F lays the party's goal; until it lands this is a no-op
            except ModuleNotFoundError:
                lay_tables = None
            if lay_tables is not None:
                lay_tables.lay_party(root, self.state_dir, chair)
        self.changed(chair)
        return {"stall": self.stall({"chair": chair}), "undo": {"slot": slot, "value": old}}

    def stall_take(self, args: dict) -> dict:
        if args.get("slot") == "craft_tools":
            chair, root, _craft = self._chair(args)
            maker_id = _text(args, "value", 100)
            maker = next((m for m in craft_tools.for_party(root, chair, goal_team.tool_of(root, chair)) if m["id"] == maker_id), None) if chair else None
            if maker is None:
                raise IdeasError("That maker is not for this party's craft")
            if not maker["here"]:
                raise IdeasError(f"{maker['maker']} is not here: {maker['why']}")
            with ideas.LOCK:
                taken = craft_tools.taken(root, chair)
                try:
                    craft_tools.set_taken(root, chair, {**taken, maker_id: {"cap": args.get("cap")}})
                except ValueError as exc:
                    raise IdeasError(str(exc)) from None
            self.changed(chair)
            return {"stall": self.stall({"chair": chair})}
        chair, root, _craft, slot, value = self._slot(args, True)
        return self._done(chair, root, slot, value)

    def stall_back(self, args: dict) -> dict:
        chair, root, craft, slot, _value = self._slot(args, False)
        return self._done(chair, root, slot, self._default(chair, craft, slot))

    # -- a hero's table --------------------------------------------------------------------------------------------

    def hero_table(self, args: dict) -> dict:
        party, root, _craft = self._chair({"chair": _text(args, "party", 100)})
        if not party:
            raise IdeasError("party is missing")
        h = goal_team.hero_of(root, party)
        got = hero_table.read(root, party)
        elements: dict[str, str] = {}
        for place in got["places"]:
            for c in place["cards"]:
                if c.get("goal") and c["goal"] not in elements:
                    elements[c["goal"]] = str((ideas.state(self.state_dir, c["goal"]) or {}).get("element") or "")
        return {**got, "party": party, "layout": h.layout if h is not None else "lanes", "elements": elements}


def stall_commands(m: Any) -> dict:
    return {"ideas.stall": m.stall, "ideas.stall_take": m.stall_take, "ideas.stall_back": m.stall_back, "ideas.hero_table": m.hero_table}
