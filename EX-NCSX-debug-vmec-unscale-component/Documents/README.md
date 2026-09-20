# NCSX 历史结果网站

> **历史 step100 归档，不是当前 component 运行结果。** 原 `highbeta_vmec_unscale/` 已迁移至 `EX-NCSX-debug-vmec-unscale-component/`。现有文件暂存于此，等待当前远程任务完成后另行核验与更新；本次只整理静态网站，不运行远程任务、不修改求解器、不生成新结果。

本地入口：[案例根入口](../index.html)或[初始化与第 100 步历史结果](index.html)。直接用浏览器打开即可，无需服务器、HINT 环境或网络；分类、关键词检索、大图前后切换和原始 PNG 下载均使用本地文件。

发布入口：[EX-NCSX-debug-vmec-unscale-component/](https://yihui-l.github.io/HINT-websites/EX-NCSX-debug-vmec-unscale-component/)。根入口自动跳转至 `Documents/index.html`；站点随 HINT-websites 仓库的发布流程部署。

## 归档范围

- 第 100 步完整空间结果与 0–100 步历史；HINT-debug 0.8.8 / e3c9155。
- 共 85 张 PNG：原有 84 张历史图片，以及此前已归档的第 0 步初始化总场庞加莱；本次不增加图片。[计算方式](index.html#initial-poincare)保留保存态来源、磁力线方程、起点、插值、积分、触壁规则及限制。
- initial / vmec / scale_after=false；人工按指定步数停止，不是收敛验收。
- 原图保留在 `../figures/`，不复制、不重采样、不更改字节；网站需与整个算例目录一起使用。
- 数字摘要来自 [原算例 README](../README.md)，不从图片反推或重算 NetCDF。
- TOML 与壁文本保留历史输入及原始校验值，不改写为当前 component 运行配置。未补传 wout、mgrid 或结果 NetCDF。

## 独立网站与导航

```text
EX-NCSX-debug-vmec-unscale-component/
  index.html                  -> Documents/index.html
  README.md                   历史算例记录与归档范围
  Documents/
    index.html                结果浏览页
    assets/results.css        本地样式
    assets/results.js         分类、搜索与大图浏览
    docs-data/                历史方法、元数据与检查记录
  figures/                    85 张原始 PNG 与原索引
  inputs/                     原始壁文件
  ncsx_*.toml                 原始输入与示例
```

案例与 Source-Code 是两个独立的一级网站。案例的 HTML、CSS、JS、图片和元数据全部位于本目录，不依赖 `manual/` 或 Source-Code 的 CSS、JS、字体及构建流程。

页面中的 [Source-Code / 程序文档](../../Source-Code/) 使用 `../../Source-Code/`，与算例目录同属 HINT-websites 根目录，仅为导航链接。算例记录只留在本目录，不复制到 Source-Code；两站分别维护自己的入口、资源和内容。公开文件入口为 [HINT-websites 新案例目录](https://github.com/Yihui-L/HINT-websites/tree/main/EX-NCSX-debug-vmec-unscale-component)，不依赖已迁出的旧仓库。

## 维护约束

`docs-data/result-notes.md` 是方法说明源稿；`docs-data/results.json` 保留历史配置、图片分类、尺寸、SHA-256 和输入文件校验值。`files["README.md"]` 校验当前含归档说明的 README，`archive_readme_sha256` 保留原历史 README 的哈希；历史来源提交、物理参数、图片元数据与输入哈希不变。构建器逐项验证当前文件，不跳过 README 校验。

原仓库的 `Documents/root-redirect.html`、`Documents/tools/build_site.py` 和 `export_site.py` 已完整迁入并适配。原建站说明另存于 [历史维护记录](docs-data/legacy-site-maintenance.md)，科学说明保留于原算例 README 与方法源稿。

从本案例根目录执行（Python 3.11+，构建依赖 `Markdown==3.10.3`）：

```bash
python -m pip install Markdown==3.10.3
python -B Documents/tools/build_site.py
python -B Documents/tools/export_site.py /tmp/ncsx-case-export
```

构建器先核对既有 JSON、85 张 PNG 和输入文件，再重建 `Documents/index.html` 与案例根入口；不读取 Git、旧仓库、远程数据或 NetCDF，不改写 CSS、JS、JSON、PNG 与 TOML。归档标记和独立站点导航已固化在本地构建模板中。

导出器拒绝非空目标、案例内部目标及符号链接，只将获准文件复制到目标根目录，保留入口、资源与这两个维护工具。导出目录本身即可作为独立案例站点；Source-Code 只是可选的同级导航目标，不影响独立浏览。检查记录见 [WEBSITE_CHECKS.md](docs-data/WEBSITE_CHECKS.md)。

未来当前 component 结果的发布需另行核验来源、版本、步号与统计口径，不能仅替换图片或把本档案改标为新结果。发布时保持本目录内部相对路径；不覆盖 HINT-websites 根入口或 Source-Code，不发布求解器、私有 Git 历史及未审阅的大型原始数据。
