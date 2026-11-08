"""Fixed Taskmaster and Grunt text shared by prompts and agent frames. Existing providers re-export their original names."""


TASKMASTER, GRUNT = "taskmaster", "grunt"


_FIXED = {
    TASKMASTER: "Each of its steps (reading a party, drafting a goal's spec, taking your answers, planning, the night's "
                "proposals) has its own prompt in Orkboard, with only what that step needs. What you write here goes "
                "before each step it runs; a party's leader, where it has one, runs that party's steps in its place.",
    GRUNT: "Every task's prompt says where it works (its own git worktree and branch), where the goal's spec is, its "
           "task and the tasks before it, the names of the secrets it may use, and that the gate then runs the critical "
           "tests and those of what it touched. Claude Code reads the project's CLAUDE.md itself. What you write here "
           "goes first.",
}


def rules(seat: str) -> str:
    """The rules of a built-in seat (spec 154 A.1): what Orkboard tells the Taskmaster (its plan) or a Grunt (its task) apart from each call's frame, which other modules build around it (the step's
    context, the task, the gate). An agent's frame (`seat_frames.agent("taskmaster", "plan")`, `("grunt", "task")`) holds this text. "" for any other slug."""
    return _FIXED.get(seat, "")

