# 证据账本 — P2 Vogels & Abbott 2009

论文：Vogels, T. P. & Abbott, L. F. (2009). *Gating multiple signals through detailed balance of excitation and inhibition in spiking networks.* Nature Neuroscience 12(4): 483–491. DOI: 10.1038/nn.2276.
源文件：`P2.pdf`（作者机构版，共 9 个物理页），文本抽取自 `text.txt`。

## 1. 实际读过的范围

| 范围 | 状态 | 备注 |
| --- | --- | --- |
| 摘要与引言（p.1 上半） | 已读 | 含"缺口陈述"与 detailed balance 的定义段 |
| RESULTS：网络搭建与平衡态（p.1–2） | 已读 | 含 Fig. 1 网络连通性与背景活动分布 |
| RESULTS：信号门控（p.2–3） | 已读 | 含 Fig. 2 的有信号／平衡／失衡三栏对比 |
| RESULTS：响应性质（p.3–4） | 已读 | 含 Fig. 3a–g：速率、振荡幅度比、白噪声相似度、阶跃瞬态 |
| RESULTS：增益性质与鲁棒性（p.4） | 已读 | 含 Fig. 4a–d：增益曲线、突触强度变异、抑制细胞数削减 |
| RESULTS：病理式失效（p.4） | 已读 | 含 Fig. 5b–d：调参正确／抑制减弱／高兴奋 |
| RESULTS：多信号门控（p.5–6） | 已读 | 含 Fig. 6a–g：双信号网络门控 |
| RESULTS：单细胞容量（p.5–7） | 已读 | 含 Fig. 7a–f 与 Table 1 |
| DISCUSSION（p.7 上半） | 已读 | 含与既有门控模型的关系、病理类比、可检验预测 |
| METHODS（p.7 下半–p.8） | 已读 | 神经元模型、网络架构、信号通路、调参、单细胞模型、相似度定义 |
| 参考文献（p.8 末–p.9） | 已读（扫读） | 未逐条核对被引文献 |
| 图表的**精确数值** | 未读 | Fig. 1–7 为位图；本卡所有数字均取自正文与图注文字，未从曲线读数 |

未读范围：无正文被跳读。本论文 PDF 不含补充材料。

## 2. 已接触作者结论的说明

**本次为"证据复核"，不是盲读。** 仓库内 `docs/gating_gain_modulation_paperlist_20261020.md` 第 4 节已给出本文的定位、机制概括与阅读任务（"输入诱发的兴奋通常被局部抑制抵消；改变 E/I 增益、打破这种详细平衡，可打开传输""区分全局平均 E/I 平衡与针对信号的 detailed balance"），并已标注其为最高优先级。本文摘要与讨论中的结论在动笔前已通过该清单进入上下文。因此下列条目按"核对既有判断是否被原文证据支持"处理，不能称为在不知道作者结论的情况下重看数据。

## 3. 支撑关键判断的直接证据

### 3.1 门控机制确实成立，但成立条件被作者自己限定

- **p.2**：把接收区局部抑制神经元的响应增益降到对照值的 15%，兴奋性接收神经元即出现锁定输入时间结构的稳健发放（"we reduced the response gain of the local inhibitory neurons in the receiver region to 15% of its control value"）。
- **p.3**：平衡态与失衡态的亚阈值膜电位平均仅差 4 mV，却足以产生明显不同的发放模式（"differ by only 4 mV, but this is sufficient to produce markedly different firing patterns"）。
- **p.3**：门控关闭时信号并未被完全抵消，快速变化的输入仍能短暂泄漏（"detailed balance does not completely cancel signals when input firing rates change rapidly"），泄漏幅度随阶跃上升时间增加而衰减。
- **p.2**：整体网络活动几乎不受门控开关影响（"Overall network activity is relatively unaffected by these changes"），因为被调制的中间神经元只占全网抑制的一小部分。这是"门控不靠压制全网"的直接证据。

### 3.2 关键数值（全部取自正文，未从图像估读）

