# LDS 本地数据审计

## 范围与结果

权威数据为本地 `handcrafted_ei/artifacts/v2/run`，未使用远端旧版作为模型。三编码 baseline zip 的SHA256通过，受保护源码全部匹配；三份衍生 recording.npz 的 rates 与原ZIP逐元素相等。Figure 1–10存在：55条figure记录、165个输出文件哈希全部通过；独立 dynamics cache 75个输出哈希全部通过。完整证据见 `AUDIT_EVIDENCE.json`，完整真实schema见 `DATA_SCHEMA.json`。

三编码one_hot/ring/topology均为 `(24,663,132)`，轴是 condition,time,neuron。每条件一条确定性轨迹，24不是重复试次。时间0–3310ms、dt5ms；率无量纲[0,1]，不是Hz。外部L输入分别6/1/2维，D/S各2维；内部Response66、共享Y6、全率132（81E/51I）。所有神经元含静息单元保留。群体与branch索引逐项写入schema，禁止由旧版neuron count推断。

样本0–200ms，delay结束1800，readout1=1900，to_R2=1910，readout2=2370，to_R3=2380，readout3=2840，to_R4=2850，readout4=3310。状态snapshot直接索引精确事件时刻，不插值、不用目标标签生成状态。

## 电流及来源

原ZIP完整保存rates/labels/times、task编码、事件、群体、干预边记录，但未逐步记录sample/clock/tonic电流。现有loader重建sample输入，新adapter重建全部三类电流并明确标记非实测。t行表示积分进入该状态的输入：sample_start < t <= sample_end；clock事件后 t>event生效。t=0无积分输入，返回零占位。tonic背景向量与实际I_tonic率神经元应区分；后者本来就是全状态的一部分。

新增adapter单独重算3×24×662个Euler转移，误差阈值3e-15全部通过，同时核验sample重建与已有loader一致。因此不是只验证shape。adapter不改变模型、连接、参数、任务或正常simulation。

## Figure 8/9专项发现

1. 旧动力学snapshot只有各编码6个L，固定D=+1,S=1，各4stage。不是R3的24个条件；全24 R3必须从原baseline提取。新extract_snapshots已提供真实24状态及clock/tonic/stimulus。
2. 旧Fig9干预从tonic-only endpoint作一次性clipped率状态kick，无50ms输入扰动。不可通过transpose转换为Zhou源实验，必须单独重跑输入协议。
3. L0/R3全网络amplitude=.3 seed7三编码均：full L2从2.06987289到1.49999997，2PC投影从0.128448164到4.67e-9，投影能量占比从0.003850955到9.68e-18。二维轨迹重合确实遗漏几乎全部最终差异，不代表恢复。
4. endpoint-centered PCA有5个完全简并奇异值1.5，另一个约1.78e-16。2PC选择不是唯一的科学轴，必须披露；不能把两PC当完整状态空间。
5. 已存offplane vector-field norm，但旧图缺少扰动能量分解。任意endpoint-PC网格的flow属于LDS诊断，不能标称Zhou Figure7源方法。
6. 旧扰动报告目标clip前RMS与全网络clip后RMS，未逐项保存目标实际RMS和clip fraction。需要新增指标，不能只更换横轴文字。
7. 旧源实验无原始spikes/session/left-right试次划分，也无256训练RNN状态；只能明确METHOD ADAPTED。方向种子不代表独立网络/动物，不能生成源论文统计。

## Adapter验收

实现：`handcrafted_ei/evaluation/reference_adapter.py`；测试：`handcrafted_ei/tests/test_reference_adapter.py`。API：load_audited_dataset、reference_axes、reconstruct_currents、extract_snapshots。显式transpose，无trial averaging、滤波、归一化、repeat制造、目标状态注入。编码/配置混淆、重复条件、轴错误、缺失事件均拒绝。

`tests_red.txt`记录实现前missing-module红测试；`tests_green.txt`记录5/5通过。此处是数据接口验收，原论文算法与最终图片忠实度由论文专家另行审查，不能由本报告代替。

## 环境与限制

使用已存在analysis env Python3.12.12、NumPy2.3.5、SciPy1.16.3；只为当前进程prepend env/Library/bin/Scripts解决DLL启动问题，没有安装或修改全局依赖。项目requirements声明numpy>=2、scipy>=1.11等，与已核验环境相容。旧archives不覆写。原图视觉审查及新的动力学结果不属于本数据agent的独立验收范围。
