// The words of the opened card and a new goal's card (docs/specs/147-one-card-four-corners.md part D, decisions §251.2, §252.4), as realm/lexicon.py says them (`slot_*`, `attach_hint`, `opened_*`; tests/test_lifted_card_browser.py keeps them so).
// A new goal's empty corners are dashed slots that say what will stand there; its window says what to drop on it while nothing is attached; the opened card's foot says who asks.
export const SLOT_RUNE = "the rune: given when it is laid", SLOT_WHO = "who: the Orkmaster routes it", SLOT_MUCH = "how much: after its estimate", ATTACH_HINT = "Drop pictures or files here, or paste a picture", LEADER = "leader", ASKS = "asks";

/** *the Tech leader asks*, *the Orkmaster asks*: who asks on the opened card's foot (`asker`: stopcard.js `askerOf`'s word, `party`: the party's name). */
export const asksWords = (asker, party) => (asker === "the Orkmaster" || !party ? `the Orkmaster ${ASKS}` : `the ${party} ${LEADER} ${ASKS}`);
