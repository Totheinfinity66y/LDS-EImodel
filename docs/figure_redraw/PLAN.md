# LDS E/I 科研绘图实施与验收

## 目标与不变量

将现有确定性 baseline 和独立动力学实验重绘为 Figure 1–10。主图使用 one_hot；ring、topology 按相同协议作为补充对照，Figure 10 联合比较。固定网络、不训练、不改连接、参数、24 条件集合、输入定义或 readout-first。潜在分支结构不是涌现低秩；固定点与局部恢复不是全局吸引子清单。

## 数据与统一出口

- 权威输入：`handcrafted_ei/artifacts/v2/run/` 的 ZIP、archives.json、source_hashes.json。
- REC：`artifacts/neural_representation_v2/data/<encoding>/recording.npz` 与 metadata.json。
- MET：`artifacts/neural_representation_v2/metrics/<encoding>/`。
- REF：`artifacts/paper2agent_reproduction/lds_results/<encoding>/`。
- 新出口：`artifacts/neural_paper_figures_v1/`，包含 derived、figures/main、figures/supplementary、manifests、METHODS.md；不覆盖旧归档。
- 实际文件、键、shape、有限性、132 神经元标签、E/I 和群体分区、24 条件、事件及输入 SHA256 必须先审计。缺失必须显式失败或调用已核验计算器，不能从图像恢复数据。
- 时间取自逐 trial 事件。baseline 核对值：sample 0–200，delay 至1800，readout 1900/2370/2840/3310，transfer 1910/2380/2850 ms。所有率无量纲，不标 Hz。

## 按图片划分的任务卡

每卡的完成状态由独立产物证据更新；任务拆分不代表图已完成。按 R0→已有数据重绘→轻量补算→新增实验→统一比较→独立验收推进。

### R0 数据契约（所有图片前置）

验证三编码 REC/RAW/MET/REF、原始归档与受保护源码哈希；保存字段、维度、事件、身份、缺口及可重算入口。产物：manifests/data_audit*、data_contract.md。验收：数据与活动逐条可追溯，确定性条件不算实验重复。

### F01 时间活动组织

A R1–R4 单条件 peak；B D/S 各自 Memory–Gate–Decay–Response；C 固定规则、六 L 的位置选择性小倍图；D E/I 活动与活跃比例。分开保存单条件与条件均值，按 stage/branch/position/population 聚合。输入 REC、population_activity。验收：事件对齐、保留静息单元、活动阈值与分母明确。

### F02 分支路由

A handcrafted 1→2→4→4 结构；B R2/R3 所有候选分支时间曲线；C 每分支六位置活动；D 激活分支数、错误支路泄漏。补算每 trial/stage/branch 的 max rate、选择裕量、onset、竞争者峰值、错误活动积分、形成后稳定性。产物 fig02_branch_dynamics.npz/csv。R1 无竞争者应 NA。验收：结构先验与功能激活分开，单条件配对点不是独立重复。

### F03 记忆交接

A/B 分别放大 D→R2 与 S→R3 的实际率；C 对其他因素平衡的规则差异轴，保存拟合条件、窗口、中心与归一化；D baseline/feedback-block/匹配随机控制；E Memory/Response 可读出性与 chance。增补交接前后关闭 memory 输出通路的独立副本干预及匹配随机连接控制。产物 fig03_handoff_axes、fig03_temporal_ablation。验收：活动下降不写成信息消失；接管结论须有阶段因果证据。

### F04 解压缩轨迹（重点）

A 固定 L 四规则共享二维 PCA；B 共享三维 PCA 与 readout；C R2–R4 按真实分支组织的同轴小倍图；D L/D/S 投影与实际回归/对比方法。补算完整132维速度、转移后位移，输出 fig04_transition_kinematics。验收：不逐 trial 拟合、保存基与中心、时间顺序和投影解释方差、共享尺度明确。

### F05 分支子空间（重点）

A 六位置×四 R3 分支真实轨迹；B 六对分支完整角谱；C 双向 cross-VAF 与 within 参照；D 时间分辨角度及完整状态质心距离。全网络/Response/shared 三种坐标分别计算；低方差与退化秩为 NA，保存rank及容差。产物 fig05_temporal_subspaces、fig05_principal_angles。验收：独立 SVD 重算、固定支持结构对照、距离效应量、不把正交支持写成涌现几何。

