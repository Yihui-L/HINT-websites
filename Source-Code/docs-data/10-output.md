# NetCDF 与 IPO 管理

## 输入 → 过程 → 输出

| 任务 | 输入 | 输出 | 是否需要外部 wout/coils/壁 |
|---|---|---|---|
| initial | main.toml + wout.nc + coils.txt + 壁文本 | 一个统一 equilibrium.nc + stdout 日志 | 都需要 |
| follow | follow.toml + 已有统一结果 | 向同一文件追加完整状态 | 不需要；使用内嵌准备数据 |
| 数值后处理 CLI | post.toml + 统一结果 | 独立 analysis.nc | 不需要 |
| Notebook 绘图 | 统一结果 + Python 调用 | PNG/PDF/SVG，可取得返回数组 | VMEC 叠加需 wout；不需线圈/壁文本 |

3 个旧预处理程序已整合进 initial。用户不再手工衔接 flx/vac/lim 三个输出，也不再以旧 NAMELIST 作为新版输入。后处理 TOML 配置的是数值分析内容；它不是所有 Notebook 绘图参数的序列化文件。

## 统一文件 schema 21

两版各有自己的 schema 属性，不能交叉续算。新状态仅保存必要基础量：

```text
/ R, Z, phi, nfp, B_reference, length_reference, density_reference, alfven_time_reference
/preprocess/flux             initial norm_s 与来源
/preprocess/profiles         目标压力、lambda、电流幅度
/preprocess/vacuum/B         固定 B0，T；线圈文本、电流密度、半径、诊断
/preprocess/wall             mask、distance、normal、对称性与来源
/preprocess/initial_response_B  vmec 初始冻结法向参考 B1，T
/equilibrium/B               每完整记录的总 B，T
/equilibrium/velocity        m/s
/equilibrium/pressure        Pa
/equilibrium/norm_s          当前演化标签
/equilibrium                time、outer_step、攀升状态、轴热启动、配置、完成标记
/equilibrium/stepb_diagnostics  可选内步标量历史
```

读取B0与总B，以B1=B-B0、J1=curl(B1)/mu0得到响应及电流，不求A。time 是归一化阿尔芬时间；axis_seed_R/Z 是归一化热启动元数据；三维场使用 SI 并不意味着内步标量也自动变成 SI。

同步基础数组后发布完整标志。不完整记录跳过。B0与初始B1参考只存一次；后者不能被当前B1覆盖。初始化未迭代状态立即写入outer_step=0。插值系数、J、grad(p)及力残差可重建，不重复保存。

Step-B 的 divb 字段为所选插值器的 JAX AD 采样诊断，不是网格差分散度。新增 `/equilibrium/magnetic_diagnostics`，独立于 `save_every` 和 `store_stepb_diagnostics`，保存第0步及每个外迭代的真空场、响应场和总场统计量，不保存三维散度场。变量命名 `divb_ad_<vacuum|response|total>_<mean_abs|mean_normalized|rms|max|sample_count>`，绝对统计量单位 T/m，归一化指标无量纲，采样范围为壁内最多1024个固定原网格节点。`max` 是采样最大值而非全空间上界。记录还含 `outer_step/time/interpolation/sample_complete`。诊断失败以 NaN 和采样数0表示并写日志，不中止演化。follow 会使超出恢复检查点的诊断记录失效。

`convergence.enabled=true` 时后处理输出 `magnetic_convergence`，直接复制上述记录，不重算磁场。绘图脚本可用 `time_series` 读取任意 `divb_ad_*` 变量，也可用 `HintPlots.magnetic_history()` 读取全部统计。

新主程序 follow 只接受 schema 21 的 B 状态。旧 schema（含1.x的A状态）均明确拒绝，不提供格式升级或兼容读取。后处理需稳定结果或安全副本，不承诺正在写入的 HDF5 可任意并发读。

## analysis.nc

数值后处理按内容写入独立文件，包含采样几何、壁信息和 `/postprocess/<内容>/run_*` 结果。重复分析不直接覆盖输入平衡；每次 run 的完整标志和 latest_run 记录用于识别有效结果。追加时检查来源文件与几何一致性，不能把不同算例悄悄混入一个 analysis.nc。

分析文件当前使用 `hint_analysis_schema=1`，根组含 R、Z、phi、nfp 和 `source_equilibrium`；壁距离场在 `/geometry/wall/signed_distance`。它不是主程序 schema 21 checkpoint，不能将 analysis.nc 当作 follow 输入。

fields 的壁外采样约定为 −1；导数量还提供有效节点掩膜。其他结果可使用 NaN/状态码标识失败。统计时必须尊重 mask/status，不能把 −1 当成真实负场强或把失败轨迹当成零旋转变换。

## 存储成本与安全

单个 3D 标量 double 原始大小约 `8*nr*nz*ntor` 字节，矢量为三倍；保存 B、v、p、s 每状态约 8 个标量场，还需坐标/元数据/压缩开销。历史文件大小随保存次数增长，压缩率取决于数据，不是固定保证。

用 `save_every` 控制完整状态间隔、`diagnostics_every` 控制标量密度；关闭标量存储会丢失内部步历史。不要仅为释放空间删除仍用于 follow 的唯一结果。异地备份应在完整状态或稳定副本上操作。

源码：[统一存储](source:debug:src/hint_debug/storage.py)、[独立分析存储](source:debug:src/hint_debug/postprocess/analysis_store.py)、[后处理流程](source:debug:src/hint_debug/postprocess/pipeline.py)。
