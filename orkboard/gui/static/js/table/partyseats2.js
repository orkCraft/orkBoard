// The right half of the one place of the parties (docs/specs/100-a-goals-way-as-cards.md §4, decisions §151.5, §164): the party that is open — the size (*Lean · Standard · Full*, each its line and what it costs a goal:
// `ideas.party_price`), the leader's row (its head, its name of its own beside its role, its map in one line, its AI tool's mark in ink and its tier), what the leader keeps of the project (read and changed here, *From the next goal*), and the squad in two columns, **Does** under orkUI's sword and **Checks** under its shield, of the craft's role cards (head, role, tool's mark, the gear of its tier), each ticked or not
// (at most five who do, two who check). A tick is the squad's; a press on the card opens the seat's popover (seatpop.js) when the party is made and the seat is in it, else it ticks the card. Under *Lean* the *Checks*
// column is dimmed (*No separate check: the doer runs its own tests*). The leaders' names (§164) are said here and nowhere else. The squad is drawn from a view of the party (parties.js `viewOf`); nothing here saves.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command } from "../link.js";
import { Head, Sign, TIER_WORDS } from "../orkui.js";
import { ask } from "../board/store.js";
import { roles } from "../shell/store.js";
import { costOf } from "../hand/cost.js";
import { MARKED, markSrc, toolOf } from "./data.js";

/** Every seat of a party wears its craft's race, its leader that race's higher form (`realm/roles.py` `PARTY_RACES`): [seat, leader]. */
const RACES = { product: ["knight", "unicorn"], "game-design": ["knight", "unicorn"], tech: ["peon", "shaman"], design: ["elf", "dryad"], art: ["elf", "dryad"], run: ["goblin", "imp"],
  liveops: ["goblin", "imp"], marketing: ["gnome", "fairy"], release: ["skeleton", "lich"] };

/** The leaders' names of their own (decisions §164): said on the leader's row of this place and nowhere else. */
const LEADERS = { product: "Angel Invest Knight", "game-design": "Dungeon Master Knight", tech: "Sh.man", design: "Pixel-Perfect Dryad", art: "Sprite Dryad", run: "Uptime Imp",
  liveops: "Event Imp", marketing: "Growth Hack Gnome", release: "Release Night King" };

/** The leader's map in one line, for the parties that have a map today (Tech's System); the others' are not read yet. */
const MAPS = { tech: "System, the code's containers and their links" };

export const SIZES = [["lean", "Lean", "plan → do, one at once"], ["standard", "Standard", "plan → do → one check, two at once"], ["full", "Full", "plan → do → every check it concerns, three at once"]];
export const CHECKS_WORDS = { lean: "No separate check: the doer runs its own tests", standard: "One checker checks each task", full: "Every checker a task concerns" };
export const MAX = { build: 5, check: 2 };
const LIMIT_WORDS = { build: "At most five who do", check: "At most two who check" };

export const libOf = (id) => (roles.value?.library || []).find((a) => a.id === id);
export const nameOf = (id) => libOf(id)?.name || id;

/** The head of a seat of the party `recipe`: its race, the tier the size gives it (else the library's). */
export function headOf(v, slug, size, lead = false) {
  const [seat, higher] = RACES[v.p.id] || ["peon", "shaman"];
  return { race: lead ? higher : seat, tier: v.p.sizes?.[size]?.tiers?.[slug] || libOf(slug)?.tier || "warrior" };
}

/** The AI tool a seat runs on: its own, the party's, else the Main tool; `{id, name}`. A made party has it from the table's data (`g`). */
export function toolFor(v, slug, tools, g) {
  if (g) return toolOf(g, { slug });
  const id = v.track?.tools?.[slug] || v.track?.tool || tools?.main || "claude";
  return { id, name: tools?.tools?.find((t) => t.id === id)?.name || id.charAt(0).toUpperCase() + id.slice(1) };
}

/** A tick's box: ticked shows orkUI's check, not ticked an empty box, a locked one dashed. */
export const Tick = ({ on, locked = false }) => html`<span class=${cls("parties__tick", { off: !on, locked })} aria-hidden="true"><${Sign} name="check" /></span>`;

