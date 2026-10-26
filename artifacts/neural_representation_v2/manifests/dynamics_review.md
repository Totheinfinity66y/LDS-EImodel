# Dynamics 独立代码与图像核验

核验范围：动力学评估、Figure 8–9 和三模型综合图的动力学部分。仅审阅代码、读回数值、使用 `view_image` 打开现有 PNG；未修改模型、分析代码、正式数据或图像。采用 code-review 技能的证据与可行动问题规范。

## 已执行的核验

- 实际打开 [Figure 8 One-hot](../figures/one_hot/figure_08_one_hot.png) 与 [Figure 9 One-hot](../figures/one_hot/figure_09_one_hot.png)。两图均有完整六个 panel，未发现空白图、标题裁切、明显图例遮挡主数据或字符乱码。
- 对旧归档 `attractor_trajectories/index.json` 中全部 72 个 NPZ 重新计算 SHA256；72/72 与可信索引匹配，无缺失、额外 NPZ、哈希不符或数组名称清单不符。
- 当前三编码的 Response 群体活动比例最大值一致：R1=1/6，R2=1/12，R3=R4=1/24。因此综合图当前 `ylim=(0,.19)` 包含全部已绘数据，未发现实际截断。
- 读回随机初态端点：每编码保存 72 行，但精确去重后仅 3 个端点。这符合三个 seed 在相同自主动力学中重复使用的实验设置，不是 72 个独立初态或随机网络。

## 需要修复的问题

### 1. 高优先级：动力学缓存不能恢复缺失指标或发现损坏输出

位置：[population_dynamics.py](../../../handcrafted_ei/evaluation/population_dynamics.py)，`run()` 的缓存判断（审阅时第 114–117 行）。

触发条件：summary 指纹匹配、72 个输出 NPZ 路径存在，但任一个 `dynamics_*.csv` 已缺失；或者某个输出 NPZ 内容已损坏但文件仍存在。

因果链：缓存只检查 NPZ 的存在性，直接返回 summary。缺失 CSV 不会重建，随后 Figure 8/9 读 CSV 失败；损坏 NPZ 也不会由此缓存检出。建议 summary 保存并验证全部必要产物的相对路径、大小与 SHA256，缺失或损坏时重新生成；同时测试删除 CSV 与损坏 NPZ 的恢复行为。此次没有破坏现有文件来触发测试，结论来自直接条件分支审阅。

### 2. 高优先级：源轨迹未在执行接口内对照可信索引

位置：[population_dynamics.py](../../../handcrafted_ei/evaluation/population_dynamics.py)，`input_paths` 与 `signature` 构建（审阅时第 110–123 行）。

触发条件：源 NPZ 被修改、缺失或目录中混入额外 NPZ。

因果链：代码对 glob 找到的现有文件计算新哈希，但没有将该哈希与旧归档 `index.json` 的预期哈希比较，也没有要求预期清单完整。缺失一个源快照会形成较小的新输入集并继续执行；修改源数据会被当成新合法输入身份。当前实际数据已独立核验全部匹配，所以这不是当前结果损坏证据。建议执行前强制对照索引的文件集合、SHA256、数组名称清单，并验证要求的 3×6×4 个快照均齐。

### 3. 高优先级：Figure 8A 自动纵轴将约 1e−5 的差别视觉放大

位置：[dynamics_figures.py](../../../handcrafted_ei/visualization/dynamics_figures.py)，`fixed_points()` 的 Response peak 曲线。

实际图像证据：纵轴使用 `1e−5 + 9.999e−1` offset，刻度约 8.8–10.0；所有曲线实际几乎都在 1 附近，却显示出明显上升区间。用户明确要求不得通过坐标范围夸大差异。建议主图纵轴固定为规范的 0–1（或略留边距）并关闭 offset；如确需观察极小收敛差，另绘明确标注的误差曲线。

### 4. 高优先级：Figure 8F 的重复端点棋盘图容易夸大独立初态覆盖

位置：[dynamics_figures.py](../../../handcrafted_ei/visualization/dynamics_figures.py)，随机初态 endpoint RDM（审阅时第 26–28 行）。

实际证据：当前图为 72×72 距离矩阵；每编码这 72 个 endpoint 精确去重仅 3 个。该实验将三个 seed 的同一随机初态在不同快照名下重复演化，sample 和 clock 均撤除后使用同一方程。

