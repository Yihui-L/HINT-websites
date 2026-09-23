"""Case-only final-checkpoint Poincare plotting; does not modify HINT sources."""

import json
import os
from pathlib import Path
import time

os.environ.update(MPLBACKEND="Agg", JAX_ENABLE_X64="true",
                  XLA_PYTHON_CLIENT_PREALLOCATE="false")
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq
from hint_debug.config import HMAGConfig
from hint_debug.postprocess.fieldline import MagneticGeometry
from hint_debug_plotting import HintPlots

import sys
STEP = int(sys.argv[1])
assert STEP in (0, 70)
CASE = Path("/root/LYH-HINT/cases/ncsx-debug-zero")
RUN = (CASE / "run").resolve()
assert RUN.name == 'ncsx-debug-zero-b-2.3.0-component-20260921T094915Z'
OUT = RUN / ("initial-poincare-component" if STEP == 0 else "final-poincare-step070-wall-coverage")
OUT.mkdir(exist_ok=True)
START = time.perf_counter()


def report(event, **data):
    data = dict(event=event, elapsed_s=time.perf_counter() - START, **data)
    line = json.dumps(data)
    print(line, flush=True)
    with (OUT / "progress.jsonl").open("a") as handle:
        handle.write(line + "\n")


plots = HintPlots(
    RUN / "hint_debug_ncsx_zero.nc", outer_step=STEP,
    wout=CASE / "inputs/wout_ncsx_c09r00_free_nonnegative.nc",
    backend="gpu", engine="jax",
)
assert plots.state.outer_step == STEP
assert plots.backend.magnetic_interpolation == "component"
grid = plots.grid
assert grid.nfp == 3
sampler = plots.magnetic_sampler()
if STEP == 0:
    assert np.max(np.abs(plots.state.total_field - plots.prepared.vacuum_field_t)) < 1e-12
report("loaded", outer_step=int(plots.state.outer_step), nfp=int(grid.nfp),
       interpolation=plots.backend.magnetic_interpolation)


def outboard(s):
    if s == 0:
        r, z = plots.geometry.evaluate(0, 0, 0)
        assert abs(z) < 1e-8
        return float(r)
    theta = np.linspace(0, 2 * np.pi, 513)
    _, z = plots.geometry.evaluate_many(np.full_like(theta, s), theta, 0)
    roots = list(theta[np.abs(z) < 1e-12])
    for i in np.flatnonzero(z[:-1] * z[1:] < 0):
        roots.append(brentq(lambda t: plots.geometry.evaluate(s, t, 0)[1],
                            theta[i], theta[i + 1]))
    return max(float(plots.geometry.evaluate(s, t, 0)[0]) for t in roots)


radii = [outboard(s) for s in np.linspace(0, 1, 128)]
trial = np.linspace(radii[-1], grid.r[-1], 2049)
inside = sampler.wall.inside_many(np.column_stack((trial, trial * 0, trial * 0)))
exits = np.flatnonzero(~inside)
assert len(exits) and exits[0] > 0
radii.extend(np.linspace(radii[-1], trial[exits[0] - 1], 12)[1:-1])
radial_seeds = np.column_stack((radii, np.zeros(len(radii))))

# Cell-centered two-dimensional launches cover the wall interior, not only Z=0.
r = grid.r[0] + (np.arange(48) + 0.5) / 48 * (grid.r[-1] - grid.r[0])
z = grid.z[0] + (np.arange(64) + 0.5) / 64 * (grid.z[-1] - grid.z[0])
rr, zz = np.meshgrid(r, z, indexing="ij")
mesh = np.column_stack((rr.ravel(), zz.ravel()))
inside = sampler.wall.inside_many(np.column_stack((mesh, np.zeros(len(mesh)))))
mesh = mesh[inside]
if STEP == 0:
    mesh = np.empty((0, 2))
seeds = np.vstack((radial_seeds, mesh))
_, indices = np.unique(np.round(seeds, 11), axis=0, return_index=True)
seeds = seeds[np.sort(indices)]
active = np.column_stack((seeds, np.zeros(len(seeds))))
_, _, valid = sampler.sample_b_many(active)
invalid = int(np.count_nonzero(~valid))
seeds, active = seeds[valid], active[valid]
nseed = len(seeds)
np.save(OUT / "launch_seeds_rz.npy", seeds)
report("seeds", total=nseed, radial=len(radial_seeds), wall_mesh=len(mesh), rejected=invalid)

