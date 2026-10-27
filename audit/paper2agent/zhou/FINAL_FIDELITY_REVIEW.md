# Zhou Figure7 → LDS Figure9 最终忠实度评审

结论：**PASS_WITH_LIMITS：METHOD ADAPTED与LDS-specific诊断可发布；EXACT AUTHOR FIGURE REPRODUCTION仍BLOCKED。** 无需为图形相似修改神经模型。原论文Fig7没有velocity-field panel，现已正确单列。

## 审阅材料和实际检查

原文18页均已实际逐页视觉检查，Paper2Skill最终`build --require-reviewed`、`verify --strict`真实exit0/status=reviewed。参考原图Figure7及Methods；最终包`artifacts/paper2agent_reproduction/reproduced_papers/zhou/verified-final/zhou2023-paper`。这是文献转换/阅读流程通过，不等于作者计算复现。

本轮实际打开12张最终PNG：one_hot/ring/topology各自input_source_time、input_R3_fixed_clock、state、flow。实际读adapter、reference_dynamics、reference_reproduction、reference_figures及FIGURE_CAPTIONS；独立重算18个input NPZ、3个state和3个flow。证据`ACTUAL_RESULTS_VERIFICATION.json`与`verify_actual_results.py`。

## 六维验收

|维度|结果|证据/边界|
|---|---|---|
|Data fidelity|PASS adaptation|真实132维全网状态，未丢静息/I群；全矩阵和条件/时序/电流/噪声归档。原作者256 recurrent population不同，不能叫same population。|
|Mathematical fidelity|PASS|独立Euclidean逐元素重算；最大典型差约8.9e-16，能量闭合约1.8e-15；control-only PCA mean/subspace独立SVD相符。|
|Experimental protocol|PASS_WITH_LIMITS|实际50ms输入、10步、共同初态和同零noise；原π通道缺失，whole-network signed random current是显式适配。source-time全程clock重放与R3固定clock两实验分开。|
|Statistical fidelity|PASS appropriate limits|三方向曲线不画SEM；24状态×3方向恢复为有限样本描述，不伪装17独立训练网络统计。原Fig7c箱须/网络SEM不可复现。|
|Visualization fidelity|PASS adaptation|图像panel、轴、色条、扰动时间窗、full/plane/outside分开，单位清楚；保留真实平台和不恢复。布局并非原Fig7精确3panel/3PC，标签明确METHOD ADAPTED。|
|Scientific interpretation|PASS_WITH_LIMITS|不能把source-time最后趋同当自主恢复，也不能凭二维箭头证明动态吸引子。固定R3驱动下大输入后未恢复，是科学差异而非绘图错误。|

## 实际数值

三种编码在此trial/共同内部动力学和相同投射方向下给出一致对应结果，不能据此推断所有噪声/全部条件都相同。

- source-time seed7 full-distance peak=2.078012734，t550ms=.627489019、t1500ms=2.061329782、t1800ms=2.061535458、t2200ms=.248173278、t3310ms=1.810637282e-5。此为随外驱时序推进的eventual reconvergence；中间长平台偏离，不是全程自主稳定动态通道证据。
- R3固定clock三seed最终距离分别1.499999962、1.499999952、1.118033989；该剂量下没有恢复原control全状态。seed7最终PC1/2解释扰动能量仅6.8698%，seed19约1.2e-18；二维轨迹近似不能替代full-state指标。
- state-kick示例初始距离2.069872888、最终1.499999973，最终PC1/2解释11.1111%；已正确标为不同于有限输入的独立实验。
- 实际电流RMS=.25，L2=2.872281323，持续50ms，RMS积分12.5 current·ms。不能等价原文单输入幅值.25后经未知权重的电流剂量。
- source-time control PC1/2占control variance约87.6158%；R3固定clock control约99.9999999854%。这是control方差比例，仍不代表扰动能量比例。

## A–G差异分类

|分类|当前判定|
|---|---|
|A 数据格式错误|未发现。显式轴适配和原始率身份已有测试。|
|B 预处理错误|未发现。PCA仅control fit，统一center/basis，无fake repeats/normalization。|
|C 算法/公式错误|本轮独立复算未发现。|
|D 原协议差异|保留：非π输入、signed whole-network current、无原作者过程noise、不同任务epoch/clock、无17训练网络。均须叫adaptation。|
|E 视觉差异|2D代替原3PC、六panel诊断代替原a/b/c，均显式适配；没有用配色掩盖数值差异。|
|F 真实动力学差异|R3固定clock大输入未回原状态、长平台/状态切换后趋同，与原动态通道结果不同；应如实报告，不要求改模型。|
|G 证据不足|原Fig7 raw/checkpoint/MATLAB、具体PCA拟合trial与平均方式缺失。不能宣布exact replication。|

## 三列对照补充验收

后续实际打开`artifacts/paper2agent_reproduction/figures/source_comparisons/zhou_SOURCE_VS_REPRODUCTION_VS_LDS.png`：左列是原论文整页图，标internal reference only；中列明确SYNTHETIC/missing author Figure7 pipeline，用合成轨迹验证full-state cdist；右列明确actual LDS paired input assay/not trained-network reproduction。视觉和fidelity结论为PASS_WITH_LIMITS：没有伪造源作者数据或将中列单位检查称exact reproduction；中/右横纵轴为sample index，而原图为time，不能据三列外观比较恢复时间常数或声称同一时间协议。中/右色条各自量纲/范围属于不同数据，不能跨列直接定量比较颜色。正式LDS assay图已保留物理时间与full132 distance。原图左列缩放较小，其最小标签核查以单独完整Figure7 JPEG和原PDF为准，此三列图是导航/范围说明而非代替原图精读。

独立Reviewer与本Agent不同，最后Gate5由主Agent另安排；本Agent不能兼任fresh package verifier。原作者代码实际仅运行task.generate_trials产生输入和target（x450×100×33/y450×100×2）；没有作者神经活动或Figure7计算。合成距离5类测试已过，明确不是原始数据。

所有可在本轮检查的数据/公式/图形问题无新增阻塞；保留公开资料缺口和真实科学差异即可，无需重复改色或更改模型。
