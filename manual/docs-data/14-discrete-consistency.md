# 离散系统、插值与一致性

## 状态和物理方程

当前两版推进 (A₁,v)，而非 B₁。固定 A₀来自平滑核心线圈解析积分；B₀=curl_h A₀、B₁=curl_h A₁、B=B₀+B₁。J₁=curl_h B₁（归一化）进入完整洛伦兹力。时间规范下：

$$ \partial_t A_1=v\times B-\eta(J_1-J_{net}),\qquad
\partial_t v=C[-\nabla p+J_1\times B+\nu\nabla^2v]. $$

对矢势方程取旋度还原原感应方程；不再添加 divB 扩散或每步投影 B。C 是原松弛预条件系数，不是新增压强/电流驱动。其平滑、速度增量滤波、lambda/ctor 定义、p/s 演化及 scale_after 策略保留。

## 网格与算符

原 HINT 均匀柱坐标网格不变，数组轴为 (R,Z,phi)，分量为 (R,phi,Z)，演化一个完整场周期。R/Z 非周期，phi 周期。A 的一阶导数内域采用四阶五点中心模板，端点为四阶单边模板；二阶 Hermite 节点 jet 的单边模板需要六点。

$$ Df_i=\frac{f_{i-2}-8f_{i-1}+8f_{i+1}-f_{i+2}}{12h}. $$

$$ (\mathrm{curl}_h A)_R=\frac{D_\phi A_Z}{R}-D_Z A_\phi,\quad
(\mathrm{curl}_h A)_\phi=D_Z A_R-D_R A_Z,\quad
(\mathrm{curl}_h A)_Z=\frac{D_R(R A_\phi)-D_\phi A_R}{R}. $$

$$ D_h\cdot B=\frac{D_R(RB_R)+D_\phi B_\phi+R D_Z B_Z}{R}. $$

共享的一维算子在不同坐标方向可交换，R 与 Z/phi 导数可交换，因此包括单边端点在内有 D_h curl_h A=0，误差为浮点舍入与消去。不能在旋度后对 B 作掩膜、硬限幅、分量外推，否则这一恒等式失效。速度黏性仍采用原含柱坐标曲率/分量交叉项的矢量拉普拉斯。

这不是 FEEC 或交错网格，也不能仅凭无散宣称离散能量守恒、所有高频模式稳定或力平衡精确。共点网格的高频分辨率、边界支撑与显式时间步仍限制解。

## C2 Hermite 保无散插值

插值协变分量 (A_R,R A_phi,A_Z)。每个一维单元以两端的值、一阶和二阶导数确定五次 Hermite 多项式，三维张量积使用共享节点 jet，保证 A 为 C2、B 为 C1。jet 与 curl_h 使用同一模板，所以节点处解析旋度与演化磁场一致，而非两个仅分别无散但值不一致的场。

离网格 B 为该多项式的解析柱坐标 curl；连续散度由实际混合导数项相消，另外用独立 JAX Jacobian 检查实现。精确离散/连续散度不是精确源场值；初始化另有独立源积分导数及空间加密误差检查。

导数 jet 收缩到每方向七个有效节点权重，每点最多取 7³ 个向量；不保存 27 个全域导数体。总场先合并 A₀+A₁再取一次旋度。每次 Step-A 不再进行 B→A 全局拟合，只做 O(N) 状态装配和局部模板取值。静态模板缓存与动态场值分离，follow 不会误用第零步磁场。

## 初始响应场

VMEC LCFS 全环面 virtual-casing 积分和近源正则化保留。随后直接用同一四阶离散 curl 的 FFT/SVD 逆解获得节点 A₁；不再作旧的加权离散修正、C4 连续拟合和重采样。curl_h(A₁) 给出用于演化和冻结边界的初始 B₁。转换必须报告平均矢量差/平均场强和最大矢量差/平均场强；分别超过 1% 或 5% 时拒绝，不通过调电流掩盖误差。此步骤不是每外步重复的成本。

zero 为 A₁=0；vmec 保存完整初始 A₁并冻结其边界法向场。固定 A₀从线圈直接积分，不参与响应边界、壁内加权或全局场拟合。壁外线圈贡献始终包含在完整装置的源积分中。

## Step-A、标签和时间离散

