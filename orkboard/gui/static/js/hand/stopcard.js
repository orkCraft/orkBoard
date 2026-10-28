// Today's stop as one card of the hand (docs/specs/98-the-table-and-the-hand.md §4.2, §4.4, decisions §160.6): one size; its face its sign or its goal's element,
// its name (two lines at most), its leader's head and, when it spends, its gem; a card of another party says its party. Pressed, it is lifted over the pane's foot with its
// answers (answers.js, the same commands the old fan sent), its cost's words and *Put it back*; the cards of the table it is about rise (about.js). A kind the hand does not
// know (a goal's route card is spec 100's) is a plain card with its text, and a press lifts it all the same.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { lift, lower } from "../frame/state.js";
import { Tiles } from "../arena/picks.js";
import { missingWords } from "../arena/arenawords.js";
import { goalLine, goalsOfRow } from "../arena/collidewords.js";
import { Answers } from "./answers.js";
import { costOf, Gem, Spend } from "./cost.js";
import { liftKey } from "./state.js";
import { leans } from "./motion.js";
import { useAbout } from "./about.js";

/** The top of a card: a failure's alert, a result's check or cross, a sign-in's alert, else the element of its goal (dim while it has none). */
export function Mark({ s }) {
  if (s.kind === "failed") return html`<span class="is-danger"><${Sign} name="alert" /></span>`;
  if (s.kind === "result") return html`<span class=${s.gem?.sign === "cross" ? "is-danger" : "is-ok"}><${Sign} name=${s.gem?.sign || "check"} /></span>`;
  if (s.kind === "sign_in") return html`<span class="is-alert"><${Sign} name="alert" /></span>`;
  if (!s.node) return html`<${Sign} name="flag" />`;
  return html`<${Elem} name=${s.node.element || ""} dim=${!s.node.element} />`;
}

const headOf = (s) => s.head || s.party?.head || null;
const partyWords = (s) => (s.other && s.party?.name ? `${s.party.name} · ` : "");
/** What a card is called for a screen reader and a long press: *Asks you in Tech: The title*. */
export const labelOf = (s) => `${s.label}${s.other && s.party?.name ? ` in ${s.party.name}` : ""}: ${s.full}`;

/** The card face of a stop `s` (the leader's head is drawn at its mid size; the narrow sheet draws it smaller). `onPress`: the press. */
export function StopCard({ s, lit = false, slot = false, top = false, dealt = null, gone = false, onPress, onFocus, children }) {
  const cost = costOf(s), head = headOf(s);
  return html`<button type="button" class=${cls("ork-card ork-leans hand-card hand-card--stop", { asks: ["asks", "goal", "pick", "collide"].includes(s.kind), fails: s.kind === "failed", "is-on": lit,
        "is-slot": slot, "is-gone": gone, "ork-deal": dealt != null })}
      data-key=${s.key} data-kind=${s.kind} data-goal=${s.node?.slug || s.row?.idea || ""} data-party=${s.party?.slug || ""} data-top=${top ? "1" : undefined}
      style=${dealt != null ? `--ork-deal-i:${dealt}` : undefined} aria-label=${labelOf(s)} title=${`${labelOf(s)}${s.text ? ` · ${s.text}` : ""}`.slice(0, 200)}
      aria-haspopup="dialog" aria-expanded=${slot ? "true" : "false"} tabindex=${slot || gone ? -1 : undefined} inert=${gone || undefined} onClick=${onPress} onFocus=${onFocus} ...${leans}>
    <span class="hand-card__mark"><${Mark} s=${s} /></span>
    ${s.other && s.party?.name ? html`<span class="hand-card__party">${s.party.name}</span>` : null}
    <span class="hand-card__name">${s.title || s.full}</span>
    <span class="hand-card__gem"><${Gem} cost=${cost} /></span>
    ${head ? html`<span class="hand-card__head"><${Head} race=${head.race} tier=${head.tier} size="mid" /></span>` : null}
    ${children}
  </button>`;
}

/** The stop's own lines on a lifted card: its text, what it waits for, the goals of a collision, the pick's tiles. */
function Body({ s }) {
  return html`${s.kind === "collide" && html`<ul class="hand-goals" aria-label="The goals">${goalsOfRow(s.row).map((g) => html`<li key=${g.idea}>${goalLine(g)}</li>`)}</ul>`}
    ${s.kind !== "pick" && s.text && html`<p class="body hand-lifted__text">${s.text}</p>`}
    ${s.why && html`<p class="cap hand-lifted__why">${s.why}</p>`}
    ${s.kind === "plan" && (s.row?.missing || []).length > 0 && html`<p class="cap hand-lifted__why">${missingWords(s.row.missing)}</p>`}
    ${s.kind === "pick" && html`<p class="body hand-lifted__text">${s.text}</p><${Tiles} row=${s.row} />`}`;
}

/** A card lifted over the pane's foot (§4.4): its answers, its cost's words, *Put it back*. `anchor`: the element of the card it lies for (its left edge is the lifted card's). */
export function Lifted({ s, anchor }) {
  const box = useRef(), [left, setLeft] = useState(null), cost = costOf(s), head = headOf(s);
  useAbout(s);
  useLayoutEffect(() => {                                              // over its stack, kept inside the hand's width
    const place = () => {
      const hand = box.current?.parentElement, a = anchor?.isConnected ? anchor.getBoundingClientRect() : null;
      if (!hand || !a) { setLeft(null); return; }
      const h = hand.getBoundingClientRect(), w = box.current.offsetWidth;
      setLeft(Math.max(0, Math.min(a.left - h.left, h.width - w)));
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [s.key, anchor]);
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [s.key]);
  const tone = s.tone === "danger" ? "danger" : s.tone === "alert" ? "alert" : "";
  return html`<aside ref=${box} class=${cls("ork-frame hand-lifted", tone)} role="dialog" tabindex="-1" aria-label=${`Lifted: ${labelOf(s)}`} data-key=${s.key} data-kind=${s.kind}
      style=${left != null ? `left:${left}px` : undefined}>
    <div class="hand-lifted__top"><${Mark} s=${s} /><p class="cap hand-lifted__title">${partyWords(s)}${s.title || s.full}</p>${head && html`<${Head} race=${head.race} tier=${head.tier} size="mid" />`}</div>
    <p class="cap hand-lifted__kind">${s.label}</p>
    <${Body} s=${s} />
    <div class="hand-answers" role="group" aria-label="Answers"><${Answers} s=${s} /></div>
    <${Spend} cost=${cost} />
    <button type="button" class="ork-btn hand-put" onClick=${lower}>Put it back</button>
  </aside>`;
}

export { lift, liftKey };
