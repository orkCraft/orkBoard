// *Low work may run at night?* (docs/specs/83-one-field-and-the-night-asked.md §0, §3; decisions §100): the one standing permission, asked once, the first time a Low goal is added while
// the Board has not been asked (`board.night_low` is null), or when *Tonight* is pressed on a pitch or a held goal. A sheet with two 44 px choices, *Yes, at night* (the default, first) and *No, by day*;
// either is `ideas.night_allow`, and the question is never drawn again. Closing it answers nothing: it is asked the next time. The host's refusal is said in the sheet, which stays.
// `ask(after)`: `after(allow)` runs once it is answered. Settings (shell-drawer.js) changes the answer at any time.
import { h, sheet } from "./util.js";

/** "01:00-07:00" → "between 01:00 and 07:00". */
const span = (night) => (/^\d\d:\d\d-\d\d:\d\d$/.test(night || "") ? night : "01:00-07:00").split("-").join(" and ");

/** `core`: the board's frame (st, call, refresh). Returns {el, ask(after), unset(), off()}. */
export function makeNightAsk(core) {
  const body = h("div", { class: "night-ask" });
  const sh = sheet("Low work may run at night?", body);
  sh.el.classList.add("night");
  let busy = false;

  function draw(after, said = "") {
    const go = async (allow) => {
      if (busy) return;
      busy = true;
      draw(after);
      const got = await core.call("ideas.night_allow", { allow }, (text) => { busy = false; draw(after, text || "That could not be saved."); });
      if (!got) return;
      busy = false;
      sh.close();
      await core.refresh();
      if (after) after(allow);
    };
    const btn = (cls, act, text, on) => h("button", { class: `ork-btn ${cls} big`.trim(), type: "button", "data-act": act, disabled: busy, onclick: on }, text);
    body.replaceChildren(...[
      said ? h("p", { class: "warn night-ask__said", role: "alert", "data-said": "refused" }, said) : null,
      h("p", { class: "cap", "data-sec": "night-line" }, `Low goals then run between ${span(core.st.board?.night)}, on what is left of the window; you can change it in Settings`),
      btn("primary", "night-yes", "Yes, at night", () => go(true)),
      btn("", "night-no", "No, by day", () => go(false))].filter(Boolean));
  }
  return {
    el: sh.el,
    ask(after) { busy = false; draw(after); sh.open(); },
    /** The Board has never been told (null); a Board that does not say is not asked. */
    unset: () => core.st.board?.night_low === null,
    /** Answered *No*: *Tonight* is not drawn. */
    off: () => core.st.board?.night_low === false,
  };
}
