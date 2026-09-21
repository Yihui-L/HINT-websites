# 验证范围与限制

当前是2.3.0直接B版本；1.x的A场精度/耗时报告不代表本版验收结果。

## 检查内容

- 平滑核心线圈、三种复制对称性、总电流与源分辨率。
- FIELDLINES内/外分支，LCFS点归类，原始节点保真度。
- B向量RBF的节点保真、周期性、无散趋势重现、独立JAX Jacobian，以及Step-A/追踪/绘图调用链；不再把旧的面磁通相容插值测试作为当前RBF验收。
- 直接B的kdivb、RKG、矩形/真实壁边界、初始法向参考。
- Step-A双向平均、压力反馈、动态s、follow恢复连续性。
- CPU/GPU/JAX、MPI空分区与实际多rank数组路径。
- NetCDF、后处理、初始化庞加莱、参数表、示例和文档链接。
- 内区同一几何 Jacobian 重构：正/负磁通、对称/非对称 Fourier、磁轴极限、NumPy/JAX 一致性，以及实际源场 Jacobian 的迹。
- 源场诊断非致命失败、LCFS 未定义状态、标量 NetCDF 往返；FD4 与演化边界算符一致性、输入场不被诊断修改、后处理直接读取统计。
- 2.3.0补充：原版分量三次插值与CPU/GPU/JAX结果一致性、RBF精确支撑裁剪、follow插值器继承与显式切换、换记录时绘图后端重选、每外迭代AD存储及MPI汇总。设备选择的多GPU分支用模拟设备验证，不等价于真实多GPU性能测试。

具体执行结果见[debug验证记录](source:debug:docs/VERIFICATION.md)和[wall验证记录](source:wall:docs/VERIFICATION.md)。测试通过不等于证明无任何bug，不替代网格/步长/边界尺寸收敛或设备benchmark。

## 数值边界

平滑核心场的连续散度为零；其采样网格差分散度存在截断误差。向量 RBF 的连续散度由核约束保证，原节点场值不修改；这不代表网格差分散度或场值误差为零。FIELDLINES 拼接的 LCFS 节点数据保留，不添加初始化修补。RBF 在节点之间是连续插值，并不能逐点重现不连续的源模型。

低散度不能替代场值、磁拓扑、力平衡检验。kdivb只作用B₁；固定B₀误差不会自动被消除。第一壁附近的虚点与辅助支撑延拓精度可能低于规则内域。速度趋于不变也不等于趋于零。

## 源码地图

| 文件 | 功能 |
|---|---|
| preprocess/coils.py, vacuum.py | 平滑核心B |
| preprocess/vmec_interior.py, vmec_field.py, casing.py | 内区几何/磁通/lambda 重构、外部B casing |
| preprocess/source_diagnostics.py, magnetic_diagnostics.py | 初始源场 AD、每外迭代插值器 AD 与网格 FD4 |
| magnetic.py / rbf.py / component.py | 可选分量或向量RBF、节点保真、周期性、实际插值器 JAX AD |
| solver/step_a.py, step_a_jax.py | 压力沿线平均 |
| solver/flux.py | 由压力层磁通更新s |
| solver/step_b.py | B/v直接演化及诊断 |
| solver/box.py, wall.py | 两版不同边界 |
| storage.py | schema22统一文件、初始源场/每外迭代AD与FD4统计、follow |
| postprocess/, hint_*_plotting/ | 数值分析和绘图 |
