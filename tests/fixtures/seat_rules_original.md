`seat_rules_original.json.gz` contains complete strings captured from the original
implementation before extraction in this task. JSON preserves whitespace and final
newlines; gzip only reduces storage size. Tests read this baseline and never write it.

`tests/seat_rule_cases.py` enumerates both Talk rounds and every on/off combination
of optional rules across crafts, section why/sketch/proposal variants, join context,
acceptance reads/context/round/line variants, role texts, and seat frames with default
and custom paths. Existing `prompts_151` fixtures additionally cover assembled workflow
prompts from repository context.
