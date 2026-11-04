// A potion pressed lifts its tool's card (docs/specs/130-the-first-open-is-the-orkmasters.md B.3, decisions §232.5, §177.2; mockup docs/mockups/setup/ #tool): the tool's mark, name and potion and its two shares in words (§192.3); **Paid by** with the same third line as the adding card (`tools.billing`); **the order the work moves on in**, the hand's marks
// with this one framed and ← → (`tools.order`: the first is the main tool; dragging a potion does the same, mana.js); **Check** (`tools.check`); **What used it** (what a press on a potion did before), over the pane; and **Put back**, with what follows said under it before it is pressed (`tools.put_back_plan`, which changes
// nothing). A tool is put back between tasks, never inside one, with **Undo** in the toast; the last tool asks first.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, town, toast } from "../link.js";
import { openOver, lower, tab } from "../frame/state.js";
import { ask } from "../board/store.js";
import { mapName, partiesAll } from "../table/data.js";
import { Who, potionOf } from "./mana.js";

/** **Put back**: what follows said under it, read when the card opens; the last tool asks first, any other goes at once, with Undo in the toast. */
function PutBack({ tool, title }) {
  const [plan, setPlan] = useState(null), [asks, setAsks] = useState(""), [busy, setBusy] = useState(false), hand = (town.value?.tools?.hand || []).map((h) => h.id).join(",");
  useEffect(() => { let live = true; command("tools.put_back_plan", { tool }, true).then((a) => { if (live && a && !a.error) setPlan(a); }).catch(() => {}); return () => { live = false; }; }, [tool, hand]);
  const send = async (sure) => {
    setBusy(true);
    try {
      const got = await ask("tools.put_back", { tool, ...(sure ? { sure: true } : {}) });
      if (!got) return;
      if (got.ok === false) { setAsks(got.ask || ""); return; }
      lower();
      toast(`${title} is out of your hand. ${got.plan?.line || ""}`.trim(), "information", "", 10, null, [{ label: "Undo", run: () => ask("tools.put_back_undo", { undo: got.undo }) }]);
    } finally { setBusy(false); }
  };
  if (asks) {
    return html`<div class="hand-tool__field hand-tool__rule" data-last="1"><span class="ork-label">Put back the last tool?</span><p class="cap">${asks}</p>
      <div class="hand-tool__row"><button type="button" class="ork-btn danger hand-tool__small" data-sure="1" disabled=${busy} onClick=${() => send(true)}>Put it back anyway</button>
        <button type="button" class="ork-btn hand-tool__small" onClick=${() => setAsks("")}>Not now</button></div></div>`;
  }
  return html`<div class="hand-tool__field hand-tool__rule"><button type="button" class="ork-btn danger hand-tool__small" data-put-back="1" disabled=${busy} onClick=${() => send(false)}>Put back</button>
    ${plan && html`<span class="cap hand-tool__muted" data-plan="1">${[plan.line, ...(plan.parties || []).map((p) => p.line)].join(". ")}</span>`}</div>`;
}

/** The result of Check, in the tool's words. */
function CheckResult({ c }) {
  if (!c) return null;
  if (c.state === "running") return html`<span class="cap ork-think" data-check="running">Checking</span>`;
  if (c.state === "ok") return html`<span class="cap is-ok" data-check="ok">${`It answered in ${(Number(c.ms || 0) / 1000).toFixed(1)} s`}</span>`;
  return html`<span class="cap is-danger" data-check="failed">${c.line}${c.action ? ` ${c.action}` : ""}</span>`;
}

export function ToolCard({ tool, style }) {
  const box = useRef(), t = town.value?.tools, row = t?.hand?.find((h) => h.id === tool), limits = town.value?.limits || [], l = limits.find((x) => x.provider === tool) || { provider: tool, name: row?.title || tool };
  useEffect(() => { box.current?.focus({ preventScroll: true }); command("tools.card", {}, true).catch(() => {}); }, [tool]);     // the look begun, so Check knows the tool
  useEffect(() => { if (t && !row) lower(); }, [!!row]);
  if (!row) return null;
  const order = t.order || [], at = order.indexOf(tool), p = potionOf(l), line = row.lines?.[row.billing];
  const move = (by) => { const next = [...order]; next.splice(at, 1); next.splice(at + by, 0, tool); ask("tools.order", { order: next }); };
  const from = { title: mapName(tab.value, partiesAll()), key: "" }, nextUp = order.length > 1 ? t.hand.find((h) => h.id === order[(at + 1) % order.length]) : null;
  return html`<aside ref=${box} class="ork-card hand-card--big hand-tool hand-tool--card" role="dialog" tabindex="-1" aria-label=${`${row.title}: its card`} data-lift="tool" data-tool=${tool} style=${style}>
    <div class="hand-tool__head">${p.read && html`<span class=${cls("ork-potion", { [`size-${p.size}`]: p.size !== "large", "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${`--ork-potion-left:${p.liquid}`} aria-hidden="true"></span>`}
      <span class="hand-tool__name"><span class="hand-tool__row"><${Who} l=${l} /><b class="ork-label">${row.title}</b></span><span class="cap" data-words="1">${p.words.replace(`${row.title}: `, "")}</span></span></div>
    <div class="hand-tool__field"><span class="ork-label">Paid by</span>
      <span class="hand-tool__seg" role="radiogroup" aria-label="Paid by">${[["subscription", "Subscription"], ["api", "API key"]].map(([id, word]) => html`<button type="button" key=${id} role="radio" aria-checked=${String(row.billing === id)} class=${cls("hand-tool__segbtn", { "is-on": row.billing === id })} data-billing=${id}
        onClick=${() => row.billing !== id && ask("tools.billing", { tool, billing: id })}>${word}</button>`)}</span>
      ${line && html`${line.warn && html`<span class="cap is-alert">${line.warn}</span>`}<span class=${cls("cap", { "is-ok": line.state === "ok" })} data-third=${line.state}>${line.line}</span>`}</div>
    <div class="hand-tool__field"><span class="ork-label">The order the work moves on in</span>
      <span class="hand-tool__order" data-order=${order.join(",")}>${t.hand.map((h) => html`<span key=${h.id} class=${cls("hand-tool__ordermark", { "is-me": h.id === tool })}><${Who} l=${{ provider: h.id, name: h.title }} /></span>`)}
        <span class="hand-tool__grow"></span>
        <button type="button" class="ork-btn hand-tool__small" data-left="1" aria-label="Move left" title="Move left" disabled=${at <= 0} onClick=${() => move(-1)}>←</button>
        <button type="button" class="ork-btn hand-tool__small" data-right="1" aria-label="Move right" title="Move right" disabled=${at >= order.length - 1} onClick=${() => move(1)}>→</button></span>
      <span class="cap hand-tool__muted">${row.main ? `The main tool: the work starts on it.${nextUp ? ` When it is out, the work goes on with ${nextUp.title}.` : ""}` : nextUp ? `When it is out, the work goes on with ${nextUp.title}.` : ""}</span></div>
    <div class="hand-tool__row"><button type="button" class="ork-btn hand-tool__small" data-check-btn="1" title="Sends one short request to its lightest model" onClick=${() => ask("tools.check", { tool })}>Check</button>
      <button type="button" class="ork-btn hand-tool__small" data-used="1" onClick=${() => { lower(); openOver("limits", { provider: tool }, from, `${row.title}: what used it`); }}>What used it</button></div>
    <${CheckResult} c=${row.check} />
    <${PutBack} tool=${tool} title=${row.title} />
  </aside>`;
}
