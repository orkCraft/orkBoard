"""Pure hero catalog used by seat texts; rendering stays in heroes."""
from __future__ import annotations
from dataclasses import dataclass

SIZES = ("lean", "standard", "full")
LAYOUTS = ("lanes", "rows")
_FRAME = ("framework", "short", "aspects")        # a default hero's: its craft's rubric


@dataclass(frozen=True)
class Hero:
    id: str
    craft: str                     # a `lens_rubrics.RUBRICS` key
    name: str
    school: str
    flow: str
    size: str                      # lean, standard or full
    decides: int                   # 1-3: asks -> itself
    says_no: int                   # 1-3: seldom -> often
    default: bool = False
    layout: str = "lanes"          # lanes or rows
    places: tuple[tuple[str, str], ...] = ()
    framework: str = ""
    short: str = ""
    aspects: tuple[dict, ...] = ()

    def __getattribute__(self, name: str):
        if name in _FRAME and object.__getattribute__(self, "default"):
            from orkboard.realm import seat_rubric_rules as lens_rubrics
            r = lens_rubrics.RUBRICS.get(object.__getattribute__(self, "craft")) or {}
            return r.get(name, () if name == "aspects" else "")
        return object.__getattribute__(self, name)


def _p(*pairs: str) -> tuple[tuple[str, str], ...]:
    return tuple((pairs[i], pairs[i + 1]) for i in range(0, len(pairs), 2))


def _a(id_: str, name: str, ask: str) -> dict:
    return {"id": id_, "name": name, "ask": ask}


def _default(id_: str, craft: str, name: str, school: str, flow: str, size: str, decides: int, says_no: int) -> Hero:
    return Hero(id_, craft, name, school, flow, size, decides, says_no, default=True)


