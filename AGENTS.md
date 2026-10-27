# AGENTS

你是本项目的代码助理。本仓库当前主线是 **Handcrafted E/I Decompression v2**：一个 handcrafted、固定连接、不训练的 E/I rate network，把已给定的 `L`/`D`/`S` 展开为四位置序列。

完整工程规格见仓库根目录 [architecture.md](architecture.md)，执行清单见仓库根目录 [todo.md](todo.md)。**本文件是强制规则**；科学边界以 `architecture.md` 的"冻结决定"为准，开发、验证与发布工作流以本文件为准；候选实现不得改写冻结决定。

---

## 0. 工作流注意事项
开工第一轮用一行钉住原始需求：
目标：A、B、C。
此后每轮只对照这份清单干活，清单只在我追加需求时才变。
每轮回复最后一行是进度条，三种状态：
🟢 还差：B、C｜搁置：X —— 原始需求有未达项，任务继续。顺手发现的改进只记进搁置，一行以内，先放着。
🟡 原始需求已全部达成。以下可做成下一轮 Plan —— 每项都附了证据。超出项能构成有明确目标和验收标准的后续计划，落盘成 plan/handoff 文件给路径，等我决定是否启动。
🔴 原始需求已全部达成，以下仅供存档 —— 每项都附了证据。超出项零散、不构成可执行计划，压成三行以内存档清单，结束。
黄灯与红灯的判定：超出项能否串成一个有明确目标和验收标准的后续计划？
能 → 🟡，
不能 → 🔴。
转黄/转红之后都停手，等我下指令。
我追加需求：更新目标清单，进度条回到 🟢。

如果输出方案文件.md，请确保你的方案是独立完整的。我不欢迎'相对于上一版本' "之前的版本中有哪些怎么样""下一方案再如何"，所有的这些不属于当前方案的内容，要么只在对话中提及，要么不说！
## 
你的修改之前最好确认之前的改动都已经提交指向项目根目录的git
---

## 1. 建模禁区与允许项

这张表是本仓库最高优先级的规则。**任何新代码违反下表，后续 agent 必须停下并提出与任务书一致的替代方案；不得为了让 24/24 通过而隐藏 oracle 或绕过 E/I 动力学。**

| 操作 | 判定 | 原因 / 可审查规则 |
| --- | --- | --- |
| 将 `L`、`D`、`S` 直接编码为本版 trial 输入 | **允许且必须** | 本版明确从已压缩 primitives 开始研究。 |
| 用 `L` 输入刺激 `R1`，用 `D`/`S` 输入刺激对应 memory | **允许且必须** | 合法外部电流输入，不是答案泄漏。 |
| 从历史、反馈、block 上下文或两个样本窗口再次提取 `L`/`D`/`S` | **禁止** | 超出本版范围且与直接输入定义冲突。 |
| `M_L`、`LocationMemory` 或冗余 `L` 存储群 | **禁止** | `L` 的保持由 `R1` 位置活动承担。 |
| `D`/`S` 输入直接选择并覆写下游正确位置神经元 | **禁止** | 绕过分支神经计算。 |
| 在 trial 运行时由 Python 用 `L+D+DS` 更新 Response 状态 | **禁止** | 此公式只能出现在 evaluator 的 target 生成中。 |
| 网络初始化时用 `T_δ` 建固定投射 | **允许** | Handcrafted 先验拓扑。 |
| 直接兴奋门控 | **必须** | M_D/M_S→E_gate→Response，E_gate有连续率且可记录/干预；不得用标签乘法代替。 |
| 用突触权重符号违反 Dale 定律 | **禁止** | 符号由突触前 E/I 身份决定，I→I 同样是抑制。 |
| `D`/`S` 输入脉冲在整个 delay 期间持续 clamp | **禁止作为记忆验证** | 应观察记忆群体在交接前的内部保持与交接后的活动依赖衰减。 |
| `R2→R3` 再次查询 `D` memory | **禁止** | 应由活跃 `R2` 分支继承方向身份。 |
| `R3→R4` 再次查询 `D` 或 `S` memory | **禁止** | 应由固定分支连线继承 `(d,s)`。 |
| 在 Readout 1 之前开放 `R1→R2` 转移 | **禁止** | 破坏在线时序假设。 |
| 一次生成四个目标后统一输出 | **禁止** | 应为四次 readout-first 事件。 |
| 为每个 rank 单独设计答案解码头 | **禁止** | 全阶段共用一个 6 位置 readout。 |
| clock 控制每阶段的开启与统一 reset | **允许** | 只能提供时间，不得携带位置和规则标签。 |
| 选择性 E→E recurrence、competition | **允许** | 前提是符号和动态可检查；主路由不使用I→I去抑制。 |
| 强制 low-rank、正交分支、指定神经活动 PCA rank | **禁止** | 把后验性质作为先验编码。 |
| 强制离散吸引子或训练神经网络 | **本版不要求/不做** | 吸引子有无是后验结果，训练不在范围内。 |
| 对 model 做 lesion、记录全神经群体、PCA/VAF | **允许且后续应做** | 事后观察和因果分析。 |

