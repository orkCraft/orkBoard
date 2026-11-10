// The stall's faces (docs/specs/157-the-inventory-a-merchants-stall.md D.2, the mockup docs/mockups/merchant/): a hero's face (head, name, school, the stats' bars), a relic (a small ware: a tool, a tier, a setting's way) and the
// price plate under each. The plate says only what the host sent: `{mine}`, `{locked}`, `{word}`, `{share}`, `{money}`; no number is made here.
import { html, cls } from "../html.js";
import { Head, Icon, Sign } from "../orkui.js";
import { MARKED, markSrc } from "./data.js";

/** The lock: a few pixels in the ink, crisp. */
export function Lock() {
  return html`<svg class="stall-lock" viewBox="0 0 7 8" aria-hidden="true"><path class="stall-lock__body" d="M2 0h3v1H2zM1 1h1v2H1zM5 1h1v2H5zM0 3h7v5H0z" /><path class="stall-lock__hole" d="M3 5h1v2H3z" /></svg>`;
}

const Vial = () => html`<span class="ork-potion size-vial" style="--ork-potion-left:.7" aria-hidden="true"></span>`;

/** The plate: what the ware adds to the first potion's week, or what it is. */
export function Plate({ price }) {
  if (!price) return null;
  if (price.mine) return html`<span class="stall-price is-mine" data-price="mine">in your hand</span>`;
  if (price.locked) return html`<span class="stall-price is-same" data-price="locked" title=${price.locked}><${Lock} />not here</span>`;
  if (price.money) return html`<span class="stall-price is-money" data-price="money" title=${price.money}><${Icon} name="coins" />${price.money}</span>`;
  if (Number.isFinite(price.share)) {
    const n = price.share;
    if (!n) return html`<span class="stall-price is-same" data-price="same">same cost</span>`;
    return html`<span class=${cls("stall-price", { "is-less": n < 0 })} data-price="share" title=${n > 0 ? `about ${n}% more of the first potion's week` : `saves about ${-n}% of the first potion's week`}><${Vial} />${n > 0 ? `+${n}%` : `−${-n}%`}</span>`;
  }
  if (price.word) {
    const kind = { lighter: "is-less", "same cost": "is-same" }[price.word] || "";
    return html`<span class=${cls("stall-price", kind)} data-price="word" title=${{ lighter: "Lighter than what you carry", heavier: "Heavier than what you carry", "one pass": "One pass of its leader", "same cost": "Costs what yours costs" }[price.word] || undefined}>${price.word}</span>`;
  }
  return null;
}

const bar = (n) => html`<span class="stall-pips">${[1, 2, 3].map((i) => html`<i key=${i} class=${i <= n ? "on" : ""}></i>`)}</span>`;
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : "");

/** A hero's face: its head, its name, its school and the stats the host gave (flow, size, how much it decides, how often it says no). */
export function HeroFace({ w, fallback = null }) {
  const h = w.head || fallback, s = w.stats || {};
  return html`<div class="stall-face stall-hero">
    ${w.star && html`<span class="ork-sign pick stall-hero__star" role="img" aria-label="The Orkmaster's pick" title="The Orkmaster's pick"></span>`}
    ${h && html`<span class="stall-hero__head"><${Head} race=${h.race} tier=${h.tier} size="big" /></span>`}
    <span class="stall-hero__name">${w.word}</span><span class="stall-hero__school">${s.school || w.line}</span>
    ${w.stats && html`<div class="stall-stats"><span>Flow</span><b>${s.flow}</b><span>Size</span><b>${cap(s.size)}</b>
      <span>Decides</span><span class="stall-bar"><span>asks</span>${bar(s.decides)}<span>itself</span></span>
      <span>Says no</span><span class="stall-bar"><span>seldom</span>${bar(s.says_no)}<span>often</span></span></div>`}
  </div>`;
}

const ICONS = { target: "sliders", look_wait: "clock", autostart: "play", build_start: "clock", review: "check", max_parallel: "list-box", push: "git-merge", tool: "robot", hero: "flag", tier: "sliders" };

/** The mark of a small thing: a tier's head in its party's race, a tool's mark, the moon of the night, else the slot's icon. `id` the value (a ware's id, or what a card carries). */
export function Mark({ slot, id, race }) {
  if (slot === "tier" && race && id) return html`<${Head} race=${race} tier=${id} />`;
  if (slot === "tool" && MARKED.includes(id)) return html`<img class="ork-mark" src=${markSrc(id)} srcset=${`${markSrc(id, true)} 2x`} alt="" draggable="false" />`;
  if (slot === "work_at_night" || slot === "night") return html`<${Sign} name="moon" />`;
  return html`<${Icon} name=${ICONS[slot] || "sliders"} />`;
}

/** A relic: a small ware, its mark above its word; its line is its title. */
export function Relic({ w, slot, race }) {
  if (slot === "craft_tools") return html`<div class="stall-face stall-relic stall-maker"><${Sign} name=${w.makes === "pictures" ? "picture" : "sound"} /><span class="stall-relic__word">${w.word}</span><span class="stall-maker__service">${w.title}</span></div>`;
  return html`<div class="stall-face stall-relic" title=${w.line || undefined}><${Mark} slot=${slot} id=${w.id} race=${race} /><span class="stall-relic__word">${w.word}</span></div>`;
}
