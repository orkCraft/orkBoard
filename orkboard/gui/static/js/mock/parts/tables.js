// The leaders' tables' part of the mock (goal 170): a framework's cards, the contract proposed as `ideas.tables` (the host does not answer it yet).
// tools/record_tables.py writes `static/mock/tables.json` (Tech's architecture read from this repository's code; Product's jobs to be done
// proposed: this repository has no personas, so each is an example, marked as such); this lays it as `data.proposed.tables` and as that reply.
import { EXAMPLE, ensure } from "./kit.js";

const mark = (x) => (x && !x.endsWith(EXAMPLE) ? x + EXAMPLE : x);

/** The personas, the job's words, the smaller jobs, hired and fired are examples: their titles say so. */
function markJobs(j) {
  for (const x of [...j.personas, ...j.jobs, ...j.fired, j.hired]) x.title = mark(x.title);
  j.job.so = mark(j.job.so);
}

export async function lay(data) {
  const r = await fetch("/static/mock/tables.json");
  if (!r.ok) return;
  const rec = await r.json();
  for (const party of Object.values(rec.tables)) if (party.jtbd) markJobs(party.jtbd);
  data.proposed = { ...(data.proposed || {}), tables: rec.tables };
  ensure(data, "ideas.tables", rec.tables);
}
