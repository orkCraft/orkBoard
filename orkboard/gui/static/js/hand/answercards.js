// A lifted card stays a hand card and its ways are the hand (docs/specs/158-the-window-as-a-table.md part F, decisions §270; the mockup docs/mockups/answer-cards/). On the desktop a card with one open question, or a failure, is
// not opened at 404 x 566: it rises out of its slot onto the table's foot as the 144 x 202 hand card it was, in its signal's ring (orkUI's `asks` and `fails`); its goal's card in the Orkmaster's column is ringed the same.
// Its answers are the hand: each way a card of the same size where the hand's cards lie, its name (the pixel face) and its whole line (the body face) at rest, the leader's pick marked by its head and by its words, a priced way's cost
// in its corner; pressing a way answers at once (`from: "hand"`). Then *<Leader> decides* (a way as any), and *Open…* (today's form, askform.js) and *Put it back* at the row's end. The rest of the hand sinks, grey and inert
// (hand.js). Under reduced motion nothing rises. The narrow page and the phone keep the inline lifted card (stopcard.js `Lifted`, decisions §270.7). A goal with more than one question keeps *Send the picks* there.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, headWords } from "../orkui.js";
import { CornerFoot, CornerTop, muchOf } from "../table/corners.js";
import { lower } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { PICTURES } from "../arena/arenawords.js";
import { askedInfo, againWords, decideStop, openStop, sendAnswers, startAgain } from "./answers.js";
import { costOf } from "./cost.js";
import { wayCostOf } from "./waycost.js";
import { named } from "./todoform.js";
import { actionOf, footOf, headOf, labelOf, signalOf } from "./stopcard.js";
import { useAbout } from "./about.js";

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

/** The ways of a stop `s` as cards, or null when the stop is not one this draws (a goal with more than one question, any other kind): `{tone, ways, decide, open}`. A way is `{id, name, line, pick, cost, sign, run}`. */
export function answerSet(s) {
  if (s.kind === "failed") {
    return { tone: "fails", ways: [{ id: "again", name: "Start again", line: againWords(s), pick: false, cost: costOf(s), sign: "play", run: () => startAgain(s) }], decide: null, open: () => openStop(s) };
  }
  if (s.kind !== "asks" && s.kind !== "goal") return null;
  const { asked, name } = askedInfo(s);
  if (asked.length !== 1) return null;
  const q = asked[0], picks = [q.pick != null ? q.choices?.[q.pick] || "" : ""];
  const ways = (q.choices || []).map((c, i) => ({ id: `way-${i}`, name: c, line: lineOf(q, i), pick: i === q.pick, cost: wayCostOf(q.costs?.[i]), sign: "compass", run: () => (c === PICTURES ? openStop(s, { picks: [c] }) : sendAnswers(s, [c])) }));
  return { tone: "asks", ways, decide: { id: "decide", name: `${named(name)} decides`, line: DECIDE_LINE, run: () => decideStop(s) }, open: () => openStop(s, { picks }) };
}

/** Rings the goal's card in the Orkmaster's column in the lifted card's signal while the card is up (`data-ringed`, table/column.css). */
function useRing(goal, tone) {
  useEffect(() => {
    if (!goal) return undefined;
    const column = document.querySelector(".frame-column");
    if (!column) return undefined;
    const mark = () => column.querySelectorAll(`.col-card[data-goal="${CSS.escape(goal)}"]`).forEach((el) => { if (el.dataset.ringed !== tone) el.dataset.ringed = tone; });
    mark();
    const watch = typeof MutationObserver === "function" ? new MutationObserver(mark) : null;
    watch?.observe(column, { childList: true, subtree: true });
    return () => { watch?.disconnect(); column.querySelectorAll("[data-ringed]").forEach((el) => el.removeAttribute("data-ringed")); };
  }, [goal, tone]);
}

