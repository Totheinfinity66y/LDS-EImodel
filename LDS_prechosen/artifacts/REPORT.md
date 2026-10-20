# 独立 response 分支模型验证报告

完整序列：24/24。实际末态拟合的方向子空间数：[1, 2, 4, 4]。每组中心化位置维数均为 2。

失败对照（完整序列正确数；沉默或并列峰均判失败）：

- no_direction: 0/24
- no_step: 0/24
- no_content: 0/24
- cut_final: 0/24
- identity_first_shift: 0/24
- all_gates_open: 0/24

原始末态及三次转移时间序列见 activities.npz；各条件见 conditions.csv；源码哈希与完整角度矩阵见 summary.json。

local_geometry.png 的各组分别投影到自身 PCA，且添加展示平移，不能用图上的距离判定子空间关系；principal_angles.png 才显示共同 66 维空间内中心化位置子空间的夹角。

这是预设分支和环移的工程验证，不是数据拟合、泛化学习或生物机制发现。未模拟真实神经元重叠、仿射偏置的提前分离、block 推断、噪声稳定性或自主时钟。
