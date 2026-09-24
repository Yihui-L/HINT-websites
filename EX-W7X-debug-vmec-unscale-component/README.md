# W7-X EIM / HINT-debug case

[Open the interactive site](https://yihui-l.github.io/HINT-websites/EX-W7X-debug-vmec-unscale-component/)

The [geometry page](https://yihui-l.github.io/HINT-websites/EX-W7X-debug-vmec-unscale-component/)
displays the 70 W7-X coil centrelines and the `s=1` surface from the
**reproduced** free-boundary VMEC wout. The separate
[results page](https://yihui-l.github.io/HINT-websites/EX-W7X-debug-vmec-unscale-component/results.html)
shows selected figures from the completed HINT-debug run; the
[full figure catalog](https://yihui-l.github.io/HINT-websites/EX-W7X-debug-vmec-unscale-component/gallery.html)
contains every generated PNG, grouped by Poincare plots, spatial sections,
profiles and convergence diagnostics. The companion
[figure and metric guide](https://yihui-l.github.io/HINT-websites/EX-W7X-debug-vmec-unscale-component/figure-guide.html)
defines the plotted quantities and their limits. The calculation finished all
50 requested outer iterations, but the force residual, divergence and kinetic
energy increased during the later iterations: **completion is not convergence**.
The geometry viewer does not calculate or display `Bn`.

## HINT output and plots

- Version HINT-debug 2.3.0; `initial`, `start_point="vmec"`, `scale_after=false`,
  component magnetic interpolation, 144 x 144 x 144 cylindrical grid, GPU/JAX.
- 50 outer iterations, 1000 Step-B inner steps each. The output NetCDF has 51
  continuous complete records for outer 0..50 and the run log has `finished`.
- Total wall-clock time: 15,564.0 s (4 h 19 min 24 s). Force RMS grew from
  0.00392 at step 5 to 0.07214 at step 50; normalized divergence RMS grew
  from 0.00754 to 0.09908 over the same interval. The end state must not be
  described as a converged equilibrium. There is also a sharp force-RMS jump
  from 0.00466 at step 9 to 0.05383 at step 10; its cause is not established.
- Figures in `figures/` are generated from the saved run using the
  HINT-debug `HintPlots` API. `poincare_step000.png` traces the saved
  pre-iteration total field; `poincare_step050.png` traces the final saved
  field. Both use one set of launch points at phi=0, 300 full toroidal turns,
  and 0/18/36-degree return sections. Initial VMEC surfaces are overlays, not
  return points.
- The full catalog follows the previous NCSX example's scope: every available
  2-D field variable at three toroidal planes; pressure, current, velocity,
  force and field profiles in s, rho, R, Z and phi; enclosed current and
  rotational-transform profiles; stored Step-B, AD and FD4 diagnostics;
  wall/plasma checkpoint reductions; and an independent final-interpolant
  divergence audit. A finite rotational-transform estimate without adequate
  trajectory or surface-resolution checks is marked unresolved, not accepted
  as an equilibrium rotational transform.
- `result_manifest.json` records hashes and dimensions for all 99 nonduplicate
  PNG figures. `results/` contains the concise run summary, initialization
  and final-interpolant diagnostics, per-record volume statistics, rotational
  transform data and Poincare tracing metadata.
  The 6.2 GB HINT NetCDF output is deliberately not in GitHub.
- The Step-B `divb_*` normalization, selected component-interpolant JAX AD,
  and saved-grid FD4 divergence are distinct metrics; none is a direct
  replacement for the continuous initialization source-expression AD result.
  The final-interpolant audit is likewise a numerical derivative of the saved
  component interpolation, not an analytic divergence of the coil or plasma
  source field.

## Calculation inputs

- `main.toml`: HINT-debug 2.3.0, `initial`, `start_point="vmec"`,
  `scale_after=false`, component magnetic interpolation, GPU/JAX, 50 outer
  iterations and 1000 Step-B inner iterations per outer step.
- `inputs/wout_eim_demo_repro.nc` and `inputs/input.eim_demo_repro`:
  reproduced five-period free-boundary VMEC equilibrium and its input.
- `inputs/coils.w7x`: public MAKEGRID centreline source. The converted
  `inputs/coils_hint.txt` preserves all 70 explicit closed loops. For this
  reproduced `wout`, each HINT loop carries `-extcur[group] * turns[group]`:
  the 50 non-planar coils use -1,454,760 A-turns per model loop, while 20
  planar loops remain at zero. The displayed tube width is symbolic.
- `inputs/vessel.part`: sourced W7-X **physical plasma vessel** contours,
  full field period, source units centimetres and degrees. The HINT conversion
  is `inputs/wall_physical_vessel_half_period.txt`, using only the first
  half-period (21 cuts x 72 unique poloidal points). This is not a full CAD
  description of in-vessel plasma-facing components.

The physical-vessel source is [ORNL-Fusion/util-library at commit
803cec6](https://github.com/ORNL-Fusion/util-library/blob/803cec6866ddf4b39507f9640afa3d1af230f1d1/matlab/bfield_library_jdl/W7X/vessel.part).
The source geometry originates from the Max Planck Institute for Plasma
Physics; its [CAD page](https://www.ipp.mpg.de/5436741/cad_druck) states the
noncommercial-use and attribution conditions. The source `vessel.part` is
included solely for reproducing this research example, with attribution.

## Geometry checks

- The supplied full-period vessel is stellarator-symmetric to within
  0.011 mm at the corresponding sampled points.
- `wall.periodic_closure_rtol=2e-6` accepts the original source rounding;
  HINT then averages paired points only on the two symmetry-end cuts, changing
  their positions by no more than about 0.005 mm.
- At every one of the 21 half-period input cuts, the reconstructed VMEC LCFS
  lies inside the vessel polygon. The smallest *point-sampled* LCFS-to-vessel
  distance is 0.118 m; this is not a rigorous minimum over continuous
  surfaces.
- The vessel spans R = 4.29765-6.46617 m and Z = -1.28295-1.28295 m.
  The HINT R-Z rectangle spans R = 4.15-6.62 m and Z = -1.42-1.42 m,
  giving more than three exterior grid layers on every rectangular side.
- The site viewer reconstructs the complete toroidal LCFS from the outermost
  VMEC `rmnc` and `zmns` coefficients using
  `R=sum(rmnc*cos(m*theta-n*phi))` and
  `Z=sum(zmns*sin(m*theta-n*phi))`. It does not use HINT output.

`inputs/geometry_manifest.json` records the geometry and current checks.
`inputs/comparison.json` compares the reproduced equilibrium with the
archived demo reference; they are close but not byte-identical. In particular,
relative differences for profiles close to zero should not be mistaken for
large absolute currents.

`inputs/orientation_check.json` records why the HINT current direction differs
from the public centreline file's positive MAKEGRID reference: the regenerated
RAW mgrid has about +2.43 T near the axis, while this signed VMEC wout has
`b0=-2.29` T. At 64 LCFS points, reversing only the coil-field sign reduces
the vector field jump from 1.985 to 0.0155 relative to the VMEC field norm.
The original geometry and wout are retained unchanged. This is a case-specific
alignment, not a reconstruction of the unavailable archived demo mgrid or a
claim about W7-X engineering current polarity. Residual LCFS mismatch is
diagnosed, not artificially smoothed.

## Site implementation

The viewer is a static GitHub Pages application. `assets/geometry.json` is
generated by `.hint-tools/W7X_EIM_demo_reproduction/export_viewer_geometry.py`
in the local working tree. It stores the exact converted coil-centreline
samples and a Fourier-reconstructed surface grid. Three.js 0.180.0 and
Lucide 0.468.0 are vendored in `vendor/` with their licence files, so the
interactive page needs no external JavaScript service.
