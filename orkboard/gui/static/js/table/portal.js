// The portal to main (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §6, decisions §177.4): in the discard's view each goal ready for main is a card; pressing one, or starting to drag it, chooses it and opens the
// portal over the pile on the table's right (the `.table-end` place) with the pixel-face label *Main* and the line the host's plan says (`ideas.to_main_plan`, asked once when the portal opens for a goal, because it
// runs a trial worktree). A card held over the portal is `is-taking`; dropped on it, or the portal pressed while a card is chosen (Enter on the focused portal too), `ideas.to_main` sends the goal alone with the goals it
// stands on, the card goes into the portal and leaves the ready goals at the next `ideas.gate` read. While the gate holds the goal the portal is `is-sealed`, the reason under it in the danger colour; a press on it says the
// reason again and plays nothing. The first time, the portal shimmers (`is-new`) with a line saying how (a per-viewer convenience in localStorage; the page works without it). Esc or a press away closes it and drops the
// choice. Pressing works as dragging does: the press path needs no drag, so it is the phone's. The portal is orkUI's (`.ork-portal`, 0.18.0); its sheet is portal.css, layout only.
import { signal } from "@preact/signals";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { toast } from "../link.js";
import { ask } from "../board/store.js";
import { mapData, refreshShell } from "../shell/store.js";
import { over } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { readyOf } from "../hand/data.js";
import { reduced, leans } from "../hand/motion.js";

const SEEN_KEY = "orkboard.portal.seen";
const NARROW = "(max-width: 759.98px)";
export const GO_MS = 260;                                  // the card's travel into the portal (portal.css `portal-go`)

const chosen = signal("");                                 // the goal chosen (its slug), "" while the portal is closed
export const plan = signal(null);                                 // what `ideas.to_main_plan` said of it: {slug, state: "wait" | "ok" | "fail", goals, titles, sealed, files}
const taking = signal(false);                              // a card is held over the portal
export const going = signal("");                                  // the goal whose card is going in
export const first = signal(false);                               // the first time the portal opens on this device
export const echo = signal(0);                                    // a press on a sealed portal says its reason again
let planning = Promise.resolve(), said = false;

const readSeen = () => { try { return !!localStorage.getItem(SEEN_KEY); } catch { return false; } };
const writeSeen = () => { try { localStorage.setItem(SEEN_KEY, "1"); } catch { /* it is said once on this page instead */ } };

/** Names in plain English: *Lobby*, *Lobby and Reconnect*, *Lobby, Reconnect and Menu*. */
export const joined = (names) => (names.length < 2 ? names.join("") : `${names.slice(0, -1).join(", ")} and ${names.at(-1)}`);

const titleOf = (slug, p) => p?.titles?.[slug] || (readyOf()?.goals || []).find((g) => g.slug === slug)?.title || slug;
export const namesOf = (p, slug) => ((p?.goals?.length ? p.goals : [slug]).map((s) => titleOf(s, p)));

/** *Into main: Lobby*, *Into main: Lobby, and Reconnect it stands on*, with more names joined in plain English. */
export function lineOf(p, slug, main = "main") {
  const [head, ...rest] = namesOf(p, slug);
  return `Into ${main}: ${head}${rest.length ? `, and ${joined(rest)} it stands on` : ""}`;
}

/** What pressing the portal does, or that it is sealed and why: its name for a screen reader. */
export function labelOf(p, slug, main = "main") {
  if (!p || p.state === "wait") return `Checking what goes to ${main}`;
  if (p.state === "fail") return `Sealed: what goes to ${main} could not be checked`;
  if (p.sealed) return `Sealed: ${p.sealed}`;
  return `Send ${joined(namesOf(p, slug))} to ${main}`;
}

export const reasonOf = (p) => (p?.state === "fail" ? "What goes to main could not be checked" : p?.sealed || "");

/** Chooses a goal and opens the portal for it: the plan is asked once. A goal already chosen keeps its plan. */
export function choose(slug) {
  if (!slug || chosen.value === slug) return;
  if (!chosen.value && !said) { said = true; first.value = !readSeen(); writeSeen(); }
  chosen.value = slug;
  taking.value = false;
  plan.value = { slug, state: "wait" };
  planning = ask("ideas.to_main_plan", { idea: slug }).then((p) => {
    if (chosen.value !== slug) return;
    plan.value = p ? { ...p, slug, state: "ok", sealed: p.sealed || "" } : { slug, state: "fail" };
  });
}

