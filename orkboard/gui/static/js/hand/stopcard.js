// **Spec 147 C (decisions §251.5): the hand's card is 144 x 202, cut under its title by the hand's rim (handcard.css). Its top is the corners' (table/corners.js): the goal's rune at the left, the kind's sign at the right in its signal's colour, then the title in three whole
// lines; under the cut why it is asked (the question or the line, up to three lines) and the foot's corners: who asks (the head) and the card's cost. Not on the face at rest: the asker's head at the top, the party's label, the gem. Hovered or focused the card rises and shows it all.
// **Spec 147 D.1 (decisions §251.6): the lifted card (below) is on the desktop the opened card, 404 x 566 (hand/openedcard.css): its corners large (the goal's rune and name, the kind's word and sign; the asker and the cost of the way picked at its foot, waycost.js), the title, a body that scrolls (the window of spec 148 B.5 at its top, 160 px),
// the answers above the foot. The phone's inline card is the same card, 5 : 7 at the screen's width (spec 147 F.3, upright.css); while the keyboard is up it gives up 5 : 7 and keeps its top corners and a title in two lines, then the field, as tall as the screen leaves.**
// A stop as one card of the hand (docs/specs/101 §4.5, decisions §167.1; docs/specs/98 §4.2, §4.4, decisions §160.6; docs/specs/142 part B, decisions §249.2): the card of a card game's anatomy, one size, **with no window**. Its
// corner (top) holds the kind's sign at its small size at the left, in its signal's colour as the card's frame is (the alert of a question, a hearing, a sign-in and *Go on paid?*, the danger of a failure, else the muted ink), and at the right the head of
// who asks at 16 px; under it the goal's element at the left, bare, then its name left-aligned in three whole lines, never cut mid-line; its label row the party's name and, when it spends, its gem at the right. Its foot (the question or the line)
// is not drawn on the card: it stays in the markup (a screen reader's and a test's) and the lifted card says it. The card is about two thirds of its former height (hand.css). Pressed, it is lifted over the pane's foot with its answers
// (answers.js, the same commands the old fan sent), its cost's words and *Put it back*; the cards of the table it is about rise (about.js). A lifted card keeps its window as it was (§249.2) and says its title once (docs/specs/140 A4,
// decisions §247.6: sayonce.js). A kind the hand does not know (a goal's route card is spec 100's) is a plain card with its text, and a press lifts it all the same.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { CornerFoot, CornerTop, muchOf } from "../table/corners.js";               // a card is read by its four corners (spec 147, decisions §251.2)
import { lift, lower } from "../frame/state.js";
import { Tiles } from "../arena/picks.js";
import { missingWords } from "../arena/arenawords.js";
import { goalLine, goalsOfRow } from "../arena/collidewords.js";
import { Answers } from "./answers.js";
import { costOf, Spend } from "./cost.js";
import { OWN_LINES, WayLine } from "./wayline.js";
import { goalOfStop } from "./data.js";
import { liftKey } from "./state.js";
import { between, boxIn, handedName, leans, reduced, useFlight } from "./motion.js";
import { useAbout } from "./about.js";
import { wayOf } from "./ways.js";
import { nightWordsOf } from "./nightwords.js";
import { SketchLifted, isSketch } from "./sketchcard.js";
import { Said } from "./sayonce.js";
import { asksWords } from "./openwords.js";
import { footCost } from "./waycost.js";
import { StopWindow, hasWindow } from "./handwindow.js";

/** The action's sign of a stop and its tone: the alert of a failure and of a sign-in, the question of a question, the check (or cross) of a result, else the sign of what is asked (a plan's page, a pick's picture, a to-do's flag). */
export function actionOf(s) {
  const w = wayOf(s.kind);
  if (w?.sign) return { sign: w.sign, tone: w.tone || "" };           // a goal's way's card (spec 100): its part's sign
  if (s.kind === "failed") return { sign: "alert", tone: "danger" };
  if (s.kind === "sign_in") return { sign: "alert", tone: "alert" };
  if (s.kind === "result") return { sign: s.gem?.sign || "check", tone: s.gem?.sign === "cross" ? "danger" : "ok" };
  if (s.kind === "asks" || s.kind === "goal" || s.kind === "collide") return { sign: "question", tone: "" };
  if (isSketch(s)) return { sign: s.row.media === "page" ? "page" : "picture", tone: "" };           // a leader's sketch is a pick made before the spec (spec 121 §7.1): a page, else a picture
  if (s.kind === "pick") return { sign: "picture", tone: "" };
  if (s.kind === "plan" || s.kind === "change") return { sign: "page", tone: "" };
  return { sign: "flag", tone: "" };
}

