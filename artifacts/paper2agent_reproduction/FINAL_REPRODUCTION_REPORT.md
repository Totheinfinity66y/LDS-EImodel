# LDS-EImodel 文献方法复现、数据适配及可视化审计报告

## 结论与验收范围

**两篇原论文的方法与数据契约已核验，LDS三编码的Figure8/9已实际重算、重绘并经过原论文专家反向评审，结论为 METHOD ADAPTED / PASS_WITH_LIMITS。原实验图的精确数值复现仍 BLOCKED，不能合并称“原论文复现成功”。**

没有修改模型方程、连接、参数、任务、编码或readout-first。所有新计算在独立状态数组上进行，历史raw和图不覆写。原始ZIP/protected source哈希与当前模型一致；已有无关PPTX改动排除在本任务提交之外。

两位独立专家以同一持久Agent分别完成四轮咨询及修复后复审，实际读本地Paper2Agent，执行真实Paper2Skill全链：Inagaki30页 `reviewed_with_limitations`，Zhou18页 `reviewed`，require-reviewed build及strict退出0。fresh reviewer另独立核对最终阅读包、关键原页和strict验证；其范围没有冒充重新逐页审完48页。论文包的局限不是LDS数学正确性的替代证据。

| 分类 | 实际达到内容 |
| --- | --- |
| METHOD REPRODUCED | 可追溯的CD/phase-line数学重建与合成测试、full-state Euclidean cross-temporal函数；Zhou未改作者task输入生成器实跑。非原实验数据复现 |
| METHOD ADAPTED | 132维全网络、24条件固定场、noise-free成对50ms输入、control-only PCA、三编码图 |
| DATA INCOMPATIBLE | 原ALM动物/session/试次统计；17独立训练RNN、原π通道/weights/raw；不能靠转换补造 |
| NUMERICAL ERROR FIXED | 补齐原流程缺失的全24条件、PCA能量闭合、clip剂量和折点稳定性充分证据。未发现旧Euler/Jacobian公式算错的证据，不虚构算术bug |
| VISUAL MISMATCH FIXED | 分开state/input/flow；纠正轴语义、实际剂量、完整状态误差、饱和尾迹缩放及折点谱标签 |
| SCIENTIFIC DYNAMICS DIFFERENT | LDS局部稳定点与clock驱动序列，不是原文受训网络的动态轨迹吸引；固定clock下代表输入扰动未恢复 |

## 证据入口与可复算性

- 来源能力及流程：[PAPER2AGENT_CAPABILITIES](../../audit/PAPER2AGENT_CAPABILITIES.md)、两专家 `audit/paper2agent/*/ORIGINAL_REPRODUCTION_REPORT.md`。
- 数据：[LDS_DATA_AUDIT](../../audit/data/LDS_DATA_AUDIT.md)、[schema](../../audit/data/DATA_SCHEMA.json)、[source-to-LDS](audit/SOURCE_TO_LDS_SCHEMA.md)。
- 数值：[独立D审计](../../audit/numerical/NUMERICAL_CONSISTENCY.md)、[生产数值汇总](manifests/numerical_summary.json)、各编码 `fixed_points.csv`、`basin.csv`、`input_summary.csv`。
- 图注：[FIGURE_CAPTIONS](FIGURE_CAPTIONS.md)，图像与来源见 [figure_manifest](figure_manifest.json)；每组PNG300dpi/SVG/PDF。共16组正式新图、48文件，另有2组三列内部对照，原图仅本地。
- 反向审稿：[Inagaki](../../audit/paper2agent/inagaki/FINAL_FIDELITY_REVIEW.md)、[Zhou](../../audit/paper2agent/zhou/FINAL_FIDELITY_REVIEW.md)；最终 [INDEPENDENT_REVIEW](INDEPENDENT_REVIEW.md) 单独给出G5结果。
- 完整回归：`audit/tests_full.txt`，70/70通过；新增10项适配/数值测试。独立审计脚本另复算真实数组，未只调用生产指标。
- 全配置、source/input/output SHA256、环境及seed见 `lds_results/*/config.json` 和 `manifests`。analysis Python3.12.12/NumPy2.3.5/SciPy1.16.3，CPU；未安装依赖。

执行入口：`python -m handcrafted_ei.visualization.plot_all --reference-grounded`。逐项入口见仓库README。完整盆NPZ约每编码229MB仅本地留存，索引记录SHA256；不复制进报告或提交。文件完整性检查与实际开图分别执行。

## 原论文：问题1–4

