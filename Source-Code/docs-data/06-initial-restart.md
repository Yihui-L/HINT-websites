# FIELDLINES 初始化与续算

## 初始场的定义

2.3.0 直接演化 B，不演化 A。设 B₀ 为完整线圈集合的平滑核心场，V 为外部 B virtual-casing 积分：

$$\mathbf B_{\rm init}(\mathbf x)=
\begin{cases}\mathbf B_{\rm wout}(\mathbf x),&\mathbf x\in\overline\Omega,\\
\mathbf B_0(\mathbf x)+\mathcal V[\mathbf B_{\rm wout}](\mathbf x),&\mathbf x\notin\overline\Omega.\end{cases}$$

$$\mathbf B_{1,\rm init}=\mathbf B_{\rm init}-\mathbf B_0.$$

LCFS内不再叠加一次真空场；内侧响应是wout总场减B₀，外侧响应来自B边界积分。这与 [FIELDLINES 的区域逻辑](https://princetonuniversity.github.io/STELLOPT/FIELDLINES.html) 一致。LCFS恰好落在网格点上时取wout侧。当前不求A、不投影、不混合、不平滑初始跳跃，不调整线圈场来匹配wout。

压强直接使用presf在初始VMEC标签处的值，v=0，攀升已完成。初始化立即写入outer_step=0，先于第一次轴搜索、Step-A和Step-B。scale_after控制之后是否维持目标轴压。

## 源积分与加速

LCFS 内采用几何一致重构。令 q=(s,θ,φ)、x(q) 为 VMEC 空间位置、λ 为 `lmns/lmnc` 定义的直磁力线角度修正，则

$$\mathcal J=\mathbf x_s\cdot(\mathbf x_\theta\times\mathbf x_\phi),\quad
\psi'=-\frac{\mathrm{wout.phi}[-1]}{2\pi},$$

$$\mathbf B_{\rm in}=\frac{\psi'}{\mathcal J}
\left[(\iota-\lambda_\phi)\mathbf x_\theta+(1+\lambda_\theta)\mathbf x_\phi\right].$$

几何及其雅可比来自同一套 Fourier/径向重构，不混用独立插值的 `gmnc`。λ、iota 使用真实半网格并排除占位行，奇 m 模恢复 √s 正则因子，磁轴值使用 ρ=√s 的解析极限。这里的 λ **不是**电流源剖面 `jdotb/bdotb`。混合偏导相消保证该连续重构的结构性无散；并不证明其磁场幅值、径向插值或磁面拓扑没有误差，近轴仍需保真检验。

仅替换内侧初始化。外部 casing 的源面仍使用 wout 原有逆变磁场系数，避免无关改变外区算法。LCFS 跳跃日志改为比较外侧极限与新的内侧极限。源场、s、压力不做投影或额外缩放。

外向面元dS、r=x-y的B积分核为：

$$\mathcal V[\mathbf B]=\frac1{4\pi}\int_S
\frac{(d\mathbf S\times\mathbf B)\times\mathbf r+
(d\mathbf S\cdot\mathbf B)\mathbf r}{|\mathbf r|^3}.$$

源面覆盖全环面，不额外乘nfp、电流或mu₀。减去局部常向量的密度正则化保留外部积分值，16/24点高斯对与局部细分估计误差。该估计不包含wout、线圈、坐标反解和HINT网格误差。

仅外侧目标执行casing；内部用批量wout Fourier计算。CPU管理自适应队列，JAX CPU/GPU驻留面片和源系数，MPI分配R-Z块。没有规范路径积分或B到A逆求。

## LCFS诊断，不做修正

日志在64个表面探针上报告外侧 B₀+V 与新内侧场的法向差、矢量差、内侧 Bn 及积分误差估计。初始化还将源表达式的 JAX AD 统计写入 `/preprocess/initial_source_diagnostics`，与网格插值器 AD 分开。后续每外迭代记录插值器 AD 和网格 FD4。LCFS 可能存在法向跳跃，此时没有普通点值意义的解析散度；仅记录 `lcfs_crossing_status=not_defined`，不创建数值变量，不伪装成零。小积分误差不保证边界两侧一致。

后续 kdivb 扩散响应场的离散散度，不清理固定 B₀。保留 LCFS 节点跳跃不等于承诺它一定在有限次迭代后消失。默认分量插值优先速度，不保证无散；可选 RBF 保持输入节点值，并在节点之间构造连续无散场。两者均不修改已经保存的 B。

## follow

paths.output_file同时是输入与追加目标。只接受同版本schema 22，恢复B₀、当前B/p/v/s、初始冻结B₁参考、轴热启动、攀升状态和每记录求解设置。未指定的数值控制继承；不能改变start_point。无需外部wout、线圈或壁文件。

不得用初始s覆盖当前s，不重算初始化，不重启已结束攀升。旧A-state或更旧B-state不自动升级。分支续算请先复制停止写入的完整结果，再让follow指向副本。每个结果只能有一个写进程。

源码：[初始化](source:debug:src/hint_debug/preprocess/vmec_field.py)、[B casing](source:debug:src/hint_debug/preprocess/casing.py)、[存储](source:debug:src/hint_debug/storage.py)。
