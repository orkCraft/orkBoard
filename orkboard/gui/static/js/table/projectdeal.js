// The project in the Orkmaster's header (docs/specs/160-the-tables-look-and-the-rooms-things.md stage J, decisions §272.5): the header's second line says the project's kind and stage in the caption face (*Game · Being made*); pressed, the kind or the stage
// deals its choices to the hand as the answer cards are dealt (hand/answercards.js): the Orkmaster's question rises onto the table, each choice is a 144 x 202 card in the hand's row with its one line of what changes, the present one marked, the rest of the
// hand sunk. A card pressed sends `ideas.project_kind_set` or `ideas.stage_set` once; *Put it back* and Esc send nothing. Wide only (760 px and over): the narrow page keeps its head. What the host says is `ideas.stage` (stage, kind, the crafts each stage offers).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { command } from "../link.js";
import { ask } from "../board/store.js";
import { CornerFoot, CornerTop } from "./corners.js";
import { KINDS, STAGES, STAGE_WORDS } from "./parties.js";

export const dealt = signal("");                          // "kind" | "stage" | "": which choice the hand holds
export const projectNow = signal(null);                   // `ideas.stage` as the host last said it, null until it has
const CROWN = { race: "peon", tier: "crown" };            // the Orkmaster's head: it asks, as any leader

/** *a game* → *Game*, *a team's wiki* → *Team's wiki*: the kind as the header and its cards say it. */
export const kindWord = (words) => { const w = String(words || "").replace(/^an? /, ""); return w.charAt(0).toUpperCase() + w.slice(1); };
const kindsOf = (id) => (!id || KINDS.some(([k]) => k === id) ? KINDS : [...KINDS, [id, id]]);
const wordsOfKind = (id) => KINDS.find(([k]) => k === id)?.[1] || id;

/** The kind and the stage as the host last said them, asked when the project is (or `again` changes); null while it has not said. */
export function useProjectNow(again) {
  useEffect(() => {
    let live = true;
    command("ideas.stage", {}, true).then((r) => { if (live && r && !r.error && r.stage) projectNow.value = r; }).catch(() => {});
    return () => { live = false; };
  }, [again]);
  return projectNow.value;
}

/** The line of a stage: what it adds to the chair's crafts, from the crafts the host offers there (`offered[stage]`, a card's `from` is the stage that adds it; Release is offered at every stage and adds nothing). "" when the host names none. */
export function stageLine(now, stage) {
  const names = (now?.offered?.[stage] || []).filter((c) => c.from === stage && c.craft !== "release").map((c) => c.name), many = names.length > 1;
  if (!names.length) return "";
  const list = many ? `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}` : names[0];
  return stage === STAGES[0] ? `${list} ${many ? "are" : "is"} the chair's first ${many ? "crafts" : "craft"}` : `${list} ${many ? "join" : "joins"} the chair's crafts`;
}

/** The ways of a choice as cards: `{id, name, line, here}`. A kind's line is the one thing the host does not list per kind: the chair's crafts are fitted to it. */
function waysOf(which, now) {
  if (which === "kind") return kindsOf(now.kind).map(([id, words]) => ({ id, name: kindWord(words), line: `The chair's crafts are fitted to ${words}.`, here: id === now.kind }));
  return STAGES.map((s) => ({ id: s, name: STAGE_WORDS[s], line: stageLine(now, s), here: s === now.stage }));
}

/** The header's second line: the kind and the stage, two buttons in the caption face. Nothing until the host has said. */
export function ProjectLine({ now }) {
  if (!now) return null;
  const pressed = (which) => () => { dealt.value = dealt.value === which ? "" : which; };
  const kind = now.kind ? kindWord(wordsOfKind(now.kind)) : "", stage = STAGE_WORDS[now.stage] || now.stage;
  const one = (which, word, said) => html`<button type="button" class="col-head__pick" data-deal=${which} aria-haspopup="dialog" aria-expanded=${String(dealt.value === which)} aria-label=${said} title=${said} onClick=${pressed(which)}>${word}</button>`;
  return html`<div class="col-head__sub" data-project-line>${kind && html`${one("kind", kind, `What the project is: ${kind}. Press to choose`)}<span class="col-head__dot" aria-hidden="true"> · </span>`}${one("stage", stage, `Where the project is: ${stage}. Press to choose`)}</div>`;
}