const Mark = ({ tool }) => (MARKED.includes(tool.id) ? html`<img class="ork-mark" src=${markSrc(tool.id)} srcset=${`${markSrc(tool.id, true)} 2x`} alt="" draggable="false" />` : null);

/** What a size costs a goal, as a gem and its words, from `ideas.party_price`'s answer (`{low, high}` in dollars); null with none. */
export const costWords = (price) => (price ? costOf({ kind: "change", row: { usd_low: price.low, usd_high: price.high } }) : null);

// -- the size ---------------------------------------------------------------------------------------------------------------------------------

/** *Lean · Standard · Full*, each its line and its price a goal. Release works Lean always (decisions §151.6). */
export function SizeSwitch({ size, onPick, prices, locked }) {
  return html`<div class="parties__sizes" role="radiogroup" aria-label="Size">${SIZES.map(([id, word, line]) => {
    const c = costWords(prices?.[id]);
    return html`<button type="button" key=${id} role="radio" class=${cls("ork-row parties__size", { "is-on": size === id })} data-size=${id} aria-checked=${String(size === id)}
      disabled=${locked && id !== "lean"} onClick=${() => onPick(id)}>
      <b class="parties__size-nm">${word}</b><span class="parties__size-line">${line}</span>
      <span class="parties__size-cost">${c ? html`<span class="ork-gem share" data-cost=${c.gem}>${c.gem}</span> a goal` : " "}</span></button>`;
  })}</div>`;
}

// -- the leader's row, what it keeps --------------------------------------------------------------------------------------------------------

/** The leader: its head, its name of its own beside its role (*Sh.man · Architect*), its map where it has one, its AI tool's mark and its tier. Pressed, it opens its popover when the party is made. */
export function LeaderRow({ v, size, tools, g, onOpen, open }) {
  const lead = v.p.leader, head = headOf(v, lead, size, true), tool = toolFor(v, lead, tools, g), map = MAPS[v.p.id];
  const inner = html`<${Head} race=${head.race} tier=${head.tier} size="mid" />
    <span class="parties__lead-tx"><span class="parties__lead-nm"><b>${LEADERS[v.p.id] || nameOf(lead)}</b> · ${nameOf(lead)}</span>
      ${map && html`<span class="parties__muted">Map: ${map}</span>`}</span>
    <span class="parties__tool"><${Mark} tool=${tool} />${tool.name} · ${TIER_WORDS[head.tier] || ""}</span>`;
  return g ? html`<button type="button" class="ork-card parties__lead" data-seat=${lead} aria-haspopup="dialog" aria-expanded=${String(open)} onClick=${() => onOpen(lead)}>${inner}</button>`
    : html`<div class="ork-card parties__lead" data-seat=${lead}>${inner}</div>`;
}

/** What the leader keeps of the project (decisions §153.4), read from the host (`ideas.project_facts {party}` → `{facts: [{key, text, by}]}`) and changed here, *From the next goal*: a fact's text is edited in place and
 *  kept as the person's on leaving the field (`ideas.project_fact_set {party, key, text}`); an empty text, or *Forget*, drops it. Drawn only for a party that is made and where the host answers with facts. */
export function Facts({ party }) {
  const [facts, setFacts] = useState([]), [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    setFacts([]);
    if (party) command("ideas.project_facts", { party }, true).then((a) => { if (live && Array.isArray(a?.facts)) setFacts(a.facts); }).catch(() => {});
    return () => { live = false; };
  }, [party]);
  const keep = async (f, text) => {
    if (busy || text.trim() === f.text) return;
    setBusy(true);
    try {
      const got = await ask("ideas.project_fact_set", { party, key: f.key, text: text.trim() });
      if (got && Array.isArray(got.facts)) setFacts(got.facts);
    } finally { setBusy(false); }
  };
  if (!party || !facts.length) return null;
  return html`<section class="parties__facts" aria-label="What it keeps of the project" data-facts>
    <h4 class="ork-label">What it keeps of the project</h4>
    <ul>${facts.map((f) => html`<li key=${f.key + f.text} data-key=${f.key} class="parties__fact">
      <input class="ork-field" defaultValue=${f.text} maxlength="300" aria-label=${`What it keeps: ${f.text}`} disabled=${busy} onBlur=${(e) => keep(f, e.target.value)}
        onKeyDown=${(e) => { if (e.key === "Enter") { e.preventDefault(); e.target.blur(); } }} />
      <small class="parties__muted">${f.by === "read" ? "read from the project" : "you said"}</small>
      <button type="button" class="ork-btn quiet" disabled=${busy} title="It stops keeping this, from the next goal" aria-label=${`Forget: ${f.text}`} onClick=${() => keep(f, "")}>Forget</button></li>`)}</ul>
    <p class="parties__muted">From the next goal</p></section>`;
}

