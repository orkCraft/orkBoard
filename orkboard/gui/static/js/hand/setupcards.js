// The Orkmaster's setup cards (docs/specs/130-the-first-open-is-the-orkmasters.md B.4, decisions §232.3, §232.8, §206.6; mockup docs/mockups/setup/ #ask, #read): the first open as a talk: the Orkmaster's bubble says `first_open.ask`'s `line` (`ork-think` while it reads) and the answers are cards in the hand, as every question for the person is: the project (**Open a folder…**, the
// system's dialog; **A new, empty folder…**; the recent projects), a folder with no git (**Start git here**, **Choose another folder**), what the project is (the signs read as chips, **Yes**, **It is something else…**; an empty folder *What is it for?* in one line). The AI tools' step lifts the adding card (addtool.js) and lights the empty slot. They have no rune and are not picked, only lifted (§248). The page asks
// when the project, its git, `laid`, the hand or the kind change, never on a timer; a snapshot with no `tools` (a paired phone's) asks nothing.
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { command, town } from "../link.js";
import { Head, Icon, Sign } from "../orkui.js";
import { ask } from "../board/store.js";
import { layLine } from "../table/laying.js";
import { chooseFolder, closeProject, currentProject, openFolder, startForm, startGit } from "../shell/projects.js";

export const setupNow = signal(null);                 // what `first_open.ask` said last: {step, line, name, recent, kind, hand, laid}; null while it was not asked, or on a host with no first open
export const reading = signal("");                    // the project being read: the bubble says so, `ork-think`
export const CARD_STEPS = ["project", "git", "kind"];  // the questions that are cards here; `tools` is the adding card, `parties` the Orkmaster's large card on the table
const THE_KINDS = [["mobile", "a mobile app"], ["game", "a game"], ["web", "a web app"], ["backend", "a backend"], ["data", "data work"], ["wiki", "a team's wiki"], ["design", "a designer's folder"], ["texts", "texts"], ["code", "code"]];

let asked = 0;
/** Asks the host what the Orkmaster asks now. */
export async function setupAsk() {
  if (!town.peek()?.tools) { setupNow.value = null; return null; }
  const mine = ++asked;
  let got = null;
  try { got = await command("first_open.ask", {}, true); } catch { got = null; }
  if (mine === asked) setupNow.value = got && !got.error ? got : null;
  return got;
}

/** What makes the question change: the project shown, its git, the table laid, the hand. The kind answered asks by itself (`first_open.kind`), and so does a card that answered. */
function useSetupKey() {
  const t = town.value, key = t?.tools ? JSON.stringify([currentProject.value?.path || "", t.repo?.git ?? t.repo ?? "", !!t.laid, (t.tools.hand || []).map((h) => h.id)]) : "";
  useEffect(() => { if (key) setupAsk(); else setupNow.value = null; }, [key]);
}

/** Mounted once on the page (frame/frame.js): keeps `setupNow` up to date. */
export function SetupWatch() {
  useSetupKey();
  return null;
}

/** The Orkmaster's line in its bubble (spec 123 §201's): its question, or *Reading <name>* while it reads. */
export function SetupBubble() {
  const s = setupNow.value, laid = layLine.value, line = reading.value ? `Reading ${reading.value}` : laid || (s?.step === "laid" ? "" : s?.line || "");
  if (!line) return null;
  return html`<div class="fo-bubble" role="status" aria-live="polite" data-step=${laid ? "laid" : s?.step || ""}><span class="ork-label">Orkmaster</span><p class=${reading.value ? "ork-think" : undefined}>${line}</p></div>`;
}

const Choice = ({ icon, sign, word, why, pick, onPress, busy, ...more }) => html`<button type="button" class=${`fo-choice${pick ? " is-pick" : ""}`} disabled=${busy} onClick=${onPress} ...${more}>
  <span class="fo-choice__t">${icon && html`<${Icon} name=${icon} />`}${sign && html`<${Sign} name=${sign} />`}${word}</span>${why && html`<span class="fo-choice__why">${why}</span>`}</button>`;

/** The system's dialog opened from the card: the folder it chose, "" when it was closed; `why`: no dialog here, or a refusal, said on the card. */
function usePick(setWhy) {
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  return async () => {
    setWhy("");
    const got = await chooseFolder("", alive);
    if (got.state === "error" && got.why) setWhy(got.why);
    return got.state === "done" ? got.path || "" : "";
  };
}

