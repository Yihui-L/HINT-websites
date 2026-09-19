# VMEC 响应场与续算

## VMEC 初始响应场不是简单相减

直接将 wout 内部场减去 B₀，只在 VMEC 内部可定义；无法给出壁和矩形域附近的整个响应场，也可能混入背景场不一致。当前实现使用**内置的正则化 virtual-casing 边界积分**，从 LCFS 完整场和几何求等离子体电流在内外区域产生的场。

积分源展开覆盖完整 2π 装置，目标点只在一个场周期取样。即使使用仿星器对称性减少目标点，也不能省略其余周期的源贡献。外部 `hiddenSymmetries/virtual-casing` 是方法参考，不是运行依赖。

定义 r=x−y，外向面积矢量 dS，核心积分为：

$$\mathcal V[\mathbf B](\mathbf x)=\frac{1}{4\pi}\int_S\frac{(d\mathbf S\times\mathbf B)\times\mathbf r+(d\mathbf S\cdot\mathbf B)\mathbf r}{|\mathbf r|^3}.$$

近表面采用局部常矢量 C 的减法正则化，结合常场内外/主值跳跃关系恢复解。外点为 V[B−C]，内点为 V[B−C]−C+B_VMEC(x)，表面按主值处理。使用成对 16×16 / 24×24 Gauss 面板误差估计与自适应细分；这些是当前内部精度控制，不是用户可填的 TOML 参数，也不是对全局物理误差的保证。

## 直接积分初始矢势

当前不使用“响应 B → 逆求 A”路径。对满足 curl A_v=B_VMEC 的内部矢势，使用广义 virtual-casing 恒等式直接计算：

$$\mathbf A_1(\mathbf x)=\mathbf 1_\Omega\mathbf A_v(\mathbf x)+\mathcal V[\mathbf A_v](\mathbf x)+\frac1{4\pi}\int_S\frac{d\mathbf S\times\mathbf B_{\rm VMEC}}{|\mathbf x-\mathbf y|}.$$

其中 V 是上面定义的通用矢量核，表面使用半跳跃极限。该表达式等于物理电流的体积分矢势加一个纯梯度规范项；不是只使用表面电流单层势。后者单独使用不能恢复 LCFS 内部的等离子体场。原理参考 [Hanson 的广义恒等式](https://sherwoodtheory.org/sw2015/uploads/146/hanson_v1.pdf)。

内部 A 从 wout 的 phipf、chipf、signgs 与角变换 lmns/lmnc 构造，而不是反演 HINT 网格上的 B。基础式为 A_v=psi grad(theta)−chi grad(phi)−psi' lambda_ang grad(s)，再作径向规范变换。这里 lambda_ang 是 VMEC 角坐标变换，**不是电流源项的 lambda(s)**。几何和角变换采用保留原节点系数的 C4 五次径向插值；bsup 参考数据保留独立的轴正则插值。

为降低强规范梯度的离散误差，星形 R-Z 截面可使用物理径向同伦规范，路径与表面表格均检查积分/插值收敛；不能构造有效参考中心时保留一般磁通坐标规范。LCFS 上附加纯标量梯度改善矢势导数连续性，不改变连续磁场。规范平滑不能替代实际 B 精度检查。MPI 分配目标块和规范表格，JAX CPU/GPU 批量计算，环向 Fourier 因子在路径批次内复用。

### 路径积分自动加密

1.3.1 起，复合16点高斯路径求积从64个节点开始，对未收敛目标逐次加倍，资源保护上限为65536。旧的2048节点不再触发提前退出。保持原判据 `|A_N-A_(N/2)| <= 2e-7*A_reference`，不放宽容差、不调整源场、不改变HINT网格。此差值是收敛估计而非真实误差证明；真正达到上限仍不收敛时报告最大变化、阈值和最差点的s/theta/phi。NaN/Inf不能被视为通过。

高节点数时自动缩小目标批次，少量剩余路径只填充至相邻的2次幂批大小；边界规范的自动微分也使用更小的批次。JAX CPU/GPU核继续批量执行，MPI仅在各自目标内细化，局部不等长循环没有新增集合通信。规范参考点的全局判据则使用集合计算保持各rank一致。没有新增TOML参数，也没有改动Step-A/B、边界条件或follow状态。

以独立读取 wout bsup 的直接 **B virtual-casing 积分**为参考，在最多640个分层网格点及256个非网格点分别校验 curl A：平均矢量误差/参考平均场强不超过1%，最大矢量误差/参考平均场强不超过5%。这是抽样保护，不是全网格精度认证。超限时检查数据、规范正则性和网格/积分收敛，不调电流、不放宽阈值。另检验磁通/角变换重建 B 与 bsup B 的一致性。散度很小不能证明场值、磁面或电流准确。

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

源码：[响应初始化](source:debug:src/hint_debug/preprocess/vmec_field.py)、[直接A积分核](source:debug:src/hint_debug/preprocess/casing.py)、[内部VMEC矢势](source:debug:src/hint_debug/preprocess/vmec_potential.py)、[独立磁场校验](source:debug:src/hint_debug/preprocess/casing_validation.py)、[演化矢势](source:debug:src/hint_debug/vector_potential.py)、[状态存储](source:debug:src/hint_debug/storage.py)、[矢势边界](source:wall:src/hint_wall/solver/potential_boundary.py)。
