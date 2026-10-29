// Play (docs/specs/88-assets-and-play.md §5, §6.5, "As built (A)"): the project's own preview of dev's head, opened in the pane. *Open the build* asks the host (`ideas.play`), which answers at once; while it
// starts (*Starting the build…*) the face asks what it is now (`ideas.play` with `peek`) about every second; once it plays, the preview is an `iframe` of its own origin — a sandbox that lets its scripts run, keeps its
// origin and lets it lock the pointer —, *Plays dev at <short commit>* over it and *Stop the build*. While it is shown the face says `peek` every minute: the host stops a Play nobody has asked about for ten minutes.
// A merge into dev changes nothing in it until *Open the build* is pressed again (`fresh`). A build that would not start says why; a project with no preview says *Nothing here yet* and how to give it one.
// The start screen (docs/specs/90-what-the-first-look-said.md §1.3, docs/specs/91-the-owners-list.md §5): while it starts the pane is black (orkUI's canvas), the project's name in the pixel face, large and centred,
// fades in and out in a slow loop (2.4 s, in steps; still under reduced motion), and under it, in the faint ink, one line says the stage — *Making its worktree*, *Starting <command>*, *Waiting for a page on :<port>* — with
// the seconds counting up (`since` from the host, local time after it); when the page has answered (`playing`) the name fades in steps and the frame comes up from the black — an `iframe` is never drawn before that; under reduced
// motion, no steps. A build that did not start says why and shows the command's last lines (`tail`) in a quiet box that scrolls; a build whose port gives no page (`why: "nopage"`) says so with the ports it tried and *Stop the build*.
// With a logo in the project (`b.logo`, realm/assets.py `logo`: its `logo.svg`, `icon.png`, …) the start screen is the logo instead of the name (docs/specs/107-what-the-owners-day-said.md §9.2): 128 px tall, up in six steps, two blinks, then the
// name under it, a light band sweeping across it every 2.4 s while it starts (play.css; none under reduced motion). *Full screen* in the bar lays the stage over the screen (Esc leaves).
// The build is the machine's own address (127.0.0.1): the phone has no Play.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { command } from "../link.js";
import { projectList } from "../shell/projects.js";

export const OPEN = "Open the build", STARTING = "Starting the build…", STOP = "Stop the build";
export const FULL = "Full screen";
export const NOTHING = "Nothing here yet";
export const NOTHING_HOW = "Say how the project opens in .orkcraft/checks.toml: preview = \"npm run dev\", or keep an index.html at its root";
export const SANDBOX = "allow-scripts allow-same-origin allow-pointer-lock";
export const playsAt = (short) => `Plays dev at ${short}`;
export const wouldNot = (why) => `The build would not start: ${why}`;
export const MAKING = "Making its worktree", STARTING_ITS = "Starting its preview", WAITING = "Waiting for a page", LAST_LINES = "Its last lines";
export const waitingOn = (ports) => (ports || []).length ? `${WAITING} on ${ports.map((p) => `:${p}`).join(", ")}` : WAITING;
export const secondsWords = (n) => `${n} s`;
export const NO_PAGE = "The build started, but no port gives a page. Name it in .orkcraft/checks.toml: preview_port or preview_path.";
export const portsTried = (ports) => `Ports tried: ${ports.join(", ")}`;

const POLL_MS = 1000, KEEP_MS = 60_000, FADE_MS = 450, TICK_MS = 500;                // while it starts; while it plays (the host's idle limit is ten minutes)

/** The build as the face shows it: `stopped`, `starting`, `playing` ({url, commit, short, dev}) or `failed` ({error, none}); what `ideas.play` answers, or `reading` before the first answer. */
function useBuild() {
  const [b, setB] = useState({ state: "reading" }), live = useRef(true);
  const take = (r) => { if (live.current) setB(r && r.state ? { ...r, at: Date.now() } : { state: "failed", error: r?.error || "did not open" }); };
  const ask = (args) => command("ideas.play", args, true).then(take).catch((e) => { if (live.current) setB({ state: "failed", error: e.message || "did not open" }); });
  useEffect(() => { live.current = true; ask({ peek: true }); return () => { live.current = false; }; }, []);
  useEffect(() => {
    if (b.state !== "starting" && b.state !== "playing") return undefined;
    const t = setInterval(() => ask({ peek: true }), b.state === "starting" ? POLL_MS : KEEP_MS);
    return () => clearInterval(t);
  }, [b.state]);
  return {
    b,
    open: (fresh) => { setB({ state: "starting", commit: "", short: "", stage: "worktree", since: 0, at: Date.now() }); ask(fresh ? { fresh: true } : {}); },
    stop: () => command("ideas.play_stop", {}, true).then(() => live.current && setB({ state: "stopped" })).catch((e) => live.current && setB({ state: "failed", error: e.message || "did not stop" })),
  };
}

const reduced = () => { try { return !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches; } catch { return false; } };

/** The open project's name, as the project switcher has it (else its folder's, else *the project*). */
function projectName() {
  const list = projectList.value || {}, cur = list.current || "";
  return (list.open || []).find((p) => p.path === cur)?.name || String(cur).split(/[\\/]/).filter(Boolean).pop() || "the project";
}

/** The time now, every `ms` while `on` (the seconds of a start count up on the page, from the host's `since`). */
function useNow(on, ms) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!on) return undefined;
    setNow(Date.now());
    const t = setInterval(() => setNow(Date.now()), ms);
    return () => clearInterval(t);
  }, [on, ms]);
  return now;
}

