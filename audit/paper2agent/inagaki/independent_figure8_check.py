from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork
result={}
for mode in ('one_hot','ring','topology'):
 p=ROOT/'artifacts/paper2agent_reproduction/lds_results'/mode
 cfg=json.loads((p/'config.json').read_text());m=EINetwork(overrides=cfg);w=m.weights*m.signs[None,:];ext=m.tonic-m.theta
 with np.load(p/'fixed_points.npz') as z:
  x=z['rates'];end=z['endpoints'];f=lambda r:(np.clip(r@w.T+ext,0,1)-r)/m.tau
  dd=np.sqrt(((end[:,None]-end[None,:])**2).sum(-1));diff=abs(np.diff(x,axis=1)-cfg['dt_ms']*f(x[:,:-1])).max()
  ident=lambda r:tuple(np.unravel_index(r[m.groups['R3']].argmax(),(4,6))) if r[m.groups['R3']].max()>=.2 else None
  exact=[]
  for q,r in enumerate(end):
   drive=w@r+ext;k=(abs(drive)<1e-7)|(abs(drive-1)<1e-7);active=((drive>0)&(drive<1))|k
   edge=active[:,None]&(w!=0);deg=edge.sum(1);queue=list(np.flatnonzero(deg==0));order=[]
   while queue:
    s=queue.pop();order.append(s)
    for t in np.flatnonzero(edge[:,s]):
     deg[t]-=1
     if deg[t]==0:queue.append(t)
   assert len(order)==132
   eq=r.copy()
   for t in order:eq[t]=np.clip(w[t]@eq+ext[t],0,1)
   assert abs(f(eq)).max()<1e-12
   exact.append(float(abs(eq-r).max()))
  peak=x[:,:,m.groups['R3']].max(-1)
  result[mode]={'Euler_step_error':float(diff),'endpoint_distance_error':float(abs(dd-z['endpoint_distance']).max()),'max_fullstate_residual_per_ms':float(abs(f(end)).max()),'identity_retained':sum(ident(a)==ident(b) and ident(a)is not None for a,b in zip(z['initial_rates'],end)),'all24_union_DAG':True,'max_exact_equilibrium_distance':max(exact),'R3_peak_min':float(peak.min()),'R3_peak_max':float(peak.max()),'R3_peak_effect_max':float(abs(peak[:,-1]-peak[:,0]).max()),'minimum_offdiagonal_endpoint_L2':float(dd[~np.eye(24,dtype=bool)].min())}
  assert diff<1e-12 and result[mode]['endpoint_distance_error']<1e-12
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
