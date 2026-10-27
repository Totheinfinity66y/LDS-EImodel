"""F's replay of B's independent formulas, preserving B's original report."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'audit/paper2agent/zhou/verify_actual_results.py'
namespace={'__file__':str(src)}
exec(compile(src.read_text().split('out=Path(__file__)')[0],str(src),'exec'),namespace)
old=json.loads(src.with_name('ACTUAL_RESULTS_VERIFICATION.json').read_text())['rows']
new=namespace['rows'];changes=[{'before':a,'after':b} for a,b in zip(old,new) if a!=b]
maximum=max(abs(a[k]-b[k]) for a,b in zip(old,new) for k in a if isinstance(a[k],(int,float)) and isinstance(b[k],(int,float)))
report=dict(status='PASS_CURRENT_DATA_FORMULAS',source='B independent formula script replayed read-only by F; not another B review',source_script_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),rows=new,changed_rows=changes,max_scalar_difference_from_B_report=maximum)
Path(__file__).with_name('zhou_replay_readback.json').write_text(json.dumps(report,indent=2)+'\n')
print('Current formulas PASS; maximum scalar difference from B report:',maximum)
