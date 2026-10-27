from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from handcrafted_ei.model.ei_network import EINetwork
output={}
for mode in ('one_hot','ring','topology'):
 folder=ROOT/'artifacts/phase_portraits_v2'/mode;m=EINetwork(overrides=json.loads((folder/'config.json').read_text()));W=m.weights*m.signs[None,:]
 with np.load(folder/'phase_portrait.npz') as z:
  B=z['basis'];D=np.linalg.pinv(B);result={'basis_condition_number':float(np.linalg.cond(B)),'dual_error':float(abs(D-z['dual']).max()),'conditions':{}}
  for key in ('autonomous','clock_held','retired'):
   origin=z[key+'_origin'];xy=z['grid_coordinates'];states=origin+xy@B.T;ext=m.tonic+z[key+'_clock']+z[key+'_stimulus']-m.theta
   F=(np.clip(states@W.T+ext,0,1)-states)/m.tau;velocity=F@D.T;off=F-velocity@B.T
   n=np.linalg.norm(F,axis=1);frac=np.divide(np.linalg.norm(off,axis=1),n,out=np.full_like(n,np.nan),where=n>1e-14)
   paths=z[key+'_paths'];pc=(paths-origin)@D.T;res=paths-origin-pc@B.T
   step=(np.clip(paths[:,:-1]@W.T+ext,0,1)-paths[:,:-1])/m.tau
   item={'all_grid_valid':bool(((states>=0)&(states<=1)).all()),'full_field_error':float(abs(F-z[key+'_full_velocity']).max()),'coordinate_velocity_error':float(abs(velocity-z[key+'_coordinate_velocity']).max()),'offplane_median':float(np.nanmedian(frac)),'offplane_norm_error':float(abs(np.linalg.norm(off,axis=1)-z[key+'_offplane_norm']).max()),'fullpath_Euler_error':float(abs(np.diff(paths,axis=1)-5*step).max()),'trajectory_projection_error':float(abs(pc-z[key+'_coordinates']).max()),'trajectory_offplane_max':float(np.linalg.norm(res,axis=-1).max()),'background_fullfield_residual':float(abs((np.clip(W@origin+ext,0,1)-origin)/m.tau).max())}
   assert max(item[k] for k in ('full_field_error','coordinate_velocity_error','offplane_norm_error','fullpath_Euler_error','trajectory_projection_error'))<1e-12
   result['conditions'][key]=item
  output[mode]=result
p=Path(__file__).with_suffix('.json');p.write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
