# 独立科学审稿

审稿人：Agent F，独立于论文转换协调者、数据适配、数值实现及绘图实现。审稿文件只写入 `audit/reviewer/` 和本报告。

最终状态：**PASS_WITH_LIMITS（LDS METHOD ADAPTED，Gate5独立验收通过）**。原论文原实验/完整作者Figure执行仍 **BLOCKED**；本验收不将其改为成功。

## 独立证据

- `audit/reviewer/fresh_check.py/json`：仅导入保护模型的系数，不调用生产adapter、field、Jacobian、PCA、距离或稳定性函数。取不同于数值审计员的trial/time/seed样本重新计算三编码结果。Euler转移误差≤5.56e−17，非终点平滑Jacobian有限差分误差≤8.13e−13，端点距离误差0，PCA能量分解误差≤1.12e−16，cross-temporal sample误差≤1.12e−16。50ms输入与同一零noise矩阵验证通过。
- 同脚本独立从保存的recording.npz及事件窗口重建R3 branch0/3样本并做SVD：三编码PR≈4.99999945，whole-state mean principal angle83.3515072818°，与归档CSV差0。另从E-only basin row173的seed/幅度重建clip后状态、实际目标RMS和clipping fraction，误差均0。
- `audit/reviewer/PACKAGE_FRESH_REVIEW.md`：本人实际读取本地Paper2Agent/Paper2Skill规则，独立执行两篇 `verify --strict`，Zhou为reviewed、Inagaki为reviewed_with_limitations；两者exit0/mechanical_ok。核对全页review记录，并抽样对照最终包与可见原页的Fig7/Methods/摘要/checkbox、Inagaki Fig5/6和reporting summary。不是本人替两专家签署全48页阅读。
- `audit/numerical/independent_check.py/json`来自另一位数值审计者，与本人的fresh_check为两套独立实现，不混淆作者身份。

## 方法、接口与实验协议

原实验Fig5/6的ALM放电、左右选择、session和重复试次不存在于LDS；Zhou Fig7的17个训练网络、完整recurrent活动/权重及绘图入口亦未提供。Zhou真实运行的作者函数是task.generate_trials，而非原Figure7。Inagaki作者MATLAB未执行。以上缺口是**DATA INCOMPATIBLE / SOURCE EXECUTION BLOCKED**，不能被Skill阅读包严格通过或合成函数单元测试覆盖。

LDS数据为三编码各24个不同条件的一条确定性轨迹，132维无量纲率，不是24次统计重复。adapter显式transpose，原样保留condition/trial身份；原始电流缺失时依据保护代码与真实事件重建，注明非实测。所有状态来自真实轨迹，无目标状态注入。PCA仅使用control拟合，距离在全132维计算，二维投影外残差被保留，未删静息神经元。与原作者未公开的精确PCA拟合集合不强行等价。

LDS新增50ms输入试验与state-kick严格分开。前者使用全网随机电流方向；原文是π/第17输入经随机投射。相同标量0.25不代表相同神经电流剂量；LDS绝对500ms和原文cue+500ms也须按真实对齐说明。共享全零噪声只能称noise-free paired adaptation，不是原文非零frozen noise复现。R3固定clock延长试验与正常task-time重放是两个不同系统条件。任意PC网格流场明确称LDS诊断，而非原Zhou Fig7面板。

## 动力学结论

24个R3初态放入同一个sample0/clock0、原tonic保留的向量场，所得24个task-seeded末端cluster保留24/24位置/分支身份。独立重算末端最大field残差4.27557e−11 rate/ms；相同Euler谱半径0.9583333333来自慢I_decay的120ms漏积分时间常数与饱和导数，不能说明吸引域相同。

clipped激活拐点处普通Jacobian并不唯一。代码排除以单一Jacobian充当严格光滑证据，另构建局部所有可变/kink行的union graph。该图为DAG时存在共同拓扑顺序；在保持其他clip分支的邻域内形成稳定漏积分串级。逐坐标平衡解、残差与邻域margin为局部认证提供依据。该论证不证明全局收敛，也不将72个随机初态的72个终点cluster计为已认证吸引子。24只是任务态采样结果，不是穷尽全系统稳定态数量。

小扰动可以恢复，大扰动可换状态。经验basin fraction仅适用于已声明的24态×3方向×四档幅度与目标集合；clip后实际RMS才是剂量。恢复判据同时要求full-state距离及非静息身份，回到静息态不会被当成正确Response恢复。二维轨迹重合不能证明全状态恢复；当前结果仍有显著投影外差异。这些是**SCIENTIFIC DYNAMICS DIFFERENT**，不应改模型或colormap消除。

## 表征与图形范围

