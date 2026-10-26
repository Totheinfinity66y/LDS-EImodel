# 逐图结果与科学解释

所有数值来自本次完整神经率分析；模型、task、时序和baseline配置没有改动。

## One-hot

### Figure 1–2：活动组织与招募

内部神经元 132，E=81、I=51。各条件按固定branch依次激活，旧阶段在retire后衰退；tonic I持续存在。当前Response的招募局限主要由预定义的六单元分支支持决定，其他活跃的memory、gate、Y和I是共享/辅助活动。factorial图显示单变量和交互条件方差，不含显著性推断。

[全网络活动](figures/one_hot/figure_01_one_hot.png) · [结构/功能招募](figures/one_hot/figure_02_one_hot.png)

### Figure 3：记忆交接

M_D：Response onset=1945 ms，90%稳定=2035 ms；memory 95%交叉=2065 ms，50%交叉=2100 ms，0.05交叉=2185 ms。
M_S：Response onset=2415 ms，90%稳定=2505 ms；memory 95%交叉=2535 ms，50%交叉=2570 ms，0.05交叉=2655 ms。

阻断反馈后M_D/M_S保持接近1，baseline交接后衰减；正常与无反馈条件均可保持行为正确，因此行为正确率不是记忆终止的验收指标。规则质心差和probe分别支持memory/Response的信息载体变化；不同population的原尺度距离不能直接相加或比较信息量。

### Figure 4–5：状态空间与维数

全网络统一PCA前三轴VAF为 17.95%, 17.09%, 13.88%。各分支完整状态的中心化维数如下；R1/R2中未固定的规则记忆增加全状态维数。

- R1: b0 rank=7, PR=5.5549, dim95=7
- R2: b0 rank=6, PR=4.7324, dim95=6, b1 rank=6, PR=4.7324, dim95=6
- R3: b0 rank=5, PR=5.0000, dim95=5, b1 rank=5, PR=5.0000, dim95=5, b2 rank=5, PR=5.0000, dim95=5, b3 rank=5, PR=5.0000, dim95=5
- R4: b0 rank=5, PR=5.0000, dim95=5, b1 rank=5, PR=5.0000, dim95=5, b2 rank=5, PR=5.0000, dim95=5, b3 rank=5, PR=5.0000, dim95=5

当前Response的位置中心化rank各阶段为5。支持折叠后的分支重合接近1，说明分支间分离主要受固定坐标块约束。全网络含共享Y/I/记忆，故真实全网络角度不必正好90°。不同L奇偶拟合方向差异很大，反映采样位置不同；同条件小输入噪声seed的95%VAF子空间稳定，不能据此声称随机网络间稳定。

### Figure 6：输入与神经表征几何

R1 b0：全网络rho=NA（等距）；当前Response rho=NA（等距），MDS stress=0.4597。
R2 b0：全网络rho=0.912871，相对opposite-adjacent距离差=0.00016143；当前Response rho=NA（六位置等距），MDS stress=0.4254。
R3 b0：全网络rho=1.000000，相对opposite-adjacent距离差=0.00013825；当前Response rho=NA（六位置等距），MDS stress=0.4255。
R4 b0：全网络rho=1.000000，相对opposite-adjacent距离差=0.00023507；当前Response rho=NA（六位置等距），MDS stress=0.4254。

R2–R4微弱全网络环排序由共享Y内旧位置的读出尾迹产生，Response和all-Response自身仍等距。高Spearman对极小距离差敏感；必须结合相对效应量与population contribution解释，不作强环流形结论。所有编码给出同样的结果。

### Figure 7：信息可读出性

L/D/S曲线与cross-temporal矩阵使用严格不相交任务条件fold；当前位置与branch另在读出窗评价。未出现独立网络/动物意义的泛化证据。固定branch的D或S可用性与该群体是否激活相关，不能把标签常量当解码成功。

### Figure 8–9：固定状态与有限盆

保留clock与撤clock的两类条件都观察到所测状态的低残差端点，tonic背景保留。局部谱和小扰动恢复支持离散、条件限定的稳定固定点候选；阈值拐点导数及有限初态覆盖限制全局判断。每编码有24个任务自主端点，随机初态再带来3个不同端点，不能将网络描述为只有六个吸引子。cross-temporal条带与固定点参照一致，没有动态吸引轨迹证据。

## 1D Ring

### Figure 1–2：活动组织与招募

内部神经元 132，E=81、I=51。各条件按固定branch依次激活，旧阶段在retire后衰退；tonic I持续存在。当前Response的招募局限主要由预定义的六单元分支支持决定，其他活跃的memory、gate、Y和I是共享/辅助活动。factorial图显示单变量和交互条件方差，不含显著性推断。

