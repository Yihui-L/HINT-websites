# VMEC、线圈与第一壁

## wout 的角色

VMEC 用嵌套磁通面坐标表达平衡。本程序从 wout 读取傅里叶几何、nfp、对称性、压力、电流信息，并将它们转换到柱坐标网格；HINT 后续不再要求这些磁面保持存在。

几何使用 cos/sin 傅里叶展开；非仿星器对称平衡保留相应非对称系数。VMEC 半网格磁场系数在径向插值时排除轴上占位项，奇 m 模按 sqrt(s) 的轴正则性处理。径向插值使用程序封装的插值策略，几何角向导数由傅里叶展开解析计算，不用随意差分 wout 表格。

VMEC 逆变基矢场转换到物理柱坐标分量：

$$B_R=B^\theta\partial_\theta R+B^\phi\partial_\phi R,\quad B_Z=B^\theta\partial_\theta Z+B^\phi\partial_\phi Z,\quad B_\phi=R B^\phi.$$

这就是不能只用某个面的 `dI/ds` 推出该面所有点电流矢量的原因：还需要三维几何、完整平衡场及其导数。

压力源采用 wout `presf` 表；lambda 源采用 `jdotb/bdotb`，不把 ac 多项式直接当作局部电流密度。VMEC 中用于直磁力线坐标的 λ 与本程序平行电流形状 λ 同名但**物理含义不同**。

## 线圈文本与全装置补全

新 initial 输入弃用 mgrid；`paths.coils` 提供 `.txt/.dat` 文本，头三行为 `HINT_COILS 1`、`nfp N`、`stellarator_symmetric true/false`，不使用等号。随后每块为 `coil 名称 总电流_A stellarator/periodic/none`、多行 XYZ 米制坐标、`end`。闭合曲线至少八个独立点，末点重复首点。正电流沿点序方向，负电流反向。

`stellarator` 表示半周期代表线圈，先按 `(x,y,z)->(x,-y,-z)` 且 **I 变号**生成镜像，再旋转补全所有 nfp 周期。`periodic` 只旋转，`none` 不复制；后两种覆盖方式必须在补全后仍满足整个装置的对称性。自对称复制只计一次，不同输入块生成同一物理线圈则报错。提供的是整条闭合线圈，不是裁切到半周期的开弧。线圈、壁、wout 的周期和对称性必须一致。

文件电流是该曲线代表的总有效电流，不再额外乘匝数、电流组倍率、场周期数或全局 scale。完整格式见 [线圈协议](source:debug:docs/COIL_FILE_FORMAT.md)。

## 有限圆截面与无散磁场

`vacuum.current_density_a_mm2` 是必填的模型电流密度，不是超导材料 Jc。由每个非零电流计算

$$a=\sqrt{|I|/(\pi J_{\rm ref}10^6)}\;\mathrm m.$$

截面内均匀电流沿局部线圈切向，体积积分包括曲率度量。程序计算全装置线圈的磁矢势，再得到网格背景场和保无散插值表示。近线圈采用观察点投影为中心的截面极坐标，对径向可积奇点解析积分，配合长度方向自适应求积；不使用任意软化分母，不进行磁场限幅。

网格取 `B0=curl_h(A0)`，使用与 HINT 四阶散度配套的差分；离网格取周期五次矢势样条的解析旋度。两种散度分别检验，同时比较独立源积分导数得到的场值，不能用无散恒等式代替物理保真检验。壁只选择诊断范围，不参与真空场加权、裁剪或边界投影。`quadrature_tolerance` 默认 1e-5，不等于插值误差或散度阈值。

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

源码：[VMEC](source:debug:src/hint_debug/preprocess/vmec.py)、[线圈体积分](source:debug:src/hint_debug/preprocess/coils.py)、[背景场](source:debug:src/hint_debug/preprocess/vacuum.py)、[壁协议](source:debug:src/hint_debug/preprocess/wall_file.py)。
