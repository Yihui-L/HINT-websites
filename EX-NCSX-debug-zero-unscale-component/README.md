# NCSX: HINT-debug / Zero / Unscale / Component

[独立网站](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-zero-unscale-component/)

本目录用于第二个NCSX实例，尚未发布结果图片。状态是提交时的静态记录，不是实时监控。

- HINT-debug 2.3.0，源码提交 `0495705cb52feb85e8db2f31f0cc91034197a01b`。
- `mode="initial"`，`start_point="zero"`，`scale_after=false`，`magnetic_interpolation="component"`。
- 外迭代200步，每个Step-B 1000内步，压强攀升20步；攀升完成后不再强制放缩峰值。
- 144×144×144网格，nfp=3，GPU/JAX；其余物理输入、网格和数值设置与前一VMEC启动例子相同。
- 响应场从零开始，矩形R-Z边界上的响应法向场保持零；真空背景场不受该约束。
- 第0步是真空磁场启动，不执行VMEC响应场初始化。VMEC仍提供几何标签和目标剖面。

## 文件

`ncsx_main.toml`为实际运行配置；`ncsx_follow.toml`为未执行的续算示例；`ncsx_post.toml`为后处理配置。
`inputs/`包含本次线圈及真实壁文本。wout、mgrid及结果NetCDF不上传。mgrid不参与本次计算，但远程原文件保留。
本网站没有完整wout输入，不能仅凭本站文件复现。`status.json`保存版本、运行路径和输入校验和。

本目录不复用前一例图片；远程旧运行结果和缓存按用户要求清除。
