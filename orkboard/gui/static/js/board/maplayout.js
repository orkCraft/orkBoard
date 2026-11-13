
/** The Needs you kinds on a goal, in words (spec 39 §4.3). */
export const NEEDS_WORDS = { asks: "asks you", plan: "plan ready", todo: "a to-do waits", failed: "failed", proposal: "proposed", pick: "asks you to pick", pitch: "a pitch judged" };
/** A task's state in words: the preview's task view says it. */
export const TASK_STATE = { waiting: "waiting", ready: "queued", running: "working", testing: "testing", review: "at Review", picking: "asks you to pick", merged: "merged",
  failed: "needs you", held: "held", dropped: "dropped" };

/** A task left to do: not merged, not dropped. */
export const leftToDo = (t) => t.state !== "merged" && t.state !== "dropped";

