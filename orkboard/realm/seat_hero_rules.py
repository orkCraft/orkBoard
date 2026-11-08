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
    also: tuple[str, ...] = ()     # the other crafts it sits at (decisions §279.1: Pillar Knight at Game design too)
    kinds: tuple[str, ...] = ()    # the project kinds it is offered in; empty is every kind
    not_here: str = ""             # its why, in words, where it is not offered

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


def _default(id_: str, craft: str, name: str, school: str, flow: str, size: str, decides: int, says_no: int, **more) -> Hero:
    return Hero(id_, craft, name, school, flow, size, decides, says_no, default=True, **more)


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
    Hero("uni-pillar", "product", "Pillar Knight", "Design pillars", "pillars → the goal against them → keep or cut", "lean", 3, 2, layout="lanes",
         also=("game-design",),
         places=_p("Pillars", "What must it always be? (the brief's pillars)",
                   "Leaves out", "What does it leave out on purpose? (the brief's leaves out)",
                   "Against them", "Which goal goes against a pillar?",
                   "Keep or cut", "Is the goal kept or cut, and why?"),
         framework="Design pillars: the few things the product must always be, what it leaves out on purpose, and each goal weighed against them to be kept or cut",
         short="Design pillars",
         aspects=(_a("pillars", "Pillars", "Are the pillars few and said in the brief, so a goal can be weighed against them?"),
                  _a("leaves_out", "Leaves out", "Is what the product leaves out on purpose said in the brief?"),
                  _a("against", "Against them", "Does any goal in line go against a pillar?"),
                  _a("keep_cut", "Keep or cut", "Is each goal that goes against a pillar kept or cut, and the why written?"))),
    _default("dry-heur", "design", "Pixel-Perfect Dryad", "Nielsen's heuristics", "walk → the ten rules → fix", "standard", 2, 2,
         kinds=('empty', 'mobile', 'game', 'web', 'design'), not_here='Pixel-Perfect Dryad walks screens: this project has no screens to walk'),
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
                  _a("test", "Test", "Did Play show how the sketch picked works, and was it written down?")),
         kinds=('empty', 'mobile', 'game', 'web', 'design'), not_here='Sprint Dryad sketches and tries screens in Play: this project has no screens'),
    Hero("dry-a11y", "design", "Inclusive Dryad", "WCAG 2.2", "barriers → contrast and keys → fix", "standard", 2, 2, layout="lanes",
         places=_p("Barriers", "Who is stopped, and on which screen?",
                   "Contrast and keys", "Which text or control fails contrast, a key or a label?",
                   "Fixed", "Which barrier is gone, seen again?"),
         framework="WCAG 2.2: the barriers that stop a person on a screen, contrast, keys and labels, fixed and looked at again",
         short="WCAG 2.2",
         aspects=(_a("barriers", "Barriers", "Is each screen a person can be stopped on named, with who is stopped?"),
                  _a("contrast", "Contrast and keys", "Do text and controls pass contrast, and have a key and a label?"),
                  _a("fixed", "Fixed", "Is each fixed barrier looked at again on its screen?"),
                  _a("labels", "Labels", "Does each control have a label a screen reader can say?")),
         kinds=('empty', 'mobile', 'game', 'web', 'design'), not_here='Inclusive Dryad reads screens for barriers: this project has no screens'),
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
    Hero("sh-scene", "tech", "Scene Shaman", "An engine's scenes", "scene → autoloads → coupling", "standard", 2, 2, layout="lanes",
         places=_p("Scenes", "Which scenes does the game hold, and what is in each?",
                   "Autoloads", "Which autoloads or singletons does every scene reach?",
                   "Coupling", "Which scene needs another's insides to work?"),
         framework="An engine's scenes: the scenes a game is built of, the autoloads they all reach, and how tightly one scene is tied to another",
         short="Scenes",
         aspects=(_a("scenes", "Scenes", "Is each scene one thing, small enough to open and understand?"),
                  _a("autoloads", "Autoloads", "Is each autoload needed by many scenes, and does it hold no more than it must?"),
                  _a("coupling", "Coupling", "Can a scene run alone, or does it reach into another's nodes?"),
                  _a("shared", "Shared state", "Is state that many scenes share kept in one place, and said?")),
         kinds=('game',), not_here="Scene Shaman reads an engine's scenes: this project is not a game"),
    _default("imp-obs", "run", "Lantern Imp", "Observability first", "trace → read → fix", "standard", 2, 2),
    _default("fairy-aarrr", "marketing", "Growth Hack Gnome", "AARRR", "acquire → activate → retain", "standard", 2, 2),
    Hero("fairy-pos", "marketing", "Position Gnome", "Positioning", "the alternatives → what only it does → who cares", "lean", 3, 1, layout="lanes",
         places=_p("The alternatives", "What do people use now instead? (the brief's why this, not what they use now)",
                   "What only it does", "What does it do that the alternatives do not?",
                   "Who cares", "Who cares most about that, and how do we know?"),
         framework="Positioning: the alternatives people use now, what only this product does, and who cares most about that",
         short="Positioning",
         aspects=(_a("alternatives", "The alternatives", "Is what people use instead said in the brief?"),
                  _a("unique", "What only it does", "Is what only this product does said plainly, apart from the alternatives?"),
                  _a("who", "Who cares", "Is the person who cares most about that named?"),
                  _a("said", "Said", "Does the store page or the brief say the position in a line?"))),
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
                  _a("tests", "Tests", "Is a change to the page tried against the old one before it stays?")),
         kinds=('mobile', 'web', 'game'), not_here='Store Gnome works on a store page: this project has none'),
    _default("uni-mda", "game-design", "Dungeon Master Knight", "MDA and the loops", "loop → reward → hook", "standard", 2, 2),
    Hero("uni-econ", "game-design", "Economy Knight", "Sources and sinks", "currency → source → sink", "lean", 2, 2, layout="lanes",
         places=_p("Currencies", "Which currencies does the game have?",
                   "Sources", "Where does each currency come from?",
                   "Sinks", "Where does each currency go, so it does not pile up?"),
         framework="Sources and sinks: every currency of the game, where it comes from and where it goes",
         short="Sources and sinks",
         aspects=(_a("currencies", "Currencies", "Is every currency of the game named?"),
                  _a("sources", "Sources", "Does every currency have a source?"),
                  _a("sinks", "Sinks", "Does every currency have a sink, so none piles up?"),
                  _a("balance", "Balance", "Does what comes in roughly match what goes out over a session?"))),
    _default("dry-sprite", "art", "Sprite Dryad", "An art bible, its pipeline and a budget", "style → pipeline → budget", "standard", 2, 2),
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

