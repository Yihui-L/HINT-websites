# VMEC 响应场与续算

## VMEC 初始响应场不是简单相减

直接将 wout 内部场减去 B₀，只在 VMEC 内部可定义；无法给出壁和矩形域附近的整个响应场，也可能混入背景场不一致。当前实现使用**内置的正则化 virtual-casing 边界积分**，从 LCFS 完整场和几何求等离子体电流在内外区域产生的场。

积分源展开覆盖完整 2π 装置，目标点只在一个场周期取样。即使使用仿星器对称性减少目标点，也不能省略其余周期的源贡献。外部 `hiddenSymmetries/virtual-casing` 是方法参考，不是运行依赖。

定义 r=x−y，外向面积矢量 dS，核心积分为：

$$\mathcal V[\mathbf B](\mathbf x)=\frac{1}{4\pi}\int_S\frac{(d\mathbf S\times\mathbf B)\times\mathbf r+(d\mathbf S\cdot\mathbf B)\mathbf r}{|\mathbf r|^3}.$$

近表面采用局部常矢量 C 的减法正则化，结合常场内外/主值跳跃关系恢复解。外点为 V[B−C]，内点为 V[B−C]−C+B_VMEC(x)，表面按主值处理。使用成对 16×16 / 24×24 Gauss 面板误差估计与自适应细分；这些是当前内部精度控制，不是用户可填的 TOML 参数，也不是对全局物理误差的保证。

## 从初始积分场到矢势状态

virtual-casing 积分给出初始 B₁样本，直接使用后续演化的同一离散 curl 反求节点 A₁，不再经过旧的 Helmholtz 修正、连续样条迭代拟合和重采样链条。设 a=(A_R,A_Z,R A_phi)，F=(-R B_R,-R B_Z,-B_phi)，以离散旋度 C 和梯度 G 求解 (CᵀC+GGᵀ)a=CᵀF。R/Z 采用包含单侧端点的完整四阶导数矩阵 SVD；phi 使用四阶差分符号对应的 FFT，而非连续波数。零空间取最小范数规范。该最小二乘目标是通量分量的未加权范数，不是磁能范数；物理磁场误差另行检查。MPI 分配 Fourier 模式，CPU/GPU 执行张量变换。

转换后矢量差的算术平均除以参考平均场强须不超过 1%；最大矢量差除以该平均场强须不超过 5%。超限报错并要求检查空间分辨率，不靠改变电流归一化掩盖差异。积分误差、离散 curl 可表示性误差及网格插值误差是不同量，均不能仅凭散度小推断为零。

从此以后直接推进节点 A₁。Step-A、磁轴、庞加莱与后处理使用同一 C2 五次 Hermite 矢势的解析 curl，不再每外步逆拟合 B。A₀直接来自平滑核心线圈解析积分，且不进入响应场边界条件。

zero 初始化 A₁=0；vmec 初始化完整 A₁、p 和 s。两版冻结**最终准备得到的初始响应场**法向值：不可在进入演化时再次把非零初始 B₁n 改成零。洛伦兹力始终使用完整 J₁×(B₀+B₁)。

## follow 读取顺序

`paths.output_file` 同时是恢复源和追加目标。schema 9 的 A 状态文件保存了预处理数据、归一化、完整状态、初始响应场边界参考、压力攀升阶段和每记录求解配置。

恢复时使用最后一个 `record_complete=1` 的状态，跳过未完成写入记录；加载实际 p、s、v、A₁和轴热启动，并从 A 推导 B。初始 VMEC 标签和初始压力不会覆盖它们。`outer_steps=N` 表示再做 N 步，而非跑到编号 N。

```toml
[paths]
output_file = "run/equilibrium.nc"

[solver]
mode = "follow"
backend = "gpu"
engine = "jax"
outer_steps = 20
save_every = 1
```

上例省略了外部 wout、线圈文本、vessel。**只对被明确继承的设置**可以省略：Step-A/B 参数、轴位置/容差、scale_after 等从保存配置恢复；起点语义不可冲突。backend、engine、追加步数、保存策略属于本次调用设置，不能假定所有参数都自动继承。

主程序与后处理仅接受当前 schema 9 的 A-state 文件。旧 schema 4–8、B-only 文件均拒绝，不提供自动升级；需要建立新的 initial 算例。debug 与 wall 的 schema 标识及边界含义不同，不支持把同一个输出当作另一版本的 follow 文件。

## 写入与并发

主程序先写数组、同步，再提交完整标记；这能识别部分写入，不等价于任意并发读取均安全。重要结果先备份；监控正在写的文件时优先使用安全副本，并检查最后完整记录。后处理写独立文件且有写锁，不要自行删除一个仍有进程持有的锁。

源码：[响应场重建](source:debug:src/hint_debug/preprocess/vmec_field.py)、[casing](source:debug:src/hint_debug/preprocess/casing.py)、[配套离散 curl 逆解](source:debug:src/hint_debug/nodal_reconstruction.py)、[演化矢势](source:debug:src/hint_debug/vector_potential.py)、[状态存储](source:debug:src/hint_debug/storage.py)、[矢势边界](source:wall:src/hint_wall/solver/potential_boundary.py)。