沿当前 B 追踪，冻结 B，以 dR/dl=B_R/|B|、dZ/dl=B_Z/|B|、dphi/dl=B_phi/(R|B|) 同时积分 W'=1/|B| 和 P'=p/|B|。正反方向分别得 P/W，再等权平均；失败方向贡献零。native 使用 DOP853，JAX 批量 DOPRI5(4)/FSAL；试探越壁先缩步重试。

磁轴为 phi=0 一场周期回归的固定点，旧轴只作热启动。每个 Step-B 入口用松弛压力的层积分和当前 B 重建 s，压层下限仍为 0.01*p_axis；不是把初始 VMEC s 固定在实空间。该内步区间 p/s 冻结，每个 RKG 阶段重算 B/J/Jnet。

四阶段低存储 Runge–Kutta–Gill 推进 A₁/v；两版在 dA₁/dt 上施加各自边界约束。速度滤波相对于参考增量，reference_every 不清零速度。固定 time_step 无通用自适应 CFL，精细网格上的电阻/黏性约束仍更严格。Step-A/B 分裂、滤波和边界误差使整套外迭代不能简单称为四阶时间精度。

## 壁的角色

debug 的电磁边界为 R/Z 矩形保护层，壁仅作轨道/压力/源项支持，壁外仍有 eta1 松弛。wall 仅在壁内演化，壁外 A 只作差分与插值支持。wall 的稀疏法向旋度迹约束施加在网格边零交叉配点，见边界章节；代数约束精度与三维几何逼近误差必须分开。无论哪一版，均不让 B₀进入响应边界。

## 其他插值器

| 变量/用途 | 方法 | 原因 |
|---|---|---|
| 新状态全部磁场 | C2 五次 Hermite A 的解析 curl | 保持节点与连续两种无散且节点值一致 |
| Step-A p | 四点张量多项式，负取样裁零 | 保留原沿线平均模型 |
| 输出 p/s | 线性及相应范围限制 | 不引入超出物理范围的展示值 |
| v | 分量四阶取样 | 模型没有不可压 div(v)=0 条件 |
| 壁距离 | 周期三线性 | 避免高阶过冲造成伪内外区 |
| VMEC Fourier 径向系数 | 轴正则 Akima，奇 m 先除后乘 sqrt(s) | 保留轴正则性 |
| 表格剖面 | s 上线性 | 与输入定义一致，lambda 幅度另按 ctor 归一 |
| 派生 J/力 | 先用当前一致网格算子计算，再于完整有效模板取样 | 不能把旧初始场或无效壁外导数混入 |

## 检验指标

网格 D_h B 与离网格解析 div B 分开检验。主要无量纲平均为：

$$ \epsilon_{mean}=\frac{\operatorname{mean}(h_i|\nabla\cdot B_i|)}{\operatorname{mean}(|B_i|)},\qquad h_i=\min(\Delta R,\Delta Z,R_i\Delta\phi). $$

同时保留绝对 RMS/max、P50/P95/P99、超阈值比例与所用点集。平均小不能代替极值检验，散度小不能代替场值、拓扑或力平衡验收。探针是有限抽样，不是全域误差上界。测试覆盖节点一致性、连续 Jacobian、四阶空间加密、原始/续算一致、后处理读取、zero/vmec 与两种边界。

## 并行和文件

CPU/native 与 JAX 共享公式，GPU/JAX 使用 float64；R/Z 内域 roll 可沿原空间分片通信，仅端点作单边 gather。Step-A/后处理 MPI 分配起点，Step-B 使用原 JAX 空间 mesh；wall 稀疏约束通信可能成为瓶颈，不保证线性扩展。无每外步全局逆拟合，但局部 7³ 插值成本仍真实存在。

schema 9 保存 A₀、初始 A₁参考和每记录 A₁/p/v/s，不重复保存可导出的 B/J。follow 不重拟合、不换规范，不重算初始场。旧 B-only schema 4–8 由全部读取路径明确拒绝，既不自动升级，也不做后处理兼容转换。派生后处理仍写独立 analysis.nc，变量名称与 SI 单位保持不变。

源码：[节点与连续矢势](source:debug:src/hint_debug/vector_potential.py)、[时间推进](source:debug:src/hint_debug/solver/step_b.py)、[壁迹](source:wall:src/hint_wall/solver/potential_boundary.py)、[存储](source:debug:src/hint_debug/storage.py)。
