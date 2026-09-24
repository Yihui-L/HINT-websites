# W7-X EIM figure definitions

All figures are read-only postprocessing of the completed HINT-debug 2.3.0
calculation. Outer records 0 through 50 are complete. The final state is **not
force-balance converged**; a saved record or a field-line plot does not change
that assessment.

## Field lines

The initial and final Poincare figures trace the saved total field at outer
steps 0 and 50. The same 332 valid starting points are selected at phi = 0,
with radial seeds from initial VMEC s values and a wall-interior R-Z mesh.
Trajectories are followed for up to 300 full toroidal turns and sampled at
phi = 0, 18 and 36 degrees. The plotted VMEC curves are reference geometry,
not HINT return points. The solver's component magnetic interpolator is used.

## Spatial sections

The three planes correspond to the beginning, middle and end of one
stellarator-symmetric half-period. They display outer step 50 within the first
wall, with initial VMEC surfaces overlaid where the variable supports a
comparison. All field-variable names are taken from the HINT plotting API.
`s` is the evolving HINT label, not necessarily a toroidal-flux surface after
relaxation. `J_phi` is the pointwise response current density; it is not VMEC
`jcurv` or dI/ds.

The local relative force residual is
`|J_response x B_total - grad(p)| / max(|J_response x B_total|, |grad(p)|)`.
It is undefined when both denominator terms vanish. Absolute force residual
uses N/m^3. Signed and absolute divergence sections are spatial derivatives
of the **saved grid field** used by the plotting API; they are not the
initialization source expression's analytic divergence.

## Profiles and rotational transform

Profiles cover pressure, pointwise toroidal response current density, speed,
force residual, local relative force residual and total field strength against
the evolving s label, rho = sqrt(s), and the requested R, Z and phi cuts.
The R cut uses Z = 0; Z and phi cuts use R = 6.0 m. VMEC comparisons are shown
only for supported variables. Profiles binned in s are point statistics, not
rigorous flux-surface averages. Enclosed toroidal response current integrates
J_phi over the section below the selected s/rho threshold.

The initial-VMEC-s rotational-transform scan launches 191 seed positions per
plane strictly within 0 < s < 1, traces up to 512 field-period returns with
128 toroidal substeps per period, and checks consistency between the two
halves of the trace plus whether the return section is sufficiently resolved.
An unfilled point can have a finite winding estimate while failing one of
those checks; it is **not** evidence of a surviving invariant magnetic
surface. At phi = 0, 18 and 36 degrees, 30, 50 and 78 of 191 seeds pass both
checks, respectively. The plotted VMEC curve is the initial equilibrium
reference.

## Time histories and precision

The Step-B diagnostic curves use the solver's stored normalized quantities.
The JAX automatic-differentiation (AD) and FD4 curves describe the selected
saved component interpolant and the saved cylindrical grid field,
respectively. Neither should be confused with the continuous analytic source
field's divergence at initialization. The final precision comparison again
checks the **actual component interpolant** at wall-interior grid nodes and
off-grid wall-interior probes; it does not validate the analytic coil or plasma
source expression.

The [initialization diagnostics](initialization_diagnostics.json) separately
record JAX AD of the continuous source expressions. A classical pointwise
analytic divergence is not defined across a possible LCFS normal-field jump.
The exterior response source's analytic diagnostic was unavailable in this
run; no value is inferred for it.

Checkpoint curves recompute derived fields from every saved outer record.
Their wall and plasma statistics are weighted by R, the cylindrical cell-volume
factor on this uniform R-Z-phi grid; the plasma mask is `0 <= s < 1` within
the first wall. The velocity-change rate is a saved-step secant in converted
relaxation seconds, not a directly measured physical acceleration. Wall-clock
curves are computation times, not physical time.

See [`../result_manifest.json`](../result_manifest.json) for image dimensions,
SHA-256 checksums and source-run identification.
