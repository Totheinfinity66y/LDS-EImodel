# 文献方法复现与LDS可视化审计

入口：`python -m handcrafted_ei.visualization.plot_all --reference-grounded`。复用已存在analysis环境；不安装、不训练、不改模型、不覆写历史归档。

- [最终科研报告](FINAL_REPRODUCTION_REPORT.md)
- [独立评审](INDEPENDENT_REVIEW.md)
- [图注与协议](FIGURE_CAPTIONS.md)
- [数据适配](audit/SOURCE_TO_LDS_SCHEMA.md)
- [Figure1–7/10一致性](audit/FIGURE_01_07_10_CONSISTENCY.md)
- [最新综合图](figures/comparison/figure_10_audited.png)

三编码独立目录 `figures/one_hot`、`figures/ring`、`figures/topology` 均含Figure8、两种input Figure9、state/flow补图的PNG300dpi、SVG、PDF。`lds_results`含实际NPZ/CSV、配置、clip剂量、PCA/全状态、配对电流、身份及谱；完整basin大文件仅本地，按 `manifests/result_hashes.json` 索引。

原论文包、作者源码快照、原图三列内部对照本地留存；完整调用、源SHA、证据和四轮评审见仓库 `audit/paper2agent`。方法与数据的真实可比性优先于外观；精确源实验阻塞与LDS适配通过分别报告。
