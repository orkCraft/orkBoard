// The Orkmaster's two rows (docs/specs/91-the-owners-list.md §8, decisions §107.6): on the project's level, at the top of the Field tab, beside the Orkmaster's crowned head, which stands over both.
// **Parties**: *New party* (a dashed card that opens New party) and two or three ready parties that suit this kind of project and the project does not have (projectdeal.js: the Orkmaster's proposals, else
// the library's in the host's deal), each its leader's head, its name, who and what for, and *Add*, which opens New party on it as the pile's card did. **New goal**: one line for the goal in the person's
// words, *for <party>* (the party it goes to: the Orkmaster's guess, `ideas.party_for` of the kind the line says; a pick of the person's stays), *Add goal*, and under it *<Party>'s kinds:* — at most three
// kinds that party offers, the guessed one marked *· guessed* once a line is typed — and *More kinds…*, the full list grouped (types.js; New goal then opens with the party the person picked, else the Orkmaster suggests it for the kind). The kind is guessed from the line as it is typed
// (`ideas.kind_for`: words, no model), never asked first; *Add goal* sends what New goal sends (`ideas.add` with the line, the party, its priority and the kind picked, if any). This is the one way in:
// the pile of New party, the pile of New goal and the + in the project line are gone. The code's goal is a party; its idea is a goal.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, toast } from "../link.js";
import { Chev, Head, Icon, Sign } from "../orkui.js";
import { PROJECT, goalList } from "../board/store.js";
import { act, mapData } from "../shell/store.js";
import { openDialog } from "../shell/modals.js";
import { askAfterLow } from "../shell/nightask.js";
import { isIdeation } from "./pitchwords.js";
import { usePartyFor } from "./projectparty.js";
import { readyParties, useProposals } from "./projectdeal.js";
import { KINDS_SHOWN, ROWS, fitWords, forWords, kindChip, kindsWords, typesFirst } from "./projectwords.js";
import { TypesSpread } from "./types.js";

const GUESS_MS = 250;                                       // the line rests this long before its kind is guessed

/** A ready party as a card: its leader's head, its name (the pixel face), who and what for, and *Add*, which opens New party on it. */
function ReadyCard({ c }) {
  const who = c.lead?.name ? `${c.lead.name}${c.size ? ` + ${c.size}` : ""}` : "";
  return html`<article class="arena-rcard" data-preset=${c.id} data-proposal=${c.open.proposal || ""} aria-label=${c.name}>
    ${c.lead && html`<span class="arena-rcard__head"><${Head} race=${c.lead.race} tier=${c.lead.tier} /></span>`}
    <b class="arena-rcard__name">${c.name}</b>
    <span class="arena-rcard__cap" title=${c.line}>${who && html`<span class="arena-rcard__who">${who}</span>${c.line ? " · " : ""}`}${c.line}</span>
    ${c.why && html`<span class="arena-rcard__why" title=${c.why}>${c.why}</span>`}
    <button type="button" class="ork-btn arena-rcard__add" aria-label=${`${ROWS.add} ${c.name}`} onClick=${() => openDialog("goal", c.open)}>${ROWS.add}</button>
  </article>`;
}

/** **Parties**: the label and its caption, *New party*, and two or three ready parties. `deal`: `ideas.map`'s `project.deal`. */
function PartiesRow({ deal }) {
  const proposals = useProposals(deal.map((d) => `${d.id}:${d.why}`).join());
  const cards = readyParties(deal, proposals);
  return html`<div class="arena-prow" data-row="parties" role="group" aria-label=${ROWS.parties}>
    <div class="arena-prow__lab"><b>${ROWS.parties}</b><span class="arena-cap">${ROWS.partiesCap}</span></div>
    <div class="arena-prow__body">
      <button type="button" class="arena-rcard arena-rcard--new" data-act="new-party" aria-haspopup="dialog" title="One of yours, or its leader, builders and checkers from the library" onClick=${() => openDialog("goal")}>
        <${Icon} name="plus" /><span>${ROWS.newParty}</span></button>
      ${cards.map((c) => html`<${ReadyCard} key=${c.id} c=${c} />`)}
    </div>
  </div>`;
}

