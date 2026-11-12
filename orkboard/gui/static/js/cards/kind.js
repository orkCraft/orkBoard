// The three kinds of card a mat draws (decisions §300.4): a goal, a decision or a part. Nothing else is a card: a check is the decision it guards, a stage a line of its
// card's L. A card's top right corner says which by its sign (a goal's is its type's), and its accessible name says it too.
export const KIND = { goal: { word: "goal", sign: "target" }, decision: { word: "decision", sign: "balance" }, part: { word: "part", sign: "compass" } };

/** The sign a card of `kind` shows at its top right: a goal's own type's when it has one. */
export const signOf = (kind, own = "") => (kind === "goal" ? own || KIND.goal.sign : (KIND[kind] || KIND.goal).sign);

/** A card's accessible name with its kind said last: `Name: line, a goal`. */
export const named = (text, kind) => `${text}, a ${(KIND[kind] || KIND.goal).word}`;
