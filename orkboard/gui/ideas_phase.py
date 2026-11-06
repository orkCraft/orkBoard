"""A goal's phase in its page, the host's half (docs/specs/151-the-board-in-the-repository-for-any-ai-tool.md part A; decisions §255.3): `Ideas` has it through `PhaseMixin`.

  - **Written with the Board's commit** (A.3): `phase_sync`, called by `tree_flush` before the tree commits, writes the keys of `realm/goal_phase.py` into each goal's page where they differ from its state.
    A state saved with another phase asks the tree for a write (`phase_watch`, an observer on `ideas.OBSERVERS`), so a phase rides in the next commit.
  - **Moved outside** (A.4): a page whose `phase` is not the one the Board wrote was moved by someone else (an AI tool, a hand). Its state moves to where that phase starts, a run on it is
    stopped as the person's *Stop* stops one, the line *<goal> was moved to <phase> in <by>* is said and `goal_moved_outside` logged. A page laid outside gets a state.
  - **A question laid outside** (A.5, A.6): the cards of `goal_phase.outside_cards` are answered by `ideas.talk_answer` as Talk's are; the answer is written under the question's line in the page
    (`idea_questions.answer_line`). A Talk's card answered in the hand is written there too, beside Talk's record.

Needs the Ideas' `host`, `state_dir`, `root()`, `keeper`, `_what`, `changed`, `tree_note`, `_idea_needs`, `_ev` and `_talked` (gui/ideas_talk.py).
"""
from __future__ import annotations

import datetime as dt
import time
import weakref
from pathlib import Path

from orkboard.gui.ideas_args import IdeasError
from orkboard.realm import event_log, goal_phase, idea_questions, ideas, read_in, write_out, write_out_bank

PHASE_READ_S = 5.0           # how often the clock looks for a page moved outside
RULES_MARK = "<!-- orkboard:begin"     # Orkboard's block in the repository's AGENTS.md (spec 151 C.1): the rules are written


def rules_written(repo: Path) -> bool:
    """Whether the repository (a checkout: the Board's tree) has the Board's rules, Orkboard's block in its root `AGENTS.md`."""
    try:
        return RULES_MARK in (Path(repo) / "AGENTS.md").read_text(encoding="utf-8")[:200_000]
    except (OSError, UnicodeDecodeError):
        return False


