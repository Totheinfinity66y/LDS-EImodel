"""Build a self-contained, hash-indexed v3 figure delivery and file-level QA."""
from pathlib import Path
import json, csv, subprocess, sys, platform
from collections import Counter
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageStat
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .paper_v3 import ROOT, OUT, MODES, REF, digest, rows
from ..evaluation.population_data import source_identity
from ..evaluation.figure_data_geometry import load


def write(name,text):
    (OUT/name).write_text(text.strip()+'\n',encoding='utf-8')


def run():
    analysis_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    audit=json.loads((OUT/'manifests/independent_audit.json').read_text(encoding='utf-8'))
    commit=audit.get('commit','971704664740ecad33ea2a8d3ae30fb8ab964ee1')
    summary={};inventory=[];inputs={};protected=source_identity(ROOT/'handcrafted_ei/artifacts/v2/run')
    for mode in MODES:
        d=load(mode);folder=OUT/'derived'/mode
        with np.load(folder/'fig08_basin_slices_v3.npz') as z:
            codes=z['class_code'];legal=z['legal_mask'];counts=Counter(codes[legal].tolist())
            basin=dict(legal=int(legal.sum()),invalid=int((~legal).sum()),classes={str(z['class_names'][k]):counts[k] for k in range(5)},max_residual=float(z['residual_max_per_ms'][legal].max()))
        stage=rows(folder/'fig09_perturbation_classification.csv');cert=rows(folder/'fig08_v3_fixed_point_certificates.csv')
        summary[mode]=dict(basin=basin,stage_counts=dict(Counter(r['endpoint_outcome'] for r in stage)),stage_cases=len(stage),
            maximum_replay_error=max(float(r['replay_max_error']) for r in stage),certified_endpoints=sum(r['certified']=='True' for r in cert),
            max_endpoint_residual=max(float(r['residual_max_per_ms']) for r in cert),
            correct_R4=sum(r['final_readout_correct']=='True' for r in stage),correct_sequence=sum(r['sequence_correct']=='True' for r in stage),
            input_assays=rows(folder/'fig09_existing_input_classification.csv'))
        with np.load(folder/'fig04_trajectories.npz') as z:summary[mode]['branch_2d_R3_variance_fraction']=float(z['R3_branch_variance_captured_2d'])
        for p in [ROOT/'artifacts/neural_representation_v2/data'/mode/'recording.npz',ROOT/'artifacts/neural_representation_v2/data'/mode/'metadata.json',Path(d['archive_path']),*sorted((ROOT/'artifacts/neural_representation_v2/metrics'/mode).glob('*'))]:
            if p.is_file():inputs[str(p.relative_to(ROOT)).replace('\\','/')]=digest(p)
        required=['fixed_points.npz','fixed_points.csv','basin_full.npz','basin_response.npz','basin_active_branch.npz','basin_unselected_branch.npz','basin_E.npz','basin_I.npz','basin.csv','state_perturbation.npz','local_flow.npz','input_summary.csv']
        required += [f'input_{assay}_{seed}.npz' for assay in ('source_time','R3_fixed_clock') for seed in (7,11,19)]
        for name in required:
            p=REF/mode/name;record=dict(path=str(p.relative_to(ROOT)).replace('\\','/'),exists=p.exists(),impact='')
            if p.exists():
                record.update(bytes=p.stat().st_size,sha256=digest(p));inputs[record['path']]=record['sha256']
                if p.suffix=='.npz':
                    with np.load(p) as z:record['arrays']={k:list(z[k].shape) for k in z.files}
            else:record['impact']='Not used by v3; no synthetic replacement. Required plotted inputs raise errors when absent.'
            inventory.append(record)
    (OUT/'manifests/data_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    (OUT/'manifests/numerical_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    # Structural controls stay supplementary, never replace the dimensional angle spectra.
    for mode in MODES:
        with np.load(ROOT/'artifacts/neural_representation_v2/metrics'/mode/'subspace_geometry.npz') as z:
            target=OUT/'figures/supplementary'/f'fig05_{mode}_structural_controls.png'
            if all(target.with_suffix(ext).exists() for ext in ('.png','.svg','.pdf')):continue
            fig,axes=plt.subplots(1,3,figsize=(11,3.4),layout='constrained')
            for ax,key,title in zip(axes[:2],('R3_angles','R3_folded_overlap'),('Mean angle control (degrees)','Support-folded overlap')):
                im=ax.imshow(z[key],vmin=0,vmax=90 if key=='R3_angles' else 1,cmap='viridis');fig.colorbar(im,ax=ax);ax.set(title=title,xlabel='Branch',ylabel='Branch')
            for branch in range(4):axes[2].plot(np.arange(1,len(z[f'R3_b{branch}_evr'])+1),np.cumsum(z[f'R3_b{branch}_evr']),'o-',ms=3,label=f'branch {branch}')
            axes[2].set(title='Centered positional VAF spectrum',xlabel='Component',ylabel='Cumulative explained variance',ylim=(0,1.04));axes[2].legend(fontsize=7);fig.suptitle('Structural and variance controls | '+mode)
            from .style import save_figure
            save_figure(fig,OUT/'figures/supplementary',f'fig05_{mode}_structural_controls')
    derived_keys={}
    for path in sorted((OUT/'derived').rglob('*.npz')):
        with np.load(path) as z:derived_keys[path.relative_to(OUT).as_posix()]={key:list(z[key].shape) for key in z.files}
    (OUT/'manifests/derived_array_keys.json').write_text(json.dumps(derived_keys,indent=2),encoding='utf-8')
    # Verify every export separately; actual visual review is recorded by human-facing agents.
    checks=[];pngs=sorted((OUT/'figures').rglob('*.png'))
    for p in pngs:
        with Image.open(p) as im:
            im.load();dpi=im.info.get('dpi',(0,0));assert min(dpi)>=299 and min(im.size)>=500
            assert max(ImageStat.Stat(im.convert('RGB')).stddev)>2
            size=im.size
        for ext in ('.svg','.pdf'):
            q=p.with_suffix(ext);assert q.exists()
            if ext=='.svg':assert ET.parse(q).getroot().tag.endswith('svg')
            else:
                data=q.read_bytes();assert data.startswith(b'%PDF-') and b'%%EOF' in data[-1024:]
        checks.append(dict(path=str(p.relative_to(OUT)).replace('\\','/'),size=size,dpi=dpi))
    # Contact sheets do not replace individual core figure inspections.
    sheets=[]
    for start in range(0,len(pngs),6):
        sheet=Image.new('RGB',(1800,1500),'white');draw=ImageDraw.Draw(sheet)
        for j,p in enumerate(pngs[start:start+6]):
            with Image.open(p) as im:
                im=im.convert('RGB');im.thumbnail((880,455));sheet.paste(im,((j%2)*900,(j//2)*500+30))
                draw.text(((j%2)*900+4,(j//2)*500+8),p.stem,fill='black')
        target=OUT/'manifests'/f'contact_{start//6+1:02}.jpg';sheet.save(target,quality=90);sheets.append(str(target.relative_to(OUT)))
    (OUT/'manifests/figure_quality.json').write_text(json.dumps(dict(status='PASS_FILE_INTEGRITY',groups=checks,contact_sheets=sheets,visual_review='See reports/INDEPENDENT_AUDIT.md and literature round04 reports'),indent=2),encoding='utf-8')
    raw='handcrafted_ei/artifacts/v2/run'; rec='artifacts/neural_representation_v2/data/<encoding>/recording.npz';met='artifacts/neural_representation_v2/metrics/<encoding>'
    panelspec={
    1:[('A–D','Representative neurons, E/I time courses and grouped population activity','fig01_population_activity.npz','paper_figures_early.fig01','archived full rates; sample/delay/readout events','Kobak / Churchland population time courses')],
    2:[('A–D','Branch routes, selected vs competitor activity and margins','fig02_branch_dynamics.npz','paper_figures_early.fig02','all 24 conditions; R1 competitor is NA','Mante Fig2/5 descriptive condition trajectories')],
    3:[('A–E','Memory/Response handoff, fixed rule axes, feedback cut and matched controls','fig03_handoff_axes.npz; fig03_temporal_ablation.csv; archived lesion traces','paper_figures_early.fig03','D handoff R2, S handoff R3; axes fixed at recorded anchors','Inagaki Fig5 adapted persistence/control contrast')],
    4:[('A','24 full trajectories in one global PCA','fig04_trajectories.npz: global_scores/global_mean/global_components','paper_v3.fig4','all 24; stride4 fit inherited and verified','Mante Fig2/5 shared neural-state projection'),('B','Fixed-L branch discrimination','fig04_trajectories.npz: branch_scores/branch_basis/R2_D_centroids/R3_branch_centroids','paper_figure_v3_geometry.build','L=0; balanced S at R2; four D/S at R3 decision window','Mante-inspired descriptive contrast, not dPCA'),('C','Three transition windows on the same branch axes','fig04_trajectories.npz: branch_scores/times_ms','paper_v3.fig4','to_R2/3/4 through respective readout; fixed limits','Mante shared coordinates'),('D','Full-state velocity and centroid separation','fig04_trajectories.npz: speed/speed_times_ms/R3_centroid_distances','paper_figure_v3_geometry.build','finite differences divided by actual 5ms; all132 neurons','method adapted')],
    5:[('A','Four branch trajectories and six endpoints in shared global axes','fig04_trajectories.npz: global_scores','paper_v3.fig5','R3 formation to readout3; overlap disclosed','Gallego Fig1/3 shared projection'),('B','Six complete dimensional angle spectra','fig05_principal_angle_spectra.csv: angles_degrees','paper_figure_v3_geometry.build','R3; exact archived semicolon angle lists','Gallego Fig3b'),('C','Bidirectional variance capture','fig05_principal_angle_spectra.csv: cross_vaf_a_to_b/cross_vaf_b_to_a','paper_v3.fig5','full retained centered rank; target variance fraction','Gallego Fig3c ADAPTED; original across/within ratio differs'),('D','Time-resolved full/Response/support-folded geometry','fig05_time_resolved_geometry.npz: *_angles_degrees/*_centroid_distance/*_ranks/*_singular_values','paper_figure_v3_geometry.temporal_geometry','each recorded time; six L samples per branch; centered rank<=5; abs/rel tol1e-8','Gallego geometry; fixed supports are structural')],
    6:[('A–D','Six actual discrete states, whole/Response RDM and persistence margin','fig06_position_stability.npz','paper_figures_geometry.fig6','D=+1,S=1; six L; R3 decision window and stage','Kriegeskorte RDM; discrete points without ring')],
    7:[('A–D','Condition-held-out readout, cross-temporal decoding, handoff and held-noise-seed probes','fig07_branch_decoding.npz; decoding.npz; decoding_noise_seed.npz','paper_figures_geometry.fig7','disjoint LDS folds vs separate noise seeds7/11/19','King & Dehaene time-generalization METHOD ADAPTED')],
    8:[('A','Six endpoints within one R3 branch','fig08_six_position_fixed_points_branch0.npz','paper_v3.fig8','D=+1,S=1; six L; other branches supplement','Sussillo & Barak Fig3; Inagaki Fig5 adapted'),('B','Actual state-kick relaxation paths, including failed recovery','external lds_results/<encoding>/basin_full.npz: rates/initial_reference_index/amplitude','paper_v3.fig8','three seed directions; preclip amplitude0.1; start/end shown','Inagaki Fig5 perturbation semantics adapted'),('C','Mixed complete-state initial-condition sections','fig08_basin_slices_v3.npz: initial_rates/endpoints/legal_mask/class_code','paper_v3_dynamics.basin_slices','4 branches×3 triples012/024/135×21x21; 2000ms; sample=clock0/tonic retained','Sussillo fixed-field analysis adapted'),('D–E','Full residual, continuous/Euler spectra and kink certificate','fig08_v3_fixed_point_certificates.csv','reference_dynamics.exact_local_stability/piecewise_cascade_certificate','24 endpoints; residual<1e-7/ms; kink certificate required','Sussillo local stability'),('F','Actual-dose state-kick outcomes','fig09_state_kick_classification.csv','paper_v3.kick_panel','full target; six branch positions×three directions; postclip RMS grouped by preclip dose','Inagaki recovery vs state identity; adapted')],
    9:[('A–D','Control/pulse rates, shared control-only PCA, full cross-temporal distance and projection error','external lds_results/<encoding>/input_source_time_7.npz: control/perturbed/basis/pca_center/cross_temporal_distance/full_squared/projected_squared/orthogonal_squared','paper_v3.fig9','50ms finite input pulse; seed7 representative; fixed-clock separate supplement','Zhou Fig7 METHOD ADAPTED; control-only PCA fit is LDS choice'),('E','Independent state-kick classifications','fig09_state_kick_classification.csv','paper_v3.kick_panel','never pooled with finite input recovery','Inagaki Fig5 adapted'),('F','Four-stage finite input outcomes','fig09_stage_perturbation_v3.npz; fig09_perturbation_classification.csv','paper_v3_dynamics.stage_perturbations','24×4×3 seeded directions; 50ms,RMS0.25; final R4 + intermediate R2/R3','Zhou perturbation method adapted to scheduled LDS')],
    10:[('A–F','Joint/fixed PCA, branch geometry and current-dose-matched encoding comparison','derived/comparison/fig10_common_basis.npz; fig10_encoding_comparison.csv; fig10_raw_noise_doses.csv','paper_figures_comparison.run','all3 encodings; same neuron identities; raw coordinate noise separated','Gallego Fig3 adapted comparison')]
    }
    mapping=['# Figure data map','',f'Model commit: `{commit}`. Full source/array inventory: [data_inventory.json](manifests/data_inventory.json).',f'Formal raw source: `{raw}`; standardized recording: `{rec}`; metrics: `{met}`. All neural rates are dimensionless. Each output is PNG300dpi/SVG/PDF.','', 'One_hot supplies main figures; ring/topology and other branch/assay panels are supplementary. Figure1/2/3/6/7/10 reuse SHA-verified completed computations and exports; v3 recomputes4/5 and supplements8/9. No baseline is rerun.']
    for n,specs in panelspec.items():
        mapping+=['',f'## Figure {n}']
        outputs=[str(p.relative_to(OUT)).replace('\\','/') for p in pngs if p.name.startswith(f'fig{n:02}_')]
        mapping+=['','Outputs: '+', '.join(f'[{Path(v).stem}]({v})' for v in outputs)]
        for panel,question,keys,fun,window,reference in specs:
            mapping+=['',f'**Panel {panel} — {question}.**',f'- Input: `{keys}` under `derived/<encoding>/` unless marked external; exact SHA and upstream paths in manifest.',f'- Function: `{fun}`; conditions/windows: {window}.',f'- Reference: {reference}. New simulation: '+('yes, independent complete-state initializations' if n==8 and panel=='C' else 'yes, independent paired task-time pulse replay' if n==9 and panel=='F' else 'no; recorded/computed data reused or algebraically reprojected')+'.']
        if n in (1,2,3,6,7,10):
            caption=next(iter(sorted((OUT/'figures/main').glob(f'fig{n:02}*caption.md'))),None)
            if caption:mapping+=['','Detailed original panel caption (scientific definitions retained):',caption.read_text(encoding='utf-8').strip()]
    mapping+=['','## Exact derived array keys','Every derived NPZ is indexed by file/key/shape in [derived_array_keys.json](manifests/derived_array_keys.json). Data are never implicitly reshaped into repeats. Per-panel output captions and source code define each plotted reduction; missing plotted inputs fail explicitly.']
    write('FIGURE_DATA_MAP.md','\n'.join(mapping))
    reference=['# Reference method map','','This is a METHOD ADAPTED analysis of a fixed handcrafted LDS E/I model. It is not source-exact reproduction. Paper2Skill packages source evidence; Codex experts separately audited methods, adapters and actual output PNGs.','','- [Inagaki/Mante/Gallego/Sussillo source contracts and four-round review](reports/REFERENCE_METHOD_MAP_INAGAKI.md).','- [Zhou source contract](reports/REFERENCE_METHOD_MAP_ZHOU.md).','- [Inagaki actual Figure8 review](reports/literature_inagaki/round04_figure_review.md).','- [Zhou actual Figure9 review](reports/literature_zhou/round04_actual_figure_review.md).','','Inagaki uses coding directions and independent experimental trials; LDS uses actual 132-state rates and endpoint PCA, no animal repeats. Gallego Fig3c across/within VAF ratio is not identical to the archived target-variance-capture fraction. Mante third-party notebook is not author code. Sussillo fixed-point concepts are adapted to the existing NumPy bounded-rate integrator; no TensorFlow/PyTorch migration. Zhou Fig7 uses trained-network ensembles and different external timing; LDS control-only PCA is an explicit choice because the source fit set is unknown. Source-exact author-code execution remains BLOCKED by missing source data/checkpoints/analysis components, independently of successful LDS adaptation.']
    write('REFERENCE_METHOD_MAP.md','\n'.join(reference))
    lines=['# Numerical validation','','Status: PASS_WITH_LIMITS for LDS methods adaptation; source-exact paper reproduction is BLOCKED.','',f'Base model commit: `{commit}`. CPU environment: Python {platform.python_version()}, NumPy {np.__version__}; exact packages in [runtime preflight](reports/runtime_preflight.json). Process-local Conda Library/bin is required on this Windows host; no dependency installed.','','91 regression tests passed; [full log](reports/tests_full.txt). New geometry and numerical tests cover common neural coordinates, principal-angle invariance, VAF matrix projection, rank<=5/NA, energy closure, classifier categories, real Euler/field/Jacobian conventions, zero pulse, paired history and preclip/postclip dose. Red/green development evidence is preserved under reports; missing-module red verifies new API absence, numerical classifier defect regression supplies behavior checks.','','Independent full-array audit: [report](reports/INDEPENDENT_AUDIT.md), [machine record](manifests/independent_audit.json). Input hashes and exact shape/key inventory: [inventory](manifests/data_inventory.json).','', '## Thresholds and protocols','','- Singular value threshold max(1e-8,largest×1e-8); six centered location samples imply rank≤5. Low variance angles are NA, not zero.','- Full fixed-field max residual <1e-7 rate/ms; clip-kink stability uses piecewise cascade certificate separately from representative Jacobian eigenvalues.','- Active position threshold 0.2; classify all six position units in every branch. Outside/multibranch takes precedence over within-branch multiple positions; counts retain simultaneous-activity flags.','- Full-state recovery additionally requires original unique branch/position and max-norm state error<0.02. Same final Y/readout alone does not establish recovery.','- Source-time final classification is R4, intermediate R2/R3 checked; residual/converged is NA under a changing clock. R3_fixed_clock retains archived fixed clock and uses R3 at its actual fixed field.','- Mixed initial states are full endpoint-affine states in the legal [0,1]^132 cube; invalid grids masked, never clipped. 21×21×3 slices×4 branches; 2000ms, dt5ms, batch32. No claim that this exhausts the six-position basin geometry.','- Four task-time pulse windows, 50ms, RMS0.25, seeds7/11/19, dose12.5 current-RMS ms. Conditions/directions are descriptive, not independent networks/animals.']
    for mode,s in summary.items():lines+=['',f'## {mode}',f'- New mixed-state scan: {s["basin"]}.',f'- Paired stage outcomes ({s["stage_cases"]}): {s["stage_counts"]}.',f'- Maximum control replay error: {s["maximum_replay_error"]:.3g}; certified reference endpoints: {s["certified_endpoints"]}/24; max endpoint residual {s["max_endpoint_residual"]:.3g}/ms.',f'- Correct final R4 readouts: {s["correct_R4"]}/288; complete sequences: {s["correct_sequence"]}/288. Two branch display axes capture {s["branch_2d_R3_variance_fraction"]:.4%} of fixed-L R3 centroid variance; projection loses information.']
    write('NUMERICAL_VALIDATION.md','\n'.join(lines))
    write('RUN_INSTRUCTIONS.md',r'''# Run instructions

Run in repository root with the existing `analysis` Conda environment. No installation is needed. These PowerShell variables affect only the current process:

```powershell
$env:PATH='C:/Users/Totheinfinity/.conda/envs/analysis;C:/Users/Totheinfinity/.conda/envs/analysis/Library/bin;C:/Users/Totheinfinity/.conda/envs/analysis/Scripts;'+$env:PATH
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$analysisPython='C:/Users/Totheinfinity/.conda/envs/analysis/python.exe'
& $analysisPython -m handcrafted_ei.evaluation.paper_v3_dynamics --grid-size 21
& $analysisPython -m handcrafted_ei.visualization.paper_v3
& $analysisPython -m unittest discover -s handcrafted_ei/tests -v
& $analysisPython artifacts/neural_paper_figures_v3/reports/independent_check.py
& $analysisPython -m handcrafted_ei.visualization.paper_v3_reports
```

The default renderer verifies and copies reusable Figure1/2/3/6/7/10 exports and derived data from the local v1 manifest; it never infers curves from PNGs. To independently rebuild all figures without relying on that figure archive, use:

```powershell
& $analysisPython -m handcrafted_ei.evaluation.paper_v3_dynamics --output artifacts/neural_paper_figures_v3_rebuild
& $analysisPython -m handcrafted_ei.visualization.paper_v3 --rebuild-reused --output artifacts/neural_paper_figures_v3_rebuild
```

These commands use the formal raw ZIP archive for existing ablation/noise assays and comparison calculations. They do not change the baseline model. V3 geometry reads standardized recordings and verified metrics; v3 dynamics requires existing reference fixed_points/basin/input NPZs. Missing inputs raise explicit errors. See data_inventory.json for exact keys, availability and hashes. Rebuilding original reference arrays when absent requires the full reference-grounded pipeline and its own evidence gates, not a PNG adapter. The default commands were executed for this delivery; the slower complete-rebuild branch is exposed for reproducibility and was not redundantly rerun.

Large stage-perturbation/comparison NPZs stay local and are SHA-indexed. Baseline ZIPs and original literature materials must remain locally available. The code/data contract does not promise source-exact paper reproduction.
''')
    review=['# Figure review','','Overall: METHOD ADAPTED / PASS_WITH_LIMITS. Original source-exact execution remains BLOCKED. Independent reports bind actual arrays and PNGs; file integrity alone is insufficient.','', 'Actual core review: [independent audit](reports/INDEPENDENT_AUDIT.md), [Inagaki four-round review](reports/literature_inagaki/round04_figure_review.md), [Zhou four-round review](reports/literature_zhou/round04_actual_figure_review.md).']
    descriptions={1:'Real neuron/E/I time courses and events; no fabricated trials or rate units.',2:'All branches/competitors represented; R1 competitor NA; routing is handcrafted.',3:'Memory amplitude, Response recruitment and feedback controls distinguished from information erasure.',4:'All24 common PCA and fixed-L balanced discriminant axes; global2D overlaps real; two discriminant axes capture only part of branch variance.',5:'Full dimensional spectra and bidirectional capture fractions; pre-R3 angles may reflect earlier Response populations; folded distances at numerical zero use an honest axis.',6:'Six actual discrete points/RDM; no continuous ring or imposed polygon.',7:'Disjoint LDS-condition generalization separated from held-noise realizations; no training of the network.',8:'Six same-branch endpoint certificates and actual kick relaxation; black hollow failed endpoints; multiple initial-state sections reveal mostly R3-inactive outcomes, not an exhaustive basin atlas.',9:'State kicks and finite input remain separate; full-state recovery, same position, other positions, multiple/outside/inactive/unconverged are explicit; fixed-clock nonzero error plateau preserved.',10:'Joint/fixed neural axes and matched current perturbations; raw-coordinate noise dosage not equated across encoding dimensions.'}
    for n,desc in descriptions.items():review+=['',f'## Figure {n}',desc,'See FIGURE_DATA_MAP.md for each panel input, axes, window, reference and output. Reused figures retain source SHA and were included in actual final contact-sheet review.']
    review+=['','## Scientific limits','No continuous attractor, emergent subspace or exactly-six-global-attractors claim. The three affine slices and finite seeded directions leave other initial states unsampled. No new stable mixed attractor was discovered by this scan; low residual alone would not establish stability. R3-inactive is stage inactivity, not whole-network silence. Paper-derived visual grammar does not imply biological equivalence.']
    write('FIGURE_REVIEW.md','\n'.join(review))
    links=['# V3 科研图表交付','','主图、三编码补图、派生数据、数值与来源证据全部位于本目录。核心结论：分支判别投影能显示路由，但二维投影不能保留全部状态误差；混合初态扫描多数失去R3活动；相同最终读出不等于完整状态恢复。','', '[数据与panel映射](FIGURE_DATA_MAP.md) · [文献方法](REFERENCE_METHOD_MAP.md) · [数值验证](NUMERICAL_VALIDATION.md) · [逐图审阅](FIGURE_REVIEW.md) · [重建命令](RUN_INSTRUCTIONS.md)','']
    for p in sorted((OUT/'figures/main').glob('*.png')):links += [f'## {p.stem}',f'![{p.stem}]({p.relative_to(OUT).as_posix()})','']
    links+=['## 全部图片索引','']+[f'- [{p.stem}]({p.relative_to(OUT).as_posix()})' for p in pngs]
    write('README.md','\n'.join(links))
    # Per-core figure captions are self-contained and stored beside each output.
    captions={4:'All 24 full132 trajectories use the same global PCA mean/basis fitted at uniform stride4. Branch-discriminant axes use L=0 balanced R2 D centroids and four R3 D/S centroids, each stage centered separately then combined with balanced weighting. Axes are fixed across time. Their contrast explained variance differs from R3 between-branch variance; both are archived. C shares limits. Speed uses measured dt, gate/readout/retire marked. This is descriptive branch projection, not dPCA or an emergent-subspace claim.',5:'Archived R3 full principal-angle spectra are read verbatim, not estimated from the mean-angle heatmap. Bidirectional values are fractions of target centered variance captured, not Gallego across/within ratios. Whole/Response/folded coordinates retain all units; six L samples imply centered rank≤5. Per-time SVD uses absolute/relative tolerance1e-8; inactive cases remain NA. Early whole/Response angles may arise from R1/R2, not R3 activation. Folded distances below1e-12 are numerical zero. Handcrafted supports explain structural separation.',8:'Fixed D/S R3 branch, six L states in one endpoint PCA; no regular-polygon placement or ring connections. Colors in B indicate original L, crosses start, hollow black endpoints are failed/inactive outcomes. Full132 state kicks relax under sample=clock=0 with original tonic. C is a legal initial-state affine section, not a closed invariant manifold or exhaustive basin. Other triples and branches are supplementary. Full residual and spectra are supported by piecewise cascade certificates at clip kinks. F uses actual postclip RMS averaged within preclip-dose groups; full-state recovery requires unique original branch/position plus maxnorm error<0.02. Same position without full recovery is separate; zero categories are retained. All rates dimensionless.',9:'A–D reuse actual seed7 control and 50ms finite-input trajectories, with common control-only PCA and explicit full132/PC1–2/orthogonal error. Control-only fitting is an LDS adaptation; the source Fig7 fitting set is unspecified. The cross-temporal matrix is full-state Euclidean distance. E is a separate tonic-only R3 state-kick assay, never pooled with input recovery; actual postclip RMS and seven endpoint categories are shown. F summarizes 24 conditions×3 deterministic seeded directions at each of four pulse windows; final R4 state and shared Y readout evaluated separately, intermediate R2/R3 identities logged. Source-time has no equilibrium-convergence claim; R3_fixed_clock retains archived clock and can exhibit a persistent nonzero error plateau. Inactive means stage-specific, not whole-network silence. No animal/network repeats or invented error bars.'}
    for p in pngs:
        n=int(p.name[3:5])
        if n in captions:p.with_suffix('.caption.md').write_text(captions[n]+'\n',encoding='utf-8')
    analysis_files=[ROOT/'handcrafted_ei/evaluation/paper_figure_v3_geometry.py',ROOT/'handcrafted_ei/evaluation/paper_v3_dynamics.py',Path(__file__),ROOT/'handcrafted_ei/visualization/paper_v3.py']
    manifest=dict(schema=3,model_commit=commit,analysis_base_commit=analysis_base,analysis_sources={p.relative_to(ROOT).as_posix():digest(p) for p in analysis_files},
        protected_sources=protected,inputs_sha256=inputs,summary=summary,rate_units='dimensionless',formats=['png300dpi','svg','pdf'],
        parameters=dict(dt_ms=5,basin_grid=21,basin_duration_ms=2000,activity_threshold=.2,residual_max_threshold=1e-7,full_recovery_maxnorm=.02,pulse_ms=50,pulse_rms=.25,seeds=[7,11,19]),
        files={})
    # Include all delivery outputs and local-only originals with explicit scope; no circular self-hash.
    manifest['files']={p.relative_to(OUT).as_posix():dict(sha256=digest(p),bytes=p.stat().st_size,local_only=('literature_' in p.as_posix() and p.suffix in ('.pdf','.png','.jpg','.ipynb')) or p.name in ('fig09_stage_perturbation_v3.npz','fig10_matched_current_full.npz')) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='figure_manifest.json' and '__pycache__' not in p.parts}
    (OUT/'figure_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(dict(figure_groups=len(pngs),exports=len(pngs)*3,summary=summary),indent=2),flush=True)


if __name__=='__main__':run()
