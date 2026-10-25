// A party's size in *About this party* and *Edit the party* (docs/specs/75-parties-fitted-to-the-project.md §5.4): **Its size**, the three-way switch Lean · Standard · Full with each size's price a goal
// (`ideas.party_price` for the size's team and Target), and **With its team**: the size's team as well — Lean empties it, Standard keeps the leader's first two builders and first checker, Full the whole
// recipe's (the host's proposal for this leader when it has one, else the party's own members). A member leaves only after *Its members leave the party* is confirmed, and never while it has work open
// (spec 52's swap holds on the host too). The field is controlled: About this party saves at once (`PartySize`), Edit the party sends `size` (and the team) with Save party.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { Switch } from "../orkui.js";
import { board } from "../board/store.js";
import { act, mapData } from "./store.js";
import { TASKMASTER, agentOf, inBand } from "./party.js";
import { SIZES, SIZE_WORD, SIZE_TARGET, WorksAs, askProposals, priceWords, proposalsOn } from "./proposals.js";
import { TARGETS } from "../board/target.js";

/** The team a size has for this leader: the host's proposal for the leader when one is known, else the party's own members cut to the size (it cannot grow past them). */
export function teamFor(size, leader, team, proposals = []) {
  const p = proposals.find((x) => x.sizes?.standard?.leader === leader);
  if (p?.sizes?.[size]) return [...p.sizes[size].team];
  if (size === "lean") return [];
  if (size === "full") return [...team];
  return [...inBand("build", leader, team).slice(0, 2), ...inBand("check", leader, team).slice(0, 1)];
}

/** Each size's price for the party (`ideas.party_price` with `size`), asked again when the party or the team option changes: {lean, standard, full} (null while asked or refused). */
function useSizePrices(on, leader, team, every, craft, withTeam, proposals) {
  const [prices, setPrices] = useState({});
  const key = JSON.stringify([on, leader, team, every, craft, withTeam, proposals.length]);
  useEffect(() => {
    if (!on) return undefined;
    let live = true;
    Promise.all(SIZES.map(async ([size]) => {
      const t = withTeam ? teamFor(size, leader, team, proposals) : team;
      try {
        const got = await command("ideas.party_price", { leader, team: t, every: every.filter((id) => t.includes(id)), size, ...(craft ? { craft } : {}) });
        return [size, got && !got.error ? got : null];
      } catch { return [size, null]; }
    })).then((rows) => { if (live) setPrices(Object.fromEntries(rows)); });
    return () => { live = false; };
  }, [key]);
  return prices;
}

const names = (ids) => ids.map((id) => agentOf(id)?.name || id).join(", ");

/** **Its size**. `size`: the party's ("" none yet); `onChange(size, team|null)`: the pick, with the size's team when *With its team* is ticked; `working(id)`: the member has work open. */
export function SizeField({ leader, team, every, craft = "", size, onChange, working = () => false, titled = true }) {
  const [withTeam, setWithTeam] = useState(false);
  const [asking, setAsking] = useState(null);          // {size, next, leaving}: the pick that waits for *Its members leave the party*
  const [note, setNote] = useState("");
  const [proposals, setProposals] = useState([]);
  const prices = useSizePrices(proposalsOn(), leader, team, every, craft, withTeam, proposals);
  useEffect(() => { if (withTeam && !proposals.length) askProposals().then((a) => setProposals(a?.proposals || [])); }, [withTeam]);
  const pick = (to, confirmed = false) => {
    setNote("");
    if (!withTeam) { setAsking(null); onChange(to, null); return; }
    const next = teamFor(to, leader, team, proposals), leaving = team.filter((id) => !next.includes(id));
    const busy = leaving.filter(working);
    if (busy.length) { setAsking(null); setNote(`${names(busy)} ${busy.length === 1 ? "has" : "have"} work open: ${busy.length === 1 ? "it cannot" : "they cannot"} leave`); return; }
    if (leaving.length && !confirmed) { setAsking({ size: to, next, leaving }); return; }
    setAsking(null);
    onChange(to, next);
  };
  const target = size ? (TARGETS.find(([id]) => id === SIZE_TARGET[size]) || TARGETS[1])[1] : (TARGETS.find(([id]) => id === (board.value?.target || "balance")) || TARGETS[1])[1];
  return html`<div class="shell-field shell-size" role="group" aria-label="Its size" data-size=${size}>${titled && html`<span class="ok-font-label">Its size</span>`}
    <${Switch} label="Size" options=${SIZES.map(([id, word]) => [id, word, priceWords(prices[id])])} value=${size} onPick=${(id) => pick(id)} />
    ${size ? html`<${WorksAs} size=${size} />` : html`<small class="ok-tone-muted">No size of its own yet: it works as ${target}</small>`}
    ${leader !== TASKMASTER || team.length > 0 ? html`<label class="ok-check shell-size__team">
      <input type="checkbox" class="gui-onb__hide" checked=${withTeam} onChange=${(e) => { setWithTeam(e.target.checked); setAsking(null); setNote(""); }} />
      <i>${withTeam ? "✓" : ""}</i><span>With its team</span></label>` : null}
    ${note && html`<p class="shell-size__note ok-font-status ok-tone-error" role="alert">${note}</p>`}
    ${asking && html`<p class="shell-size__ask" role="alert">Its members leave the party: ${names(asking.leaving)}.
      <button type="button" class="ork-btn primary" onClick=${() => pick(asking.size, true)}>Make it ${SIZE_WORD[asking.size]}</button>
      <button type="button" class="ork-btn" onClick=${() => setAsking(null)}>Keep them</button></p>`}
  </div>`;
}

/** In *About this party*: the field, saved at once (`ideas.goal_save` with `size`, and the leader, team and checks when the team goes with it). */
export function PartySize({ slug, leader, team, every, craft, size, party }) {
  const track = (board.value?.tracks || []).find((t) => t.slug === slug);
  if (!proposalsOn() || !track) return null;
  const working = (id) => (party || []).some((m) => m.slug === id && m.band !== "lead" && m.state && m.state !== "free");
  const change = (to, next) => act("ideas.goal_save", { slug, about: track.about, priority: track.priority || "normal", size: to,
    ...(next ? { leader, team: next, every: every.filter((id) => next.includes(id)) } : {}) });
  return html`<section class="shell-goal__sec" data-sec="size"><h3 class="board-sub">Its size</h3>
    <${SizeField} titled=${false} leader=${leader} team=${team} every=${every} craft=${craft} size=${size} onChange=${change} working=${working} /></section>`;
}

export const sizeOf = (slug) => (mapData.value?.goals || []).find((g) => g.slug === slug)?.size || "";
