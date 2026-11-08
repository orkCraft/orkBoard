"""Pure shared Orkmaster section join rules and limits."""

MAX_FORKS, SAYS_CHARS, ABOUT_CHARS, GIST_CHARS = 3, 240, 200, 200

def join_rules() -> str:
    """The Orkmaster's rules for the join of the sections (spec 154 A.1): the lines under *Rules:*."""
    return f"""- `gist`: one line, {GIST_CHARS} characters at most, what the goal is once its parties' parts are put together.
- A fork is only where two sections say things that cannot both hold (a number, an order, a choice of one thing over another); a difference of detail or of craft is no fork. \
Each side is a party's id from above, what it `says` in its own words and its `why`. At most {MAX_FORKS} forks; none where the sections agree."""

