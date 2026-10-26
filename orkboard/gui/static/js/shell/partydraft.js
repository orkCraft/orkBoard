// The party New party and Edit the party are making (docs/specs/91-the-owners-list.md §7): its leader, its team, its size, its AI tool and each seat's. One hook holds it and
// every change the dialog makes — a preset pressed, a size picked, a seat taken out or put in, a tool picked for a seat — so the seats and their tiers follow at once (partymodel.js).
// `rec` is the candidates of the seats, the builders and the checkers most needed first: a preset's, then what the person put in or took out; a size seats the first of them (Lean none,
// Standard the first builder, Full the first builder and the first checker). `pool` is the preset's own candidates, which a free seat's list offers first. A seat changed by hand ends the preset (`lit`): the party is then the person's own.
import { useState } from "preact/hooks";
import { TASKMASTER, agentOf, pitchParty } from "./party.js";
import { recOf, seatsOf, sizedTeam, tiersFor } from "./partymodel.js";

const bandOf = (id) => agentOf(id)?.band || "build";

/** `init`: {leader, team, every, size, tool, tools, title, lit, rec}. Returns the state and what changes it. */
export function usePartyDraft(init) {
  const [d, setD] = useState(() => ({ leader: init.leader || TASKMASTER, team: [...(init.team || [])], every: [...(init.every || [])], size: init.size ?? "", tool: init.tool || "", seatTools: { ...(init.tools || {}) },
    lit: init.lit || "", row: init.row || null, partyId: "", craft: init.craft || "", rec: init.rec || recOf(init.team || []), pool: init.rec || recOf(init.team || []), moved: false }));
  const set = (patch) => setD((was) => ({ ...was, ...(typeof patch === "function" ? patch(was) : patch) }));
  const seats = (leader, team) => seatsOf(leader, team);
  /** Seats that left take their tools and their `every` with them. */
  const kept = (leader, team, was) => ({ every: was.every.filter((id) => team.includes(id)), seatTools: Object.fromEntries(Object.entries(was.seatTools).filter(([a]) => a === leader || team.includes(a))) });
  const api = {
    d,
    set,
    /** A preset pressed: its leader and its candidates, the team of the size picked. */
    preset: (p, ifFresh = false) => set((was) => {
      if (ifFresh && (was.lit || was.moved || was.partyId)) return {};                       // the person pressed one meanwhile: theirs stays
      const leader = p.leader || TASKMASTER, rec = { build: [...(p.build || [])], check: [...(p.check || [])] };
      const have = pitchParty(leader) && !was.size ? { build: rec.build.length, check: rec.check.length } : seats(leader, []);       // Ideation with no size is its views and the Skeptic whole
      const team = sizedTeam(rec, was.size, have);
      return { leader, rec, pool: rec, team, every: [], seatTools: {}, lit: p.id, row: p, craft: p.craft || "", partyId: "" };
    }),
    /** A saved party of the person's (Your parties): its seats as they are, whatever the size. */
    own: (p) => set((was) => {
      const leader = p.leader || TASKMASTER, team = [...p.team];
      return { leader, team, rec: recOf(team), pool: recOf(team), every: [...p.every], seatTools: {}, lit: "", row: null, craft: p.craft || "", partyId: p.id, size: was.size };
    }),
    /** A size picked: the seats and the tiers change at once. */
    size: (size) => set((was) => {
      const team = sizedTeam(was.rec, size, seats(was.leader, []));
      return { size, team, ...kept(was.leader, team, was), partyId: JSON.stringify(team) === JSON.stringify(was.team) ? was.partyId : "" };       // a saved party's seats changed by the size are no longer that party's
    }),
    /** A member put into a band: a leader takes the leading seat (the Taskmaster leads when none). */
    add: (band, id) => set((was) => {
      if (band === "lead") return { leader: id, lit: "", row: null, partyId: "", moved: true };
      const team = [...was.team.filter((s) => s !== id), id], mine = team.filter((s) => bandOf(s) === band);
      return { team, rec: { ...was.rec, [band]: mine }, lit: "", row: null, partyId: "", moved: true };
    }),
    /** A member taken out of its seat (the leader: the Taskmaster leads again). */
    remove: (id) => set((was) => {
      if (id === was.leader) return { leader: TASKMASTER, ...kept(TASKMASTER, was.team, was), lit: "", row: null, partyId: "", moved: true };
      const team = was.team.filter((s) => s !== id), band = bandOf(id);
      return { team, rec: { ...was.rec, [band]: team.filter((s) => bandOf(s) === band) }, ...kept(was.leader, team, { ...was, team }), lit: "", row: null, partyId: "", moved: true };
    }),
    seatTool: (id, tool) => set((was) => ({ seatTools: tool ? { ...was.seatTools, [id]: tool } : Object.fromEntries(Object.entries(was.seatTools).filter(([a]) => a !== id)) })),
    setEvery: (every) => set({ every, lit: "", row: null, partyId: "" }),
    /** Whether a band is full: no seat is free to put a member in. */
    full: (band) => {
      const mine = band === "lead" ? [d.leader].filter((x) => x !== TASKMASTER) : d.team.filter((s) => bandOf(s) === band);
      return mine.length >= seats(d.leader, d.team)[band];
    },
    fixed: pitchParty(d.leader),
  };
  api.tiers = tiersFor(d.leader, d.team, d.size);
  return api;
}
