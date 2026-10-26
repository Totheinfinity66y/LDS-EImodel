# 方法与复现

## 数据与独立性

正式数据为本地 v2 三编码 baseline，各 24 条 L/D/S 条件、663 时间点、132 神经元；dt=5 ms，0–3310 ms。8 个决定动力学的源文件与归档 SHA256 一致。标准化数据保留 labels、E/I、群体/分支、事件、配置、派生种子及来源哈希。rate 是无量纲 [0,1]，不是 Hz。input_currents 从 encoded 输入和 sample 时序重建，行含义为积分至该时刻的电流。全轨迹无删静息神经元。

baseline 确定性条件没有置信区间。噪声数据为同一固定网络的独立输入噪声 realization（seeds 7/11/19），不是三个独立网络。扰动 seed 指不同方向，不将相邻时间点或所有位置视为独立生物学重复。不报告无重复支撑的 p 值；720 位置置换只描述固定六点几何的标签置换尾部比例。

## 群体活动、招募与选择性

减去每 trial 实际 t=0 向量，active 定义为增量 >0.1。阶段均值取 (readout−20 ms, readout]。报告群体 mean、peak、基线增量、active fraction 与 total。功能参与矩阵在该分支所有六位置条件中任一越阈值即参与；结构矩阵仅标记固定连接中分配给该 Response 分支的六坐标，不包含共享 Y、memory、I。因此全网络功能支持比结构块大是预期现象，不能将二者不同当成额外涌现模块。

参与率 PR_activity=(Σa)²/Σa²；Jaccard=交集/并集；cosine 使用分支平均活动。均衡 6×2×2 条件均值作正交 factorial 分解 L、D、S、LD、LS、DS、LDS，效应平方均值占总条件方差；零方差单元的份额为零且保留原方差字段。它是描述性分解，不是显著性检验。

记忆强度取群体 max。Response onset/stabilization 为许可后第一次达到0.1/0.9；memory decay onset/half/baseline 为许可后第一次低于交接前峰值的95%/50%以及绝对0.05。half_life_from_decay 是50%与95%交叉之差，不能当作指数拟合的生物半衰期；未交叉写 NA。规则信息另看条件质心距离与独立条件probe，不能只用群体平均率推断。反馈和tonic消融及各反馈随机边对照从原全率归档复用，行为准确率一起保存。

## PCA、子空间与几何

全局 PCA 每编码独立拟合：全部24条件、全部132神经元，每4个时间点均匀采样，统一减训练样本均值。所有轨迹在同一套轴中投影；不逐trial拟合。变量投影使用 L 的 cos/sin 与 D/S 编码，对时间平均状态作联合最小二乘并归一化系数轴；仅描述性，不叫 dPCA。噪声单trial和对齐均值使用 baseline 同一 PCA。

阶段和分支各自中心化 SVD：奇异值 s、VAF=s²/Σs²，有效维数 PR=1/ΣVAF²，90%/95%维数为累积阈值。数值rank依 max(shape)·machine_epsilon·s_max。基 Q 的角度为 arccos(SVD(QaᵀQb))；投影重合=||QaᵀQb||F²/min(ka,kb)，距离=√(ka+kb−2||QaᵀQb||F²)。cross VAF=||X_centered Q||F²/||X_centered||F²，两个方向分别保存。

全状态分支比较使用同一132坐标。结构控制将当前阶段不同 branch 的六位置折叠到共同六坐标；这会有意移除branch身份，不能当作真实跨脑神经元配准。另报告互不重叠的结构支持。L奇偶拆分仅检验不同位置采样敏感性；独立噪声seed稳定性在相同条件/坐标、每侧95%VAF基上估计。R1含未固定D/S的记忆方差，R2含S方差，不能对它们套六位置rank≤5；固定DS的六均值中心化才有此上限。

固定同一branch，六位置按实际当前输出分组，取132维均值；Euclidean原尺度、cosine和逐向量中心化correlation距离分别计算。独立当前Response与全部Response对照排除共享Y和旧阶段。理论环距离 min(|i−j|,6−|i−j|)，chord=2sin(πd/6)。Spearman在容差内并列秩；等距非对角矩阵相关性 undefined/NA。邻居正确率对并列候选分配fractional credit（等距chance=2/5），同时报告相对距离差，防止微小尾迹被高rank相关夸大。

