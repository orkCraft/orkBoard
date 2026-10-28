// Choose a card (docs/specs/100-a-goals-way-as-cards.md §2.1, §3.2, decisions §167.2, §168.1; the mockup docs/mockups/cards/, states 3, 4, 6, 7): a question as a banner over a row of choice cards dealt over the pane, the leader's pick raised
// with its why at its foot, a choice that spends more with its gem, a choice of a look its preview in the window, *Other…* a blank card with + (it opens a field with the pick's words), and under the row a quiet button, *Let <leader> decide*.
// The face of a card is the Board's (spec 101 §2): the element at the left of its header, bare, then the name left-aligned in the body face; its window one sign (or the preview, or a head); its label row the asker and the gem at its right.
//
//   <Choose question choices pick onChoose onOther decide … />      the component: a question and its choices, used by Talk's questions (questioncard.js) and by a fork's two sides (spec 100 C)
//     question   the question, in the banner
//     choices    [{id, name, why?, gem?, preview?, head?, sign?}]  two to four, in the row's order
//                  id        the string `onChoose` is given
//                  name      the header (three lines, then cut; the whole in its title)
//                  why       what the foot says (the pick's why; a fork's side its why)
//                  gem       "3%": it spends more; orkUI's gem at the label row's right
//                  preview   a choice of a look: an image address (a path or a data: address) or a vnode, drawn in the window
//                  head      {race, tier}: the head of who says it (a fork's side), in the window (over the preview's corner when there is one)
//                  sign      the window's sign by name, when there is no preview nor head (default `question`, the pick's `check`)
//                  by        this card's label row (a fork's side: its party's name), in place of the row's `by`
//     pick       the id of the leader's pick, raised; "" for none
//     onChoose(id)    a press on a card answers at once
//     onOther(text)   *Other…*: a blank card with +; pressed it opens a field with the pick's name in it, Enter or its *Send* answers; omit it for a choice with no *Other…*
//     decide     {label, onDecide}: the quiet button under the row (*Let <leader> decide*); omit for none
//     together   {label, onTogether}: a second quiet button (the questions together over the pane); omit for none
//     onBack     *Put it back*: the quiet button's press; omit for none
//     by         the asker, in each card's label row (a party's name); element  the goal's element, at the left of each header; head  {race, tier} the asker's head, in the window of a card with none of its own
//     hint       one muted line under the banner (*Pick an answer: the leader writes it into the spec*)
//
//   chooseFor(source, Component)   registers who fills the pane's `choose` kind for `openOver("choose", {source, …}, from, title)`: `Component({props, close}) -> html` reads its own data and draws a <Choose>;
//                                  `source` "question" is questioncard.js's. The kind `choose` is drawn here (frame/kinds.js).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { leans } from "./motion.js";

// Its sheet (hand/questions.css) is loaded with the first card dealt, as frame.js loads the window's.
const sheet = typeof document !== "undefined" ? new URL("./questions.css", import.meta.url).href : "";
if (sheet && !document.querySelector(`link[href="${sheet}"]`)) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = sheet;
  document.head.appendChild(link);
}

/** The window of a choice: its preview, its head, or its sign. */
function Window({ c, picked, head }) {
  const own = c.head || null, pre = c.preview;
  return html`<span class="q-card__window">
    ${pre ? (typeof pre === "string" ? html`<img class="q-card__preview" src=${pre} alt="" draggable="false" />` : pre)
      : own ? html`<span class="q-card__fig"><${Head} race=${own.race} tier=${own.tier} size="mid" /></span>`
      : html`<span class="q-card__fig"><span class="q-card__sign"><${Sign} name=${c.sign || (picked ? "check" : "question")} big=${true} /></span>
        ${head && html`<span class="q-card__asker"><${Head} race=${head.race} tier=${head.tier} /></span>`}</span>`}
    ${pre && own && html`<span class="q-card__asker"><${Head} race=${own.race} tier=${own.tier} /></span>`}
  </span>`;
}

