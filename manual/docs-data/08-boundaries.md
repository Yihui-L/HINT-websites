# 两种边界与矢势约束

![矩形边界与第一壁边界的对比示意](assets/boundaries.png)

图为定性 R–Z 截面。两版共同约定：线圈背景 B₀ 已穿透壁且固定，只有响应场受边界约束。

$$\mathbf n\cdot\mathbf B_1(t)=\mathbf n\cdot\mathbf B_{1,0},\qquad \mathbf v|_S=0.$$

zero 初始法向响应为零；vmec 保留准备完成的非零分布。用 F=∂A₁/∂t 表示更新，只约束 F，不把完整 A 或 curl(A) 重置。时间规范下 F=−E；冻结 B₁n 是法拉第定律给出的磁通约束，不等于要求总 Bn=0。模型没有有限电阻壁电流方程，也不是真空开放边界匹配问题。

## debug：矩形边界

R/Z 两层保护节点上的 F 切向分量为零，因而 curl_h(F) 的法向分量为零；速度为零，phi 周期。B₁由 A₁导出后不再独立外推切向 B。物理冻结法向条件保留，但旧 B 表示的独立保护层闭合被 A 闭合替代。

第一壁仅截断磁力线并界定压力/源电流支持。壁外到矩形边界仍演化 A₁和 v；eta1=0 表示继承 eta0，eta1 不同于 eta0 时保留原十次 R/Z 平滑。这不是无质量真空 Maxwell 外域。矩形域过近仍会影响平衡，不能由“与原版边界原理一致”推出无限空间自由边界结果。

## wall：三维第一壁

物理更新只在第一壁内；壁外 A 值仅作导数与插值的数值支持，不代表壁外 MHD 演化。先用原感应通量 ghost 延拓，然后在 signed-distance 的网格边零交叉处约束**同一 Hermite 解析旋度**的法向增量。

以 L 表示这些离散壁点处的法向 curl 迹，每行按其范数归一化：

$$ (L L^T)y=L F,\qquad F_c=F-L^Ty,\qquad L F_c=0. $$

这是节点 A 增量的最小欧氏范数边界修正，只改变壁迹支撑中的节点；不是对 B 的全体积投影，也不是修改 B₀或新增物理电流。稀疏 CG 每个 RKG 阶段执行，默认上限 512、残差容差 1e-11；不满足接受标准则拒绝区间。

**精度边界：**冻结法向条件在这些配点处满足代数容差，不代表在精确 CAD 壁面每一点都精确满足。signed-distance 几何、法向和点间迹仍有空间误差。ghost 前处理沿用原电边界，末尾约束保证其冻结磁通结果；不能据此宣称投影后连续切向电场处处严格为零。边界敏感的定量结果仍需几何/网格加密验证。

## 磁场散度

两版都以共享张量算子的恒等式 D_h curl_h(A)=0 保持节点无散。连续插值采用同一个 A 的解析 curl。新版演化删除旧 divB 扩散与 B 状态投影参数；不可把新壁面 CG 容差当成磁场散度容差。

源码：[矩形闭合](source:debug:src/hint_debug/solver/box.py)、[壁延拓](source:wall:src/hint_wall/solver/wall.py)、[矢势壁约束](source:wall:src/hint_wall/solver/potential_boundary.py)、[推进](source:wall:src/hint_wall/solver/step_b.py)。