// -- the squad: Does and Checks ---------------------------------------------------------------------------------------------------------------

function RoleCard({ v, slug, size, tools, g, on, full, onTick, onPress }) {
  const head = headOf(v, slug, size), tool = toolFor(v, slug, tools, g), name = nameOf(slug), made = !!g && (g.party || []).some((m) => m.slug === slug);
  const stuck = !on && full;                                                                         // the column is full: this card cannot be ticked
  return html`<div class=${cls("parties__role", { "is-off": !on })} data-seat=${slug} data-on=${String(on)}>
    <button type="button" class="parties__tickbtn" role="checkbox" aria-checked=${String(on)} aria-label=${`${name}: in the squad`} disabled=${stuck} title=${stuck ? LIMIT_WORDS[libOf(slug)?.band === "check" ? "check" : "build"] : undefined}
      onClick=${() => onTick(slug)}><${Tick} on=${on} /></button>
    <button type="button" class="ork-row parties__seat" aria-haspopup=${made ? "dialog" : undefined} onClick=${() => (made ? onPress(slug) : onTick(slug))} disabled=${stuck && !made}>
      <${Head} race=${head.race} tier=${head.tier} /><span class="parties__seat-nm">${name}</span><${Mark} tool=${tool} /></button></div>`;
}

function Column({ band, v, slug, size, tools, g, squad, onTick, onPress, dim }) {
  const seats = [...new Set([...(v.p[band] || []), ...squad.filter((s) => (libOf(s)?.band || "build") === band)])];
  const ticked = seats.filter((s) => squad.includes(s)).length, full = ticked >= MAX[band];
  const word = band === "build" ? "Does" : "Checks", hint = band === "build" ? "The leader gives each task to the one it is for." : CHECKS_WORDS[size];
  return html`<div class=${cls("parties__col", { "is-dim": dim })} data-band=${band} aria-label=${word} role="group">
    <h3 class="parties__col-h"><${Sign} name=${band === "build" ? "sword" : "shield"} /> ${word}</h3>
    ${seats.map((s) => html`<${RoleCard} key=${s} v=${v} slug=${s} size=${size} tools=${tools} g=${g} on=${squad.includes(s)} full=${full} onTick=${onTick} onPress=${onPress} />`)}
    <p class="parties__hint">${hint}</p></div>`;
}

/** The party that is open, at the right. `prices`: size → `{low, high}`; `g`: the table's data of the party when it is made (its seats' popovers); `popover`: the popover, drawn by the page. */
export function PartyRight({ v, size, setSize, setSquad, prices, tools, g, onOpen, open }) {
  const bandOf = (s) => (libOf(s)?.band === "check" || v.p.check.includes(s) ? "check" : "build");
  const tick = (slug) => {
    const squad = v.squad, band = bandOf(slug);
    if (squad.includes(slug)) setSquad(squad.filter((s) => s !== slug));
    else if (squad.filter((s) => bandOf(s) === band).length < MAX[band]) setSquad([...squad, slug]);
  };
  return html`<div class="parties__party" data-party=${v.p.id} data-size=${size}>
    <${SizeSwitch} size=${size} onPick=${setSize} prices=${prices} locked=${v.p.locked} />
    <${LeaderRow} v=${v} size=${size} tools=${tools} g=${g} onOpen=${onOpen} open=${open === v.p.leader} />
    <${Facts} party=${v.track?.slug || ""} />
    <div class="parties__cols">
      <${Column} band="build" v=${v} size=${size} tools=${tools} g=${g} squad=${v.squad} onTick=${tick} onPress=${onOpen} dim=${false} />
      <${Column} band="check" v=${v} size=${size} tools=${tools} g=${g} squad=${v.squad} onTick=${tick} onPress=${onOpen} dim=${size === "lean"} />
    </div></div>`;
}
