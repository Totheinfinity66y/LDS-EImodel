"""External coordinates and nonnegative population embedding; no trial routing."""
import numpy as np

MODES = ('one_hot', 'ring', 'topology')
ANGLES = 2*np.pi*np.arange(6)/6
VECTORS = np.stack((np.cos(ANGLES), np.sin(ANGLES)), axis=1)


def permutation(delta):
    """Initialization-only [post,pre] Z6 operator."""
    t=np.zeros((6,6))
    for k in range(6): t[(k+delta)%6,k]=1
    return t


def rotation(delta):
    a=delta*np.pi/3
    return np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])


class LocationEncoding:
    def __init__(self,mode='one_hot',kappa=4.):
        if mode not in MODES: raise ValueError('unknown location encoding')
        if not np.isfinite(kappa) or kappa<=0: raise ValueError('invalid tuning width')
        self.mode=mode; self.kappa=kappa
        self.dimension={'one_hot':6,'ring':1,'topology':2}[mode]
        self.neural_dimension=6

    @staticmethod
    def circular_distance(a,b):
        delta=(np.asarray(a)-np.asarray(b))*np.pi/3
        return np.abs(np.arctan2(np.sin(delta),np.cos(delta)))

    def encode(self,k,noise_sigma=0.,seed=7):
        if k not in range(6): raise ValueError('invalid position')
        if not np.isfinite(noise_sigma) or noise_sigma<0: raise ValueError('invalid noise')
        if self.mode=='one_hot': x=np.eye(6)[k]
        elif self.mode=='ring': x=np.array([ANGLES[k]])
        else: x=VECTORS[k].copy()
        if noise_sigma:
            x=x+np.random.default_rng(seed).normal(0,noise_sigma/np.sqrt(self.dimension),self.dimension)
        if self.mode=='ring': x=np.mod(x,2*np.pi)
        elif self.mode=='topology':
            norm=np.linalg.norm(x)
            if norm: x=x/norm
        else: x=np.clip(x,0,None)
        return x

    def to_current(self,x):
        x=np.asarray(x,dtype=float)
        if x.shape!=(self.dimension,) or not np.all(np.isfinite(x)):
            raise ValueError('invalid location coordinate')
        if self.mode=='one_hot':
            if np.any(x<0): raise ValueError('negative one-hot current')
            current=x.copy()
        elif self.mode=='ring':
            current=np.exp(self.kappa*(np.cos(x[0]-ANGLES)-1))
        else:
            norm=np.linalg.norm(x)
            if not norm: return np.zeros(6)
            current=np.exp(self.kappa*(VECTORS@(x/norm)-1))
        norm=np.linalg.norm(current)
        return current/norm if norm else current

    def geometry(self):
        coordinates=np.array([self.encode(k) for k in range(6)])
        currents=np.array([self.to_current(x) for x in coordinates])
        distances=self.circular_distance(np.arange(6)[:,None],np.arange(6)[None,:])
        return {'mode':self.mode,'coordinate_dimension':self.dimension,
                'neural_dimension':6,'coordinates':coordinates.tolist(),
                'circular_distances':distances.tolist(),
                'coordinate_euclidean_distances':np.linalg.norm(coordinates[:,None]-coordinates[None,:],axis=2).tolist(),
                'currents':currents.tolist(),
                'current_distances':np.linalg.norm(currents[:,None]-currents[None,:],axis=2).tolist()}