[全网络活动](figures/ring/figure_01_ring.png) · [结构/功能招募](figures/ring/figure_02_ring.png)

### Figure 3：记忆交接

M_D：Response onset=1945 ms，90%稳定=2035 ms；memory 95%交叉=2065 ms，50%交叉=2100 ms，0.05交叉=2185 ms。
M_S：Response onset=2415 ms，90%稳定=2505 ms；memory 95%交叉=2535 ms，50%交叉=2570 ms，0.05交叉=2655 ms。

阻断反馈后M_D/M_S保持接近1，baseline交接后衰减；正常与无反馈条件均可保持行为正确，因此行为正确率不是记忆终止的验收指标。规则质心差和probe分别支持memory/Response的信息载体变化；不同population的原尺度距离不能直接相加或比较信息量。

### Figure 4–5：状态空间与维数

全网络统一PCA前三轴VAF为 17.95%, 17.09%, 13.88%。各分支完整状态的中心化维数如下；R1/R2中未固定的规则记忆增加全状态维数。

- R1: b0 rank=7, PR=5.5549, dim95=7
- R2: b0 rank=6, PR=4.7324, dim95=6, b1 rank=6, PR=4.7324, dim95=6
- R3: b0 rank=5, PR=5.0000, dim95=5, b1 rank=5, PR=5.0000, dim95=5, b2 rank=5, PR=5.0000, dim95=5, b3 rank=5, PR=5.0000, dim95=5
- R4: b0 rank=5, PR=5.0000, dim95=5, b1 rank=5, PR=5.0000, dim95=5, b2 rank=5, PR=5.0000, dim95=5, b3 rank=5, PR=5.0000, dim95=5

当前Response的位置中心化rank各阶段为5。支持折叠后的分支重合接近1，说明分支间分离主要受固定坐标块约束。全网络含共享Y/I/记忆，故真实全网络角度不必正好90°。不同L奇偶拟合方向差异很大，反映采样位置不同；同条件小输入噪声seed的95%VAF子空间稳定，不能据此声称随机网络间稳定。

### Figure 6：输入与神经表征几何

R1 b0：全网络rho=NA（等距）；当前Response rho=NA（等距），MDS stress=0.4597。
R2 b0：全网络rho=0.912871，相对opposite-adjacent距离差=0.00016143；当前Response rho=NA（六位置等距），MDS stress=0.4254。
R3 b0：全网络rho=1.000000，相对opposite-adjacent距离差=0.00013825；当前Response rho=NA（六位置等距），MDS stress=0.4255。
R4 b0：全网络rho=1.000000，相对opposite-adjacent距离差=0.00023507；当前Response rho=NA（六位置等距），MDS stress=0.4254。

R2–R4微弱全网络环排序由共享Y内旧位置的读出尾迹产生，Response和all-Response自身仍等距。高Spearman对极小距离差敏感；必须结合相对效应量与population contribution解释，不作强环流形结论。所有编码给出同样的结果。

### Figure 7：信息可读出性

L/D/S曲线与cross-temporal矩阵使用严格不相交任务条件fold；当前位置与branch另在读出窗评价。未出现独立网络/动物意义的泛化证据。固定branch的D或S可用性与该群体是否激活相关，不能把标签常量当解码成功。

### Figure 8–9：固定状态与有限盆

保留clock与撤clock的两类条件都观察到所测状态的低残差端点，tonic背景保留。局部谱和小扰动恢复支持离散、条件限定的稳定固定点候选；阈值拐点导数及有限初态覆盖限制全局判断。每编码有24个任务自主端点，随机初态再带来3个不同端点，不能将网络描述为只有六个吸引子。cross-temporal条带与固定点参照一致，没有动态吸引轨迹证据。

## 2D Topology

### Figure 1–2：活动组织与招募

内部神经元 132，E=81、I=51。各条件按固定branch依次激活，旧阶段在retire后衰退；tonic I持续存在。当前Response的招募局限主要由预定义的六单元分支支持决定，其他活跃的memory、gate、Y和I是共享/辅助活动。factorial图显示单变量和交互条件方差，不含显著性推断。

[全网络活动](figures/topology/figure_01_topology.png) · [结构/功能招募](figures/topology/figure_02_topology.png)

### Figure 3：记忆交接

M_D：Response onset=1945 ms，90%稳定=2035 ms；memory 95%交叉=2065 ms，50%交叉=2100 ms，0.05交叉=2185 ms。
M_S：Response onset=2415 ms，90%稳定=2505 ms；memory 95%交叉=2535 ms，50%交叉=2570 ms，0.05交叉=2655 ms。

