# 实际运行结果

- 六位置 × 两方向 × 两步长：24/24 条完整序列正确。
- 四秩准确率：[1.0, 1.0, 1.0, 1.0]。
- 未选中继的最大末态率：0.0。
- 环周诊断：288/288 条通过；使用 72 个非边界角度、4 个 D/S 组合。
- 示例 L=1,D=+1,S=2：实际输出 [1, 2, 4, 5]。

模型读取的是给定 L/D/S，固定环移和秩连接包含任务规则；以上结果只验证该工程回路的执行能力。
环周诊断以最近的六位置标签评分，不是连续位置精确恢复或吸引子证明。
目标序列只存在于 evaluation.py；绘图读取 activities.npz 中的真实模型活动。

## 图与原始数据

- [联合调谐](joint_tuning.png)
- [编码率与归一化活动](encoding_activity.png)
- [三秩位移读出和门控](rank_readout.png)
- [真实 E/I 与中继时间过程](ei_dynamics.png)
- [完整序列时间轴：E1…E6、读出、门控与中继](sequence_dynamics.png)
- [全部47个率单元的活动总览](all_units_timeline.png)
- [时间轴解释与复现](../VISUALIZATION.md)
- [时间轴原始数组](sequence_timeline.npz)
- [24 条条件与实际输出](conditions.csv)
- [环周诊断](spatial_probes.csv)
- [运行配置和结果](summary.json)
- [活动及连接矩阵](activities.npz)
