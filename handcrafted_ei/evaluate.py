"""Full v2 experiment receipt. Truth is used only after neural trials return."""
import argparse
from copy import deepcopy
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
import platform
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED
import numpy as np
import yaml
from .model.ei_network import EINetwork
from .model.location_encoding import LocationEncoding, MODES
from .simulation import run_trial
from .task import conditions, encode, target
from .evaluation.behavior import accuracy
from .evaluation.memory import analyze_memory
from .evaluation.representation import analyze
from .evaluation.attractors import analyze_snapshots
from .receipt import verify


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).parent/'artifacts'/'v2'/'run')
    args=parser.parse_args(); out=args.output
    if out.exists() and any(out.iterdir()): parser.error('choose a fresh empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    package=Path(__file__).parent
    write_json(out/'config.json',EINetwork().config)
    write_json(out/'environment.json',{'python':sys.version,'executable':sys.executable,
        'numpy':np.__version__,'yaml':yaml.__version__,'platform':platform.platform(),
        'compute':'CPU NumPy; no training or GPU'})
    sources=list(package.rglob('*.py'))+list((package/'config').glob('*.yaml'))
    sources=[p for p in sources if 'artifacts' not in p.parts]
    sources += [package.parent/n for n in ('architecture.md','AGENTS.md','todo.md','README.md','docs/v2_protocol.md')]
    write_json(out/'source_hashes.json',{str(p.relative_to(package.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    write_json(out/'git.json',{'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'status':subprocess.check_output(['git','status','--porcelain'],text=True),
        'source_identity':'source_hashes.json describes uncommitted implementation; HEAD is baseline ancestry'})
    references=[target(*c) for c in conditions()]
    summary={}; manifest=[]; archives={}; geometry={}; memories={}; snapshots={}; controls={}
    def experiment(mode,name,overrides=None,intervention=None,random_seed=None,sigma=0.,seed=7,delay=0):
        config={'location_encoding':mode,**(overrides or {})}
        name=mode+'__'+name
        results=[]; dose=[]; metrics_memory=[]
        resolved=EINetwork(overrides=config).config
        with ZipFile(out/(name+'.zip'),'w',ZIP_DEFLATED,compresslevel=6) as z:
            for i,c in enumerate(conditions()):
                trial_seed=int(np.random.SeedSequence([seed,i]).generate_state(1)[0])
                encoded=encode(*c,noise_sigma=sigma,seed=trial_seed,mode=mode)
                model=EINetwork(overrides=config)
                def capture(network,stage):
                    # Six independent positions per stage; branch choice fixed in this probe set.
                    if name.endswith('__baseline') and c[1:]==(1,1):
                        snapshots[f'{mode}_L{c[0]}_R{stage}']=deepcopy(network)
                r=run_trial(model,encoded,intervention=intervention,random_seed=random_seed,
                            after_readout=capture,permission_delay_ms=delay)
                results.append(r); metrics_memory.append(analyze_memory(r))
                clean=LocationEncoding(mode).to_current(encode(*c,mode=mode)['x_L'])
                dose.append(float(np.linalg.norm(model.encoding.to_current(encoded['x_L'])-clean)))
                task={'L':c[0],'D':c[1],'S':c[2],'encoding':mode,'schema':2,
                      'encoded':{k:v.tolist() for k,v in encoded.items()},'target':references[i],
                      'seed':trial_seed,'experiment_seed':seed,'sigma_L':sigma}
                z.writestr(f'{i:02}_task.json',json.dumps(task))
                z.writestr(f'{i:02}_events.json',json.dumps({'events':r.events,'lesions':r.lesions,
                    'outputs':r.outputs,'decisions':r.decisions.tolist(),
                    'groups':{k:v.tolist() for k,v in r.groups.items()},'memory':metrics_memory[-1]}))
                buffer=BytesIO()
                np.savez_compressed(buffer,times_ms=r.times,rates=r.rates,y=r.y,labels=np.array(model.labels))
                z.writestr(f'{i:02}_rates.npz',buffer.getvalue())
        archives[name+'.zip']=hashlib.sha256((out/(name+'.zip')).read_bytes()).hexdigest()
        metrics=accuracy([r.outputs for r in results],references)
        summary[name]=metrics
        manifest.append({'experiment':name,'schema':2,'config':resolved,'intervention':intervention,
                         'random_seed':random_seed,'seed':seed,'noise_sigma_L':sigma,
                         'permission_delay_ms':delay,'current_error_l2':dose})
        memories[name]=metrics_memory
        print(name,metrics,flush=True)
        return results
    # P4 gate: every baseline must pass before post-hoc analysis/ablations.
    baselines={mode:experiment(mode,'baseline') for mode in MODES}
    write_json(out/'summary.json',summary)
    if any(v['sequences_correct']!=24 for v in summary.values()):
        raise RuntimeError('P4 failed; baselines saved, stop before P5')
    for mode,baseline in baselines.items():
        geometry[mode]={'encoding':LocationEncoding(mode).geometry(),'neural':analyze(baseline)}
        for seed in (11,19): experiment(mode,f'zero_seed_{seed}',seed=seed)
        for sigma in (.03,.2,.6):
            for seed in (7,11,19): experiment(mode,f'noise_{sigma}_{seed}',sigma=sigma,seed=seed)
        for kind in ('A','B','C','D','gate_D','gate_S','early_D','early_S','feedback_D','feedback_S','tonic','recurrence'):
            experiment(mode,'lesion_'+kind,intervention=kind)
            for seed in (7,11,19):
                experiment(mode,f'random_{kind}_{seed}',intervention=kind,random_seed=seed)
        for name,overrides in [('no_feedback',{'w_response_decay':0}),
                               ('no_direct_gate',{'w_activation':0}),
                               ('no_tonic',{'w_tonic_response':0,'w_tonic_memory':0,'w_tonic_r1':0}),
                               ('no_recurrence',{'w_rec':0}),
                               ('no_permission',{'clock_activation':0,'clock_activation3':0})]:
            experiment(mode,name,overrides=overrides)
        experiment(mode,'delayed_handoff',delay=1500)
        expected={'A':[1,0,0,0],'B':[1,1,1,1],'C':[1,1,0,0],'D':[1,1,1,1],
                  'gate_D':[1,0,0,0],'gate_S':[1,1,0,0],'early_D':[1,0,0,0],'early_S':[1,1,0,0]}
        controls[mode]={k:summary[f'{mode}__lesion_{k}']['stage_accuracy']==v for k,v in expected.items()}
        controls[mode]['baseline_memory_decay']=all(
            item[m]['pre_handoff_min']>.9 and item[m]['terminal_activity']<.05 and
            item[m]['half_after_formation_ms'] is not None and item[m]['half_after_formation_ms']>0
            for item in memories[mode+'__baseline'] for m in ('M_D','M_S'))
        controls[mode]['feedback_block_preserves_memory']=all(
            item[m]['terminal_activity']>.9 for item in memories[mode+'__no_feedback'] for m in ('M_D','M_S'))
        controls[mode]['delayed_handoff_correct']=summary[mode+'__delayed_handoff']['sequences_correct']==24
    write_json(out/'summary.json',summary); write_json(out/'manifest.json',manifest)
    write_json(out/'archives.json',archives); write_json(out/'representation.json',geometry)
    write_json(out/'memory.json',memories); write_json(out/'causal_checks.json',controls)
    print('attractor probes: 72 snapshots, 12 perturbations + 3 random initial states each',flush=True)
    attractors=analyze_snapshots(snapshots,out/'attractor_trajectories.npz')
    write_json(out/'attractors.json',attractors)
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['experiment','sequences_correct','n','stage1','stage2','stage3','stage4'])
        for name,m in summary.items(): writer.writerow([name,m['sequences_correct'],m['n'],*m['stage_accuracy']])
    plot_results(out,baselines,summary,attractors)
    report_results(out,summary,memories,attractors,controls)
    verify(out)
    if not all(all(v.values()) for v in controls.values()):
        raise RuntimeError('scientific criterion failed; saved evidence is not a pass')


def plot_results(out,baselines,summary,attractors):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    r=baselines['one_hot'][1]
    for name in ('R1','R2','R3','R4','M_D','M_S'):
        axes[0,0].plot(r.times,r.rates[:,r.groups[name]].max(axis=1),label=name)
    axes[0,0].legend(ncol=3); axes[0,0].set(xlabel='Time (ms)',ylabel='Actual normalized rate')
    for name in ('E_gate_D','E_gate_S','I_decay_D','I_decay_S','I_tonic_R'):
        axes[0,1].plot(r.times,r.rates[:,r.groups[name]].max(axis=1),label=name)
    axes[0,1].legend(); axes[0,1].set(xlabel='Time (ms)',ylabel='Actual normalized rate')
    for mode in MODES:
        sigmas=[0,.03,.2,.6]
        for seed in (7,11,19):
            vals=[100]+[100*summary[f'{mode}__noise_{s}_{seed}']['sequences_correct']/24 for s in sigmas[1:]]
            axes[1,0].plot(sigmas,vals,'o-',alpha=.5,label=f'{mode} seed {seed}')
    axes[1,0].legend(fontsize=6); axes[1,0].set(xlabel='Raw-coordinate RMS noise',ylabel='Sequence accuracy (%)')
    for name in ('M_D','M_S'):
        axes[1,1].plot(r.times,r.rates[:,r.groups[name]].max(axis=1),label=name)
    for stage in (2,3): axes[1,1].axvline(r.events[f'to_R{stage}'],color='grey',alpha=.4)
    axes[1,1].legend(); axes[1,1].set(xlabel='Time (ms)',ylabel='Rule memory rate',xlim=(1850,3310))
    fig.savefig(out/'validation.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(11,10),constrained_layout=True)
    for row,mode in enumerate(MODES):
        currents=np.array(LocationEncoding(mode).geometry()['currents'])
        axes[row,0].imshow(currents,vmin=0,vmax=1); axes[row,0].set(title=mode+' input currents',xlabel='Population unit',ylabel='Position')
        endpoints=np.array([x.rates[np.argmin(abs(x.times-x.events['readout3'])),x.groups['R3']] for x in baselines[mode]])
        folded=endpoints.reshape(24,4,6).sum(axis=1)
        positions=np.array([x.outputs[2] for x in baselines[mode]])
        means=np.array([folded[positions==k].mean(axis=0) for k in range(6)])
        axes[row,1].imshow(np.linalg.norm(means[:,None]-means[None,:],axis=2),vmin=0,vmax=1.5)
        axes[row,1].set(title='R3 within-position distances',xlabel='Position',ylabel='Position')
        centered=endpoints-endpoints.mean(axis=0)
        u,s,v=np.linalg.svd(centered,full_matrices=False); scores=u[:,:2]*s[:2]
        axes[row,2].scatter(scores[:,0],scores[:,1],c=positions,cmap='hsv',vmin=0,vmax=6)
        axes[row,2].set(title='R3 neural PCA',xlabel='PC1',ylabel='PC2')
    fig.savefig(out/'representation.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for mode in MODES:
        rows=[p for x in attractors['snapshots'] if x['snapshot'].startswith(mode+'_L') for p in x['basin_probes']]
        amplitudes=sorted({p['amplitude_rms_before_clipping'] for p in rows})
        fractions=[np.mean([p['recovered'] for p in rows if p['amplitude_rms_before_clipping']==a]) for a in amplitudes]
        axes[0].plot(amplitudes,fractions,'o-',label=mode)
        residuals=[x['autonomous']['field_residual_per_ms'] for x in attractors['snapshots'] if x['snapshot'].startswith(mode+'_L')]
        axes[1].plot(np.arange(len(residuals)),np.maximum(residuals,1e-18),'o',label=mode,alpha=.5)
    axes[0].legend(); axes[0].set(xlabel='Perturbation RMS before clipping',ylabel='Recovered fraction (finite probes)',ylim=(-.05,1.05))
    axes[1].set(yscale='log',xlabel='Sampled endpoint',ylabel='Field residual / ms')
    fig.savefig(out/'attractor_recovery.png',dpi=160); plt.close(fig)


def report_results(out,summary,memories,attractors,controls):
    stable=[x for x in attractors['snapshots'] if x['autonomous']['field_residual_per_ms']<1e-8 and
            x['autonomous']['euler_spectral_radius']<1]
    local=[x for x in stable if x['small_perturbation_local_recovery']]
    lines=['# E/I Decompression v2 实验报告','',
      '范围：相同六位置Response网络上的三种外部编码。固定连接、不训练；全部结果为条件穷举和有限扰动，不是泛化或生理拟合。','',
      '## 行为与机制','']
    for mode in MODES:
        b=summary[mode+'__baseline']
        lines.append(f'- {mode}：{b["sequences_correct"]}/24，逐stage {b["stage_accuracy"]}；机制检查 {controls[mode]}。')
        for m in ('M_D','M_S'):
            x=memories[mode+'__baseline'][0][m]
            lines.append(f'  - {m}：形成 {x["response_formation_ms"]} ms；半活动时刻 {x["half_activity_ms"]} ms；形成后半衰间隔 {x["half_after_formation_ms"]} ms；80–20%拟合有效τ {x["fit_effective_tau_ms_80_to_20"]:.3f} ms；终末 {x["terminal_activity"]:.3g}；AUC {x["auc_after_sample_rate_ms"]:.3f} rate·ms。')
    lines += ['', '直接激活：source、gate和clock缺项负对照见自动化测试；A/C和gate_D/S损伤对应阶段，B/D保留继承。',
      '切反馈不必损伤行为，其机制失败是memory未终止；无tonic的机制失败是提前/未选支路泄漏，不能要求所有消融均降低正确率。',
      '全部单项和随机对照、noise各seed原值见metrics.csv；memory.json给出每个trial的时间、AUC、终末与交接后分支margin。',
      '随机对照匹配边数/权重/突触前符号/窗口。tonic和全recurrence的精确匹配池可能只有目标边本身，不能由退化的随机池证明靶点特异性；池规模记录在events。','',
      '## 吸引子检测','',
      f'关闭sample和全部clock、保留tonic：72个快照中 {len(stable)} 个达到残差<1e-8/ms且Euler谱半径<1；其中 {len(local)} 个在全部0.02/0.1 RMS抽样扰动后恢复至全状态误差<0.02。',
      '预置的饱和递归结构可以产生离散稳定点；这不是连续吸引子或自主阶段推进证据。未恢复的扰动、状态跳转/衰减及随机初态均原样保存在attractors.json。',
      '早期测试曾假定0.1 RMS都恢复，但反例显示吸引域可能较窄；未修改检测阈值和实验幅度。单元测试仅检查已确认的小扰动恢复和无recurrence衰减，完整研究仍保留所有幅度。',
      'attractor_trajectories/index.json索引每个快照的自由/受迫、全部扰动和初态轨迹NPZ分包及SHA256。比较受迫与自主条件明确分开；谱为分段线性局部Jacobian，阈值处用对称导数，不是全局证明。','',
      '## 编码和子空间解释边界','',
      '原始编码维度6/1/2，内部各分支均6。ring/topology无噪声电流相同，二者差异来自噪声空间，不能宣称内部编码动力学不同。',
      '各编码原始噪声期望能量σ²，sample一次采样；映射后电流L2归一化。manifest记录实际电流误差；相同原始能量不是相同神经误差，不作编码优越性推断。',
      'representation.json分别给出编码几何与实际神经轨迹、均值、SVD/VAF、PR、分支内位置距离、principal angles和交接后活动。分支坐标预置分离，角度不证明涌现正交；候选分支数不是rank。',
      '吸引域仅有限初态/种子/幅度扫描；没有统计显著性、全参数稳健性、细胞生物对应或学习结论。','',
      '## 复现与身份','',
      '完整配置见manifest/config，源码见source_hashes，环境见environment。HEAD只表示祖先，未提交实现由文件哈希标识。',
      '`python -m unittest discover -s handcrafted_ei/tests -v`',
      '`python -m handcrafted_ei.evaluate --output <fresh-dir>`',
      '`python -m handcrafted_ei.receipt <dir>`','',
      '![实际活动与噪声对照](validation.png)','']
    lines += ['![输入与神经表示](representation.png)','', '![扰动恢复与固定点残差](attractor_recovery.png)','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__': main()