/** The signal a card's corner sign is drawn in (docs/specs/142 B.2): the danger of a failure, the alert of a question, a hearing, a sign-in and *Go on paid?*, else none (the muted ink). */
export function signalOf(s) {
  const a = actionOf(s);
  return a.tone === "danger" || a.tone === "alert" ? a.tone : a.sign === "question" || a.sign === "alert" ? "alert" : "";
}

/** The action's sign of a stop, at the signs' big size or the small one (`big`); `corner`: in the card's signal colour (`signalOf`), not the action's tone. */
export function Mark({ s, big = false, corner = false }) {
  const a = actionOf(s), tone = corner ? signalOf(s) : a.tone;
  return html`<span class=${cls("hand-mark", tone && `is-${tone}`)}><${Sign} name=${a.sign} big=${big} /></span>`;
}

/** The goal's element, bare; dim while it has none (a stop of no goal). */
export const ElemOf = ({ s }) => html`<${Elem} name=${s.node?.element || ""} hue=${s.node?.hue || ""} dim=${!s.node?.element} />`;

export const headOf = (s) => wayOf(s.kind)?.head?.(s) || s.head || s.party?.head || null;           // a goal's way's card may name its asker (spec 100: the route's is the Orkmaster)
export const footOf = (s) => wayOf(s.kind)?.foot?.(s) ?? (s.text || s.why || "");           // a goal's way's card may say its own foot (spec 100 C: *Decision 118*, *Design and Tech disagree*)
/** What a card is called for a screen reader and a long press: *Asks you in Tech: The title*. */
export const labelOf = (s) => `${s.label}${s.other && s.party?.name ? ` in ${s.party.name}` : ""}: ${s.full}`;

/** Who hands a card (spec 120 §6.9): the Orkmaster for what the Orkmaster plays (a route, a decision, a hearing, a fork, a collision, *Go on paid?*), else the leader of the party that asks (its name). */
const ORK_KINDS = ["route", "start", "decision", "fork", "collide", "paid", "hearing", "objection", "groups", "spec_change"];
export const askerOf = (s) => (ORK_KINDS.includes(s.kind) ? "the Orkmaster" : s.party?.lead || s.party?.name || "the Orkmaster");

/** Who plays a stop, for where it comes from (motion.js `fromWhere`): its goal, its party, and whether the Orkmaster plays it (a card of a goal: the Orkmaster's tab is its origin when its goal's card is not in view; *Go on paid?* has no goal and no party: dealt from under its place). */
export const whoOf = (s) => ({ goal: goalOfStop(s), party: (s.party?.name ? s.party.slug : "") || s.row?.goal || "", ork: askerOf(s) === "the Orkmaster" && !!goalOfStop(s) });

/** What a card is, for the line said when it lands (*Sh.man hands you a question: …*). */
export const handsWords = (s) => `${s.card ? "a question" : "a card"}: ${s.full}`.slice(0, 160);

/** The card face of a stop `s` (docs/specs/101 §4.5). `top`: the front card of its stack. `onPress`: the press. `dealt`: it came (motion.js `useHanded`: `{i, el, hold}`; `el` the box it flies from, none: it is dealt from under its place). `gone`: it left;
 *  `back`: the box it came from, when it was answered: it is played back there (spec 120 §6.10), else it crumbles where it lay (the shards are its children). */
