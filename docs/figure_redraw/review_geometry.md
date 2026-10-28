# Figure 4–7 独立数值与视觉审查

审查日期：2026-10-28。审查者 `/root/fig01_03` 未参与 Figure 4–7 实现；未改这些图的数据计算器或 renderer。独立验算程序及完整输入/输出 SHA256 分别为 `artifacts/neural_paper_figures_v1/manifests/review_geometry.py` 和 `review_geometry.json`。

## 数值结果

使用已实测的 analysis Python 3.12 / NumPy 2.3.5 / SciPy 1.16.3 环境执行独立程序，读取三编码各自的 REC 与 metadata，再读 Figure 4–7 新派生文件。程序不导入生产 figure_data 或 rendering 实现，也不调用生产 probe、basis、PCA 函数。

| 检查 | 独立方法 | 三编码结果 |
| --- | --- | --- |
| 24 trial 共享 PCA scores | 对全体原始 rates 用归档 center/components 直接 einsum；对归档 fit-time 集协方差独立 eigh，与 PCA 子空间、EVR 比较，不要求任意特征向量符号相同 | PASS，投影最大误差 `4.440892098500626e-16` |
| 全状态速度 | 对相邻 132 维 rates 差求欧氏范数，再除每个实际时间差 | PASS，最大误差 `0` |
| 三 scope 时变秩和 NA | 663 个实际时间点 × whole/response/shared，逐分支中心化后用 SciPy SVD 重算秩；方差不足或零秩时要求角谱全部 NaN | PASS，每编码 24 个比较为 undefined，未填零 |
| 时变 principal angles | 用独立 SciPy `subspace_angles`（稳定的 sin/cos 联合法）与生产 acos-SVD 角谱比对 | PASS，最大差 `3.1945283931956693e-6` 度，角容差 `1e-5` 度；零角附近 acos 数值精度解释此差 |
| R3 决策窗 6 pairs × 3 scope 完整角谱 | 从各 branch 的六条件状态重新中心化、求基、计算全部角，未混坐标或只核对均值 | PASS |
| 双向 cross-VAF | 使用 `1 - ||X - XQQᵀ||²_F / ||X||²_F` 独立算两个方向，对照 CSV | PASS |
| 六位置 RDM | 从真实 20 ms 决策窗均值状态，逐对循环算欧氏距离，分别使用全 132 维和 Response 索引 | PASS；PCA 散点的归档中心/投影另核对 |
| Branch decoder folds | 24 个唯一 LDS tuple；训练/测试索引无交集、内部无重复；每 fold 两边四类齐全 | PASS，两个 folds 均 4/4 类 |
| Branch probe accuracy | 手动按归档 splits 构造四类质心并独立计算距离及 tie fractional credit；R3 transfer 前要求 NaN | PASS，与新 NPZ 最大差 `0` |

验算覆盖三编码完整数组，不只是代表 trial。within-VAF 指 full retained numerical rank；没有把不同 branch 各自坐标的方差当共享投影 cross-VAF。确定性条件没有被当成 bootstrap 重复。

## 实际视觉检查

本轮通过 `view_image` 实际逐一打开 one-hot 的 `fig04_one_hot.png`、`fig05_one_hot.png`、`fig06_one_hot.png`、`fig07_one_hot.png`。四图均无空白 panel 或坐标裁切，图例、色标及不同问题的分隔可读。

- F4：全程轨迹和三个 stage 小图使用同一归档 PCA 基；stage panel 使用同一全程轴范围。R4 在前两个全局 PC 上接近投影塌缩是实际数据，不等于 132 维无状态差异；图中独立全状态速度提供补充证据。D panel 明标 descriptive regression axes / no dPCA。
- F5：完整六对角谱、双向 cross-VAF、三个 scope 的时变角与质心距离都分别呈现；结构支持为零且 folded overlap 为一的对照可见，不能把约直角完全归因于动力学涌现。
- F6：六真实点没有连成环、没有强制规则六边形；RDM 热图保留，Response-only 与 whole 使用相同色标；六条位置峰值/裕量因对称机制重合，没有为了可见度添加伪偏移。该有限窗口保持不自动证明自治吸引子。
- F7：baseline condition-held-out 与 held-out noise realization 分开，chance 线分别明确；四类 branch 在 transfer 前不显示假准确率；低 baseline 分支probe结果没有被高 noise-repeat 结果掩盖。

其他编码的数值已经完整验证；本文件只声明实际打开 one-hot 四图，不把它扩充为已看三编码十二图。

## 原方法和结论边界

本轮核对 [Kobak et al. 2016 原文](https://elifesciences.org/articles/10989)：其 dPCA 使用任务参数 marginalization 和 reduced-rank encoder/decoder 重建目标；普通 PCA 的重建目标不含任务参数。当前 F4 的整体 PCA 与独立任务回归轴没有执行该 dPCA 目标，因此图注正确称 PCA / descriptive regression，不能称 Kobak dPCA 的数值复现。

[Churchland et al. 2012](https://www.nature.com/articles/nature11129) 的题名、DOI `10.1038/nature11129` 和来源身份由期刊索引本轮核对。直接全文访问遇验证码/429，未取得或实际打开其原 Fig3；本轮不声称已视觉核对该原 panel。当前图只执行协方差 PCA，没有拟合旋转动力学或反对称速度映射，不支持把曲线称为 jPCA、旋转模式或该论文的 source-exact 图形复现。

F5 的 principal angles 和 cross-VAF 是当前条件矩阵的数学量；F6 是六个离散位置；F7 是固定网络条件和输入噪声的探针。没有训练、学习泛化、生物学重复、连续环流形或全局 basin 结论。

裁决：**F4–7 数值 PASS；one-hot 四图视觉 PASS；文献方法映射 PASS_WITH_LIMITS（METHOD_ADAPTED）**。没有发现阻塞计算缺陷。原论文 exact-panel 视觉对照的未完成部分如上披露，不与本轮 LDS 数值验收混合。
