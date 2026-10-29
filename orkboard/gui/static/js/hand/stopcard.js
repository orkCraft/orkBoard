// A stop as one card of the hand (docs/specs/101 §4.5, decisions §167.1; docs/specs/98 §4.2, §4.4, decisions §160.6): the card of a card game's anatomy, one size. Its header the goal's element at the left, bare, then its
// name left-aligned (three lines at most); its window low, with the action's sign toned down (the alert of a failure, the question of a question, the check of a result) and the head of who asks small over the sign's lower right corner, the two one figure centred in the window (decisions §168.3); its
// label row the party's name and, when it spends, its gem at the right; its foot the question or the line (two lines at most). The hand shows the header and the window; the rest lies under the window's edge until the card
// rises (hand.css). Pressed, it is lifted over the pane's foot with its answers (answers.js, the same commands the old fan sent), its cost's words and *Put it back*; the cards of the table it is about rise (about.js). A kind the
// hand does not know (a goal's route card is spec 100's) is a plain card with its text, and a press lifts it all the same.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { lift, lower } from "../frame/state.js";
import { Tiles } from "../arena/picks.js";
import { missingWords } from "../arena/arenawords.js";
import { goalLine, goalsOfRow } from "../arena/collidewords.js";
import { Answers } from "./answers.js";
import { costOf, Gem, Spend } from "./cost.js";
import { goalOfStop } from "./data.js";
import { liftKey } from "./state.js";
import { leans } from "./motion.js";
import { useAbout } from "./about.js";
import { wayOf } from "./ways.js";

/** The action's sign of a stop and its tone: the alert of a failure and of a sign-in, the question of a question, the check (or cross) of a result, else the sign of what is asked (a plan's page, a pick's picture, a to-do's flag). */
export function actionOf(s) {
  const w = wayOf(s.kind);
  if (w?.sign) return { sign: w.sign, tone: w.tone || "" };           // a goal's way's card (spec 100): its part's sign
  if (s.kind === "failed") return { sign: "alert", tone: "danger" };
  if (s.kind === "sign_in") return { sign: "alert", tone: "alert" };
  if (s.kind === "result") return { sign: s.gem?.sign || "check", tone: s.gem?.sign === "cross" ? "danger" : "ok" };
  if (s.kind === "asks" || s.kind === "goal" || s.kind === "collide") return { sign: "question", tone: "" };
  if (s.kind === "pick") return { sign: "picture", tone: "" };
  if (s.kind === "plan" || s.kind === "change") return { sign: "page", tone: "" };
  return { sign: "flag", tone: "" };
}

/** The action's sign of a stop, at the signs' big size or the small one (`big`). */
export function Mark({ s, big = false }) {
  const a = actionOf(s);
  return html`<span class=${cls("hand-mark", a.tone && `is-${a.tone}`)}><${Sign} name=${a.sign} big=${big} /></span>`;
}

/** The goal's element, bare; dim while it has none (a stop of no goal). */
export const ElemOf = ({ s }) => html`<${Elem} name=${s.node?.element || ""} dim=${!s.node?.element} />`;

const headOf = (s) => wayOf(s.kind)?.head?.(s) || s.head || s.party?.head || null;           // a goal's way's card may name its asker (spec 100: the route's is the Orkmaster)
const footOf = (s) => wayOf(s.kind)?.foot?.(s) ?? (s.text || s.why || "");           // a goal's way's card may say its own foot (spec 100 C: *Decision 118*, *Design and Tech disagree*)
/** What a card is called for a screen reader and a long press: *Asks you in Tech: The title*. */
export const labelOf = (s) => `${s.label}${s.other && s.party?.name ? ` in ${s.party.name}` : ""}: ${s.full}`;

