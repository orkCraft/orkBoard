// The Orkmaster's question about the Board in the code as a stop (docs/specs/151 F.1, decisions §255.10): a goal-free row `{kind: "in_code", step, title, text, ask, held, words, pages_in_history}`
// (gui/ideas_in_code.py), one stop of no party (it holds the Board's pushes), under the first lane (hand/data.js `laneOf`); its asker the Orkmaster's crowned head. The words come with the row, from realm/lexicon.py.

/** The stop of each `in_code` row of the Needs you rows. `ork`: the Orkmaster's head (the map's `project.orkmaster`). */
export function inCodeStopsOf(needs, shown, ork = null) {
  const head = ork ? { race: ork.race || "peon", tier: ork.tier || "crown" } : null;
  return needs.filter((row) => row.kind === "in_code").map((row) => ({ key: "in_code", kind: "in_code", row, node: null, task: null, label: "Orkmaster asks", gem: "", tone: "alert",
    gemTip: "", head, small: false, whoTip: "asked by the Orkmaster", title: row.title || "", full: row.title || "", text: row.step === "private" ? row.ask || "" : row.text || "", why: "",
    g: null, party: { slug: shown, name: "", head, lead: "Orkmaster" }, other: false }));
}
