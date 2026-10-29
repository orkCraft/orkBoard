// What works moves (docs/specs/107-what-the-owners-day-said.md §7, decisions §182.7): a task card at work says the time it has worked, ticking each second, and a card whose state changed flashes its frame once. The motion is
// table.css's (off under reduced motion); the time ticks whatever the person asked for motion.
import { useEffect, useRef, useState } from "preact/hooks";

/** A task at work (its card moves; nothing that waits does). */
export const aliveState = (state) => state === "running" || state === "testing";

/** *12 s*, *1 m 12 s*, *1 h 5 m*: the time a task has worked. */
export function workedWords(secs) {
  const s = Math.max(0, Math.floor(secs));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} m ${s % 60} s`;
  return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} m`;
}

/** The seconds since `since` (an ISO time of the host, local), ticking each second while `on`; -1 with no usable time. */
export function useWorked(since, on) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!on) return undefined;
    setNow(Date.now());
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [on]);
  const from = Date.parse(since || "");
  return on && Number.isFinite(from) ? Math.max(0, Math.floor((now - from) / 1000)) : -1;
}

/** Whether the card's task changed its state since the last draw (not on the first read, not for what changed while the page was hidden): `is-changed` for 0.6 s, then still. */
export function useChanged(state) {
  const was = useRef(state), [changed, setChanged] = useState(false);
  useEffect(() => {
    if (was.current === state) return undefined;
    was.current = state;
    if (typeof document !== "undefined" && document.hidden) return undefined;
    setChanged(true);
    const t = setTimeout(() => setChanged(false), 650);
    return () => clearTimeout(t);
  }, [state]);
  return changed;
}