### 1.1 本版明确移出范围的功能

以下不是"延后实现"，而是本版范围外。**不得**出现在当前目录设计、里程碑清单、模型接口或结论中，**也不得以"先保留占位模块"为由生成**：

- `T1`/`T2` 位置差比较、方向比较器、`direction_comparator.py`；
- 根据位置关系反推 `L`/`D`/`S` 的编码器或算法；
- 历史反馈、奖惩、block context、跨 trial 的 `S` 学习、block switch 恢复；
- `block_context.py`、`feedback.py`、`block_runner.py`、`apply_scalar_feedback()` 等旧接口；
- 以"只有位置观察可用"或"禁止 D/S 输入"为本版规范的任何表述；
- 为旧任务构建额外感官样本、反馈或奖励通道；
- 独立 `L` memory，或把 `L` 与 `D`/`S` 并列持续保持的联合 `M_DS`。

将来要做 primitive extraction 或 block learning 时，通过版本化扩展单独定义新任务。

### 1.2 冻结决定（引用 `architecture.md` 第 1 章）

`L`/`D`/`S` 是合法直接输入；专门记忆只有 `M_D`、`M_S`；`D`/`S` 不得绕开神经回路给答案；显式 M→E_gate→Response 直接激活、真实 tonic I 背景抑制、R2/R3驱动的抑制反馈终止记忆；先 D 后 S 再分支继承；四次"先 readout 后 transition"；单个共享六位置 readout；不强加吸引子/low-rank/PCA rank；固定网络不训练。

---

## 2. 信息泄露检查

以下检查必须能由自动化测试复核，不得只靠代码评审时"看一眼"。

1. **model 的公开接口只接受编码后的 `L`/`D`/`S` 与内容无关的 clock 事件。** 目标序列、下一位置索引、环境算出的 `R2`/`R3`/`R4` 一律不得作为参数。
2. **`model` 模块不得 import `task` 的真值求解函数**，也不得 import `evaluation` 的任何符号。`evaluation` 不得反向 import `model` 的状态写入接口。
3. **不得存在** `set_true_D_branch()`、`force_correct_response()`、`update_S_from_reward()` 一类便捷入口。
4. **trial 运行路径中不得出现**读取 `L`/`D`/`S` 标签后写回神经元状态的语句。`L`/`D`/`S` 只能在 `apply_input()` 处以配置选择的位置编码及 D/S one-hot 电流进入网络。
5. **不得存在**运行时按真实 `D`/`S` 生成的 `roll`/环移操作。`architecture.md` 第 5 章的 `T_δ` 只能在 `connectivity` 初始化期间生成一次。
6. **`readout()` 的 `argmax` 只允许作为外部观测输出**，不得反向写入 Response、不得决定路由、不得触发按标签查表的转移。
7. **`simulation` 层不得做"标签判断 → 直接设某分支活动"的隐藏 if/else。** `advance_phase()` 只能施加非内容特异的时序控制电流、解除统一阶段抑制或触发回路阶段许可。
8. **读数隔离测试**：`environment` 的 target 在 trial 执行期间不可被模型对象访问（例如用代理对象在运行期屏蔽 target 属性，模型仍须正常跑完并产生正确输出）。