HEROES: dict[str, Hero] = {h.id: h for h in (
    _default("uni-ost", "product", "Angel Invest Knight", "Opportunity solution tree", "outcome → opportunities → solutions", "standard", 2, 2),
    Hero("uni-jtbd", "product", "Jobwise Knight", "Jobs to be done", "job → struggle → goal", "lean", 2, 1, layout="lanes",
         places=_p("The job", "What job does a person hire this product for?",
                   "Struggles", "What gets in the way of that job today?",
                   "Hired instead", "What do people hire instead, and why?",
                   "Our goals", "Which goal takes one struggle away?"),
         framework="Jobs to be done: the job a person hires the product for, the struggle in the way, and what they hire instead",
         short="Jobs to be done",
         aspects=(_a("job", "The job", "Is the job said in the person's words, free of any solution?"),
                  _a("struggle", "Struggles", "Is each struggle one that really stops the person from getting the job done?"),
                  _a("alternatives", "Hired instead", "Do we know what people hire today, even if it is a spreadsheet or nothing?"),
                  _a("progress", "Progress", "Does each goal make the person's progress on the job easier to see?"))),
    Hero("uni-lean", "product", "Pivot Knight", "Lean Startup", "hypothesis → test → pivot or persevere", "standard", 1, 3, layout="lanes",
         places=_p("Believe", "What do we believe is true that has not been tested?",
                   "Testing", "Which test is running, and what would prove the belief wrong?",
                   "Learned", "What did the last test teach us?",
                   "Decide", "Do we pivot or persevere, and on what evidence?"),
         framework="Lean Startup: a belief written as a hypothesis, the smallest test of it, what was learned, then pivot or persevere",
         short="Lean Startup",
         aspects=(_a("hypothesis", "Hypothesis", "Is each belief written so a test can prove it wrong?"),
                  _a("experiment", "Smallest test", "Is the test the smallest thing that could teach us?"),
                  _a("metric", "Metric", "Is the number that decides named before the test runs?"),
                  _a("learning", "Learning", "Is what was learned written down, and did it change what comes next?"),
                  _a("pivot", "Pivot or persevere", "Is the next step chosen by what was learned, not by hope?"))),
    Hero("uni-shape", "product", "Appetite Knight", "Shape Up", "shape → bet → build in the appetite", "lean", 3, 2, layout="lanes",
         places=_p("Pitches", "Which shaped pitch is worth betting on?",
                   "Bet this cycle", "What did we bet on, and how long may it take?",
                   "Not now", "What do we leave out for this cycle?",
                   "The hill", "Is the work still being figured out, or being done?"),
         framework="Shape Up: pitches shaped to an appetite, a bet on a few of them for one cycle, no backlog, and the hill from figuring out to making it happen",
         short="Shape Up",
         aspects=(_a("shaped", "Shaped", "Is the pitch rough enough to leave room, and solved enough to build?"),
                  _a("appetite", "Appetite", "Is the time we will spend said before the work starts?"),
                  _a("bet", "The bet", "Is each bet small enough to finish in one cycle?"),
                  _a("hill", "The hill", "Is each piece uphill (figuring out) or downhill (making it), and said so?"))),
    _default("dry-heur", "design", "Pixel-Perfect Dryad", "Nielsen's heuristics", "walk → the ten rules → fix", "standard", 2, 2),
    Hero("dry-diamond", "design", "Diamond Dryad", "Double Diamond", "discover → define → develop → deliver", "full", 1, 2, layout="lanes",
         places=_p("Discover", "What did we learn about the people and their problem?",
                   "Define", "Which one problem do we solve?",
                   "Develop", "Which ways could solve it, and which did we try?",
                   "Deliver", "Which solution is built and checked?"),
         framework="The Double Diamond: open wide and then narrow twice, first to the right problem (discover, define), then to the right solution (develop, deliver)",
         short="Double Diamond",
         aspects=(_a("discover", "Discover", "Did we look at the people before we picked a problem?"),
                  _a("define", "Define", "Is the problem said in one sentence everyone agrees on?"),
                  _a("develop", "Develop", "Did we draw more than one way before choosing?"),
                  _a("deliver", "Deliver", "Was the chosen way tested with people before it shipped?"))),
    Hero("dry-atom", "design", "Atom Dryad", "Atomic design", "tokens → parts → screen", "lean", 3, 3, layout="rows",
         places=_p("Tokens", "Which colours, sizes and type does everything draw from?",
                   "Atoms", "Which smallest parts (a button, a field) are there?",
                   "Molecules", "Which atoms make one small working group?",
                   "Organisms", "Which groups make one section of a screen?",
                   "Screens", "Which screens are made only of these parts?"),
         framework="Atomic design: tokens, then atoms, molecules, organisms and screens, each made only of the level below it",
         short="Atomic design",
         aspects=(_a("tokens", "Tokens", "Does every colour, size and font come from a token?"),
                  _a("atoms", "Atoms", "Is each smallest part made once and reused?"),
                  _a("molecules", "Molecules", "Does each group do one job?"),
                  _a("organisms", "Organisms", "Is each section built from the groups, not from loose parts?"),
                  _a("screens", "Screens", "Does a screen use only parts the system has?"))),
    Hero("dry-sprint", "design", "Sprint Dryad", "Design sprint", "map → sketch → decide → test", "standard", 2, 1, layout="lanes",
         places=_p("Map", "What is the long-term goal, and where does the person's path start?",
                   "Sketch", "Which ideas did each of us sketch alone?",
                   "Decide", "Which sketch do we build, and who decided?",
                   "Prototype", "What is the fake that looks real enough to test?",
                   "Test", "What did five people say and do?"),
         framework="The design sprint: in a week, map the problem, sketch alone, decide, build a prototype and test it with five people",
         short="Design sprint",
         aspects=(_a("map", "Map", "Is the path from a person's start to the goal drawn?"),
                  _a("sketch", "Sketches", "Did each of us sketch alone before we talked?"),
                  _a("decision", "Decision", "Is the chosen sketch the one a clear vote picked?"),
                  _a("prototype", "Prototype", "Is the prototype real enough to test and no more?"),
                  _a("test", "Test", "Did we watch five people use it and write down what they did?"))),
    _default("sh-c4", "tech", "Sh.man", "C4 and hotspots", "containers → parts → hotspots", "standard", 2, 2),
    Hero("sh-ddd", "tech", "Domain Shaman", "Domain-driven design", "words → borders → code", "full", 1, 3, layout="lanes",
         places=_p("Contexts", "Which parts of the product have their own words and rules?",
                   "Links", "How does one context talk to another?",
                   "The words", "Which words mean one thing here, and what is it?"),
         framework="Domain-driven design: one shared language, bounded contexts with clear borders, and code that uses the language's words",
         short="Domain-driven design",
         aspects=(_a("language", "Shared language", "Do the code and the people use the same word for the same thing?"),
                  _a("contexts", "Contexts", "Does each context have its own borders and its own meaning for a word?"),
                  _a("links", "Links", "Is each link between contexts one-way and said how it translates?"),
                  _a("core", "Core", "Is the part that makes the product special kept apart and given the best care?"))),
    Hero("sh-xp", "tech", "Spike Shaman", "Extreme programming", "test → code → refactor", "standard", 3, 2, layout="lanes",
         places=_p("Red", "Which test fails, written before its code?",
                   "Green", "What is the least code that makes it pass?",
                   "Refactor", "What can be cleaned up while the tests stay green?",
                   "Released small", "Which small step is already in main?"),
         framework="Extreme programming: a failing test first, the least code to pass it, refactoring while green, and small releases often",
         short="Extreme programming",
         aspects=(_a("test_first", "Test first", "Is each change begun with a test that fails?"),
                  _a("simple", "Simple design", "Is this the simplest code that passes, with nothing for later?"),
                  _a("refactor", "Refactoring", "Is the code cleaned each time the tests go green?"),
                  _a("small_releases", "Small releases", "Does each step reach main small and often?"),
                  _a("integration", "Integration", "Does the whole build and test run after every change?"))),
    Hero("sh-fit", "tech", "Fitness Shaman", "Evolutionary architecture", "fitness → change → check", "full", 2, 3, layout="lanes",
         places=_p("The fitness functions", "Which automatic check says the design is still healthy?",
                   "Breaking", "Which check fails now, and why?",
                   "Checked changes", "Which change was made and then passed every check?"),
         framework="Evolutionary architecture: fitness functions that check the design automatically, so each change is guided and checked as it is made",
         short="Evolutionary architecture",
         aspects=(_a("fitness", "Fitness functions", "Is each quality we care about measured by an automatic check?"),
                  _a("guided", "Guided change", "Does each change say which check it must keep green?"),
                  _a("incremental", "Small steps", "Is each change small enough to check on its own?"),
                  _a("coupling", "Coupling", "Can a part change without the checks of others failing?"))),
    _default("imp-slo", "run", "Uptime Imp", "SLOs and error budgets", "objective → budget → alert", "lean", 2, 3),
    Hero("imp-obs", "run", "Lantern Imp", "Observability first", "trace → read → fix", "standard", 2, 2, layout="lanes",
         places=_p("Slow traces", "Which request takes longer than it should?",
                   "Errors", "Which error happens most, and for whom?",
                   "Read", "What do the traces and logs say is the cause?",
                   "Fixed", "Which fix is out, and did the trace get better?"),
         framework="Observability first: read what the running product tells you (traces, logs, metrics) before you guess, then fix and look again",
         short="Observability",
         aspects=(_a("traces", "Traces", "Can one request be followed from the person's press to the answer?"),
                  _a("logs", "Logs", "Do the logs say what happened, with enough to find it again?"),
                  _a("metrics", "Metrics", "Are the numbers that show health watched where people can see them?"),
                  _a("questions", "Questions", "Can we ask a new question of the running product without a new release?"))),
    _default("fairy-aarrr", "marketing", "Growth Hack Gnome", "AARRR", "acquire → activate → retain", "standard", 2, 2),
    Hero("fairy-aso", "marketing", "Store Gnome", "The store page first", "title → shots → test", "lean", 3, 1, layout="lanes",
         places=_p("The title", "Does the title say what it is and who it is for?",
                   "The shots", "Does each screenshot show a reason to install?",
                   "The words", "Does the description lead with what the person gets?",
                   "Tests", "Which store page variant is being tried, and what moved?"),
         framework="The store page first: the title, the shots and the words of the store page are the first marketing, and each is tested",
         short="Store page",
         aspects=(_a("title", "Title", "Does the title say what it is, within the store's limits?"),
                  _a("shots", "Screenshots", "Do the first screenshots show the best reason to install?"),
                  _a("words", "Description", "Do the first lines say what the person gets?"),
                  _a("tests", "Tests", "Is a change to the page tried against the old one before it stays?"))),
    _default("release", "release", "Release Night King", "DORA's keys, readiness and semver", "dev → the gate → main", "standard", 1, 3),
)}


def of(craft: str) -> list[Hero]:
    """The heroes of a craft, in the catalog's order; [] for a craft with none."""
    return [h for h in HEROES.values() if h.craft == craft]


def get(hero_id: str) -> Hero | None:
    """One hero by its id; None for none."""
    return HEROES.get(hero_id or "")


def default(craft: str) -> Hero | None:
    """The craft's default hero; None for a craft with none."""
    return next((h for h in HEROES.values() if h.craft == craft and h.default), None)


