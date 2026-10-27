"""Source-checked repairs after strict diagnostics, without suppressing checks."""
import json
from pathlib import Path

root=Path(__file__).parent/'paper-review/documents/s001-zhou2023'
for i in range(1,19):
    path=root/'pages'/f'page-{i:04d}.json';p=json.loads(path.read_text(encoding='utf-8'))
    for item in p['items']:
        if 2<=i<=15 and (item['id'].endswith('-b000') or item['id'].endswith('-b001') or item.get('markdown')=='Nature Human Behaviour'):
            item.update(kind='omit',markdown='',reason='Visually verified repeated journal/Article/DOI header or journal footer; DOI retained on first page. Explicit region excludes duplicate running furniture.')
        if i>=16:
            item['markdown']=item.get('markdown','').replace('<u>','').replace('</u>','')
            if item['bbox'][0]>560 and item['bbox'][2]<590:
                item.update(kind='omit',markdown='',reason='Visually verified vertical natureportfolio reporting-summary template sidebar, March2021 form version or page number, not study data.')
    if i==3:
        next(x for x in p['items'] if x['kind']=='figure')['bbox'][3]=238
        p['review_notes']+=' Figure1 crop bottom238pt excludes caption starting239pt, preventing caption number double counting.'
    if i==12:
        p['items'].append({'id':'p0012-noise-inline-formula','kind':'formula','bbox':[306,463,564,480],'markdown':'','label':'Gaussian noise definition (inline equation)','asset_name':'noise-definition-inline'})
        p['review_notes']+=' Inline Gaussian-noise equation retained as source image due to square-root typography discrepancy.'
    path.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
print('Explicit furniture omissions, underline-markup repairs, caption crop and inline formula crop saved.')
