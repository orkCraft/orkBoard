() => { (() => {
  // each lane wears its leader's head as a watermark, an empty lane says whose it is, the hand's lanes take their party's colour
  const names = {};
  for (const t of document.querySelectorAll('.table-tab[data-tab]')) {
    const img = t.querySelector('img.ork-race__head');
    const nm = (t.querySelector('.table-tab__main')?.textContent || t.dataset.tab).trim();
    names[t.dataset.tab] = nm;
    for (const lane of document.querySelectorAll(`.table-lane[data-party="${t.dataset.tab}"]`)) {
      if (img) lane.style.setProperty('--lane-head', `url("${img.currentSrc || img.src}")`);
      const empty = lane.getBoundingClientRect().width >= 140 && !lane.querySelector('.ork-card, .table-goal, .ork-card-place');
      if (empty) lane.dataset.empty = `${nm.charAt(0) + nm.slice(1).toLowerCase()} is free\nthrow a goal here or @${nm.charAt(0) + nm.slice(1).toLowerCase()}`;
      else delete lane.dataset.empty;
    }
  }
  const lanes = [...document.querySelectorAll('.table-lane[data-party]')].map(l => [l.getBoundingClientRect().x, l.dataset.party]);
  for (const h of document.querySelectorAll('.hand-lane')) {
    const x = h.getBoundingClientRect().x;
    const hit = lanes.find(([lx]) => Math.abs(lx - x) < 4);
    if (hit) h.dataset.party = hit[1];
  }
})(); (() => {
  // the table's dither: on the inner side of each band's edge, a 2 px checker in the next band's colour
  const pane = document.querySelector('.table-pane.ork-table');
  if (!pane || pane.querySelector('.rt-dither')) return;
  const stops = [24, 40, 56, 74], w = 4;
  stops.forEach((at, i) => {
    const d = document.createElement('div');
    d.className = 'rt-dither';
    const ring = `radial-gradient(var(--rings), transparent 0 ${at - w}%, #000 ${at - w}% ${at}%, transparent ${at}%)`;
    d.style.background = `repeating-conic-gradient(var(--b${i + 2}) 0 25%, transparent 0 50%) 0 0 / 4px 4px`;
    d.style.webkitMask = ring; d.style.mask = ring;
    pane.prepend(d);
  });
})(); }