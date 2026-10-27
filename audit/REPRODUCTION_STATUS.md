# 文献方法复现与神经可视化重建

目标：A、核验 Paper2Agent 与两篇原论文方法；B、审计三编码数据并修复分析流程、重建 Figure 8/9；C、审查 Figure 1–7/10、完成反向评审与独立验收；D、更新文档、归档并提出提交提案。

## 执行契约

本地 `D:/Library/10-16-handcrafted` 为唯一当前模型来源。保护 model/task/simulation/config 及历史归档；仅修改分析、独立副本实验、绘图、测试与文档。不训练、不安装依赖、不使用 computer use、不推送。开工 Git 除一份既有 PPTX 外干净，该 PPTX 不纳入本任务。

## 所有权与依赖

| Owner | 独占写入 | 任务 |
| --- | --- | --- |
| root/inagaki | audit/paper2agent/inagaki；新归档 references/inagaki、reproduced_papers/inagaki | 原文/源码/数据契约，多轮适配及反向评审 |
| root/zhou | audit/paper2agent/zhou；新归档 references/zhou、reproduced_papers/zhou | 原文/源码/数据契约，多轮适配及反向评审 |
| root/data_auditor | audit/data；evaluation/reference_adapter.py；test_reference_adapter.py | 原始数据、schema、adapter及负例测试 |
| root | 其它新分析/绘图/测试/基础文档 | 集成、独立副本实验、数值验证、归档 |
| fresh reviewer | audit/reviewer | 实现结束后独立验收，不参与实现 |

仅4个并发槽，A/B/C先并行，数值审计与绘图由主 Agent 执行，最后释放槽位启动独立 Reviewer。每位论文专家保留同一 Agent 身份，沟通写入 communication。所有 gate 依据实际证据，不提前通过。

## 阶段与验收

| 阶段 | 依赖 | 输入 → 输出 | 验收 | 状态 |
| --- | --- | --- | --- | --- |
| T0 capability | 无 | 本地 Skill → 能力审计、真实命令 | PAPER2AGENT_CAPABILITIES；skill_identity hash | PASS_WITH_LIMITS |
| T1 Inagaki | T0 | PDF/作者代码 → 契约/来源复现 | 30页正式包strict reviewed_with_limitations；源码/数学测试 | 方法核验通过；作者MATLAB exact BLOCKED |
| T2 Zhou | T0 | PDF/作者代码 → 契约/来源复现 | 18页正式包strict reviewed；作者task真实执行 | 方法核验通过；原Fig7 exact BLOCKED |
| T3 data | 无 | 本地ZIP/NPZ → schema/缺陷/数据流 | audit/data；47,664全状态转移验证 | PASS |
| T4 contracts | T1–T3 | schema+契约 → PASS/ADAPT/RERUN/INCOMPATIBLE | 两专家round2；SOURCE_TO_LDS_SCHEMA | ADAPT；原统计INCOMPATIBLE |
| T5 adapter | T4 | adapter+测试 → 源方法审阅 | 两专家round3；5项adapter测试 | PASS_WITH_LIMITS |
| T6 numerical | T5 | 独立副本 → 24状态终点/残差/谱/扰动指标 | D独立脚本；70项完整回归；局部分段证书 | PASS（限局部及有限实验） |
| T7 rendering | T6 | 真实指标+spec → 三编码8/9+源对照 | 16组48文件QA；独立开图；统一CLI成功 | PASS_WITH_LIMITS |
| T8 fidelity | T7 | 图/代码/数据 → 两专家六维审阅 | Inagaki round4/4.1/4.2，Zhou round4+report review | LDS适配PASS_WITH_LIMITS |
| T9 consistency | T6 | 1–7/10旧图与共享分析 → 一致性结果 | reference_consistency独立SVD/角度；新Figure10 | PASS_WITH_LIMITS |
| T10 independent | T8/T9 | 全材料 → 独立报告 | fresh F；114结果/68源码/8受保护源码/165旧图hash；追加复算及实际开图 | PASS_WITH_LIMITS（LDS适配）；source exact BLOCKED |
| T11 archive | T10 | 报告/哈希/环境/文档 → 提交提案 | 全部证据已落盘；提交仅Nimbalyst提案 | commit状态以交互提案及Git实际结果为准；不推送 |

## 已确认事实

- analysis Python 3.12.12，NumPy 2.3.5，SciPy 1.16.3，Matplotlib 3.10.7，PyYAML 6.0.3，CPU数值分析。直接exe需将同环境 Library/bin 加入当前进程 PATH；未修改全局环境。
- 旧动力学快照只覆盖固定 D=+1,S=1，不能用于全24分支盆结论。
- 旧Figure9为endpoint状态扰动；原文输入扰动必须独立重跑，不能改名冒充复现。
- 本地Paper2Skill负责文献包构建、不执行论文算法；Paper2MCP只封装实际存在的作者代码。独立专家适配与反向审查属于Codex工作，不伪称Skill原生功能。

## Figure跟踪

| Figure | Source Agent | Method | Data gate | Plot | Fidelity review | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | root/inagaki | 原文/代码范围核验、Methods重建 | ADAPT全24状态 | 三编码实际完成 | 同Agent四轮及修后复审 | PASS_WITH_LIMITS；source exact BLOCKED |
| 9 | root/zhou | Fig7真实协议核验 | RERUN50ms输入已完成 | 三编码各两输入assay+state/flow补图 | 同Agent四轮及对照/报告审阅 | PASS_WITH_LIMITS；source exact BLOCKED |
| 1–7/10 | root+fresh F | 正确共享分析复用 | PASS_WITH_LIMITS | 1–7历史图保留，新10已完成 | 独立SVD/角度/RSA及代表图审阅 | 方法一致性通过；不冒充全部论文实验复现 |

## 最终解释与外部限制

每编码24个task-seeded局部稳定平衡点在共同tonic场下保留身份，不是全局吸引域或全系统仅24点。R3固定clock代表输入扰动不恢复；正常时序最终重合属于schedule-assisted reconvergence。源文献原实验raw/训练权重、部分分析代码及MATLAB运行时缺失，精确源结果复现保持BLOCKED，不通过训练/安装/改模型绕过。

Zhou最后一次图hash刷新followup遇到子Agent usage limit；此前四轮、12图实看、18input/3state/3flow数值审阅与root报告审阅均已完成并落盘。最后统一重跑的PNG/数组身份由fresh reviewer核对，PDF元数据变化不冒称同Agent重新审阅。

F最终追加验收明确：部分state/flow图发生PC符号翻转，部分NPZ字节改变；独立重放全部当前input/state/flow指标与B原审数值差最高3.240477e−12，full距离不变。六张受影响PNG已由F重新实际打开，四项修复全部关闭。最终G5 PASS_WITH_LIMITS，详见INDEPENDENT_REVIEW与audit/reviewer。
