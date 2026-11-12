// The portal to main (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §6, decisions §177.4; docs/specs/156-one-pick-and-the-release-column.md D.4, decisions §261.8): the goal ready for main is chosen, its plan asked once (`ideas.to_main_plan`, it runs a trial
// worktree), its checks run at the wide width (`ideas.to_main_checks`, checks.js), and `play()` sends it alone with the goals it stands on (`ideas.to_main`); the card goes into the portal and leaves the ready goals at the next `ideas.gate` read.
// While the gate holds the goal the portal is sealed, the reason in the danger colour; a press on it says the reason again and plays nothing. The portal is orkUI's (`.ork-portal`, 0.18.0; at the wide width its ring `.ork-portal-ring`, 0.20.0); its sheet is portal.css.
// **At the wide width** (760 px and up) there is no portal of its own: the ring is drawn only round the top card of Release's lane while a goal is ready for main, its checks run or the rite plays (ring.js); the ready card **picked** (part B) is the
// one chosen (lane.js calls `choose`), **To main is its act on the table** (tomain.js) and Release's table shows its checks (checksview.js). The rite plays in the ring (`is-sending rite-<element>`, once, 1.2 s, in the goal's colour).
// **At the narrow width** the portal opens above the pile at the lanes' end (`.table-end`) while a goal done is chosen in the discard's view, orkUI's `small`, the line over it and the pixel-face label *Main*; a card held over it is `is-taking`, dropped on it or the portal pressed
// sends the goal. Pressing works as dragging does: the press path needs no drag, so it is the phone's (hand/readycard.js lays it on the goal's card there).
import { signal } from "@preact/signals";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { ask } from "../board/store.js";
import { mapData, refreshShell } from "../shell/store.js";
import { openOver, over } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { readyOf } from "../hand/data.js";
import { reduced, leans } from "../hand/motion.js";
import { wide } from "./data.js";
import { CHECKING, checksOf, forgetChecks, isRed, pending, readChecks, redOf, sealedWords, startChecks, whenAsked } from "./checks.js";

const SEEN_KEY = "orkboard.portal.seen";
const NARROW = "(max-width: 759.98px)";
export const GO_MS = 260;                                  // the card's travel into the portal (portal.css `portal-go`)

const chosen = signal("");                                 // the goal chosen (its slug), "" while the portal is closed
export const plan = signal(null);                                 // what `ideas.to_main_plan` said of it: {slug, state: "wait" | "ok" | "fail", goals, titles, sealed, files}
export const taking = signal(false);                              // a card is held over the portal
export const going = signal("");                                  // the goal whose card is going in
export const first = signal(false);                               // the first time the portal opens on this device
export const sending = signal("");                                // the element of the goal that went in: the ring plays its rite (`is-sending rite-<element>`) for RITE_MS
export const RITE_MS = 1200;
export const woke = signal(false);                                       // the ring's first waking has played: its class comes off, so the ring opening and closing again (the checks) does not play it again
export const dissolving = signal([]);                              // the cards of the goals that went through the portal, dissolving into its ring of runes while the rite plays (spec 168 F3; none under reduced motion)
export const DISSOLVE_MS = 640;
export const stopped = signal(null);                              // what stopped the goal on its way into main, in words: {slug, words, none}; `none` when the project has no tests (the card then offers *To main without the tests*)
export const echo = signal(0);                                    // a press on a sealed portal says its reason again
let planning = Promise.resolve(), said = false, selection = 0;

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
  const request = ++selection;
  chosen.value = slug;
  taking.value = false;
  plan.value = { slug, state: "wait" };
  stopped.value = null;
  planning = ask("ideas.to_main_plan", { idea: slug }).then((p) => {
    if (chosen.value !== slug || request !== selection) return;
    plan.value = p ? { ...p, slug, state: "ok", sealed: p.sealed || "" } : { slug, state: "fail" };
    if (p && wide.value && (!p.sealed || p.conflict)) readChecks(slug);                    // the way into main is checked (a seal no check owns is not: it keeps its X)
  });
}

