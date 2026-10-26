"""Initialization-only, fixed Dale topology. Matrix orientation [post,pre]."""
import numpy as np
from .location_encoding import permutation


def build(config):
    c=config
    groups,labels,signs={},[],[]
    specs=[('R1',6,1),('R2',12,1),('R3',24,1),('R4',24,1),
           ('M_D',2,1),('M_S',2,1),('Y',6,1),
           ('E_gate_D',2,1),('E_gate_S',2,1),('E_gate_34',1,1),
           ('I_tonic_R',1,-1),('I_tonic_M',1,-1),
           ('I_decay_D',12,-1),('I_decay_S',24,-1),
           ('comp_R1',6,-1),('comp_D',2,-1),('comp_S',2,-1),('retire',3,-1)]
    for name,n,sign in specs:
        groups[name]=np.arange(len(labels),len(labels)+n)
        labels.extend(f'{name}[{i}]' for i in range(n)); signs.extend([sign]*n)
    signs=np.array(signs); n=len(labels)
    w=np.zeros((n,n)); theta=np.zeros(n); tonic=np.zeros(n)
    tau=np.where(signs==1,c['tau_e_ms'],c['tau_i_ms'])
    def connect(post,pre,value):
        w[np.ix_(np.atleast_1d(post),np.atleast_1d(pre))]=value
    for name in ('R1','R2','R3','R4','M_D','M_S'):
        idx=groups[name]; w[idx,idx]=c['w_rec']
        theta[idx]=c['theta_e']; tonic[idx]=c['tonic_e']
    for name in ('I_tonic_R','I_tonic_M'): tonic[groups[name]]=c['tonic_i']
    for name in ('M_D','M_S'): connect(groups[name],groups['I_tonic_M'],c['w_tonic_memory'])
    connect(groups['R1'],groups['I_tonic_R'],c['w_tonic_r1'])
    for name in ('R2','R3','R4'): connect(groups[name],groups['I_tonic_R'],c['w_tonic_response'])
    for name in ('E_gate_D','E_gate_S'): theta[groups[name]]=c['theta_activation']
    theta[groups['E_gate_34']]=c['theta_activation3']
    theta[groups['retire']]=c['theta_retire']; theta[groups['Y']]=c['theta_y']
    # Structural candidate d/s only: these are never per-trial labels.
    r2=groups['R2'].reshape(2,6); r3=groups['R3'].reshape(4,6); r4=groups['R4'].reshape(4,6)
    for b,d in enumerate((1,-1)):
        connect(r2[b],groups['R1'],c['w_projection']*permutation(d))
        connect(groups['E_gate_D'][b],groups['M_D'][b],c['w_mem'])
        connect(r2[b],groups['E_gate_D'][b],c['w_activation'])
        for j,s in enumerate((1,2)):
            branch=2*b+j
            connect(r3[branch],r2[b],c['w_projection']*permutation(d*s))
            connect(r4[branch],r3[branch],c['w_projection']*permutation(d))
            connect(r3[branch],groups['E_gate_S'][j],c['w_activation'])
            connect(r4[branch],groups['E_gate_34'],c['w_activation'])
    for j in range(2): connect(groups['E_gate_S'][j],groups['M_S'][j],c['w_mem'])
    # Per-unit detection: no threshold on summed R1/all-response activity.
    for response,memory,decay in [('R2','M_D','I_decay_D'),('R3','M_S','I_decay_S')]:
        idx=groups[decay]; tau[idx]=c['tau_decay_ms']; theta[idx]=c['theta_decay']
        w[idx,groups[response]]=c['w_response_decay']
        connect(groups[memory],idx,c['w_decay'])
    for response,competition in [('R1','comp_R1'),('M_D','comp_D'),('M_S','comp_S')]:
        e,i=groups[response],groups[competition]; w[i,e]=c['w_comp_drive']
        for k in range(len(e)): connect(np.delete(e,k),i[k],c['w_comp'])
    for stage in range(1,5):
        for branch in groups[f'R{stage}'].reshape(-1,6):
            w[groups['Y'],branch]=c['w_out']
        if stage<4: connect(groups[f'R{stage}'],groups['retire'][stage-1],c['w_retire'])
    if np.any(w<0): raise ValueError('Dale magnitudes must be nonnegative')
    return groups,labels,signs,w,tau,theta,tonic
