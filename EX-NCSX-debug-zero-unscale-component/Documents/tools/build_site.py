"""Build this case's static result website from verified export metadata."""
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import struct
import tomllib

DOCS = Path(__file__).resolve().parents[1]
SITE = DOCS.parent
DATA = DOCS/'docs-data'
GROUPS = {'convergence':'收敛与耗时', 'section':'二维截面', 'profile':'一维剖面', 'poincare':'庞加莱', 'iota':'旋转变换'}
LABELS = {
    'pressure':'压强', 's':'演化 s 标签', 'rho':'ρ 标签', 'speed':'流速大小',
    'velocity_change_rate':'流速矢量变化率', 'speed_change_rate':'流速大小变化率',
    'field_strength':'总场强', 'response_field_strength':'响应场强', 'vacuum_field_strength':'真空场强',
    'force_residual':'力残差大小', 'force_residual_relative':'局域归一化力残差',
    'lorentz_force':'洛伦兹力', 'pressure_gradient':'压强梯度', 'parallel_pressure_gradient':'平行压强梯度',
    'current_density':'响应电流密度大小', 'toroidal_current_density':'环向电流密度 Jφ',
    'parallel_current_density':'平行电流密度', 'enclosed_toroidal_current':'累计环向电流',
    'rotational_transform':'旋转变换 ι', 'divergence_b':'总场网格散度',
    'divergence_b_abs':'总场网格散度绝对值', 'divergence_b_response':'响应场网格散度',
    'divergence_b_response_abs':'响应场网格散度绝对值', 'divergence_b_vacuum':'真空场网格散度',
    'divergence_b_vacuum_abs':'真空场网格散度绝对值',
}
for prefix, label in [('field','总磁场'), ('response_field','响应磁场'), ('velocity','流速')]:
    for component in ('r','phi','z'):
        LABELS[f'{prefix}_{component}'] = f'{label} {component} 分量'
SPECIAL = {
    'convergence_checkpoint_means':'流速与力残差体平均',
    'convergence_checkpoint_rms':'流速与力残差体 RMS',
    'convergence_checkpoint_peaks':'压强、场强及流速峰值',
    'convergence_checkpoint_field_means':'压强及磁场体平均',
    'convergence_checkpoint_velocity_change_rate':'流速变化率体 RMS',
    'convergence_wall_clock_timings':'每次外迭代实际耗时',
    'convergence_final_divergence_precision':'末态插值场高精度散度核验',
}
for method, description in [('ad','分量插值器 JAX AD'), ('fd4','HINT 网格四阶差分')]:
    for field, label in [('vacuum','真空场'), ('response','响应场'), ('total','总场')]:
        SPECIAL[f'convergence_{method}_{field}'] = f'{label} {description} 散度'


def read(name):
    return json.loads((DATA/name).read_text())


