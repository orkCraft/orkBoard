"""Pure shared rules for a leader's spec section."""
from orkboard.realm import seat_section_limits_rules as spec_sections

WHY_FREE = "- `why`: why this matters for your craft, two or three lines."


WHY_CAUSE = "- `why`: the cause above, in your words."


def rules(*, why: str = WHY_FREE, sketched: str = "", prop: tuple[str, str] = ("", "")) -> str:
    """A leader's rules for its section (spec 154 A.1): the section's parts and their limits, the lines under *Rules:*, apart from the call's frame. The same for every craft. `instruction` and an
    agent's frame (`seat_frames.agent("<craft>-leader", "section", craft)`) both hold this text; a call adds the `why` rule of its goal, the sketch's rule and a slice it may propose."""
    return f"""{why}
- `done_when`: one to {spec_sections.MAX_DONE} scenarios, each one line `When <a person or the product does something>, then <what is seen or kept>`, checkable by a test and proving your party's part is done, never a task. A line about a screen names the state it opens in, as a person first meets it.
  Each line says how it is proven, as `{{"line": "…", "proof": "test"}}`: `test` when a test the gate runs can prove it, `look` when only a picture or Play shows it (a screen's state, a sound), `person` when only the person can judge it (a word's tone, a price). `test` for a line about what a person sees only when its test opens the screen in the state the line names, as a person first meets it; else `look`. Prefer `test` for the rest.
- `checks`: up to {spec_sections.MAX_CHECKS} things your party's checkers verify, apart from the theses.
- `will_be`: one line a part of your map the work changes — `new <part id>`, `changed <part id>` or `gone <part id>`, the id as your map names it (its path), then a short why after a dash. None where \
your party has no map.{sketched}
- `out`: up to {spec_sections.MAX_OUT} things your section does not do. `risks`: up to {spec_sections.MAX_RISKS}. `risk`: low, medium or high.
- Ask nothing more: where you are unsure, decide, and say what you assumed in `assumed` (up to {spec_sections.MAX_ASSUMED} lines).{prop[0]}"""

