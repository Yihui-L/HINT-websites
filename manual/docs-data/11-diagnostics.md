# 收敛性与平均方式

## 先确定量、区域和时刻

同名“RMS”可能不是同一个统计。比较两版本、原版日志或不同图片前，应固定：B₁还是总 B、SI 还是归一化、矩形域还是壁内、是否排除差分无效节点、每内步还是完整保存态、点平均还是体平均。

令有效节点集合为 Ω，柱坐标体元权重 w_i=R_i ΔR ΔZ Δφ：

$$\overline f_{\rm point}=\frac1N\sum_i f_i,\quad f_{\rm RMS,point}=\sqrt{\frac1N\sum_i|f_i|^2},$$

$$\langle f\rangle_V=\frac{\sum_iw_i f_i}{\sum_iw_i},\quad f_{\rm RMS,V}=\sqrt{\frac{\sum_iw_i|f_i|^2}{\sum_iw_i}}.$$

绝对平均是对 |f| 求平均，有符号平均可能正负抵消；RMS 与最大绝对值则不会。三者不能互换。统计极值不加体积权重。

## Step-B 诊断

| 字段 | 定义/解释 |
|---|---|
| kinetic_energy | 归一化体积分 1/2 ∫v² dV |
| response_magnetic_energy | 归一化体积分 1/2 ∫B₁² dV；不是总场能量 |
| force_max / force_rms | F=J₁×B−grad p 的最大模 / 点 RMS，不含黏性和预条件因子 |
| divb_max / divb_rms | div B₁ 最大绝对值 / 点 RMS；不是 div B₀ 或总场 |
| force_volume_rms / divb_volume_rms | 上述量的 R 加权体 RMS |
| parallel_pressure_volume_rms | b·grad p 的体 RMS |
| boundary_bn_max | 相对冻结法向参考的最大边界误差，不是绝对 Bn |
| boundary_velocity_max | 适用边界上的速度模最大值 |

debug 的常规内域诊断排除矩形保护层，包含数值壁外区；wall 在其有效内域统计。因此同网格两版本的诊断范围也可能不同。实际 mask 由相应算子决定。

内部最后一步诊断可能发生在外迭代末尾轴压反馈之前；保存态压力可能已反馈。`scale_after=false` 不再有该压力倍率，但重新计算导数、掩膜及 SI 换算仍可造成差异。

## 相对力残差

绘图的局域相对量为：

$$\epsilon_F(\mathbf x)=\frac{|\mathbf J_1\times\mathbf B-\nabla p|}{\max(|\mathbf J_1\times\mathbf B|,|\nabla p|)}.$$

在分母有效时范围为 [0,2]。两项同时低于相对数值门槛时掩膜，而不是人为给小分母制造很大的比值。它与“所有点绝对残差 RMS 再除全局梯度 RMS”不同：

$$\epsilon_{F,\rm global}=\sqrt{\frac{\sum_i R_i|F_i|^2}{\sum_i R_i|\nabla p_i|^2}}.$$

后一式是另一种可解释的归一化，不能把当前 `force_rms` 自动称为这个比值。局域相对图在低压真空附近往往无定义，不宜据此说真空不平衡极大。

## 磁场散度解读

保存态可分别计算 D·B₀、D·B₁、D·(B₀+B₁)。相同线性算子下三者相加关系成立，但插值、掩膜、采样网格改变会影响数值。B₁ 的舍入级散度不能消除 B₀ 的限幅/插值散度。

fields/MAGVAL 类输出用 T/m，其相对最大散度指标还乘特征域尺度再除最大场强；这不是 Step-B 的 B_ref/L_ref 归一化。没有给出离散精度、网格和场梯度时，不存在对所有 mgrid 都必须满足的绝对 10⁻¹⁰ 阈值。

## 如何判断趋于平衡

同时观察力残差、平行压力梯度、速度/动能、响应能量、散度和边界误差，结合晚期变化趋势。v 变化很小只说明近稳态，不说明 v 已趋零；固定非零流速也可能与残余力/耗散平衡。单一残差小也可能来自压力整体衰减，需一起看轴压/峰值及目标剖面。

对 signed 分量使用线性或 symlog；严格非负且跨数量级量适合 log。包含零或舍入噪声的曲线不要偷偷加偏移量。zero 攀升可在第 N 外迭代画垂线；vmec 无攀升，不应套用“第 20 步攀升结束”标记。

源码：[Step-B 统计](source:debug:src/hint_debug/solver/step_b.py)、[后处理量](source:debug:src/hint_debug/postprocess/quantities.py)、[绘图数据](source:debug:postprocess/hint_debug_plotting/data.py)。