/** *Which project shall we work on?* */
function ProjectCard({ s }) {
  const [why, setWhy] = useState(""), [busy, setBusy] = useState(false), [parent, setParent] = useState(""), [name, setName] = useState(""), [typed, setTyped] = useState(""), [typing, setTyping] = useState(false), pickFolder = usePick(setWhy);
  const open = async (path) => {
    if (!path) return;
    setBusy(true);
    const got = await openFolder(path);
    setBusy(false);
    if (!got?.ok) { if (got?.error) setWhy(got.error); return; }
    setupAsk();
  };
  const choose = async () => { const path = await pickFolder(); if (path) open(path); else setTyping(true); };
  useEffect(() => { if (startForm.value) { startForm.value = false; choose(); } }, [startForm.value]);      // Ctrl+O opens the same dialog (spec 130 D.3)
  const fresh = async () => { const path = await pickFolder(); if (path) setParent(path); };
  const make = async (e) => {
    e?.preventDefault();
    setBusy(true);
    const got = await command("projects.new_folder", { parent, name }, true).catch((err) => ({ error: err.message }));
    setBusy(false);
    if (got?.error) { setWhy(got.error); return; }
    setParent("");
    setupAsk();
  };
  if (parent) {
    return html`<form class="fo-field" data-new-folder="1" onSubmit=${make}><span class="ork-label">A new, empty folder in ${parent}</span>
      <input class="ork-field" autofocus value=${name} aria-label="The new folder's name" placeholder="The folder's name" onInput=${(e) => { setName(e.target.value); setWhy(""); }} />
      ${why && html`<p class="cap is-danger" role="alert">${why}</p>`}
      <span class="fo-row"><button type="submit" class="ork-btn primary" disabled=${!name.trim() || busy}>Make it</button><button type="button" class="ork-btn quiet" onClick=${() => { setParent(""); setWhy(""); }}>Back</button></span></form>`;
  }
  return html`<div class="fo-choices">
    <${Choice} icon="folder" word="Open a folder…" why="A project you have: code, a game, a wiki, design files." pick=${true} busy=${busy} data-open-folder="1" onPress=${choose} />
    <${Choice} icon="plus" word="A new, empty folder…" busy=${busy} data-new="1" onPress=${fresh} />
    ${(s.recent || []).map((r) => html`<${Choice} key=${r.path} word=${r.name} why=${r.path} busy=${busy} data-recent=${r.path} onPress=${() => open(r.path)} />`)}
    ${typing && html`<form class="fo-field" onSubmit=${(e) => { e.preventDefault(); open(typed.trim()); }}><input class="ork-field" autofocus value=${typed} aria-label="The folder's path" placeholder="The path of a project's folder, such as ~/code/shop" onInput=${(e) => { setTyped(e.target.value); setWhy(""); }} />
      <button type="submit" class="ork-btn" disabled=${!typed.trim() || busy}>Open</button></form>`}
    ${why && html`<p class="cap is-danger" role="alert">${why}</p>`}
  </div>`;
}

/** *No git in <name> yet. Start git here?* */
function GitCard({ path }) {
  const [busy, setBusy] = useState(false);
  const start = async () => { setBusy(true); try { if (await startGit(path)) await setupAsk(); } finally { setBusy(false); } };
  const another = async () => { setBusy(true); try { await closeProject(path); await setupAsk(); } finally { setBusy(false); } };
  return html`<div class="fo-choices"><p class="cap fo-muted">Start git here makes a first commit of the folder's files as they are, and changes nothing else.</p>
    <${Choice} word="Start git here" pick=${true} busy=${busy} data-start-git="1" onPress=${start} />
    <${Choice} word="Choose another folder" busy=${busy} data-another="1" onPress=${another} /></div>`;
}

/** *<name> is a game, made in Godot. Right?*, or an empty folder's *What is it for?* */
function KindCard({ s }) {
  const k = s.kind || {}, [other, setOther] = useState(false), [line, setLine] = useState(""), [busy, setBusy] = useState(false), [why, setWhy] = useState("");
  const send = async (args) => {
    setBusy(true);
    setWhy("");
    if (args.about) reading.value = s.name;
    try {
      const got = await ask("first_open.kind", args);
      if (got) await setupAsk();
    } catch (e) { setWhy(e.message || ""); } finally { reading.value = ""; setBusy(false); }
  };
  if (other || k.empty) {
    return html`<div class="fo-choices">
      ${k.empty && !other ? html`<form class="fo-field" onSubmit=${(e) => { e.preventDefault(); send({ about: line }); }}>
          <input class="ork-field" autofocus value=${line} aria-label="What is it for?" placeholder="A line is enough: a mobile app for…, our team's wiki, my design files" onInput=${(e) => setLine(e.target.value)} />
          <span class="fo-row"><button type="submit" class="ork-btn primary" data-read="1" disabled=${!line.trim() || busy}>Read it</button><button type="button" class="ork-btn quiet" data-kinds="1" onClick=${() => setOther(true)}>Pick a kind instead</button></span></form>`
        : THE_KINDS.map(([id, words]) => html`<${Choice} key=${id} word=${words} busy=${busy} data-kind=${id} onPress=${() => send({ kind: id })} />`)}
      ${why && html`<p class="cap is-danger" role="alert">${why}</p>`}</div>`;
  }
  return html`<div class="fo-choices">${(k.signs || []).length > 0 && html`<span class="fo-chips">${k.signs.map((c) => html`<span class="ork-chip" key=${c}>${c}</span>`)}</span>`}
    <${Choice} sign="check" word=${`Yes, ${k.words}`} pick=${true} busy=${busy} data-yes="1" onPress=${() => send({ kind: k.id })} />
    <${Choice} word="It is something else…" busy=${busy} data-else="1" onPress=${() => setOther(true)} /></div>`;
}

/** The question as a card lifted in the hand, the Orkmaster's head at its corner; it goes when it is answered. `at`: the place it landed in the first open's room (frame/firstopen.js: `ring`, `table`), `foot`: what the room adds under it (the release branch). */
export function SetupCard({ at = "", foot = null } = {}) {
  const s = setupNow.value;
  if (!s || !CARD_STEPS.includes(s.step)) return null;
  const question = s.step === "kind" && s.kind?.empty ? `The folder is empty. What is it for?` : s.line;
  return html`<article class=${`ork-card hand-card--big hand-tool fo-card${at ? ` fo-at-${at}` : ""}`} role="dialog" aria-label="The Orkmaster's question" data-setup=${s.step}>
    <div class="hand-tool__top"><span class="ork-label">The project</span><span class="is-alert"><${Sign} name="question" /></span></div>
    <div class="fo-q"><p class="body">${question}</p><${Head} race="peon" tier="crown" size="mid" /></div>
    ${s.step === "project" ? html`<${ProjectCard} s=${s} />` : s.step === "git" ? html`<${GitCard} key=${s.name} path=${s.path} />` : html`<${KindCard} key=${s.name} s=${s} />`}
    ${foot}
  </article>`;
}
