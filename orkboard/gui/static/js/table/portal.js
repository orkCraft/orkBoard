// The portal to main (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §6, decisions §177.4; docs/specs/110-runes-on-the-table.md §3.2, decisions §185.2, §186.3, §186.5): in the discard's view each goal ready for main is a card; pressing one, or starting to drag it, chooses it
// and sends it through the portal on the table's right (the `.table-end` place) with the pixel-face label *Main* and the line the host's plan says (`ideas.to_main_plan`, asked once when a goal is chosen, because it
// runs a trial worktree). A card held over the portal is `is-taking`; dropped on it, or the portal pressed while a card is chosen (Enter on the focused portal too), `ideas.to_main` sends the goal alone with the goals it
// stands on, the card goes into the portal and leaves the ready goals at the next `ideas.gate` read. While the gate holds the goal the portal is `is-sealed`, the reason under it in the danger colour; a press on it says the
// reason again and plays nothing. Pressing works as dragging does: the press path needs no drag, so it is the phone's. The portal is orkUI's (`.ork-portal`, 0.18.0); its sheet is portal.css, layout only.
// At the wide width (760 px and up) its place is always laid (§185.2): orkUI's ring of runes (`.ork-portal-ring`, 0.20.0), asleep (grey, nothing to press, *Main* in the faint ink) while no goal is ready for main, and open (the portal
// inside it, a button) as long as one is, whether or not one is chosen. The first time it opens on a device it wakes (`is-waking`, the portal's `is-new`, a per-viewer convenience in localStorage; the page works without it) with a line
// saying how. The chosen goal's element lies in the ring's seal (§186.3: its rune, in its own colour; faint while the portal is sealed). With no goal chosen the open portal, pressed, opens the discard's view where the goals ready are
// chosen; closing the view (or Esc, or a press away) drops the choice and no longer closes the portal. At the narrow width nothing changes: the portal opens above the pile when a goal is chosen and closes with the choice.
// **The road** (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4, decisions §188): at the wide width the ring also holds Release (lower left, before main) and Live (upper right) as corners (road.js), and a goal chosen for
// main has its checks run (`ideas.to_main_checks`, checks.js): each check is a skeleton in the gate in front of the portal (`is-sealed is-guarded`, the line *Checking the way into main*) until it passes and goes to Release's corner with a
// tick; a red one stays, the sealed line says *Sealed: <check> is red: <why>*; with every check passed the portal opens. A seal no check owns (a goal not done, main behind its origin) keeps the sealed portal with its X. When a goal goes
// in, the ring plays the rite in the goal's colour (`is-sending rite-<element>`, once, 1.2 s).
import { signal } from "@preact/signals";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { toast } from "../link.js";
import { ask } from "../board/store.js";
import { mapData, refreshShell } from "../shell/store.js";
import { openOver, over } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { readyOf } from "../hand/data.js";
import { reduced, leans } from "../hand/motion.js";
import { wide } from "./data.js";
import { CHECKING, checksOf, forgetChecks, isRed, pending, sealedWords, skeletonsOf, startChecks, whenAsked } from "./checks.js";
import { Corner, Gate, roadNow } from "./road.js";

const SEEN_KEY = "orkboard.portal.seen";
const NARROW = "(max-width: 759.98px)";
export const GO_MS = 260;                                  // the card's travel into the portal (portal.css `portal-go`)

const chosen = signal("");                                 // the goal chosen (its slug), "" while the portal is closed
export const plan = signal(null);                                 // what `ideas.to_main_plan` said of it: {slug, state: "wait" | "ok" | "fail", goals, titles, sealed, files}
const taking = signal(false);                              // a card is held over the portal
export const going = signal("");                                  // the goal whose card is going in
export const first = signal(false);                               // the first time the portal opens on this device
export const sending = signal("");                                // the element of the goal that went in: the ring plays its rite (`is-sending rite-<element>`) for RITE_MS
export const RITE_MS = 1200;
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
  if (!chosen.value) openedOnce();
  chosen.value = slug;
  taking.value = false;
  plan.value = { slug, state: "wait" };
  planning = ask("ideas.to_main_plan", { idea: slug }).then((p) => {
    if (chosen.value !== slug) return;
    plan.value = p ? { ...p, slug, state: "ok", sealed: p.sealed || "" } : { slug, state: "fail" };
    if (p && wide.value && (!p.sealed || p.conflict)) startChecks(slug);                    // the way into main is checked (a seal no check owns is not: it keeps its X)
  });
}