def table(rows, headings=('指标','数值','口径')):
    return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in headings)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def entry(path, initial, final):
    stem = path.stem
    category = stem.split('_',1)[0]
    step = 70
    if category == 'section':
        key = stem[len('section_'):]
        title = LABELS.get(key, key)
        caption = '第70步；φ=0°/30°/60°，壁内 contourf + contour；叠加真实壁、计算域和适用的初始 VMEC 参考。'
        if key.startswith('divergence_'):
            caption += '此处为空间网格四阶差分，不是源场解析散度或插值器AD。'
    elif category == 'profile':
        key, coordinate = stem[len('profile_'):].rsplit('_',1)
        if stem == 'profile_rotational_transform_initial_vmec_s':
            key, coordinate = 'rotational_transform', '初始 VMEC s'
        title = LABELS.get(key, key)+' · '+coordinate
        caption = '第70步；s/ρ曲线采用截面面积分箱，非严格磁面平均；R/Z/φ曲线取固定位置。适用量叠加VMEC剖面。'
        if key == 'rotational_transform':
            category = 'iota'
            caption = '每截面191个初始VMEC s起点，分别追踪512个场周期。实心通过检查，空心未充分解析；失败点不伪造。'
    elif category == 'poincare':
        is_initial = '_initial_' in stem
        step = 0 if is_initial else 70
        meta = initial if is_initial else final
        plane = '三截面' if stem.endswith('three_sections') else str(int(stem.rsplit('_',1)[1]))+'°'
        title = f'庞加莱 · {"初始真空场" if is_initial else "第70步总场"} · {plane}'
        caption = f"{meta['seeds']}个起点统一从φ=0出发，最多500全环向圈；触壁停止。显示完整计算域，VMEC磁面仅作参考。"
    elif category == 'convergence':
        step = None
        title = SPECIAL.get(stem, 'Step-B存储诊断 · '+stem.rsplit('_',1)[-1])
        caption = '0–70步；第20步虚线标记攀升完成，第21步点线标记续算检查点。'
        if '_checkpoint_' in stem:
            caption += 'R加权体平均/RMS，分别统计壁内和壁内演化0≤s<1区域；峰值不加权。'
        elif '_ad_' in stem:
            caption += '实际component插值器的JAX导数，不等于原始源场散度。'
        elif '_fd4_' in stem:
            caption += '原HINT网格FD4统计，包含网格尺度截断误差。'
        elif stem.endswith('timings'):
            caption += '来自两段实际作业日志；不把等待续算的间隔算作迭代耗时。'
        elif stem.endswith('precision'):
            step = 70
            caption = '第70步：壁内节点和离网格点各32768个；float64 JAX AD，另有2048点扩展精度多项式导数交叉核验。'
        else:
            caption += '每个外步最后一个Step-B内步；保留求解器归一化，非SI或局域相对残差。'
    else:
        raise ValueError(stem)
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', data[16:24])
    digest = hashlib.sha256(data).hexdigest()
    return dict(id=stem, category=category, title=title, caption=caption, outer_step=step,
                file='../figures/'+path.name+'?v='+digest[:12], width=width, height=height,
                bytes=len(data), sha256=digest)


