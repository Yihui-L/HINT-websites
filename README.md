# HINT Websites

独立的静态网站。统一入口为 [index.html](index.html)，不依赖求解器仓库，不需要运行 HINT。GitHub 仓库保持私有，未开启公开 Pages。

| 目录 | 内容 |
|---|---|
| [Source-Code](Source-Code/README.md) | HINT-debug / HINT-wall 程序与使用手册 |
| [NCSX · debug · VMEC](EX-NCSX-debug-vmec-unscale-component/README.md) | 三维输入几何、初始场和第 50 步结果 |
| [NCSX · debug · zero](EX-NCSX-debug-zero-unscale-component/README.md) | 20 步压强攀升、初始真空场与第 70 步结果 |
| [NCSX · wall · VMEC](EX-NCSX-wall-vmec-unscale-component/README.md) | 第 0–12 步及第一壁诊断，第 13 步中止 |
| [W7-X · debug · VMEC](EX-W7X-debug-vmec-unscale-component/README.md) | 自由边界 VMEC 复现、三维输入几何与第 50 步结果 |

## 本机预览

在仓库根目录运行以下命令，然后打开 [本机首页](http://127.0.0.1:8765/)：

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

本机 HTTP 服务用于加载三维页面的 JS 模块和几何文件。地址只在运行服务的机器上可用，不是供合作者访问的在线链接。

## 维护

手册的独立重建与版本刷新见 [Source-Code/README.md](Source-Code/README.md)。保留算例的已收录输入、图片、诊断与生成脚本；不要提交求解输出、运行缓存或凭据。达到计划步数不代表收敛。
