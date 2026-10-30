// The goal's Spec on the pane (docs/specs/100-a-goals-way-as-cards.md §3.2; docs/specs/99-a-goals-way.md §7.1; decisions §117.3, §118.3): the spec as its format has it — the common part (*Asked*, *Gist*, *Route*, *Depends on*,
// *Decisions*), then a section a party on the route, each with its leader's head and its party's name, its *Done when* at the left and its *Will be* (the parts of its map by their ids) at the right. While a fork of the goal is open
// (the Board's `fork` row) the sections of its sides are lit, and in each the lines that say what the side says. Props: `{idea}`. Registered as the pane's kind `spec` (frame/kinds.js); a fork's card lays it under its sides
// (hand/forkcard.js). It reads the page once and again when the Board changes (`ideas.page`: `sections` `{name, text}`, the party sections' text holding their `###` parts); an older page, with no party's section, reads as one
// section of the goal's party (decisions §118.8).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { board } from "../board/store.js";
import { command } from "../link.js";
import { mapData } from "../shell/store.js";
import { Elem, Head } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { nameOf, partiesAll } from "./data.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./spec.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const COMMON = ["Asked", "Gist", "Route", "Depends on", "Decisions"];
const OLD = ["Why", "Done when", "Out", "Risks"];                       // the old sections a page of before keeps under its party (realm/spec_sections.py `FOLDED`)
const RESERVED = new Set([...COMMON, ...OLD, "Stages", "Open questions", "Checks", "Will be", "Defaults", "Questions", "Plan"].map((x) => x.toLowerCase()));
const WILL = /^(?:[-*]\s*)?(new|changed|gone)\s+(?:part\s+)?([A-Za-z0-9_./@:\\-]+)(?:\s*[—–-]+\s*(.*))?$/i;

/** A section's `###` parts by name, in order (realm/spec_sections.py `split`); what stands before the first one is kept under `""`. */
export function partsOf(text) {
  const src = String(text || "").replace(/\r\n/g, "\n"), out = {}, heads = [...src.matchAll(/^###[ \t]+(.+?)[ \t]*#*[ \t]*$/gm)];
  if (!heads.length) { if (src.trim()) out[""] = src.trim(); return out; }
  if (src.slice(0, heads[0].index).trim()) out[""] = src.slice(0, heads[0].index).trim();
  heads.forEach((m, i) => { out[m[1].trim()] = src.slice(m.index + m[0].length, i + 1 < heads.length ? heads[i + 1].index : src.length).trim(); });
  return out;
}

/** The lines of a part, bullets and numbers and bold taken off. */
export const linesOf = (text) => String(text || "").split("\n").map((l) => l.replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "").replace(/\*\*|__/g, "").trim()).filter(Boolean);

/** *Will be* as `[{kind: new|changed|gone, id, note}]`; a line that is none of these is kept as a note of no kind. */
export function willBe(text) {
  return String(text || "").split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
    const m = WILL.exec(l);
    return m ? { kind: m[1].toLowerCase(), id: m[2], note: (m[3] || "").trim() } : { kind: "", id: "", note: l.replace(/^[-*]\s*/, "") };
  });
}

const words = (t) => new Set(String(t || "").toLowerCase().match(/[\p{L}\p{N}]{3,}/gu) || []);
/** Whether a line says (a good part of) what a side says: at least two words they share, and a third of the side's words. */
export function sharesWords(line, says) {
  const a = words(line), b = words(says);
  let n = 0;
  for (const w of b) if (a.has(w)) n += 1;
  return n >= 2 && n >= b.size / 3;
}

const norm = (t) => String(t || "").toLowerCase().replace(/\s*\(party\)\s*$/, "").trim();
const partyOf = (name, parties) => parties.find((g) => [nameOf(g), g.title, g.slug].some((x) => x && norm(x) === norm(name))) || null;

/** The page's sections made into `{common: [{name, text}], sections: [{name, party: g|null, done: [lines], will: [{kind,id,note}]}]}`. `home`: the goal's party, for a page of before. */
export function readSpec(page, parties, home) {
  const all = (page?.sections || []).map((x) => ({ name: String(x.name || ""), text: String(x.text || "") })), have = (n) => all.find((x) => norm(x.name) === norm(n));
  const common = COMMON.map((n) => have(n)).filter((x) => x && x.text.trim()).map((x) => ({ ...x, name: COMMON.find((n) => norm(n) === norm(x.name)) }));
  const sections = all.filter((x) => !RESERVED.has(norm(x.name)) && x.text.trim() && Object.keys(partsOf(x.text)).some((k) => k && ["done when", "will be", "why", "checks"].includes(k.toLowerCase())))
    .map((x) => {
      const p = partsOf(x.text), at = (n) => p[Object.keys(p).find((k) => k.toLowerCase() === n) || ""] || "";
      return { name: x.name, party: partyOf(x.name, parties), done: linesOf(at("done when")), will: willBe(at("will be")) };
    });
  if (!sections.length) {                                               // a page of before: one section of its party
    const done = have("Done when");
    if (done?.text.trim()) sections.push({ name: nameOf(home) || "", party: home, done: linesOf(done.text), will: [] });
  }
  return { common, sections };
}

