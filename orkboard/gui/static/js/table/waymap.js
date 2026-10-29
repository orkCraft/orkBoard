// Marketing's map: the way in (docs/specs/102-the-other-maps-and-picking-on-them.md §3.3, §5.6; decisions §151.7, §171.1; mockup docs/mockups/s3/ state 6). Four steps as columns — *Channels*, *The store page or the site*, *The install*,
// *The first session* — and what each holds as cards (a file's name, its path in the label row, a two-tone sign of its kind); a step with nothing to read says *Nothing to read yet: …* and what would be read. At the narrow width the
// steps lie one under another. The files are read by name from dev's tree (`ideas.way_map`): no goal changed them, so a card carries no element and no gem. Registered with maps.js for the craft `marketing`.
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { mapFor } from "./maps.js";
import { FileLink, MapBack, MapCard, MapFrame, Nothing, Sec, Win, baseOf, keyOf, useLifted, useRead } from "./mapkit.js";

const MAP = "marketing";
const STEPS = [
  ["channels", "1 · Channels", "the campaigns' folders (marketing/, campaigns/, ads/, social/, press/)"],
  ["store", "2 · The store page or the site", "the store's metadata (fastlane/metadata/, store/) or the site's pages (landing/, site/, web/)"],
  ["install", "3 · The install", "the install's files (install.sh, a Dockerfile, fastlane/Fastfile)"],
  ["first_session", "4 · The first session", "the app's entry screen"],
];
const SIGNS = { channel: "horn", store: "store", site: "landing", install: "release", entry: "screen" };      // each kind's two-tone drawing
const KIND_WORDS = { channel: "A file of a folder for reaching people", store: "A file of the store's page: its words or its pictures", site: "A page of the site",
  install: "A file that puts the project on a machine", entry: "The app's entry screen: what a person sees first" };

function FileCard({ h, step }) {
  return html`<${MapCard} map=${MAP} id=${h.path} name=${baseOf(h.path)} code=${true} group=${step} row=${h.path} rowCode=${true} className="mp-file-card">
    <${Win}><${Sign} name=${SIGNS[h.kind] || "page"} big=${true} /></${Win}>
  </${MapCard}>`;
}

function Step({ id, head, what, hold, last }) {
  const left = Math.max(0, (hold.more || 0));
  return html`<section class="mp-step" data-step=${id} aria-label=${head}>
    <header class="mp-step__head"><span class="ork-label">${head}</span><span class="mp-grow"></span>${!last && html`<i class="ork-chev right mp-step__chev" aria-hidden="true"></i>`}</header>
    ${hold.none || !hold.holds.length ? html`<${Nothing} what=${what} />`
      : html`<div class="mp-grid mp-grid--step">${hold.holds.map((h) => html`<${FileCard} key=${h.path} h=${h} step=${id} />`)}</div>
        ${left > 0 && html`<span class="mp-more">and ${left} more</span>`}`}
  </section>`;
}

function Back({ h }) {
  const key = keyOf(MAP, h.path);
  return html`<h3 class="mp-back__nm is-code">${baseOf(h.path)}</h3>
    <p class="mp-back__line">${KIND_WORDS[h.kind] || "A file of the project"}</p>
    <${Sec} label="File"><${FileLink} path=${h.path} from=${key} /></${Sec}>`;
}

export function WayMap({ g, narrow }) {
  const host = useRef(), [rd] = useRead("ideas.way_map"), d = rd.data, at = useLifted(MAP);
  const hold = d ? STEPS.map(([id]) => d[id] || { holds: [], none: true, more: 0 }) : [];
  const file = at ? hold.flatMap((x) => x.holds).find((h) => h.path === at) : null;
  const back = file ? html`<${MapBack} host=${host} name=${baseOf(file.path)} narrow=${narrow}><${Back} key=${file.path} h=${file} /></${MapBack}>` : null;
  return html`<${MapFrame} map=${MAP} host=${host} back=${back} className="mp--way">
    ${d && html`<div class=${cls("mp-way", { "is-narrow": narrow })}>${STEPS.map(([id, head, what], i) => html`<${Step} key=${id} id=${id} head=${head} what=${what} hold=${hold[i]} last=${i === STEPS.length - 1} />`)}</div>`}
    ${!d && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}

mapFor(MAP, WayMap);
