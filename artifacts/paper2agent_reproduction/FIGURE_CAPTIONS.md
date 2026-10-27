# 图注与分析边界

## Figure 8（三编码分别输出）

实际24个R3读出状态，固定同一sample=0、clock=0、原tonic保留的132维向量场，延长2000ms，dt5ms。A为R3最大活动，纵轴固定0–1.05，另标实际约1.23e−5的最大尾部变化；B为24×24完整终点Euclidean距离；C为预声明D=+1、S=1、L=0/3两个条件的描述性CD，方向为两个终点差的单位向量，未作源论文session端点归一化；D为这两条轨迹的中心差分，每10ms坐标变化，非随机漂移估计；E为完整场残差；F为折点斜率取0.5的代表性广义Jacobian谱，稳定性计数依赖独立覆盖所有允许折点斜率的DAG级联证书，不能仅由此单一谱证明。所有率无量纲。端点聚类以maxnorm .02的greedy complete-link定义；稳定计数还要求低残差、数值导数检查以及光滑或分段充分条件，不能直接把cluster等同attractor。

这属于 **METHOD ADAPTED** 与LDS-specific dynamics diagnosis。没有动物/session、左右选择重复试次或层级bootstrap；不宣称重现Inagaki主Figure5/6的实验统计。CD只作配对示例，不是本任务唯一coding direction。24个task-seeded固定点不意味着全系统恰有24个吸引子。

## Figure 9 input（三编码各两种assay）

仿照Zhou的50ms有限输入扰动，独立control/perturbed对共享相同外驱和全零过程noise。固定随机whole-network外部电流投射由seed7/11/19定义，方向向量RMS=1，标量.25，故实际电流RMS=.25、L2=.25√132、RMS时间积分12.5 current·ms；不等于原作者单个π输入通道幅值.25。电流允许正负，Dale权重及模型不变。actual current数组、noise配对、刺激与clock均归档。

source_time assay在trial0起点500ms（sample onset+500ms，sample offset后300ms）开始，重放完整正常时序；control逐步与归档一致。R3_fixed_clock assay由trial0实际R3读出状态开始，sample关闭、该快照clock固定，20ms后施加输入；这是独立固定驱动诊断，不是正常trial中的R3后续轨迹。

A展示control中时间变动最大的5个单元，仅用于展示；距离和PCA采用全部132状态。B只在control时间轨迹上center和拟合PCA，不能把二维重合判为恢复；C为D[t_control,t_perturbed]=完整率空间Euclidean距离；D精确分解完整/二维投影/正交距离；E为实际添加电流RMS；F为三种固定输入方向的完整距离，不绘SEM。没有17个独立训练RNN，不能复现原论文网络总体统计。真实LDS持续平台不能通过色图制造动态斜带。

## Figure 9 state 与 flow补图

state为一次性合法率状态扰动，不能与50ms输入扰动混称。六类目标为full、all Response、active branch、unselected branches、E、I；目标由活动选择。幅值预裁剪RMS .001/.02/.1/.3，每24个终点各3方向；记录裁剪后实际target/whole RMS及裁剪比例。恢复要求全状态max误差<.02且原R3位置/分支身份保留，静息不算恢复。分类群体另列final距离及带身份约束的恢复值。

flow是固定点中心、control-only PCA平面的裁剪切片；完整f先算再投影，另显示平面外范数。**Zhou Figure7没有velocity-field panel**，因此这只是LDS-specific补充诊断，二维箭头不证明动态吸引子。

## 源图三列对照与Figure10

source_comparisons目录仅本地保存受版权限制的原图；Inagaki中列为明确标记的synthetic illustration，函数单元测试证据单独保存；Zhou中列确实调用Euclidean distance函数作synthetic method unit check。两者均不能冒充缺失作者数据的原图复现；右列为真实LDS数据。精确源图执行的阻塞保留。

Figure10复用经独立复算的R3有效维数/角度，结合新全24状态稳定性及身份计数，不使用复合得分。Figure1–7审查复用正确共享分析与历史图，细节见audit/FIGURE_01_07_10_CONSISTENCY.md。
