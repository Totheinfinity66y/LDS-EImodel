# Handcrafted E/I Decompression v2：架构规格

## 1. 科学问题与冻结定义

研究给定压缩 primitive 后神经活动如何依次解压缩四个位置。固定连接、handcrafted E/I rate network，不训练、不拟合生理数据，不研究历史推断、奖励或 block learning。专门记忆只有 M_D/M_S；L 由 R1 自身维持，禁止 M_L/M_DS。

六位置为 Z6，顺时针递增。L∈{0,…,5}，D∈{+1,−1}，S∈{1,2}。仅 task.target 生成真值：

$$ (R_1,R_2,R_3,R_4)=(L,L+D,L+D+DS,L+2D+DS)\pmod6. $$

模型不接收标签、target 或下一位置。两次选择依次使用 D、S；潜在分支数1→2→4→4。R2 形成后方向由分支继承；R3 后不再查询 D/S。每次先读出再转移，四次独立窗口共用唯一六位置 Y。clock 仅提供无内容许可与统一退役电流。

## 2. 群体、连接与 Dale

实现：handcrafted_ei/model/connectivity.py，矩阵方向 [post,pre]。

| 群体 | 类型/维度 | 功能 |
| --- | --- | --- |
| R1/R2/R3/R4 | E，6/12/24/24 | 每分支六位置，递归保持 |
| M_D/M_S；Y | E，各2；6 | 规则记忆；共享读出 |
| E_gate_D/E_gate_S/E_gate_34 | E，2/2/1 | 前两层规则与时钟重合；第三层仅时钟 |
| I_tonic_R/I_tonic_M | I，各1 | 实际背景抑制单元 |
| I_decay_D/I_decay_S | I，12/24 | R2/R3逐位置慢反馈 |
| comp_R1/comp_D/comp_S | I，6/2/2 | 输入候选竞争 |
| retire | I，3 | 旧Response统一退役 |

共132个率状态：81 E、51 I。I_decay 每个单元仅感受对应层一个 Response 位置，逐单元阈值后再抑制对应 memory。R1 不驱动 decay；R2 只终止 D，R3 只终止 S。多个弱分支不在阈值前求和。足够强且持久的错误 Response 也可能触发终止；这是活动检测，不是答案正确性检测。

```mermaid
flowchart LR
  L[L编码] --> R1
  R1 -->|固定T_d| R2
  R2 -->|固定T_ds| R3
  R3 -->|固定T_d| R4
  MD[M_D E] --> GD[E_gate_D]
  GD --> R2
  MS[M_S E] --> GS[E_gate_S]
  GS --> R3
  R2 --> ID[I_decay_D]
  ID -->|抑制| MD
  R3 --> IS[I_decay_S]
  IS -->|抑制| MS
  IT[I_tonic_R] -->|背景抑制| R2
  IT -->|背景抑制| R3
  IT -->|背景抑制| R4
```

## 3. 连续动力学、初值与静息态

所有 E/I、Y、gate、反馈使用 model/neuron.py 的统一方程：

$$\tau_i\dot r_i=-r_i+\phi(\sum_j s_jW_{ij}r_j+b_i+u_i+c_i-\theta_i),\quad\phi(z)=\min(1,\max(0,z)).$$

W≥0，s_j仅由突触前E/I身份决定；I→I如存在也为抑制。Euler dt=5 ms，τ_E=40、τ_I=20、τ_decay=120 ms。全部率初始0，仅两个 tonic I 以无输入稳态1初始化。率、权重、电流无量纲，不解释为Hz；参数集中于 config/baseline.yaml，均为手工工程选择，无数据拟合。

Response递归权重2、tonic E=.15、θ_E=.25。I_tonic_R 对R1投射.1、对下游.8。下游净静息偏置−.9；位置源投射.8；选中gate稳态.8、投射.8，提供.64。暗态仅source驱动−.1，仅gate为−.26，组合为.54。已亮态无gate时2−.9=1.1，可自维持。gate对分支内六位置提供相同亚阈兴奋，具体位置只由源的固定投射决定。R1用较弱背景抑制保持起点。

