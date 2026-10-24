// The goals bar and the Goals sheet (docs/specs/50-parties-and-goals.md §3.5, §6.2, §6.4; spec 52 §5.2, §5.8). Under the top bar, one quiet line of 44 px that says the party: at its far left the party's deck (spec 53 §1.1), then
// *⌄ Tech · 3 of 12 goals done* (while the filter is on, the party, the picked goals' elements, *1 of 7 goals* and *Show all*), at its right the gate (shell-party.js). A tap on the left opens the Goals sheet from the bottom: *About Tech ›* (the party's sheet), a line that says
// what a tap does, **At work**, **Planning**, **New · n** and **Flags · n** (folded rows, 44 px, spec 73 §5: *Process now* at the right of New, *k wait for main* at the right of Flags, which holds the goals that
// wait for main and the flags); a goal's row is one line of 44 px: its element (14 px), its type's sign (in its goal's colour; the space kept without one), its title (cut with an ellipsis), its mark (no alert edge, no alert words: the
// mark is the stop's one sign) and ✓ when picked, then › (44 px) that opens it; its old second line is its `aria-label` after the title. A tap picks or unpicks: only the picked goals' cards stay on the field, only their results and stops
// stay along the bottom (the filter, kept per party for the session in `st.picks`).
import { h, icon, sheet } from "./util.js";
import { elem, sign, typeTone } from "./shell-marks.js";
import { barName, barWords, filterWords, flagRelease, flagTally, goalsOf, hasReleaseParty, mainWaitWords, newOf, partyNameOf, releaseLine, waitWords } from "./shell-goals-words.js";

const LIT_MS = 700;                                  // a flag lit once in the sheet

