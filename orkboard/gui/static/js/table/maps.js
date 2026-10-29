// A party's one map by its craft (docs/specs/102-the-other-maps-and-picking-on-them.md §4, decisions §134.2): the pane draws the open tab's. Written by the lead;
// a map's part registers its face with `mapFor(craft, Component)` from its own module (`({g, narrow}) => html`), and wraps each card it draws in `Pickable`
// (part F fills it: a card of the map the + card's field is addressed to is taken as a mark, §6). Tech's map stays syspane.js's System.
import { html } from "../html.js";
import { leadsSystem } from "./data.js";

const MAPS = {};

/** `Component` draws the map of a party of `craft` (`tech`, `design`, `product`, `game-design`, `art`, `release`, `marketing`, …). */
export function mapFor(craft, Component) { MAPS[craft] = Component; }

/** The craft whose map a party's tab shows: its own (`party_craft`), Tech's for a party the Architect leads, else none. */
export const craftOf = (g) => g?.party_craft || (leadsSystem(g) ? "tech" : "");

/** The map's face of party `g`, or null (System is drawn by the pane itself, a craft with no map yet draws its header alone). */
export const mapOf = (g) => (craftOf(g) === "tech" ? null : MAPS[craftOf(g)] || null);

// Picking's seam (§6): until part F, a card is itself.
let wrap = ({ children }) => children;
/** Part F sets how a pickable card is drawn: `({map, id, name, group, children}) => html`. */
export function pickWith(fn) { wrap = fn; }
/** A card of a map that an addressed idea may pin: `map` the map's id (its craft), `id` the card's, `name` its words, `group` the group it belongs to. */
export const Pickable = (props) => html`${wrap(props)}`;
