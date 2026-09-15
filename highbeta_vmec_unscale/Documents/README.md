# NCSX 结果浏览网站

在线入口：[NCSX 第 100 步结果浏览器](https://yihui-l.github.io/HINT-websites/highbeta_vmec_unscale/Documents/)。网站公开访问，原 GitHub 仓库仍为私有；GitHub 档案和源码链接需要仓库权限。

也可在浏览器直接打开 [index.html](index.html)，无需服务器、HINT 环境或网络。网站展示本算例现有 84 张 PNG，可按内容分类、关键词检索、打开大图、前后切换及下载原始 PNG。

## 范围

- 第 100 步完整空间结果与 0–100 步历史；HINT-debug 0.8.8 / e3c9155。
- initial / vmec / scale_after=false；人工按指定步数停止，不是收敛验收。
- 原图仍保留在 `../figures/`，不复制大文件、不重采样或更改 PNG；网站需与整个算例目录一起使用。
- 数字摘要来自 `../README.md`，不从图片反推或重算 NetCDF。
- 输入下载仍指向本算例的 TOML 和壁文本。未补传 wout、mgrid 或结果 NetCDF。

## 管理

`docs-data/result-notes.md` 为说明源稿；`docs-data/results.json` 包含本次配置、每图分类/分辨率/SHA-256 和文件校验值。`assets/` 为本地脚本和样式。所有新增的网站逻辑及说明均在本 Documents 下，原结果只引用不移动。

重建需要 Python 3.11+ 和 `Markdown==3.10.3`：

```bash
python -m pip install Markdown==3.10.3
python highbeta_vmec_unscale/Documents/tools/build_site.py
```

构建只索引 PNG，不运行计算或绘图。已审阅数字和预期图数属于固定档案；当结果替换时，应先更新说明和摘要，不能只自动刷新图片索引而沿用旧数字。

## 公开发布

当前账号套餐不支持从私有仓库发布 Pages，因此仅将静态文件放入单独的公开仓库 [HINT-websites](https://github.com/Yihui-L/HINT-websites)。Pages 发布该仓库 `main` 分支根目录，HTTPS 强制开启。网站保留 `highbeta_vmec_unscale/Documents/`、`figures/`、输入 TOML、壁文本和 README 的相对关系。不会发布 `startup_zero/`、wout、mgrid、结果 NetCDF、求解器或私有仓库 Git 历史。

重建后，导出到新的空目录，核对清单，将其中 `highbeta_vmec_unscale/` 同步至公开仓库的同名子目录，再提交并推送：

```bash
python highbeta_vmec_unscale/Documents/tools/export_site.py /tmp/ncsx-results-public
```

导出器按文件、目录及扩展名白名单复制，拒绝符号链接及非空目标目录。导出根目录的跳转页用于单独部署本结果网站；合并到 HINT-websites 时不要覆盖公共仓库根入口或 `manual/`。更新本私有仓库不会自动更新网站，必须重新导出并同步公开仓库，随后 Pages 自动部署。公开下载的 TOML 和壁数据不应包含凭据；新增公开资料需先审阅。

[程序手册](https://yihui-l.github.io/HINT-websites/manual/)解释模型、数值方法、参数、输入输出与统计；本网站解释本次结果。源码快照与算例档案快照分别记录，避免混用。
