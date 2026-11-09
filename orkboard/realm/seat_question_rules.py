"""Question way-line text and its authoritative length limit. Existing providers re-export their original names."""

from orkboard.realm.way_kinds import KINDS_RULE

LINE_CHARS = 80                  # a way's own line (spec 159), at most


LINES_RULE = (f"`lines` is one line for each way, in the ways' order: what that way leads to, its point in its first words, {LINE_CHARS} characters at most so it fits "
              "under the way's name on its card, never the `why` said again; give a line for every way or none. " + KINDS_RULE)      # the one rule every place that tells a leader how to ask says (spec 159 C, §270.2, §270.5)

