# 论文式流线相图：来源核验与LDS方法契约

## 来源身份与实际核验

用户截图已实际打开；出版原Figure2 webp也已实际打开，两者三列标题、蓝流线、红轨迹/端点、lambda1/2轴与红数字1/2完全对应。来源为Paul Saighi、Marcelo Rozenberg，*Autonomous retrieval for continuous learning in associative memory networks*，Frontiers in Computational Neuroscience19 (2025)，DOI10.3389/fncom.2025.1655701，Figure2。原PDF10页，目标图位于PDF第5页；另有ICLR2025 workshop前稿Figure1，但本次使用出版Figure2，不混用前稿beta或更新规则。

来源链接：https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2025.1655701/full 。下载PDF、HTML、原图及来源哈希保存在本目录；此为targeted source review，不冒称新论文完成全篇Paper2Skill转换。原先已审两篇来源技能可复用审计方法，截图新来源单独列明。

## 原图方法（已核验的来源信息）

原图在两个稳定**膜电位状态**ū1/ū2张成的二维平面计算完整N维向量场再投影，坐标lambda是模式系数而非PCA得分；原文区别u与rate v=sigma(u)，neutral u=0对应rate .5。红线是完整网络轨迹投影。三列是实际权重训练和随后adaptation改变；LDS不训练，不复制这些实验标签。图注明投影回平面，但未给Gram/QR/dual具体实现，故投影矩阵细节为unknown，不伪称作者用了正交或dual算法。

## LDS适配数学定义（本审查推导，不冒充原作者源码）

选择两个同一R3活动分支、不同活动位置的真实task-seeded端点，选择依据神经活动，不用目标标签生成状态。令tonic-only真实无sample背景为r0，B=[r1−r0,r2−r0]，B形状132×2；必须rank2，报告singular values/condition number。系数与导数采用least-squares dual D=(BᵀB)⁻¹Bᵀ，实际实现可SVD/QR以稳健求解。

三列各从相同实际默认rest开始，在各自固定clock/tonic且sample0下真实积分得到content-free背景r0c。先检验fullstate残差，未达到阈值只能称finite-time background。定义每列平行affine切片r_c(a)=r0c+B a；坐标称a1/a2或lambda_LDS，并显著说明其为LDS无量纲率状态系数，非原u、非PC。

二维蓝场g_c(a)=D f_c(r_c(a))。完整正交投影算子P=B D，未显示场为f_perp=(I−P)f；必须保存norm、relative norm及零场NA。不能用Bᵀf替代D f，除非B已正交归一且坐标语义同步改变。

合法区域要求逐格0≤r_c(a)≤1。**不允许clip网格点**再称固定affine平面；无效格mask并显示边界/feasible fraction，可能是三角或更小域，不为模仿论文方形域而绕过。若网格为空或不足以画流线，报告不兼容并修改可审计设计，不能补假箭头。

完整红轨迹必须从合法r_c(a_initial)在匹配的原132维场独立积分，再画a(t)=D(r(t)−r0c)。保存完整状态、输入、时间及offplane displacement e(t)=(I−P)(r(t)−r0c)。蓝streamline仅为切片限制投影场的积分，**不是**完整网络轨迹；两者可能不相同。只有f全态残差小才可标固定点，二维g=0不足以判断。真实rest若保持稳定、轨迹不选择源图式另一吸引子，应如实画出。

## 三条件及比较意义

建议列名为Clock-off background、R3-permission background、R3-retirement background。条件1 sample0/clock0/原tonic；条件2 sample0/快照clock固定；条件3在条件2已有clock基础上施加模型config指定的内容无关retire3电流。禁止改权重、tau、Dale或训练。

每列r0c不同，图比较的是**各固定外驱已平衡背景的平行切片**，不是same-state场比较，也不是瞬时clock切换。背景平衡用于明确所分析的条件，不为制造预期流形。共同B/dual使坐标可比，但不同slice origins必须在图注明示，保存全部origin/current向量。若某源端点在另一condition不是平衡点，只称参考pattern方向，不画成该condition稳定吸引子。

## 科学/绘图验收

1. 原图来源、膜电位vs率、训练vs固定clock差异明示，METHOD ADAPTED。
2. 网格真实fullfield，合法域mask，common basis与dual闭合验证。
3. 至少两档网格/积分步长数值一致性；不使用任意箭头指向中心。
4. 蓝流线与红fullstate轨迹风格区分；红时间方向箭头只沿实际记录。
5. 每列显著显示offplane场比例和真实trajectory平面外误差；不能只藏在附录。
6. 端点标记经fullstate残差验证，不根据二维视觉宣称separatrix/盆/稳定性。
7. 三编码分别实际计算，缓存检查source/config/origin/basis/current hashes。
8. 最终同一专家实际重开三编码图+数值复核后裁决PASS/REVISE。

## 当前设计裁决

**PASS_WITH_LIMITS（设计适配）**。不同origin、合法域、平面不闭合与真实轨迹误差是强制披露条件。尚未见实现或最终图，不提前验收。
