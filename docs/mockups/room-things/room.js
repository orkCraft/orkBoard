(mode) => {
  // The mockup "the room's things": the top row's three controls as things at the table. The lamp's chain (the person
  // Here or Away; the table's light goes with it), the backpack (drawn shut and open; open, the table lies in its leather),
  // the new chair (its crafts dealt to the hand, the Orkmaster's star on one; the pick opens the backpack on that craft).
  // Laid over the live page and ../table-look/; nothing here is in the product. mode: "on" | "off" | "chair" | "pack".
  const $ = (s, r = document) => r.querySelector(s);
  const RACES = '/ds/orkui/races/';
  const img = (name, w = 24, h = 22) => `<img class="ork-race__head" src="${RACES}${name}.png" srcset="${RACES}${name}@2x.png 2x" width="${w}" height="${h}" alt="">`;

  // ---- the lamp's chain, at the top row's right end, where the door stood ----------------------------------------
  const away = mode === 'off';
  document.documentElement.classList.toggle('lamp-off', away);
  $('.rt-lamp')?.remove();
  const lamp = document.createElement('button');
  lamp.type = 'button';
  lamp.className = 'rt-lamp' + (away ? ' is-off' : '');
  lamp.setAttribute('aria-pressed', String(!away));
  lamp.title = away ? 'Pull: you are back, the lamp is lit' : 'Pull: you are away, the lamp goes out';
  lamp.innerHTML = `<span class="rt-lamp__chain" aria-hidden="true"></span><span class="rt-lamp__bead" aria-hidden="true"></span>
    <span class="rt-lamp__txt"><span class="rt-lamp__w">${away ? 'Away' : 'Here'}</span><span class="rt-lamp__l">until ${away ? '19:00' : '23:00'}</span></span>`;
  document.body.append(lamp);

  // ---- the backpack: shut or open, drawn in pixels ---------------------------------------------------------------
  const pack = $('.stall-pack');
  if (pack) {
    const open = pack.classList.contains('is-open') || mode === 'pack';
    $('.rt-pack', pack)?.remove();
    pack.querySelector('svg')?.style.setProperty('display', 'none');
    const px = (x, y, w, h, c) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${c}"/>`;
    const L = '#7a5534', D = '#4a3020', K = '#2a1a10', S = '#c9a97a', B = '#d9b45c', I = '#140d08';
    const shut = px(5, 6, 10, 12, L) + px(4, 8, 1, 9, D) + px(15, 8, 1, 9, D) + px(5, 18, 10, 1, D)          // the body
      + px(7, 3, 6, 1, D) + px(6, 4, 1, 2, D) + px(13, 4, 1, 2, D)                                           // the handle
      + px(5, 6, 10, 6, '#8d6440') + px(5, 12, 10, 1, K)                                                      // the flap
      + px(9, 11, 2, 3, B) + px(9, 12, 2, 1, K)                                                               // the buckle
      + px(6, 14, 1, 3, S) + px(13, 14, 1, 3, S) + px(7, 15, 6, 2, D);                                        // stitches, the pocket
    const opened = px(5, 8, 10, 10, L) + px(4, 9, 1, 8, D) + px(15, 9, 1, 8, D) + px(5, 18, 10, 1, D)
      + px(5, 8, 10, 3, I) + px(7, 6, 3, 4, '#e6e1d8') + px(7, 6, 3, 1, '#7fbf9a')                             // the mouth, a card in it
      + px(5, 2, 10, 5, '#8d6440') + px(5, 2, 10, 1, D) + px(5, 6, 10, 1, K)                                   // the flap thrown back
      + px(9, 2, 2, 2, B)                                                                                      // its buckle, loose
      + px(6, 13, 1, 3, S) + px(13, 13, 1, 3, S) + px(7, 14, 6, 2, D);
    pack.insertAdjacentHTML('afterbegin', `<svg class="rt-pack" viewBox="3 1 14 18" width="31" height="40" shape-rendering="crispEdges" aria-hidden="true">${open ? opened : shut}</svg>`);
  }

  // ---- the new chair: its crafts dealt to the hand, as a question's answers are --------------------------------
  const ork = $('.col-head__tab img.ork-race__head')?.outerHTML || '';
  const CRAFTS = [
    { id: 'liveops', name: 'LiveOps', head: 'goblin-elder', line: 'Events, the numbers of play, what players say, small fixes', cost: '+12% a week' },
    { id: 'marketing', name: 'Marketing', head: 'gnome-elder', line: 'Pages, posts and search; the store page and the way people come', cost: '+9% a week', star: true },
  ];
  if (mode === 'chair') {
    $('.table-chair')?.classList.add('rt-lit');
    const hand = $('.hand')?.getBoundingClientRect(), plus = $('.hand .hand-plus')?.getBoundingClientRect();
    const card = (o, cls, kind) => `<button type="button" class="ork-card ac-card ${cls || ''}" data-craft="${o.id || ''}">
        <span class="ac-top"><span class="ac-rune">${o.rune || ''}</span><span class="ac-kind">${kind}</span></span>
        <span class="ac-name">${o.name}</span><span class="ac-text">${o.line}</span>
        <span class="ac-foot"><span class="ac-who">${o.who || ''}</span><span class="ac-much">${o.cost ? `<span class="rt-cost">${o.cost}</span>` : ''}</span></span></button>`;
    const q = card({ name: 'A new chair at the table', line: 'Which craft sits in it?', who: `${ork}<span>the Orkmaster</span>`,
      rune: '<span class="ork-chair is-empty rt-chair-mini" aria-hidden="true"></span>' }, 'ac-q asks', '<span class="ork-sign question is-alert" aria-hidden="true"></span>');
    const cards = CRAFTS.map((c) => card({ ...c, rune: c.star ? '<span class="rt-star" title="The Orkmaster\'s pick">★</span>' : '', who: c.star ? `${ork}<span>its pick</span>` : '' }, c.star ? 'is-pick' : '', img(c.head)));
    const stage = document.createElement('div');
    stage.className = 'ac-stage';
    stage.innerHTML = `<div class="ac-qbox">${q}</div><div class="ac-hand"><div class="ac-row">${cards.join('')}
      <div class="ac-acts"><button type="button" class="ork-btn">Put it back</button></div></div></div>`;
    document.body.append(stage);
    if (hand) {
      const qb = $('.ac-qbox', stage), hr = $('.ac-hand', stage);
      const x = plus ? plus.right + 28 : hand.left + 200;
      qb.style.left = `${x}px`; qb.style.top = `${hand.top - 202 - 18}px`;
      hr.style.left = `${x}px`; hr.style.top = `${hand.top + 8}px`;
    }
    document.body.classList.add('ac-on');
  }

  // ---- the pick: the backpack opens on that craft's chair, its heroes on the rug, the star on its default -------
  if (mode === 'pack') {
    const rel = $('.table-tabcell[data-cell="release"]');
    if (rel && !$('.table-tabcell[data-cell="marketing"]')) {
      const cell = rel.cloneNode(true);
      cell.dataset.cell = 'marketing';
      cell.classList.add('is-open', 'rt-new');
      const tab = $('.table-tab', cell);
      tab.dataset.tab = 'marketing'; tab.setAttribute('aria-selected', 'true'); tab.removeAttribute('id');
      const h = $('img.ork-race__head', cell);
      if (h) { h.src = `${RACES}fairy-elder.png`; h.srcset = `${RACES}fairy-elder@2x.png 2x`; }
      const main = $('.table-tab__main', cell); if (main) main.textContent = 'Marketing';
      const marks = $('.table-tab__marks', cell); if (marks) marks.innerHTML = '<span class="rt-new-word">new</span>';
      $('.table-tabs__end')?.prepend(cell);   // where the chair was: the new chair is now a tab, before the backpack
    }
    document.querySelectorAll('.col-head__tab, .table-tab:not([data-tab="marketing"])').forEach((t) => t.setAttribute('aria-selected', 'false'));
    const name = $('.stall-merchant__role'); if (name) name.textContent = "Marketing's heroes";
    const rug = $('.stall-rug');
    if (rug) {
      rug.dataset.rug = 'marketing';
      const ware = (o) => `<div class="rt-ware"><button type="button" class="ork-card ac-card ${o.star ? 'is-pick' : ''}">
          <span class="ac-top"><span class="ac-rune"></span><span class="ac-kind">${img('fairy-elder')}</span></span>
          <span class="ac-name">${o.name}</span><span class="ac-text">${o.line}</span>
          <span class="ac-foot"><span class="ac-who">${o.star ? `<span class="rt-star">★</span><span>the default</span>` : ''}</span></span></button>
          <span class="rt-plate">${o.price}</span></div>`;
      rug.innerHTML = `<div class="rt-wares">${ware({ name: 'Growth Hack Gnome', line: 'AARRR: acquire → activate → retain', price: '+9% a week · in your hand', star: true })}
        ${ware({ name: 'Store Gnome', line: 'The store page first: title → shots → test', price: '+6% a week' })}</div>`;
    }
  }

  // ---- the leather and its buckles round the table while the backpack is open ---------------------------------
  const pane = $('.table-pane.ork-table');
  pane?.querySelectorAll('.rt-buckle').forEach((b) => b.remove());
  if (pane && pane.dataset.stall === 'open') {
    for (const at of [22, 78]) pane.insertAdjacentHTML('beforeend', `<span class="rt-buckle" style="left:${at}%" aria-hidden="true"></span>`);
  }
  return mode;
}
