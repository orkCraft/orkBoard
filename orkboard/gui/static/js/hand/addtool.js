// The card that adds one AI tool (docs/specs/130-the-first-open-is-the-orkmasters.md B.2, decisions §232.4, §232.10; mockup docs/mockups/setup/ #shelf): lifted from the potions' empty slot, as every hand card is (§176.4). *Add an AI tool · n of up to 6*; **AI tool**: the tools found in three groups
// (*Ready*, *Not signed in*, *Not installed*: toolpick.js's words), a tool not installed with how to install it and never picked, the first ready one picked; **Paid by**; a third line that follows them (`lines[billing]`: signed in, **Sign in**, or the key named, never a field to type one in). **Test & add** sends one short request and
// waits for its answer: then the tool is in the hand and the card turns (*<Tool> is in your hand. Add another AI tool?*, **Add another** and, at the first open, **Go on to the parties**, later **Done**); at the sixth tool it goes on by itself. A failure says why on the card, in the tool's words, and nothing is added. An experimental tool asks its warning first;
// closed with no tool added at the first open it says what follows (`first_open.tools_skip`). Nothing here reads a key or runs a tool but Test & add.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, openLink, town, toast } from "../link.js";
import { lower } from "../frame/state.js";
import { signIn } from "../shell/signin.js";
import { ask } from "../board/store.js";
import { setupNow, setupAsk } from "./setupcards.js";

const GROUPS = [["ready", "Ready"], ["signed_out", "Not signed in"], ["not_installed", "Not installed"]];
const FOUND = "Found on this computer. Nothing else was run, and no key was read.";

/** The first open: the Orkmaster asked for a tool, or the first one was just added and the parties come next: the card goes on to them when it is done. */
const firstOpen = () => ["tools", "parties"].includes(setupNow.value?.step);

/** `tools.card`, asked when the card opens, when the tools were still being looked for and the page was pushed, when a sign-in moved and when the hand changed. */
function useCard(tick) {
  const [got, setGot] = useState(null), t = town.value, sig = JSON.stringify([tick, (t?.sign_in || []).map((e) => [e.harness, e.state]), (t?.tools?.hand || []).map((h) => h.id), !!t?.tools?.looked]);
  useEffect(() => {
    let live = true;
    command("tools.card", {}, true).then((a) => { if (live && a && !a.error) setGot(a); }).catch(() => {});
    return () => { live = false; };
  }, [sig]);
  return got;
}

/** A tool the orks cannot run on yet: a filled-in GitHub issue, nothing sent from here. */
function Request() {
  const [open, setOpen] = useState(false), [name, setName] = useState("");
  const send = async () => { const r = await command("tools.request", { name }, true).catch(() => null); if (r?.url) { openLink(r.url); setOpen(false); setName(""); } else toast("That could not be opened", "error"); };
  return open ? html`<div class="hand-tool__row"><input class="ork-field" value=${name} aria-label="The tool's name" placeholder="The tool's name" onInput=${(e) => setName(e.target.value)} />
      <button type="button" class="ork-btn" disabled=${!name.trim()} onClick=${send}>Open the request</button></div>`
    : html`<button type="button" class="ork-btn quiet hand-tool__link" data-request="1" onClick=${() => setOpen(true)}>Request a tool</button>`;
}

/** The third line: what `lines[billing]` says of the tool picked, how it is paid, with **Sign in** when it waits for one; the warning of a key that would win over a subscription stands above it. */
function ThirdLine({ row, billing }) {
  const line = row.lines?.[billing];
  if (!line) return null;
  const bad = line.needs === "sign_in" || line.state === "no_key" || line.state === "no_keys";
  return html`<div class="hand-tool__field" data-third=${line.state}>
    ${line.warn && html`<span class="cap is-alert" data-warn="1">${line.warn}</span>`}
    <span class=${cls("cap", { "is-ok": line.state === "ok", "is-alert": bad })}>${line.line}</span>
    ${line.cost && html`<span class="cap hand-tool__muted">${line.cost}</span>`}
    ${line.needs === "sign_in" && html`<button type="button" class="ork-btn hand-tool__small" data-sign-in=${row.id} onClick=${() => signIn(row.id)}>Sign in</button>`}
  </div>`;
}

/** The card turned: the tool is in the hand. */
function Added({ out, onAnother, onDone }) {
  const first = firstOpen();
  const full = !!out.full;
  useEffect(() => { if (full) onDone(); }, [full]);                      // at the sixth tool it goes on by itself
  return html`<div class="hand-tool__turned" data-turned="1">
    <p class="body">${out.line}</p>
    <p class="cap hand-tool__muted">The work moves on to the next one when ${out.title} runs dry.</p>
    <div class="hand-tool__stack">${!full && html`<button type="button" class="ork-btn" data-another="1" onClick=${onAnother}>Add another</button>`}
      <button type="button" class="ork-btn primary" data-done="1" onClick=${onDone}>${first ? "Go on to the parties" : "Done"}</button></div>
  </div>`;
}

