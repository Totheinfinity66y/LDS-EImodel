# 科研重绘数据契约与审计

本契约针对 Figure 1–10 的本地正式输入。审计程序为 [data_audit.py](../../artifacts/neural_paper_figures_v1/manifests/data_audit.py)，机器可读结果为 [data_audit.json](../../artifacts/neural_paper_figures_v1/manifests/data_audit.json)。全部路径相对仓库根目录，历史归档保持只读。

## 实际核验结果

2026-10-28 本地核验为 **PASS_WITH_LIMITS**。三编码各 24 条确定性条件、663 个时间点、132 个神经元；共 72 条标准化轨迹与各自原始 baseline ZIP 中 `00_rates.npz`–`23_rates.npz` 的 `rates` 和 `times_ms` **逐值相同**。3 个 baseline ZIP SHA256 同时匹配 metadata 与 RAW archives 索引。8 个受保护源码 SHA256 与正式归档一致。147 个 REC、MET、REF 文件完成存在性、SHA256 和 NPZ 数组头/CSV 列名清点；REF 全部数组的科学数值正确性仍须按具体图独立复算，不能由文件完整性替代。

实际环境为 `C:/Users/Totheinfinity/.conda/envs/analysis/python.exe`，Python 3.12.12、NumPy 2.3.5、SciPy 1.16.3、Matplotlib 3.10.7。CPU 足以执行本审计及线性代数。Windows 直接启动此解释器时，需要在该命令进程内将该环境根目录、`Library/bin`、`Scripts` 加入 PATH，否则 NumPy 导入可能 exit 1。未安装或修改任何依赖，未运行模型仿真。

## REC 标准入口

每编码入口为 `artifacts/neural_representation_v2/data/<encoding>/recording.npz` 与同目录 `metadata.json`，其中 `<encoding>` 为 `one_hot`、`ring`、`topology`。MET 正确目录为 `artifacts/neural_representation_v2/metrics/<encoding>/`。

| 字段 | 实际形状 / 语义 |
| --- | --- |
| rates | `(24,663,132)` float64，全 E/I 无量纲率，有限且处于 0–1 |
| times_ms | `(663,)`，0–3310 ms，步长 5 ms |
| neuron_labels / neuron_types | `(132,)`，唯一标签 / E 或 I，81 E、51 I |
| input_currents | `(24,663,132)`，由已记录输入与sample时序重建；不是独立实测字段 |
| outputs | `(24,4)`，匹配独立 task target |
| trial_id | `(24,)`，trial行身份 |

`metadata.tasks` 提供各行 L/D/S、encoded 输入、独立 target、trial seed；`metadata.events` **是 24 个 trial 字典的列表**，不能当作单个字典访问。`population_indices` 为完整132单元无重叠分区，`branch_indices` 为每分支六单元列表。当前三编码的标签、分区及事件相同，但计算入口仍须逐编码验证，不能用文件夹名代替身份检查。

| 事件 | 实际 ms |
| --- | --- |
| sample_start / sample_end | 0 / 200 |
| delay_end | 1800 |
| readout1 / to_R2 / retire1 | 1900 / 1910 / 2110 |
| readout2 / to_R3 / retire2 | 2370 / 2380 / 2580 |
| readout3 / to_R4 / retire3 | 2840 / 2850 / 3050 |
| readout4 | 3310 |

Response 索引：R1 0–5，R2 6–17，R3 18–41，R4 42–65；M_D 66–67，M_S 68–69；Y 70–75；E_gate_D 76–77，E_gate_S 78–79，E_gate_34 80；I_tonic_R/M 81/82；I_decay_D 83–94，I_decay_S 95–118。所有计算须从 metadata 取索引，本表用于核对。分支顺序应根据标签/受保护连线核验，不能凭绘图颜色猜测。绘图可离线使用 task 标签分组，不能把 target 或分支选择写回网络。

## 既有派生字段的直接复用

