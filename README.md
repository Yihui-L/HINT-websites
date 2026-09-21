# HINT Websites

HINT 的独立公开网站。源码和网站分开维护；HINT-docs 源码仓库仍为私有。

| 一级目录 | 内容 | 网站 |
|---|---|---|
| `Source-Code/` | HINT-debug / HINT-wall 程序与使用手册，无具体算例记录 | [阅读手册](https://yihui-l.github.io/HINT-websites/Source-Code/) |
| `EX-NCSX-debug-vmec-unscale-component/` | NCSX HINT-debug 2.3.0，VMEC启动，第50步结果 | [查看VMEC启动结果](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-vmec-unscale-component/) |
| `EX-NCSX-debug-zero-unscale-component/` | NCSX HINT-debug 2.3.0，zero启动，200外步、20步压强攀升；已提交，结果尚未发布 | [查看zero启动实例](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-zero-unscale-component/) |

除 Git 管理目录外，仓库保留以上三个一级文件夹。各有独立入口，不依赖其他网站的资源文件。根目录仅保留 `.nojekyll` 和本 README，分别用于静态发布配置和仓库说明。

## 内容边界

- `Source-Code/` 包含正文、参数表、通用模板、资源、构建与校验工具。文件夹名称不表示其中包含求解器源码。
- 实例目录分别维护输入、图片和结果说明。VMEC实例保留第0步、第50步及0-50步历史；zero实例当前仅含输入与提交状态，不混用旧图。网站提交状态是静态快照，不是实时任务监控。
- 不上传 wout、mgrid、计算 NetCDF、凭据、运行缓存或私有仓库 Git 历史。
- 初始化磁面图和达到预定外迭代步数均不等价于已经验证力平衡收敛。

## 维护与发布

通用手册的构建命令见 [Source-Code/README.md](Source-Code/README.md)。实例的输入、图片、方法说明和结果清单只在各自实例目录维护。

GitHub Pages 使用 `main` 分支根目录并强制 HTTPS。提交推送后需要等待 Pages 构建完成。各网站从各自目录的 `index.html` 进入；仓库根网址不提供首页或自动跳转，也不维护旧网址兼容。
