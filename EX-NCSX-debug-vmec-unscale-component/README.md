# NCSX: HINT-debug 2.3.0, VMEC / Unscale / Component

仅展示本次50步运行及第0步初始化。程序正常达到迭代上限，但末期力残差和动能上升，不能视为力平衡收敛结果。

- [结果网站](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-vmec-unscale-component/)
- 源码提交：0495705cb52feb85e8db2f31f0cc91034197a01b
- 完成时间：2026-09-21T08:48:39.422802+00:00
- 144×144×144，nfp=3，50次外迭代，每次Step-B 1000内步。
- initial / start_point=vmec / scale_after=false / magnetic_interpolation=component；kdivb=1e-4。
- 矩形R-Z边界冻结初始响应法向场，真实第一壁只截断追踪；真空场不受该边界约束。
- 本次2.3.0使用几何、磁通、iota和lambda一致的VMEC内区磁场重构。

## 文件

main是实际配置，follow是未执行的续算示例，post是数值后处理CLI示例。发布副本只更新了历史注释中的版本与提交号，解析后的TOML参数与实际输入完全相同，原文件和发布文件哈希分别记录。输入含线圈及真实壁文本；不上传wout、mgrid或输出NetCDF。

PNG用于网页，庞加莱另有PDF和无损gzip压缩SVG（解压后为SVG）；没有对矢量点进行栅格化。初始图138个径向起点，末态图1422个壁内起点，最多500整环圈。两者点密度不能直接比较。所有图片属于本次同一运行。

## 散度口径

初始化源表达式AD、实际component插值器AD、HINT网格FD4是不同指标。源AD很小不证明插值场也无散。LCFS外补充源AD为64点，平均绝对值1.62022e-16 T/m、最大值1.33574e-15 T/m；固定与自适应积分场值差6.96759e-8 T由用户接受，生产门槛未改动。跨LCFS普通点值解析散度未定义，未计算。

末态高数值精度检验对实际插值器使用float64 JAX AD及扩展精度多项式导数交叉核验，不是把演化后场重新解释为解析源场。完整采样数、归一化、误差和字段含义见网站及Documents/docs-data。正常结束不等同于收敛。