/** `core`: the board's frame (st, draw, open); `about(slug)`: opens About this party; `process(model)`: *Process now* (the next new goal is read now). Returns {sheets, bar(model, gate), sync(model), clear()}. */
export function makeGoals(core, about, process = () => {}) {
  const st = core.st;
  const body = h("div", { class: "goals" });
  const sh = sheet("Goals", body);
  const count = h("span", { class: "ork-count" });
  const all = h("button", { class: "ork-btn quiet", type: "button", "data-act": "show-all", onclick: () => clear() }, "Show all");
  sh.bar.insertBefore(count, sh.shut);
  sh.bar.insertBefore(h("span", { class: "spacer" }), sh.shut);
  sh.bar.insertBefore(all, sh.shut);
  let shown = null;                                  // the party and its goals as they were drawn last

  const picked = (m) => m.picks;                       // the picks that are still among the party's open goals
  function setPicks(party, list) { st.picks = { ...(st.picks || {}), [party]: list }; core.draw(); }
  function toggle(slug) {
    const party = shown.m.goal.slug, now = picked(shown.m);
    setPicks(party, now.includes(slug) ? now.filter((s) => s !== slug) : [...now, slug]);
  }
  function clear() { if (shown) setPicks(shown.m.goal.slug, []); }

  // -- one goal's row ---------------------------------------------------------------------------------------------------------------------------------
  function row(r, on) {
    const words = `${r.title} · ${r.line}`;
    return h("div", { class: `dk${on ? " is-on" : ""}`, "data-idea": r.slug },
      h("button", { class: "dk__main", type: "button", "aria-pressed": String(on), "data-idea": r.slug, "aria-label": words, title: words, onclick: () => toggle(r.slug) },
        h("span", { class: "dk__elem", "aria-hidden": "true" }, elem(r.element, { dim: r.raw })),
        r.type ? h("span", { class: `dk__type ${typeTone(r.element, r.raw)}`, "data-type": r.type.id }, sign(r.type.sign, r.type.name)) : h("span", { class: "dk__gap", "aria-hidden": "true" }),
        h("span", { class: "dk__title" }, r.title),
        r.mark ? h("span", { class: "dk__mark" }, sign(r.mark, r.markTip)) : null, on ? h("span", { class: "dk__check" }, sign("check", "picked")) : null),
      h("button", { class: "dk__open", type: "button", "aria-label": `Open ${r.title}`, onclick: () => { sh.close(); core.open(r.open, "map"); } }, h("i", { class: "ork-chev right", "aria-hidden": "true" })));
  }

  // -- the folded rows, New and Flags (spec 73 §3, §5): 44 px, the chevron, the word, the count; the folds are kept for the session ---------------------------------
  const folds = { new: false, flags: false };
  function foldRow(key, word, n, at) {
    const open = folds[key];
    return h("div", { class: `gfold${open ? " is-open" : ""}`, "data-fold": key },
      h("button", { class: "gfold__head", type: "button", "aria-expanded": String(open), "aria-label": `${word} ${n}`, onclick: () => { folds[key] = !open; drawSheet(); } },
        h("i", { class: open ? "ork-chev" : "ork-chev right", "aria-hidden": "true" }), h("span", { class: "gfold__word" }, word), h("span", { class: "gfold__n" }, `· ${n}`)), at);
  }

  // -- the Flags group: a flag's release, and a release's *Mark it out* (spec 68 §7.4, §7.5) --------------------------------------------------------------
  let asking = "", outError = "";                    // the release being asked about (*Is 1.4 out in the stores?*), and a refusal said under it
  const nameOf = (slug) => partyNameOf(st, slug);
  async function markOut(slug) {
    outError = "";
    const r = await core.call("ideas.release_out", { slug }, (e) => { outError = e || "Not done"; if (sh.el.open) drawSheet(); });
    if (!r) return;
    asking = "";
    await core.refresh();
  }
  /** A flag's line; a release's own row says its version and goals, then **Mark it out** (asking first) or, once said, *Out in 1.4*. */
  function flagRow(f, lit) {
    const cls = `cap goals__line goals__flag${lit.has(f.slug) ? " is-reward" : ""}`;
    if (!f.own) {
      const rel = flagRelease(f, hasReleaseParty(st), nameOf);
      return h("p", { class: cls, "data-idea": f.slug }, sign("flag"), " ", h("span", { class: "goals__ink" }, f.short), ` · ${flagTally(f)}`,
        rel ? h("span", { class: "goals__rel", "data-release": f.release ? (f.release.out ? "out" : "in") : "waits" }, ` · ${rel}`) : null);
    }
    const v = f.own.version, ask = asking === f.slug;
    return h("div", { class: "goals__release", "data-idea": f.slug, "data-out": f.own.out ? "yes" : "no" },
      h("p", { class: cls }, sign("flag"), " ", h("span", { class: "goals__ink" }, f.short), ` · ${releaseLine(f.own)}`),
      f.own.out ? null : ask
        ? h("div", { class: "goals__ask", role: "alert" }, h("p", {}, `Is ${v || "it"} out in the stores? Orkboard submits nothing: say so once you have.`),
          outError ? h("p", { class: "warn" }, outError) : null,
          h("div", { class: "row" }, h("button", { class: "ork-btn primary", type: "button", "data-act": "out", onclick: () => markOut(f.slug) }, "Out"),
            h("button", { class: "ork-btn", type: "button", "data-act": "not-yet", onclick: () => { asking = ""; outError = ""; drawSheet(); } }, "Not yet")))
        : h("button", { class: "ork-btn goals__out", type: "button", "data-act": "mark-out", onclick: () => { asking = f.slug; outError = ""; drawSheet(); } }, "Mark it out"));
  }

  function drawSheet() {
    const { m, list } = shown;
    const on = new Set(picked(m));
    const lit = new Set(st.lit || []);
    const lines = (rows, mark) => rows.map((r) => h("p", { class: "cap goals__line" }, sign(mark), ` ${r.title} · ${r.line}`));
    const { fresh, planning } = newOf(list, Boolean(m.goal.ideation));
    if (lit.size) folds.flags = true;                                    // a flag just raised is shown, not folded away
    const next = m.process?.next;
    const rows = (rs) => rs.map((r) => row(r, on.has(r.slug)));
    count.textContent = String(list.n);
    all.hidden = !on.size;
    body.replaceChildren(...[
      h("button", { class: "goals__about", type: "button", "data-act": "about", "aria-haspopup": "dialog", title: "About this party: what it is for, its checks, its price and its flags",
        onclick: () => { sh.close(); about(m.goal.slug); } }, h("span", {}, `About ${m.goal.short || m.goal.title}`), h("i", { class: "ork-chev right", "aria-hidden": "true" })),
      m.goal.wait_release > 0 ? h("button", { class: "goals__wait", type: "button", "data-act": "wait-release", "aria-haspopup": "dialog", title: "New goal of A release, with these flags ticked",
        onclick: () => { sh.close(); core.newIdea("release", m.goal.slug); } }, sign("flag"), h("span", {}, waitWords(m.goal.wait_release)), h("i", { class: "ork-chev right", "aria-hidden": "true" })) : null,
      h("p", { class: "cap goals__how" }, "A tap shows only that goal’s tasks; tap more to add them. ", h("i", { class: "ork-chev right", "aria-hidden": "true" }), " opens one."),
      h("h3", {}, "At work"), ...(list.atWork.length ? rows(list.atWork) : [h("p", { class: "cap" }, "Nothing at work.")]),
      h("h3", {}, "Planning"), ...(planning.length ? rows(planning) : [h("p", { class: "cap" }, "Nothing in Planning.")]),
      fresh.length ? foldRow("new", "New", fresh.length, h("button", { class: "ork-btn gfold__act", type: "button", "data-act": "process", disabled: !next, title: next ? `${m.process?.lead?.name || "Taskmaster"} reads “${next.title}” now` : "No new goal to read",
        onclick: () => process(m) }, "Process now")) : null, ...(fresh.length && folds.new ? rows(fresh) : []),
      foldRow("flags", "Flags", list.flags.length, list.waits.length ? h("span", { class: "gfold__note" }, mainWaitWords(list.waits.length)) : null),
      ...(folds.flags ? [...lines(list.waits, "check"), ...(list.flags.length ? list.flags.map((f) => flagRow(f, lit)) : [h("p", { class: "cap" }, "None yet.")])] : [])].filter(Boolean));
    if (lit.size && sh.el.open) { st.lit = new Set(); setTimeout(() => body.querySelectorAll(".is-reward").forEach((e) => e.classList.remove("is-reward")), LIT_MS + 50); }
  }

  // -- the bar ------------------------------------------------------------------------------------------------------------------------------------------
  /** The bar: at its left the party's deck (`deck`: a node or null), then *⌄ Tech · 3 of 12 goals done* (the filter on: the party, the picked goals' elements, *1 of 7 goals*, *Show all*) and at its right the gate (`gate`: a node or null). */
  function bar(m, gate, deck) {
    const list = goalsOf(st, m);
    const on = picked(m);
    shown = { m, list };
    const head = on.length
      ? h("button", { class: "gbar__head", type: "button", "aria-haspopup": "dialog", "data-act": "goals", "aria-label": `${filterWords(on, list)}: only their tasks are shown. Goals`, onclick: () => open() },
        h("i", { class: "ork-chev", "aria-hidden": "true" }), h("span", { class: "gbar__lbl" }, barName(m.goal)), h("span", { class: "gbar__els" }, ...on.map((s) => elem(m.nodes.find((n) => n.slug === s)?.element, { dim: false }))),
        h("span", { class: "gbar__words" }, filterWords(on, list)))
      : h("button", { class: "gbar__head", type: "button", "aria-haspopup": "dialog", "data-act": "goals", title: "The goals: a tap on one shows only its tasks",
        onclick: () => open() },
        h("i", { class: "ork-chev", "aria-hidden": "true" }), h("span", { class: "gbar__lbl" }, barName(m.goal)), " ", h("span", { class: "gbar__quiet" }, `· ${barWords(m.goal)}`));
    return h("div", { class: `gbar${on.length ? " is-on" : ""}` }, deck || null, head, on.length ? h("button", { class: "ork-btn quiet gbar__all", type: "button", "data-act": "show-all", onclick: () => clear() }, "Show all") : null, gate || null);
  }

  function open() { sh.open(); drawSheet(); }                   // open first: what is lit once is lit as it opens

  return {
    sheets: [sh.el],
    bar,
    /** The field was drawn again: an open sheet shows what it drew. */
    sync() { if (sh.el.open && shown) drawSheet(); },
    clear,
  };
}