/** The first open fork of the goal on the Board, null for none. */
export const forkOf = (idea) => (board.value?.needs_you || []).find((r) => r.kind === "fork" && r.idea === idea) || null;

/** The page of a goal, read now and again when the Board changes. */
function usePage(idea) {
  const [page, setPage] = useState(undefined), rev = board.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.page", { slug: idea }, true).then((p) => { if (live) setPage(p && !p.error ? p : null); }).catch(() => { if (live) setPage((was) => was || null); });
    return () => { live = false; };
  }, [idea, rev]);
  return page;
}

function Line({ text, lit }) {
  return html`<li class=${cls("spec-line", { "is-lit": lit })} data-lit=${lit ? "1" : undefined}>${text}</li>`;
}

function Will({ w }) {
  return html`<li class="spec-line spec-will" data-will=${w.kind || undefined}>${w.id ? html`<span class="ork-label spec-will__kind">${w.kind}</span> <code class="spec-will__id">${w.id}</code>${w.note ? html` <span class="spec-will__note">${w.note}</span>` : ""}` : w.note}</li>`;
}

function Section({ sec, lit, says }) {
  const g = sec.party, head = g?.leader?.head, match = (l) => lit && says.some((t) => sharesWords(l, t));
  return html`<li class=${cls("spec-section", { "is-lit": lit })} data-party=${g?.slug || ""} data-lit=${lit ? "1" : undefined}>
    <div class="spec-section__head">${head && html`<${Head} race=${head.race} tier=${head.tier} size="mid" />`}<span class="spec-section__nm">${nameOf(g) || sec.name}</span>
      ${lit && html`<span class="ork-label spec-section__flag">Disagrees</span>`}</div>
    <div class="spec-section__cols">
      <div class="spec-col" data-part="done"><span class="ork-label">Done when</span>
        ${sec.done.length ? html`<ul class="spec-list">${sec.done.map((l, i) => html`<${Line} key=${i} text=${l} lit=${match(l)} />`)}</ul>` : html`<p class="table-over__muted">Nothing yet.</p>`}</div>
      ${sec.will.length > 0 && html`<div class="spec-col" data-part="will"><span class="ork-label">Will be</span>
        <ul class="spec-list">${sec.will.map((w, i) => html`<${Will} key=${i} w=${w} />`)}</ul></div>`}
    </div>
  </li>`;
}

export function SpecPage({ props }) {
  const idea = props?.idea, page = usePage(idea), parties = partiesAll(), node = (mapData.value?.nodes || []).find((n) => n.slug === idea) || null;
  const fork = forkOf(idea), sides = (fork?.sides || []).filter((s) => s && s.party), lit = new Set(sides.map((s) => s.party));
  if (page === undefined) return html`<p class="table-over__muted" data-kind="spec">Reading the spec…</p>`;
  if (!page) return html`<p class="table-over__muted" data-kind="spec">The spec could not be read now.</p>`;
  const { common, sections } = readSpec(page, parties, parties.find((g) => g.slug === node?.goal) || null);
  return html`<article class="spec-page" data-kind="spec" data-idea=${idea} aria-label="Spec">
    <header class="spec-page__head"><${Elem} name=${node?.element || ""} dim=${!node?.element} /><h2 class="spec-page__title">${node?.title || page.title || idea}</h2><span class="ork-label">Spec</span></header>
    ${common.length > 0 && html`<dl class="spec-common">${common.map((c) => html`<div class="spec-common__one" key=${c.name} data-part=${c.name}><dt class="ork-label">${c.name}</dt><dd class="body">${c.text.trim()}</dd></div>`)}</dl>`}
    ${sections.length > 0
      ? html`<ol class="spec-sections" aria-label="The sections">${sections.map((sec, i) => {
          const mine = sec.party && lit.has(sec.party.slug);
          return html`<${Section} key=${sec.party?.slug || i} sec=${sec} lit=${!!mine} says=${sides.filter((s) => s.party === sec.party?.slug).map((s) => s.says)} />`;
        })}</ol>`
      : html`<p class="table-over__muted">No section is written yet.</p>`}
  </article>`;
}
drawn("spec", SpecPage);
