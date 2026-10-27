# LDS适配第二轮独立审查

PASS_WITH_LIMITS for LDS-specific dynamics; INCOMPATIBLE exact experimental Fig5/6 reproduction

## rates axes · ADAPT
显式transpose(1,0,2)到time,condition,neuron；保留条件身份，不可把condition改名trial重复。

## measurement · ADAPT
LDS无量纲率与ALM spikes/s不同；端点归一化后也不能声称原始测量等价。

## repeated trials/session · INCOMPATIBLE
24个不同条件每个一次，无session，不可层级bootstrap、trial SEM、行为错误率复制原图。

## population · ADAPT
whole132为LDS主诊断；Response-only可独立补充，不可和原文ALM前运动细胞筛选混用。

## fixed field · PASS
共同tonic+clock0+stimulus0使24初态属同一自治向量场；记录tonic向量与模型配置哈希。

## R3 snapshots · PASS
同一真实事件取24条件能检验initial condition dependence；原图5/6没有四阶段语义等价。

## extension and random initials · RERUN
需要实际新独立副本积分；初态采样域/种子/稳定阈值/2000ms不足收敛的例外必须记录。

## fullstate metrics · ADAPT
严谨LDS-specific diagnosis；不能挂Exact source-method reproduction标签。

## pairwise CD · ADAPT
必须事先指定两个科学条件、固定同一field；确定性每条件单次不具备heldout trial CD验证。六位置/四分支无唯一二选择，不建议CD作为主结论。

## phase line · ADAPT
5ms原采样可取每隔一点的真实10ms采样，无插值；中心差分/2为per10ms，除0.01才/s。仅二维压缩观测，不能替全状态稳定。

## clock reconstruction · ADAPT
事件t>eventtime必须核对积分左/右端约定；记录reconstructed，不冒充原始电流日志。共同clock0实验最好直接保存实际输入。

## PCA · PASS
原CD方法不需PCA；PCA仅视觉辅助，不能替代fullstate endpoint距离。

## endpoint count · ADAPT
距离阈值须明示；不同位置/分支身份需从状态解码并以无活动→undefined规则避免静息argmax伪身份。

## basins · ADAPT
只称给定采样域和样本的经验basin fraction；24结构初态不是全吸引域估计。

## 可比较面板
CD轨迹、端点分布、phase-line可作为明确标注的数学适配；单次条件不产生原文统计。主Figure8应以统一field24×24末端矩阵、全状态残差、连续/离散谱和身份保持为主。没有天然二选择的LDS不应硬选CD制造原文外观。

未见实际adapter与结果，本轮是设计审查，不能替代第三/第四轮。

## 第三轮：实际Adapter与数值代码

PASS_WITH_LIMITS adapter; analysis acceptance contingent on result-layer thresholds

- axes,conditions,repetitions：PASS。explicit transpose(1,0,2), unique24, repetitions1; no averaging
- R3 provenance：PASS。per trial exact event match; tests actual rates[:,568] at2840ms
- reconstructed currents：PASS。t>event convention; t0 placeholder; measuredFalse; all662 Euler transitions x24 x3 checked atol3e-15 in supplied log
- projection decomposition：PASS。orthonormality check, deltaBBT residual, full-plane-off closure
- endpoint clustering：ADAPT。maxnorm greedy complete-link descriptive order-sensitive; cannot call attractor count without field residual and convergence
- local stability：ADAPT。analytic vs FD and Euler consistent; strict boolean excludes kinks but does NOT itself include equilibrium residual or FD tolerance
- phase drift：ADAPT。np.gradient coordinate/ms; explicit scale differs source per10ms; label correct units
- experimental Fig5/6：INCOMPATIBLE。deterministic24 conditions one trajectory, no session/trial repetition

稳定端点计数必须再联立残差与FD误差容差；目前未见结果，不提前通过。
