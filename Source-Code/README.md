# HINT 程序与使用手册

[在线阅读](https://yihui-l.github.io/HINT-websites/Source-Code/) · [程序源码（需仓库权限）](https://github.com/Yihui-L/HINT-docs)

本目录是 HINT-debug / HINT-wall 通用网站手册的唯一维护位置，由原 `HINT-docs/Documents/` 迁入。仅包含物理模型、数值方法、输入输出、参数模板、后处理接口和维护工具；不包含任何装置算例、运行日志或结果图片。源码包的 `docs/` 仍随包保留。

这是独立的静态网站，自有入口、样式、脚本与数据。`index.html` 可离线打开，无远程字体、脚本或公式服务依赖。源码版本及逐文件 SHA-256 见 `SOURCE_VERSION.md`、`docs-data/source-manifest.json`。源码权限与本公开网站相互独立。

## 目录

```text
Source-Code/
  index.html                 网站阅读入口，自动生成
  README.md                  维护说明
  SOURCE_VERSION.md          源码版本记录，自动生成
  assets/                    样式、检索脚本、通用数值流程示意
  docs-data/                 Markdown 正文、参数说明及生成的索引
    templates/debug/         通用 TOML 和未执行 Notebook
    templates/wall/
  tools/                     构建、静态校验及浏览器检查
```

## 重建

Python 3.11+。在 HINT-websites 根目录运行，显式提供独立的源码检出位置：

```bash
python -m pip install -r Source-Code/tools/requirements.txt
python Source-Code/tools/build_docs.py --source-repo /path/to/HINT-docs
python Source-Code/tools/verify_docs.py --source-repo /path/to/HINT-docs
```

也可设置 `HINT_SOURCE_REPO`；若未指定，工具寻找与 HINT-websites 同级的 `HINT-docs/` 或 `HINT-docs-sync/`。构建只读取源码 AST、安装元数据与独立绘图变量目录，不运行求解器或算例，不将源码复制到网站仓库。

无源码访问权限时，可以验证已有网站的链接、公式、参数和结构：

```bash
python Source-Code/tools/verify_docs.py
```

有源码时额外校验参数覆盖、模板字节一致性和源码哈希。构建自动刷新默认值，但模型文字仍需人工审查，不能用文档检查替代物理验证。

浏览器检查需 Node.js、Playwright 和 Chromium。运行 `node Source-Code/tools/check_browser.cjs Source-Code /path/to/result-website /tmp/hint-site-check`；省略结果目录可只检查手册。截图保存在指定临时目录，不提交至本目录。

## 更新与发布

1. 先核对当前源码版本，再修改 `docs-data/` 正文和 `parameter-notes.json`。
2. 重建并运行静态及桌面/移动浏览器检查，审查生成结果。
3. 仅提交文档、资源、通用模板与工具；不加入密钥、真实物理输入、NetCDF、计算日志或私有源码。
4. 推送 HINT-websites 的 `main` 后，现有 GitHub Pages 从仓库根目录发布。

不要继续在 HINT-docs 仓库维护 `Documents/` 副本。文档工具只需要源码读取权限，网站可独立部署。
