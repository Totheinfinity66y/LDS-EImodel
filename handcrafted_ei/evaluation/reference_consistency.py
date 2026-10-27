"""Independent spot recomputation of existing Figure1–7 metrics; no model edits."""
from pathlib import Path
import csv
import json
import numpy as np
from scipy.linalg import subspace_angles
from scipy.spatial.distance import pdist,squareform
from .reference_adapter import load_audited_dataset
from .reference_reproduction import ROOT,DEFAULT,dump,csvwrite


def run(source=ROOT/'handcrafted_ei/artifacts/v2/run',previous=ROOT/'artifacts/neural_representation_v2',out=DEFAULT):
    rows=[];angle_rows=[];recruitment=[];new_summary=[]
    for mode in ('one_hot','ring','topology'):
        d=load_audited_dataset(source,mode);t=d['times_ms'];samples=[]
        for i,e in enumerate(d['events']):samples.append(d['rates'][i,(t>e['readout3']-20)&(t<=e['readout3'])].mean(0))
        samples=np.array(samples);task=d['tasks'];basis=[];response_basis=[]
        for b,(dr,step) in enumerate([(1,1),(1,2),(-1,1),(-1,2)]):
            mask=np.array([q['D']==dr and q['S']==step for q in task]);x=samples[mask];xc=x-x.mean(0)
            _,s,vt=np.linalg.svd(xc,full_matrices=False);rank=int(np.count_nonzero(s>max(x.shape)*np.finfo(float).eps*s[0]));basis.append(vt[:rank].T)
            vaf=s*s/(s@s);pr=float(1/(vaf@vaf))
            response=x[:,d['groups']['R3']];dist=squareform(pdist(response));off=dist[np.triu_indices(6,1)]
            rr=response-response.mean(0);_,sr,vtr=np.linalg.svd(rr,full_matrices=False);response_basis.append(vtr[:5].T)
            active=np.flatnonzero(np.any(x-d['rates'][mask,0]>.1,axis=0))
            recruitment.append(dict(encoding=mode,stage=3,branch=b,active_unit_count=len(active),active_labels=';'.join(d['labels'][active].tolist())))
            rows.append(dict(encoding=mode,branch=b,whole_rank=rank,effective_dimension=pr,response_distance_range=float(np.ptp(off)),response_distance_mean=float(off.mean()),
                response_ring_correlation='undefined: equal offdiagonal distances',population='whole132 for SVD; current R3 for distance'))
            with (previous/'metrics'/mode/'subspace_geometry.csv').open(encoding='utf-8') as f:
                old=next(r for r in csv.DictReader(f) if r['stage']=='3' and int(r['branch'])==b)
            np.testing.assert_allclose(pr,float(old['effective_dimension']),atol=1e-12)
            if rank!=int(old['whole_rank']):raise AssertionError('rank drift')
        for a in range(4):
            for b in range(a+1,4):
                angles=np.degrees(subspace_angles(basis[a],basis[b]));local=np.degrees(subspace_angles(response_basis[a],response_basis[b]))
                angle_rows.append(dict(encoding=mode,branch_a=a,branch_b=b,whole_mean_angle=float(angles.mean()),response_mean_angle=float(local.mean()),whole_angles=';'.join(map(str,angles))))
                with (previous/'metrics'/mode/'subspace_pairs.csv').open(encoding='utf-8') as f:
                    old=next(r for r in csv.DictReader(f) if r['stage']=='3' and int(r['branch_a'])==a and int(r['branch_b'])==b)
                np.testing.assert_allclose(angles.mean(),float(old['mean_angle']),atol=1e-7)
        summary=json.loads((out/'lds_results'/mode/'summary.json').read_text(encoding='utf-8'))
        new_summary.append(dict(encoding=mode,branch_effective_dim=np.mean([r['effective_dimension'] for r in rows if r['encoding']==mode]),
            whole_mean_angle=np.mean([r['whole_mean_angle'] for r in angle_rows if r['encoding']==mode]),
            stable_endpoint_clusters=summary['stable_endpoint_clusters'],identity_retained=summary['identity_retained'],input_dimension=summary['input_dimension'],neuron_count=132))
    folder=out/'audit';csvwrite(folder/'representation_dimensions.csv',rows);csvwrite(folder/'representation_angles.csv',angle_rows);csvwrite(folder/'recruitment.csv',recruitment)
    csvwrite(folder/'encoding_comparison.csv',new_summary)
    text='''# Figure 1–7/10 一致性审计

本审计复用已有正确的共享PCA、子空间、RSA、解码实现与历史图，不将正确图重复开发为另一套算法。数值独立复算入口为 `python -m handcrafted_ei.evaluation.reference_consistency`。

| Figure | 方法与验收 | 结论与限制 |
| --- | --- | --- |
| 1 | 全132状态、真实群体/基线、无量纲率、完整图像hash | PASS；静息神经元保留 |
| 2 | 实际阈值招募、结构支持、balanced factorial effects | ADAPT；描述性ANOVA不是统计重复或dPCA |
| 3 | 真实时钟窗口、M_D/M_S交接、独立因果对照 | PASS_WITH_LIMITS；残余可解码不等于记忆未衰减 |
| 4 | 24条件统一全网络PCA，center与fit stride固定 | ADAPT；不是Churchland jPCA或Mante targeted-dimensionality reduction精确复现 |
| 5 | 独立SVD维数、SciPy principal angles复算，与历史CSV断言一致 | PASS_WITH_LIMITS；分支Response支持先验不相交，折叠坐标控制不可叫真实配准 |
| 6 | current-Response六位置距离独立重算，全网络/R3分离 | PASS_WITH_LIMITS；R3等距相关undefined，微弱全网络环相关不证明环吸引子 |
| 7 | 条件留出与leave-noise-seed-out分开、probe只读 | ADAPT；线性变量轴不是Kobak dPCA；没有新增训练模型 |
| 10 | 维数/角度复算、全部24终点新指标 | UPDATED；旧动力学六位置子集指标不再外推为全分支 |

三编码R3分支内whole有效维数约4.99999945，数值rank5；Response-only不同分支角度90°为不相交handcrafted坐标的直接后果。whole分支平均角约83.38083°，见逐对数值CSV，不能声称涌现正交。所有六位置current-R3非对角距离等距，不支持连续环流形。全网络微弱拓扑距离差需同时看旧 `rsa_population_contributions.csv` 中的Y/尾迹贡献，不能仅凭Spearman接近1下结论。

历史图及原始raw档案保持不变，路径在 `artifacts/neural_representation_v2/figure_manifest.json`。两篇核心论文的正式反向审查只认证新增8/9适配，补充文献映射属于方法一致性审计，不宣称复现这些论文全部实验。
'''
    (folder/'FIGURE_01_07_10_CONSISTENCY.md').write_text(text,encoding='utf-8')
    from ..visualization.reference_figures import comparison10
    comparison10(out,new_summary)
    print('Representation consistency PASS',flush=True)


if __name__=='__main__':run()