/** Closes the portal and drops the choice. */
export function close() {
  chosen.value = ""; plan.value = null; taking.value = false; first.value = false; going.value = "";
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** Plays the portal: the chosen goal goes to main, alone with the goals it stands on. A sealed portal says its reason again and plays nothing. */
export async function play() {
  const slug = chosen.value;
  if (!slug || going.value) return;
  await planning;
  const p = plan.value;
  if (chosen.value !== slug || !p || p.slug !== slug) return;
  if (p.state !== "ok" || p.sealed) { echo.value += 1; return; }
  const got = await ask("ideas.to_main", { idea: slug });                                   // an error is toasted by `ask`, as every failed act of the page is
  if (!got) return;
  if (got.note) toast(got.note, "warning");
  const card = document.querySelector(`[data-portal-card="${CSS.escape(slug)}"]`), door = document.querySelector(".portal-host .ork-portal");
  if (card && door && !reduced()) {
    const a = card.getBoundingClientRect(), b = door.getBoundingClientRect();
    card.style.setProperty("--dx", `${Math.round(b.left + b.width / 2 - (a.left + a.width / 2))}px`);
    card.style.setProperty("--dy", `${Math.round(b.top + b.height / 2 - (a.top + a.height / 2))}px`);
    going.value = slug;
    await wait(GO_MS);
  }
  close();
  await refreshShell();
}

function useNarrow() {
  const [narrow, set] = useState(() => typeof matchMedia === "function" && matchMedia(NARROW).matches);
  useEffect(() => {
    if (typeof matchMedia !== "function") return undefined;
    const m = matchMedia(NARROW), on = () => set(m.matches);
    m.addEventListener("change", on);
    on();
    return () => m.removeEventListener("change", on);
  }, []);
  return narrow;
}

/** The portal, above the pile in the table's right column; nothing while no goal is chosen, and none on a phone (hand/readycard.js lays it on the goal's card there). */
export function Portal() {
  return uprightNow.value ? null : html`<${PortalDoor} />`;
}

function PortalDoor() {
  const slug = chosen.value, p = plan.value, narrow = useNarrow(), door = useRef(), r = readyOf();
  const here = !!slug && (r?.goals || []).some((g) => g.slug === slug);
  useEffect(() => { if (slug && !here) close(); }, [slug, here]);                          // the goal left the ready goals (sent, or the gate changed): the portal closes
  useEffect(() => { if (slug && over.value?.kind !== "discard") close(); }, [slug, over.value?.kind]);
  useLayoutEffect(() => { if (slug) door.current?.focus({ preventScroll: true }); }, [slug]);   // Enter on a card moves the focus here
  useEffect(() => {
    if (!slug) return undefined;
    const away = (e) => { if (chosen.value && !e.target?.closest?.(".portal-host, [data-portal-card]")) close(); };
    const esc = (e) => { if (e.key === "Escape" && chosen.value && !e.defaultPrevented) { e.preventDefault(); close(); } };   // a listener that outlives its portal by a frame says nothing
    document.addEventListener("pointerdown", away, true);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("pointerdown", away, true); document.removeEventListener("keydown", esc); };
  }, [slug]);
  if (!slug || !here) return null;
  const main = r.main || "main", sealed = p?.state === "fail" || !!p?.sealed, reason = reasonOf(p);
  const held = (e) => { if (!chosen.value) return; e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = "move"; taking.value = true; };
  const left = (e) => { if (!e.currentTarget.contains(e.relatedTarget)) taking.value = false; };
  const drop = (e) => { e.preventDefault(); taking.value = false; play(); };
  return html`<div class=${cls("portal-host", { "is-new": first.value })} data-portal=${p?.state === "ok" ? (sealed ? "sealed" : "open") : p?.state || "wait"}>
    <p class="portal__line">${p?.state === "ok" ? lineOf(p, slug, main) : p?.state === "fail" ? `Into ${main}: ${titleOf(slug, p)}` : `Checking ${titleOf(slug, p)}…`}</p>
    <span class="portal__label">${main === "main" ? "Main" : main}</span>
    <button type="button" ref=${door} class=${cls("ork-portal", { small: narrow, "is-taking": taking.value, "is-sealed": sealed, "is-new": first.value })}
      aria-label=${labelOf(p, slug, main)} aria-disabled=${p?.state === "wait" ? "true" : undefined} onClick=${play}
      onDragEnter=${held} onDragOver=${held} onDragLeave=${left} onDrop=${drop}></button>
    ${first.value && !sealed && html`<p class="portal__hint">${narrow ? "Tap the portal to send it to main" : "Drag a goal done into the portal to send it to main"}</p>`}
    <p class="portal__sealed" role="status" aria-live="polite">${sealed && html`<span key=${echo.value}>Sealed: ${reason}</span>`}</p>
  </div>`;
}

/** The goals ready for main, each a card as the pile's top card is drawn (the goal's element and name, the check in its window, *Done* and *Ready for main*): pressed or begun to be dragged, a card is chosen. */
export function ReadyCards({ goals, main }) {
  const nodes = Object.fromEntries((mapData.value?.nodes || []).map((n) => [n.slug, n]));
  const held = chosen.value;
  return html`<ul class="portal-cards" aria-label=${`Goals ready for ${main}`}>${goals.map((g) => {
    const n = nodes[g.slug] || {}, on = held === g.slug, gone = going.value === g.slug;
    return html`<li key=${g.slug}><button type="button" data-portal-card=${g.slug} draggable="true" aria-pressed=${on ? "true" : "false"}
        class=${cls(`ork-card ork-leans hand-card hand-card--stop${n.element ? ` el-${n.element}` : ""}`, { "ork-picked": on, "is-going": gone })}
        aria-label=${`${g.title}, ready for ${main}`}
        onClick=${() => { if (!on) choose(g.slug); else document.querySelector(".portal-host .ork-portal")?.focus(); }}
        onDragStart=${(e) => { choose(g.slug); if (e.dataTransfer) { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", g.slug); } }}
        onDragEnd=${() => { taking.value = false; }} ...${leans}>
      <span class="hand-card__head"><${Elem} name=${n.element} dim=${!n.element} /><span class="hand-card__name">${g.title}</span></span>
      <span class="hand-card__window"><span class="hand-card__act"><span class="hand-mark is-ok"><${Sign} name="check" big=${true} label="Done" /></span></span></span>
      <span class="hand-card__label"><span class="hand-card__party">Done</span></span>
      <span class="hand-card__foot">Ready for ${main}</span>
    </button></li>`;
  })}</ul>`;
}
