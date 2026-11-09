// A spec through a leader (docs/specs/168 C4, decisions §283.16.6; mockup docs/mockups/table-template/ shot 8's header): **a header of its steps' small cards** (56 x 78, smallcard.js) each with its seats' heads and tools, **a seat whose tool cannot do what
// its step needs marked !** (a browser for its tests, git's index, the network, a command not on the path: what trials 149, 152-e and 160 hit; the host says it in the map node's `steps`, realm/step_needs.py, over `harnesses.can`); under it the parts
// of the leader's scheme the spec changes, **now and as they will be**: what is new as a ghost, what changes outlined, what goes struck through, and Design's screens' picture where one was made. Under both, the leader's section as written (specpage.js).
// The parts are the *Will be* lines of its section (goalmap.js `partsOf`), the map as the host reads it (`useMap`). Layout: spec.css (sheet of the Spec page).
import { html, cls } from "../html.js";
import { Head, Icon, Sign } from "../orkui.js";
import { SmallCard } from "./smallcard.js";
import { partFor, partsOf, useMap } from "./goalmap.js";
import { Pair } from "./goalview.js";
import { PartySection, readSpec, usePage } from "./specpage.js";
import { nameOf, partiesAll } from "./data.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./specsteps.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const LACK_WORDS = { browser: "a browser", git: "git's index", network: "the network" };
const lackWords = (lacks) => lacks.map((x) => LACK_WORDS[x] || (x.startsWith("command:") ? `the command ${x.slice(8)}` : x)).join(", ");

/** One seat: its head, its tool (the Main tool where none is named) and, where the tool cannot do what the step needs, a **!** that says what is missing. */
export function SeatMark({ seat }) {
  const tool = seat.tool_name || "Main tool";
  return html`<li class=${cls("spec-seat", { "is-lacking": seat.marked })} data-seat=${seat.slug} data-tool=${seat.tool || "main"} data-lacks=${seat.lacks.join(" ") || undefined}
    title=${seat.marked ? `${tool} cannot do what this step needs: ${lackWords(seat.lacks)}` : tool}>
    ${seat.head && html`<${Head} race=${seat.head.race} tier=${seat.head.tier} />`}<span class="spec-seat__tool">${tool}</span>
    ${seat.marked && html`<span class="spec-seat__lack" role="img" aria-label=${`${tool} cannot do what this step needs: ${lackWords(seat.lacks)}`}><${Sign} name="alert" /></span>`}</li>`;
}

/** The header: a small card for each step of the route, its party's name and its seats under it. */
export function StepsHeader({ n }) {
  const parties = partiesAll(), steps = n.steps || [];
  if (!steps.length) return null;
  const slugs = steps.map((s) => s.party);
  return html`<ol class="spec-steps" aria-label="The steps">${steps.map((s, i) => html`<li key=${s.party} class=${cls("spec-step", { "is-mine": s.own })} data-step=${s.party} data-marked=${s.marked ? "1" : undefined}>
    <${SmallCard} n=${n} parties=${slugs.map((p) => parties.find((g) => g.slug === p) || p)} done=${slugs.slice(0, i)} preview=${false} extra=${{ "data-step-card": s.party }}
      picture=${s.leader ? html`<${Head} race=${s.leader.race} tier=${s.leader.tier} size="mid" />` : null} />
    <div class="spec-step__who"><b class="spec-step__nm">${s.name}</b>
      <ul class="spec-step__seats" aria-label=${`${s.name}'s seats`}>${s.seats.map((x) => html`<${SeatMark} key=${x.slug || x.name} seat=${x} />`)}</ul></div></li>`)}</ol>`;
}

/** The parts the spec changes, each *Now* and *As it will be*: new a ghost, changed outlined, gone struck through; Design's screens as their picture and the wireframe. */
export function SpecParts({ g, will }) {
  const info = useMap(g), parts = partsOf(will, info).filter((p) => p.kind !== "read");
  if (!parts.length) return null;
  return html`<section class="spec-parts" aria-label="The parts it changes">
    <div class="spec-parts__hd"><span class="ork-label">Now</span><span class="ork-label">As it will be</span></div>
    <ul class="spec-parts__list">${parts.map((p) => {
      const now = partFor(info, p.id), sign = { new: "+", changed: "~", gone: "-" }[p.kind] || "·";
      return html`<li key=${p.id} class=${cls("spec-part", `is-${p.kind}`)} data-part=${p.id} data-kind=${p.kind}>
        <div class="spec-part__now" data-side="now"><b>${p.name}</b>${now ? html`<span class="cap">${(now.uses || []).length ? `uses ${now.uses.length}` : "stands alone"}</span>` : html`<em class="cap">none yet</em>`}</div>
        ${info?.kind === "screens" && p.kind !== "gone" ? html`<${Pair} part=${p} info=${info} />` : html`<span class="spec-part__arrow"><${Icon} name="arrow-right" /></span>`}
        <div class="spec-part__will" data-side="will"><b class="spec-part__nm">${p.kind === "gone" ? html`<s>${p.name}</s>` : p.name}</b><span class="cap">${sign} ${p.note || p.lines[0]?.replace(/^[+~-]\s*/, "") || ""}</span></div>
      </li>`;
    })}</ul></section>`;
}

/** A spec through the leader `g`: the steps, the parts now and as they will be, the section as written. */
export function SpecTable({ n, g }) {
  const page = usePage(n.slug), parties = partiesAll(), spec = page ? readSpec(page, parties, parties.find((x) => x.slug === n.goal) || null).sections.find((s) => s.party?.slug === g.slug) || null : null;
  return html`<div class="phase-view spec-table" data-view="spec" data-goal=${n.slug} data-party=${g.slug} aria-label=${`${nameOf(g)}'s spec of ${n.title}`}>
    <${StepsHeader} n=${n} />
    ${spec && html`<${SpecParts} g=${g} will=${spec.will} />`}
    <${PartySection} idea=${n.slug} party=${g.slug} />
  </div>`;
}
