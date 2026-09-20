# 结果网站检查

- 本实例入口为 `EX-NCSX-debug-vmec-unscale-component/index.html`，转到本目录的 `Documents/index.html`；不依赖仓库根入口或自定义 404 页面。
- CSS、JS、图片和元数据均在实例目录内部；Source-Code 仅为另一个网站的导航链接。
- 当前展示 85 张 PNG，分别为收敛与耗时 10、二维截面 32、一维剖面 32、庞加莱 6、旋转变换 5。页面明确区分第 0 步和第 100 步，不将暂存的历史数据称为当前 component 运行结果。
- 构建器校验 PNG、TOML、壁文件与 README 的哈希及元数据，不运行求解器、不重绘图片。当前文件清单见 `results.json`。
- 链接、图片及输入哈希使用 Source-Code 的 `tools/verify_docs.py --results` 检查；桌面和移动端交互使用 `tools/check_browser.cjs` 检查。
- 浏览器检查包括分类、搜索、空结果、图片放大、键盘关闭、页面横向溢出及 JavaScript 错误。关闭 JavaScript 后仍可直接浏览和打开原图。
- `viewer-image` 初始为空，打开图片时由脚本设置图片地址和替代文本。
- 检查产物放在临时目录，不提交运行缓存、截图副本或大型 NetCDF 文件。
