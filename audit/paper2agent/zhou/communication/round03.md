# Round 3：实际 adapter 与数值代码审阅

agent_id: /root/zhou；paper_id: zhou2023；task_id: B；status: PASS_WITH_LIMITS for LDS adaptation (not exact source reproduction)。

Request：审阅实际 `handcrafted_ei/evaluation/reference_adapter.py`、`tests/test_reference_adapter.py`、`audit/data/ADAPTER_DESIGN.md`、`tests_green.txt`；5测试含3编码24trial全662transition Euler一致atol3e-15。另审`reference_dynamics.py`输入probe/cdist/投影能量。计划cue+500ms和R3-readout+20ms两个独立协议、RMS1 whole-state随机外投射、amplitude0.25、control-only PCA。

Response：实际读取全部上述文件与测试日志。无阻塞算法错误；允许进入明确标记的LDS adaptation正式绘图。

- `reference_axes`显式transpose，无重复制造、平均、插值、归一化。
- reconstructed_currents注明reconstructed/measured=false，进入timestamp的sample与clock边界合理；全部662transition的数值重建是来源一致性强证据。测试green是阅读已有执行记录，非本Agent另行运行。
- `paired_input_probe`实际分支状态共同初态，噪声数组相同；`onset<t<=offset`对应转换区间`[onset,offset)`，dt5/50ms=10更新，未做state kick。外signed current不属于Dale突触。
- `cross_temporal_distance`为control行、perturbed列全状态Euclidean，无隐式除N。
- `projection_energy`检查正交列，正确计算full=projected+orthogonal；零扰动fraction为NA。

必须随实际图归档：actual输入电流矩阵或direction+scalar+pulse的无歧义重建、实际current RMS和integrated L2 dose、PCA center/basis/fit样本窗口、fixed clock/tonic状态、noise数组。代码probe当前未直接返回actual输入阵列，调用方必须补齐。

重要限界：RMS1方向×0.25在132维的L2电流是0.25sqrt132，不是原作者0.25单通道后未知权重的相同剂量。R3固定clock延长是独立LDS实验，不能称正常stage trajectory；必须让其control与perturbed共享固定系统。原Fig7动态任务与本模型持久状态不同，不要求恢复斜带。

Open questions：等待实际NPZ、CSV、PNG、plot脚本、caption进行第四轮。source figure视觉p10、Methods视觉p13已核，不代表18页strict复审。
