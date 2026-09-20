"""Build the self-contained manual from reviewed prose and current source ASTs."""

from __future__ import annotations

import ast
import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import markdown
import tomllib
from latex2mathml.converter import convert
from source_repo import locate_source

DOCS = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-repo", help="Separate HINT-docs source checkout")
REPO = locate_source(parser.parse_args().source_repo)
DATA = DOCS / "docs-data"
NOTES = json.loads((DATA / "parameter-notes.json").read_text())
MAIN = {
    "paths": "PathsConfig",
    "grid": "GridConfig",
    "flux": "FluxConfig",
    "vacuum": "VacuumConfig",
    "wall": "WallConfig",
    "profiles": "ProfilesConfig",
    "profiles.pressure": "ProfileDefinition",
    "profiles.current": "ProfileDefinition",
    "solver": "SolverConfig",
    "solver.step_a": "StepAConfig",
    "solver.step_b": "StepBConfig",
    "output": "OutputConfig",
}
POST = {
    "execution": "PostExecutionConfig",
    "fields": "MagvalConfig",
    "force_balance": "GPRTSConfig",
    "magnetic_axis": "AxisConfig",
    "field_lines": "HMAGConfig",
    "poincare": "HMAGConfig",
    "flux_surfaces": "HMAGConfig",
    "boundary_trace": "HMAGConfig",
    "convergence": "FeatureConfig",
}
SOURCE_REF = subprocess.check_output(
    ["git", "log", "-1", "--format=%H", "--", "HINT-debug", "HINT-wall"],
    cwd=REPO,
    text=True,
).strip()
SOURCE_DIRTY = bool(subprocess.check_output(
    ["git", "status", "--porcelain", "--", "HINT-debug", "HINT-wall"],
    cwd=REPO, text=True,
).strip())


def source_url(variant: str, relative: str, line: int = 1) -> str:
    path = f"HINT-{variant}/{relative}"
    if not (REPO / path).is_file():
        raise ValueError(f"Missing source link: {path}")
    return f"https://github.com/Yihui-L/HINT-docs/blob/{SOURCE_REF}/{path}#L{line}"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plotting_catalog(variant: str) -> dict:
    """Read metadata without importing the solver or initializing GPU runtimes."""
    root = REPO / f"HINT-{variant}"
    diagnostics = root / f"src/hint_{variant}/magnetic_diagnostics.py"
    namespace = {"__name__": "__main__"}
    for node in ast.parse(diagnostics.read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"AD_FIELDS", "AD_STATISTICS"}:
                    namespace[target.id] = ast.literal_eval(node.value)
    if not {"AD_FIELDS", "AD_STATISTICS"} <= namespace.keys():
        raise ValueError(f"Missing AD metadata in {diagnostics}")
    path = root / f"postprocess/hint_{variant}_plotting/variables.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom)
        and node.module == f"hint_{variant}.magnetic_diagnostics"
    )]
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace["variable_catalog"]()


def parse_classes(path: Path) -> dict:
    tree = ast.parse(path.read_text())
    nodes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    result = {}

    def fields(name):
        if name in result:
            return result[name]
        node = nodes[name]
        values = {}
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in nodes:
                values.update(fields(base.id))
        for field in node.body:
            if not isinstance(field, ast.AnnAssign) or field.value is None:
                continue
            value = field.value
            if isinstance(value, ast.Call):
                kw = {k.arg: k.value for k in value.keywords}
                if "default_factory" in kw:
                    factory = ast.unparse(kw["default_factory"])
                    if factory != "list":
                        continue  # Nested config objects are expanded under their TOML tables.
                    default = []
                elif "default" in kw:
                    default = ast.literal_eval(kw["default"])
                else:
                    continue
            else:
                default = ast.literal_eval(value)
            values[field.target.id] = {
                "type": ast.unparse(field.annotation),
                "default": default,
                "line": field.lineno,
                "owner": name,
            }
        result[name] = values
        return values

    for name in nodes:
        fields(name)
    return result


