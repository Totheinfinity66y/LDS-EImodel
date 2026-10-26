# 本地归档与版本化范围

本轮完整扰动率NPZ位于 `../data/dynamics/`，保留本地，不从磁盘删除；输出哈希、配置/源身份和原始输入哈希在同目录summary.json。其规模约数百MB，Git仅版本化该索引、数值CSV、可执行分析/绘图代码及最终图。统一CLI在NPZ缺失或损坏时按已核验原始v2数据重建。

`../reference_evidence/` 为论文PDF与原图核验材料，仅保留本地。公开来源URL、实际下载身份/哈希、视觉核验状态在config/reference_evidence_manifest.json和FIGURE_REFERENCES.md，不将论文图当本模型结果或重复分发进仓库。

所有本轮其他未忽略代码、文档、配置、指标、标准轨迹和图表进入同一提交提案。既有PPTX修改排除；未执行推送。提交成功与否必须由commit ID和Git状态读回确认。
