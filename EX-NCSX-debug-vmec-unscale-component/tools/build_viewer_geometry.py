"""Export the NCSX input geometry for the static Three.js viewer.

Run with the HINT-debug 2.3.0 package installed. The wout file is used only
to build the lightweight LCFS mesh; it is not copied into the website.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

from hint_debug.preprocess.coils import CoilSet


EXPECTED_WOUT_SHA256 = "f479637de1aa77cba5a58c679fa62deced67864ab6ed493bacf4916492ebec25"
EXPECTED_COILS_SHA256 = "60373fec15c70b0b2ea4a7c25f20a4ceb749abbe9ecd55bb09f1c21d67935c2e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lcfs_mesh(path: Path) -> dict:
    with Dataset(path) as dataset:
        if int(dataset.variables["lasym__logical__"][...].item()) != 0:
            raise ValueError("this NCSX viewer expects a stellarator-symmetric VMEC equilibrium")
        nfp = int(dataset.variables["nfp"][...].item())
        xm = np.asarray(dataset.variables["xm"][:], dtype=float)
        xn = np.asarray(dataset.variables["xn"][:], dtype=float)
        rmnc = np.asarray(dataset.variables["rmnc"][-1, :], dtype=float)
        zmns = np.asarray(dataset.variables["zmns"][-1, :], dtype=float)

    nphi, ntheta = 180, 96
    phi = np.arange(nphi) * (2.0 * np.pi / nphi)
    theta = np.arange(ntheta) * (2.0 * np.pi / ntheta)
    angle = theta[None, :, None] * xm[None, None, :] - phi[:, None, None] * xn[None, None, :]
    radius = np.einsum("ptm,m->pt", np.cos(angle), rmnc)
    height = np.einsum("ptm,m->pt", np.sin(angle), zmns)
    xyz = np.stack((radius * np.cos(phi[:, None]), radius * np.sin(phi[:, None]), height), axis=-1)
    if nfp != 3 or not np.all(np.isfinite(xyz)) or np.min(radius) <= 0.0:
        raise ValueError("invalid NCSX LCFS reconstruction")
    return {
        "nfp": nfp,
        "nphi": nphi,
        "ntheta": ntheta,
        "xyz": np.round(xyz.ravel(), 6).tolist(),
        "radius_range_m": [float(np.min(radius)), float(np.max(radius))],
        "height_range_m": [float(np.min(height)), float(np.max(height))],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wout", type=Path, required=True)
    parser.add_argument("--coils", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if sha256(args.wout) != EXPECTED_WOUT_SHA256:
        raise ValueError("wout SHA-256 differs from the equilibrium used in this published run")
    if sha256(args.coils) != EXPECTED_COILS_SHA256:
        raise ValueError("coil SHA-256 differs from the coils used in this published run")
    coil_set = CoilSet.read(args.coils)
    if coil_set.nfp != 3 or not coil_set.stellarator_symmetric or len(coil_set.representatives) != 27:
        raise ValueError("unexpected NCSX representative coil ensemble")
    expanded = coil_set.expanded()
    if len(expanded) != 78:
        raise ValueError("NCSX symmetry expansion did not produce 78 physical coils")
    coils = [
        {
            "name": coil.name,
            "current_a": float(coil.current_a),
            "xyz": np.round(coil.points_m.ravel(), 7).tolist(),
        }
        for coil in expanded
    ]
    data = {
        "provenance": {
            "equilibrium_sha256": EXPECTED_WOUT_SHA256,
            "coils": "inputs/ncsx_coils.txt",
            "coils_sha256": EXPECTED_COILS_SHA256,
            "surface": "Initial VMEC s=1, Fourier reconstruction over three full field periods",
            "coil_geometry": "27 input representatives expanded by HINT CoilSet to 78 physical loops",
            "coil_current": "Signed total current in A per loop; color uses absolute current",
        },
        "surface": lcfs_mesh(args.wout),
        "coils": coils,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"{args.output}: {len(coils)} coils, {data['surface']['nphi']} toroidal sections")


if __name__ == "__main__":
    main()
