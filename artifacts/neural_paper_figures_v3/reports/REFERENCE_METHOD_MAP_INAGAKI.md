# 文献方法核验：Inagaki 及群体几何参考

专家唯一 ID：`inagaki_v3`。本文件是 v3 独立咨询记录；不改变主模型、历史归档或既有论文包。当前状态：来源、兼容性、新adapter及Figure8实际图像四轮咨询完成；修订后one_hot主图复审 **METHOD ADAPTED / PASS_WITH_LIMITS**，源实验精确执行未完成。

## 来源和实际执行边界

已实际读取本地 Paper2Agent 及 Paper2Skill 的 SKILL.md。Paper2Skill 是来源转换和阅读包工具，不执行论文算法，也没有自动科研审图 API。既有 Inagaki 阅读包的 `audit/paper2agent/inagaki/strict_final_stdout.json` 当前记录 `reviewed_with_limitations`、`mechanical_ok:true`、全部页面已审、33 项指纹裁定。本轮复用现存包，不将历史页审称为本轮重新逐页审阅。

本轮实际打开 Inagaki 原 Figure 5、Extended Data Figure 1 的本地原图；逐项重新阅读 INPUT_CONTRACT、FIGURE_CONTRACT、REFERENCE_METHODS、FINAL_FIDELITY_REVIEW 及原论文文本。在线 Nature 链接发生身份认证跳转，未将网页失败说成论文不可用。公开作者仓库 [ALM_attractors](https://github.com/fontolanl/ALM_attractors) 页面明确是作者动力系统模型 MATLAB 代码。作者实验数据和 MATLAB 未在本轮执行；历史精确复现 BLOCKED 不升级为 PASS。

## Inagaki：Reference Data Contract

来源：[Discrete attractor dynamics underlies persistent activity in the frontal cortex](https://doi.org/10.1038/s41586-019-0919-7)，Figure 5a–g，ED1、ED6；本地 30 页 PDF 及阅读包。

| 字段 | 原方法 | LDS 适配判定 |
|---|---|---|
| 状态与单位 | 多 session 同时记录胞外放电率；投影前 spikes/s，端点归一化后 AU | ADAPT：132 个 dimensionless rate；不能标 Hz |
| 条件与重复 | 左/右、实际正确/错误、光抑制强度；真实 trial/session | INCOMPATIBLE：24 个确定性任务条件不是动物、session 或独立网络 |
| 预处理 | 100 ms 平滑，10 ms 步长；实验 CD 末 600 ms 选择性均值差归一化 | ADAPT：LDS 可用明示的固定对比轴；共同 PCA 不是 CD |
| 拟合集 | 固定延迟 correct control trial 50% 训练/50% 测试并交换；随机延迟非 2 s 拟合、2 s 测试 | INCOMPATIBLE：无独立试次时不伪造交叉验证 |
| 作者模型 | 末 400 ms 定 CD；模型代码未照搬实验交叉验证 | ADAPT：不能混称 400/600 ms 或模型/实验统计 |
| 扰动 | delay 初 600 ms 光抑制及 400 ms ramp-down；模型有自身平滑协议 | ADAPT：50 ms 电流、state kick 是不同干预，分别报告 |
| phase line | CD 对时间中央差分，原代码每 10 ms bin；原 phase-line 不是完整状态向量场 | ADAPT：LDS 明确 rate/ms；残差、谱、初态切片为额外数学分析 |
| 稳定证据 | CD 端点分布、恢复/切换、端点邻域负 drift slope | ADAPT：LDS 须完整场残差、共同外驱、clip 折点和稳定性证明；PCA 近邻不作归属 |
| 统计 | session/trial hierarchical bootstrap；原模型 trial SD | INCOMPATIBLE：随机方向占比只描述指定方向与条件，不套实验 SEM |
| 未知 | 原实验 Figshare 文件原生 schema 未在本轮下载验证 | UNKNOWN：不宣称源数据精确数值复现 |

原图视觉语义：Figure 5b–d 左列是 CD–time，右列是中途和端点分布；5e 叠加 control/perturbation，5f 是漂移相线，5g 是 session 配对点。蓝/红表示双选择，不是六位置。ED1 并排比较连续、移动和多离散模型，既展示正确恢复也展示错误切换。v3 Figure 8 六位置投影和全状态谱是 METHOD ADAPTED，不能称原 Fig5 EXACT METHOD。

额外稳定状态不能删掉；六个任务端点的稳定性不等价于系统只有六个吸引子。clock=0 固定场与正常 readout-first 任务轨迹必须分开叙述；固定场中的静息或多位置稳定点应独立分类。

## Mante：固定坐标的轨迹参考

核验 [原论文](https://doi.org/10.1038/nature12742) Figure 2/5 与 [PMC 原作者文本](https://pmc.ncbi.nlm.nih.gov/articles/PMC4121670/)。另从 Stanford 课程存档获取正式 PDF，实际打开第 3 页 Figure 2 与第 5 页 Figure 5。Figure 2 用条件平均群体响应，12-PC 去噪后对 choice/motion/color/context 回归并正交化，形成任务相关固定轴；Figure 5 的模型轴根据连接定义，含输入关闭后的平衡点和局部方向。LDS 固定 L 的 branch-centroid SVD 是 **METHOD ADAPTED：branch-discriminant projection**，不是 dPCA、原文回归轴或 line attractor 复现。

已下载并检查 [第三方教学 notebook](https://github.com/dvoina13/mante_and_sussillo_2013)：`pca_plot_condition_trajectories` 合并各条件的时间×神经元矩阵后只拟合一次 PCA，再切回轨迹。该片段可作共同 PCA 的实现参考；没有执行其训练模型。作者身份为第三方；另一个逐 trial 示例仍有 `reshape(...)` 练习占位，不可直接当完整算法。

## Gallego：principal angles 和 VAF 的语义

来源：[原论文](https://doi.org/10.1038/s41467-018-06560-z)，Figure 1/3 及 Methods。本轮实际打开 Fig3 原图。每条线是一个任务对逐维主角度；虚线来自保留时间/目标协方差的 surrogate，并非任意 90°线。原研究用固定 12 维流形，Fig3c 为 across-task/within-task VAF 比例，汇总来自实际 session。LDS 不执行该 surrogate，不绘制假显著性。

现有 `subspace_geometry.principal_angles` 使用正交基内积的 SVD，**EXACT METHOD（线性代数公式）**；数据与采样为 **METHOD ADAPTED**。其 `cross_vaf(y,qa)` 是 y 自身中心化总方差被 qa 捕获的比例，不是 Fig3c 的 across/within VAF ratio，轴标签应清楚区分。六位置中心化 rank≤5，微小数值方向必须披露阈值；低方差或未活动状态角度无定义。support-folded 是 LDS 结构控制，不是原文共同神经坐标比较。

## Sussillo–Barak：全状态轨迹与平衡点同空间

已读取 [原论文 PDF](https://compneurojc.github.io/pdf/NECO_a_00409.pdf) Figure 3 图注和正文，并实际打开第 9 页的该原图。图中 3-bit 模型有 8 个记忆稳态，鞍点、真实输入驱动转移及沿不稳定方向积分的轨迹；其三维 PCA 不决定稳定性。LDS 六位置和混合终态是 **METHOD ADAPTED**；不得把纯二维流线说成真实全系统路径。

[FixedPointFinder](https://github.com/mattgolub/fixed-point-finder) 是 Golub/Sussillo 工具，仓库当前同时列有 Torch/TF 实现；[tripdancer 实现](https://github.com/tripdancer0916/pytorch-fixed-point-analysis) 是第三方。两者均未在本轮运行，不是本模型的积分器，不要求迁移 NumPy 网络。LDS 继续使用现有 field/integrator/Jacobian，在 clip 折点处单个经典 Jacobian 谱不能单独证明稳定。

## 本轮源文件与可追溯性

- Inagaki PDF SHA256：`ead9c08588d753cc4fad8023bdebd41fbcb95701cbe975df4ebc9a7ef6bcb326`，对应既有 source_manifest，本轮再校验见独占目录证据。
- 本轮第三方 notebook 与 Gallego Fig3 原图只保留本地参考证据；不作为 LDS 结果或模型数据。
- 四轮及修订后4.1轮的请求、响应、实际代码/图片SHA256位于 `reports/literature_inagaki/consultations.json`。第4轮完整报告见同目录 `round04_figure_review.md`；未用待生成图片提前授予PASS。

## 第三轮：v3 adapter 独立阅读

已实际读取 `paper_v3_dynamics.py`、`paper_figure_v3_geometry.py` 以及既有 `reference_adapter.py`、`reference_dynamics.py`。共同坐标、原样固定点输入和三切片全状态积分、非法初态 mask、脉冲前历史逐位一致和 control 重放误差检查均与本轮科学任务匹配。当前判定 **METHOD ADAPTED / PASS_WITH_LIMITS**；不是源实验的 EXACT execution。

必须保留的解释条件：

1. `rest` 是指定阶段 Response 单元均低于 0.2，不等价全网络 132 维静息。图注用 R3-inactive 更准确。
2. 低全状态残差说明接近平衡，不直接证明新混合终态局部稳定。当前 24 参考端点的 certificate 不自动覆盖所有新增多位置状态；若称其稳定，须对代表新终态独立计算证书/稳定分析。
3. 互斥类别按 unconverged→inactive→outside-branch→multiple→single 的优先次序。跨分支多位置终态归 outside，不等价没有多位置共激活；原始 active counts 和 4×6 activity 应保留。
4. time-resolved Response-only 坐标含 R1–R4，R3 激活前仍可能存在 R1 位置方差。此时角度反映相同初始位置支持，不证明 R3 已建立；R3-only 激活检查可额外明确无定义时段。
5. 现有 control 比较的 source-time 恢复是终态完整状态 maxnorm<0.02 加身份匹配，不是固定点收敛。50 ms 扰动的实际 RMS、剂量和 seeded directions 已归档，三种子不是独立网络。

上述问题已向主 Agent 返回。第4.1轮实际复审确认B失活终点标记、F完整状态恢复与身份保留区分落实；三编码每编码2772合法初态中216单位置、2556 R3-inactive，本次切片未发现多位置终态。最终稳定性边界与负结果见第四轮报告。