- `subspace_geometry.npz`：`global_scores(24,663,3)`、`global_components(3,132)`、`global_mean(132)`、`global_evr(132)`、`variable_axes(4,132)`、`variable_scores(24,663,4)`。PCA 投影用 `(rates-global_mean) @ global_components.T`。每编码独立拟合，Figure 10 必须另建共同基。
- `memory_transfer.npz`：M_D/M_S/R2/R3/I_decay_D/I_decay_S/E_gate_D/E_gate_S 各为 `(24,663)`；同时含 baseline/no_feedback/no_tonic/random_feedback 聚合曲线。聚合曲线不能冒充单条件轨迹。
- `decoding.npz`：`times_ms(41)`、`whole__D` 等时序准确率 `(41,)`、`cross_temporal__D/S(41,41)`。`decoding_noise_seed.npz` 使用另一套 `times_ms(43)`，`seed_ids(3)`，单seed字段如 `whole__D__seed_accuracies(3,43)`。两套协议及时间轴分开处理，结合对应 splits JSON。
- `rsa.npz` 的 `R3_b0_means(6,132)` 是全网络六位置状态；`rsa_response.npz` 的同名字段为 `(6,24)`，是当前 R3 全阶段群体坐标，不能直接假定为六单元活动分支。
- `subspace_pairs.csv` 提供完整角谱和双向 cross-VAF；先核验分支、窗口、中心化和坐标，再选择 Figure 5 的六对 R3 结果。完整列名已列入审计JSON。

## REF 动力学入口

统一目录为 `artifacts/paper2agent_reproduction/lds_results/<encoding>/`。

| 文件 | 实际核心字段 | 必须保留的解释边界 |
| --- | --- | --- |
| fixed_points.npz | rates `(24,401,132)`、endpoints `(24,132)`、conditions `(24,3)`、eigenvalues `(24,132)`、clock_used/stimulus_used/tonic_used `(132,)`、basis `(132,2)` | 固定D/S筛六条件后才能称该分支六位置状态；共同外驱须显式报告 |
| basin_full / basin_active_branch等 | rates `(288,401,132)`、initial_reference_index/amplitude/seed `(288,)` | reference_index对应fixed_points行；actual剂量及恢复/身份判据在basin.csv，不能只用名义amplitude |
| input_source_time_seed | control/perturbed `(663,132)`，实际电流 `(663,132)`，direction `(132,)`，condition_LDS `(3,)`，recorded_trial_id标量，cross_temporal_distance `(166,166)` | 每seed仅一个预选trial，不能当作24条件覆盖 |
| input_R3_fixed_clock_seed | control/perturbed `(401,132)`，cross_temporal_distance `(101,101)`，basis `(132,3)` | 固定clock协议与正常时间推进协议分开 |
| local_flow.npz | actual_states/full_field `(121,132)`、xy/velocity `(121,2)`、offplane_norm `(121,)` | 2D切片向量场不是完整状态吸引盆分类 |

所有seed文件实际存在于7/11/19。`state_perturbation.npz` 是一次性state kick；不能混同50ms输入电流扰动。六位置 basin 网格、24条件多阶段输入扰动、交接前后通路消融尚须由新增独立仿真产物证明，本审计不宣称其已完成。

## 参考材料证据范围

参考目录实际为 `artifacts/neural_representation_v2/reference_evidence/`，不是仓库根目录。历史 `config/references.json` 保存题目、DOI、caption_checked 与 visually_checked；本次仅核验文件身份，未重新逐页或逐图审阅，不能将历史状态写成新审图通过。

发现 **Churchland2012.pdf 与 Gallego2018.pdf 不是有效PDF头文件**，不可当作本地论文PDF阅读；相应panel图像文件独立存在。Kobak、Mante、Kriegeskorte、Seelig、Inagaki、Zhou、Langdon列入历史清单的本地证据均存在，具体SHA与有效PDF头结果在审计JSON。Figure 7新增 King & Dehaene 2014、Figure 8 Sussillo & Barak 2013、Figure 4 Remington 2018 不在该历史参考清单内，需另行核实来源与对应panel。

`paper2agent_reproduction/audit/source_comparison_manifest.json` 明确说明 source comparison 中间图为 synthetic method illustration，**不是作者原始数据复现**。原论文图、作者代码执行、Methods重建和LDS适配须保持独立状态。

## 图级验收边界

确定性24条件不作为独立重复，不产生虚构置信区间。静息或近零方差时间点的主角度写NA并保存容差。活动幅度下降不能推出规则信息完全消失。投影重合不能推出完整状态恢复。每张图保留实际输入hash、使用条件/窗口/单元、中心/投影基、数值参数与完整图注，再做独立复算及打开图像的视觉检查。