经典MDS用 −HD²H/2 的前两正特征轴，stress=√(Σ(D−Dhat)²/ΣD²)。二维形状有旋转/镜像/尺度局限，六个离散点不证明连续流形。720种位置标签置换完整枚举。群体平方距离贡献用于定位微弱距离差来源。

## 解码

nearest-centroid线性probe使用两折分层条件拆分；同一L/D/S的所有重复留在同一fold。全部类别训练/测试覆盖；零距离并列给fractional credit。报告L chance1/6、D/S chance1/2；current location与branch仅在四个读出窗定义，不给transition伪造真值。全网络、Response、memory及各branch分别评价；cross-temporal全网络train-time×test-time使用相同隔离fold。probe只拟合离线读出，不训练或写回神经模型；结果只对应固定任务条件组合的有限外推。

## 动力学、扰动与向量场

72个既有快照覆盖三编码、六L、四阶段，历史固定D=+1,S=1；未覆盖所有branch的吸引域。完整率与clock复制到隔离模型，sample关，延长2000 ms；保留snapshot clock的强迫条件和撤clock保留tonic的自主条件分别测试。撤所有任务输入但保留规定背景与后者数学等价，不伪装成不同实验。

连续场 f(r)=[−r+clip(W_signed r+b+c−theta,0,1)]/tau；保存L2/max残差。解析piecewise Jacobian J=(−I+diag(phi′)W_signed)/tau，Euler F映射为I+dtJ；报告完整谱、max Re(lambda)与rho(I+dtJ)。clip拐点用对称导数0.5并计数，局部谱不是全局非线性稳定性证明。稳定候选必须结合残差、状态身份与扰动恢复，不由投影聚类判定。

从已稳定的自主端点开始，full、all Response、当前活动branch、未选branch、E、I六类目标，幅度为目标单元内RMS .02/.1/.3/.7，seeds7/11/19，高斯后裁剪[0,1]；记录实际全状态剂量。当前branch由活动判定，不查真实标签。R1无未选branch时明确NA。864条full轨迹复用，新增4320个目标条件，其中216为NA；有效独立方向条件4968。原状态与对照全N距离、归一化距离、max误差、恢复时间、switch及最终身份保存。恢复要求max误差<.02且原Response branch/位置一致、峰>.2；共同静息从不算恢复。恢复时间为最后一次越界后的持续阈值满足时间。

cross-temporal距离选择full幅度.3 seed7，控制几乎是固定点，因此条带并非动态轨迹吸引。13×13局部截面取同阶段六自主端点的前两PC，反投影后裁剪合法状态，评价完整f再投影，同时记录平面外范数。该图只是局部切片；固定点残差用完整状态。随机初态每seed在相同方程下重复引用，不当作每个快照新的独立初态；图中端点去重。

## 图源、版本与复现

每张图有300 dpi PNG、SVG和PDF；figure_manifest记录输入、代码hash、metric路径、参考文献ID、窗口和预处理。DATA_AUDIT、FIGURE_REFERENCES、config/analysis.json、manifests/analysis_source_hashes.json是完整溯源的一部分。论文原图仅供核验，不当作本模型图。文件完整性与人工视觉QA分别记录。

```powershell
$env:PATH="C:\Users\Totheinfinity\.conda\envs\analysis\Library\bin;"+$env:PATH
& C:\Users\Totheinfinity\.conda\envs\analysis\python.exe -m handcrafted_ei.visualization.plot_all --input handcrafted_ei/artifacts/v2/run --output artifacts/neural_representation_v2 --formats png,svg,pdf
```

也可在已激活兼容环境中执行相同的 `python -m` 命令。支持--figures 1,3,6、--encoding ring、--force。缓存按分析代码与原始归档hash确定，动力学原始输入逐个匹配历史index，输出有hash，缺失/损坏重新生成。测试命令为 `python -m unittest discover -s handcrafted_ei/tests -v`，文件QA为 `python -m handcrafted_ei.visualization.quality_check artifacts/neural_representation_v2`。

## 独立噪声试次解码补充

另用相同sigma=.03的三seed完整24条件记录，leave-one-noise-seed-out训练两个seed/测试另一个seed。验证实验seed与全部72个trial噪声seed不重叠、坐标/时序/条件顺序一致。它是已见任务条件下的噪声重复，不是OOD；不与严格条件留出混合。保留每seed的准确率而不虚构独立fold置信区间。记忆幅度终止不意味着信息擦除。