违反本节任一条即为阻塞缺陷，必须先修复再继续。

---

## 3. 模块接口约束

- `task` 生成 `L`/`D`/`S` 编码与目标序列；不得把目标数组或"下一位置"作为 model 接口参数。
- `model` 实现神经活动动力学、固定连线、输入电流与读取活动；不依赖 `task` 的真值求解函数。
- `simulation` 只安排时钟和积分，不做隐藏的标签分支。
- `evaluation` 只在模型输出后评估结果，不能修改正常运行网络状态；吸引子与扰动实验只能操作独立深拷贝，明确记录条件。
- 推荐网络公开接口：`initialize()`、`apply_input()`、`remove_stimulus()`、`step()`/`integrate()`、`advance_phase()`、`get_activity()`、`readout()`。
- **不得公开** `set_true_D_branch()`、`force_correct_response()`、`update_S_from_reward()` 等违背本版边界的入口。
- 实现阶段可在保持接口约束的前提下合并文件，但**不得合并** `task` / `model` / `simulation` / `evaluation` 的职责边界。

---

## 4. 验收门槛

| 层级 | 门槛 | 判据位置 |
| --- | --- | --- |
| Level 1 · 行为 | 无噪声 baseline 下 **24/24 条完整四位置序列正确**；各 stage accuracy 单独报告 | `todo.md` P4 |
| Level 1 · 记忆 | 撤除输入后 `R1`/`M_D`/`M_S` 在所需 delay 与 gate 期间保持可分辨选择性；不得以持续外部 clamp 取代 | `todo.md` P1、P2 |
| Level 1 · 门 | source/gate/clock单独不能产生位置；正确组合激活所选通路，未选通路静息 | `todo.md` P1、P2 |
| Level 1 · 时序 | `t_readout1 < t_Dgate`、`t_readout2 < t_Sgate`、`t_readout3 < t_R4transition` 全部成立；Readout 1 前无提前的 D 路由 | `todo.md` P4 |
| Level 1 · 继承 | `R2` 之后不再依赖 `D` 记忆下游输出完成 `R3`/`R4`；`R3` 之后不再依赖 `D`/`S` 记忆下游输出形成 `R4` | `todo.md` P4 |
| Level 1 · 边界 | 第 2 节的信息泄露检查全部通过；Dale 符号检查全部通过 | `todo.md` P0 |
| Level 2 · 干预 | 干预 A/B/C/D 各自具有阶段特异后果；每项干预配等剂量随机 lesion 对照 | `todo.md` P5、P6 |
| Level 3 · 表征 | 报告分支间分离角**与**分支内位置张成维数两个量；不预设结果为 1/2/4/4、low-rank 或吸引子 | `todo.md` P6 |

**24/24 是解压缩网络行为的验收标准，不是"网络从不完整观测学习出 L/D/S"的证据。** 本版不考察后一个问题。

失败处理顺序固定为：先定位信息泄漏 → 再查 Dale 符号 → 再查时序/门控 → 最后查数值稳定。**不得通过绕开神经回路来"修好"行为指标。**

---

## 5. 测试与日志

### 5.1 必备测试文件

| 文件 | 覆盖内容 |
| --- | --- |
| `tests/test_information_boundary.py` | 第 2 节全部 8 条信息边界检查 |
| `tests/test_dale_constraints.py` | E→E、E→I、I→E、I→I 符号与状态更新；I→I 必须是抑制 |
| `tests/test_memory_delay.py` | `R1`/`M_D`/`M_S` 在 delay 内的保持与可分辨选择性；clamp 对照为负 |
| `tests/test_direct_activation.py` | 直接激活的重合条件、错误支路静息、E_gate活动及因果阻断 |
| `tests/test_readout_order.py` | 三个时序不等式；Readout 1 前无 D 路由；四次 readout 分属四个事件 |
| `tests/test_pathway_inheritance.py` | `R2`/`R3` 之后的分支继承；`R3→R4` 不依赖 `M_D`/`M_S` |
| `tests/test_24_sequences.py` | 24 条完整序列与逐 stage 准确率 |