class PhaseMixin:
    # -- written with the Board's commit (A.3) ----------------------------------------------------------------

    def phase_watch(self) -> None:
        """A state saved with a phase the page has not been told asks the tree for a write (once per Ideas; the host's thread does it)."""
        if getattr(self, "_phase_watching", False):
            return
        self._phase_watching = True
        me = weakref.ref(self)

        def watch(state_dir, slug: str, state: str) -> None:
            ideas_ = me()
            if ideas_ is None:
                ideas.OBSERVERS.remove(watch)
                return
            try:
                if Path(state_dir) != ideas_.state_dir or goal_phase.of(state) == ideas.state(state_dir, slug).get("phase_written"):
                    return
                tree = getattr(ideas_, "_board_tree", None)
                if tree is not None and tree.exists():
                    tree.touch(time.time())
            except Exception:                  # a note that cannot be made never stops a save
                pass
        ideas.OBSERVERS.append(watch)

    def phase_sync(self, tree, force: bool) -> None:
        """Before the tree commits: the tree at its branch's tip, the pages moved outside followed (every `PHASE_READ_S`, and at a commit), and, when a commit is due, the keys written.
        Never raises: the Board goes on without."""
        now = time.time()
        due = force or tree.due(now)
        if not due and now - getattr(self, "_phase_at", 0.0) < PHASE_READ_S:
            return
        self._phase_at = now
        if not tree.exists():
            return
        try:
            with tree.git.lock:
                tree.follow()
        except Exception:                       # held for now; the commit says why
            pass
        try:
            self.phase_moved(tree)
            self.journals_sync(tree, due)
            if due:
                root = tree.root()
                goal_phase.mirror(root, self.state_dir, lambda i, st, plan, asks: self._idea_needs(i, st, plan, asks, root))
        except Exception as e:                  # a page that cannot be read never stops the commit; said once, not at every look
            said = f"{type(e).__name__}: {' '.join(str(e).split())[:200]}"
            if said != getattr(self, "_phase_error", ""):
                self._phase_error = said
                self.host.toast(said, title="The Board", severity="warning")
            return
        self._phase_error = ""

    # -- the journals and the brief in the tree (spec 151 B) ----------------------------------------------------

    def journals_sync(self, tree, due: bool) -> None:
        """The journals' Markdown in the Board's tree (`<wiki>/journals/`) and the brief (`<wiki>/project.md`): a line added outside is read in first (once, by its ref; a line of a kind the scope
        has not is left: `journal_left`), then the files are written again where the journals changed, so they ride in the Board's next commit. Looked at when a journal file changed since the last look, and at a commit."""
        if not rules_written(tree.path):           # nothing of B before the person's yes to the Board's rules (spec 151 C.4): a public repository's journals wait for its question
            return
        root, mine = tree.root(), Path(self.state_dir) / "journals"

        def stats(folder: Path, pattern: str) -> tuple:
            return tuple((p.name, s.st_mtime_ns, s.st_size) for p in sorted(folder.glob(pattern)) for s in [p.stat()]) if folder.is_dir() else ()
        sig = (stats(mine, "*.jsonl"), stats(mine, "*.digest.json"), stats(root / "journals", "*.md"), stats(Path(self.state_dir), "project.json"))
        if sig == getattr(self, "_journals_sig", None) and not due:
            return
        got = read_in.take_outside(root, self.state_dir)
        self.journal_left = got["left"]
        wrote = write_out.journals_into(self.state_dir, write_out_bank.parties(root), root / "journals")
        wrote += write_out.brief_into(Path(self.host.repo_root), self.state_dir, root, root)
        if wrote:
            tree.touch(time.time())
        self._journals_sig = (stats(mine, "*.jsonl"), stats(mine, "*.digest.json"), stats(root / "journals", "*.md"), sig[3])

    # -- moved outside (A.4) --------------------------------------------------------------------------------

    def phase_moved(self, tree) -> None:
        """The pages that say a phase the Board did not write, followed; looked at only when a page changed since the last look."""
        root = tree.root()
        folder = root / ideas.IDEAS
        sig = tuple((p.name, s.st_mtime_ns, s.st_size) for p in sorted(folder.glob("*.md")) for s in [p.stat()]) if folder.is_dir() else ()
        if sig == getattr(self, "_phase_sig", None):
            return
        self._phase_sig = sig
        for m in goal_phase.moved(root, self.state_dir):
            commit, author = tree.last_change(folder / f"{m['slug']}.md")
            by = m["by"] if m["by"] not in ("", goal_phase.PERSON) else author or ""       # who moved it, as far as the Board can tell: the tool that laid it, else the commit's author; the page's `by` (who laid it) is never changed
            if not m["new"]:
                self.phase_stop(m["slug"], m["to"])
            goal_phase.move_to(self.state_dir, m["slug"], m["to"])
            self._ev(event_log.GOAL_MOVED_OUTSIDE, slug=m["slug"], to=m["to"], commit=commit, **{"from": m["was"]})
            if not m["new"]:
                self.host.toast(f"{m['title']} was moved to {m['to']} " + (f"in {by}" if by else "outside Orkboard"), title="The Board")
            self._what[m["slug"]] = "moved"
            self.changed(m["slug"])

    def phase_stop(self, slug: str, phase: str) -> bool:
        """What runs on a goal moved from outside stops as *Stop* stops it (`ideas.stop`: its running tasks, the plan stopped for the person; `ideas.read_stop`: the keeper's call). True when
        something was running."""
        stopped = False
        runner = self._runner
        if runner is not None and any(s == slug for s, _t in runner.running_tasks()):
            runner.stop(slug, f"moved to {phase} from outside")
            if ideas.plan(self.state_dir, slug) is not None:
                ideas.edit_plan(self.state_dir, slug, lambda p: p.update(stopped=True))
            stopped = True
        if self.keeper.busy(slug):
            self.keeper.read_stop(slug)
            stopped = True
        return stopped

    # -- a question laid outside, an answer's line (A.5, A.6) --------------------------------------------------

    def talk_answer(self, args: dict) -> dict:
        """The cards of a page's question (`page-<n>`) are answered here; Talk's own go to the keeper, and are written to the page as well."""
        answers = args.get("answers")
        if isinstance(answers, list) and any(isinstance(a, dict) and str(a.get("id")).startswith(goal_phase.OUTSIDE_ID) for a in answers):
            return self.outside_answer(args)
        slug = str(args.get("idea") or "")
        waiting = {c["id"]: c for c in idea_questions.record(self.state_dir, slug).get("waiting") or [] if isinstance(c, dict) and "id" in c} if slug else {}
        got = super().talk_answer(args)
        if waiting:
            self.answers_written(slug, [(c["q"], *(idea_questions.answer_of(c, next((a for a in answers or [] if isinstance(a, dict) and a.get("id") == i), None))
                                                  or (idea_questions.default_of(c), "decide"))) for i, c in waiting.items()])
        return got

    def answers_written(self, slug: str, taken: list[tuple[str, str, str]]) -> None:
        """Each `(question, answer, how)` written under its line in the goal's *Open questions* (a question the page lacks is added): `how` "decide" is a leader's pick, not the person's."""
        day = dt.date.today().isoformat()
        try:
            with ideas.LOCK:
                root = self.root()
                page = ideas.idea_page(root, slug)
                if page is None:
                    return
                text = page.section("Open questions")
                for q, answer, how in taken:
                    text = idea_questions.with_answer(text, q, answer, day, "the leader" if how == "decide" else "the person")
                ideas.set_section(root, slug, "Open questions", text)
        except Exception:                       # the page is the tools' copy: Talk's record is the Board's, and has it
            pass

    def outside_answer(self, args: dict) -> dict:
        """The cards of a page's questions answered together (`{idea, answers: [{id, pick?|text?}], decide?}`): each answer under its question's line; `decide` takes the card's pick for the rest. The
        page's `asks` is cleared by the next write of the Board's keys, when no question is left."""
        slug, answers = self._talked(args)
        page = ideas.idea_page(self.root(), slug)
        cards = {c["id"]: c for c in goal_phase.outside_cards(page)}
        given = {}
        for a in answers:
            card = cards.get(a["id"])
            if card is None:
                raise IdeasError("That question is not asked now")
            if got := idea_questions.answer_of(card, a):
                given[card["id"]] = got
        decide = args.get("decide") is True
        left = [c for i, c in cards.items() if i not in given]
        if left and not decide:
            raise IdeasError("Answer every question, or let the leaders decide")
        if not given and not decide:
            raise IdeasError("Answer at least one question")
        day, text = dt.date.today().isoformat(), page.section("Open questions")
        for i, c in cards.items():
            answer, how = given.get(i) or (idea_questions.default_of(c), "decide")
            text = idea_questions.with_answer(text, int(i[len(goal_phase.OUTSIDE_ID):]), answer, day, "the leader" if how == "decide" else "the person")
        ideas.set_section(self.root(), slug, "Open questions", text)
        self._ev(event_log.IDEA_ANSWERED, args, idea=slug, answers=len(given), decided=decide, talk=True, round=1, recommended=0,
                 picked=sum(1 for _a, h in given.values() if h == "pick"), typed=sum(1 for _a, h in given.values() if h == "text"))
        self._what[slug] = "answered"
        self.changed(slug)
        return {"ok": True}
