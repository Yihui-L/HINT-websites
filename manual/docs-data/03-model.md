# 物理模型与归一化

## 哪些量在演化

采用柱坐标 (R,φ,Z)，网格数组轴序为 **(R,Z,φ)**，矢量分量顺序为 **(R,φ,Z)**。两者不能混淆。B₀ 是线圈背景场，B₁ 是全部等离子体响应场：

$$\mathbf B=\mathbf B_0+\mathbf B_1,\qquad \mathbf J_1=\nabla\times\mathbf B_1.$$

本章未特别标 SI 的方程均为程序归一化形式，因而安培定律没有 μ₀。SI 电流为 curl(B₁)/μ₀。响应场包含 VMEC 初始响应场及其后续变化，不仅指“相对 VMEC 的新增量”。

稳态目标是静态 MHD 力平衡、压力沿磁力线一致、磁场无散：

$$\mathbf J_1\times\mathbf B-\nabla p=0,\qquad \mathbf B\cdot\nabla p=0,\qquad \nabla\cdot\mathbf B=0.$$

程序将它们分为两种松弛：Step-A 沿磁力线平均压力；Step-B 固定该次压力，推进速度和磁场。

$$\frac{\partial\mathbf v}{\partial\tau}=C(\mathbf x)\left[-\nabla p+\mathbf J_1\times\mathbf B+\nu\nabla^2\mathbf v\right],$$

$$\frac{\partial\mathbf B_1}{\partial\tau}=\nabla\times\left[\mathbf v\times\mathbf B-\eta(\mathbf J_1-\mathbf J_{\rm net})\right]+\mathcal Q_{\rm div}.$$

`C` 是数值松弛预条件系数；ν 是黏性；η 是电阻形式的松弛系数；`Q_div` 是与版本边界相容的数值散度控制。`Jnet` 是维持环向电流的外加平行电流目标，不是另一个应与 J₁ 相加的真实等离子体电流。

**模型中没有**完整密度连续方程、温度/能量输运方程、速度对流惯性项、旋转平衡驱动、可演化外部线圈电流或有限电阻壁电流方程。因此输出 v 是松弛速度；“几秒弛豫时间”不能直接解释为真实装置的输运时间。

## 归一化标度

当前代码取 `L_ref=(R_min+R_max)/2`，`B_ref` 为准备后的 B₀ 在网格中央索引 `((nr-1)//2,(nz-1)//2,0)` 的模，密度参考值固定为 1 kg/m³。**B_ref 不是磁轴场强**；极强场限幅用的轴上参考是另外一个量。

$$v_{\rm ref}=\frac{B_{\rm ref}}{\sqrt{\mu_0\rho_{\rm ref}}},\quad t_{\rm ref}=\frac{L_{\rm ref}}{v_{\rm ref}},\quad p_{\rm ref}=\frac{B_{\rm ref}^2}{\mu_0}.$$

| 数量 | 归一化量乘此标度得到 SI |
|---|---|
| 坐标、弧长 | L_ref，m |
| 时间 | t_ref，s；仍为弛豫时间 |
| B / v / p | B_ref / v_ref / p_ref |
| J | B_ref/(μ₀ L_ref)，A/m² |
| 力密度 | B_ref²/(μ₀ L_ref)，N/m³ |
| div B | B_ref/L_ref，T/m |
| 电阻率 | μ₀ L_ref v_ref，Ω·m |
| 运动黏性、散度扩散系数 | L_ref v_ref，m²/s |
| 体积分能量 | B_ref² L_ref³/μ₀，J |

归一化 η=0.001 不是 0.001 Ω·m。原版日志、Step-B 存储诊断和后处理 SI 数据必须先对齐标度与统计区域，才可比较数量级。

## 哪些约束“天然满足”

| 关系 | 当前实现 | 仍需注意 |
|---|---|---|
| B=B₀+B₁ | 直接代数定义 | 背景场插值/限幅后可能已有散度 |
| J₁=curl B₁ | 由离散旋度计算，无独立 J 演化 | 安培关系成立不意味着电流足够准确；导数放大误差 |
| div(curl)=0 | 共同差分算子在兼容内域可达到舍入级 | 端点延拓、壁掩膜、投影和不同算子会破坏恒等式 |
| B·grad p=0 | 有限长度双向平均近似 | 开放线、随机区、积分误差、压力壁闭合不保证精确为零 |
| J₁×B=grad p | 需要实际松弛收敛 | 黏性、滤波、轴压反馈、固定边界可能留下残差 |
| v→0 | 是有意义的静态验收目标 | 不能仅凭速度变化小判断已经 v=0；非零稳态可能由残余力和耗散平衡 |

`scale_after=false` 去掉一项外部压力反馈，但不新增能量守恒或保证所有例子最终静止。磁拓扑、源电流、边界和稳定性仍决定能否达到静态平衡。

源码：[归一化](source:debug:src/hint_debug/pipeline.py)、[Step-B](source:debug:src/hint_debug/solver/step_b.py)、[差分算子](source:debug:src/hint_debug/numerics.py)。理论背景为 Suzuki 2006 / 2017；当前实现包含另外的离散修复与边界约束，不宣称是论文每个选项的完整复现。
