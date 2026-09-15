# 后处理与 Notebook

## 数值 CLI 按内容分类

后处理读取统一结果，`selection.record=-1` 默认选择最后完整状态；`requested_time` 提供时选最近完整时间，不做状态插值。至少启用一个内容。

| TOML 表 | 内容 | 关键限制 |
|---|---|---|
| fields | 场采样、导数与磁场指标 | 壁外 −1；导数有效区需额外掩膜 |
| force_balance | 力平衡、梯度、电流等 | 使用响应电流与当前总场；不是重复读初始源项 |
| magnetic_axis | 当前场磁轴 | 保存轴作热启动，并重新验证闭合 |
| field_lines | 普通弧长磁力线及兼容边界模式 | 线性 R–Z 起点序列 |
| poincare | 周期截面交点 | 一个场周期，不是每步都输出完整环向圈 |
| flux_surfaces | 可解析磁面的积分量 | 散布/积分精度不合格需保留失败状态 |
| boundary_trace | 边界曲线追踪 | 内部固定 mode=vmec；名字不表示调用 VMEC 求解器 |
| convergence | 保存的 Step-B 历史 | 无法恢复没有存储的内部诊断 |

旧 `magval/gprts/hmag` 分别是 `fields/force_balance/field_lines` 的兼容别名，同一输入不能同时给新旧表。共有 HMAGConfig 中某些参数被内容分支覆盖或不使用，完整参数表逐项说明，不建议把所有公共字段都复制到每个表。

追踪圈数的接口差异：CLI `flux_surfaces.surface_circuits` 按完整 2π 环向圈计，源码乘 nfp 扩展到场周期；CLI `poincare.boundary_points` 和 Notebook `crossings` 按场周期回归计。三个量不能直接等值替换。

## Python 绘图入口

```python
from hint_debug_plotting import HintPlots, variable_catalog

plots = HintPlots(
    "run/equilibrium.nc",         # 稳定结果或安全副本
    wout="inputs/wout_case.nc",    # 可选；叠加 VMEC 时必需
    outer_step=100,               # 可省略，使用最后完整状态
    backend="cpu", engine="jax",
)
print(variable_catalog())
```

wall 使用 `hint_wall_plotting`。`outer_step` 与 `record` 不可同时给出；record 是保存记录序号，不是步号。构造对象不会启动主程序，不修改结果。传入的 wout 需同一算例、周期与对称性一致；仅凭 nfp 匹配仍不能替代用户确认正确文件。

### 二维截面

```python
figure = plots.sections(
    "pressure", levels=48, contour_lines=12,
    vmec_surfaces=(0, .25, .5, .75, 1),
)
figure.save("figures/pressure.png", dpi=300)
plots.sections("force_residual_relative").save("figures/relative_force.png", dpi=300)
```

默认截面 φ=0、π/(2nfp)、π/nfp，纵向排列，contourf+contour、统一色标、壁与矩形边界。角度是弧度。非对称算例也保留这一默认值，查看整周期需显式改 angles。LCFS 是**初始 VMEC 边界**，不是演化后的 s=1 平台。

`show_lcfs=true` 需 wout；默认叠加 VMEC 磁轴、三张内部面与 LCFS。壁来自保存的距离场零等值线，不要求再次读取壁文本。不存在可比 VMEC 量时不伪造速度/残差参考。

### 一维剖面和时间曲线

```python
plots.profiles("pressure", coordinate="s", bins=50).save("figures/p_s.png", dpi=300)
plots.profiles("toroidal_current_density", coordinate="R", z_m=0.0)
plots.profiles("field_strength", coordinate="Z", r_m=1.5)
plots.profiles("speed", coordinate="phi", r_m=1.5, z_m=0.0)
plots.time_series(["force_rms", "divb_rms", "kinetic_energy"], scale="auto")
plots.time_series("speed", reduction="mean", scope="wall")
```

示例 R/Z 位置必须按装置调整。R/Z 剖面是指定物理线上的采样；φ 剖面覆盖一个场周期，不能再同时给 angles。矢量先插值分量再求模/投影，避免把模的插值误当矢量插值。

s/ρ 剖面用保存的演化标签，按截面**等面积**分箱，显示平均与箱内标准差，不是体平均或严格磁面平均；ρ=sqrt(s)，分箱仍均匀于 s，s=1 外侧桶排除。±标准差不是数值误差棒。点数不足的箱不强行插值补齐。

wout 压力参考用原始 presf；无 wout 时可用内嵌的缩放后目标压力作有限参考。s 图两套曲线分别用自己的标签，不宣称 HINT s 与 VMEC s 为同一磁面；R/Z/φ 参考在相同实空间位置独立反解 VMEC，不外推到 LCFS 外。

`toroidal_current_density` 是点值 J₁φ，A/m²；`toroidal_current` 是标签阈值内 ∫J₁φ dR dZ，A。VMEC 对比用其完整场导数/安培环路积分，不把 jcurv 当局部 Jφ，也不为强行匹配 ctor 再缩放曲线。

### 庞加莱

```python
result = plots.poincare(crossings=256, toroidal_steps=128)
result.save("figures/poincare.png", dpi=300)
```

可通过 `poincare_data` 指定种子和更长追踪，再传 `data=` 重画。有效种子位于第一壁内，不受初始 LCFS 限制；扩大种子范围/加密可显示外侧磁岛，但空白可能是出壁、奇异积分或取样不足，不应人工连接成磁面。启动种子不冒充回归交点。

### 旋转变换 iota

```python
data = plots.rotational_transform_data(
    seed_s=[.02, .1, .2, .4, .6, .8, .95, .99],
    crossings=256, toroidal_steps=128,
    rtol=1e-8, atol=1e-10,
    convergence_tolerance=.002, surface_tolerance=.02,
)
plots.rotational_transform(data=data, coordinate="s")
```

先在**当前磁场**定位磁轴，再连续追踪、展开相对磁轴的极向角，计算长程 Δθ/Δφ，并转换到 VMEC 的角向约定。使用密集自适应 RK4 步长加倍，而非仅凭稀疏庞加莱点 unwrap，以免角度混叠。

默认 32 个初始 VMEC s∈[0.02,0.98]，每个 s、每个环向截面用一个 θ=0 起点。是**同一条磁力线的长程绕转平均**，不是同 s 多起点平均。可加密 seed_s；但随机区里长程绕转存在也不意味着严格磁面存在。

返回有限长度前后半段一致性、角度分辨、表面散布等标志；未通过的有限值用区别标记，失败值掩膜。坐标轴默认 HINT 的起点演化 s/ρ；不能误标为初始 seed_s。独立的 NCSX 结果网站会说明该次加密扫描的特别参数。

## 输出和变量

各绘图方法返回 `PlotResult(figure, axes, data)`，`.save()` 支持 PNG/PDF/SVG；不用图时也可读取 field/section/line/point/temporal。Notebook **不自动创建 analysis.nc**。绘图可用变量名、单位和适用功能由源码自动提取在下方变量索引中。

源码：[绘图 API](source:debug:postprocess/hint_debug_plotting/plots.py)、[变量](source:debug:postprocess/hint_debug_plotting/variables.py)、[iota](source:debug:postprocess/hint_debug_plotting/rotational_transform.py)、[VMEC 对比](source:debug:postprocess/hint_debug_plotting/vmec_reference.py)。
