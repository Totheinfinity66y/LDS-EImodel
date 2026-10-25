"""Reproducible M0-M5 receipt. Truth is evaluated only after each trial returns."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
import sys
import numpy as np
import yaml
from .model.ei_network import EINetwork
from .simulation import run_trial
from .task import conditions, encode, target
from .evaluation.behavior import accuracy
from .evaluation.representation import analyze
from .receipt import pack_and_verify


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path(__file__).parent/'artifacts'/'v1')
    args=parser.parse_args(); out=args.output
    if (out/'manifest.json').exists():
        parser.error('output already contains a receipt; choose a fresh --output path')
    out.mkdir(parents=True,exist_ok=True)
    package=Path(__file__).parent
    config=EINetwork().config
    write_json(out/'config.json',config)
    write_json(out/'environment.json',{'python':sys.version,'executable':sys.executable,
                'numpy':np.__version__,'yaml':yaml.__version__,'platform':platform.platform(),
                'compute':'CPU NumPy; no GPU or training'})
    sources=list(package.rglob('*.py'))+list((package/'config').glob('*.yaml'))
    sources += [package.parent/n for n in ('architecture.md','AGENTS.md','todo.md','README.md')]
    write_json(out/'source_hashes.json',{str(p.relative_to(package.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sources})
    references=[target(*c) for c in conditions()]
    summary={}; baseline=[]; rows=[]; manifest=[]
    def experiment(name,overrides=None,intervention=None,random_seed=None,sigma=0.,seed=7):
        results=[]; directory=out/name; directory.mkdir(parents=True)
        for i,c in enumerate(conditions()):
            encoded=encode(*c,noise_sigma=sigma,seed=seed)
            result=run_trial(EINetwork(overrides=overrides),encoded,intervention=intervention,random_seed=random_seed)
            results.append(result)
            # Independent input/truth file, never passed to the neural state updater.
            write_json(directory/f'{i:02}_task.json',{'L':c[0],'D':c[1],'S':c[2],
                'encoded':{k:v.tolist() for k,v in encoded.items()},'target':references[i],
                'seed':seed,'sigma_L':sigma})
            write_json(directory/f'{i:02}_events.json',{'events':result.events,'lesions':result.lesions,
                        'outputs':result.outputs,'decisions':result.decisions.tolist()})
            np.savez_compressed(directory/f'{i:02}_rates.npz',times_ms=result.times,rates=result.rates,
                                y=result.y,labels=np.array(EINetwork().labels))
        metrics=accuracy([r.outputs for r in results],references)
        summary[name]=metrics
        rows.append({'experiment':name,**metrics})
        manifest.append({'experiment':name,'config_overrides':overrides or {},'intervention':intervention,
                          'random_seed':random_seed,'seed':seed,'noise_sigma_L':sigma})
        print(name,metrics,flush=True)
        return results
    baseline=experiment('baseline')
    if summary['baseline']['sequences_correct']!=24: raise RuntimeError('M4 failed; stop before M5')
    # Exact sequence/stage hypotheses are measured, not forced into the model.
    for kind in 'ABCD':
        experiment(f'lesion_{kind}',intervention=kind)
        for seed in (7,11,19): experiment(f'random_{kind}_{seed}',intervention=kind,random_seed=seed)
    experiment('null_no_i_to_i',intervention='no_i_to_i')
    for delay in (2400,3200,4000): experiment(f'delay_{delay}',overrides={'delay_ms':delay})
    for sigma in (.03,.1,.2,.4):
        for seed in (7,11,19): experiment(f'noise_{sigma}_{seed}',sigma=sigma,seed=seed)
    for release in (0.,.4,1.2): experiment(f'gate_{release}',overrides={'w_release':release})
    for recurrence in (0.,1.6,2.2): experiment(f'recurrence_{recurrence}',overrides={'w_rec':recurrence})
    write_json(out/'summary.json',summary); write_json(out/'manifest.json',manifest)
    geometry=analyze(baseline); write_json(out/'representation.json',geometry)
    gates={}
    for group in ('R1','R2','R3','R4','M_D','M_S','gate12','gate23','release12','release23'):
        gates[group]={'min':float(min(r.rates[:,r.groups[group]].min() for r in baseline)),
                      'max':float(max(r.rates[:,r.groups[group]].max() for r in baseline))}
    write_json(out/'activity_ranges.json',gates)
    with (out/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['experiment','sequences_correct','n','stage1','stage2','stage3','stage4'])
        for name,metric in summary.items():
            writer.writerow([name,metric['sequences_correct'],metric['n'],*metric['stage_accuracy']])
    # Static scientific figures, no interactive or generated-image approximations.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
    r=baseline[1]
    for name in ('R1','R2','R3','R4','M_D','M_S'):
        axes[0,0].plot(r.times,r.rates[:,r.groups[name]].max(axis=1),label=name)
    axes[0,0].legend(ncol=3); axes[0,0].set(xlabel='Time (ms)',ylabel='Normalized rate')
    for name,selected in (('gate12',0),('release12',0),('gate23',1),('release23',1)):
        axes[0,1].plot(r.times,r.rates[:,r.groups[name][selected]],label=name+' selected')
    axes[0,1].legend(); axes[0,1].set(xlabel='Time (ms)',ylabel='Normalized rate')
    sigmas=[0,.03,.1,.2,.4]
    for seed in (7,11,19):
        vals=[100]+[100*summary[f'noise_{s}_{seed}']['sequences_correct']/24 for s in sigmas[1:]]
        axes[1,0].plot(sigmas,vals,'o-',label=f'seed {seed}')
    axes[1,0].legend(); axes[1,0].set(xlabel='Position current noise SD',ylabel='Sequence accuracy (%)',ylim=(-5,105))
    vals=[100*summary[f'lesion_{k}']['sequences_correct']/24 for k in 'ABCD']
    axes[1,1].bar(list('ABCD'),vals)
    axes[1,1].set(xlabel='Specific lesion',ylabel='Sequence accuracy (%)',ylim=(0,105))
    fig.savefig(out/'validation.png',dpi=160); plt.close(fig)
    lines=['# Handcrafted E/I v1 验证报告','',
        '本结果验证给定 L/D/S、固定连接和外部时钟下的机制原型，不代表 primitive 推断、学习或生理参数拟合。',
        '',f"无噪声完整序列：{summary['baseline']['sequences_correct']}/24；逐 stage：{summary['baseline']['stage_accuracy']}。",'',
        '所有实验的逐步率向量、群体标签、事件、干预连接及窗口均已归档；输入与 target 保存在独立 task 文件。',
        'metrics.csv 为逐实验指标，manifest.json 为完整协议；source_hashes.json、config.json、environment.json 固定复现身份。','',
        '## 因果干预','']
    for k in 'ABCD':
        lines.append(f"- {k}: {summary[f'lesion_{k}']}；等剂量随机对照 seeds 7/11/19："+
                     str([summary[f'random_{k}_{seed}']['sequences_correct'] for seed in (7,11,19)]))
    lines += ['', '## 表征与限制','',
        'representation.json 同时给出分支间 principal angles、分支内线性/中心化位置维数、奇异值、VAF、participation ratio 和活跃比例。',
        '分支由固定的独立坐标群体构成，分离角受该拓扑直接影响，不能用来宣称涌现正交性。1/2/4/4 是潜在分支数。',
        '保持测试只证明有限时窗中的持续活动；未证明连续吸引子、全局稳定性或自主阶段转换。',
        '随机 lesion 仅三组连接抽样；报告原始数值，不作统计显著性或普适鲁棒性推断。噪声只在 sample 的 x_L 上采样一次。','',
        '## 复现','', '```powershell',
        'python -m unittest discover -s handcrafted_ei/tests -v',
        'python -m handcrafted_ei.evaluate --output <fresh-output-directory>', '```','',
        '![验证图](validation.png)','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    # Explicit stage-specific hypotheses; stop/report on failure rather than rewriting truth.
    expected={'A':[1,0,0,0],'B':[1,1,1,1],'C':[1,1,0,0],'D':[1,1,1,1]}
    checks={k:summary[f'lesion_{k}']['stage_accuracy']==v for k,v in expected.items()}
    write_json(out/'causal_checks.json',checks)
    if not all(checks.values()): raise RuntimeError(f'causal acceptance failed: {checks}')
    pack_and_verify(out)


if __name__=='__main__': main()