记忆与反馈：

$$\tau_E\dot m_a=-m_a+\phi(2m_a-.3-I_{comp,a}-3\sum_qz_q+u_a),$$
$$120\dot z_q=-z_q+\phi(2.4r_q-1.4).$$

memory背景I权重.2，sample电流.8x；撤输入后已亮状态抵抗抑制。q分别为R2/R3单元，r_q>7/12才驱动反馈，慢积分滤除瞬态。递归权重不变；增强抑制降低有效维持能力，不能声称等价于乘法gain调制。不存在clock→decay、事件清零、标签判断或正常运行期改权。反馈切断、提前破坏memory递归维持、延后Response形成需作因果验证。

## 4. 直接激活、继承与退役

$$\tau_E\dot g_{D/S,a}=-g_{D/S,a}+\phi(.9m_a+c-1),\quad c\in\{0,.9\}.$$

memory和clock单独均不产生gate，重合时选中gate趋近.8。D gate分别投R2两支；S gate投两个方向内相同步长子支，方向来自活跃R2。不存在I_release→I_gate路由。第三层单个E_gate_34由clock驱动，对全部R4候选支等价，只由R3源携带内容。旧Response由retire I提供3.2统一抑制，独立于选择。Y接收各阶段同位置.8投射、阈值.3；argmax仅是外部观察。

## 5. 编码、固定变换及噪声

model/location_encoding.py；配置location_encoding取one_hot、ring、topology。外部维度6/1/2；内部每分支均6，输出6。

- one_hot：e_k，直接映射六位置电流。
- ring：θ_k=2πk/6；周期距离|atan2(sinΔ,cosΔ)|；电流exp[κ(cos(θ−θ_j)−1)]。
- topology：v_k=[cosθ_k,sinθ_k]；非零输入投回单位圆，电流exp[κ(v·v_j−1)]。零向量映射零电流。

κ=4；两种连续编码产生宽调谐，邻居非零，不做离散解码。映射后L2归一化。范围仅是外部编码对相同Response网络的影响；ring/topology无噪声电流相同，不声称比较不同内部维度。

$$ (T_\delta)_{post,pre}=1\ \text{iff}\ post=(pre+\delta)\bmod6,$$
$$A=\begin{bmatrix}\cos(\pi/3)&-\sin(\pi/3)\\\sin(\pi/3)&\cos(\pi/3)\end{bmatrix}.$$

固定拓扑在初始化建全部W12=w_pT_d、W23=w_pT_ds、W34=w_pT_d。A只验证外部二维几何，不把负系数写入E连接。ring用模2π加法，不存在非平凡1×1实旋转矩阵；内部用六维T嵌入。测试A⁶=I、逆、平方以及全部位置±1/±2映射。

sample开始采样一次原始坐标高斯，总期望平方范数σ²，每坐标SD=σ/√dim；ring wrap，topology投回圆，one_hot截负后归一化。三种电流均归一化，并记录实际电流扰动范数。相同原始噪声能量不意味着相同神经电流误差，禁止由此直接宣称编码优越性。seeds7/11/19，各条件使用可复现派生种子。

## 6. 时序、接口与日志

sample200、delay1600、readout100、decision20、gap10、transfer200、retire160 ms。读出结束1900/2370/2840/3310；转移许可1910/2380/2850。先传输后退役；未来Response在许可前保持低活动。延迟交接实验只推迟内容无关许可，不改正常顺序。

task编码及真值；model不import task/evaluation；simulation仅clock、积分与观测；evaluation在返回输出后评价。正常接口initialize/apply_input(x_L,x_D,x_S)/remove_stimulus/step/integrate/advance_phase/get_activity/readout。apply_input只写stimulus，不写rates。字符串与数值分别校验；时间窗必须是dt整数倍。