阻断反馈后M_D/M_S保持接近1，baseline交接后衰减；正常与无反馈条件均可保持行为正确，因此行为正确率不是记忆终止的验收指标。规则质心差和probe分别支持memory/Response的信息载体变化；不同population的原尺度距离不能直接相加或比较信息量。

### Figure 4–5：状态空间与维数

全网络统一PCA前三轴VAF为 17.95%, 17.09%, 13.88%。各分支完整状态的中心化维数如下；R1/R2中未固定的规则记忆增加全状态维数。

- R1: b0 rank=7, PR=5.5549, dim95=7
- R2: b0 rank=6, PR=4.7324, dim95=6, b1 rank=6, PR=4.7324, dim95=6
- R3: b0 rank=5, PR=5.0000, dim95=5, b1 rank=5, PR=5.0000, dim95=5, b2 rank=5, PR=5.0000, dim95=5, b3 rank=5, PR=5.0000, dim95=5
- R4: b0 rank=5, PR=5.0000, dim95=5, b1 rank=5, PR=5.0000, dim95=5, b2 rank=5, PR=5.0000, dim95=5, b3 rank=5, PR=5.0000, dim95=5

当前Response的位置中心化rank各阶段为5。支持折叠后的分支重合接近1，说明分支间分离主要受固定坐标块约束。全网络含共享Y/I/记忆，故真实全网络角度不必正好90°。不同L奇偶拟合方向差异很大，反映采样位置不同；同条件小输入噪声seed的95%VAF子空间稳定，不能据此声称随机网络间稳定。

### Figure 6：输入与神经表征几何

R1 b0：全网络rho=NA（等距）；当前Response rho=NA（等距），MDS stress=0.4597。
R2 b0：全网络rho=0.912871，相对opposite-adjacent距离差=0.00016143；当前Response rho=NA（六位置等距），MDS stress=0.4254。
R3 b0：全网络rho=1.000000，相对opposite-adjacent距离差=0.00013825；当前Response rho=NA（六位置等距），MDS stress=0.4255。
R4 b0：全网络rho=1.000000，相对opposite-adjacent距离差=0.00023507；当前Response rho=NA（六位置等距），MDS stress=0.4254。

R2–R4微弱全网络环排序由共享Y内旧位置的读出尾迹产生，Response和all-Response自身仍等距。高Spearman对极小距离差敏感；必须结合相对效应量与population contribution解释，不作强环流形结论。所有编码给出同样的结果。

### Figure 7：信息可读出性

L/D/S曲线与cross-temporal矩阵使用严格不相交任务条件fold；当前位置与branch另在读出窗评价。未出现独立网络/动物意义的泛化证据。固定branch的D或S可用性与该群体是否激活相关，不能把标签常量当解码成功。

### Figure 8–9：固定状态与有限盆

保留clock与撤clock的两类条件都观察到所测状态的低残差端点，tonic背景保留。局部谱和小扰动恢复支持离散、条件限定的稳定固定点候选；阈值拐点导数及有限初态覆盖限制全局判断。每编码有24个任务自主端点，随机初态再带来3个不同端点，不能将网络描述为只有六个吸引子。cross-temporal条带与固定点参照一致，没有动态吸引轨迹证据。

## Figure 10：三编码比较

内部网络相同，ring/topology无噪声电流相同；one_hot早期sample电流不同，但竞争与饱和动力学使读出期Response表征趋同。综合图保留完整坐标尺度，定量summary不混合量纲、不构造最佳模型评分。raw-coordinate噪声.2的比较必须同时参考原manifest中的current_error_l2，不推断编码优越。

## 解码对照及记忆终止的边界

严格条件留出的baseline probe在2315 ms的R2/D、2810 ms的R3/S均为0.5，不能据此声称未见任务组合上的规则读出泛化；one-hot的未见坐标支持影响了该分类器。额外使用噪声sigma=.03、seeds7/11/19，以完整24条件训练两seed、测试另一seed，三个编码在readout2的R2/D和readout3的R3/S均为1.0。这个结果支持已见条件下独立输入噪声重复的信息可用性，不能代替条件外推。

同一噪声probe在这两个读出时刻的M_D/D和M_S/S也为1.0。即使幅度低于0.05，非零残差仍可在数值精度与probe容差内携带规则身份。这里的memory终止是活动幅度机制，不是严格信息擦除；不能声称信息只存在于Response或已经从memory完全消失。所有fold实际trial noise seed写入decoding_noise_seed_splits.json，fold共享训练seed，不计算独立fold置信区间。

