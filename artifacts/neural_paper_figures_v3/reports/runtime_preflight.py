import sys, importlib.metadata, json, platform
from pathlib import Path
packages = ('numpy','scipy','matplotlib','scikit-learn','Pillow','PyYAML')
result = {'executable': sys.executable, 'python': sys.version, 'platform': platform.platform(),
          'capability': 'CPU NumPy/SciPy; GPU not required',
          'packages': {p: importlib.metadata.version(p) for p in packages}}
print(json.dumps(result, indent=2), flush=True)
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2), encoding='utf-8')
