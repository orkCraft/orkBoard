// What a slot's card and its ways' cards share (docs/specs/168 H1, decisions §283.30; the look: docs/mockups/table-template/ scenes `inventory` and `leader-inventory`): the picture in a card's window (the owner's where orkUI has it, slotpics.js; else
// the kind's sign), the pips of a slot's ways, the price in words. The page never makes a price: it says what the host sent (`{mine}`, `{locked}`, `{money}`, `{share}`, `{word}`).
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { Mark } from "./stallfaces.js";
import { pictureOf } from "./slotpics.js";

if (typeof document !== "undefined") {
  const href = new URL("./slots.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** A way's picture: the owner's file where orkUI has one, else a hero's or a tier's head in the party's race, else the slot's sign. `race`: the party leader's race, "" for the Orkmaster's chair. */
export function SlotPic({ slot, w, race = "" }) {
  const url = pictureOf(slot, w.id);
  const inside = url ? html`<img class="slot-pic__img" src=${url} alt="" loading="lazy" decoding="async" draggable="false" />`
    : slot === "hero" && w.head ? html`<${Head} race=${w.head.race} tier=${w.head.tier} size="big" />`
    : slot === "tier" && race ? html`<${Head} race=${race} tier=${w.id || "warrior"} size="big" />`
    : html`<${Mark} slot=${slot} id=${w.id} race=${race} />`;
  return html`<span class=${cls("slot-pic", { "has-picture": !!url })} data-pic=${url ? "picture" : "sign"} aria-hidden="true">${inside}</span>`;
}

/** The pips of a slot's ways, the one carried lit. */
export function Pips({ n, at }) {
  return html`<span class="slot-pips" aria-hidden="true">${Array.from({ length: n }, (_, i) => html`<i key=${i} class=${i === at ? "is-on" : ""}></i>`)}</span>`;
}

/** A way's price in words, for the bottom right of its card: `{text, kind}`, or null for what is carried (it says *Yours* at its top) and for what has no price. */
export function priceWords(price) {
  if (!price || price.mine) return null;
  if (price.locked) return { text: "not here", kind: "locked", why: price.locked };
  if (price.money) return { text: price.money, kind: "money" };
  if (Number.isFinite(price.share)) return price.share === 0 ? { text: "same cost", kind: "same" } : { text: `${price.share > 0 ? "+" : "−"}${Math.abs(price.share)}% a week`, kind: price.share < 0 ? "less" : "more" };
  if (price.word) return { text: price.word, kind: { lighter: "less", heavier: "more", "same cost": "same" }[price.word] || "same" };
  return null;
}