/** Whether a check of the goal still stands in the way (running, waiting or red), or its checks were just asked. */
const checkedOpen = (slug) => pending.value === slug || checksOf(slug).some((c) => c.state !== "passed");

/** Closes the portal and drops the choice. */
export function close() {
  chosen.value = ""; plan.value = null; taking.value = false; first.value = false; going.value = "";
  forgetChecks();
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/** Plays the portal: the chosen goal goes to main, alone with the goals it stands on. A sealed portal says its reason again and plays nothing. */
export async function play() {
  const slug = chosen.value;
  if (!slug || going.value) return;
  await planning;
  await whenAsked();                                                                         // a press before the host has said what its checks stand at waits for that
  const p = plan.value;
  if (chosen.value !== slug || !p || p.slug !== slug) return;
  if (p.state !== "ok" || (p.sealed && !(p.conflict && checksOf(slug).length)) || checkedOpen(slug)) { echo.value += 1; return; }
  const got = await ask("ideas.to_main", { idea: slug });                                   // an error is toasted by `ask`, as every failed act of the page is
  if (!got) return;
  if (got.note) toast(got.note, "warning");
  const element = (mapData.value?.nodes || []).find((n) => n.slug === slug)?.element || "";
  if (element && !reduced() && document.querySelector(".portal-host.is-ring")) sending.value = element;       // the rite in the ring, in the goal's colour
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

/** Whether the window is at the narrow width (under 760 px): the table's end is laid always above it and only as it is needed below. */
export function useNarrow() {
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

/** The first time the portal opens on this device (the wide ring opening, or a goal chosen at the narrow width): `first` says so until the choice is dropped; said once a page. */
function openedOnce() {
  if (said) return;
  said = true;
  first.value = !readSeen();
  writeSeen();
}

/** The portal's place, above the pile in the table's right column: at the wide width the ring of runes always (asleep, or open with the portal inside), at the narrow one the portal alone while a goal is chosen; none on a phone (hand/readycard.js lays it on the goal's card there). */
export function Portal() {
  return uprightNow.value ? null : html`<${PortalDoor} />`;
}

const openDiscard = () => openOver("discard", {}, null, "Done");

function PortalDoor() {
  const slug = chosen.value, p = plan.value, narrow = useNarrow(), door = useRef(), r = readyOf();
  const ready = !!r && r.goals.length > 0, here = !!slug && (r?.goals || []).some((g) => g.slug === slug);
  const ring = !narrow;                                                                    // the wide ring: laid always
  useEffect(() => { if (slug && !here) close(); }, [slug, here]);                          // the goal left the ready goals (sent, or the gate changed): the choice is dropped
  useEffect(() => { if (slug && over.value?.kind !== "discard") close(); }, [slug, over.value?.kind]);   // the view closed: the choice is dropped (the ring stays open at the wide width)
  useLayoutEffect(() => { if (ring && ready) openedOnce(); }, [ring, ready]);               // the ring opens: it wakes the first time on a device
  useLayoutEffect(() => { if (slug) door.current?.focus({ preventScroll: true }); }, [slug]);   // Enter on a card moves the focus here
  useEffect(() => {
    if (!slug) return undefined;
    const away = (e) => { if (chosen.value && !e.target?.closest?.(".portal-host, [data-portal-card]")) close(); };
    const esc = (e) => { if (e.key === "Escape" && chosen.value && !e.defaultPrevented) { e.preventDefault(); close(); } };   // a listener that outlives its portal by a frame says nothing
    document.addEventListener("pointerdown", away, true);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("pointerdown", away, true); document.removeEventListener("keydown", esc); };
  }, [slug]);
  useEffect(() => {                                                                          // the rite plays once: its class is taken off after RITE_MS (the ring's animations are done by then)
    if (!sending.value) return undefined;
    const t = setTimeout(() => { sending.value = ""; }, RITE_MS);
    return () => clearTimeout(t);
  }, [sending.value]);
  const open = !!slug && here;
  if (!ring && !open) return null;
  const main = r?.main || "main";
  // The checks on the way into main (wide width only): a skeleton in the gate for each check that has not passed, the portal sealed and guarded while one stands; a seal no check owns keeps its X.
  const owned = ring && open && p?.state === "ok" && (!p.sealed || p.conflict), list = owned ? checksOf(slug) : [], asking = owned && pending.value === slug && !list.length;
  const red = isRed(list), guard = owned && (asking || list.some((c) => c.state !== "passed")), checking = guard && !red;
  const skeletons = skeletonsOf(list), mine = owned && list.length > 0;
  const sealed = open && (p?.state === "fail" || (!!p?.sealed && !(p.conflict && (list.length > 0 || asking)))), shut = sealed || guard;
  const reason = sealed ? reasonOf(p) : red ? sealedWords(list) : "", said = html`<span key=${echo.value}>Sealed: ${reason}</span>`;
  const held = (e) => { if (!chosen.value) return; e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = "move"; taking.value = true; };
  const left = (e) => { if (!e.currentTarget.contains(e.relatedTarget)) taking.value = false; };
  const drop = (e) => { e.preventDefault(); taking.value = false; play(); };
  const state = open ? (p?.state === "ok" ? (sealed || red ? "sealed" : checking ? "check" : "open") : p?.state || "wait") : ready ? "ready" : "asleep";
  const none = !open, line = open && (checking ? CHECKING : red ? "" : p?.state === "ok" ? lineOf(p, slug, main) : p?.state === "fail" ? `Into ${main}: ${titleOf(slug, p)}` : `Checking ${titleOf(slug, p)}…`);
  const waits = open && (p?.state === "wait" || checking);
  const button = html`<button type="button" ref=${door} class=${cls("ork-portal", { small: narrow, "is-taking": taking.value, "is-sealed": shut, "is-guarded": guard, "is-new": first.value })}
      aria-label=${none ? `Choose a goal done to send it to ${main}` : checking ? CHECKING : red ? `Sealed: ${reason}` : labelOf(p, slug, main)} aria-disabled=${waits ? "true" : undefined} onClick=${none ? openDiscard : play}
      onDragEnter=${held} onDragOver=${held} onDragLeave=${left} onDrop=${drop}></button>`;
  const element = open ? (mapData.value?.nodes || []).find((n) => n.slug === slug)?.element || "" : "";
  const label = main === "main" ? "Main" : main;
  const hint = first.value && !shut && (ready || open) && html`<p class="portal__hint">${narrow ? "Tap the portal to send it to main" : "Drag a goal done into the portal to send it to main"}</p>`;
  const reasoned = html`<p class="portal__sealed" role="status" aria-live="polite">${sealed && said}</p>`;
  if (!ring) {
    return html`<div class=${cls("portal-host", { "is-new": first.value })} data-portal=${state}>
      <p class="portal__line">${line}</p>
      <span class="portal__label">${label}</span>
      ${button}${hint}${reasoned}
    </div>`;
  }
  const road = roadNow(skeletons, checking), passed = mine ? skeletons.filter((s) => s.state === "passed") : null, corners = !!(road.release || road.live);
  return html`<div class=${cls("portal-host is-ring", { "is-new": first.value, "is-asleep": !ready })} data-portal=${state}>
    ${open && line && html`<p class="portal__line">${line}</p>`}
    ${red && !sealed && html`<p class="portal__line is-red" role="status" aria-live="polite">${said}</p>`}
    <span class="portal__label">${label}</span>
    <span class=${cls("ork-portal-ring", { "is-open": (ready && !shut) || !!sending.value, "is-sealed": shut, "is-waking": ready && first.value, "is-taking": taking.value, "is-sending": !!sending.value, [`rite-${sending.value}`]: !!sending.value })}
        aria-hidden=${ready || corners ? undefined : "true"}>
      ${ready && button}
      <span class="ork-portal-ring__seal" aria-hidden="true">${element && html`<${Elem} name=${element} />`}</span>
      <${Corner} side="before" words="Release: open its view" c=${road.release} passed=${passed} />
      <${Corner} side="after" words="Live: open its view" c=${road.live} />
      ${guard && html`<${Gate} skeletons=${skeletons} onPress=${play} />`}
    </span>
    ${hint}${reasoned}
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
