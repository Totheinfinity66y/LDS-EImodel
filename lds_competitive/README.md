# 共享中继竞争门控L/D/S率回路

[仓库首页：完整率单元、编码与动力学公式、连接矩阵、测试方法和三张实际活动图](../README.md)。

本包独立实现[完整设计](../plans/lds_shared_relay_competitive_design.md)，不导入其他模型或将目标位置用于运行。输入是已知的L、D、S；不学习压缩规则，不推断D/S。

## 模型与输入

六个位置标签L=1…6，θ_k=(k−1)π/3，坐标(cosθ_k,−sinθ_k)，编号增加为物理顺时针。D=+1为顺时针，D=−1为逆时针，S∈{1,2}。

四个输出由实际位置E峰值读出，任务位移为D、S·D、D，所有位置按六点环取模。

率变量共29个：E×6、Direction×2、Step×2、联合J×4、竞争读出V×4、抑制门控G×4、共享中继M×6、全局I×1。D/S/J八个编码率在检索中保持；其余21个变量同步积分。

另有归一化源H的六维采样保持、外部秩脉冲、分支整流及编码乘积等计算资源。29不是完整生物神经元数的证明；M是共享有效驱动状态。

## 编码与动力学

D/S采用sigmoid重叠调谐，带独立单元增益；编码从零以一阶响应的解析终值获得。J的原始驱动为D/S归一化活动的外积。raw_drive、rates、activity分别保存，检索使用保持的joint.activity。

位置输入为归一化的exp{κ[cos(θ−θ_k)−1]}，κ=8。初始化E=I=0，用位置调谐驱动E/I共0.8 s；此时V/G/M保持0。

每次转移从活动J经秩连接W_r形成读出驱动b。令φ为逐元素整流、C=11ᵀ−I₄，默认控制方程为：

\[
\tau_V\dot V=-V+\phi(b-G),\qquad
\tau_G\dot G=-G+CV.
\]

V激活其他路径的G；G反过来抑制自己的V与空间分支。没有用argmax或符号路径标签控制模型。

每秩H=N(E)采样并保持，四路分支及共享中继为：

\[
F_p=\phi(A_pH+C_pG),\qquad
\tau_M\dot M=-M+\sum_pB_pF_p.
\]

默认A_p分别为+1、+2、−1、−2环移，B_p=I₆，C_pG=−2G_p·1₆。先逐分支整流再汇总，不将四路兴奋和抑制先合并整流。

位置动力学为：

\[
\tau_E\dot E=-E+\phi(M+0.15E-0.20I),\qquad
\tau_I\dot I=-I+0.25\sum_kE_k.
\]

默认τ_V=τ_G=0.020 s、τ_M=0.030 s、τ_E=0.100 s、τ_I=0.050 s、dt=0.002 s。每秩0.8 s，使用同步Euler；全部下一步值从同一旧时刻计算。

E/I/V/G跨秩接续，只有M重置。四个观察时刻为初始化结束后的0、0.8、1.6、2.4 s。±2直接投射，不增加中间转移。

## 可检查连接

矩阵方向均为[突触后,突触前]，每个实例独立分配：

| 字段 | 形状 | 作用 |
| --- | --- | --- |
| e_to_branch | 4×6×6 | 四路共享环移A |
| branch_to_m | 4×6×6 | 汇总投射B |
| rank_to_readout | 3×4×4 | 三片独立秩连接 |
| readout_to_gate | 4×4 | V→其他G的非负连接 |
| gate_to_readout | 4×4 | G→对应V的负连接 |
| gate_to_branch | 4×6×4 | G→对应空间分支的负连接 |

使用ModelParameters逐实例调整参数，修改connections实施连接干预。NeuralState与所有输出数组是只读快照；可用dataclasses.replace构造明确的状态干预。

## 运行与复现

已核验CPU环境：Python 3.12.12、NumPy 2.3.5、Matplotlib 3.10.7、SciPy 1.16.3。解释器为现有analysis环境；本任务没有安装或修改任何依赖。声明见[requirements.txt](requirements.txt)。

在仓库根目录执行：

```powershell
.\lds_competitive\run.ps1 -Test
.\lds_competitive\run.ps1
```

脚本显式使用analysis解释器，并在单次调用内设置Conda DLL路径，结束时恢复PATH。可用-PythonPath指定另一个已检查的解释器，或-OutputDirectory指定独立产物目录。

在已经正确激活的兼容环境中，可直接调用：

```python
from lds_competitive import CompressedCode, RateDecompressor

model = RateDecompressor()
result = model.decompress(CompressedCode(1, 1, 2))
print(result.positions)
print(result.transitions[1].v_rates[-1])
print(result.transitions[1].branch_target[-1])
```

decompress只在initialize读取一次符号码；advance(state)/resume(state)只接受率状态。M每秩重置，因此advance是秩边界接口，不是任意时刻的中途恢复接口。

## 图、数据与验证

- [实际运行报告](artifacts/REPORT.md)
- [全部29单元代表图](artifacts/all_units_timeline.png)
- [完整机制过程](artifacts/sequence_dynamics.png)
- [24条件全部29单元多页PDF](artifacts/all_conditions_rates.pdf)
- [24条件图片索引](artifacts/all_conditions/INDEX.md)
- [实际数值与环境](artifacts/summary.json)
- [预先固定的验收条件](VALIDATION_CONTRACT.md)
- [验证记录](VALIDATION.md)

图从activities.npz的真实数组生成，不平滑、不逐行归一化。全部24条件使用共同原始率色标；保持编码用棕色标签，积分活动用青色标签。分支驱动标为派生量，不画成额外神经元率。

## 结果解释范围

控制有真实延迟，起始与切换时未选路径可能短暂活动；末段静默不能解释为全程无泄漏。有限角度诊断不是任意连续位置保证。

固定环、乘积联合、归一化、源保持和外部时钟是显式先验或机制。正确输出不证明学到了规则、自主工作记忆、时钟、六位置吸引子或完整细胞级Dale实现。
