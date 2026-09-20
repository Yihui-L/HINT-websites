# 文档构建检查

当前手册为HINT-debug / HINT-wall 2.0.0，统一B状态schema20。参数类型和默认值从配置AST生成，示例按字节同步，源码哈希记录于source-manifest.json。

重点核对：直接B₁/v推进、kdivb、FIELDLINES内外分支、LCFS只诊断不修正、相容面磁通插值而非A逆求、两种冻结初始法向边界、follow不覆盖当前s、初始化第0步写入。旧A文件不兼容。

构建后运行verify_docs.py检查链接、MathML、参数、示例和SHA-256；物理回归见两套程序的VERIFICATION.md。
