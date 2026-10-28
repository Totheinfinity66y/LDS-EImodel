# round04 — Figure 9 实际图像反向审阅

专家 ID：zhou_v3。日期：2026-10-28。最终结论：**PASS_WITH_LIMITS（修订后两种协议实际审图通过）**。本文件保留首次快照发现作为审计记录；下方最终裁决关闭其中待修项。

## 本轮实际打开的图像

`figures/main/fig09_one_hot_perturbation_dynamics_source_time.png`，本轮审阅快照 SHA256 `AFABD8FEC3749D0BC199A96CBEAC326B8973CDF14B0BCD3656C400DF42614150`。参照已实际看过的原论文Figure7 source p10与Methods p13。没有把“原文图注已读”替代实际审图，也没有审阅尚未产生的所有编码图。

## Adapter 修复复核

- `classify(require_converged=False)` 当前明确 `converged=None`、`residual=NaN`、scope=`not_applicable_source_time`；source-time不再报告默认固定场的伪残差，第三轮问题1已修。
- 多分支优先归outside_branch，即使各分支相同位置也不会single_position；第三轮问题2已修。
- `classify_archived()` 中source_time=stage4、R3_fixed_clock=stage3，fixed-clock使用归档最终clock和stimulus；stage分类R4、时序与场语义分开。
- 新盆扫未发现多位置终态，报告保留“未发现，不穷尽”，故没有宣称未经稳定性验证的额外混合吸引子。

## 逐 panel 审阅

| Panel | 图像与数据核验 | 判定 |
|---|---|---|
| A | 三个受扰影响最大的神经元，post hoc选择有披露；control与pulse用实/虚线，dimensionless rate明确 | PASS_WITH_LIMITS：需要50ms pulse时段标记；数值神经元ID适合追踪但群体标签可更清晰 |
| B | 同一control-only PCA；方差/能量69.0%、18.6%；实际轨迹有大段重合而非刻意形状匹配 | PASS：是LDS适配选择，非原文已证明的PCA定义；补pulse onset/offset可增强时间解释 |
| C | x=perturbed time、y=control time；色标明确132-D Euclidean distance；存在持久活动方块，非原文瞬态hypertube形态 | PASS：cross-temporal使用存档实际stride4时间，未插值造轨迹 |
| D | full132、PC1/2、orthogonal complement分列；真实非零平台持续至约2s，随后任务进程下降 | PASS：平台没有隐藏；不能由此推断自主dynamic attractor；建议y轴明确132-D/投影距离区分 |
| E | 明确单独state-kick；但读fig08 branch0类别文件，recover只检同位置而不检完整状态恢复；other把静息/未收敛等合并 | REQUIRED FIX：用fig09_state_kick_classification.csv既有严格full_state_recovered及显式类别；标6位置×3方向和branch0；不可用recover暗示full-state恢复 |
| F | 四stage完整24条件×3方向；readout-correct/state-not-recovered独立显出；无虚构误差条 | PASS_WITH_LABEL_FIX：rest应写R4-inactive；此字段不表示tonic I等全部单元静默 |

## Panel E 修复建议（已有数据足够，无须新模拟）

复用 `derived/one_hot/fig09_state_kick_classification.csv`，筛 `target=full`，如保留branch0需明确筛选同一六个reference trials。类别至少区分full-state recovered、same position but not full-state recovered、position switch、multiple positions、outside branch、R3-inactive、unconverged。没有出现的类别允许0比例，但不应把它们混为other。当前whole full-target汇总实际为single_position245、rest43；不同branch子集的实际数字应按筛选重新计算，不从图估计。

Preclip幅度已正确标注为preclip；CSV保存实际postclip剂量。若主图仍用preclip轴，图注指出实际剂量随状态/方向变化，另提供数值表或补图，不能称为统一有效kick剂量。

## 与 Zhou 原 Figure7 的真实差异

原文显示trained T+WM网络的近似时间对齐恢复，n=17独立训练网络。LDS source-time图展示外部clock推进下的阶段保持和后续误差消退，不能据此推导自主稳定瞬态通道。固定R3 clock图的误差平台与normal-clock source-time是不同协议；平台必须保留。新增state-kick与stage堆叠是本项目独立诊断，非Zhou原实验图形复现。

## 审阅范围与状态

本轮已读当前renderer `handcrafted_ei/visualization/paper_v3.py` 的fig9实现与分类CSV头/类别，未执行额外Python。主Agent应在修改E后重新导出PNG/SVG/PDF并更新manifest；此快照审核不能自动覆盖后续改图。数值全量测试由独立验收记录支撑，不以本次视觉评审冒充测试通过。

## 修订后最终裁决（再次实际打开两张PNG）

最终审阅对象与SHA256：

- `figures/main/fig09_one_hot_perturbation_dynamics_source_time.png`：`68CF1C176F46A6D16E468810F1FDD3EB0A3D99A4D9062BA1422A47F56F0F0E6D`。
- `figures/supplementary/fig09_one_hot_perturbation_dynamics_R3_fixed_clock.png`：`C8D5769C522F34DBDC6BD5A8BD3B651B32515875823D76B35341D15F0EB405C4`。

已实际复开上述两图，并核查renderer修订。A/D新增50ms脉冲阴影，B新增onset/offset；E来自严格state-kick分类CSV，图例显示七类，完整恢复与同位置但状态不同已分开，x为实际postclip RMS，y明确六位置×三方向，标题明确R3 branch0；F已将rest显示为R4-inactive。首次审阅提出的所有必要修订均关闭。

source-time Panel D保留约500–2000ms的显著完整状态误差平台及之后时钟推进下的消退；fixed-clock Panel D保留约1.5的完整状态距离、约1.45的正交补误差，未伪造成恢复。固定场的非恢复与正常clock驱动任务的后续误差消退在两张图中清楚分开。E实际说明：较大kick可保留同一位置而不恢复完整state，另有R3-inactive；这是原图未提供的LDS诊断。

保留限制：fixed-clock control的PC2解释能量显示0.0%，此方向不具可解释的control方差，不能把其二维轨迹形状当作可靠二维流形；完整距离及正交误差已提供必要防护。图中均为单固定网络的条件/方向汇总，无训练网络SEM或显著性。最终PASS仅绑定上述one_hot两张PNG及所读adapter，不外推为全部编码、全部图或原作者实验复现成功。
