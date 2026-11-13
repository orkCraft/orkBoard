// The onboarding's first screen (gui/onboarding.py): in Orkboard the first open is the Orkmaster's (docs/specs/130 D.2,
// hand/setupcards.js, hand/addtool.js), so a step the host still names is skipped at once and nothing of it is drawn.
import { useEffect } from "preact/hooks";
import { html } from "./html.js";
import { command, town } from "./link.js";

function Skipping() {
  useEffect(() => { command("onboarding.skip", {}).catch(() => {}); }, []);
  return null;
}

export function Onboarding() {
  return town.value?.onboarding ? html`<${Skipping} />` : null;
}
