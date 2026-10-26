# LDS-EImodel：当前实现与科学验收报告

## 结论与范围

本次已实现直接兴奋性门控、真实tonic I背景抑制、Response触发的规则记忆终止，以及三种外部位置编码。冻结任务、共享Y、readout-first、固定拓扑与Dale约束维持；无训练、标签辅助、状态硬覆写或新增依赖安装。

结论为PASS_WITH_LIMITS：核心行为与机制验收通过；位置比较仅改变外部编码，内部六位置网络不变；扰动恢复只支持有限局部稳定性，不能推为连续吸引子、全局盆或编码优越性。

## 关键动力学

矩阵按[post,pre]，W≥0，突触前符号s_j决定E/I作用：

$$ \tau_i\dot r_i=-r_i+\phi(\sum_j s_jW_{ij}r_j+b_i+u_i+c_i-\theta_i),\quad\phi(z)=\min(1,\max(0,z)). $$

$$ \tau_E\dot g_a=-g_a+\phi(.9m_a+c-1),\quad c\in\{0,.9\}. $$

$$ \tau_E\dot m_a=-m_a+\phi(2m_a-.3-I_{comp,a}-3\sum_q z_q+u_a),\quad120\dot z_q=-z_q+\phi(2.4r_q-1.4). $$

q分别逐一取R2/R3单元，仅终止M_D/M_S。阈值前不汇总全Response；慢积分避免瞬态触发。递归W不变，反馈增加抑制性电流，不能等同于乘法gain调制。132个率状态（81 E/51 I），dt5 ms，τ_E40、τ_I20、τ_decay120 ms。

下游静息偏置−.9；source最大.8、gate最大.64，单独亚阈，组合.54。已亮状态无gate仍有2−.9=1.1维持。详细时序、参数和模块接口见[architecture.md](../architecture.md)。

## 测试与行为证据

- 当前32/32测试通过，见[测试日志](../handcrafted_ei/artifacts/v2/tests_full.txt)。
- 7类故障注入全部RED、恢复后GREEN：Dale、memory、直接激活、反馈衰减、提前路由、tonic、分支继承。见[变异检查](../handcrafted_ei/artifacts/v2/mutation_checks.txt)。
- 三编码各24/24，逐stage均[1,1,1,1]；无噪声seeds7/11/19结果相同。
- 全部198组、4,752个trial：A/C及gate阻断分别损伤R2后/R3后；B/D在交接后切memory输出仍全部正确；提前去memory维持损伤对应阶段；延迟许可1500 ms仍24/24。
- source、gate、clock缺项负对照、未来阶段静息、target代理隔离、固定拓扑、Dale、六位置变换均有自动化测试。

## 记忆交接与终止

下列为baseline条件0，三编码及全部条件时间/幅度见[memory.json](../handcrafted_ei/artifacts/v2/run/memory.json)。

| 量 | M_D | M_S |
| --- | ---: | ---: |
| 对应Response持续超过.9时刻/ms | 2035 | 2505 |
| 半活动时刻/ms | 2100 | 2570 |
| 形成后至半活动延迟/ms | 65 | 65 |
| 80–20%拟合有效τ/ms | 37.59996 | 37.6 |
| 门控前最小活动 | 0.9942875 | 0.9942875 |
| 终末活动 | 4.266723e-15 | 1.205988e-09 |
| sample结束后AUC/rate·ms | 1907.07 | 2377.07 |

形成至半活动的65 ms包含反馈延迟，不是纯指数半衰期。拟合有效τ对应指数半衰期约26.062 ms。R2/R3交接后选择分支margin约1；两类memory降到.05以下后，所选Response仍接近1。

切Response→I_decay反馈，memory终末仍>.9；行为仍可正确，因此这项机制的否证指标是终止失败。M_S不因R2形成而衰减；无许可或延迟Response时memory继续保持。短脉冲和多个弱Response状态不触发错误终止。

## 三编码比较

| 编码 | σ=.03（seed7/11/19） | σ=.2 | σ=.6 |
| --- | --- | --- | --- |
| one_hot | [24, 24, 24] | [24, 24, 24] | [19, 19, 19] |
| ring | [24, 24, 24] | [21, 17, 21] | [12, 9, 12] |
| topology | [24, 24, 24] | [23, 20, 21] | [11, 11, 14] |

每个数字分母为24。原始坐标期望噪声能量σ²，神经电流L2归一化；实际映射误差记录在manifest。由于坐标和非线性映射不同，不能把同一σ直接当作同一神经误差，不能由本表宣称编码优越性。

