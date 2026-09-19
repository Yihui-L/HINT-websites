# 文档构建检查

当前文档面向 HINT-debug / HINT-wall 1.3.2，主状态 schema 9；精确源码提交、版本和参数数量见自动生成的 source-manifest.json。构建工具从配置 AST 读取默认值、单位说明、类型和分支差异，复制当前示例并校验 SHA-256。

本轮重点核对：A₁/v 推进，A_ref=B_ref L_ref，C2 Hermite 与节点 curl 一致，两种冻结法向边界，只接受当前 A-state 文件，follow 无再次逆拟合，主结果只存必要 A/p/v/s 与恢复元数据。原压强/标签/电流源项逻辑保留。

验证工具检查公式 MathML、本地链接/锚点、示例字节一致、参数覆盖及源文件哈希。源码回归、制造解及实际可用加速环境的检查范围见两版 docs/VERIFICATION.md；不以文档构建或小型测试冒充 NCSX 生产算例、全尺度跨节点性能或精确曲壁收敛验证。
