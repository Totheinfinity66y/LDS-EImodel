# Figure 4/5 实图预审

专家 `inagaki_v3` 实际打开 `fig04_one_hot_decompression_trajectories.png` 与 `fig05_one_hot_branch_subspaces.png`。此为首次图像预审；后续重导出的图片须按新 SHA256 复查，不能自动沿用该状态。

## Figure 4

四组 fixed-L branch-discriminant 轨迹可区分，R2/R3/R4 小图共用坐标；全局 PCA 的轨迹重叠应保留，它反映该投影的遮蔽而非数据缺失。线宽、背景、轴和全状态速度单位可读。

需修：速度 panel 的 gate/readout/retire 目前仅不同虚线，没有文字或 legend 解码；readout 四种 shape 也需 legend 指明 1–4。与 Mante 原图的关系是固定轴、稀疏轨迹和条件比较的方法适配，轨迹真实形状不要求相似。

## Figure 5

主图已用逐维主角度谱而非平均热图；C 明确标 captured target variance fraction，避免冒充 Gallego across/within VAF ratio。R3 分支在全局 PC1/PC2 中大量重叠，只见少量轮廓，因此 A 图应明示 projection overlap；不能由视觉重叠否认全空间 branch 分离。

需修：folded distance 的自动纵轴为 1e-17 数值量级，应标 numerical zero 并采用不夸大浮点噪声的尺度。D panel 的分支对颜色需注明沿用 B legend。R1–R4 Response-only 的早期角度不单独表示 R3 branch 已形成，应在 caption 解释。

本预审不评价尚未生成的 Figure 8，也不替代独立数值验收。
