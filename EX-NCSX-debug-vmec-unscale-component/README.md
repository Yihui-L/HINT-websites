# NCSX: HINT-debug 2.2.0, VMEC / Unscale / Component

本目录只展示当前 50 步任务，旧算例内容已替换。主程序正常达到外迭代上限，不代表已经通过力平衡收敛验收。

- [结果网站](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-vmec-unscale-component/)
- 网格 144×144×144，nfp=3，矩形 R–Z 边界，真实第一壁用于追踪截断。
- initial、start_point=vmec、scale_after=false、magnetic_interpolation=component。
- 外迭代 50，每外迭代 Step-B 1000 内步；VMEC 起点没有压强攀升或后续幅度放缩。
- 源码提交：84c2cf2e2ce7fb956c7b101a57722a681156e9ac。
- 结束时间：2026-09-20 16:44:15 UTC / 2026-09-21 00:44:15 北京时间。

## 内容

`ncsx_main.toml` 为实际运行配置；`ncsx_follow.toml` 是未执行的续算示例；`ncsx_post.toml` 是当前数值后处理 CLI 示例。`inputs/` 包含本次线圈与真实壁文本。图像由 `tools/` 中的算例脚本调用已安装的 HINT 绘图 API 生成，参数不完全等同于 CLI 示例。

`figures/` 仅存 PNG。第0步初始化图、第50步末态图和0–50步历史均来自同一个任务。末态庞加莱使用1422个壁内起点，初始化图使用138个径向起点，两者点密度不能直接比较。完整统计口径、旋转变换检查、文件SHA-256见网站。

## 散度指标

网格四阶差分散度用于了解离散方程中的约束误差，但粗网格截断误差可能显著，不能当作连续源场误差。component 插值器 JAX AD 用于判断磁力线实际取样场的散度；AD 无差分步长，但不消除插值误差。末态另取32768个壁内节点和32768个离网格点，使用float64 AD，并以2048个离网格点的扩展精度多项式解析导数交叉核验。交叉检验的数值求导误差和场本身散度是两个不同指标，不能把前者小值冒充后者。

不上传wout、mgrid、主程序或后处理NetCDF、运行缓存或凭据；mgrid不参与此次运行。缺少wout及结果NetCDF时，不能仅靠本公开目录复现主程序或后处理。

## 初始源场直接求导

网站补充了初始线圈场、LCFS内wout重构场、LCFS外virtual-casing场的float64 JAX直接求导结果，未使用HINT网格磁场插值。线圈场及外部casing核散度接近舍入量级，但当前wout重构场包含径向系数插值，不应据此假定其数值散度也达到机器精度。LCFS跳跃需单独看待；这些有限采样结果不代表界面连续性。数据及核验脚本见 `Documents/docs-data/initial_source_ad.json` 和 `tools/check_initial_source_divergence.py`。
