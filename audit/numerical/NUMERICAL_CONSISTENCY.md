# 独立数值动力学审计

目标：独立复算完整状态动力学、固定点与稳定性、扰动剂量、PCA 能量和有限输入脉冲；不修改模型或正式分析实现。

审计实现：`audit/numerical/independent_check.py`。该程序仅从受保护模型读取固定系数，以独立公式计算；不调用 production 的 field、Jacobian、evolve_batch、adapter、projection 或 distance 函数。结果逐项写入 `independent_check.json`。三编码分别检查真实输出，不由一份结果复制。

## 结论及数值证据

- **数值公式通过**：三编码24条件完整400步 tonic-only 延长轨迹，Euler 增量与独立完整132维 field 的最大误差均 `5.551115123125783e-17`。完整 `24×24` 欧氏距离矩阵独立重算误差0。
- 每编码24个 task-seeded endpoint 在 maxnorm tolerance `.02` 下为24簇，24个保持 R3 branch/position 身份；原2s终点最大连续残差 `4.275570176061969e-11 /ms`。这不是同一静息点的24次重复。
- 首终点独立解析 Jacobian 与中心差分误差 `3.174387835924719e-11`；与保存谱排序后误差0。最大实部 `-1/120=-.008333333333333333 /ms`，Euler 谱半径 `1-5/120=.9583333333333334`。共同谱半径来自局部饱和与共同时间常数，不说明吸引域相同。
- 生产 smooth certificate 因13个 clip kink 为 false，这是保守的**未认证**，不能解释成“不存在稳定固定点”。另外的独立分段线性充分条件见下文；它没有修改原 smooth 判据。
- 独立抽查每编码3类 perturbation target、每类4个实际trial/amplitude/seed组合，重新生成随机方向和 clipping，初始状态、target RMS、clipping fraction、第一步积分与归档相符，误差均低于 `1e-12`。例如首trial full-target nominal `.001` seed7 的实际 RMS为 `.0006005310341793871`，clipping fraction为 `.5681818181818182`；nominal幅值不能作为实际剂量。
- PCA 正交误差 `5.55e-16`；完整能量=平面能量+正交能量闭合误差 `1.78e-15`；独立 cross-temporal distance 误差 `6.66e-16`。示例state kick首时刻仅 **2.5963%** 能量在所画二维PCA平面，轨迹看起来相近不能代替完整状态恢复。
- 50ms input pulse 与 state kick 是分开的两个实验。source-time脉冲从500ms状态之后作用，存储的 current rows为505…550ms共10步；R3-fixed-clock为25…70ms，对应20ms开始的10个区间。每行是“积分进入该时刻”的电流，而非该时刻之后的电流。实际 RMS `.25`、积分RMS `12.5 current·ms`。控制与扰动在onset及之前完全相同，noise arrays逐项相同且全零。独立控制/扰动全轨迹 Euler 残差最大 `8.33e-17`。

## Clip kink 的局部稳定性独立充分条件

动力学为

\[
\dot r_i=\tau_i^{-1}\{-r_i+\mathrm{clip}(W_i r+b_i,0,1)\},\quad b=\mathrm{tonic}-\theta.
\]

sample与clock均为零，tonic保留，全部24初态使用**同一个**向量场。首终点13个kink包括 `I_tonic_R/M`（其W行全零）、`I_decay_S[2]`、6个 `comp_R1`、2个 `comp_D`、2个 `comp_S`。其余trial的具体索引通过逐状态JSON记录。

独立证明算法：在平衡点邻域内，严格在clip外的行导数恒0，严格在 `(0,1)` 内的行导数恒1，kink行导数允许整个 `[0,1]`。用“内部行或kink行”的全部非零 W 元素构造 **union dependency graph**。图的边方向是 `source→target`，即矩阵 `[target,source]`。对每个状态做 Kahn 拓扑排序；全部24状态×三编码均为DAG。

因此存在同一个局部拓扑次序，使所有允许kink斜率下的 Jacobian 同时为三角矩阵，diagonal始终为 `-1/tau_i`。这比“分别采样若干Hurwitz矩阵”强：局部非线性系统是无反馈的、Lipschitz 的标量稳定泄漏级联，按拓扑次序用标量稳定系统的输入收敛性质逐级证明局部渐近稳定。离散Euler对应每级自系数 `1-dt/tau_i` 均在 `(0,1)`，同样为局部稳定级联。所有 kink 斜率都由此覆盖，不需枚举2048个角点，更不假定任意稳定矩阵切换必稳定。

为排除“近似终点不是固定点”，另按每个状态的union DAG次序求解 `r_i=clip(W_i r+b_i,0,1)`；全部72份结果完整field残差为0（double precision），与轨迹终点最大差 `5.130684211274363e-9`，身份全部保留。这提供邻近固定点与局部分段稳定性的独立充分证据。

对非kink且非零W行，记录

\[
\delta=\min_i\frac{\min(|a_i|,|a_i-1|)}{\|W_i\|_1},\quad a_i=W_i r_*+b_i.
\]

当状态与平衡点的maxnorm差小于该值，非kink行不会改变clip分支。首状态约 `.007792208`；每状态的具体值在JSON中。该值只是证明所用的局部clip分区邻域，**不是保证所有轨迹不出该邻域的吸引域半径**。稳定级联论证保证存在足够小的初态邻域，但本审计没有给出其最大半径或全局吸引域体积。

## 限制及不可混淆的量

1. 24个task-seeded局部稳定平衡点不代表全部平衡点只有24个。72个uniform初态有72个描述性endpoint簇；它们没有逐一做平衡点、身份和局部分段证书，不可称72个吸引子。
2. perturbation seeds是随机方向，不是独立网络、动物或训练重复；恢复比例是有限方向经验结果。局部稳定不证明大扰动全恢复。
3. `final_l2` 以有限时长control终点为基准，存在约 `5e-9` 的control继续漂移量，远低于 `.02`恢复门槛。不能把该底噪说成积分不一致。
4. 同样的终点/谱/PCA结果与编码输入维度不同不矛盾：这里分析的是内部132维状态，不是原始6/1/2维输入。
5. 50ms输入脉冲已对时间与配对公式核验；它仍是LDS方法适配，不凭此认定等价于原文受训网络或原始实验数据。

## 重算

使用已验证的 analysis 环境直接执行 `python audit/numerical/independent_check.py`，设置 `OPENBLAS_NUM_THREADS=1`。脚本执行数值assertions并归档其自身SHA256；没有安装依赖、修改模型或调用computer use。现有生产测试覆盖了合成cross-temporal案例、投影闭合、输入非状态跳变；本脚本补上真实产物的独立公式验证。

审计范围内没有发现阻塞数值错误。需要修正的解释问题是把 `smooth stable certificate=0` 当作“零稳定点”，或把24/72个描述性簇直接当完整吸引子计数；独立分段证据与有限实验范围必须同时保留。
