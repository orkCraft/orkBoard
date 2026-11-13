// Pair a phone (docs/design/mobile.md §2): a QR code the phone scans, which carries the listener's address, the
// certificate's fingerprint the phone pins and a one-time code good for two minutes; the host's phones.* commands
// (gui/phones.py), drawn by shell/pair.js. The app in the phone's browser (gui/pwa.py): with Tailscale here and its
// certificate, the QR code leads the person through it — Tailscale's download while no phone of theirs is in the
// tailnet, then the app's link, which opens Orkboard in the phone's browser and pairs it at once.
// Once a phone is paired, asked once (decisions-2026-10 §18): keep the computer awake, on power, so the phone can
// reach it all day (gui/keep_awake.py `awake.offer`; Settings → Keep the computer awake changes it later).
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "./html.js";
import { command, say, PRODUCT } from "./link.js";

/** "Keep this Mac awake so your phone can reach it all day?" Yes / Not now, once (`machine`: "Mac" or ""). */
export function AwakeOffer({ machine, onDone }) {
  const [gone, setGone] = useState(false);
  if (!machine || gone) return null;
  const answer = (yes) => { setGone(true); command("awake.offer", { yes }).then(() => onDone && onDone(), () => {}); };
  return html`<span class="gui-phones__awake" role="group" aria-label=${say("Keep the computer awake")}>
    <span class="ok-font-status">${say(`Keep this ${machine} awake so your phone can reach it all day? Only on power.`)}</span>
    <span><button class="ork-btn primary" onClick=${() => answer(true)}>${say("Yes")}</button>
      <button class="ork-btn" onClick=${() => answer(false)}>${say("Not now")}</button></span>
  </span>`;
}

/** While a code shows: Tailscale's state each few seconds, and what the QR code says now — `{qr, alt, lines}`.
 *  No phone opens the `orkcraft://` link (no app takes it yet: tools/phone.py does), so without Tailscale and its
 *  certificate here the code leads to what is missing, and Pair a phone again looks for the tailnet anew. */
export function useAppStep(offer, left) {
  const [t, setT] = useState(null);
  useEffect(() => {
    if (!offer) { setT(null); return undefined; }
    const read = () => command("phones.tailnet").then(setT, () => {});
    read();
    const timer = setInterval(read, 3000);
    return () => clearInterval(timer);
  }, [offer]);
  if (!offer) return null;
  if (!t) return { qr: null, link: "", alt: "", lines: [say("Looking for Tailscale…")] };
  const again = say("Then Cancel and Pair a phone again: the town looks for Tailscale anew.");
  if (!offer.app_link && !t.running) {
    return { qr: t.install_qr, link: t.install, alt: say("QR code to install Tailscale"), lines: [
      say(t.installed ? "Tailscale is on this computer but not running or not logged in: start it and log in."
        : "The phone reaches the town through Tailscale, and it is not on this computer: install it here (tailscale.com/download) and log in."),
      say("On the phone: scan this code, install Tailscale and log in with the same account."), again] };
  }
  if (!offer.app_link) {
    return { qr: t.dns_qr, link: t.dns, alt: say("QR code to the tailnet's DNS settings"), lines: [
      say("Tailscale runs, but the tailnet gives this computer no HTTPS certificate, and the phone's browser needs one."),
      say("Turn on MagicDNS and HTTPS Certificates in the tailnet's DNS settings (this code opens them; login.tailscale.com/admin/dns)."), again] };
  }
  const phone = t.phones.find((p) => p.online);
  if (!phone) {
    return { qr: t.install_qr, link: t.install, alt: say("QR code to install Tailscale"), lines: [
      say("1. Scan it with the phone's camera and install Tailscale."),
      say(t.account ? `2. Log in to Tailscale on the phone as ${t.account} and turn it on.` : "2. Log in to Tailscale on the phone with this computer's account and turn it on."),
      say(`3. When the phone is in the tailnet, this code turns into the link that opens ${PRODUCT} on it.`),
      say(`The pairing code is good for ${left} s; show a new one if it runs out.`)] };
  }
  return { qr: offer.app_qr, link: offer.app_link, alt: say(`QR code to open ${PRODUCT} on the phone`), lines: [
    say(`${phone.name} (${phone.os}) is in the tailnet. Scan it with the phone's camera: ${PRODUCT} opens in its browser and pairs.`),
    say(phone.os === "iOS" ? "Then Share → Add to Home Screen." : "Then Install app (or Add to Home screen) in the browser's menu."),
    say(`Good for ${left} s, once.`)] };
}

/** Pair a phone (shell/pair.js): a code while it is good, the time left and the phone that paired with it, named
 *  once; closing the place voids a code not used. The place keeps the paired phones' list and Forget. */
export function usePairing() {
  const [offer, setOffer] = useState(null);
  const [left, setLeft] = useState(0);
  const [paired, setPaired] = useState("");
  const [awake, setAwake] = useState("");
  const live = useRef(null);
  live.current = offer;
  useEffect(() => () => { if (live.current) command("phones.pair_stop").catch(() => {}); }, []);
  useEffect(() => {
    if (!offer) return undefined;
    const known = new Set(offer.phones.map((d) => d.id));
    const t = setInterval(() => command("phones.list").then((r) => {
      setLeft(Math.round(r.pairing));
      const fresh = r.phones.find((d) => !known.has(d.id));
      if (fresh) { setPaired(fresh.name); setAwake(r.awake_offer || ""); }
      if (!r.pairing || fresh) setOffer(null);
    }, () => {}), 1000);
    return () => clearInterval(t);
  }, [offer]);
  const pair = () => command("phones.pair").then((r) => { setPaired(""); setLeft(Math.round(r.pairing)); setOffer(r); }, () => {});
  const cancel = () => command("phones.pair_stop").then(() => setOffer(null), () => {});
  const step = useAppStep(offer, left);
  return { offer, left, paired, awake, pair, cancel, step };
}

/** The code itself, at the right of the head in the menu's top block (under it when the sheet is too narrow). */
export function PairQr({ pairing: { step } }) {
  if (!step) return null;
  return step.qr
    ? html`<img class="gui-phones__qr gui-you__qr" src=${step.qr} width="128" height="128" alt=${step.alt} />`
    : step.link && html`<div class="gui-you__qr"><p class="ok-font-status ok-tone-wait">${say("No QR code: this install lacks segno. Run pip install segno and open the town again — or type this link on the phone:")}</p>
      <code class="gui-phones__link">${step.link}</code></div>`;
}
