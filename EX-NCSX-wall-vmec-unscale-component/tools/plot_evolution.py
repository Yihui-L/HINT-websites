"""Plot completed NCSX-wall history and audit raw saved-field wall traces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np

from hint_wall.solver.wall import WallGhostMap
from hint_wall.storage import UnifiedStore


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def wall_trace_setup(mapping: WallGhostMap):
    ghosts = mapping.ghosts
    ghost_index = tuple(ghosts.T)
    sources = mapping.source[ghost_index]
    source_index = tuple(sources.T)
    half = mapping.grid.ntor // 2
    plane_delta = (sources[:, 2] - ghosts[:, 2] + half) % mapping.grid.ntor - half
    angle = plane_delta * mapping.grid.dphi
    boundary_index = tuple(mapping.boundary.T)

    def trace(field: np.ndarray) -> np.ndarray:
        values = []
        if ghosts.size:
            source = field[source_index]
            cosine, sine = np.cos(angle), np.sin(angle)
            rotated = np.stack(
                (
                    cosine * source[:, 0] - sine * source[:, 1],
                    sine * source[:, 0] + cosine * source[:, 1],
                    source[:, 2],
                ),
                axis=-1,
            )
            ratio = mapping.ratio[ghost_index][:, None]
            wall_field = (ratio * rotated + field[ghost_index]) / (1.0 + ratio)
            values.append(np.einsum("ij,ij->i", wall_field, mapping.normal[ghost_index]))
        if mapping.boundary.size:
            values.append(
                np.einsum(
                    "ij,ij->i", field[boundary_index], mapping.wall.normal[boundary_index]
                )
            )
        return np.concatenate(values)

    return trace


def draw(summary: dict, destination: Path) -> None:
    rows = summary["records"]
    finished = summary["completed_outer"]
    x = np.asarray([row["outer_step"] for row in rows], dtype=int)
    y = np.asarray([row["outer_step"] for row in finished], dtype=int)
    fig, axes = plt.subplots(7, 1, figsize=(10, 18), layout="constrained", dpi=180)

    def series(axis, steps, values, label, color, *, logarithmic=False):
        axis.plot(steps, values, "o-", ms=3.5, lw=1.6, color=color, label=label)
        if logarithmic:
            axis.set_yscale("log")
        axis.legend(loc="best", fontsize=8, frameon=False)

    series(axes[0], y, [row["force_rms"] for row in finished], "Force RMS", "#af442c", logarithmic=True)
    series(axes[0], y, [row["force_max"] for row in finished], "Force maximum", "#d18b24", logarithmic=True)
    axes[0].set_ylabel("Normalized force")

    series(axes[1], y, [row["kinetic_energy"] for row in finished], "Kinetic energy", "#147c7d", logarithmic=True)
    series(axes[1], y, [row["response_magnetic_energy"] for row in finished], "Response magnetic energy", "#4365a5", logarithmic=True)
    axes[1].set_ylabel("Normalized energy")

    series(axes[2], x, [row["field_max_t"] for row in rows], "Total |B| maximum", "#b44934")
    series(axes[2], x, [row["response_max_t"] for row in rows], "Response |B1| maximum", "#355d9c")
    axes[2].set_ylabel("Magnetic field [T]")

    series(axes[3], x, [row["speed_max_m_s"] for row in rows], "Speed maximum", "#138574")
    axes[3].set_ylabel("Speed [m/s]")

    series(axes[4], y, [row["ad_response_mean_abs_t_m"] for row in finished], "Component-interpolant AD", "#aa5633", logarithmic=True)
    series(axes[4], y, [row["fd4_response_mean_abs_t_m"] for row in finished], "HINT-grid FD4", "#347f90", logarithmic=True)
    axes[4].set_ylabel("Mean |div B1| [T/m]")

    positive_error = np.asarray([row["frozen_bn_error_max_t"] for row in rows], dtype=float)
    positive_error[positive_error <= 0.0] = np.nan
    series(axes[5], x, positive_error, "Max |B1n - B1n(initial)|", "#76589b", logarithmic=True)
    axes[5].set_ylabel("Wall B1n error [T]")

    series(axes[6], x, [row["pressure_max_pa"] for row in rows], "Pressure maximum", "#426a37")
    axes[6].set_ylabel("Pressure [Pa]")

    for axis in axes:
        axis.axvline(13, ls="--", lw=1.2, color="#8b3333", alpha=0.8)
        axis.set_xlim(-0.25, 13.5)
        axis.set_xticks(np.arange(0, 14, 2))
        axis.set_xlabel("Completed outer iteration")
        axis.grid(True, alpha=0.2)
    axes[0].annotate("Step 13 failed", (13, 1), xycoords=("data", "axes fraction"),
                     xytext=(-4, -4), textcoords="offset points", ha="right", va="top", fontsize=8)
    fig.suptitle("NCSX HINT-wall 2.3.2 | completed iterations 0-12", fontsize=15)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--progress", required=True, type=Path)
    parser.add_argument("--figure", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    events = [json.loads(line) for line in args.progress.read_text().splitlines() if line]
    completed = [item for item in events if item.get("event") == "outer_complete"]
    failed = [item for item in events if item.get("event") == "failed"]
    if [item["diagnostic"]["outer_step"] for item in completed] != list(range(1, 13)):
        raise ValueError("Expected exactly 12 completed outer iterations")
    if len(failed) != 1 or "RK-stage divergence constraint failed" not in failed[0]["message"]:
        raise ValueError("The recorded failure does not match this case")

    prepared, _ = UnifiedStore(args.input).load_prepared()
    trace = wall_trace_setup(WallGhostMap.build(prepared.grid, prepared.wall))
    vacuum = np.asarray(prepared.vacuum_field_t, dtype=np.float64)
    inside = prepared.wall.mask
    records = []
    with nc.Dataset(args.input) as dataset:
        eq = dataset["equilibrium"]
        if len(eq.dimensions["time"]) != 13 or not np.all(eq["record_complete"][:] == 1):
            raise ValueError("Expected complete NetCDF records 0 through 12")
        initial = np.asarray(eq["B"][0], dtype=np.float64) - vacuum
        reference_bn = trace(initial)
        initial_bn_max = float(np.max(np.abs(reference_bn)))
        for index in range(13):
            step = int(eq["outer_step"][index])
            if step != index:
                raise ValueError("Unexpected checkpoint order")
            field = np.asarray(eq["B"][index], dtype=np.float64)
            velocity = np.asarray(eq["velocity"][index], dtype=np.float64)
            pressure = np.asarray(eq["pressure"][index], dtype=np.float64)
            response = field - vacuum
            bn = trace(response)
            error = bn - reference_bn
            records.append(
                dict(
                    outer_step=step,
                    time=float(eq["time"][index]),
                    field_max_t=float(np.max(np.linalg.norm(field[inside], axis=-1))),
                    response_max_t=float(np.max(np.linalg.norm(response[inside], axis=-1))),
                    speed_max_m_s=float(np.max(np.linalg.norm(velocity[inside], axis=-1))),
                    pressure_max_pa=float(np.max(pressure[inside])),
                    response_bn_max_t=float(np.max(np.abs(bn))),
                    frozen_bn_error_max_t=float(np.max(np.abs(error))),
                    frozen_bn_error_rms_t=float(np.sqrt(np.mean(error**2))),
                )
            )

    for event in events:
        if event.get("event") != "boundary_check" or event.get("outer_step") not in (0, 1, 2):
            continue
        step = event["outer_step"]
        if len(reference_bn) != event["sample_count"]:
            raise ValueError("Wall sample count disagrees with run-time trace")
        np.testing.assert_allclose(initial_bn_max, event["initial_response_bn_max_t"], atol=1e-12)
        np.testing.assert_allclose(
            records[step]["frozen_bn_error_max_t"], event["frozen_bn_error_max_t"], atol=1e-14
        )

    history = []
    for event in completed:
        diagnostic = event["diagnostic"]
        magnetic = event["magnetic_statistics"]
        history.append(
            dict(
                outer_step=diagnostic["outer_step"],
                elapsed_s=event["outer_elapsed_s"],
                force_rms=diagnostic["force_rms"],
                force_max=diagnostic["force_max"],
                kinetic_energy=diagnostic["kinetic_energy"],
                response_magnetic_energy=diagnostic["response_magnetic_energy"],
                ad_response_mean_abs_t_m=magnetic["divb_ad_response_mean_abs"],
                fd4_response_mean_abs_t_m=magnetic["divb_fd4_response_mean_abs"],
            )
        )
    summary = dict(
        title="NCSX HINT-wall 2.3.2 VMEC/unscale/component, incomplete run",
        source_commit="8609e184e1d7b8bcabab662ddf1fb170243ded60",
        input_nc_sha256=file_hash(args.input),
        complete_records=13,
        completed_outer_count=12,
        failure=failed[0],
        wall_sample_count=len(reference_bn),
        initial_response_bn_max_t=initial_bn_max,
        max_frozen_bn_error_t=max(row["frozen_bn_error_max_t"] for row in records),
        wall_trace_definition="Raw saved response field; ghost/source image interpolation with cylindrical rotation; no boundary reapplication",
        records=records,
        completed_outer=history,
    )
    draw(summary, args.figure)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: summary[key] for key in ("complete_records", "completed_outer_count", "wall_sample_count", "initial_response_bn_max_t", "max_frozen_bn_error_t")}, indent=2))


if __name__ == "__main__":
    main()
