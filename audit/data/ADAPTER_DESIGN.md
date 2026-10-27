# LDS 数据接口设计

## 已核验事实

- authoritative input: `handcrafted_ei/artifacts/v2/run/{encoding}__baseline.zip`；archives.json SHA256验证通过，受保护源码与source_hashes.json一致。
- three encodings one_hot/ring/topology: rates `[condition=24,time=663,neuron=132]`，t=0..3310ms，dt=5ms，81 E / 51 I。
- 24条件为6 L × 2 D × 2 S，每条件单条确定性轨迹；不是24独立随机重复。
- 原始输入L维度6/1/2；D/S分别2；内部Response维度66；全率132。率无量纲。
- 原始ZIP保存每trial的task JSON、event JSON、rates NPZ；绘图recording.npz与ZIP率逐元素相等。
- ZIP未逐步记录sample/clock/tonic电流。sample由编码输入与已验证模型配置重建；clock由事件与配置重建；tonic为固定模型向量。不得称为原始实测电流。
- 进入时间t的积分电流：sample_start < t <= sample_end；clock事件生效于t > event。t=0无积分输入，以零占位并明确不代表physical initial current。
- 状态快照在R3 readout=2840ms，继承实际记录全率；此时sample关闭，clock延续已有许可，snapshot条件必须保存。

## 共享API（不定义论文算法）

`load_audited_dataset(input_dir,mode)`：source_identity + archive checksum + shape/metadata validation。

`reconstruct_currents(d)`：返回stimulus/clock/tonic `[condition,time,neuron]` 及 provenance，各项严格注明重建。每个流量表示积分进入该时间样本的电流。

`extract_snapshots(d,stage=3)`：返回24真实rates、snapshot时刻实际固定clock、tonic、trial_id、conditions L/D/S及population identity。不得由任务标签生成神经状态。

`reference_axes(d)`：仅transpose到 `[time,condition,neuron]`，不制造trial重复，不对时间插值，不作归一化或滤波，不决定population/PCA拟合。

## 需论文专家决定

- Whole network / recurrent-like subset的科学对应。
- exact paper CD/PCA/normalization/perturbation/recovery定义。
- 是否将delay或单stage当作可比epoch。
- input perturbation必须重新仿真，不能通过state kick文件适配。
