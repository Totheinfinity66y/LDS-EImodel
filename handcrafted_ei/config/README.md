# 配置与实验参数

[baseline.yaml](baseline.yaml)是主模型完整配置；[架构规格](../../architecture.md)给出方程和时间轴。权重为非负magnitude，符号来自突触前身份。率/电流/权重无量纲，时间ms；参数未经生理数据拟合。

location_encoding：one_hot/ring/topology；encoding_kappa=4控制连续编码非负调谐宽度。内部每支6单元。通过EINetwork(overrides=...)切换；task.encode须使用一致mode和kappa。每个实验归档完整解析config。

sample/delay/transfer/retire/readout/decision/gap=200/1600/200/160/100/20/10 ms，均为dt=5整数倍。tau_e/i/decay=40/20/120 ms。初始率0，仅两个tonic I初始化为稳态1。

w_rec=2；w_tonic_r1=.1、w_tonic_response=.8、w_tonic_memory=.2分别控制起点、下游与规则背景抑制。tonic_i=1是实际I率单元驱动。

w_mem=.9、clock_activation=.9、theta_activation=1构成规则与clock重合；w_activation=.8提供亚阈分支许可。第三级clock_activation3=1、theta_activation3=.2，不输入规则。

w_response_decay=2.4、theta_decay=1.4、tau_decay_ms=120为逐Response单元慢检测；w_decay=3抑制对应memory。递归权重不被事件修改。

noise_sigma为原始坐标RMS范数，每坐标SD=σ/√dim。task.encode在sample开始一次采样，ring wrap、topology径向归一化；神经电流L2归一化。D/S无噪声。evaluate记录实验seed、每条件派生seed、输入及实际电流偏差。

消融用独立网络与完整配置：w_activation=0、w_response_decay=0、tonic投射为0、w_rec=0、clock_activation/3=0。memory decay和tonic必要性分别看终止与暗态泄漏，不强制所有消融都损伤行为。
