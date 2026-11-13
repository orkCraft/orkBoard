// **Spec 168 D1 (decisions §283.19, §286): the card in play stands at the table's foot at its left, 144 x 202 (openedcard.css `is-play`, handplace.js), its goal picked and its asker's tab opened (frame/state.js `playAt`); its ways are the hand's row from the same left edge,
// cut by the hand's rim and rising when hovered (each carries `data-way-kind`, the leader's kind of it, J1, for the pictures to come); *Your own words…* lays a field as large as the hand in the ways' place; a goal of several questions asks them one after another, each its own card.**
// A lifted card stays a hand card and its ways are the hand (docs/specs/158-the-window-as-a-table.md part F, decisions §270; the mockup docs/mockups/answer-cards/). On the desktop a card with open questions, or a failure, is
// not opened at 404 x 566: it rises out of its slot onto the table's foot as the 144 x 202 hand card it was, in its signal's ring (orkUI's `asks` and `fails`).
// Its answers are the hand: each way a card of the same size where the hand's cards lie, its name (the pixel face) and its whole line (the body face) at rest, the leader's pick marked by its head and by its words, a priced way's cost
// in its corner; pressing a way answers at once (`from: "hand"`). Then *<Leader> decides* (a way as any), and *Open…* (today's form, askform.js) and *Put it back* at the row's end. The rest of the hand sinks, grey and inert
// (hand.js). Under reduced motion nothing rises. The narrow page and the phone keep the inline lifted card (stopcard.js `Lifted`, decisions §270.7).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, headWords } from "../orkui.js";
import { CornerFoot, CornerTop, muchOf } from "../table/corners.js";
import { ORKMASTER, lower, playAt } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { PICTURES } from "../arena/arenawords.js";
import { askedInfo, againWords, decideStop, openStop, sendAnswers, startAgain } from "./answers.js";
import { costOf } from "./cost.js";
import { wayCostOf } from "./waycost.js";
import { named } from "./todoform.js";
import { actionOf, askerOf, footOf, headOf, labelOf, signalOf } from "./stopcard.js";
import { usePlace } from "./handplace.js";
import { PenField } from "./penfield.js";
import { useAbout } from "./about.js";

// The Pen (stage G, now §286): after *<Leader> decides* comes *Your own words…* (dashed until pressed): a field as large as the hand lies in the ways' place, focused, with *Send to <leader>* beside it (an empty field sends nothing; Enter sends, Shift+Enter is a new line;
// Esc closes it and gives the focus back to the way it came from). Tab runs the ways, *<Leader> decides*, *Your own words…*, *Open…*, *Put it back*; Esc and *Put it back* lower the card and give the focus back to the hand card it rose from.
export const OWN_WORDS = "Your own words…", OWN_LINE = "Write it what you want; it reads it and goes on.";
export const ITS_PICK = "its pick", NO_LINE = "Answers with this.", PICK_LINE = "What its leader recommends.", DECIDE_LINE = "It answers with what it recommends.";

const WIDE = typeof matchMedia === "function" ? matchMedia("(min-width: 760px)") : null;

/** Whether the page is wide enough for the cards (760 px and over) and no touch phone upright: the narrow page and the phone keep the inline card. */
export function useWide() {
  const [wide, setWide] = useState(!!WIDE?.matches);
  useEffect(() => {
    const on = () => setWide(!!WIDE?.matches);
    WIDE?.addEventListener?.("change", on);
    return () => WIDE?.removeEventListener?.("change", on);
  }, []);
  return wide && !uprightNow.value;
}

/** The line a way says of itself: the leader's own (`lines[i]`, written to fit the card), else the question's why for the pick, else a plain one. */
const lineOf = (q, i) => String(q.lines?.[i] || q.hints?.[i] || (i === q.pick ? q.why || PICK_LINE : NO_LINE));
export const pickOf = (q) => (q.pick != null ? q.choices?.[q.pick] || "" : "");

/** The ways of one question `q` as cards; `run(choice, i)` plays one. A way is `{id, name, line, own (the line is the leader's own), pick, cost, sign, kind (the leader's kind of it: realm/way_kinds.py), run}`. */
function waysOf(q, run) {
  return (q.choices || []).map((c, i) => ({ id: `way-${i}`, name: c, line: lineOf(q, i), own: !!q.lines?.[i], pick: i === q.pick, cost: wayCostOf(q.costs?.[i]), sign: "compass", kind: q.kinds?.[i] || "", run: () => run(c, i) }));
}