建议显示去重后的三随机初态端点（明确 seed 标签），另行展示 24 个任务状态端点；或在原图标题/图注明确 `72 records; 3 unique random initial conditions`。不得将该图解读为 72 个独立初态、72 个吸引域采样或 72 个独立网络。

### 5. 高优先级：Figure 8–9 的 manifest 未准确记录实际指标与 PCA 来源

位置：[plot_all.py](../../../handcrafted_ei/visualization/plot_all.py)，`export()` 通用记录与 Figure 8–9 的 `metrics` 参数。

因果链：Figure 8/9 实际读取根级 `metrics/dynamics_*.csv` 和 `data/dynamics/<encoding>_L0_R*.npz`，但导出时传入的是 `metrics/<encoding>/` 下的分析文件。通用 `pca_scope=all 24 conditions; stride 4` 对 Figure 9 也不成立：其平面由同编码/阶段六位置自主端点拟合，交叉时间距离才使用步长 4。通用 20 ms stage window 与状态延长/端点扰动实验也不相同。

建议按 figure 类型记录确切原始 NPZ、CSV、source 指纹、2000 ms 延长、稳定端点扰动起点、六位置 endpoint PCA、幅值/seed/目标、[0,1] 裁剪和恢复准则。

### 6. 中优先级：Figure 导出缓存没有包含动力学数据身份

位置：[plot_all.py](../../../handcrafted_ei/visualization/plot_all.py)，顶层 `signature`。

当前 figure cache 签名包括分析/绘图源码、旧 ZIP archives 索引与导出格式，但未包含源动力学 NPZ 索引/哈希或生成的 dynamics summary 指纹。若动力学输入发生合法更新并重建指标，而源码和 `archives.json` 未变，图像可能被判缓存命中而保留旧内容。建议把实际 figure 使用的全部输入数据身份纳入签名；Figure 8–10 至少包含 dynamics summary 的输入指纹和必要指标哈希。

### 7. 中优先级：速度单位将 dt=5 ms 写死

位置：[dynamics_figures.py](../../../handcrafted_ei/visualization/dynamics_figures.py)，`np.diff(x)/5`。

当前归档 dt=5 ms，因此这次轴单位数值正确；若输入换成其他合法 dt，则纵轴会错误。建议使用 `np.diff(times_ms)`，或直接读取已保存的完整场速度 `*_velocity_l2_per_ms`。若保留差分速度，应标明它是 Euler 步长平均速度。

### 8. 中优先级：综合图的证据分类是固定文本

位置：[comparison_figures.py](../../../handcrafted_ei/visualization/comparison_figures.py)，dynamics 分支的 `Evidence classification`。

当前“局部稳定固定点、有限恢复盆、无连续环证据”与数值相符；但文本不读取 fixed-points 分类/残差，输入改变时会继续输出相同结论。建议从指标验证后生成文本，或明确限制图函数只支持已核验的固定数据集并断言相应判据。

## 科学解释与可读性建议

- Figure 9A 中扰动投影靠近原点，不能说明完整状态恢复；同一幅 Figure 9C 保留非零距离条带。建议在 9A 标注该特定试次的最终完整 L2 距离与恢复/身份判据，增加起点/终点标志和时间色条。控制是固定点附近的点，建议明确画出点标记。
- Figure 9D/E 的不同 target 分母不同：unselected-branch 排除无此分支的 R1，而其他 target 包含 R1。每编码每幅值其有效条件数分别为 54 与 72（状态×方向 seed），建议图注注明；这些是有限方向探测比例，不是独立随机网络上的成功概率置信估计。
- Figure 9F 已正确标注“clipped local slice”并给出 off-plane 颜色。建议补投影向量的 quiver key；该切片不能用于证明完整系统的全局吸引域。
- Figure 8D/E 应用颜色或 marker 区分固定外驱条件，并注明 tonic-only 与 autonomous 是等价重复条件。当前把它们按索引重复显示是数据透明性问题，不是独立实验重复。
- 图中未发现 E/I 身份或标签参与状态推进的入口；六类干预目标来自神经元类别与观察到的活动分支。恢复判据仍要求完整状态误差及原 Response 身份，未把共同静息算作恢复。

## 当前结论边界

所审阅图像和字段读取在当前 dt=5 ms、132 神经元配置下与保存的指标一致。主要必须修复项是坐标呈现、重复初态说明、缓存/来源校验和逐图追溯信息。当前数据支持恒定 tonic 背景下的局部稳定固定点候选与有限方向恢复测试，不支持连续环吸引子、全局吸引域或大量独立网络重复的结论。
