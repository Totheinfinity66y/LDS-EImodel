"""Only task encoding and evaluator truth use symbolic trial labels."""
from itertools import product
import numpy as np


def conditions():
    return list(product(range(6),(1,-1),(1,2)))


def target(l,d,s):
    if (l,d,s) not in conditions(): raise ValueError('invalid LDS condition')
    return tuple(int(x%6) for x in (l,l+d,l+d+d*s,l+2*d+d*s))


def encode(l,d,s,noise_sigma=0.,seed=7):
    if (l,d,s) not in conditions(): raise ValueError('invalid LDS condition')
    if not np.isfinite(noise_sigma) or noise_sigma<0: raise ValueError('invalid noise')
    x=np.eye(6)[l]
    if noise_sigma: x=np.clip(x+np.random.default_rng(seed).normal(0,noise_sigma,6),0,1)
    return {'x_L':x,'x_D':np.eye(2)[0 if d==1 else 1],'x_S':np.eye(2)[s-1]}
