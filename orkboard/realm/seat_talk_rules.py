"""Pure shared Talk rules; core owns the call frame and workflow."""
from orkboard.realm import seat_question_rules as idea_questions, seat_lens_rules as idea_objections
from orkboard.realm.seat_talk_limits_rules import LINE, MAX_BETTER, MAX_GOAL, MAX_NEEDS, MAX_PROJECT, MAX_WAYS
from orkboard.realm.idea_words import CARD_RULE

CARDS = ("Each question is a card for the person: two to four real choices taken from what the project holds (a container, a screen, a fact above), never from what is "
         "common and never padded to fill four; `pick` is the index of the one you recommend and `why` says why in one line; `blocks` is true only when your party "
         "cannot start its work without the answer. " + idea_questions.LINES_RULE + " Ask nothing the goal's words, your map or the facts above already answer.")


AFTER_RULE = "\n- `after` (with a `no` only, optional): the slug of one goal in line above that this goal should wait for; else leave it out."


def project_rules(tail: str = "") -> tuple[str, str]:
    """`(rule, json)` of a party's first goal in the project: its questions about the project itself. `tail`: the keys already answered, said."""
    return (f"\n- This is your party's first goal in this project: also ask at most {MAX_PROJECT} questions about the project itself that your party cannot work "
            f"without and no fact above answers (`project_questions`: each with a `key`, a lowercase name of one to forty letters, digits and underscores, e.g. "
            f"stack or runs_on).{tail}",
            ',\n "project_questions": [{"key": "stack", "ask": "…", "choices": ["…", "…"], "pick": 0, "why": "…", "lines": ["…", "…"], "blocks": false}]')


def rules(craft: str = "", *, mine: str = "your party", second: bool = False, for_rule: str = "", project: tuple[str, str] = ("", ""), after: tuple[str, str] = ("", ""),
          weight: tuple[str, str] = ("", ""), prop: tuple[str, str] = ("", ""), again: tuple[str, str] = ("", "")) -> str:
    """A leader's rules in Talk (spec 154 A.1): what it judges and how, apart from the call's frame. The lines under *Rules:* of the first round; of the `second` round, the sentence of what it asks.
    Called with the call's words (`mine` and the rules only some calls add: `for_rule`, `project`, `after`, `weight`, `prop`, `again`, each `(rule, json)`) it is exactly what `instruction` holds;
    an agent's frame (`seat_frames.agent("<craft>-leader", "talk", craft)`) holds the text with none."""
    cards = CARDS + for_rule
    if second:
        return f"""Ask only what these answers open and your party cannot start without: at most {MAX_GOAL} questions, none if the answers leave nothing open. {CARD_RULE} Each question's `ask` is its title, at most seven words; its `why` is its line. {cards}{again[0]}"""
    return f"""- {CARD_RULE} Each question's `ask` is its title, at most seven words; its `why` is its line.
- `stance`, `for` and `against` are one line each, {LINE} characters at most: where your party stands, what speaks for the goal, what against.
- You are not here to agree. Judge the goal as the one who answers for {mine}, against {idea_objections.lens(craft)}. `verdict` is `go`, `doubt` or `no`. \
Say `no` when it is not worth its cost now or harms what your party keeps; say it plainly in `why` (one line, {LINE} characters at most) with the part, the goal in line or the fact \
it rests on: a no without one is not a no. `doubt` is for a goal you would do only if something changed: `why` says what. `why` is needed for a `doubt` and a `no`; without it your \
verdict reads as `go`. A `doubt` that reading the code would settle says what to look up in `check` (a name, a file, a question of one line); else leave `check` empty. \
A worse thing than a needless goal is one you let through in silence.
- `instead` (optional, one line): a smaller or different goal that would serve, when you can name one.{after[0]}
- If this goal rests on something no one has shown, say it in `assumes`: `{{"text": "what it rests on", "signal": "what would show it"}}`, a line each, {LINE} characters at most; else leave it out.
- Ask at most {MAX_GOAL} questions about the goal. {cards}{project[0]}{weight[0]}{prop[0]}
- `needs` (at most {MAX_NEEDS}, optional): what the person must settle that no fact above settles. Each has a `kind` (`risk`, `conflict` or `question`), a `line` ({LINE} characters at most), what it \
`rests_on` (the slug of a goal in line or in the pile above, a `§N` of a decision above, or the id of a part of your map) and at most {MAX_WAYS} `ways`, each `{{"name": "…", "line": "…"}}`: a way out and what it does to the goal.
- `better` (at most {MAX_BETTER}, optional): a line of the goal rewritten so that it serves your party better, each `{{"line": "…", "weight": "same"}}`, `weight` being `lighter`, `same` or `heavier`: the work it makes against the goal as it stands.
- `second_round` is true only when the answers to your questions may open a question your party cannot start without; else false."""

