# 局部不动点与流形相图：来源及方法契约

## 来源已实际确认

用户新截图与出版原图逐项实际比对，确切来源是Natalia B. Janson、Christopher J. Marsden (2017)，*Dynamical system with plastic self-organized velocity field as an alternative conceptual model of a cognitive system*，Scientific Reports7:17007，Figure1，DOI10.1038/s41598-017-16994-y。不是Langdon2023 Box1：本地Langdon图已打开，内容为任务角度/调谐曲线/神经环流形，不匹配。

原图：https://media.springernature.com/m685/springer-static/image/art%3A10.1038%2Fs41598-017-16994-y/MediaObjects/41598_2017_16994_Fig1_HTML.jpg 。实际有效图保存在source2017_figure1_m685.jpg。出版全文：https://www.nature.com/articles/s41598-017-16994-y ，PMC作者全文：https://pmc.ncbi.nlm.nih.gov/articles/PMC5717027/ 。直接PDF/full-resolution图片下载曾返回JS挑战HTML，这些失败响应已按challenge.html命名，不能冒充有效PDF/原图。

来源Figure1为二维示例系统相图：蓝实心表示稳定点、空心表示saddle、红线表示saddle稳定流形/盆边界、粗蓝表示其不稳定流形。原示例是Bonhoeffer–van der Pol式，不是本LDS方程；这里只采用经证明的动力系统对象与视觉语义，不复制其坐标−3..3、曲线或学习机制。

## LDS闭合pair与完整网络的区别

从真实archive活动选择一个R3率单元r及其一对一I_decay_S率单元z。sample=clock=0、原tonic保留，在已验证不变的上游背景条件下，候选闭合方程为

 dr/dt = [−r+clip(2r−.9,0,1)]/40,
 dz/dt = [−z+clip(2.4r−1.4,0,1)]/120。

全部系数、阈值、tau必须由原固定模型逐项提取并检查，不能为了获得三固定点手设新模型。验证r,z∈[0,1]时上游nuisance初态为实际tonic-rest且保持不变；Y等下游单元可随pair变化，但不反馈r,z。**闭合子系统**表示其导数不依赖下游自由状态；它不要求把其它130单元固定的affine平面为完整网络不变流形。

这比此前非闭合二维投影更直接回答局部稳定问题。横纵轴为实际无量纲神经率，不叫PC、latent或源论文x。不改变正常trial、模型参数、Dale或任务。

## 固定点与局部结构的验收

闭合pair解析候选为(0,0)、(1,1)、(.9,.76)。这些候选不能替代完整132维平衡求解。完整field/root应从真实rest、真实高活动endpoint及interior候选生成独立完整解，报告full residual、连续与Euler谱、source/config哈希。

中间pair处两行激活均在clip内部，Jacobian为[[1/40,0],[2.4/120,−1/120]]，特征值+.025/ms与−.008333333/ms，pair局部saddle；不稳定pair方向比例dz/dr=.6，稳定方向为r不变。完整网络还要核查其它模态，不能从pair直接宣称full132 saddle。

sink的辅助clip kink不得仅使用半斜率代表谱证明稳定。完整局部union dependency graph满足共同三角级联时，可覆盖全部允许kink斜率，给出分段局部稳定充分证据。完整saddle若去除对角后的union图无环，且所有kink行自身权重为0，允许斜率不改变对角；一正其余负可支持分段级联saddle结构。不能未经说明对不光滑完整系统套经典光滑stable-manifold theorem。

## 流形与轨迹

在闭合pair中r=.9是稳定流形的合法有限区段，z向.76收敛；可用解析解或真实pair积分绘红线，并与完整Euler自由演化的有限时间结果比较。不得运行时clamp r后把红线称为完整网络自由轨迹。

完整132维saddle稳定集合一般为131维，不能把2D红线称为它的全体。红图例须明确reduced-system stable manifold。蓝双支应从完整saddle±epsilon完整特征向量开始，合法[0,1]检查，不允许clip后仍冒称同一特征方向，随后原完整网络自由积分；绘pair坐标，报告连续/数值有限epsilon近似与完整终点。

full stable equilibrium与Response recovery分开：回到rest只是rest control。新图两个sink是同一selected单元低/高活动状态，不是两个不同位置答案；若真实结果不支持两sink一saddle，不得伪造。

## 交付判定

设计目前**PASS_WITH_LIMITS**。最终需实际打开三编码主/补图，读取实际完整解与谱、独立核pair/fullfield一致、sink/kink证书和saddle正模态、蓝双支/红稳定线的真实时间方向。源Figure1只作视觉/数学对象参考，不声称精确复现原作者示例。