/** The card face of a stop `s` (docs/specs/101 §4.5). `top`: the front card of its stack. `onPress`: the press. */
export function StopCard({ s, lit = false, slot = false, top = false, dealt = null, gone = false, onPress, onFocus, children }) {
  const cost = costOf(s), head = headOf(s), element = s.node?.element || "";
  return html`<button type="button" class=${cls(`ork-card ork-leans hand-card hand-card--stop${element ? ` el-${element}` : ""}`, { asks: ["asks", "goal", "pick", "collide"].includes(s.kind), fails: s.kind === "failed", "is-on ork-picked": lit,
        "is-slot": slot, "is-gone": gone, "ork-deal": dealt != null })}
      data-key=${s.key} data-kind=${s.kind} data-goal=${goalOfStop(s)} data-party=${s.party?.slug || ""} data-top=${top ? "1" : undefined}
      style=${dealt != null ? `--ork-deal-i:${dealt}` : undefined} aria-label=${labelOf(s)} title=${`${labelOf(s)}${s.text ? ` · ${s.text}` : ""}`.slice(0, 200)}
      aria-haspopup="dialog" aria-expanded=${slot ? "true" : "false"} tabindex=${slot || gone ? -1 : undefined} inert=${gone || undefined} onClick=${onPress} onFocus=${onFocus} ...${leans}>
    <span class="hand-card__head"><${ElemOf} s=${s} /><span class="hand-card__name">${s.title || s.full}</span></span>
    <span class="hand-card__window"><span class="hand-card__fig"><span class="hand-card__act"><${Mark} s=${s} big=${true} /></span>${head ? html`<span class="hand-card__asker"><${Head} race=${head.race} tier=${head.tier} /></span>` : null}</span></span>
    <span class="hand-card__label"><span class="hand-card__party">${s.party?.name || s.label}</span><span class="hand-card__gem"><${Gem} cost=${cost} /></span></span>
    <span class="hand-card__foot">${footOf(s)}</span>
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

/** A card lifted over the pane's foot (docs/specs/104 §5, decisions §176.4): the hand card grown to twice its width, held up a degree or two, its foot on the hand's line where its stack lies. Its anatomy is the hand card's (the
 * element and name, the window with the action's sign and the asker's head, the party and the gem); between the window and the foot its body holds the stop's lines, its answers (or a goal's way's own body), its cost's words and
 * *Put it back*, and scrolls inside when the card reaches its most height; its foot says what the card is. `anchor`: the element of the card it lies for (its left edge is the lifted card's, its side the card's lean). */
export function Lifted({ s, anchor }) {
  const box = useRef(), [at, setAt] = useState(null), cost = costOf(s), head = headOf(s), element = s.node?.element || "";
  useAbout(s);
  useLayoutEffect(() => {                                              // over its stack, kept inside the hand's width; it leans toward the side of the hand its stack lies on
    const place = () => {
      const hand = box.current?.parentElement, a = anchor?.isConnected ? anchor.getBoundingClientRect() : null;
      if (!hand || !a) { setAt(null); return; }
      const h = hand.getBoundingClientRect(), w = box.current.offsetWidth;
      setAt({ left: Math.max(0, Math.min(a.left - h.left, h.width - w)), lean: a.left + a.width / 2 < h.left + h.width / 2 ? -1 : 1 });
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [s.key, anchor]);
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [s.key]);
  const tone = s.tone === "danger" ? "danger" : s.tone === "alert" ? "alert" : "", Way = wayOf(s.kind)?.Lifted;
  return html`<aside ref=${box} class=${cls(`ork-card hand-card hand-card--stop hand-card--big hand-lifted${element ? ` el-${element}` : ""}`, tone, { asks: ["asks", "goal", "pick", "collide"].includes(s.kind), fails: s.kind === "failed" })}
      role="dialog" tabindex="-1" aria-label=${`Lifted: ${labelOf(s)}`} data-key=${s.key} data-kind=${s.kind}
      style=${at ? `left:${at.left}px;--hc-lean:${at.lean}` : undefined}>
    <span class="hand-card__head"><${ElemOf} s=${s} /><span class="hand-card__name hand-lifted__title">${s.title || s.full}</span></span>
    <span class="hand-card__window"><span class="hand-card__fig"><span class="hand-card__act"><${Mark} s=${s} big=${true} /></span>${head ? html`<span class="hand-card__asker"><${Head} race=${head.race} tier=${head.tier} /></span>` : null}</span></span>
    <span class="hand-card__label"><span class="hand-card__party">${s.party?.name || s.label}</span><span class="hand-card__gem"><${Gem} cost=${cost} /></span></span>
    <div class="hand-lifted__body">
      ${Way ? html`<${Way} s=${s} close=${lower} />` : html`<${Body} s=${s} />
      <div class="hand-answers" role="group" aria-label="Answers"><${Answers} s=${s} /></div>`}
      <${Spend} cost=${cost} />
      <button type="button" class="ork-btn hand-put" onClick=${lower}>Put it back</button>
    </div>
    <span class="hand-card__foot hand-lifted__kind">${s.label}</span>
  </aside>`;
}

export { lift, liftKey };
