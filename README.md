# HINT 程序手册与算例

本仓库收录 HINT-debug 和 HINT-wall 的公开程序手册，以及 NCSX、W7-X 的四组计算记录。五个站点各自独立发布，打开下表链接即可浏览，无需登录、安装 HINT 或访问求解器仓库。

## 在线入口

| 站点 | 内容与运行状态 | 目录说明 |
|---|---|---|
| [程序手册](https://yihui-l.github.io/HINT-websites/Source-Code/) | HINT-debug 2.3.0 / HINT-wall 2.3.2：模型、数值方法、参数、输入输出与后处理模板。 | [Source-Code](Source-Code/README.md) |
| [NCSX · debug · VMEC 启动](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-vmec-unscale-component/) | 第 0 和第 50 步图集及三维输入几何。完成 50 步，末期力残差和动能上升，未验证收敛。 | [运行记录](EX-NCSX-debug-vmec-unscale-component/README.md) |
| [NCSX · debug · 零启动](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-zero-unscale-component/) | 初始真空场、20 步压强攀升；从第 21 步检查点续算至第 70 步。 | [运行记录](EX-NCSX-debug-zero-unscale-component/README.md) |
| [NCSX · wall · VMEC 启动](https://yihui-l.github.io/HINT-websites/EX-NCSX-wall-vmec-unscale-component/) | 第 0–12 步和第一壁法向场诊断；第 13 步因 RK 阶段离散约束未通过而中止。 | [运行记录](EX-NCSX-wall-vmec-unscale-component/README.md) |
| [W7-X EIM · debug · VMEC 启动](https://yihui-l.github.io/HINT-websites/EX-W7X-debug-vmec-unscale-component/) | 复现的自由边界 VMEC 输入、三维几何及第 0 和第 50 步图集。完成 50 步，末期诊断量上升，未验证收敛。 | [运行记录](EX-W7X-debug-vmec-unscale-component/README.md) |

## 如何阅读算例

- **运行设置：**四例均采用分量磁场插值（`component`）。`unscale` 表示压强达到目标后不再反复放缩轴上压强；VMEC 启动从目标压强开始。
- **三维视图：**NCSX debug 的 VMEC 启动例和 W7-X 展示线圈中心线及初始 VMEC 最后闭合磁面，不是 HINT 末态磁面。
- **诊断：**完成预定迭代不等于达到力平衡。初始源表达式 AD、插值器 AD 和网格四阶差分（FD4）是不同的磁场散度指标，须按各站图注解释。
- **数据范围：**各例按目录说明提供输入、图集、摘要和来源校验值；不包含大型 HINT 输出 NetCDF。W7-X 另提供复现用 VMEC `wout`；NCSX 的 `wout` 未发布。输入几何和第三方资源的来源及使用条件见各算例说明。

## 本机预览

在仓库根目录启动本机 HTTP 服务，再打开 [本机手册](http://127.0.0.1:8765/Source-Code/) 或对应算例的目录网址。交互式三维页面通过 HTTP 加载本地模块和几何数据：

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

## 维护与发布

- 手册从检入的快照独立构建。版本与校验值见[源码快照](Source-Code/docs-data/source-manifest.json)，重建与可选刷新步骤见[手册维护说明](Source-Code/README.md)。
- 更新算例时，同步核对版本、运行状态、图注、数据来源及校验值。运行 `python Source-Code/tools/verify_docs.py` 检查静态链接、手册快照和两套 NCSX debug 图集的清单。
- GitHub Pages 从 `main` 根目录原样发布静态文件。根目录只保留五个站点目录、`README.md` 和 `.nojekyll`，不设总首页；网页内容保留在各自目录。
