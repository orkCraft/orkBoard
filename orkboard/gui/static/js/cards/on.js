// Whether the window draws the table of cards (goal 170, the talk of 11 November 2026; docs/mockups/table-cards/): on mocks
// (`?mock=1`) and with `?table=cards`; otherwise the table as it is until the decisions on the cards are written.
import { onMocks } from "../link.js";

const ASKED = new URLSearchParams(location.search).get("table") === "cards";
export const cardsOn = () => ASKED || onMocks();
