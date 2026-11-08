// One party on the Orkmaster's large card (docs/specs/130-the-first-open-is-the-orkmasters.md C.2, decisions §232.6; mockup docs/mockups/setup/ #parties): **one line**, its tick, its leader's head with its AI tool's mark in the corner (framed when the party follows the main tool, bare when a tool is set for it), its name (its line of what it does is the name's words) and its size, a small switch whose words
// say a goal's price (`ideas.party_price`); **under it its team**, *Does* after orkUI's sword and *Checks* after its shield, the seats the size gives as heads and the seats the craft has and the size leaves empty as shadows, up to five who do and two who check. Changing the size changes the heads at once, nothing saved. Under *Lean* the Checks are dimmed. A shadow is not pressed, for now. A member's head wears a tool's mark only when its tool differs from the party's. **Release** is ticked and locked, its size locked at Lean.
// A head or a mark pressed opens its seat (seatpop.js `SeatDraft`). What the leader keeps of the project (`Facts`) is said on the leader's seat of a party that is made. Nothing here saves. orkUI first: `.ork-race__head.is-empty`, the small size switch.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command } from "../link.js";
import { Head, Sign } from "../orkui.js";
import { ask } from "../board/store.js";
import { roles } from "../shell/store.js";
import { MARKED, markSrc } from "./data.js";

/** Every seat of a party wears its craft's race, its leader that race's higher form (`realm/roles.py` `PARTY_RACES`): [seat, leader]. */
const RACES = { product: ["knight", "unicorn"], "game-design": ["knight", "unicorn"], tech: ["peon", "shaman"], design: ["elf", "dryad"], art: ["elf", "dryad"], run: ["goblin", "imp"],
  liveops: ["goblin", "imp"], marketing: ["gnome", "fairy"], release: ["skeleton", "lich"] };

/** The leaders' names of their own (decisions §164): said on the leader's seat and nowhere else. */
export const LEADERS = { product: "Angel Invest Knight", "game-design": "Dungeon Master Knight", tech: "Sh.man", design: "Pixel-Perfect Dryad", art: "Sprite Dryad", run: "Lantern Imp",
  marketing: "Growth Hack Gnome", release: "Release Night King" };

export const SIZES = [["lean", "Lean"], ["standard", "Standard"], ["full", "Full"]];
export const LEAN_LINE = "Lean: one does it, the leader accepts it";
export const MAX = { build: 5, check: 2 };

export const libOf = (id) => (roles.value?.library || []).find((a) => a.id === id);
export const nameOf = (id) => libOf(id)?.name || id;

/** The head of a seat of the party `v`: its race; the tier set by hand, else the one the size gives it, else the library's. */
export function headOf(v, slug, size, lead = false) {
  const [seat, higher] = RACES[v.p.id] || ["peon", "shaman"];
  return { race: lead ? higher : seat, tier: v.tiers?.[slug] || v.p.sizes?.[size]?.tiers?.[slug] || libOf(slug)?.tier || "warrior" };
}

/** The race's three gears of a seat (§158: its tier is the gear on its head). */
export const raceOf = (v, lead = false) => { const [seat, higher] = RACES[v.p.id] || ["peon", "shaman"]; return lead ? higher : seat; };

/** Whether a seat is one who checks. */
export const bandOf = (v, slug) => (libOf(slug)?.band === "check" || (v.p.check || []).includes(slug) ? "check" : "build");

/** The seats of a band in a size (spec 81 §2, decisions §232.6): `{on, shadows}`. Lean: the first who does, the rest shadows, no one checks (the leader accepts). Standard: the first two who do and the first who checks. Full: the whole squad. The seats the craft has and the size leaves empty are shadows, up to five who do and two who check. */
export function seatsOf(v, band, size) {
  const squad = (v.squad || []).filter((s) => bandOf(v, s) === band), craft = [...new Set([...(band === "build" ? v.p.build : v.p.check) || [], ...squad])];
  const on = size === "lean" ? (band === "build" ? squad.slice(0, 1) : []) : size === "standard" ? squad.slice(0, band === "build" ? 2 : 1) : squad;
  return { on, shadows: craft.filter((s) => !on.includes(s)).slice(0, Math.max(0, MAX[band] - on.length)) };
}

/** A tick's box: ticked shows orkUI's check, not ticked an empty box, a locked one dashed. */
export const Tick = ({ on, locked = false }) => html`<span class=${cls("parties__tick", { off: !on, locked })} aria-hidden="true"><${Sign} name="check" /></span>`;

/** A tool's mark, in its own colours. */
const Mark = ({ id }) => (MARKED.includes(id) ? html`<img src=${markSrc(id, false, true)} srcset=${`${markSrc(id, true, true)} 2x`} alt="" draggable="false" />` : null);

/** Dollars as a card says them: *$0.40–0.90*; "" with none. */
export const usdWords = (p) => (p ? `$${Number(p.low).toFixed(2)}–${Number(p.high).toFixed(2)}` : "");