def parameters():
    rows = {}
    for variant in ("debug", "wall"):
        relative = f"src/hint_{variant}/config.py"
        classes = parse_classes(REPO / f"HINT-{variant}" / relative)
        for program, mapping in (("main", MAIN), ("post", POST)):
            for prefix, name in mapping.items():
                for key, entry in classes[name].items():
                    full = f"{prefix}.{key}"
                    unit, description = NOTES[entry["owner"]][key]
                    row = rows.setdefault(
                        (program, full),
                        {
                            "program": program,
                            "name": full,
                            "type": entry["type"],
                            "unit_condition": unit,
                            "description": description,
                            "versions": {},
                        },
                    )
                    if row["type"] != entry["type"]:
                        raise ValueError(f"Type drift: {full}")
                    row["versions"][variant] = {
                        "default": entry["default"],
                        "source": source_url(variant, relative, entry["line"]),
                    }
        # These keys are mapped explicitly by PostConfig.from_toml, not table dataclasses.
        root = [
            ("input_file", "str", "", "PostRoot"),
            ("output_file", "str", "", "PostRoot"),
            ("selection.record", "int", -1, "Selection"),
            ("selection.requested_time", "float | None", None, "Selection"),
        ]
        for full, typ, default, owner in root:
            unit, description = NOTES[owner][full.split(".")[-1]]
            row = rows.setdefault(
                ("post", full),
                {
                    "program": "post",
                    "name": full,
                    "type": typ,
                    "unit_condition": unit,
                    "description": description,
                    "versions": {},
                },
            )
            row["versions"][variant] = {
                "default": default,
                "source": source_url(variant, relative),
            }
    return list(rows.values())


def render_md(text):
    # Only fenced standalone $$ blocks are converted; keep code examples untouched.
    formulas = []

    def math_block(match):
        formulas.append(
            '<div class="equation">'
            + convert(match.group(1), display="block")
            + "</div>"
        )
        return f"\n\nMATHPLACEHOLDER{len(formulas) - 1}END\n\n"

    text = re.sub(
        r"^\$\$(.+?)\$\$\s*$", math_block, text, flags=re.MULTILINE | re.DOTALL
    )
    rendered = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]
    )
    for i, block in enumerate(formulas):
        rendered = rendered.replace(f"<p>MATHPLACEHOLDER{i}END</p>", block)
    rendered = re.sub(
        r'href="source:(debug|wall):([^"#]+)"',
        lambda m: 'href="' + source_url(m[1], m[2]) + '"',
        rendered,
    )
    rendered = rendered.replace(
        "<table>", '<div class="table-scroll" tabindex="0"><table>'
    )
    rendered = rendered.replace("</table>", "</table></div>")
    return rendered


def default_text(value):
    if value is None:
        return "省略 (None)"
    return json.dumps(value, ensure_ascii=False)


def parameter_table(rows, program):
    body = []
    for row in rows:
        if row["program"] != program:
            continue
        versions = row["versions"]
        cells = []
        for variant in ("debug", "wall"):
            entry = versions.get(variant)
            cells.append(
                "不接受"
                if entry is None
                else f'<a href="{entry["source"]}"><code>{html.escape(default_text(entry["default"]))}</code></a>'
            )
        name = row["name"]
        body.append(
            f'<tr data-version="{" ".join(versions)}" id="param-{program}-{name}">'
            f"<td><code>{html.escape(name)}</code><small>{html.escape(row['type'])}</small></td>"
            f"<td>{cells[0]}</td><td>{cells[1]}</td>"
            f"<td><strong>{html.escape(row['unit_condition'])}</strong><p>{html.escape(row['description'])}</p></td></tr>"
        )
    return (
        '<div class="param-tools"><label>参数检索<input class="param-search" type="search" placeholder="名称、物理量、单位"></label>'
        '<label>适用版本<select class="param-version"><option value="all">两个版本</option><option value="debug">HINT-debug</option>'
        '<option value="wall">HINT-wall</option><option value="different">差异项</option></select></label>'
        '<output class="param-count" aria-live="polite"></output></div>'
        '<div class="table-scroll"><table class="parameters"><thead><tr><th scope="col">参数 / Python 类型</th>'
        '<th scope="col">debug 默认</th><th scope="col">wall 默认</th><th scope="col">单位、适用条件与含义</th></tr></thead>'
        "<tbody>" + "".join(body) + "</tbody></table></div>"
    )


