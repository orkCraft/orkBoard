// The new chair deals its crafts (docs/specs/160-the-tables-look-and-the-rooms-things.md stage I, decisions §272, §274.1, §160.6; the mockup docs/mockups/room-things/ mode `chair`). On the desktop (760 px and over) the chair at the tabs' end,
// pressed, is lit and the Orkmaster's question rises onto the table as the 144 x 202 card of a question (*A new chair at the table · Which craft sits in it?*, hand/answercards.js' mechanism and classes, not bent): the hand holds a card for each craft
// of the project's kind not seated yet (`ideas.party_presets` of group `stage`, the stage's reached first, Release among them while it is not seated): its race's head as its sign, its name (the pixel face), its whole line, and its price in the
// corner and in words (`ideas.party_price`, said as every card's cost: hand/waycost.js; with no price the card says so). The Orkmaster's pick, when a preset says one (`pick`, `recommended` or `default`), is starred and named in words; the host
// says none today, so none is starred and none invented. The rest of the hand sinks (hand.js). A craft's card pressed seats it by `ideas.goal_save` as the parties' place does (table/parties.js), then the backpack opens on its chair; *Put it back*,
// Esc and any tab pressed send nothing. The narrow page and the phone keep the parties' place (*New party*).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Chair, Head, Sign } from "../orkui.js";
import { command } from "../link.js";
import { ask, board } from "../board/store.js";
import { currentProject } from "../shell/projects.js";
import { refreshShell } from "../shell/store.js";
import { inventory, openInventory, openTab, over, tab } from "../frame/state.js";
import { CornerFoot, CornerTop, muchOf } from "../table/corners.js";
import { madeFrom } from "../table/parties.js";
import { headOf } from "../table/partyseats2.js";
import { wayCostOf } from "./waycost.js";

/** Whether the chair's deal is up. */
export const dealing = signal(false);
export const QUESTION = "A new chair at the table", QUESTION_LINE = "Which craft sits in it?", PICK_WORDS = "the Orkmaster's pick", NO_PRICE = "no price yet";
const STAGES = ["idea", "being_made", "live"];

/** Opens the deal, or puts it away. */
export const dealCrafts = (on = !dealing.peek()) => { dealing.value = on; };

/** The Orkmaster's pick among the presets: what a preset says of itself (`pick`, `recommended`, `default`); false when it says nothing. */
export const pickOf = (p) => !!(p.pick || p.recommended || p.default);

/** The crafts not seated yet, with their prices: `crafts` null while asked; `price[id]` undefined while asked, `false` when the host has none. */
function useCrafts() {
  const project = currentProject.value?.path || "", tracks = (board.value?.tracks || []).filter((t) => t.slug !== "general");
  const [got, setGot] = useState(null), [price, setPrice] = useState({});
  useEffect(() => {
    let live = true;
    Promise.all([command("ideas.party_presets", {}, true), command("ideas.stage", {}, true).catch(() => null)]).then(([r, st]) => {
      if (live) setGot({ presets: (r?.presets || []).filter((p) => p && p.group === "stage"), stage: st?.stage || "" });
    }).catch(() => { if (live) setGot({ presets: [], stage: "" }); });
    return () => { live = false; };
  }, [project]);
  const open = got ? got.presets.filter((p) => !madeFrom(p, tracks)) : null;
  const reached = open && got.stage ? open.filter((p) => STAGES.indexOf(p.stage) <= STAGES.indexOf(got.stage)) : open;
  const crafts = open && (reached.length ? reached : open), sig = (crafts || []).map((p) => p.id).join("|");
  useEffect(() => {
    if (!crafts) return undefined;
    let live = true;
    for (const p of crafts) {
      command("ideas.party_price", { leader: p.leader, team: p.squad || [], every: [], size: p.size }, true)
        .then((a) => { if (live) setPrice((was) => ({ ...was, [p.id]: a && !a.error && Number.isFinite(Number(a.low)) ? { low: a.low, high: a.high } : false })); })
        .catch(() => { if (live) setPrice((was) => ({ ...was, [p.id]: false })); });
    }
    return () => { live = false; };
  }, [sig]);
  return { crafts, price };
}

/** The right edge of `el` from the left of `root`, by layout and not by paint: the sunk hand is scaled, and a rect measured while it shrinks would move the cards. */
function rightIn(el, root) {
  let x = el.offsetWidth, at = el;
  while (at && at !== root) { x += at.offsetLeft; at = at.offsetParent; }
  return at === root ? x : root.offsetWidth;
}

