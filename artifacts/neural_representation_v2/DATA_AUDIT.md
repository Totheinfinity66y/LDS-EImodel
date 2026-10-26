# 数据审计

审计对象是本地独立 Git 仓库 `D:/Library/10-16-handcrafted`。正式数据来自 `handcrafted_ei/artifacts/v2/run`；不使用 v1 或 activity-analysis-2026-10-25 的轨迹替代 v2 数据。

## 当前实现与源码身份

直接兴奋性门控、真实 tonic I、逐单元 Response→I_decay⊣M_D/M_S 和三种外部位置编码均已实现。`manifests/protected_source.json` 对正式归档的 8 个模型、task、simulation、配置文件逐一核验 SHA256，全部匹配当前实际文件。模型与 baseline 参数不因绘图修改。

三编码各有 132 个内部率状态，81 E、51 I；Response 每分支均六单元。R1/R2/R3/R4 为 6/12/24/24，M_D/M_S 各 2，Y 为 6，E_gate_D/S/34 为 2/2/1，I_tonic_R/M 各 1，I_decay_D/S 为 12/24，competition 为 6/2/2，retire 为 3。唯一正式配置差异是 location_encoding：one_hot/ring/topology；外部原始维数为 6/1/2，不能当作内部维数。ring/topology 的无噪声调谐电流数学等价。

## 1. 已存在且可直接使用

- 每编码 baseline ZIP 含 24 条件，每 trial 663 个时间样本（0–3310 ms，dt=5 ms），每样本全部 132 个率。保存 times_ms、labels、Y、独立 task JSON 和 events JSON。
- task 文件保存 L/D/S、编码、原始 encoded 输入、target、派生 trial seed、实验 seed、噪声强度。target 只用于模型返回后的离线评价。
- events 文件保存群体索引、四次读出、转移、退役、干预边及幅度；归档 manifest 保存完整解析配置。archives.json 保存 ZIP SHA256。
- 三编码、seeds 7/11/19 的原始坐标噪声重复、反馈/tonic/gate/记忆等消融和匹配随机边对照均有全率轨迹。它们可用于噪声可靠性与因果对照，不当作独立随机网络。
- 旧独立吸引子实验有 72 个完整状态快照、clock、强迫/撤 clock 轨迹、864 个扰动轨迹与初态扫描。其 v2 验证文件报告逐步 Euler 复算；本分析同时保留其来源并补充干预群体与指标。

## 2. 可由现有数据重算

全神经元热图、群体统计、阶段/分支窗、记忆/门/tonic/decay 曲线、四次读出、活动阈值参与率、条件因子分解、全网络 PCA、SVD、子空间角度与 VAF、RDM/MDS、规则可分辨性、残差和扰动距离。E/I 分类可由匹配源码的 signs 重建；branch_indices 可由群体索引每六单元分块。

输入电流未逐步归档，但 encoded 向量、sample 起止和 w_input 已保存，故可无损重建 sample 电流。`recording.npz` 的 input_currents 明确标注 reconstructed：每一行是积分到该时刻所用电流，sample_start 行为零，sample_end 行仍为 sample 电流。内容无关 clock 可从事件和配置重建。

## 3. 需要增加记录接口的字段

新增统一只读接口聚合 rates[trial,time,neuron]、neuron_types、population_indices、branch_indices、encoding_type、trial_id、events、重建 input_currents、config、seed、archive_path/hash。各编码独立文件，不假定跨模型 N 相同。原始 source_hash 及当前受保护源码核对保存在 manifests。

## 4. 必须新增仿真的部分

既有数据不包含六类群体限定扰动与局部向量场切片。它们仅在独立状态副本运行：full/Response/当前活动分支/未选分支/E/I，固定种子、幅度和背景条件。所有状态克隆包含 rates、stimulus、clock、weights、config 与时刻；不得仅替换率而遗失外驱。已有正式 baseline 不重复生成。

本模型撤除全部阶段 clock 与撤除全部任务输入后保留规定 tonic 背景是同一个条件；如展示三项要求，必须标注后两项等价。率是无量纲 bounded rate，不标 Hz。基线减法使用 t=0 的实际率向量。

## 5. 复现与风险

数据入口逐 ZIP 核验 SHA256，验证标签/群体分区、E/I、率边界、时间步和 metadata 完整性。新标准数据在 data/one_hot、data/ring、data/topology。已有 PPTX 未提交修改与本分析无关，保留原样。

可辨认分支来自固定候选块；六个位置平均向量中心化 rank≤5 是样本上限。无噪声条件无独立统计重复，不能产生置信区间或显著性结论。数值退化或未达阈值写 NA，不填零；持续状态和 PCA 分离不能替代吸引子动力学证据。
