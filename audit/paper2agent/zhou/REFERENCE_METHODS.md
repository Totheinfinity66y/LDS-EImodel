# Zhou 2023：Figure 7 原方法契约

论文：*Multiplexing working memory and time in the trajectories of neural networks*，DOI 10.1038/s41562-023-01592-y。主证据为本地 `artifacts/neural_representation_v2/reference_evidence/Zhou2023.pdf`，实际文字核查 p9–10 Results/Figure7、p12–13 Methods；作者源码下载于 `artifacts/paper2agent_reproduction/references/zhou/author-source/Timing-WM_RNN_2022-main/`。

## 数据要求（尚不针对 LDS 设计转换）

1. 原作者 recurrent activity `h[time, trial, neuron]`，源码 `standard_analysis.py` 明确 time/condition/neuron。batch 实际包含条件和重复，不可将 trial 与 condition 自动等同。原网络 256 recurrent units；输入、输出是另外的数组。
2. `network.py:164–179` 状态是 leaky ReLU rate 输出：`h_next=(1-alpha)h+alpha ReLU(h E |W|+input+b+noise)`；不是 membrane potential。率为模型活动单位。
3. Fig7a 展示 long B cue 一个示例网络十个单元及 PC 轨迹；图注未明确这些轨迹是否已重复平均。Fig7c 的独立统计单位是 17 个训练网络，不是 17 时间点或 trial。原文其他分析的25重复不自动约束 Fig7。
4. 需要完整 cue 和 long-delay trajectory、准确 cue onset，以及500ms onset后50ms扰动区间；比较1.5s时的距离。训练标准delay为1s/2.2s。作者默认 dt=10ms、tau=50ms（train.py），须以真实归档hp为准。
5. 必须保存 control/perturbed 的输入、共同初态、权重、噪声矩阵及时间；随机种子相同不等于已证明同一噪声矩阵。
6. Methods p13：额外输入位于拓扑 π（中心第17 input），经类似正常输入的随机输入权重作用于 recurrent units，幅值0.25；cue onset后500ms，持续50ms。不能用一次 rate state kick替代。
7. 配对实验共享 across-unit/time noise realization（frozen noise）。作者网络默认每步 `tf.random_normal`，公开源码没有 Fig7 frozen-noise配对实现。
8. Fig7b 是全 recurrent 状态交叉欧氏距离 `D[t,s]=sqrt(sum_i((h_control[t,i]-h_perturbed[s,i])**2))`。Fig7c左为其主对角的17网络均值±SEM；右为1.5s网络级距离，median/IQR/1.5IQR whiskers、two-sided ranksum。不能替换成 RMS而仍用原单位。
9. Fig7a PC拟合集合、中心化、是否先平均、过滤与标准化，在核查的 Methods/图注中未明确说明。标记 unknown；不得宣称 control-only 或 pooled-fit是已核实原作者做法。对本地适配必须预声明且投影一致。
10. Fig7只有a/b/c，**没有 velocity-field panel**。切向/正交采样与PC网格场均不能标记成 Zhou Fig7 的原方法。

## 可执行性边界

公开仓库包含 MULTI.py、MULTI_Output.py、network.py、standard_analysis.py、task.py、tools.py、train.py、README.md。入口训练并导出 MATLAB 数据；README明确后续分析在MATLAB完成，但仓库无MATLAB Figure7分析、无已训练权重、无Fig7 raw data。禁止训练的本任务无法直接产生原作者 Figure7。可复现的欧氏距离是依据 Methods/Results 重建，必须标为 `reconstructed implementation`。

## Paper2Agent 实际使用

已读取真实 paper2agent/SKILL.md、paper2skill/SKILL.md 与其bundle-review/review-plan，实际运行 `prepare`、`extract`、`review-aid`、草稿构建、18/18页逐页视觉审阅与提取修复、`build --require-reviewed`、`verify --strict`。最终exit0、status=reviewed、mechanical_ok=true，未使用adjudication。最终包位于`artifacts/paper2agent_reproduction/reproduced_papers/zhou/verified-final/zhou2023-paper`。这是文献转换与审阅工作流，不自动执行科学方法或自动审图；fresh independent package verification由主Agent另安排。Paper2MCP已读取规范，因缺训练权重、Fig7实现及 TensorFlow依赖，作者Figure7运行和tested MCP阶段阻塞；不造CLI或成功marker。