one_hot/ring/topology外部维度6/1/2，内部均六位置。ring/topology无噪声宽调谐电流相同；三模式settled Response几何相同。Response中心化rank为5/11/23/23，PR对应约5/11/23/23；不是1/2/4/4。分支内六位置中心化rank5，固定分支坐标影响principal angles。内部位置两两距离近似相等，圆环邻接没有在settled几何中保留；相关系数因此记null（无距离方差），不是填0。

全部Response轨迹、trial平均轨迹、PCA得分/成分、SVD/VAF、PR、活跃比例、选择性、位置距离与衰减后稳定性见[representation.json](../handcrafted_ei/artifacts/v2/run/representation.json)。

## 吸引子与有限盆扫描

每编码采样6个L×4个readout状态，D=+1、S=1，共24个快照；三编码共72。不是全部规则分支的穷尽盆扫描。关闭sample和全部clock，保留tonic；与保留阶段电流的受迫对照分开。

- 72/72自由演化终态残差<1e−8/ms，最大约4.28e−11/ms；Euler谱半径最大0.958333。
- 每编码采样24个可区分终态；不能推断网络总共只有24个吸引子。
- 每快照4幅度×3seed，共864个扰动；另216个随机初态轨迹。

| RMS幅度（clip前） | 每编码恢复/72 | 其他结果 |
| --- | ---: | --- |
| .02 | 72 | 所有采样扰动恢复 |
| .1 | 24 | 48进入其他收敛状态 |
| .3 | 9 | 1跳至另一采样态，62进入其他收敛态 |
| .7 | 0 | 72进入其他收敛态 |

支持所测饱和递归网络附近的局部稳定离散固定点；恢复范围有限，较大扰动可产生非任务状态。未证明连续吸引子、自主阶段转换、全局吸引域、生物真实性或所有分支的稳定盆。Jacobian在分段线性阈值处用对称导数，属于局部诊断。

## 归档和独立复算

- [行为复算](../handcrafted_ei/artifacts/v2/run/verification.json)：198个压缩包、4,752个trial，重建输入、Y、窗口、独立真值、行为和memory指标，PASS。
- [分析复算](../handcrafted_ei/artifacts/v2/run/analysis_verification.json)：72个baseline、72快照、864扰动，重建表征、谱与每一步自由/受迫/扰动/随机初态Euler更新，PASS；最大更新误差约1.11e−16。
- [拆包核验](../handcrafted_ei/artifacts/v2/run/sharding_verification.json)：1368数组完全相同，72个NPZ分包，最大3.82 MB；[索引](../handcrafted_ei/artifacts/v2/run/attractor_trajectories/index.json)记录SHA256。
- [完整实验协议](../handcrafted_ei/artifacts/v2/run/manifest.json)、[配置](../handcrafted_ei/artifacts/v2/run/config.json)、[环境](../handcrafted_ei/artifacts/v2/run/environment.json)、执行时源码及最终源码哈希均保留。
- 执行后改动限于文档、报告和无损归档/复算逻辑；独立audit确认执行的model/config/simulation/task源码未漂移。

## 当前模块

- [输入与独立真值](../handcrafted_ei/task/__init__.py)
- [位置编码](../handcrafted_ei/model/location_encoding.py)、[固定连接](../handcrafted_ei/model/connectivity.py)、[网络动力学](../handcrafted_ei/model/ei_network.py)
- [时序与干预](../handcrafted_ei/simulation/__init__.py)
- [记忆指标](../handcrafted_ei/evaluation/memory.py)、[表征](../handcrafted_ei/evaluation/representation.py)、[吸引子检测](../handcrafted_ei/evaluation/attractors.py)
- [完整实验](../handcrafted_ei/evaluate.py)、[行为复算](../handcrafted_ei/receipt.py)、[分析复算](../handcrafted_ei/recompute.py)
- [当前验证与清理记录](../handcrafted_ei/artifacts/current-cleanup/REPORT.md)

## 复现与Git纪律

```text
python -m unittest discover -s handcrafted_ei/tests -v
python -m handcrafted_ei.evaluate --output <fresh-directory>
python -m handcrafted_ei.receipt <directory>
python -m handcrafted_ei.recompute <directory> --report-directory <fresh-report-directory>
```

使用已预检analysis绝对解释器或run.ps1，CPU。未安装环境、未训练、未推送。全部本次未提交文件须按AGENTS工作流发起Nimbalyst提交提案；只有用户确认且读回commit后才标记已提交。
