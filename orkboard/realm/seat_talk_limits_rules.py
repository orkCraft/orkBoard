"""Authoritative limits for Talk rules and answer parsing. Existing providers re-export their original names."""


MAX_GOAL = 3                       # a leader's questions about the goal, at most


MAX_PROJECT = 2                    # … and about the project, at most (a bug's Tech: one it cannot do without)


LINE = 200                         # a stance, a for, an against



MAX_NEEDS = 3                      # what a leader says needs the person's answer (a risk, a conflict, a question), at most (spec 168 C1, decisions §283.23)


MAX_WAYS = 3                       # … each with at most this many ways out


MAX_BETTER = 3                     # what a leader says would make the goal better, at most


NEED_KINDS = ("risk", "conflict", "question")          # what a need is


WEIGHTS = ("lighter", "same", "heavier")               # how an improvement weighs against the goal as it stands
