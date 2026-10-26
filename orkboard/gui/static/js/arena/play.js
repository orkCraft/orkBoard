// Play (docs/specs/88-assets-and-play.md §5, §6.5, "As built (A)"): the project's own preview of dev's head, opened in the pane. *Open the build* asks the host (`ideas.play`), which answers at once; while it
// starts (*Starting the build…*) the face asks what it is now (`ideas.play` with `peek`) about every second; once it plays, the preview is an `iframe` of its own origin — a sandbox that lets its scripts run, keeps its
// origin and lets it lock the pointer —, *Plays dev at <short commit>* over it and *Stop the build*. While it is shown the face says `peek` every minute: the host stops a Play nobody has asked about for ten minutes.
// A merge into dev changes nothing in it until *Open the build* is pressed again (`fresh`). A build that would not start says why; a project with no preview says *Nothing here yet* and how to give it one.
// The build is the machine's own address (127.0.0.1): the phone has no Play.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { command } from "../link.js";

export const OPEN = "Open the build", STARTING = "Starting the build…", STOP = "Stop the build";
export const NOTHING = "Nothing here yet";
export const NOTHING_HOW = "Say how the project opens in .orkcraft/checks.toml: preview = \"npm run dev\", or keep an index.html at its root";
export const SANDBOX = "allow-scripts allow-same-origin allow-pointer-lock";
export const playsAt = (short) => `Plays dev at ${short}`;
export const wouldNot = (why) => `The build would not start: ${why}`;

const POLL_MS = 1000, KEEP_MS = 60_000;                // while it starts; while it plays (the host's idle limit is ten minutes)

/** The build as the face shows it: `stopped`, `starting`, `playing` ({url, commit, short, dev}) or `failed` ({error, none}); what `ideas.play` answers, or `reading` before the first answer. */
function useBuild() {
  const [b, setB] = useState({ state: "reading" }), live = useRef(true);
  const take = (r) => { if (live.current) setB(r && r.state ? r : { state: "failed", error: r?.error || "did not open" }); };
  const ask = (args) => command("ideas.play", args, true).then(take).catch((e) => { if (live.current) setB({ state: "failed", error: e.message || "did not open" }); });
  useEffect(() => { live.current = true; ask({ peek: true }); return () => { live.current = false; }; }, []);
  useEffect(() => {
    if (b.state !== "starting" && b.state !== "playing") return undefined;
    const t = setInterval(() => ask({ peek: true }), b.state === "starting" ? POLL_MS : KEEP_MS);
    return () => clearInterval(t);
  }, [b.state]);
  return {
    b,
    open: (fresh) => { setB({ state: "starting", commit: "", short: "" }); ask(fresh ? { fresh: true } : {}); },
    stop: () => command("ideas.play_stop", {}, true).then(() => live.current && setB({ state: "stopped" })).catch((e) => live.current && setB({ state: "failed", error: e.message || "did not stop" })),
  };
}

export function Play() {
  const { b, open, stop } = useBuild();
  if (b.state === "reading") return html`<div class="playpane" data-state="reading"><p class="arena-cap play-note"><span class="ork-busy"></span></p></div>`;
  if (b.state === "starting") {
    return html`<div class="playpane" data-state="starting"><p class="play-note" role="status"><span class="ork-busy"></span> ${STARTING}</p></div>`;
  }
  if (b.state === "playing") {
    const moved = b.dev && b.commit && b.dev !== b.commit;
    return html`<div class="playpane" data-state="playing">
      <div class="play-bar">
        <span class="play-at"><${Sign} name="play" /> <span>${playsAt(b.short || String(b.commit || "").slice(0, 7))}</span></span>
        ${moved && html`<span class="arena-cap play-moved">dev is at ${String(b.dev).slice(0, 7)} now</span>`}
        <span class="arena-spacer"></span>
        ${moved && html`<button type="button" class="ork-btn" onClick=${() => open(true)}>${OPEN}</button>`}
        <button type="button" class="ork-btn" onClick=${stop}>${STOP}</button>
      </div>
      <iframe class="play-frame" src=${b.url} title="Play" sandbox=${SANDBOX} allow="autoplay; fullscreen; gamepad"></iframe>
    </div>`;
  }
  if (b.state === "failed" && b.none) {
    return html`<div class="playpane" data-state="none"><div class="assets-none"><p class="assets-none__title">${NOTHING}</p><p class="arena-cap">${NOTHING_HOW}</p></div></div>`;
  }
  return html`<div class=${cls("playpane", { "is-failed": b.state === "failed" })} data-state=${b.state === "failed" ? "failed" : "idle"}>
    <div class="play-start">
      ${b.state === "failed" && html`<p class="play-error" role="alert">${wouldNot(b.error)}</p>`}
      <button type="button" class="ork-btn primary" onClick=${() => open(false)}>${OPEN}</button>
    </div>
  </div>`;
}
