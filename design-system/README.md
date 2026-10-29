# Orkboard's design system

- `orkui/` is a copy of [orkUI](https://github.com/orkCraft/orkUI)'s `office` look, stamped in `orkui/ORKUI.json` (its
  version, commit and every file's hash). Never edit it here: change orkUI, then copy it over with
  `python -m orkboard.design.orkui <a checkout of orkUI>` (docs/specs/40-design-system.md §2).
- `logo/orkboard/` is Orkboard's mark, the Orkmaster's crowned ork head, made from orkUI's `races/peon-crown@2x.png` by
  whole numbers only (`python -m orkboard.design.mark`, Pillow, a dev tool): `mark.svg`, `favicon.ico`, the phone's and
  the Dock's icons. `logo/` itself is the ork mark and the favicon Orkline keeps. Marks, not licensed with the code
  (`NOTICE`).
