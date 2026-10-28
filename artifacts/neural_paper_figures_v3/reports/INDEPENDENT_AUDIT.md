# LDS 科研绘图 v3 独立验收

本验收由独立代理 `independent_audit` 完成，未修改分析、绘图或模型实现。独占审计脚本为本目录的 `independent_check.py`，机器可读结果位于 `../manifests/independent_audit.json`。验收针对实际本地 NPZ/CSV 与真实输出图片，未沿用历史报告的 PASS。

## 结论与证据范围

**数值验收 PASS；科学结论 PASS_WITH_LIMITS。** 三编码均通过独立数组重算，12 项新增几何/数值测试全部通过。这里的通过表示数据来源、计算约定与所报告局部实验相符，不表示已证明全局吸引域、恰好六个吸引子或原论文科学结论复现。

代码版本基准为 Git `971704664740ecad33ea2a8d3ae30fb8ab964ee1`。三份新分析/绘图模块及本验收脚本的 SHA256 已写入独立清单。本次审计独立验证原始归档保护的 8 份 model/task/simulation/config 源文件哈希全部相符；全部正式 ZIP 校验由正式 loader 实际执行。标准化记录与 ZIP 内完整率数组数值完全一致，各为 `24 × 663 × 132`，条件集合为 24 个不同的 L/D/S 组合。Git 状态中的其他会话文件没有纳入本审计写入范围。

## 独立数值检查

- **Figure 4：** 对所有条件重新计算共同 mean/components 投影与全 132 维速度。固定 L=0 下 D/S 四条件严格平衡；从 R2 的 S 平均方向对比和 R3 四条件质心独立 SVD 重建投影子空间，与归档 basis 的投影矩阵一致。整段轨迹使用同一 basis。前两分支轴解释 R3 分支间方差约 **36.6688%**，不可把二维重叠解释为完整状态未分离。
- **Figure 5：** 三编码的六组 R3 逐维角度谱 CSV 与正式源 CSV 逐字段相同；没有从平均角热图重估。whole、Response-only、folded 的时间分辨几何，在六个分布于全程的时刻独立 SVD 重算角谱、奇异值和质心距离；全部匹配。全时程实际 rank 不超过 5，初态无有效子空间时角度为 NA，低于有效 rank 的缺失维度保留 NA。
- **固定点：** 三编码共 72 个端点，独立手写全向量场残差与 132 列中心有限差分 Jacobian；最大残差 **4.2756×10⁻¹¹ rate/ms**，最大 Jacobian 误差 **3.1744×10⁻¹¹**。连续谱最大实部为 **−1/120 ms⁻¹**，Euler 谱半径为 **0.9583333**。每个点有 13 个 clip 折点，`strict_local_stability=False` 被如实保留。负光滑谱不是折点稳定性的充分证明；本批端点另有局部分段前馈级联 certificate（CSV `certified=True`），只能支持相应局部结论。
- **Figure 8 初态切片：** 每编码为四分支、三组不同位置三元组、21×21 网格，共 5292 个候选点，其中 **2772 合法、2520 非法**。逐点检查完整初态属于 [0,1]¹³²，非法点保存 NA 且未 clipping。独立重算仿射构造与全部合法终态的完整场残差、全部 R3 分支/位置活动分类。每个切片额外独立 Euler 积分一个中间合法点，三编码合计 36 条重放与归档端点匹配。
- **Figure 8 负结果：** 各编码每分支三切片合计 693 个合法点，54 个达到单位置类别，639 个为 **R3-inactive**。这里的 inactive 仅指 R3 无阈上单元，并非全网所有神经元静息。本切片未观察到稳定多位置终态，不能据此排除其他初态/其他切片的混合稳定态。
- **Figure 9 跨阶段电流：** 每编码 `4阶段 × 3 seeded directions × 24条件`，共 288 对；三编码共 864 对。全部干预前历史与正式 baseline 在 10⁻¹² 以内相同；原实现中 control/perturbed 前史的精确同源检查亦保留。每编码独立手写 Euler 重放四个控制与对应脉冲试次、四个零脉冲对照，均匹配。全部 288 行 CSV 的四次 readout、R2/R3 中间分支与位置错误旗标、末次正确性及剂量逐行重算通过。
- **实际剂量：** 四阶段均为 50 ms，电流 RMS=0.25，RMS×时间=12.5 current·ms，全维平方电流积分=412.5 current²·ms。seed 是扰动方向，不是独立受训网络或动物。state-kick 另存 clipping 前幅度与 clipping 后实际 RMS，不能混用。
- **输入扰动投影：** 两种协议、三种子、三编码共 18 份归档，独立按固定 PC1/PC2 basis 计算全状态、投影内与正交补平方距离，均与源数组一致并满足能量分解。source-time 终态不使用固定场残差作恢复判据；fixed-clock 使用其实际固定外驱。两种协议已分开呈现。

