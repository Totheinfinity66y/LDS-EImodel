import os, sys
print('python',sys.executable,flush=True)
for name in ('numpy','scipy','matplotlib','yaml','PIL'):
    print('importing',name,flush=True)
    module=__import__(name)
    print('OK',getattr(module,'__version__','unknown'),flush=True)
