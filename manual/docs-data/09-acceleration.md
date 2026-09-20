# 加速、并行与资源

CPU/GPU是硬件，JAX是编译/数组执行系统，OpenMP是共享内存线程API，MPI是进程通信标准，Open MPI是其实现之一。这些不是同义词，也不是线程数越大利用率越高。

| 环节 | 当前执行 |
|---|---|
| 全线圈平滑核心B | 共享源线段，CPU批量线程/GPU JAX、MPI目标分区 |
| VMEC内部B | 批量Fourier和径向数据求值 |
| LCFS外B casing | JAX驻留基础/细分源面片、MPI R-Z块轮转分配 |
| 自适应控制与根求解 | CPU，适合的点批量送JAX |
| 磁场插值设置 | O(N)局部面平均，无全局逆求 |
| Step-A | MPI起点分区、JAX DOPRI5批量追踪，native DOP853参考 |
| Step-B | JAX分片数组、缓存编译RKG块、缓冲区复用 |
| 后处理 | MPI种子、CPU/GPU JAX批量采样/追踪，CPU画图 |
| 文件 | rank0读写协调 |

初始化不再执行内部A/规范路径，不对每个Step-A求B到A逆问题。仅外部点进入VC积分，内域直接读取wout场。规则尺寸填充、FSAL、源缓存等优化不放宽精度要求。

主程序多rank需engine=jax；native主程序仍为单进程参考。用户用mpiexec显式启动，推荐每GPU一个rank，避免多rank争抢同GPU。线程预算取决于亲和性/调度/cgroup；支持的数值库线程池限制过度订阅。并非每一个Python循环都由OpenMP执行。

JAX初始化需先设置闭包常量处理选项，CLI自动完成。多节点仍需用户正确配置通信网络、MPI和JAX环境。本地双rank通过不等于多节点扩展性已验证。

测量应同步GPU输出，区分首次编译、预处理、暖态迭代、I/O。报告实际CPU占用、GPU利用率、MPI ranks和线程预算，不能把空闲线程计入有效并行量。参见[执行说明](source:debug:docs/EXECUTION.md)及[JAX异步机制](https://docs.jax.dev/en/latest/async_dispatch.html)。
