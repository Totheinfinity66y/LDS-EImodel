from pathlib import Path
import numpy as np
import yaml
from .connectivity import build
from .neuron import euler
from .location_encoding import LocationEncoding


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
        self.encoding=LocationEncoding(c['location_encoding'],c['encoding_kappa'])
        for key,value in c.items():
            if key=='location_encoding': continue
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value) or value<0:
                raise ValueError(f'invalid numeric config: {key}')
        for key in ('dt_ms','tau_e_ms','tau_i_ms','tau_decay_ms'):
            if c[key]<=0: raise ValueError(f'{key} must be positive')
        if c['dt_ms']>.5*min(c['tau_e_ms'],c['tau_i_ms'],c['tau_decay_ms']):
            raise ValueError('integration step too large')
        for key in ('sample_ms','delay_ms','transfer_ms','retire_ms','readout_ms','decision_ms','gap_ms'):
            if not float(c[key]/c['dt_ms']).is_integer(): raise ValueError(f'{key} must be a multiple of dt')
        if not 0<c['decision_ms']<=c['readout_ms']: raise ValueError('invalid decision window')
        if not isinstance(c['seed'],int): raise ValueError('seed must be an integer')
        (self.groups,self.labels,self.signs,self.weights,self.tau,self.theta,self.tonic)=build(c)
        self.initialize()

    @property
    def signed_weights(self):
        return self.weights*self.signs[None,:]

    def initialize(self):
        self.rates=np.zeros(len(self.labels))
        for name in ('I_tonic_R','I_tonic_M'):
            idx=self.groups[name]; self.rates[idx]=np.clip(self.tonic[idx]-self.theta[idx],0,1)
        self.stimulus=np.zeros(len(self.labels)); self.clock=np.zeros(len(self.labels))
        self.time_ms=0.

    def apply_input(self,x_L,x_D,x_S):
        self.stimulus[:]=0
        for x,name in ((self.encoding.to_current(x_L),'R1'),(x_D,'M_D'),(x_S,'M_S')):
            x=np.asarray(x,dtype=float)
            if x.shape!=self.groups[name].shape or not np.all(np.isfinite(x)) or np.any(x<0) or np.any(x>1):
                raise ValueError('input currents must be bounded encoded vectors')
            self.stimulus[self.groups[name]]=self.config['w_input']*x

    def remove_stimulus(self):
        self.stimulus[:]=0

    def advance_phase(self,event):
        # These fixed currents enable all candidate branches equally.
        events={'to_R2':('E_gate_D','clock_activation'),
                'to_R3':('E_gate_S','clock_activation'),
                'to_R4':('E_gate_34','clock_activation3')}
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
