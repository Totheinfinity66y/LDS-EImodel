# Figure 1–10 科研重绘交付索引

## 图片与计算产物

主图使用one_hot，三编码共享分析协议；Figure10为三编码综合图。每幅同时提供PNG300dpi、SVG、PDF、完整图注。所有图片均使用真实轨迹，没有改模型、训练或改变原有任务；历史归档保留。

1. [Figure1：时间活动组织](../../artifacts/neural_paper_figures_v1/figures/main/fig01_one_hot.png)。单条件R1–R4、Memory–Gate–Decay、六位置选择性与E/I比例。
2. [Figure2：分支路由](../../artifacts/neural_paper_figures_v1/figures/main/fig02_one_hot.png)。结构先验、候选分支动态、六单元调谐和泄漏；R1无竞争者为NA。
3. [Figure3：记忆交接](../../artifacts/neural_paper_figures_v1/figures/main/fig03_one_hot.png)。真实率、平衡规则轴、feedback阻断/随机控制、可读出性；前后因果消融见derived/各编码/fig03_temporal_ablation.csv。
4. [Figure4：四阶段群体轨迹](../../artifacts/neural_paper_figures_v1/figures/main/fig04_one_hot.png)。共享PCA、真实时间顺序与完整状态运动，未实现jPCA/dPCA。
5. [Figure5：分支子空间几何](../../artifacts/neural_paper_figures_v1/figures/main/fig05_one_hot.png)。完整角谱、双向VAF、时变距离/角度、三种坐标及固定支持对照。
6. [Figure6：六位置表征](../../artifacts/neural_paper_figures_v1/figures/main/fig06_one_hot.png)。真实状态投影、RDM、位置保持，未预设环或正六边形。
7. [Figure7：L/D/S可读出性](../../artifacts/neural_paper_figures_v1/figures/main/fig07_one_hot.png)。条件留出、时间泛化与独立噪声协议分别报告；branch probe保留实际机会水平/低于机会水平结果。
8. [Figure8：固定分支六位置稳定态](../../artifacts/neural_paper_figures_v1/figures/main/fig08_one_hot_branch0.png)。真实有限扰动轨迹、完整状态残差、谱与折点证书。其他分支与编码有单独补图。
9. [Figure9：输入扰动与完整状态恢复](../../artifacts/neural_paper_figures_v1/figures/main/fig09_one_hot_source_time.png)。单元活动、control-only PCA、交叉时间距离、完整误差及独立state-kick恢复。
10. [Figure10：三编码共同坐标与电流匹配](../../artifacts/neural_paper_figures_v1/figures/main/fig10_encoding_comparison.png)。联合PCA与one_hot固定基、外部维度/实际神经调谐、几何与固定点指标、匹配电流恢复。

## 新实验及阴性结果

[Figure8六端点均值切片](../../artifacts/neural_paper_figures_v1/figures/supplementary/fig08_one_hot_sixmean_control_slices.png)保留预指定平面的阴性结果。每branch41×41网格只有144合法状态，全部进入其他平衡态，不代表六目标盆不存在。其余点因率范围非法而mask，未clip或虚构轨迹。

[Figure8三端点对比切片](../../artifacts/neural_paper_figures_v1/figures/supplementary/fig08_one_hot_three_endpoint_slices.png)是明确单独定义的平面。branch0有551合法初态，其中534进入其他平衡态，17个匹配所选三任务端点（6/6/5）。这只是该平面与有限时间内盆的交集，不能称完整六位置吸引盆或全局吸引子清单。完整初态、132维路径、分类、阈值与基均留存。

[Figure9分阶段扰动](../../artifacts/neural_paper_figures_v1/figures/supplementary/fig09_one_hot_stage_perturbations.png)覆盖24条件×三时段×三个固定方向，50ms实际电流RMS0.25。每时段72个条件/方向组合，四次输出全正确分别52、53、51；身份约束的完整状态恢复分别42、53、48。三编码在此协议下相同，不能声称随阶段单调增强或编码优劣。数据是确定性条件和固定方向计数，没有生物学重复/显著性。

Figure10另用RMS0.05/0.2/0.5的匹配full132电流；它与原始L坐标噪声分开。后者的原坐标和实际R1电流剂量保存在fig10_raw_noise_doses.csv，不直接比较不同维坐标的同一sigma。

## 证据与复现

- [任务拆分与验收条件](PLAN.md)、[数据契约](data_contract.md)、[独立计算方法与命令](../../artifacts/neural_paper_figures_v1/METHODS.md)。
- [数据审计](../../artifacts/neural_paper_figures_v1/manifests/data_audit.json)：72条REC轨迹与RAW逐值相同，8个受保护源码SHA匹配。
- [Figure1–3与Figure10实际开图记录](../../artifacts/neural_paper_figures_v1/manifests/fig01_03_10_visual_validation.json)、[Figure4–7独立原率复算](../../artifacts/neural_paper_figures_v1/manifests/review_early.json)、[Figure4–7独立数值审阅](review_geometry.md)、[Figure8–10独立数值与视觉审阅](independent_validation.md)。
- [Inagaki来源与实际图反审](review_inagaki.md)。原作者资料/运行时缺口与LDS适配分开，不声称source-exact复现。
- [全回归日志](../../artifacts/neural_paper_figures_v1/manifests/tests_full.txt)：79项通过。该回归不同于逐图独立验算。
- [综合manifest](../../artifacts/neural_paper_figures_v1/figure_manifest.json)索引逐图输入、源码、数值数组和输出哈希；大型全路径NPZ留本地，通过统一CLI重建，不提交受版权限制原图。manifest另记录326个产物文件与10个项目文档的SHA256，导出完整性见export_integrity.json（49个图版本/147个导出文件）。

每张图片的最终状态以独立审阅报告和manifest为准，文件存在不代替验收。没有改变冻结科学定义，也没有将活动衰减、投影重合、固定连接支持或单一Jacobian谱提升为超出证据的机制结论。
