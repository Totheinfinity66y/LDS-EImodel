# Paper2Skill 组装包独立复核

审稿人：Agent F（未参与论文包转换、adapter、数值实现或绘图）。

独立调用现有 `paper2agent-test/python.exe`，确认PyMuPDF1.28.2后，分别真实运行 `paper_bundle.py verify --work audit/paper2agent/{zhou,inagaki}/paper-review --strict`。两次命令均完成，exit0。独立stdout存于本目录 `zhou_strict.json` / `inagaki_strict.json`。Zhou为reviewed，0 adjudication；Inagaki为reviewed_with_limitations，33 fingerprint裁定、0 stale、mechanical_ok=true。fontTools缺失警告仍存在，未安装依赖。

本人的视觉复核是抽样fresh verification，不冒签原专家的全页审阅。全页覆盖证据分别为Zhou的18页SOURCE_REVIEW_COVERAGE.json和各page review_notes、Inagaki的30页plan/page review_notes；strict检查确认全部页reviewed。覆盖登记不是本人重新阅读全部48页。

本人实际打开并比较的关键内容：

- Zhou最终组装包Figure7 JPEG与源PDF第10页预览：a为10单元轨迹和3PC轨迹、时间球；b为cross-Euclidean；c为17网络均值/SEM和箱须。包中小标签与caption一致；Figure7并没有velocity-field panel。
- Zhou源第13页Methods与组装包可检索正文：π/第17输入、0.25、首cue后500ms、50ms、同一units×time noise矩阵。维数方法为256×320，95%variance；不把这当LDS数据格式。
- Zhou源第1页与最终摘要JPEG：标题、作者、20April2023和摘要文字保留；没有把hidden占位日期作为事实。最终reporting-field-checkboxes图保留Behavioural/social sciences选中；源第18页所有材料/方法N/A框清晰，不解释为空值表格。
- Inagaki最终Figure5 JPEG：spike rasters、CD、端点分布、phase line和session统计可辨。源第5页Figure6/caption和最终paper.md共同确认stationary/random-delay科学语义。源第30页与最终reporting-summary-page-2 JPEG：Life sciences与animal选中，其余N/A、样本量等文字保留。没有丢弃checkbox意义。
- 仅通过最终paper.md检索回答：Inagaki实验CD最后600ms与simulation最后400ms并非同一拟合窗；Zhou冻结噪声是配对相同随机实现，LDS零数组只是明确的noise-free adaptation。

结论：组装阅读包关键内容及机械完整性独立通过，Inagaki保留image-only/字体解析限制。此结论不验证原论文实验数据、训练权重或作者完整Figure执行。缺原数据/权重/MATLAB runtime时，原结果精确复现仍BLOCKED；Paper2Skill没有内建自动LDS图片审稿API。
