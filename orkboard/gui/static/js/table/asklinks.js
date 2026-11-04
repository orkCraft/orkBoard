// A decision's number said in a leader's answer is a link (docs/specs/131-a-leaders-slices-and-the-cascade.md §C, decisions §233.3, §237.5): *§240.2* in the bubble's text, or in one of its sources, opens that decision over the pane
// (chronicle.js `openChronicle({decision})`), the entry with its *Changes* and *changed by*. What is not a number stays text. The bubble's text is plain, so nothing here reads Markdown.
import { html } from "../html.js";
import { openChronicle } from "./chronicle.js";

const LINK = /§(\d{1,5})(?:\.\d{1,3})?/g;

/** `text` as the parts the bubble draws: strings and, for each `§N` or `§N.k`, a quiet button that opens decision N. */
export function Linked({ text }) {
  const src = String(text || ""), out = [];
  let last = 0;
  for (const m of src.matchAll(LINK)) {
    if (m.index > last) out.push(src.slice(last, m.index));
    out.push(html`<button type="button" key=${m.index} class="table-ask__link" data-decision=${m[1]} title=${`Open decision ${m[1]}`} onClick=${() => openChronicle({ decision: Number(m[1]) })}>${m[0]}</button>`);
    last = m.index + m[0].length;
  }
  if (last < src.length) out.push(src.slice(last));
  return out;
}
