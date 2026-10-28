# round02 — LDS 兼容性

- 请求：判断 132-D LDS、control-only PCA、state-kick 与50 ms current pulse如何适配 Zhou 方法。
- 专家 ID：zhou_v3。
- 执行：实际阅读 `reference_reproduction.py` 的 run_mode、input assays、basis 与误差数据写盘路径。
- 响应：全状态 cross-Euclidean 的数学定义可 EXACT METHOD；网络、任务、电流方向、PCA选择与外部clock均 METHOD ADAPTED。训练网络统计和自主 dynamic-attractor 结论 INCOMPATIBLE。
- 数据契约：control/perturbed 前史/clock/tonic/初态配对；同一固定 control-only mean/basis；energy closure；R3 fixed-clock 与 source-time R4终态判据分离；分类不能仅取 argmax。
- 发现：历史 R3_fixed_clock 保留 R3 快照clock，并非 clock=0；既有 state_identity 不足以排除多位置。v3 不得沿用不充分的唯一位置判定。
- 状态：LDS METHOD ADAPTED 可执行；v3 adapter 与实际图尚待 round03/04。
- 输出：`../REFERENCE_METHOD_MAP_ZHOU.md`。
