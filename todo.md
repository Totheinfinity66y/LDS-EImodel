# Handcrafted E/I v2 — P0–P7 执行与验收

当前规范见[architecture.md](architecture.md)，强制规则见[AGENTS.md](AGENTS.md)。下列新阶段未经独立验证不得勾选。文末M0–M5只表示历史v1验收。

## P0 — 冻结边界、归档基线与红测试

- [x] 完成并通过独立验收。证据：旧16测试、源码与红测试：handcrafted_ei/artifacts/v2/baseline/。
- 目标：冻结边界、归档基线与红测试。
- 代码：AGENTS/architecture/todo、tests。
- 必备测试：旧16测试及新机制失败。
- 可证伪判据：旧机制不应通过新判据。
- 产物：baseline源码、身份、tests_red。
- 完成条件：原模型可复原且失败原因明确。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P1 — 直接兴奋激活与静息抑制

- [x] 完成并通过独立验收。证据：直接激活/tonic/Dale：tests_full.txt；机制变异RED/GREEN：mutation_checks.txt。
- 目标：直接兴奋激活与静息抑制。
- 代码：connectivity/ei_network/config。
- 必备测试：direct_activation、tonic_inhibition、Dale。
- 可证伪判据：source/gate/clock单独无答案，组合正确。
- 产物：全率及门控消融。
- 完成条件：逐条件合法激活，无I→I路由。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P2 — 活动依赖记忆衰减

- [x] 完成并通过独立验收。证据：memory_decay测试与run/memory.json、causal_checks.json。
- 目标：活动依赖记忆衰减。
- 代码：connectivity、memory分析。
- 必备测试：memory_decay。
- 可证伪判据：R2只终止D、R3只终止S；延迟形成仍保持。
- 产物：半衰期、AUC、反馈及提前抑制对照。
- 完成条件：交接前保持，交接后终止且因果成立。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P3 — 模块化位置编码

- [x] 完成并通过独立验收。证据：location_encoding/transform测试；三模式六位置数学关系通过。
- 目标：模块化位置编码。
- 代码：location_encoding/task/config。
- 必备测试：location_encoding/transform。
- 可证伪判据：周期边界与全部变换正确，无负E权重。
- 产物：编码/刺激几何及噪声剂量。
- 完成条件：三模式接口及数学校验通过。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P4 — 行为、时序与继承

- [x] 完成并通过独立验收。证据：三编码各24/24；31/31测试含时序/target隔离/继承。
- 目标：行为、时序与继承。
- 代码：simulation、behavior、tests。
- 必备测试：24_sequences、boundary、order、inheritance。
- 可证伪判据：三编码各24/24、四次readout-first、target隔离。
- 产物：逐stage准确率、完整轨迹。
- 完成条件：行为与信息边界通过才进入P5。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P5 — 因果与机制消融

- [x] 完成并通过独立验收。证据：198组实验与匹配随机对照；run/metrics.csv及causal_checks.json。
- 目标：因果与机制消融。
- 代码：simulation/evaluate。
- 必备测试：interventions、变异测试。
- 可证伪判据：必要性效应及相应随机对照。
- 产物：A/B/C/D、gate/tonic/recurrence/decay等消融。
- 完成条件：预期与实际逐项记录，失败不可改真值。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P6 — 表征与吸引子后验检测

- [x] 完成并通过独立验收。证据：72快照/864扰动、全轨迹与谱/表征复算：run/analysis_verification.json。
- 目标：表征与吸引子后验检测。
- 代码：representation、attractors。
- 必备测试：subspace/attractor。
- 可证伪判据：关闭clock后残差/恢复可独立检测，不预设吸引子。
- 产物：轨迹均值、SVD/VAF、角度、盆与谱。
- 完成条件：检测能区分稳定、衰减及受迫状态。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

## P7 — 三编码对照与完整归档

- [x] 完成并通过独立验收。证据：4752trial复算PASS；全配置/环境/源码、图表和实现报告，提交提案另按Git工作流执行。
- 目标：三编码对照与完整归档。
- 代码：evaluate/receipt、README、docs。
- 必备测试：全套测试、独立复算、文档检查。
- 可证伪判据：可从保存数据重算结果，原v1不变。
- 产物：config/source/environment、图表、REPORT。
- 完成条件：全部证据与局限齐备，提交提案。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

---


当前完整结果见[实现验收报告](docs/v2_implementation_report.md)。吸引子存在与否不是通过条件；有限盆、输入编码比较及退化随机池等局限均如实保留。提交状态由实际commit读回确认，实验通过不代表已提交。

## 历史v1验收记录（不代表v2通过）

# Handcrafted E/I v1 — M0–M5 执行与验收清单

[架构规格](architecture.md)与[强制规则](AGENTS.md)共同约束本清单。范围是给定L/D/S后的固定E/I解压缩，不包含primitive extraction、feedback/block learning或训练。

## 执行纪律与复现

- [x] 在实现前建立七个必备判据测试文件，运行确认缺少实现导致失败；原始记录见 handcrafted_ei/artifacts/tests_red.txt。该记录是导入失败，不应冒充逐条行为性失败。
- [x] 复用已核实的analysis环境，不安装新依赖；配置集中于handcrafted_ei/config/baseline.yaml。
- [x] 新机制与架构同步；模型不导入task/evaluation，时钟不携带内容，标签不回流。
- [x] 最终16/16测试、完整配置、源码SHA256、Python/NumPy/平台、逐trial输入与独立target、完整rates和事件完成归档。
- [x] 五类机制故障注入均触发失败，恢复后通过；见handcrafted_ei/artifacts/mutation_checks_final.txt。首次故障注入暴露的“对照和干预同时错误仍相等”测试漏洞已修复，保留原始诊断记录。