**1. 真正运行了哪些作者代码？** Zhou公开仓库未修改的 `task.py generate_trials('ITdDNMS',...,mode='test',noise_on=False)` 实际输出x=(450,100,33)、y=(450,100,2)，输入NPZ与源码SHA归档。未训练RNN、未取得作者weights，未运行缺失的Figure7扰动/Matlab绘图。Inagaki公开MATLAB代码首注只覆盖ED1/ED9；本机限定搜索未发现MATLAB/Octave，并缺辅助绘图函数，未实际运行作者模拟。原始源码与环境缺口均保留。

**2. Paper2Agent转化了什么？** 两篇正式可检索阅读包、原图/图注/Methods对应、机器可读Input/Figure契约和真实来源。Paper2Skill本身不执行论文方法；咨询、适配、数学实现与反向审稿是Codex专家工作，明确记录这种替代机制。没有虚构自动审图API或没有运行就标成功的MCP服务。

**3. 哪些是Methods重建？** Inagaki CD、endpoint normalization、per10ms phase-line及其合成测试；Zhou full-space交叉距离的数学实现和新的输入assay。中列三列对照明确标synthetic方法检查/示意，不是原始数据。Inagaki示意本身不作为CD/phase-line函数执行证据，实际函数测试在其source_methods与测试日志。

**4. 原始分析数据与扰动？** Inagaki主Fig5/6是同时记录ALM spike-derived rates，session/trial/time/neuron，100ms滑窗10ms步进；实验CD以最后600ms左右选择差拟合并split-half/不同delay验证、session endpoint归一化及层级统计。作者ED模型为4群率、1000trial/条件、模型CD末400ms；不可混称。Zhou Fig7用256 recurrent rates，50ms、π输入通道、标量.25、first cue后500ms，control/pert共享frozen noise；D(t,s)为全recurrent Euclidean，统计跨17训练网络。公开仓库未提供该完整分析路径；PCA具体fit集合和Fig7精确noise剂量仍unknown。Fig7无velocity field panel。

## LDS管线：问题5–10

**5. 原来存在什么问题？** 三编码raw均[24,663,132]、t=0..3310ms、dt5ms，未发现转置错误或raw损坏：55旧图记录165文件、75动力学输出hash通过。真正缺口是旧动力学仅固定D=+1/S=1的六位置；旧Figure9 endpoint瞬时state kick与原论文输入协议不等价；二维basis来自五重简并endpoint空间，PCA内误差掩盖全状态误差；预裁剪横轴不能代表实际剂量；单一折点代表谱不足以独立证明稳定性。

**6. 修复了什么？** 新严格loader显式transpose、保持24条件单次，全部47,664个全状态Euler转移验证重建sample/clock的积分边界；完整24个R3快照进入同一field；补齐真实50ms输入、control-only PCA、投影/正交能量、实际clip RMS/比例、局部小幅扰动、群体距离/恢复、连续/Euler/分段稳定性。图像经审查修正全量纵轴、折点谱和非原文flow标签。

**7. 哪些重跑？** 全部三编码24R3在同一tonic场的2s延长、每编码1728条state方向探针、72个uniform初态、两个input assay×3方向；均为评估副本，正常模型与raw不改。原source实验由于raw/运行时/weights缺失仍未重跑。

**8. 旧图与论文差异根因？** 部分是协议/范围/PCA展示问题；更根本的是handcrafted饱和点保持与原论文受训动态轨迹、实验重复结构不同。不是调色问题，也没有证据显示只需转置即可恢复原图。

**9. 哪些视觉差异消失？** 完整24条件矩阵可见；输入脉冲与状态kick被正确分图；二维误差外的完整能量可见；饱和峰约1.23e−5的变化不再通过自动offset占满纵轴；折点代表谱与稳定性证明分开。源数据缺失使精确source曲线差异无法进行数值消除。

**10. 仍保留的真实差异？** R3 fixed-clock三方向输入终点距离分别约1.500000、1.500000、1.118034，没有恢复原完整状态。source_time seed7在550ms距离.62749、1500ms为2.06133、1800ms为2.06154，最终仅1.81e−5；下降发生在后续clock切换之后，只支持 **schedule-assisted eventual reconvergence**，不是自主动态吸引恢复。

旧Figure9代表状态kick初始全距2.06987、最终1.5，旧二维初始能量仅0.3851%、最终近0；新control-only basis代表最终平面占11.111%，仍大部分误差在平面外。basis改变不能改变full-state结论。

## Neural subspace：问题11–16

独立复算结果见 [招募](audit/recruitment.csv)、[维数](audit/representation_dimensions.csv)、[角度](audit/representation_angles.csv)、[一致性](audit/FIGURE_01_07_10_CONSISTENCY.md)。

