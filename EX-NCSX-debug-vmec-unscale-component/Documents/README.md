# 当前结果网站维护

`docs-data/` 为当前任务数据、图像清单与溯源。`assets/` 为此站独立资源，`tools/build_site.py` 读取PNG、输入和统计数据生成网站，不重新进行物理计算。

构建：`python Documents/tools/build_site.py`（标准库）。源数据在远程运行目录；生成图像的脚本见上一级 `tools/`。更新必须整体匹配源码版本、输入、迭代步及图像，不混入历史任务数据。
