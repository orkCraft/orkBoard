// *Remove party* (docs/specs/80-a-party-removed.md §0, §3, §5; decisions §97): the question at the foot of the party's sheet. A sheet with 44 px choices: *Move its k goals to General and remove* (the default,
// first), *Remove the party and its k goals* (the danger colour), *Cancel*; a party with no goal says *It has no goals* and asks *Remove* / *Cancel*. The host's refusal (*2 goals at work: stop them first*) is
// said in the question, which stays. After it: the toast, the Board read again, and General (else the first party) shown when the removed one was open. General has no *Remove party*.
import { h, sheet } from "./util.js";
import { nodesOf } from "./shell-arena-words.js";

export const GENERAL = "general";                              // the party a goal without a party belongs to: it stays
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

/** `core`: the board's frame (st, call, refresh, parties(), pick(slug), flash(text)). Returns {el, ask(g, done), can(slug)}; `done`: called once the party is gone (the party's sheet is put away). */
export function makeRemove(core) {
  const body = h("div", { class: "remove-ask" });
  const sh = sheet("Remove party?", body);
  sh.el.classList.add("remove");
  let busy = false;

  function draw(g, said, done) {
    const n = nodesOf(core.st, g.slug).length;
    const go = async (goals) => {
      if (busy) return;
      busy = true;
      draw(g, "", done);
      const was = core.parties().shown === g.slug;
      const got = await core.call("ideas.track_drop", { slug: g.slug, goals }, (text) => { busy = false; draw(g, text || "That party could not be removed.", done); });
      if (!got) return;
      busy = false;
      sh.close();
      done();
      const moved = got.moved || 0, dropped = got.dropped || 0;
      core.flash(`${got.title || g.title} removed${moved ? ` · ${plural(moved, "goal")} moved to General` : ""}${dropped ? ` · ${plural(dropped, "goal")} removed` : ""}`);
      await core.refresh();
      if (was) { const list = core.parties().list; core.pick((list.find((c) => c.slug === GENERAL) || list[0])?.slug || GENERAL); }
    };
    const btn = (cls, act, text, on) => h("button", { class: `ork-btn ${cls}`.trim(), type: "button", "data-act": act, disabled: busy, onclick: on }, text);
    sh.title(`Remove ${g.title}?`);
    body.replaceChildren(...[
      said ? h("p", { class: "warn remove-ask__said", role: "alert", "data-said": "refused" }, said) : null,
      n ? h("p", { class: "cap" }, `${plural(n, "goal")} in this party`) : h("p", { class: "cap", "data-sec": "no-goals" }, "It has no goals"),
      ...(n ? [btn("primary", "remove-move", `Move its ${plural(n, "goal")} to General and remove`, () => go("move")),
        btn("danger", "remove-drop", `Remove the party and its ${plural(n, "goal")}`, () => go("drop"))]
        : [btn("danger", "remove-empty", "Remove", () => go("move"))]),
      btn("", "remove-cancel", "Cancel", () => sh.close())].filter(Boolean));
  }
  return { el: sh.el, ask(g, done) { busy = false; draw(g, "", done); sh.open(); }, can: (slug) => slug !== GENERAL };
}
