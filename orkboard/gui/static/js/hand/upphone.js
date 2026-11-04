// What only the phone's app has, at the foot of the crown's menu (docs/specs/117-the-phone-a-menu-of-the-leaders.md As built E): *Fix {product}* (docs/specs/119-the-hammer-and-the-bug.md §4.2: above Notifications, only when the computer can fix it; its line is the bug's title,
// a tap opens the bug panel's content in the menu: the line and Fix it, or Stop the fix, or Update and restart, or the error and Try again; no Save logs: a phone saves nothing on the computer), *Notifications* on or off and *Unpair this phone*, asked of the frame (pwa/frame.js
// `globalThis.orkboardPhone`; the page imports nothing of it). Drawn only when the frame is there and paired: a browser on the computer, or the page opened from the link, has neither. Unpairing asks a second press
// (*Press again to unpair*), never a dialog. A refusal (the phone's settings, an iPhone's browser not on the Home Screen) is said in the row's line, in the frame's own words.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { PRODUCT } from "../link.js";
import { RepairBody, repairOf, repairTitle } from "./logsbtn.js";

const phone = () => globalThis.orkboardPhone || null;

/** The rows; nothing outside the paired app. */
export function PhoneRows() {
  const p = phone(), [st, setSt] = useState(null), [line, setLine] = useState(""), [sure, setSure] = useState(false), [busy, setBusy] = useState(false), [fixing, setFixing] = useState(false), [said, setSaid] = useState("");
  const r = repairOf(), field = useRef();
  const read = () => p?.push.state().then(setSt).catch(() => setSt(null));
  useEffect(() => { read(); }, []);
  useEffect(() => { if (fixing) document.getElementById("up-phone-fix")?.scrollIntoView?.({ block: "nearest" }); }, [fixing]);          // the menu scrolls: the panel comes into view
  if (!p || !p.paired()) return null;
  const on = !!st?.on, why = st && !st.supported ? st.why : "";
  const flip = async () => {
    if (busy || why) return;
    setBusy(true);
    const r = await (on ? p.push.off() : p.push.on()).catch((e) => ({ ok: false, error: e?.message || String(e) }));
    setLine(r?.ok === false ? r.error || "" : "");
    await read();
    setBusy(false);
  };
  const unpair = () => { if (!sure) { setSure(true); return; } p.unpair(); };
  return html`<section class="up-group up-phone" aria-label="This phone"><p class="up-group__label">This phone</p>
    ${r.can && html`<button type="button" class=${`up-phone__row${r.state === "ready" ? " is-ready" : ""}`} data-repair-state=${r.state} aria-expanded=${String(fixing)} aria-controls="up-phone-fix" onClick=${() => setFixing(!fixing)}>
        <span class="up-phone__name">Fix ${PRODUCT}</span></button>
      <p class="up-phone__line" role="status">${repairTitle(r)}</p>
      ${fixing && html`<div id="up-phone-fix" class="up-phone__fix"><${RepairBody} r=${r} line=${said} setLine=${setSaid} fieldId="up-phone-fix-line" field=${field} done=${() => setFixing(false)} /></div>`}`}
    <button type="button" class="up-phone__row" role="switch" aria-checked=${String(on)} disabled=${!!why || busy} onClick=${flip}>
      <span class="up-phone__name">Notifications</span><span class="up-phone__state">${on ? "On" : "Off"}</span></button>
    ${(why || line) && html`<p class="up-phone__line" role="status">${why || line}</p>`}
    <${RepoRows} p=${p} />
    <button type="button" class="up-phone__row is-danger" onClick=${unpair}>${sure ? "Press again to unpair" : "Unpair this phone"}</button></section>`;
}

/** *Your repository* (docs/specs/136 C.1): the project's own remote, for when the computer cannot be reached. The frame draws the fields (pwa/shell-remote-settings.js); the row opens them in the menu. */
function RepoRows({ p }) {
  const [open, setOpen] = useState(false), [, tick] = useState(0), box = useRef();
  const remote = p.remote;
  useEffect(() => remote?.subscribe(() => tick((n) => n + 1)), []);
  useEffect(() => {
    if (!open || !box.current || !remote) return;
    box.current.replaceChildren(remote.settingsNode());
    box.current.scrollIntoView?.({ block: "nearest" });
  }, [open]);
  if (!remote) return null;
  const set = remote.state();
  return html`<button type="button" class="up-phone__row" aria-expanded=${String(open)} aria-controls="up-phone-repo" onClick=${() => setOpen(!open)}>
      <span class="up-phone__name">Your repository</span><span class="up-phone__state">${set.token && set.repo ? "Set" : "Not set"}</span></button>
    ${set.line && html`<p class="up-phone__line" role="status">${set.line}</p>`}
    ${open && html`<div id="up-phone-repo" class="up-phone__fix" ref=${box}></div>`}`;
}
