# 两种边界与直接B闭合

两套版本的真空场B₀固定且完全穿透壁，不参与响应场边界条件。零启动冻结B₁·n=0；VMEC启动冻结初始非零法向分布：

$$\mathbf B_1(t)\cdot\mathbf n=\mathbf B_{1,\rm init}\cdot\mathbf n.$$

## debug：矩形R-Z边界

恢复B演化基线的两层R/Z守卫行，法向增量为零，切向分量按原有外推闭合，速度为零，环向周期。第一壁终止磁力线并限制压强/源电流区域，不是磁场边界。壁外仍推进数值松弛变量；eta1=0表示沿用eta0，不是无限真空的Maxwell解。

## wall：三维第一壁

第一壁是演化边界，只推进壁内物理区，使用子网格距离/法向和虚点闭合。没有eta1。仿射参考提升使虚点闭合作用于相对初始场的变化，避免把VMEC初始法向场压成零。初始参考不从洛伦兹力中扣除，J₁仍是完整curl(B₁)。

保留B基线中每个RKG阶段的旋度增量相容约束：用体积内积下的最小修正保持齐次法向条件和增量散度。它与可选的完整状态投影不同，iterations=0不会关闭该增量约束；内部预算至少max(400,4*最大网格维数)。这不在初始化执行，失败则报告，不伪造通过。

较宽的B插值支撑可能触及未计算外部节点。仅对响应场的这些占位支撑，从有效物理/虚点延拓辅助磁通；不改变已保存数据或边界，不对真空场使用壁权重。该延拓近壁较低阶，不能据此宣称全域四阶。

## 散度控制

$$\partial_t(\nabla\cdot\mathbf B_1)
=k_{\rm divB}\nabla^2(\nabla\cdot\mathbf B_1)$$

这是连续内域关系，前提是感应旋度项的散度为零。实际边界和离散误差仍须检查。可选演化投影默认关闭，不在初始化执行。两者都不是开放空间匹配边界；debug需检查箱体尺寸，wall需考虑冻结壁通量的物理约束。

源码：[矩形闭合](source:debug:src/hint_debug/solver/box.py)、[虚点](source:wall:src/hint_wall/solver/wall.py)、[冻结参考](source:wall:src/hint_wall/solver/boundary_reference.py)、[推进](source:wall:src/hint_wall/solver/step_b.py)。