/** *for Website*: the parties of the project as a list under the button, each with how it fits the kind the line says; a press picks one, Esc or a press elsewhere puts it away. */
function ForParty({ pf, name }) {
  const [open, setOpen] = useState(false), root = useRef();
  useEffect(() => {
    if (!open) return undefined;
    const away = (e) => { if (!root.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("pointerdown", away, true);
    return () => document.removeEventListener("pointerdown", away, true);
  }, [open]);
  const key = (e) => { if (e.key === "Escape" && open) { e.stopPropagation(); setOpen(false); root.current?.querySelector(".arena-for__btn")?.focus(); } };
  const pick = (slug) => { pf.pick(slug); setOpen(false); root.current?.querySelector(".arena-for__btn")?.focus(); };
  return html`<div class="arena-for" ref=${root} onKeyDown=${key}>
    <button type="button" class="ork-btn arena-for__btn" aria-haspopup="listbox" aria-expanded=${String(open)} disabled=${!pf.parties.length} onClick=${() => setOpen(!open)}>
      <span>${forWords(name || "…")}</span><${Chev} dir=${open ? "up" : "down"} /></button>
    ${open && html`<ul class="arena-for__list" role="listbox" aria-label="Its party">${pf.parties.map((p) => html`<li key=${p.party} role="presentation">
      <button type="button" role="option" class=${cls("arena-for__opt", { "is-picked": p.party === pf.picked })} data-party=${p.party} aria-selected=${String(p.party === pf.picked)} onClick=${() => pick(p.party)}>
        <b>${p.name}</b>${fitWords(p) && html`<small>${fitWords(p)}</small>`}</button></li>`)}</ul>`}
  </div>`;
}

/** **New goal**: the line, *for <party>*, *Add goal*; under it the party's kinds (at most three) and *More kinds…*. */
function GoalRow() {
  const [text, setText] = useState(""), [said, setSaid] = useState("");        // `said`: the line once it has rested
  const [kind, setKind] = useState("");                                         // the kind the line says, over every kind
  const [own, setOwn] = useState("");                                           // … among the picked party's
  const [mine, setMine] = useState(undefined);                                  // the kind the person picked ("" none), undefined: the guessed one
  const [busy, setBusy] = useState(false), [from, setFrom] = useState(null), more = useRef();
  const line = text.trim();
  useEffect(() => { const t = setTimeout(() => setSaid(line), GUESS_MS); return () => clearTimeout(t); }, [line]);
  useEffect(() => {
    if (!said) { setKind(""); return undefined; }
    let live = true;
    command("ideas.kind_for", { text: said }, true).then((r) => { if (live) setKind(r?.type || ""); }).catch(() => { if (live) setKind(""); });
    return () => { live = false; };
  }, [said]);
  const pf = usePartyFor(true, kind, "", true), party = pf.picked;
  const goals = (mapData.value?.goals || []).filter((g) => g.slug !== "general"), shown = goals.find((g) => g.slug === party), types = shown?.types || [];
  const name = pf.parties.find((p) => p.party === party)?.name || shown?.short || shown?.title || "";
  useEffect(() => {
    if (!said || !party) { setOwn(""); return undefined; }
    if (!kind || types.some((t) => t.id === kind)) { setOwn(kind); return undefined; }
    let live = true;
    command("ideas.kind_for", { text: said, party }, true).then((r) => { if (live) setOwn(r?.type || ""); }).catch(() => { if (live) setOwn(""); });
    return () => { live = false; };
  }, [said, party, kind]);
  const guessed = line && types.some((t) => t.id === own) ? own : "";
  const chips = (guessed ? [types.find((t) => t.id === guessed), ...types.filter((t) => t.id !== guessed)] : types).slice(0, KINDS_SHOWN);
  const picked = mine !== undefined ? (types.some((t) => t.id === mine) ? mine : "") : guessed;
  const pitch = isIdeation(mapData.value, party);
  const pickParty = (slug) => { pf.pick(slug); setMine(undefined); };

  const send = async () => {
    if (!line || !party || busy) return;
    const g = goalList().find((x) => x.slug === party), priority = pitch ? (g?.priority === "high" ? "high" : "normal") : g?.priority || "normal";
    setBusy(true);
    const got = await act("ideas.add", { text: line, track: party, priority, ...(picked && !pitch ? { type: picked } : {}) });
    setBusy(false);
    if (!got?.slug) return;
    setText(""); setSaid(""); setKind(""); setOwn(""); setMine(undefined);
    toast(`Added to ${name}.`);
    askAfterLow(priority);
  };
  const open = (e) => {
    if (from) return;
    setFrom(e.currentTarget.getBoundingClientRect());
  };
  const every = typesFirst(goals, party);                                    // the party's own kinds first, then the others' of the project, a kind once
  const at = { slug: PROJECT, first: pf.mine, title: "the project", short: "the project", text: line,
    groups: [[kindsWords(name), every.slice(0, types.length)], [ROWS.others, every.slice(types.length)]], types: every };
  return html`<div class="arena-prow" data-row="goal" role="group" aria-label=${ROWS.goal}>
    <div class="arena-prow__lab"><b>${ROWS.goal}</b><span class="arena-cap">${ROWS.goalCap}</span></div>
    <div class="arena-prow__body arena-prow__body--goal">
      <div class="arena-goalrow">
        <input class="ork-field arena-goalrow__text" type="text" value=${text} aria-label=${ROWS.goal} placeholder=${ROWS.placeholder} maxlength="2000" autocomplete="off"
          onInput=${(e) => setText(e.target.value)} onKeyDown=${(e) => { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); send(); } }} />
        <${ForParty} pf=${{ ...pf, pick: pickParty }} name=${name} />
        <button type="button" class="ork-btn primary arena-goalrow__add" disabled=${!line || !party || busy} onClick=${send}>${ROWS.addGoal}</button>
      </div>
      <div class="arena-kinds" role="group" aria-label=${kindsWords(name)}>
        ${pitch ? html`<span class="arena-cap">${name} ${ROWS.pitch}</span>` : html`<span class="arena-kinds__label">${kindsWords(name)}</span>
          ${chips.map((t) => html`<button key=${t.id} type="button" class=${cls("ork-btn arena-kind", { "is-picked": t.id === picked })} data-type=${t.id} data-guessed=${String(t.id === guessed)} aria-pressed=${String(t.id === picked)}
            title=${t.line} onClick=${() => setMine(t.id === picked ? "" : t.id)}><${Sign} name=${t.sign} /><span>${kindChip(t.name, t.id === guessed)}</span></button>`)}
          <button type="button" ref=${more} class="ork-btn quiet arena-kinds__more" aria-haspopup="dialog" onClick=${open}>${ROWS.more}</button>`}
      </div>
    </div>
    ${from && html`<${TypesSpread} g=${at} from=${from} back=${more.current} done=${() => setFrom(null)} />`}
  </div>`;
}

/** The two rows beside the Orkmaster's head. `ork`: `project.orkmaster`; `deal`: `project.deal`. */
export function ProjectRows({ ork, deal }) {
  return html`<section class="arena-prows" aria-label="Parties and goals">
    <span class="arena-prows__ork" title="Orkmaster"><${Head} race=${ork?.race || "peon"} tier=${ork?.tier || "crown"} size="big" /></span>
    <${PartiesRow} deal=${deal} />
    <${GoalRow} />
  </section>`;
}
