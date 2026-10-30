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
// Play is a die (docs/specs/112-the-bars-marks-and-the-play-die.md §3.3–§3.4, decisions §190.3): the die in the hand (hand/playdie.js) opens this view, and the view starts the build at once when none runs (it asks with `peek` first, then starts: no second press
// of *Open the build*; that button is left for a build stopped or failed). A build that starts is thrown onto the pane: a `.ork-die is-rolling` flies from the hand's die (its rectangle: `dieRect`, a WAAPI flight of five steps, 300 ms, translate and rotate only) to the black pane's
// middle, grows there in whole cells (3, 4, 6 px a cell, 120 ms: `--_n`; never a scale, which would fix the die's raster at a small scale and show the seams between its cells) and rolls the whole start, the stage line under it; the logo is not shown meanwhile. When the page answers the roll stops on `face-ok` (the green tick), turned by the lean token the other way, a three-step landing, *It started* for a moment; the die leaves
// and today's intro stands in its place (the logo up in six steps, two blinks, the name: about 1.8 s with a logo, 1 s with the name alone), then today's fade and the frame rising out of the black. When the start failed the roll stops on `face-no` (the red cross), the
// die tips over in three steps and today's failure view takes its place. The hand's die is hidden while its copy is out and is back, glowing (`is-playing`), when the frame rises, or when the failure shows. A view opened on a build already playing (*warm*) has no
// throw and no intro: the frame opens at once and the hand's die wobbles twice. Under reduced motion none of it: today's start screen exactly (the logo or the name while it starts, no die on the pane, no fade). The throw's phases are `ph`: `fly` · `roll` · `ok` /
// `no` (landed) · `ok-leave` / `no-leave` · `logo` · `out`; the pane says it as `data-throw`.
// A project with no preview (the snapshot's `preview` is "", the die in the hand asleep: spec 113 §3, decisions §191.1) is not asked to start: the view says *Nothing here yet* and how at once, with no throw.
// The build is the machine's own address (127.0.0.1): the phone has no Play.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { command } from "../link.js";
import { projectList } from "../shell/projects.js";
import { asleepNow, dieRect, playing, thrown, warmed } from "../hand/playdie.js";

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
export const STARTED = "It started", NOT_STARTED = "It did not start";

const POLL_MS = 1000, KEEP_MS = 60_000, FADE_MS = 450, TICK_MS = 500;                // while it starts; while it plays (the host's idle limit is ten minutes)
const FLY_MS = 420, HOLD_OK_MS = 600, HOLD_NO_MS = 700, LEAVE_OK_MS = 300, LEAVE_NO_MS = 360, INTRO_LOGO_MS = 1800, INTRO_NAME_MS = 1000;      // the throw: the flight; landed (the landing and a moment); leaving; the intro (the name shows after the logo's blinks)