/** *Lean · Standard · Full*, one line high; its words say what a goal costs. Release works Lean always (decisions §151.6). */
export function SizeSwitch({ size, onPick, prices, locked, name }) {
  return html`<span class=${cls("pc-sizes", { "is-locked": locked })} role="radiogroup" aria-label=${`${name}: its size`}>${SIZES.map(([id, word]) => {
    const said = prices?.[id] ? `${word}: about ${usdWords(prices[id])} a goal` : word;
    return html`<button type="button" key=${id} role="radio" class=${cls("pc-size", { "is-on": size === id })} data-size=${id} aria-checked=${String(size === id)} aria-label=${said} title=${said} disabled=${locked && id !== "lean"} onClick=${() => onPick(id)}>${word}</button>`;
  })}</span>`;
}

/** One head of the team: a seat given, pressed to open it; a shadow is the head's silhouette, not pressed. */
function Seat({ v, slug, size, shadow, own, open, onSeat }) {
  const head = headOf(v, slug, size), name = nameOf(slug);
  if (shadow) return html`<span class="pc-hd is-empty" data-shadow=${slug} title=${`${name}: an empty seat`}><${Head} race=${head.race} tier=${head.tier} /></span>`;
  return html`<button type="button" class=${cls("pc-hd", { "is-open": open })} data-seat=${slug} aria-haspopup="dialog" aria-expanded=${String(open)} aria-label=${`${name}: its seat`} title=${name} onClick=${() => onSeat(slug)}>
    <${Head} race=${head.race} tier=${head.tier} />${own && html`<span class="pc-own"><${Mark} id=${own} /></span>`}</button>`;
}

function Team({ v, band, size, partyTool, open, onSeat }) {
  const { on, shadows } = seatsOf(v, band, size), word = band === "build" ? "Does" : "Checks";
  return html`<span class=${cls("pc-grp", { "is-dim": band === "check" && size === "lean" })} role="group" aria-label=${word} data-band=${band}><span title=${word}><${Sign} name=${band === "build" ? "sword" : "shield"} /></span>
    ${on.map((s) => { const own = v.tools?.[s] || ""; return html`<${Seat} key=${s} v=${v} slug=${s} size=${size} own=${own && own !== partyTool ? own : ""} open=${open === s} onSeat=${onSeat} />`; })}
    ${shadows.map((s) => html`<${Seat} key=${s} v=${v} slug=${s} size=${size} shadow=${true} />`)}</span>`;
}

/** One party: its line and its team. `main`: the main tool's id; `prices`: size → `{low, high}`. */
export function PartyRow({ v, main, prices, open, onTick, onSize, onSeat }) {
  const { p } = v, stuck = p.locked || v.made, size = v.size, lead = p.leader, leadHead = headOf(v, lead, size, true), partyTool = v.tool || "", shows = partyTool || main;
  return html`<div class="pc-row" data-party=${p.id} data-on=${String(v.on)} data-locked=${String(!!p.locked)} data-size=${size}>
    <button type="button" class="parties__tickbtn" role="checkbox" aria-checked=${String(v.on)} aria-label=${`In the project: ${p.name}`} aria-disabled=${stuck ? "true" : undefined}
      title=${p.locked ? "In every project" : v.made ? "It is made: remove it from its tab's menu" : undefined} onClick=${() => !stuck && onTick(p.id)}><${Tick} on=${v.on} locked=${stuck} /></button>
    <button type="button" class=${cls("pc-lead", { "is-open": open === lead })} data-seat=${lead} aria-haspopup="dialog" aria-expanded=${String(open === lead)} aria-label=${`${nameOf(lead)}: its seat`} title=${nameOf(lead)} onClick=${() => onSeat(lead)}>
      <${Head} race=${leadHead.race} tier=${leadHead.tier} size="big" />${shows && html`<span class=${cls("pc-lmark", { "is-framed": !partyTool })} data-tool=${shows} data-follows=${partyTool ? undefined : "1"}><${Mark} id=${shows} /></span>`}</button>
    <b class="pc-name" title=${p.line}>${p.name}</b>
    <${SizeSwitch} size=${size} onPick=${onSize} prices=${prices} locked=${p.locked} name=${p.name} />
    <span class="pc-team">
      <${Team} v=${v} band="build" size=${size} partyTool=${shows} open=${open} onSeat=${onSeat} />
      <${Team} v=${v} band="check" size=${size} partyTool=${shows} open=${open} onSeat=${onSeat} />
      ${p.locked ? html`<span class="pc-muted">in every project</span>` : size === "lean" && html`<span class="pc-muted" data-lean="1">${LEAN_LINE}</span>`}
    </span>
  </div>`;
}