turns = 500
cycles = turns * grid.nfp
rows = [dict(phi=float(phi), points=np.full((cycles, nseed, 3), np.nan),
             status=np.ones((cycles, nseed), dtype=np.int32), seeds=seeds.copy(),
             field_source="hint", turns=turns, interpolation="component",
             max_step_phi=grid.period / 128)
        for phi in (0, grid.period / 4, grid.period / 2)]
geometry = MagneticGeometry(
    sampler, HMAGConfig(relative_tolerance=1e-8, absolute_tolerance=1e-10), plots.backend,
)
status = np.zeros(nseed, dtype=np.int32)

# Exact quarter-period endpoints yield all three planes from one set of orbits.
# Chunk 64 endpoints per device call to avoid per-plane host synchronization.
for first in range(0, 4 * cycles, 64):
    count_quarters = min(64, 4 * cycles - first)
    path, flags, _ = geometry.paths(
        active, grid.period / 128, count_quarters * 32,
        initial_status=status, stride=32,
    )
    for local in range(1, count_quarters + 1):
        quarter = first + local
        plane = {0: 0, 1: 1, 2: 2}.get(quarter % 4)
        if plane is None:
            continue
        cycle = (quarter - 1) // 4
        rows[plane]["points"][cycle] = np.where(
            (flags[local] == 0)[:, None], path[local], np.nan,
        )
        rows[plane]["status"][cycle] = flags[local]
    active, status = path[-1], flags[-1]
    report("tracing", full_turns=(first + count_quarters) / (4 * grid.nfp),
           surviving=int(np.count_nonzero(status == 0)),
           status_counts={str(i): int(np.count_nonzero(status == i)) for i in range(4)})
    if not np.any(status == 0):
        break

plots.check_stable()
np.savez_compressed(OUT / "crossings.npz", **{
    f"section_{i}_{key}": row[key]
    for i, row in enumerate(rows) for key in ("points", "status", "seeds")
})
metadata = dict(
    source=str(plots.path), outer_step=STEP, turns=turns, nfp=int(grid.nfp),
    launch_phi_rad=0, seeds=nseed, radial_seeds=len(radial_seeds),
    wall_mesh_seeds=len(mesh), rejected_seeds=invalid,
    interpolation="component", backend="gpu", engine="jax",
    max_step_phi=float(grid.period / 128), rtol=1e-8, atol=1e-10,
    elapsed_tracing_s=time.perf_counter() - START,
    sections=[dict(phi_degrees=float(np.degrees(row["phi"])),
                   points=int(np.count_nonzero(row["status"] == 0))) for row in rows],
    final_status_counts={str(i): int(np.count_nonzero(status == i)) for i in range(4)},
)
(OUT / "plot_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
report("tracing_complete", sections=metadata["sections"])

outputs = []
for selected, stem in [(rows, "final_poincare_wall_coverage")] + [
    ([row], f"final_poincare_phi_{round(np.degrees(row['phi'])):03d}") for row in rows
]:
    if STEP == 0:
        stem = stem.replace("final_poincare_wall_coverage", "initial_poincare_domain").replace("final_poincare_phi", "initial_poincare_domain_phi")
    result = plots.poincare(data=selected, marker_size=0.05, dpi=320,
                            vmec_surfaces=(0, 0.25, 0.5, 0.75, 1))
    result.figure.set_size_inches(8.8, 17.8 if len(selected) == 3 else 7.7)
    result.figure.suptitle(
        f"NCSX | outer {STEP} | {'initial vacuum field (B1=0)' if STEP == 0 else 'final total magnetic field'}\n"
        f"{nseed} wall-interior launches at phi=0 | 500 full toroidal turns\n"
        "Component interpolation | initial VMEC surfaces for reference", fontsize=11,
    )
    for axis in result.axes:
        for artist in axis.collections:
            artist.set_rasterized(False)
        axis.set_xlim(float(grid.r[0]), float(grid.r[-1]))
        axis.set_ylim(float(grid.z[0]), float(grid.z[-1]))
        axis.tick_params(labelsize=10)
        axis.set_xlabel("R [m]", fontsize=11)
        axis.set_ylabel("Z [m]", fontsize=11)
    for suffix in ("png", "svg", "pdf"):
        path = result.save(OUT / f"{stem}.{suffix}", dpi=320)
        outputs.append(dict(file=str(path), size_bytes=path.stat().st_size))
        report("saved", **outputs[-1])
    plt.close(result.figure)
metadata["outputs"] = outputs
metadata["elapsed_total_s"] = time.perf_counter() - START
(OUT / "plot_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
report("complete", outputs=outputs)
