(mode) => {
  // The mockup "no big card": a lifted card is not opened at 404 x 566. It stays a hand card (the question), its answers
  // are cards of the same size under it, and the table shows its goal, its card marked in the column. Read from the product's lifted
  // card, which is then hidden; nothing here is in the product.
  const lifted = document.querySelector('.hand-lifted');
  if (!lifted) return 'no lifted card';
  document.querySelector('.ac-stage')?.remove();
  const kind = lifted.dataset.kind, failed = kind === 'failed';
  const elem = [...lifted.classList].find((c) => c.startsWith('el-')) || '';
  const rune = lifted.querySelector('.corner__rune .ork-elem')?.outerHTML || '';
  const goal = lifted.querySelector('.corner__name')?.textContent.trim() || '';
  const title = lifted.querySelector('.hand-lifted__title')?.textContent.trim() || '';
  const text = lifted.querySelector('.hand-lifted__text')?.textContent.trim() || '';
  const head = lifted.querySelector('.corner__who img')?.outerHTML || '';
  const who = lifted.querySelector('.corner__who .corner__word')?.textContent || '';
  const asker = who.replace(/^the /, '').replace(/ leader asks$/, '');
  const gem = lifted.querySelector('.hand-spend .ork-gem')?.outerHTML || '';

  // the mockup's own words for what each way leads to (the product has only a button's title today)
  const WHY = {
    'Server counts, phones show it': 'One clock on the server; every phone draws the same second.',
    'Each phone counts down alone': 'No server time; phones may drift a second apart.',
    'Start again': 'Its tasks not merged or at Review run again.',
  };
  const answers = [];
  for (const b of lifted.querySelectorAll('.hand-answers .ork-btn')) {
    const t = b.textContent.replace(/^●\s*/, '').trim();
    if (/^Open/.test(t)) continue;
    if (/^Let /.test(t)) { answers.push({ t: `${asker} decides`, sign: 'lead', why: `It answers with its own pick and says so tonight.` }); continue; }
    answers.push({ t, sign: failed ? 'play' : 'compass', pick: !failed && b.classList.contains('primary'), why: WHY[t] || b.title || '', cost: failed ? gem : '' });
  }
  if (!failed) answers.push({ t: 'Your own words…', sign: 'text', pen: true, why: `Write ${asker} what you want; it reads it and goes on.` });

  const card = (o, cls) => `<button type="button" class="ork-card ac-card ${elem} ${cls || ''}" ${o.pen ? 'data-pen="1"' : ''}>
      <span class="ac-top"><span class="ac-rune">${rune}</span><span class="ac-kind">${o.kindHtml || (o.sign === 'lead' ? head : `<span class="ork-sign ${o.sign}" aria-hidden="true"></span>`)}</span></span>
      <span class="ac-name">${o.t}</span>
      <span class="ac-text">${o.why || ''}</span>
      <span class="ac-foot"><span class="ac-who">${o.pick ? `${head}<span>its pick</span>` : o.footWho || ''}</span><span class="ac-much">${o.cost || ''}</span></span>
    </button>`;
  const q = card({ t: title, why: text, kindHtml: `<span class="ork-sign ${failed ? 'alert' : 'question'} ${failed ? 'is-danger' : 'is-alert'}" aria-hidden="true"></span>`,
    footWho: `${head}<span>${failed ? 'Tech' : asker}</span>`, cost: failed ? gem : '' }, `ac-q ${failed ? 'fails' : 'asks'}`);

  const stage = document.createElement('div');
  stage.className = 'ac-stage';
  stage.innerHTML = `<div class="ac-qbox">${q}</div>
    <div class="ac-answers"><span class="ac-label">${failed ? 'What now' : 'Your answer'}</span><div class="ac-row">${answers.map((a) => card(a, a.pick ? 'is-pick' : '')).join('')}</div></div>
    <div class="ac-acts"><button type="button" class="ork-btn quiet">Open…</button><button type="button" class="ork-btn">Put it back</button></div>
    <div class="ac-pen"><textarea class="ork-input" rows="2" placeholder="Your words to ${asker}…">The server counts, but a phone that drops keeps counting and checks back on reconnect.</textarea><button type="button" class="ork-btn primary">Send to ${asker}</button></div>`;
  document.body.append(stage);
  document.body.classList.add('ac-on');
  if (mode === 'pen') { stage.classList.add('is-pen'); stage.querySelector('[data-pen]')?.classList.add('is-on'); }

  // place it: the answers stand on the hand's rim, risen out of it; the question a row above them
  const hand = document.querySelector('.hand')?.getBoundingClientRect();
  const pane = document.querySelector('.table-pane')?.getBoundingClientRect();
  if (hand && pane) {
    stage.style.left = `${pane.left + 24}px`;
    stage.style.bottom = `${innerHeight - hand.top - 40}px`;
  }

  // the context is the table's own: lifting a card already turns the table to its goal; its card in the column is marked
  const slug = (lifted.dataset.key || '').split('/')[1];
  document.querySelectorAll('.ac-about').forEach((e) => e.classList.remove('ac-about'));
  const mine = document.querySelector(`.col-card[data-goal="${slug}"]`);
  if (mine) mine.classList.add('ac-about', failed ? 'is-danger' : 'is-alert');
  return `${kind}: ${answers.length} answers`;
}
