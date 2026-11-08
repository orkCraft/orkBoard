"""Craft lenses for Talk verdicts, using the pure default rubric catalog. Existing providers re-export their original names."""
from orkboard.realm import seat_rubric_rules as lens_rubrics

LENS = {"product": "the goals in line and the product's aim: is this worth doing before them, now, and the open hypotheses: is this goal built on one no one has tested?",
        "tech": "the architecture on your map: does it add a caller, a cycle or a part that is already too big",
        "design": "the people's way through the screens: does it add a step, a screen or a look that gets in their way",
        "game-design": "the loop and its economy: does it break a step or a currency, or pad the loop",
        "art": "the look the product keeps: does it add art or a style the rest will not carry",
        "run": "what is live: does it add a thing to watch or to keep running that nobody will",
        "liveops": "what is live: does it add a thing to watch or to keep running that nobody will",
        "marketing": "the way in: does it reach the people who come, or only add to what is said",
        "release": "what goes to main: does it make a release harder to cut or to take back"}


def lens(craft: str) -> str:
    """What the leader of a party of this craft judges a goal against (the spec's per-craft lens); what its party keeps, for a craft that has none. It ends with the framework a senior of the craft
    reviews by when the craft has a rubric (`realm/lens_rubrics.py`, spec 109 §2.4), so a verdict in Talk judges by the frame of the leader's look."""
    r = lens_rubrics.RUBRICS.get(craft)
    return LENS.get(craft, "what your party keeps") + (f", as a senior of it would: by {r['framework']}" if r else "")

