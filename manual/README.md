# HINT 程序与使用手册

在线入口：[HINT 程序与使用手册](https://yihui-l.github.io/HINT-websites/manual/)。网站公开访问，源码仓库仍为私有；页面中的 GitHub 源码链接需要相应仓库权限。

也可直接在浏览器打开 [index.html](index.html)。这是可离线使用的静态网站，不需要运行开发服务器或安装 HINT；GitHub 的 HTML 源码预览不是网站部署。

网站参考同账号 M3DC1-docs/Documents 的阅读与资料组织方式，依据当前 HINT-debug / HINT-wall 源码编写。含模型与归一化、源项、初始响应场、Step-A/B、边界与散度、并行、完整参数表、NetCDF、后处理、统计与使用限制。

## 文件布局

- `index.html`：生成的阅读入口；公式已转换为 MathML，无在线脚本/字体。
- `assets/`：页面样式、检索脚本、科学流程/边界示意 PNG。
- `docs-data/01-*.md` 至 `14-*.md`：可编辑正文。
- `docs-data/parameter-notes.json`：人工核对的参数含义，按配置类组织。
- `docs-data/parameters.json/csv`：从配置 AST 提取的完整展开表。
- `docs-data/variables.json`：两版绘图变量目录。
- `docs-data/examples/`：源码示例原样副本，非自足物理算例。
- `docs-data/source-manifest.json`、`SOURCE_VERSION.md`：源码快照、参数数量、SHA-256。
- `tools/`：构建与校验，依赖只用于文档，不属于求解器依赖。

## 重建

在仓库根目录：

```bash
python -m pip install -r Documents/tools/requirements.txt
python Documents/tools/build_docs.py
python Documents/tools/verify_docs.py
```

可选浏览器检查：安装 Playwright 及其 Chromium 后，运行 `node Documents/tools/check_browser.cjs Documents /path/to/test_HINT-debug_ncsx/highbeta_vmec_unscale/Documents /tmp/hint-docs-browser`。截图和测试报告写入指定临时目录，不放入求解器目录。

Python 3.11+。构建不导入求解器、不启动 JAX、不运行算例；只对已审阅的独立变量目录使用 runpy。默认值从 dataclass AST 提取，新增参数缺少中文含义时构建失败。正文中的 `source:debug:...` / `source:wall:...` 转为固定源码提交链接。

源快照使用最近触及两个程序目录的提交，而不是文档提交，因此文档自身提交不会递归改变源码标记。参数默认值变化会自动更新表格，物理说明仍需人工复查，自动提取不能验证文字物理正确性。

文档验证不替代求解器单元测试、网格收敛或独立 benchmark。当前手册包含 2.0.0 直接B演化和FIELDLINES初始化迁移；具体测试和兼容性限制见两版本 docs/VERIFICATION.md。

## 公开发布

当前账号套餐不支持从私有仓库发布 Pages，因此网站托管于单独的公开仓库 [HINT-websites](https://github.com/Yihui-L/HINT-websites)。Pages 使用该仓库 `main` 分支根目录，手册位于 `manual/`，HTTPS 强制开启。公开内容为本文档、网站资源、参数数据及文档示例；求解器、测试、算例 NetCDF 和私有仓库 Git 历史不在发布仓库中。

重建并校验后，用下列命令导出到新的空目录，再审阅清单，将导出内容同步至公开仓库的 `manual/`（只同步此子目录），提交并推送：

```bash
python Documents/tools/export_site.py /tmp/hint-manual-public
```

导出器只复制允许的目录、文件及扩展名，拒绝符号链接和非空目标目录。更新本私有仓库的文档不会自动更新网站，必须重新导出并同步公开仓库；公开仓库推送后 Pages 自动部署。发布脚本保留在私有源码仓库，不属于公开网站。不要将整个源码仓库或其 Git 历史推送到公开仓库。

结果网站：[NCSX 第 100 步结果浏览器](https://yihui-l.github.io/HINT-websites/highbeta_vmec_unscale/Documents/)。它保留结果自身版本/取样/统计说明，不把达到预定步数等同于收敛。
