# Round 1：原始输入契约

agent_id: /root/zhou；paper_id: zhou2023；task_id: B；status: partial-source-verified。

Request：主Agent要求独立通过Paper2Agent核查Figure7实际数据轴、神经状态、输入扰动、共享噪声、PCA、cross-temporal distance和局部场，先给原论文要求，不替LDS设计转换。

Response：见REFERENCE_METHODS.md、INPUT_CONTRACT.json、FIGURE_CONTRACT.json。核心是rate[time,trial,recurrent_unit]、50ms transient input、cue+500ms、0.25、中心输入17、相同noise matrices；Fig7没有velocity-field panel。

Evidence：原PDFp9–10/p12–13；作者standard_analysis.py/network.py/train.py；paper-review prepare/extract结果。

Input files：本地Zhou2023.pdf、作者source zip；Output files：本目录5份契约/报告与本记录。

Open questions：原数据/checkpoint、Fig7 MATLAB代码、具体PCA fit/averaging、实际fig7 hp；等待主Agent提供LDS audited schema进入round2。