Figure1–7/10复用原共享分析；审查PCA/SVD、principal angles、RSA及条件留出probe代码，并对R3维数和分支角度独立复算。局部Response分支角90°来自手工不相交支持；whole-state角约83°不等于涌现正交。六位置current-R3等距时相关性必须undefined；全网络很小的环相关效应与输入几何、Y/残余活动贡献分开解释。二维MDS连成六边形且stress≈0.425不能证明连续环流形或环吸引子。线性变量轴不是Kobak dPCA，描述性nearest-centroid probe不是模型学习证据。

本人已实际打开新增三编码contact sheets（每编码5幅）与新Figure10概览，并全尺寸抽查三编码Figure8、source-time input、R3-clock input、state-kick及flow；历史代表图1/3/5/6/7/10实际打开。原图比较只用于内部；合成中列必须明确标为合成方法检查/示意，不能叫原实验复现。完整图片哈希检查与全尺寸逐像素检查不是同一声明。

## 审稿发现与修复要求

1. CLOSED：Figure8A自动offset将约1.23e−5末端变化视觉放大；最终三编码图统一[0,1.05]率轴并标excursion，已实际开图确认。
2. CLOSED：Inagaki source-comparison中列最初只画合成指数曲线但标题称CD/drift方法检查；现明确标synthetic illustration / method tests separate，manifest同步，已实看修后图。函数执行证据单列，不将示意当算法调用。
3. CLOSED：renders_before_repair中原图保留本地；最终.gitignore已覆盖中间renders和阅读包，未删除证据。
4. CLOSED：两专家METHOD_IMPLEMENTATION已更新当前正式包/strict状态，早期draft明确历史。另source_time图注已精确为trial起点500ms，即sample onset+500ms、sample offset后300ms。

## 最终文件身份与重跑读回

主Agent声明final-ready后，本人真实运行 `audit/reviewer/check_final_inventory.py`：114项新result哈希、68项源码哈希、8项归档保护源码、55条历史figure记录/165个历史图片文件全部匹配，0失败。证据为同目录JSON。result manifest SHA256=e453f5aa48361ff407434e9c5a79fe55fe91b410fd03cb08d72f98ec062f2fbe，source manifest SHA256=79e3a63b8f64bf52b5f9acd6d88e6235032044d591b18b4e6213d9e63bb2e005。完整统一CLI日志 `audit/workflow_execution.txt` 证明三编码重算、consistency及16组图片导出真实成功；不是只渲染静态示意。

已读回A的round4.1/4.2、B的round4及ROOT_REPORT_REVIEW，均为LDS适配PASS_WITH_LIMITS。必须披露：B最终额度限制前已审原结果，但未完成统一重跑后的全部文件hash刷新。与B的REVIEWED_INPUT_HASHES逐项比较后，六张input PNG与source-comparison PNG相同；六张state/flow PNG和24个NPZ不同，故不能说B审过完全相同的最终二进制文件。

F因此另执行 `audit/reviewer/readback_zhou.py`：只读重放B的独立NumPy验证代码，不覆写B报告，不把这称为B再次审稿；18个input、3个state、3个flow当前数组全部通过。与B原数值报告相比，full-state初始/最终/peak距离一致；最大指标差3.240477e−12，state最终二维能量比例从0.111110649668266变为0.111110649671506，仍为11.111%；flow最大隐藏范数差约9.63e−14。最终报告数值精度足够，没有过时的full-state结论。重跑的简并SVD显示轴方向可以改变，不能以字节hash或轨迹朝向当科学差异；本次不是仅凭“NPZ容器变化”推定等价。对应JSON保留逐项前后值。

本人已重新全尺寸打开最终三编码state/flow共6图，确认轴方向改变未改变误差分解/有限盆比例的科学含义，source/state/flow标签与全状态非恢复结论一致，无裁切/空白。原方法的unknown和protocol不同仍保留。本人另再次运行自己的fresh_check，独立采样全部通过。上述追加验收属于F，不能替不可联系的B伪造新一轮响应。

## Gate结论

| Gate | 独立判定 |
| --- | --- |
| 0 capability | PASS_WITH_LIMITS：真实Skill流程与可用能力已核实，不冒称自动科学审图API |
| 1 original method | 方法来源/契约PASS_WITH_LIMITS；原实验/完整作者Fig执行BLOCKED |
| 2 LDS compatibility | ADAPT；源统计/测量数据INCOMPATIBLE，输入实验RERUN已实施 |
| 3 numerical | PASS，限已运行局部认证/有限样本，不作全局basin证明 |
| 4 reverse fidelity | PASS_WITH_LIMITS：A round4.1/4.2、B round4与报告审查已读回；B重跑后字节变动由F追加实算/开图覆盖，限制明确 |
| 5 independent | PASS_WITH_LIMITS：最终manifest/保护源码/历史图读回、独立数值与真实图片检查完成；原实验exact BLOCKED保持 |

本报告不宣称METHOD REPRODUCED等于作者原结果复现。合成数学检查、METHOD ADAPTED、NUMERICAL ERROR FIXED、VISUAL MISMATCH FIXED和真实动力学差异应分别归档。
