"""A goal by dialog (spec 34 §1, §4; spec 35 §2: a description and a priority, the keeper writes the rest), as
`gui/ideas.py`'s `Ideas` has it: `ideas.goal_save`, `ideas.goal`, `ideas.read_now`, `ideas.words` (New idea's completion).

Saving a goal sends it to the keeper at once (core/idea_goals.py); a goal's state (`reading` → `asks` | `ready`) lives
beside its page (`<state_dir>/goals/<slug>/`). Split from ideas.py to keep it under ~600 lines.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from orkboard.core import idea_keeper
from orkboard.gui.ideas_args import IdeasError, _device, _opt, _text
from orkboard.hooks.warder import is_secret
from orkboard.realm import (event_log, goal_team, goal_types, goal_verdict, harnesses, idea_questions, idea_target, idea_words, ideas, library, own_parties,
                            party_proposals, party_recipes, project_kind, roles)


DOC_CHARS = 100_000
NO_SECRETS = "That file may hold secrets: open it in your own editor"
UNMADE = "General, Team and Ideation are not made any more: pick a party of the project's crafts"
HIDDEN_DIRS = (".git", ".orkcraft")           # git's own and the machine's own: never shown


def _kept_back(rel: Path) -> bool:
    """A path `ideas.doc` does not read: what the Warder keeps from the orks (`is_secret`), or under .git/ or .orkcraft/."""
    return is_secret(rel.as_posix()) or any(part in HIDDEN_DIRS for part in rel.parts)


class GoalsMixin:
    def goal_state(self, slug: str) -> dict:
        st = ideas.goal_state(self.state_dir, slug)
        if st["state"] == "reading" and not self.keeper.busy_goal(slug):
            st["state"] = "raw"                        # a reading the host lost (it closed)
        return st

    def _goal_row(self, g: dict) -> dict:
        """A goal as the board lists it: its fields, its state in the keeper's words."""
        st = self.goal_state(g["slug"])
        lead = roles.role(self.state_dir, g.get("leader") or roles.TASKMASTER) or roles.role(self.state_dir, roles.TASKMASTER)
        root, craft = self.root(False), goal_team.craft_of(self.root(False), g["slug"])
        return {**g, "race": roles.PARTY_RACES[craft][0] if craft in roles.PARTY_RACES else roles.RACES[g["craft"]], "party_craft": craft,
                "state": st["state"], "state_error": st["error"], "ideas": g["count"],
                "leader": {"slug": lead["slug"], "name": lead["name"], "head": goal_team.head_in(root, g["slug"], lead, idea_target.target_for(self.board_settings(), g))},
                "party": goal_team.party_of(root, g["slug"]),
                "verdict": goal_verdict.read(self.state_dir, g["slug"])}

    def goal(self, args: dict) -> dict:
        slug = _text(args, "slug", 100)
        g = next((t for t in ideas.tracks(self.root(), make=False) if t["slug"] == slug), None)
        if g is None:
            raise IdeasError("That party is gone")
        st = self.goal_state(slug)
        page = ideas.track_page(self.root(), slug)
        return {**self._goal_row(g), "description": g["about"],
                "sections": [{"name": n, "text": page.section(n)} for n in ideas.TRACK_SECTIONS],
                "talk": ideas.talk(self.state_dir, slug, goal=True),
                "busy": bool(self.keeper.busy_goal(slug)) or st["state"] == "reading"}

    def words(self, args: dict) -> dict:
        """`{"track"}`: the words New idea completes with (realm/idea_words.py): the goal's title and its ideas' titles,
        then the words of its description, summary, metrics, questions and its ideas' theses, the most used first."""
        root = self.root()
        track = _opt(args, "track")
        g = next((t for t in ideas.tracks(root, make=False) if t["slug"] == track), None)
        if g is None:
            raise IdeasError("That party is gone")
        mine = ideas.ideas(root, track)
        texts = [g["title"], g["about"], g["summary"], *(m["name"] for m in g["metrics"]), *g["questions"],
                 *(f"{i['title']}\n{i.get('thesis') or ''}" for i in mine)]
        return {"track": track, "words": idea_words.words(texts, [g["title"], *(i["title"] for i in mine)])}

    def goal_accept(self, args: dict) -> dict:
        """`{"slug"}`: the goal's leader accepts it against its metrics now (its verdict: realm/goal_verdict.py)."""
        slug = _text(args, "slug", 100)
        try:
            self.keeper.accept_goal(slug)
        except idea_keeper.KeeperError as e:
            raise IdeasError(str(e)) from None
        self.changed(f"goal:{slug}")
        return {"ok": True}

    def goal_save(self, args: dict) -> dict:
        """`{"slug"?, "about", "priority", "title"?, "craft"?, "team"?, "every"?, "leader"?, "size"?, "tool"?, "tools"?}`: a party (realm/goal_team.py:
        a leader, builders and checkers in their seats); its agents of the library are made
        roles of the project (realm/library.py), the person's own agents taken as they are; `every`: the team's checkers
        whose check applies to every idea, not only where it applies (realm/idea_checks.py): a title typed is the person's (never rewritten); spec 34's
        metrics, links and deadline are still taken and kept when given."""
        slug = _opt(args, "slug") or None
        about = args.get("about", None if slug else "")          # a goal that exists keeps what is left out (spec 41 §7)
        title = args.get("title", "")
        if about is not None and not isinstance(about, str) or not isinstance(title, str):
            raise IdeasError("about is not text")
        before = next((t for t in ideas.tracks(self.root(), make=False) if t["slug"] == slug), None) if slug else None
        recipe = _opt(args, "proposal") or _opt(args, "preset")
        if not slug:
            self._unmade(args, title, recipe)                  # General, Team and Ideation are not made (spec 99 §1.1)
        routines = self.routines_asked(args, party_recipes.routines_of(recipe, project_kind.read(self.host.repo_root)["kind"])) if not slug else []        # the running party's recurring goals the person kept (spec 92 §2)
        metrics, links = args.get("metrics"), args.get("links")
        if metrics is not None and not isinstance(metrics, list) or links is not None and not isinstance(links, list):
            raise IdeasError("Metrics and links are lists")
        deadline = args.get("deadline") if isinstance(args.get("deadline"), str) else None
        notes: list[str] = []
        party = _opt(args, "party")
        same_party = bool(party and slug and party == goal_team.party_of(self.root(), slug))      # sent again as it is: nothing is picked
        kept: list[str] = []                                   # the team a party made before was saved with: seats do not refuse it (spec 87 §5)
        if party and not same_party:                           # a saved party picked (spec 43 §6.2): its own agents the project has not are made
            saved = own_parties.get(party)
            if saved is None:
                raise IdeasError("That party is gone")
            kept = list(saved.get("team") or [])
            if args.get("team") is None and args.get("leader") is None:        # only its id was sent: the party as it was saved
                args = {**args, "team": saved.get("team") or [], "every": saved.get("every") or [], "leader": saved.get("leader") or roles.TASKMASTER}
            for o in saved.get("own") or []:
                if roles.install_own(self.state_dir, o):
                    continue
                if roles.role(self.state_dir, str(o.get("slug") or "")) is not None:
                    notes.append(f"{o.get('name') or o.get('slug')} is this project's already: kept as it is")
        team = None
        if args.get("team") is not None:
            try:
                team = goal_team.clean(args.get("team"))
            except ValueError as e:
                raise IdeasError(str(e)) from None
            if bad := [s for s in team if library.get(s) is None and roles.role(self.state_dir, s) is None]:
                raise IdeasError(f"No agent {bad[0]!r}")
        leader = _opt(args, "leader") or None
        if leader is not None and library.get(leader) is None:
            raise IdeasError(f"No agent {leader!r}")
        tool = self._tool_asked(args, slug)
        tools = self._tools_asked(args, slug, team, leader)      # each seat's own AI tool (spec 91 §6)
        if slug and ideas.track_page(self.root(False), slug) is not None:
            kept += goal_team.team_of(self.root(False), slug)
        if why := goal_team.seats(team or [], leader or "", kept):          # a size sent changes the tiers, never the squad (spec 99 §1.3)
            raise IdeasError(why)
        size = self._size_asked(args, slug, team)
        got, new = ideas.save_goal(self.root(), slug, title[:ideas.TITLE_CHARS],
                                   about[:ideas.SECTION_CHARS] if about is not None else None, metrics,
                                   _opt(args, "priority") or (None if slug else "normal"), links, deadline,
                                   _opt(args, "craft") or None)
        if team is not None:
            library.install(self.state_dir, [s for s in team if library.get(s) is not None])
            every = args.get("every") if isinstance(args.get("every"), list) else []
            goal_team.set_team(self.root(), got, team, [s for s in every if isinstance(s, str)], leader, party)
            party_proposals.drop_left(self.root(), self.state_dir, got)
        elif leader is not None:
            goal_team.set_team(self.root(), got, goal_team.team_of(self.root(), got), goal_team.every_of(self.root(), got), leader, party)
        if party and not same_party:
            own_parties.used(party, own_parties.project_key(self.host.repo_root), Path(self.host.repo_root).name, got)
        if leader:
            library.install(self.state_dir, [leader])
        if tool is not None:
            goal_team.set_tool(self.root(), got, tool)
        if tools is not None:
            goal_team.set_tools(self.root(), got, tools)
        elif team is not None or leader is not None:         # a seat that left the party takes its tool with it
            self._tools_pruned(got)
        if size:
            self._size_kept(args, got, size, before)
        elif team is not None or leader is not None:
            self._tiers_kept(got)                           # a party with a size: its seats' tiers follow its team (spec 81 §2)
        if "releases_from" in args:                          # a Release party's sources (spec 68 §3.2)
            self.save_releases_from(got, args["releases_from"])
        if before is None and recipe in party_recipes.CRAFTS and not goal_team.recipe_of(self.root(), got):
            goal_team.set_recipe(self.root(), got, recipe)       # a party of a craft keeps it: its heads are its craft's race (spec 99 §1.4)
        if before is None and routines:
            self.running_made(got, recipe, routines, args)       # the recurring goals added (spec 92)
        g = next(t for t in ideas.tracks(self.root(), make=False) if t["slug"] == got)
        self._ev(event_log.GOAL_SAVED, args, goal=got, new=new, preset=self._preset_kept(args, g), metrics=[m["name"] for m in g["metrics"]], links=g["links"],
                 priority=g["priority"], craft=g["craft"], team=g["team"], every=g["every"], leader=g["leader"] or roles.TASKMASTER,
                 party=goal_team.party_of(self.root(), got), tool=g["tool"], tools=[f"{a}:{t}" for a, t in g["tools"].items()])
        if new or before is None or _what_it_says(before) != _what_it_says(g):
            self._read_goal(got)                   # a save of its party alone reads nothing again (spec 41 §7)
        self.changed(f"goal:{got}")
        return {"slug": got, **({"notes": notes} if notes else {})}

    def _size_asked(self, args: dict, slug: str | None, team: list[str] | None) -> str:
        """`size` of `ideas.goal_save` (spec 75 §3.1): lean · standard · full, "" when none was sent. A team that lets a member with work open
        go with the size is refused (spec 52's swap holds): *<name> has work open: it cannot leave*."""
        size = args.get("size")
        if size is None:
            return ""
        if size not in goal_team.SIZES:
            raise IdeasError("A size is lean, standard or full")
        if slug and team is not None:
            left = [s for s in goal_team.team_of(self.root(), slug) if s not in team]
            if left and (busy := [s for s in left if s in goal_types.Party(self.state_dir, self.root(), slug).busy()]):
                r = roles.role(self.state_dir, busy[0])
                raise IdeasError(f"{(r or {}).get('name') or busy[0]} has work open: it cannot leave")
        return size

    def _tool_asked(self, args: dict, slug: str | None) -> str | None:
        """`tool` of `ideas.goal_save` (spec 81 §1): an AI tool's id, or "" for the Main tool; None when none was sent. Refused: *No AI tool <id>*,
        and a tool this computer does not have (unless the party has it already): *<Title> is not installed*."""
        tool = args.get("tool")
        if tool is None:
            return None
        if not isinstance(tool, str) or (tool and harnesses.get(tool) is None):
            raise IdeasError(f"No AI tool {tool}" if isinstance(tool, str) else "tool is not text")
        if tool and tool != (goal_team.tool_of(self.root(False), slug) if slug else "") and tool not in self.tools_installed():
            raise IdeasError(f"{harnesses.title(tool)} is not installed")
        return tool

    def _tools_asked(self, args: dict, slug: str | None, team: list[str] | None, leader: str | None) -> dict[str, str] | None:
        """`tools` of `ideas.goal_save` (spec 91 §6): `{agent: tool}`, each seat's own AI tool (a `harnesses` id); {} clears them; None when none was sent.
        Refused: *No AI tool <id>*, and *<agent> is not in the party* for one that is not in the team the party has after this save (its leader too)."""
        tools = args.get("tools")
        if tools is None:
            return None
        if not isinstance(tools, dict):
            raise IdeasError("tools is not a map of agent to tool")
        for tool in tools.values():
            if not isinstance(tool, str) or harnesses.get(tool) is None:
                raise IdeasError(f"No AI tool {tool}")
        root, there = self.root(False), bool(slug) and ideas.track_page(self.root(False), slug) is not None
        seats = {*(team if team is not None else goal_team.team_of(root, slug) if there else []),
                 leader or (goal_team.leader_of(root, slug) if there else roles.TASKMASTER)}
        if gone := next((a for a in tools if a not in seats), None):
            raise IdeasError(f"{gone} is not in the party")
        return {str(a): t for a, t in tools.items()}

    def _tools_pruned(self, got: str) -> None:
        """The party's seats' tools without those of seats that left it."""
        root = self.root()
        mine = goal_team.tools_of(root, got)
        seats = {*goal_team.team_of(root, got), goal_team.leader_of(root, got)}
        if any(a not in seats for a in mine):
            goal_team.set_tools(root, got, {a: t for a, t in mine.items() if a in seats})

    def _unmade(self, args: dict, title: object, recipe: str) -> None:
        """General, Team and Ideation are never made (spec 99 §1.1, decisions §122): a new party of their recipe, their leader or their name is refused. A party of
        theirs the project has stays until the person removes it, and is edited as it was."""
        name = " ".join(str(title or "").split()).lower()
        if recipe in ("ideation", party_recipes.TEAM_ID) or _opt(args, "leader") == library.INVESTOR or name in (ideas.GENERAL, "team", "ideation"):
            raise IdeasError(UNMADE)

    def _tiers_kept(self, got: str) -> None:
        """The tiers a party's size gives its seats, kept with it (spec 81 §2); none for a party with no size."""
        root = self.root()
        if size := goal_team.size_of(root, got):
            goal_team.set_tiers(root, got, party_recipes.tiers_for(goal_team.leader_of(root, got), goal_team.team_of(root, got), size))

    def _size_kept(self, args: dict, got: str, size: str, before: dict | None) -> None:
        """The party's size kept, with `party_resized` (and who `joins` and `leaves`) when a party that was there changed it, and `proposal_taken`
        when it was made from one of the Orkmaster's (`proposal`: the recipe's id, or a recipe's `preset`), which the party keeps (spec 81 §3)."""
        goal_team.set_size(self.root(), got, size)
        self._tiers_kept(got)
        was = (before or {}).get("size") or ""
        if before is not None and was != size:
            now, had = goal_team.team_of(self.root(), got), (before or {}).get("team") or []
            self._ev(event_log.PARTY_RESIZED, args, party=got, joins=[s for s in now if s not in had], leaves=[s for s in had if s not in now],
                     **{"from": was, "to": size})
        recipe = _opt(args, "proposal") or _opt(args, "preset")
        if before is None and party_recipes.get(recipe) is not None:
            goal_team.set_recipe(self.root(), got, recipe)
            self._ev(event_log.PROPOSAL_TAKEN, args, kind=party_recipes.kind_of(recipe, project_kind.read(self.host.repo_root)["kind"]), recipe=recipe, size=size)

    @staticmethod
    def _preset_kept(args: dict, g: dict) -> str:
        """The library's party (`preset`) a party was picked from, as it is saved (spec 59 §5): "" when none was sent, it is not one
        of the library's, or the leader or the team is not what it gives (a seat changed after)."""
        one = next((p for p in library.presets() if p["id"] == _opt(args, "preset")), None)
        same = one is not None and (g["leader"] or roles.TASKMASTER) == one["lead"] and sorted(g["team"]) == sorted([*one["build"], *one["check"]])
        return one["id"] if same else ""

    def _read_goal(self, slug: str, said: str = "") -> None:
        """The keeper reads the goal at once, in the background; a keeper that may not run (the demo, the spend limit)
        leaves it `raw` with the reason on it."""
        try:
            self.keeper.read_goal(slug, said)
        except idea_keeper.KeeperError as e:
            if said:
                raise IdeasError(str(e)) from None

    def read_now(self, args: dict) -> dict:
        slug = _text(args, "slug", 100)
        try:
            self.keeper.read_now(slug)
        except idea_keeper.KeeperError as e:
            raise IdeasError(str(e)) from None
        self.changed(slug)
        return {"ok": True}

    def doc(self, args: dict) -> dict:
        """A document a goal links, to show in the preview: a path in the repository or a page of the Wiki, read only,
        cut at DOC_CHARS; a Markdown one with its `html` too. Nothing outside those two folders; a URL is never fetched (the page opens it in the browser)."""
        link = _text(args, "path", 300).split("#")[0]
        if "://" in link:
            raise IdeasError("A web link opens in the browser")
        for base in (Path(self.host.repo_root), self.root()):
            path = (base / link.lstrip("/")).resolve()
            if path.is_file() and base.resolve() in path.parents:
                # the name asked for and the file it resolves to (a link to a `.env` is a `.env`)
                if _kept_back(Path(link.lstrip("/"))) or _kept_back(path.relative_to(base.resolve())):
                    raise IdeasError(NO_SECRETS)
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    raise IdeasError("That file cannot be read as text") from None
                out = {"path": link, "text": text[:DOC_CHARS], "truncated": len(text) > DOC_CHARS}
                if path.suffix.lower() in (".md", ".markdown"):      # rendered as the Files pane renders it (spec 37 §8)
                    from orkboard.gui import markdown
                    out["html"] = markdown.render(out["text"])
                return out
        raise IdeasError("That document is not in the repository or the Wiki")

    def goal_event(self, slug: str) -> None:
        """`goal_read` when a goal's reading ends (asks, ready, or raw: it could not)."""
        import time
        st = ideas.goal_state(self.state_dir, slug)["state"]
        now = time.monotonic()
        was, since = self._seen.get(f"goal:{slug}", ("", None))
        if st == was:
            return
        self._seen[f"goal:{slug}"] = (st, now)
        if st in ("asks", "ready", "raw") and was == "reading":
            got = ideas.goal_state(self.state_dir, slug)
            m = got["measure"] or {}
            self._ev(event_log.GOAL_READ, goal=slug, state=st, seconds=round(now - since, 1) if since else None,
                     tier=got["tier"], effort=got["effort"], step=m.get("step") or "goal", prompt_chars=m.get("prompt_chars"),
                     tokens=m.get("tokens"), cost=m.get("cost"))

    def goal_needs(self, goals: list[dict]) -> list[dict[str, Any]]:
        """A goal that asks is in Needs you (spec 35 §10: its own priority, oldest first)."""
        out = []
        for g in goals:
            if g["state"] == "asks":
                asked = [idea_questions.parse(q) for q in g["questions"][:5]]
                out.append({"idea": "", "goal": g["slug"], "kind": "goal", "title": g["title"],
                            "text": asked[0]["ask"] if asked else "The keeper asks you about this party",
                            "questions": g["questions"][:5], "asked": asked,
                            "priority": g["priority"], "blocks": False,
                            "at": ideas.goal_state(self.state_dir, g["slug"])["read_time"]})
        return out + party_proposals.rows(self.root(False), self.state_dir, goals)       # a party's proposal waits too (spec 43 §4.2)


def _what_it_says(g: dict) -> tuple:
    """What a goal says, which the keeper reads: its words, title, priority, craft, metrics, links and deadline (not
    its party)."""
    return (g["about"], g["title"], g["priority"], g["craft"], json.dumps(g["metrics"], sort_keys=True), g["links"],
            g["deadline"])
