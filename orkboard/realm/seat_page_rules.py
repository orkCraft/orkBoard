"""Page section names and answer marker used by text providers. Existing providers re-export their original names."""
import re

SECTIONS = ("Gist", "Why", "Done when", "Out", "Risks", "Depends on", "Stages", "Open questions", "Decisions")   # spec 35 §3


ANSWERED = re.compile(r"^[ \t]+[-*+][ \t]+Answered:[ \t]*(.*?)\s*$")     # a question's answer, the line under it (spec 151 A.6: realm/idea_questions.py)

