# Figure 1–7/10 一致性审计

本审计复用已有正确的共享PCA、子空间、RSA、解码实现与历史图，不将正确图重复开发为另一套算法。数值独立复算入口为 `python -m handcrafted_ei.evaluation.reference_consistency`。

| Figure | 方法与验收 | 结论与限制 |
| --- | --- | --- |
| 1 | 全132状态、真实群体/基线、无量纲率、完整图像hash | PASS；静息神经元保留 |
| 2 | 实际阈值招募、结构支持、balanced factorial effects | ADAPT；描述性ANOVA不是统计重复或dPCA |
| 3 | 真实时钟窗口、M_D/M_S交接、独立因果对照 | PASS_WITH_LIMITS；残余可解码不等于记忆未衰减 |
| 4 | 24条件统一全网络PCA，center与fit stride固定 | ADAPT；不是Churchland jPCA或Mante targeted-dimensionality reduction精确复现 |
| 5 | 独立SVD维数、SciPy principal angles复算，与历史CSV断言一致 | PASS_WITH_LIMITS；分支Response支持先验不相交，折叠坐标控制不可叫真实配准 |
| 6 | current-Response六位置距离独立重算，全网络/R3分离 | PASS_WITH_LIMITS；R3等距相关undefined，微弱全网络环相关不证明环吸引子 |
| 7 | 条件留出与leave-noise-seed-out分开、probe只读 | ADAPT；线性变量轴不是Kobak dPCA；没有新增训练模型 |
| 10 | 维数/角度复算、全部24终点新指标 | UPDATED；旧动力学六位置子集指标不再外推为全分支 |

三编码R3分支内whole有效维数约4.99999945，数值rank5；Response-only不同分支角度90°为不相交handcrafted坐标的直接后果。whole分支平均角约83.38083°，见逐对数值CSV，不能声称涌现正交。所有六位置current-R3非对角距离等距，不支持连续环流形。全网络微弱拓扑距离差需同时看旧 `rsa_population_contributions.csv` 中的Y/尾迹贡献，不能仅凭Spearman接近1下结论。

历史图及原始raw档案保持不变，路径在 `artifacts/neural_representation_v2/figure_manifest.json`。两篇核心论文的正式反向审查只认证新增8/9适配，补充文献映射属于方法一致性审计，不宣称复现这些论文全部实验。
