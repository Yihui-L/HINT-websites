# 安装与运行

## 环境与安装

Python **3.11 或更新版本**；当前依赖下限包含 NumPy 2、SciPy 1.14、netCDF4 1.7.2、JAX 0.5、threadpoolctl 3.5。实际解析结果取决于平台。MPI 的系统库/启动器以及 CUDA 驱动不是 pip 自动配置的集群资源。

```bash
git clone git@github.com:Yihui-L/HINT-docs.git
cd HINT-docs
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install './HINT-debug[plots,distributed]'
# 另一版本：python -m pip install './HINT-wall[plots,distributed]'
```

GPU 路径按驱动兼容性选择包内 extra，例如 `./HINT-debug[jax-cuda12,plots,distributed]` 或 `jax-cuda13`。`native/gpu` 使用 `gpu-cuda11` / `gpu-cuda12` 的 CuPy 路径，不要同时安装多个互相冲突的 CuPy CUDA 包。`vmec` extra 是历史兼容入口，内置响应场算法不需要额外安装 virtual-casing。

私有仓库需使用用户自己的 GitHub SSH key 或授权凭据；不要把口令、token 写进 TOML、Notebook 或脚本。多节点运行要求每个节点看到一致的代码、环境和输入路径。

## 最小文件隔离

```text
work/
  source/HINT-docs/              # 源码
  environments/                 # 虚拟环境，可在其他位置
  cases/ncsx/
    main.toml
    follow.toml
    post.toml
    inputs/wout_case.nc
    inputs/coils_case.txt
    inputs/vessel.txt
    run/                        # 结果、日志
    figures/                    # PNG，不混入源码
```

相对路径以 **TOML 文件所在目录** 为基准，不以当前 shell 的工作目录为基准。安装成功不意味着输入几何通过校验。

## 主程序和后处理

```bash
hint-debug main.toml
hint-debug follow.toml
hint-debug-post post.toml
# wall 对应 hint-wall / hint-wall-post
```

没有 Slurm 时可以使用 shell 后台或 screen/tmux。以下启动命令只运行一次，不包含自动重启策略：

```bash
nohup hint-debug main.toml > run/main.log 2>&1 &
echo $! > run/main.pid
tail -f run/main.log
```

停止前确认 PID 对应本次任务。若有 MPI 子进程，按作业/进程组管理，而不是只杀一个任意 Python 进程。不要同时对同一个结果启动 initial、follow 或写入后处理。

MPI 示例：`mpiexec -n 4 hint-debug main.toml`。这只演示启动语法，不代表四个 rank 对任意 GPU/网格都更快。GPU 必须合理绑定设备；多节点由启动器/调度系统分配主机，程序不会自行申请资源。

## 推荐准备顺序

1. 确认 wout 的 nfp、对称性、自由边界平衡及物理剖面，保留其生成信息。
2. 核对线圈周期/对称性、闭合点序、带符号总电流和参考电流密度。
3. 准备严格包围初始 LCFS 的真实壁，并使矩形域留足壁外网格余量。
4. 选 debug/wall、zero/vmec、scale_after，再设网格、时间步和保存策略。
5. 阅读启动诊断：几何残差、背景场限幅/散度、VMEC 响应场投影修正和边界误差。
6. 按完整 checkpoint 评估力、速度、散度和轴闭合，不仅看日志是否继续输出。

文档内提供[debug 示例目录](docs-data/examples/debug/main.toml)和[wall 示例目录](docs-data/examples/wall/main.toml)的源码原样副本。它们不是包含 wout/coils 的自足 benchmark。

源码：[安装元数据](source:debug:pyproject.toml)、[命令行](source:debug:src/hint_debug/cli.py)、[执行约定](source:debug:docs/EXECUTION.md)。