STARS: dict[str, tuple[str, ...]] = {                # decisions §278.5, §279.4: the Orkmaster's star by the project's kind (marks a ware on the shelf, seats nothing: §281.1)
    "game": ("uni-mda", "dry-sprite", "sh-scene", "fairy-pos"),
    "web": ("uni-ost", "dry-heur", "sh-xp", "fairy-aso"),
    "mobile": ("uni-ost", "dry-heur", "sh-xp", "fairy-aso"),
}


def sits_at(hero: Hero, craft: str) -> bool:
    """Whether a hero sits at a craft: its own, or one of its `also`."""
    return hero.craft == craft or craft in hero.also


def of(craft: str) -> list[Hero]:
    """The heroes of a craft: its default first, then its own in the catalog's order, then those that sit there by `also`; [] for a craft with none."""
    own = [h for h in HEROES.values() if h.craft == craft]
    own.sort(key=lambda h: not h.default)
    return own + [h for h in HEROES.values() if h.craft != craft and craft in h.also]


def get(hero_id: str) -> Hero | None:
    """One hero by its id; None for none."""
    return HEROES.get(hero_id or "")


def default(craft: str) -> Hero | None:
    """The craft's default hero; None for a craft with none."""
    return next((h for h in HEROES.values() if h.craft == craft and h.default), None)


