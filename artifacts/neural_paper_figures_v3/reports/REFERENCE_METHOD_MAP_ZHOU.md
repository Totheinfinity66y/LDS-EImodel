# Zhou 2023 Figure 7：文献方法契约与 LDS 适配

专家：`zhou_v3`。核验日期：2026-10-28。独占证据目录：`reports/literature_zhou/`。

## 来源与已执行核验

论文：Zhou et al., *Multiplexing working memory and time in the trajectories of neural networks*, Nature Human Behaviour (2023), DOI [10.1038/s41562-023-01592-y](https://doi.org/10.1038/s41562-023-01592-y)。作者代码：[BuonoLab/Timing-WM_RNN_2022](https://github.com/BuonoLab/Timing-WM_RNN_2022)。本轮实时打开作者仓库，核对 README 与八文件公开树；本地作者副本 `artifacts/paper2agent_reproduction/references/zhou/author-source/Timing-WM_RNN_2022-main/` 的 `standard_analysis.py` 已实际读取。

本轮已读取真实 Paper2Agent 与 Paper2Skill SKILL.md，实际打开 `audit/paper2agent/zhou/figure7-source-page10.png` 与 `methods-source-page13.png`，同时读取 p9–10 Results/Figure 7 与 p13 Methods 的提取正文、INPUT_CONTRACT、FIGURE_CONTRACT。视觉核验对象是原论文页面，不是 LDS 输出图。既有文献转换 verification.json 当前为 reviewed / mechanical_ok=true / all_sources_agent_reviewed=true；本轮复用该包，不声称重新逐页审阅十八页或重新运行作者模型。Paper2Skill 负责文献转换，下面的科学方法审查由 Codex 专家完成。

## Reference Data Contract

| 字段 | 原文/作者代码要求 | LDS 判定与约束 |
|---|---|---|
| 神经状态 | `h[time, trial, recurrent unit]`；256 个 leaky-ReLU recurrent rate units，输入/输出另列 | METHOD ADAPTED：132 维完整 E/I rate，不删静息单元，单位 dimensionless rate |
| 条件 | Fig7a 为 T+WM 的 long B cue 示例；trial 平均细节未说明 | METHOD ADAPTED：24 个 L/D/S 条件；不能将条件当重复 |
| 独立重复 | Fig7c 为 17 个独立训练网络 | INCOMPATIBLE：一个固定网络，seed/direction/条件均不是受训网络，不作原统计检验或虚构 SEM |
| 干预 | 输入拓扑 π 中心第17输入，随机输入权重；幅值0.25，cue onset后500 ms，50 ms | METHOD ADAPTED：LDS seed 固定的全神经元电流方向；50 ms 保留，但无第17输入拓扑的等价性 |
| 配对 | control 与 perturbed 用相同 unit×time noise matrices（frozen noise） | PASS（适配前提）：同一历史、初态、外驱、时钟，差异只有指定电流；确定性模型声明无噪声 |
| 前处理 | Fig7 PCA 拟合集合、中心化、标准化、平滑及平均细节未明确 | UNKNOWN（源）；METHOD ADAPTED（LDS）：明确 control-only centered PCA，固定 mean/components 投影两组 |
| 交叉时间距离 | `D[t,s]=sqrt(sum_i((h_ctrl[t,i]-h_pert[s,i])²))`，全部 recurrent units | EXACT METHOD（数学定义）；132-D Euclidean distance（具体系统适配） |
| 同时刻误差 | 主对角 `D[t,t]`；考察恢复与时间对齐，原文不声称精确归零 | EXACT METHOD（定义），保留非零平台；不能只画 PC 距离 |
| 投影内/外分解 | 原 Fig7 未明确报告该分解 | LDS 追加诊断：正交 PCA 基下 full²=PC1/2²+orthogonal²；不得标原方法复现 |
| 动力学解释 | T+WM 受训网络中局部稳定瞬态通道，dynamic attractor/hypertube | INCOMPATIBLE：LDS 有外部 clock、固定 handcrafted 分支；固定场点稳定不证明自主动态吸引子 |

`EXACT METHOD` 仅指已有明确公式的数学操作一致，不表示原 Figure 7 数据、参数、网络或结果复现。源文 Figure 7 的 PCA unknown 不可被“control-only”悄悄替代成原作者做法。

## 原图逐 panel 语义

- Fig7a 左：10 个示例 recurrent unit 的黑色 control / 红色 perturbed 曲线；右：同两条轨迹的 PC1/2/3 与配对时间标记。原图不是六位置点吸引盆图。
- Fig7b：control time × perturbed time 的全状态 cross-Euclidean distance；主对角趋近低值表明近似时间对齐。最小值离开对角表示时移，不能仅凭投影重合判断恢复。
- Fig7c 左：17 训练网络的同时刻距离 mean ± SEM；右：1.5 s 的网络级比较，median/IQR/1.5IQR whiskers 与双侧 ranksum。LDS 不复制该统计单位。

本轮实际看过上述原图，图注与视觉核验均 PASS。未把 Fig7 说成存在 velocity-field panel；它只有 a/b/c。

## 作者代码与原始复现的限制

README 明确 TensorFlow 训练并将测试数据导出 .mat 后作 MATLAB 分析。公开八文件中没有 MATLAB Figure 7 实现、已训练 checkpoint 或 Figure 7 raw state arrays。`standard_analysis.write2mat()` 导出 recurrent `h` 等数组，并不包含公开的 Figure 7 frozen-noise配对、PCA 或绘图函数。因此原作者 Figure 7 执行仍 BLOCKED；没有为本任务训练，也没有把第三方重实现冒称作者代码执行。

## LDS 当前 adapter 审查依据

已读 `handcrafted_ei/evaluation/reference_reproduction.py`：source_time 使用正式重建输入/clock，并断言 control 与归档 trial0 一致；R3_fixed_clock 使用 R3 快照与冻结快照 clock，不能称为全部 clock=0；两者 50 ms 电流探针以 seed7/11/19 固定方向。其 PCA 单独对每个 assay/seed 的 control 拟合；如果跨 assay/encoding 直接比较坐标，必须另设共同 basis。`basis[:,:2]` 的误差能量和 full-state cross-temporal distance 分开保存。

既有 `identify()` 仅包装 `state_identity(..., stage=3)`，不能据此证明唯一位置或排除共同激活；v3 分类需要竞争单元、完整残差、场身份及原分支/多分支的显式检查。source-time 最终阶段为 R4，不可使用 R3 保持恢复判据。State kick 与 finite input pulse 必须分组报告。

## v3 图的验收约束

Figure 9 必须标明全 132-D distance 与 control-only PCA 的区别，分别画 state kick / finite input pulse；固定 clock 的非零平台保持真实；phase/stage 试次注明样本是条件×seeded direction，非动物或独立受训网络。原任务 readout 正确、原位置保留、完整状态恢复是不同指标。实际 v3 adapter 与输出图的第三/四轮审阅待文件产生后追加至本专家独占目录。
