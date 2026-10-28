// A party's size in *About this party* and *Edit the party* (docs/specs/81-a-party-its-tool-and-size.md §4.3, decisions §98): **Its size**, the three-way switch Lean · Standard · Full with each size's price a goal
// (`ideas.party_price` for the size's team and its tiers). The size is the team: the host gives the party the size's team and its seats' tiers in one save (a party of a recipe; a party of the library with no recipe
// keeps its team), so there is no *With its team* and no second confirm. Under the switch, before the press, **the heads that join and leave** for each other size (`ideas.party_sizes`: *Joins: …* / *Leaves: …*);
// a member with work open is not let go (spec 52's swap holds on the host too): *<Name> has work open: it cannot leave*, said in place. The field is controlled: About this party saves at once (`PartySize`),
// Edit the party sends `size` (and the team the size gave) with Save party.
// **`SizeBar`** (docs/specs/91-the-owners-list.md §7) is New party's and Edit the party's: the label *Size*, the switch Lean · Standard · Full — a press changes the seats and their tiers on the dialog at once
// (partydraft.js) — and a line saying what the size gives (*3 agents: the leader Veteran, the rest Seasoned · works as Balance*), with the party's own AI tool beside it (toolpick.js).
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { Head, Switch } from "../orkui.js";
import { board } from "../board/store.js";
import { mapData, refreshShell } from "./store.js";
import { SIZES, SIZE_TARGET, WorksAs, priceWords, proposalsOn } from "./proposals.js";
import { TARGETS } from "../board/target.js";
import { sizeWords } from "./partymodel.js";
import { ToolPick } from "./toolpick.js";

/** What each size would make of the party (`ideas.party_sizes`): {lean, standard, full: {team, joins, leaves}}, null while asked or refused. Asked again when the saved party changes. */
function useMoves(slug) {
  const [moves, setMoves] = useState(null);
  const g = (mapData.value?.goals || []).find((x) => x.slug === slug);
  const sig = JSON.stringify([slug, g?.size, (g?.party || []).map((m) => m.slug)]);
  useEffect(() => {
    if (!slug) return undefined;
    let live = true;
    command("ideas.party_sizes", { slug }, true).then((a) => { if (live && a?.sizes) setMoves(a.sizes); }).catch(() => {});
    return () => { live = false; };
  }, [sig]);
  return moves;
}

/** Each size's price for the party (`ideas.party_price` with `size`, on the team that size would have), asked again when the party or the moves change: {lean, standard, full} (null while asked or refused). */
function useSizePrices(on, leader, team, every, craft, moves) {
  const [prices, setPrices] = useState({});
  const key = JSON.stringify([on, leader, team, every, craft, SIZES.map(([s]) => moves?.[s]?.team)]);
  useEffect(() => {
    if (!on) return undefined;
    let live = true;
    Promise.all(SIZES.map(async ([size]) => {
      const t = moves?.[size]?.team || team;
      try {
        const got = await command("ideas.party_price", { leader, team: t, every: every.filter((id) => t.includes(id)), size, ...(craft ? { craft } : {}) });
        return [size, got && !got.error ? got : null];
      } catch { return [size, null]; }
    })).then((rows) => { if (live) setPrices(Object.fromEntries(rows)); });
    return () => { live = false; };
  }, [key]);
  return prices;
}

const names = (rows) => rows.map((a) => a.name).join(", ");

/** The heads that join or leave if a size is picked: *Lean · Leaves: Grunt, Artist* (the heads beside the names). Nothing for a size that changes no one. */
function Moves({ moves, size }) {
  const rows = SIZES.filter(([id]) => id !== size && (moves?.[id]?.joins?.length || moves?.[id]?.leaves?.length));
  if (!rows.length) return null;
  return html`<ul class="shell-size__moves" aria-label="Who joins and leaves">${rows.map(([id, word]) => html`<li key=${id} data-size-move=${id}><b>${word}</b>
    ${[["joins", "Joins"], ["leaves", "Leaves"]].map(([k, label]) => moves[id][k].length ? html`<span key=${k} class="shell-size__move" data-move=${k}>
      ${label}: <span class="shell-size__heads">${moves[id][k].map((a) => a.head && html`<${Head} key=${a.slug} race=${a.head.race} tier=${a.head.tier} title=${a.name} />`)}</span> ${names(moves[id][k])}</span>` : null)}</li>`)}</ul>`;
}

