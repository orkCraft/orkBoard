// The Orkmaster's ready parties (docs/specs/70-orkmaster-and-the-project.md §3, §4.1; docs/specs/91-the-owners-list.md §8): what the *Parties* row of the project's level offers beside *New party* — the parties
// that suit this kind of project and the project does not have yet, in the host's order (`ideas.map` `project.deal`: Release first when flags wait and no party releases them, Ideation next when none judges pitches,
// the ones the project has last). With the Orkmaster's reading of the project (spec 75 §5.3, `ideas.map` `project.kind`) they are first its proposals (`ideas.proposals`), then the library's.
// Pure words and a hook: projectrows.js draws them, and *Add* opens New party on one (`openDialog("goal", {proposal | preset})`, as the pile's card did).
import { useEffect, useState } from "preact/hooks";
import { agentOf, presetsOf, raceOfAgent } from "../shell/party.js";
import { askProposals, proposalsOn } from "../shell/proposals.js";
import { whyWords } from "./projectwords.js";

/** The ready parties in the deal's order (the proposals' ids first; one the deal lacks goes first), each `{id, name, line, lead: {race, tier, name}, size, have, open}`: `open` is the props
 *  New party opens with (`{proposal}` or `{preset}`). `deal`: `project.deal`; `proposals`: `ideas.proposals`'; `presets` the library's. */
export function dealCards(deal, proposals, presets = presetsOf()) {
  const byId = new Map(proposals.map((p) => [p.id, p])), seen = new Set(), out = [];
  const ofProposal = (p) => {
    const std = p.sizes?.standard, lead = std?.heads?.[0], who = agentOf(std?.leader);
    return { id: p.id, name: p.name, line: p.line, why: p.why || "", lead: lead ? { race: lead.race, tier: lead.tier, name: who?.name || "" } : null, size: std ? Math.max(0, (std.agents || 1) - 1) : 0,
      have: !!p.have, open: { proposal: p.id } };
  };
  const ofPreset = (p, entry) => {
    const lead = agentOf(p.lead);
    return { id: p.id, name: p.name, line: p.line, why: whyWords(entry), lead: { race: lead ? raceOfAgent(lead) : p.race, tier: lead?.tier || "elder", name: lead?.name || "" },
      size: (p.build || []).length + (p.check || []).length, have: entry?.why === "have", open: { preset: p.id } };
  };
  for (const p of proposals) if (!deal.some((e) => e.id === p.id)) { out.push(ofProposal(p)); seen.add(p.id); }
  for (const e of deal) {
    if (seen.has(e.id)) continue;
    seen.add(e.id);
    if (byId.has(e.id)) out.push(ofProposal(byId.get(e.id)));
    else if (presets.some((p) => p.id === e.id)) out.push(ofPreset(presets.find((p) => p.id === e.id), e));
  }
  return out;
}

/** The two or three ready parties for the *Parties* row: the dealt ones the project does not have, the first three. */
export const READY = 3;
export const readyParties = (deal, proposals, presets) => dealCards(deal, proposals, presets).filter((c) => !c.have).slice(0, READY);

/** The Orkmaster's proposals (`ideas.proposals`) for a host that reads the project, [] meanwhile and for a host that does not; asked again when the Board's deal changes. */
export function useProposals(key = "") {
  const [got, setGot] = useState([]), reads = proposalsOn();
  useEffect(() => {
    if (!reads) { setGot([]); return undefined; }
    let live = true;
    askProposals().then((a) => { if (live) setGot(a?.proposals || []); });
    return () => { live = false; };
  }, [reads, key]);
  return got;
}
