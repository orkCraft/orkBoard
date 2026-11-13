// Whether the person asked for no motion (`prefers-reduced-motion`); the System's look (systemmap.js) plays only when they did not.
// What moves elsewhere is the hand's (hand/motion.js) and the task card's (table/work.css).

export const reducedMotion = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