| 量 | 值 | 出处 |
| --- | --- | --- |
| 网络规模 | 20,164 个 LIF 神经元，142×142 网格，15,123 兴奋 + 5,041 抑制 | p.7–8 |
| 背景平均发放率 | 8 Hz／神经元 | p.1 |
| ISI 变异系数 | 中心略大于 1 | p.1 |
| 平衡态净电流 | 近零（兴奋与抑制膜电流幅度近似相等） | p.1 |
| 门控开启所需增益下调 | 对称降至 15%；非对称只需 30% 增益位移 | p.2, p.4 |
| 门控开启时信号相似度 | ~90% | p.3 |
| 门控关闭时信号相似度 | ~25% | p.3 |
| 失效临界：抑制接收细胞数 | 少于 40 个则关门失败；少于 25 个即使增强权重也无法挽救 | p.4 |
| 挽救条件 | 允许抑制细胞发放至 600 Hz 时，20 个抑制细胞可门控多达 600 个兴奋细胞 | p.4, p.8 |
| 单突触／单通路时的切换上限 | 约 10 条（1 信号／1 通路），约 20 条（Fig. 7d 表述） | p.5 |
| 每突触承载 ~40 条信号时的上限 | 仍不超过 30 条 | p.6 |
| 同时只存在 5 条信号时 | 1–600 条候选信号范围内相似度不下降 | p.6 |

### 3.3 多信号门控的关键对照

- **p.5**：两个信号各自被打开时，接收区活动准确跟随被打开的信号，被关闭的信号不跟随（"Activity of the receiver subnetwork does not follow the signal that is in the off state"）；两条信号各自的相似度高值区在增益空间中彼此分离（"The regions where similarity is high for either signal are well separated from each other"），各自在被打开区域超过 85%。
- **p.5**：只打开一条信号时，另一条反而变弱，甚至因抑制过冲（inhibitory overshoot）使相似度变为负值——这是"关闭"并非单纯"不传"而带有反向影响的直接证据。

### 3.4 容量上限的真实来源（作者自己给出的界）

- **p.6**：作者明确把上限归因于发放率编码本身而非门控方案（"the limitation is, in fact, not a deficit of the detailed balance scheme but a fundamental problem with encoding multiple signals using firing rates"）：M 条信号相加后均值按 M 增长而涨落只按 √M 增长（"there is a strong tendency for the mean input to drown out the signals to which we want the post-synaptic neuron to respond"）。
- **p.6**：把同时存在的信号限制为 5 条后，容量不再受限。但作者明写 "The number 5 is arbitrary"（p.6），这一取值只要求信号不因 √M 缩放而不可检测。

## 4. 未能核实的部分与原因

1. **图中精确读数**：Fig. 1–7 在 PDF 中为位图，本卡未从曲线读任何数值。§3.2 的全部数字来自正文与图注文字。
2. **随机性与重复**：本文未报告随机种子、每组重复次数、误差条或置信区间（本文未报告）。相似度是模型内部的确定性相关量，其跨实现稳定性无法评估。
3. **代码**：正文 p.7 写明"simulations in C"，但论文与本文所用机构 PDF 均未提供代码仓库（本文未报告）。因此本文全部数值**不可独立复现**，本卡不把任何结果写成"已复现"。
4. **补充材料**：Nature Neuroscience 论文通常附 Supplementary Information，本机构 PDF 只有 9 页正文，未包含补充材料（本次按用户指示不追补）。若补充材料含更细的调参扫描，本卡"未报告"判断可能不完整。
5. **突触可塑性**：正文 p.3 提到若兴奋与抑制突触具有不同的短时程可塑性，瞬态泄漏会更明显，但本文未做任何可塑性模拟（本文未报告）。

## 5. 已检查但本任务未实施的补充材料、数据、代码

- **补充材料**：PMC 页面（PMC 编号未在本轮核对）与机构 PDF 均未随附补充 PDF；本轮不下载。
- **代码**：无公开仓库地址被本文给出；不实施。
- **外部实验数据**：本文为纯计算模拟，无实验数据可核对。

## 6. 与仓库既有判断的对照

`docs/gating_gain_modulation_paperlist_20261020.md` 第 4 节对 P2 的既有判断为："输入诱发的兴奋通常被局部抑制抵消；改变 E/I 增益、打破这种详细平衡，可打开传输""门控不一定要改变结构权重，也可以改变固定网络中信号的有效传输"。

本次复核结论：两条判断均被正文直接证据支持，且证据强度高于清单所述——因为"固定网络、只改增益即开关信号"这一点在本文中是以**手调好的精确平衡**为前提的（见 §3.1 与第 5 步的替代解释）。清单未提及的三点需要补上：门控关闭时存在快速瞬态泄漏；容量上限源于发放率编码而非门控；"详细平衡"是手工调参设定的属性而非自发涌现属性。