**11. 活动群体？** 三编码R3各分支跨六位置的阈值>0.1招募并集为26个单元：当前R3分支六位置、Y六位置、对应I_decay_D六位置、I_decay_S六位置和两个retire单元。这个并集不是单trial同时激活26个；tonic初始已活跃，基线扣除招募不计它们，但全网络分析仍包含它们。逐单元名字完整归档。

**12. 分支子空间可区分？** 可区分；whole132坐标分支平均夹角约83.38083066°。当前Response-only角度90°，与固定不重叠分支坐标直接相关，不能称涌现正交。

**13. 有效维数？** 三编码R3每分支六位置中心化rank5，有效PR≈4.99999945。R1/R2仍混合规则记忆条件，whole rank分别7/6，不强套1/2/4/4为PCA rank。

**14. Principal angles？** 六对whole分支均值约83.35149–83.43950°，各对五个角逐项CSV；Response-only五角均90°。这不是两个单元活动的夹角。

**15. 哪些来自handcrafted支持？** Response-only正交、不重叠招募、潜在1/2/4/4分支数为结构先验。whole空间共享Y/反馈及尾迹使角度小于90°；折叠到共同六位置的高重合只是移除branch坐标的控制，不是神经配准。

**16. 六位置有环几何？** 当前R3的六位置非对角距离等距，ring Spearman应undefined。whole-network极小相对距离差≈1.38246e−4可使rank相关接近1，不能当作显著环流形。旧MDS stress约.425/.460且二维embedding可任意旋转，画成六边形不能证明连续环或环吸引子。

Figure1–7正确共享分析被复用并核对；没有把普通PCA/变量回归改名dPCA、jPCA或Mante精确复现。Figure10以本次全24状态结果和独立维数/角度重绘。

## Attractor：问题17–23

**17. 完整空间稳定固定点？** 每编码24个task-seeded终点，最大field分量残差4.27557e−11/ms。独立按局部DAG顺序求邻近精确平衡点，double残差0，与2s终点最大差5.13068e−9；完整132维Euler一致性≤5.56e−17、FD误差≤3.18e−11。clip折点全允许斜率的局部union图均无反馈，稳定泄漏级联提供局部分段充分条件，不依赖二维图。

**18. 身份是否保持？** 每编码24/24当前R3位置与(d,s)分支保持。分支编码D/S，位置加该分支足以离线对应L；没有额外L memory，M_D/M_S不是持续外部clamp。

**19. 多个离散稳定状态？** 在同一个sample=clock=0、相同tonic向量场中，这24个终点可区分，最小pairwise L2约2且有局部证书，支持至少这些task-seeded局部稳定平衡点。不是宣称系统恰好24个；72个uniform初态还得到72描述性endpoint簇，未逐个认证为吸引子。

**20. 扰动能恢复？** 对full-state一次性kick，预裁剪RMS .001与.02均72/72恢复；.1为47/72，.3为9/72，三编码相同。72=24状态×3方向，是有限条件比例，不是动物/网络重复或置信区间。恢复要求maxerror<.02且原位置/分支身份保留，静息不计。

**21. 吸引域大小？** 未估计全局体积或最大半径。约.007792的maxnorm界是保持非kink分区的证明邻域界，不是保证不出界的吸引域半径。实际clip后剂量、target群体、裁剪比例、每条恢复及身份已保存于basin.csv；图上的实际RMS均值不能替代逐条剂量。

**22. 是否仅受迫平衡？** 这里不需要内容特异或阶段clock持续驱动，24状态共用撤sample/clock的tonic背景即可保持；因此不是24个不同内容输入条件下分别得到的单平衡。tonic是原定义背景的一部分，未声称撤除tonic仍多稳态。R3_fixed_clock输入实验另外保留快照clock，不能与自主盆结果混合。

**23. 更接近什么机制？** 所测已形成R3状态属于离散局部点保持机制；完整四次序列由内容无关clock驱动阶段转移。当前证据不支持把正常序列命名为自主dynamic attractor，也不证明连续流形。大输入扰动造成未恢复与局部点稳定不矛盾，两者剂量/条件不同。

## Gate结果与未实现项

G0能力实测、G1方法/公开源码覆盖核验、G2显式数据适配、G3数值、G4两专家反向审查均有对应文件；LDS范围PASS_WITH_LIMITS。G5以独立报告实际结论为准。作者exact执行/实验统计复现仍受上述缺失资料/运行时阻塞，不通过安装、训练、伪造重复或改模型绕过。

没有独立模型科学缺陷迫使改变回路；没有为期望图案修改标准。提交只通过Nimbalyst提案，确认前保持uncommitted；远端不推送。
