"""Verify static documentation, optionally against a separate source checkout."""

import argparse
import ast
import hashlib
import json
import re
from html.parser import HTMLParser
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import tomllib

DOCS = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.resources = []
        self.duplicate = []
        self.math = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicate.append(attrs["id"])
            self.ids.add(attrs["id"])
        if "href" in attrs:
            self.links.append(attrs["href"])
        if "src" in attrs:
            self.resources.append(attrs["src"])
        self.math += tag == "math"
        if tag == "img":
            unloaded_viewer = attrs.get("id") == "viewer-image" and not attrs.get("src")
            assert attrs.get("alt") or (unloaded_viewer and "alt" in attrs), "Missing image alternative text"


def check_html(file):
    parser = Page()
    text = file.read_text()
    parser.feed(text)
    assert not parser.duplicate, parser.duplicate
    assert "MATHPLACEHOLDER" not in text and 'href="source:' not in text
    for target in parser.links + parser.resources:
        part = urlsplit(target)
        if part.scheme or part.netloc:
            continue
        path = (file.parent / unquote(part.path)).resolve() if part.path else file
        if path.is_dir():
            path /= "index.html"
        assert path.is_file(), f"Broken link in {file}: {target}"
        if part.fragment and path == file:
            assert unquote(part.fragment) in parser.ids, f"Missing anchor in {file}: {target}"
    for target in parser.resources:
        assert not urlsplit(target).scheme, "Static site must not require remote assets"
    return parser


def check_manual(repo=None):
    page = check_html(DOCS / "index.html")
    assert page.math >= 15, "Equation conversion incomplete"
    data = DOCS / "docs-data"
    manifest = json.loads((data / "source-manifest.json").read_text())
    rows = json.loads((data / "parameters.json").read_text())
    assert len({(r["program"], r["name"]) for r in rows}) == len(rows)
    for variant in ("debug", "wall"):
        for program, count in manifest["parameter_counts"][variant].items():
            assert sum(r["program"] == program and variant in r["versions"] for r in rows) == count
        for name in ("main.toml", "follow.toml", "post.toml", "postprocess_demo.ipynb"):
            template = data / "templates" / variant / name
            if name.endswith("toml"):
                tomllib.loads(template.read_text())
            else:
                notebook = json.loads(template.read_text())
                assert all(not c.get("outputs") and c.get("execution_count") is None
                           for c in notebook["cells"] if c["cell_type"] == "code")
            if repo:
                source = repo / f"HINT-{variant}/examples/{name}"
                assert source.read_bytes() == template.read_bytes(), f"Template drift: {template}"
    for row in rows:
        for entry in row["versions"].values():
            path, _, line = entry["source"].partition("#L")
            assert path in manifest["source_sha256"] and line.isdecimal(), entry["source"]
    eta = next(r for r in rows if r["name"] == "solver.step_b.eta1")
    assert set(eta["versions"]) == {"debug"}
    interpolation = next(r for r in rows if r["name"] == "solver.magnetic_interpolation")
    assert all(v["default"] == "component" for v in interpolation["versions"].values())
    assert not any("potential_boundary" in r["name"] for r in rows)
    for path in [DOCS / "index.html", *data.glob("*.md")]:
        assert not re.search(r"\b(?:NCSX|W7X|highbeta_vmec_unscale)\b", path.read_text(), re.I), path
    assert not list(DOCS.rglob("*.nc")), "Physical data belong outside the manual"
    if repo:
        for relative, sha in manifest["source_sha256"].items():
            assert hashlib.sha256((repo / relative).read_bytes()).hexdigest() == sha, f"Source drift: {relative}"
        ignored = {"config_path", "paths", "grid", "flux", "vacuum", "wall", "profiles", "solver", "output",
                   "solver_overrides", "pressure", "current", "step_a", "step_b", "magval", "gprts", "hmag",
                   "execution", "magnetic_axis", "poincare", "flux_surfaces", "boundary_trace", "convergence"}
        for variant in ("debug", "wall"):
            tree = ast.parse((repo / f"HINT-{variant}/src/hint_{variant}/config.py").read_text())
            exported = {r["name"].split(".")[-1] for r in rows if variant in r["versions"]}
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign):
                            assert item.target.id in exported | ignored, f"Uncatalogued field: {variant}:{item.target.id}"
    print(f"Manual: {len(rows)} union parameters, {page.math} MathML equations; links, templates and case separation pass.")
    print("Source hashes and parameter coverage pass." if repo else "Checked the self-contained snapshot.")


def check_results(folder):
    data = json.loads((folder / "docs-data/results.json").read_text())
    assert Counter(f["category"] for f in data["figures"]) == data["figure_counts"]
    for figure in data["figures"]:
        path = (folder / unquote(urlsplit(figure["file"]).path)).resolve()
        assert path.stat().st_size == figure["bytes"], path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == figure["sha256"], path
    for relative, info in data["provenance"]["input_checksums"].items():
        path = folder.parent / relative
        assert path.stat().st_size == info["bytes"], path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"], path
    print(f"Result website: {len(data['figures'])} figure hashes, input hashes and links pass.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path)
    args = parser.parse_args()
    check_manual(args.source_repo)
    root = DOCS.parent
    pages = sorted(root.rglob("*.html"))
    for page in pages:
        check_html(page)
    for manifest in sorted(root.glob("EX-*/Documents/docs-data/results.json")):
        check_results(manifest.parents[1])
    print(f"Static links and resources checked in {len(pages)} HTML pages.")