def build():
    summary, provenance = read('run_summary.json'), read('provenance.json')
    precision, sources = read('final_ad_precision.json'), read('initial_source_ad.json')
    initial, final = read('poincare_initial_metadata.json'), read('poincare_final_metadata.json')
    iota, reductions = read('iota_summary.json'), read('checkpoint_reductions.json')
    config = tomllib.loads((SITE/'ncsx_main.toml').read_text())
    follow = tomllib.loads((SITE/'ncsx_follow.toml').read_text())
    assert summary['outer_step']==70 and provenance['version']=='2.3.0'
    assert config['solver']['start_point']=='zero' and follow['solver']['outer_steps']==49
    assert [row['outer'] for row in reductions]==list(range(71))
    figures = [entry(path, initial, final) for path in sorted((SITE/'figures').glob('*.png'))]
    assert {'section_'+key for key in summary['fields']} <= {f['id'] for f in figures}
    counts = Counter(f['category'] for f in figures)
    manifest = dict(version='2.3.0', outer_step=70, configuration=config, follow_configuration=follow,
                    provenance=provenance, figure_counts=dict(counts), figures=figures)
    (DATA/'results.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    priorities = ['poincare_final_three_sections','poincare_initial_three_sections','section_pressure',
                  'convergence_checkpoint_means','profile_pressure_s','section_force_residual_relative',
                  'profile_rotational_transform_initial_vmec_s']
    figures.sort(key=lambda f:(priorities.index(f['id']) if f['id'] in priorities else 99, f['id']))
    cards = []
    for figure in figures:
        f = figure
        vectors = ''.join(f' <a href="../figures/{f["id"]}.{suffix}" download>{label}</a>' for suffix,label in [('pdf','PDF'),('svg.gz','SVG (gzip)')] if (SITE/'figures'/f'{f["id"]}.{suffix}').exists())
        cards.append(f'''<article id="figure-{f['id']}" class="figure-card" data-category="{f['category']}" data-id="{f['id']}"><div class="figure-text"><span class="category">{GROUPS[f['category']]}</span><h2>{html.escape(f['title'])}</h2><p>{html.escape(f['caption'])}</p></div><a class="image-link" href="{f['file']}" aria-label="查看原图"><img src="{f['file']}" alt="{html.escape(f['title'])}" width="{f['width']}" height="{f['height']}" loading="lazy" decoding="async"></a><div class="figure-text"><div class="figure-foot"><small>{f['width']} × {f['height']} px</small><a href="{f['file']}" download>PNG</a>{vectors}</div><code>{f['id']}</code></div></article>''')
    tabs = f'<button class="category-tab active" data-category="all" aria-pressed="true">全部 <small>{len(figures)}</small></button>'+''.join(f'<button class="category-tab" data-category="{k}" aria-pressed="false">{label} <small>{counts[k]}</small></button>' for k,label in GROUPS.items())
    last, checkpoint = summary['last'], reductions[-1]
    diag, magnetic = last['diagnostic'], last['magnetic_statistics']
    metrics = [('外迭代 / 每步内迭代','70 / 1000','正常完成，非平衡收敛验收'),
               ('完成时间',provenance['completed_beijing'],'北京时间'),
               ('初始启动耗时',f"{summary['initialization'][0]['initialization_elapsed_s']:.3f} s",'真空场计算、源AD、诊断及第0步输出'),
               ('最后一步耗时',f"{last['outer_elapsed_s']:.3f} s",'包括Step-A/B、磁轴、诊断及保存'),
               ('最后一步Step-A / Step-B',f"{last['stage_seconds']['Step-A']:.3f} / {last['stage_seconds']['Step-B']:.3f} s",'墙钟时间'),
               ('动能',f"{diag['kinetic_energy']:.8g}",'Step-B归一化'),
               ('力残差RMS',f"{diag['force_rms']:.8g}",'Step-B归一化，非相对力残差'),
               ('壁内流速体平均',f"{checkpoint['speed_wall_mean']:.8g} m/s",'R加权'),
               ('壁内压强峰值',f"{checkpoint['pressure_wall_max']:.8g} Pa",'网格峰值，非轴上插值压强')]
    sourcerows = []
    for key,label in [('vacuum_domain','真空场 / 全计算域抽样'),('vacuum_wall','真空场 / 壁内抽样'),('response_lcfs_inside','响应场 / LCFS内'),('response_lcfs_outside','响应场 / LCFS外')]:
        value = sources['fields'][key]
        sourcerows.append((label,f"{value['divergence_mean_abs']:.8g} / {value['divergence_max']:.8g} T/m",f"绝对均值/最大值；{value['sample_count']}点；归一化均值{value['divergence_relative_mean']:.8g}"))
    divrows = []
    for method,description in [('fd4','HINT FD4'),('ad','分量插值器AD')]:
        for key,label in [('vacuum','真空场'),('response','响应场'),('total','总场')]:
            prefix = f'divb_{method}_{key}_'
            divrows.append((label+' / '+description, f"{magnetic[prefix+'mean_abs']:.8g} / {magnetic[prefix+'max']:.8g} T/m",f"绝对均值/最大值；{magnetic[prefix+'sample_count']}点；归一化均值{magnetic[prefix+'mean_normalized']:.8g}"))
    precisionrows=[]
    for key,label in [('vacuum','真空场'),('response','响应场'),('total','总场')]:
        for scope,where in [('nodes_wall','节点'),('offgrid_wall','离网格')]:
            value=precision['fields'][key][scope]
            precisionrows.append((label+' / '+where,f"{value['divergence_mean_abs']:.8g} / {value['divergence_max']:.8g} T/m",f"{value['sample_count']}点；归一化均值{value['divergence_relative_mean']:.8g}"))
        check=precision['fields'][key]['independent_polynomial_check']
        precisionrows.append((label+' / 独立求导最大差',f"{check['max_abs_difference_t_per_m']:.8g} T/m",f"{check['samples']}点；这是求导实现误差，不是场的散度"))
    iotatable=table([(f"{r['phi_degrees']:.0f}°",f"{r['resolved']} / {r['finite']} / {r['requested']}",f"通过检查/有限/起点；轴闭合误差{r['axis_closure_m']:.5g} m") for r in iota])
    links=''.join(f'<li><a href="../{name}" download>{name}</a></li>' for name in ('ncsx_main.toml','ncsx_follow.toml','ncsx_post.toml','inputs/ncsx_coils.txt','inputs/NCSX_physical_vessel_half_period.txt'))
    figure_json=json.dumps(figures,ensure_ascii=False).replace('<','\\u003c')
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NCSX 零启动 · 第70步 | HINT-debug 2.3.0</title><meta name="description" content="NCSX零响应启动、20步压强攀升、无后续放缩、70步结果与初始化真空场。"><link rel="stylesheet" href="assets/results.css"><script src="assets/results.js" defer></script></head><body>
<a class="skip" href="#gallery">跳至图片</a><aside><a class="brand" href="#top">NCSX<span>HINT-debug 2.3.0 / 第70步</span></a><p class="case-name">EX-NCSX-debug-zero-unscale-component</p><nav aria-label="结果导航"><a class="source-link" href="../../Source-Code/">程序与使用说明</a><a href="#gallery">结果图集</a><a href="#diagnostics">数值指标</a><a href="#method">计算与统计方法</a><a href="#inputs">输入与溯源</a></nav><div class="case-state"><strong>70步正常完成</strong><span>完成运行不等于力平衡收敛</span><dl><dt>起点</dt><dd>zero，B₁=0</dd><dt>压强攀升</dt><dd>20步</dd><dt>后续反馈</dt><dd>scale_after=false</dd><dt>磁场插值</dt><dd>component</dd></dl></div><div class="aside-links"><a href="https://github.com/Yihui-L/HINT-websites/tree/main/EX-NCSX-debug-zero-unscale-component">GitHub算例文件</a><a href="../README.md">算例说明</a></div></aside>
<main id="top"><header><p class="eyebrow">HINT / NCSX RESULTS</p><h1>NCSX</h1><p class="subtitle">零响应启动 · 20步压强攀升 · 后续不放缩 · 分量插值</p><div class="meta"><span>完整外迭代70</span><span>144 × 144 × 144</span><span>nfp=3</span><span>截面0°/30°/60°</span><span>2026-09-22完成（北京时间）</span></div></header>
<div class="archive-notice" role="note"><h2>本次运行与续算</h2><p>全部图片来自同一零启动任务的0–70步。初始庞加莱使用第0步保存的总场，此时B₁=0，故它就是线圈真空场；VMEC曲线只作参考。所有末态截面、剖面与庞加莱均为第70步。</p><p class="archive-scope">初始配置计划200步，在第22步末的磁轴试探越界后退出，最后完整检查点为21。随后用户将总目标改为70，按原检查点追加49步；没有重新攀升。磁轴接受阈值在检查点调到归一化长度约10⁻⁴。运行正常结束，但未据此宣称力平衡收敛。</p></div>
<section id="gallery" aria-label="结果图片"><div class="gallery-toolbar"><div class="tabs" role="group" aria-label="图片分类">{tabs}</div><label>检索图片<input id="figure-search" type="search" placeholder="压强、流速、力残差、iota、变量名"></label><output id="figure-count" aria-live="polite">{len(figures)}张图片</output></div><div class="gallery-grid">{''.join(cards)}</div><p id="empty" hidden>没有匹配的图片。</p></section>
<section id="diagnostics"><h2>第70步指标</h2>{table(metrics)}<h3>初始化连续源表达式的散度</h3>{table(sourcerows)}<p>平滑核心线圈源表达式直接用float64 JAX求导，不经过HINT网格插值，也没有有限差分步长。响应场初始化恒为零，其两侧散度均严格为零，不调用VMEC响应场或virtual-casing。本次zero初始化不存在LCFS分区磁场拼接；未另外计算“跨LCFS散度”统计。源场小散度只针对该模型及有限样本，不是对插值器或末态的保证。</p><h3>第70步存储散度：两种不同口径</h3>{table(divrows)}<p class="notice">响应场FD4可保持10⁻¹⁵量级，但component插值器AD不必小。前者反映网格离散算符约束，后者是追踪实际调用的分量插值场。二者不可互相替代，更不能把任一个指标单独当作平衡收敛验收。</p><h3>末态插值器的高数值精度复核</h3>{table(precisionrows)}<p>壁内节点和离网格点分别取32768点。float64 JAX AD不含有限差分步长误差；另外以{precision['independent_precision_bits']}位尾数扩展精度对同一Lagrange多项式直接求导，交叉检查2048个离网格点。求导吻合不代表所得散度小。<a href="docs-data/final_ad_precision.json">完整精度数据</a>。</p></section>
<section id="method" class="prose"><h2>计算与统计方法</h2><h3>物理设置与续算</h3><p>直接演化响应磁场B₁；固定线圈背景B₀由文本线圈和50 A/mm²参考电流密度的平滑核心模型计算，不使用mgrid。初始B₁=0，小压强剖面在20个外步内攀升，此后scale_after=false，不再强制轴上压强保持目标。第一壁用于截断追踪，响应场Bn=0的边界位于矩形R–Z计算域，背景场不受此边界条件约束。kdivb=10⁻⁴，Step-B每外步1000内步。</p><p>follow从第21步完整读取B、v、p、演化s、磁轴种子及攀升状态（20/20、scale=1），继续第22–70步并追加原NC。容忍度输入是倍率902.9238869591517，在检查点对应归一化长度10⁻⁴，即1.425×10⁻⁴m；阈值仍随网格和磁轴位置略变，不是恒定绝对容差。磁力线积分精度未放宽。</p>
<h3>截面、剖面与力平衡</h3><p>二维图取0°/30°/60°，contourf叠加contour及真实壁、计算域、初始VMEC参考。压力/环向电流等适用量叠加VMEC。s与ρ剖面按各自标签作截面面积分箱，不假定最终存在嵌套磁面。R剖面固定Z=0；Z和φ剖面固定R=1.57m，φ另固定Z=0。</p><p>局域相对力残差为|J₁×B−∇p| / max(|J₁×B|,|∇p|)。分母低于有效区域最大值10⁻¹⁰时屏蔽；空间导数采用现有四阶网格算符。虚线VMEC参考不是对最终平衡的约束。</p>
<h3>演化曲线与散度解释</h3><p>历史曲线覆盖所有完整保存态0–70，未把失败的未保存第22步重复拼入。第20步虚线是攀升结束，第21步点线为续算检查点。平均/RMS采用柱坐标R体积权重，分别显示壁内及壁内演化0≤s&lt;1区；峰值不加权。Step-B存储量保持求解器归一化，其他曲线标SI单位。速度变化率使用相邻保存态之差除以归一化时间换算的弛豫时间，不是实验加速度。零值采用线性或适当的对数显示，不人为加正数。</p><p>散度平均归一化定义为mean(hᵢ|divBᵢ|)/mean(|Bᵢ|)，hᵢ=min(ΔR,ΔZ,RᵢΔφ)，这里是采样点算术平均而不是体积加权。主程序存储AD为1024个壁内节点；FD4遍历687944个壁内网格点。粗网格FD4的截断误差可能明显，适合诊断离散演化，不等同于源场解析散度。component节点处可能切换模板，节点AD是所选分支的导数；离网格精度核验避开切换面。末态响应场没有可直接复用的初始化解析表达式。</p>
<h3>庞加莱</h3><p>初始真空场使用{initial['seeds']}个φ=0、Z=0起点（128个初始VMEC s∈[0,1]、10个外侧点）；末态另补二维壁内网格，共{final['seeds']}个起点。每组起点只追踪一次，通过同一轨道获取0°/30°/60°交点；最多500整环圈，最大环向步长为一个场周期的1/128（自适应步长可更小），使用当前GPU/JAX后处理积分器，rtol=10⁻⁸、atol=10⁻¹⁰。触壁停止，失败点不补造。点密度不同不能直接解释为磁结构变化。图中叠加s=0、0.25、0.5、0.75、1的VMEC参考，并显示完整计算域。</p>
<h3>旋转变换</h3><p>每截面取191个初始VMEC θ=0起点，s覆盖10⁻⁴至0.9999，分别追踪512场周期。由相对闭合磁轴的连续R–Z极角绕转求几何ι，前后半窗误差阈值0.002、截面解析度阈值0.02。不是同一s多点平均；有限但未通过检查的值绘为空心，失败值屏蔽。VMEC曲线转换到相同绕转约定。后处理沿用第70步存储的磁轴容忍度，不另行放宽。</p>{iotatable}</section>
<section id="inputs"><h2>输入与溯源</h2><ul>{links}</ul><p>main为实际初始运行输入（计划200步），follow为实际追加49步的输入，不是未使用的示例；post为末态数值后处理CLI配置示例。图集由现有hint_debug_plotting公开API生成，完整脚本在<a href="../tools/export_zero70.py">导出入口</a>与<a href="../tools/postprocess_zero70.py">绘图脚本</a>，并非只运行post.toml的默认30个起点。</p><p>源码版本2.3.0，提交<code>{provenance['source_commit']}</code>。<a href="docs-data/provenance.json">来源与SHA-256</a> · <a href="docs-data/run_summary.json">耗时与日志指标</a> · <a href="docs-data/checkpoint_reductions.json">各步场量统计</a> · <a href="docs-data/initial_source_ad.json">初始源场AD</a> · <a href="docs-data/results.json">图像清单</a>。</p><p>不上传wout、mgrid、主程序/后处理NC、追踪数组和缓存。PNG用于网页，庞加莱保留PDF与无损压缩SVG；未对矢量点栅格化。复现须另行提供同哈希wout与本次输出数据，并调整脚本中部署路径。</p></section><footer>本次NCSX零启动0–70步结果 · <a href="../../Source-Code/">HINT程序文档</a></footer></main>
<dialog id="viewer" aria-labelledby="viewer-title"><div class="viewer-toolbar"><button id="prev" title="上一张" aria-label="上一张">←</button><button id="next" title="下一张" aria-label="下一张">→</button><div class="viewer-heading"><p class="viewer-archive">HINT-debug 2.3.0 · 零启动</p><h2 id="viewer-title"></h2></div><a id="original-link" target="_blank" rel="noopener">原始PNG</a><button id="close-viewer" title="关闭" aria-label="关闭">×</button></div><div class="viewer-scroll"><p id="viewer-caption"></p><img id="viewer-image" alt=""></div></dialog><script id="figure-data" type="application/json">{figure_json}</script></body></html>'''
    (DOCS/'index.html').write_text(page)
    (SITE/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=Documents/index.html"><title>NCSX零启动第70步</title><a href="Documents/index.html">查看完整结果</a></html>\n')
    (SITE/'figures/README.md').write_text('# 零启动0–70步图集\n\n'+ '\n'.join(f'- [{f["title"]}]({f["id"]}.png)' for f in figures)+'\n')
    print(json.dumps(dict(figures=len(figures), categories=dict(counts)), ensure_ascii=False))


if __name__ == '__main__':
    build()