/** The line under the name: the stage in words, and the seconds since the start. */
function StageLine({ b }) {
  const now = useNow(true, TICK_MS), secs = Math.max(0, Math.floor((Number(b.since) || 0) + (now - (b.at || now)) / 1000));
  const words = b.stage === "command"
    ? (b.command ? html`Starting <code class="play-cmd">${b.command}</code>` : STARTING_ITS)
    : b.stage === "page" ? waitingOn(b.ports) : MAKING;
  return html`<p class="play-starting" role="status"><span class="play-stage-words">${words}</span> <span class="play-secs" aria-hidden="true">${secondsWords(secs)}</span></p>`;
}

/** The project's logo, 128 px tall (a picture under 64 px wide stays in whole pixels), a light band laid over it masked by its own shape. */
function Logo({ src }) {
  const [pixel, setPixel] = useState(false), mask = `url("${src}")`;
  const loaded = (e) => { const w = e.currentTarget.naturalWidth; if (!/\.svg(\?|$)/i.test(src) && w > 0 && w < 64) setPixel(true); };
  return html`<span class="play-logo"><img class=${cls("play-logo__img", { "is-pixel": pixel })} src=${src} alt="" height="128" draggable="false" onLoad=${loaded} />
    <span class="play-logo__sweep" aria-hidden="true" style=${`-webkit-mask-image:${mask};mask-image:${mask}`}></span></span>`;
}

/** The black pane with the project's logo, else its name: `fading` once the page answered (it goes in steps over the frame under it). */
function Intro({ name, fading, done, b }) {
  return html`<div class=${cls("play-intro", { "is-fading": fading, "has-logo": !!b.logo })} aria-hidden=${fading ? "true" : undefined} onAnimationEnd=${(e) => { if (fading && e.animationName === "play-intro-out") done(); }}>
    ${b.logo && html`<${Logo} src=${b.logo} />`}
    <h2 class="play-title">${name}</h2>
    ${!fading && html`<${StageLine} b=${b} />`}
  </div>`;
}

/** The command's last lines, in a quiet box that scrolls (about twelve lines show), the newest at the foot. */
function Tail({ lines }) {
  const box = useRef(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [lines.length]);
  if (!lines.length) return null;
  return html`<div class="play-tail"><p class="arena-cap play-tail__cap">${LAST_LINES}</p><pre class="play-tail__lines" ref=${box} tabindex="0" aria-label=${LAST_LINES}>${lines.join("\n")}</pre></div>`;
}

export function Play() {
  const { b, open, stop } = useBuild(), name = projectName(), stage = useRef(null);
  const full = () => { try { stage.current?.requestFullscreen?.()?.catch?.(() => {}); } catch { /* the browser would not */ } };
  const came = useRef(false), [gone, setGone] = useState(false);
  if (b.state === "starting") came.current = true;
  else if (b.state !== "playing") came.current = false;
  useEffect(() => {                                    // the start screen leaves by its own animation; a timer is the net
    if (b.state !== "playing" || !came.current) { setGone(false); return undefined; }
    const t = setTimeout(() => setGone(true), FADE_MS + 250);
    return () => clearTimeout(t);
  }, [b.state]);
  if (b.state === "reading") return html`<div class="playpane" data-state="reading"><p class="arena-cap play-note"><span class="ork-busy"></span></p></div>`;
  if (b.state === "starting") {
    return html`<div class="playpane is-black" data-state="starting"><${Intro} name=${name} b=${b} /></div>`;
  }
  if (b.state === "playing") {
    const moved = b.dev && b.commit && b.dev !== b.commit, intro = came.current && !gone && !reduced();
    return html`<div class="playpane" data-state="playing">
      <div class="play-bar">
        <span class="play-at"><${Sign} name="play" /> <span>${playsAt(b.short || String(b.commit || "").slice(0, 7))}</span></span>
        ${moved && html`<span class="arena-cap play-moved">dev is at ${String(b.dev).slice(0, 7)} now</span>`}
        <span class="arena-spacer"></span>
        ${moved && html`<button type="button" class="ork-btn" onClick=${() => open(true)}>${OPEN}</button>`}
        <button type="button" class="ork-btn play-full" title="Fill the screen with it: Esc leaves" onClick=${full}>${FULL}</button>
        <button type="button" class="ork-btn" onClick=${stop}>${STOP}</button>
      </div>
      <div class=${cls("play-stage", { "is-rising": intro })} ref=${stage}>
        <iframe class="play-frame" src=${b.url} title="Play" sandbox=${SANDBOX} allow="autoplay; fullscreen; gamepad"></iframe>
        ${intro && html`<${Intro} name=${name} fading=${true} done=${() => setGone(true)} />`}
      </div>
    </div>`;
  }
  if (b.state === "failed" && b.none) {
    return html`<div class="playpane" data-state="none"><div class="assets-none"><p class="assets-none__title">${NOTHING}</p><p class="arena-cap">${NOTHING_HOW}</p></div></div>`;
  }
  if (b.state === "failed" && b.why === "nopage") {
    return html`<div class="playpane is-failed" data-state="nopage">
      <div class="play-start">
        <p class="play-error" role="alert">${NO_PAGE}</p>
        ${(b.ports || []).length > 0 && html`<p class="arena-cap play-ports">${portsTried(b.ports)}</p>`}
        <${Tail} lines=${b.tail || []} />
        <button type="button" class="ork-btn primary" onClick=${stop}>${STOP}</button>
      </div>
    </div>`;
  }
  return html`<div class=${cls("playpane", { "is-failed": b.state === "failed" })} data-state=${b.state === "failed" ? "failed" : "idle"}>
    <div class="play-start">
      ${b.state === "failed" && html`<p class="play-error" role="alert">${wouldNot(b.error)}</p>`}
      ${b.state === "failed" && html`<${Tail} lines=${b.tail || []} />`}
      <button type="button" class="ork-btn primary" onClick=${() => open(false)}>${OPEN}</button>
    </div>
  </div>`;
}
