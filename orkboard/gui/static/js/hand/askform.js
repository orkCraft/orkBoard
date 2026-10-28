// The questions of a spec or a goal as one form (docs/specs/35-goals-window.md §0, §11.2; docs/specs/98-the-table-and-the-hand.md §7): a box per question, one Send
// (`ideas.answer`). It lies in the stop opened over the pane (stopface.js): a lifted card's *Open…*, with the answers pressed in the card carried over (`picks`).
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { ask, items } from "../board/store.js";
import { Questions } from "../board/ask.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";

/** `asked`/`picks`: the row's questions as the host sends them and the answers pressed in its card; More fills them in. */
export function AskForm({ slug, goal = false, asked = null, picks = [], done = () => {} }) {
  const [questions, setQuestions] = useState(asked ? asked.map((q) => q.ask) : null);
  useEffect(() => {
    if (asked) return undefined;
    let live = true;
    (async () => {
      const got = goal ? await ask("ideas.goal", { slug }) : await ask("ideas.page", { slug });
      if (!live) return;
      setQuestions(goal ? (got?.questions || []) : items(got?.sections?.find((s) => s.name === "Open questions")?.text));
    })();
    return () => { live = false; };
  }, [slug, goal]);
  const send = async (answers, photos = []) => {
    const got = await act("ideas.answer", { slug, answers, ...(photos.length && !goal ? { photos: photos.map((url) => ({ data: url.slice(url.indexOf(",") + 1) })) } : {}), ...(goal ? { goal: true } : {}) });
    if (got) done();
    else if (photos.length) toast("The pictures could not be sent: try fewer or smaller ones.", "warning");
  };
  return html`<div class="hand-askform" data-form="ask">
    ${questions === null ? html`<p class="ok-tone-muted">Opening…</p>`
      : questions.length ? html`<${Questions} questions=${questions} onSend=${send} initial=${asked ? picks : []} hints=${asked ? asked.map((q) => q.why || "") : []} choices=${asked ? asked.map((q) => q.choices || []) : []} pictures=${!goal} />`
        : html`<p class="ok-tone-muted">No question is open any more.</p>`}
  </div>`;
}
