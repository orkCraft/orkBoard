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
    Hero("dry-sprint", "design", "Sprint Dryad", "Design sprint", "map → sketch → decide → test", "standard", 2, 1, layout="lanes",
         places=_p("Map", "What is the long-term goal, and where does the person's path start?",
                   "Sketch", "Which ideas did each of us sketch alone?",
                   "Decide", "Which sketch do we build, and who decided?",
                   "Test", "What did Play show of the sketch picked on the phone?"),
         framework="The design sprint: map the problem, sketch alone, decide on the phone, then try the sketch picked in Play",
         short="Design sprint",
         aspects=(_a("map", "Map", "Is the path from a person's start to the goal drawn?"),
                  _a("sketch", "Sketches", "Did each of us sketch alone before we talked?"),
                  _a("decision", "Decision", "Is the chosen sketch the one a clear vote picked?"),
                  _a("test", "Test", "Did Play show how the sketch picked works, and was it written down?"))),
    _default("sh-c4", "tech", "Sh.man", "C4 and hotspots", "containers → parts → hotspots", "standard", 2, 2),
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
    _default("imp-obs", "run", "Lantern Imp", "Observability first", "trace → read → fix", "standard", 2, 2),
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


CUT: dict[str, tuple[str, str]] = {                  # decisions §278.3: the heroes not taken, {id: (name, why)}
    "uni-lean": ("Pivot Knight", "no measure to pivot by: the project's analytics are not read"),
    "dry-diamond": ("Diamond Dryad", "full and dear, research there is none of, and its four steps are a goal's phases again"),
    "dry-atom": ("Atom Dryad", "only for a project with a component library of its own, and Consistency has no hint"),
    "sh-ddd": ("Domain Shaman", "an indie game's architecture is rewritten in an evening"),
    "sh-fit": ("Fitness Shaman", "fitness functions as records are later"),
    "imp-slo": ("Uptime Imp", "no server and no SLO: nothing gathered"),
}


def of(craft: str) -> list[Hero]:
    """The heroes of a craft, in the catalog's order; [] for a craft with none."""
    return [h for h in HEROES.values() if h.craft == craft]


def get(hero_id: str) -> Hero | None:
    """One hero by its id; None for none."""
    return HEROES.get(hero_id or "")


def default(craft: str) -> Hero | None:
    """The craft's default hero; None for a craft with none."""
    return next((h for h in HEROES.values() if h.craft == craft and h.default), None)