### F06 六位置表征

A 固定规则六位置真实投影，保存 PCA 或 MDS/stress；B/C whole/Response RDM 与共享 Y/I 贡献；D 六位置活动、identity、margin、相对 readout 的完整状态 drift。产物 fig06_position_stability。验收：不造六边形、不连接成环、不以六状态推断连续流形；等距相关 undefined。

### F07 信息可读出性

A L/D/S 在 whole/Memory/Response 的时间曲线；B D/S train-time×test-time；C M_D/R2 与 M_S/R3 交接窗口；D seed7/11/19 独立噪声结果与条件留出分开。新增 Response branch identity decoder，记录各阶段有效标签、训练/测试条件、缺失类别与 chance。产物 fig07_branch_decoding。验收：不将固定标签解码；不混合条件泛化和同条件独立噪声泛化。

### F08 六位置离散稳定态（重点）

固定 D/S 主分支六位置：A 共享投影稳定端点；B 真实有限扰动收敛轨迹；C 全132维无穷范数残差；D 连续最大实部/Euler谱及折点证书；E 按实际剂量、位置和目标群体的恢复比例。其余三分支补图。二维初态切片 r_ref+αu+βv 使用41×41网格，非法率状态 mask，不 clip；每个合法点完整积分，并按全状态残差、距离、身份分类，保留未收敛/其他状态。产物 fig08_six_point_basins、fig08_fixed_point_certificates。验收：端点按分支筛选、固定 sample/clock=0 与原tonic；不以投影距离判盆、不宣称穷尽吸引子。

### F09 扰动恢复（重点）

A 代表单元实际率；B control-only PCA；C 完整132维 cross-temporal 距离；D seed7/11/19三个方向完整误差；E state-kick身份约束恢复曲线。新增24条件×三个阶段×三个固定方向的配对50ms输入扰动，相同电流RMS及方向定义，保存control/perturbed、实际电流、clock、行为与分支/位置身份。产物 fig09_stage_perturbations、fig09_recovery_by_stage。验收：与state kick分开；正常clock重放恢复和自主恢复区分。

### F10 三编码综合比较

A 外部输入维度6/1/2及六位置Response tuning；B 联合PCA共享轴，one_hot固定基敏感性对照；C 角度、RDM和稳定端点数量；D 实际电流匹配的身份保持、恢复和完整误差。产物 fig10_common_basis、fig10_encoding_comparison。验收：不直接对比独立PC坐标；原始坐标噪声与映射后实际电流剂量分别保存。

## 实现分工与执行顺序

使用独立 figure_data 计算层与只读绘图层。共享底层按 branch_dynamics、memory_handoff、population_trajectories、position_states、attractor_basins、perturbation_by_stage 组织，避免每图重复模拟。主代理维护调度、文档和集成；子代理按F01–03、F04–07以及数据审计分配独占源码/产物前缀。审计完成后释放并行槽进行F08–10与fresh审查；不得多人写同一文件。

先完成数据审计和已有数组支持的图，再补轻量指标；新增模拟仅操作副本，积分器须与真实model.step逐步对照。模型源码未改无需为样式改动创建模型红绿测试；新增科学判据要有失败负例。来源专家对真实参考panel、算法与最终图做核查；未实际看到原图的部分标记未视觉核验。

## 逐图交付与验收证据

每图 PNG300dpi/SVG/PDF、完整图注、NPZ/CSV、配置和条件/窗口/索引、PCA中心/基、输入/输出SHA256、环境、源码哈希、种子与独立重复单位、参考论文题目/DOI/panel、数值及实际开图记录。来源精确复现与LDS方法适配分开，不继承旧图PASS代替新图审查。

最终检查：全率可追溯；角度/VAF独立重算；共享坐标；全状态稳定性及身份恢复；缺失/NA明确；不造置信区间或重复；受保护源码未改；历史产物未覆盖。完成必要验证后核对会话编辑文件与Git状态，发起仅含本任务全部未提交修改的Nimbalyst提交提案，用户确认后读回commit，不自行推送。