/** The build as the face shows it: `stopped`, `starting`, `playing` ({url, commit, short, dev}) or `failed` ({error, none}); what `ideas.play` answers, or `reading` before the first answer. */
function useBuild() {
  const [b, setB] = useState({ state: "reading" }), live = useRef(true);
  const take = (r) => { if (live.current) setB(r && r.state ? { ...r, at: Date.now() } : { state: "failed", error: r?.error || "did not open" }); };
  const fail = (e) => { if (live.current) setB({ state: "failed", error: e.message || "did not open" }); };
  const ask = (args) => command("ideas.play", args, true).then(take).catch(fail);
  const begin = (fresh) => { setB({ state: "starting", commit: "", short: "", stage: "worktree", since: 0, at: Date.now() }); ask(fresh ? { fresh: true } : {}); };
  useEffect(() => {                                   // the die was pressed: a build that is not running is started at once (spec 112 §3.4)
    live.current = true;
    if (asleepNow()) { setB({ state: "failed", none: true, error: "no preview" }); return () => { live.current = false; }; }      // the project has no preview (the die sleeps, spec 113 §3): *Nothing here yet*, nothing asked, nothing thrown
    command("ideas.play", { peek: true }, true).then((r) => (r?.state === "stopped" && live.current ? begin(false) : take(r))).catch(fail);
    return () => { live.current = false; };
  }, []);
  useEffect(() => {
    if (b.state !== "starting" && b.state !== "playing") return undefined;
    const t = setInterval(() => ask({ peek: true }), b.state === "starting" ? POLL_MS : KEEP_MS);
    return () => clearInterval(t);
  }, [b.state]);
  return {
    b,
    open: begin,
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

/** The black pane with the project's logo, else its name: `fading` once the page answered (it goes in steps over the frame under it). `line` false: no stage line under it (after the throw, the start is over). */
function Intro({ name, fading, done, b, line = true }) {
  return html`<div class=${cls("play-intro", { "is-fading": fading, "has-logo": !!b.logo })} aria-hidden=${fading ? "true" : undefined} onAnimationEnd=${(e) => { if (fading && e.animationName === "play-intro-out") done(); }}>
    ${b.logo && html`<${Logo} src=${b.logo} />`}
    <h2 class="play-title">${name}</h2>
    ${!fading && line && html`<${StageLine} b=${b} />`}
  </div>`;
}

/** The die thrown onto the black pane (spec 112 §3.4): it flies from the hand's die to the middle (once, on arrival), rolls the whole start with the stage line under it, lands on its outcome (`ok` the tick, `no` the cross) with a line, and leaves
 *  (`ok-leave` fades, `no-leave` tips over). The hand's die is the flight's start: `dieRect()`. */
function Throw({ ph, b }) {
  const slot = useRef(null), die = useRef(null), [n, setN] = useState(ph === "fly" ? 3 : 6);
  const ok = ph === "ok" || ph === "ok-leave", no = ph === "no" || ph === "no-leave", landed = ok || no;
  useLayoutEffect(() => {                              // the flight: the die as the hand's (3 px a cell) from the hand to the slot's middle, then it grows in whole cells to its 6
    const el = die.current, to = slot.current?.getBoundingClientRect(), from = dieRect(), t = [setTimeout(() => setN(4), FLY_MS - 120), setTimeout(() => setN(6), FLY_MS - 60)];
    if (el && to && typeof el.animate === "function") {
      const dx = from ? from.left + from.width / 2 - (to.left + to.width / 2) : 0, dy = from ? from.top + from.height / 2 - (to.top + to.height / 2) : 240;
      el.animate([{ transform: `translate(${dx}px, ${dy}px) rotate(-30deg)`, offset: 0 }, { transform: "translate(20px, -60px) rotate(160deg)", offset: 0.6 },
        { transform: "translate(0, 0) rotate(360deg)", offset: 1 }], { duration: FLY_MS - 120, easing: "steps(5)" });
    }
    return () => t.forEach(clearTimeout);
  }, []);
  return html`<div class="play-intro play-throw" data-phase=${ph}>
    <div class="play-slot" ref=${slot}>
      <div ref=${die} class=${cls("play-die", { "is-rolling": ph === "roll", "is-landing": ph === "ok" || ph === "no", "is-fading": ph === "ok-leave", "is-tipping": ph === "no-leave" })}>
        <span class=${cls("ork-die big", { "is-rolling": !landed, "face-ok": ok, "face-no": no, "is-landed": landed })} style=${n === 6 ? undefined : `--_n:${n}`} aria-hidden="true"></span>
      </div>
    </div>
    ${(ph === "fly" || ph === "roll") && html`<${StageLine} b=${b} />`}
    ${(ph === "ok" || ph === "no") && html`<p class="play-starting play-landed" role="status">${ok ? STARTED : NOT_STARTED}</p>`}
  </div>`;
}

/** What lies over the pane in the throw: the die (`fly` to `no-leave`), then today's intro (`logo`), then its fade over the frame (`out`). */
function Story({ ph, name, b, done }) {
  if (ph === "logo" || ph === "out") return html`<${Intro} name=${name} b=${b} fading=${ph === "out"} done=${done} line=${false} />`;
  return html`<${Throw} ph=${ph} b=${b} />`;
}

/** The command's last lines, in a quiet box that scrolls (about twelve lines show), the newest at the foot. */
function Tail({ lines }) {
  const box = useRef(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [lines.length]);
  if (!lines.length) return null;
  return html`<div class="play-tail"><p class="arena-cap play-tail__cap">${LAST_LINES}</p><pre class="play-tail__lines" ref=${box} tabindex="0" aria-label=${LAST_LINES}>${lines.join("\n")}</pre></div>`;
}

export function Play() {
  const { b, open, stop } = useBuild(), name = projectName(), stage = useRef(null), before = useRef("reading");
  const full = () => { try { stage.current?.requestFullscreen?.()?.catch?.(() => {}); } catch { /* the browser would not */ } };
  const [ph, setPh] = useState(""), motion = !reduced(), starting = b.state === "starting";
  const end = b.state === "playing" ? "ok" : b.state === "failed" ? "no" : "";                 // what the start came to, once the roll may stop on it
  const story = ph || (starting && motion ? "fly" : "");                                      // a start is thrown from its first frame (the effect below makes it so)
  useEffect(() => {                                    // a start begins the throw; a start that is gone (stopped) before it came to anything ends it
    if (!motion) return;
    if (starting && !ph) setPh("fly");
    else if ((ph === "fly" || ph === "roll") && !starting && !end) setPh("");
  }, [b.state]);
  useEffect(() => {                                    // the throw's phases: each leaves by its own time, the roll by the answer
    if (!ph) return undefined;
    const go = (next, ms) => { const t = setTimeout(() => setPh(next), ms); return () => clearTimeout(t); };
    if (ph === "fly") return go("roll", FLY_MS);
    if (ph === "roll") { if (end) setPh(end); return undefined; }
    if (ph === "ok") return go("ok-leave", HOLD_OK_MS);
    if (ph === "no") return go("no-leave", HOLD_NO_MS);
    if (ph === "ok-leave") return go("logo", LEAVE_OK_MS);
    if (ph === "no-leave") return go("", LEAVE_NO_MS);
    if (ph === "logo") return go("out", b.logo ? INTRO_LOGO_MS : INTRO_NAME_MS);
    return go("", FADE_MS + 250);                      // `out`: the fade leaves by its own animation; a timer is the net
  }, [ph, end]);
  useLayoutEffect(() => {                              // the hand's die: hidden while its copy is out, glowing while the frame plays
    thrown.value = !!story && story !== "out";
    playing.value = b.state === "playing" && (!story || story === "out");
  }, [story, b.state]);
  useEffect(() => () => { thrown.value = false; playing.value = false; }, []);
  useEffect(() => {                                    // opened on a build already playing: no throw, the die in the hand wobbles twice
    if (before.current === "reading" && b.state === "playing" && !story) warmed.value += 1;
    before.current = b.state;
  }, [b.state]);
  if (b.state === "reading") return html`<div class="playpane" data-state="reading"><p class="arena-cap play-note"><span class="ork-busy"></span></p></div>`;
  if (story && b.state !== "playing") {                // rolling, or landed on the cross: the black pane and the die
    return html`<div class="playpane is-black" data-state=${b.state} data-throw=${story}><${Story} key="story" ph=${story} name=${name} b=${b} done=${() => setPh("")} /></div>`;
  }
  if (!story && starting) {                            // reduced motion: today's start screen
    return html`<div class="playpane is-black" data-state="starting"><${Intro} name=${name} b=${b} /></div>`;
  }
  if (b.state === "playing") {
    const moved = b.dev && b.commit && b.dev !== b.commit;
    return html`<div class=${cls("playpane", { "is-black": story && story !== "out" })} data-state="playing" data-throw=${story || undefined}>
      <div class="play-bar" key="bar">
        <span class="play-at"><${Sign} name="play" /> <span>${playsAt(b.short || String(b.commit || "").slice(0, 7))}</span></span>
        ${moved && html`<span class="arena-cap play-moved">dev is at ${String(b.dev).slice(0, 7)} now</span>`}
        <span class="arena-spacer"></span>
        ${moved && html`<button type="button" class="ork-btn" onClick=${() => open(true)}>${OPEN}</button>`}
        <button type="button" class="ork-btn play-full" title="Fill the screen with it: Esc leaves" onClick=${full}>${FULL}</button>
        <button type="button" class="ork-btn" onClick=${stop}>${STOP}</button>
      </div>
      <div key="stage" class=${cls("play-stage", { "is-rising": story === "out" })} ref=${stage}>
        <iframe class="play-frame" src=${b.url} title="Play" sandbox=${SANDBOX} allow="autoplay; fullscreen; gamepad"></iframe>
      </div>
      ${story && html`<${Story} key="story" ph=${story} name=${name} b=${b} done=${() => setPh("")} />`}
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
