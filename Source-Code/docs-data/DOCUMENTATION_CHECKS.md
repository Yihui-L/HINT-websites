# 文档构建检查

当前手册为HINT-debug / HINT-wall 2.3.0，统一B状态schema22。参数类型和默认值从配置AST生成，示例按字节同步，源码哈希记录于source-manifest.json。

重点核对：直接 B₁/v 推进、kdivb、FIELDLINES 内外分支、内区同一几何 Jacobian 重构、LCFS 源数据只诊断不修正、默认 component 与可选耦合向量 RBF、源场 AD/插值器 AD/网格 FD4 分开存储、两种冻结初始法向边界、follow 不覆盖当前 s、初始化第 0 步写入。当前文件为 schema22，不读取旧 schema；现有历史结果保留原版本读取方式。

手册现独立维护于 HINT-websites/Source-Code。内容边界校验应拒绝具体装置名称、真实输入数据和运行结果；通用 TOML/Notebook 模板单独保存在 docs-data/templates。网站构建不运行物理算例。

构建后运行verify_docs.py检查链接、MathML、参数、示例和SHA-256；物理回归见两套程序的VERIFICATION.md。
