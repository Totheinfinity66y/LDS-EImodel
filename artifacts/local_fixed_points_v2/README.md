# 本项目的局部稳定不动点相图

这组图回答：在sample=clock=0、保留原tonic背景的同一固定动力系统下，是否存在局部稳定不动点？答案是存在。没有修改神经元方程、权重、时间常数、任务或正常trial。

[One-hot主图](one_hot/fixed_point_portrait.png)

[1D Ring主图](ring/fixed_point_portrait.png)

[2D Topology主图](topology/fixed_point_portrait.png)

[完整状态恢复与谱诊断](one_hot/stability_diagnostics.png)

细蓝带箭头曲线是闭合的R3/对应I_decay_S二维子系统流线；实心蓝点是已在全部132状态中验证的局部稳定平衡；空心点是完整系统的鞍点。红线是闭合二维子系统的稳定流形，粗蓝两支由完整132状态自由积分产生。完整网络其余辅助坐标可以变化，二维红线不表示完整132维稳定集合。

两个实心点分别是静息控制态与同一选定R3单元的保持态，不是两个位置，也不是穷尽全网络吸引子的结果。R3单元通过归档实际活动选择；高态初猜在独立副本构造并积分，再通过完整场求根，不能称为直接记录的原始trial终点。三个编码在此所选局部回路方程相同，不能据此宣称完整表征相同。

闭合pair坐标的平衡为(0,0)、(0.9,0.76)、(1,1)。三编码完整场最大残差均≤1.32e−19/ms。两稳定点的广义三角Jacobian最大实部上界−0.008333/ms，Euler(dt5ms)谱半径上界0.958333；鞍点一个正方向+0.025/ms，Euler不稳定特征1.125。饱和折点处不依赖单个中点Jacobian判断：包含所有折点斜率的非对角依赖联合图无环，各对角区间具有同一严格符号，给出局部分类；不声称全局盆大小。

每个稳定点使用3个请求RMS剂量(0.001/0.01/0.03)与seed7/11/19，共18个完整状态扰动。状态裁切后的实际RMS与clipping fraction逐项记录；1600ms后最大完整状态距离2.083e−7。这是有限方向恢复证据，不是统计置信区间或全局吸引域估计；静息恢复不计作任务Response身份恢复。

图形语义参考[Janson与Marsden2017 Figure1](https://www.nature.com/articles/s41598-017-16994-y/figures/1)，是LDS方法适配（METHOD ADAPTED），没有执行作者B-vdP示例代码，也没有复制源曲线。坐标使用本模型真实无量纲率[0,1]。

复算：`python -m handcrafted_ei.visualization.plot_all --local-fixed-points`。依赖使用现有analysis环境。每编码保存PNG300dpi/SVG/PDF、analysis.npz、nodes.json、perturbations.csv及config.json；summary.json/provenance.json保留数据身份、受保护源码、环境与分析源码哈希。图像完整性见[figure_quality.json](manifests/figure_quality.json)；来源反审及独立审稿见仓库audit/local_fixed_points。77项回归已通过，首次红测试为新增模块不存在，随后3项新判据转绿。