每步记录全部132维rates、labels/groups、Y和时间；事件、干预边/单元、幅度、窗口独立保存。LDS/编码/target/seed在独立task文件。分析与正常运行隔离；吸引子测试仅在独立副本施加明确记录的扰动，不反馈到任务状态。

## 7. 验收、因果与后验分析

旧16测试与源码先归档。P4须三编码各24/24、逐stage、Dale、信息边界、readout-first、门前保持与分支继承通过，才开展P5–P7。

A首次转移前切M_D→E_gate_D，预期只保留R1；C第二次前切M_S→E_gate_S，预期保留R1/R2；B/D在R2/R3读出后切已用memory输出，后续保持。另测gate→Response、tonic、recurrence、Response→decay、早期记忆抑制、延迟交接。随机lesion匹配边数、幅度、突触前符号及窗口。移除tonic或decay不必降低任务正确率；分别以未选通路泄漏、不能终止memory作为机制退化指标。

分阶段记录全Response与trial平均轨迹、SVD/VAF、participation ratio、分支内位置几何、principal angles、活跃比例、分支选择性、拓扑距离、memory消退后的分支稳定性。固定分支坐标影响角度，不能称为涌现正交；1/2/4/4不是PCA rank。

吸引子：关闭sample；关闭全部clock的自由演化与保留阶段电流的受迫对照分开，明确保留tonic。测静息初态、已形成Response、不同初态、扰动幅度、恢复/跳转/衰减、盆扫描、向量场残差及Euler谱半径。低残差、谱半径<1、局部恢复共同支持所测固定点局部稳定，不证明全局盆或连续吸引子；分段线性阈值附近有限差分有局限。吸引子存在与否都可接受。

## 8. 复现与解释边界

依赖numpy≥2.0（记忆AUC使用trapezoid）、PyYAML≥6、matplotlib≥3.8，analysis环境CPU。命令：`python -m unittest discover -s handcrafted_ei/tests -v`、`python -m handcrafted_ei.evaluate --output <fresh-dir>`、`python -m handcrafted_ei.receipt <dir>`、`python -m handcrafted_ei.recompute <dir>`。吸引子轨迹按快照分包，index.json记录SHA256；recompute独立复算表征、扰动、谱及全部自由演化步。

历史artifacts/v1不覆盖；新结果artifacts/v2。归档完整配置、源码SHA256、环境、轨迹及复算。失败如实保存；不把24/24当作学习/泛化，不把高活动、聚类或分支结构当吸引子证据。未测参数范围、连续时间稳定性、生物参数映射均属局限。

## 9. Whole-population Evaluation Workflow

分析系统只读正式v2 ZIP，位于evaluation/population_data、population_activity、neuron_selectivity、subspace_geometry、representational_similarity、decoding、memory_transfer、population_dynamics；模型不import这些模块。原模型、task、simulation、baseline.yaml不因分析改变。

population_data逐ZIP校验SHA和标签/群体分区，以每编码独立的[trial,time,neuron]数据集保留全部132状态；E/I和branch映射从匹配源码恢复，sample电流明确重建。population_activity按实际事件取窗，neuron_selectivity提供结构与功能支持、描述性因子分解；subspace_geometry用全部条件/神经元统一PCA与各stage/branch SVD，另有支持折叠和独立输入噪声seed对照。RSA包含全网络/当前Response/全部Response，保存效应量和群体距离贡献，解码使用不相交L/D/S条件fold。

population_dynamics的独立实验API接受原始归档和输出目录，完整状态复制、恒定外驱、延长演化、六类合法率扰动、残差/完整谱、身份保留及局部向量场；恢复条件在完整状态中判断，投影仅展示。撤任务输入但保留tonic与clock全关在本模型等价；不产生虚构的第三种动力学。

