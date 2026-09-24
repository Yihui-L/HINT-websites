# W7-X EIM figures

This directory contains all PNG figures produced from the completed
HINT-debug 2.3.0 run, outer records 0 through 50. The run completed but did
not converge to force balance. The visual catalog is
[`../gallery.html`](../gallery.html), and the numerical meaning of each group
is documented in [`../figure-guide.html`](../figure-guide.html).

- `poincare_step000*` and `poincare_step050*`: initial and final saved total
  fields. VMEC surfaces are reference geometry.
- `section_*_step050`: all 32 spatial variables exposed by the plotting API,
  each at 0, 18 and 36 degrees.
- `profile_*_step050`: pressure, current, velocity, field and force profiles,
  including initial-VMEC-s rotational-transform scans with resolution flags.
- `evolution_*` and `convergence_*`: stored Step-B diagnostics, checkpoint
  reductions, final-interpolant AD, grid FD4, and wall-clock timings. These
  names encode distinct numerical definitions.

The SHA-256 manifest is [`../result_manifest.json`](../result_manifest.json).