export function StopCard({ s, lit = false, slot = false, top = false, dealt = null, gone = false, back = null, onPress, onFocus, children }) {
  const cost = costOf(s), head = headOf(s), element = s.node?.element || "", hue = s.node?.hue || element, ref = useRef(), from = handedName(s.key), plain = !!dealt && !dealt.el && !dealt.hold;
  useFlight(ref, dealt);
  useLayoutEffect(() => {                                            // answered: it flies back into where it came from (orkUI's `.ork-play`, its end the origin's middle)
    const el = ref.current, origin = gone && back && !reduced() ? boxIn(back) : null;
    if (!el || !origin) return;
    const v = between(el.getBoundingClientRect(), origin);
    el.style.setProperty("--ork-play-x", `${v.x}px`);
    el.style.setProperty("--ork-play-y", `${v.y}px`);
    el.classList.add("ork-play");
  }, [gone]);
  return html`<button ref=${ref} type="button" class=${cls(`ork-card ork-leans hand-card hand-card--stop hand-card--face${element ? ` el-${hue}` : ""}`, { asks: ["asks", "goal", "pick", "collide"].includes(s.kind), fails: s.kind === "failed", "is-on ork-picked": lit,
        "is-slot": slot, "is-gone": gone, "ork-deal": plain })}
      data-key=${s.key} data-kind=${s.kind} data-goal=${goalOfStop(s)} data-party=${s.party?.slug || ""} data-top=${top ? "1" : undefined} data-from=${from || undefined}
      style=${dealt ? `--ork-deal-i:${dealt.i}` : undefined} aria-label=${`${labelOf(s)}${from ? `, from ${from}` : ""}`} title=${`${labelOf(s)}${s.text ? ` · ${s.text}` : ""}`.slice(0, 200)}
      aria-haspopup="dialog" aria-expanded=${slot ? "true" : "false"} tabindex=${slot || gone ? -1 : undefined} inert=${gone || undefined} onClick=${onPress} onFocus=${onFocus} ...${leans}>
    <${CornerTop} rune=${{ name: element, hue, dim: !element }} kind=${actionOf(s).sign} signal=${signalOf(s)} />
    <span class="hand-card__name" title=${s.full || s.title}>${s.title || s.full}</span>
    ${hasWindow(s) ? html`<span class="hand-card__foot has-window" data-foot="window"><${StopWindow} s=${s} /></span>` : html`<span class="hand-card__foot">${footOf(s)}</span>`}
    <${CornerFoot} who=${head || from ? { heads: [head], word: from ? `From ${from}` : "" } : null} much=${cost ? { ...muchOf({ cost: cost.gem }), share: !!cost.share } : null} />
    ${children}
  </button>`;
}

/** A card's name upright on a phone: a question card is called by the question itself (the goal's name is in the context above it), any other by its title. */
export const upName = (s) => (s.card ? s.full : s.title || s.full);

/** The stop's own lines on a lifted card: its text and what it waits for as one sentence (a line that repeats the title is not drawn, the rest behind its **…**: sayonce.js), the goals of a collision, the pick's tiles. */
function Body({ s }) {
  const title = [s.title, s.full];
  return html`${s.kind === "collide" && html`<ul class="hand-goals" aria-label="The goals">${goalsOfRow(s.row).map((g) => html`<li key=${g.idea}>${goalLine(g)}</li>`)}</ul>`}
    ${s.kind !== "pick" && html`<${Said} key=${s.key} title=${title} lines=${[s.text, s.why]} tag="body hand-lifted__text" />`}
    ${s.kind === "plan" && (s.row?.missing || []).length > 0 && html`<p class="cap hand-lifted__why">${missingWords(s.row.missing)}</p>`}
    ${s.kind === "plan" && !(s.row?.missing || []).length && s.node?.start_at === "night" && html`<p class="cap hand-lifted__why" data-night="waits">${nightWordsOf().waits}</p>`}
    ${s.kind === "pick" && html`<p class="body hand-lifted__text">${s.text}</p><${Tiles} row=${s.row} />`}`;
}

/** A card lifted over the pane's foot (docs/specs/104 §5, decisions §176.4): the hand card grown to twice its width, held up a degree or two, its foot on the hand's line where its stack lies. Its anatomy is the hand card's (the
 * element and name, the window with the action's sign and the asker's head, the party and the gem); between the window and the foot its body holds the stop's lines, its answers (or a goal's way's own body), its cost's words and
 * *Put it back*, and scrolls inside when the card reaches its most height; its foot says what the card is. `anchor`: the element of the card it lies for (its left edge is the lifted card's, its side the card's lean).
 * `inline` (upright on a touch phone, hand/upright.js): the top of the one stack, drawn in its place with its answers on it, nothing to put back; `typing`: the keyboard is up (upkeys.js). */
