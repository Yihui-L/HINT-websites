# 文档构建检查

当前手册为HINT-debug / HINT-wall 2.2.0，统一B状态schema21。参数类型和默认值从配置AST生成，示例按字节同步，源码哈希记录于source-manifest.json。

重点核对：直接 B₁/v 推进、kdivb、FIELDLINES 内外分支、LCFS 源数据只诊断不修正、默认 component 与可选耦合向量 RBF、实际插值器的 JAX 自动微分诊断、两种冻结初始法向边界、follow 不覆盖当前 s、初始化第 0 步写入。旧 A 文件不兼容。

手册现独立维护于 HINT-websites/Source-Code。内容边界校验应拒绝具体装置名称、真实输入数据和运行结果；通用 TOML/Notebook 模板单独保存在 docs-data/templates。网站构建不运行物理算例。

构建后运行verify_docs.py检查链接、MathML、参数、示例和SHA-256；物理回归见两套程序的VERIFICATION.md。
