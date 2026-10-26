"""Symbolic labels and evaluator truth stay outside neural state advancement."""
from itertools import product
import numpy as np
from ..model.location_encoding import LocationEncoding


def conditions():
    return list(product(range(6),(1,-1),(1,2)))


def target(l,d,s):
    if (l,d,s) not in conditions(): raise ValueError('invalid LDS condition')
    return tuple(int(x%6) for x in (l,l+d,l+d+d*s,l+2*d+d*s))


def encode(l,d,s,noise_sigma=0.,seed=7,mode='one_hot',kappa=4.):
    if (l,d,s) not in conditions(): raise ValueError('invalid LDS condition')
    x=LocationEncoding(mode,kappa).encode(l,noise_sigma,seed)
    return {'x_L':x,'x_D':np.eye(2)[0 if d==1 else 1],'x_S':np.eye(2)[s-1]}