### 5.2 判据测试的写法

**一条永远为绿的判据没有判别力。** 每个判据测试必须先在模型改造前写出来并确认其失败（红），再做模型改造（绿）。A2/A3/B1/B2/D2 型的判据尤其如此。

### 5.3 日志

每个 time step 至少记录：全体 E/I 率向量（含群体标签映射）、每个 E_gate、I_tonic 与 I_decay 活动、每个 response 分支的活动、`Y` 的 6 个读出值与该窗口决策值、事件时间戳、干预窗口（类型、起止、目标单元或连接）。

trial 输入 `(L,D,S)` 与 evaluator 的 target **写在独立日志文件中**，不回流模型。

### 5.4 归档

零模型结果、噪声退化曲线、门扫描、角度矩阵、参数敏感性、干预对照，全部写入 `artifacts/`，并附**源码哈希与环境版本**。报告必须可由产物直接复算。

---

## 6. 复现标准

- 每次实验归档：解析后的完整配置快照、源码指纹（文件哈希）、环境版本（Python、NumPy 版本、平台）。
- 随机试验必须记录种子（`7`、`11`、`19`）；**无噪声模型的结果不应依赖种子**，这是必须测的确定性检查。
- 复现命令固定为：
  - `python -m unittest discover -s handcrafted_ei/tests -v`
  - `python -m handcrafted_ei.evaluate`
- 参数、阈值、tonic drive、兴奋门控电流、时间窗、噪声采样位置集中在 `config/baseline.yaml` 一类配置文件中管理，并写明单位、量纲、初值状态、仿真时间轴、噪声采样位置、日志格式。
- 权重初值是手工设定的先验，**不是**对任何数据的拟合。报告中不得把初步调参说成生理数据拟合。

---

## 7. 变更管理

- **先写判据测试并确认其失败（红），再做模型改造（绿），最后归档该阶段结果。**
- 每个里程碑结束时归档：配置快照、测试结果、复现命令、预期与实际对照。
- 阶段按 `todo.md` 的 P0 → P7 依赖顺序推进。P4行为与边界验收前不进入P5–P7后验分析；全程不加入训练。
- P4 的行为、信息边界与时序判据未通过前，不进入 P5–P7 的噪声、敏感性或表征分析。
- 每次修改模型拓扑或机制，必须同步更新 `architecture.md` 的对应章节。文档与实现不一致时，以实现为准并立即修文档。

### 7.1 Git 提交工作流

- 项目文件夹是独立 Git 仓库，仓库根目录就是本目录。提交前确认 `git rev-parse --show-toplevel` 指向此处；只处理本仓库文件，不在上级 `E-I-MODEL` 仓库暂存、提交或推送本项目。
- 每个产生文件修改的 AI 任务，在完成必要验证后，核对本会话编辑文件与 Git 状态，并为**本次任务仍未提交的全部修改**发起一次提交提案。不同仓库分别提交；不要用 `git add -A` 纳入无关文件。
- 在 Nimbalyst 中使用 `developer_git_commit_proposal`，让用户检查文件范围、diff 和提交说明后确认；不要用命令行 `git commit` 绕过此流程。提交被拒绝或失败时，明确报告仍未提交的文件，不得声称已经完成同步。
- 用户确认提交后，检查 commit ID 与本次文件的 Git 状态，才将会话标记为已提交。一个完成的任务对应一个可回溯的 commit；不要求对每次临时编辑或保存分别提交。推送远端是独立操作，只有用户明确要求时才执行。

没有用户的授权，禁止使用computer use 功能。

---

## 8. Stop conditions

出现下列情况，**立即停止实现并向用户报告**，不要自行绕过：