/** The ways of a stop `s` as cards, or null when the stop is not one this draws (any other kind): `{tone, ways, decide, open, asked}`. A goal of several questions asks them one after another: `asked` is all of them, `ways` the first's, and AnswerLifted steps through them (`stepWays`). */
export function answerSet(s) {
  if (s.kind === "failed") {
    return { tone: "fails", ways: [{ id: "again", name: "Start again", line: againWords(s), pick: false, cost: costOf(s), sign: "play", kind: "", run: () => startAgain(s) }], decide: null, open: () => openStop(s), asked: [] };
  }
  if (s.kind !== "asks" && s.kind !== "goal") return null;
  const { asked, name } = askedInfo(s);
  if (!asked.length) return null;
  const picks = asked.map(pickOf), ways = waysOf(asked[0], (c) => (c === PICTURES ? openStop(s, { picks: [c] }) : sendAnswers(s, [c])));
  return { tone: "asks", ways: asked.length === 1 ? ways : [], decide: { id: "decide", name: `${named(name)} decides`, line: DECIDE_LINE, run: () => decideStop(s) }, open: () => openStop(s, { picks }), asked };
}

/** The ways of question `i` of several: pressing one keeps it (`keep(all)`) and asks the next; the last sends them all, in the order asked. `kept`: what was picked before. */
export function stepWays(s, asked, i, kept, keep) {
  const last = i === asked.length - 1;
  return waysOf(asked[i], (c) => {
    const all = [...kept.slice(0, i), c];
    if (c === PICTURES) openStop(s, { picks: [...all, ...asked.slice(i + 1).map(pickOf)] });
    else if (last) sendAnswers(s, all);
    else keep(all);
  });
}

/** One way as a hand card: its goal's rune and the way's sign at the top, its name (the pixel face), its whole line, and at the foot who (its pick) and what it costs. */
export function WayCard({ w, s, head, rune, btn = null, on = undefined }) {
  const cost = w.cost, much = cost ? { ...muchOf({ cost: cost.gem }), share: !!cost.share } : null, leader = w.id === "decide";
  const kind = leader && head ? html`<${Head} race=${head.race} tier=${head.tier} title=${headWords(head)} />` : null;
  return html`<button type="button" ref=${btn} class=${cls(`ork-card hand-ans el-${rune.hue}`, { "is-pick": w.pick, "is-decide": leader, "hand-ans--pen": w.id === "own" })} aria-expanded=${on === undefined ? undefined : String(on)} data-way=${w.id} data-way-kind=${w.kind || undefined} data-pick=${w.pick ? "1" : undefined} data-cost=${cost?.gem || undefined}
      aria-label=${`${w.name}${w.pick ? `, ${ITS_PICK}` : ""}${w.own || w.disabled ? `, ${w.line}` : ""}: ${s.full}`} title=${w.line} disabled=${w.disabled || undefined} onClick=${w.run}>
    <${CornerTop} rune=${rune} kind=${w.sign} kindNode=${kind} />
    <span class="hand-ans__name">${w.name}</span>
    <span class="hand-ans__line">${w.line}</span>
    <${CornerFoot} who=${w.pick && head ? { heads: [head], word: ITS_PICK } : null} much=${much} />
  </button>`;
}

/** Whose tab a card in play opens (§283.19): the asking leader's, the Orkmaster's for what the Orkmaster plays (stopcard.js `askerOf`). */
export const tabOf = (s) => (askerOf(s) === "the Orkmaster" ? ORKMASTER : s.party?.slug || ORKMASTER);

/** A card in play (§283.19): its goal picked and its asker's tab opened, once for each card lifted. */
export function usePlay(s) {
  useEffect(() => { playAt(tabOf(s), s.node?.slug || s.row?.idea || s.row?.goal || ""); }, [s.key]);
}

