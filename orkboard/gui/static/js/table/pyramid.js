// The pyramid in the portal (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.3, decisions §254.7; mockup docs/mockups/table-edge/ section 5, *Or out of the portal itself*, the pyramid): the way into the past, in the ring's eye.
// The open tab's craft's last three decisions (`ideas.chronicle_last {party?, n: 3}`, by code; the whole project's on the Orkmaster's tab) stand as small face-up cards (56 x 78: the rune, the sign `page`, *§<n>*, the heads of the parties holding a slice of it),
// **the newest in front and whole, each older one smaller (0.74, 0.54) and darker (brightness 0.62, 0.42), higher, going into the swirl**: the depth is the age. A decision newer than the party's last look (pastseen.js) comes out to the front with its edge
// in the ink and the others step one deeper (one motion, none under reduced motion); else it lies still. A step hovered or focused rises whole under the ring (144 x 202: its title, its why in a line, its version); pressed, it opens the past
// (chronicle.js) with that card lit. **While something is ready for main or checked, or the rite plays, the pyramid is not drawn**: it sinks into the eye (once) and the ring is the gate's (`sunk`, from portal.js). Its sheet is pyramid.css.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { mapData } from "../shell/store.js";
import { reduced } from "../hand/motion.js";
import { partiesAll } from "./data.js";
import { ask, whose } from "./chronicleparts.js";
import { openChronicle } from "./chronicle.js";
import { UNRELEASED } from "./chroniclewords.js";
import { seenOf, seenTick, setSeen } from "./pastseen.js";

