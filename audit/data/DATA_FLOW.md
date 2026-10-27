# 数据流与所有权

```mermaid
flowchart TD
 A[本地v2 baseline ZIP + archives.json] --> B[SHA256 + protected source identity]
 B --> C[population_data.load_dataset]
 C --> D[rates condition × time × neuron]
 C --> E[task/events/config offline metadata]
 D --> F[reference_axes 显式transpose]
 D --> G[extract_snapshots 精确readout索引]
 E --> H[reconstruct_currents]
 H --> I[3 × 24 × 662 Euler transition tests]
 G --> J[独立固定场动力学评估]
 F --> K[论文契约指定算法]
 J --> L[全状态数值与投影诊断]
 K --> M[Figure specification / renderer]
 L --> M
 M --> N[同一论文agent反向忠实度审核]
 N --> O[独立科学review]
```

- raw rates/labels/times来自ZIP NPZ；task/seed/encoded input来自task JSON；population/events/interventions来自events JSON。
- archive配置来自manifest；neuron E/I与sample/clock/tonic由protected-code identity一致的模型构建信息重建。保存真实与重建字段的界限。
- `target`只保存在offline任务信息，不传入神经网络，不用于构造snapshot或决定分支。
- reference_axes不决定CD/PCA/距离算法；论文agent拥有原方法contract，主agent负责复现实现与适配。
- 原始数据、旧Figure与旧metrics只读；新代码只写数据audit与新reproduction archive。
- `audit/data/`与reference_adapter.py/test_reference_adapter.py由Agent C独占写入；不会同时修改主agent动力学/renderer。