1. 为达成 24/24 只能靠标签索引、位置覆写或绕过 E/I 动力学。
2. 信息泄露检查（第 2 节）无法通过，且修复需要修改 `task`/`model`/`simulation`/`evaluation` 的职责边界。
3. Dale 约束无法满足而唯一解法是给 E 突触引入负符号或负 magnitude。
4. 直接激活只能靠重新引入 I_release⊣I_gate 路由、标签乘法或位置覆写才能实现。
5. 某项干预没有产生预期的阶段特异后果，且原因不是"预期本身写错"——此时先排查日志与拓扑，不得修改任务真值。
6. 需要新增训练、损失函数、optimizer 或 architecture search 才能继续。
7. 需要修改 `L`/`D`/`S` 的输入定义、目标序列定义或 24 条件集合才能通过测试。
8. 用户只授权文档/设计阶段时，不得自行进入实现。本次2026-10-26用户已明确授权v2代码修改、测试、实验与归档；不允许训练或擅自安装依赖。

报告时给出：现象、已排除的原因、卡住的具体判据、可行替代方案。

---

## 9. 术语约定

全仓库统一使用：`L`/`D`/`S`、`M_D`/`M_S`、`R1`–`R4`、`E_gate`、`I_tonic`、`I_decay`、`readout-first`。

- `L` 初始位置，`D` 方向（`+1`/`-1`），`S` 步长（`1`/`2`）；位置沿顺时针递增，运算在 `Z_6` 上取模。
- `R1`–`R4` 是四个 response 阶段；`R2` 有两个方向分支，`R3`/`R4` 各有四个 `(d,s)` 分支。
- E_gate 是兴奋性率单元，由规则记忆与内容无关阶段许可共同激活；I_tonic提供背景抑制，I_decay由对应Response驱动并抑制memory。主模型不使用I→I去抑制选择。
- "默认关闭"指通路在未收到足够直接激活 时不传递内容，不指模型被写成"若无事件则输出恒零"。
- "分支继承"指 `R3→R4` 沿当前分支的固定连线推进，不再查询 `D`/`S` 记忆。
- "1/2/4/4"指固定 `L`、遍历 `D`/`S` 时的**潜在 response 分支数**；它不是同时激活的分支数，也不是活动矩阵的 PCA rank。
- "神经子空间"是**事后观察对象**，不是预先构造的低秩结构；稀疏活跃 ≠ 低秩。

## 10. 编码、记忆终止与后验分析的强制判据

- location_encoding支持one_hot/ring/topology；原始维度6/1/2与内部六位置维度分开报告。连续编码不得先离散解码为one-hot后宣称内部表示不同。ring用周期距离；二维A验证A⁶、逆、平方与方向；A负系数不得作为负E权重。
- 所有候选T_d/T_ds仅初始化构建。运行时不得使用真实D/S调用roll、matrix_power/inverse或选取拓扑；模型不import task/evaluation。
- M_D保持至R2形成，M_S保持至R3形成；显式Response→I_decay⊣memory反馈按层、逐单元阈值和慢率积分，不对全Response总量作软件阈值。不允许phase事件清零、定时降低gain。
- direct activation通过source/gate/clock缺一负对照、E_gate连接符号与阻断验证；tonic inhibition必须来自实际I率单元。位置由源固定投射，gate只提供分支许可。
- 必备新增测试：test_tonic_inhibition.py、test_memory_decay.py、test_location_encoding.py、test_location_transform.py、test_attractor_dynamics.py、test_subspace_representation.py。旧去抑制测试与故障注入须替换；历史记录保留。
- 反馈切断应阻止终止；延迟Response应延长memory保持；过早抑制memory应损伤相应阶段。各必要性干预配等边数/幅度/符号/时窗随机对照。
- 吸引子分析仅在独立副本中，关闭sample、明确clock/tonic条件，记录残差、扰动恢复、初态扫描与稳定性谱。检测不得影响正常状态推进；吸引子不存在不是失败，不许为结论改标准。
- 源码或机制变更同步完整架构。历史artifacts/v1与receipt不覆写；v2独立归档完整配置、源码哈希、环境、种子、全率、事件及复算。
- 不允许运行时答案注入、训练、额外规则记忆、改变24条件或读出顺序；如需这些才能继续立即停止报告。

## 11. 正式神经群体绘图与分析工作流

