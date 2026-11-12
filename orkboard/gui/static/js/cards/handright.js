// The hand's right on the table of cards (decisions §298.9; docs/mockups/table-grammar/ ?face=desk): two groups, *What you do* (the die, Play) and
// *What you have* (the backpack, *Inventory*, and the book, *History*), a thin line between, and at the window's right edge the deck of blank cards:
// a small pile of card backs, half hidden past the edge, its top card rising when pointed at or focused, *New goal* and the key N. Pressing the deck
// does what the + card at the hand's left did (hand/hand.js `plus`); the + card is not drawn there on the table of cards. Layout: handright.css.
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { fieldOpen } from "../hand/state.js";
import { focusInPress } from "../hand/fieldturn.js";
import { PlayDie } from "../hand/playdie.js";

if (typeof document !== "undefined") {                         // this sheet loads with its module, as the places' does
  const href = new URL("./handright.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** The deck of blank cards: pressed it makes a new goal's card, as the + card did. */
export function BlankDeck({ onPress }) {
  const open = fieldOpen.value;
  return html`<div class="hr-deck"><button type="button" class=${cls("hr-blank", { "is-under": open })} data-blank-deck aria-label="New goal" title="New goal" aria-haspopup="dialog" aria-keyshortcuts="N"
      aria-expanded=${open ? "true" : "false"} onClick=${(e) => { if (!fieldOpen.value) focusInPress(); onPress?.(e); }}>
    <span class="hr-blank__top ork-card ork-plus" aria-hidden="true"><${Icon} name="plus" /></span>
    <span class="hr-blank__cap" aria-hidden="true">New goal <kbd class="hr-key">N</kbd></span></button></div>`;
}

/** The hand's right: what the person does, what it has, and the deck of blank cards. `places` the backpack and the book, `pots` the AI tools' potions when they lie here. */
export function HandRight({ places = null, pots = null, onPress }) {
  return html`<div class="hand-end hr">
    <div class="hr-group" role="group" aria-label="What you do"><span class="hr-lab">What you do</span><div class="hr-items"><${PlayDie} /></div></div>
    ${places && html`<span class="hr-sep" aria-hidden="true"></span><div class="hr-group" role="group" aria-label="What you have"><span class="hr-lab">What you have</span><div class="hr-items">${places}</div></div>`}
    ${pots}
    <${BlankDeck} onPress=${onPress} />
  </div>`;
}
