// Game design's map: the loop (docs/specs/102-the-other-maps-and-picking-on-them.md §2, §5.3; decisions §112.8, §171.1; mockup docs/mockups/s3/ state 3). Four to six cards in a ring with a chevron between each, round and round,
// or a row wrapped two a line at the narrow width; each its name, its window with the loop's sign, *Proposed by <party>* (its leader's head at the right) or *Yours*, its line. Lifted, a card shows what it rests on (each file a press that
// opens it over the pane) and **Edit** (its name, line and files: `ideas.loop_set`); with no loop kept, **Propose** (`ideas.loop_propose`: one call of the party's leader, never made unasked). Registered with maps.js for the craft `game-design`.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { nameOf } from "./data.js";
import { mapFor } from "./maps.js";
import { FileLink, MapBack, MapCard, MapFrame, Nothing, Sec, Win, keyOf, useLifted, useRead, useWidth } from "./mapkit.js";

const MAP = "game-design", NONE_WHAT = "the game's configs", POLL_MS = 2500;
const STEPS = { 4: "Four", 5: "Five", 6: "Six" };
const CARD_W = 256, RING_H = 470, RING_MIN = 640;

/** The cards' places on the ring, clockwise from the top: each card's centre, and the chevron after it (at the mid-angle to the next card, pointing along the loop). */
export function ringOf(n, w, h = RING_H) {
  const cx = w / 2, cy = h / 2, rx = Math.max(60, (w - CARD_W) / 2 - 6), ry = Math.max(60, (h - 170) / 2);
  const at = (a) => [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  return Array.from({ length: n }, (_, i) => {
    const a = -Math.PI / 2 + (i / n) * 2 * Math.PI, m = a + Math.PI / n, [x, y] = at(a), [mx, my] = at(m);
    const dx = -rx * Math.sin(m), dy = ry * Math.cos(m);
    const dir = Math.abs(dx) >= Math.abs(dy) ? (dx > 0 ? "right" : "left") : dy > 0 ? "down" : "up";
    return { x, y, mx, my, dir };
  });
}

function LoopCard({ c, i, n, g, narrow }) {
  const mine = c.by === "person", who = nameOf(g), head = g.leader?.head;
  const by = mine ? "Yours" : `Proposed by ${who}`;
  return html`<${MapCard} map=${MAP} id=${c.id} name=${c.name} group="loop" className="mp-loop"
    row=${narrow ? `${i + 1} of ${n}` : by}
    foot=${html`<p class=${cls("mp-card__foot", { "is-three": narrow })}>${c.line}</p>${narrow && html`<span class="mp-by">${!mine && head && html`<${Head} race=${head.race} tier=${head.tier} />`}<span>${by}</span></span>`}`}
    mark=${!narrow && !mine && head ? html`<${Head} race=${head.race} tier=${head.tier} />` : null}>
    <${Win}><${Sign} name="mechanic" big=${true} /></${Win}>
  </${MapCard}>`;
}

function Ring({ cards, g, width }) {
  const places = ringOf(cards.length, width), head = g.leader?.head;
  const rx = Math.max(60, (width - CARD_W) / 2 - 6), ry = Math.max(60, (RING_H - 170) / 2);
  return html`<div class="mp-ring" style=${`height:${RING_H}px`}>
    <svg class="mp-ring__line" width=${width} height=${RING_H} aria-hidden="true"><ellipse cx=${width / 2} cy=${RING_H / 2} rx=${rx} ry=${ry} /></svg>
    ${places.map((p, i) => html`<i key=${`c${i}`} class=${`ork-chev ${p.dir} mp-ring__chev`} style=${`left:${p.mx}px;top:${p.my}px`} aria-hidden="true"></i>`)}
    ${cards.map((c, i) => html`<div key=${c.id} class="mp-slot" style=${`left:${places[i].x}px;top:${places[i].y}px`}><${LoopCard} c=${c} i=${i} n=${cards.length} g=${g} narrow=${false} /></div>`)}
    <div class="mp-ring__mid" style=${`left:${width / 2}px;top:${RING_H / 2}px`}>
      ${head && html`<${Head} race=${head.race} tier=${head.tier} size="big" />`}
      <span class="ork-label">The loop</span>
      <span class="mp-cap">${STEPS[cards.length] || cards.length} steps, round and round</span>
    </div>
  </div>`;
}

/** The back of a loop card: its line, who keeps it, what it rests on, **Edit**; while editing, the form for its name, line and files. */
function Back({ c, cards, g, reload }) {
  const [editing, setEditing] = useState(false), [form, setForm] = useState(null), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const key = keyOf(MAP, c.id), who = nameOf(g), mine = c.by === "person";
  const start = () => { setForm({ name: c.name, line: c.line, files: (c.rests_on || []).join("\n") }); setErr(""); setEditing(true); };
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const save = async () => {
    const rests = form.files.split("\n").map((x) => x.trim()).filter(Boolean);
    const next = cards.map((x) => (x.id === c.id ? { id: c.id, name: form.name.trim(), line: form.line.trim(), rests_on: rests } : { id: x.id, name: x.name, line: x.line, rests_on: x.rests_on || [] }));
    setBusy(true);
    try {
      const got = await command("ideas.loop_set", { cards: next }, true);
      if (got?.dropped?.length) toast(`Not in the project, left out: ${got.dropped.map((d) => d.path || d).join(", ")}`, "warning");
      setEditing(false);
      reload();
    } catch (e) { setErr(e.message || "The loop could not be kept"); }
    setBusy(false);
  };
  if (editing) {
    return html`<form class="mp-form" onSubmit=${(e) => { e.preventDefault(); save(); }}>
      <label class="mp-sec"><span class="ork-label">Name</span><input class="ork-field" name="name" maxlength="40" value=${form.name} onInput=${set("name")} required /></label>
      <label class="mp-sec"><span class="ork-label">Line</span><textarea class="ork-field" name="line" maxlength="160" rows="3" value=${form.line} onInput=${set("line")} required></textarea></label>
      <label class="mp-sec"><span class="ork-label">Files</span><textarea class="ork-field mp-code" name="files" rows="3" value=${form.files} onInput=${set("files")} placeholder="config/balance.ts"></textarea>
        <span class="mp-cap">One file or folder of the project a line; one that is not there is left out</span></label>
      ${err && html`<p class="mp-err" role="alert">${err}</p>`}
      <div class="mp-acts"><button type="submit" class="ork-btn primary" disabled=${busy || !form.name.trim() || !form.line.trim()}>Save</button>
        <button type="button" class="ork-btn" onClick=${() => setEditing(false)}>Cancel</button></div>
    </form>`;
  }
  return html`<h3 class="mp-back__nm">${c.name}</h3>
    <p class="mp-back__line">${c.line}</p>
    <span class="mp-by">${!mine && g.leader?.head && html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />`}<span>${mine ? "Yours" : `Proposed by ${who}`}</span></span>
    <${Sec} label="Rests on">${(c.rests_on || []).length
      ? html`<ul class="mp-list">${c.rests_on.map((p) => html`<li key=${p}><${FileLink} path=${p} from=${key} /></li>`)}</ul>`
      : html`<span class="mp-cap">It rests on no file yet</span>`}</${Sec}>
    <div class="mp-acts"><button type="button" class="ork-btn" onClick=${start}>Edit</button></div>`;
}

export function LoopMap({ g, narrow }) {
  const host = useRef(), ring = useRef(), [rd, reload] = useRead("ideas.loop"), d = rd.data, width = useWidth(ring);
  const [asked, setAsked] = useState(""), [busy, setBusy] = useState(false), at = useLifted(MAP), who = nameOf(g);
  const cards = d?.cards || [], proposing = !!d?.proposing;
  useEffect(() => {                                                            // a proposal being made: look again until it is kept
    if (!proposing) return undefined;
    const t = setInterval(reload, POLL_MS);
    return () => clearInterval(t);
  }, [proposing]);
  const propose = async () => {
    setBusy(true);
    setAsked("");
    try {
      const got = await command("ideas.loop_propose", {}, true);
      if (got && got.asked === false) setAsked(got.why || `${who} could not be asked now`);
    } catch (e) { setAsked(e.message || `${who} could not be asked now`); }
    setBusy(false);
    reload();
  };
  const card = cards.find((x) => x.id === at);
  const back = card ? html`<${MapBack} host=${host} name=${card.name} narrow=${narrow}><${Back} key=${card.id} c=${card} cards=${cards} g=${g} reload=${reload} /></${MapBack}>` : null;
  const rung = !narrow && width >= RING_MIN;
  return html`<${MapFrame} map=${MAP} host=${host} back=${back} className="mp--loop">
    <div class="mp-ring-host" ref=${ring}>
      ${d && cards.length > 0 && (rung ? html`<${Ring} cards=${cards} g=${g} width=${width} />`
        : html`<div class="mp-grid">${cards.map((c, i) => html`<${LoopCard} key=${c.id} c=${c} i=${i} n=${cards.length} g=${g} narrow=${true} />`)}</div>`)}
    </div>
    ${d && cards.length === 0 && html`<div class="mp-propose">
      <${Nothing} what=${NONE_WHAT} />
      <div class="mp-acts"><button type="button" class="ork-btn primary" disabled=${busy || proposing} onClick=${propose}>${proposing ? "Proposing…" : "Propose"}</button>
        <span class="mp-cap">${who} reads the game's configs and proposes four to six steps of its loop, in one short call</span></div>
      ${(asked || d.error) && html`<p class="mp-err" role="alert">${asked || d.error}</p>`}
    </div>`}
    ${!d && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}

mapFor(MAP, LoopMap);