export function Lifted({ s, anchor, inline = false, typing = false }) {
  const box = useRef(), [at, setAt] = useState(null), cost = costOf(s), head = headOf(s), element = s.node?.element || "", hue = s.node?.hue || element;
  useAbout(inline ? null : s);
  useLayoutEffect(() => {                                              // over its stack, kept inside the hand's width; it leans toward the side of the hand its stack lies on
    if (inline) return undefined;                                      // upright on a touch phone the card is the stack's top, in its place (hand/upright.js)
    const place = () => {
      const hand = box.current?.parentElement, a = anchor?.isConnected ? anchor.getBoundingClientRect() : null;
      if (!hand || !a) { setAt(null); return; }
      const h = hand.getBoundingClientRect(), w = box.current.offsetWidth;
      setAt({ left: Math.max(0, Math.min(a.left - h.left, h.width - w)), lean: a.left + a.width / 2 < h.left + h.width / 2 ? -1 : 1 });
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [s.key, anchor, inline]);
  useEffect(() => { if (!inline) box.current?.focus({ preventScroll: true }); }, [s.key]);
  useLayoutEffect(() => {                                              // the keyboard is up on a phone (spec 147 F.3, `typing`: the px of the screen the keyboard leaves, upkeys.js): the card gives up 5 : 7 and is as tall as that leaves, from where it starts
    const el = box.current;
    if (!inline || !el) return;
    el.style.removeProperty("--up-h");
    if (!typing) return;
    const look = el.closest(".up-look");
    if (look) look.scrollTop = 0;
    el.style.setProperty("--up-h", `${Math.max(160, Math.floor(typing - el.getBoundingClientRect().top - 8))}px`);
  }, [typing, inline, s.key]);
  const tone = s.tone === "danger" ? "danger" : s.tone === "alert" ? "alert" : "", Way = wayOf(s.kind)?.Lifted || (isSketch(s) ? SketchLifted : null);
  const shown = footCost(s.key, cost), asker = askerOf(s), party = s.party?.name || "";                  // the opened card (spec 147 D.1; on the phone F.3): its corners large, the title, a body that scrolls, the answers above its foot
  return html`<aside ref=${box} class=${cls(`ork-card hand-card hand-card--stop hand-card--big hand-lifted hand-lifted--card${inline ? " hand-lifted--up" : ""}${typing ? " is-typing" : ""}${element ? ` el-${hue}` : ""}`, tone, { asks: ["asks", "goal", "pick", "collide"].includes(s.kind), fails: s.kind === "failed" })}
      role="dialog" tabindex="-1" aria-label=${`Lifted: ${labelOf(s)}`} data-key=${s.key} data-kind=${s.kind} data-typing=${typing ? "1" : undefined} style=${!inline && at ? `left:${at.left}px;--hc-lean:${at.lean}` : undefined}>
    <${CornerTop} large=${true} rune=${{ name: element, hue, dim: !element }} name=${s.node?.short || s.node?.title || ""} kind=${actionOf(s).sign} signal=${signalOf(s)} word=${s.label} kindClass="hand-lifted__kind" />
    <span class="hand-card__name hand-lifted__title" title=${s.full || s.title}>${inline ? upName(s) : s.title || s.full}</span>
    <div class="hand-lifted__body">
      ${hasWindow(s) && html`<div class="hand-lifted__win"><${StopWindow} s=${s} h=${inline ? 96 : 160} /></div>`}
      ${Way ? html`<${Way} s=${s} close=${lower} />` : html`<${Body} s=${s} />`}
    </div>
    <div class="hand-lifted__acts">
      ${!Way && html`<div class="hand-answers" role="group" aria-label="Answers"><${Answers} s=${s} /></div>`}
      ${s.row?.level && s.row?.pulls && !OWN_LINES.has(s.kind) ? html`<${WayLine} row=${s.row} own=${cost?.words || ""} />` : html`<${Spend} cost=${cost} />`}
      ${!inline && !wayOf(s.kind)?.puts && html`<button type="button" class="ork-btn hand-put" onClick=${lower}>Put it back</button>`}
    </div>
    <${CornerFoot} large=${true} who=${{ heads: [head], word: asksWords(asker, party) }} much=${shown ? { ...muchOf({ cost: shown.gem }), share: !!shown.share } : null} />
  </aside>`;
}

export { lift, liftKey };
