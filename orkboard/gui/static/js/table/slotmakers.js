// A leader's makers under its slots (docs/specs/168 H1; the makers of docs/specs/156, kept as they were on the stall's shelf): what its party may have made on the person's own key (a picture maker, a sound maker), each with its cap per round.
// A maker is no slot (it has no ways to deal): it is a small card with the cap agreed on its plate; pressed, it opens the cap's form. A maker not here says why and where to fix it. The page says only what the host sent (`ideas.stall`'s shelf `craft_tools`).
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { openPlace } from "../frame/place.js";
import { Plate } from "./stallfaces.js";
import { makerPlate, take } from "./stallstate.js";

function Maker({ shelf, w, chair }) {
  const locked = !!w.price?.locked || w.here === false;
  const [editing, setEditing] = useState(false), [amount, setAmount] = useState(""), [error, setError] = useState(""), [saving, setSaving] = useState(false);
  const input = useRef(null), trigger = useRef(null), restoreFocus = useRef(false);
  useLayoutEffect(() => {
    if (makerPlate.value === w.id) {
      trigger.current?.scrollIntoView({ block: "nearest" });
      trigger.current?.focus();
      makerPlate.value = "";
    }
  }, [w.id, makerPlate.value]);
  const currency = w.prices?.[0]?.currency || w.cap?.currency;
  const fieldId = `maker-cap-${w.id}`, whyId = `maker-why-${w.id}`;
  useLayoutEffect(() => {                                              // focus after the form has been inserted or removed, before the redraw is painted
    if (editing) input.current?.focus();
    else if (restoreFocus.current) {
      restoreFocus.current = false;
      trigger.current?.focus();
    }
  }, [editing]);
  const close = () => { restoreFocus.current = true; setEditing(false); setError(""); };
  const edit = () => { setAmount(w.cap?.amount || ""); setError(""); setEditing(true); };
  const save = async (e) => {
    e.preventDefault();
    if (saving) return;
    if (!/^(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/.test(amount.trim()) || !Number.isFinite(Number(amount)) || Number(amount) <= 0) {
      setError(`Enter a positive amount in ${currency}.`); input.current?.focus(); return;
    }
    setSaving(true);
    const ok = await take(chair, shelf.slot, w.id, { amount: amount.trim(), currency });
    setSaving(false);
    if (ok) close(); else setError("The maker cap could not be saved. Try again.");
  };
  return html`<div class=${cls("stall-ware", { "is-locked": locked })} data-ware=${w.id} data-slot=${shelf.slot} onKeyDown=${(e) => { if (e.key === "Escape" && editing) { e.preventDefault(); e.stopPropagation(); close(); } }}>
    <button ref=${trigger} type="button" class="stall-ware__press" aria-expanded=${!locked ? editing : undefined} aria-controls=${!locked ? fieldId : undefined} aria-describedby=${locked ? whyId : undefined} aria-disabled=${locked ? "true" : undefined} title=${locked ? w.price.locked : w.line || undefined} aria-label=${`${shelf.label}: ${w.word}`} onClick=${() => { if (!locked) edit(); }}>
      <div class="stall-face stall-relic stall-maker"><${Sign} name=${w.makes === "pictures" ? "picture" : "sound"} /><span class="stall-relic__word">${w.word}</span><span class="stall-maker__service">${w.title}</span></div>
    </button>
    ${!locked ? html`<button type="button" class="stall-maker__cap" tabIndex="-1" aria-expanded=${editing} aria-controls=${fieldId} onClick=${edit}><${Plate} price=${w.price} /></button>` : html`<${Plate} price=${{ locked: w.why }} />`}
    ${editing && html`<form class="stall-maker__form" id=${fieldId} onSubmit=${save} noValidate>
      <label for=${`${fieldId}-amount`}>Cap per round (${currency})</label>
      <input ref=${input} id=${`${fieldId}-amount`} type="text" inputMode="decimal" value=${amount} onInput=${(e) => setAmount(e.currentTarget.value)} aria-invalid=${error ? "true" : undefined} aria-describedby=${error ? `${fieldId}-error` : undefined} />
      ${error && html`<p id=${`${fieldId}-error`} role="alert">${error}</p>`}
      <button type="submit" class="ork-btn" disabled=${saving}>Save cap</button>
    </form>`}
    ${locked && html`<p class="stall-maker__why" id=${whyId}>${w.why}
      ${w.why === "no key on this computer" && html`<button type="button" class="ork-btn quiet" onClick=${() => openPlace("settings", {}, "Settings")}>Settings · sign-ins</button>`}
    </p>`}
    <p class="stall-maker__leaves"><b>What leaves this computer</b>${w.leaves}</p>
  </div>`;
}

/** The makers of a leader's party, under its slots and its seats. */
export function Makers({ shelf, chair }) {
  return html`<div class="stall-shelf is-makers" data-shelf=${shelf.slot}>
    <p class="stall-shelf__lab"><b>${shelf.label}</b>${shelf.sub}</p>
    <div class="stall-wares">${shelf.wares.map((w) => html`<${Maker} key=${w.id} shelf=${shelf} w=${w} chair=${chair} />`)}</div>
  </div>`;
}