## 实际图像检查

已实际打开十张 one_hot 主图拼图，以及三编码核心补图拼图；Figure 8 主图和 fixed-clock Figure 9 另以原分辨率打开。可见真实数据和坐标，没有空白占位、明显裁切或错误色标；rate 单位为无量纲，热图保留在对应距离/解码数学对象中。Figure 4/5 的条件重叠是真实共同投影现象；folded 距离近零被保留，没有制造分离。Figure 8 的六点没有圆周连线，收敛路径来自真实完整系统积分，切片非法域有独立颜色。Figure 9 固定时钟对照保留约 1.5 的全状态非零误差平台，投影外误差明显，没有把二维接近伪装成恢复。

有两个视觉解释限制必须随图注保留：六端点 PCA 存在退化特征值，平面中点的排列不是唯一几何形状；fixed-clock control 近一维，PC2 解释方差约 0%，该轴方向不唯一，不能把它解释为稳健的第二控制动力学方向。

最终增补的三编码 Figure 5 structural-controls 补图已实际打开拼图。源码直接读取正式 `subspace_geometry.npz` 的 `R3_angles`、`R3_folded_overlap` 与四个 `R3_b*_evr`，累计 VAF 使用真实累积和，没有重新定义 PCA。热图仅作为补充结构对照；主图仍是逐维角谱、双向方差捕获与时变几何。最终交付为 **55 组 PNG/SVG/PDF**。旧合并分类的临时 `fig08_state_kick_classes_branch*.csv` 已移除，正式七类来源统一为 `fig09_state_kick_classification.csv`，独立输出哈希清单已刷新，不索引已移除文件。

审计曾发现并反馈四项实现问题：Figure 9 CSV outcome 键不一致；中间 R2/R3 错误旗标遗漏分支身份；source-time 错用固定场收敛语义；state-kick 图中 `other` 合并 R3-inactive、outside-branch、unconverged。当前源码与派生 CSV 已修复，独立数值复算通过。最新三编码 Figure 8/9 已实际重新打开，state-kick 七类独立显示，横轴改为真实 postclip RMS。one_hot 分支0最高归档 preclip 幅度0.3时，约44.4%保留原位置却未完整恢复，约55.6%变为R3-inactive，完整状态恢复为0%；不能把位置保留率写成完整状态恢复率。最终版本图片/hash 复核状态记录在独立 JSON。

## 可复查命令

先按项目规则使用已核验的 `analysis` 环境，设置其根目录、Library/bin、Scripts 到 PATH 前端，并设置 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1`。执行：

```powershell
& C:\Users\Totheinfinity\.conda\envs\analysis\python.exe artifacts/neural_paper_figures_v3/reports/independent_check.py
& C:\Users\Totheinfinity\.conda\envs\analysis\python.exe -m unittest handcrafted_ei.tests.test_paper_v3_geometry handcrafted_ei.tests.test_paper_v3_numerics -v
```

测试实际输出保存在 `independent_tests.txt`。独立审计未重跑已有 baseline，全部新增重放使用审计进程本地数组，未写回历史轨迹或主模型文件。对历史归档的“未覆盖”证据限于正式归档校验与受保护源码哈希；本审计没有为仓库内所有未关联历史文件构造完整前后文件系统快照。