export function AddTool({ style }) {
  const [tick, setTick] = useState(0), card = useCard(tick), box = useRef(), [pick, setPick] = useState(""), [billing, setBilling] = useState(""), [risk, setRisk] = useState(false), [sent, setSent] = useState(""), done = useRef(false);
  const rows = card?.tools || [], choosable = rows.filter((r) => r.pickable), row = rows.find((r) => r.id === pick) || null, adding = town.value?.tools?.adding || {}, out = sent ? adding[sent] : null;
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, []);
  useEffect(() => {                                                       // the first ready tool picked; a tool that left the list gives its place
    if (card?.ready && (!pick || !choosable.some((r) => r.id === pick))) { setPick(card.first || ""); setBilling(""); setRisk(false); }
  }, [card?.ready, card?.first, rows.length, pick]);
  useEffect(() => () => {                                                 // closed at the first open with no tool added: it says what follows, and the parties come
    if (!done.current && setupNow.peek()?.step === "tools") {
      command("first_open.tools_skip", {}, true).then((r) => { if (r?.line) toast(r.line); setupAsk(); }).catch(() => {});
    }
  }, []);
  const paid = billing || (row?.billing === "api" ? "api" : "subscription"), line = row?.lines?.[paid], running = out?.state === "running", added = out?.state === "added", failed = out?.state === "failed";
  const waits = !row || !!line?.needs || running || (!!row?.risk && !risk) || card?.full;
  const test = async () => {
    setSent(row.id);
    await ask("tools.test_add", { tool: row.id, billing: paid, risk_read: !!row.risk && risk });
  };
  const another = () => { setSent(""); setPick(""); setBilling(""); setRisk(false); setTick((n) => n + 1); };
  const finish = () => { done.current = true; lower(); setupAsk(); };
  const close = () => { lower(); };
  return html`<aside ref=${box} class="ork-card hand-card--big hand-tool hand-tool--add" role="dialog" tabindex="-1" aria-label="Add an AI tool" data-lift="add-tool" style=${style}>
    <div class="hand-tool__top"><span class="ork-label">${`Add an AI tool · ${(card?.n || 0) + (added ? 0 : 1)} of up to ${card?.max || 6}`}</span>
      <button type="button" class="ork-btn quiet hand-tool__small" data-close="1" onClick=${close}>Close</button></div>
    ${added ? html`<${Added} out=${out} onAnother=${another} onDone=${finish} />`
      : !card?.ready ? html`<p class="cap ork-think" data-looking="1">Looking for the AI tools</p>`
      : html`<div class="hand-tool__field"><label class="ork-label" for="add-tool-pick">AI tool</label>
          <span class="ork-select"><select id="add-tool-pick" class="ork-field" name="tool" value=${pick} onChange=${(e) => { setPick(e.target.value); setBilling(""); setRisk(false); setSent(""); }}>
            ${!pick && html`<option value="" selected>Choose one</option>`}
            ${GROUPS.map(([id, word]) => { const inn = rows.filter((r) => r.group === id); return inn.length > 0 && html`<optgroup key=${id} label=${word} data-group=${id}>${inn.map((r) => html`<option key=${r.id} value=${r.id} selected=${r.id === pick} disabled=${!r.pickable}>${r.pickable ? `${r.title}${r.version ? ` ${r.version}` : ""}` : `${r.title} · ${r.install}`}</option>`)}</optgroup>`; })}
          </select></span></div>
        <div class="hand-tool__field"><label class="ork-label" for="add-tool-paid">Paid by</label>
          <span class="ork-select"><select id="add-tool-paid" class="ork-field" name="billing" value=${paid} disabled=${!row} onChange=${(e) => { setBilling(e.target.value); setSent(""); }}>
            <option value="subscription" selected=${paid === "subscription"}>Subscription</option><option value="api" selected=${paid === "api"}>API key</option></select></span></div>
        ${row && html`<${ThirdLine} row=${row} billing=${paid} />`}
        ${row?.risk && html`<label class="hand-tool__risk cap"><input type="checkbox" checked=${risk} onChange=${(e) => setRisk(e.target.checked)} /><span>${`Turn on ${row.title} at my own risk: it is experimental, and its tasks may do what the others would not.`}</span></label>`}
        ${failed && html`<div class="hand-tool__field" data-failed="1" role="alert"><span class="cap is-danger">${out.line}</span>${out.action && html`<span class="cap hand-tool__muted">${out.action}</span>`}
          ${out.sign_in && html`<button type="button" class="ork-btn hand-tool__small" onClick=${() => signIn(sent)}>Sign in</button>`}</div>`}
        <div class="hand-tool__field"><button type="button" class="ork-btn primary" data-test-add="1" disabled=${waits} onClick=${test}>${running ? "Testing…" : "Test & add"}</button>
          <span class="cap hand-tool__muted">Sends one short request to its lightest model${paid === "api" ? ": about $0.001" : ""}.</span></div>
        <p class="cap hand-tool__muted">${FOUND}</p>
        <${Request} />`}
  </aside>`;
}