visualization/plot_all统一调度数学分析与Figure1–10、多格式导出、中文报告和figure_manifest。quality_check检查文件并生成contact sheet，实际视觉复核另记。代码、输入/输出哈希参与缓存；缺失数据显式失败，退化指标NA。完整方法、参考panel和科学边界见artifacts/neural_representation_v2/METHODS.md及FIGURE_REFERENCES.md。

## 10. Reference-Grounded Representation & Dynamics Analysis

本层不修改模型、神经元方程或参数。Paper2Agent实际入口按Paper2Skill构建经过逐页审阅及strict验证的阅读包；Paper2MCP只适用于可执行的作者实现。论文子Agent独立输出输入和Figure契约，主Agent依次咨询原数据需求、真实LDS兼容性、adapter及最终图；每轮请求响应及证据持久归档。Skill未提供的适配/反向审图由Codex完成并披露，不虚称原生能力。

`evaluation/reference_adapter.py`读取校验过的ZIP，保留[24,663,132]率及身份；显式transpose到[time,condition,neuron]，不造重复。sample/clock/tonic按记录事件重建且逐步Euler复算，标明来源而非称实测。`extract_snapshots`取全部24个R3真实读出状态。三编码外部维度6/1/2与共同132状态分开。

`reference_dynamics.py`定义完整Euclidean cross-temporal距离、PCA正交能量分解、clip剂量、配对50ms输入及独立稳定性判据。24状态共用sample=clock=0、原tonic保留向量场。低残差、连续/Euler检查、身份及局部充分条件分别保存；折点处单个0.5斜率谱不能独立证明稳定。允许活跃/折点全部连接的union图为DAG时，稳定泄漏级联提供分段局部充分条件，并求邻近精确平衡点核验。局部clip邻域界不叫吸引域半径。

`reference_reproduction.py`编排独立副本与全率归档。一次性state kick与有限输入脉冲分开；source-time assay重放正常时序，R3 assay固定实际clock。两者均有完整control/perturbed、实际外电流与共享零noise。源π通道、训练网络/动物重复缺失均标不兼容；不把阶段切换后重合解释为自主恢复。

`visualization/reference_figures.py`按审计数据绘图；`reference_comparison.py`生成仅本地的原图/明确synthetic方法检验/真实LDS三列对照，不能以synthetic替代缺失原数据。`reference_consistency.py`复算1–7正确共享方法并更新10，不实现第二套dPCA。全流程入口 `visualization.plot_all --reference-grounded`，产物独立保存 `artifacts/paper2agent_reproduction`。G0–G5分层验收，最终图交回同论文专家反审，并由fresh reviewer核验来源/数据/数值/解释。exact源实验阻塞与METHOD ADAPTED通过分别记录。

## 11. Affine State-Plane Stream Portraits

`evaluation/phase_portrait.py`与`visualization/phase_portrait.py`提供独立的论文式相图工作流，入口 `visualization.plot_all --phase-portraits`，产物 `artifacts/phase_portraits_v2`。参考Saighi/Rozenberg2025 Figure2的状态模式张成平面，不使用局部PC quiver代替streamlines。原膜电位u与本率r分开解释，不引入训练。

两实际R3终点由活动选择，构成共同B；各clock条件从内容无关初态积分得到平衡背景b_c。r=b_c+B lambda，速度由dual=(BᵀB)⁻¹Bᵀ乘完整f(r)，非法状态mask不clip。三列分别clock全关、实际R3快照clock固定、再启用原configured retire3；无sample，保留tonic，权重/参数与正常trial均不变。

蓝流线是affine切片投影场的二维积分，红轨迹是完整132状态积分后投影；不能混同。完整离面field比例和真实轨迹离面距离保存并印在主图，平面不闭合不能以蓝线估计全状态吸引域。参考点满/空仅区分完整field的stationarity与非stationary坐标参考，不由二维图认证稳定性。36/71网格和Euler步长refinement用于独立数值核验，正式数据仍dt5ms。源方法专家反审及fresh独立review后交付，不改变handcrafted结构以模仿参考图吸引子数量。