/** One way as a hand card: its goal's rune and the way's sign at the top, its name (the pixel face), its whole line, and at the foot who (its pick) and what it costs. */
function WayCard({ w, s, head, rune }) {
  const cost = w.cost, much = cost ? { ...muchOf({ cost: cost.gem }), share: !!cost.share } : null, leader = w.id === "decide";
  const kind = leader && head ? html`<${Head} race=${head.race} tier=${head.tier} title=${headWords(head)} />` : null;
  return html`<button type="button" class=${cls("ork-card hand-ans", `el-${rune.hue}`, { "is-pick": w.pick, "is-decide": leader })} data-way=${w.id} data-pick=${w.pick ? "1" : undefined} data-cost=${cost?.gem || undefined}
      aria-label=${`${w.name}${w.pick ? `, ${ITS_PICK}` : ""}: ${s.full}`} title=${w.line} onClick=${w.run}>
    <${CornerTop} rune=${rune} kind=${w.sign} kindNode=${kind} />
    <span class="hand-ans__name">${w.name}</span>
    <span class="hand-ans__line">${w.line}</span>
    <${CornerFoot} who=${w.pick && head ? { heads: [head], word: ITS_PICK } : null} much=${much} />
  </button>`;
}

/** The lifted question or failure: the hand card it was, 144 x 202, risen onto the table's foot over the slot it left, in its signal's ring; and under it, in the hand's row, its ways (`set`: `answerSet`). */
export function AnswerLifted({ s, anchor, set }) {
  const box = useRef(), row = useRef(), [at, setAt] = useState(null), element = s.node?.element || "", hue = s.node?.hue || element, head = headOf(s);
  const rune = { name: element, hue, dim: !element }, goal = s.node?.slug || s.row?.idea || "";
  useAbout(s);
  useRing(goal, set.tone === "fails" ? "fails" : "asks");
  useLayoutEffect(() => {                                              // over the slot it left, kept inside the hand's width; its ways start where the hand's cards lie, after the + card
    const place = () => {
      const hand = box.current?.parentElement, a = anchor?.isConnected ? anchor.getBoundingClientRect() : null;
      if (!hand) { setAt(null); return; }
      const h = hand.getBoundingClientRect(), plus = hand.querySelector(".hand-plus")?.getBoundingClientRect();
      setAt({ left: a ? Math.max(0, Math.min(a.left - h.left, h.width - 144)) : 0, ways: Math.max(0, plus ? plus.right - h.left + 28 : 200) });
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [s.key, anchor]);
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [s.key]);
  const { ways, decide } = set, tone = set.tone;
  return html`<aside ref=${box} class=${cls(`ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked${element ? ` el-${hue}` : ""}`, { asks: tone === "asks", fails: tone === "fails" })}
      role="dialog" tabindex="-1" aria-label=${`Lifted: ${labelOf(s)}`} data-key=${s.key} data-kind=${s.kind} style=${at ? `left:${at.left}px` : undefined}>
    <${CornerTop} rune=${rune} kind=${actionOf(s).sign} signal=${signalOf(s)} />
    <span class="hand-card__name" title=${s.full || s.title}>${s.title || s.full}</span>
    <span class="hand-card__foot">${footOf(s)}</span>
    <${CornerFoot} who=${head ? { heads: [head], word: "" } : null} much=${set.tone === "fails" && ways[0]?.cost ? { ...muchOf({ cost: ways[0].cost.gem }), share: !!ways[0].cost.share } : null} />
  </aside>
  <div ref=${row} class="hand-ways-row" role="group" aria-label="Answers" style=${at ? `--hc-wleft:${at.ways}px` : undefined}>
    <div class="hand-ways-cards">
      ${ways.map((w) => html`<${WayCard} key=${w.id} w=${w} s=${s} head=${head} rune=${rune} />`)}
      ${decide && html`<${WayCard} key=${decide.id} w=${{ ...decide, sign: "compass", pick: false, cost: null }} s=${s} head=${head} rune=${rune} />`}
    </div>
    <div class="hand-ways-acts">
      <button type="button" class="ork-btn quiet" data-act="open" onClick=${set.open}>Open…</button>
      <button type="button" class="ork-btn hand-put" data-act="put" onClick=${lower}>Put it back</button>
    </div>
  </div>`;
}
