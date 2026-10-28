// A lifted card's answers (docs/specs/98-the-table-and-the-hand.md §4.4): today's stop answered from the card, the same commands as arena/stops.js sends, in the same
// words (a plan: *Start the work*, a question: its choices and *Let <name> decide*, a failure: *Start again*, a proposal, a to-do, a collision, a pick, a result, a sign-in).
// They are the only ones (the old window's fan went with spec 98 E), written over the parts shared with the pane (TodoWays, CollideAnswers, ResultActions, SignInButton, Tiles). A press that needs more room than a card has
// (*Open…*: the plan's tasks, a pick's variants large) opens the stop over the pane (`openOver("stop")`, face: stopface.js). Starting a plan deals no cards onto the
// field yet (that is the table's, spec 98 C).
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { say, toast } from "../link.js";
import { act } from "../shell/store.js";
import { ResultActions } from "../shell/review.js";
import { TodoWays, named } from "./todoform.js";
import { SignInButton } from "../shell/signin.js";
import { CollideAnswers } from "../arena/collide.js";
import { PICTURES, askedOf, changeToast } from "../arena/arenawords.js";
import { choiceOf } from "../arena/picks.js";
import { manyWords, variantOf } from "../arena/pickwords.js";
import { openOver } from "../frame/state.js";
import { openParties } from "../table/parties.js";

const SENT = "Sent: the Taskmaster answers in a moment.";

/** The stop opened over the pane, whole: its text, its tasks, its choices large (stopface.js). */
/** The stop opened over the pane, whole (`extra`: what the form there starts with, the answers pressed in the card). */
export const openStop = (s, extra = {}) => openOver("stop", { key: s.key, ...extra }, null, s.title || s.full || "");

/** An answer and its refusal: the first button answers at once, the second opens one line (*Why not?*) that the third sends. */
function Decline({ s, yes, ask, sure, take, go }) {
  const [reason, setReason] = useState(""), [declining, setDeclining] = useState(false);
  return declining ? html`<div class="hand-why">
      <input class="ork-field" value=${reason} aria-label=${`Why not: ${s.full}`} placeholder="Why not? (optional, one line)" autofocus
        onInput=${(e) => setReason(e.target.value)} onKeyDown=${(e) => { if (e.key === "Enter") go(reason.trim()); }} />
      <button type="button" class="ork-btn" aria-label=${`${sure}: ${s.full}`} onClick=${() => go(reason.trim())}>${ask[0]}</button>
      <button type="button" class="ork-btn quiet" onClick=${() => setDeclining(false)}>Cancel</button></div>`
    : html`<button type="button" class="ork-btn primary" aria-label=${`${yes[1]}: ${s.full}`} onClick=${take}>${yes[0]}</button>
      <button type="button" class="ork-btn" aria-label=${`${ask[1]}: ${s.full}`} onClick=${() => setDeclining(true)}>${ask[0]}</button>`;
}

/** A question's way out: *Let <name> decide*, last and quiet; the one who asks answers with what it recommends. */
function Decide({ s, target, isGoal, name }) {
  const [busy, setBusy] = useState(false);
  const decide = async () => {
    setBusy(true);
    const got = await act("ideas.answer", { slug: target, decide: true, ...(isGoal ? { goal: true } : {}) });
    setBusy(false);
    if (got) toast(say(`Sent: ${named(name)} decides.`));
  };
  return html`<button type="button" class="ork-btn quiet" disabled=${busy} aria-label=${`Let ${named(name)} decide: ${s.full}`} title="It answers with what it recommends"
    onClick=${decide}>Let ${named(name)} decide</button>`;
}

/** A pick's answers: *Take B* once one is picked (it answers at once), and the way to the large tiles and the note. */
function PickAnswers({ s }) {
  const row = s.row, key = choiceOf(row).key, [busy, setBusy] = useState(false);
  const take = async () => { setBusy(true); await act("ideas.pick", { slug: row.slug, task: row.task, key, via: "hand" }); setBusy(false); };
  return html`${key && html`<button type="button" class="ork-btn primary" disabled=${busy} title=${`Goes on with ${key} · ${variantOf(row, key)?.name || ""}`}
      aria-label=${`Take ${key}: ${s.full}`} onClick=${take}>Take ${key}</button>`}
    <button type="button" class="ork-btn" title=${`The ${manyWords(row)} large, a note, None of them`} aria-label=${`${key ? "Add a note" : "Pick, with a note"}: ${s.full}`}
      onClick=${() => openStop(s)}>${key ? "Add a note…" : "Pick, with a note…"}</button>`;
}

function PlanAnswers({ s, slug, row, g, here }) {
  const miss = row?.missing || [], start = (args) => act("ideas.start", { slug, ...args, via: "hand" });
  if (miss.length) {
    const m = miss[0];
    const join = async () => { const got = await start({ join: { add: m.agent } }); if (got) toast(`${m.name} joined the party; the work started.`); };
    return m.free ? html`<button type="button" class="ork-btn primary" title=${`${m.name} joins the party, then the work starts`} onClick=${join}>Add and start</button>
        <button type="button" class="ork-btn" title="Passes the plan as it is; the Grunt does that work" onClick=${() => start({})}>Start without</button>`
      : html`<button type="button" class="ork-btn primary" title="Passes the plan as it is; the Grunt does that work" onClick=${() => start({})}>Start without</button>
        <button type="button" class="ork-btn" title="Change a member of the party" onClick=${() => openParties({ party: row.goal || g?.slug })}>Edit the party</button>`;
  }
  return html`<button type="button" class="ork-btn primary" title="Passes the plan; the work starts" onClick=${() => start({})}>Start the work</button>
    ${!here && html`<button type="button" class="ork-btn" title="The plan's tasks, over the pane" onClick=${() => openStop(s)}>Open the plan</button>`}`;
}

