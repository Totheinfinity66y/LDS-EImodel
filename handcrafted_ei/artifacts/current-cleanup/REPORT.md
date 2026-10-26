# 当前实现独立性与清理验证

当前实现独立包含输入编码、固定E/I回路、连续动力学、时序、行为评价、机制干预、表征、吸引子检测及归档复算。活动运行路径无需历史实现或旧版资料。

本次清理移除旧receipt schema兼容分支与未使用的打包入口；当前复算只接受schema 2。根README、wiki说明、架构配套清单和实现报告只介绍当前实现。已被替代的演示生成脚本、草稿、图片和迁移说明先经逐文件SHA256核验封存，再从活动资料区移除，见superseded_materials.zip与对应JSON索引。

模型拓扑、配置、task和simulation未修改。原科研结果、receipt、源码快照、外部文献资料、现有未提交PPTX保留。归档源码用于对应归档的复现，不作为活动模型入口。

分析复算支持`--report-directory`，可将新核验和源码快照写入独立目录，避免覆盖原科研归档。

验证记录：receipt_red.txt为清理前的真实回归失败；tests.txt、receipt_verification.json、analysis_verification.json与integrity.json记录清理后的测试、独立复算、模型来源及保护文件校验。

实际结果：当前目录32/32测试通过；仅复制当前包、清空PYTHONPATH、排除全部科研归档和项目说明的独立副本同样32/32通过。4,752个trial、72个快照及864个扰动复算PASS；全部自由演化步与保存轨迹一致。当前73个Markdown本地链接有效。原模型、配置、任务、时序、已归档科研结果及外部文献内容无Git差异。