/** **Its size**. `size`: the party's ("" none yet); `onChange(to, team|null)`: the pick, with the team the size gives when it changes who is in the party (it may return a promise: a refusal rejects it and is said here);
 *  `working(id)`: the member has work open. */
export function SizeField({ slug, leader, team, every, craft = "", size, onChange, working = () => false, titled = true }) {
  const [note, setNote] = useState("");
  const moves = useMoves(slug);
  const prices = useSizePrices(proposalsOn(), leader, team, every, craft, moves);
  const pick = (to) => {
    const plan = moves?.[to];
    const busy = (plan?.leaves || []).filter((a) => working(a.slug));
    if (busy.length) { setNote(`${names(busy)} ${busy.length === 1 ? "has" : "have"} work open: ${busy.length === 1 ? "it cannot" : "they cannot"} leave`); return; }
    setNote("");
    const changes = plan && (plan.joins.length || plan.leaves.length);
    Promise.resolve(onChange(to, changes ? plan.team : null)).catch((e) => setNote(String(e?.message || e)));
  };
  const target = size ? (TARGETS.find(([id]) => id === SIZE_TARGET[size]) || TARGETS[1])[1] : (TARGETS.find(([id]) => id === (board.value?.target || "balance")) || TARGETS[1])[1];
  return html`<div class="shell-field shell-size" role="group" aria-label="Its size" data-size=${size}>${titled && html`<span class="ok-font-label">Its size</span>`}
    <${Switch} label="Size" options=${SIZES.map(([id, word]) => [id, word, priceWords(prices[id])])} value=${size} onPick=${pick} />
    ${size ? html`<${WorksAs} size=${size} />` : html`<small class="ok-tone-muted">No size of its own yet: it works as ${target}</small>`}
    <${Moves} moves=${moves} size=${size} />
    ${note && html`<p class="shell-size__note ok-font-status ok-tone-error" role="alert">${note}</p>`}
  </div>`;
}

/** In *About this party*: the field, saved at once in one press (`ideas.goal_save` with `size`: the host gives the party the size's team and tiers). */
export function PartySize({ slug, leader, team, every, craft, size, party }) {
  const track = (board.value?.tracks || []).find((t) => t.slug === slug);
  if (!proposalsOn() || !track) return null;
  const working = (id) => (party || []).some((m) => m.slug === id && m.band !== "lead" && m.state && m.state !== "free");
  const change = async (to) => {
    const got = await command("ideas.goal_save", { slug, about: track.about, priority: track.priority || "normal", size: to }, true);       // a refusal is said in place, not toasted
    if (got?.error) throw new Error(got.error);
    await refreshShell();
  };
  return html`<section class="shell-goal__sec" data-sec="size"><h3 class="board-sub">Its size</h3>
    <${SizeField} titled=${false} slug=${slug} leader=${leader} team=${team} every=${every} craft=${craft} size=${size} onChange=${change} working=${working} /></section>`;
}

export const sizeOf = (slug) => (mapData.value?.goals || []).find((g) => g.slug === slug)?.size || "";

/** New party's size bar (spec 91 §7): **Size**, the switch, what the size gives, and the party's **Its AI tool** (the seats' own are on their rows). `agents`: how many agents the party has now. */
export function SizeBar({ size, agents, onPick, note = "", tools = null, tool = "", onTool = () => {} }) {
  const works = size ? (TARGETS.find(([id]) => id === SIZE_TARGET[size]) || TARGETS[1])[1].toLowerCase() : "";
  return html`<div class="shell-sizebar" role="group" aria-label="Size" data-size=${size}>
    <div class="shell-sizebar__size"><span class="ok-font-label">Size</span>
      <${Switch} label="Size" options=${SIZES} value=${size} onPick=${onPick} />
      <small class="shell-sizebar__says ok-tone-muted">${size ? `${sizeWords(size, agents)} · works as ${works}` : "No size of its own yet"}</small>
      ${note && html`<p class="shell-size__note ok-font-status ok-tone-error" role="alert">${note}</p>`}</div>
    ${tools && html`<${ToolPick} tools=${tools} value=${tool} onChange=${onTool} />`}</div>`;
}
