# 科研重绘方法与复现

## 数据身份与运行环境

本轮只读正式v2归档。三编码各24条确定性条件、663个时刻、132个率单元（81 E/51 I）；0–3310 ms，dt=5 ms。REC逐值对照RAW ZIP，输入SHA256和受保护源码匹配结果见 manifests/data_audit.json。input_currents、clock由编码、配置、事件重建，不能称为原始实测电流。

已实测环境：analysis，Python3.12.12、NumPy2.3.5、SciPy1.16.3、Matplotlib3.10.7、PyYAML6.0.3、scikit-learn1.7.2、Pillow12.2.0，CPU。直接启动Conda Python前须在当前进程PATH加入该环境及Library/bin/Scripts，避免Windows DLL导入失败；没有安装或升级依赖。

```powershell
$env:PATH='C:\Users\Totheinfinity\.conda\envs\analysis;C:\Users\Totheinfinity\.conda\envs\analysis\Library\bin;C:\Users\Totheinfinity\.conda\envs\analysis\Scripts;'+$env:PATH
$env:OPENBLAS_NUM_THREADS='1'
& C:\Users\Totheinfinity\.conda\envs\analysis\python.exe -m handcrafted_ei.visualization.plot_all --paper-figures --encoding all
& C:\Users\Totheinfinity\.conda\envs\analysis\python.exe -m unittest discover -s handcrafted_ei/tests -v
```

`--figures 4,5` 可选择图片；Figure10必须使用all编码。新出口独立于所有历史归档；图像缓存若未实现则重新分析，不把文件存在当验证通过。大数组留本地并由manifest或receipt的SHA256索引。

## 计算定义

F01–02直接使用原率，不跨L平均后再推断位置选择性。各分支活动取其六单元最大值，选择裕量为所选支活动减最大竞争者。选择标签仅作离线分组，不写神经状态。R1无竞争者，其竞争和裕量为NA。活跃阈值0.1，E/I活跃比例分母分别保留全部E/I单元。

F03规则轴是平衡全因子条件的规则质心差；Memory轴在delay_end、Response轴在对应readout拟合，保存轴、中心、锚点与每trial投影。真实feedback-block与随机feedback、交接前后A/B/C/D及seed7/11/19匹配随机消融从原归档复用。活动衰减、探针可读出性和下游因果必要性分别报告。

F04复用并核对每编码global PCA：全部24条件、全部132单元、时间stride4拟合，共享一个中心和基。完整状态速度为相邻时刻L2位移除dt，投影仅作展示。L/D/S轴按保存的实际条件对比方法命名，不称dPCA或jPCA。

F05每branch六位置状态中心化SVD，奇异值阈值max(1e-8,s_max×1e-8)，方差阈值1e-8。主角度由Q_a转置Q_b奇异值的arccos获得；低方差/零秩为NA。双向cross-VAF分别用各自能量归一化，within-VAF为相同全秩基的参照，不能当泛化性能。whole/Response/shared分开坐标；质心距离按完整所选坐标计算，另报告固定互斥支持与折叠位置支持对照。

F06固定D=+1/S=1，在同一R3分支取六个位置的真实状态，保存PCA基和中心。RDM是原率空间欧氏距离；不人为形成六边形、不连接成环。position identity和margin只在已指定活动分支计算，drift参照R3读出完整132维状态。

F07复用带split身份的nearest-centroid条件留出，tie用fractional credit。独立噪声seed probe是另一种泛化协议，独立展示。新four-way branch probe只在R3转移后有意义，之前mask，使用不相交条件fold，不能向模型反馈输出。低于chance的结果保留，不当作绘图错误。

F08按固定D/S分别展示六位置端点，sample=clock=0，原tonic保留。全132维残差、连续最大特征实部、Euler谱半径和clip折点的分段级联证书共同报告。折点处代表Jacobian用斜率0.5，其谱不能单独证明稳定。真实state-kick轨迹及actual postclip剂量复用REF；身份约束恢复不能由PCA重合替代。

新增二维初态切片每branch 41×41网格，非法[0,1]率状态mask而不clip；合法初态完整132维积分2000ms。预定义six-mean plane保留为负对照；额外three-endpoint plane使用前三条件端点均值和其实际活跃位置对比轴。两个plane分别保存，未匹配的平衡态、未收敛和非法状态不并入六目标点。切片不是全局盆，更不是全部吸引子的穷尽。

F09分别展示旧单trial有限输入与state kick；新增24条件×3时段×3方向的50ms外电流，whole132实际RMS0.25，seed7/11/19。阶段以记录事件定义，方向跨阶段/编码一致。control按真实sample/clock逐步重放并对照REC，完整状态距离、R4分支/位置与正式Y窗口行为分别归档。共享时序下恢复不是自主共同向量场恢复。

F10联合PCA用三编码等权样本、全部条件/单元、stride4；one_hot固定基是敏感性对照。匹配电流实验使用R3转移后100ms、50ms持续输入、full132 RMS0.05/0.2/0.5，所有编码共享方向；它是相同神经电流注入，不是对三种原始L坐标的同分布噪声。原归档sigma_L0.03另在fig10_raw_noise_doses.csv报告原坐标维度/剂量及映射后实际R1电流剂量。恢复要求R4身份保留及相对配对control的全状态Linf<0.02；行为比较用正式20ms窗口及配置阈值。

## 统计、来源与解释边界

baseline每条件一条确定性轨迹，24条件不是24次独立重复；三个seed是固定电流方向或输入噪声实现，不是训练网络或动物重复。没有伪造SEM/CI、显著性、缺失值或源论文曲线。所有率无量纲，不使用Hz。

参考题名/DOI/panel与图注基于本地正式来源目录；本轮实际打开Kobak1/3、Churchland2/3、Mante2/5、Gallego3、Kriegeskorte2的原图联系表，核对布局语义。Inagaki和Zhou由独立来源审阅记录。Churchland/Gallego的无效PDF不作PDF证据，独立有效panel仍可核验。所有新图均为LDS数据的方法适配，没有声称执行缺失的原作者数据/权重/完整算法。具体范围见docs/figure_redraw各审阅文件及逐图caption。

逐图文件检查、实际打开记录与独立数值验收分开；完整输出哈希在各manifest，综合索引为figure_manifest.json。模型/task/simulation/config哈希必须持续匹配，发现不符即停止。
