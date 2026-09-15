# VMEC、线圈与第一壁

## wout 的角色

VMEC 用嵌套磁通面坐标表达平衡。本程序从 wout 读取傅里叶几何、nfp、对称性、压力、电流信息，并将它们转换到柱坐标网格；HINT 后续不再要求这些磁面保持存在。

几何使用 cos/sin 傅里叶展开；非仿星器对称平衡保留相应非对称系数。VMEC 半网格磁场系数在径向插值时排除轴上占位项，奇 m 模按 sqrt(s) 的轴正则性处理。径向插值使用程序封装的插值策略，几何角向导数由傅里叶展开解析计算，不用随意差分 wout 表格。

VMEC 逆变基矢场转换到物理柱坐标分量：

$$B_R=B^\theta\partial_\theta R+B^\phi\partial_\phi R,\quad B_Z=B^\theta\partial_\theta Z+B^\phi\partial_\phi Z,\quad B_\phi=R B^\phi.$$

这就是不能只用某个面的 `dI/ds` 推出该面所有点电流矢量的原因：还需要三维几何、完整平衡场及其导数。

压力源采用 wout `presf` 表；lambda 源采用 `jdotb/bdotb`，不把 ac 多项式直接当作局部电流密度。VMEC 中用于直磁力线坐标的 λ 与本程序平行电流形状 λ 同名但**物理含义不同**。

## mgrid 的 R / S 模式

设第 g 组的实际输入电流为 I_g=`extcur_a[g]`，整体倍率 f=`field_scale`：

$$\mathbf B_0=f\sum_g I_g\mathbf B_g\quad(S\text{ 模式：组场单位 T/A}),$$

$$\mathbf B_0=f\sum_g\frac{I_g}{I_{g,\rm raw}}\mathbf B_g\quad(R\text{ 模式：组场为原参考电流产生的 T}).$$

`raw_coil_cur` 为 R 模式参考电流。参考电流为零而用户要求非零电流无法缩放，程序报错。旧文件缺少模式元数据时会警告并按兼容约定解释；显式未知模式不应猜测。`extcur_a` 长度按文件线圈组数确定，不再引入模糊的“group-current 倍率”。

mgrid 一个场周期内的数据应当已由**全装置线圈**计算得到；HINT 不会把一个周期的近场线圈单独当成全装置真空场。只有目标网格是一个场周期。

插值将源 mgrid 的合成场重采样到 HINT 网格。`cubic` 与 `linear` 影响采样误差和耗时；源点数量、坐标方向、范围必须合法，不外推填充矩形域。

## 极强场限幅与散度

先在未限幅背景场中求 VMEC 磁轴 φ=0 处模 B_axis，设置 B_cap=`max_field_axis_ratio`×B_axis。超过阈值的向量乘 B_cap/|B|，保持方向。源 mgrid 合成场和最终插值场都受该限制。

$$\mathbf B_{\rm limited}=\mathbf B\min(1,B_{\rm cap}/|\mathbf B|).$$

**限幅不保散度，也不保持原线圈精确解。** 它是线圈附近奇异/极强场的数值处理，阈值过低可能影响等离子体附近的真实场。应检查限幅点数、阈值、最大场、插值后散度及其空间位置。程序不自动清除 B₀ 的全部离散散度。

## 壁文本协议

所有壁信息在一个文本中，当前主程序不要求用户先生成壁 NetCDF：

```text
HINT_WALL 1
nfp = 3
stellarator_symmetric = true
toroidal_planes = 4
poloidal_points = 64
DATA
# 每行 phi_rad R_m Z_m；此处仅说明布局，不是完整壁数据
```

DATA 后必须有 `toroidal_planes*poloidal_points` 行，按平面优先排列。同一平面所有行的 φ 相同；R>0，数值有限，使用 e/E 浮点指数而不是 Fortran D 指数。支持 # 注释和空行。不要把注释布局示意当作完整可运行壁。

| 壁类型 | φ 数据范围 | 端点处理 |
|---|---|---|
| 轴对称 2D | 单平面，φ=0 | 一个闭合 R–Z 轮廓 |
| 仿星器对称 3D | 0 到 π/nfp，均匀，至少 4 平面 | 包含两端，端面对称一致；内部补为一场周期 |
| 非对称 3D | 0 到 2π/nfp，均匀，至少 6 平面 | 包含末端且与首端逐点闭合，内部去掉重复平面 |

极向每平面至少 4 点，不重复首点作为末点；各平面对应点需表示同一极向序列，方向一致。建议角度保留约 17 位有效数字。壁 `nfp` 必须等于 wout，壁对称性必须等于 `not lasym`，不能由文件名猜测。

主程序检查 **LCFS 严格在壁内、壁严格在矩形域内**，并要求壁外至少配置的网格层余量。壁几何生成 signed distance（正值在内）、外法向、有效掩膜，写入统一结果。即使 debug 的磁边界在矩形上，真实壁仍参与压力、源项支撑区域和后处理可用区。

源码：[VMEC](source:debug:src/hint_debug/preprocess/vmec.py)、[mgrid](source:debug:src/hint_debug/preprocess/vacuum.py)、[壁协议](source:debug:src/hint_debug/preprocess/wall_file.py)、[几何](source:wall:src/hint_wall/preprocess/wall.py)。
