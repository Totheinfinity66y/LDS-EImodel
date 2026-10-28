# Figure 8–10 独立数值与方法验收

验收状态：**PASS_WITH_LIMITS**。验收者负责 Figure 4–7 的实现，未参与 Figure 8–10 的计算或绘图实现。本验收只读取冻结的科学数组与固定模型参数，未修改模型、未训练、未重新生成正常任务轨迹。

可执行验收源：[independent_validate.py](../../artifacts/neural_paper_figures_v1/manifests/independent_validate.py)。机器收据：[independent_validation.json](../../artifacts/neural_paper_figures_v1/manifests/independent_validation.json)。命令为 `python artifacts/neural_paper_figures_v1/manifests/independent_validate.py`；已在 analysis Python 3.12 / NumPy 2.3.5 环境运行至 exit 0。Windows 运行需要该环境及其 Library/bin、Scripts 在 PATH 中。

## Figure 8：完整状态切片与局部稳定性

三编码、四个 R3 规则分支全部通过以下独立复算：

- 从保存的中心、方向、网格重建每个初态；逐点检查 `[0,1]^132` 合法性、mask 和合法点索引。每个三端点切片有 551/1681 个合法初态，其余明确标记非法，没有 clip 后再冒充原网格。
- 在多个时间步用固定网络的完整 Euler 方程复核已保存轨迹，核对终态全 132 维向量场残差、对全部 24 个参考端点的 max-norm 距离，以及按残差 `<1e-7` rate/ms、端点距离 `<0.02` 生成的分类。
- 每个分支切片只匹配到该平面所选前三个 L 条件的参考端点及其他平衡态；没有将二维最近投影误当作完整状态盆归属。
- 原六端点均值平面的四份控制切片均保留，并独立验证初态与终态分类。该平面出现的其他平衡态不应被删去或改称六位置恢复。
- 每编码全部 24 个端点重新计算全状态残差、局部 Jacobian 最大特征值实部与 Euler 谱半径。clip 折点使用包含两侧可能变化行的依赖图检查；其 union 均无环，按拓扑顺序重建精确平衡点后残差 `<1e-12`，平衡点位移小于其合法局部 regime 邻域余量。24/24 份分段级联证书成立。

这些证据支持任务初始化得到的不同平衡点的局部稳定性与指定有限切片的终态分类。三端点中心的二维 Response 对比平面不包含全部六端点，不是完整吸引盆，更不能证明全系统恰好只有 24 个吸引子。

## Figure 9：配对输入扰动与完整距离

每编码 `24 条件 × 3 时段 × 3 方向 = 216` 条新扰动轨迹均独立核验，共 648 条：

- 对照轨迹逐元素等于 REC，control/perturbed 的显式 process-noise 数组均为零。
- 各方向的全 132 维 RMS 为 1；50 ms 脉冲采用 `onset < t ≤ onset+50` 的积分入样本约定，实际附加电流 RMS 为 0.25。不同阶段及编码复用同一方向定义。
- 使用保存的刺激、clock、tonic 和附加电流在多个时间步重新核对 Euler 方程；独立复算 CSV 的终态 L2、max-norm、R4 分支与位置身份，以及正式 Y 末 20 ms 窗口均值和 decision threshold 下的四次读出与序列准确性。
- `recovered` 在阶段 CSV 中是完整状态 max-norm `<0.02` 的独立指标；R4 分支/位置保持另列，不能把单独的该字段说成同时满足身份约束。

此外，三编码 × 两种旧 assay（source-time / fixed-R3-clock）× 三方向的 18 份原始输入扰动归档全部独立重算 control-time × perturbed-time 的全 132 维欧氏距离矩阵、同时间完整状态平方距离、前两 PC 投影能量及共享噪声。归档保存三列 PC 基，但 `projected_squared` 定义使用前两列；验收按实际源码定义核对，不将其误作三 PC 能量。

瞬时 state kick 与持续 50 ms 的输入电流是不同实验；图中分别展示，不合并统计。投影重合不代替全状态恢复或身份保持。

## Figure 10：共同 PCA 与匹配电流

