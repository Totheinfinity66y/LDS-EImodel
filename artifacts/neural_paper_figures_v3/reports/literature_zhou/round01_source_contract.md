# round01 — 原数据与图形语义

- 请求：核实 Zhou 2023 Figure 7 的原数据矩阵、干预、PCA、统计与代码。
- 专家 ID：zhou_v3。
- 执行：读取 Paper2Agent/Paper2Skill、既有正式文献包与原数据契约；实时打开作者 GitHub；实际打开原 p10 Figure7 与 p13 Methods。
- 证据：`audit/paper2agent/zhou/figure7-source-page10.png`、`methods-source-page13.png`、`INPUT_CONTRACT.json`、作者 `standard_analysis.py`。
- 响应：256 recurrent rates；0.25 输入扰动、cue后500 ms、50 ms；配对 frozen noise；全状态 cross-Euclidean；Fig7c n=17 训练网络。Fig7 PCA 拟合集合 unknown，不能认定 control-only 为原方法。
- 状态：SOURCE CONTRACT PASS_WITH_LIMITS；原作者 Figure7 执行 BLOCKED（无 checkpoint/MATLAB Figure7 实现/原数据）。
- 输出：`../REFERENCE_METHOD_MAP_ZHOU.md`。

本轮没有重新运行作者神经模型，未重新声称十八页视觉覆盖；复用已有 strict reviewed 文献包，本轮图像核验限定原 p10/p13。
