// Tech's table: the architecture (docs/mockups/frameworks/, ?f=arch), laid from the code (tools/record_tables.py): layers from the
// outside in, a card lying on the one it needs; a pile of a package is spread on press to its biggest modules; the rules it keeps with
// their tests; Tech's own risk token on a module that reaches up. Pressed, a module turns over to what it needs and how big it is.
import { useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { Token } from "../card.js";
import { placed } from "./state.js";
import { TCard, TPile, YouToken } from "./parts.js";

const SIGN = { ext: "link", frame: "page", pile: "work", mod: "work" };

/** What a card says behind it: its size, what it needs (a package's imports), the rule it is past. */
function backOf(c, limit) {
  const needs = Object.entries(c.needs || {}).map(([k, v]) => `${k}/ ×${v}`).join(", ");
  return [c.lines ? `${c.lines.toLocaleString("en")} lines${c.modules ? ` in ${c.modules} modules` : ""}` : "", needs ? `needs ${needs}` : "needs nothing of the package",
    c.past ? `past the ~${limit} a module may grow to` : "", c.imports?.length ? `imports ${c.imports.join(", ")}` : ""].filter(Boolean);
}

function Pile({ ctx, c, open, toggle, limit }) {
  return html`<${TPile} ctx=${ctx} id=${c.id} title=${c.title} line=${c.line} n=${Math.min(5, Math.max(2, Math.round(Math.log10(c.lines || 10))))} open=${open} onSpread=${toggle} mono=${true}
    kind="top" count=${`${c.modules} modules · ${c.lines.toLocaleString("en")} lines`} />`;
}

function Spread({ ctx, c, risk, limit }) {
  return html`<div class="tb-spread" data-spread=${c.id}><p class="tb-colh">${c.title} spread <i>· its biggest</i></p>
    <div class="tb-fan">${c.biggest.map((m, i) => html`<${TCard} key=${m.id} ctx=${ctx} id=${m.id} title=${m.title} line=${m.line} size="sm" kind=${m.past ? "stray" : "mod"} mono=${true}
      tilt=${[-5, -2, 1, 4][i % 4]} back=${backOf(m, limit)} />`)}</div></div>`;
}

/** Tech's table. `ctx`: {party, framework, race}; `data`: the architecture the record holds. */
export function Architecture({ ctx, data }) {
  const [open, setOpen] = useState({}), flip = (id) => setOpen({ ...open, [id]: !open[id] }), risks = new Set((data.tech_tokens || []).map((t) => t.card));
  const sent = placed.value.filter((t) => t.party === ctx.party && t.framework === ctx.framework);
  return html`<div class="tb-arch">
    <div class="tb-layers">${data.layers.map((l) => html`<section key=${l.id} class=${cls("tb-layer", { "has-spread": l.cards.some((c) => c.kind === "pile" && open[c.id]) })} data-layer=${l.id}>
      <span class="tb-ln">${l.name}<i>${l.line}</i></span>
      ${l.cards.map((c) => (c.kind === "pile" ? html`<${Pile} key=${c.id} ctx=${ctx} c=${c} open=${!!open[c.id]} toggle=${() => flip(c.id)} limit=${data.limit} />`
        : html`<${TCard} key=${c.id} ctx=${ctx} id=${c.id} title=${c.title} line=${c.line} kind=${c.kind} size=${c.kind === "ext" ? "wide" : "md"} sign=${SIGN[c.kind] || "work"} mono=${c.kind !== "ext"}
          back=${c.kind === "ext" ? ["Orkline is the line; Orkboard is the Board on its own.", "Orkboard starts with no module of Orkline's."] : backOf(c, data.limit)} />`))}
      ${(l.stray || []).map((s) => html`<${TCard} key=${s.id} ctx=${ctx} id=${s.id} title=${s.title} line=${s.line} kind="stray" size="md" tilt=${8} mono=${true} back=${backOf(s, data.limit)}
        tokens=${risks.has(s.id) ? [{ leader: ctx.party, view: "risk" }] : []} />`)}
      ${l.cards.filter((c) => c.kind === "pile" && open[c.id]).map((c) => html`<${Spread} key=${c.id} ctx=${ctx} c=${c} limit=${data.limit} />`)}
    </section>`)}</div>
    <aside class="tb-rules" aria-label="The rules it keeps"><p class="tb-colh">The rules it keeps</p>
      ${data.rules.map((r, i) => html`<p key=${i} class="tb-rule" data-view=${r.view}><${Token} leader=${ctx.party} view=${r.view} word=" " /><span>${r.text}<small>${r.where}</small></span></p>`)}
      ${sent.map((t, i) => html`<p key=${`s${i}`} class="tb-rule tb-sent" data-sent=${t.view}><${YouToken} view=${t.view} /><span><b>Your ${t.view} to ${ctx.leader}</b> · on <i>${t.name}</i>${t.text ? html`: “${t.text}”` : ""}<small>sent ${new Date(t.at).toTimeString().slice(0, 5)}</small></span></p>`)}
      <p class="tb-legend">A card lying on another needs it; a pile spread shows its biggest.</p></aside>
  </div>`;
}