if (typeof document !== "undefined") {                                  // the sheet, once
  const href = new URL("./pyramid.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const SCALES = [1, 0.74, 0.54], DARK = [1, 0.62, 0.42];
export const STEP_MS = 420, SINK_MS = 360, READ_WAIT = 400;
const whys = {};                                                         // a decision's why, read once a page when its step rises (`ideas.chronicle_decision`)

/** The first line of a decision's *Why*, from its entry. */
const whyOf = (entry) => (/^Why:[ \t]*(.+)$/m.exec(String(entry || ""))?.[1] || "").trim();

const headsOf = (slugs) => (slugs || []).map((s) => partiesAll().find((g) => g.slug === s)?.leader?.head).filter(Boolean).slice(0, 2);

/** A step's place (its age 0 the front): how far above the eye's middle, how small, how dark. */
const placeOf = (age) => ({ y: [24, -18, -50, -70][age] ?? -70, s: SCALES[age] ?? 0.4, b: DARK[age] ?? 0.3 });

function Step({ d, age, fresh, from, onRise, onLeave }) {
  const p = placeOf(age), q = from === null ? p : placeOf(from), heads = headsOf(d.parties);
  const [at, setAt] = useState(q), ref = useRef();
  useLayoutEffect(() => {                                                // one motion: from where it lay to its step (a new one from deeper than the deepest)
    if (from === null || reduced()) { setAt(p); return undefined; }
    const id = requestAnimationFrame(() => requestAnimationFrame(() => setAt(p)));
    return () => cancelAnimationFrame(id);
  }, [age, from]);
  return html`<button type="button" ref=${ref} class=${cls("ork-card pyramid__step", { "is-new": fresh, "is-moving": from !== null })} data-age=${age} data-decision=${d.number}
      style=${`transform:translateY(${at.y}px) scale(${at.s});filter:brightness(${at.b});z-index:${4 - age}`} aria-label=${`§${d.number} ${d.title}: open the past`}
      onMouseEnter=${() => onRise(d)} onFocus=${() => onRise(d)} onMouseLeave=${onLeave} onBlur=${onLeave} onClick=${() => openChronicle({ lit: d.number })}>
    <span class="pyramid__top"><${Elem} name=${d.element || ""} dim=${!d.element} /><${Sign} name="page" /></span>
    <span class="pyramid__n">§${d.number}</span>
    <span class="pyramid__bot">${heads.map((h, i) => html`<${Head} key=${i} race=${h.race} tier=${h.tier} />`)}</span>
  </button>`;
}

/** The step hovered or focused, whole, under the ring: its title, its why in a line, its version. */
function Rise({ d }) {
  const [why, setWhy] = useState(whys[d.number] ?? "");
  useEffect(() => {
    if (d.number in whys) { setWhy(whys[d.number]); return undefined; }
    let live = true;
    ask("ideas.chronicle_decision", { number: d.number }).then(([r]) => { whys[d.number] = whyOf(r?.entry); if (live) setWhy(whys[d.number]); });
    return () => { live = false; };
  }, [d.number]);
  const heads = headsOf(d.parties);
  return html`<span class="ork-card pyramid__rise" role="tooltip" data-rise=${d.number}>
    <span class="corner corner--top"><span class="corner__rune"><${Elem} name=${d.element || ""} dim=${!d.element} /></span><span class="corner__kind"><${Sign} name="page" /></span></span>
    <span class="pyramid__ti">§${d.number} · ${d.title}</span>
    ${why && html`<span class="pyramid__why">${why}</span>`}
    <span class="corner corner--foot"><span class="corner__who">${heads.map((h, i) => html`<${Head} key=${i} race=${h.race} tier=${h.tier} />`)}</span><span class="corner__much" data-much="version">${d.version || UNRELEASED}</span></span>
  </span>`;
}

/** The pyramid in the ring's eye. `sunk`: something is ready for main, checked or sent: it sinks and is not drawn. */
export function Pyramid({ sunk = false }) {
  const { party } = whose(), rev = mapData.value?.rev, [list, setList] = useState(null), [rise, setRise] = useState(null), [gone, setGone] = useState(sunk), [sinking, setSinking] = useState(false);
  const was = useRef({ party: null, numbers: [] }), [moved, setMoved] = useState({});
  useEffect(() => {                                                      // the open tab's last three, read again when the tab or the Board changes
    if (sunk) return undefined;
    let live = true;
    const id = setTimeout(() => ask("ideas.chronicle_last", { ...(party ? { party } : {}), n: 3 }).then(([r]) => { if (live) setList((r?.decisions || []).slice(0, 3)); }), list ? READ_WAIT : 0);
    return () => { live = false; clearTimeout(id); };
  }, [party, rev, sunk]);
  useEffect(() => {                                                      // ready for main: it sinks into the eye, once, then it is not drawn
    if (sunk && !gone) {
      if (reduced()) { setGone(true); return undefined; }
      setSinking(true);
      const t = setTimeout(() => { setGone(true); setSinking(false); }, SINK_MS);
      return () => clearTimeout(t);
    }
    if (!sunk && gone) setGone(false);
    return undefined;
  }, [sunk]);
  useLayoutEffect(() => {                                                // where each step lay before this read: a new one comes out to the front, the others step one deeper; the same tab's first read lies still
    if (!list) return;
    const numbers = list.map((d) => d.number), before = was.current;
    const next = {};
    if (before.party === party) numbers.forEach((n, i) => { const j = before.numbers.indexOf(n); if (j !== i) next[n] = j < 0 ? 3 : j; });
    else if (seenOf(party) === null && numbers.length) setSeen(party, numbers[0]);          // never looked at: nothing is new
    else { const seen = seenOf(party) ?? 0; if (numbers[0] > seen) numbers.forEach((n, i) => { next[n] = n > seen ? 3 : Math.max(0, i - 1); }); }
    was.current = { party, numbers };
    setMoved(next);
  }, [list]);
  seenTick.value;                                                        // a look written: the mark is read again
  if (gone || !list || !list.length) return null;
  const seen = seenOf(party) ?? Infinity;
  return html`<span class=${cls("pyramid", { "is-sinking": sinking })} data-party=${party || "orkmaster"}>
    ${list.map((d, age) => ({ d, age })).reverse().map(({ d, age }) => html`<${Step} key=${d.number} d=${d} age=${age} fresh=${age === 0 && d.number > seen} from=${d.number in moved ? moved[d.number] : null}
      onRise=${setRise} onLeave=${() => setRise(null)} />`)}
    ${rise && !sinking && html`<${Rise} key=${rise.number} d=${rise} />`}
  </span>`;
}
