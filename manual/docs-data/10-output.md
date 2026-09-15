# NetCDF 与 IPO 管理

## 输入 → 过程 → 输出

| 任务 | 输入 | 输出 | 是否需要外部 wout/mgrid/壁 |
|---|---|---|---|
| initial | main.toml + wout.nc + mgrid.nc + 壁文本 | 一个统一 equilibrium.nc + stdout 日志 | 都需要 |
| follow | follow.toml + 已有统一结果 | 向同一文件追加完整状态 | 不需要；使用内嵌准备数据 |
| 数值后处理 CLI | post.toml + 统一结果 | 独立 analysis.nc | 不需要 |
| Notebook 绘图 | 统一结果 + Python 调用 | PNG/PDF/SVG，可取得返回数组 | VMEC 叠加需 wout；不需 mgrid/壁文本 |

3 个旧预处理程序已整合进 initial。用户不再手工衔接 flx/vac/lim 三个输出，也不再以旧 NAMELIST 作为新版输入。后处理 TOML 配置的是数值分析内容；它不是所有 Notebook 绘图参数的序列化文件。

## 统一文件 schema 7

版本有各自 schema 属性：`hint_debug_python_schema` / `hint_wall_python_schema`。以下是数据布局重点；精确字段、属性和单位应以文件自身及 storage.py 为准。

```text
/
  R, Z, phi, nfp
  B_reference, length_reference, density_reference, alfven_time_reference
  preprocess/
    initial_response_B          # VMEC 起点时保存；T
    flux/norm_s_initial
    vacuum/B                   # 固定背景场；T
    wall/inside, signed_distance, normal
    profiles/pressure_s, pressure, current_s, current_shape
    profiles/total_toroidal_current
  equilibrium/
    time, outer_step, record_complete
    B, velocity, pressure, norm_s
    pressure_scale, pressure_ramp_step
    axis_seed_R, axis_seed_Z, axis_seed_valid
    solver_configuration
    stepb_diagnostics/
      time, outer_step, inner_step, sample_complete
      kinetic_energy, response_magnetic_energy, force_max, force_rms
      divb_max, divb_rms, boundary_bn_max, boundary_velocity_max
      force_volume_rms, divb_volume_rms, parallel_pressure_volume_rms
```

`equilibrium/B` 的含义需特别注意：**保存的是总场 B₀+B₁**；减去 `preprocess/vacuum/B` 才得到响应 B₁。向量字段形状为 (time,R,Z,phi,component)，分量序 R,phi,Z。p 单位 Pa，速度 m/s，B 单位 T，`norm_s` 无量纲。`time` 是归一化弛豫时间；乘根组 `alfven_time_reference` 得到换算的弛豫秒数。绘图 API 的变量字符串 `s` 对应文件内 `norm_s`，不要混淆。

轴热启动坐标是归一化求解器元数据，不应未经标度直接当作 m；绘图 API 负责使用正确换算。Step-B 标量诊断是归一化量，不因三维数组采用 SI 就自动成为 SI。

`preprocess/vacuum` 属性包括 mgrid 模式、合成规则、未限幅最大值、磁轴参考、限幅阈值/点数和散度诊断。`preprocess/wall` 包含周期/对称性、几何余量与来源。`initial_response_B` 是后续和 follow 的冻结法向参考，不可当作每步应重置的场。

根组/配置字符串含溯源信息，不要只复制一个 B 数组当作完整可续算文件。主结果内可能存在空的历史兼容 `/postprocess` 组；新版 CLI 的结果在另一个 analysis.nc 中。

## analysis.nc

数值后处理按内容写入独立文件，包含采样几何、壁信息和 `/postprocess/<内容>/run_*` 结果。重复分析不直接覆盖输入平衡；每次 run 的完整标志和 latest_run 记录用于识别有效结果。追加时检查来源文件与几何一致性，不能把不同算例悄悄混入一个 analysis.nc。

分析文件当前使用 `hint_analysis_schema=1`，根组含 R、Z、phi、nfp 和 `source_equilibrium`；壁距离场在 `/geometry/wall/signed_distance`。它不是主程序 schema 7 checkpoint，不能将 analysis.nc 当作 follow 输入。

fields 的壁外采样约定为 −1；导数量还提供有效节点掩膜。其他结果可使用 NaN/状态码标识失败。统计时必须尊重 mask/status，不能把 −1 当成真实负场强或把失败轨迹当成零旋转变换。

## 存储成本与安全

单个 3D 标量 double 原始大小约 `8*nr*nz*ntor` 字节，矢量为三倍；保存 B、v、p、s 每状态约 8 个标量场，还需坐标/元数据/压缩开销。历史文件大小随保存次数增长，压缩率取决于数据，不是固定保证。

用 `save_every` 控制完整状态间隔、`diagnostics_every` 控制标量密度；关闭标量存储会丢失内部步历史。不要仅为释放空间删除仍用于 follow 的唯一结果。异地备份应在完整状态或稳定副本上操作。

源码：[统一存储](source:debug:src/hint_debug/storage.py)、[独立分析存储](source:debug:src/hint_debug/postprocess/analysis_store.py)、[后处理流程](source:debug:src/hint_debug/postprocess/pipeline.py)。