def figures():
    # Keep optional plotting caches out of the user's home and source tree.
    import tempfile

    os.environ.setdefault(
        "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "hint-docs-matplotlib")
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Ellipse, Rectangle

    plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans"})
    fig, ax = plt.subplots(figsize=(12, 3.1), layout="constrained")
    ax.set(xlim=(0, 12), ylim=(0, 3))
    ax.axis("off")
    labels = [
        (0.1, "Inputs", "TOML\nwout + coils\nwall text"),
        (
            3.15,
            "Preparation",
            "VMEC / coils / wall\nB0, p, s, B1 initial\nnormalization",
        ),
        (
            6.2,
            "Relaxation",
            "Step-A: pressure\nStep-B: B1 and v\naxis / s / pressure policy",
        ),
        (9.25, "Results", "restart NetCDF\nseparate analysis.nc\nfigures"),
    ]
    for x, title, text in labels:
        ax.add_patch(
            Rectangle(
                (x, 0.55),
                2.6,
                1.95,
                facecolor="#eff5f4",
                edgecolor="#557975",
                linewidth=1.2,
            )
        )
        ax.text(x + 0.16, 2.16, title, color="#164d4b", weight="bold")
        ax.text(x + 0.16, 1.88, text, va="top", linespacing=1.7, fontsize=10)
        if x < 9:
            ax.annotate(
                "",
                (x + 3.03, 1.5),
                (x + 2.66, 1.5),
                arrowprops={"arrowstyle": "->", "color": "#576a70"},
            )
    ax.annotate(
        "follow: restore evolving state, not initial profiles",
        (6.3, 0.18),
        (9.4, 0.18),
        arrowprops={"arrowstyle": "->", "color": "#8d3947"},
        fontsize=9,
        ha="center",
    )
    fig.savefig(DOCS / "assets/workflow.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout="constrained")
    for ax, variant in zip(axes, ("HINT-debug", "HINT-wall"), strict=True):
        ax.set(
            xlim=(0.4, 2.5),
            ylim=(-1.1, 1.1),
            xlabel="R (schematic)",
            ylabel="Z (schematic)",
        )
        ax.set_aspect("equal")
        ax.set_title(variant, loc="left", weight="bold")
        ax.add_patch(
            Rectangle(
                (0.5, -1),
                1.9,
                2,
                facecolor="#f6efcc",
                edgecolor="#555d69",
                linewidth=2.4 if variant.endswith("debug") else 1,
            )
        )
        theta = np.linspace(0, 2 * np.pi, 240)
        r = 1.45 + 0.69 * np.cos(theta) + 0.10 * np.cos(2 * theta)
        z = 0.82 * np.sin(theta) - 0.13 * np.sin(2 * theta)
        ax.fill(
            r,
            z,
            facecolor="#e2efed",
            edgecolor="#a34250",
            linewidth=2.4 if variant.endswith("wall") else 1.3,
            label="First wall",
        )
        ax.add_patch(
            Ellipse(
                (1.45, 0),
                0.82,
                1.12,
                facecolor="#bfdad7",
                edgecolor="#267a77",
                linestyle="--",
                label="Initial LCFS",
            )
        )
        ax.text(1.45, 0, "plasma", ha="center", color="#174c4a")
        ax.text(0.59, 0.88, "R-Z box", fontsize=9)
        ax.text(
            1.5,
            -0.93,
            "exterior evolution"
            if variant.endswith("debug")
            else "ghost / extension only",
            ha="center",
            fontsize=9,
        )
        ax.legend(loc="upper right", fontsize=8, frameon=False)
    fig.savefig(DOCS / "assets/boundaries.png", dpi=180)
    plt.close(fig)


def build():
    (DOCS / "assets").mkdir(exist_ok=True)
    rows = parameters()
    (DATA / "parameters.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(
        [
            "program",
            "name",
            "type",
            "debug_default",
            "wall_default",
            "unit_condition",
            "description",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["program"],
                row["name"],
                row["type"],
                *[
                    default_text(row["versions"][v]["default"])
                    if v in row["versions"]
                    else "NOT_ACCEPTED"
                    for v in ("debug", "wall")
                ],
                row["unit_condition"],
                row["description"],
            ]
        )
    (DATA / "parameters.csv").write_text(out.getvalue(), encoding="utf-8-sig")
    sections = []
    for path in sorted(DATA.glob("[0-9][0-9]-*.md")):
        text = path.read_text()
        title = text.splitlines()[0].removeprefix("# ")
        sections.append((path.stem.split("-", 1)[1], title, render_md(text)))
    for program, title in (("main", "主程序参数全表"), ("post", "后处理参数全表")):
        intro = (
            "默认值来自源码配置类；0/空值可能只是必填占位。默认值链接到对应定义行。"
            "条件不生效不一定意味着可以输入非法类型。TOML 的 None 表示省略该键。"
        )
        sections.append(
            (
                program + "-parameters",
                title,
                f"<h1>{title}</h1><p>{intro}</p>" + parameter_table(rows, program),
            )
        )
    catalogs = {}
    for variant in ("debug", "wall"):
        catalogs[variant] = plotting_catalog(variant)
    (DATA / "variables.json").write_text(
        json.dumps(catalogs, ensure_ascii=False, indent=2) + "\n"
    )
    varrows = []
    for name, info in catalogs["debug"].items():
        varrows.append(
            f"<tr><td><code>{name}</code></td><td>{html.escape(info['units'])}</td>"
            f"<td>{html.escape(', '.join(info['supports']))}</td>"
            f"<td>{html.escape(info.get('description') or info['label'])}</td></tr>"
        )
    sections.append(
        (
            "variables",
            "绘图变量索引",
            "<h1>绘图变量索引</h1><p>字符串区分大小写；profile=剖面、section=二维截面、time_series=历史曲线。"
            "英文定义由源码直接提取；中文统计解释见收敛诊断章节。debug/wall 的边界诊断对应各自边界。</p>"
            '<div class="table-scroll"><table><thead><tr><th>变量名</th><th>单位</th><th>适用功能</th><th>定义</th></tr></thead>'
            "<tbody>" + "".join(varrows) + "</tbody></table></div>",
        )
    )
    versions = {}
    hashes = {}
    for variant in ("debug", "wall"):
        root = REPO / f"HINT-{variant}"
        versions[variant] = tomllib.loads((root / "pyproject.toml").read_text())[
            "project"
        ]["version"]
        for p in sorted(root.rglob("*")):
            if (
                p.is_file()
                and p.suffix in {".py", ".toml", ".md"}
                and not any(x.startswith(".") for x in p.relative_to(root).parts)
            ):
                hashes[str(p.relative_to(REPO))] = digest(p)
        target = DATA / "templates" / variant
        target.mkdir(parents=True, exist_ok=True)
        for name in ("main.toml", "follow.toml", "post.toml", "postprocess_demo.ipynb"):
            shutil.copyfile(root / "examples" / name, target / name)
    manifest = {
        "source_commit": SOURCE_REF,
        "source_working_tree_changes": SOURCE_DIRTY,
        "versions": versions,
        "parameter_counts": {
            v: {
                p: sum(r["program"] == p and v in r["versions"] for r in rows)
                for p in ("main", "post")
            }
            for v in versions
        },
        "plot_variable_count": len(catalogs["debug"]),
        "source_sha256": hashes,
        "validation_scope": "Documentation/source contract and browser checks; no new equilibrium benchmark.",
    }
    (DATA / "source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    download = "<h1>文档与输入模板</h1><p>参数模板来自当前源码，不包含任何装置输入、运行记录或计算结果。</p><ul>"
    for filename, label in [
        ("parameters.json", "参数 JSON"),
        ("parameters.csv", "参数 CSV"),
        ("variables.json", "绘图变量 JSON"),
        ("source-manifest.json", "源码版本与 SHA-256"),
        ("DOCUMENTATION_CHECKS.md", "文档检查记录"),
    ]:
        download += f'<li><a href="docs-data/{filename}">{label}</a></li>'
    for v in versions:
        for filename in (
            "main.toml",
            "follow.toml",
            "post.toml",
            "postprocess_demo.ipynb",
        ):
            download += f'<li><a href="docs-data/templates/{v}/{filename}">HINT-{v} / {filename}</a></li>'
    download += '</ul><p><a href="README.md">维护与重建说明</a> · <a href="SOURCE_VERSION.md">版本说明</a></p>'
    sections.append(("downloads", "文档与输入模板", download))
    nav = "".join(
        f'<a href="#{sid}">{i:02d}<span>{title}</span></a>'
        for i, (sid, title, _) in enumerate(sections, 1)
    )
    articles = "".join(
        f'<section class="chapter" id="{sid}" data-title="{html.escape(title)}">{body}</section>'
        for sid, title, body in sections
    )
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="HINT-debug 与 HINT-wall 物理模型、数值方法、参数及使用手册"><title>HINT | 程序与使用手册</title>
<link rel="stylesheet" href="assets/manual.css"><script src="assets/manual.js" defer></script></head>
<body><a class="skip" href="#content">跳至正文</a><header class="mobile-header"><a href="#overview">HINT / 程序手册</a>
<button id="menu-toggle" aria-label="章节导航" title="章节导航" aria-controls="sidebar" aria-expanded="false">☰</button></header>
<aside id="sidebar"><a class="brand" href="#overview">HINT<span>程序与使用手册</span></a>
<div class="versions"><span>HINT-debug {versions["debug"]}</span><span>HINT-wall {versions["wall"]}</span></div>
<label class="search-label" for="global-search">全文检索</label><input id="global-search" type="search" placeholder="方程、参数、关键字" autocomplete="off">
<output id="search-status" aria-live="polite"></output><nav aria-label="章节">{nav}</nav>
<div class="sidebar-bottom"><a href="https://github.com/Yihui-L/HINT-websites/tree/main/Source-Code">GitHub · 手册文档</a>
<a href="https://github.com/Yihui-L/HINT-docs">GitHub · 程序源码（需权限）</a></div></aside>
<main id="content"><div class="document-meta"><span>HINT / SOURCE-CODE / 使用说明</span><span>源码 {SOURCE_REF[:7]}{' + 未提交工作区' if SOURCE_DIRTY else ''} · schema 21</span></div>
<div class="manual-intro"><p class="eyebrow">MODEL · NUMERICS · WORKFLOW</p><p>从物理方程到输入输出</p><div class="quick-links"><a href="#model">物理模型</a><a href="#installation">安装运行</a><a href="#main-parameters">参数索引</a><a href="#postprocess">后处理</a></div></div>
{'<p><strong>未发布的工作区快照。</strong>源码链接指向最近提交，未包含当前候选修改；请结合逐文件哈希及核验章节阅读，不能将本页视为已验收版本。</p>' if SOURCE_DIRTY else ''}
{articles}<p id="no-results" hidden>未找到匹配章节。</p><footer>源代码定义行为，离散诊断支持判断；本文不代替算例验证。<br>HINT-debug {versions["debug"]} / HINT-wall {versions["wall"]}</footer></main>
</body></html>"""
    (DOCS / "index.html").write_text(page)
    (DOCS / "SOURCE_VERSION.md").write_text(
        f"# Source Version\n\n- HINT-debug {versions['debug']} / HINT-wall {versions['wall']}\n"
        f"- Source commit: `{SOURCE_REF}`\n- NetCDF schema: 21 (variant-specific identifiers)\n"
        f"- Uncommitted source-tree changes: {SOURCE_DIRTY}. "
        "When true, the commit is a base reference, not this complete snapshot.\n"
        "- 参数默认值与字段类型由配置 AST 生成，解释为本快照人工核对。\n"
        "- 本快照包含插值约束、诊断、存储与加速路径修正；未重新运行物理 benchmark。\n"
        "- 逐文件 SHA-256 与参数数量见 docs-data/source-manifest.json。\n"
    )
    figures()
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in ("versions", "parameter_counts", "plot_variable_count")
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    build()