/** One craft as a hand card: its race's head at the top right, its name, its whole line, its price in words and in the corner, and, when it is the Orkmaster's pick, a star and the words. */
function CraftCard({ p, price, orkmaster, onSeat }) {
  const head = headOf({ p }, p.leader, p.size), pick = pickOf(p), cost = price ? wayCostOf({ usd_low: price.low, usd_high: price.high }) : null;
  const much = cost ? { ...muchOf({ cost: cost.gem }), share: !!cost.share } : null, said = price === undefined ? "" : cost ? cost.words : NO_PRICE;
  return html`<button type="button" class=${cls("ork-card hand-ans hand-craft", { "is-pick": pick })} data-craft=${p.id} data-pick=${pick ? "1" : undefined} data-price=${cost ? cost.gem : price === undefined ? undefined : "none"}
      aria-label=${`${p.name}${pick ? `, ${PICK_WORDS}` : ""}: ${p.line}${said ? `. ${said}` : ""}`} title=${p.line} onClick=${() => onSeat(p)}>
    <${CornerTop} runeNode=${pick ? html`<span class="hand-craft__star" data-star="1" aria-hidden="true">★</span>` : null} kindNode=${html`<${Head} race=${head.race} tier=${head.tier} title=${p.name} />`} />
    <span class="hand-ans__name">${p.name}</span>
    <span class="hand-ans__line">${p.line}</span>
    ${pick && html`<span class="hand-craft__pick" data-pick-words="1">${PICK_WORDS}</span>`}
    <span class="hand-craft__price" data-said="1">${said}</span>
    <${CornerFoot} who=${pick ? { heads: [orkmaster], word: "" } : null} much=${much} />
  </button>`;
}

/** The deal: the Orkmaster's question risen over the ways' row, and the crafts in the hand's row. */
export function ChairDeal() {
  const box = useRef(), row = useRef(), busy = useRef(false), [at, setAt] = useState(null), { crafts, price } = useCrafts(), orkmaster = { race: "peon", tier: "crown" };
  const was = useRef([tab.peek(), inventory.peek(), over.peek()]);
  useLayoutEffect(() => {                                              // the question over the first craft; the sunk hand shrinks into the strip right of the row
    const place = () => {
      const hand = box.current?.parentElement, r = row.current?.getBoundingClientRect();
      if (!hand) { setAt(null); return; }
      const h = hand.getBoundingClientRect(), plus = hand.querySelector(".hand-plus"), ways = Math.max(0, plus ? rightIn(plus, hand) + 28 : 200);
      const end = r && r.width ? r.right - h.left : h.width;
      hand.style.setProperty("--hc-sunk-s", String(Math.max(0.2, Math.min(0.5, (h.width - end - 16) / h.width))));
      setAt({ ways });
    };
    place();
    const watch = typeof ResizeObserver === "function" && row.current ? new ResizeObserver(place) : null;
    watch?.observe(row.current);
    window.addEventListener("resize", place);
    return () => { watch?.disconnect(); window.removeEventListener("resize", place); box.current?.parentElement?.style.removeProperty("--hc-sunk-s"); };
  }, [crafts?.length]);
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, []);
  useEffect(() => {                                                    // Esc puts it back and the focus goes back to the chair
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); dealCrafts(false); } };
    addEventListener("keydown", esc);
    return () => { removeEventListener("keydown", esc); setTimeout(() => document.querySelector(".table-chair")?.focus?.({ preventScroll: true }), 0); };
  }, []);
  useEffect(() => {                                                    // another tab, the backpack or a thing over the pane puts it back
    const [t, i, o] = was.current;
    if (t !== tab.value || i !== inventory.value || o !== over.value) dealCrafts(false);
  }, [tab.value, inventory.value, over.value]);
  const seat = async (p) => {
    if (busy.current) return;
    busy.current = true;
    const got = await ask("ideas.goal_save", { title: p.name, about: p.line, leader: p.leader, team: p.squad || [], every: [], size: p.size, preset: p.id });      // as the parties' place makes a party ticked
    if (!got) { busy.current = false; return; }
    await refreshShell();
    const slug = got.slug || madeFrom(p, (board.value?.tracks || []).filter((t) => t.slug !== "general"))?.slug || "";
    dealing.value = false;
    if (slug) { openTab(slug); openInventory(slug); }                                                    // its tab where the chair stood, the backpack on its chair
  };
  return html`<aside ref=${box} class="ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked asks" role="dialog" tabindex="-1" aria-label=${`Lifted: ${QUESTION}`} data-chair-deal="question" style=${at ? `left:${at.ways}px` : undefined}>
    <${CornerTop} runeNode=${html`<${Chair} empty=${true} small=${true} />`} kindNode=${html`<${Sign} name="question" />`} signal="alert" />
    <span class="hand-card__name" title=${QUESTION}>${QUESTION}</span>
    <span class="hand-card__foot">${QUESTION_LINE}</span>
    <${CornerFoot} who=${{ heads: [orkmaster], word: "" }} />
  </aside>
  <div ref=${row} class="hand-ways-row hand-crafts" role="group" aria-label="Crafts" data-chair-deal="crafts" style=${at ? `--hc-wleft:${at.ways}px` : undefined}>
    <div class="hand-ways-cards">
      ${crafts === null ? html`<p class="hand-crafts__wait ok-tone-muted">Looking at the table…</p>` : crafts.map((p) => html`<${CraftCard} key=${p.id} p=${p} price=${price[p.id]} orkmaster=${orkmaster} onSeat=${seat} />`)}
      ${crafts && !crafts.length && html`<p class="hand-crafts__wait ok-tone-muted">Every craft sits at the table.</p>`}
    </div>
    <div class="hand-ways-acts"><button type="button" class="ork-btn hand-put" data-act="put" onClick=${() => dealCrafts(false)}>Put it back</button></div>
  </div>`;
}
