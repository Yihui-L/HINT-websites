# HINT Public Websites

This repository contains only the public static websites approved for publication.
The original HINT source and NCSX archive repositories remain private.

- [HINT program and user manual](https://yihui-l.github.io/HINT-websites/manual/)
- [NCSX step 100 results](https://yihui-l.github.io/HINT-websites/highbeta_vmec_unscale/Documents/)

## Published Content

- `manual/`: model, numerical methods, inputs, outputs, acceleration, workflow,
  static assets and documented examples for HINT-debug 0.8.8 / HINT-wall 0.15.8.
- `highbeta_vmec_unscale/`: selected result website, 84 original PNGs, three TOML
  files, wall text and archive explanations for the NCSX step 100 result.
- `index.html`: redirects to the manual, which links to the result website.

Solver source, source repository history, credentials, wout, mgrid, computation
NetCDF files and the historical `startup_zero` case are not published here.
Links to the private repositories require separate GitHub access.

The numerical result is an archive stopped at a requested iteration count, not
a claim that equilibrium convergence has been demonstrated.

## Updating

Edit and validate the canonical `Documents/` files in the original private
repositories. Use their `Documents/tools/export_site.py` scripts to export only
approved static files into empty staging directories. Synchronize the manual
into `manual/` and the selected result into `highbeta_vmec_unscale/`; preserve
this root README, redirect and `.nojekyll`. Review the diff before pushing.
Do not merge or push either private repository's history into this repository.

GitHub Pages serves `main` at `/` with HTTPS enforced. Updates to this repository
automatically trigger deployment; private source changes alone do not publish.
