# Source-to-LDS 数据兼容与实验适配

详细机器契约由独立专家生成：`audit/paper2agent/{inagaki,zhou}/INPUT_CONTRACT.json`、`FIGURE_CONTRACT.json`；真实LDS schema见 `audit/data/DATA_SCHEMA.json`。本表不替代原方法。

| 字段/分析 | Inagaki | Zhou | 实际处理 |
| --- | --- | --- | --- |
| rate量与轴 | ADAPT：实验spikes→rate；ED模型4群 | ADAPT：256 recurrent rates | LDS无量纲132全率；24×663×132，无单位转换冒充Hz |
| 时间/条件轴 | ADAPT | PASS显式transpose | `reference_axes`返回663×24×132，不reshape造repeat |
| session/重复 | INCOMPATIBLE | 17训练网络INCOMPATIBLE | 每条件一次确定性trial，seed仅外投射/扰动方向，不SEM/bootstrap |
| 原CD与预处理 | INCOMPATIBLE原左右选择split-half | 原PCA fit集合unknown | LDS两个预声明条件pairwise CD；PCA control-only并归档center/basis/window |
| clock/sample/tonic | 固定场需RERUN | 正常时序配对需RERUN | 重建字段明确reconstructed，47,664步完整Euler验证 |
| 24状态共同field | LDS-specific ADAPT | 非源目标 | 全部R3实际snapshot，sample/clock均0、原tonic保留 |
| 原始phase-line | ADAPT：deterministic pair trace | 无此Fig7 panel | 真实10ms隔点，中心差分/2标per10ms，无session分箱统计 |
| 有限输入扰动 | 原PV通道INCOMPATIBLE | RERUN：50ms、.25、cue+500ms | 新增source-time和R3-fixed-clock两实验，whole132固定signed投射RMS1 |
| frozen noise | 实验重复缺失 | ADAPT：成对全零noise | 数组实际保存，不称noisy robustness |
| 状态kick | LDS-specific ADAPT | 不可等同原输入 | 原状态扰动独立label，加入实际clip剂量及局部小幅 |
| 完整距离 | 全状态数学诊断ADAPT | PASS Euclidean公式 | D[control time,perturbed time]，不除√N |
| velocity field | LDS-specific | Fig7没有该panel | 单独flow补图，完整f及off-plane保存 |
| 数值谱 | 不是源实验图 | 不是源Fig7 | 完整132状态、FD/Euler、折点代表谱与DAG证书分开 |
| 原统计图完整重画 | BLOCKED source data/runtime | BLOCKED weights/raw/pipeline | 不制造17网络/动物数据；源图对照中列synthetic明确注明 |

## 数据流

原始ZIP/hash及protected source → 严格loader → 重建电流逐步验算 → 实际24个R3状态 → 同一固定场/独立配对输入 → 完整数值与投影分解 → spec绘图 → 原专家反审 → fresh reviewer。

完整配置在各编码 `lds_results/<encoding>/config.json`，位置/分支映射及来源在 `audit/data/DATA_SCHEMA.json`；大型全率盆轨迹不复制，manifest记录其SHA256并由CLI重建。源raw、原模型、历史图均不覆写。
