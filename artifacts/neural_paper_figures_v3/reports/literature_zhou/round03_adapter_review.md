# round03 — v3 adapter 方法反向审查

专家 ID：`zhou_v3`。日期：2026-10-28。状态：PASS_WITH_REQUIRED_FIXES；尚未验收最终图片。

## 请求与实际审查范围

主 Agent 请求核查 `handcrafted_ei/evaluation/paper_v3_dynamics.py`、`paper_figure_v3_geometry.py`，配合 `reference_dynamics.paired_input_probe` 以及历史 Fig9 arrays 的生成实现。已实际读取这些文件与 `population_dynamics.py` 的 field/state_identity/recovery。没有重新运行模型，数值回归结果应由主 Agent 独立报告。

## 已符合的方法约束

- 新阶段扰动在独立 control/perturbed 数组执行，复用 paired_input_probe 真实 Euler 积分；同一前史、完整时变刺激、clock 与 tonic。逐试次断言 control 与归档差异不超过1e-12，并检查onset之前逐位一致。
- 扰动50 ms、幅值0.25、seed7/11/19方向；actual current RMS 与两种积分剂量写盘。随机全神经元电流是 LDS 适配，不冒充原文输入拓扑。
- `stage_perturbations()` 的四个 readout 依 rank=1..4分别分类；最终 `patterns[-1]` 明确为 R4，不再误用 R3。固定R3保持与source-time完整任务在科学含义上分开。
- `classify()` 检查所有 stage Response units 的阈上活动数量，不仅最大神经元；actual传入control的expected_branch，错误分支会被outside_branch捕捉；多位置可被识别。
- 既有 cross_temporal_distance 使用完整state的Euclidean距离；projection_energy核查正交基并记录全/内/外平方和。历史 input arrays 的basis由每个assay的control独自拟合。复用它们无需对perturbed重新拟合PCA。
- branch几何的时间点全部处于统一neuron坐标；rank阈值明示；无效角度保留NaN。branch-discriminant axes固定拟合后用于所有时刻，未称dPCA。

## 必须修复或明确标注

1. **source-time场残差不适用**：`classify(require_converged=False)` 仍在缺省model（clock/stimulus默认状态）中计算field并返回converged。这个数值不是相应scheduled readout的实际向量场残差。当前恢复判据没有使用它，故不直接改变已报readout；但日志不能称其为任务末稳定性证据。建议该协议 residual/converged返回明确NA和not_applicable，或传入该时刻完整外驱后说明“瞬时场残差”仍不等同固定场稳定性。
2. **通用分类的同位置多分支角落情况**：expected_branch=None、多个分支同一位置阈上时，code=single_position但branch=-1。调用者可能误以为唯一位置状态。建议多分支显式列outside_branch/multiple_branches，至少唯一类别要求active_branch_count==1。当前stage actual传expected_branch后可抓到跨分支，但一般classifier与control参考仍应防守。
3. **新增混合终态不能仅凭小残差称吸引子**：basin slice当前新混合endpoint只计算完整残差；既有稳定性证书只对参考24 endpoints执行。若报告“额外稳定混合吸引子”，需对不同混合pattern代表点调用exact_local_stability与kink证书；否则只能写“低残差共同激活终态，稳定性未判定”。

## 非阻塞改进

- `paper_figure_v3_geometry.project_energy()` 没有独立验证basis正交性；优先复用已验证的reference_dynamics.projection_energy，减少重复公式。
- 四阶段统计的恢复率、readout正确率与唯一位置保留率必须独立；现有CSV已分别提供，多分类堆叠图不得吞掉正确readout但状态异常的交叉属性。
- source-time中“未收敛”不能自动等于固定场残差失败；它没有平衡态实验含义。图注写明是有限任务终点模式与相对control误差。
- 历史cross-temporal arrays为stride4真实采样，按其cross_temporal_times_ms画矩阵，不使用完整times_ms作为同维坐标，也不插值伪造中间状态。

## 接下来的验收

第四轮应实际打开最终Figure9，核对pulse与时间轴、三种距离的单位、control-only投影注释、跨时间矩阵方向，以及source-time R4 / frozen R3 / clock=0 state kick三种协议的标签。不能继承旧版本验收状态冒充v3审图通过。
