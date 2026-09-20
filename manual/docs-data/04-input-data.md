# VMEC、线圈与第一壁

## wout 的角色

VMEC 用嵌套磁通面坐标表达平衡。本程序从 wout 读取傅里叶几何、nfp、对称性、压力、电流信息，并将它们转换到柱坐标网格；HINT 后续不再要求这些磁面保持存在。

几何使用 cos/sin 傅里叶展开；非仿星器对称平衡保留相应非对称系数。VMEC 半网格磁场系数在径向插值时排除轴上占位项，奇 m 模按 sqrt(s) 的轴正则性处理。径向插值使用程序封装的插值策略，几何角向导数由傅里叶展开解析计算，不用随意差分 wout 表格。

VMEC 逆变基矢场转换到物理柱坐标分量：

$$B_R=B^\theta\partial_\theta R+B^\phi\partial_\phi R,\quad B_Z=B^\theta\partial_\theta Z+B^\phi\partial_\phi Z,\quad B_\phi=R B^\phi.$$

这就是不能只用某个面的 `dI/ds` 推出该面所有点电流矢量的原因：还需要三维几何、完整平衡场及其导数。

压力源采用 wout `presf` 表；lambda 源采用 `jdotb/bdotb`，不把 ac 多项式直接当作局部电流密度。VMEC 中用于直磁力线坐标的 λ 与本程序平行电流形状 λ 同名但**物理含义不同**。

## 线圈文本与全装置补全

新 initial 输入弃用 mgrid；`paths.coils` 提供 `.txt/.dat` 文本，头三行为 `HINT_COILS 1`、`nfp N`、`stellarator_symmetric true/false`，不使用等号。随后每块为 `coil 名称 总电流_A stellarator/periodic/updown/none`、多行 XYZ 米制坐标、`end`。闭合曲线至少八个独立点，末点重复首点。正电流沿点序方向，负电流反向。

每条线圈可独立选择三种对称生成规则：`stellarator` 同时补全仿星器伙伴和场周期旋转，`periodic` 仅补全场周期旋转，`updown` 仅做 `(x,y,z)->(x,y,-z)` 且保持点序和电流符号不变，不做环向复制。典型 PF 线圈是完整环向圆环，本身轴对称，因此“不做环向复制”不等于破坏场周期性。`none` 表示所有实例已经显式提供。无论哪种规则，补全后的完整电流集合仍须满足文件声明的全局周期性和仿星器对称性；不能把任意不具周期性的线圈放进单周期计算域。

`stellarator` 表示半周期代表线圈，先按 `(x,y,z)->(x,-y,-z)` 且 **I 变号**生成镜像，再旋转补全所有 nfp 周期。`periodic` 只旋转，`none` 不复制；后两种覆盖方式必须在补全后仍满足整个装置的对称性。自对称复制只计一次，不同输入块生成同一物理线圈则报错。提供的是整条闭合线圈，不是裁切到半周期的开弧。线圈、壁、wout 的周期和对称性必须一致。

文件电流是该曲线代表的总有效电流，不再额外乘匝数、电流组倍率、场周期数或全局 scale。完整格式见 [线圈协议](source:debug:docs/COIL_FILE_FORMAT.md)。

## 平滑核心与无散磁场

`vacuum.current_density_a_mm2` 是必填的模型电流密度，不是超导材料 Jc。由每个非零电流计算

$$a=\sqrt{|I|/(\pi J_{\rm ref}10^6)}\;\mathrm m.$$

当前使用近似的平滑核心线圈模型，不再对均匀硬边界圆截面做昂贵体积分：

```text
A(x) = mu0/(4*pi) sum I integral dl'/sqrt(|x-x'|^2+a^2)
a = sqrt(abs(I)/(pi*J_ref*1e6))
```

局部无限长直导线极限下，J(rho)=I*a²/[pi*(rho²+a²)²]，中心密度绝对值为 J_ref，总电流仍为 I；a 是平滑核心尺度，不是工程截面半径。场在核心内有限，远离核心恢复丝状场。每段 A 与其解析 curl(B) 均使用解析积分；周期样条中心线逐级细分，通过 A 和 B 的变化检验精度。全体线圈段共同批处理，不再逐线圈做近场修正。该近似由源模型明确给出，不对最终磁场逐点限幅。模型误差、中心线离散误差和 HINT 网格插值误差需区分，严格无散并不能保证磁面完全正确。

网格直接采样平滑核心的解析 B 积分；离网格使用保持面磁通散度的相容 B 插值。连续源模型无散不意味着采样网格的四阶差分散度恰为机器零。节点值不投影、不平滑，插值后另行检验场值误差及散度。壁只选择诊断范围，不参与真空场加权、裁剪或边界投影。`quadrature_tolerance` 默认 1e-5，不等于插值误差或散度阈值。

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

源码：[VMEC](source:debug:src/hint_debug/preprocess/vmec.py)、[平滑核心线圈积分](source:debug:src/hint_debug/preprocess/coils.py)、[背景场](source:debug:src/hint_debug/preprocess/vacuum.py)、[壁协议](source:debug:src/hint_debug/preprocess/wall_file.py)。
