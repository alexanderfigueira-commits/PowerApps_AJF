# Canvas app screens to Figma (wireframe generator)

Reads an unpacked `.msapp` (the `Controls/*.json` files) and produces, for every screen and scenario, a flat list of draw operations
(position, size, text, colours, stacking order) that `render_tpl.js` draws in Figma with the Plugin API (`use_figma`), using the token
variables, text styles and the Button / Input / Checkbox components of the design file.

1. `extract.py`: small Power Fx evaluator (If, And, Or, Not, Coalesce, Max, Min, Switch, `in`, RGBA, ColorFade, ...) that resolves X, Y, Width, Height,
   Visible, Text, Fill, Color, Size ... for a scenario (role, production type, status, flags). Unknown values get a safe default.
2. `run.py`: the scenario list (28 frames). Usage: `python3 run.py` after setting the path to the unpacked app in `sys.argv[1]` (default `../newV46`); writes `all.json`.
3. `compact.py`: compacts `all.json` into `comp.json` (colour palette per screen, short arrays).
4. `mk.py a b start`: builds the `use_figma` script for screens `a..b-1` (data embedded in `render_tpl.js`; a call is limited to 50,000 characters).

Limits: formulas the evaluator cannot resolve fall back to sample text or the first branch; pop-ups and the scrolled part of the long tab forms are shown only
for the scenarios listed in `run.py`; icons are drawn as lettered circles and images as grey placeholders; emoji are removed from labels.
The Figma file ids used by `render_tpl.js` (`5:12`, `5:21`, `5:29`) are the Button, Input and Checkbox component sets of the file in `docs/figma-design-system-rules.md`.
