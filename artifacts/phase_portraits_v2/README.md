# 本项目三编码状态流线相图

这里是本项目实际动力学计算得到的论文式三列流线图，均提供PNG300dpi、SVG、PDF。科学机制与参数未修改，不包含训练。

[One-hot](one_hot/phase_portrait.png)

[1D Ring](ring/phase_portrait.png)

[2D Topology](topology/phase_portrait.png)

每编码另有 `projection_diagnostics.png`、`phase_portrait.npz`、`diagnostics.csv`、`endpoints.csv`、`config.json` 与 `provenance.json`。总计3张主图、3张补图、18份图文件。

## 图中表示什么

三列为Autonomous hold、R3 clock held、R3 retired，均关闭sample、保留原tonic，clock固定在相应配置值。各条件从内容无关初态真实积分2000ms得到自己的背景平衡点，因此是不同origin的平行状态切片，不能称同一全状态受不同clock的瞬间比较。

共同方向B来自两个由实际R3活动选择的、同branch相对位置的已归档终点，减去tonic-only静息背景；L/D/S仅作离线来源记录，不参与状态选择或路由。横纵轴lambda是本项目率状态平面的展开系数，**不是PCA，也不是原论文膜电位**。

数学定义为r_c(lambda)=background_c+B lambda；dual=(BᵀB)⁻¹Bᵀ；二维速度=dual·f(r_c)。每格先计算完整132维field，再投影。非法率点mask而不clip，本次3×3×5041个点全部合法。

蓝色连续流线沿这个投影切片场积分；红线是12组初态在完整132维模型中真实积分后投影，主图固定展示其中4个网格初态。不是用二维流线冒充完整神经轨迹。编号实心参考点仅表示完整field残差<1e−8/ms，空心编号点只是坐标参考，不据此认证稳定性或吸引子。

## 必须保留的真实结果

- 前两列流场相同：已形成的R3位置状态不需要继续依靠阶段clock保持。退役列则回到静息。这是当前网络的真实结果，不能为了模仿原图制造三种不同流场。
- 当前结构允许所选两个位置共同保持，因此显示1+2共同活动的平衡参考点，不能隐藏它来强凑原论文两个模式互斥。
- 平面不是不变流形。保持/clock两列场平面外比例中位数37.268%，退役55.344%；真实轨迹最大离面距离分别.206125与.436237。这些数字已直接印在主图，完整分布见补图。不能将蓝流线的分区直接解释为完整系统吸引域。
- 正式积分dt5ms。独立dt2.5ms复核终点活跃身份全部一致，终点差最高约1.33e−8，但瞬态单元率差可达.0537；不能声称整段连续时间轨迹已高精度收敛。36/71网格共点的解析field误差为0。
- 三编码此次共同内部状态平面给出相同图，不由此声称输入噪声或所有试次相同。

## 来源与审核

用户参考截图已核实为Saighi & Rozenberg (2025), *Autonomous retrieval for continuous learning in associative memory networks*, Figure2，DOI10.3389/fncom.2025.1655701。原图用两个储存膜电位模式张成的平面、训练/抑制条件；本项目仅适配其全场投影与视觉组织，使用真实率状态和clock/退役条件，明确METHOD ADAPTED。

来源专家合同与反审：仓库 `audit/phase_portrait/source/`。新fresh reviewer独立代码、全量grid/path、步长复核及最终视觉验收：`audit/phase_portrait/reviewer/`。原论文PDF与原图仅本地保存，不提交或发布。完整文件和代码SHA256在manifest.json。

## 复现

```powershell
$env:PATH="C:\Users\Totheinfinity\.conda\envs\analysis\Library\bin;"+$env:PATH
$env:OPENBLAS_NUM_THREADS="1"
$env:OMP_NUM_THREADS="1"
& C:\Users\Totheinfinity\.conda\envs\analysis\python.exe -m handcrafted_ei.visualization.plot_all --phase-portraits
```

单独只重绘可运行 `python -m handcrafted_ei.evaluation.phase_portrait --render-only`。历史图与历史科研归档不覆盖。当前正式输出是Euler5ms的独立评估，不会写回正常模型。