/** Whether a check of the goal still stands in the way (running, waiting or red), or its checks were just asked. */
const checkedOpen = (slug) => pending.value === slug || checksOf(slug).some((c) => c.state !== "passed");

/** The goals the picked one takes along (`goal_main.plan`: the goal and what it stands on that main lacks), lit on the pile while it is chosen. */
export const alongOf = (slug) => new Set(chosen.value === slug && plan.value?.slug === slug && plan.value.state === "ok" ? (plan.value.goals || []).filter((s) => s !== slug) : []);

/** Closes the portal and drops the choice. */
export function close() {
  selection += 1;
  chosen.value = ""; plan.value = null; stopped.value = null; taking.value = false; first.value = false; going.value = "";
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
  const owned = p.state === "ok" && (!p.sealed || p.conflict);                              // a seal no check owns is not checked: it keeps its X
  let asked = false;
  if (owned && !checksOf(slug).length && pending.value !== slug) {                          // the checks come first, on every width: nothing is sent that was not checked (decisions §274.2)
    asked = true;
    await readChecks(slug);
    while (chosen.value === slug && (pending.value === slug || checksOf(slug).some((c) => c.state === "waiting" || c.state === "running"))) await wait(150);
    if (chosen.value !== slug) return;
  }
  if (isRed(checksOf(slug))) {                                                              // a red check stops it, and says which test
    stopped.value = { slug, words: `Sealed: ${sealedWords(checksOf(slug))}`, none: false };
    echo.value += 1;
    return;
  }
  if (p.state !== "ok" || (p.sealed && !(p.conflict && checksOf(slug).length)) || (!asked && checkedOpen(slug))) {
    echo.value += 1;
    if (p.state === "ok" && checkedOpen(slug) && !(p.sealed && !p.conflict)) toast(CHECKING, "information", "", 3);   // a press or a drop while the checks run is not lost in silence
    return;
  }
  stopped.value = null;
  await enter(slug, false);
}

/** **To main without the tests** (decisions §274.3): the one way past a project that has no tests, sent only from the card that said so. */
export async function playUntested(slug) {
  if (!slug || going.value || chosen.value !== slug) return;
  await enter(slug, true);
}

