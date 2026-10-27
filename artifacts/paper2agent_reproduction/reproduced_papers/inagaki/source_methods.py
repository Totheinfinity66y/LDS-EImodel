"""Methods reconstruction, not execution of original MATLAB/experimental pipeline.
Input rates are [trial,time,neuron], already binned/smoothed in caller.
No trial simulation or biological uncertainty is manufactured.
"""
import numpy as np


def fit_coding_direction(right_fit,left_fit,fit_mask):
    r=np.asarray(right_fit,float); l=np.asarray(left_fit,float); mask=np.asarray(fit_mask,bool)
    if r.ndim!=3 or l.ndim!=3 or r.shape[1:]!=l.shape[1:] or mask.shape!=(r.shape[1],) or not mask.any() or not len(r) or not len(l):
        raise ValueError('fit trials [trial,time,neuron] and nonempty time mask required')
    delta=(r.mean(0)-l.mean(0))[mask].mean(0)
    norm=np.linalg.norm(delta)
    if not np.isfinite(norm) or norm==0: raise ValueError('coding direction undefined')
    return delta/norm


def project_and_normalize(test_rates,cd,left_endpoint_median,right_endpoint_median):
    x=np.asarray(test_rates,float); cd=np.asarray(cd,float)
    if x.ndim!=3 or cd.shape!=(x.shape[-1],) or not np.isclose(cd@cd,1): raise ValueError('shape/unit CD')
    scale=right_endpoint_median-left_endpoint_median
    if not np.isfinite(scale) or scale==0: raise ValueError('endpoint normalization undefined')
    return (x@cd-left_endpoint_median)/scale


def source_phase_line(projected,bin_centers,dt_ms=10):
    """Public MATLAB logic: central difference then normalize to per10ms.
    Empty bins stay NaN. No bootstrap is performed without real replication.
    """
    x=np.asarray(projected,float); centers=np.asarray(bin_centers,float)
    if x.ndim!=2 or x.shape[1]<3 or centers.ndim!=1 or len(centers)<2 or dt_ms<=0:
        raise ValueError('projected [trial,time], at least two equally spaced bin centers')
    spacing=np.diff(centers)
    if not np.allclose(spacing,spacing[0]) or spacing[0]<=0: raise ValueError('regular bins')
    state=x[:,1:-1].ravel(); speed=((x[:,2:]-x[:,:-2])/2).ravel()*(10/dt_ms)
    means=np.full(len(centers),np.nan); counts=np.zeros(len(centers),int)
    for k,c in enumerate(centers):
        selected=(state>c-spacing[0]/2)&(state<=c+spacing[0]/2)
        counts[k]=selected.sum()
        if counts[k]: means[k]=speed[selected].mean()
    return {'centers':centers,'drift_per_10ms':means,'counts':counts}
