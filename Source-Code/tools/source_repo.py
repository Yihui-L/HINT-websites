"""Locate the separate, access-controlled HINT source checkout."""

import os
from pathlib import Path


def locate_source(argument=None, *, required=True):
    configured = argument or os.environ.get("HINT_SOURCE_REPO")
    parent = Path(__file__).resolve().parents[3]
    candidates = [Path(configured).expanduser()] if configured else [
        parent / "HINT-docs", parent / "HINT-docs-sync",
    ]
    for path in candidates:
        if all((path / f"HINT-{variant}/pyproject.toml").is_file() for variant in ("debug", "wall")):
            return path.resolve()
    if required or configured:
        raise SystemExit("Provide --source-repo /path/to/HINT-docs or HINT_SOURCE_REPO; no solver files are bundled here.")
    return None
