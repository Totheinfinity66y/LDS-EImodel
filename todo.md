# Handcrafted E/I v2 — P0–P7 执行与验收

当前规范见[architecture.md](architecture.md)，强制规则见[AGENTS.md](AGENTS.md)。下列新阶段未经独立验证不得勾选。清单只描述当前实现。

## P0 — 冻结边界、归档基线与红测试

- [x] 完成并通过独立验收。证据：源码与机制判据红测试：handcrafted_ei/artifacts/v2/baseline/。
- 目标：冻结边界、归档基线与红测试。
- 代码：AGENTS/architecture/todo、tests。
- 必备测试：机制判据失败与恢复。
- 可证伪判据：机制缺陷必须触发对应判据。
- 产物：baseline源码、身份、tests_red。
- 完成条件：实验输入与失败原因可追溯。
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

- [x] 完成并通过独立验收。证据：三编码各24/24；32/32测试含时序/target隔离/继承。
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
- 可证伪判据：可从保存数据重算结果，科研归档保持完整。
- 产物：config/source/environment、图表、REPORT。
- 完成条件：全部证据与局限齐备，提交提案。
- 失败处理：保存失败，按信息泄漏→Dale→时序/门控→数值定位；不改冻结定义；触及stop condition立即报告。

---


当前完整结果见[实现验收报告](docs/v2_implementation_report.md)。吸引子存在与否不是通过条件；有限盆、输入编码比较及退化随机池等局限均如实保留。提交状态由实际commit读回确认，实验通过不代表已提交。

## V — Visualization & Representation Analysis（独立于模型里程碑）

- [x] V0 数据审计：DATA_AUDIT.md及manifests/protected_source.json，8个动力学源文件SHA匹配；各24×663×132。
- [x] V1 文献来源：FIGURE_REFERENCES.md及config/references.json，九篇具体panel，原图/图注状态独立记录。
- [x] V2 Figure1–3：全活动、结构/功能支持、memory条件差及反馈/tonic/随机对照，metrics按编码归档。
- [x] V3 Figure4–7：统一PCA、SVD/角度/交叉VAF/独立seed稳定性、三类RDM与Response控制、两种独立拆分解码。
- [x] V4 Figure8–9：72状态包、5184扰动条件（216无未选branch为NA）、完整谱/恢复身份/盆切片及全率NPZ本地归档。
- [x] V5 Figure10：定位/几何/动力学/量化四张综合图，metrics/encoding_summary.csv；无复合评分。
- [x] V6 科学验收：SUMMARY.md十问，明确固定支持、Y尾迹、Response等距、memory残余可解码与局部稳定性边界。
- [x] V7 归档与质量：55组/165图文件、60测试通过；figure_manifest.json、manifests/figure_quality.json及visual_review.md。

证据统一保存于artifacts/neural_representation_v2；正式完成后依据实际产物勾选，不以脚本未报错代替视觉验收。模型机制和历史artifacts/v1、v2保持不变。提交提案与推送分别遵循AGENTS。

## T — Reference-Grounded Reproduction & Visualization Audit

状态证据：`audit/REPRODUCTION_STATUS.md`；本表在独立评审结束前不提前勾选。source exact与LDS adaptation分别验收。

| 阶段/Owner | 依赖 | Input → Output | Tests/Acceptance | Blocking issues |
| --- | --- | --- | --- | --- |
| T0 root capability | 无 | 本地SKILL及组件 → PAPER2AGENT_CAPABILITIES | 实际命令、环境、支持/限制核验 | 无；Skill非自动审图服务 |
| T1 A Inagaki | T0 | PDF/作者MATLAB → 阅读包、契约、Methods代码 | require-reviewed+strict+独立核验；源码范围明确 | exact作者执行缺MATLAB/Octave与辅助函数 |
| T2 B Zhou | T0 | PDF/作者Python → 阅读包、契约、输入执行 | require-reviewed+strict；真实task入口执行 | exact Figure7缺权重/raw/扰动绘图源码 |
| T3 C data | 无 | 本地三编码ZIP/NPZ → schema/defects | 3×24×662全状态步、archive及protected hash | 无 |
| T4 root+A/B contracts | T1–3 | 原方法+schema → source-to-LDS判定 | 第二轮四状态逐项判定，无伪重复 | 原实验统计INCOMPATIBLE |
| T5 C+A/B adapter | T4 | lossless adapter → interface/tests/reviews | 第三轮实际代码审阅及负例测试 | 无 |
| T6 root+D numerical | T5 | 24R3快照 → field/J/Euler/盆/输入实验 | 合成5轨迹、能量闭合、独立数值脚本、折点证明 | 全局吸引域未测，不列为已证 |
| T7 root visual | T6 | metrics/spec → 三编码8/9/新10及三列对照 | 300dpi PNG+SVG/PDF、hash和实际打开 | 原图内部使用，synthetic中列不冒充源结果 |
| T8 A/B reverse review | T7 | 实际图+NPZ+CSV+代码+图注 → 六维审稿 | 第四轮及修后复审均PASS_WITH_LIMITS，见两FINAL_FIDELITY_REVIEW | exact源实验仍受资料/运行时限制 |
| T9 root consistency | T6 | 共享1–7及10 → 独立SVD/角度/RSA核对 | 历史CSV数值断言、明确非dPCA/jPCA精确复现 | 无源统计重复，不扩张结论 |
| T10 fresh F | T8–9 | 全部证据 → INDEPENDENT_REVIEW | 独立公式、来源包strict及实际视觉核验 | 等最终锁定文件 |
| T11 root archive | T10 | 全配置/源码/环境/图/报告 → final及提交提案 | 完整manifest、保护源码未改、70项回归 | 仅用户确认后才有commit；不推送 |