function ChangeAnswers({ slug }) {
  const take = async () => { const got = await act("ideas.revise_answer", { slug, take: true, via: "hand" }); if (got) toast(changeToast(got)); };
  const keep = async () => { if (await act("ideas.revise_answer", { slug, take: false, via: "hand" })) toast(changeToast({})); };
  return html`<button type="button" class="ork-btn primary" title="The tasks not started take the change; the ones that started stay as they are" onClick=${take}>Take the new plan</button>
    <button type="button" class="ork-btn" title="The plan stays as it is" onClick=${keep}>Keep the plan</button>`;
}

function AskAnswers({ s, row, n, slug, here }) {
  const isGoal = s.kind === "goal", target = isGoal ? row.goal : slug, asked = askedOf(row, n);
  const send = async (answers) => { const got = await act("ideas.answer", { slug: target, answers, ...(isGoal ? { goal: true } : {}) }); if (got) toast(say(SENT)); };
  const more = (picks) => openStop(s, { picks });                                          // the questions as a form, over the pane
  const picks = asked.map((q) => (q.pick != null ? q.choices[q.pick] || "" : ""));
  const decide = html`<${Decide} s=${s} target=${target} isGoal=${isGoal} name=${isGoal ? s.party.lead : asked.find((q) => q.by?.name)?.by?.name || s.party.lead} />`;
  if (here) return decide;                                                                   // the form is under it: it answers
  if (asked.length === 1 && asked[0].choices.length) {
    return html`${asked[0].choices.map((c, i) => html`<button type="button" key=${c} class=${cls("ork-btn", { primary: i === asked[0].pick })}
        title=${c === PICTURES ? "Opens the form: add the pictures there" : i === asked[0].pick ? "Picked for you: one click answers" : "One click answers with this"}
        onClick=${() => (c === PICTURES ? more([c]) : send([c]))}>${i === asked[0].pick ? "● " : ""}${c}</button>`)}
      <button type="button" class="ork-btn quiet" onClick=${() => more(picks)}>Open…</button>${decide}`;
  }
  return html`${asked.length > 1 && html`<button type="button" class="ork-btn primary" disabled=${!picks.some(Boolean)} onClick=${() => send(picks)}>Send the picks</button>`}
    <button type="button" class="ork-btn" onClick=${() => more(picks)}>Open…</button>${decide}`;
}

/** The answers of a stop `s` (arenawords.js): buttons that say what happens. Nothing for a kind the hand does not know (a route card is spec 100's). */
export function Answers({ s, here = false }) {
  const row = s.row, n = s.node, slug = row?.idea || n?.slug || "";
  switch (s.kind) {
    case "result": return html`<${ResultActions} r=${s.result} />`;
    case "pick": return html`<${PickAnswers} s=${s} />`;
    case "plan": return html`<${PlanAnswers} s=${s} slug=${slug} row=${row} g=${s.g} here=${here} />`;
    case "change": return html`<${ChangeAnswers} slug=${slug} />`;
    case "asks": case "goal": return html`<${AskAnswers} s=${s} row=${row} n=${n} slug=${slug} here=${here} />`;
    case "proposal": {
      const take = () => act("ideas.proposal", { slug, take: true, priority: s.g?.priority || "normal" });
      return html`<${Decline} s=${s} yes=${["Take", "Take"]} ask=${["No", "No"]} sure="Decline" take=${take} go=${(reason) => act("ideas.proposal", { slug, take: false, ...(reason ? { reason } : {}) })} />`;
    }
    case "party": {
      const goal = row.goal;
      return html`<${Decline} s=${s} yes=${["Take it out", "Take it out"]} ask=${["Keep it", "Keep it"]} sure="Keep" take=${() => act("ideas.party_answer", { goal, take: true })}
        go=${(reason) => act("ideas.party_answer", { goal, take: false, ...(reason ? { reason } : {}) })} />`;
    }
    case "todo": return here ? null : html`<button type="button" class="ork-btn" onClick=${() => openStop(s)}>Open…</button>
      <${TodoWays} idea=${row.idea} todo=${row.todo} lead=${s.party.lead} agent=${row.todo?.by?.name} />`;
    case "failed": return html`<button type="button" class="ork-btn primary" title="Its goal’s tasks that are not merged or at Review run again"
        onClick=${() => act("ideas.start", { slug: n?.slug || row.idea, via: "hand" })}>Start again</button>
      ${!here && html`<button type="button" class="ork-btn" title="Its brief, state and log, over the pane" onClick=${() => openStop(s)}>Open…</button>`}`;
    case "pitch": return here ? null : html`<button type="button" class="ork-btn primary" title="Its views, the case against and the decision" onClick=${() => openStop(s)}>Open the pitch</button>`;
    case "collide": return html`<${CollideAnswers} s=${s} />`;
    case "sign_in": return html`<${SignInButton} harness=${row.harness} tool=${row.tool} />`;
    default: return null;
  }
}
