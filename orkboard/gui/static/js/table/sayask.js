// A leader's card of the say, lifted and answered (docs/specs/168 C4, decisions §283.16.4, §283.19, §283.23): the same lifted card as a question's (hand/choose.js, `chooseFor("say", …)`, opened with frame/state.js `openOver("choose", {source: "say", idea, id})`):
// a need's ways are its choices (`ideas.take_way {idea, id, way}`), a better's are *Take it* (`ideas.take_better {idea, id}`) and *Leave it*, a need's *Leave it* is the quiet button (`ideas.leave_say {idea, id}`), and the open fork's choices
// answer it (`ideas.say_fork {idea, pick}`). A question of the old kind (`legacy`) is answered as it always was, together over the pane (`ideas.talk_answer`, table/talkpage.js). Where the card rises and the hand's shape are stage D1's: this
// is the card as the page lifts one today. The command's refusal is the keeper's plain words (a toast); the card goes back once it is answered.
import { useLayoutEffect } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { mapData } from "../shell/store.js";
import { openOver } from "../frame/state.js";
import { Choose, chooseFor } from "../hand/choose.js";
import { partiesAll, nameOf } from "./data.js";

/** Lift the item `id` of the idea `n` (a need, a better or the open fork) where the person is. `from`: where the pane came from, for *Put it back*. */
export function liftSay(n, id, from = null) {
  const fork = n.say?.fork?.id === id, item = (n.say?.leaders || []).flatMap((l) => [...l.needs, ...l.better]).find((x) => x.id === id);
  if (item?.legacy) { openOver("talk", { idea: n.slug, together: true }, from, n.title); return; }                // a question of the old kind: the questions together
  if (fork || item) openOver("choose", { source: "say", idea: n.slug, id }, from, n.title);
}

const ask = (name, args, close) => command(name, args).then(() => close()).catch(() => {});      // refused: its toast says why, the card stays

function Say({ props, close }) {
  const n = (mapData.value?.nodes || []).find((x) => x.slug === props.idea), say = n?.say;
  const fork = say?.fork && say.fork.id === props.id ? say.fork : null;
  const lead = (say?.leaders || []).find((l) => [...l.needs, ...l.better].some((x) => x.id === props.id)), item = lead ? [...lead.needs, ...lead.better].find((x) => x.id === props.id) : null;
  const gone = !fork && (!item || item.state !== "open");
  useLayoutEffect(() => { if (gone) close(); }, [gone]);                                                        // answered (here or elsewhere): the card goes back
  if (gone) return null;
  const g = partiesAll().find((x) => x.slug === lead?.party) || null, by = nameOf(g) || lead?.party || "", head = g?.leader?.head || null, idea = props.idea;
  if (fork) {
    return html`<${Choose} question=${fork.card.q} choices=${fork.card.choices.map((name, i) => ({ id: String(i), name, why: fork.card.lines?.[i] || (i === fork.card.pick ? fork.card.why || "" : "") }))} pick=${String(fork.card.pick ?? "")}
      element=${n.element || ""} hue=${n.hue || ""} onChoose=${(i) => ask("ideas.say_fork", { idea, pick: Number(i) }, close)} onBack=${close} />`;
  }
  if (item.ways) {                                                                                               // a need: its ways
    return html`<${Choose} question=${item.title || item.line} hint=${item.rests_on ? `Rests on ${item.rests_on}` : ""} by=${by} head=${head} element=${n.element || ""} hue=${n.hue || ""}
      choices=${item.ways.map((w, i) => ({ id: String(i), name: w.name, why: w.line || "" }))} onChoose=${(i) => ask("ideas.take_way", { idea, id: item.id, way: Number(i) }, close)}
      decide=${{ label: "Leave it", onDecide: () => ask("ideas.leave_say", { idea, id: item.id }, close) }} onBack=${close} />`;
  }
  return html`<${Choose} question=${item.line} by=${by} head=${head} element=${n.element || ""} hue=${n.hue || ""}
    choices=${[{ id: "take", name: "Take it", why: `${item.weight || "same"}`, sign: "check" }, { id: "leave", name: "Leave it", why: "", sign: "cross" }]}
    onChoose=${(i) => ask(i === "take" ? "ideas.take_better" : "ideas.leave_say", { idea, id: item.id }, close)} onBack=${close} />`;
}
chooseFor("say", Say);
