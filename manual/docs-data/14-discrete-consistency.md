# 离散系统、插值与一致性

## 两种散度不要混淆

主程序以节点B为状态，四阶差分计算J、力和散度。插值器以由节点数据积分得到的面磁通为自由度。两者同在HINT均匀柱坐标网格上，但离散算符不同。

$$D_h\cdot B=\frac{D_R(RB_R)+D_\phi B_\phi}{R}+D_Z B_Z.$$

不能要求相容面磁通插值的点值散度逐点等于上述FD4结果，也不能把初始有跳跃的B自动解释为无散数据。

## 直接B的相容重构

令计算坐标为(R,Z,phi)，磁通密度为：

$$q=(RB_R,RB_Z,B_\phi),\qquad \nabla\cdot B=\frac{\partial_Rq_R+\partial_Zq_Z+\partial_\phi q_\phi}{R}.$$

四个子区间上的五个节点定义四次Lagrange基L_i，定义三次积分基：

$$e_i(\xi)=-\sum_{j=0}^{i}L'_j(\xi),\qquad
\int_k^{k+1}e_i(\xi)d\xi=\delta_{ik}.$$

法向分量用L，横向用e：

$$q_R=\sum_{i,j,k}F^R_{ijk}L_i(R)e_j(Z)e_k(\phi),$$

另两分量循环置换。F来自局部四点三次源数据在横向区间的积分（两点Gauss对此多项式精确）。系数导数即面差分的关联矩阵，保证：

$$\int_{\rm cell}\nabla\cdot B\,dV=\sum_{\rm faces}\Phi_f.$$

这继承[拟态微分形式方法](https://arxiv.org/abs/1111.4304)的交换结构，不是HINT全系统改成有限元。相邻宏单元法向迹连续，切向迹不保证C1。只有面差分散度为零时，重构才保留相应零散度；非零值不会被投影掉。光滑区域场值误差为四阶，原始节点数组不改，但并非所有横向节点都精确插值。

## 初始化及壁

内部总B=wout，外部总B=线圈B+外部VC。LCFS跳跃保留。节点数据写入后才开始边界闭合和演化。插值不使用人为LCFS修正带，不改变s。

debug使用整个矩形域；wall只推进第一壁内。为避免宽模板读到无效外部占位零，wall响应场的辅助支撑从有效物理/虚点延拓，固定真空场不受此处理。物理节点、虚点和保存数据不被该辅助处理覆盖。近壁精度另做检查，不能由内域四阶推断。

## 时间与其他变量

$$p_\pm=\frac{\int_\pm p\,dl/|B|}{\int_\pm dl/|B|},\qquad p_{\rm new}=(p_++p_-)/2.$$

Step-A在当前B上进行有限长度双向平均，失败方向贡献零；随后重建s。Step-B冻结本轮p/s，使用四阶段RKG推进B₁/v，包含正的kdivb grad(divB₁)。压力攀升/维持只改变幅度，不恢复初始磁面。

p沿线用周期三次，负取样裁零；输出p/s及壁距离线性；v/J分量插值不强加磁场约束。每次源B变化即失效旧磁系数缓存，CPU/JAX共用核，follow不复用其他时刻的场。

## 检验与存储

$$E_{\rm mean}=\frac{\operatorname{mean}(h_i|\nabla\cdot B_i|)}
{\operatorname{mean}(|B_i|)},\qquad h_i=\min(\Delta R,\Delta Z,R_i\Delta\phi).$$

分别报告FD4网格、面磁通单元平均、解析插值导数及独立JAX Jacobian。均值、P95/P99、极大值及场值误差各有作用；小散度不能证明磁面正确。

schema20存B₀、初始B₁参考、每步总B/p/v/s与恢复元数据，不存A和派生插值系数。初始化第0步在演化前写入；follow使用当前s，不覆盖初始标签。

源码：[B插值](source:debug:src/hint_debug/magnetic.py)、[Step-B](source:debug:src/hint_debug/solver/step_b.py)、[壁闭合](source:wall:src/hint_wall/solver/wall.py)、[存储](source:debug:src/hint_debug/storage.py)。
