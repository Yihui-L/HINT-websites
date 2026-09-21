# HINT Websites

HINT 的两个独立公开网站。源码和网站分开维护；HINT-docs 源码仓库仍为私有。

| 一级目录 | 内容 | 网站 |
|---|---|---|
| `Source-Code/` | HINT-debug / HINT-wall 程序与使用手册，无具体算例记录 | [阅读手册](https://yihui-l.github.io/HINT-websites/Source-Code/) |
| `EX-NCSX-debug-vmec-unscale-component/` | NCSX 当前 HINT-debug 2.2.0 第 50 步结果 | [查看实例档案](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-vmec-unscale-component/) |

除 Git 管理目录外，仓库只保留以上两个一级文件夹。各有独立入口、样式、脚本和数据，不依赖对方的资源文件。根目录仅保留 `.nojekyll` 和本 README，分别用于静态发布配置和仓库说明；浏览网站请使用上表中的两个独立入口。

## 内容边界

- `Source-Code/` 包含正文、参数表、通用模板、资源、构建与校验工具。文件夹名称不表示其中包含求解器源码。
- 实例目录集中维护输入、图片和结果说明。当前展示 HINT-debug 2.2.0 的 VMEC / unscale / component 任务：初始化第0步、完整第50步及0–50步历史；旧实例内容已整体替换。
- 不上传 wout、mgrid、计算 NetCDF、凭据、运行缓存或私有仓库 Git 历史。
- 初始化磁面图和达到预定外迭代步数都不等价于已经验证力平衡收敛。

## 维护与发布

通用手册的构建命令见 [Source-Code/README.md](Source-Code/README.md)。实例的输入、图片、方法说明和结果清单只在实例目录维护。

GitHub Pages 使用 `main` 分支根目录并强制 HTTPS。提交推送后需要等待 Pages 构建完成。两个网站分别从各自目录的 `index.html` 进入；仓库根网址不提供首页或自动跳转，也不维护旧网址兼容。