/** The parties of a stage not reached, in one line of heads and names; a tick seats one now. */
export function LaterRow({ views, words, onTick }) {
  return html`<div class="pc-later" data-later="1">${views.map((v) => { const h = headOf(v, v.p.leader, v.size, true); return html`<span class="pc-later__one" key=${v.p.id} data-party=${v.p.id} data-on=${String(v.on)}>
      <button type="button" class="parties__tickbtn" role="checkbox" aria-checked=${String(v.on)} aria-label=${`In the project: ${v.p.name}`} onClick=${() => onTick(v.p.id)}><${Tick} on=${v.on} /></button><${Head} race=${h.race} tier=${h.tier} /><span>${v.p.name}</span></span>`; })}
    <span class="pc-muted">${words}</span></div>`;
}

/** The keys a party's fact may not take: the project's common core (`realm/project_facts.py` `COMMON_KEYS`) is not a party's to replace. */
const COMMON_KEYS = ["for_whom", "hurts", "leaves_out"];

/** A key the host accepts (`a-z`, `0-9` and `_`, up to 40) for a new fact: the first words of its text, slugged, and unique among the party's keys (`_2`, `_3`, …); `fact` when the text has no letter or digit to slug. */
export function factKey(text, taken = []) {
  const base = String(text || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim().split(" ").filter(Boolean).slice(0, 4).join("_").slice(0, 36).replace(/_+$/, "") || "fact";
  const used = new Set([...taken, ...COMMON_KEYS]);
  let key = base, n = 1;
  while (used.has(key)) key = `${base.slice(0, 36 - String(++n).length - 1)}_${n}`;
  return key;
}

/** What the leader keeps of the project (decisions §153.4, §169.6), read from the host (`ideas.project_facts {party}` → `{facts: [{key, text, by}]}`) and changed here, *From the next goal*: a fact's text is edited in place and
 *  kept as the person's on leaving the field (`ideas.project_fact_set {party, key, text}`); an empty text, or *Forget*, drops it; *Add a fact* opens one field, Enter (or *Add*) keeps it under a key made of its first words.
 *  Drawn only for a party that is made and where the host answers with facts (an empty list too: the first fact is added here). */
export function Facts({ party }) {
  const [facts, setFacts] = useState(null), [busy, setBusy] = useState(false), [adding, setAdding] = useState(false), [draft, setDraft] = useState("");
  useEffect(() => {
    let live = true;
    setFacts(null); setAdding(false); setDraft("");
    if (party) command("ideas.project_facts", { party }, true).then((a) => { if (live && Array.isArray(a?.facts)) setFacts(a.facts); }).catch(() => {});
    return () => { live = false; };
  }, [party]);
  const send = async (key, text) => {
    setBusy(true);
    try {
      const got = await ask("ideas.project_fact_set", { party, key, text });
      if (got && Array.isArray(got.facts)) { setFacts(got.facts); return true; }
      return false;
    } finally { setBusy(false); }
  };
  const keep = async (f, text) => {
    if (busy || text.trim() === f.text) return;
    await send(f.key, text.trim());
  };
  const add = async () => {
    const text = draft.trim();
    if (busy || !text) return;
    if (await send(factKey(text, facts.map((f) => f.key)), text)) { setAdding(false); setDraft(""); }
  };
  if (!party || !facts) return null;
  return html`<section class="parties__facts" aria-label="What it keeps of the project" data-facts>
    <h4 class="ork-label">What it keeps of the project</h4>
    ${facts.length > 0 && html`<ul>${facts.map((f) => html`<li key=${f.key + f.text} data-key=${f.key} class="parties__fact">
      <input class="ork-field" defaultValue=${f.text} maxlength="300" aria-label=${`What it keeps: ${f.text}`} disabled=${busy} onBlur=${(e) => keep(f, e.target.value)}
        onKeyDown=${(e) => { if (e.key === "Enter") { e.preventDefault(); e.target.blur(); } }} />
      <small class="parties__muted">${f.by === "read" ? "read from the project" : "you said"}</small>
      <button type="button" class="ork-btn quiet" disabled=${busy} title="It stops keeping this, from the next goal" aria-label=${`Forget: ${f.text}`} onClick=${() => keep(f, "")}>Forget</button></li>`)}</ul>`}
    ${adding
      ? html`<div class="parties__fact parties__fact-add" data-adding>
          <input class="ork-field" value=${draft} maxlength="300" aria-label="A new fact" placeholder="What it should know of the project" disabled=${busy}
            ref=${(el) => { if (el && !el.dataset.seen) { el.dataset.seen = "1"; el.focus(); } }} onInput=${(e) => setDraft(e.target.value)}
            onKeyDown=${(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } else if (e.key === "Escape") { e.preventDefault(); setAdding(false); setDraft(""); } }} />
          <button type="button" class="ork-btn primary" disabled=${busy || !draft.trim()} onClick=${add}>Add</button></div>`
      : html`<div><button type="button" class="ork-btn quiet" data-act="add-fact" onClick=${() => setAdding(true)}>Add a fact</button></div>`}
    <p class="parties__muted">From the next goal</p></section>`;
}
