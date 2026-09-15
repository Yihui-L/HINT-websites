# VMEC 响应场与续算

## VMEC 初始响应场不是简单相减

直接将 wout 内部场减去 B₀，只在 VMEC 内部可定义；无法给出壁和矩形域附近的整个响应场，也可能混入背景场不一致。当前实现使用**内置的正则化 virtual-casing 边界积分**，从 LCFS 完整场和几何求等离子体电流在内外区域产生的场。

积分源展开覆盖完整 2π 装置，目标点只在一个场周期取样。即使使用仿星器对称性减少目标点，也不能省略其余周期的源贡献。外部 `hiddenSymmetries/virtual-casing` 是方法参考，不是运行依赖。

定义 r=x−y，外向面积矢量 dS，核心积分为：

$$\mathcal V[\mathbf B](\mathbf x)=\frac{1}{4\pi}\int_S\frac{(d\mathbf S\times\mathbf B)\times\mathbf r+(d\mathbf S\cdot\mathbf B)\mathbf r}{|\mathbf r|^3}.$$

近表面采用局部常矢量 C 的减法正则化，结合常场内外/主值跳跃关系恢复解。外点为 V[B−C]，内点为 V[B−C]−C+B_VMEC(x)，表面按主值处理。使用成对 16×16 / 24×24 Gauss 面板误差估计与自适应细分；这些是当前内部精度控制，不是用户可填的 TOML 参数，也不是对全局物理误差的保证。

## 离散无散约束

积分得到的连续意义磁场再采样到差分网格后，D·B 不会自动精确为零。当前程序对初始响应场作加权最小范数离散 Helmholtz 修正：

$$\mathbf B_1=\mathbf B_* -D^\dagger(DD^\dagger)^{-1}D\mathbf B_*.$$

D 为所用离散散度，D†是对应加权伴随。柱坐标权重包含 R。矩形初始化求解使用环向 FFT 和 R–Z 小算子的谱分解，CPU 根进程处理后广播；**不是后续全程改为演化矢势 A**。

必须同时检查初始散度、投影修正相对大小、VMEC 内部总场匹配和投影前后电流变化。即使投影残差达到舍入级，若修正很大或 B₀ 与 wout 不一致，也不能宣称物理场正确。深内部相容导数能保护 curl-grad 恒等式，但保护层附近仍需关注导数误差。

两版都冻结**数值准备/约束后的初始响应场法向分量**。zero 为零法向；vmec 通常非零。后续力平衡仍用完整 J₁×(B₀+B₁)，不减去这部分初始电流。

## follow 读取顺序

`paths.output_file` 同时是恢复源和追加目标。schema 7 文件保存了预处理数据、归一化、完整状态、初始响应场边界参考、压力攀升阶段和每记录求解配置。

恢复时使用最后一个 `record_complete=1` 的状态，跳过未完成写入记录；加载实际 p、s、v、B₁和轴热启动。初始 VMEC 标签和初始压力不会覆盖它们。`outer_steps=N` 表示再做 N 步，而非跑到编号 N。

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

上例省略了外部 wout、mgrid、vessel。**只对被明确继承的设置**可以省略：Step-A/B 参数、轴位置/容差、scale_after 等从保存配置恢复；起点语义不可冲突。backend、engine、追加步数、保存策略属于本次调用设置，不能假定所有参数都自动继承。

旧 schema 4–6 在兼容条件下升级到当前状态格式；更旧格式和旧电流剖面语义不可盲目恢复。debug 与 wall 的 schema 标识及边界含义不同，不支持把同一个输出当作另一版本的 follow 文件。

## 写入与并发

主程序先写数组、同步，再提交完整标记；这能识别部分写入，不等价于任意并发读取均安全。重要结果先备份；监控正在写的文件时优先使用安全副本，并检查最后完整记录。后处理写独立文件且有写锁，不要自行删除一个仍有进程持有的锁。

源码：[响应场重建](source:debug:src/hint_debug/preprocess/vmec_field.py)、[casing](source:debug:src/hint_debug/preprocess/casing.py)、[投影](source:debug:src/hint_debug/preprocess/solenoidal.py)、[状态存储](source:debug:src/hint_debug/storage.py)、[边界参考](source:wall:src/hint_wall/solver/boundary_reference.py)。
