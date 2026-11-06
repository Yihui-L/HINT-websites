# HINT 程序与使用手册

[阅读手册](index.html) · [网站首页](../index.html)

本目录包含 HINT-debug / HINT-wall 的通用程序手册，不包含装置算例或求解器源码。公式、样式、参数和通用模板均随仓库提供；浏览和常规重建无需连接源码仓库。快照版本与文件校验值见 [SOURCE_VERSION.md](SOURCE_VERSION.md) 和 [版本清单](docs-data/source-manifest.json)。

## 重建

在 HINT-websites 根目录使用 Python 3.11 或以上版本：

```bash
python -m pip install -r Source-Code/tools/requirements.txt
python Source-Code/tools/build_docs.py
python Source-Code/tools/verify_docs.py
```

正文和注释维护在 `docs-data/`；参数、绘图变量和模板从检入的快照读取。已有示意图默认保留，用 `--figures` 显式重绘。

如需同步新的求解器版本，可指定本机有权限读取的源码目录：

```bash
python Source-Code/tools/build_docs.py --source-repo /path/to/source
python Source-Code/tools/verify_docs.py --source-repo /path/to/source
```

该步骤更新参数快照、模板及来源校验值，不导入求解器或运行算例。模型说明须按源码人工核对；文档检查不替代物理验证。
