# W7-X EIM input provenance

This directory contains the public W7-X coil geometry, the reproduced
free-boundary VMEC input and wout, and the HINT-debug text inputs.

| File | Meaning |
|---|---|
| `coils.w7x` | Public MAKEGRID filament centrelines, 70 physical coils. |
| `coils_hint.txt` | Same explicit closed centrelines, converted to HINT_COILS 1. Each current is `extcur * turns` in equivalent ampere-turns. |
| `input.eim_demo_repro` | VMEC free-boundary input reconstructed from the archived W7-X EIM wout. |
| `wout_eim_demo_repro.nc` | Converged reproduced free-boundary equilibrium, not a HINT result. |
| `vessel.part` | ORNL-Fusion W7-X physical plasma-vessel contours; source data are centimetres and degrees. |
| `wall_physical_vessel_half_period.txt` | HINT_WALL 1 conversion of the first half-period of `vessel.part`, metres and radians. |
| `comparison.json` | Reproduced versus archived VMEC-equilibrium comparison. |
| `geometry_manifest.json` | Coil-current and vessel-geometry checks. |

The vessel source is [ORNL-Fusion/util-library, commit 803cec6](https://github.com/ORNL-Fusion/util-library/blob/803cec6866ddf4b39507f9640afa3d1af230f1d1/matlab/bfield_library_jdl/W7X/vessel.part).
Its accompanying [reader](https://github.com/ORNL-Fusion/util-library/blob/803cec6866ddf4b39507f9640afa3d1af230f1d1/matlab/bfield_library_jdl/W7X/load_W7X_vessel.m)
specifies one complete 72-degree field period in centimetres and degrees.
The first 21 inclusive cuts (0-36 degrees) are retained without changing
their R-Z coordinates, except unit conversion and removing each duplicate
poloidal endpoint. The original full-period pair differs from its stellarator
reflection by at most 0.011 mm in the sampled points. The W7-X vessel
geometry originates from the Max Planck Institute for Plasma Physics; source
attribution and noncommercial use conditions are described on the
[IPP CAD page](https://www.ipp.mpg.de/5436741/cad_druck).

This is the *physical plasma vessel*, not an exhaustive model of every
in-vessel plasma-facing component or divertor target. It should not be
interpreted as an exact engineering first-wall contact model. The VMEC LCFS
was found inside every supplied half-period vessel cut; the smallest sampled
LCFS-to-wall-point distance was 0.118 m. The chosen R-Z rectangle fully
contains the source vessel with more than three exterior grid layers.
