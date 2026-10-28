// The Orkmaster's proposals on the desktop (docs/specs/75-parties-fitted-to-the-project.md §5.1–§5.2, decisions §90; docs/specs/91-the-owners-list.md §7, §8): the words and the host's asking. The Orkmaster's
// *Parties* row (arena/projectrows.js) shows the proposals first, *Add* opens New party on one (`openOver("party", {proposal})`) and New party (goalwizard.js, partyform.js) takes it as a stage of the project with its
// seats and its size switch (Lean · Standard · Full, partysize.js). A host that does not send `project.kind` has no proposals: New party is today's.
import { html } from "../html.js";
import { command, toast } from "../link.js";
import { pctRange } from "../spend.js";
import { mapData } from "./store.js";
import { closePlace } from "../frame/place.js";
import { openTab } from "../frame/state.js";
import { TARGETS } from "../board/target.js";

export const SIZES = [["lean", "Lean"], ["standard", "Standard"], ["full", "Full"]];
export const SIZE_WORD = Object.fromEntries(SIZES);
/** What a size works as, the Target's words (board/target.js `TARGETS`): Lean works as Thrift, Standard as Balance, Full as Quality. */
export const SIZE_TARGET = { lean: "thrift", standard: "balance", full: "quality" };

/** The host sends the Orkmaster's reading of the project (spec 75 §4.3): only then New party opens on proposals. */
export const proposalsOn = () => !!mapData.value?.project?.kind;

/** *Works as Balance: the default…*: what a size does to the party's goals, in the Target's words. */
export function WorksAs({ size }) {
  const [, word, line] = TARGETS.find(([id]) => id === SIZE_TARGET[size]) || TARGETS[1];
  return html`<small class="shell-size__works ok-tone-muted">Works as ${word}: ${line}</small>`;
}

export const agentsWords = (n) => (n === 1 ? "one agent" : `${n} agents`);

/** *≈$0.40–1.20 a goal*; on the subscription its share of the window, *≈3–8 % of 5h a goal*. */
export function priceWords(price) {
  if (!price) return "";
  const { low, high } = price, pct = pctRange(low, high);
  if (pct) return `≈${pct} a goal`;
  if (low < 1) return `≈$${low.toFixed(2)}–${high.toFixed(2)} a goal`;
  const a = Math.round(low), b = Math.round(high);
  return a === b ? `≈$${a} a goal` : `≈$${a}–${b} a goal`;
}

/** `ideas.proposals` ({about?}): its answer, or null (an older host, a refusal — said once by `command`). */
export async function askProposals(about = "") {
  try {
    const got = await command("ideas.proposals", about ? { about } : {});
    return got && !got.error && Array.isArray(got.proposals) ? got : null;
  } catch { return null; }
}

/** A party is saved (New party's Save party): the place closes and the party's own tab opens (the person made it). */
export function savedParty(got) {
  for (const note of got.notes || []) toast(note);       // an agent of the project's own that the party carries stays as it was
  closePlace();
  openTab(got.slug);
}
