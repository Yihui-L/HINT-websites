# 压力、电流源与 s 标签

## 压力不是固定的三维源场

初始 p(s) 来自 VMEC（或 input 的同样升幂/分段线性定义），在柱坐标网格赋值。之后 Step-A 沿**当前**磁力线松弛压力，s 也根据当前压力和磁场重建。因此最终同一空间点的压力、s 和电流源都不必等于初始 VMEC 值。

`profiles.pressure_scale` 是准备阶段的倍率；`solver.scale_after` 决定攀升后是否保留轴压反馈；输出 `pressure_scale` 是记录的攀升进度。三者不相同。

### zero 起点

B₁=0、v=0。初始压力是整个目标剖面的缩小版本。小压力尺度由真空磁轴处 beta=10⁻³ 对应的压力与目标值取较小者：

$$p_{\rm small}=\frac{10^{-3}}{2\mu_0}|\mathbf B_{0,\rm axis}|^2,\quad a_0=\min(1,p_{\rm small}/p_{\rm target,axis}).$$

当 a₀>0 且小于 1 时，每个外迭代的目标比例按几何因子 a₀^(−1/N) 提高，N=`pressure_ramp_iterations`，到达 1 后停止攀升。初始和随后反馈以插值的当前磁轴压力为依据作统一倍率修正。零目标压力的退化情形不应用这个比例公式直接相除。

攀升改变整体幅度，不把每个网格的 p 强行重置回初始 VMEC p(s)。在变化后的磁结构、标签分布下，压力形状会继续变化。只保证执行所选的轴压反馈，不保证每一个原磁面的 p 值或全空间单调性。

### vmec 起点

`start_point="vmec"` 要求 `profiles.source="vmec"`、`profiles.pressure_scale=1`。初始直接使用完整 VMEC 压力和重建的等离子体响应场，v=0，不再将初始压力缩小。`pressure_ramp_iterations` 在物理流程中不起作用。

- `scale_after=true`：从后续完整外迭代起，仍把当前轴压统一反馈到目标值。
- `scale_after=false`：不再施加目标轴压反馈，压力由现有 Step-A/B 和边界流程继续演化。

false 不会取消每步的磁轴定位，也不会停止 s 重建；它不是切换为完整绝热/等温输运方程。原 VMEC p(0) 与离散网格最大 p 未必精确重合。

## 电流源的实际定义

$$\lambda_{\rm VMEC}(s)=\frac{\langle\mathbf J\cdot\mathbf B\rangle}{\langle B^2\rangle},\qquad \mathbf J_{\rm net}=A\lambda(s)\mathbf B.$$

wout 的 `jdotb/bdotb` 给出上述形状；该比值在 SI 下量纲 A/(m²·T)。在本程序中其整体幅度由 ctor 再归一化，输入形状的共同倍数会消去。`input.current` 用相同的 **lambda 形状**，不是 jcurv，也不是 I(s) 或 dI/ds。这比“所有 VMEC ac 与 HINT input 完全同义”更严格：这里只共享升幂多项式的数学表示，因变量须按 lambda 定义转换。

每个 Step-B RKG 阶段根据当前 B、冻结于本次 Step-B 的 s，在壁内 0≤s<1 建立源项并按 φ=0 截面总电流调整 A：

$$A=\frac{\mu_0 I_{\rm target}/(L_{\rm ref}B_{\rm ref})}{\sum_{R,Z}[\lambda(s)B_\phi]_{\phi=0}\,\Delta R\Delta Z}.$$

该积分是环向电流穿过 R–Z 截面的通量，**没有 R 权重或 2π 因子**。分母严重正负抵消时不能安全归一化，代码拒绝近退化归一化。源电流不乘压力攀升比例。

电阻项是 η(J₁−Jnet)，体现维持平行净电流的驱动。J₁由完整响应场的旋度决定，还包含力平衡所需的横向/其他电流成分。不能据此认为 J₁在每点完整地趋于 Jnet，也不能把 Jnet+J₁作为总等离子体电流。

## 演化中的 s 如何定义

初始 `norm_s_initial` 是 VMEC 归一化环向磁通。演化的 s 是压力排序所重建的标签，不需要预先识别每一张闭合磁面：

1. 在 φ=0 截面、壁内且排除矩形两层差分保护节点，选 501 个压力层，范围为 0.01 p_axis 到 p_axis。
2. 对每个压力阈值 p_k，积分满足 p≥p_k 的区域内的 Bφ dR dZ，得到包围该高压区域的环向磁通标签。
3. 以最低压力层包围的磁通归一化，轴端设 0、边端设 1，施加单调累积约束。
4. 通过压力到标签的插值给三维点赋 s；低于压力底层取 1，高于轴压取 0。

实现采用排序、累积和及二分索引，避免对每个压力层重复扫描全域。0.01 乘的是**压力底层阈值**，不是 s=1 处磁场的倍率。它沿用模型的低压边界标签约定。

在磁岛、随机区或压力平台，s 不再是唯一、严格的磁通面坐标。图上的 `rho=sqrt(s)` 也只是该标签的变换，不是独立几何小半径。保存态中的 `s` 应作为后处理和 follow 的依据，不能用 `norm_s_initial` 覆盖。

源码：[剖面准备](source:debug:src/hint_debug/preprocess/vmec.py)、[标签重建](source:debug:src/hint_debug/solver/flux.py)、[外迭代](source:debug:src/hint_debug/solver/equilibrium.py)、[电流归一化](source:debug:src/hint_debug/solver/step_b.py)。
