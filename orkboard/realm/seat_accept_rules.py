"""Pure shared acceptance rules and limits, also used by core validation."""

ROUNDS = 2                        # a step goes back twice at most (the third look only accepts, or leaves what is left as findings)


BACK_MAX = 4                      # items a leader sends back in one look


LINE_CHARS = 200                  # an item's `what` and `where`


LEARNED_MAX = 2                   # lines a leader keeps of what it learned


def rules() -> str:
    """A leader's rules for accepting a step (spec 154 A.1): the lines met / not met / cannot see, what it sends back and what it learns; the lines under *Rules:*, apart from the call's frame. The same for
    every craft. `instruction` and an agent's frame (`seat_frames.agent("<craft>-leader", "accept", craft)`) both hold this text."""
    return f"""- Judge each *Done when* line by its number (a line code has decided is not yours; code's `unseen` stands): `met` true (it is so), false (it is not) or "unseen" (you cannot see it: a picture or Play it needs is not there, or only the person can judge it).
  Never say true for a line you could not look at. `why` is one line.
- `back`: at most {BACK_MAX} things that must change, each one line of at most {LINE_CHARS} characters (`what`), where (`where`), the task it is in (`task`: its id, or "") and the *Done when* line it fails
  (`done_when`: its number, or 0). Send back only what your section promised and the step missed; send nothing back for a line you cannot see.
- `learned`: up to {LEARNED_MAX} lines you keep of your party's work from this step, or none.
- Invent nothing the words above and the files do not show."""