发布步骤按AGENTS.md 7.1执行：核对本会话文件与Git状态，发起提交提案；确认后推送并读回远端HEAD。发布状态以实际Git记录为准。

复现：`python -m unittest discover -s handcrafted_ei/tests -v`；`python -m handcrafted_ei.evaluate`。Windows可用handcrafted_ei/run.ps1。最终结果以artifacts/v1中的receipt为准；历史模型通过不替代v1验收。

## M0 — 率神经元、固定连接与信息边界

- [x] Neuron/E/I类、统一bounded-ReLU Euler、非负/有限/步长检查。
- [x] 初始化固定环移投射与R1–R4分支；L/D/S one-hot仅进入R1/M_D/M_S电流。
- [x] 四类Dale连接、I→I抑制、target隔离、readout不写回、无运行期roll及拓扑不随标签改变。
- [x] 置换矩阵行列和、逆与复合性质测试。

交付：model/neuron.py、connectivity.py、ei_network.py、task/__init__.py、config/baseline.yaml。测试：test_dale_constraints.py、test_information_boundary.py、test_interventions.py。Gate：符号/边界全部通过才进M1。失败停机：需要答案注入、负magnitude或修改职责边界才能通过。

## M1 — R1保持与第一个在线读出

- [x] 无独立L memory，撤除sample输入后R1保持六种L选择性。
- [x] 单个Y、100 ms读窗取末20 ms均值；输出argmax在simulation观测层，不能回写。
- [x] Readout1前R2无提前路由；1.6与4.0 s无输入保持及去recurrence负对照。

测试：test_memory_delay.py、test_readout_order.py；交付完整轨迹与时序。Gate：六起点首读正确、撤输入保持且无提前路由。失败停机：只能通过持续clamp或读取标签保持。

## M2 — M_D与第一层真实去抑制

- [x] M_D(E)→I_release(I)⊣I_gate(I)⊣R2(E)，固定±1投射。
- [x] 默认门抑制、release/gate逐层活动、错误方向分支沉默。
- [x] 12种(L,D)首两阶段正确；无release与无I→I对照导致退化。

测试：test_disinhibition.py；交付gate/release及R2轨迹。Gate：12/12且真实去抑制证据可见。失败停机：只能用D标签选择矩阵或绕开I→I回路。

## M3 — M_S与四分支R3

- [x] M_S外部电流撤除后保持，S release作用于两个方向的相同步长门。
- [x] 固定T_ds连接；方向由R2活动继承；切断D memory输出后R3/R4保持。
- [x] 24条件正确且每trial仅一个主要R3分支携带位置。

测试：test_pathway_inheritance.py、test_disinhibition.py；交付四路线轨迹。Gate：24/24前三项正确且无需再次查询M_D。失败停机：需要重读D或根据试次标签设置R3。

## M4 — R4继承与四次readout-first

- [x] R3→R4固定T_d，无D/S内容控制；R3位置扰动改变R4。
- [x] content-free clock、先传输再统一退役、旧阶段残余<0.05再读出。
- [x] 无噪声24/24完整序列，各stage单独准确率；三时序不等式；seed7/11/19确定性。
- [x] R3形成后切断M_D/M_S输出仍完成R4；全阶段只一个六位置Y。

测试：test_24_sequences.py、test_readout_order.py、test_pathway_inheritance.py。Gate：全部通过后才进M5。失败停机：需要运行时公式注入、rank-specific答案头或修改24条件。

## M5 — 因果、鲁棒性与表征

- [x] A/B/C/D覆盖全部24条件，检验阶段特异预期；每项等边数、等权重幅度、等时窗随机lesion，seed7/11/19。
- [x] delay扫描1600/2400/3200/4000 ms；位置噪声σ=0/.03/.1/.2/.4，seed7/11/19。
- [x] gate幅度0/.4/.8/1.2与recurrence0/1.6/2/2.2敏感性，包含零模型。
- [x] 全率轨迹、gate/release、Y、时序与干预日志完整，输入/target独立；39个实验、936个trial的压缩包校验与轨迹重算PASS。
- [x] 同时报告分支间principal angles与分支内位置线性/中心化维数，附SVD、VAF、participation ratio、活跃比例。
- [x] 写明固定群体坐标对角度的影响，不把1/2/4/4当PCA rank，不把有限保持当连续吸引子。

交付：evaluate.py、evaluation/behavior.py与representation.py、artifacts/v1/REPORT.md及各JSON/CSV/NPZ/图。测试：test_interventions.py；因果gate由causal_checks.json记录。Gate：A只保留R1、C保留R1/R2、B/D保持四项；如不符合，停止扩展并先查日志/拓扑，不能改真值。随机对照结果如实报告，不能强制成预期方向。

## 未覆盖的后验问题

最小I规模、连续噪声、更长delay、吸引子盆、自主stage转换与生物参数映射没有在本验收中确定，不作为通过标准，也不作已完成结论。
