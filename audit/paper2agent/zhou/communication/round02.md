# Round 2：LDS 数据与协议适配咨询

agent_id: /root/zhou；paper_id: zhou2023；task_id: B；status: ADAPT/RERUN/INCOMPATIBLE explicitly separated。

## 完整 request

主Agent提供：三编码rates=(24,663,132)，t0..3310、dt5，每LDS条件单次，无过程noise，无训练网络；132=81E+51I，外部L维6/1/2而内部同。旧Fig9是R3自主终点瞬时state perturb，原轨迹末期稳态。拟新跑50ms additive input perturbation、sample onset+500ms，双方同一content-free clock/sample schedule；因无原π通道，seed7/11/19固定随机whole-network projection、幅值.25，允许正负外电流且明标LDS adaptation；noise矩阵均0；无17网络故不SEM。PCA只fit control whole-state，full-state cdist、投影/正交能量，flow单列。询问逐项分类、onset适配和定量接口。

## Response

|项目|判定|条件|
|---|---|---|
|time/trial/neuron轴|PASS|transpose显式；24是条件，不是独立训练网络|
|132 whole-network代替256 recurrent|ADAPT|标whole-network；response-only另列，不混指标|
|dt5代替作者默认dt10|ADAPT|保留真实时间，不为同采样伪造时间点|
|旧终点state kick|RERUN|不能转成50ms输入扰动|
|50ms输入窗、cue+500ms|ADAPT|保留原elapsed-time，并说明本模型处持久delay，非原动态WM任务|
|R3窗口输入扰动|ADAPT|独立第二实验，stage-targeted LDS diagnosis，不合并为源原协议|
|随机whole-network ±电流投射|ADAPT|不存在原π通道，必须明确输入标量和投射向量归一化、E/I受扰范围、实际电流RMS及积分剂量|
|frozen noise全0|ADAPT|合法同噪声配对，但只说明确定性恢复，不是 noisy robustness 复现|
|17训练网络SEM/箱须|INCOMPATIBLE|不使用24条件/3投射seed冒充训练网络重复|
|control-only PCA fit|ADAPT|原fit集合unknown；统一中心和basis用于两条件|
|全状态Euclidean|PASS|不得静默变成RMS；RMS是另列LDS指标|
|局部flow|ADAPT|不是Zhou Fig7原panel，另行LDS诊断|

定量接口建议保存 `rates_control[T,N]`、`rates_perturbed[T,N]`、`time_ms[T]`、`input_control[T,N]`、`input_perturbation[T,N]`、`noise[T,N]`（本实验确为0）、`schedule_id`、`state0_hash`、`projection[N]`、`projection_seed`、`onset_index`、`offset_index`、`actual_current_rms`、`integrated_current_L2`、`population_ids`。50ms窗用 `[onset,onset+50)`，dt5应10步。不得复用不同clock时间的轨迹作控制。

原图视觉核验：实际打开 `figure7-source-page10.png`；a黑红单元轨迹与3PC带时间球，b cross distance，c三task mean±SEM及箱须；没有velocity-field。Methods页已渲染，尚未全部18页视觉审阅。

输入：主Agent传入已审计schema；输出：本轮意见。Open questions：actual adapter/source metrics/plots待第三、四轮。
