# NCSX: HINT-wall 2.3.2 / VMEC / Unscale / Component

此目录已建立，计算结果尚未发布。远程任务完成并核验后，将在这里加入输入配置、结果说明和后处理图像；目前页面不代表最终平衡或收敛结论。

- 源码版本：HINT-wall 2.3.2，提交 `8609e184e1d7b8bcabab662ddf1fb170243ded60`。
- 设置：`mode=initial`、`start_point=vmec`、`scale_after=false`、`magnetic_interpolation=component`。
- 网格：144 x 144 x 144；计划 50 个外迭代，每步 Step-B 1000 个内步。
- 壁面条件：响应场的法向分量保持 VMEC 初始化时的分布。

结果入口：[实例状态页](index.html)。运行中的 NetCDF、mgrid 和缓存不会上传到此公开仓库。