/** The lifted question or failure: the hand card it was, 144 x 202, risen onto the table's foot at its left, in its signal's ring; and under it, in the hand's row from the same left edge, its ways (`set`: `answerSet`), cut by the hand's rim. */
export function AnswerLifted({ s, anchor, set }) {
  const box = useRef(), row = useRef(), element = s.node?.element || "", hue = s.node?.hue || element, head = headOf(s);
  const rune = { name: element, hue, dim: !element };
  const [step, setStep] = useState(0), [kept, setKept] = useState([]), [pen, setPen] = useState(false), penBtn = useRef(), from = useRef(null), wasPen = useRef(false);
  useAbout(s);
  usePlay(s);
  const at = usePlace(box, row, [s.key, anchor], pen);                  // the card and the ways from the table's left edge; the ways cut by the hand's rim; the sunk hand shrinks into the strip right of the ways (or of the field)
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [s.key]);
  const { decide } = set, tone = set.tone, asking = tone === "asks", own = asking ? askedInfo(s).name : "", many = set.asked.length > 1, q = many ? set.asked[Math.min(step, set.asked.length - 1)] : set.asked[0] || null;
  const ways = many ? stepWays(s, set.asked, step, kept, (all) => { setKept(all); setStep(step + 1); }) : set.ways;
  if (anchor?.isConnected) from.current = anchor;
  useEffect(() => { setPen(false); setStep(0); setKept([]); }, [s.key]);
  useEffect(() => { if (wasPen.current && !pen) penBtn.current?.focus({ preventScroll: true }); wasPen.current = pen; }, [pen]);                // the field closed: the focus goes back to the way it came from
  useEffect(() => () => {                                              // lowered: the focus goes back to the hand card it rose from (answered, that card is gone)
    const key = s.key;
    setTimeout(() => { const back = from.current?.isConnected ? from.current : document.querySelector(`.hand-places .hand-card[data-key="${CSS.escape(key)}"]`); if (back && !document.querySelector(".hand-lifted")) back.focus({ preventScroll: true }); }, 0);
  }, [s.key]);
  const opens = () => (many ? openStop(s, { picks: set.asked.map((x, i) => (i < step ? kept[i] : pickOf(x))) }) : set.open());
  const foot = many && q ? `${step + 1}/${set.asked.length} · ${q.ask}` : footOf(s);
  return html`<aside ref=${box} class=${cls(`ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked is-play${element ? ` el-${hue}` : ""}`, { asks: tone === "asks", fails: tone === "fails" })}
      role="dialog" tabindex="-1" aria-label=${`Lifted: ${labelOf(s)}`} data-key=${s.key} data-kind=${s.kind} data-step=${many ? String(step) : undefined} style=${at ? `left:${at.left}px` : undefined}>
    <${CornerTop} rune=${rune} kind=${actionOf(s).sign} signal=${signalOf(s)} />
    <span class="hand-card__name" title=${s.full || s.title}>${s.title || s.full}</span>
    <span class="hand-card__foot">${foot}</span>
    <${CornerFoot} who=${head ? { heads: [head], word: "" } : null} much=${set.tone === "fails" && ways[0]?.cost ? { ...muchOf({ cost: ways[0].cost.gem }), share: !!ways[0].cost.share } : null} />
  </aside>
  <div ref=${row} class=${cls("hand-ways-row is-play", { "is-writing": pen })} role="group" aria-label="Answers">
    <div class="hand-ways-cards">
      ${ways.map((w) => html`<${WayCard} key=${`${step}:${w.id}`} w=${w} s=${s} head=${head} rune=${rune} />`)}
      ${decide && html`<${WayCard} key=${decide.id} w=${{ ...decide, sign: "compass", pick: false, cost: null }} s=${s} head=${head} rune=${rune} />`}
      ${asking && html`<${WayCard} key="own" w=${{ id: "own", name: OWN_WORDS, line: OWN_LINE, sign: "text", pick: false, cost: null, run: () => setPen(!pen) }} s=${s} head=${head} rune=${rune} btn=${penBtn} on=${pen} />`}
    </div>
    <div class="hand-ways-acts">
      <button type="button" class="ork-btn quiet" data-act="open" onClick=${opens}>Open…</button>
      <button type="button" class="ork-btn hand-put" data-act="put" onClick=${lower}>Put it back</button>
    </div>
  </div>
  ${pen && html`<${PenField} at=${at} who=${named(own)} close=${() => setPen(false)} send=${(text) => (many ? sendAnswers(s, [...kept.slice(0, step), text, ...set.asked.slice(step + 1).map(pickOf)]) : sendAnswers(s, [text]))} />`}`;
}
