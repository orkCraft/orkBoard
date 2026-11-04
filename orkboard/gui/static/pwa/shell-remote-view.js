// The screen the journal draws while the computer cannot be reached (docs/specs/136 C.4, decisions §243.3, §243.5): the project as far as `status.json` tells it. It is the frame's own, over the
// page (pwa/frame.js shows it only while the link to the computer has failed and a journal was read), and plain DOM like the other cards the frame draws. Its header says *As of 14:02*, the
// journal's `written`, in the muted ink; the parties come with their goals and each goal's state, the goals that need the person are marked and their button is not pressable
// (*Needs your computer*), what failed is said with its error, and the goals this phone sent that the computer has not taken lie face down with the person's own words
// (*Waiting to be taken*, or *Waits for the network*, or the error's words). A small card at its top writes a goal into the inbox (shell-remote-send.js).
import { NEEDS_COMPUTER, SENT, WAITING, WAITS } from "./shell-remote-words.js";

const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid);
  return el;
};

/** The node's children, replaced: arrays flattened, nothing that is not a node or a text left in. */
const fill = (el, ...kids) => el.replaceChildren(...kids.flat().filter((k) => k !== null && k !== undefined && k !== false));

const PHASES = { talk: "Talk", spec: "Spec", work: "Work", done: "Done" };

/** One goal of a party, as the journal has it: its title, its state, a mark when the person is needed. */
function goalRow(g) {
  const phase = PHASES[g.phase] || "";
  return h("li", { class: "remote-goal", "data-slug": g.slug, "data-state": g.state, "data-needs": g.needs_you ? "1" : null },
    h("span", { class: "remote-goal__title" }, String(g.title || g.slug)),
    h("span", { class: "remote-goal__state" }, [String(g.state || ""), phase && `· ${phase}`].filter(Boolean).join(" ")),
    g.needs_you && h("span", { class: "remote-goal__needs" }, h("span", { class: "remote-mark" }, "Needs you"),
      h("button", { class: "ork-btn", type: "button", disabled: true, title: NEEDS_COMPUTER, "aria-label": `${NEEDS_COMPUTER}: ${g.title || g.slug}` }, NEEDS_COMPUTER)),
    g.error && h("span", { class: "remote-goal__error" }, String(g.error)));
}

/** A goal of this phone's that the computer has not laid on the Board: face down, the person's own words. */
function downCard(w) {
  const note = w.state === "error" ? w.error : w.state === "network" ? WAITS : w.state === "taken" ? "Taken: your computer is laying it on the Board" : WAITING;
  return h("article", { class: "remote-down", "data-state": w.state, "data-id": w.id },
    h("p", { class: "remote-down__words" }, w.text || "A goal"), h("p", { class: `remote-down__note${w.state === "error" ? " is-bad" : ""}` }, note));
}

/** The goal box: words, a party when the journal names some, Send. It is made once and kept across redraws, so what is being written and what was said stay. */
function goalBox(remote) {
  const area = h("textarea", { class: "ork-field", name: "goal", rows: "3", placeholder: "Write a goal…", "aria-label": "Write a goal" });
  const to = h("select", { class: "ork-field", name: "party", "aria-label": "To" }, h("option", { value: "" }, "The Orkmaster finds its party"));
  const line = h("p", { class: "remote-line", role: "status" });
  const send = h("button", { class: "ork-btn primary", type: "button" }, "Send");
  send.addEventListener("click", async () => {
    if (!area.value.trim() || send.disabled) return;
    send.disabled = true;
    const r = await remote.sendGoal({ text: area.value, party: to.value });
    send.disabled = false;
    line.className = `remote-line${r.ok ? "" : " is-bad"}`;
    line.textContent = r.ok ? (r.kept ? WAITS : SENT) : r.error;
    if (r.ok) area.value = "";
  });
  const box = h("section", { class: "remote-newgoal", "aria-label": "New goal" }, area, to, h("div", { class: "remote-row" }, send), line);
  /** The parties the journal names, as the *To* choices. */
  box.parties = (parties) => {
    const held = to.value;
    to.replaceChildren(h("option", { value: "" }, "The Orkmaster finds its party"), ...parties.filter((p) => p.slug).map((p) => h("option", { value: p.slug }, p.title)));
    to.value = parties.some((p) => p.slug === held) ? held : "";
  };
  return box;
}

/**
 * The journal screen for `remote`: `{node, draw()}`. `seeBoard()` is what the button *Show the Board as last seen* does. `draw` is called by the frame whenever the remote says it changed.
 * `reachedNote` is the line under *As of*.
 */
export function journalScreen(remote, { seeBoard, retry, note }) {
  const node = h("main", { id: "journal", class: "phone-frame remote-journal", hidden: true, "aria-label": "The journal" });
  const box = goalBox(remote), page = h("div", { class: "remote-page" }), head = h("header", { class: "remote-head" }), body = h("div", { class: "remote-body" });
  page.append(head, box, body);
  node.append(page);
  function draw() {
    const v = remote.view();
    if (!v) { fill(head,); fill(body,); return; }
    box.parties(v.parties);
    fill(head,
      h("p", { class: "remote-asof", "data-asof": "1" }, v.asOf),
      h("p", { class: "remote-sub" }, note || "Your computer cannot be reached: this is what its journal says."),
      v.line && h("p", { class: "remote-line is-bad", role: "status" }, v.line),
      h("div", { class: "remote-row" },
        h("button", { class: "ork-btn", type: "button", onclick: retry }, "Try again"),
        h("button", { class: "ork-btn", type: "button", onclick: seeBoard }, "Show the Board as last seen")));
    fill(body,
      v.waiting.length > 0 && h("section", { class: "remote-section", "aria-label": "Sent from this phone" }, h("h2", {}, "From this phone"), v.waiting.map(downCard)),
      v.refused.length > 0 && h("section", { class: "remote-section" }, h("h2", {}, "Answers not taken"), v.refused.map((a) => h("p", { class: "remote-line is-bad" }, a.error))),
      v.failed.length > 0 && h("section", { class: "remote-section", "aria-label": "Failed" }, h("h2", {}, "Failed"),
        h("ul", { class: "remote-goals" }, v.failed.map((f) => h("li", { class: "remote-goal", "data-state": "failed" }, h("span", { class: "remote-goal__title" }, String(f.title || f.slug)),
          f.error && h("span", { class: "remote-goal__error" }, String(f.error)))))),
      v.parties.map((p) => h("section", { class: "remote-section", "data-party": p.slug }, h("h2", {}, p.title),
        p.goals.length ? h("ul", { class: "remote-goals" }, p.goals.map(goalRow)) : h("p", { class: "remote-line" }, "No goals"))),
      v.parties.length === 0 && h("p", { class: "remote-line" }, "No parties or goals yet"));
  }
  return { node, draw };
}
