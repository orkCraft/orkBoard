// A leader's header (docs/specs/168 E1, decisions §283.16.2, §283.20, §283.21; mockup docs/mockups/table-template/ shot 8): with no goal picked the leader's tab shows its project, and over its scheme a header **held while the table scrolls**, in three groups of small cards,
// every card 56 x 78 (smallcard.js, with its preview on hover: preview.js):
//  - **At work**: this leader's goals in flight: their ideas and specs face down (a back with the goal's rune), their implementation face up; pressed, the goal is picked and this leader's table of its stage opens (stageboard.js `open`, phaseview.js).
//  - **Concerns**: its open concerns face down with the goal's rune or a + (concernrow.js); pressed, lifted and played as the hand plays it: *Not a problem*, *Later*, *Make it a goal* (hand/concernplay.js).
//  - **Ask**: the ? card; pressed, it opens the quick question to this leader (ask.js `openAsk`: the one bubble the head's press also opens; the answer comes back as the ? card in the hand, hand/askcard.js). **A hand to take the scheme's parts into it** (askparts.js): while the
//    question is open a press on a part of the scheme names that part in the question, as the chip with × says.
// Its seats and tools are not here any more: they lie in the leader's inventory (stallseats.js) and its … menu (the pane title's, partymenu.js). The aspects it looks at (concerns.js `Aspects`) keep their place at the header's right. At the narrow width the header is the squad's, as it was (header.js).
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { mapData } from "../shell/store.js";
import { askOpen, askPart, closeAsk, openAsk } from "./ask.js";
import { Aspects } from "./concerns.js";
import { ConcernCards } from "./concernrow.js";
import { partiesAll } from "./data.js";
import { SmallCard } from "./smallcard.js";
import { backSpec, withPreview } from "./preview.js";
import { kindOf } from "./stages.js";
import { leadersOf, open } from "./stageboard.js";
import { useTakingParts } from "./askparts.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./leaderhead.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const SHOWN = 5;                                                 // the cards a group draws at most; never a count of the rest

/** This leader's goals in flight, in the Board's order: `{back: [...]}` its ideas and specs (face down), `{face: [...]}` its implementation (face up). A goal lies where `kindOf` (stages.js) puts it, with this leader on its route or a task of its own. */
export function atWork(g, nodes = mapData.value?.nodes || []) {
  const mine = (n) => n.place === "table" && !n.folded && (leadersOf(n).includes(g.slug) || (n.tasks || []).some((t) => (t.party || n.goal) === g.slug));
  const back = [], face = [];
  for (const n of nodes) {
    const k = kindOf(n);
    if (!k || !mine(n)) continue;
    (k.pile === "work" ? face : back).push({ n, pile: k.pile });
  }
  return { back, face };
}

const BACK_LINE = { analysis: "Idea · its leaders talk it over", review: "Spec · being written, or ready" };

/** A goal's small back: its rune on the seal; face down, as an idea and a spec lie in the Board's column. */
function GoalBack({ n, g, pile }) {
  const el = n.element || "", hue = n.hue || el, name = n.title || n.short || "";
  const props = withPreview({ class: "ork-card sb-back hd-back", "data-goal": n.slug, "data-party": g.slug, "data-stage": pile === "analysis" ? "idea" : "spec", "aria-label": `${name}: ${pile === "analysis" ? "idea" : "spec"}` }, backSpec(name, BACK_LINE[pile], n));
  return html`<button type="button" ...${props} onClick=${() => open(n.slug, g.slug)}><span class="ork-card-back small" aria-hidden="true"><span class="ork-card-back__seal"><${Elem} name=${el} hue=${hue} dim=${!el} /></span></span></button>`;
}

/** The ? card: the quick question to this leader. Pressed it opens the bubble under the leader's head (and shuts it again); it says how many parts it has taken in. */
function AskCard({ g }) {
  const on = askOpen.value === g.slug, part = on ? askPart.value : null, name = g.leader?.name || "its leader";
  const props = withPreview({ class: cls("ork-card sm hd-ask", { "is-open": on }), "data-ask-card": g.slug, "aria-pressed": String(on), "aria-label": part ? `Ask ${name}, about ${part.name}` : `Ask ${name} a quick question`,
    "aria-expanded": String(on) }, () => ({ mode: "face", name: `Ask ${name}`, element: "", hue: "", kind: "question", signal: "", picture: "", node: null }));
  return html`<button type="button" ...${props} onClick=${() => (on ? closeAsk() : openAsk(g.slug, part))}><span class="sm-pic" aria-hidden="true"><${Sign} name="question" big=${true} /></span>${part && html`<span class="hd-ask__part" aria-hidden="true">${part.name}</span>`}</button>`;
}

const Group = ({ id, word, children }) => html`<section class="hd-group" data-group=${id} aria-label=${word}><span class="ork-label hd-group__label">${word}</span><div class="hd-group__cards">${children}</div></section>`;

export function LeaderHead({ g }) {
  const { back, face } = atWork(g), parties = partiesAll(), partyOf = (s) => parties.find((x) => x.slug === s), shown = [...back, ...face].slice(0, SHOWN);
  useTakingParts(g.slug);
  return html`<section class="table-head hd" aria-label=${`${g.leader?.name || g.name || "Leader"}: its project`} data-party=${g.slug}>
    ${shown.length > 0 && html`<${Group} id="work" word="At work">${shown.map(({ n, pile }) => (pile === "work"
      ? html`<${SmallCard} key=${n.slug} n=${n} parties=${leadersOf(n).map(partyOf).filter(Boolean)} signal=${n.asks_you ? "alert" : (n.tasks || []).some((t) => t.state === "failed") ? "danger" : ""} onPress=${() => open(n.slug, g.slug)} extra=${{ "data-party": g.slug, "data-stage": "work" }} />`
      : html`<${GoalBack} key=${n.slug} n=${n} g=${g} pile=${pile} />`))}<//>`}
    ${(g.concerns?.list || []).length > 0 && html`<${Group} id="concerns" word="Concerns"><${ConcernCards} g=${g} /><//>`}
    <${Group} id="ask" word="Ask"><${AskCard} g=${g} /><//>
    <span class="table-grow"></span>
    <${Aspects} g=${g} />
  </section>`;
}
