# Handcrafted E/I Decompression v1

当前主线为固定连接、不训练的 E/I rate network：直接接收 L/D/S 编码电流，由 R1 活动、M_D/M_S、两层真实 I→I 去抑制、Response 分支继承和四次在线共享读出生成六位置环上的四项序列。

- [完整架构](architecture.md)、[开发约束](AGENTS.md)、[M0–M5验收](todo.md)
- [神经元方程](handcrafted_ei/model/neuron.py)、[固定拓扑](handcrafted_ei/model/connectivity.py)、[网络](handcrafted_ei/model/ei_network.py)
- [运行时钟](handcrafted_ei/simulation/__init__.py)、[配置](handcrafted_ei/config/baseline.yaml)

L∈{0,…,5}，D∈{−1,+1}，S∈{1,2}。环境真值为 [L,L+D,L+D+DS,L+2D+DS] mod6；模型不接收该数组。例：(0,+1,2)→[0,1,3,4]。104个归一化率状态、统一bounded-ReLU Euler动力学、一个六位置Y。所有位置转移连接在初始化时固定；外部clock只提供时间。

## 运行与证据

需要Python、NumPy、PyYAML、Matplotlib，见[声明依赖](handcrafted_ei/requirements.txt)。Windows已验证使用analysis环境的CPU NumPy，不需要GPU或安装新包。

```powershell
.\handcrafted_ei\run.ps1 -Test
.\handcrafted_ei\run.ps1
```

其他环境：

```bash
python -m unittest discover -s handcrafted_ei/tests -v
python -m handcrafted_ei.evaluate --output results/v1-run
```

输出目录已有manifest时拒绝覆盖；默认归档到handcrafted_ei/artifacts/v1。每个试验保存逐步全体E/I rates、标签、Y、事件与干预连接，输入与target独立保存；配置、源码SHA256和环境版本同时归档。评估包括24条件、A/B/C/D与等剂量随机对照、delay/噪声/gate/recurrence扫描、SVD与分支内位置维数。实际数值以生成报告为准。

当前验证：16/16测试通过；无噪声24/24，四stage均100%；A/C出现阶段特异退化，B/D保持24/24。39个实验、936个trial已从保存的轨迹独立复算通过。见[完整报告](handcrafted_ei/artifacts/v1/REPORT.md)和[复算记录](handcrafted_ei/artifacts/v1/verification.json)。

每个实验的ZIP保留24套task/events/rates文件，展开目录仅为本地副本。可独立复核：`python -m handcrafted_ei.receipt handcrafted_ei/artifacts/v1`。位置噪声σ=0.03的三个种子均24/24；更大噪声可退化，不代表普适鲁棒性。

这验证给定primitive后的解压缩机制，不是primitive推断或学习。固定分支坐标会影响分离角；不能据此宣称涌现正交性、低秩或连续吸引子。

## 历史实现

[lds_decompressor](lds_decompressor/README.md)、[LDS_prechosen](LDS_prechosen/README.md)保留为历史实现；其测试与旧坐标/机制不能替代v1验收。v1不导入这些包。
