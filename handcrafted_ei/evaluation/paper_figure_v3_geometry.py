"""V3 geometry in fixed neural coordinates; no model execution or state writes."""
from pathlib import Path
import csv
import itertools
import numpy as np
from .figure_data_geometry import load, SOURCE
from .population_activity import stage_samples, branch_masks, population_sets, save_rows
from .subspace_geometry import pca, principal_angles, cross_vaf

PAIRS=list(itertools.combinations(range(4),2))
ABS_TOL=1e-8
REL_TOL=1e-8


def discriminant_axes(centroids):
    x=np.asarray(centroids,float); fit=pca(x)
    s=fit['singular_values']; keep=s>max(ABS_TOL,(s[0] if len(s) else 0)*REL_TOL)
    return fit['components'][keep].T,fit['mean'],s,fit['evr'][keep]


def project_energy(delta,basis):
    inside=delta@basis
    outside=delta-inside@basis.T
    return np.sum(delta**2,axis=-1),np.sum(inside**2,axis=-1),np.sum(outside**2,axis=-1)


def temporal_geometry(r,ids):
    ntime=r.shape[1]; angles=np.full((ntime,6,5),np.nan)
    distances=np.zeros((ntime,6)); ranks=np.zeros((ntime,4),int); singular=np.zeros((ntime,4,6))
    for time in range(ntime):
        matrices=[r[ix,time] for ix in ids]; fits=[pca(x) for x in matrices]
        qs=[]
        for j,f in enumerate(fits):
            s=f['singular_values']; keep=s>max(ABS_TOL,s[0]*REL_TOL)
            singular[time,j,:len(s)]=s; ranks[time,j]=keep.sum()
            qs.append(f['components'][keep].T)
        for k,(a,b) in enumerate(PAIRS):
            distances[time,k]=np.linalg.norm(matrices[a].mean(0)-matrices[b].mean(0))
            if qs[a].shape[1] and qs[b].shape[1]:
                v=principal_angles(qs[a],qs[b]); angles[time,k,:len(v)]=v
    return dict(angles_degrees=angles,centroid_distance=distances,ranks=ranks,singular_values=singular)


def build(mode,output):
    d=load(mode); r=d['rates']; t=d['times_ms']; tasks=d['tasks']; out=Path(output)/'derived'/mode
    out.mkdir(parents=True,exist_ok=True)
    with np.load(SOURCE/'metrics'/mode/'subspace_geometry.npz') as z:
        global_data={k:z[k] for k in ('global_scores','global_components','global_mean','global_evr')}
    np.testing.assert_allclose(global_data['global_scores'],(r-global_data['global_mean'])@global_data['global_components'].T,atol=1e-10)
    fixed=np.array([i for i,v in enumerate(tasks) if v['L']==0]); cond=np.array([(v['L'],v['D'],v['S']) for v in tasks])
    r2=stage_samples(d,2)[fixed]; r3=stage_samples(d,3)[fixed]
    # D contrast uses balanced S averages at R2; R3 uses four D/S centroids.
    dcent=np.array([r2[cond[fixed,1]==v].mean(0) for v in (1,-1)])
    contrast=np.concatenate([(dcent-dcent.mean(0))/np.sqrt(2),(r3-r3.mean(0))/2])
    axes,_,sv,evr=discriminant_axes(contrast)
    center=r3.mean(0); scores=(r-center)@axes
    dist=np.array([np.linalg.norm(r3[a]-r3[b]) for a,b in PAIRS])
    k=min(2,axes.shape[1]); fraction=float(np.sum(((r3-r3.mean(0))@axes[:,:k])**2)/np.sum((r3-r3.mean(0))**2))
    pack=dict(times_ms=t,conditions=cond,fixed_L_trials=fixed,branch_basis=axes,branch_center=center,
              branch_scores=scores,branch_singular_values=sv,branch_contrast_evr=evr,
              R2_D_centroids=dcent,R3_branch_centroids=r3,R3_centroid_distances=dist,
              R3_branch_variance_captured_2d=np.array(fraction),
              speed=np.linalg.norm(np.diff(r,axis=1),axis=2)/np.diff(t)[None,:],speed_times_ms=t[1:],**global_data)
    np.savez_compressed(out/'fig04_trajectories.npz',**pack)
    masks=branch_masks(d,3); ids=[np.flatnonzero(m) for m in masks]; response=population_sets(d)['response']
    # Folding aligns homologous position units across branch supports. All R3 activity retained.
    folded=r[:,:,d['groups']['R3']].reshape(24,len(t),4,6).sum(2)
    geom=dict(times_ms=t,pairs=np.array(PAIRS),absolute_singular_threshold=np.array(ABS_TOL),relative_singular_threshold=np.array(REL_TOL))
    for name,states in [('whole',r),('response',r[:,:,response]),('folded',folded)]:
        geom.update({name+'_'+key:val for key,val in temporal_geometry(states,ids).items()})
    np.savez_compressed(out/'fig05_time_resolved_geometry.npz',**geom)
    # Preserve archived dimensional spectra verbatim; do not infer them from mean angles.
    with (SOURCE/'metrics'/mode/'subspace_pairs.csv').open(encoding='utf-8') as f:
        rows=[row for row in csv.DictReader(f) if int(row['stage'])==3]
    save_rows(out/'fig05_principal_angle_spectra.csv',rows)
    return d,pack,geom,rows
