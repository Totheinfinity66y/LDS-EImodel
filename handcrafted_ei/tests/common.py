from functools import lru_cache
from handcrafted_ei.model.ei_network import EINetwork
from handcrafted_ei.task import conditions, encode, target
from handcrafted_ei.simulation import run_trial


@lru_cache(None)
def baseline():
    return [(c, run_trial(EINetwork(), encode(*c))) for c in conditions()]