/** Sends the goal (`untested` only from *To main without the tests*); a refusal of the host is said on the card in its words. */
async function enter(slug, untested) {
  let got = null;
  try { got = await command("ideas.to_main", { idea: slug, sealed: true, ...(untested ? { untested: true } : {}) }, true); } catch (e) { if (!e.refused) toast(e.message, "error", "ideas.to_main"); stoppedBy(slug, e.message); return; }
  if (got?.error) { toast(got.error, "error"); stoppedBy(slug, got.error); return; }
  got = got || {};
  if (got.note) toast(got.note, "warning");
  const sent = (mapData.value?.nodes || []).find((n) => n.slug === slug), element = sent?.hue || sent?.element || "";
  const ring = !!document.querySelector(".portal-host.is-ring"), still = reduced();
  if (element && !still && ring) sending.value = element;       // the rite in the ring, in the goal's colour
  if (ring && !still) {                                                                    // the cards it took dissolve into the ring of runes, then leave (decisions §283.28); under reduced motion nothing moves
    dissolving.value = [...new Set([slug, ...(got.goals || []), ...(plan.value?.slug === slug ? plan.value.goals || [] : [])])];
    await wait(DISSOLVE_MS);
    dissolving.value = [];
  }
  const card = document.querySelector(`[data-portal-card="${CSS.escape(slug)}"]`), door = document.querySelector(".portal-host .ork-portal");      // no door at the wide width: the card stays in its ring while the rite plays
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

function stoppedBy(slug, words) {
  if (!words || chosen.value !== slug) return;
  stopped.value = { slug, words, none: /^This project has no tests/.test(words) };
  echo.value += 1;
}

/** What stopped the chosen goal and, for a project with no tests, the one way on: *To main without the tests*. */
export function Stopped({ slug, tone = "portal__sealed", button = true }) {
  const s = stopped.value;
  if (!s || s.slug !== slug) return null;
  return html`<p class=${tone} role="status" aria-live="polite" data-stopped=${slug}>${s.words}</p>${s.none && button && html`<button type="button" class="ork-btn quiet" data-to-main-untested
    title="Sends the goal to main with no test run: nothing has shown it is safe" onClick=${() => playUntested(slug)}>To main without the tests</button>`}`;
}

/** The goal chosen for the portal (its slug), "" when none is. */
export const chosenSlug = () => chosen.value;

/** The discard's **To main** (spec 149 G.1, decisions §253.7): the portal's way, not dev whole. The goal is chosen (as a card pressed is), its plan asked and, at the wide width, its checks run; the press waits while they run and then plays the portal:
 *  a red check or a seal says its reason as the portal does, and nothing is sent. */
export async function toMain(slug) {
  if (!slug) return;
  choose(slug);
  await planning;
  await whenAsked();
  while (chosen.value === slug && (pending.value === slug || checksOf(slug).some((c) => c.state === "waiting" || c.state === "running"))) await wait(150);
  if (chosen.value === slug) await play();
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
export function openedOnce() {
  if (said) return;
  said = true;
  first.value = !readSeen();
  writeSeen();
}

/** The portal's place at the narrow width: above the pile at the lanes' end, only while a goal is chosen; none at the wide width (the ring lies round the lane's top card: ring.js) and none on a phone (hand/readycard.js lays it on the goal's card there). */
export function Portal() {
  const narrow = useNarrow();
  return narrow && !uprightNow.value ? html`<${PortalDoor} />` : null;
}

const openDiscard = () => openOver("discard", {}, null, "Done");

function PortalDoor() {
  const slug = chosen.value, p = plan.value, door = useRef(), r = readyOf();
  const here = !!slug && (r?.goals || []).some((g) => g.slug === slug);
  useEffect(() => { if (slug && !here) close(); }, [slug, here]);                          // the goal left the ready goals (sent, or the gate changed): the choice is dropped
  useEffect(() => { if (slug && over.value?.kind !== "discard") close(); }, [slug, over.value?.kind]);   // the view closed: the choice is dropped
  useLayoutEffect(() => { if (slug) door.current?.focus({ preventScroll: true }); }, [slug]);   // Enter on a card moves the focus here
  useEffect(() => {
    if (!slug) return undefined;
    const away = (e) => { if (chosen.value && !e.target?.closest?.(".portal-host, [data-portal-card], [data-to-main]")) close(); };
    const esc = (e) => { if (e.key === "Escape" && chosen.value && !e.defaultPrevented) { e.preventDefault(); close(); } };   // a listener that outlives its portal by a frame says nothing
    document.addEventListener("pointerdown", away, true);
    document.addEventListener("keydown", esc);
    return () => { document.removeEventListener("pointerdown", away, true); document.removeEventListener("keydown", esc); };
  }, [slug]);
  const open = !!slug && here;
  if (!open) return null;
  const candidate = r?.goals.find((g) => g.slug === slug);
  const checking = pending.value === slug || checksOf(slug).some((c) => c.state === "waiting" || c.state === "running");
  const main = r?.main || "main", red = redOf(slug, candidate), sealed = red || p?.state === "fail" || !!p?.sealed, reason = red ? sealedWords(checksOf(slug)) || candidate?.main_reason || "Checks failed" : sealed ? reasonOf(p) : "", said = html`<span key=${echo.value}>Sealed: ${reason}</span>`;
  const held = (e) => { if (!chosen.value) return; e.preventDefault(); if (e.dataTransfer) e.dataTransfer.dropEffect = "move"; taking.value = true; };
  const left = (e) => { if (!e.currentTarget.contains(e.relatedTarget)) taking.value = false; };
  const drop = (e) => { e.preventDefault(); taking.value = false; play(); };
  const state = p?.state === "ok" ? (sealed ? "sealed" : "open") : p?.state || "wait";
  const line = p?.state === "ok" ? lineOf(p, slug, main) : p?.state === "fail" ? `Into ${main}: ${titleOf(slug, p)}` : `Checking ${titleOf(slug, p)}…`;
  const button = html`<button type="button" ref=${door} class=${cls("ork-portal small", { "is-taking": taking.value, "is-sealed": sealed, "is-new": first.value })}
      aria-label=${labelOf(p, slug, main)} disabled=${red || checkedOpen(slug)} aria-disabled=${p?.state === "wait" ? "true" : undefined} onClick=${play}
      onDragEnter=${held} onDragOver=${held} onDragLeave=${left} onDrop=${drop}></button>`;
  const hint = first.value && !sealed && html`<p class="portal__hint">Tap the portal to send it to main</p>`;
  return html`<div class=${cls("portal-host", { "is-new": first.value })} data-portal=${state}>
    <p class="portal__line">${line}</p>
    <span class="portal__label">${main === "main" ? "Main" : main}</span>
    ${button}${hint}${red && html`<button type="button" class="ork-btn" disabled=${checking} onClick=${() => startChecks(slug, true)}>Test again</button>`}<p class="portal__sealed" role="status" aria-live="polite">${checking ? CHECKING : sealed && said}</p><${Stopped} slug=${slug} />
  </div>`;
}

/** The goals ready for main, each a card as the pile's top card is drawn (the goal's element and name, the check in its window, *Done* and *Ready for main*): pressed or begun to be dragged, a card is chosen. */
export function ReadyCards({ goals, main, onPress = null, on: picked = "" }) {
  const nodes = Object.fromEntries((mapData.value?.nodes || []).map((n) => [n.slug, n]));
  const held = onPress ? picked : chosen.value;
  return html`<ul class="portal-cards" aria-label=${goals.some((g) => redOf(g.slug, g)) ? "Goals awaiting checks before main" : `Goals ready for ${main}`}>${goals.map((g) => {
    const n = nodes[g.slug] || {}, on = held === g.slug, gone = going.value === g.slug, red = redOf(g.slug, g), along = !!held && !on && alongOf(held).has(g.slug), melting = dissolving.value.includes(g.slug);
    return html`<li key=${g.slug}><button type="button" data-portal-card=${g.slug} draggable=${onPress ? undefined : "true"} aria-pressed=${on ? "true" : "false"}
        class=${cls(`ork-card ork-leans hand-card hand-card--stop${n.element ? ` el-${n.hue || n.element}` : ""}`, { "ork-picked": on, "is-going": gone, "is-along": along, "is-dissolving": melting })} data-along=${along ? "1" : undefined}
        aria-label=${`${g.title}, ${red ? "checks failed" : `ready for ${main}`}`}
        onClick=${() => { if (onPress) onPress(g.slug); else if (!on) choose(g.slug); else document.querySelector(".portal-host .ork-portal")?.focus(); }}
        onDragStart=${(e) => { if (onPress) { e.preventDefault(); return; } choose(g.slug); if (e.dataTransfer) { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", g.slug); } }}
        onDragEnd=${() => { taking.value = false; }} ...${leans}>
      <span class="hand-card__head"><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} /><span class="hand-card__name">${g.title}</span></span>
      <span class="hand-card__window"><span class="hand-card__act"><span class="hand-mark is-ok"><${Sign} name="check" big=${true} label="Done" /></span></span></span>
      <span class="hand-card__label"><span class="hand-card__party">Done</span></span>
      <span class="hand-card__foot">${red ? "Checks failed" : `Ready for ${main}`}</span>
    </button></li>`;
  })}</ul>`;
}