独立核验了联合 PCA 训练集合的均值、132 维基的正交性、训练协方差特征值对应的解释方差、所有编码的三 PC 投影，以及 one-hot 固定基的敏感性投影。共同拟合集使用三编码等样本数、全 24 条件、全神经元、stride 4；不把独立拟合的同名 PC 当作相同坐标。

对 `3 编码 × 24 条件 × 3 剂量 × 3 方向 = 648` 条匹配电流实验，逐条复算实际电流 RMS、完整状态每时刻 L2 距离、最大与终态误差、R4 身份保持、身份约束下恢复，以及正式决策窗口下的 sequence_matches_control。三编码的附加电流数组逐元素相等。主图比较的是 R3 transfer 后的 full132 电流脉冲，并非原始 L 坐标噪声。

另外从九个原始 noise ZIP 的 task JSON 读取编码值，独立写出 one-hot / 周期角 / 二维向量的非负调谐映射公式，复核单独的 216 行原坐标噪声剂量表及 ZIP SHA256。原坐标 L2 与映射后的 R1 电流 RMS/L2 分列；原 sigma=0.03 下实际电流不匹配，不混入匹配电流的主图鲁棒性结论。

## Zhou Figure 7：来源方法与适配边界

已实际读取本地 Paper2Agent 入口说明、[INPUT_CONTRACT.json](../../audit/paper2agent/zhou/INPUT_CONTRACT.json)、[FIGURE_CONTRACT.json](../../audit/paper2agent/zhou/FIGURE_CONTRACT.json)、[REFERENCE_METHODS.md](../../audit/paper2agent/zhou/REFERENCE_METHODS.md)，并实际打开 [Zhou2023_p10.png](../../artifacts/neural_representation_v2/reference_evidence/Zhou2023_p10.png) 核查原 Figure 7a/b/c 及图注。论文为 *Multiplexing working memory and time in the trajectories of neural networks*，DOI `10.1038/s41562-023-01592-y`。

原图以黑/红活动与 PCA 轨迹对照、完整 recurrent-state 交叉欧氏距离、同时间恢复距离为主要证据；17 个独立训练网络的均值±SEM 与网络级距离统计不适用于当前单个固定 handcrafted 网络。当前 LDS 适配保留了有限时长输入扰动、配对控制和全状态欧氏距离；明确使用控制轨迹拟合 PCA，不声称这是原作者已核实的拟合选择；不伪造 17 个训练网络或生物学重复，不画对应 SEM。原输入拓扑、神经元数、任务时序与训练网络均未被冒充为 LDS 设置。

**Source-exact reproduction 为 BLOCKED**：公开材料缺少原 Figure 7 对应的训练权重、原始神经轨迹及 MATLAB 绘图分析入口；没有运行作者训练或把作者 task 输入生成称作完整 Figure 7 复现。Paper2Skill 生成文献包本身也不执行算法或审阅本轮实际图，本轮数值复算及实际图检查由 Codex 验收者完成。

## 实际图像检查

已实际打开 Figure 8 one-hot 最终主图、Figure 9 one-hot source-time 主图、Figure 10 综合主图以及 Zhou 原 Figure 7 图像；均无空白或关键轴裁切，量纲与完整状态/投影范围区分清楚。最终渲染冻结后还实际打开 Figure 8 one-hot 的 three-endpoint 与 sixmean-control 两张具名切片补图及 Figure 9 one-hot stage-perturbations 补图。三端点图中主要为 other equilibrium，只有边缘少量网格匹配三个任务端点；解释框位于非法区域，没有覆盖底端真实收敛网格。六均值控制的全部合法网格为其他平衡态，负结果清楚保留。其他编码补图由计算作者完成逐图检查；本报告不声称独立验收者已逐张打开全部 27 张动力学图。

Figure 4–7 的 12 张 PNG 另有 [数值验收](../../artifacts/neural_paper_figures_v1/manifests/fig04_07_numeric_validation.json) 与 [逐张视觉验收](../../artifacts/neural_paper_figures_v1/manifests/fig04_07_visual_validation.json)。该部分是实现者自检，不冒充 Figure 8–10 的独立验收。
