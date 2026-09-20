#!/usr/bin/env python3
"""Export the selected result website and its approved assets only."""
from pathlib import Path
import shutil
import sys

from build_site import validate_archive

DOCS = Path(__file__).resolve().parents[1]
CASE = DOCS.parent
ALLOWED = {".html", ".md", ".css", ".js", ".png", ".json", ".toml", ".txt", ".py"}


def export(destination):
    target = Path(destination).resolve()
    if target.is_relative_to(CASE):
        raise ValueError("Export outside the source case")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError("Destination must be a new or empty directory")
    validate_archive()
    files = [CASE / name for name in (
        "index.html", "README.md", "ncsx_main.toml", "ncsx_follow.toml", "ncsx_post.toml",
        "inputs/NCSX_physical_vessel_half_period.txt", "figures/README.md",
        "Documents/index.html", "Documents/README.md", "Documents/.nojekyll",
        "Documents/root-redirect.html", "Documents/tools/build_site.py", "Documents/tools/export_site.py")]
    figures = sorted((CASE / "figures").glob("*.png"))
    if len(figures) != 85 or not any(p.name == "poincare_total_initial_three_sections.png" for p in figures):
        raise ValueError("Review changed archive before publication: expected 84 archived PNGs and one initialization PNG")
    files.extend(figures)
    for directory in (DOCS / "assets", DOCS / "docs-data"):
        if directory.is_symlink():
            raise ValueError(f"Symlink not permitted: {directory}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink not permitted: {path}")
            if path.is_file():
                files.append(path)
    mapping = [(p, p.relative_to(CASE)) for p in files]
    mapping += [(DOCS / ".nojekyll", Path(".nojekyll"))]
    for path, _ in mapping:
        if path.is_symlink() or not path.is_file() or path.resolve() != path:
            raise ValueError(f"Invalid or symlinked static file: {path}")
        if path.name != ".nojekyll" and path.suffix not in ALLOWED:
            raise ValueError(f"Unapproved file type: {path}")
    for path, relative in sorted(mapping):
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, output)
        print(relative)
    print(f"Exported {len(mapping)} case-local files; no solver or NetCDF. Source-Code is a navigation link only.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: export_site.py EMPTY_DESTINATION")
    export(sys.argv[1])
