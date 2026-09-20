# 验证范围与限制

当前是2.0.0直接B版本；1.x的A场精度/耗时报告不代表本版验收结果。

## 检查内容

- 平滑核心线圈、三种复制对称性、总电流与源分辨率。
- FIELDLINES内/外分支，LCFS点归类，原始节点保真度。
- B插值的多项式精确性、非零散度保留、磁通/散度交换关系、网格细化、独立JAX Jacobian。
- 直接B的kdivb、RKG、矩形/真实壁边界、初始法向参考。
- Step-A双向平均、压力反馈、动态s、follow恢复连续性。
- CPU/GPU/JAX、MPI空分区与实际多rank数组路径。
- NetCDF、后处理、初始化庞加莱、参数表、示例和文档链接。

具体执行结果见[debug验证记录](source:debug:docs/VERIFICATION.md)和[wall验证记录](source:wall:docs/VERIFICATION.md)。测试通过不等于证明无任何bug，不替代网格/步长/边界尺寸收敛或设备benchmark。

## 数值边界

平滑核心场的连续散度为零；其采样网格差分散度存在截断误差。相容插值保存面磁通离散散度，并非所有输入自动变成无散场。FIELDLINES拼接的LCFS不连续保留，不添加初始化修补。

低散度不能替代场值、磁拓扑、力平衡检验。kdivb只作用B₁；固定B₀误差不会自动被消除。第一壁附近的虚点与辅助支撑延拓精度可能低于规则内域。速度趋于不变也不等于趋于零。

## 源码地图

| 文件 | 功能 |
|---|---|
| preprocess/coils.py, vacuum.py | 平滑核心B |
| preprocess/vmec_field.py, casing.py | 内部wout、外部B casing |
| magnetic.py | 相容B面磁通插值 |
| solver/step_a.py, step_a_jax.py | 压力沿线平均 |
| solver/flux.py | 由压力层磁通更新s |
| solver/step_b.py | B/v直接演化及诊断 |
| solver/box.py, wall.py | 两版不同边界 |
| storage.py | schema20统一文件和follow |
| postprocess/, hint_*_plotting/ | 数值分析和绘图 |
