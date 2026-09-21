"""Build the current NCSX results site from PNGs and machine-readable provenance."""
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import struct
import tomllib

DOCS = Path(__file__).resolve().parents[1]
CASE = DOCS.parent
DATA = DOCS / 'docs-data'
GROUPS = {'convergence':'收敛与耗时', 'section':'二维截面', 'profile':'一维剖面',
          'poincare':'庞加莱', 'iota':'旋转变换'}
LABELS = {
 'pressure':'压强', 's':'演化 s 标签', 'rho':'ρ 标签', 'speed':'流速大小',
 'velocity_change_rate':'流速矢量变化率', 'speed_change_rate':'流速大小变化率',
 'field_strength':'总场强', 'response_field_strength':'响应场强', 'vacuum_field_strength':'真空场强',
 'force_residual':'力残差大小', 'force_residual_relative':'局域归一化力残差',
 'lorentz_force':'洛伦兹力', 'pressure_gradient':'压强梯度',
 'parallel_pressure_gradient':'平行压强梯度', 'current_density':'响应电流密度大小',
 'toroidal_current_density':'环向电流密度 Jφ', 'parallel_current_density':'平行电流密度',
 'enclosed_toroidal_current':'累计环向电流', 'rotational_transform':'旋转变换 ι',
 'divergence_b':'总场网格散度', 'divergence_b_abs':'总场网格散度绝对值',
 'divergence_b_response':'响应场网格散度', 'divergence_b_response_abs':'响应场网格散度绝对值',
 'divergence_b_vacuum':'真空场网格散度', 'divergence_b_vacuum_abs':'真空场网格散度绝对值',
}
for prefix,label in [('field','总磁场'),('response_field','响应磁场'),('velocity','流速')]:
    for component in ('r','phi','z'):
        LABELS[f'{prefix}_{component}']=f'{label} {component} 分量'
SPECIAL = {
 'convergence_checkpoint_means':'流速与力残差体平均',
 'convergence_checkpoint_rms':'流速与力残差体 RMS',
 'convergence_checkpoint_peaks':'压强、场强及流速峰值',
 'convergence_checkpoint_field_means':'压强及磁场体平均',
 'convergence_checkpoint_velocity_change_rate':'流速变化率体 RMS',
 'convergence_wall_clock_timings':'每次外迭代实际耗时',
 'convergence_ad_vacuum':'真空场插值器 JAX AD 散度',
 'convergence_ad_response':'响应场插值器 JAX AD 散度',
 'convergence_ad_total':'总场插值器 JAX AD 散度',
 'convergence_final_divergence_precision':'末态高精度散度核验 · 节点与离网格点',
}


def entry(path):
    stem=path.stem
    category=stem.split('_',1)[0]
    step=50
    if category=='section':
        key=stem[len('section_'):]
        title=LABELS.get(key,key)
        caption='完整第 50 步；0° / 30° / 60°，壁内 contourf + contour；叠加真实壁、计算域与初始 VMEC 参考。'
        if key.startswith('divergence_'):
            caption+=' 此图为四阶网格差分散度，不是解析源场或插值器 AD 散度。'
    elif category=='profile':
        key,coordinate=stem[len('profile_'):].rsplit('_',1)
        if stem=='profile_rotational_transform_initial_vmec_s':
            key,coordinate='rotational_transform','初始 VMEC s'
        title=LABELS.get(key,key)+' · '+coordinate
        caption=('s / ρ 为各自数据的标签；HINT 为截面面积分箱，不是假定存在磁面后的磁面平均。'
                 if coordinate in ('s','rho') else '固定位置剖面；取样位置和单位见坐标标注。')
        if key=='rotational_transform':
            category='iota'
            caption='每截面 191 个初始 VMEC s 起点；512 场周期、每周期 128 个积分步。实心为通过检查，空心为未充分解析，失败点不绘制。'
    elif category=='poincare':
        initial='_initial_' in stem
        step=0 if initial else 50
        plane='三截面' if stem.endswith('three_sections') else str(int(stem.rsplit('_',1)[1]))+'°'
        title=f'庞加莱 · 第 {step} 步 · {plane}'
        caption=('138 个中平面径向起点' if initial else '1,422 个壁内起点，含 1,284 个二维网格起点')
        caption+='；统一从 φ=0 追踪最多 500 全环向圈，触壁即停，只画真实截面交点。'
    elif category=='convergence':
        step=None
        title=SPECIAL.get(stem,'Step-B 存储诊断 · '+stem.rsplit('_',1)[-1])
        if stem=='convergence_final_divergence_precision':
            step=50
            caption='第50步：每类32768个壁内节点及32768个离网格点，float64 AD；另以扩展精度多项式导数交叉核验。数值求导精确不代表场散度接近零。'
        elif '_ad_' in stem:
            caption='直接读取每个外迭代保存的 JAX AD 统计量；作用于 component 插值器，不代表解析源场散度。'
        elif '_checkpoint_' in stem:
            caption='0–50 步完整保存态；R 加权体统计，分别显示壁内及壁内演化 0≤s<1 区域；max 为网格峰值。'
        elif stem.endswith('timings'):
            caption='运行日志中的 Step-A、Step-B 和完整外迭代墙钟时间；不同于归一化弛豫时间。'
        else:
            caption='每个外迭代最后一个 Step-B 内步；保留求解器归一化，勿与 SI 或局域相对力残差混用。'
    else:
        raise ValueError(f'Uncatalogued figure: {path.name}')
    data=path.read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    width,height=struct.unpack('>II',data[16:24])
    checksum=hashlib.sha256(data).hexdigest()
    return dict(id=stem,category=category,title=title,caption=caption,outer_step=step,
                file='../figures/'+path.name+'?v='+checksum[:12],width=width,height=height,bytes=len(data),
                sha256=checksum)


