# 局部不动点相图：来源专家最终反向审查

审查者：`/root/inagaki`，2026-10-27。最终裁决：**PASS_WITH_LIMITS / METHOD ADAPTED**。本报告是 Codex 来源专家基于实际来源、代码、数据与图片的审查，不是 Paper2Agent 自动审图，也不是原作者程序执行证明。

## 来源及可比较对象

用户截图已与实际出版图片确认匹配：Janson、Marsden (2017)，*Dynamical system with plastic self-organized velocity field as an alternative conceptual model of a cognitive system*，Scientific Reports 7:17007，DOI `10.1038/s41598-017-16994-y`，Figure 1。来源图片为本目录 `source2017_figure1_m685.jpg`；来源契约及获取局限见 `METHOD_CONTRACT.md`、`SOURCE_EVIDENCE.json`。

对应的是稳定点、鞍点及稳定/不稳定流形的数学和视觉语义。原论文的二维示例系统与 LDS 神经率网络不同。未运行该论文作者代码，不能标为 exact source reproduction；没有复制原曲线或把源坐标范围用作 LDS 数据范围。

## 实际检查范围

已实读 `handcrafted_ei/evaluation/local_fixed_points.py`、`handcrafted_ei/visualization/local_fixed_points.py`、完整原网络状态与积分实现。已实际打开三编码各自的 `fixed_point_portrait.png` 和 `stability_diagnostics.png`，共六张；最后打开的主图已经具有红线朝向鞍点及粗蓝轨迹远离鞍点的箭头，Held R3 标签与图例不再重叠，单位、图例和页脚完整。

独立数值检查位于本目录 `independent_check.py`、`independent_check.json`，已成功执行。它不调用生产分析函数或绘图函数，直接使用原网络权重与参数计算完整率场，并以传递闭包核查局部 union 图无环，区别于生产代码的拓扑排序实现。检查三编码的所有 10201 网格点、三个完整 132 维根以及两条完整自由积分路径的全部相邻时间步。

## 六维审查

| 维度 | 裁决 | 实际证据与边界 |
| --- | --- | --- |
| Data fidelity | PASS_WITH_LIMITS | 活动选择坐标为 R3 单元 20 与对应 I_decay_S 单元 97；没有读取任务答案来选择高/低位置。高态初猜是独立评估副本由 rest 加选定 pair 高率再自由积分得到，不是直接读取的完整 archive endpoint。不得将该构造初猜称为原始记录。 |
| Mathematical fidelity | PASS | 完整率场核查二维闭合方程；10201 点最大误差 2.82e-18/ms，上游 nuisance 导数最大值 0，readout 反馈权重非零数 0。全部三个 132 维根残差不超过 2.78e-18/ms。独立 union 图核验无环，三个解分别为 132 负模态、1 正加 131 负模态、132 负模态，覆盖 clip 折点允许斜率。 |
| Experimental protocol | PASS_WITH_LIMITS | sample=clock=0，原 tonic 保留，固定权重参数；实验仅操作独立副本。闭合 pair 依赖静默上游背景，不能推广成任意外驱下的同一相图。蓝支从完整鞍点邻域特征方向出发，完整 132 维自由 Euler 积分；时间步一致性误差 5.55e-17。 |
| Statistical fidelity | PASS_WITH_LIMITS | 图中是确定性动力学与有限扰动方向，不能把 3 seed 当生物学重复、置信区间或全局吸引域证明。生产实现记录 requested/actual RMS 和 clipping；本轮额外 CSV 读取被自动审批额度阻塞，没有独立重读所有剂量行。 |
| Visualization fidelity | PASS | 蓝填充 sink、空心 saddle、红稳定流形及蓝不稳定双支的符号和时间方向与来源语义一致。坐标明确为无量纲实际神经率。补图注明 midpoint 谱与 kink 证书分开，不以代表谱单独证明折点稳定。 |
| Scientific interpretation | PASS_WITH_LIMITS | 支持给定外驱下所求完整平衡的局部稳定/鞍点分类。两个 sink 是同一响应单元的 rest/held 状态，不是两个位置记忆。红线只称闭合 pair 稳定流形，不能称整个 132 维稳定集合。 |

## 关键数值与可回答结论

三编码本次被选择的内部子系统相同，以下数值相同；这不是三种编码所有表征的等价证明。

* pair 根为 `(0,0)`、`(0.9000000000000001,0.7600000000000002)`、`(1,1)`；每个点同时具备完整 132 维平衡解与残差检查。
* 两个局部 sink 的最右模态上界为 `-0.008333333333333333 /ms`，Euler 谱半径上界为 `0.9583333333333334`。鞍点唯一正模态为 `+0.025 /ms`，对应 Euler 模为 `1.125`。折点数依次为 12、12、13；分类使用全部允许斜率的共同三角级联证据，不能声称系统在这些点经典光滑。
* 蓝支积分 1600 ms 后分别距完整低/高平衡 `2.933939690287272e-5`、`7.13803514196254e-6`（全状态 L2）。这些是有限时间轨迹终点距离，与根残差不同。独立检查最初采用 `1e-5` 的轨迹接近阈值而失败；实际低支距离如上，随后明确改用有限时长 `1e-4` 检查并保留真实数值，没有改模型或轨迹。
* 红线条件 `r=0.9` 的原完整场 r 导数最大值 `2.78e-18/ms`，z 导数与 `(0.76-z)/120` 的误差 `2.17e-18/ms`。红线是闭合子系统的解析对象，没有把 runtime clamp 冒称完整自由轨迹；其余下游状态可变化，故这不证明固定其余坐标的 affine 平面不变。

因此可以直接回答：**该固定外驱下，已求得的 rest 与 selected-R3 held 完整状态是局部稳定平衡，二者之间存在所验证的完整鞍点。** 不能据本图宣称全网络仅有两个吸引子、所有 24 条件恰好对应 24 个吸引子、全局吸引域已被测量、两个不同位置之间完成切换，或存在动态轨迹吸引子。

## 修复与剩余限制

审查发现的可修复问题为 E 类视觉问题：主图 Held 标签遮挡及流形时间方向不清。已在最终六图的实际打开检查中确认修复。未发现需要修改科学模型的问题；LDS 与源二维示例曲率/范围差异属于 F 类真实系统差异。

本新增来源仅完成 targeted Figure/caption/method contract 审计，没有冒充新增整篇 Paper2Skill 转换。之前两篇核心论文的正式文献包与本新增来源审查属于不同范围。

最后一次补充读取 `perturbations.csv`、目录清单的终端请求被自动审批 review failure 拒绝：审批服务额度用尽，并非该操作被判为 unsafe。没有重试、代执行或绕过；本结论使用此前已经成功完成的代码读取、六图打开及独立复算。图像新哈希未在该拒绝后重新生成，本报告不声称完成拒绝后的额外检查。