- 分析入口为 `python -m handcrafted_ei.visualization.plot_all`；先完成 DATA_AUDIT，核验原始轨迹、编码身份、受保护源码与归档哈希。完整率数据优先复用；重建字段必须标注来源。
- 绘图参考必须核对原始论文题目、DOI、具体 Figure/panel、图注及实际原图。分别记录图注核验和视觉核验，无法获取的来源不得声称已看过。原图仅作参考，不当成本模型结果。
- 不伪造神经活动、统计重复、置信区间、显著性、缺失阈值或 NA。全网络为核心，明确率为无量纲；不删静息神经元以夸大低维。位置等距的相关性保持 undefined，不能填零。
- 区分输入几何、实际表征几何、结构性分支支持和动力学稳定性。角度必须有结构对照；微小距离差同时报告效应量。六个位置不是连续流形或连续环吸引子证据。
- 严禁为了图好看改变模型、动力学参数、L/D/S边界、固定连接或readout-first。独立动力学干预只操作副本，按活动选择目标，不把真实答案注入状态。
- 固定seed7/11/19并记录独立重复单位、噪声实际剂量、预处理与窗口。每图PNG300dpi及SVG/PDF、数值CSV/NPZ、配置、源码和输入哈希、参考panel写入figure_manifest。
- 文件完整性检查与实际打开图像的视觉检查缺一不可；记录空白、裁切、轴范围、图例、色标、E/I、panel、跨编码缓存身份。缓存须校验输入和输出哈希，缺失/损坏重新计算。
- 正式分析位于 `artifacts/neural_representation_v2`。大型完整扰动NPZ保留本地且由summary哈希索引、统一CLI重建，不覆盖旧版归档；参考PDF/原图仅本地保留。

## 12. Reference-grounded 科学复现与可视化

- 文献复现前实际读取本地 `C:/Users/Totheinfinity/.codex/skills/paper2agent/SKILL.md`，按真实组件及CLI执行，禁止猜测API。Paper2Skill构建文献包，不自动执行算法或审图；Codex专家补足的职责必须披露。正式包须逐页审阅、require-reviewed build、strict verify和fresh verifier。
- 两篇核心论文分别由独立、可持续咨询的子Agent负责；至少保存原数据要求、LDS兼容性、adapter审阅、实际图反向评审四轮请求/响应/证据/文件/状态。角色有唯一ID及独占写目录，不并发修改同文件，不强制覆盖会话状态。
- 每篇建立Reference Data Contract：来源/panel、变量及轴、单位、trial/condition/repeat、外驱、时序、扰动/配对noise、预处理/PCA拟合集、距离/稳定性/统计公式、视觉语义、unknown。逐字段判PASS/ADAPT/RERUN/INCOMPATIBLE；禁止reshape造重复、插值造缺失试次、状态扰动冒充输入扰动。
- 原图、作者代码执行、Methods重建、LDS适配及真实动力学差异分别归档。不可伪造源数据/作者代码执行，不为图像相似修改模型、参数、固定连接或任务。
- Scientific Fidelity Gates：G0能力实测；G1来源/代码覆盖与缺口；G2数据兼容；G3数值正确；G4同一论文专家实际图反向审阅；G5未参与实现的独立验收。不能将source exact BLOCKED与LDS adaptation PASS合并成“复现成功”。
- 共同向量场检验须完整24个R3条件、sample/clock/tonic显式固定、完整残差/连续与Euler谱/身份、clip折点证据。局部稳定、有限方向恢复、全局盆和dynamic attractor为不同结论。
- 源方法审计入口 `python -m handcrafted_ei.visualization.plot_all --reference-grounded`，产物 `artifacts/paper2agent_reproduction`。历史入口与图保留，不冒充已通过新gate。大型完整basin NPZ/受版权限制原图及文献包本地留存，由manifest索引。
- 论文式affine相图入口 `visualization.plot_all --phase-portraits`，独立归档 `artifacts/phase_portraits_v2`。明确展开系数与PC不同；非法全状态mask而不clip；蓝slice-streamlines与红完整轨迹分开；主图披露场与轨迹离面量，不能把不闭合切片当完整吸引域或为了图形好看隐藏共同活动平衡。
