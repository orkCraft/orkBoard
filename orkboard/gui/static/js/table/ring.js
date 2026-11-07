// The portal's ring round the top card of Release's lane (docs/specs/156-one-pick-and-the-release-column.md D.4, decisions §261.8): orkUI's `.ork-portal-ring` (0.20.0), drawn only while a goal is ready for main, its checks run or the rite plays, behind the first ready
// card, which lies in its middle; else there is no ring. Open while the way is clear, sealed while the gate holds the goal or a check is not passed (the reasons are said on the table: tomain.js, checksview.js), waking the first time it opens on a device, and
// playing the rite in the goal's colour when the goal goes in (`is-sending rite-<element>`, portal.js `play`). It is a picture and takes no press: the card is picked, To main is the picked card's act. Its sheet is lane.css.
import { useEffect, useLayoutEffect } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem } from "../orkui.js";
import { mapData } from "../shell/store.js";
import { RITE_MS, openedOnce, woke, first, plan, sending, taking, chosenSlug } from "./portal.js";
import { checksOf, pending } from "./checks.js";

/** Whether the way into main is shut for the chosen goal: the gate holds it (a seal no check owns, or a plan that failed), or a check has not passed. */
export function shutFor(slug) {
  const p = plan.value, mine = !!slug && chosenSlug() === slug && p?.slug === slug;
  if (!mine) return false;
  const owned = p.state === "ok" && (!p.sealed || p.conflict), list = owned ? checksOf(slug) : [], asking = owned && pending.value === slug && !list.length;
  const sealed = p.state === "fail" || (!!p.sealed && !(p.conflict && (list.length > 0 || asking)));
  return sealed || asking || list.some((c) => c.state !== "passed");
}

/** The ring round `children` (the first ready card) of the goal `slug` (null while only the rite plays). */
export function RingAround({ slug = null, children }) {
  const node = slug ? (mapData.value?.nodes || []).find((n) => n.slug === slug) : null, element = node?.element || "", hue = node?.hue || element, shut = shutFor(slug), rite = sending.value;
  const state = shut ? "sealed" : "open";
  useLayoutEffect(() => { if (slug) openedOnce(); }, [slug]);                      // the ring opens: it wakes the first time on a device
  useEffect(() => {                                                                  // the rite plays once: its class comes off after RITE_MS (the ring's animations are done by then)
    if (!rite) return undefined;
    const t = setTimeout(() => { sending.value = ""; }, RITE_MS);
    return () => clearTimeout(t);
  }, [rite]);
  return html`<div class="portal-host is-ring" data-portal=${state} data-ring=${slug || "rite"}>
    <span class=${cls("ork-portal-ring", { "is-open": !shut || !!rite, "is-sealed": shut && !rite, "is-waking": !shut && first.value && !woke.value, "is-taking": taking.value, "is-sending": !!rite, [`rite-${rite}`]: !!rite })}
        aria-hidden="true" onAnimationEnd=${(e) => { if (e.animationName === "ork-ring-eye") woke.value = true; }}>
      <span class="ork-portal-ring__seal">${element && html`<${Elem} name=${element} hue=${hue} />`}</span>
    </span>
    ${children}
  </div>`;
}