function ChoiceCard({ c, i, picked, element, by, head, onPress }) {
  return html`<button type="button" class=${cls(`ork-card q-card ork-deal${element ? ` el-${element}` : ""}`, { "is-pick ork-picked": picked })} data-choice=${c.id} data-pick=${picked ? "1" : undefined}
      style=${`--ork-deal-i:${i}`} aria-label=${`${c.name}${picked ? ", the leader’s pick" : ""}${c.gem ? `, about ${c.gem}` : ""}`} title=${c.name} onClick=${onPress} ...${leans}>
    <span class="q-card__head"><${Elem} name=${element || ""} dim=${!element} /><span class="q-card__name">${c.name}</span></span>
    <${Window} c=${c} picked=${picked} head=${head} />
    <span class="q-card__label"><span class="q-card__by">${c.by || by || ""}</span>${c.gem && html`<span class="ork-gem share" data-cost=${c.gem}>${c.gem}</span>`}</span>
    <span class="q-card__foot">${c.why || ""}</span>
  </button>`;
}

/** *Other…*: a blank card with +; pressed, the field opened on it with the pick's words. */
function OtherCard({ i, seed, onOther }) {
  const [open, setOpen] = useState(false), [text, setText] = useState(seed), box = useRef();
  useEffect(() => { if (open) box.current?.focus({ preventScroll: true }); }, [open]);
  const send = () => { const said = text.trim(); if (said) onOther(said); };
  if (!open) {
    return html`<button type="button" class="ork-card q-card q-card--blank ork-deal" data-choice="other" style=${`--ork-deal-i:${i}`} aria-label="Other…" onClick=${() => { setText(seed); setOpen(true); }} ...${leans}>
      <span class="q-card__head"><span class="q-card__name">Other…</span></span>
      <span class="q-card__window"><${Icon} name="plus" /></span>
      <span class="q-card__label"></span><span class="q-card__foot"></span>
    </button>`;
  }
  const key = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setOpen(false); }
    else if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };
  return html`<div class="ork-card q-card q-card--blank is-open" data-choice="other" role="group" aria-label="Other…">
    <span class="q-card__head"><span class="q-card__name">Other…</span></span>
    <textarea ref=${box} class="ork-field q-card__field" aria-label="Your own answer" rows="3" value=${text} onInput=${(e) => setText(e.target.value)} onKeyDown=${key}></textarea>
    <span class="q-card__label q-card__label--acts"><button type="button" class="ork-btn quiet" onClick=${() => setOpen(false)}>Cancel</button>
      <button type="button" class="ork-btn primary" disabled=${!text.trim()} onClick=${send}>Send</button></span>
  </div>`;
}

/** A question and its choices dealt as cards (the props are the file's top). */
export function Choose({ question, choices, pick = "", onChoose, onOther, decide, together, onBack, by = "", element = "", head = null, hint = "" }) {
  const root = useRef(), seed = (choices.find((c) => c.id === pick) || choices[0] || {}).name || "";
  useEffect(() => { (root.current?.querySelector(".q-card.is-pick") || root.current?.querySelector(".q-card"))?.focus({ preventScroll: true }); }, [question]);
  return html`<section class="q-choose" ref=${root} data-kind="choose" aria-label=${question}>
    <div class="ork-frame q-choose__q" role="heading" aria-level="2">${question}</div>
    ${hint && html`<p class="cap q-choose__hint">${hint}</p>`}
    <div class="q-choose__row" role="group" aria-label="Choices" key=${question}>
      ${choices.map((c, i) => html`<${ChoiceCard} key=${c.id} c=${c} i=${i} picked=${c.id === pick} element=${element} by=${by} head=${head} onPress=${() => onChoose(c.id)} />`)}
      ${onOther && html`<${OtherCard} key="other" i=${choices.length} seed=${seed} onOther=${onOther} />`}
    </div>
    <div class="q-choose__acts">
      ${decide && html`<button type="button" class="ork-btn quiet" onClick=${decide.onDecide}>${decide.label}</button>`}
      ${together && html`<button type="button" class="ork-btn quiet" onClick=${together.onTogether}>${together.label}</button>`}
      ${onBack && html`<button type="button" class="ork-btn quiet" onClick=${onBack}>Put it back</button>`}
    </div>
  </section>`;
}

const SOURCES = {};
/** Who draws the pane's `choose` for `source` (see the top). */
export function chooseFor(source, Component) { SOURCES[source] = Component; }

function ChooseKind({ props, close }) {
  const Source = SOURCES[props?.source || "question"];
  return Source ? html`<${Source} props=${props || {}} close=${close} />` : null;
}
drawn("choose", ChooseKind);
