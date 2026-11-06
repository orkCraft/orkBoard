// The conflict's card (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.1, decisions §254.6; mockup docs/mockups/table-edge/ section 4): the Orkmaster found that a goal's decision goes against a standing decision and throws
// a card of the kind *conflict* into the hand under the first lane, before *Confirm and start*, so nothing of the spec is paid. The row is `{kind: "conflict", idea, goal, title, number, point, title_then, why_then, text}`, one for each conflict open
// (the decision's row has `conflicted` while one is). Its face is the hand's card (stopcard.js): the sign `conflict` (orkUI 0.30.0: two cards crossed; it draws nothing until that copy is in), the Orkmaster's crowned head as its asker, *Goes against
// §<n>* at its foot and the alert's edge (it asks you). Lifted, there are **two L cards side by side over the pane**: the new goal's side (its title, its why, *Goes against §<n>: <point>*, the three choices) and **the earlier decision, come out of the
// portal** (its title, its why, and *Open in the past*): it flies once from the ring in the table's edge to its place, and under reduced motion it lies there. The choices send `ideas.conflict {idea, number, choice, text?}`: **The new one replaces §<n>**,
// **Keep §<n>**, **Other…** (the person's own words, in a field). Nothing is decided without a press; answered, the conflict leaves the hand and the last one lets *Confirm and start* show. The earlier card lies outside the lifted card (its body clips),
// drawn into a box of the hand's own (`render`), the way a portal is. Its sheet is conflictcard.css, linked as the hand's are.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { h, render } from "preact";
import { html } from "../html.js";
import { act } from "../shell/store.js";
import { toast } from "../link.js";
import { board } from "../board/store.js";
import { CornerFoot, CornerTop } from "../table/corners.js";
import { openChronicle } from "../table/chronicle.js";
import { reduced } from "./motion.js";
import { bodyOf } from "./decisioncard.js";
import { spendWords } from "./costline.js";
import { orkHead } from "./routecard.js";
import { way } from "./ways.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as the hand's are linked
  const href = new URL("./conflictcard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

// the words, as realm/lexicon.py says them (goes_against, new_one_replaces, keep_decision, conflict_other: tests/test_conflict_browser.py keeps them so)
export const goesAgainst = (n) => `Goes against §${n}`;
export const replacesWords = (n) => `The new one replaces §${n}`;
export const keepWords = (n) => `Keep §${n}`;
export const OTHER = "Other…";
export const FLY_MS = 420;                                                // the earlier card's flight out of the ring (conflictcard.css `conflict-out`)

/** The new goal's why: the first lines of its decision's *Why* (the decision row of the same goal), else nothing. */
function whyOf(row) {
  const d = (board.value?.needs_you || []).find((r) => r.kind === "decision" && r.idea === row.idea);
  return bodyOf(d?.text)?.why || "";
}

/** The earlier decision as a card of its own beside the lifted one: its title, its why, a press to open it in the past. It comes out of the ring once. */
function Earlier({ row, anchor }) {
  const box = useRef();
  useLayoutEffect(() => {
    const el = box.current;
    if (!el || !anchor?.isConnected || reduced()) return;
    const ring = document.querySelector(".portal-host .ork-portal-ring, .release-lane .release-lane__label");
    if (!ring) return;
    const a = el.getBoundingClientRect(), r = ring.getBoundingClientRect();
    el.style.setProperty("--dx", `${Math.round(r.left + r.width / 2 - (a.left + a.width / 2))}px`);
    el.style.setProperty("--dy", `${Math.round(r.top + r.height / 2 - (a.top + a.height / 2))}px`);
    el.classList.add("is-out");
    const t = setTimeout(() => el.classList.remove("is-out"), FLY_MS + 80);
    return () => clearTimeout(t);
  }, [row.number]);
  return html`<aside ref=${box} class="ork-card hand-card hand-card--stop hand-card--big hand-lifted hand-lifted--card hand-earlier" role="region" aria-label=${`The earlier decision, §${row.number}`} data-earlier=${row.number}>
    <${CornerTop} large=${true} rune=${{ name: "", dim: true }} name=${`§${row.number}`} kind="page" word="Earlier" kindClass="hand-lifted__kind" />
    <span class="hand-card__name hand-lifted__title">${row.title_then || `§${row.number}`}</span>
    <div class="hand-lifted__body">
      ${row.why_then && html`<div class="hand-way__why"><span class="ork-label">Why</span><p class="body">${row.why_then}</p></div>`}
    </div>
    <div class="hand-lifted__acts"><button type="button" class="ork-btn quiet" data-answer="past" onClick=${() => openChronicle({ decision: row.number })}>Open in the past</button></div>
    <${CornerFoot} large=${true} who=${{ heads: [], word: `§${row.number}` }} />
  </aside>`;
}

/** The earlier card, drawn into a box of the hand's own beside the lifted card (`anchor`: the lifted card's element), taken away with it. */
function useEarlier(row, anchor) {
  useEffect(() => {
    const hand = anchor?.closest?.(".hand");
    if (!hand) return undefined;
    const box = document.createElement("div");
    box.className = "hand-earlier-host";
    hand.appendChild(box);
    const place = () => {
      const w = anchor.offsetWidth;
      box.style.left = `${anchor.offsetLeft + w + 16}px`;
      box.style.width = `${w}px`;
      box.style.setProperty("--hc-lean", getComputedStyle(anchor).getPropertyValue("--hc-lean") || "1");
    };
    place();
    const frame = requestAnimationFrame(place);                          // the lifted card is placed after its first layout
    render(h(Earlier, { row, anchor }), box);
    window.addEventListener("resize", place);
    return () => { cancelAnimationFrame(frame); window.removeEventListener("resize", place); render(null, box); box.remove(); };
  }, [anchor, row.number, row.title_then, row.why_then]);
}

export function ConflictLifted({ s, close }) {
  const row = s.row || {}, n = row.number, why = whyOf(row), [other, setOther] = useState(false), [text, setText] = useState(""), [busy, setBusy] = useState(false), [box, setBox] = useState(null), field = useRef();
  useLayoutEffect(() => { setBox(document.querySelector(`.hand-lifted[data-key="${CSS.escape(s.key)}"]`)); }, [s.key]);
  useEarlier(row, box);
  useEffect(() => { if (other) field.current?.focus({ preventScroll: true }); }, [other]);
  const choose = async (choice, words = "") => {
    setBusy(true);
    try {
      const got = await act("ideas.conflict", { idea: row.idea, number: n, choice, ...(words ? { text: words } : {}) });
      if (got) {
        const price = got.reworded && got.cost ? spendWords(got.cost.usd_high) : "";
        if (got.reworded) toast(`The Orkmaster words the decision again${price ? `: ${price}` : ""}`, "information");
        close?.();
      }
    } finally { setBusy(false); }
  };
  const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setOther(false); } };
  return html`<div class="hand-way hand-way--conflict" data-conflict=${n}>
    ${why && html`<div class="hand-way__why"><span class="ork-label">Why</span><p class="body">${why}</p></div>`}
    <p class="body hand-way__goes" data-line="goes"><b>${goesAgainst(n)}:</b> ${row.point || row.text}</p>
    ${other && html`<label class="hand-way__why hand-way__say"><span class="ork-label">${OTHER}</span>
      <textarea ref=${field} class="ork-field" aria-label="Say it in your own words" rows="4" maxlength="2000" value=${text} onInput=${(e) => setText(e.target.value)} onKeyDown=${key} placeholder="The Orkmaster words the decision again with them"></textarea></label>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Choices">
      <button type="button" class="ork-btn primary" data-choice="replace" disabled=${busy} title="The decision says it changes the earlier one, and its slices replace the earlier one's" onClick=${() => choose("replace")}>${replacesWords(n)}</button>
      <button type="button" class="ork-btn" data-choice="keep" disabled=${busy} title="The goal is talked again within the earlier decision" onClick=${() => choose("keep")}>${keepWords(n)}</button>
      ${other ? html`<button type="button" class="ork-btn" data-choice="other" disabled=${busy || !text.trim()} title="The decision is worded again with your words" onClick=${() => choose("other", text.trim())}>Send</button>
          <button type="button" class="ork-btn quiet" disabled=${busy} onClick=${() => { setOther(false); setText(""); }}>Cancel</button>`
        : html`<button type="button" class="ork-btn quiet" data-choice="other" disabled=${busy} title="Say it in your own words: the Orkmaster words the decision again" onClick=${() => setOther(true)}>${OTHER}</button>`}
    </div>
  </div>`;
}

// The face: the conflict sign, the Orkmaster as its asker, *Goes against §<n>* at its foot, no price (nothing is spent until the person answers).
way("conflict", { sign: "conflict", head: orkHead, foot: (s) => goesAgainst(s.row?.number), price: () => null, Lifted: ConflictLifted });
