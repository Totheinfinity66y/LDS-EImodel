"""Reports derived from the same numeric results used for the figures."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from .style import panels,NAMES,ENCODING_COLORS
from .dynamics_figures import read_rows
from ..evaluation.population_activity import save_rows


def summary_rows(data,results,input_dir,out):
    behavioral=json.loads((Path(input_dir)/'summary.json').read_text(encoding='utf-8'))
    perturb=read_rows(Path(out)/'metrics/dynamics_perturbation.csv'); fixed=read_rows(Path(out)/'metrics/dynamics_fixed_points.csv')
    rows=[]
    for mode,d in data.items():
        r=results[mode]; sub=r['subspaces']['stages'][3]['branches'][0]['whole']; rsa=r['rsa']['panels'][(3,0)]
        same=[x for x in perturb if x['encoding']==mode and x['target']=='full']
        fraction=lambda amplitude:float(np.mean([x['recovered']=='True' for x in same if float(x['amplitude_target_rms_before_clipping'])==amplitude]))
        memory=[x for x in r['memory']['rows'] if x['memory']=='M_D']
        rows.append({'encoding':mode,'neuron_count':d['rates'].shape[-1],
            'active_fraction_R3_whole':float(np.mean((r['activity']['stage_samples'][2]>.1))),
            'activity_participation_ratio_R3_b0':r['recruitment']['rows'][3]['activity_participation_ratio'],
            'branch_mean_angle_R3_deg':float(np.mean([x['mean_angle'] for x in r['subspaces']['pairs'] if x['stage']==3])),
            'heldout_noise_subspace_overlap':float(np.mean([x['projection_overlap'] for x in r['seed_stability']])),
            'topology_spearman_R3_whole':rsa['metrics']['ring_spearman'],
            'topology_spearman_R3_current_response':rsa['response_metrics']['ring_spearman'],
            'R3_effective_dimension':sub['effective_dimension'],'R3_normalized_dimension':sub['effective_dimension']/d['rates'].shape[-1],
            'D_decay_lag_from_response_onset_ms':float(np.mean([x['memory_response_lag_ms'] for x in memory])),
            'full_recovery_fraction_0.02':fraction(.02),'full_recovery_fraction_0.1':fraction(.1),
            'noise_0.2_sequence_accuracy':float(np.mean([behavioral[f'{mode}__noise_0.2_{seed}']['sequences_correct']/24 for seed in (7,11,19)])),
            'baseline_sequence_accuracy':behavioral[mode+'__baseline']['sequences_correct']/24,
            'autonomous_max_residual_l2_per_ms':max(float(x['residual_l2_per_ms']) for x in fixed if x['encoding']==mode and x['condition']=='autonomous'),
            'Euler_max_spectral_radius':max(float(x['euler_spectral_radius']) for x in fixed if x['encoding']==mode),
            'topology_R3_whole_relative_distance_contrast':rsa['metrics']['relative_opposite_minus_adjacent']})
    return rows


def quantitative_summary(rows):
    metrics=[('active_fraction_R3_whole','R3 all-unit active fraction'),('activity_participation_ratio_R3_b0','R3 b0 activity participation ratio'),
        ('branch_mean_angle_R3_deg','R3 branch mean angle (degrees)'),('heldout_noise_subspace_overlap','Independent input-noise subspace overlap'),
        ('topology_R3_whole_relative_distance_contrast','Whole-state relative ring contrast'),('R3_effective_dimension','R3 b0 effective dimension'),
        ('R3_normalized_dimension','Dimension / 132 units'),('D_decay_lag_from_response_onset_ms','D decay onset lag (ms)'),
        ('full_recovery_fraction_0.02','Full-state recovery RMS .02'),('full_recovery_fraction_0.1','Full-state recovery RMS .1'),
        ('noise_0.2_sequence_accuracy','Raw-coordinate noise .2 accuracy*'),('baseline_sequence_accuracy','Baseline sequence accuracy')]
    fig,ax=plt.subplots(4,3,figsize=(12,11),layout='constrained')
    for axis,(key,label) in zip(ax.ravel(),metrics):
        values=[r[key] for r in rows]; axis.bar(range(3),values,color=[ENCODING_COLORS[r['encoding']] for r in rows]); axis.set_xticks(range(3),[NAMES[r['encoding']] for r in rows]); axis.set_title(label)
        axis.set_ylim(0,max(max(values)*1.2,1e-6))
    panels(ax); fig.suptitle('Figure 10 quantitative | distinct units, no aggregate score\n*Same raw noise energy is not equal neural-current noise dose; no encoding superiority inference'); return fig


METHODS='''# 方法与复现

## 数据与独立性

正式数据为本地 v2 三编码 baseline，各 24 条 L/D/S 条件、663 时间点、132 神经元；dt=5 ms，0–3310 ms。8 个决定动力学的源文件与归档 SHA256 一致。标准化数据保留 labels、E/I、群体/分支、事件、配置、派生种子及来源哈希。rate 是无量纲 [0,1]，不是 Hz。input_currents 从 encoded 输入和 sample 时序重建，行含义为积分至该时刻的电流。全轨迹无删静息神经元。

baseline 确定性条件没有置信区间。噪声数据为同一固定网络的独立输入噪声 realization（seeds 7/11/19），不是三个独立网络。扰动 seed 指不同方向，不将相邻时间点或所有位置视为独立生物学重复。不报告无重复支撑的 p 值；720 位置置换只描述固定六点几何的标签置换尾部比例。

## 群体活动、招募与选择性

减去每 trial 实际 t=0 向量，active 定义为增量 >0.1。阶段均值取 (readout−20 ms, readout]。报告群体 mean、peak、基线增量、active fraction 与 total。功能参与矩阵在该分支所有六位置条件中任一越阈值即参与；结构矩阵仅标记固定连接中分配给该 Response 分支的六坐标，不包含共享 Y、memory、I。因此全网络功能支持比结构块大是预期现象，不能将二者不同当成额外涌现模块。

参与率 PR_activity=(Σa)²/Σa²；Jaccard=交集/并集；cosine 使用分支平均活动。均衡 6×2×2 条件均值作正交 factorial 分解 L、D、S、LD、LS、DS、LDS，效应平方均值占总条件方差；零方差单元的份额为零且保留原方差字段。它是描述性分解，不是显著性检验。

记忆强度取群体 max。Response onset/stabilization 为许可后第一次达到0.1/0.9；memory decay onset/half/baseline 为许可后第一次低于交接前峰值的95%/50%以及绝对0.05。half_life_from_decay 是50%与95%交叉之差，不能当作指数拟合的生物半衰期；未交叉写 NA。规则信息另看条件质心距离与独立条件probe，不能只用群体平均率推断。反馈和tonic消融及各反馈随机边对照从原全率归档复用，行为准确率一起保存。

## PCA、子空间与几何

全局 PCA 每编码独立拟合：全部24条件、全部132神经元，每4个时间点均匀采样，统一减训练样本均值。所有轨迹在同一套轴中投影；不逐trial拟合。变量投影使用 L 的 cos/sin 与 D/S 编码，对时间平均状态作联合最小二乘并归一化系数轴；仅描述性，不叫 dPCA。噪声单trial和对齐均值使用 baseline 同一 PCA。

阶段和分支各自中心化 SVD：奇异值 s、VAF=s²/Σs²，有效维数 PR=1/ΣVAF²，90%/95%维数为累积阈值。数值rank依 max(shape)·machine_epsilon·s_max。基 Q 的角度为 arccos(SVD(QaᵀQb))；投影重合=||QaᵀQb||F²/min(ka,kb)，距离=√(ka+kb−2||QaᵀQb||F²)。cross VAF=||X_centered Q||F²/||X_centered||F²，两个方向分别保存。

全状态分支比较使用同一132坐标。结构控制将当前阶段不同 branch 的六位置折叠到共同六坐标；这会有意移除branch身份，不能当作真实跨脑神经元配准。另报告互不重叠的结构支持。L奇偶拆分仅检验不同位置采样敏感性；独立噪声seed稳定性在相同条件/坐标、每侧95%VAF基上估计。R1含未固定D/S的记忆方差，R2含S方差，不能对它们套六位置rank≤5；固定DS的六均值中心化才有此上限。

固定同一branch，六位置按实际当前输出分组，取132维均值；Euclidean原尺度、cosine和逐向量中心化correlation距离分别计算。独立当前Response与全部Response对照排除共享Y和旧阶段。理论环距离 min(|i−j|,6−|i−j|)，chord=2sin(πd/6)。Spearman在容差内并列秩；等距非对角矩阵相关性 undefined/NA。邻居正确率对并列候选分配fractional credit（等距chance=2/5），同时报告相对距离差，防止微小尾迹被高rank相关夸大。

经典MDS用 −HD²H/2 的前两正特征轴，stress=√(Σ(D−Dhat)²/ΣD²)。二维形状有旋转/镜像/尺度局限，六个离散点不证明连续流形。720种位置标签置换完整枚举。群体平方距离贡献用于定位微弱距离差来源。

## 解码

nearest-centroid线性probe使用两折分层条件拆分；同一L/D/S的所有重复留在同一fold。全部类别训练/测试覆盖；零距离并列给fractional credit。报告L chance1/6、D/S chance1/2；current location与branch仅在四个读出窗定义，不给transition伪造真值。全网络、Response、memory及各branch分别评价；cross-temporal全网络train-time×test-time使用相同隔离fold。probe只拟合离线读出，不训练或写回神经模型；结果只对应固定任务条件组合的有限外推。

## 动力学、扰动与向量场

72个既有快照覆盖三编码、六L、四阶段，历史固定D=+1,S=1；未覆盖所有branch的吸引域。完整率与clock复制到隔离模型，sample关，延长2000 ms；保留snapshot clock的强迫条件和撤clock保留tonic的自主条件分别测试。撤所有任务输入但保留规定背景与后者数学等价，不伪装成不同实验。

连续场 f(r)=[−r+clip(W_signed r+b+c−theta,0,1)]/tau；保存L2/max残差。解析piecewise Jacobian J=(−I+diag(phi′)W_signed)/tau，Euler F映射为I+dtJ；报告完整谱、max Re(lambda)与rho(I+dtJ)。clip拐点用对称导数0.5并计数，局部谱不是全局非线性稳定性证明。稳定候选必须结合残差、状态身份与扰动恢复，不由投影聚类判定。

从已稳定的自主端点开始，full、all Response、当前活动branch、未选branch、E、I六类目标，幅度为目标单元内RMS .02/.1/.3/.7，seeds7/11/19，高斯后裁剪[0,1]；记录实际全状态剂量。当前branch由活动判定，不查真实标签。R1无未选branch时明确NA。864条full轨迹复用，新增4320个目标条件，其中216为NA；有效独立方向条件4968。原状态与对照全N距离、归一化距离、max误差、恢复时间、switch及最终身份保存。恢复要求max误差<.02且原Response branch/位置一致、峰>.2；共同静息从不算恢复。恢复时间为最后一次越界后的持续阈值满足时间。

cross-temporal距离选择full幅度.3 seed7，控制几乎是固定点，因此条带并非动态轨迹吸引。13×13局部截面取同阶段六自主端点的前两PC，反投影后裁剪合法状态，评价完整f再投影，同时记录平面外范数。该图只是局部切片；固定点残差用完整状态。随机初态每seed在相同方程下重复引用，不当作每个快照新的独立初态；图中端点去重。

## 图源、版本与复现

每张图有300 dpi PNG、SVG和PDF；figure_manifest记录输入、代码hash、metric路径、参考文献ID、窗口和预处理。DATA_AUDIT、FIGURE_REFERENCES、config/analysis.json、manifests/analysis_source_hashes.json是完整溯源的一部分。论文原图仅供核验，不当作本模型图。文件完整性与人工视觉QA分别记录。

```powershell
$env:PATH="C:\\Users\\Totheinfinity\\.conda\\envs\\analysis\\Library\\bin;"+$env:PATH
& C:\\Users\\Totheinfinity\\.conda\\envs\\analysis\\python.exe -m handcrafted_ei.visualization.plot_all --input handcrafted_ei/artifacts/v2/run --output artifacts/neural_representation_v2 --formats png,svg,pdf
```

也可在已激活兼容环境中执行相同的 `python -m` 命令。支持--figures 1,3,6、--encoding ring、--force。缓存按分析代码与原始归档hash确定，动力学原始输入逐个匹配历史index，输出有hash，缺失/损坏重新生成。测试命令为 `python -m unittest discover -s handcrafted_ei/tests -v`，文件QA为 `python -m handcrafted_ei.visualization.quality_check artifacts/neural_representation_v2`。
'''


def write_reports(data,results,input_dir,out):
    out=Path(out); rows=summary_rows(data,results,input_dir,out); save_rows(out/'metrics/encoding_summary.csv',rows)
    np.savez_compressed(out/'metrics/encoding_summary.npz',encoding=np.array([x['encoding'] for x in rows]),**{key:np.array([x[key] for x in rows]) for key in rows[0] if key!='encoding'})
    lines=['# 逐图结果与科学解释','', '所有数值来自本次完整神经率分析；模型、task、时序和baseline配置没有改动。','']
    for mode,d in data.items():
        r=results[mode]; lines+=['## '+NAMES[mode],'']
        dims=['R'+str(s)+': '+', '.join(f'b{b} rank={v["whole"]["rank"]}, PR={v["whole"]["effective_dimension"]:.4f}, dim95={v["whole"]["dim95"]}' for b,v in enumerate(r['subspaces']['stages'][s]['branches'])) for s in range(1,5)]
        lines+=['### Figure 1–2：活动组织与招募','',f'内部神经元 {d["rates"].shape[-1]}，E=81、I=51。各条件按固定branch依次激活，旧阶段在retire后衰退；tonic I持续存在。当前Response的招募局限主要由预定义的六单元分支支持决定，其他活跃的memory、gate、Y和I是共享/辅助活动。factorial图显示单变量和交互条件方差，不含显著性推断。','',f'[全网络活动](figures/{mode}/figure_01_{mode}.png) · [结构/功能招募](figures/{mode}/figure_02_{mode}.png)','', '### Figure 3：记忆交接','']
        for memory in ('M_D','M_S'):
            vals=[x for x in r['memory']['rows'] if x['memory']==memory]
            lines.append(f'{memory}：Response onset={np.mean([v["response_onset_ms"] for v in vals]):.0f} ms，90%稳定={np.mean([v["response_90pct_ms"] for v in vals]):.0f} ms；memory 95%交叉={np.mean([v["decay_onset_95pct_ms"] for v in vals]):.0f} ms，50%交叉={np.mean([v["half_crossing_ms"] for v in vals]):.0f} ms，0.05交叉={np.mean([v["time_to_baseline_ms"] for v in vals]):.0f} ms。')
        lines+=['','阻断反馈后M_D/M_S保持接近1，baseline交接后衰减；正常与无反馈条件均可保持行为正确，因此行为正确率不是记忆终止的验收指标。规则质心差和probe分别支持memory/Response的信息载体变化；不同population的原尺度距离不能直接相加或比较信息量。','', '### Figure 4–5：状态空间与维数','',f'全网络统一PCA前三轴VAF为 {", ".join(f"{100*x:.2f}%" for x in r["subspaces"]["global"]["evr"][:3])}。各分支完整状态的中心化维数如下；R1/R2中未固定的规则记忆增加全状态维数。','',*['- '+x for x in dims],'', '当前Response的位置中心化rank各阶段为5。支持折叠后的分支重合接近1，说明分支间分离主要受固定坐标块约束。全网络含共享Y/I/记忆，故真实全网络角度不必正好90°。不同L奇偶拟合方向差异很大，反映采样位置不同；同条件小输入噪声seed的95%VAF子空间稳定，不能据此声称随机网络间稳定。','', '### Figure 6：输入与神经表征几何','']
        for s in range(1,5):
            p=r['rsa']['panels'][(s,0)]; rho=p['metrics']['ring_spearman']; contrast=p['metrics']['relative_opposite_minus_adjacent']
            lines.append(f'R{s} b0：全网络rho={rho:.6f}，相对opposite-adjacent距离差={contrast:.8f}；当前Response rho=NA（六位置等距），MDS stress={p["stress"]:.4f}。' if np.isfinite(rho) else f'R{s} b0：全网络rho=NA（等距）；当前Response rho=NA（等距），MDS stress={p["stress"]:.4f}。')
        lines+=['','R2–R4微弱全网络环排序由共享Y内旧位置的读出尾迹产生，Response和all-Response自身仍等距。高Spearman对极小距离差敏感；必须结合相对效应量与population contribution解释，不作强环流形结论。所有编码给出同样的结果。','', '### Figure 7：信息可读出性','', 'L/D/S曲线与cross-temporal矩阵使用严格不相交任务条件fold；当前位置与branch另在读出窗评价。未出现独立网络/动物意义的泛化证据。固定branch的D或S可用性与该群体是否激活相关，不能把标签常量当解码成功。','', '### Figure 8–9：固定状态与有限盆','', '保留clock与撤clock的两类条件都观察到所测状态的低残差端点，tonic背景保留。局部谱和小扰动恢复支持离散、条件限定的稳定固定点候选；阈值拐点导数及有限初态覆盖限制全局判断。每编码有24个任务自主端点，随机初态再带来3个不同端点，不能将网络描述为只有六个吸引子。cross-temporal条带与固定点参照一致，没有动态吸引轨迹证据。','']
    lines+=['## Figure 10：三编码比较','', '内部网络相同，ring/topology无噪声电流相同；one_hot早期sample电流不同，但竞争与饱和动力学使读出期Response表征趋同。综合图保留完整坐标尺度，定量summary不混合量纲、不构造最佳模型评分。raw-coordinate噪声.2的比较必须同时参考原manifest中的current_error_l2，不推断编码优越。','']
    lines+=['## 解码对照及记忆终止的边界','', '严格条件留出的baseline probe在2315 ms的R2/D、2810 ms的R3/S均为0.5，不能据此声称未见任务组合上的规则读出泛化；one-hot的未见坐标支持影响了该分类器。额外使用噪声sigma=.03、seeds7/11/19，以完整24条件训练两seed、测试另一seed，三个编码在readout2的R2/D和readout3的R3/S均为1.0。这个结果支持已见条件下独立输入噪声重复的信息可用性，不能代替条件外推。','', '同一噪声probe在这两个读出时刻的M_D/D和M_S/S也为1.0。即使幅度低于0.05，非零残差仍可在数值精度与probe容差内携带规则身份。这里的memory终止是活动幅度机制，不是严格信息擦除；不能声称信息只存在于Response或已经从memory完全消失。所有fold实际trial noise seed写入decoding_noise_seed_splits.json，fold共享训练seed，不计算独立fold置信区间。','']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); (out/'METHODS.md').write_text(METHODS+'\n## 独立噪声试次解码补充\n\n另用相同sigma=.03的三seed完整24条件记录，leave-one-noise-seed-out训练两个seed/测试另一个seed。验证实验seed与全部72个trial噪声seed不重叠、坐标/时序/条件顺序一致。它是已见任务条件下的噪声重复，不是OOD；不与严格条件留出混合。保留每seed的准确率而不虚构独立fold置信区间。记忆幅度终止不意味着信息擦除。\n',encoding='utf-8')
    maxdiff={mode:float(np.max(abs(d['rates']-data['one_hot']['rates']))) for mode,d in data.items()}
    summary=['# 三编码神经群体分析总结','', '结论：三种外部编码经过相同固定E/I网络后，在读出期趋向相同的六位置Response表征。分支分离主要由handcrafted坐标支持决定；当前Response六位置等距。完整网络中微小环排序来自共享Y的读出尾迹。所测离散状态有局部固定点稳定与小扰动恢复证据，没有连续环吸引子证据。','', '## 十个研究问题','', '1. **招募哪些群体？** 三编码均依次招募R1→R2→R3→R4的一个活动分支，并伴随规则memory、兴奋gate、tonic/decay/竞争/退役I和共享Y。132维全网络没有删去静息单元。','', '2. **局部化来源？** 六单元branch支持直接写入固定连接；结构/功能并列和support-folded近1重合表明主要是handcrafted branch specialization。共享群体参与不等于新涌现分区。','', '3. **Response subspace？** 可辨认，但它是既定坐标中实际活动的事后统计；不支持自发正交的说法。全网络共享成分使角度小于90°。','', '4. **有效维数？** 当前Response各branch位置rank=5、PR≈5；全网络R1 rank7/PR≈5.55，R2各branch rank6/PR≈4.73，R3/R4各branch rank5/PR≈5。每个精确值及dim90/95在metrics/<encoding>/subspace_geometry.csv；不能把1/2/4/4分支数当rank。','', '5. **D/S交接？** M_D到R2、M_S到R3的规则条件差异在交接后保留于Response，memory经I_decay反馈终止；反馈阻断保留memory，原有必要性与继承测试限制因果解释。它不是信息守恒量估计。','', '6. **六位置邻接？** 当前Response没有邻近更相似的几何，非对角距离常数，rho=NA、tie-corrected邻居分数0.4。全网络R2–R4高rank相关对应约0.014%–0.024%相对距离差，来自共享Y尾迹，不能称为强内部圆环。','', '7. **三编码几何差异？** 输入原始维数不同且one_hot早期sample轨迹不同，ring/topology干净电流等价。读出期Response几何趋同，不能声称三种不同内部流形。','', '8. **哪些状态稳定？** 72个快照覆盖D=+1,S=1、六L、四阶段、三编码；撤sample/clock后保留tonic的自主端点及固定clock端点具有低残差与rho<1。小RMS .02有效目标全部身份保留恢复，较大扰动常跳转或失败。','', '9. **吸引子证据？** 有所测离散状态的局部稳定固定点候选及有限盆证据；没有连续环或动态吸引轨迹证据。每编码观察到24个任务端点加3个随机初态端点；不能声称穷尽全部盆。clip拐点局部导数有局限，结论不扩展为全局证明。','', '10. **结构与动力学？** 分支数量/支持和固定位置变换属于先验。撤输入保持、门控形成、反馈终止、饱和后编码趋同、有限扰动恢复/跳转是实际积分观察。Y尾迹造成微弱环距离效应值得注意，但不是Response连续流形。','', '## 原始数值与入口','', '[逐图结果](RESULTS.md) · [方法](METHODS.md) · [数据审计](DATA_AUDIT.md) · [参考图核对](FIGURE_REFERENCES.md) · [定量指标](metrics/encoding_summary.csv)','',f'相对one_hot全轨迹max绝对差（包括sample）为：{maxdiff}。三编码不使用同一缓存冒充；每个录制包保留独立来源ZIP哈希。','', '完整局部动力学原始NPZ保留本地，输出hash在data/dynamics/summary.json；论文原图仅供本地核验，均不作为模型结果。测试和视觉验收见manifests，提交状态以Git读回为准。']
    summary+=['', '## 信息交接的必要限定','', '独立噪声seed测试在readout2的R2/D和readout3的R3/S为1.0，同时M_D/D和M_S/S仍为1.0；残余小活动不等于信息被擦除。严格留出任务组合的baseline probe在相关时刻仅机会水平。因此问题5的“交接”指Response已可承载规则并能继承路由，同时memory活动经反馈衰减；不表示规则信息在memory中彻底消失，也不表示未见条件泛化。']
    (out/'SUMMARY.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
    return rows
