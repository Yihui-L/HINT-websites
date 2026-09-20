#!/usr/bin/env python3
"""Index the existing archived PNGs without altering or recomputing results."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import struct
import tomllib

DOCS = Path(__file__).resolve().parents[1]
CASE = DOCS.parent
DATA = DOCS / "docs-data"
GROUPS = {"convergence":"收敛与耗时", "section":"二维截面", "profile":"一维剖面", "poincare":"庞加莱", "iota":"旋转变换"}
VARIABLES = {
    "pressure":"压强", "s":"演化 s 标签", "rho":"ρ 标签", "current_density":"电流密度模",
    "toroidal_current_density":"环向电流密度 Jφ", "enclosed_toroidal_current":"累计环向电流",
    "parallel_current_density":"平行电流密度", "field_strength":"总场强", "response_field_strength":"响应场强",
    "vacuum_field_strength":"真空场强", "speed":"流速大小", "velocity_change_rate":"流速矢量变化率",
    "speed_change_rate":"流速模变化率", "force_residual":"力残差模", "force_residual_relative":"局域相对力残差",
    "lorentz_force":"洛伦兹力模", "pressure_gradient":"压力梯度模", "parallel_pressure_gradient":"平行压力梯度",
    "rotational_transform":"旋转变换 ι", "divergence_b":"总场散度", "divergence_b_abs":"总场散度绝对值",
    "divergence_b_response":"响应场散度", "divergence_b_response_abs":"响应场散度绝对值",
    "divergence_b_vacuum":"真空场散度", "divergence_b_vacuum_abs":"真空场散度绝对值",
}
for prefix, label in (("field","总磁场"),("response_field","响应磁场"),("velocity","流速")):
    for component in ("r","phi","z"):
        VARIABLES[f"{prefix}_{component}"]=f"{label} {component} 分量"
SPECIAL = {
    "poincare_total_initial_three_sections":("初始化总场庞加莱 · 第 0 步", "迭代前保存的 B=B₀+B₁；0° / 30° / 60°，叠加初始 VMEC 磁面。非第 100 步结果。"),
    "convergence_checkpoint_field_means":("场强体平均","完整保存态；R 加权体平均，区分壁内及演化 s<1。"),
    "convergence_checkpoint_means":("流速与残差体平均","完整保存态；不同有效区域的 R 加权体平均。"),
    "convergence_checkpoint_peaks":("峰值随迭代变化","完整保存态网格最大值；不是每步磁轴插值值。"),
    "convergence_checkpoint_rms":("流速与残差体 RMS","完整保存态；柱坐标 R 加权，不是算术 RMS。"),
    "convergence_checkpoint_velocity_change_rate":("速度变化率历史","相邻保存态、换算弛豫时间；并非实验加速度。"),
    "convergence_response_divergence_si":("响应场散度 · SI","物理矩形域算术 RMS / 最大绝对值，T/m。"),
    "convergence_stepb_01":("Step-B 诊断 · 01","归一化已存指标，各外迭代最后一个内部步。"),
    "convergence_stepb_02":("Step-B 诊断 · 02","归一化已存指标，参见原图坐标与标签。"),
    "convergence_stepb_03":("Step-B 诊断 · 03","归一化已存指标；边界法向误差相对冻结初值。"),
    "convergence_wall_clock_timings":("实际计算耗时","墙钟时间；与归一化弛豫时间不同。"),
    "poincare_three_sections":("庞加莱 · 第 100 步 · 三截面","0° / 30° / 60°；第 100 步总场，叠加初始 VMEC 磁面。"),
    "poincare_outboard_detail":("庞加莱 · 第 100 步 · 外侧细节","与第 100 步全图同批轨迹；扩大显示外侧磁结构。"),
    "poincare_000.0deg":("庞加莱 · 第 100 步 · 0°","第 100 步；最多 600 场周期，只绘有效回归点。"),
    "poincare_030.0deg":("庞加莱 · 第 100 步 · 30°","第 100 步；最多 600 场周期，只绘有效回归点。"),
    "poincare_060.0deg":("庞加莱 · 第 100 步 · 60°","第 100 步；最多 600 场周期，只绘有效回归点。"),
}


def figure_entry(path):
    stem=path.stem
    category=stem.split("_",1)[0]
    if stem in SPECIAL:
        title,caption=SPECIAL[stem]
    elif category=="section":
        variable=stem.removeprefix("section_")
        title=VARIABLES[variable]
        caption="第 100 步，φ=0° / 30° / 60°。颜色、单位及有效区以原图标注为准。"
    elif category=="profile":
        if "initial_vmec_s" in stem:
            variable="rotational_transform"; coordinate="初始 VMEC s"
        else:
            variable,coordinate=stem.removeprefix("profile_").rsplit("_",1)
        title=VARIABLES[variable]+" · "+coordinate
        caption=("横坐标为演化 HINT 标签；截面面积分箱，不是磁面平均。" if coordinate in {"s","rho"}
                 else "固定物理位置的剖面，取样位置见方法说明。")
        if variable=="rotational_transform":
            category="iota"
            caption="每截面 191 个初始 VMEC 起点；有限/通过/失败分开，不同截面不取平均。"
    else:
        raise ValueError(f"Uncatalogued figure {path.name}")
    raw=path.read_bytes()
    if raw[:8]!=b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    width,height=struct.unpack(">II",raw[16:24])
    return {"id":stem,"category":category,"title":title,"caption":caption,
            "outer_step":0 if stem=="poincare_total_initial_three_sections" else (None if category=="convergence" else 100),
            "file":"../figures/"+path.name,"width":width,"height":height,
            "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


def validate_archive():
    """Check the frozen manifest without changing scientific or provenance fields."""
    manifest=json.loads((DATA/"results.json").read_text(encoding="utf-8"))
    figures=manifest["figures"]
    if len(figures)!=85 or len({f["id"] for f in figures})!=85 or sum(f["outer_step"]==0 for f in figures)!=1:
        raise ValueError("Archive changed; review result notes and expected figure coverage before rebuilding")
    expected={f["id"]+".png" for f in figures}
    if {p.name for p in (CASE/"figures").glob("*.png")}!=expected:
        raise ValueError("PNG inventory differs from the frozen archive")
    for f in figures:
        p=CASE/"figures"/(f["id"]+".png")
        if f["file"]!="../figures/"+p.name or p.is_symlink() or p.resolve()!=p:
            raise ValueError(f"Invalid archived figure path: {p}")
        actual=figure_entry(p)
        if actual!=f:
            raise ValueError(f"Figure or metadata changed: {p.name}")
    config=tomllib.loads((CASE/"ncsx_main.toml").read_text(encoding="utf-8"))
    if config!=manifest["configuration"]:
        raise ValueError("Input configuration differs from the frozen archive")
    for name, checksum in manifest["files"].items():
        p=CASE/name
        if not p.resolve().is_relative_to(CASE) or p.is_symlink() or p.resolve()!=p:
            raise ValueError(f"Invalid archived input path: {name}")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=checksum:
            raise ValueError(f"Archived input changed: {name}")
    return manifest


def build():
    import markdown

    manifest=validate_archive()
    figures=manifest["figures"]
    revision=manifest["archive_commit"]
    cards=[]
    priority={name:i for i,name in enumerate(["poincare_total_initial_three_sections","poincare_three_sections","section_pressure","convergence_checkpoint_means","profile_pressure_s","profile_rotational_transform_initial_vmec_s","section_force_residual_relative"])}
    ordered=sorted(figures,key=lambda f:(priority.get(f["id"],99),f["id"]))
    for f in ordered:
        method_link='<a href="#initial-poincare">第 0 步图片计算方式</a>' if f["outer_step"]==0 else ''
        cards.append(f'''<article id="figure-{f['id']}" class="figure-card" data-category="{f['category']}" data-id="{f['id']}">
<a class="image-link" href="{f['file']}" aria-label="查看原图：{html.escape(f['title'])}"><img src="{f['file']}" alt="{html.escape(f['title'])}；{html.escape(f['caption'])}" width="{f['width']}" height="{f['height']}" loading="lazy" decoding="async"></a>
<div class="figure-text"><span class="category">{GROUPS[f['category']]}</span><h2>{html.escape(f['title'])}</h2>
<p>{html.escape(f['caption'])}</p>{method_link}<div class="figure-foot"><small>{f['width']} × {f['height']} px</small><a href="{f['file']}" download>PNG ↓</a></div><code>{f['id']}</code></div></article>''')
    notes=markdown.markdown((DATA/"result-notes.md").read_text(encoding="utf-8"),extensions=["tables","fenced_code"])
    notes=notes.replace("<h1>", '<h2 class="section-title">', 1).replace("</h1>", "</h2>", 1)
    notes=notes.replace("<table>",'<div class="table-scroll"><table>').replace("</table>","</table></div>")
    tabs=f'<button class="category-tab active" data-category="all" aria-pressed="true">全部 <small>{len(figures)}</small></button>'
    for key,label in GROUPS.items():
        count=sum(f["category"]==key for f in figures)
        tabs+=f'<button class="category-tab" data-category="{key}" aria-pressed="false">{label} <small>{count}</small></button>'
    input_links=''
    for file,desc in [("ncsx_main.toml","实际运行配置：200 步上限，人工停止于第 100 步"),("ncsx_follow.toml","未使用的续算示例"),("ncsx_post.toml","数值 CLI 示例；不是本批 PNG 的绘图参数"),("inputs/NCSX_physical_vessel_half_period.txt","真实壁半周期文本，含 nfp 与对称性")]:
        input_links+=f'<tr><td><a href="../{file}" download>{file}</a></td><td>{desc}</td></tr>'
    safe_json=json.dumps(ordered,ensure_ascii=False).replace("<","\\u003c")
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCSX | 历史 step100 归档 · 非当前 component 结果</title><meta name="description" content="暂存于 EX-NCSX-debug-vmec-unscale-component 的历史 HINT-debug 0.8.8 初始化与第100步结果，不是当前 component 运行产物。">
<link rel="stylesheet" href="assets/results.css"><script src="assets/results.js" defer></script></head><body>
<a class="skip" href="#gallery">跳至图片</a><aside><a class="brand" href="#top">NCSX<span>历史归档 / 第 100 步</span></a>
<p class="case-name">EX-NCSX-debug-vmec-unscale-component</p><nav aria-label="结果导航"><a class="source-link" href="../../Source-Code/">Source-Code / 程序文档</a><a href="#gallery">图片目录</a><a href="#initial-poincare">初始化庞加莱方法</a><a href="#diagnostics">第 100 步指标</a><a href="#method">方法与统计口径</a><a href="#inputs">输入与溯源</a></nav>
<div class="case-state"><strong>指定步数停止</strong><span>不是收敛验收</span><dl><dt>程序</dt><dd>HINT-debug 0.8.8</dd><dt>起点</dt><dd>VMEC</dd><dt>压力反馈</dt><dd>scale_after=false</dd><dt>边界</dt><dd>R–Z 矩形域</dd></dl></div>
<div class="aside-links"><a href="https://github.com/Yihui-L/HINT-websites/tree/main/EX-NCSX-debug-vmec-unscale-component">GitHub 公开算例文件 ↗</a><a href="README.md">归档维护说明</a></div></aside>
<main id="top"><header><p class="eyebrow">HINT / EQUILIBRIUM ARCHIVE</p><h1>NCSX</h1><p class="subtitle">VMEC 初始化 · 目标压力后自由演化</p><div class="meta"><span>初始化 + 完整外迭代 100</span><span>nfp = 3</span><span>144 × 144 × 144</span><span>0° / 30° / 60°</span></div></header>
<div class="archive-notice" role="note" aria-labelledby="archive-title">
<h2 id="archive-title">历史 step100 归档，不是当前 component 运行结果</h2>
<p>原 <code>highbeta_vmec_unscale</code> 文件暂存于此，等待当前远程任务完成后另行核验与更新。迁移不代表重新计算或完成新结果验收。</p>
<p class="archive-scope">HINT-debug 0.8.8 · 第 0 步初始化、完整第 100 步及 0–100 步历史 · 指定步数停止，非收敛验收</p>
</div>
<section id="gallery" aria-label="结果图片"><div class="gallery-toolbar"><div class="tabs" role="group" aria-label="图片分类">{tabs}</div>
<label>检索图片<input id="figure-search" type="search" placeholder="初始化、压强、散度、iota、变量名"></label><output id="figure-count" aria-live="polite">{len(figures)} 张图片</output></div>
<div class="gallery-grid">{''.join(cards)}</div><p id="empty" hidden>没有匹配的图片。</p></section>
<section id="diagnostics"><h2>第 100 步指标</h2><p>来源为已归档算例 README。网站不读取 NetCDF，也未重新计算这些数值。</p>
<div class="table-scroll"><table><thead><tr><th>指标</th><th>数值</th><th>口径</th></tr></thead><tbody>
<tr><td>外迭代总耗时</td><td>262.721 s</td><td>第 100 步墙钟时间</td></tr><tr><td>Step-A / Step-B</td><td>223.738 / 14.139 s</td><td>不含其余处理与 I/O</td></tr>
<tr><td>初始化</td><td>505.851 s</td><td>不含首个 checkpoint 额外写入</td></tr><tr><td>div(B₁) RMS</td><td>8.13519 × 10⁻¹⁵ T/m</td><td>保存态；物理矩形域，算术 RMS</td></tr>
<tr><td>max |div(B₁)|</td><td>2.05669 × 10⁻¹³ T/m</td><td>保存态；不是总场散度</td></tr><tr><td>流速 RMS / 最大值</td><td>6.30322 / 268.398 m/s</td><td>物理矩形域；RMS 为算术值</td></tr>
<tr><td>网格峰值压力</td><td>68693.8 Pa</td><td>不是刚性维持的轴压；初始约 68555.3 Pa</td></tr><tr><td>Step-B 力 RMS</td><td>0.00744826</td><td>归一化存储量；不是局域相对力残差</td></tr>
</tbody></table></div><p class="notice">响应场散度小不能单独证明平衡收敛。需结合速度、力残差、压力变化和磁结构。</p></section>
<section id="method" class="prose">{notes}</section><section id="inputs"><h2>输入与溯源</h2><div class="table-scroll"><table><thead><tr><th>文件</th><th>用途</th></tr></thead><tbody>{input_links}</tbody></table></div>
<p>wout、mgrid 与结果 NetCDF 未随本档案提供。<a href="../README.md">原算例说明</a> · <a href="../figures/README.md">原图片索引</a> · <a href="docs-data/results.json">配置、图片元数据与 SHA-256</a> · <a href="README.md">网站维护说明</a></p>
<p>算例源码 <a href="https://github.com/Yihui-L/HINT-docs/commit/e3c91557c1c38ae8e2ea5dcfae461460a0db3836">e3c9155</a>；归档提交 {revision[:7]}。PNG 保留原文件，不重复压缩或重绘。</p></section>
<footer>历史 step100 静态归档 · 非当前 component 运行结果 · 原图保留在 ../figures/ · <a href="../../Source-Code/">Source-Code / 程序文档</a></footer></main>
<dialog id="viewer" aria-labelledby="viewer-title" aria-describedby="viewer-archive"><div class="viewer-toolbar"><button id="prev" title="上一张" aria-label="上一张">←</button><button id="next" title="下一张" aria-label="下一张">→</button><div class="viewer-heading"><p id="viewer-archive" class="viewer-archive">历史归档 · 非当前 component 结果</p><h2 id="viewer-title"></h2></div><a id="original-link" target="_blank" rel="noopener">原始 PNG ↗</a><button id="close-viewer" title="关闭" aria-label="关闭">×</button></div><div class="viewer-scroll"><img id="viewer-image" alt=""><p id="viewer-caption"></p></div></dialog>
<script id="figure-data" type="application/json">{safe_json}</script></body></html>'''
    (DOCS/"index.html").write_text(page,encoding="utf-8")
    root_entry=(DOCS/"root-redirect.html").read_text(encoding="utf-8")
    root_entry=root_entry.replace('url=index.html', 'url=Documents/index.html').replace('href="index.html"', 'href="Documents/index.html"')
    (CASE/"index.html").write_text(root_entry,encoding="utf-8")
    print(f"Indexed {len(figures)} PNGs; archive {revision[:7]}; numerical data untouched.")


if __name__=="__main__":
    build()