/** One choice as a hand card: a sign at the top, its name (the pixel face), its one line, and at the foot the mark of the present one. */
function Way({ w, run }) {
  return html`<button type="button" class=${cls("ork-card hand-ans", { "is-pick": w.here })} data-way=${w.id} data-pick=${w.here ? "1" : undefined} aria-pressed=${String(w.here)} aria-label=${`${w.name}${w.here ? ", the project is here" : ""}${w.line ? `: ${w.line}` : ""}`} title=${w.line || w.name} onClick=${run}>
    <${CornerTop} kind="compass" />
    <span class="hand-ans__name">${w.name}</span>
    ${w.line && html`<span class="hand-ans__line">${w.line}</span>`}
    <${CornerFoot} who=${w.here ? { heads: [CROWN], word: "here now" } : null} />
  </button>`;
}

/** What the hand holds while a choice is dealt: the question risen at the table's foot, its ways in the hand's row, *Put it back* at the row's end. */
export function ProjectDeal({ which }) {
  const now = projectNow.value, box = useRef(), row = useRef(), [at, setAt] = useState(null), busy = useRef(false);
  const close = () => { dealt.value = ""; };
  useLayoutEffect(() => {                                                // as AnswerLifted: the ways after the question, the sunk hand shrunk into the strip right of them
    const place = () => {
      const hand = box.current?.parentElement, r = row.current?.getBoundingClientRect();
      if (!hand) return;
      const h = hand.getBoundingClientRect(), plus = hand.querySelector(".hand-plus")?.getBoundingClientRect(), ways = Math.max(0, plus ? plus.right - h.left + 28 : 200);
      const end = r && r.width ? r.right - h.left : h.width;
      hand.style.setProperty("--hc-sunk-s", String(Math.max(0.2, Math.min(0.5, (h.width - end - 16) / h.width))));
      setAt({ ways, left: Math.max(0, Math.min(end - 144, h.width - 144 - 12)) });
    };
    place();
    const watch = typeof ResizeObserver === "function" && row.current ? new ResizeObserver(place) : null;
    watch?.observe(row.current);
    window.addEventListener("resize", place);
    return () => { watch?.disconnect(); window.removeEventListener("resize", place); box.current?.parentElement?.style.removeProperty("--hc-sunk-s"); };
  }, [which, !now]);
  useEffect(() => {
    box.current?.focus({ preventScroll: true });
    row.current?.querySelector(".is-pick")?.scrollIntoView?.({ inline: "center", block: "nearest" });
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); e.stopPropagation(); close(); } };
    addEventListener("keydown", esc, true);
    return () => { removeEventListener("keydown", esc, true); setTimeout(() => document.querySelector(`.col-head__pick[data-deal="${which}"]`)?.focus({ preventScroll: true }), 0); };
  }, [which, !now]);
  if (!now) return null;
  const ways = waysOf(which, now), kind = which === "kind";
  const pick = async (w) => {
    if (busy.current) return;
    if (w.here) { close(); return; }                                      // the present one: nothing changes, nothing is sent
    busy.current = true;
    try {
      const got = await ask(kind ? "ideas.project_kind_set" : "ideas.stage_set", kind ? { kind: w.id } : { stage: w.id });
      if (got) {
        const fresh = kind ? await command("ideas.stage", {}, true).catch(() => null) : got;           // a kind corrected changes the parties fitted to it: the host is asked what it says now
        if (fresh && fresh.stage) projectNow.value = fresh;
        close();
      }
    } finally { busy.current = false; }
  };
  const title = kind ? "What is the project?" : "Where is the project?", foot = kind ? kindWord(wordsOfKind(now.kind)) : STAGE_WORDS[now.stage];
  return html`<aside ref=${box} class="ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked asks" role="dialog" tabindex="-1" aria-label=${`The Orkmaster asks: ${title}`} data-project-deal=${which} style=${at ? `left:${at.left}px` : undefined}>
    <${CornerTop} kind="compass" signal="alert" />
    <span class="hand-card__name">${title}</span>
    <span class="hand-card__foot">${foot}</span>
    <${CornerFoot} who=${{ heads: [CROWN], word: "" }} />
  </aside>
  <div ref=${row} class="hand-ways-row" role="group" aria-label=${kind ? "The kinds" : "The stages"} style=${at ? `--hc-wleft:${at.ways}px` : undefined}>
    <div class="hand-ways-cards">${ways.map((w) => html`<${Way} key=${w.id} w=${w} run=${() => pick(w)} />`)}</div>
    <div class="hand-ways-acts"><button type="button" class="ork-btn hand-put" data-act="put" onClick=${close}>Put it back</button></div>
  </div>`;
}
