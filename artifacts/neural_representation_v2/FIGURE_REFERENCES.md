# 绘图文献核对与方法来源

核验日期：2026-10-26。A–I 对应任务书顺序。以下区分原文图注核对、原图视觉核对和本项目方法选择；参考文献结果不构成本模型的证据。图中的数据必须来自本项目归档的实际神经状态。没有复制原作者数据或将论文图片作为模型结果。

Nature HTML 多次跳转到身份验证页；能读到的官方索引/图注、官方原图及作者公开 PDF 互相核对。网页可读不等于下载到的文件有效：一次 Gallego PDF 下载实际为 3 KB 验证 HTML，已排除，不作证据。原图核验材料在 `reference_evidence/`，机器可读来源与本项目 Figure 对应关系见 `config/references.json`。

## A · Kobak 等，2016

**Demixed principal component analysis of neural population data**。Dmitry Kobak、Wieland Brendel、Christos Constantinidis、Claudia E. Feierstein、Adam Kepecs、Zachary F. Mainen、Xue-Lian Qi、Ranulfo Romo、Naoshige Uchida、Christian K. Machens。DOI：[10.7554/eLife.10989](https://doi.org/10.7554/eLife.10989)。

- **已核对图注与原图**：[Figures](https://elifesciences.org/articles/10989/figures)，[正式 PDF](https://cdn.elifesciences.org/articles/10989/elife-10989-v2.pdf) 的第 3、5、7、14 页。
- **具体 panel / 数据**：Fig.1b 为四个代表 PFC 神经元的条件平均 PSTH，颜色编码 F1、线型编码决策；1g 为回归系数分布；1i 为 PCA 累计方差；Fig.2b/d/f 分别解释 LDA/PCA/dPCA 投影；Fig.3b 为各 marginalization 的条件轨迹、3c 为累计 VAF、3d 为方差组成；Fig.7a 是 dPCA **encoder** 权重分布，7b 是权重空间密度峰聚类，不能称为单元响应直方图。
- **布局与借鉴**：共享时间轴、小倍图、条件颜色/线型、谱与投影并列；用于本项目 Fig.1/2/4/5/7。条件差异投影可作为可解释的描述性替代，但必须使用实际方法名称，不能标作已实现 dPCA。
- **不适用**：原文 ANOVA 显著性、单试次分类区间及噪声方差扣除依赖真实重复；不能移植到 24 个确定性条件上。dPCA 权重的连续分布也不能预设为 handcrafted 网络的结果。公开分析代码：[machenslab/dPCA](https://github.com/machenslab/dPCA)。

## B · Churchland 等，2012

**Neural population dynamics during reaching**。Mark M. Churchland、John P. Cunningham、Matthew T. Kaufman、Justin D. Foster、Paul Nuyujukian、Stephen I. Ryu、Krishna V. Shenoy。DOI：[10.1038/nature11129](https://doi.org/10.1038/nature11129)。

- **已核对图注与原图**：[原文及图注](https://pmc.ncbi.nlm.nih.gov/articles/PMC3393826/)，[Fig.2 官方原图](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fnature11129/MediaObjects/41586_2012_Article_BFnature11129_Fig2_HTML.jpg)，[Fig.3 官方原图](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fnature11129/MediaObjects/41586_2012_Article_BFnature11129_Fig3_HTML.jpg)。一次期刊 PDF 下载是期刊网页的打印 PDF，含文字占位图，不能当成原稿图像证据。
- **具体 panel / 数据**：Fig.2 是 10 个代表运动/前运动皮层神经元、多 reaching 条件的平均率轨迹，事件分别对齐；Fig.3a–f 是六套记录数据在 jPC 平面的群体轨迹，每条线一个条件，圆点标准备状态，颜色由准备状态投影确定。
- **数学、布局、用途**：原文先降维，再以反对称动力学拟合得到 jPCA；借鉴多条件共用投影、初态标记和时间方向，用于本项目 Fig.4。普通 PCA 与 jPCA 的目标函数不同，图例必须说明实际方法。
- **不适用**：本模型不预设旋转；不得强制拟合 jPCA 后凭漂亮环线声称旋转机制。原文 reaching 数据与神经元数量不作为本模型的对照样本。

## C · Mante 等，2013

**Context-dependent computation by recurrent dynamics in prefrontal cortex**。Valerio Mante、David Sussillo、Krishna V. Shenoy、William T. Newsome。DOI：[10.1038/nature12742](https://doi.org/10.1038/nature12742)。

- **已核对图注与原图**：[PMC 原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4121670/)，[Stanford 公开原稿及补充](https://web.stanford.edu/class/psych209/Readings/ManteEtAl13ContDepCompWithSupp.pdf) 第 3–5 页。
- **具体 panel / 数据**：Fig.2a–f 是 PFC 活动在 choice/motion/colour 任务轴上的轨迹；Fig.3a–d 是实验现象与三种选择机制的**概念示意**；Fig.4 是经训练的 recurrent rate 模型架构；Fig.5a–f 是模型轨迹及在固定 context、无感觉输入条件下求得的固定点和局部近零特征向量。
- **数学、布局、用途**：原文 PCA 去噪加多变量回归构建任务轴；同一投影跨 context 比较，配起止标记与轴比例。用于本项目 Fig.2/4/7/8；L 是六类循环位置，宜用类别或 sin/cos 轴，不能把 0–5 当无周期连续量。
- **不适用**：不得导入训练或把原文 line attractor 结论套用于本网络。正交化的任务轴是分析选择，不是自发产生正交性的证据；简化条件差异轴应明确区别于完整 TDR。

## D · Gallego 等，2018

**Cortical population activity within a preserved neural manifold underlies multiple motor behaviors**。Juan A. Gallego、Matthew G. Perich、Stephanie N. Naufel、Christian Ethier、Sara A. Solla、Lee E. Miller。DOI：[10.1038/s41467-018-06560-z](https://doi.org/10.1038/s41467-018-06560-z)。

- **已核对**：[官方 PDF](https://www.nature.com/articles/s41467-018-06560-z.pdf) 第 5 页图注与[官方 Fig.3 原图](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41467-018-06560-z/MediaObjects/41467_2018_6560_Fig3_HTML.png)。
- **具体 panel / 数据**：Fig.3a 是同一 M1 群体在不同任务的 PCA 子空间 principal-angle 谱；3b 汇总显著相似模式数量；3c 是 across-task / within-task VAF 比及随机子空间对照。布局为角谱、计数、VAF 三组并列。
- **数学与用途**：正交基交叉乘积的奇异值给出夹角；将一组数据投影到另一组的基，测 VAF。用于本项目 Fig.5/10，必须保持同一神经元坐标并说明中心化、rank、阈值及 VAF 分母。
- **不适用**：原文 12-D、tensor maximum entropy 显著性阈值均不能照搬。不同模型若单元身份不匹配不能直接求角度；本项目 branch 坐标块导致的正交应配结构支持基线与移除支持差异后的比较。

## E · Kriegeskorte、Mur、Bandettini，2008

**Representational similarity analysis – connecting the branches of systems neuroscience**。Nikolaus Kriegeskorte、Marieke Mur、Peter Bandettini。DOI：[10.3389/neuro.06.004.2008](https://doi.org/10.3389/neuro.06.004.2008)。

- **来源**：[正式全文和图注](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/neuro.06.004.2008/full)，[Fig.2 原图](https://www.frontiersin.org/files/Articles/249/fnsys-02-004/image_n/fnsys-02-004-g002.gif)。
- **具体图 / 数据**：Fig.2 展示条件活动模式两两比较形成对称、零对角 RDM 的流程，主要距离为 1−Pearson correlation；Fig.4 是 96 个视觉物体条件的非度量 MDS，行区分 EVC/FFA、列区分距离；Fig.10 比较距离选择形成的 RDM。
- **数学、布局、用途**：只比较 RDM 非对角上三角；距离矩阵与二维图并列，MDS 报告 stress。用于本项目 Fig.6/10，保留 Euclidean 主分析及 cosine/correlation 补充；六位置跨模型可比较 RDM 而不要求神经元逐一匹配。
- **不适用**：本项目不继承 fMRI 被试 bootstrap/显著性；常数非对角 RDM 的秩相关必须 undefined。MDS 外观、旋转镜像不确定性及二维失真不能证明连续环流形或吸引子。

## F · Seelig、Jayaraman，2015

**Neural dynamics for landmark orientation and angular path integration**。Johannes D. Seelig、Vivek Jayaraman。DOI：[10.1038/nature14446](https://doi.org/10.1038/nature14446)。

- **已核对图注与原图**：[期刊页](https://www.nature.com/articles/nature14446)，[高校公开原稿](https://neuroscience.stanford.edu/sites/default/files/seeligjayaramannature2015_14446.pdf) 第 2、5 页。
- **具体 panel / 数据**：果蝇椭球体 calcium imaging；Fig.1f/g 是实际活动图像和 wedge/PVA 构造，1h/i 是展开的角度×时间热图及 PVA 对照视觉线索；Fig.4a–d 展示全暗条件活动与旋转，4e–g 是停止/行走期间 bump 持续，4h/i 量化停止前后方向与漂移。
- **数学、布局、用途**：向量加权圆均值、角度展开与周期坐标；同步热图/角位置/事件。用于本项目 Fig.1/6/8 的位置分布、时间保持展示。
- **不适用**：本模型率不是钙荧光，不能标 ΔF/F 或套荧光时间尺度；只有六个离散位置，周期输入与活动峰不是连续环吸引子的充分证据。

## G · Inagaki 等，2019

**Discrete attractor dynamics underlies persistent activity in the frontal cortex**。Hidehiko K. Inagaki、Lorenzo Fontolan、Sandro Romani、Karel Svoboda。DOI：[10.1038/s41586-019-0919-7](https://doi.org/10.1038/s41586-019-0919-7)。

- **来源**：[正式网页与扩展图注](https://www.nature.com/articles/s41586-019-0919-7)，[Fig.1 官方原图](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-019-0919-7/MediaObjects/41586_2019_919_Fig1_HTML.png)，[Fig.5 官方原图](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-019-0919-7/MediaObjects/41586_2019_919_Fig5_HTML.png)。
- **已视觉核对 panel**：Fig.1b 对比单元衰减、连续积分器、移动单吸引子、多离散吸引子的保持与干预；Fig.5a 单元 raster/PSTH；5b–d 为正常、干预正确、干预错误的 coding-direction 轨迹及中期/末期分布；5e 合并轨迹，5f 相位线，5g 中期至末期扰动差。
- **已核对扩展图注和原图**：[ED1](https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41586-019-0919-7/MediaObjects/41586_2019_919_Fig7_ESM.jpg) 的 b–h/i–o/p–v 分别为连续/移动/离散模型的轨迹、末态分布、恢复与 phase line；[ED6](https://media.springernature.com/lw685/springer-static/esm/art%3A10.1038%2Fs41586-019-0919-7/MediaObjects/41586_2019_919_Fig12_ESM.jpg) 的 b/m 是 fit/test 半试次 CD 时间稳定性，e–h/p–s 末态分布，j–l/u–x 是干预前解码筛选后的轨迹、phase line、期中/末期差。它不是单纯的 PCA 轨迹图。
- **用途和边界**：本项目 Fig.8/9 将延长演化、完整残差、固定外驱条件、Jacobian、身份保持及扰动恢复并列。原文投影相位线不替代本网络完整状态稳定性检验；共同衰减到静息、单次恢复或类群聚类不能单独判定吸引子。

## H · Zhou 等，2023

**Multiplexing working memory and time in the trajectories of neural networks**（正式题名）。Shanglin Zhou、Michael Seay、Jiannis Taxidis、Peyman Golshani、Dean V. Buonomano。DOI：[10.1038/s41562-023-01592-y](https://doi.org/10.1038/s41562-023-01592-y)。任务书与 [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10913811/) 的 *encoding retrospective and prospective information in neural trajectories* 是作者稿题名，不能因此当作另一篇论文；PMC 公开于 2024，不是论文发表年份。

- **已核对原图与图注**：[作者实验室正式 PDF](https://www.buonomanolab.com/Publications/ZhouBuonoNatureHumanBehaviour2023.pdf) 第 10 页；[期刊记录](https://www.nature.com/articles/s41562-023-01592-y)。
- **具体 panel**：Fig.7a 左侧十个单元黑/红正常/受扰率，右侧 PCA 三维轨迹与时间球；7b 是正常与受扰轨迹的 cross-Euclidean distance；7c 左侧是 17 个独立训练 RNN 的平均同时间距离±SEM，右侧为晚期距离分布。
- **数学、布局、用途**：原始状态距离矩阵及对角线恢复，区分同时间恢复、路径时移和平行偏离；用于本项目 Fig.9。展示投影共享 PCA，判据使用完整空间。
- **不适用**：本网络不训练，不能照搬 17-RNN SEM 或“训练涌现”。本任务若使用多个扰动 seed，误差描述的是扰动 realization，不是网络群体。公开代码：[BuonoLab/Timing-WM_RNN_2022](https://github.com/BuonoLab/Timing-WM_RNN_2022)。

## I · Langdon、Genkin、Engel，2023

**A unifying perspective on neural manifolds and circuits for cognition**。Christopher Langdon、Mikhail Genkin、Tatiana A. Engel。DOI：[10.1038/s41583-023-00693-x](https://doi.org/10.1038/s41583-023-00693-x)。

- **来源**：[公开作者稿](https://pmc.ncbi.nlm.nih.gov/articles/PMC11058347/)；已查看 [Box 1 原图](https://cdn.ncbi.nlm.nih.gov/pmc/blobs/039a/11058347/5232f649a202/nihms-1985044-f0004.jpg)；Fig.1 的具体描述来自原图注，未单独视觉核验 Fig.1。
- **具体概念图**：Box 1 区分任务变量、单元 tuning、N 维状态轨迹、非线性流形嵌入；Fig.1a–c 连接头方向变量、实测 ring activity 与假设电路。这些是综述组织与部分重绘图，不是新模型实验证据。
- **用途**：作为全部图及总结的术语审查，明确线性子空间≠非线性流形、几何描述≠因果电路、输入相位维数≠神经活动 rank、持续状态≠自治吸引子。
- **不适用**：不能把综述对 low-rank 电路的讨论变成本模型结构约束；本项目固定连接与局部支持矩阵是已知先验，需要干预证据才能进一步谈动力学贡献。

## 本项目 Figure 方法对应

| 本项目图 | 直接方法/布局参考 | 自有机制或补充 |
|---|---|---|
| 1 全活动 | A 1b；B 2；F 1h/i | 全 E/I 单元、绝对/基线扣除率 |
| 2 招募与选择性 | A 1g/7a；C ED3 | structural support 对 functional recruitment |
| 3 记忆交接 | A 1b/3b | Response→I_decay 反馈及匹配干预 |
| 4 状态轨迹 | B 3a–f；C 2a–f；A 2/3b | 全网络共用 PCA；条件差异轴 |
| 5 子空间 | D 3a–c；A 1i/3c | 结构坐标 null、去支持后的几何 |
| 6 六位置 | E 2/4/10；F 1/4 | 等距退化、离散环距离、置换对照 |
| 7 信息 | A 12；C ED3/TDR | 独立划分；不足时描述性 separation |
| 8 稳态候选 | G 1b；C 5a–f | 完整状态残差、固定外驱及 Jacobian |
| 9 扰动 | G 5b–g/ED1；H 7a–c | 全状态恢复、身份保持及投影外运动 |
| 10 三编码 | 上述方法的统一比较 | 归一化维数，NA，不构造最佳评分 |

## 代码和复制边界

本项目分析代码为独立实现；本文件记录思想、数学定义与布局来源，没有移植第三方库代码。引用 dPCA/TDR 文献不等于实现其完整算法。若后续直接复用公开代码，应额外记录仓库 commit、文件与许可证。全部参考原图只作为内部核验材料，不能混入 `figures/` 模型结果。
