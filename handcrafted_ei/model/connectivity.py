"""Initialization-only topology. Matrix orientation is [post, pre]."""
import numpy as np


def build(config):
    c = config
    groups, labels, signs = {}, [], []
    for name, n, sign in [('R1',6,1),('R2',12,1),('R3',24,1),('R4',24,1),
                          ('M_D',2,1),('M_S',2,1),('Y',6,1),
                          ('gate12',2,-1),('gate23',4,-1),('gate34',4,-1),
                          ('release12',2,-1),('release23',2,-1),('release34',1,-1),
                          ('comp_R1',6,-1),('comp_D',2,-1),('comp_S',2,-1),('retire',3,-1)]:
        groups[name]=np.arange(len(labels),len(labels)+n)
        labels.extend(f'{name}[{i}]' for i in range(n)); signs.extend([sign]*n)
    signs=np.array(signs)
    w=np.zeros((len(labels),len(labels)))
    theta=np.zeros(len(labels)); tonic=np.zeros(len(labels))
    tau=np.where(signs==1,c['tau_e_ms'],c['tau_i_ms'])
    def connect(post,pre,value):
        w[np.ix_(np.atleast_1d(post),np.atleast_1d(pre))]=value
    for name in ('R1','R2','R3','R4','M_D','M_S'):
        idx=groups[name]; w[idx,idx]=c['w_rec']
        theta[idx]=c['theta_e']; tonic[idx]=c['tonic_e']
    for name in ('gate12','gate23','gate34'):
        theta[groups[name]]=c['theta_gate']; tonic[groups[name]]=c['tonic_gate']
    theta[groups['release12']]=c['theta_release']
    theta[groups['release23']]=c['theta_release']
    theta[groups['release34']]=c['theta_release3']
    theta[groups['retire']]=c['theta_retire']
    theta[groups['Y']]=c['theta_y']
    # Fixed ring projections; d,s below are structural constants, never trial labels.
    r2=groups['R2'].reshape(2,6); r3=groups['R3'].reshape(4,6); r4=groups['R4'].reshape(4,6)
    for b,d in enumerate((1,-1)):
        for k in range(6): w[r2[b,(k+d)%6],groups['R1'][k]]=c['w_projection']
        connect(groups['release12'][b],groups['M_D'][b],c['w_mem'])
        connect(groups['gate12'][b],groups['release12'][b],c['w_release'])
        connect(r2[b],groups['gate12'][b],c['w_gate'])
        for j,s in enumerate((1,2)):
            branch=2*b+j
            for k in range(6):
                w[r3[branch,(k+d*s)%6],r2[b,k]]=c['w_projection']
                w[r4[branch,(k+d)%6],r3[branch,k]]=c['w_projection']
            connect(groups['gate23'][branch],groups['release23'][j],c['w_release'])
            connect(r3[branch],groups['gate23'][branch],c['w_gate'])
            connect(groups['gate34'][branch],groups['release34'],c['w_release'])
            connect(r4[branch],groups['gate34'][branch],c['w_gate'])
    for j in range(2): connect(groups['release23'][j],groups['M_S'][j],c['w_mem'])
    for response,competition in [('R1','comp_R1'),('M_D','comp_D'),('M_S','comp_S')]:
        e,i=groups[response],groups[competition]
        w[i,e]=c['w_comp_drive']
        for k in range(len(e)): connect(np.delete(e,k),i[k],c['w_comp'])
    for stage in range(1,5):
        for branch in groups[f'R{stage}'].reshape(-1,6):
            w[groups['Y'],branch]=c['w_out']
        if stage<4: connect(groups[f'R{stage}'],groups['retire'][stage-1],c['w_retire'])
    if np.any(w<0): raise ValueError('Dale magnitudes must be nonnegative')
    return groups, labels, signs, w, tau, theta, tonic
