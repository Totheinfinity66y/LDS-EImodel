from pathlib import Path
import numpy as np
import yaml
from .connectivity import build
from .neuron import euler


class EINetwork:
    """Content enters only through apply_input; phase inputs carry timing only."""
    def __init__(self, config_path=None, overrides=None):
        path=Path(config_path) if config_path else Path(__file__).parents[1]/'config'/'baseline.yaml'
        self.config=yaml.safe_load(path.read_text(encoding='utf-8'))
        if overrides:
            unknown=set(overrides)-set(self.config)
            if unknown: raise ValueError(f'unknown parameters: {unknown}')
            self.config.update(overrides)
        c=self.config
        if any(not np.isfinite(v) or v<0 for v in c.values()): raise ValueError('invalid config')
        (self.groups,self.labels,self.signs,self.weights,self.tau,self.theta,self.tonic)=build(c)
        self.initialize()

    @property
    def signed_weights(self):
        return self.weights*self.signs[None,:]

    def initialize(self):
        self.rates=np.zeros(len(self.labels))
        for name in ('gate12','gate23','gate34'):
            idx=self.groups[name]; self.rates[idx]=np.clip(self.tonic[idx]-self.theta[idx],0,1)
        self.stimulus=np.zeros(len(self.labels)); self.clock=np.zeros(len(self.labels))
        self.time_ms=0.

    def apply_input(self,x_L,x_D,x_S):
        self.stimulus[:]=0
        for x,name in ((x_L,'R1'),(x_D,'M_D'),(x_S,'M_S')):
            x=np.asarray(x,dtype=float)
            if x.shape!=self.groups[name].shape or not np.all(np.isfinite(x)) or np.any(x<0) or np.any(x>1):
                raise ValueError('input currents must be bounded encoded vectors')
            self.stimulus[self.groups[name]]=self.config['w_input']*x

    def remove_stimulus(self):
        self.stimulus[:]=0

    def advance_phase(self,event):
        # These fixed currents enable all candidate branches equally.
        events={'to_R2':('release12','clock_release'),
                'to_R3':('release23','clock_release'),
                'to_R4':('release34','clock_release3')}
        if event in events:
            name,key=events[event]; self.clock[self.groups[name]]=self.config[key]
        elif event in ('retire1','retire2','retire3'):
            self.clock[self.groups['retire'][int(event[-1])-1]]=self.config['clock_retire']
        else: raise ValueError(f'unknown content-free clock event: {event}')

    def step(self):
        drive=self.signed_weights@self.rates+self.tonic+self.stimulus+self.clock-self.theta
        self.rates=euler(self.rates,drive,self.tau,self.config['dt_ms'])
        self.time_ms+=self.config['dt_ms']

    def integrate(self,duration_ms):
        n=duration_ms/self.config['dt_ms']
        if n<0 or not float(n).is_integer(): raise ValueError('duration must be a nonnegative multiple of dt')
        for _ in range(int(n)): self.step()

    def get_activity(self):
        return self.rates.copy()

    def readout(self):
        return self.rates[self.groups['Y']].copy()