def table(rows):
    return '<div class="table-scroll"><table><thead><tr><th>指标</th><th>数值</th><th>口径</th></tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows
    )+'</tbody></table></div>'


def build():
    summary=json.loads((DATA/'run_summary.json').read_text())
    checkpoints=json.loads((DATA/'checkpoint_reductions.json').read_text())
    provenance=json.loads((DATA/'provenance.json').read_text())
    precision=json.loads((DATA/'final_ad_precision.json').read_text())
    iota=json.loads((DATA/'iota_summary.json').read_text())
    iotatable=table([(f"{r['phi_degrees']:.0f}°",f"{r['resolved']} / {r['finite']} / {r['requested']}",
                     f"通过检查 / 有限 / 总起点；轴闭合误差 {r['axis_closure_m']:.3g} m") for r in iota])
    if provenance.get('postprocess_axis_warnings'):
        iotatable+='<p class="notice">磁轴定位沿用本算例 axis_residual_tolerance_scale=100 的网格容差；出现未达到严格非线性阈值的警告，未另行放宽容差。轴定位误差也是旋转变换的误差来源。</p><ul>'+''.join('<li><code>'+html.escape(w)+'</code></li>' for w in provenance['postprocess_axis_warnings'])+'</ul>'
    config=tomllib.loads((CASE/'ncsx_main.toml').read_text())
    figures=[entry(p) for p in sorted((CASE/'figures').glob('*.png'))]
    expected_fields={'section_'+name for name in summary['fields']}
    assert expected_fields.issubset({f['id'] for f in figures})
    assert summary['outer_step']==50 and config['solver']['magnetic_interpolation']=='component'
    counts=Counter(f['category'] for f in figures)
    manifest=dict(version='2.2.0',outer_step=50,configuration=config,provenance=provenance,
                  figure_counts=dict(counts),figures=figures)
    (DATA/'results.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    priorities=['poincare_final_three_sections','section_pressure','convergence_checkpoint_means',
                'profile_pressure_s','section_force_residual_relative',
                'profile_rotational_transform_initial_vmec_s','poincare_initial_three_sections']
    figures.sort(key=lambda f:(priorities.index(f['id']) if f['id'] in priorities else 99,f['id']))
    cards=[]
    for f in figures:
        cards.append(f'''<article id="figure-{f['id']}" class="figure-card" data-category="{f['category']}" data-id="{f['id']}">
<a class="image-link" href="{f['file']}" aria-label="查看原图：{html.escape(f['title'])}"><img src="{f['file']}" alt="{html.escape(f['title'])}" width="{f['width']}" height="{f['height']}" loading="lazy" decoding="async"></a>
<div class="figure-text"><span class="category">{GROUPS[f['category']]}</span><h2>{html.escape(f['title'])}</h2><p>{html.escape(f['caption'])}</p>
<div class="figure-foot"><small>{f['width']} × {f['height']} px</small><a href="{f['file']}" download>下载 PNG</a></div><code>{f['id']}</code></div></article>''')
    tabs=f'<button class="category-tab active" data-category="all" aria-pressed="true">全部 <small>{len(figures)}</small></button>'
    tabs+=''.join(f'<button class="category-tab" data-category="{k}" aria-pressed="false">{v} <small>{counts[k]}</small></button>' for k,v in GROUPS.items())
    last=summary['last']; diag=last['diagnostic']; ad=last['magnetic_statistics']; fields=checkpoints[-1]
    metrics=[('外迭代 / 内步','50 / 1000','达到预定迭代上限，程序正常结束'),
             ('初始化总耗时',f"{summary['initialization'][0]['initialization_elapsed_s']:.3f} s",'包括初始化诊断与第0步输出'),
             ('第 50 步完整耗时',f"{last['outer_elapsed_s']:.3f} s",'墙钟时间'),
             ('第 50 步 Step-A / Step-B',f"{last['stage_seconds']['Step-A']:.3f} / {last['stage_seconds']['Step-B']:.3f} s",'墙钟时间'),
             ('动能',f"{diag['kinetic_energy']:.8g}",'Step-B 归一化存储值'),
             ('力残差 RMS',f"{diag['force_rms']:.8g}",'Step-B 归一化存储值；非相对力残差'),
             ('壁内流速体平均',f"{fields['speed_wall_mean']:.8g} m/s",'R 加权；完整第 50 步'),
             ('壁内压强峰值',f"{fields['pressure_wall_max']:.8g} Pa",'网格峰值，不是磁轴插值值')]
    adrows=[]
    for key,label in [('vacuum','真空場'),('response','响应场'),('total','总场')]:
        adrows.extend([(label+' AD 平均归一化散度',f"{ad[f'divb_ad_{key}_mean_normalized']:.8g}",'无量纲；component 插值器'),
                      (label+' AD 绝对均值 / 最大值',f"{ad[f'divb_ad_{key}_mean_abs']:.8g} / {ad[f'divb_ad_{key}_max']:.8g} T/m",f"壁内 {ad[f'divb_ad_{key}_sample_count']} 个网格节点")])
    precisionrows=[]
    for key,label in [('vacuum','真空场'),('response','响应场'),('total','总场')]:
        for scope,where in [('nodes_wall','节点'),('offgrid_wall','离网格')]:
            values=precision['fields'][key][scope]
            precisionrows.append((label+' / '+where+' / 平均归一化',f"{values['divergence_relative_mean']:.10g}",f"{values['sample_count']}个壁内样本；无量纲"))
            precisionrows.append((label+' / '+where+' / 绝对均值与最大值',f"{values['divergence_mean_abs']:.10g} / {values['divergence_max']:.10g} T/m",'实际分量插值场的散度'))
        check=precision['fields'][key]['independent_polynomial_check']
        precisionrows.append((label+' / AD与独立导数最大差',f"{check['max_abs_difference_t_per_m']:.10g} T/m",f"{check['samples']}离网格点；此值是求导误差而非磁场散度"))
    inputnames=['ncsx_main.toml','ncsx_follow.toml','ncsx_post.toml','inputs/ncsx_coils.txt','inputs/NCSX_physical_vessel_half_period.txt']
    links=''.join(f'<li><a href="../{name}" download>{name}</a></li>' for name in inputnames)
    safe_json=json.dumps(figures,ensure_ascii=False).replace('<','\\u003c')
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCSX · 第50步 | HINT-debug 2.2.0</title><meta name="description" content="NCSX当前50步结果：VMEC初始化、无压强再放缩、分量插值。收敛曲线、剖面、截面、庞加莱和旋转变换。">
<link rel="stylesheet" href="assets/results.css"><script src="assets/results.js" defer></script></head><body>
<a class="skip" href="#gallery">跳至图片</a><aside><a class="brand" href="#top">NCSX<span>HINT-debug 2.2.0 / 第 50 步</span></a>
<p class="case-name">EX-NCSX-debug-vmec-unscale-component</p><nav aria-label="结果导航"><a class="source-link" href="../../Source-Code/">程序与使用说明</a><a href="#gallery">结果图集</a><a href="#diagnostics">末步指标</a><a href="#method">计算与统计方法</a><a href="#inputs">输入与溯源</a></nav>
<div class="case-state"><strong>50 步正常完成</strong><span>完成运行不等同于平衡收敛验收</span><dl><dt>起点</dt><dd>VMEC</dd><dt>压强反馈</dt><dd>scale_after=false</dd><dt>插值</dt><dd>component</dd><dt>边界</dt><dd>R–Z 矩形域</dd></dl></div>
<div class="aside-links"><a href="https://github.com/Yihui-L/HINT-websites/tree/main/EX-NCSX-debug-vmec-unscale-component">GitHub 算例文件</a><a href="../README.md">算例说明</a></div></aside>
<main id="top"><header><p class="eyebrow">HINT / NCSX RESULTS</p><h1>NCSX</h1><p class="subtitle">VMEC 初始化 · 不再放缩压强 · 分量磁场插值</p><div class="meta"><span>完整外迭代 50</span><span>144 × 144 × 144</span><span>nfp = 3</span><span>截面 0° / 30° / 60°</span><span>2026-09-21 完成（北京时间）</span></div></header>
<div class="archive-notice" role="note"><h2>当前任务结果</h2><p>本页面所有图片、输入与指标均来自本次 HINT-debug 2.2.0 任务。初始化图为同一任务第 0 步，演化后截面与剖面为完整第 50 步，历史曲线覆盖保存的 0–50 步。</p><p class="archive-scope">50 次外迭代，每次 Step-B 1000 内步；VMEC 起点不执行压强攀升。达到预定步数正常结束，未据此宣称力平衡已收敛。</p></div>
<section id="gallery" aria-label="结果图片"><div class="gallery-toolbar"><div class="tabs" role="group" aria-label="图片分类">{tabs}</div><label>检索图片<input id="figure-search" type="search" placeholder="压强、流速、力残差、iota、变量名"></label><output id="figure-count" aria-live="polite">{len(figures)} 张图片</output></div><div class="gallery-grid">{''.join(cards)}</div><p id="empty" hidden>没有匹配的图片。</p></section>
<section id="diagnostics"><h2>第 50 步指标</h2>{table(metrics)}<h3>已存插值器 AD 散度</h3>{table(adrows)}<p class="notice">AD 对 component 插值器求导，不是直接对平滑核心 Biot–Savart 或 virtual-casing 解析源场求导。它与四阶 HINT 网格差分散度不同，也不能单独作为平衡收敛判断。</p><h3>结束后的高数值精度散度核验</h3>{table(precisionrows)}<p>此核验未修改磁场、网格或插值器。双精度 JAX 自动微分没有有限差分步长截断误差；另外直接对相同四点 Lagrange 多项式解析求导，使用 {precision['independent_precision_bits']} 位尾数的扩展精度作独立计算。完整 RMS、分位数、采样最小值与误差见 <a href="docs-data/final_ad_precision.json">核验数据</a>。最大值仅对已采样点成立，不是全空间严格上界。</p></section>
<section id="method" class="prose"><h2>计算与统计方法</h2>
<h3>主程序与输入</h3><p>真空场由线圈文本、总电流及 50 A/mm² 参考电流密度的平滑核心模型计算，自动按线圈对称性补全。当前任务不使用 mgrid。VMEC 初始化遵循 FIELDLINES 分区：LCFS 内使用 wout 总场，外部使用线圈场加 B virtual-casing 响应场；随后直接演化 B，kdivb=10⁻⁴。壁用于磁力线截断，响应场法向边界约束位于矩形计算域，并冻结 VMEC 初始值；真空场不施加该约束。</p>
<h3>截面、剖面和相对力残差</h3><p>所有末态图取完整第 50 步。截面为壁内 contourf 叠加 contour；黑线为真实壁，虚线为计算域与初始 VMEC 参考。s、ρ 曲线采用截面面积分箱，不能视为严格磁面平均。R 剖面固定 Z=0，Z 与 φ 剖面固定 R=1.57 m；φ 剖面还固定 Z=0。VMEC 参考只在有效内部区域使用，不向外推。</p><p>局域相对力残差为 |J₁×B−∇p| / max(|J₁×B|,|∇p|)。分母低于有效区域最大值的 10⁻¹⁰ 时屏蔽，不用人为下限替代。其他力、电流及散度空间导数使用当前程序的四阶网格算符。</p>
<h3>历史曲线</h3><p>场量平均和 RMS 采用柱坐标 R 体积权重，分别统计壁内和壁内演化 0≤s&lt;1 区域；网格最大值不使用体积权重。Step-B 曲线直接读取每个外迭代最后内步的归一化存储值。速度变化率以相邻完整保存态之差除以换算弛豫时间，不是实验加速度。VMEC 起点没有 20 步压强攀升，故图中不添加第 20 步攀升结束线。</p><p>插值器 AD 主指标为 mean(hᵢ|div Bᵢ|)/mean(|Bᵢ|)，hᵢ=min(ΔR,ΔZ,RᵢΔφ)；它是采样点算术平均，不是 R 加权体平均。RMS 与最大值另列。初始化与每外迭代每类场取壁内 1024 个网格节点。</p>
<h3>哪些散度指标具有参考意义？</h3><ul><li>四阶网格差分：对当前离散演化算符及 kdivb 项有直接参考意义；粗网格截断误差可能较大，不能据此断言输入连续场违反无散条件。</li><li>当前 component 插值器的 AD 散度：对磁力线追踪实际调用的插值场有直接参考意义，数值求导高精度；不能等同于原始连续源场的散度，也不自动等同于磁结构误差。</li><li>节点处四点 Lagrange 模板会切换，插值器不保证全域一阶导数连续。节点 AD 指程序选定模板分支的导数，不能理解为唯一双侧导数；离网格探针位于单元1/4或3/4处，避开切换面，独立高精度核验也仅针对这些离网格点。</li><li>AD 与独立扩展精度多项式求导之差：用于验证求导实现与舍入误差，无权替代磁场散度值。即使两种求导相差很小，所求场的散度仍可能明显非零。</li><li>连续线圈模型的解析无散性质不意味着其粗网格分量插值也无散。最终响应场已经演化，不能借用初始化 virtual-casing 的解析性质宣称末态散度为10⁻¹⁵；本页不通过换插值器或投影来制造低散度结果。</li></ul>
<h3>庞加莱</h3><p>所有截面共用 φ=0 起点。末态采用 128 个初始 VMEC s∈[0,1] 径向起点、10 个 LCFS 外起点和 1284 个壁内二维网格起点，共 1422 个；初始化图保留同一任务此前的 138 个径向起点。最多追踪 500 个完整 2π 环向圈，每场周期取 128 步，RK4 步长加密控制 rtol=10⁻⁸、atol=10⁻¹⁰。0°、30°、60° 为积分端点，只绘真实交点，不把发射点当回归点；触壁停止。两者起点覆盖不同，不能仅凭点密度变化推断磁结构变化。</p>
<h3>旋转变换</h3><p>每个截面沿初始 VMEC θ=0 取 191 个 s 起点，覆盖 10⁻⁴ 至 0.9999；分别追踪 512 个场周期，利用相对于闭合磁轴的连续 R–Z 极角绕转计算几何 ι。比较前后半窗误差（阈值 0.002）及截面解析度（阈值 0.02）。不同截面独立计算，不是在同一 s 上多点取平均。失败点屏蔽，未通过解析度检查的有限结果以空心点显示。VMEC 曲线已转换到相同几何绕转约定。</p>{iotatable}</section>
<section id="inputs"><h2>输入与溯源</h2><ul>{links}</ul><p>main 为本次实际运行配置；follow 为未执行的续算示例；post 为数值后处理 CLI 示例。网站 PNG 使用公开绘图 API，具体绘图参数见 <a href="../tools/postprocess_ncsx_220_complete.py">图集脚本</a> 与 <a href="../tools/plot_final_poincare.py">末态追踪脚本</a>，不是仅执行 post.toml 所得。</p><p>运行源码提交 <code>{html.escape(provenance['source_commit'])}</code>；<a href="docs-data/provenance.json">输入与源文件 SHA-256</a>；<a href="docs-data/run_summary.json">日志指标</a>；<a href="docs-data/checkpoint_reductions.json">保存态统计</a>；<a href="docs-data/results.json">完整图片清单与校验和</a>。</p><p>不上传 wout、mgrid、主程序/后处理 NetCDF 和缓存。线圈与壁文本已包含；wout 需另行提供，不能仅凭本站文件声称完整可复现。</p></section>
<footer>当前 NCSX 第 50 步结果 · 所有图像为本次任务数据 · <a href="../../Source-Code/">HINT 程序文档</a></footer></main>
<dialog id="viewer" aria-labelledby="viewer-title"><div class="viewer-toolbar"><button id="prev" title="上一张" aria-label="上一张">←</button><button id="next" title="下一张" aria-label="下一张">→</button><div class="viewer-heading"><p class="viewer-archive">HINT-debug 2.2.0 · 当前 NCSX 任务</p><h2 id="viewer-title"></h2></div><a id="original-link" target="_blank" rel="noopener">原始 PNG</a><button id="close-viewer" title="关闭" aria-label="关闭">×</button></div><div class="viewer-scroll"><img id="viewer-image" alt=""><p id="viewer-caption"></p></div></dialog><script id="figure-data" type="application/json">{safe_json}</script></body></html>'''
    (DOCS/'index.html').write_text(page)
    (CASE/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=Documents/index.html"><title>NCSX 第50步结果</title><a href="Documents/index.html">查看当前 NCSX 结果</a></html>\n')
    (CASE/'figures/README.md').write_text('# 当前 NCSX 图集\n\n全部为本次 2.2.0 任务，初始化第0步、末态第50步。详细方法见网站。\n\n'+
        '\n'.join(f'- [{f["title"]}]({f["id"]}.png)' for f in figures)+'\n')
    print(json.dumps(dict(figures=len(figures),categories=dict(counts)),ensure_ascii=False))


if __name__=='__main__':
    build()
